from __future__ import annotations

import re
from datetime import date

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
        if document_id and not source_text.strip():
            doc = await self.document_repo.by_id(document_id)
            if not doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            source_text = doc.text_content
        if not source_text.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No analyzable text provided")

        await self.knowledge_service.ensure_defaults()

        classification = await self.groq.classify_input(source_text)
        if classification is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "classification_unavailable", "message": "AI input validation is unavailable. Please retry."},
            )
        if not classification.is_quality_deviation:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "not_quality_deviation", "message": classification.reason},
            )

        # Try real LLM extraction first
        ai_extraction = await self.groq.extract_deviation_data(source_text)
        if ai_extraction:
            extraction = ai_extraction.model_dump()

            def _map_label(k: str) -> str:
                if k == "batch":
                    return "Batch Number"
                if k == "product":
                    return "Product"
                if k == "parameter":
                    return "Parameter"
                if k == "actual_value":
                    return "Actual Value"
                if k == "duration_minutes":
                    return "Duration"
                return k.replace("_", " ").title()

            extraction["fields"] = [
                {"label": _map_label(k), "value": str(v), "confidence": 99, "source": "ai", "citation": "ai_extract"}
                for k, v in extraction.items() if v is not None and k not in ["description", "fields", "title"]
            ]
        else:
            extraction = self._extract(source_text)

        recommendation = await self.risk_agent.assess(
            approved_min=extraction.get("approved_min"),
            approved_max=extraction.get("approved_max"),
            actual_value=extraction.get("actual_value"),
            duration_minutes=extraction.get("duration_minutes"),
            rationale_input=source_text[:4000],
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
                site=extraction.get("site") or "",
                occurrence_date=extraction.get("occurrence_date"),
                title=extraction.get("title") or "Process deviation requiring investigation",
                source=extraction.get("source") or "Internal Deviation",
                product=extraction.get("product") or "General API",
                batch=extraction.get("batch") or "BATCH-PENDING",
                severity=recommendation.get("severity", "Medium"),  # type: ignore[arg-type]
                status="Under Review",
                owner="AIVOA AI",
                parameter=extraction.get("parameter") or "",
                approved_min=extraction.get("approved_min"),
                approved_max=extraction.get("approved_max"),
                actual_value=extraction.get("actual_value"),
                duration_minutes=extraction.get("duration_minutes"),
                description=extraction.get("description") or source_text[:1000],
                actions="",
                initial_impact=extraction.get("initial_impact") or "Potential Quality Impact",
                review_required=True,
                document_id=document_id,
            ),
            evidence=evidence,
        )
        similar_cases = await self.deviation_service.similar_cases(created.id)
        trace_id = self.workflow_trace_service.save_trace(state.trace)
        return AnalyzeResponse(
            deviation_id=created.id,
            recommendation=recommendation.get("severity", "Medium"),  # type: ignore[arg-type]
            rationale=recommendation.get("rationale", "No rationale provided."),
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
        number = r"(-?\d+(?:\.\d+)?)"
        actual = self._first_float(
            rf"(?:actual(?:\s+(?:temperature|value))?|reached|increased\s+to|decreased\s+to|recorded(?:\s+at)?|measured(?:\s+at)?)\s*(?:was|of|to|:|=)?\s*{number}\s*(?:°?C|°?F|bar|psi|rpm|kg|%|mg/mL)",
            text,
        )
        approved_range = re.search(
            r"(?:approved|acceptable|specified|operating)\s+(?:temperature\s+)?(?:range|limits?)\s*(?:is|of|:|=)?\s*(-?\d+(?:\.\d+)?)\s*(?:°?[CF]|bar|psi|%)?\s*(?:-|–|—|to)\s*(-?\d+(?:\.\d+)?)\s*(?:°?[CF]|bar|psi|%)?",
            text,
            re.IGNORECASE,
        )
        approved_max = float(approved_range.group(2)) if approved_range else self._first_float(
            r"(?:approved\s+)?(?:upper\s+)?(?:limit|max(?:imum)?)\s*(?:of|is|:|=)?\s*(-?\d+(?:\.\d+)?)",
            text,
        )
        approved_min = float(approved_range.group(1)) if approved_range else None
        duration_match = re.search(r"(\d+)\s*(minutes?|mins?|hours?|hrs?|min|h)\b", text, re.IGNORECASE)
        duration = None
        if duration_match:
            duration = int(duration_match.group(1))
            if duration_match.group(2).lower().startswith(("hour", "hr")) or duration_match.group(2).lower() == "h":
                duration *= 60

        if actual is None:
            actual = self._first_float(
                r"(-?\d+(?:\.\d+)?)\s*(?:°?C|°?F|bar|psi|rpm|kg|%|mg/mL)",
                text,
            )

        site = (self._first_group(r"(?:site|plant)\s*[:#-]\s*([^\n\r]+)", text) or "")[:255]
        raw_source = self._first_group(r"source\s*[:#-]\s*([^\n\r]+)", text) or ""
        source = self._classify_source(raw_source)
        raw_impact = self._first_group(r"impact\s*[:#-]\s*([^\n\r]+)", text) or ""
        initial_impact = self._classify_impact(raw_impact)
        occurrence_date = self._extract_date(text)

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
            "title": "Temperature excursion during API processing",
            "site": site,
            "occurrence_date": occurrence_date,
            "source": source,
            "initial_impact": initial_impact,
            "product": product[:100],
            "batch": batch[:64],
            "parameter": parameter[:120],
            "actual_value": actual,
            "approved_max": approved_max,
            "approved_min": approved_min,
            "duration_minutes": duration,
            "description": text[:1000],
            "fields": fields,
        }

    def _detect_conflict(self, extraction: dict) -> bool:
        approved_min = extraction.get("approved_min")
        approved_max = extraction.get("approved_max")
        actual = extraction.get("actual_value")
        if actual is None:
            return False
        below_min = approved_min is not None and actual < approved_min
        above_max = approved_max is not None and actual > approved_max
        return not (below_min or above_max)

    @staticmethod
    def _extract_date(text: str) -> date | None:
        match = re.search(r"(?:date|occurred\s+on)\s*[:#-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
        if not match:
            return None
        value = match.group(1)
        try:
            if "/" in value:
                month, day, year = value.split("/")
                return date(int(year), int(month), int(day))
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _classify_source(value: str) -> str:
        normalized = value.lower()
        if "customer" in normalized or "complaint" in normalized:
            return "Customer Complaint"
        if "audit" in normalized or "observation" in normalized:
            return "Audit Observation"
        if "vendor" in normalized or "supplier" in normalized:
            return "Vendor Deviation"
        return "Internal Deviation"

    @staticmethod
    def _classify_impact(value: str) -> str:
        normalized = value.lower()
        if "critical" in normalized or "safety" in normalized:
            return "Critical Safety Risk"
        if "major" in normalized:
            return "Major Product Impact"
        if "minor" in normalized or "no impact" in normalized:
            return "Minor Impact"
        return "Potential Quality Impact"

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
