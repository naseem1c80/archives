# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.settings import blueprint
from flask import render_template, request,session,redirect
from flask_login import login_required
from jinja2 import TemplateNotFound

@blueprint.route('/set_language/<lang>')
def set_language(lang):
    prev_url = request.referrer
    if lang in ['en', 'ar']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.index'))
    
@blueprint.route('/settings')
@login_required
def settings():

    return render_template('settings/settings.html', segment='settings')

