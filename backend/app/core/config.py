from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized Application Configuration loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
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

    # RAG & Knowledge Base Settings
    EMBEDDING_PROVIDER: str = "fake"  # "fake" (deterministic offline) or "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    KNOWLEDGE_BASE_DIR: str = "knowledge_base"

    # Future Configuration Placeholders (Do not hardcode production credentials)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    JWT_SECRET_KEY: str = "development_jwt_secret_key_change_in_production"


settings = Settings()
