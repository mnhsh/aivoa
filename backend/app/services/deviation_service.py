from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Deviation, Evidence
from app.db.repositories.audit_repository import AuditRepository
from app.db.repositories.deviation_repository import DeviationRepository
from app.db.repositories.evidence_repository import EvidenceRepository
from app.integrations.groq_client import GroqClient
from app.schemas.deviations import DeviationCreate, DeviationOut, DeviationUpdate, ReassessResponse


def map_deviation_out(model: Deviation) -> DeviationOut:
    return DeviationOut(
        id=model.id,
        code=model.code,
        title=model.title,
        product=model.product,
        batch=model.batch,
        severity=model.severity,
        status=model.status,
        owner=model.owner,
        parameter=model.parameter,
        approved_min=model.approved_min,
        approved_max=model.approved_max,
        actual_value=model.actual_value,
        duration_minutes=model.duration_minutes,
        description=model.description,
        actions=model.actions,
        review_required=model.review_required,
        review_notes=model.review_notes,
        ai_assisted=model.ai_assisted,
        analysis_confidence=model.analysis_confidence,
        conflict_flag=model.conflict_flag,
        version=model.version,
        document_id=model.document_id,
        source_excerpt=model.source_excerpt,
        created_at=model.created_at,
        updated_at=model.updated_at,
        evidence=[
            {
                "source_id": e.source_id,
                "title": e.title,
                "detail": e.detail,
                "meta": e.meta,
                "relevance": e.relevance,
                "kind": e.kind,
                "citation": e.citation,
            }
            for e in model.evidence_items
        ],
        audit_trail=[
            {
                "actor": a.actor,
                "action": a.action,
                "detail": a.detail,
                "created_at": a.created_at,
            }
            for a in model.audit_events
        ],
    )


class DeviationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = DeviationRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.audit_repo = AuditRepository(db)
        self.groq = GroqClient()

    async def list(self) -> list[DeviationOut]:
        rows = await self.repo.list()
        return [map_deviation_out(row) for row in rows]

    async def get(self, deviation_id: str) -> DeviationOut:
        row = await self.repo.get(deviation_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
        return map_deviation_out(row)

    async def create(self, payload: DeviationCreate, evidence: list[dict] | None = None) -> DeviationOut:
        code = await self._next_code()
        model = Deviation(
            code=code,
            title=payload.title,
            product=payload.product,
            batch=payload.batch,
            severity=payload.severity,
            status=payload.status,
            owner=payload.owner,
            parameter=payload.parameter,
            approved_min=payload.approved_min,
            approved_max=payload.approved_max,
            actual_value=payload.actual_value,
            duration_minutes=payload.duration_minutes,
            description=payload.description,
            actions=payload.actions,
            review_required=payload.review_required,
            review_notes=payload.review_notes,
            ai_assisted=True,
            analysis_confidence=0.95,
            source_excerpt=payload.source_excerpt,
            document_id=payload.document_id,
        )
        model = await self.repo.create(model)
        if evidence:
            await self.evidence_repo.replace_for_deviation(
                model.id,
                [
                    Evidence(
                        deviation_id=model.id,
                        source_id=item["source_id"],
                        title=item["title"],
                        detail=item["detail"],
                        meta=item["meta"],
                        relevance=item["relevance"],
                        kind=item["kind"],
                        citation=item["citation"],
                    )
                    for item in evidence
                ],
            )
        await self.audit_repo.add(
            deviation_id=model.id, actor="AIVOA AI", action="Deviation created", detail="Created from analysis workflow"
        )
        reloaded = await self.repo.get(model.id)
        assert reloaded is not None
        return map_deviation_out(reloaded)

    async def update(self, deviation_id: str, payload: DeviationUpdate) -> tuple[DeviationOut, bool]:
        row = await self.repo.get(deviation_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
        updates = payload.model_dump(exclude_none=True, exclude={"expected_version"})
        updated, ok = await self.repo.update_with_version(row, payload.expected_version, updates)
        await self.audit_repo.add(
            deviation_id=row.id,
            actor="Reviewer",
            action="Deviation updated" if ok else "Conflict detected",
            detail=f"Version expected={payload.expected_version}, actual={row.version}",
        )
        reloaded = await self.repo.get(row.id)
        assert reloaded is not None
        return map_deviation_out(reloaded), ok

    async def delete(self, deviation_id: str) -> None:
        row = await self.repo.get(deviation_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
        await self.repo.delete(row)

    async def similar_cases(self, deviation_id: str) -> list[dict]:
        row = await self.repo.get(deviation_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
        all_rows = await self.repo.list()
        similar = []
        for candidate in all_rows:
            if candidate.id == row.id:
                continue
            score = 0.0
            if candidate.product == row.product:
                score += 55
            if candidate.parameter == row.parameter:
                score += 35
            if candidate.severity == row.severity:
                score += 10
            if score > 0:
                similar.append(
                    {
                        "code": candidate.code,
                        "title": candidate.title,
                        "relevance": min(99.0, score),
                        "status": candidate.status,
                    }
                )
        similar.sort(key=lambda item: item["relevance"], reverse=True)
        return similar[:5]

    async def evidence(self, deviation_id: str) -> list[dict]:
        row = await self.repo.get(deviation_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
        return [
            {
                "source_id": e.source_id,
                "title": e.title,
                "detail": e.detail,
                "meta": e.meta,
                "relevance": e.relevance,
                "kind": e.kind,
                "citation": e.citation,
            }
            for e in row.evidence_items
        ]

    async def fields(self, deviation_id: str) -> list[dict]:
        row = await self.repo.get(deviation_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
        return [
            {"label": "Batch Number", "value": row.batch, "confidence": 96, "source": "analysis", "citation": "source text"},
            {"label": "Product", "value": row.product, "confidence": 94, "source": "analysis", "citation": "source text"},
            {"label": "Parameter", "value": row.parameter, "confidence": 98, "source": "analysis", "citation": "source text"},
            {"label": "Actual Value", "value": str(row.actual_value), "confidence": 97, "source": "analysis", "citation": "source text"},
            {
                "label": "Duration",
                "value": f"{row.duration_minutes} minutes" if row.duration_minutes is not None else "unknown",
                "confidence": 91,
                "source": "analysis",
                "citation": "source text",
            },
        ]

    async def reassess(self, deviation_id: str, rationale: str) -> ReassessResponse:
        row = await self.repo.get(deviation_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
        delta = 0.0
        if row.approved_max is not None and row.actual_value is not None:
            delta = max(0.0, row.actual_value - row.approved_max)
        recommended = await self.groq.recommend_severity(
            observed_delta=delta, duration_minutes=row.duration_minutes or 0, rationale=rationale
        )
        await self.audit_repo.add(
            deviation_id=row.id,
            actor="AIVOA AI",
            action="Deviation reassessed",
            detail=f"Rationale: {rationale[:150]}",
        )
        return ReassessResponse(
            deviation_id=row.id,
            prior_severity=row.severity,  # type: ignore[arg-type]
            recommended_severity=recommended,  # type: ignore[arg-type]
            provider=self.groq.provider_name,
            demo_mode=self.groq.provider_name == "demo",
        )

    async def _next_code(self) -> str:
        year = datetime.utcnow().year
        for idx in range(1, 10000):
            code = f"DEV-{year}-{idx:04d}"
            if not await self.repo.get_by_code(code):
                return code
        raise HTTPException(status_code=500, detail="Unable to allocate deviation code")
