# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from email.policy import default
from apps.exceptions.exception import InvalidUsage
import datetime as dt
from sqlalchemy.orm import relationship
from enum import Enum


from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

from apps import db, login_manager
from apps.authentication.util import hash_pass

class CURRENCY_TYPE(Enum):
    usd = 'usd'
    eur = 'eur'
class Files(db.Model):

    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    doc_id = db.Column(db.Integer,db.ForeignKey('documents.id'))
    path_file = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=dt.datetime.utcnow())

    def __init__(self, **kwargs):
        super(Files, self).__init__(**kwargs)

    def __repr__(self):
        return f"{self.name} / ${self.price}"

    @classmethod
    def find_by_id(cls, _id: int) -> "Document":
        return cls.query.filter_by(id=_id).first() 

    @classmethod
    def get_list(cls):
        return cls.query.all()

    def save(self) -> None:
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)

    def delete(self) -> None:
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)
        return

class Document(db.Model):

    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=True)
    account_number = db.Column(db.String(255), nullable=True)
    transfer_number= db.Column(db.String(255), nullable=True)
    sender_name= db.Column(db.String(255), nullable=True)
    recipient_name= db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    number_doc = db.Column(db.Integer,default=0)
    status = db.Column(db.Integer,default=0)
    verify_user = db.Column(db.Integer,db.ForeignKey('users.id'))
    branch_id= db.Column(db.Integer,  db.ForeignKey('branchs.id'))
    description = db.Column(db.Text, nullable=True)
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_types.id'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=dt.datetime.utcnow())

    # Define relationships
    user = db.relationship("Users", foreign_keys=[user_id], backref="documents", lazy=True)
    verifier = db.relationship("Users", foreign_keys=[verify_user], backref="verified_documents", lazy=True)
    branch = db.relationship("Branch", backref="documents", lazy=True)
    files = db.relationship("Files", backref="documents", lazy=True)
        # علاقة مع المستندات
    type_document = db.relationship('DocumentType', backref='documents', lazy=True)

    def __init__(self, **kwargs):
        super(Document, self).__init__(**kwargs)

    def __repr__(self):
        return f"{self.name} / ${self.price}"

    @classmethod
    def find_by_id(cls, _id: int) -> "Document":
        return cls.query.filter_by(id=_id).first() 

    @classmethod
    def get_list(cls):
        return cls.query.all()

    def save(self) -> None:
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)

    def delete(self) -> None:
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)
        return
      
class Branch(db.Model):

    __tablename__ = 'branchs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    branch_number = db.Column(db.Integer, default=0)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=dt.datetime.utcnow())

    def __init__(self, **kwargs):
        super(Branch, self).__init__(**kwargs)

    def __repr__(self):
        return f"{self.name}"

    @classmethod
    def find_by_id(cls, _id: int) -> "branch":
        return cls.query.filter_by(id=_id).first() 

    @classmethod
    def get_list(cls):
        return cls.query.all()

    def save(self) -> None:
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)

    def delete(self) -> None:
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)
        return      





class Users(db.Model, UserMixin):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)  # Updated field
    password= db.Column(db.String(255), nullable=False)
    branch_id = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role', backref='users')


    readonly_fields = ["id", "phone", "full_name", "oauth_github", "oauth_google"]
    def has_permission(self, perm):
        return perm in self.role.permissions

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'full_name': self.full_name,
            'branch_id': self.branch_id,
            'created_at': self.created_at,
            'active': self.active,
            'role': {
                'id': self.role.id,
                'name': self.role.name,
                'permissions': self.role.permissions
            } if self.role else None
        }
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.phone)

    @classmethod
    def find_by_email(cls, email: str) -> "Users":
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_phone(cls, phone: str) -> "Users":
        return cls.query.filter_by(phone=phone).first()
    
    @classmethod
    def find_by_id(cls, _id: int) -> "Users":
        return cls.query.filter_by(id=_id).first()
   
    def save(self) -> None:
        try:
            db.session.add(self)
            db.session.commit()
          
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise IntegrityError(error, 422)
    
    def delete_from_db(self) -> None:
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise IntegrityError(error, 422)
        return

@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    phone = request.form.get('phone')
    user = Users.query.filter_by(phone=phone).first()
    return user if user else None

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="cascade"), nullable=False)
    user = db.relationship(Users)



class Role(db.Model):
    
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    permissions = db.Column(db.JSON)  # قائمة بالصلاحيات كـ JSON أو كـ علاقات منفصلة



class DocumentType(db.Model):
    __tablename__ = 'document_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)


   