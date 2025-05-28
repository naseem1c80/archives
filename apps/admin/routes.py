from flask import Blueprint, render_template, redirect, url_for
from apps import db
from apps.models import DeviceInfo

blueprint = Blueprint('blueprint', __name__, url_prefix='/admin')

@blueprint.route('/devices')
def device_list():
    devices = DeviceInfo.query.all()
    return render_template('admin/devices.html', devices=devices)

@blueprint.route('/device/authorize/<int:device_id>')
def authorize_device(device_id):
    device = DeviceInfo.query.get_or_404(device_id)
    device.is_authorized = True
    db.session.commit()
    return redirect(url_for('blueprint.device_list'))

@blueprint.route('/device/deauthorize/<int:device_id>')
def deauthorize_device(device_id):
    device = DeviceInfo.query.get_or_404(device_id)
    device.is_authorized = False
    db.session.commit()
    return redirect(url_for('blueprint.device_list'))
