from gavel import app
from flask import send_from_directory
import os


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# Google site verification file handler
import gavel.settings as settings
from flask import Response

if settings.GOOGLE_SITE_VERIFICATION_FILENAME:
    # Register a route for the exact filename
    filename = settings.GOOGLE_SITE_VERIFICATION_FILENAME
    route_path = f"/{filename}"

    def google_site_verification():
        content = f"google-site-verification: {filename}"
        return Response(content, mimetype="text/html")

    # Dynamically add the route
    app.add_url_rule(route_path, "google_site_verification", google_site_verification)
