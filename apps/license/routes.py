import datetime
from flask import Blueprint, render_template, request, flash,session,redirect,url_for
from pymysql import IntegrityError
from apps.license.controller import check_device_license
from apps.models import Device
from apps import db

license_bp = Blueprint('license', __name__, url_prefix='/license')

@license_bp.route('/request', methods=['GET', 'POST'])
def license_request():
    device_id = session.get('device_id')
    if not device_id:
        return redirect(url_for('home_blueprint.index'))
        #return redirect(url_for('home.index'))
        
    device = Device.query.filter_by(device_id=device_id).first_or_404()
    
    if request.method == 'POST':
        license_key = request.form.get('license_key')
        if not license_key:
            flash('الرجاء إدخال كود الترخيص', 'danger')
            return redirect(url_for('license.license_request'))
            
        device.license_key = license_key
        db.session.commit()
        flash('تم إرسال طلب الترخيص، الرجاء انتظار الموافقة', 'success')
        return redirect(url_for('license.license_pending'))
    
    return render_template('license/request.html', device=device)

@license_bp.route('/pending')
def license_pending():
    return render_template('license/pending.html')



@license_bp.route('/activated', methods=['GET', 'POST'])
def activate_licensed():
    device_id = session.get('device_id')
    if not device_id:
        return redirect(url_for('home_blueprint.index'))
        #return redirect(url_for('home.index'))
        
    device = Device.query.filter_by(device_id=device_id).first_or_404()
   
    if request.method == 'POST':
        license_key = request.form.get('license_key')
        device_id = request.form.get('device_id')
        
        # التحقق من الترخيص في قاعدة البيانات
        license = Device.query.filter_by(device_id=device_id, is_approved=False).first()
        
        if license:
            license.activate(device_id)
            db.session.commit()
            flash('تم تفعيل الترخيص بنجاح', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('كود الترخيص غير صالح أو مستخدم مسبقاً', 'danger')
    
    return render_template('license/activate.html',device=device)


@license_bp.route('/activate', methods=['GET', 'POST'])
def activate_license():
    if request.method == 'POST':
        license_key = request.form.get('license_key').strip()
        hardware_id = Device.generate_hardware_id()
        
        # التحقق من عدم استخدام الترخيص لنفس الجهاز
        existing = Device.query.filter_by(
            hardware_id=hardware_id,
            license_key=license_key
        ).first()
        
        if existing:
            flash('هذا الترخيص مفعل بالفعل على هذا الجهاز', 'warning')
            return redirect(url_for('license.activate'))
            
        # التحقق من صحة الترخيص
        license = License.query.filter_by(
            key=license_key,
            is_used=False
        ).first()
        
        if not license:
            flash('كود الترخيص غير صالح أو مستخدم', 'danger')
            return redirect(url_for('license.activate'))
            
        try:
            new_activation = Device(
                hardware_id=hardware_id,
                license_key=license_key,
                is_active=True,
                activated_at=datetime.utcnow()
            )
            license.is_used = True
            db.session.add(new_activation)
            db.session.commit()
            flash('تم تفعيل الترخيص بنجاح', 'success')
            return redirect(url_for('dashboard.index'))
        except IntegrityError:
            db.session.rollback()
            flash('حدث خطأ أثناء التفعيل، حاول مرة أخرى', 'danger')
    
    hardware_id = Device.generate_hardware_id()
    return render_template('license/activate.html', hardware_id=hardware_id)