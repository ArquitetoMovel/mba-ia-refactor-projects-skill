from database import db
from middlewares.error_handler import AppError
from models.category import Category
from models.task import Task


class CategoryController:
    @staticmethod
    def list_categories():
        categories = Category.query.all()
        return [
            category.to_dict(task_count=Task.query.filter_by(category_id=category.id).count())
            for category in categories
        ]

    @staticmethod
    def create_category(payload):
        category = Category(
            name=payload['name'],
            description=payload.get('description', ''),
            color=payload.get('color', '#000000'),
        )
        db.session.add(category)
        db.session.commit()
        return category.to_dict(), 201

    @staticmethod
    def update_category(category_id, payload):
        category = Category.query.get(category_id)
        if not category:
            raise AppError('Categoria não encontrada', 404)

        if 'name' in payload:
            category.name = payload['name']
        if 'description' in payload:
            category.description = payload['description']
        if 'color' in payload:
            category.color = payload['color']

        db.session.commit()
        return category.to_dict()

    @staticmethod
    def delete_category(category_id):
        category = Category.query.get(category_id)
        if not category:
            raise AppError('Categoria não encontrada', 404)

        db.session.delete(category)
        db.session.commit()
        return {'message': 'Categoria deletada'}
