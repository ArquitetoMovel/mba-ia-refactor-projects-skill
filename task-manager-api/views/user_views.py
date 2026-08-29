from config.settings import Settings
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from flask import Blueprint, g, jsonify, request
from middlewares.auth import role_required, token_required
from schemas.common_schema import PaginationSchema
from schemas.task_schema import tasks_schema
from schemas.user_schema import (
    LoginSchema,
    UserCreateSchema,
    UserUpdateSchema,
    user_schema,
    users_schema,
)

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
@role_required(Settings.ROLE_ADMIN)
def get_users():
    params = PaginationSchema().load(request.args)
    result = UserController.list_users(page=params['page'], per_page=params['per_page'])
    result['items'] = users_schema.dump(result['items'])
    return jsonify(result), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    return jsonify(user_schema.dump(UserController.get_user(user_id, g.current_user))), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    payload = UserCreateSchema().load(request.get_json() or {})
    data, status = UserController.create_user(payload)
    return jsonify(user_schema.dump(data)), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    payload = UserUpdateSchema().load(request.get_json() or {})
    data = UserController.update_user(user_id, payload, g.current_user)
    return jsonify(user_schema.dump(data)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required(Settings.ROLE_ADMIN)
def delete_user(user_id):
    return jsonify(UserController.delete_user(user_id)), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@token_required
def get_user_tasks(user_id):
    tasks = UserController.get_user_tasks(user_id, g.current_user)
    return jsonify(tasks_schema.dump(tasks)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    payload = LoginSchema().load(request.get_json() or {})
    return jsonify(AuthController.login(payload['email'], payload['password'])), 200
