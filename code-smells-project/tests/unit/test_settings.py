"""Unit tests for secure environment configuration."""

from __future__ import annotations

import pytest

from src.config.settings import load_settings


def test_production_requires_a_long_secret(monkeypatch):
    monkeypatch.setenv("AMBIENTE", "producao")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        load_settings()


def test_development_generates_a_non_static_secret(monkeypatch):
    monkeypatch.setenv("AMBIENTE", "desenvolvimento")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    first = load_settings().secret_key
    second = load_settings().secret_key

    assert first
    assert first != second
