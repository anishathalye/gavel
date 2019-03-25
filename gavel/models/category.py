from gavel.models import db
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    annotators = db.relationship('AnnotatorCategory', cascade="all,delete")
    items = db.relationship('ItemCategory', cascade="all,delete")

    def __init__(self, name, description):
        self.name = name
        self.description = description

    @classmethod
    def by_id(cls, uid):
        if uid is None:
            return None
        try:
            item = cls.query.get(uid)
        except NoResultFound:
            item = None
        return item

    @classmethod
    def by_name_or_id(cls, uid):
        category = cls.by_id(uid)
        if category:
            return category

        try:
            return cls.query.filter(cls.name == uid).first()
        except NoResultFound:
            return None
