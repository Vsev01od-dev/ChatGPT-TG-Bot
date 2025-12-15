from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из .env файла."""

    # Ключи API
    BOT_TOKEN: str
    OPENROUTER_API_KEY: str
    OPENROUTER_SITE: Optional[str] = None
    OPENROUTER_TITLE: Optional[str] = None

    # Основная модель
    OPENROUTER_MODEL: str = "openai/gpt-oss-20b:free"

    # Резервные модели
    # OPENROUTER_FALLBACK_MODELS: str = "openai/gpt-5.2-pro,openai/gpt-5-mini"
    OPENROUTER_FALLBACK_MODELS: List[str] = []

    # Лимиты
    TEXT_DAILY_LIMIT: int = 200
    CHAT_WINDOW_LIMIT: int = 30
    """
    @field_validator("OPENROUTER_FALLBACK_MODELS")
    @classmethod
    def parse_fallback_models(cls, v: str) -> List[str]:
        #Парсит строку с резервными моделями в список.
        if not v:
            return []
        # Удаляем пробелы и разбиваем по запятой
        models = [model.strip() for model in v.split(",") if model.strip()]
        print(f"✅ Загружены резервные модели: {models}")
        return models
    """

    @field_validator("OPENROUTER_FALLBACK_MODELS", mode="before")
    @classmethod
    def parse_fallback_models(cls, v):
        if isinstance(v, list):
            return v

        if isinstance(v, str):
            return [model.strip() for model in v.split(",") if model.strip()]

        return []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Глобальный объект настроек
settings = Settings()
print(f"✅ Основная модель: {settings.OPENROUTER_MODEL}")
print(f"✅ Всего моделей в цепочке: {[settings.OPENROUTER_MODEL] + settings.OPENROUTER_FALLBACK_MODELS}")