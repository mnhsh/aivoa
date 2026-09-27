from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.knowledge import KnowledgeDocOut, KnowledgeIndexRequest
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/docs", response_model=list[KnowledgeDocOut])
async def list_knowledge_docs(db: AsyncSession = Depends(get_db)) -> list[KnowledgeDocOut]:
    return await KnowledgeService(db).list_docs()


@router.post("/index", response_model=list[KnowledgeDocOut])
async def index_knowledge_docs(payload: KnowledgeIndexRequest, db: AsyncSession = Depends(get_db)) -> list[KnowledgeDocOut]:
    return await KnowledgeService(db).index_docs(payload.docs)
