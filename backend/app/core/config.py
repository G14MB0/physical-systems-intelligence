from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "physical-systems-intelligence"
    database_url: str = "sqlite:///./.state/app.db"
    domains_root: Path = Path("app/domains")
    vector_backend: str = "memory"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "physical_system_docs"
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimensions: int = 384
    openai_embedding_model: str = "text-embedding-3-small"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:15173",
        "http://127.0.0.1:15173",
    ]
    openai_api_key: str = ""
    openai_diagnostics_enabled: bool = False

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
