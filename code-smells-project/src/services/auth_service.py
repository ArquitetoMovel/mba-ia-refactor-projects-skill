"""Signed, expiring authentication tokens."""

from __future__ import annotations

from itsdangerous import BadData, URLSafeTimedSerializer

from src.models.usuario_model import UsuarioModel
from src.services.errors import UnauthorizedError


class AuthService:
    def __init__(
        self,
        model: UsuarioModel,
        secret_key: str,
        max_age_seconds: int,
    ) -> None:
        self._model = model
        self._serializer = URLSafeTimedSerializer(secret_key, salt="loja-auth")
        self._max_age_seconds = max_age_seconds

    def criar_token(self, usuario_id: int) -> str:
        return self._serializer.dumps({"usuario_id": usuario_id})

    def usuario_do_token(self, token: str) -> dict[str, object]:
        try:
            payload = self._serializer.loads(token, max_age=self._max_age_seconds)
        except BadData as exc:
            raise UnauthorizedError("Token inválido ou expirado") from exc

        if not isinstance(payload, dict):
            raise UnauthorizedError("Token inválido ou expirado")
        usuario_id = payload.get("usuario_id")
        if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
            raise UnauthorizedError("Token inválido ou expirado")

        usuario = self._model.buscar_por_id(usuario_id)
        if not usuario:
            raise UnauthorizedError("Usuário não encontrado")
        return usuario
