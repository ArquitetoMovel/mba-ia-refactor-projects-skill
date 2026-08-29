"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
import secrets
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from importlib import metadata
from pathlib import Path

CATEGORIAS_VALIDAS = (
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
)

# Discount tiers for sales report (faturamento threshold → rate)
DESCONTO_FAIXAS: tuple[tuple[float, float], ...] = (
    (10_000.0, 0.10),
    (5_000.0, 0.05),
    (1_000.0, 0.02),
)

PRODUCTION_ENVIRONMENTS = frozenset({"prod", "producao", "production"})
SeedUser = tuple[str, str, str, str]


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    db_path: str
    ambiente: str
    admin_token: str | None
    token_max_age_seconds: int = 86_400
    cors_origins: tuple[str, ...] = ()
    seed_users: tuple[SeedUser, ...] = ()


@lru_cache(maxsize=1)
def project_version() -> str:
    """Read the version from installed metadata or the project manifest."""
    try:
        return metadata.version("code-smells-project")
    except metadata.PackageNotFoundError:
        manifest = Path(__file__).resolve().parents[2] / "pyproject.toml"
        try:
            with manifest.open("rb") as file:
                return str(tomllib.load(file)["project"]["version"])
        except (OSError, KeyError, TypeError):
            return "desenvolvimento"


def _load_seed_users() -> tuple[SeedUser, ...]:
    definitions = (
        ("Admin", "admin@loja.com", "SEED_ADMIN_PASSWORD", "admin"),
        ("João Silva", "joao@email.com", "SEED_JOAO_PASSWORD", "cliente"),
        ("Maria Santos", "maria@email.com", "SEED_MARIA_PASSWORD", "cliente"),
    )
    users: list[SeedUser] = []
    for name, email, environment_name, role in definitions:
        password = os.environ.get(environment_name)
        if password:
            users.append((name, email, password, role))
    return tuple(users)


def _load_cors_origins() -> tuple[str, ...]:
    raw_origins = os.environ.get("CORS_ORIGINS", "")
    return tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())


def _load_positive_int(environment_name: str, default: str) -> int:
    value = int(os.environ.get(environment_name, default))
    if value <= 0:
        raise ValueError(f"{environment_name} deve ser positivo")
    return value


def load_settings() -> Settings:
    ambiente = os.environ.get("AMBIENTE", "desenvolvimento").strip().lower()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    secret_key = os.environ.get("SECRET_KEY", "").strip()
    if ambiente in PRODUCTION_ENVIRONMENTS and len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres em produção")
    if ambiente in PRODUCTION_ENVIRONMENTS and debug:
        raise RuntimeError("FLASK_DEBUG deve estar desativado em produção")
    if not secret_key:
        secret_key = secrets.token_urlsafe(32)

    return Settings(
        secret_key=secret_key,
        debug=debug,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5003")),
        db_path=os.environ.get("DB_PATH", "loja.db"),
        ambiente=ambiente,
        admin_token=os.environ.get("ADMIN_TOKEN", "").strip() or None,
        token_max_age_seconds=_load_positive_int("AUTH_TOKEN_MAX_AGE_SECONDS", "86400"),
        cors_origins=_load_cors_origins(),
        seed_users=_load_seed_users(),
    )
