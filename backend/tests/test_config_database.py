import os

import pytest

from app.core.config import Settings


def test_production_rejects_localhost_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="локальный хост"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
        )


def test_production_requires_explicit_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="явный DATABASE_URL"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL=None,
            POSTGRES_HOST="amvera-test-cnpg-db-rw",
        )


def test_development_allows_localhost() -> None:
    settings = Settings(
        ENVIRONMENT="development",
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/retention",
    )
    assert settings.database_host == "localhost"


def test_amvera_internal_host() -> None:
    settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL=(
            "postgresql+asyncpg://user:pass@"
            "amvera-ivankudinov-cnpg-retention-rw:5432/retention"
        ),
    )
    assert settings.database_host == "amvera-ivankudinov-cnpg-retention-rw"
