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
        render_template('error.html', message='Gavel has encoutered an error. Click the button below to go back. Refreshing the page from there usually fixes things.'),
        403
    )

@app.errorhandler(500)
def error_500(e):
    return (
        render_template('error.html', message='Internal server error. Click the button below and go back. Refreshing the page from there usually fixes things.'),
        500
    )
