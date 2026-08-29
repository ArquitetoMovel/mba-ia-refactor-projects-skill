"""HTTP authentication and authorization decorators."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import g, request

from src.controllers.deps import auth_service
from src.services.errors import ForbiddenError, UnauthorizedError


def _authenticate() -> dict[str, object]:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Autenticação Bearer obrigatória")

    usuario = auth_service().usuario_do_token(token)
    g.current_user = usuario
    return usuario


def require_auth(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        _authenticate()
        return view(*args, **kwargs)

    return wrapped


def require_roles(*roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any):
            usuario = _authenticate()
            if usuario.get("tipo") not in roles:
                raise ForbiddenError("Permissão insuficiente")
            return view(*args, **kwargs)

        return wrapped

    return decorator
