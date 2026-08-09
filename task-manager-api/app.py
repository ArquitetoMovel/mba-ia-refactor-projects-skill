import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from views import category_bp, health_bp, report_bp, task_bp, user_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)


def create_app(config=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Settings.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = Settings.SECRET_KEY

    if config:
        app.config.update(config)

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
