"""Typed and reusable payload validation for application use cases."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.config.settings import CATEGORIAS_VALIDAS
from src.domain.pedido import STATUS_PEDIDO_VALIDOS


class SchemaError(ValueError):
    """Raised when an input mapping does not satisfy its DTO contract."""


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise SchemaError("Dados inválidos")
    return value


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise SchemaError(f"{label} inválido")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"{label} inválido") from exc
    if result <= 0:
        raise SchemaError(f"{label} deve ser positivo")
    return result


def _non_negative_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise SchemaError(f"{label} inválido")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"{label} inválido") from exc
    if result < 0:
        raise SchemaError(f"{label} não pode ser negativo")
    return result


def _non_negative_float(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise SchemaError(f"{label} inválido")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"{label} inválido") from exc
    if not math.isfinite(result) or result < 0:
        raise SchemaError(f"{label} inválido")
    return result


@dataclass(frozen=True)
class ProdutoPayload:
    nome: str
    descricao: str
    preco: float
    estoque: int
    categoria: str

    @classmethod
    def from_mapping(cls, value: Any) -> ProdutoPayload:
        data = _mapping(value)
        missing = next((field for field in ("nome", "preco", "estoque") if field not in data), None)
        if missing:
            labels = {"nome": "Nome", "preco": "Preço", "estoque": "Estoque"}
            raise SchemaError(f"{labels[missing]} é obrigatório")

        name = data["nome"]
        if not isinstance(name, str):
            raise SchemaError("Nome inválido")
        name = name.strip()
        if len(name) < 2:
            raise SchemaError("Nome muito curto")
        if len(name) > 200:
            raise SchemaError("Nome muito longo")

        description = data.get("descricao", "")
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise SchemaError("Descrição inválida")

        stock = _non_negative_int(data["estoque"], "Estoque")
        price = _non_negative_float(data["preco"], "Preço")
        category = data.get("categoria", "geral")
        if not isinstance(category, str) or category not in CATEGORIAS_VALIDAS:
            raise SchemaError(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")

        return cls(name, description, price, stock, category)


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class UsuarioPayload:
    nome: str
    email: str
    senha: str

    @classmethod
    def from_mapping(cls, value: Any) -> UsuarioPayload:
        data = _mapping(value)
        name = data.get("nome")
        email = data.get("email")
        password = data.get("senha")
        if not isinstance(name, str) or not name.strip():
            raise SchemaError("Nome é obrigatório")
        if not isinstance(email, str) or not email.strip():
            raise SchemaError("Email é obrigatório")
        if not EMAIL_PATTERN.fullmatch(email.strip()):
            raise SchemaError("Email inválido")
        if not isinstance(password, str) or not password:
            raise SchemaError("Senha é obrigatória")
        if len(password) < 8:
            raise SchemaError("Senha deve ter pelo menos 8 caracteres")
        return cls(name.strip(), email.strip().lower(), password)


@dataclass(frozen=True)
class LoginPayload:
    email: str
    senha: str

    @classmethod
    def from_mapping(cls, value: Any) -> LoginPayload:
        data = _mapping(value)
        email = data.get("email")
        password = data.get("senha")
        if not isinstance(email, str) or not email.strip():
            raise SchemaError("Email é obrigatório")
        if not isinstance(password, str) or not password:
            raise SchemaError("Senha é obrigatória")
        return cls(email.strip().lower(), password)


@dataclass(frozen=True)
class PedidoItemPayload:
    produto_id: int
    quantidade: int

    @classmethod
    def from_mapping(cls, value: Any) -> PedidoItemPayload:
        data = _mapping(value)
        return cls(
            _positive_int(data.get("produto_id"), "Produto ID"),
            _positive_int(data.get("quantidade"), "Quantidade"),
        )


@dataclass(frozen=True)
class PedidoPayload:
    usuario_id: int
    itens: tuple[PedidoItemPayload, ...]

    @classmethod
    def from_mapping(cls, value: Any) -> PedidoPayload:
        data = _mapping(value)
        usuario_id = _positive_int(data.get("usuario_id"), "Usuario ID")
        raw_items = data.get("itens")
        if not isinstance(raw_items, (list, tuple)) or not raw_items:
            raise SchemaError("Pedido deve ter pelo menos 1 item")
        return cls(usuario_id, tuple(PedidoItemPayload.from_mapping(item) for item in raw_items))


@dataclass(frozen=True)
class StatusPedidoPayload:
    status: str

    @classmethod
    def from_mapping(cls, value: Any) -> StatusPedidoPayload:
        data = _mapping(value)
        status = data.get("status")
        if not isinstance(status, str) or status not in STATUS_PEDIDO_VALIDOS:
            raise SchemaError("Status inválido")
        return cls(status)


@dataclass(frozen=True)
class BuscaProdutosQuery:
    termo: str
    categoria: str | None
    preco_min: float | None
    preco_max: float | None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> BuscaProdutosQuery:
        term = str(value.get("q", "") or "").strip()
        category = value.get("categoria") or None
        if category is not None and category not in CATEGORIAS_VALIDAS:
            raise SchemaError("Categoria inválida")
        minimum = cls._parse_price(value.get("preco_min"), "Preço mínimo")
        maximum = cls._parse_price(value.get("preco_max"), "Preço máximo")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise SchemaError("Faixa de preço inválida")
        return cls(term, category, minimum, maximum)

    @staticmethod
    def _parse_price(value: Any, label: str) -> float | None:
        if value in (None, ""):
            return None
        return _non_negative_float(value, label)
