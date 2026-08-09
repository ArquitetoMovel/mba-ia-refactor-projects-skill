from flask import Blueprint, jsonify, request

from controllers.category_controller import CategoryController
from schemas.category_schema import CategoryCreateSchema, CategoryUpdateSchema

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(CategoryController.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    payload = CategoryCreateSchema().load(request.get_json() or {})
    data, status = CategoryController.create_category(payload)
    return jsonify(data), status


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    payload = CategoryUpdateSchema().load(request.get_json() or {})
    return jsonify(CategoryController.update_category(category_id, payload)), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    return jsonify(CategoryController.delete_category(category_id)), 200
