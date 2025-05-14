# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.charts import blueprint
from flask import render_template
from apps.models import Document

@blueprint.route('/charts')
def charts():
    documents = [{'name': document.name, 'user_id': document.user_id} for document in Document.get_list()]
    return render_template('charts/index.html', segment='charts', documents=documents)