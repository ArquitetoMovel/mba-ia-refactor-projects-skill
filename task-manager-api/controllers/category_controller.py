from sqlalchemy import func

from config.settings import Settings
from database import db, transaction
from middlewares.error_handler import AppError
from models.category import Category
from models.task import Task


class CategoryController:
    @staticmethod
    def list_categories():
        rows = (
            db.session.query(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.id)
            .all()
        )
        return [category.to_dict(task_count=count) for category, count in rows]

    @staticmethod
    def create_category(payload):
        category = Category(
            name=payload['name'],
            description=payload.get('description', ''),
            color=payload.get('color', Settings.DEFAULT_COLOR),
        )
        with transaction():
            db.session.add(category)
        return category.to_dict(), 201

    @staticmethod
    def update_category(category_id, payload):
        with transaction():
            category = db.session.get(Category, category_id)
            if not category:
                raise AppError('Categoria não encontrada', 404)

            if 'name' in payload:
                category.name = payload['name']
            if 'description' in payload:
                category.description = payload['description']
            if 'color' in payload:
                category.color = payload['color']

        return category.to_dict()

    @staticmethod
    def delete_category(category_id):
        with transaction():
            category = db.session.get(Category, category_id)
            if not category:
                raise AppError('Categoria não encontrada', 404)
            Task.query.filter_by(category_id=category_id).update(
                {Task.category_id: None}, synchronize_session=False
            )
            db.session.delete(category)
        return {'message': 'Categoria deletada'}
