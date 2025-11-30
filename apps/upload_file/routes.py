from flask import Blueprint
from flask import jsonify, render_template, redirect, request, url_for
from apps import db
from apps.models import Device, License, Section,ActivityLog
import os
import uuid
#blueprint = Blueprint('blueprint', __name__, url_prefix='/admin')
from user_agents import parse

from datetime import datetime
UPLOAD_FOLDER = 'static/uploads_cropped'
SCAN_IMAGE = 'static/scan_image'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
upload_print = Blueprint('upload_blueprint',__name__,url_prefix='/')
def save_file_storage(file_storage):
    # file_storage: werkzeug.datastructures.FileStorage
    ext = os.path.splitext(file_storage.filename)[1] or ".png"
    filename = datetime.utcnow().strftime("%Y%m%d%H%M%S%f") + ext
    path = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(path)
    return filename, path

@upload_print.route('/upload_document')
def index():
    # صفحة الاختبار: يمكنك أيضاً تقديم ملف HTML ثابت
    return render_template("documents/upload_document.html")

@upload_print.route('/upload_screenshot', methods=['POST'])
def upload_screenshot():
    """
    يستقبل ملف من نوع multipart/form-data باسم الحقل 'screenshot'
    أو يمكن إرسال base64 في حقل 'b64' (اختياري).
    """
    # خيار 1: ملف عادي
    if 'screenshot' in request.files:
        f = request.files['screenshot']
        if f.filename == "":
            return jsonify({"ok": False, "error": "empty filename"}), 400
        filename, path = save_file_storage(f)
        return jsonify({"ok": True, "filename": filename, "url": f"{path}"}), 200

    # خيار 2: بيانات base64 (data URL)
    b64 = request.form.get('b64')
    if b64:
        import base64, re
        m = re.match(r'data:(image/[^;]+);base64,(.+)', b64)
        if not m:
            return jsonify({"ok": False, "error": "invalid base64 data"}), 400
        mime, data = m.group(1), m.group(2)
        ext = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/webp': '.webp'
        }.get(mime, '.png')
        filename = datetime.utcnow().strftime("%Y%m%d%H%M%S%f") + ext
        path = os.path.join(UPLOAD_FOLDER, filename)
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(data))
        return jsonify({"ok": True, "filename": filename, "url": f"{path}"}), 200

    return jsonify({"ok": False, "error": "no file provided"}), 400






@upload_print.route('/save-cropped', methods=['POST'])
def save_cropped():
    image = request.files.get('cropped_image')
    if image:
        filename = f"cropped_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(path)
                # قراءة النص من الصورة
        return jsonify({
            'success': True,
            'url': path
        })
        return jsonify({'success': True, 'url': f"{path}"})
    return jsonify({'success': False, 'error': 'No image received'})

@upload_print.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)