# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from email.policy import default
from xmlrpc.client import DateTime

from flask import current_app
from apps.exceptions.exception import InvalidUsage
import datetime as dt
from sqlalchemy.orm import relationship
from enum import Enum
import hashlib

from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
import uuid
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





class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    from_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.String(200))
    seen = db.Column(db.Boolean, default=False)
   
    user = db.relationship("Users", foreign_keys=[user_id], back_populates="notifications", lazy=True)
    from_user = db.relationship("Users", foreign_keys=[from_id], back_populates="from_notifications", lazy=True)

class DocumentType(db.Model):
    __tablename__ = 'document_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

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
    section_id= db.Column(db.Integer,  db.ForeignKey('sections.id'))
    description = db.Column(db.Text, nullable=True)
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_types.id'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=dt.datetime.utcnow())
    is_signature = db.Column(db.Boolean, default=False)
    user_signature = db.Column(db.Integer,
    db.ForeignKey('users.id'),nullable=True)
    signature = db.Column(db.Text, nullable=True)


    # Define relationships
    user = db.relationship("Users", foreign_keys=[user_id], backref="documents", lazy=True)
    verifier = db.relationship("Users", foreign_keys=[verify_user], backref="verified_documents", lazy=True)
    branch = db.relationship("Branch", backref="documents", lazy=True)
    files = db.relationship("Files", backref="documents", lazy=True)
    signer = db.relationship("Users", foreign_keys=[user_signature], backref="signed_documents", lazy=True)
    section = db.relationship('Section', backref='documents')
        # علاقة مع المستندات
    type_document = db.relationship('DocumentType', backref='documents', lazy=True)

    def __init__(self, **kwargs):
        super(Document, self).__init__(**kwargs)

    def __repr__(self):
        return f"{self.name}"

    @classmethod
    def find_by_id(cls, _id: int) -> "Document":
        return cls.query.filter_by(id=_id).first() 

    @classmethod
    def get_list(cls):
        return cls.query.all()

    def save(self) -> None:
        print(f'****self SQLAlchemyError')
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            print(f'****SQLAlchemyError {e}')
            db.session.rollback()
            db.session.close()
            error =str(e.__dict__['orig'])
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



class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)

    old_data = db.Column(db.Text, nullable=True)
    new_data = db.Column(db.Text, nullable=True)

    # بيانات الجهاز
    ip_address = db.Column(db.String(50), nullable=True)
    device_type = db.Column(db.String(100), nullable=True)  # mobile / desktop
    os = db.Column(db.String(100), nullable=True)
    browser = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("Users", backref="activity_logs")


class Users(db.Model, UserMixin):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)  # Updated field
    password= db.Column(db.String(255), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branchs.id'))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job_title.id'))
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'))
    is_admin = db.Column(db.Boolean, default=False)
    permissions = db.Column(db.JSON)
    role = db.relationship('Role', backref='users')
    brnach = db.relationship('Branch', backref='users')
    job = db.relationship('JobTitle', backref='users')
    section = db.relationship('Section', backref='users') 
    #notifications = db.relationship('Notification', backref='users')
      # Define both relationships explicitly
        # FIXED: back_populates name must match the corresponding property
    notifications = db.relationship("Notification", foreign_keys='Notification.user_id', back_populates="user", lazy=True)
    from_notifications = db.relationship("Notification", foreign_keys='Notification.from_id', back_populates="from_user", lazy=True)


    readonly_fields = ["id", "phone", "full_name", "oauth_github", "oauth_google"]
    
    
    def has_permission(self, perm):
      perms = self.permissions

      if not perms:
        return False
    
      # إذا مخزن كـ نص JSON
      if isinstance(perms, str):
          try:
              perms = json.loads(perms)
          except:
              return False
    
      return perm in perms
    def has_permission2(self, perm):
        return perm in self.permissions
    def has_perm(self, perm):
        if not self.permissions:
            return False
        perms = [p.strip() for p in self.permissions.split(",")]
        return perm in perms
        '''
            'role': {
                'id': self.role.id,
                'name': self.role.name,
                'permissions': self.role.permissions
            } if self.role else None,
        '''
    def to_dict(self):
        return {
            'id': self.id,
            #'role_id':self.role_id,
            'phone': self.phone,
            'permissions_count': len(self.permissions) if self.permissions else None,
            'full_name': self.full_name,
            'branch_id': self.branch_id,
            'section_id': self.section_id,
            'created_at': self.created_at,
            'active': self.active,
            'permissions':self.permissions,
            'branch': {
                'id': self.brnach.id,
                'name': self.brnach.name
            } if self.brnach else None,
            'section': {
                'id': self.section.id,
                'name': self.section.name
            } if self.section else None,
             'job': {
                'id': self.job.id,
                'name': self.job.name
            } if self.job else None
        }
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            #if property == 'password':
                #value = hash_pass(value)  # we need bytes here (not plain str)

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
            raise IntegrityError(e, 422)
    
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



