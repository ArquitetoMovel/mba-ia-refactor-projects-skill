"""Application health and administrative data operations."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.config.settings import Settings, project_version
from src.db.database import reset_all_data
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.errors import ForbiddenError


class HealthService:
    def __init__(self, db: sqlite3.Connection, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    def status(self) -> dict[str, Any]:
        self._db.execute("SELECT 1")
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": ProdutoModel(self._db).contar(),
                "usuarios": UsuarioModel(self._db).contar(),
                "pedidos": PedidoModel(self._db).contar(),
            },
            "versao": project_version(),
            "ambiente": self._settings.ambiente,
        }

    def reset(self, admin_token: str) -> None:
        if not self._settings.admin_token or admin_token != self._settings.admin_token:
            raise ForbiddenError("Admin token inválido ou não configurado")
        try:
            reset_all_data(self._db, self._settings.seed_users)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
