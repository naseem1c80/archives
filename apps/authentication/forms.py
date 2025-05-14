# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import  DataRequired

# login and registration


class LoginForm(FlaskForm):
    phone = StringField('phone',
                         id='phone_login',
                         validators=[DataRequired()])
    password = PasswordField('Password',
                             id='pwd_login',
                             validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    phone = StringField('Phone',
                         id='phone_create',
                         validators=[DataRequired()])
    full_name = StringField('Full_name',
                      id='full_name_create',
                      validators=[DataRequired()])
    password = PasswordField('Password',
                             id='pwd_create',
                             validators=[DataRequired()])