class JobTitle(db.Model):
    __tablename__ = 'job_title'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)





class CustomerDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    issue_date = db.Column(db.Date, nullable=False,default=datetime.utcnow)
    expiry_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    place_of_issue = db.Column(db.String(255), nullable=True)
    document_type = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship('CustomerDocumentImage', backref='document', cascade="all, delete", lazy=True)
    def save(self):
        try:
            # معالجة الحقول التاريخية الفارغة
            if self.issue_date == "" or self.issue_date is None:
                self.issue_date = None
            elif isinstance(self.issue_date, str) and self.issue_date.strip():
                # تحويل النص إلى تاريخ إذا كان غير فارغ
                self.issue_date = datetime.strptime(self.issue_date, '%Y-%m-%d').date()
                
            if self.expiry_date == "" or self.expiry_date is None:
                self.expiry_date = None
            elif isinstance(self.expiry_date, str) and self.expiry_date.strip():
                self.expiry_date = datetime.strptime(self.expiry_date, '%Y-%m-%d').date()
                
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            #db.session.rollback()
            raise InvalidUsage(str(e), 500)
        
    def save2(self) -> None:
     try:
         db.session.add(self)
         db.session.commit()
     except SQLAlchemyError as e:
            print(f"err CustomerDocument {e}")
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)

class CustomerDocumentImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('customer_document.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    def save(self) -> None:
     try:
         db.session.add(self)
         db.session.commit()
     except SQLAlchemyError as e:
            print(f"err CustomerDocumentImage {e}")
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)





