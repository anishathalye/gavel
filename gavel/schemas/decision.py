from marshmallow_sqlalchemy import ModelSchema

from gavel.models import Decision


class DecisionSchema(ModelSchema):
    class Meta:
        model = Decision
