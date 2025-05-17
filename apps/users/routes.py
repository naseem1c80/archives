# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.users import blueprint

from apps import db, login_manager
from flask import render_template, redirect, request, url_for,jsonify
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
