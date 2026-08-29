"""Pedido HTTP controllers."""

from __future__ import annotations

from flask import g, jsonify, request

from src.controllers.deps import pedido_service
from src.middlewares.auth import require_auth, require_roles
from src.services.errors import ForbiddenError


@require_auth
def criar_pedido():
    dados = request.get_json(silent=True)
    usuario_atual = g.current_user
    if usuario_atual["tipo"] != "admin" and isinstance(dados, dict):
        try:
            usuario_id = int(dados.get("usuario_id"))
        except (TypeError, ValueError):
            usuario_id = None
        if usuario_id != usuario_atual["id"]:
            raise ForbiddenError("Você só pode criar pedidos para o próprio usuário")

    resultado = pedido_service().criar(dados)
    return jsonify(
        {
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }
    ), 201


@require_auth
def listar_pedidos_usuario(usuario_id: int):
    usuario_atual = g.current_user
    if usuario_atual["tipo"] != "admin" and usuario_atual["id"] != usuario_id:
        raise ForbiddenError("Você só pode consultar os próprios pedidos")
    pedidos = pedido_service().listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@require_roles("admin")
def listar_todos_pedidos():
    pedidos = pedido_service().listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@require_roles("admin")
def atualizar_status_pedido(pedido_id: int):
    pedido_service().atualizar_status(pedido_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
