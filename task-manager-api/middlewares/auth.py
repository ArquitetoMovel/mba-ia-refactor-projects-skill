from functools import wraps

from controllers.auth_controller import AuthController
from database import db
from flask import g, request
from middlewares.error_handler import AppError
from models.user import User


def _extract_bearer_token():
    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        raise AppError('Token de autenticacao ausente. Envie o header Authorization: Bearer <token>', 401)
    return token.strip()


def current_user():
    return getattr(g, 'current_user', None)


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = AuthController.verify_token(_extract_bearer_token())
        user = db.session.get(User, user_id)
        if not user or not user.active:
            raise AppError('Sessao invalida ou encerrada', 401)
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @token_required
        def wrapper(*args, **kwargs):
            if g.current_user.role not in roles:
                raise AppError('Permissao insuficiente', 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def ensure_self_or_admin(user_id, actor):
    if actor.id != user_id and not actor.is_admin():
        raise AppError('Acesso negado: acao restrita ao proprio usuario ou admin', 403)
