from sqlalchemy.orm.exc import NoResultFound

from gavel.models import db
from datetime import datetime

from gavel.models._basemodel import BaseModel

class Flag(BaseModel):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    annotator_id = db.Column(db.Integer, db.ForeignKey('annotator.id'))
    annotator = db.relationship('Annotator', foreign_keys=[annotator_id], uselist=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    item = db.relationship('Item', foreign_keys=[item_id], uselist=False)
    reason = db.Column(db.Text, nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    _default_fields = ["annotator_id","item_id","reason","resolved","time"]

    relations_keys = ("item", "annotator")

    def __init__(self, annotator, item, reason):
        self.annotator = annotator
        self.item = item
        self.reason = reason

    def __repr__(self):
        return '<Flag %r>' % self.id

    @classmethod
    def by_id(cls, uid):
        if uid is None:
            return None
        try:
            flag = cls.query.with_for_update().get(uid)
        except NoResultFound:
            flag = None
        return flag
