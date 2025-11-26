# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request,session,redirect
from flask_login import login_required
from jinja2 import TemplateNotFound
from flask import jsonify
from apps.models import Users,Notification,Role
from flask_login import login_required
from jinja2 import TemplateNotFound
import os
import json
from collections import defaultdict

from apps.models import Branch
@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/getdataarchivs2')
@login_required
def getdataarchivs2():
   root_path ='static/uploads'
   # غيّر هذا إلى المسار الصحيح

   # إعداد العدادات
   daily_count = defaultdict(int)
   monthly_count = defaultdict(int)
   yearly_count = defaultdict(int)
   branch_count = defaultdict(int)

   # استعراض الملفات
   for dirpath, dirnames, filenames in os.walk(root_path):
      parts = dirpath.replace(root_path, '').strip(os.sep).split(os.sep)
      if len(parts) >= 4:
        year, month, day, branch = parts[:4]
        date_str = f"{year}-{month}-{day}"
        month_str = f"{year}-{month}"

        count = len(filenames)

        # جمع البيانات
        daily_count[date_str] += count
        monthly_count[month_str] += count
        yearly_count[year] += count
        branch_count[branch] += count

   # تجهيز البيانات لتصديرها كـ JSON
   result = {
    "by_day": dict(daily_count),
    "by_month": dict(monthly_count),
    "by_year": dict(yearly_count),
    "by_branch": dict(branch_count)
    }

  # حفظ البيانات في ملف JSON
  #with open("archived_stats.json", "w", encoding="utf-8") as f:
 #   json.dump(result, f, ensure_ascii=False, indent=4)
   return result

@blueprint.route('/getdataarchivs')
@login_required
def getdataarchivs():
    root_path = 'static/uploads'
    
    # إعداد العدادات
    daily_count = defaultdict(int)
    monthly_count = defaultdict(int)
    yearly_count = defaultdict(int)
    branch_count = defaultdict(int)

    # استعراض الملفات
    for dirpath, dirnames, filenames in os.walk(root_path):
        parts = dirpath.replace(root_path, '').strip(os.sep).split(os.sep)
        if len(parts) >= 4:
            year, month, day, branch_folder = parts[:4]
            date_str = f"{year}-{month}-{day}"
            month_str = f"{year}-{month}"

            count = len(filenames)

            # جمع البيانات
            daily_count[date_str] += count
            monthly_count[month_str] += count
            yearly_count[year] += count
            
            # البحث عن اسم الفرع الحقيقي من قاعدة البيانات
            branch = Branch.query.filter_by(id=branch_folder).first()
            if branch:
                branch_name = branch.name  # استخدام حقل name من نموذج Branch
                branch_count[branch_name] += count
            else:
                # إذا لم يتم العثور على الفرع، استخدم اسم المجلد كبديل
                branch_count[branch_folder] += count

    # تجهيز البيانات لتصديرها كـ JSON
    result = {
        "by_day": dict(daily_count),
        "by_month": dict(monthly_count),
        "by_year": dict(yearly_count),
        "by_branch": dict(branch_count),
        "size":getSizearchivs()
    }

    return result



from flask import jsonify

