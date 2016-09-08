from gavel import app
from flask import render_template

@app.errorhandler(404)
def error_404(e):
    return (
        render_template('error.html', message='Page not found.'),
        404
    )

@app.errorhandler(403)
def error_403(e):
    return (
        render_template('error.html', message='Forbidden. Go back, refresh the page, and try again.'),
        403
    )

@app.errorhandler(500)
def error_500(e):
    return (
        render_template('error.html', message='Internal server error. Go back and try again.'),
        500
    )
