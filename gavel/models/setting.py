from gavel.models import db
from sqlalchemy.orm.exc import NoResultFound

from gavel.models._basemodel import BaseModel

class Setting(BaseModel):
    key = db.Column(db.Text, unique=True, nullable=False, primary_key=True)
    value = db.Column(db.Text, nullable=False)

    _default_fields = ["key","value"]

    def __init__(self, key, value):
        self.key = key
        self.value = value

    @classmethod
    def by_key(cls, key):
        try:
            setting = cls.query.filter(cls.key == key).one()
        except NoResultFound:
            setting = None
        return setting

    @classmethod
    def value_of(cls, key):
        setting = cls.by_key(key)
        if setting:
            return setting.value
        else:
            return None

    @classmethod
    def set(cls, key, value):
        setting = cls.by_key(key)
        if setting:
            setting.value = value
        else:
            setting = cls(key, value)
            db.session.add(setting)
