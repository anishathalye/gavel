# Copyright (c) 2015-2018 Anish Athalye (me@anishathalye.com)
#
# This software is released under AGPLv3. See the included LICENSE.txt for
# details.
import os

from flask import Flask
from flask_minify import minify

app = Flask(__name__)
minify(app=app)
app.config['DEBUG'] = os.environ.get('DEBUG', False)

import gavel.settings as settings
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.SECRET_KEY

from flask_assets import Environment, Bundle
assets = Environment(app)
assets.config['pyscss_style'] = 'expanded'
assets.url = app.static_url_path
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

from gavel.models import db, ma
db.app = app
db.init_app(app)
ma.app = app
ma.init_app(app)

import gavel.template_filters # registers template filters

import gavel.controllers # registers controllers

# send usage stats
import gavel.utils
gavel.utils.send_telemetry('gavel-boot', {
    'base-url': settings.BASE_URL or '',
    'min-views': settings.MIN_VIEWS,
    'timeout': settings.TIMEOUT,
    'disable-email': settings.DISABLE_EMAIL
})
