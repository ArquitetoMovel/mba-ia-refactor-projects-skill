from config.settings import Settings
from controllers.category_controller import CategoryController
from flask import Blueprint, jsonify, request
from middlewares.auth import role_required, token_required
from schemas.category_schema import (
    CategoryCreateSchema,
    CategoryUpdateSchema,
    category_schema,
    categories_schema,
)

category_bp = Blueprint('categories', __name__)

_EDIT_ROLES = (Settings.ROLE_ADMIN, Settings.ROLE_MANAGER)


@category_bp.route('/categories', methods=['GET'])
@token_required
def get_categories():
    return jsonify(categories_schema.dump(CategoryController.list_categories())), 200


@category_bp.route('/categories', methods=['POST'])
@role_required(*_EDIT_ROLES)
def create_category():
    payload = CategoryCreateSchema().load(request.get_json() or {})
    data, status = CategoryController.create_category(payload)
    return jsonify(category_schema.dump(data)), status


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@role_required(*_EDIT_ROLES)
def update_category(category_id):
    payload = CategoryUpdateSchema().load(request.get_json() or {})
    return jsonify(category_schema.dump(CategoryController.update_category(category_id, payload))), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@role_required(*_EDIT_ROLES)
def delete_category(category_id):
    return jsonify(CategoryController.delete_category(category_id)), 200
