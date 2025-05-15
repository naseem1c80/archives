# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.documents import blueprint

from apps.models import Document
from PIL import Image
import pytesseract
#from scanner import scan_document
import mysql.connector
import os
import uuid
from flask_cors import cross_origin
import PyPDF2
from pdf2image import convert_from_bytes
from flask import render_template, request, redirect, url_for, flash, jsonify, session,send_from_directory
from flask_login import  current_user
from apps.inc.Convert import convert_pdf_to_images
from werkzeug.utils import secure_filename
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SCAN_IMAGE='E:\scan_image'
@blueprint.route('/documents')
def documents():
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('documents/documents.html')


@blueprint.route('/create_document')
def create_document():
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('documents/create_document.html')



'''

UPLOAD_FOLDER = 'read-doc'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'لم يتم إرسال الملف', 400

    file = request.files['file']
    filename = file.filename
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return f'تم حفظ الملف باسم: {filename}'
'''

@blueprint.route('/getdocuments', methods=['GET','OPTIONS'])
@cross_origin()
def getdocuments():
    try:
        # Get 'limit' from query parameters, default to None
        limit = request.args.get('limit', type=int)

        # Fetch documents, apply limit if provided
        query = Document.query
        if limit:
            query = query.limit(limit)
        documents = query.all()

        # Build response
        response = [{
            "id": doc.id,
            "name": doc.name,
            "number_doc": doc.number_doc,
            "verify_user": doc.verify_user,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        } for doc in documents]

        return jsonify({"status":'success','data':response})

    except Exception as e:
        return jsonify({"error": f"Internal server error{e}"}), 500
'''
@blueprint.route('/getdocuments',methods=['OPTIONS','GET'])
def getdocuments():
    documents = Document.query.all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "number_doc": u.number_doc,
        "verify_user": u.verify_user,
        "created_at": u.created_at
    } for u in documents])
   
'''   
   
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    #return render_template('documents/documents.html')


@blueprint.route('/read-doc', methods=['POST'])
def read_doc():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم إرسال الملف'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'اسم الملف غير موجود'})

    ext = os.path.splitext(file.filename)[1].lower()

    try:
        if ext == '.pdf':
            # تحويل أول صفحة من PDF إلى صورة
            images = convert_from_bytes(file.read(), dpi=200, fmt='png',poppler_path=r'C:\poppler\Library\bin' )
            if not images:
                return jsonify({'success': False, 'error': 'لم يتمكن من تحويل PDF إلى صورة'})
            
            image = images[0]  # أول صفحة فقط
            filename = f"{uuid.uuid4()}.png"
            path = os.path.join(SCAN_IMAGE, filename)
            image.save(path, 'PNG')

        elif ext in ['.png', '.jpg', '.jpeg']:
            filename = f"{uuid.uuid4()}.png"
            path = os.path.join(SCAN_IMAGE, filename)
            file.save(path)

        else:
            return jsonify({'success': False, 'message': 'نوع الملف غير مدعوم'})

        # قراءة النص من الصورة
        result = read_text_from_image(path, lang='ara')

        if 'error' in result:
            return jsonify({'success': False, 'message': result['error']})

        return jsonify({
            'success': True,
            'text': result['text'],
            'processed_image_path': result['processed_image_path']
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def read_text_from_image(image_path, lang='ara+en'):
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang=lang)
        #return 
        return {
            'text': text.strip(),
            'processed_image_path': image_path
        }

    except Exception as e:
        return {
            'text': '',
            'error': f"خطأ في قراءة الصورة: {str(e)}",
            'processed_image_path': image_path
        }
    #except Exception as e:
        #return f"خطأ في قراءة الصورة: {str(e)}"

# السماح بامتدادات الملفات
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
'''
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
            temp_img_path = os.path.join(SCAN_IMAGE, f"temp_page_{i}.jpg")
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
    

@blueprint.route('/read-doc', methods=['POST'])
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
            file_path = os.path.join(SCAN_IMAGE, filename)
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
'''
