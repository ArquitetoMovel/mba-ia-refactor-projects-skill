from datetime import timedelta

from sqlalchemy import case, func

from config.settings import Settings
from controllers.task_controller import TaskController
from database import db
from middlewares.error_handler import AppError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage
from utils.time import as_utc, utcnow


class ReportController:
    @staticmethod
    def summary():
        now = utcnow()
        counts = TaskController.status_counts()

        priorities = dict(
            db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
        )
        priority_labels = {
            1: 'critical',
            2: 'high',
            3: 'medium',
            4: 'low',
            5: 'minimal',
        }

        overdue_tasks = Task.query.filter(*TaskController._overdue_filter()).all()
        overdue_list = [
            {
                'id': task.id,
                'title': task.title,
                'due_date': as_utc(task.due_date).isoformat(),
                'days_overdue': (now - as_utc(task.due_date)).days,
            }
            for task in overdue_tasks
        ]

        seven_days_ago = now - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == Settings.STATUS_DONE,
            Task.updated_at >= seven_days_ago,
        ).count()

        productivity = (
            db.session.query(
                User.id,
                User.name,
                func.count(Task.id),
                func.sum(case((Task.status == Settings.STATUS_DONE, 1), else_=0)),
            )
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id, User.name)
            .order_by(User.id)
            .all()
        )
        user_stats = [
            {
                'user_id': user_id,
                'user_name': user_name,
                'total_tasks': total,
                'completed_tasks': completed or 0,
                'completion_rate': calculate_percentage(completed or 0, total),
            }
            for user_id, user_name, total, completed in productivity
        ]

        return {
            'generated_at': now.isoformat(),
            'overview': {
                'total_tasks': counts['total'],
                'total_users': User.query.count(),
                'total_categories': Category.query.count(),
            },
            'tasks_by_status': {
                Settings.STATUS_PENDING: counts[Settings.STATUS_PENDING],
                Settings.STATUS_IN_PROGRESS: counts[Settings.STATUS_IN_PROGRESS],
                Settings.STATUS_DONE: counts[Settings.STATUS_DONE],
                Settings.STATUS_CANCELLED: counts[Settings.STATUS_CANCELLED],
            },
            'tasks_by_priority': {
                label: priorities.get(value, 0) for value, label in priority_labels.items()
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    @classmethod
    def user_report(cls, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        rows = dict(
            db.session.query(Task.status, func.count(Task.id))
            .filter(Task.user_id == user_id)
            .group_by(Task.status)
            .all()
        )
        total = sum(rows.values())
        overdue = Task.query.filter(Task.user_id == user_id, *TaskController._overdue_filter()).count()
        high_priority = Task.query.filter(
            Task.user_id == user_id,
            Task.priority <= Settings.HIGH_PRIORITY_MAX,
        ).count()

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': rows.get(Settings.STATUS_DONE, 0),
                'pending': rows.get(Settings.STATUS_PENDING, 0),
                'in_progress': rows.get(Settings.STATUS_IN_PROGRESS, 0),
                'cancelled': rows.get(Settings.STATUS_CANCELLED, 0),
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(rows.get(Settings.STATUS_DONE, 0), total),
            },
        }
