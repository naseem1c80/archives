from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image
import pytesseract
from scanner import scan_document
import mysql.connector
import cv2
app = Flask(__name__)

# إعداد الاتصال بقاعدة البيانات
db = mysql.connector.connect(
    host="localhost",       # اسم المضيف
    user="root",            # اسم المستخدم لقاعدة البيانات
    password="",            # كلمة المرور لقاعدة البيانات
    database="archives" # اسم قاعدة البيانات
)

# الاتصال بكائن الكيرسور



app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 ميغابايت كمثال
base_path = os.path.dirname(os.path.abspath(__file__))
#pytesseract.pytesseract.tesseract_cmd = os.path.join(base_path, "Tesseract-OCR","tesseract.exe")# "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/read-doc', methods=['POST'])
def read_doc():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم إرسال الملف'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'اسم الملف غير موجود'})

    if file:
        filename = f"{uuid.uuid4()}.png"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        # قراءة النص من الصورة
        text = read_text_from_image(path, lang='ara')

        return jsonify({'success': True, 'text': text})



def read_text_from_image(image_path, lang='eng+ara'):
    try:
        # قراءة الصورة باستخدام OpenCV
        img = cv2.imread(image_path)

        # تحويل الصورة إلى رمادية
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # تطبيق Threshold لتحسين التباين
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # (اختياري) قص المنطقة التي تحتوي على رقم الحوالة فقط
        # تأكد من تعديل القيم بناءً على موقع الرقم بدقة
        roi = thresh[75:115, 580:850]  # تقريبًا موقع رقم الحوالة في الصورة

        # تحويل الصورة إلى صيغة PIL لاستخدام pytesseract
        roi_pil = Image.fromarray(roi)

        # استخراج النص باستخدام pytesseract
        text = pytesseract.image_to_string(roi_pil, lang=lang)
        return text.strip()
    
    except Exception as e:
        return f"خطأ في قراءة الصورة: {str(e)}"




def read_text_from_image2(image_path, lang='ara'):
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang=lang)
        return text.strip()
    except Exception as e:
        return f"خطأ في قراءة الصورة: {str(e)}"
@app.route('/save-docs', methods=['POST'])
def save_docs():
    try:
        all_docs = []
        inserted_id =save_document(request)
        for key in request.form:
         if key.startswith('docs[') and key.endswith('][name]'):
                index = key.split('[')[1].split(']')[0]
                #name = request.form.get(f'docs[{index}][name]')
                doc_id = request.form.get(f'docs[{index}][id]')
                source = request.form.get(f'docs[{index}][source]')
                details = request.form.get(f'docs[{index}][details]')

                filename = f"{uuid.uuid4()}.png"
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                if source == 'scan':
                    scan_document(full_path)
                elif source == 'upload':
                    file = request.files.get(f'docs[{index}][file]')
                    if file and file.filename:
                        file.save(full_path)
                    else:
                        continue  # skip if no file provided
                        

                all_docs.append({
                    #'name_file': name,
                    'doc_id': inserted_id,
                    'file_path': '/' + full_path.replace('\\', '/'),
                    'details': details
                })

        res=insert_files(all_docs)
        return jsonify({'success': True, 'docs': all_docs})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def insert_files(docs):
    cursor = db.cursor()
    insert_query = """
    INSERT INTO files (doc_id, details, file_path, name_file)
    VALUES (%s, %s, %s, %s)
    """
    for doc in docs:
      cursor.execute(insert_query, (
        doc["doc_id"],
        doc["details"],
        doc["file_path"]
        #doc["name_file"]
      ))
    # حفظ التغييرات وإغلاق الاتصال
    db.commit()
    cursor.close()
    db.close()
    return jsonify({'docs':'add all document'})

def save_document(request):
        cursor = db.cursor()
        doc_id2 = request.form.get('doc_id')
        dat = request.form.get('date')
        name_d = request.form.get('name')
        query = "INSERT INTO documents (name, doc_id,date) VALUES (%s, %s, %s)"
        cursor.execute(query, (name_d, doc_id2,dat))
        db.commit()
        inserted_id = cursor.lastrowid
        cursor.close()
        return inserted_id

@app.route('/save-docss', methods=['POST'])
def save_docss():
    try:
        all_docs = []
        for key in request.form:
            if key.startswith('docs[') and key.endswith('][name]'):
                index = key.split('[')[1].split(']')[0]
                name = request.form[f'docs[{index}][name]']
                doc_id = request.form[f'docs[{index}][id]']
                source = request.form[f'docs[{index}][source]']
                details = request.form.get(f'docs[{index}][details]', '')

                filename = f"{uuid.uuid4()}.png"
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                if source == 'scan':
                    scan_document(full_path)
                elif source == 'upload':
                    file = request.files.get(f'docs[{index}][file]')
                    if file and file.filename:
                        file.save(full_path)
                    else:
                        return jsonify({'success': False, 'error': f'لم يتم رفع ملف للمستند رقم {index} ${request.form}'}), 200

                all_docs.append({
                    'name': name,
                    'doc_id': doc_id,
                    'file_path': full_path,
                    'details': details
                })

        return jsonify({'success': True, 'docs': all_docs})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/scan', methods=['POST'])
def scan():
    try:
        name = request.form.get('name', '')
        doc_id = request.form.get('doc_id', '')
        image_path = scan_document()
        return jsonify({
            'success': True,
            'image_url': '/' + image_path,
            'name': name,
            'doc_id': doc_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
if __name__ == '__main__':
    app.run(debug=True)
