from gavel.models import db
from gavel.models.category import Category
import gavel.crowd_bt as crowd_bt
from sqlalchemy.orm.exc import NoResultFound

view_table = db.Table('view',
    db.Column('item_category_id', db.Integer, db.ForeignKey('item_category.id')),
    db.Column('annotator_id', db.Integer, db.ForeignKey('annotator.id'))
)

class ItemCategory(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    mu = db.Column(db.Float)
    sigma_sq = db.Column(db.Float)
    prioritized = db.Column(db.Boolean, default=False, nullable=False)

    viewed = db.relationship('Annotator', secondary=view_table)
    item = db.relationship('Item')
    category = db.relationship('Category')


    def __init__(self, item_id, category_id):
        self.item_id = item_id
        self.category_id = category_id
        self.mu = crowd_bt.MU_PRIOR
        self.sigma_sq = crowd_bt.SIGMA_SQ_PRIOR

    @classmethod
    def by_id(cls, uid):
        if uid is None:
            return None
        try:
            annotator = cls.query.with_for_update().get(uid)
        except NoResultFound:
            annotator = None
        return annotator



class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    categories = db.relationship('ItemCategory', cascade="all,delete")

    def __init__(self, name, location, description, *categories):
        self.name = name
        self.location = location
        self.description = description
        self.categories = [
            ItemCategory(-1, Category.by_name_or_id(category).id)
            for category in categories
        ]


    def get_category(self, category_id):
        for category in self.categories:
            if category.category_id == int(category_id):
                return category


    @classmethod
    def by_id(cls, uid):
        if uid is None:
            return None
        try:
            item = cls.query.get(uid)
        except NoResultFound:
            item = None
        return item
