from datetime import datetime, timezone

from sqlalchemy.orm import joinedload

from database import db
from middlewares.error_handler import AppError
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import notification_service
from utils.helpers import serialize_tags, to_datetime


class TaskController:
    @staticmethod
    def list_tasks():
        tasks = Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category),
        ).all()
        return [task.to_dict(include_relations=True) for task in tasks]

    @staticmethod
    def get_task(task_id):
        task = Task.query.get(task_id)
        if not task:
            raise AppError('Task não encontrada', 404)
        return task.to_dict()

    @staticmethod
    def _ensure_user(user_id):
        if user_id is None:
            return
        if not User.query.get(user_id):
            raise AppError('Usuário não encontrado', 404)

    @staticmethod
    def _ensure_category(category_id):
        if category_id is None:
            return
        if not Category.query.get(category_id):
            raise AppError('Categoria não encontrada', 404)

    @classmethod
    def create_task(cls, payload):
        cls._ensure_user(payload.get('user_id'))
        cls._ensure_category(payload.get('category_id'))

        task = Task(
            title=payload['title'],
            description=payload.get('description', ''),
            status=payload.get('status', 'pending'),
            priority=payload.get('priority', 3),
            user_id=payload.get('user_id'),
            category_id=payload.get('category_id'),
            due_date=to_datetime(payload.get('due_date')),
            tags=serialize_tags(payload.get('tags')),
        )

        db.session.add(task)
        db.session.commit()

        if task.user_id and task.user:
            notification_service.notify_task_assigned(task.user, task)

        return task.to_dict(), 201

    @classmethod
    def update_task(cls, task_id, payload):
        task = Task.query.get(task_id)
        if not task:
            raise AppError('Task não encontrada', 404)

        if 'user_id' in payload:
            cls._ensure_user(payload['user_id'])
            task.user_id = payload['user_id']
        if 'category_id' in payload:
            cls._ensure_category(payload['category_id'])
            task.category_id = payload['category_id']
        if 'title' in payload:
            task.title = payload['title']
        if 'description' in payload:
            task.description = payload['description']
        if 'status' in payload:
            task.status = payload['status']
        if 'priority' in payload:
            task.priority = payload['priority']
        if 'due_date' in payload:
            task.due_date = to_datetime(payload['due_date'])
        if 'tags' in payload:
            task.tags = serialize_tags(payload['tags'])

        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return task.to_dict()

    @staticmethod
    def delete_task(task_id):
        task = Task.query.get(task_id)
        if not task:
            raise AppError('Task não encontrada', 404)

        db.session.delete(task)
        db.session.commit()
        return {'message': 'Task deletada com sucesso'}

    @staticmethod
    def search_tasks(query='', status='', priority='', user_id=''):
        q = Task.query

        if query:
            like = f'%{query}%'
            q = q.filter(db.or_(Task.title.like(like), Task.description.like(like)))
        if status:
            q = q.filter(Task.status == status)
        if priority:
            q = q.filter(Task.priority == int(priority))
        if user_id:
            q = q.filter(Task.user_id == int(user_id))

        return [task.to_dict() for task in q.all()]

    @staticmethod
    def stats():
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()
        overdue_count = sum(1 for task in Task.query.all() if task.is_overdue())

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }
