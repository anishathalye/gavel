from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import desc
from datetime import datetime
import crowd_bt
import base64
import os

class SerializableAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if not 'isolation_level' in options:
            # XXX is this slow? are there better ways?
            options['isolation_level'] = 'SERIALIZABLE'
        return super(SerializableAlchemy, self).apply_driver_hacks(app, info, options)

db = SerializableAlchemy()

def gen_secret(length):
    return base64.b32encode(os.urandom(length))[:length].decode('utf8').lower()

ignore_table = db.Table('ignore',
    db.Column('annotator_id', db.Integer, db.ForeignKey('annotator.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)

view_table = db.Table('view',
    db.Column('item_id', db.Integer, db.ForeignKey('item.id')),
    db.Column('annotator_id', db.Integer, db.ForeignKey('annotator.id'))
)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    location = db.Column(db.Text)
    description = db.Column(db.Text)
    viewed = db.relationship('Annotator', secondary=view_table)

    mu = db.Column(db.Float)
    sigma_sq = db.Column(db.Float)

    def __init__(self, name, location, description):
        self.name = name
        self.location = location
        self.description = description
        self.mu = crowd_bt.MU_PRIOR
        self.sigma_sq = crowd_bt.SIGMA_SQ_PRIOR

    @classmethod
    def by_id(cls, uid):
        if uid is None:
            return None
        try:
            item = cls.query.get(uid)
        except NoResultFound:
            item = None
        return item


class Annotator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    description = db.Column(db.Text)
    secret = db.Column(db.String(32), unique=True, nullable=False)
    next_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    next = db.relationship('Item', foreign_keys=[next_id], uselist=False)
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
        self.secret = gen_secret(32)

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


class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    annotator_id = db.Column(db.Integer, db.ForeignKey('annotator.id'))
    annotator = db.relationship('Annotator', foreign_keys=[annotator_id], uselist=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    winner = db.relationship('Item', foreign_keys=[winner_id], uselist=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    loser = db.relationship('Item', foreign_keys=[loser_id], uselist=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, annotator, winner, loser):
        self.annotator = annotator
        self.winner = winner
        self.loser = loser
