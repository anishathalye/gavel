import gavel.settings as settings
import gavel.constants as constants
from gavel.models import *
from flask import url_for
import requests
import time

def check_send_telemetry():
    try:
        _check_send_telemetry()
    except Exception:
        pass # don't want this to break anything else

def _check_send_telemetry():
    if not settings.SEND_STATS:
        return
    last = Setting.value_of(constants.SETTING_TELEMETRY_LAST_SENT)
    if last is not None:
        if time.time() - int(last) < constants.TELEMETRY_DELTA:
            return
    Setting.set(constants.SETTING_TELEMETRY_LAST_SENT, str(int(time.time())))
    db.session.commit()
    stats = gather_stats()
    send_telemetry('gavel-v1', stats)

def gather_stats():
    return {
        'base-url': url_for('index', _external=True),
        'disable-email': settings.DISABLE_EMAIL,
        'use-sendgrid': settings.USE_SENDGRID,
        'custom-messages': (
            settings.WELCOME_MESSAGE != constants.DEFAULT_WELCOME_MESSAGE or
            settings.CLOSED_MESSAGE != constants.DEFAULT_CLOSED_MESSAGE or
            settings.DISABLED_MESSAGE != constants.DEFAULT_DISABLED_MESSAGE or
            settings.LOGGED_OUT_MESSAGE != constants.DEFAULT_LOGGED_OUT_MESSAGE or
            settings.WAIT_MESSAGE != constants.DEFAULT_WAIT_MESSAGE or
            settings.EMAIL_SUBJECT != constants.DEFAULT_EMAIL_SUBJECT or
            settings.EMAIL_BODY != constants.DEFAULT_EMAIL_BODY
        ),
        'judges': Annotator.query.count(),
        'items': Item.query.count(),
        'decisions': Decision.query.count(),
    }

def send_telemetry(identifier, data):
    requests.post(
        constants.TELEMETRY_URL,
        json={'identifier': identifier, 'data': data},
        timeout=3
    )
