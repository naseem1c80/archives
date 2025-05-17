# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from flask import current_app as app 
from flask_login import current_user, login_user
from flask_dance.consumer import oauth_authorized # type: ignore
from flask_dance.contrib.github import github, make_github_blueprint # type: ignore
from flask_dance.contrib.google import google, make_google_blueprint # type: ignore
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage # type: ignore
from sqlalchemy.orm.exc import NoResultFound # type: ignore
from apps.config import Config
from apps.models import Users, db, OAuth
from flask import redirect, url_for # type: ignore
from flask import flash # type: ignore

github_blueprint = make_github_blueprint(
    client_id=Config.GITHUB_ID,
    client_secret=Config.GITHUB_SECRET,
    scope = 'user',
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,        
    ),   
)

@oauth_authorized.connect_via(github_blueprint)
def github_logged_in(blueprint, token):
    info = github.get("/user")

    if info.ok:

        account_info = info.json()
        phone     = account_info["login"]

        query = Users.query.filter_by(oauth_github=phone)
        try:

            user = query.one()
            login_user(user)

        except NoResultFound:

            # Save to db
            user              = Users()
            user.phone     = '(gh)' + phone
            user.oauth_github = phone

            # Save current user
            db.session.add(user)
            db.session.commit()

            login_user(user)

# Google

google_blueprint = make_google_blueprint(
    client_id=Config.GOOGLE_ID,
    client_secret=Config.GOOGLE_SECRET,
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,        
    ),   
)

@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
    info = google.get("/oauth2/v1/userinfo")

    if info.ok:
        account_info = info.json()
        phone     = account_info["given_name"]
        email        = account_info["email"]

        query = Users.query.filter_by(oauth_google=phone)
        try:

            user = query.one()
            login_user(user)

        except NoResultFound:
            # Save to db
            user              = Users()
            user.phone     = '(google)' + phone
            user.oauth_google = phone
            user.email        = email

            # Save current user
            db.session.add(user)
            db.session.commit()

            login_user(user)
