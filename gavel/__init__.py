# Copyright (c) Anish Athalye (me@anishathalye.com)
#
# This software is released under AGPLv3. See the included LICENSE.txt for
# details.

from flask import Flask
app = Flask(__name__)

import gavel.settings as settings
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['SERVER_NAME'] = settings.SERVER_NAME

if settings.PROXY:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

# Configure CORS for HackPSU auth integration
from flask_cors import CORS
import os
allowed_origins = [
    'https://auth.hackpsu.org',
    'https://hackpsu.org',
    'http://localhost:3000',
    'http://localhost:5000',
    os.environ.get('AUTH_SERVER_URL', '').replace('/api/sessionUser', '') if os.environ.get('AUTH_SERVER_URL') else None
]
allowed_origins = [origin for origin in allowed_origins if origin]  # Filter out None values

CORS(app,
     origins=allowed_origins,
     supports_credentials=True)

from flask_assets import Environment, Bundle
assets = Environment(app)
assets.config['pyscss_style'] = 'expanded'
scss = Bundle(
    'css/style.scss',
    depends='**/*.scss',
    filters=('pyscss',),
    output='all.css'
)
assets.register('scss_all', scss)

from celery import Celery
app.config['CELERY_BROKER_URL'] = settings.BROKER_URI
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from gavel.models import db
db.app = app
db.init_app(app)

import gavel.template_filters # registers template filters

import gavel.controllers # registers controllers

# Set up automatic project sync from HackPSU API
if os.environ.get('ENABLE_PROJECT_SYNC', 'true').lower() == 'true':
    from gavel.project_sync import setup_project_sync
    setup_project_sync()
