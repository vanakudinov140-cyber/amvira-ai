class YclientsError(Exception):
    """Базовая ошибка интеграции YCLIENTS."""


class YclientsApiError(YclientsError):
    """Ошибка HTTP при обращении к API YCLIENTS."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class YclientsResponseError(YclientsError):
    """Ответ API с success=false или неожиданной структурой."""

    pass