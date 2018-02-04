from gavel import app
import gavel.settings as settings
from flask import send_from_directory
import os

@app.route(settings.BASE_PATH + 'favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )
