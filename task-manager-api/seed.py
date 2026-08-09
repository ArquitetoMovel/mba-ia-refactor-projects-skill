"""Script para popular o banco com dados iniciais."""
from datetime import datetime, timedelta, timezone

from app import app
from database import db
from models.category import Category
from models.task import Task
from models.user import User


def seed_data():
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = [
            ('João Silva', 'joao@email.com', '12345678', 'admin'),
            ('Maria Santos', 'maria@email.com', 'abcd1234', 'user'),
            ('Pedro Oliveira', 'pedro@email.com', 'pass1234', 'manager'),
        ]
        user_objs = []
        for name, email, password, role in users:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            user_objs.append(user)

        db.session.commit()
        u1, u2, u3 = user_objs

        categories = [
            ('Backend', 'Tarefas de backend', '#3498db'),
            ('Frontend', 'Tarefas de frontend', '#2ecc71'),
            ('DevOps', 'Tarefas de infraestrutura', '#e74c3c'),
            ('Bug', 'Correção de bugs', '#e67e22'),
        ]
        category_objs = []
        for name, description, color in categories:
            category = Category(name=name, description=description, color=color)
            db.session.add(category)
            category_objs.append(category)

        db.session.commit()
        c1, c2, c3, c4 = category_objs

        now = datetime.now(timezone.utc)
        tasks_data = [
            {
                'title': 'Implementar autenticação JWT',
                'description': 'Adicionar autenticação real com JWT',
                'status': 'pending',
                'priority': 1,
                'user_id': u1.id,
                'category_id': c1.id,
                'due_date': now - timedelta(days=3),
            },
            {
                'title': 'Criar tela de login',
                'description': 'Tela de login responsiva',
                'status': 'in_progress',
                'priority': 2,
                'user_id': u2.id,
                'category_id': c2.id,
                'due_date': now + timedelta(days=5),
            },
            {
                'title': 'Configurar CI/CD',
                'description': 'Pipeline com GitHub Actions',
                'status': 'done',
                'priority': 2,
                'user_id': u3.id,
                'category_id': c3.id,
                'tags': 'devops,ci,github',
            },
            {
                'title': 'Corrigir bug no filtro de busca',
                'description': 'Filtro não funciona com caracteres especiais',
                'status': 'pending',
                'priority': 1,
                'user_id': u1.id,
                'category_id': c4.id,
                'due_date': now - timedelta(days=1),
            },
            {
                'title': 'Adicionar paginação na API',
                'description': 'Endpoints retornam todos os registros',
                'status': 'pending',
                'priority': 3,
                'user_id': u1.id,
                'category_id': c1.id,
                'due_date': now + timedelta(days=10),
            },
            {
                'title': 'Escrever testes unitários',
                'description': 'Cobertura mínima de 80%',
                'status': 'pending',
                'priority': 2,
                'user_id': u2.id,
                'category_id': c1.id,
            },
            {
                'title': 'Documentar API com Swagger',
                'description': 'Gerar documentação automática',
                'status': 'cancelled',
                'priority': 4,
                'user_id': u3.id,
                'category_id': c1.id,
            },
            {
                'title': 'Refatorar models',
                'description': 'Melhorar organização dos models',
                'status': 'in_progress',
                'priority': 3,
                'user_id': u2.id,
                'category_id': c1.id,
                'tags': 'refactor,tech-debt',
            },
            {
                'title': 'Configurar monitoramento',
                'description': 'Prometheus + Grafana',
                'status': 'pending',
                'priority': 4,
                'user_id': u3.id,
                'category_id': c3.id,
                'due_date': now + timedelta(days=20),
            },
            {
                'title': 'Melhorar validações de input',
                'description': 'Usar marshmallow ou pydantic',
                'status': 'pending',
                'priority': 3,
                'user_id': u1.id,
                'category_id': c1.id,
                'tags': 'improvement,validation',
            },
        ]

        for data in tasks_data:
            task = Task(**data)
            db.session.add(task)

        db.session.commit()
        print('Seed concluído com sucesso!')
        print(f'  {User.query.count()} usuários')
        print(f'  {Category.query.count()} categorias')
        print(f'  {Task.query.count()} tasks')


if __name__ == '__main__':
    seed_data()
