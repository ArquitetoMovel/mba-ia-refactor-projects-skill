"""Produto business rules and validation."""

from __future__ import annotations

import logging
from typing import Any

from src.models.produto_model import ProdutoModel
from src.schemas.payloads import ProdutoPayload, SchemaError
from src.services.errors import DomainError, NotFoundError

logger = logging.getLogger(__name__)


class ProdutoService:
    def __init__(self, model: ProdutoModel) -> None:
        self._model = model

    def listar(self) -> list[dict[str, Any]]:
        produtos = self._model.listar_todos()
        logger.info("Listando %s produtos", len(produtos))
        return produtos

    def buscar_por_id(self, produto_id: int) -> dict[str, Any]:
        produto = self._model.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado")
        return produto

    def criar(self, dados: dict[str, Any] | None) -> int:
        payload = self._validar_payload(dados)
        try:
            produto_id = self._model.criar(
                payload.nome,
                payload.descricao,
                payload.preco,
                payload.estoque,
                payload.categoria,
            )
            self._model.commit()
        except Exception:
            self._model.rollback()
            raise
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id: int, dados: dict[str, Any] | None) -> None:
        if not self._model.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        payload = self._validar_payload(dados)
        try:
            self._model.atualizar(
                produto_id,
                payload.nome,
                payload.descricao,
                payload.preco,
                payload.estoque,
                payload.categoria,
            )
            self._model.commit()
        except Exception:
            self._model.rollback()
            raise

    def deletar(self, produto_id: int) -> None:
        if not self._model.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        try:
            self._model.deletar(produto_id)
            self._model.commit()
        except Exception:
            self._model.rollback()
            raise
        logger.info("Produto %s deletado", produto_id)

    def buscar(
        self,
        termo: str = "",
        categoria: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> list[dict[str, Any]]:
        return self._model.buscar(termo, categoria, preco_min, preco_max)

    def _validar_payload(self, dados: dict[str, Any] | None) -> ProdutoPayload:
        try:
            return ProdutoPayload.from_mapping(dados)
        except SchemaError as exc:
            raise DomainError(str(exc)) from exc
