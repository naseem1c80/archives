from flask import Flask, render_template, request, jsonify,send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image
import pytesseract
from scanner import scan_document
import mysql.connector
import cv2
from pdf2image import convert_from_path
import easyocr
import PyPDF2
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





# السماح بامتدادات الملفات
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_image(image_path, lang='ara'):
    try:
        # معالجة الصورة وتحسينها قبل OCR
        img = cv2.imread(image_path)
        if img is None:
            return {'error': 'تعذر قراءة ملف الصورة'}
            
        # تحسين الصورة لتحسين دقة OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, processed_img = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # حفظ الصورة المعالجة
        processed_path = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_{os.path.basename(image_path)}")
        cv2.imwrite(processed_path, processed_img)
        
        # استخراج النص باستخدام EasyOCR
        reader = easyocr.Reader([lang])
        results = reader.readtext(processed_img)
        extracted_text = [text[1] for text in results]
        
        return {
            'text': '\n'.join(extracted_text),
            'processed_image_path': processed_path
        }
        
    except Exception as e:
        return {'error': f'حدث خطأ أثناء معالجة الصورة: {str(e)}'}

def extract_text_from_pdf(pdf_path, lang='ara'):
    try:
        # المحاولة أولاً باستخراج النص مباشرة من PDF
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
               text += page.extract_text() or ""
        
        # إذا كان النص المباشر كافياً
        if len(text.strip()) > 50:
            return {'text': text}
        
        # إذا كان PDF ممسوحاً ضوئياً (صور)
        images = convert_from_path(pdf_path)
        extracted_text = ""
        
        for i, img in enumerate(images):
            # حفظ الصورة مؤقتاً
            temp_img_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_page_{i}.jpg")
            img.save(temp_img_path, 'JPEG')
            
            # استخراج النص من الصورة
            result = read_text_from_image(temp_img_path, lang)
            
            if 'text' in result:
                extracted_text += result['text'] + "\n"
            
            # حذف الصورة المؤقتة
            os.remove(temp_img_path)
        
        return {'text': extracted_text.strip()}
        
    except Exception as e:
        return {'error': f'حدث خطأ أثناء معالجة PDF: {str(e)}'}
    

@app.route('/read-doc', methods=['POST'])
def read_doc():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم إرسال الملف'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'اسم الملف غير موجود'})

    if file and allowed_file(file.filename):
        try:
            # حفظ الملف المرفق
            filename = secure_filename(f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # تحديد نوع الملف ومعالجته
            if filename.lower().endswith('.pdf'):
                result = extract_text_from_pdf(file_path, lang='ara')
            else:
                result = read_text_from_image(file_path, lang='ara')
            
            # حذف الملف الأصلي بعد المعالجة
            #os.remove(file_path)
            
            if 'error' in result:
                return jsonify({'success': False, 'error': result['error']})
            
            return jsonify({
                'success': True,
                'text': result['text'],
                'processed_image_path': result.get('processed_image_path', '')
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'حدث خطأ أثناء المعالجة: {str(e)}'})
    
    return jsonify({'success': False, 'error': 'نوع الملف غير مدعوم'})


@app.route('/read-docs', methods=['POST'])
def read_docs():
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
        #text = read_text_from_image(path, lang='ara')
        result = read_text_from_image(path, lang='ara')
        if 'error' in result:
         return jsonify({'success': True, 'text': result['error']})
         print(result['error'])
        else:
         print("النص:", result['text'])
         print("تم حفظ الصورة في:", result['processed_image_path'])
         return jsonify({'success': True, 'text': result['text'],'processed_image_path':result['processed_image_path']})

@app.route('/processed_images/<filename>')
def serve_processed_image(filename):
    return send_from_directory('processed_images', filename)




def read_text_from_image(image_path, lang='eng+ara', save_processed=True, output_dir='processed_images'):
    try:
        # إنشاء مجلد الإخراج إذا لم يكن موجوداً
        if save_processed and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # قراءة الصورة
        img = cv2.imread(image_path)

        # تحويل إلى رمادي
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Threshold لتحسين التباين
        _, thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)

        # قص منطقة رقم الحوالة فقط
        roi = thresh[75:115, 580:850]  # عدل القيم إذا لزم الأمر

        # حفظ الصورة بعد المعالجة (ROI)
        processed_image_path = None
        if save_processed:
            filename =f"{uuid.uuid4()}.png"
            processed_image_path = os.path.join(output_dir, filename)
            cv2.imwrite(processed_image_path, thresh)

        # تحويل إلى PIL للصيغة المتوافقة مع pytesseract
        roi_pil = Image.fromarray(thresh)

        # التعرف على النص
        text = pytesseract.image_to_string(image_path, lang=lang).strip()

        # إرجاع النص ومسار الصورة
        return {
            'text': text,
            'processed_image_path': processed_image_path
        }

    except Exception as e:
        return {
            'text': '',
            'error': f"خطأ في قراءة الصورة: {str(e)}",
            'processed_image_path': None
        }



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
