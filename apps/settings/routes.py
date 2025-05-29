# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps import socketio  
from apps.settings import blueprint
from flask import render_template, request,session,redirect,jsonify
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound
from apps import db, login_manager
from apps.models import Users,Notification,Role,DeviceInfo
#import eventlet
#from apps.extensions import 
import re

import platform
import socket
import os
import psutil


@blueprint.route('/getinfo_device')
def get_system_info():
    info = {
        "System": platform.system(),
        "Node Name": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Architecture": platform.architecture()[0],
        "CPU Cores (logical)": psutil.cpu_count(logical=True),
        "CPU Cores (physical)": psutil.cpu_count(logical=False),
        "RAM (GB)": round(psutil.virtual_memory().total / (1024**3), 2),
        "Hostname": socket.gethostname(),
        "IP Address": socket.gethostbyname(socket.gethostname()),
        "Current User": os.getlogin(),
    }
    return info

@blueprint.route('/send_notification', methods=['POST'])
@login_required
def send_notification():
    user_id = request.form['user_id']
    from_id = current_user.id
    message = request.form['message']
    notification = Notification(user_id=user_id, message=message,from_id=from_id)
    db.session.add(notification)
    db.session.commit()

    # إرسال إشعار مباشر عبر WebSocket
    socketio.emit('new_notification', {
        'user_id': user_id,
        'from_id': from_id,
        'message': message
    })

    return jsonify({'status': 'sent'})

@blueprint.route('/set_language/<lang>')
def set_language(lang):
    prev_url = request.referrer
    if lang in ['en', 'ar']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.index'))
    
@blueprint.route('/settings')
@login_required
def settings():

    return render_template('settings/settings.html', segment='settings')



@blueprint.route("/permissions", methods=["GET"])
@login_required
def user_permission():
    try:
        return render_template('permissions/permissions.html')
    except Exception as e:
     return jsonify({'success': False, 'message': str(e)})

    return jsonify(success=True)


@blueprint.route('/get_roles')
@login_required
def get_roles():
    roles = Role.query.all()
    data = [{
        'id': role.id,
        'name': role.name,
        'permissions': role.permissions  # this works if permissions is JSON-serializable
    } for role in roles]
    
    return jsonify({'roles': data})

 
@blueprint.route('/role', methods=['POST', 'PUT'])
@login_required
def save_or_update_role():
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'error': 'Role name is required'}), 400

    role_id = data.get('id')  # Optional for update
    name = data['name']
    permissions = data.get('permissions', [])

    if request.method == 'POST':
        # Create new role
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            return jsonify({'error': 'Role already exists'}), 400

        new_role = Role(name=name, permissions=permissions)
        db.session.add(new_role)
        db.session.commit()
        return jsonify({'message': 'Role created', 'role': {'id': new_role.id, 'name': new_role.name}}), 201

    elif request.method == 'PUT':
        # Update existing role
        if not role_id:
            return jsonify({'error': 'Role ID is required for update'}), 400

        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404

        role.name = name
        role.permissions = permissions
        db.session.commit()
        return jsonify({'message': 'Role updated', 'role': {'id': role.id, 'name': role.name}})
   


def collect_device_info():
    info = {
        "hostname": socket.gethostname(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "cpu_cores": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
    }
    return info

def register_or_check_license(license_key):
    info = collect_device_info()
    device = DeviceInfo.query.filter_by(hostname=info["hostname"]).first()

    if device:
        if device.license_key == license_key and device.is_authorized:
            return True  # ✔️ الاتصال مسموح
        else:
            return False  # ❌ غير مرخّص أو مفتاح خاطئ
    else:
        # تسجيل الجهاز لأول مرة
        new_device = DeviceInfo(**info, license_key=license_key, is_authorized=False)
        db.session.add(new_device)
        db.session.commit()
        return False  # ❌ يحتاج إلى تفعيل الترخيص يدوياً من المسؤول

