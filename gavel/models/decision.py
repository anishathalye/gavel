from gavel.models import db
from datetime import datetime

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    annotator_id = db.Column(db.Integer, db.ForeignKey('annotator.id'))
    annotator = db.relationship('Annotator', foreign_keys=[annotator_id], uselist=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    winner = db.relationship('Item', foreign_keys=[winner_id], uselist=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    loser = db.relationship('Item', foreign_keys=[loser_id], uselist=False)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, annotator, winner, loser):
        self.annotator = annotator
        self.winner = winner
        self.loser = loser
