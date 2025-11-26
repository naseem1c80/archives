# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.documents import blueprint

from apps.models import Document,Files,Branch,Users,DocumentType,Notification
from apps.documents.insert import addDocument
from PIL import Image
import pytesseract
#from scanner import scan_document
import mysql.connector
import os
import uuid

from apps import db, login_manager
from flask_cors import cross_origin
import PyPDF2
from pdf2image import convert_from_bytes
from flask import render_template, request, redirect, url_for, flash, jsonify, session,send_from_directory
from flask_login import  current_user
from flask_login import login_required

from datetime import datetime
from flask import current_app
from apps.inc.Convert import convert_pdf_to_images
from werkzeug.utils import secure_filename
from sqlalchemy import func
from apps.inc.scanner import scan_document
import base64

SCAN_IMAGE = 'static/scan_image'
if os.name == 'nt':  # 'nt' يعني Windows
    #SCAN_IMAGE='E:\scan_image' # استخدم r لجعل السلسلة raw لتجنب مشاكل الـ backslash
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#else:
    #pytesseract.pytesseract.tesseract_cmd='/Tesseract-OCR/ara.traineddata'


UPLOAD_FOLDER = 'static/uploads_cropped'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@blueprint.route('/save-cropped', methods=['POST'])
def save_cropped():
    image = request.files.get('cropped_image')
    if image:
        filename = f"cropped_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(path)
                # قراءة النص من الصورة
        result = read_text_from_image(path, lang='ara+en')

        if 'error' in result:
            return jsonify({'success': False, 'message': result['error']})

        return jsonify({
            'success': True,
            'text': result['text'],
            'url': result['processed_image_path']
        })
        return jsonify({'success': True, 'url': f"{path}"})
    return jsonify({'success': False, 'error': 'No image received'})

@blueprint.route('/documents')
@login_required
def documents():
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('documents/documents.html')


@blueprint.route('/create_document')
@login_required
def create_document():
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('documents/create_document.html')

@blueprint.route('/document/<int:doc_id>')
def document_profile(doc_id):
    document = Document.query.get_or_404(doc_id)
    return render_template('documents/document_profile.html', document=document)

@blueprint.route('/verify-document/<int:doc_id>', methods=['POST'])
@login_required
def verify_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    document.status = 1  # تم التوثيق
    document.verify_user = current_user.id
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'تم التوثيق'})



@blueprint.route('/getdocuments', methods=['GET', 'OPTIONS'])
@cross_origin()
def getdocuments():
    try:
        # التحقق من وجود وسائط الطلب وتعيين القيم الافتراضية
        limit = min(request.args.get('limit', default=10, type=int), 100)  # حد أقصى 100 سجل
        offset = request.args.get('offset', default=0, type=int)
        status = request.args.get('status', default=None)
        document_type = request.args.get('document_type', default=None)
        is_signature= request.args.get('is_signature', default=None)
        sort_by = request.args.get('sort', default='id')
        sort_order = request.args.get('order', default='asc')
        search = request.args.get('search', default=None, type=str)

        # قائمة الحقول المسموح الفرز بها (لحماية من SQL injection)
        sort_column_map = {
            'id': Document.id,
            'name': Document.name,
            'number_doc': Document.number_doc,
            'user_name': Users.full_name,
            'branch_name': Branch.name,
            'created_at': Document.created_at
        }

        # إنشاء الاستعلام الأساسي
        query = db.session.query(Document).\
            outerjoin(Users, Document.user_id == Users.id).\
            outerjoin(Files, Document.id == Files.doc_id).\
            outerjoin(Branch, Document.branch_id == Branch.id)

        # تطبيق البحث إذا وجد
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                  Files.description.ilike(search_term),
                    Document.name.ilike(search_term),
                    Document.number_doc.ilike(search_term),
                    Users.full_name.ilike(search_term),
                    Branch.name.ilike(search_term)
                )
            )
            
        if status is not None:
            query = query.filter(Document.status == status)
        
        if document_type is not None:
            query = query.filter(Document.document_type_id == document_type)
        if is_signature is not None:
             print(f"is_signature {is_signature} {bool(is_signature)}")
             if is_signature == 'false':
                 query = query.filter(Document.is_signature==False)
             else:
                 query = query.filter(Document.is_signature==True)

        # الحصول على العدد الكلي قبل التقسيم
        total = query.count()

        # تطبيق الفرز
        if sort_by in sort_column_map:
            column = sort_column_map[sort_by]
            if sort_order.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            # الترتيب الافتراضي إذا كان حقل الفرز غير صحيح
            query = query.order_by(Document.id.asc())

        # تطبيق التقسيم الصفحي
        print(f'*****sql{query}*****')
        documents = query.offset(offset).limit(limit).all()

        # بناء الاستجابة
        response = {
            "status": "success",
            "rows": [{
                "id": doc.id,
                "name": doc.name,
                "number_doc": doc.number_doc,
                "account_number": doc.account_number,
                "type_document": doc.type_document.name if doc.type_document else None,
                "transfer_number": doc.transfer_number,
                "document_type_id": doc.document_type_id,
                "is_signature": doc.is_signature,
                "signer":doc.signer.full_name if doc.signer else None,
                "signature": doc.signature,
                "user_id": doc.user_id,
                "user_name": doc.user.full_name if doc.user else None,
                "branch_id": doc.branch_id,
                "branch_name": doc.branch.name if doc.branch else None,
                "verify_user": doc.verify_user,
                "status": doc.status,
                "created_at": doc.created_at.strftime('%Y-%m-%d %H:%M')  if doc.created_at else None
            } for doc in documents],
            "limit": limit,
            "offset": offset,
            "total": total
        }

        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f"Error in getdocuments: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error {e}"}), 500
    
    

