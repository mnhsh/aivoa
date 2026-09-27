from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def by_hash(self, content_hash: str) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.content_hash == content_hash))
        return result.scalar_one_or_none()

    async def by_id(self, document_id: str) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def create(self, *, file_name: str, mime_type: str, content_hash: str, text_content: str) -> Document:
        document = Document(
            file_name=file_name,
            mime_type=mime_type,
            content_hash=content_hash,
            text_content=text_content,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document
