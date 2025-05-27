# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.customers import blueprint
from flask import request, jsonify,render_template
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

from flask_login import current_user, login_required
from apps.models import CustomerDocument,CustomerDocumentImage

from apps import db, login_manager
from flask_cors import cross_origin

ALLOWED_EXTENSIONS = {'png', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@blueprint.route('/getcustomers', methods=['GET', 'OPTIONS'])
@cross_origin()
def getcustomers():
    try:
        # التحقق من وجود وسائط الطلب وتعيين القيم الافتراضية
        limit = min(request.args.get('limit', default=10, type=int), 100)  # حد أقصى 100 سجل
        offset = request.args.get('offset', default=0, type=int)
        status = request.args.get('status', default=None)
        document_type = request.args.get('document_type', default=None)
        sort_by = request.args.get('sort_by', default='id')
        sort_order = request.args.get('sort_order', default='asc')
        search = request.args.get('search', default=None, type=str)

        # قائمة الحقول المسموح الفرز بها (لحماية من SQL injection)
        sort_column_map = {
            'id': CustomerDocument.id
            }

        # إنشاء الاستعلام الأساسي
        query = db.session.query(CustomerDocument)
        # تطبيق البحث إذا وجد
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    CustomerDocument.name.ilike(search_term),
                    CustomerDocument.phone.ilike(search_term)
                )
            )
            
        if status is not None:
            query = query.filter(CustomerDocument.status == status)
        
        if document_type is not None:
            query = query.filter(CustomerDocument.document_type_id == document_type)
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
            query = query.order_by(CustomerDocument.id.asc())

        # تطبيق التقسيم الصفحي
        documents = query.offset(offset).limit(limit).all()

        # بناء الاستجابة
        response = {
            "status": "success",
            "rows": [{
                "id": doc.id,
                "name": doc.name,
                "phone": doc.phone,
                
            } for doc in documents],
            "limit": limit,
            "offset": offset,
            "total": total
        }

        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f"Error in getdocuments: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error {e}"}), 500
    
    
@blueprint.route('/list')
@login_required
def list():
    return render_template("card/customers.html")

@blueprint.route('/activity')
@login_required
def activity():
    return render_template("card/activity.html")


@blueprint.route('/reports')
@login_required
def reports():
    return render_template("card/reports.html")

@blueprint.route('/customers')
@login_required
def customers():
    return render_template("customers/customers.html")

@blueprint.route('/customers/add_customer')
@login_required
def add_customer():
    return render_template("card/add_customer.html")


@blueprint.route('/add_customer_doc', methods=['POST'])
def add_customer_doc():
    try:
        all_docs = []
        name =request.form.get('name')
        phone = request.form.get('phone')
        issue_date =""# request.form['issue_date']
        expiry_date =""# request.form['expiry_date']
        address =""# request.form.get('address')
        place_of_issue =""# request.form.get('place_of_issue')
        document_type = request.form.get('document_type_id')

        doc = CustomerDocument(
            name=name,
            phone=phone,
            issue_date=issue_date,
            expiry_date=expiry_date,
            address=address,
            place_of_issue=place_of_issue,
            document_type=document_type
        )
        doc.save()

        base_dir = os.path.join('static', 'uploads',"doc_customer",phone )
        os.makedirs(base_dir, exist_ok=True)
        for key in request.form:
                if key.startswith('docs[') and key.endswith('][path]'):
                    index = key.split('[')[1].split(']')[0]

                    filename = f"{uuid.uuid4().hex}.png"  # صيغة افتراضية
                    full_path = os.path.join(base_dir, filename)

                    #if source == 'scan':
                        #scan_document(full_path)
                    #elif source == 'upload':
                    #file = request.files.get(f'docs[{index}][file]')
                    file = request.form.get(f'docs[{index}][path]')
                    #if file and file.filename:
                    if allowed_file(file):
                      ext = file.rsplit('.', 1)[1].lower()
                      filename = f"{uuid.uuid4().hex}.{ext}"
                      full_path = os.path.join(base_dir, filename)
                      os.replace(file,full_path)
                      
                            #file.save(full_path)
                        #else:
                          #continue  # تجاهل الملفات غير المدعومة
                    else:
                       continue  # لا يوجد ملف مرفوع

                    all_docs.append({
                        'doc_id': doc.id,
                        'file_path': '/' + full_path.replace('\\', '/')
                    })

        if all_docs:
            res = insert_files(all_docs)
        return jsonify({'success': True, 'docs': all_docs})

        #files = request.files.getlist('images')
        


        folder_name = datetime.today().strftime('%Y/%m')
        upload_path = os.path.join('static/uploads/documents', folder_name)
        os.makedirs(upload_path, exist_ok=True)

        for file in files:
            if file.filename:
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                filepath = os.path.join(upload_path, filename)
                file.save(filepath)

                img = CustomerDocumentImage(
                    document_id=doc.id,
                    image_path=filepath.replace("\\", "/")
                )
                db.session.add(img)

        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'errorgg': str(e)})



def insert_files(docs):
    print(f"Received form data:{current_user.id if current_user.is_authenticated else 0} {docs}")
    for doc in docs:
      fi=CustomerDocumentImage(document_id=doc["doc_id"],
        image_path=doc["file_path"])
      # حفظ التغييرات وإغلاق الاتصال
      fi.save()
    return jsonify({'docs':'add all document'})


@blueprint.route('/api/customer-documents')
def get_documents():
    docs = CustomerDocument.query.order_by(CustomerDocument.id.desc()).all()
    return jsonify([
        {
            "id": d.id,
            "name": d.name,
            "phone": d.phone,
            "issue_date": d.issue_date.strftime("%Y-%m-%d"),
            "expiry_date": d.expiry_date.strftime("%Y-%m-%d"),
            "document_type": d.document_type
        } for d in docs
    ])


@blueprint.route('/add_customerdocument')
def add_customerdocument():
    return render_template("customers/add_customer_document.html")


@blueprint.route('/api/customer-documents/<int:doc_id>')
def get_document_detail(doc_id):
    doc = CustomerDocument.query.get_or_404(doc_id)
    return jsonify({
        "id": doc.id,
        "name": doc.name,
        "phone": doc.phone,
        "issue_date": doc.issue_date.strftime("%Y-%m-%d"),
        "expiry_date": doc.expiry_date.strftime("%Y-%m-%d"),
        "document_type": doc.document_type,
        "address": doc.address,
        "place_of_issue": doc.place_of_issue,
        "images": [{"image_path": img.image_path} for img in doc.images]
    })
