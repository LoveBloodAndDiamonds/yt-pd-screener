__all__ = ["SettingsDTO"]

from pydantic import BaseModel


class SettingsDTO(BaseModel):
    """Модель настроек для передачи данных между слоями приложения."""

    model_config = {"from_attributes": True}

    id: int
    interval: int
    min_growth: float
    timeout: int
    chat_id: int | None
    bot_token: str | None
