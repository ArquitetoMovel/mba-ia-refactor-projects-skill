from config.settings import Settings
from controllers.user_authz import ensure_can_modify, ensure_can_view
from database import db, transaction
from middlewares.error_handler import AppError
from models.task import Task
from models.user import User
from sqlalchemy import func


class UserController:
    @staticmethod
    def list_users(page=1, per_page=Settings.DEFAULT_PER_PAGE):
        counts = dict(
            db.session.query(Task.user_id, func.count(Task.id))
            .group_by(Task.user_id)
            .all()
        )
        pagination = User.query.order_by(User.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            'items': [
                user.to_dict(task_count=counts.get(user.id, 0))
                for user in pagination.items
            ],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }

    @staticmethod
    def get_user(user_id, actor):
        ensure_can_view(user_id, actor)
        user = db.session.get(User, user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        data = user.to_dict()
        data['task_count'] = Task.query.filter_by(user_id=user_id).count()
        data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
        return data

    @staticmethod
    def create_user(payload):
        if User.query.filter_by(email=payload['email']).first():
            raise AppError('Email já cadastrado', 409)

        user = User(
            name=payload['name'],
            email=payload['email'],
            role=payload.get('role', Settings.DEFAULT_ROLE),
        )
        user.set_password(payload['password'])

        with transaction():
            db.session.add(user)
        return user.to_dict(), 201

    @staticmethod
    def update_user(user_id, payload, actor):
        ensure_can_modify(user_id, actor, changing_role='role' in payload)

        with transaction():
            user = db.session.get(User, user_id)
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

        return user.to_dict()

    @staticmethod
    def delete_user(user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise AppError('Usuário não encontrado', 404)

        with transaction():
            Task.query.filter_by(user_id=user_id).delete()
            db.session.delete(user)
        return {'message': 'Usuário deletado com sucesso'}

    @staticmethod
    def get_user_tasks(user_id, actor):
        ensure_can_view(user_id, actor)
        if not db.session.get(User, user_id):
            raise AppError('Usuário não encontrado', 404)

        tasks = Task.query.filter_by(user_id=user_id).all()
        return [task.to_dict() for task in tasks]
