from marshmallow import Schema, fields, validate, EXCLUDE

from config.settings import Settings


class CategoryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default='')
    color = fields.Str(
        load_default=Settings.DEFAULT_COLOR,
        validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'),
    )


class CategoryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))


class CategoryResponseSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    color = fields.Str()
    created_at = fields.Str(allow_none=True)
    task_count = fields.Int()


category_schema = CategoryResponseSchema()
categories_schema = CategoryResponseSchema(many=True)
