import logging
import secrets

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from views import category_bp, health_bp, report_bp, task_bp, user_bp

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)


def _configure_secret(app):
    secret = app.config.get('SECRET_KEY')
    if secret and secret not in Settings.WEAK_SECRETS:
        return
    if Settings.DEBUG or app.config.get('TESTING'):
        app.config['SECRET_KEY'] = secrets.token_urlsafe(48)
        logger.warning(
            'SECRET_KEY ausente ou fraca; usando chave efemera gerada em memoria '
            '(aprovada apenas para debug/tests). Tokens serao invalidados no restart.'
        )
        return
    raise RuntimeError(
        'SECRET_KEY forte e obrigatoria em producao. Defina a variavel de ambiente '
        "SECRET_KEY (ex.: python -c \"import secrets; print(secrets.token_urlsafe(48))\")."
    )


def create_app(config=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Settings.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = Settings.SECRET_KEY

    if config:
        app.config.update(config)

    _configure_secret(app)

    CORS(app)
    db.init_app(app)
    register_error_handlers(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
