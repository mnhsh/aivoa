from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeDocument


class KnowledgeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_docs(self) -> list[KnowledgeDocument]:
        result = await self.db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
        return list(result.scalars().all())

    async def upsert(self, *, external_id: str, title: str, content: str, metadata: dict) -> KnowledgeDocument:
        result = await self.db.execute(select(KnowledgeDocument).where(KnowledgeDocument.external_id == external_id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.title = title
            existing.content = content
            existing.metadata_json = metadata
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        doc = KnowledgeDocument(external_id=external_id, title=title, content=content, metadata_json=metadata)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc
