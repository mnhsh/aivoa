from __future__ import annotations

from app.integrations.rag.base import BaseRAGStore, RAGResult


class PgVectorRAGStore(BaseRAGStore):
    """Pgvector-ready interface. This stub can be wired to SQL embeddings/indexes."""

    async def index(self, docs: list[dict]) -> None:
        return None

    async def search(self, query: str, *, k: int = 5) -> list[RAGResult]:
        return []
