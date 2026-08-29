"""Map domain errors to JSON HTTP responses."""

from __future__ import annotations

import logging
import sqlite3

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from src.services.errors import DomainError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(exc: DomainError):
        payload = {"erro": exc.message, "sucesso": False}
        return jsonify(payload), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        payload = {"erro": exc.description, "sucesso": False}
        return jsonify(payload), exc.code or 500

    @app.errorhandler(sqlite3.IntegrityError)
    def handle_integrity_error(exc: sqlite3.IntegrityError):
        logger.warning("Database integrity error: %s", exc)
        return jsonify({"erro": "Conflito de dados", "sucesso": False}), 409

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
