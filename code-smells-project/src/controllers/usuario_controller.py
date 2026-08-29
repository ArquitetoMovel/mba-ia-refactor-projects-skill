"""Usuario HTTP controllers."""

from __future__ import annotations

from flask import g, jsonify, request

from src.controllers.deps import auth_service, usuario_service
from src.middlewares.auth import require_auth, require_roles
from src.services.errors import ForbiddenError


@require_roles("admin")
def listar_usuarios():
    usuarios = usuario_service().listar()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


@require_auth
def buscar_usuario(id: int):
    usuario_atual = g.current_user
    if usuario_atual["tipo"] != "admin" and usuario_atual["id"] != id:
        raise ForbiddenError("Você só pode consultar o próprio usuário")
    usuario = usuario_service().buscar_por_id(id)
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    usuario_id = usuario_service().criar(request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    usuario = usuario_service().login(request.get_json(silent=True))
    usuario["token"] = auth_service().criar_token(usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
