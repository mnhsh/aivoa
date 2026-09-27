from __future__ import annotations

import asyncio

from app.db.session import SessionLocal, initialize_database
from app.schemas.deviations import DeviationCreate
from app.schemas.knowledge import KnowledgeDocIn
from app.services.deviation_service import DeviationService
from app.services.knowledge_service import KnowledgeService


async def run_seed() -> None:
    await initialize_database()
    async with SessionLocal() as db:
        knowledge = KnowledgeService(db)
        await knowledge.index_docs(
            [
                KnowledgeDocIn(
                    external_id="SOP-DEV-004",
                    title="Deviation Classification Procedure",
                    content="Section 4.2 describes severity classification and QA escalation.",
                    metadata={"kind": "SOP", "citation": "SOP-DEV-004 §4.2", "meta": "SOP · v3.2 · Active"},
                )
            ]
        )
        deviation_service = DeviationService(db)
        existing = await deviation_service.list()
        if existing:
            return
        await deviation_service.create(
            DeviationCreate(
                title="Temperature excursion during API processing",
                product="API-ACM-01",
                batch="B240918",
                severity="High",
                status="Under Review",
                owner="Sarah Mitchell",
                parameter="Reactor Temperature",
                approved_min=78,
                approved_max=82,
                actual_value=86.5,
                duration_minutes=18,
                description="Seeded demo deviation",
                actions="Heating stopped, QA notified.",
                review_required=True,
            ),
            evidence=[
                {
                    "source_id": "SOP-DEV-004",
                    "title": "Deviation Classification Procedure",
                    "detail": "Section 4.2",
                    "meta": "SOP · v3.2 · Active",
                    "relevance": 94,
                    "kind": "SOP",
                    "citation": "SOP-DEV-004 §4.2",
                }
            ],
        )


if __name__ == "__main__":
    asyncio.run(run_seed())
