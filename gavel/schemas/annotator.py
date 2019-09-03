from marshmallow_sqlalchemy import ModelSchema, fields

from gavel.models import Annotator, Item


class AnnotatorSchema(ModelSchema):
    next = fields.Nested('ItemSchema')
    prev = fields.Nested('ItemSchema')

    class Meta:
        model = Annotator
