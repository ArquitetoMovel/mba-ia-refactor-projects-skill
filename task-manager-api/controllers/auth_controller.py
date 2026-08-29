from config.settings import Settings
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from middlewares.error_handler import AppError
from models.user import User
from utils.time import utcnow


class AuthController:
    @staticmethod
    def _serializer():
        return URLSafeTimedSerializer(current_app.secret_key, salt=Settings.AUTH_TOKEN_SALT)

    @classmethod
    def create_token(cls, user_id):
        return cls._serializer().dumps({'user_id': user_id, 'issued_at': utcnow().isoformat()})

    @classmethod
    def verify_token(cls, token):
        try:
            payload = cls._serializer().loads(token, max_age=Settings.TOKEN_MAX_AGE_SECONDS)
        except SignatureExpired as exc:
            raise AppError('Token expirado', 401) from exc
        except BadSignature as exc:
            raise AppError('Token inválido', 401) from exc
        user_id = payload.get('user_id')
        if user_id is None:
            raise AppError('Token inválido', 401)
        return user_id

    @classmethod
    def login(cls, email, password):
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise AppError('Credenciais inválidas', 401)
        if not user.active:
            raise AppError('Usuário inativo', 403)

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': cls.create_token(user.id),
        }
