"""Produto HTTP controllers — thin request/response adapters."""

from __future__ import annotations

from flask import jsonify, request

from src.controllers.deps import produto_service
from src.middlewares.auth import require_roles
from src.schemas.payloads import BuscaProdutosQuery, SchemaError
from src.services.errors import DomainError


def listar_produtos():
    produtos = produto_service().listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id: int):
    produto = produto_service().buscar_por_id(id)
    return jsonify({"dados": produto, "sucesso": True}), 200


@require_roles("admin")
def criar_produto():
    produto_id = produto_service().criar(request.get_json(silent=True))
    return jsonify(
        {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}
    ), 201


@require_roles("admin")
def atualizar_produto(id: int):
    produto_service().atualizar(id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@require_roles("admin")
def deletar_produto(id: int):
    produto_service().deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    try:
        query = BuscaProdutosQuery.from_mapping(request.args)
    except SchemaError as exc:
        raise DomainError(str(exc)) from exc

    resultados = produto_service().buscar(
        query.termo,
        query.categoria,
        query.preco_min,
        query.preco_max,
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
