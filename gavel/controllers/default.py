from gavel import app
from flask import send_from_directory
import os

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# Google site verification file handler
import gavel.settings as settings
from flask import Response

if settings.GOOGLE_SITE_VERIFICATION_FILENAME:
    @app.route(f"/{{filename}}", methods=["GET"])
    def google_site_verification(filename):
        if filename == settings.GOOGLE_SITE_VERIFICATION_FILENAME:
            content = f"google-site-verification: {filename}"
            return Response(content, mimetype="text/html")
        return ("Not Found", 404)
