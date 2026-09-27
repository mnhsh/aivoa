from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.risk_agent import RiskAgent
from app.ai.graph import get_analysis_workflow
from app.db.repositories.document_repository import DocumentRepository
from app.integrations.groq_client import GroqClient
from app.schemas.analysis import AnalyzeResponse
from app.schemas.deviations import DeviationCreate
from app.services.deviation_service import DeviationService
from app.services.knowledge_service import KnowledgeService
from app.services.workflow_service import WorkflowTraceService

DEMO_TEXT = (
    "During API-ACM-01 batch B240918 processing, reactor temperature increased to 86.5°C and remained above "
    "the approved upper limit of 82°C for approximately 18 minutes. The excursion was identified through "
    "in-process monitoring."
)


class AnalysisService:
    def __init__(self, db: AsyncSession, workflow_trace_service: WorkflowTraceService) -> None:
        self.db = db
        self.document_repo = DocumentRepository(db)
        self.deviation_service = DeviationService(db)
        self.knowledge_service = KnowledgeService(db)
        self.workflow_trace_service = workflow_trace_service
        self.groq = GroqClient()
        self.knowledge_agent = KnowledgeAgent(KnowledgeService.rag_store)
        self.risk_agent = RiskAgent(self.groq)

    async def analyze(self, *, text: str | None, document_id: str | None) -> AnalyzeResponse:
        source_text = text or ""
        if document_id:
            doc = await self.document_repo.by_id(document_id)
            if not doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            source_text = doc.text_content
        if not source_text.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No analyzable text provided")

        await self.knowledge_service.ensure_defaults()
        extraction = self._extract(source_text)
        recommendation = await self.risk_agent.assess(
            approved_max=extraction["approved_max"],
            actual_value=extraction["actual_value"],
            duration_minutes=extraction["duration_minutes"],
        )
        evidence = await self.knowledge_agent.retrieve(source_text)
        conflict_detected = self._detect_conflict(extraction)
        workflow = get_analysis_workflow()
        similar_baseline = [
            {"code": "DEV-2025-0187", "title": "Similar temperature excursion", "relevance": 89, "status": "Closed"}
        ]
        state = workflow.run(
            text=source_text,
            fields=extraction["fields"],
            evidence=evidence,
            recommendation=recommendation,
            conflict_detected=conflict_detected,
            similar_cases=similar_baseline,
        )
        created = await self.deviation_service.create(
            DeviationCreate(
                title="Temperature excursion during API processing",
                product=extraction["product"],
                batch=extraction["batch"],
                severity=recommendation,  # type: ignore[arg-type]
                status="Under Review",
                owner="AIVOA AI",
                parameter=extraction["parameter"],
                approved_min=extraction["approved_min"],
                approved_max=extraction["approved_max"],
                actual_value=extraction["actual_value"],
                duration_minutes=extraction["duration_minutes"],
                description=extraction["description"],
                actions=(
                    "Heating was stopped and the reactor was returned to the approved operating range. "
                    "QA was notified and the batch was placed on temporary hold pending assessment."
                ),
                review_required=True,
                source_excerpt=source_text[:1000],
                document_id=document_id,
            ),
            evidence=evidence,
        )
        similar_cases = await self.deviation_service.similar_cases(created.id)
        trace_id = self.workflow_trace_service.save_trace(state.trace)
        return AnalyzeResponse(
            deviation_id=created.id,
            recommendation=recommendation,  # type: ignore[arg-type]
            extracted_fields=state.fields,
            evidence=state.evidence,
            similar_cases=similar_cases,
            conflict_detected=conflict_detected,
            trace_id=trace_id,
            provider=self.groq.provider_name,
            demo_mode=self.groq.provider_name == "demo",
        )

    def _extract(self, text: str) -> dict:
        product = (
            self._first_group(r"(?:product|api|item|material)\s*[:#-]?\s*([A-Za-z0-9_-]+)", text)
            or self._first_group(r"\b([A-Z0-9]{2,8}(?:-[A-Z0-9]{2,8})+)\b", text)
            or ""
        )
        batch = (
            self._first_group(r"(?:batch|lot|b/n|b#)\s*[:#-]?\s*([A-Za-z0-9_-]+)", text)
            or self._first_group(r"\b(B\d{4,10}[A-Z0-9]*)\b", text)
            or ""
        )
        actual = self._first_float(r"(\d+(?:\.\d+)?)\s*(?:°?C|°?F|bar|psi|rpm|kg|%|mg/mL)", text) or self._first_float(r"(?:actual|reached|increased to|was)\s*[:#-]?\s*(\d+(?:\.\d+)?)", text)
        approved_range = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:°?[CF]|bar|psi|%)?\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)\s*(?:°?[CF]|bar|psi|%)?",
            text,
            re.IGNORECASE,
        )
        approved_max = float(approved_range.group(2)) if approved_range else self._first_float(r"(?:limit|max|approved)\s*(?:of|is)?\s*(\d+(?:\.\d+)?)", text)
        approved_min = float(approved_range.group(1)) if approved_range else None
        duration = self._first_int(r"(\d+)\s*(?:minutes|mins|hours|hrs|min|h)\b", text)

        param_match = re.search(r"(?:parameter|metric|variable)\s*[:#-]?\s*([A-Za-z\s]{3,30})", text, re.IGNORECASE)
        parameter = param_match.group(1).strip() if param_match else ""
        if not parameter:
            text_lower = text.lower()
            if "temperature" in text_lower or "temp" in text_lower:
                parameter = "Reactor Temperature"
            elif "pressure" in text_lower:
                parameter = "Differential Pressure"
            elif "humidity" in text_lower:
                parameter = "Relative Humidity"
            elif "ph" in text_lower:
                parameter = "pH Value"
            elif "flow" in text_lower:
                parameter = "Flow Rate"

        fields = []
        if batch:
            fields.append({"label": "Batch Number", "value": batch, "confidence": 96, "source": "input", "citation": "input:batch"})
        if product:
            fields.append({"label": "Product", "value": product, "confidence": 94, "source": "input", "citation": "input:product"})
        if parameter:
            fields.append({"label": "Parameter", "value": parameter, "confidence": 98, "source": "input", "citation": "input:parameter"})
        if actual is not None:
            fields.append({"label": "Actual Value", "value": f"{actual}°C", "confidence": 97, "source": "input", "citation": "input:actual"})
        if duration is not None:
            fields.append({"label": "Duration", "value": f"{duration} minutes", "confidence": 91, "source": "input", "citation": "input:duration"})

        return {
            "product": product,
            "batch": batch,
            "parameter": parameter,
            "actual_value": actual,
            "approved_max": approved_max,
            "approved_min": approved_min,
            "duration_minutes": duration,
            "description": text[:1000],
            "fields": fields,
        }

    def _detect_conflict(self, extraction: dict) -> bool:
        approved_max = extraction.get("approved_max")
        actual = extraction.get("actual_value")
        if approved_max is None or actual is None:
            return False
        return actual <= approved_max

    @staticmethod
    def _first_group(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _first_float(pattern: str, text: str) -> float | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        return float(match.group(1))

    @staticmethod
    def _first_int(pattern: str, text: str) -> int | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1))
