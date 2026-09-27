from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Evidence


class EvidenceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def for_deviation(self, deviation_id: str) -> list[Evidence]:
        result = await self.db.execute(select(Evidence).where(Evidence.deviation_id == deviation_id).order_by(Evidence.relevance.desc()))
        return list(result.scalars().all())

    async def replace_for_deviation(self, deviation_id: str, evidence_items: list[Evidence]) -> None:
        existing = await self.for_deviation(deviation_id)
        for row in existing:
            await self.db.delete(row)
        for row in evidence_items:
            self.db.add(row)
        await self.db.commit()
