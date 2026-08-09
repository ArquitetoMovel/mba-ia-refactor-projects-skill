from database import db
from middlewares.error_handler import AppError
from models.task import Task
from models.user import User


class UserController:
    @staticmethod
    def list_users():
        users = User.query.all()
        return [user.to_dict(include_task_count=True) for user in users]

    @staticmethod
    def get_user(user_id):
        user = User.query.get(user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
        return data

    @staticmethod
    def create_user(payload):
        existing = User.query.filter_by(email=payload['email']).first()
        if existing:
            raise AppError('Email já cadastrado', 409)

        user = User(
            name=payload['name'],
            email=payload['email'],
            role=payload.get('role', 'user'),
        )
        user.set_password(payload['password'])

        db.session.add(user)
        db.session.commit()
        return user.to_dict(), 201

    @staticmethod
    def update_user(user_id, payload):
        user = User.query.get(user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        if 'email' in payload:
            existing = User.query.filter_by(email=payload['email']).first()
            if existing and existing.id != user_id:
                raise AppError('Email já cadastrado', 409)
            user.email = payload['email']

        if 'name' in payload:
            user.name = payload['name']
        if 'password' in payload:
            user.set_password(payload['password'])
        if 'role' in payload:
            user.role = payload['role']
        if 'active' in payload:
            user.active = payload['active']

        db.session.commit()
        return user.to_dict()

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        Task.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        return {'message': 'Usuário deletado com sucesso'}

    @staticmethod
    def get_user_tasks(user_id):
        user = User.query.get(user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        tasks = Task.query.filter_by(user_id=user_id).all()
        return [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'overdue': task.is_overdue(),
            }
            for task in tasks
        ]
