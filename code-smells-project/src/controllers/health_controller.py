"""Health and protected admin controllers."""

from __future__ import annotations

import logging

from flask import jsonify, request

from src.config.settings import project_version
from src.controllers.deps import health_service

logger = logging.getLogger(__name__)


def health_check():
    return jsonify(health_service().status()), 200


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": project_version(),
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


def reset_database():
    health_service().reset(request.headers.get("X-Admin-Token", ""))
    logger.warning("Banco de dados resetado via admin")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
