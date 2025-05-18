# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.documents import blueprint

from apps.models import Document,Files,Branch,Users,DocumentType
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
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SCAN_IMAGE='E:\scan_image'
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
@blueprint.route('/getdocuments', methods=['GET', 'OPTIONS'])
@cross_origin()
def getdocuments():
    try:
        # Get query parameters
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)
        search = request.args.get('search', type=str)

        # Base query with LEFT JOINs
        query = db.session.query(Document).\
            outerjoin(Users, Document.user_id == Users.id).\
            outerjoin(Files, Document.id == Files.doc_id).\
            outerjoin(Branch, Document.branch_id == Branch.id)

        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Document.name.ilike(search_term),
                    Document.number_doc.ilike(search_term),
                    Users.name.ilike(search_term),
                    Files.description.ilike(search_term),
                    Branch.name.ilike(search_term)
                )
            )

        # Apply limit and offset
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        documents = query.all()

        # Build response
        response = []
        for doc in documents:
            response.append({
                "id": doc.id,
                "name": doc.name,
                "number_doc": doc.number_doc,
                "account_number":doc.account_number,
                "transfer_number":doc.transfer_number,
                "sender_name":doc.sender_name,
                "recipient_name":doc.recipient_name,
                "user_id": doc.user_id,
                "user_name": doc.user.full_name if doc.user else None,
                "branch_id": doc.branch_id,
                "branch_name": doc.branch.name if doc.branch else None,
                "verify_user": doc.verify_user,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "files": [file.description for file in doc.files] if hasattr(doc, 'files') else []
            })

        return jsonify({"status": "success", "data": response})

    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500


@blueprint.route('/scan', methods=['POST','GET'])
def scan():
    try:
        name =""# request.form.get('name', '')
        doc_id =""# request.form.get('doc_id', '')
        image_path = scan_document()
        return jsonify({
            'success': True,
            'image_url':  image_path,
            'name': name,
            'doc_id': doc_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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







@blueprint.route('/save-docs', methods=['POST'])
def save_docs():
    try:
        all_docs = []
        inserted_id = 0
        ressave = save_document()

        if ressave['success']:
            inserted_id = int(ressave['document_id'])

            # استخراج التاريخ
            now = datetime.now()
            year = now.strftime('%Y')
            month = now.strftime('%m')

            # استخراج branch_id من form أو من المستخدم الحالي
            branch_id = request.form.get('branch_id') or str(getattr(current_user, 'branch_id', 'unknown'))

            # مسار التخزين الأساسي
            base_dir = os.path.join('static', 'uploads', year, month, branch_id)
            os.makedirs(base_dir, exist_ok=True)

            for key in request.form:
                if key.startswith('docs[') and key.endswith('][source]'):
                    index = key.split('[')[1].split(']')[0]
                    source = request.form.get(f'docs[{index}][source]')
                    details = request.form.get(f'docs[{index}][details]')

                    filename = f"{uuid.uuid4().hex}.png"
                    full_path = os.path.join(base_dir, filename)

                    if source == 'scan':
                        scan_document(full_path)
                    elif source == 'upload':
                        file = request.files.get(f'docs[{index}][file]')
                        if file and file.filename:
                            file.save(full_path)
                        else:
                            continue  # تخطي إذا لم يتم رفع الملف

                    all_docs.append({
                        'doc_id': inserted_id,
                        'file_path': '/' + full_path.replace('\\', '/'),
                        'details': details
                    })

            if all_docs:
                res = insert_files(all_docs)
            return jsonify({'success': True, 'docs': all_docs})

        else:
            return ressave
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

'''
@blueprint.route('/save-docs', methods=['POST'])
def save_docs():
    try:
        all_docs = []
        inserted_id=0
        ressave =save_document()
        #print(f'ressave{ressave.success}')
        if ressave['success']:
          inserted_id=int(ressave['document_id'])
          for key in request.form:
            if key.startswith('docs[') and key.endswith('][source]'):
                index = key.split('[')[1].split(']')[0]
                doc_id = request.form.get(f'docs[{index}][id]')
                source = request.form.get(f'docs[{index}][source]')
                details = request.form.get(f'docs[{index}][details]')

                filename = f"ah{uuid.uuid4()}.png"
                full_path = os.path.join('static/uploads', filename)
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
        else:
          return ressave
    except Exception as e:
        return jsonify({'success': False, 'errory': str(e)})
'''
def insert_files(docs):
    print(f"Received form data:{current_user.id if current_user.is_authenticated else 0} {docs}")
    for doc in docs:
      fi=Files(name="new",doc_id=doc["doc_id"],description=doc["details"],
        path_file=doc["file_path"])
      # حفظ التغييرات وإغلاق الاتصال
      fi.save()
    return jsonify({'docs':'add all document'})





def save_document():
    #print(request.form.to_dict())
    try:
        # طباعة الطلب للتصحيح
        print(f"Received form data:{current_user.branch_id} {current_user.id if current_user.is_authenticated else 0} {request.form}")


        # إنشاء المستند
        doc = Document(
            name=request.form.get('name', 'مستند بدون اسم'),
            recipient_name=request.form.get('recipient_name'),
            transfer_number=request.form.get('transfer_number'),
            sender_name=request.form.get('sender_name'),
            number_doc=request.form.get('number_doc'),
            account_number=request.form.get('account_number', '000'),
            user_id=current_user.id if current_user.is_authenticated else 0,
            branch_id=current_user.branch_id if current_user.is_authenticated else 0,
            verify_user=0,
            description=request.form.get('description', '')
        )

        # الحفظ
        doc.save()

        return {
            "success": True,
            "message": "تم حفظ المستند بنجاح",
            "document_id": doc.id
        }

    except Exception as e:
        return {
            "success": False,
            "message": "حدث خطأ أثناء الحفظ",
            "error": str(e)
        }


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

@blueprint.route("/document_types", methods=["GET"])
def view_document_types():
    types = DocumentType.query.all()
    return render_template("document_types/document_types.html", types=types)

@blueprint.route("/document_types/add", methods=["POST"])
def add_document_type():
    try:
        name = request.form.get("name")
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
        name = request.form.get("name")
        doc_type = DocumentType.query.get(type_id)
        if not doc_type:
            return jsonify(success=False, message="النوع غير موجود")
        doc_type.name = name
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))
