from marshmallow import Schema, fields, validate, EXCLUDE, pre_load

from config.settings import Settings


class TaskCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(
        required=True,
        validate=validate.Length(min=Settings.MIN_TITLE_LENGTH, max=Settings.MAX_TITLE_LENGTH),
    )
    description = fields.Str(load_default='')
    status = fields.Str(
        load_default='pending',
        validate=validate.OneOf(Settings.VALID_STATUSES),
    )
    priority = fields.Int(
        load_default=Settings.DEFAULT_PRIORITY,
        validate=validate.Range(min=1, max=5),
    )
    user_id = fields.Int(allow_none=True, load_default=None)
    category_id = fields.Int(allow_none=True, load_default=None)
    due_date = fields.Date(allow_none=True, load_default=None, format='%Y-%m-%d')
    tags = fields.Raw(allow_none=True, load_default=None)

    @pre_load
    def normalize_tags(self, data, **kwargs):
        return data


class TaskUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(
        validate=validate.Length(min=Settings.MIN_TITLE_LENGTH, max=Settings.MAX_TITLE_LENGTH),
    )
    description = fields.Str()
    status = fields.Str(validate=validate.OneOf(Settings.VALID_STATUSES))
    priority = fields.Int(validate=validate.Range(min=1, max=5))
    user_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
    due_date = fields.Date(allow_none=True, format='%Y-%m-%d')
    tags = fields.Raw(allow_none=True)


class TaskResponseSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str(allow_none=True)
    status = fields.Str()
    priority = fields.Int()
    user_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
    created_at = fields.Str(allow_none=True)
    updated_at = fields.Str(allow_none=True)
    due_date = fields.Str(allow_none=True)
    tags = fields.List(fields.Str())
    overdue = fields.Bool()
    user_name = fields.Str(allow_none=True)
    category_name = fields.Str(allow_none=True)


task_schema = TaskResponseSchema()
tasks_schema = TaskResponseSchema(many=True)
