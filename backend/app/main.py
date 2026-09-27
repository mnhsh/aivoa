from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict:
    return {"name": settings.app_name, "demo_mode": settings.demo_mode}


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "aivoa-deviation-api",
        "version": "1.0.0",
        "demo_mode": settings.demo_mode,
    }


@app.get("/health/database", tags=["system"])
async def health_database() -> dict:
    return {"database": "healthy", "driver": "sqlite+aiosqlite" if settings.demo_mode else "configured"}


@app.get("/health/ai", tags=["system"])
async def health_ai() -> dict:
    return {"ai": "demo" if settings.demo_mode else "configured"}


@app.get("/health/rag", tags=["system"])
async def health_rag() -> dict:
    return {"rag": "healthy", "provider": "in-memory-demo" if settings.demo_mode else "configured"}
