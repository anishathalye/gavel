from gavel.models import db
from gavel.models.category import Category
import gavel.utils as utils
import gavel.crowd_bt as crowd_bt
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime

ignore_table = db.Table('ignore',
    db.Column('annotator_category_id', db.Integer, db.ForeignKey('annotator_category.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)


class AnnotatorCategory(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    annotator_id = db.Column(db.Integer, db.ForeignKey('annotator.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    alpha = db.Column(db.Float)
    beta = db.Column(db.Float)

    next_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    next = db.relationship('Item', foreign_keys=[next_id], uselist=False)
    updated = db.Column(db.DateTime)
    prev_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    prev = db.relationship('Item', foreign_keys=[prev_id], uselist=False)

    annotator = db.relationship('Annotator')
    category = db.relationship('Category')

    ignore = db.relationship('Item', secondary=ignore_table)


    def __init__(self, annotator_id, category_id):
        self.annotator_id = annotator_id
        self.category_id = category_id
        self.alpha = crowd_bt.ALPHA_PRIOR
        self.beta = crowd_bt.BETA_PRIOR

    def update_next(self, new_next):
        if new_next is not None:
            new_next.prioritized = False # it's now assigned, so cancel the prioritization
            # it could happen that the judge skips the project, but that
            # doesn't re-prioritize the project
            self.updated = datetime.utcnow()
            self.next = new_next.item
        else:
            self.next = None

    @classmethod
    def by_id(cls, uid):
        if uid is None:
            return None
        try:
            annotator = cls.query.with_for_update().get(uid)
        except NoResultFound:
            annotator = None
        return annotator


class Annotator(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    read_welcome = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text, nullable=False)
    secret = db.Column(db.String(32), unique=True, nullable=False)
    categories = db.relationship('AnnotatorCategory', cascade="all,delete")

    def __init__(self, name, email, description, *categories):
        self.name = name
        self.email = email
        self.description = description
        self.secret = utils.gen_secret(32)
        self.categories = [
            AnnotatorCategory(-1, Category.by_name_or_id(category).id)
            for category in categories
        ]

    def get_category(self, category_id):
        for category in self.categories:
            if category.category_id == int(category_id):
                return category

    @classmethod
    def by_secret(cls, secret):
        try:
            annotator = cls.query.filter(cls.secret == secret).one()
        except NoResultFound:
            annotator = None
        return annotator

    @classmethod
    def by_id(cls, uid):
        if uid is None:
            return None
        try:
            annotator = cls.query.with_for_update().get(uid)
        except NoResultFound:
            annotator = None
        return annotator
