import re
from functools import lru_cache
from typing import Self
from pydantic import computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Retention API"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    # production — для Amvera: обязателен DATABASE_URL с внутренним хостом cnpg-*-rw
    ENVIRONMENT: str = "development"

    POSTGRES_USER: str = "retention"
    POSTGRES_PASSWORD: str = "retention"
    POSTGRES_DB: str = "retention"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str | None = None

    YCLIENTS_API_KEY: str = ""
    YCLIENTS_PARTNER_TOKEN: str = ""
    YCLIENTS_COMPANY_ID: int = 0
    YCLIENTS_BASE_URL: str = "https://api.yclients.com/api/v1"

    # FlowSell Flow API (WhatsApp): https://dev.flowsell.me/docs/
    # FLOWSELL_INSTANCE_ID = idInstance, FLOWSELL_API_KEY = apiTokenInstance
    FLOWSELL_API_BASE_URL: str = "https://dev.flowsell.me/api/v1"
    FLOWSELL_INSTANCE_ID: str = ""
    FLOWSELL_API_KEY: str = ""
    FLOWSELL_DRY_RUN: bool = True
    # Устарело: оставлено для совместимости; не используется клиентом
    FLOWSELL_API_URL: str = ""

    TEST_MODE: bool = False
    TEST_RECIPIENTS: str = ""

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_TEST_CHAT_ID: str = ""

    SEND_PENDING_LIMIT: int = 5
    SCHEDULER_AUTOMATION_ENABLED: bool = True
    SCHEDULER_STAGING_FOUNDATION_ENABLED: bool = False
    SCHEDULER_STAGING_MODE: bool = True
    SCHEDULER_STAGING_MAX_RECORDS: int = 1
    SCHEDULER_STAGING_REQUIRE_DRY_RUN: bool = True
    SCHEDULER_STAGING_ONLY_TEST_RECIPIENTS: bool = True
    RETENTION_ATTRIBUTION_DAYS: int = 30

    DUPLICATE_WINDOW_DAYS: int = 7
    RETENTION_COOLDOWN_DAYS: int = 14
    DAILY_SEND_LIMIT: int = 50
    QUIET_HOURS_START: int = 21
    QUIET_HOURS_END: int = 10

    AI_REWRITE_ENABLED: bool = False
    AI_PROVIDER: str = "mock"

    # Доп. origins для CORS (через запятую), например demo dashboard URL
    CORS_ORIGINS: str = ""

    @field_validator("AI_PROVIDER", mode="before")
    @classmethod
    def normalize_ai_provider(cls, value: object) -> str:
        if value is None:
            return "mock"
        return str(value).strip().lower() or "mock"

    @field_validator("QUIET_HOURS_START", "QUIET_HOURS_END", mode="after")
    @classmethod
    def validate_quiet_hours(cls, value: int) -> int:
        if not 0 <= value <= 23:
            raise ValueError("QUIET_HOURS_START/END должны быть в диапазоне 0–23 (UTC).")
        return value

    @field_validator("SCHEDULER_STAGING_MAX_RECORDS", mode="after")
    @classmethod
    def validate_scheduler_staging_max_records(cls, value: int) -> int:
        if value != 1:
            raise ValueError("SCHEDULER_STAGING_MAX_RECORDS must stay 1 for staging safety.")
        return value

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> str:
        if value is None:
            return "development"
        return str(value).strip().lower() or "development"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def empty_database_url_is_none(cls, value: object) -> object | None:
        if value is None:
            return None
        text = str(value).strip()
        return None if not text else text

    @field_validator("TEST_RECIPIENTS", mode="before")
    @classmethod
    def normalize_test_recipients(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @computed_field
    @property
    def cors_allowed_origins(self) -> list[str]:
        defaults = [
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:5175",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:4173",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:8080",
            "http://localhost:4173",
            "http://192.168.0.6:5173",
            "http://192.168.0.6:5174",
            "http://192.168.0.6:5175",
            "http://192.168.0.6:8080",
            "http://10.114.112.117:5173",
            "http://10.114.112.117:5174",
            "http://10.114.112.117:5175",
            "http://10.114.112.117:8080",
        ]
        extra: list[str] = []
        if self.CORS_ORIGINS.strip():
            extra = [p.strip() for p in re.split(r"[,;\s]+", self.CORS_ORIGINS) if p.strip()]
        merged = list(dict.fromkeys(defaults + extra))
        return merged

    @computed_field
    @property
    def flowsell_configured(self) -> bool:
        return bool(
            (self.FLOWSELL_INSTANCE_ID or "").strip()
            and (self.FLOWSELL_API_KEY or "").strip(),
        )

    @computed_field
    @property
    def test_recipient_phones(self) -> list[str]:
        if not self.TEST_RECIPIENTS:
            return []
        parts = re.split(r"[,;\s]+", self.TEST_RECIPIENTS.strip())
        return [p for p in (part.strip() for part in parts) if p]

    @model_validator(mode="after")
    def validate_test_mode(self) -> Self:
        if self.TEST_MODE and not self.test_recipient_phones:
            raise ValueError(
                "TEST_MODE=true требует непустой TEST_RECIPIENTS (номера через запятую или пробел).",
            )
        return self

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.strip()
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def database_host(self) -> str:
        """Хост БД для логов (без пароля)."""
        uri = self.sqlalchemy_database_uri
        # postgresql+asyncpg://user:pass@host:5432/db
        without_scheme = uri.split("://", 1)[-1]
        if "@" in without_scheme:
            host_part = without_scheme.rsplit("@", 1)[-1]
        else:
            host_part = without_scheme
        host = host_part.split("/", 1)[0]
        return host.split(":")[0] if host else "unknown"

    @staticmethod
    def _is_local_database_host(host: str) -> bool:
        normalized = host.strip().lower()
        return normalized in {"localhost", "127.0.0.1", "::1"}

    @model_validator(mode="after")
    def validate_database_configuration(self) -> Self:
        uri = self.sqlalchemy_database_uri.strip()
        if not uri:
            raise ValueError(
                "Не задано подключение к БД: укажите DATABASE_URL "
                "или пару POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB / POSTGRES_HOST.",
            )
        if not uri.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL должен начинаться с postgresql+asyncpg:// "
                "(async SQLAlchemy + asyncpg).",
            )

        host = self.database_host
        is_production = self.ENVIRONMENT == "production"

        if is_production and not self.DATABASE_URL:
            raise ValueError(
                "ENVIRONMENT=production требует явный DATABASE_URL "
                "(внутренний хост Amvera PostgreSQL, не POSTGRES_HOST по умолчанию).",
            )

        if is_production and self._is_local_database_host(host):
            raise ValueError(
                f"ENVIRONMENT=production: запрещён локальный хост БД ({host!r}). "
                "Задайте DATABASE_URL с внутренним хостом Amvera "
                "(amvera-<user>-cnpg-<project>-rw).",
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
