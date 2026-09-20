from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized Application Configuration loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Application Settings
    APP_NAME: str = "AI Incident Commander"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database Settings (PostgreSQL + pgvector)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres_password@localhost:5432/ai_incident_commander"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Future Configuration Placeholders (Do not hardcode production credentials)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    JWT_SECRET_KEY: str = "development_jwt_secret_key_change_in_production"


settings = Settings()
