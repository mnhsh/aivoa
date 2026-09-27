from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.db import session as db_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "demo_mode": settings.demo_mode,
        "database_driver": db_session.engine.url.drivername,
    }


@router.get("/live")
async def liveness() -> dict:
    return {"status": "alive"}


@router.get("/ready")
async def readiness() -> dict:
    settings = get_settings()
    return {"status": "ready", "demo_mode": settings.demo_mode}
