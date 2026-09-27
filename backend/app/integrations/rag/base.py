from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RAGResult:
    source_id: str
    title: str
    detail: str
    meta: str
    relevance: float
    kind: str
    citation: str


class BaseRAGStore:
    async def index(self, docs: list[dict]) -> None:
        raise NotImplementedError

    async def search(self, query: str, *, k: int = 5) -> list[RAGResult]:
        raise NotImplementedError
