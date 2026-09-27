from __future__ import annotations

from app.integrations.rag.base import BaseRAGStore


class KnowledgeAgent:
    def __init__(self, rag_store: BaseRAGStore) -> None:
        self.rag_store = rag_store

    async def retrieve(self, query: str) -> list[dict]:
        results = await self.rag_store.search(query, k=3)
        return [
            {
                "source_id": result.source_id,
                "title": result.title,
                "detail": result.detail,
                "meta": result.meta,
                "relevance": result.relevance,
                "kind": result.kind,
                "citation": result.citation,
            }
            for result in results
        ]
