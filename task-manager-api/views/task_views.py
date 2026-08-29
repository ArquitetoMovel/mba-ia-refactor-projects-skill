from controllers.task_controller import TaskController
from flask import Blueprint, jsonify, request
from middlewares.auth import token_required
from schemas.common_schema import PaginationSchema
from schemas.task_schema import TaskCreateSchema, TaskSearchSchema, TaskUpdateSchema, task_schema, tasks_schema

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
@token_required
def get_tasks():
    params = PaginationSchema().load(request.args)
    result = TaskController.list_tasks(page=params['page'], per_page=params['per_page'])
    result['items'] = tasks_schema.dump(result['items'])
    return jsonify(result), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    return jsonify(task_schema.dump(TaskController.get_task(task_id))), 200


@task_bp.route('/tasks', methods=['POST'])
@token_required
def create_task():
    payload = TaskCreateSchema().load(request.get_json() or {})
    data, status = TaskController.create_task(payload)
    return jsonify(task_schema.dump(data)), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    payload = TaskUpdateSchema().load(request.get_json() or {})
    return jsonify(task_schema.dump(TaskController.update_task(task_id, payload))), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    return jsonify(TaskController.delete_task(task_id)), 200


@task_bp.route('/tasks/search', methods=['GET'])
@token_required
def search_tasks():
    filters = TaskSearchSchema().load(request.args)
    params = PaginationSchema().load(request.args)
    result = TaskController.search_tasks(
        query=filters['q'],
        status=filters['status'],
        priority=filters['priority'],
        user_id=filters['user_id'],
        page=params['page'],
        per_page=params['per_page'],
    )
    result['items'] = tasks_schema.dump(result['items'])
    return jsonify(result), 200


@task_bp.route('/tasks/stats', methods=['GET'])
@token_required
def task_stats():
    return jsonify(TaskController.stats()), 200
