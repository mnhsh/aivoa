from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.knowledge_repository import KnowledgeRepository
from app.integrations.rag.in_memory import InMemoryRAGStore
from app.schemas.knowledge import KnowledgeDocIn, KnowledgeDocOut


DEFAULT_KNOWLEDGE = [
    {
        "external_id": "SOP-DEV-004",
        "title": "Deviation Classification Procedure",
        "content": "Section 4.2 requires excursions above approved process limits to be reviewed by QA within the same shift.",
        "detail": "Section 4.2",
        "meta": "SOP · v3.2 · Active",
        "kind": "SOP",
        "citation": "SOP-DEV-004 §4.2",
    },
    {
        "external_id": "QMS-012",
        "title": "Process Parameter Excursions",
        "content": "Temperature excursions above 3°C for >10 minutes should be classified at least High severity.",
        "detail": "Quality Manual",
        "meta": "Quality manual · v5.1 · Active",
        "kind": "MANUAL",
        "citation": "QMS-012 p.18",
    },
]


class KnowledgeService:
    rag_store = InMemoryRAGStore()
    initialized = False

    def __init__(self, db: AsyncSession) -> None:
        self.repo = KnowledgeRepository(db)

    async def ensure_defaults(self) -> None:
        if KnowledgeService.initialized:
            return
        await KnowledgeService.rag_store.index(DEFAULT_KNOWLEDGE)
        KnowledgeService.initialized = True

    async def list_docs(self) -> list[KnowledgeDocOut]:
        await self.ensure_defaults()
        docs = await self.repo.list_docs()
        return [
            KnowledgeDocOut(
                id=doc.id,
                external_id=doc.external_id,
                title=doc.title,
                content=doc.content,
                metadata=doc.metadata_json,
            )
            for doc in docs
        ]

    async def index_docs(self, docs: list[KnowledgeDocIn]) -> list[KnowledgeDocOut]:
        await self.ensure_defaults()
        payload = []
        created = []
        for doc in docs:
            row = await self.repo.upsert(
                external_id=doc.external_id,
                title=doc.title,
                content=doc.content,
                metadata=doc.metadata,
            )
            created.append(
                KnowledgeDocOut(
                    id=row.id,
                    external_id=row.external_id,
                    title=row.title,
                    content=row.content,
                    metadata=row.metadata_json,
                )
            )
            payload.append(
                {
                    "external_id": doc.external_id,
                    "title": doc.title,
                    "content": doc.content,
                    "detail": doc.metadata.get("detail", "Indexed document"),
                    "meta": doc.metadata.get("meta", "Knowledge doc"),
                    "kind": doc.metadata.get("kind", "MANUAL"),
                    "citation": doc.metadata.get("citation", doc.external_id),
                }
            )
        await KnowledgeService.rag_store.index(payload)
        return created
