from gavel.models import db
from datetime import datetime

class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    annotator_id = db.Column(db.Integer, db.ForeignKey('annotator.id'))
    annotator = db.relationship('Annotator', foreign_keys=[annotator_id], uselist=False)
    project_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    project = db.relationship('Item', foreign_keys=[project_id], uselist=False)
    reason = db.Column(db.Text, nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, annotator, project, reason):
        self.annotator = annotator
        self.project = project
        self.reason = reason
