from __future__ import annotations

from app.integrations.rag.base import BaseRAGStore, RAGResult


class InMemoryRAGStore(BaseRAGStore):
    def __init__(self) -> None:
        self._docs: list[dict] = []

    async def index(self, docs: list[dict]) -> None:
        self._docs.extend(docs)

    async def search(self, query: str, *, k: int = 5) -> list[RAGResult]:
        query_tokens = set(query.lower().split())
        scored: list[tuple[float, dict]] = []
        for doc in self._docs:
            content = f"{doc.get('title', '')} {doc.get('content', '')}".lower()
            score = sum(1.0 for token in query_tokens if token in content)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        output = []
        for score, doc in scored[:k]:
            output.append(
                RAGResult(
                    source_id=doc["external_id"],
                    title=doc["title"],
                    detail=doc.get("detail", "Retrieved from knowledge index"),
                    meta=doc.get("meta", "Knowledge document"),
                    relevance=min(99.0, 80.0 + score * 3),
                    kind=doc.get("kind", "MANUAL"),
                    citation=doc.get("citation", f"{doc['external_id']}"),
                )
            )
        return output
