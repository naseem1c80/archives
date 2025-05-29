# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os
from flask_migrate import Migrate   # لإدارة ترحيل قواعد البيانات (migrations)
from flask_minify import Minify     # لضغط ملفات HTML (ويمكن JS و CSS) لتسريع التحميل
from sys import exit                # للخروج من البرنامج في حالة حدوث خطأ
from apps.config import config_dict # استيراد إعدادات التكوين حسب البيئة (Debug أو Production)
from apps import create_app, db     # استيراد دالة إنشاء التطبيق وقاعدة البيانات

# تحديد وضع التصحيح DEBUG عبر قراءة متغير البيئة 'DEBUG'
# إذا كانت قيمته 'True' فإن DEBUG ستكون True، وإلا False
DEBUG = (os.getenv('DEBUG', 'False') == 'True')

# تعيين اسم وضع التكوين إما 'Debug' أو 'Production' بناءً على قيمة DEBUG
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # جلب إعدادات التطبيق بناءً على وضع التكوين المحدد (Debug أو Production)
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    # في حال لم يكن الوضع صحيحًا (غير موجود في config_dict) يتم الخروج برسالة خطأ
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

# إنشاء التطبيق باستخدام الإعدادات المحملة
app = create_app(app_config)

# فتح سياق التطبيق (app context) لإنشاء الجداول في قاعدة البيانات
with app.app_context():
    try:
        # محاولة إنشاء كل الجداول الموجودة في النماذج (models) باستخدام SQLAlchemy
        db.create_all()
    except Exception as e:
        # في حال حدوث خطأ أثناء إنشاء الجداول (مثلاً بسبب عدم وجود قاعدة البيانات)
        print('> Error: DBMS Exception: ' + str(e))

        # إعدادات متغيرات البيئة الخاصة بقاعدة البيانات (عادة MySQL)
        basedir = os.path.abspath(os.path.dirname(__file__))
        DB_ENGINE   = os.getenv('DB_ENGINE'   , None)
        DB_USERNAME = os.getenv('DB_USERNAME' , None)
        DB_PASS     = os.getenv('DB_PASS'     , None)
        DB_HOST     = os.getenv('DB_HOST'     , None)
        DB_PORT     = os.getenv('DB_PORT'     , None)
        DB_NAME     = os.getenv('DB_NAME'     , None)

        # إعداد عنوان الاتصال بقاعدة البيانات (MySQL) بناءً على المتغيرات أعلاه
        app.config['SQLALCHEMY_DATABASE_URI']  = f'mysql+pymysql://{DB_USERNAME}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

        # تعليق السطر التالي معناه أن هناك خيار للاتصال بقاعدة SQLite بدلاً من MySQL (لم يستخدم فعلاً)
        # app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir, 'db.sqlite3')

        print('> Fallback to SQLite ')  # رسالة توضح أن البرنامج يرجع لاستخدام SQLite كاحتياط

        # إعادة محاولة إنشاء الجداول الآن مع إعداد الاتصال الجديد (عادة SQLite)
        db.create_all()

# تهيئة ترحيل قاعدة البيانات (migrations) لتمكين التحديثات المستقبلية على قاعدة البيانات
Migrate(app, db)

# إذا لم يكن التطبيق في وضع التصحيح (أي في الإنتاج) يتم تفعيل ضغط ملفات HTML فقط
if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

# لو كان التطبيق في وضع التصحيح، نطبع بعض المعلومات في سجل التطبيق (log)
if DEBUG:
    app.logger.info('DEBUG            = ' + str(DEBUG))
    app.logger.info('Page Compression = ' + ('FALSE' if DEBUG else 'TRUE'))
    app.logger.info('DBMS             = ' + app_config.SQLALCHEMY_DATABASE_URI)

# نقطة دخول التطبيق عند تشغيل الملف مباشرة
if __name__ == "__main__":
    # تشغيل التطبيق على جميع عناوين الشبكة (0.0.0.0) مع المنفذ الافتراضي 5000 أو المنفذ المحدد في متغير البيئة PORT
    # ملاحظة: وضع debug هنا False حتى لو كانت المتغيرات تشير إلى True (يمكن تغييره حسب الحاجة)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
