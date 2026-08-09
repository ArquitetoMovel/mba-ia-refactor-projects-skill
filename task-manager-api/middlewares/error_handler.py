import logging

from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        messages = error.messages
        if isinstance(messages, dict):
            first = next(iter(messages.values()))
            message = first[0] if isinstance(first, list) else str(first)
        else:
            message = str(messages)
        return jsonify({'error': message}), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        logger.exception('Integrity error')
        return jsonify({'error': 'Conflito de dados'}), 409

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.exception('Internal server error')
        return jsonify({'error': 'Erro interno'}), 500
