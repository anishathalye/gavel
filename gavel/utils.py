from gavel import celery
import gavel.settings as settings
import gavel.crowd_bt as crowd_bt
import gavel.constants as constants
from flask import Markup, Response, request, render_template
import markdown
import requests
from functools import wraps
import base64
import os
import csv
import io
import re
import smtplib
import email
import email.mime.multipart
import email.mime.text

def gen_secret(length):
    return base64.b32encode(os.urandom(length))[:length].decode('utf8').lower()

def check_auth(username, password):
    return username == 'admin' and password == settings.ADMIN_PASSWORD

def authenticate():
    return Response('Access denied.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def data_to_csv_string(data):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue()

def data_from_csv_string(string):
    data_input = io.StringIO(string)
    reader = csv.reader(data_input)
    return list(reader)

def get_paragraphs(message):
    paragraphs = re.split(r'\n\n+', message)
    paragraphs = [i.replace('\n', ' ') for i in paragraphs if i]
    return paragraphs

@celery.task
def send_emails(emails):
    '''
    Send a batch of emails.

    This function takes a list [(to_address, subject, body)].
    '''

    if settings.EMAIL_AUTH_MODE == 'tls':
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
    elif settings.EMAIL_AUTH_MODE == 'ssl':
        server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
    elif settings.EMAIL_AUTH_MODE == 'none':
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.ehlo()
    else:
        raise ValueError('unsupported auth mode: %s' % settings.EMAIL_AUTH_MODE)

    server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)

    exceptions = []
    for e in emails:
        try:
            to_address, subject, body = e
            msg = email.mime.multipart.MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = to_address
            recipients = [to_address]
            if settings.EMAIL_CC:
                msg['Cc'] = ', '.join(settings.EMAIL_CC)
                recipients.extend(settings.EMAIL_CC)
            msg['Subject'] = subject
            msg.attach(email.mime.text.MIMEText(body, 'plain'))
            server.sendmail(settings.EMAIL_FROM, recipients, msg.as_string())
        except Exception as e:
            exceptions.append(e) # XXX is there a cleaner way to handle this?

    server.quit()
    if exceptions:
        raise Exception('Error sending some emails: %s' % exceptions)

def render_markdown(content):
    return Markup(markdown.markdown(content))

def user_error(message):
    return render_template('error.html', message=message), 400

def server_error(message):
    return render_template('error.html', message=message), 500

def send_telemetry(identifier, data):
    if not settings.SEND_STATS:
        return
    try:
        requests.post(
            constants.TELEMETRY_URL,
            json={'identifier': identifier, 'data': data},
            timeout=5
        )
    except Exception:
        pass # don't want this to break anything else

def cast_row(row):
    '''
    Convert workbook sheet cells into integers if they are equal to integer
    values and convert everything to a string.

    The xlrd library seems to import cells as float values if the cell had a
    numeric value, so this method is needed to correct that.
    '''
    for i, item in enumerate(row):
        if isinstance(item, (float, int)) and int(item) == item:
            row[i] = str(int(item))
        else:
            row[i] = str(item)
    return row
