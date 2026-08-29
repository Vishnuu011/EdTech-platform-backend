from pydantic_settings import BaseSettings
from typing import Optional

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str
    APP_ENV: str
    DEBUG: bool

    APP_VERSION: Optional[str] = "1.0.0"

    DATABASE_URL: str
    REDIS_URL: str
    RABBITMQ_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str

    CORS_ORIGINS: list[str]=["*"]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8"
    )

settings = Settings()    