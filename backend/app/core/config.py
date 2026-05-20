from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "mysql+asyncmy://root:password@127.0.0.1:3306/ai_admin"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEBUG: bool = False
    PROJECT_NAME: str = "AI Admin"
    VERSION: str = "0.1.0"


# Determine the project root (directory containing .env)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

settings = Settings(_env_file=PROJECT_ROOT / ".env")  # type: ignore[call-arg]
