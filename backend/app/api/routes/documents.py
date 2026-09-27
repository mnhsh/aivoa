from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.documents import DocumentOut
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> DocumentOut:
    payload = await file.read()
    service = DocumentService(db)
    return await service.upload(payload=payload, filename=file.filename or "uploaded.bin", mime_type=file.content_type or "")
