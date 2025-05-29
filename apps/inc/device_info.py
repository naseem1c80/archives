import platform
import socket
import uuid
import getpass

def get_device_info():
return {
"device_name": socket.gethostname(),
"ip_address": socket.gethostbyname(socket.gethostname()),
"mac_address": ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
for ele in range(0, 8 * 6, 8)][::-1]),
"os": platform.system(),
"os_version": platform.version(),
"architecture": platform.machine(),
"processor": platform.processor(),
"user": getpass.getuser()
}
