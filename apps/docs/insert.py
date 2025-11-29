from apps.models import Document,Files,Branch,Users,DocumentType
import pytesseract
#from scanner import scan_document
import os
import uuid

from apps import db, login_manager
import PyPDF2
from flask import request,jsonify
from flask_login import  current_user


from datetime import datetime
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def addDocument():
    try:
        all_docs = []
        inserted_id = 0
        ressave = save_document()

        if ressave['success']:
            inserted_id = int(ressave['document_id'])

            now = datetime.now()
            year = now.strftime('%Y')
            month = now.strftime('%m')
            day = now.strftime('%d')

            branch_id = request.form.get('branch_id') or str(getattr(current_user, 'branch_id', 'unknown'))

            base_dir = os.path.join('static', 'uploads', year, month, day,branch_id)
            os.makedirs(base_dir, exist_ok=True)

            for key in request.form:
                if key.startswith('docs[') and key.endswith('][details]'):
                    index = key.split('[')[1].split(']')[0]
                    source = request.form.get(f'docs[{index}][source]')
                    details = request.form.get(f'docs[{index}][details]')

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
        # نحصل على القيمة، إذا كانت موجودة اعتبرها True، غير ذلك Fals
        
        is_signature=False
        user_signature=None
        print(f"Received form data:is_signature {is_signature}{request.form}")
        
        
        if not request.form.get('is_signature'):
         is_signature=False
         user_signature=None
        else:
          is_signature = bool(request.form.get('is_signature'))
          user_signature=request.form.get('user_signature')
          

        
          
        


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
            description=request.form.get('description', ''),
            document_type_id=request.form.get('document_type_id', '1'),
            user_signature=user_signature,
            is_signature=is_signature
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

'''
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