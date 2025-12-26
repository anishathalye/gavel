from gavel import app
import gavel.utils as utils
from flask import abort, request, session

@app.before_request
def csrf_protect():
    print(f"[DEBUG] CSRF check for {request.method} {request.path}")

    # Skip CSRF for health check and other safe endpoints
    if request.path in ['/health', '/favicon.ico']:
        print(f"[DEBUG] Skipping CSRF for {request.path}")
        return

    if request.method == "POST":
        token = session.get('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            print(f"[DEBUG] CSRF check failed for {request.path}")
            abort(403)

    print(f"[DEBUG] CSRF check passed for {request.path}")

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = utils.gen_secret(32)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token
