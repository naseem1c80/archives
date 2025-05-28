# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.branchs import blueprint
from flask import render_template, redirect, request, url_for,jsonify
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from apps.models import Branch

@blueprint.route('/branchs')
def branchs():
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('branchs/branchs.html')

@blueprint.route('/getbranchs')
def getbranchs():
    branchs = Branch.query.all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "branch_number": u.branch_number,
        "phone": u.phone,
        "address": u.address,
        "created_at":u.created_at.strftime('%Y-%m-%d %H:%M')  if u.created_at else None
    } for u in branchs])
 
 
@blueprint.route("/add_branch", methods=["POST"])
def add_branch():
    #if current_user.role != 1:
        #return "Access Denied", 403
    print(f'{request}')
    data = request.json
    
    branch = Branch(name=data["name"], phone=data["phone"], branch_number=data['branch_number'], address=data["address"])
    branch.save()
    #db.session.commit()
    return jsonify(success=True)

@blueprint.route("/update_branch/<int:branch_id>", methods=["PUT"])
def update_branch(branch_id):
    #if current_user.role != 1:
        #return "Access Denied", 403
    branch = Branch.query.get(branch_id)
    data = request.json
    branch.name = data["name"]
    branch.branch_number = data["branch_number"]
    branch.phone = data["phone"]
    branch.address = data["address"]
    branch.save()
    return jsonify(success=True)

 
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    #return render_template('branchs/branchs.html')


