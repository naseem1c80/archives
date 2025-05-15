# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from email.policy import default
from apps import db
from sqlalchemy.exc import SQLAlchemyError
from apps.exceptions.exception import InvalidUsage
import datetime as dt
from sqlalchemy.orm import relationship
from enum import Enum

class CURRENCY_TYPE(Enum):
    usd = 'usd'
    eur = 'eur'
class Files(db.Model):

    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    doc_id = db.Column(db.Integer, default=0)
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
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, default=0)
    number_doc = db.Column(db.Integer,default=0)
    verify_user = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=dt.datetime.utcnow())
    '''
    id            = db.Column(db.Integer,      primary_key=True)
    name          = db.Column(db.String(128),  nullable=False)
    info          = db.Column(db.Text,         nullable=True)
    price         = db.Column(db.Integer,      nullable=False)
    currency      = db.Column(db.Enum(CURRENCY_TYPE), default=CURRENCY_TYPE.usd, nullable=False)

    date_created  = db.Column(db.DateTime,     default=dt.datetime.utcnow())
    date_modified = db.Column(db.DateTime,     default=db.func.current_timestamp(),
                                               onupdate=db.func.current_timestamp())
    '''
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