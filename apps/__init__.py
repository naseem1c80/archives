# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
# __init__.py
import os
import pymysql
from flask import Flask, request, session
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_babel import Babel
from importlib import import_module
from datetime import datetime

# إعداد الاتصال بـ MySQL
pymysql.install_as_MySQLdb()

# الكائنات الأساسية
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*")
babel = Babel()

# اللغات المدعومة
LANGUAGES = {
    'en': 'English',
    'ar': 'العربية'
}

def get_locale():
    return session.get('lang') or request.accept_languages.best_match(LANGUAGES.keys())

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    
    # إعدادات إضافية لنظام الترخيص
    app.config['LICENSE_REQUIRED'] = True  # تفعيل نظام الترخيص
    app.config['VALID_LICENSES'] = []  # سيتم ملؤها من قاعدة البيانات

def register_blueprints(app):
    # تسجيل البلوبيرنتس الأساسية
    for module_name in ('authentication', 'home', 'dyn_dt', 'charts', 'users',
                      'documents', 'branchs','settings','customers','admin'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)
    
    # تسجيل بلوبيرنت نظام الترخيص
    from apps.license.routes import license_bp
    app.register_blueprint(license_bp, url_prefix='/license')
# OAuth blueprints
from apps.authentication.oauth import github_blueprint, google_blueprint
def create_app(config):
    # ... (بقية الإعدادات كما هي)
        # إعداد المسارات للقوالب والستايل
    static_prefix = '/static'
    templates_dir = os.path.dirname(config.BASE_DIR)

    TEMPLATES_FOLDER = os.path.join(templates_dir, 'templates')
    STATIC_FOLDER = os.path.join(templates_dir, 'static')

    print(' > TEMPLATES_FOLDER: ' + TEMPLATES_FOLDER)
    print(' > STATIC_FOLDER:    ' + STATIC_FOLDER)

    # إنشاء تطبيق Flask
    app = Flask(__name__, static_url_path=static_prefix,
                template_folder=TEMPLATES_FOLDER,
                static_folder=STATIC_FOLDER)
    @app.context_processor
    def inject_locale():
        """جعل الدالة get_locale متاحة في جميع القوالب"""
        def get_template_locale():
            return session.get('lang') or request.accept_languages.best_match(LANGUAGES.keys())
        return dict(get_locale=get_template_locale)
    # تحميل إعدادات المشروع
    app.config.from_object(config)

    # إعداد الترجمة
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    # تسجيل المكونات
    register_extensions(app)
    register_blueprints(app)

    # تسجيل OAuth
    app.register_blueprint(github_blueprint, url_prefix="/login")
    app.register_blueprint(google_blueprint, url_prefix="/login")
    
    # إعداد middleware للتحقق من الترخيص
    @app.before_request
    def check_license():
        if not app.config['LICENSE_REQUIRED']:
            return
            
        if request.endpoint in ['static', 'license.license_request', 
                              'license.license_pending', 
                              'license.activate_license', 'authentication.login','settings_blueprint.set_language']:
            return
            
        from apps.license.controller import check_device_license
        return check_device_license()
    
    return app
'''
import os
import pymysql
from flask import Flask, request, session
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_babel import Babel
from importlib import import_module

# إعداد الاتصال بـ MySQL
pymysql.install_as_MySQLdb()

# الكائنات الأساسية
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*")
babel = Babel()  # Babel بدون ربطه بـ app الآن

# اللغات المدعومة
LANGUAGES = {
    'en': 'English',
    'ar': 'العربية'
}

# اختيار اللغة بناءً على session أو لغة المتصفح
def get_locale():
    return session.get('lang') or request.accept_languages.best_match(LANGUAGES.keys())

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    babel.init_app(app, locale_selector=get_locale)  # التهيئة الصحيحة هنا

def register_blueprints(app):
    for module_name in ('authentication', 'home', 'dyn_dt', 'charts', 'users',
    'documents', 'branchs','settings','customers','admin'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

# OAuth blueprints
from apps.authentication.oauth import github_blueprint, google_blueprint

def create_app(config):

    # إعداد المسارات للقوالب والستايل
    static_prefix = '/static'
    templates_dir = os.path.dirname(config.BASE_DIR)

    TEMPLATES_FOLDER = os.path.join(templates_dir, 'templates')
    STATIC_FOLDER = os.path.join(templates_dir, 'static')

    print(' > TEMPLATES_FOLDER: ' + TEMPLATES_FOLDER)
    print(' > STATIC_FOLDER:    ' + STATIC_FOLDER)

    # إنشاء تطبيق Flask
    app = Flask(__name__, static_url_path=static_prefix,
                template_folder=TEMPLATES_FOLDER,
                static_folder=STATIC_FOLDER)

    # تحميل إعدادات المشروع
    app.config.from_object(config)

    # إعداد الترجمة
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    # تسجيل المكونات
    register_extensions(app)
    register_blueprints(app)

    # تسجيل OAuth
    app.register_blueprint(github_blueprint, url_prefix="/login")
    app.register_blueprint(google_blueprint, url_prefix="/login")

    return app
'''
'''
import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
import pymysql
from flask_socketio import SocketIO



pymysql.install_as_MySQLdb()
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*")
def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)

def register_blueprints(app):
    for module_name in ('authentication', 'home', 'dyn_dt', 'charts',  'users', 'documents','branchs'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

from apps.authentication.oauth import github_blueprint, google_blueprint

def create_app(config):

    # Contextual
    static_prefix = '/static'
    templates_dir = os.path.dirname(config.BASE_DIR)

    TEMPLATES_FOLDER = os.path.join(templates_dir,'templates')
    STATIC_FOLDER = os.path.join(templates_dir,'static')

    print(' > TEMPLATES_FOLDER: ' + TEMPLATES_FOLDER)
    print(' > STATIC_FOLDER:    ' + STATIC_FOLDER)

    app = Flask(__name__, static_url_path=static_prefix, template_folder=TEMPLATES_FOLDER, static_folder=STATIC_FOLDER)
    socketio.init_app(app)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    app.register_blueprint(github_blueprint, url_prefix="/login")    
    app.register_blueprint(google_blueprint, url_prefix="/login")    
    return app
'''