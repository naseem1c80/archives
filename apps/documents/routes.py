# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.documents import blueprint
from flask import render_template,jsonify
from apps.models import Document
@blueprint.route('/documents')
def documents():
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('documents/documents.html')

@blueprint.route('/getdocuments')
def getdocuments():
    documents = Document.query.all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "number_doc": u.number_doc,
        "verify_user": u.verify_user,
        "created_at": u.created_at
    } for u in documents])
    #documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    #return render_template('documents/documents.html')


