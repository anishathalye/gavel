from marshmallow_sqlalchemy import ModelSchema, fields
from marshmallow_sqlalchemy.fields import Nested

from gavel.models import Item, Annotator


class ItemSchema(ModelSchema):
    viewed = Nested('AnnotatorSchema',
                    exclude=Annotator.relations_keys,
                    dump_only=True,
                    many=True)

    class Meta:
        model = Item

