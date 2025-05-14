# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.users import blueprint
from flask import render_template,jsonify
from apps.models import Document
from apps.authentication.models import Users

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


