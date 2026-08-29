from config.settings import Settings
from marshmallow import EXCLUDE, Schema, fields, validate


class UserCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True, validate=validate.Length(min=1, max=Settings.MAX_NAME_LENGTH))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=Settings.MIN_PASSWORD_LENGTH),
        load_only=True,
    )
    role = fields.Str(
        load_default=Settings.DEFAULT_ROLE,
        validate=validate.OneOf(Settings.VALID_ROLES),
    )


class UserUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(validate=validate.Length(min=1, max=Settings.MAX_NAME_LENGTH))
    email = fields.Email()
    password = fields.Str(
        validate=validate.Length(min=Settings.MIN_PASSWORD_LENGTH),
        load_only=True,
    )
    role = fields.Str(validate=validate.OneOf(Settings.VALID_ROLES))
    active = fields.Bool()


class LoginSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class UserResponseSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    email = fields.Email()
    role = fields.Str()
    active = fields.Bool()
    created_at = fields.Str(allow_none=True)
    task_count = fields.Int()
    tasks = fields.List(fields.Dict())


user_schema = UserResponseSchema()
users_schema = UserResponseSchema(many=True)
