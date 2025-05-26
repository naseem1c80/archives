from PIL import Image
import subprocess
import os
import uuid
from PIL import Image

def scan_document(output_path="static/uploads/"):
    naps2_path = r"C:\Program Files\NAPS2\NAPS2.Console.exe"
    profile_name = "default-profile"

    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
        
    filename = f"ah{uuid.uuid4()}.png"
    full_path = os.path.join('static/uploads', filename)
    result = subprocess.run([
        naps2_path,
        "scan",
        "--profile", profile_name,
        "--output", full_path
    ])

    if result.returncode == 0:
        print(f"✅ تم المسح بنجاح وحفظ الملف في: {full_path}")
        return full_path
    else:
        print("❌ حدث خطأ أثناء المسح.")
        return None

def scan_documentolllll(output_path="static/uploads/"):
    naps2_path = r"C:\Program Files\NAPS2\NAPS2.Console.exe"
    profile_name = "default-profile"

    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
        
    filename = f"ah{uuid.uuid4()}.png"
    full_path = os.path.join('static/uploads', filename)
    result = subprocess.run([
        naps2_path,
        "scan",
        "--profile", profile_name,
        "--output", full_path
    ])

    if result.returncode == 0:
        print(f"✅ تم المسح بنجاح وحفظ الملف في: {result}")
        return full_path
    else:
        print("❌ حدث خطأ أثناء المسح.")
        return None