class Section(db.Model):
    __tablename__ = 'sections'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # للتفرقة بين الأجهزة
    created_at = db.Column(db.DateTime, 
                         default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, 
                         default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
    

class Device(db.Model):
    """
    نموذج موحد لإدارة أجهزة والتراخيص مع حل مشكلة التكرار
    """
    __tablename__ = 'devices'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    hardware_hash = db.Column(db.String(255), unique=True, nullable=False)  # للتفرقة بين الأجهزة
    
    # معلومات الجهاز
    hostname = db.Column(db.String(255))
    system = db.Column(db.String(100))
    release = db.Column(db.String(100))
    processor = db.Column(db.String(255))
    ip_address = db.Column(db.String(100))
    mac_address = db.Column(db.String(100))
    cpu_cores = db.Column(db.Integer)
    ram_gb = db.Column(db.Float)
    
    # معلومات الترخيص
    license_key = db.Column(db.String(255))
    license_hash = db.Column(db.String(255))
    is_authorized = db.Column(db.Boolean, default=False)
    license_expiry = db.Column(db.DateTime)
    
    # التواريخ
    first_seen = db.Column(db.DateTime, 
                         default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, 
                         default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, 
                         default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, 
                         default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
    licenses = db.relationship("License", back_populates="device", cascade="all, delete-orphan")
    __table_args__ = (
        db.UniqueConstraint('hardware_hash', 'license_key', name='_hw_license_uc'),
    )
    @classmethod
    def generate_hardware_id(cls):
        """إنشاء معرف فريد للجهاز بناءً على خصائصه"""
        import hashlib, platform
        h = hashlib.sha256()
        h.update(platform.node().encode())  # اسم الجهاز
        h.update(platform.processor().encode())  # المعالج
        return h.hexdigest()

    def __init__(self, **kwargs):
        # توليد الهاشات التلقائية
        if 'license_key' in kwargs:
            kwargs['license_hash'] = self._generate_hash(kwargs['license_key'])
        
        if 'hardware_info' in kwargs:
            kwargs['hardware_hash'] = self._generate_hardware_hash(kwargs.pop('hardware_info'))
        
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Device {self.device_id} ({'Authorized' if self.is_authorized else 'Pending'})>"

    # ==============
    #  الأساليب الثابتة
    # ==============
    @staticmethod
    def _generate_hash(data):
        """توليد هاش مشفر لأي بيانات"""
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def get_hardware_info():
        """جمع معلومات الجهاز الفريدة"""
        import platform, socket, subprocess, re
        
        def get_mac():
            try:
                mac = subprocess.getoutput("cat /sys/class/net/*/address | head -1")
                if not mac:
                    mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
                return mac
            except:
                return "00:00:00:00:00:00"
        
        return {
            'hostname': socket.gethostname(),
            'mac': get_mac(),
            'processor': platform.processor(),
            'machine': platform.machine()
        }

    @staticmethod
    def _generate_hardware_hash(hardware_info):
        """إنشاء هاش فريد للجهاز"""
        h = hashlib.sha256()
        for k, v in sorted(hardware_info.items()):
            h.update(f"{k}:{v}".encode())
        return h.hexdigest()

    # ==============
    #  أساليب الترخيص
    # ==============
    def verify_license(self, license_key):
        """التحقق من صحة الترخيص"""
        return self.license_hash == self._generate_hash(license_key)

    def authorize(self, valid_licenses, expiry_days=365):
        """
        تفعيل الجهاز مع التحقق من الترخيص
        """
        if self.license_key in valid_licenses:
            self.is_authorized = True
            self.license_expiry = datetime.utcnow() + timedelta(days=expiry_days)
            return True
        return False

    def check_status(self):
        """فحص حالة الترخيص الحالية"""
        if not self.is_authorized:
            return "غير مرخص"
        elif datetime.utcnow() > self.license_expiry:
            return "منتهي الصلاحية"
        return "نشط"
    




class License(db.Model):
    """
    جدول تراخيص الأجهزة مع نظام متكامل للإدارة
    """
    __tablename__ = 'licenses'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    key_hash = db.Column(db.String(128), unique=True, nullable=False)
    device_id = db.Column(db.String(36), db.ForeignKey('devices.device_id'))
    
    # معلومات الترخيص
    license_type = db.Column(db.String(20), default='STANDARD')  # STANDARD, PREMIUM, ENTERPRISE
    is_active = db.Column(db.Boolean, default=True)
    activation_count = db.Column(db.Integer, default=0)
    max_activations = db.Column(db.Integer, default=1)
    
    # فترات الصلاحية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # علاقات
    device = db.relationship('Device', back_populates='licenses')
    
    # إعدادات الجدول
    __table_args__ = (
        db.Index('ix_license_key_hash', 'key_hash'),
        db.CheckConstraint('max_activations >= 1', name='check_max_activations'),
    )

    def __init__(self, **kwargs):
        if 'key' in kwargs:
            kwargs['key_hash'] = self._generate_hash(kwargs['key'])
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f'<License {self.key[:8]}... ({self.license_type})>'
    

    # ==============
    #  الأساليب الثابتة
    # ==============
    @staticmethod
    def _generate_hash(key):
        """توليد هاش مشفر للترخيص"""
        salt = current_app.config.get('LICENSE_SALT', 'default_salt')
        return hashlib.sha512(f"{salt}{key}".encode()).hexdigest()
    
    @staticmethod
    def generate_license_key(length=16):
      """إنشاء كود ترخيص عشوائي"""
      import secrets
      import string
      chars = string.ascii_uppercase + string.digits
      return '-'.join([''.join(secrets.choice(chars) for _ in range(4)) for _ in range(4)])
    
    # ==============
    #  أساليب الترخيص
    # ==============
    def can_activate(self, device_id=None):
        """التحقق من إمكانية تفعيل الترخيص"""
        conditions = [
            self.is_active,
            self.activation_count < self.max_activations,
            (self.expires_at is None) or (datetime.utcnow() < self.expires_at),
            (device_id is None) or (self.device_id in [None, device_id])
        ]
        return all(conditions)
    
    def activate(self, device_id, days_valid=365):
        """تفعيل الترخيص على جهاز معين"""
        if not self.can_activate(device_id):
            return False
        
        self.device_id = device_id
        self.activation_count += 1
        self.activated_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=days_valid)
        
        try:
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False
    
    def revoke(self):
        """إلغاء تفعيل الترخيص"""
        self.device_id = None
        self.is_active = False
        db.session.commit()
    
    def status(self):
        """حالة الترخيص الحالية"""
        if not self.is_active:
            return "REVOKED"
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return "EXPIRED"
        if self.activation_count >= self.max_activations:
            return "MAX_USED"
        return "ACTIVE"
    
    def remaining_days(self):
        """الأيام المتبقية للانتهاء"""
        if not self.expires_at:
            return float('inf')
        return (self.expires_at - datetime.utcnow()).days