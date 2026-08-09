from flask import Blueprint, jsonify, request

from controllers.task_controller import TaskController
from schemas.task_schema import TaskCreateSchema, TaskUpdateSchema

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(TaskController.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(TaskController.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    payload = TaskCreateSchema().load(request.get_json() or {})
    data, status = TaskController.create_task(payload)
    return jsonify(data), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    payload = TaskUpdateSchema().load(request.get_json() or {})
    return jsonify(TaskController.update_task(task_id, payload)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return jsonify(TaskController.delete_task(task_id)), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    return jsonify(TaskController.search_tasks(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(TaskController.stats()), 200
