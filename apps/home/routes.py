# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request,session,redirect
from flask_login import login_required
from jinja2 import TemplateNotFound

from apps.models import Users,Notification,Role
from flask_login import login_required
from jinja2 import TemplateNotFound
import os
import json
from collections import defaultdict
    
@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/getdataarchivs')
@login_required
def getdataarchivs():
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
