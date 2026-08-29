"""Order status policy."""

from __future__ import annotations

from enum import StrEnum


class StatusPedido(StrEnum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


STATUS_PEDIDO_VALIDOS = tuple(status.value for status in StatusPedido)

TRANSICOES_PEDIDO: dict[str, frozenset[str]] = {
    StatusPedido.PENDENTE.value: frozenset(
        {StatusPedido.PENDENTE.value, StatusPedido.APROVADO.value, StatusPedido.CANCELADO.value}
    ),
    StatusPedido.APROVADO.value: frozenset(
        {StatusPedido.APROVADO.value, StatusPedido.ENVIADO.value, StatusPedido.CANCELADO.value}
    ),
    StatusPedido.ENVIADO.value: frozenset(
        {StatusPedido.ENVIADO.value, StatusPedido.ENTREGUE.value}
    ),
    StatusPedido.ENTREGUE.value: frozenset({StatusPedido.ENTREGUE.value}),
    StatusPedido.CANCELADO.value: frozenset({StatusPedido.CANCELADO.value}),
}


def transicao_permitida(status_atual: str, novo_status: str) -> bool:
    """Return whether an order can move to ``novo_status``."""
    return novo_status in TRANSICOES_PEDIDO.get(status_atual, frozenset())
