from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Deviation


class DeviationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self) -> list[Deviation]:
        result = await self.db.execute(
            select(Deviation)
            .options(selectinload(Deviation.evidence_items), selectinload(Deviation.audit_events))
            .order_by(Deviation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, deviation_id: str) -> Deviation | None:
        result = await self.db.execute(
            select(Deviation)
            .where(Deviation.id == deviation_id)
            .options(selectinload(Deviation.evidence_items), selectinload(Deviation.audit_events))
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Deviation | None:
        result = await self.db.execute(select(Deviation).where(Deviation.code == code))
        return result.scalar_one_or_none()

    async def create(self, deviation: Deviation) -> Deviation:
        self.db.add(deviation)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(deviation)
        return deviation

    async def delete(self, deviation: Deviation) -> None:
        await self.db.delete(deviation)
        await self.db.commit()

    async def update_with_version(self, deviation: Deviation, expected_version: int, updates: dict) -> tuple[Deviation, bool]:
        if deviation.version != expected_version:
            deviation.conflict_flag = True
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()
                raise
            await self.db.refresh(deviation)
            return deviation, False
        for key, value in updates.items():
            setattr(deviation, key, value)
        deviation.version += 1
        deviation.updated_at = datetime.utcnow()
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(deviation)
        return deviation, True
