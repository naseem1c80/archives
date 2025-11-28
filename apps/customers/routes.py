# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.customers import blueprint
from apps.admin.routes import log_action
from flask import request, jsonify,render_template
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

from flask_login import current_user, login_required
from apps.models import CustomerDocument,CustomerDocumentImage

from apps import db, login_manager
from flask_cors import cross_origin
import base64
import traceback
ALLOWED_EXTENSIONS = {'png', 'pdf'}

def allowed_file2(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file(filename):
    """التحقق من نوع الملف المسموح به"""
    if not filename:
        return False
    allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

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

@blueprint.route('/customer/<int:doc_id>')
def customer_profile(doc_id):
    log_action(current_user.id, "customer_profile", "customer_document", doc_id)
    document = CustomerDocument.query.get_or_404(doc_id)
    return render_template('customers/customer_profile.html', document=document)

@blueprint.route('/add_customer_doc', methods=['POST'])
def add_customer_doc():
    try:
        print("=== بيانات الطلب المستلمة ===")
        print("Form data:", dict(request.form))
        print("Files:", dict(request.files))
        
        all_docs = []
        
        # جلب البيانات من النموذج
        name = request.form.get('name')
        phone = request.form.get('phone')
        document_type = request.form.get('document_type_id')
        
        print(f"البيانات الأساسية - الاسم: {name}, الهاتف: {phone}, النوع: {document_type}")

        # التحقق من الحقول المطلوبة
        if not name or not phone or not document_type:
            return jsonify({
                'success': False, 
                'error': 'جميع الحقول (الاسم، الهاتف، نوع الوثيقة) مطلوبة'
            })

        # إنشاء المستند في قاعدة البيانات
        doc = CustomerDocument(
            name=name,
            phone=phone,
            issue_date=request.form.get('issue_date', '2025-11-22'),
            expiry_date=request.form.get('expiry_date', '2025-11-22'),
            address=request.form.get('address', ''),
            place_of_issue=request.form.get('place_of_issue', ''),
            document_type=document_type
        )
        doc.save()
        log_action(current_user.id, "add_customer_doc", "customer_document", doc.id)
        print(f"تم إنشاء المستند برقم: {doc.id}")

        # إنشاء المجلد
        base_dir = os.path.join('static', 'uploads', 'doc_customer', phone)
        os.makedirs(base_dir, exist_ok=True)
        print(f"المجلد المستهدف: {base_dir}")

        # معالجة الملفات المرفوعة
        files_processed = 0
        
        # البحث عن جميع حقول الملفات في النموذج
        for key in request.files:
            if key.startswith('docs[') and 'path' in key:
                file = request.files[key]
                if file and file.filename:
                    try:
                        # توليد اسم فريد للملف
                        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                        filename = f"{uuid.uuid4().hex}.{ext}"
                        full_path = os.path.join(base_dir, filename)
                        
                        # حفظ الملف
                        file.save(full_path)
                        files_processed += 1
                        
                        all_docs.append({
                            'doc_id': doc.id,
                            'file_path': '/' + full_path.replace('\\', '/')
                        })
                        print(f"تم حفظ الملف: {filename}")
                        
                    except Exception as file_error:
                        print(f"خطأ في حفظ الملف {key}: {file_error}")
                        continue

        # معالجة الملفات من المسارات (إذا كانت موجودة)
        for key in request.form:
            if key.startswith('docs[') and key.endswith('][path]') and request.form[key]:
                file_path = request.form[key]
                if file_path and not file_path.startswith('data:'):  # تجاهل بيانات base64
                    try:
                        if os.path.exists(file_path):
                            # نسخ الملف من المسار المؤقت
                            ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else 'png'
                            filename = f"{uuid.uuid4().hex}.{ext}"
                            full_path = os.path.join(base_dir, filename)
                            
                            import shutil
                            shutil.copy2(file_path, full_path)
                            files_processed += 1
                            
                            all_docs.append({
                                'doc_id': doc.id,
                                'file_path': '/' + full_path.replace('\\', '/')
                            })
                            print(f"تم نسخ الملف من: {file_path} إلى: {full_path}")
                            
                    except Exception as path_error:
                        print(f"خطأ في معالجة مسار الملف {key}: {path_error}")
                        continue

        print(f"تم معالجة {files_processed} ملف بنجاح")

        # حفظ المعلومات في قاعدة البيانات
        if all_docs:
            try:
                res = insert_files(all_docs)
                print(f"تم إدراج {len(all_docs)} ملف في قاعدة البيانات")
            except Exception as db_error:
                print(f"خطأ في قاعدة البيانات: {db_error}")
                return jsonify({
                    'success': False, 
                    'error': f'خطأ في حفظ الملفات في قاعدة البيانات: {str(db_error)}'
                })

        return jsonify({
            'success': True, 
            'message': f'تم إضافة {len(all_docs)} ملف بنجاح',
            'doc_id': doc.id,
            'docs_count': len(all_docs)
        })

    except Exception as e:
        print(f"خطأ عام: {str(e)}")
        import traceback
        print(f"تفاصيل الخطأ: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'{str(e)}'})

@blueprint.route('/add_customer_doc2', methods=['POST'])
def add_customer_doc2():
    try:
        all_docs = []
        name = request.form.get('name')
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
        return jsonify({'success': False, 'errorgg':f'{str(e)}'})



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
