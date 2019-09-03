from marshmallow_sqlalchemy import ModelSchema

from gavel.models.setting import Setting


class SettingSchema(ModelSchema):
    class Meta:
        model = Setting
