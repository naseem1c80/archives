# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.users import blueprint

from apps import db, login_manager
from flask import render_template, redirect, request, url_for,jsonify,flash
from werkzeug.security import generate_password_hash # type: ignore
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from apps.models import Users

@blueprint.route('/users')
def users():
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('users/users.html')

@blueprint.route('/getusers')
def getusers():
    users = Users.query.all()
    return jsonify([user.to_dict() for user in users])
    return jsonify([{
        "id": u.id,
        "full_name": u.full_name,
        "phone": u.phone,
        "role": u.role,
        "active": u.active
    } for u in users])
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    #return render_template('users/users.html')

@blueprint.route('/add_user', methods=['GET', 'POST'])
def add_user():
    try:
     data=request.json
     phone = data['phone']
     print(data)
        #email = request.form['email']

        # Check usename exists
     user = Users.query.filter_by(phone=phone).first()
     if user:
        return jsonify({'message':'اسم المستخدم او رقم الهاتف موجود مسبقاً',
                                   'success':False})

     user = Users(branch_id=data['branch_id'],full_name=data['full_name'],phone=data['phone'],password=generate_password_hash(data['password'])) 
        #user = Users(**request.form)
     db.session.add(user)
     db.session.commit()     #user.save()
     return  jsonify({'message':'تم انشاء الحساب بنجاح','success':True})
    except Exception as e:
     return jsonify({'success': False, 'message': str(e)})


@blueprint.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
    #if current_user.role != 1:
    #    return "Access Denied", 403
     user = Users.query.get(user_id)
     data = request.json
     user.full_name = data["full_name"]
     user.branch_id = data["branch_id"]
     user.role = data["role"]
     db.session.commit()
     return  jsonify({'message':'تم تحديث الحساب بنجاح','success':True})
    except Exception as e:
     return jsonify({'success': False, 'message': str(e)})

    return jsonify(success=True)



@blueprint.route("/user_permission/<int:user_id>", methods=["GET"])
def user_permission(user_id):
    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'المستخدم غير موجود'}), 404

        return render_template('permissions/permission.html', user=user)
    except Exception as e:
     return jsonify({'success': False, 'message': str(e)})

    return jsonify(success=True)


@blueprint.route('/admin/set-permissions', methods=['POST'])
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
