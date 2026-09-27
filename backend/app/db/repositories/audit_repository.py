from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add(self, *, deviation_id: str, actor: str, action: str, detail: str) -> AuditEvent:
        event = AuditEvent(deviation_id=deviation_id, actor=actor, action=action, detail=detail)
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def list_for_deviation(self, deviation_id: str) -> list[AuditEvent]:
        result = await self.db.execute(
            select(AuditEvent).where(AuditEvent.deviation_id == deviation_id).order_by(AuditEvent.created_at.asc())
        )
        return list(result.scalars().all())
