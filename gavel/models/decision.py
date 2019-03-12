from gavel.models import db
from datetime import datetime
from gavel.models._basemodel import BaseModel


class Decision(BaseModel):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    annotator_id = db.Column(db.Integer, db.ForeignKey('annotator.id'))
    annotator = db.relationship('Annotator', foreign_keys=[annotator_id], uselist=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    winner = db.relationship('Item', foreign_keys=[winner_id], uselist=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    loser = db.relationship('Item', foreign_keys=[loser_id], uselist=False)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    _default_fields = ["annotator_id",
                       "winner_id",
                       "loser_id",
                       "time"]

    def __init__(self, annotator, winner, loser):
        self.annotator = annotator
        self.winner = winner
        self.loser = loser
