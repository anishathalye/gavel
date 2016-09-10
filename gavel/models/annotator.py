from gavel.models import db
import gavel.utils as utils
import gavel.crowd_bt as crowd_bt
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime

ignore_table = db.Table('ignore',
    db.Column('annotator_id', db.Integer, db.ForeignKey('annotator.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)

class Annotator(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    read_welcome = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text, nullable=False)
    secret = db.Column(db.String(32), unique=True, nullable=False)
    next_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    next = db.relationship('Item', foreign_keys=[next_id], uselist=False)
    updated = db.Column(db.DateTime)
    prev_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    prev = db.relationship('Item', foreign_keys=[prev_id], uselist=False)
    ignore = db.relationship('Item', secondary=ignore_table)

    alpha = db.Column(db.Float)
    beta = db.Column(db.Float)

    def __init__(self, name, email, description):
        self.name = name
        self.email = email
        self.description = description
        self.alpha = crowd_bt.ALPHA_PRIOR
        self.beta = crowd_bt.BETA_PRIOR
        self.secret = utils.gen_secret(32)

    def update_next(self, new_next):
        if new_next is not None:
            new_next.prioritized = False # it's now assigned, so cancel the prioritization
            # it could happen that the judge skips the project, but that
            # doesn't re-prioritize the project
            self.updated = datetime.utcnow()
        self.next = new_next

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
