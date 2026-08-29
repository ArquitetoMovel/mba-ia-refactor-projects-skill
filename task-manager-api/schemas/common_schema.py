from config.settings import Settings
from marshmallow import EXCLUDE, Schema, fields, validate


class PaginationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(
        load_default=Settings.DEFAULT_PER_PAGE,
        validate=validate.Range(min=1, max=Settings.MAX_PER_PAGE),
    )
