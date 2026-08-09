from datetime import datetime, timedelta, timezone

from middlewares.error_handler import AppError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage


class ReportController:
    @staticmethod
    def summary():
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        priorities = {
            'critical': Task.query.filter_by(priority=1).count(),
            'high': Task.query.filter_by(priority=2).count(),
            'medium': Task.query.filter_by(priority=3).count(),
            'low': Task.query.filter_by(priority=4).count(),
            'minimal': Task.query.filter_by(priority=5).count(),
        }

        now = datetime.now(timezone.utc)
        overdue_list = []
        for task in Task.query.all():
            if task.is_overdue():
                due = task.due_date
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                overdue_list.append({
                    'id': task.id,
                    'title': task.title,
                    'due_date': due.isoformat(),
                    'days_overdue': (now - due).days,
                })

        seven_days_ago = now - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago,
        ).count()

        user_stats = []
        for user in User.query.all():
            user_tasks = Task.query.filter_by(user_id=user.id).all()
            total = len(user_tasks)
            completed = sum(1 for task in user_tasks if task.status == 'done')
            user_stats.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            })

        return {
            'generated_at': now.isoformat(),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': priorities,
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

    @staticmethod
    def user_report(user_id):
        user = User.query.get(user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        done = sum(1 for task in tasks if task.status == 'done')
        pending = sum(1 for task in tasks if task.status == 'pending')
        in_progress = sum(1 for task in tasks if task.status == 'in_progress')
        cancelled = sum(1 for task in tasks if task.status == 'cancelled')
        overdue = sum(1 for task in tasks if task.is_overdue())
        high_priority = sum(1 for task in tasks if task.priority <= 2)

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(done, total),
            },
        }
