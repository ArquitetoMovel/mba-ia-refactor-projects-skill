"""Sales report queries."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.domain.pedido import StatusPedido


class RelatorioModel:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def agregados_vendas(self) -> dict[str, Any]:
        row = self._db.execute(
            "SELECT COUNT(*) AS total_pedidos, COALESCE(SUM(total), 0) AS faturamento, "
            "SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pendentes, "
            "SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS aprovados, "
            "SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS cancelados "
            "FROM pedidos",
            (
                StatusPedido.PENDENTE.value,
                StatusPedido.APROVADO.value,
                StatusPedido.CANCELADO.value,
            ),
        ).fetchone()
        return {
            "total_pedidos": row["total_pedidos"],
            "faturamento": float(row["faturamento"]),
            "pendentes": row["pendentes"] or 0,
            "aprovados": row["aprovados"] or 0,
            "cancelados": row["cancelados"] or 0,
        }
