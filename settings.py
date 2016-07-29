import os

ADMIN_PASSWORD = os.environ['ADMIN_PASSWORD']
ANNOTATOR_ID = 'annotator_id'
# Todo: Consider renaming DB_URI to DATABASE_URL for consistency across local
# and heroku platform.
DB_URI = os.environ.get('DB_URI', 
        os.environ.get('DATABASE_URL', 'postgresql://localhost/gavel'))
SECRET_KEY = os.environ.get('SECRET_KEY', 'gavel-secret')
PORT = int(os.environ.get('PORT', 5000))
