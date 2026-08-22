import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]

ENV_FILE = os.getenv(
    "FACTORYPULSE_ENV_FILE",
    str(BACKEND_DIR / ".env"),
)


class Settings(BaseSettings):
    app_name: str = "FactoryPulse AI API"
    environment: str = "development"
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()