def format_size(size_bytes):
    """تحويل الحجم إلى الوحدة المناسبة تلقائياً"""
    if size_bytes == 0:
        return "0 Byte"
    
    size_names = ["Byte", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return {
        'value': round(size_bytes, 2),
        'unit': size_names[i],
        'original_bytes': size_bytes * (1024 ** i) if i > 0 else size_bytes
    }

@blueprint.route('/get_branch_stats')
@login_required
def get_branch_stats():
    branch_data = getSizearchivs()
    return jsonify(branch_data)
def getSizearchivs():
    root_path = 'static/uploads'
    
    branch_count = defaultdict(int)
    branch_size = defaultdict(int)

    # استعراض الملفات
    for dirpath, dirnames, filenames in os.walk(root_path):
        parts = dirpath.replace(root_path, '').strip(os.sep).split(os.sep)
        if len(parts) >= 4:
            year, month, day, branch_folder = parts[:4]
            
            count = len(filenames)
            
            # حساب حجم الملفات
            total_size = 0
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)

            # البحث عن اسم الفرع
            branch = Branch.query.filter_by(id=branch_folder).first()
            if branch:
                branch_name = branch.name
                branch_count[branch_name] += count
                branch_size[branch_name] += total_size
            else:
                branch_count[branch_folder] += count
                branch_size[branch_folder] += total_size

    # تحويل الحجم إلى الوحدة المناسبة
    branch_data = []
    for branch_name, size_bytes in branch_size.items():
        # التحويل التلقائي للوحدة
        if size_bytes < 1024:
            size_value = size_bytes
            size_unit = "Byte"
            max_size = 1024  # 1 KB كحد أقصى
        elif size_bytes < 1024 * 1024:
            size_value = size_bytes / 1024
            size_unit = "KB"
            max_size = 1024  # 1 MB كحد أقصى
        elif size_bytes < 1024 * 1024 * 1024:
            size_value = size_bytes / (1024 * 1024)
            size_unit = "MB"
            max_size = 1024  # 1 GB كحد أقصى
        else:
            size_value = size_bytes / (1024 * 1024 * 1024)
            size_unit = "GB"
            max_size = 2  # 2 GB كحد أقصى
        
        # حساب النسبة المئوية
        percentage = min((size_bytes / (max_size * (1024 ** (['Byte', 'KB', 'MB', 'GB'].index(size_unit))))) * 100, 100)
        
        branch_data.append({
            'name': branch_name,
            'percentage': round(percentage, 1),
            'size_value': round(size_value, 2),
            'size_unit': size_unit,
            'max_size': max_size,
            'count': branch_count[branch_name],
            'display_text': f"{round(size_value, 2)} {size_unit}"
        })

    branch_data.sort(key=lambda x: x['percentage'], reverse=True)
    return branch_data
def getSizearchivs0():
    root_path = 'static/uploads'
    
    # إعداد العدادات
    daily_count = defaultdict(int)
    monthly_count = defaultdict(int)
    yearly_count = defaultdict(int)
    branch_count = defaultdict(int)
    branch_size = defaultdict(int)  # لحجم الملفات بالبايت

    # استعراض الملفات
    for dirpath, dirnames, filenames in os.walk(root_path):
        parts = dirpath.replace(root_path, '').strip(os.sep).split(os.sep)
        if len(parts) >= 4:
            year, month, day, branch_folder = parts[:4]
            date_str = f"{year}-{month}-{day}"
            month_str = f"{year}-{month}"

            count = len(filenames)
            
            # حساب حجم الملفات في هذا المجلد
            total_size = 0
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)

            # جمع البيانات
            daily_count[date_str] += count
            monthly_count[month_str] += count
            yearly_count[year] += count
            
            # البحث عن اسم الفرع الحقيقي من قاعدة البيانات
            branch = Branch.query.filter_by(id=branch_folder).first()
            if branch:
                branch_name = branch.name
                branch_count[branch_name] += count
                branch_size[branch_name] += total_size
            else:
                branch_count[branch_folder] += count
                branch_size[branch_folder] += total_size

    # تحويل الحجم إلى الوحدة المناسبة وحساب النسبة المئوية
    branch_data = []
    for branch_name, size_bytes in branch_size.items():
        # تحويل الحجم إلى الوحدة المناسبة
        formatted_size = format_size(size_bytes)
        
        # تحديد السعة القصوى بناءً على الوحدة
        max_size = 2  # 2 من الوحدة الحالية
        if formatted_size['unit'] == 'KB':
            max_size_bytes = 2 * 1024  # 2 KB
        elif formatted_size['unit'] == 'MB':
            max_size_bytes = 2 * 1024 * 1024  # 2 MB
        elif formatted_size['unit'] == 'GB':
            max_size_bytes = 2 * 1024 * 1024 * 1024  # 2 GB
        else:  # Bytes
            max_size_bytes = 2 * 1024  # 2 KB افتراضي للبايت
            
        # حساب النسبة المئوية
        percentage = min((size_bytes / max_size_bytes) * 100, 100)
        
        branch_data.append({
            'name': branch_name,
            'percentage': round(percentage, 1),
            'size_value': formatted_size['value'],
            'size_unit': formatted_size['unit'],
            'max_size': max_size,
            'count': branch_count[branch_name],
            'raw_bytes': size_bytes
        })

    # ترتيب الفروع حسب النسبة (من الأعلى إلى الأدنى)
    branch_data.sort(key=lambda x: x['percentage'], reverse=True)

    return branch_data

@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
