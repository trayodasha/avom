from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "AVOM"
    PROJECT_DESCRIPTION: str = "Evaluation-First RAG Engineering Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "avom-super-secret-dev-key-change-in-production-12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./avom_dev.db",
        description="Async database connection string. e.g. postgresql+asyncpg://postgres:postgres@localhost:5432/avom"
    )
    
    # Vector Database (Qdrant)
    QDRANT_URL: Optional[str] = Field(default=None, description="Qdrant server URL, or None for local memory/storage")
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_PREFIX: str = "avom_"

    # Redis Cache & Task Broker
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM & Embedding API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
