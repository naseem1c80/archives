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

from flask_login import login_required
from apps.models import CustomerDocument,CustomerDocumentImage


ALLOWED_EXTENSIONS = {'png', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@blueprint.route('/customers')
@login_required
def customers():
    return render_template("customers/customers.html")


@blueprint.route('/add_customer_doc', methods=['POST'])
def add_customer_doc():
    try:
        name = request.form['name']
        phone = request.form['phone']
        issue_date = request.form['issue_date']
        expiry_date = request.form['expiry_date']
        address = request.form.get('address')
        place_of_issue = request.form.get('place_of_issue')
        document_type = request.form['document_type']

        doc = CustomerDocument(
            name=name,
            phone=phone,
            issue_date=issue_date,
            expiry_date=expiry_date,
            address=address,
            place_of_issue=place_of_issue,
            document_type=document_type
        )
        db.session.add(doc)
        db.session.commit()

        files = request.files.getlist('images')
        


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
        return jsonify({'success': False, 'error': str(e)})


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
