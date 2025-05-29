from flask import session, redirect, url_for, current_app
from datetime import datetime, timedelta
import socket
import platform
import psutil
import uuid
import hashlib
from apps.models import Device
from apps import db

def get_hardware_fingerprint():
    """إنشاء بصمة فريدة للجهاز"""
    h = hashlib.sha256()
    h.update(platform.node().encode())  # اسم الجهاز
    h.update(platform.processor().encode())  # المعالج
    try:
        import subprocess
        mac = subprocess.getoutput("cat /sys/class/net/*/address | head -1")
        h.update(mac.encode())  # عنوان MAC
    except:
        pass
    return h.hexdigest()

def check_device_license():
    """التحقق من ترخيص الجهاز وتوجيهه للتفعيل إذا لزم"""
    if not current_app.config.get('LICENSE_REQUIRED', True):
        return None

    hardware_hash = get_hardware_fingerprint()
    device = Device.query.filter_by(hardware_hash=hardware_hash).first()

    # إذا كان الجهاز مسجل ومفعل
    if device and device.is_authorized and device.license_expiry > datetime.utcnow():
        device.last_seen = datetime.utcnow()
        db.session.commit()
        return None

    # إذا كان الجهاز غير مسجل
    if not device:
        device_info = {
            'hardware_hash': hardware_hash,
            'hostname': socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname()),
            'system': platform.system(),
            'processor': platform.processor(),
            'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
        }
        
        device = Device(**device_info)
        db.session.add(device)
        db.session.commit()

    session['device_id'] = device.device_id
    return redirect(url_for('license.activate_license'))

def activate_device_license(license_key):
    """تفعيل ترخيص الجهاز"""
    device_id = session.get('device_id')
    if not device_id:
        return False

    device = Device.query.get(device_id)
    if not device:
        return False

    # التحقق من صحة الترخيص (هنا يمكن إضافة اتصال بخدمة التحقق)
    valid_licenses = current_app.config.get('VALID_LICENSES', [])
    
    if license_key in valid_licenses:
        device.license_key = license_key
        device.license_hash = hashlib.sha256(license_key.encode()).hexdigest()
        device.is_authorized = True
        device.license_expiry = datetime.utcnow() + timedelta(days=365)
        db.session.commit()
        return True
    
    return False

def get_device_status():
    """الحصول على حالة الجهاز الحالية"""
    device_id = session.get('device_id')
    if not device_id:
        return 'unregistered'
    
    device = Device.query.get(device_id)
    if not device:
        return 'unregistered'
    
    if not device.is_authorized:
        return 'unauthorized'
    
    if datetime.utcnow() > device.license_expiry:
        return 'expired'
    
    return 'authorized'

def register_device(device_info):
    """تسجيل جهاز جديد (نسخة احتياطية)"""
    try:
        hardware_hash = get_hardware_fingerprint()
        
        device = Device(
            hardware_hash=hardware_hash,
            hostname=device_info.get('hostname'),
            ip_address=device_info.get('ip_address'),
            system=device_info.get('system'),
            processor=device_info.get('processor'),
            license_key=device_info.get('license_key', None),
            status='pending'
        )
        
        if device_info.get('license_key'):
            device.license_hash = hashlib.sha256(device_info['license_key'].encode()).hexdigest()
        
        db.session.add(device)
        db.session.commit()
        return device
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Device registration failed: {str(e)}")
        raise