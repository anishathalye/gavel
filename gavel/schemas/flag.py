from marshmallow_sqlalchemy import fields, ModelSchema
from marshmallow_sqlalchemy.fields import Nested

from gavel.models import Flag, Annotator, Item


class FlagSchema(ModelSchema):
    annotator = fields.Nested('AnnotatorSchema')
    item = fields.Nested('ItemSchema')

    class Meta:
        model = Flag
