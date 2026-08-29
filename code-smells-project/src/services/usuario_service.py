"""Usuario and authentication business rules."""

from __future__ import annotations

import logging
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from src.models.usuario_model import UsuarioModel
from src.schemas.payloads import LoginPayload, SchemaError, UsuarioPayload
from src.services.errors import DomainError, NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, model: UsuarioModel) -> None:
        self._model = model

    def listar(self) -> list[dict[str, Any]]:
        return self._model.listar_todos()

    def buscar_por_id(self, usuario_id: int) -> dict[str, Any]:
        usuario = self._model.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados: dict[str, Any] | None) -> int:
        try:
            payload = UsuarioPayload.from_mapping(dados)
        except SchemaError as exc:
            raise DomainError(str(exc)) from exc

        try:
            usuario_id = self._model.criar(
                payload.nome,
                payload.email,
                generate_password_hash(payload.senha),
            )
            self._model.commit()
        except Exception:
            self._model.rollback()
            raise
        logger.info("Usuário criado: %s", payload.email)
        return usuario_id

    def login(self, dados: dict[str, Any] | None) -> dict[str, Any]:
        try:
            payload = LoginPayload.from_mapping(dados)
        except SchemaError as exc:
            raise DomainError(str(exc)) from exc

        usuario = self._model.buscar_por_email(payload.email)
        if not usuario or not check_password_hash(usuario["senha"], payload.senha):
            logger.info("Login falhou: %s", payload.email)
            raise UnauthorizedError("Email ou senha inválidos")

        logger.info("Login bem-sucedido: %s", payload.email)
        return UsuarioModel.para_login(usuario)
