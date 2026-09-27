from __future__ import annotations

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.document_repository import DocumentRepository
from app.parsers.document_parser import parse_document_bytes
from app.schemas.documents import DocumentOut


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = DocumentRepository(db)

    async def upload(self, *, payload: bytes, filename: str, mime_type: str) -> DocumentOut:
        content_hash = hashlib.sha256(payload).hexdigest()
        existing = await self.repo.by_hash(content_hash)
        if existing:
            return DocumentOut(
                id=existing.id,
                file_name=existing.file_name,
                mime_type=existing.mime_type,
                content_hash=existing.content_hash,
                created_at=existing.created_at,
                idempotent_reuse=True,
            )
        text_content = parse_document_bytes(payload, filename)
        doc = await self.repo.create(
            file_name=filename,
            mime_type=mime_type or "application/octet-stream",
            content_hash=content_hash,
            text_content=text_content,
        )
        return DocumentOut(
            id=doc.id,
            file_name=doc.file_name,
            mime_type=doc.mime_type,
            content_hash=doc.content_hash,
            created_at=doc.created_at,
            idempotent_reuse=False,
        )
