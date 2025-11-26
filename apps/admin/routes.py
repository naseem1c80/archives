from apps.admin import blueprint
from flask import jsonify, render_template, redirect, request, url_for
from apps import db
from apps.models import Device, License, Section

#blueprint = Blueprint('blueprint', __name__, url_prefix='/admin')

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