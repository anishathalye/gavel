import os
ADMIN_PASSWORD = os.environ['ADMIN_PASSWORD']
ANNOTATOR_ID = 'annotator_id'
DB_URI = os.environ.get('DB_URI', 'postgresql://localhost/gavel')
SECRET_KEY = os.environ.get('SECRET_KEY', 'gavel-secret')
