from apps.models import DeviceInfo
from inc.device_info import get_device_info
from apps import db

def check_or_register_device(license_key: str):
info = get_device_info()
device = DeviceInfo.query.filter_by(mac_address=info["mac_address"]).first()

python
نسخ الكود
