from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import AuditEventOut

Severity = Literal["Low", "Medium", "High", "Critical"]
Status = Literal["Draft", "Under Review", "Investigation", "Closed"]
Source = Literal["Internal Deviation", "Customer Complaint", "Audit Observation", "Vendor Deviation"]
Impact = Literal["Minor Impact", "Potential Quality Impact", "Major Product Impact", "Critical Safety Risk"]


class EvidenceOut(BaseModel):
    source_id: str
    title: str
    detail: str
    meta: str
    relevance: float
    kind: Literal["SOP", "CASE", "MANUAL"]
    citation: str


class ExtractedField(BaseModel):
    label: str
    value: str
    confidence: float
    source: str
    citation: str


class DeviationBase(BaseModel):
    site: str = Field(default="", max_length=255)
    occurrence_date: date | None = None
    title: str = Field(min_length=3, max_length=255)
    source: Source = "Internal Deviation"
    product: str = Field(min_length=1, max_length=100)
    batch: str = Field(min_length=1, max_length=64)
    severity: Severity
    status: Status = "Draft"
    owner: str = Field(default="AIVOA AI", max_length=120)
    parameter: str = Field(max_length=120)
    approved_min: float | None = None
    approved_max: float | None = None
    actual_value: float | None = None
    duration_minutes: int | None = None
    description: str = ""
    actions: str = ""
    initial_impact: Impact = "Potential Quality Impact"
    review_required: bool = True
    review_notes: str | None = None

    @field_validator("duration_minutes")
    @classmethod
    def valid_duration(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("duration_minutes must be >= 0")
        return value


class DeviationCreate(DeviationBase):
    document_id: str | None = None
    source_excerpt: str | None = None


class DeviationUpdate(BaseModel):
    site: str | None = Field(default=None, max_length=255)
    occurrence_date: date | None = None
    title: str | None = Field(default=None, min_length=3, max_length=255)
    source: Source | None = None
    product: str | None = Field(default=None, min_length=1, max_length=100)
    batch: str | None = Field(default=None, min_length=1, max_length=64)
    severity: Severity | None = None
    status: Status | None = None
    owner: str | None = Field(default=None, max_length=120)
    parameter: str | None = Field(default=None, max_length=120)
    approved_min: float | None = None
    approved_max: float | None = None
    actual_value: float | None = None
    duration_minutes: int | None = None
    description: str | None = None
    actions: str | None = None
    initial_impact: Impact | None = None
    review_required: bool | None = None
    review_notes: str | None = None
    expected_version: int


class DeviationOut(DeviationBase):
    id: str
    code: str
    ai_assisted: bool
    analysis_confidence: float
    conflict_flag: bool
    version: int
    document_id: str | None
    source_excerpt: str | None
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceOut] = Field(default_factory=list)
    audit_trail: list[AuditEventOut] = Field(default_factory=list)


class SimilarCaseOut(BaseModel):
    code: str
    title: str
    relevance: float
    status: str


class ReassessRequest(BaseModel):
    rationale: str = Field(min_length=5, max_length=1000)


class ReassessResponse(BaseModel):
    deviation_id: str
    prior_severity: Severity
    recommended_severity: Severity
    provider: str
    demo_mode: bool


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    deviation: DeviationOut
    updated_fields: list[str]
    message: str
    rationale: str | None = None
