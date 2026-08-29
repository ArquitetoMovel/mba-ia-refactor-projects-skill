from sqlalchemy import func
from sqlalchemy.orm import joinedload

from config.settings import Settings
from database import db, transaction
from middlewares.error_handler import AppError
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import notification_service
from utils.helpers import serialize_tags, to_datetime
from utils.time import utcnow


class TaskController:
    @staticmethod
    def _query():
        return Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category),
        )

    @staticmethod
    def list_tasks(page=1, per_page=Settings.DEFAULT_PER_PAGE):
        pagination = TaskController._query().order_by(Task.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            'items': [task.to_dict(include_relations=True) for task in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }

    @staticmethod
    def get_task(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            raise AppError('Task não encontrada', 404)
        return task.to_dict(include_relations=True)

    @staticmethod
    def _ensure_user(user_id):
        if user_id is None:
            return
        if not db.session.get(User, user_id):
            raise AppError('Usuário não encontrado', 404)

    @staticmethod
    def _ensure_category(category_id):
        if category_id is None:
            return
        if not db.session.get(Category, category_id):
            raise AppError('Categoria não encontrada', 404)

    @classmethod
    def create_task(cls, payload):
        cls._ensure_user(payload.get('user_id'))
        cls._ensure_category(payload.get('category_id'))

        task = Task(
            title=payload['title'],
            description=payload.get('description', ''),
            status=payload.get('status', Settings.DEFAULT_STATUS),
            priority=payload.get('priority', Settings.DEFAULT_PRIORITY),
            user_id=payload.get('user_id'),
            category_id=payload.get('category_id'),
            due_date=to_datetime(payload.get('due_date')),
            tags=serialize_tags(payload.get('tags')),
        )

        with transaction():
            db.session.add(task)

        if task.user_id and task.user:
            notification_service.notify_task_assigned(task.user, task)

        return task.to_dict(), 201

    @classmethod
    def update_task(cls, task_id, payload):
        with transaction():
            task = db.session.get(Task, task_id)
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

        return task.to_dict()

    @staticmethod
    def delete_task(task_id):
        with transaction():
            task = db.session.get(Task, task_id)
            if not task:
                raise AppError('Task não encontrada', 404)
            db.session.delete(task)
        return {'message': 'Task deletada com sucesso'}

    @staticmethod
    def search_tasks(query='', status='', priority=None, user_id=None, page=1,
                     per_page=Settings.DEFAULT_PER_PAGE):
        q = TaskController._query()

        if query:
            like = f'%{query}%'
            q = q.filter(db.or_(Task.title.like(like), Task.description.like(like)))
        if status:
            q = q.filter(Task.status == status)
        if priority is not None:
            q = q.filter(Task.priority == priority)
        if user_id is not None:
            q = q.filter(Task.user_id == user_id)

        pagination = q.order_by(Task.id).paginate(page=page, per_page=per_page, error_out=False)
        return {
            'items': [task.to_dict(include_relations=True) for task in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }

    @staticmethod
    def _overdue_filter():
        return (
            Task.due_date.isnot(None),
            Task.due_date < utcnow(),
            Task.status.notin_(Settings.NON_OVERDUE_STATUSES),
        )

    @classmethod
    def status_counts(cls):
        rows = dict(
            db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
        )
        counts = {status: rows.get(status, 0) for status in Settings.VALID_STATUSES}
        counts['total'] = sum(rows.values())
        return counts

    @classmethod
    def stats(cls):
        counts = cls.status_counts()
        total = counts['total']
        overdue_count = Task.query.filter(*cls._overdue_filter()).count()

        return {
            'total': total,
            'pending': counts[Settings.STATUS_PENDING],
            'in_progress': counts[Settings.STATUS_IN_PROGRESS],
            'done': counts[Settings.STATUS_DONE],
            'cancelled': counts[Settings.STATUS_CANCELLED],
            'overdue': overdue_count,
            'completion_rate': round((counts[Settings.STATUS_DONE] / total) * 100, 2) if total > 0 else 0,
        }
