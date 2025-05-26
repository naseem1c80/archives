# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.users import blueprint

from apps import db, login_manager
from flask import render_template, redirect, request, url_for,jsonify,flash, Response
from werkzeug.security import generate_password_hash # type: ignore
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from PIL import Image, ImageDraw, ImageFont
import hashlib
import io
import base64
from apps.models import Users,Notification,Role
#import eventlet
#from apps.extensions import 
import re
from flask_login import login_required

@blueprint.route('/users')
@login_required
def users():
#  print(f"*****has_permission{current_user.has_permission('users')}")
  #if not current_user.has_permission('users'):
   # return render_template('home/page-no-permission.html'), 404
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
  return render_template('users/users.html')

@blueprint.route('/getusers')
@login_required
def getusers():
    #users = Users.query.all()
    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    search = request.args.get('search', default=None, type=str)
    sort_by = request.args.get('sort_by', default='id')
    sort_order = request.args.get('sort_order', default='asc')
    # خريطة الحقول المسموح بها للفرز
    sort_column_map = {
    'id': Users.id,
    'full_name': Users.full_name,
    'phone': Users.phone,
    'created_at': Users.created_at
    }
    # بداية الاستعلام
    query = db.session.query(Users)
    # تطبيق البحث
    if search:
       term = f"%{search}%"
       query = query.filter(
       db.or_(
            Users.full_name.ilike(term),
            Users.phone.ilike(term)
        )
        )

# تطبيق الفرز
    if sort_by in sort_column_map:
       column = sort_column_map[sort_by]
       if sort_order == 'desc':
        query = query.order_by(column.desc())
       else:
        query = query.order_by(column.asc())
    else:
       query = query.order_by(Users.id.asc())  # ترتيب افتراضي

# عدد النتائج الكلي قبل limit/offset
    total = query.count()

# تطبيق limit و offset
    users = query.offset(offset).limit(limit).all()
    response = {
            "status": "success",
            "rows": [
               user.to_dict()
             for user in users],
            "total": total
        }

    return jsonify(response)

    return jsonify([user.to_dict() for user in users])

@blueprint.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    try:
     data=request.json
     print(f'{data}')
     phone = data['phone']
     role_id=data['role']
     
     print(jsonify({'success': False, 'message':'', 'branch_id':data['branch_id'],'full_name':data['full_name'],'phone':data['phone'],'password':generate_password_hash(data['password'])}))
        #email = request.form['email']

        # Check usename exists
     user = Users.query.filter_by(phone=phone).first()
     if user:
        return jsonify({'message':'اسم المستخدم او رقم الهاتف موجود مسبقاً',
                                   'success':False})

     user = Users(branch_id=data['branch_id'],full_name=data['full_name'],phone=data['phone'],password=generate_password_hash(data['password']),role_id=role_id,job_id=1) 
        #user = Users(**request.form)
     db.session.add(user)
     db.session.commit()     #user.save()
     return  jsonify({'message':'تم انشاء الحساب بنجاح','success':True})
    except Exception as e:
     return jsonify({'success': False, 'message': str(e)})


@blueprint.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    try:
    #if current_user.role != 1:
    #    return "Access Denied", 403
     user = Users.query.get(user_id)
     data = request.json
     user.full_name = data["full_name"]
     user.branch_id = data["branch_id"]
     user.role_id = data["role"]
     db.session.commit()
     return  jsonify({'message':'تم تحديث الحساب بنجاح','success':True})
    except Exception as e:
     return jsonify({'success': False, 'message': str(e),'ss':'ssee'})

    return jsonify(success=True)




@blueprint.route('/admin/set-permissions', methods=['POST'])
@login_required
def set_permissions():
    user_id = request.form['user_id']
    selected_permissions = request.form.getlist('permissions')

    user = Users.query.get(user_id)
    if user and user.role:
        user.role.permissions = selected_permissions
        db.session.commit()
        flash("تم تحديث صلاحيات المستخدم بنجاح", "success")
    else:
        flash("حدث خطأ أثناء تحديث الصلاحيات", "danger")

    return redirect(url_for('users_blueprint.users'))


@blueprint.route("/save_permissions/<int:user_id>", methods=["POST"])
@login_required
def save_permissions(user_id):
    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'المستخدم غير موجود'}), 404

        # استرجاع الصلاحيات المحددة من النموذج
        selected_permissions = request.form.getlist('permissions')

        # تأكد من أن لدى المستخدم دور يمكننا تعديل صلاحياته
        if not user.role:
            return jsonify({'success': False, 'message': 'لا يمكن تعديل صلاحيات مستخدم بدون دور'}), 400

        # تحديث صلاحيات الدور مباشرة (يفترض أن role.permissions هو حقل JSON)
        user.role.permissions = selected_permissions
        db.session.commit()

        flash("تم تحديث صلاحيات المستخدم بنجاح", "success")
        return redirect(url_for('users_blueprint.users', user_id=user.id))

    except Exception as e:
        db.session.rollback()
        flash(f"حدث خطأ: {str(e)}", "danger")
        return redirect(url_for('users_blueprint.user_permission', user_id=user.id))



@blueprint.route('/myprofile')
@login_required
def myprofile():
    return render_template("users/myprofile.html")

@blueprint.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = Users.query.get_or_404(user_id).to_dict()
    print(f'****user**{user}')
    return render_template("users/profile.html", user=user)

@blueprint.route('/update_password', methods=['POST'])
@login_required
def update_password():
    user_id = request.form['user_id']
    new_password = request.form['new_password']
    user = Users.query.get(user_id)
    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Password updated successfully'})

@blueprint.route('/get_notifications/<int:user_id>')
def get_notifications(user_id):
    notifications = Notification.query.filter_by(user_id=user_id).all()
    data = [{'id': n.id,'message': n.message,'from_id': n.from_id,'user_id': n.user_id, 'seen': n.seen} for n in notifications]
    return jsonify({'notifications': data})




def phone_to_colors(phone_number):
    hash_object = hashlib.sha256(phone_number.encode())
    hex_dig = hash_object.hexdigest()
    colors = []
    for i in range(0, 30, 6):
        r = int(hex_dig[i:i+2], 16)
        g = int(hex_dig[i+2:i+4], 16)
        b = int(hex_dig[i+4:i+6], 16)
        colors.append((r, g, b))
    return colors

def generate_logo(username, phone_number):
    width, height = 100, 100
    # استخراج أول حرف من كل جملة
    # افترض أن الجمل تفصلها نقطة أو علامة تعجب أو استفهام متبوعة بمسافة أو نهاية السطر
    #sentences = re.split(r'[.!؟\?]\s*', username.strip())
    sentences = re.split(r' ', username.strip())
    initials = ''.join([s[0] for s in sentences if s])  # جمع أول حرف من كل جملة
    
    # توليد لون واحد من رقم الهاتف
    hash_object = hashlib.sha256(phone_number.encode())
    hex_color = hash_object.hexdigest()[:6]  # أول 6 رموز = لون RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    color = (r, g, b)

    # إنشاء صورة بلون موحد
    image = Image.new("RGB", (width, height), color)

    # يمكنك عدم كتابة الاسم إذا أردت شعارًا لونيًا فقط
    # ولكن إذا أردت، أضف النص داخل الصورة
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("fonts/Amiri-Regular.ttf", 40)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 3
    draw.text((text_x, text_y), initials, fill=(255, 255, 255), font=font)  # أول حرف من الاسم

    # تحويل الصورة إلى base64
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()



def generate_logo_from_sentences(text, phone_number, width=100, height=100):
    # استخراج أول حرف من كل جملة
    # افترض أن الجمل تفصلها نقطة أو علامة تعجب أو استفهام متبوعة بمسافة أو نهاية السطر
    sentences = re.split(r'[.!؟\?]\s*', text.strip())
    initials = ''.join([s[0] for s in sentences if s])  # جمع أول حرف من كل جملة

    # توليد لون من رقم الهاتف
    hash_object = hashlib.sha256(phone_number.encode())
    hex_color = hash_object.hexdigest()[:6]  # أول 6 أحرف = لون RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    bg_color = (r, g, b)

    # إنشاء صورة
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # تحميل خط عريض (تأكد أن الخط موجود على جهازك، أو استخدم خط آخر)
    try:
        font = ImageFont.truetype("fonts/Amiri-Bold.ttf", size=40)
    except IOError:
        font = ImageFont.load_default()

    # حساب موقع النص للتمركز في الصورة
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    # رسم النص باللون الأبيض بخط عريض
    draw.text((text_x, text_y), initials, font=font, fill=(255, 255, 255))

    # حفظ الصورة مؤقتاً في الذاكرة وتحويلها ل base64 (اختياري)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return img_str

@blueprint.route('/get_imgae_user/<int:user_id>')
def get_imgae_user(user_id):
    user = Users.query.get_or_404(user_id)
    username = user.full_name
    phone = user.phone
    image_data = generate_logo(username, phone)
    # فك base64 وإرجاع الصورة مباشرة كـ Response
    image_bytes = base64.b64decode(image_data)
    return Response(image_bytes, mimetype='image/png')
   