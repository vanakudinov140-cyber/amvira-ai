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

    FLOWSELL_API_URL: str = ""
    FLOWSELL_API_KEY: str = ""

    TEST_MODE: bool = False
    TEST_RECIPIENTS: str = ""

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_TEST_CHAT_ID: str = ""

    SEND_PENDING_LIMIT: int = 5
    SCHEDULER_AUTOMATION_ENABLED: bool = True
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
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
