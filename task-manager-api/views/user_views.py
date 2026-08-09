from flask import Blueprint, jsonify, request

from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from schemas.user_schema import LoginSchema, UserCreateSchema, UserUpdateSchema

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(UserController.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify(UserController.get_user(user_id)), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    payload = UserCreateSchema().load(request.get_json() or {})
    data, status = UserController.create_user(payload)
    return jsonify(data), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    payload = UserUpdateSchema().load(request.get_json() or {})
    return jsonify(UserController.update_user(user_id, payload)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    return jsonify(UserController.delete_user(user_id)), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return jsonify(UserController.get_user_tasks(user_id)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    payload = LoginSchema().load(request.get_json() or {})
    return jsonify(AuthController.login(payload['email'], payload['password'])), 200
