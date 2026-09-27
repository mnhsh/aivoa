from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AIVOA Backend"
    api_v1_prefix: str = "/api/v1"
    demo_mode: bool = True
    database_url: str | None = None
    sqlite_fallback_path: str = str(Path(__file__).resolve().parents[2] / "aivoa.db")
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"

    @field_validator("database_url")
    @classmethod
    def normalize_db_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
