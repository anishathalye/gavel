from gavel.settings import ADMIN_PASSWORD
import gavel.crowd_bt as crowd_bt
from flask import Response, request
from functools import wraps
import base64
import os
import csv
import io

def gen_secret(length):
    return base64.b32encode(os.urandom(length))[:length].decode('utf8').lower()

def check_auth(username, password):
    return username == 'admin' and password == ADMIN_PASSWORD

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
