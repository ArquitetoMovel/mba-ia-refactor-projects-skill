"""Pedido business rules: stock, totals, status transitions."""

from __future__ import annotations

from typing import Any

from src.domain.pedido import StatusPedido, transicao_permitida
from src.models.pedido_model import PedidoModel
from src.schemas.payloads import PedidoPayload, SchemaError, StatusPedidoPayload
from src.services.errors import DomainError, NotFoundError
from src.services.notificacao_service import NotificacaoService


class PedidoService:
    def __init__(
        self,
        model: PedidoModel,
        notificacoes: NotificacaoService | None = None,
    ) -> None:
        self._model = model
        self._notificacoes = notificacoes or NotificacaoService()

    def listar_todos(self) -> list[dict[str, Any]]:
        return self._model.listar_todos()

    def listar_por_usuario(self, usuario_id: int) -> list[dict[str, Any]]:
        return self._model.listar_por_usuario(usuario_id)

    def criar(self, dados: dict[str, Any] | None) -> dict[str, Any]:
        try:
            payload = PedidoPayload.from_mapping(dados)
        except SchemaError as exc:
            raise DomainError(str(exc)) from exc

        try:
            self._model.iniciar_transacao()
            if not self._model.usuario_existe(payload.usuario_id):
                raise DomainError("Usuário não encontrado")

            linhas, total = self._preparar_linhas(payload)
            pedido_id = self._model.criar(payload.usuario_id, total)
            for produto_id, quantidade, preco in linhas:
                if not self._model.reservar_estoque(produto_id, quantidade):
                    raise DomainError("Estoque insuficiente para o produto solicitado")
                self._model.adicionar_item(pedido_id, produto_id, quantidade, preco)
            self._model.commit()
        except Exception:
            self._model.rollback()
            raise

        resultado = {"pedido_id": pedido_id, "total": total}
        self._notificacoes.pedido_criado(pedido_id, payload.usuario_id)
        return resultado

    def atualizar_status(self, pedido_id: int, dados: dict[str, Any] | None) -> None:
        try:
            novo_status = StatusPedidoPayload.from_mapping(dados).status
        except SchemaError as exc:
            raise DomainError(str(exc)) from exc

        try:
            self._model.iniciar_transacao()
            pedido = self._model.buscar_status(pedido_id)
            if pedido is None:
                raise NotFoundError("Pedido não encontrado")
            if not transicao_permitida(pedido["status"], novo_status):
                raise DomainError("Transição de status inválida")
            if not self._model.atualizar_status(pedido_id, novo_status):
                raise NotFoundError("Pedido não encontrado")
            if novo_status == StatusPedido.CANCELADO.value:
                for item in self._model.itens_para_reposicao(pedido_id):
                    self._model.restaurar_estoque(item["produto_id"], item["quantidade"])
            self._model.commit()
        except Exception:
            self._model.rollback()
            raise
        self._notificacoes.status_atualizado(pedido_id, novo_status)

    def _preparar_linhas(
        self,
        payload: PedidoPayload,
    ) -> tuple[list[tuple[int, int, float]], float]:
        quantidades: dict[int, int] = {}
        for item in payload.itens:
            quantidades[item.produto_id] = quantidades.get(item.produto_id, 0) + item.quantidade

        linhas: list[tuple[int, int, float]] = []
        total = 0.0
        for produto_id, quantidade in quantidades.items():
            produto = self._model.produto_para_pedido(produto_id)
            if produto is None:
                raise DomainError(f"Produto {produto_id} não encontrado")
            if produto["estoque"] < quantidade:
                raise DomainError(f"Estoque insuficiente para {produto['nome']}")
            preco = float(produto["preco"])
            total += preco * quantidade
            linhas.append((produto_id, quantidade, preco))
        return linhas, total
