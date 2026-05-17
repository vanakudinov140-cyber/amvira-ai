from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


def _import_models() -> None:
    """Import model modules so metadata is registered on :class:`Base`."""

    import app.models  # noqa: F401


_import_models()