@blueprint.route('/update-document-status/<int:doc_id>', methods=['POST'])
def update_document_status(doc_id):
    data = request.get_json()
    status = int(data.get('status'))
    reason = data.get('reason', '')

    document = Document.query.get_or_404(doc_id)
    document.status = status
    if status == 2:
      # إرسال إشعار إلى المستخدم
      notify_user(current_user.id,document.user_id, reason,doc_id)

    db.session.commit()

    return jsonify({'status': 'success', 'message': 'تم تحديث الحالة بنجاح'})

def notify_user(from_user,user_id, message,doc_id=0):
    notification = Notification(from_id=from_user,user_id=user_id,
    message=message,seen=False)
    db.session.add(notification)
    db.session.commit()


@blueprint.route('/sign-document/<int:doc_id>', methods=['POST'])
def sign_document(doc_id):
    document = Document.query.get_or_404(doc_id)

    if not document.is_signature:
        return jsonify({'status': 'error', 'message': 'التوقيع غير مفعل لهذا المستند'}), 400

    # مثال: استلام توقيع كصورة Base64 من الواجهة
    signature_data = request.json.get('signature')  # توقيع مرسل من Canvas مثلاً

    if not signature_data:
        return jsonify({'status': 'error', 'message': 'لا يوجد توقيع مرسل'}), 400

    try:
        # استخراج بيانات الصورة
        header, encoded = signature_data.split(",", 1)
        data = base64.b64decode(encoded)

        # تحديد المسار الذي سيتم حفظ الصورة فيه
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'signature_{doc_id}_{timestamp}.png'
        signature_folder = os.path.join( 'static', 'signatures')
        os.makedirs(signature_folder, exist_ok=True)
        filepath = os.path.join(signature_folder, filename)

        with open(filepath, 'wb') as f:
            f.write(data)

        # تحديث حقل التوقيع في قاعدة البيانات
        document.signature = f'/static/signatures/{filename}'
        document.user_signature = current_user.id  # أو رقم المستخدم الحالي
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'تم التوقيع وحفظ التوقيع بنجاح'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@blueprint.route('/scan', methods=['POST','GET'])
def scan():
    name =""# request.form.get('name', '')
    doc_id =""# request.form.get('doc_id', '')
    image_path="static/scan_image/20294e63-d2ce-42bf-9f7a-b2fd9277c66c.png";
    try:
        
        image_path = scan_document()
        return jsonify({
            'success': True,
            'image_url':  image_path,
            'name': name,
            'doc_id': doc_id
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'image_url':f'{e}'  ,
            'name': name,
            'doc_id': doc_id
        })
        return jsonify({'success': False, 'error': str(e)})

@blueprint.route('/read-doc', methods=['POST'])
def read_doc():
  
    if  request.form.get('path'):
      result = read_text_from_image(request.form.get('path'), lang='ara+en')
      return jsonify({
            'success': True,
            'text': result['text'],
            'processed_image_path': result['processed_image_path']
        })
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم إرسال الملف'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'اسم الملف غير موجود'})

    ext = os.path.splitext(file.filename)[1].lower()

    try:
        if ext == '.pdf':
            # تحويل أول صفحة من PDF إلى صورة
            if os.name == 'nt': 
             images = convert_from_bytes(file.read(), dpi=200, fmt='png',poppler_path=r'C:\poppler\Library\bin' )
            else:
               images = convert_from_bytes(file.read(), dpi=200,
              fmt='png')
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
        result = read_text_from_image(path, lang='ara+en')

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


ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/save-docs', methods=['POST'])
def save_docs():
  res=addDocument()
  return res


@blueprint.route("/report/documents", methods=["GET"])
def get_documents_report():
    try:
        counts = (
            db.session.query(Document.status, func.count(Document.id))
            .filter(Document.status.in_([0, 1, 2]))
            .group_by(Document.status)
            .all()
        )
        #all=db.session.query(Document.status, func.count(Document.id)).all()
        # إجمالي كل المستندات (بغض النظر عن الحالة)
        total_documents = db.session.query(func.count(Document.id)).scalar()
        # تحويل النتائج إلى dict
        result = {0: 0, 1: 0, 2: 0}  # تأكد من ظهور كلا الحالتين حتى لو إحداهما صفر
        for status, count in counts:
            result[status] = count

        return jsonify({
            'success': True,
            'status_all_count': total_documents,
            'status_0_count': result[0],
            'status_1_count': result[1],
            'status_2_count': result[2]
           
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    





#from flask import Blueprint, render_template, request, jsonify
#from .models import db, 

#blueprint = Blueprint("document_types", __name__)

@blueprint.route("/getdocument_types", methods=["GET"])
def getdocument_types():
  types = DocumentType.query.all()
  response = []
  for doc in types:
    response.append({
          "id": doc.id,
          "name": doc.name})
  return response          
  
@blueprint.route("/document_types", methods=["GET"])
def view_document_types():
    return render_template("document_types/document_types.html")

@blueprint.route("/document_types/add", methods=["POST"])
def add_document_type():
    try:
        data = request.json
        name =data['name']# request.form.get("name")
        if not name:
            return jsonify(success=False, message="الاسم مطلوب")
        new_type = DocumentType(name=name)
        db.session.add(new_type)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@blueprint.route("/document_types/update/<int:type_id>", methods=["POST"])
def update_document_type(type_id):
    try:
        data = request.json
        name =data['name']# request.form.get("name")
        doc_type = DocumentType.query.get(type_id)
        if not doc_type:
            return jsonify(success=False, message="النوع غير موجود")
        doc_type.name = name
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))
