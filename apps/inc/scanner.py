import pyinsane2
from PIL import Image
import subprocess
import os
import uuid


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
        print(f"✅ تم المسح بنجاح وحفظ الملف في: {result}")
        return full_path
    else:
        print("❌ حدث خطأ أثناء المسح.")
        return None

def scan_document254(output_path="static/scanned.png", scanner_name=None):
    try:
        pyinsane2.init()
        devices = pyinsane2.get_devices()
        if not devices:
            raise Exception("لم يتم العثور على ماسح ضوئي.")

        if scanner_name:
            scanner = next((d for d in devices if scanner_name in d.name), devices[0])
        else:
            scanner = devices[0]

        scan_session = scanner.scan(multiple=False)
        while not scan_session.done:
            try:
                scan_session.scan.read()
            except EOFError:
                break

        if scan_session.images:
            image = scan_session.images[0]
            image.save(output_path)
        else:
            raise Exception("لم يتم الحصول على صورة من الماسح.")

        return output_path

    finally:
        pyinsane2.exit()

def scan_document3(output_path="static/scanned.png"):
    try:
        pyinsane2.init()
        devices = pyinsane2.get_devices()
        if not devices:
            raise Exception("لم يتم العثور على ماسح ضوئي.")
        
        scanner = devices[0]

        # إعداد الجلسة
        scan_session = scanner.scan(multiple=False)

        # تنفيذ المسح
        while not scan_session.done:
            try:
                scan_session.scan.read()
            except EOFError:
                break  # بعض الماسحات قد ترجع EOF في نهاية الصفحة

        # حفظ الصورة
        if scan_session.images:
            image = scan_session.images[0]
            image.save(output_path)
        else:
            raise Exception("لم يتم الحصول على صورة من الماسح.")

        return output_path

    except Exception as e:
        raise Exception(f"خطأ في المسح الضوئي: {str(e)}")

    finally:
        pyinsane2.exit()

def scan_document5(output_path="static/scanned.png"):
    pyinsane2.init()
    devices = pyinsane2.get_devices()
    if not devices:
        raise Exception("لم يتم العثور على ماسح ضوئي.")
    scanner = devices[0]

    scan_session = scanner.scan(multiple=False)
    while not scan_session.done:
        scan_session.scan.read()
    
    image = scan_session.images[0]
    image.save(output_path)

    pyinsane2.exit()
    return output_path

def scan_documents(output_path="static/scanned.png"):
    pyinsane2.init()
    devices = pyinsane2.get_devices()
    if not devices:
        #return output_path
        raise Exception("لم يتم العثور على ماسح.")
    scanner = devices[0]
    session = scanner.scan(multiple=False)

    while not session.done:
        session.scan.read()

    image = session.images[0]
    image.save(output_path)
    pyinsane2.exit()
    return output_path

