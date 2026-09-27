from pydantic import BaseModel, Field

from app.schemas.deviations import EvidenceOut, ExtractedField, Severity


class AnalyzeRequest(BaseModel):
    text: str | None = None
    document_id: str | None = None


class AnalyzeResponse(BaseModel):
    deviation_id: str
    recommendation: Severity
    extracted_fields: list[ExtractedField]
    evidence: list[EvidenceOut]
    similar_cases: list[dict]
    conflict_detected: bool
    trace_id: str
    provider: str
    demo_mode: bool


class AnalyzeStreamRequest(BaseModel):
    text: str = Field(min_length=10)
