from apps.admin import blueprint
from flask import jsonify, render_template, redirect, request, url_for
from apps import db
from apps.models import Device, License, Section,ActivityLog

#blueprint = Blueprint('blueprint', __name__, url_prefix='/admin')
from user_agents import parse

def get_device_info(request):
    ua_string = request.headers.get("User-Agent", "")
    user_agent = parse(ua_string)

    return {
        "ip_address": request.remote_addr,
        "device_type": "mobile" if user_agent.is_mobile else "desktop",
        "os": user_agent.os.family,
        "browser": user_agent.browser.family,
        "user_agent": ua_string
    }
def log_action(user_id, action, table_name, record_id, old_data=None, new_data=None):
    device = get_device_info(request)
    log = ActivityLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_data=json.dumps(old_data, default=str) if old_data else None,
        new_data=json.dumps(new_data, default=str) if new_data else None,
        
        # بيانات الجهاز
        ip_address=device["ip_address"],
        device_type=device["device_type"],
        os=device["os"],
        browser=device["browser"],
        user_agent=device["user_agent"]
    )

    db.session.add(log)
    db.session.commit()



@blueprint.route('/getactivitylogs', methods=['GET', 'OPTIONS'])
#@cross_origin()
def getactivitylogs():
    try:
        # قراءة الباراميترات مع قيم افتراضية
        limit = min(request.args.get('limit', default=20, type=int), 100)
        offset = request.args.get('offset', default=0, type=int)

        action = request.args.get('action', default=None, type=str)
        table_name = request.args.get('table_name', default=None, type=str)
        device_type = request.args.get('device_type', default=None, type=str)
        search = request.args.get('search', default=None, type=str)

        sort_by = request.args.get('sort_by', default='id')
        sort_order = request.args.get('sort_order', default='desc')

        # الحقول المسموح استخدامها في sort_by
        sort_column_map = {
            'id': ActivityLog.id,
            'action': ActivityLog.action,
            'table_name': ActivityLog.table_name,
            'created_at': ActivityLog.created_at,
            'record_id': ActivityLog.record_id
        }

        # الاستعلام الأساسي
        query = db.session.query(ActivityLog)

        # فلترة نوع العملية
        if action:
            query = query.filter(ActivityLog.action == action)

        # فلترة الجدول
        if table_name:
            query = query.filter(ActivityLog.table_name.ilike(f"%{table_name}%"))

        # فلترة نوع الجهاز
        if device_type:
            query = query.filter(ActivityLog.device_type == device_type)

        # البحث في عدة حقول
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    ActivityLog.action.ilike(search_term),
                    ActivityLog.table_name.ilike(search_term),
                    ActivityLog.browser.ilike(search_term),
                    ActivityLog.os.ilike(search_term),
                    ActivityLog.user_agent.ilike(search_term)
                )
            )

        # العدد الكلي
        total = query.count()

        # الفرز
        if sort_by in sort_column_map:
            column = sort_column_map[sort_by]
            if sort_order.lower() == 'asc':
                query = query.order_by(column.asc())
            else:
                query = query.order_by(column.desc())
        else:
            query = query.order_by(ActivityLog.id.desc())

        # limit + offset
        logs = query.offset(offset).limit(limit).all()

        # تحويل البيانات
        response = {
            "status": "success",
            "rows": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "user_name": log.user.full_name if log.user else None,
                    "action": log.action,
                    "table_name": log.table_name,
                    "record_id": log.record_id,
                    "old_data": log.old_data,
                    "new_data": log.new_data,
                    "ip_address": log.ip_address,
                    "device_type": log.device_type,
                    "os": log.os,
                    "browser": log.browser,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for log in logs
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f"Error in getactivitylogs: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error {e}"}), 500


@blueprint.route("/activity-logs")
def activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.id.desc()).all()
    return render_template("admin/activity_logs.html", logs=logs)


@blueprint.route('/devices')
def device_list():
    devices =  Device.query.all()
    return render_template('admin/devices.html', devices=devices)

@blueprint.route('/device/authorize/<int:device_id>')
def authorize_device(device_id):
    device =  Device.query.get_or_404(device_id)
    device.is_authorized = True
    db.session.commit()
    return redirect(url_for('blueprint.device_list'))

@blueprint.route('/device/deauthorize/<int:device_id>')
def deauthorize_device(device_id):
    device =  Device.query.get_or_404(device_id)
    device.is_authorized = False
    db.session.commit()
    return redirect(url_for('blueprint.device_list'))



@blueprint.route('/licenses')
def manage_licenses():
    pending_licenses = License.query.filter_by(is_approved=False).all()
    approved_licenses = License.query.filter_by(is_approved=True).all()
    return render_template('admin/licenses.html', 
                         pending=pending_licenses,
                         approved=approved_licenses)













@blueprint.route("/getsections", methods=["GET"])
def getsections():
  sections_data = Section.query.all()
  response = []
  for doc in sections_data:
    response.append({
          "id": doc.id,
          "name": doc.name,
        "created_at":doc.created_at.strftime('%Y-%m-%d %H:%M')  if doc.created_at else None})
  return response          
  
@blueprint.route("/sections", methods=["GET"])
def view_sections():
    return render_template("admin/sections.html")

@blueprint.route("/sections/add", methods=["POST"])
def add_section():
    try:
        name = request.json['name']#.form.get("name")
        if not name:
            return jsonify(success=False, message="الاسم مطلوب")
        new_type = Section(name=name)
        db.session.add(new_type)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@blueprint.route("/sections/update/<int:type_id>", methods=["POST"])
def update_section(type_id):
    try:
        name = request.json['name']#.form.get("name")
        doc_type = Section.query.get(type_id)
        if not doc_type:
            return jsonify(success=False, message="النوع غير موجود")
        doc_type.name = name
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))




def seed_sections():
    if Section.query.count() == 0:
        default_sections = [
            Section(name='الاستقبال'),
            Section(name='التحويلات المحلية'),
            Section(name='التحويلات الدولية'),
            Section(name='خدمة العملاء'),
            Section(name='الامتثال والمطابقة'),
            Section(name='المحاسبة'),
            Section(name='تقنية المعلومات'),
            Section(name='إدارة المخاطر')
        ]
        db.session.add_all(default_sections)
        db.session.commit()
        print("✅ تم إدخال البيانات الافتراضية إلى جدول الأقسام.")
    else:
        print("ℹ️ جدول الأقسام يحتوي بالفعل على بيانات.")