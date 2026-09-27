from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base


def _sqlite_url() -> str:
    settings = get_settings()
    return f"sqlite+aiosqlite:///{settings.sqlite_fallback_path}"


def _normalized_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw_url


def create_db_engine() -> tuple[AsyncEngine, bool]:
    settings = get_settings()
    default_url = _sqlite_url()
    if not settings.database_url:
        return create_async_engine(default_url, future=True), True
    preferred = _normalized_url(settings.database_url)
    return create_async_engine(preferred, future=True), settings.demo_mode


engine, using_demo_db = create_db_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def initialize_database() -> bool:
    settings = get_settings()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.run_sync(Base.metadata.create_all)
            return engine.url.drivername.startswith("sqlite")
    except Exception:
        if settings.database_url:
            fallback_engine = create_async_engine(_sqlite_url(), future=True)
            globals()["engine"] = fallback_engine
            globals()["SessionLocal"] = async_sessionmaker(
                fallback_engine, class_=AsyncSession, expire_on_commit=False
            )
            async with fallback_engine.begin() as fallback_conn:
                await fallback_conn.run_sync(Base.metadata.create_all)
            return True
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
