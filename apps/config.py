# -*- encoding: utf-8 -*-
"""
حقوق النشر (c) 2019 - حتى الآن AppSeed.us
"""

# استيراد المكتبات المطلوبة
import os
from pathlib import Path  # لإدارة المسارات بطريقة أكثر مرونة

# تعريف الكلاس الأساسي للإعدادات العامة
class Config(object):
  try:
    # تحديد مسار المجلد الأساسي للتطبيق
    BASE_DIR = Path(__file__).resolve().parent

    # تعريف أدوار المستخدمين كنظام ترميز رقمي
    USERS_ROLES  = { 'ADMIN'  : 1, 'USER'      : 2 }
    # تعريف حالات المستخدمين
    USERS_STATUS = { 'ACTIVE' : 1, 'SUSPENDED' : 2 }
    
    # إعدادات Celery (للمهام الخلفية Asynchronous Tasks)
    CELERY_BROKER_URL     = "redis://localhost:6379"   # موقع Redis Broker
    CELERY_RESULT_BACKEND = "redis://localhost:6379"   # موقع Redis لحفظ النتائج
    CELERY_HOSTMACHINE    = "celery@app-generator"     # اسم مضيف Celery

    # تعيين مفتاح سري للتطبيق (لأمان الجلسات والتوقيعات)
    SECRET_KEY  = os.getenv('SECRET_KEY', 'S3cret_999')

    # تمكين/تعطيل تسجيل الدخول باستخدام GitHub
    SOCIAL_AUTH_GITHUB  = False
    GITHUB_ID      = os.getenv('GITHUB_ID', None)
    GITHUB_SECRET  = os.getenv('GITHUB_SECRET', None)

    # إذا تم توفير بيانات GitHub، فعّل تسجيل الدخول به
    if GITHUB_ID and GITHUB_SECRET:
        SOCIAL_AUTH_GITHUB = True    

    # إعدادات تسجيل الدخول باستخدام Google
    GOOGLE_ID      = os.getenv('GOOGLE_ID', None)
    GOOGLE_SECRET  = os.getenv('GOOGLE_SECRET', None)

    # إذا تم توفير بيانات Google، فعّل تسجيل الدخول به
    if GOOGLE_ID and GOOGLE_SECRET:
        SOCIAL_AUTH_GOOGLE = True    

    # تعطيل ميزة تتبع التعديلات في SQLAlchemy لتقليل الاستهلاك
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # إعدادات الاتصال بقاعدة البيانات من متغيرات البيئة
    DB_ENGINE   = os.getenv('DB_ENGINE', None)
    DB_USERNAME = os.getenv('DB_USERNAME', None)
    DB_PASS     = os.getenv('DB_PASS', None)
    DB_HOST     = os.getenv('DB_HOST', None)
    DB_PORT     = os.getenv('DB_PORT', None)
    DB_NAME     = os.getenv('DB_NAME', None)

    # افتراض استخدام SQLite كخيار افتراضي
    USE_SQLITE = True 

    # محاولة استخدام قاعدة بيانات علائقية إذا كانت بيانات الاتصال مكتملة
    if DB_ENGINE and DB_NAME and DB_USERNAME:
        try:
            # تكوين URI لقاعدة البيانات العلائقية مثل MySQL أو PostgreSQL
            #SQLALCHEMY_DATABASE_URI =f'mysql+pymysql://{DB_USERNAME}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
            
            SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
                DB_ENGINE,
                DB_USERNAME,
                DB_PASS,
                DB_HOST,
                DB_PORT,
                DB_NAME
            )
            
            USE_SQLITE = False  # تم التحقق من توفر قاعدة علائقية

        except Exception as e:
            # في حالة حدوث خطأ أثناء تكوين قاعدة البيانات
            print('> Error: DBMS Exception: ' + str(e))
            print('> Fallback to SQLite ')

    # إذا تم تعيين استخدام SQLite
    if USE_SQLITE:
        # استخدام ملف قاعدة بيانات SQLite في مجلد التطبيق
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR,'database.sqlite3')
        #SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:775275740@192.168.1.5:5432/archives'
        # ملاحظة: يمكن استبدال السطر أعلاه بسطر MySQL معلق لاستخدامه لاحقاً

    # إعداد أسماء الجداول الديناميكية المرتبطة بنماذج محددة
    DYNAMIC_DATATB = {
        "documents": "apps.models.Document"  # مثال: جدول الوثائق المرتبط بالنموذج Document
    }

    # إعدادات CDN (شبكة توصيل المحتوى)
    CDN_DOMAIN = os.getenv('CDN_DOMAIN')              # اسم النطاق الخاص بـ CDN
    CDN_HTTPS  = os.getenv('CDN_HTTPS', True)         # هل يدعم HTTPS
  except Exception as e:
    print(f'******err run.py 32{e}')
# إعدادات وضع الإنتاج
class ProductionConfig(Config):
    DEBUG = False  # إيقاف التصحيح

    # إعدادات أمنية للجلسات والكوكيز
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600  # مدة تذكر الجلسة (ثانية)

# إعدادات وضع التطوير
class DebugConfig(Config):
    DEBUG = True  # تفعيل التصحيح

# قاموس يحتوي على جميع إعدادات التكوين المحتملة
config_dict = {
    'Production': ProductionConfig,  # تكوين الإنتاج
    'Debug'     : DebugConfig        # تكوين التصحيح
}
