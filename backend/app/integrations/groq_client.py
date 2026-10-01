from __future__ import annotations

import json
from datetime import date
from pydantic import BaseModel, Field
from groq import AsyncGroq
from app.core.config import get_settings
from app.schemas.deviations import Impact, Source


class ExtractionResponse(BaseModel):
    site: str | None = Field(default=None, max_length=255)
    occurrence_date: date | None = None
    title: str = Field(min_length=3, max_length=255, description="A concise, 5-10 word title summarizing the deviation event.")
    source: Source = "Internal Deviation"
    initial_impact: Impact = "Potential Quality Impact"
    description: str = Field(max_length=2000, description="A detailed summary of the event.")
    product: str | None = Field(default=None, max_length=100)
    batch: str | None = Field(default=None, max_length=64)
    parameter: str | None = Field(default=None, max_length=120)
    actual_value: float | None = None
    approved_max: float | None = None
    approved_min: float | None = None
    duration_minutes: int | None = None


class ChatUpdateResponse(BaseModel):
    site: str | None = Field(default=None, max_length=255)
    occurrence_date: date | None = None
    title: str | None = Field(default=None, max_length=255)
    source: Source | None = None
    product: str | None = Field(default=None, max_length=100)
    batch: str | None = Field(default=None, max_length=64)
    parameter: str | None = Field(default=None, max_length=120)
    approved_max: float | None = None
    approved_min: float | None = None
    actual_value: float | None = None
    duration_minutes: int | None = None
    description: str | None = None
    actions: str | None = None
    initial_impact: Impact | None = None
    severity: str | None = None


class InputClassificationResponse(BaseModel):
    is_quality_deviation: bool
    reason: str = Field(min_length=3, max_length=500)



class GroqClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.groq_api_key and not self.settings.demo_mode:
            try:
                self._client = AsyncGroq(api_key=self.settings.groq_api_key)
            except Exception:
                pass

    @property
    def provider_name(self) -> str:
        if self._client is None:
            return "demo"
        return "groq"

    @property
    def model(self) -> str:
        return self.settings.groq_model

    async def recommend_severity(self, *, observed_delta: float, duration_minutes: int, rationale_input: str = "") -> dict:
        rule_severity = "High" if observed_delta >= 3.0 and duration_minutes >= 10 else (
            "Medium" if observed_delta >= 2.0 else "Low"
        )
        if self.provider_name == "demo":
            return {
                "severity": rule_severity,
                "rationale": f"Assessed as {rule_severity} from an excursion of {observed_delta:g} for {duration_minutes} minutes.",
            }

        try:
            prompt = (
                f"Assess severity based on observed delta of {observed_delta} and duration {duration_minutes} mins. "
                f"Deviation context: {rationale_input}. "
                "Consider the parameter-specific relative excursion, duration, affected critical quality attributes, "
                "batch containment, potential product impact, and required QA escalation. A sustained out-of-range "
                "condition that can affect a critical quality attribute and requires a batch hold is at least High. "
                "For temperature excursions, the SOP rule also requires an excursion of at least 3 degrees for at "
                "least 10 minutes to be High or Critical. "
                "Respond in JSON format with two keys: 'severity' (Low, Medium, High, or Critical) and 'rationale' (a 1-2 sentence justification)."
            )
            completion = await self._client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a quality assurance severity assessor. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = completion.choices[0].message.content
            result = json.loads(content)
            severity = str(result.get("severity", rule_severity)).capitalize()
            allowed = ["Low", "Medium", "High", "Critical"]
            if severity not in allowed:
                severity = rule_severity
            if allowed.index(severity) < allowed.index(rule_severity):
                severity = rule_severity
            return {
                "severity": severity,
                "rationale": str(result.get("rationale") or f"Assessed as {severity} under SOP-DEV-004."),
            }
        except Exception as e:
            print(f"Severity Error: {e}")
            return {
                "severity": rule_severity,
                "rationale": f"Assessed as {rule_severity} using the SOP rule because AI reasoning was unavailable.",
            }

    async def extract_deviation_data(self, text: str) -> ExtractionResponse | None:

        if self.provider_name == "demo":
            return None # We will fallback to regex if None is returned

        try:
            prompt = (
                "Extract the deviation details from the document below. Distinguish the observed actual value "
                "from approved minimum and maximum limits, normalize durations to minutes, and preserve negative values. "
                "Return JSON with title, description, product, batch, parameter, actual_value, approved_min, "
                "approved_max, duration_minutes, site, occurrence_date (YYYY-MM-DD), source, and initial_impact. "
                "Classify source as exactly one of: Internal Deviation, Customer Complaint, Audit Observation, or Vendor Deviation. "
                "Classify initial_impact as exactly one of: Minor Impact, Potential Quality Impact, Major Product Impact, or Critical Safety Risk. "
                "Use null when a value is absent.\n\n"
                f"---\n{text}\n---"
            )
            completion = await self._client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a precise data extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = completion.choices[0].message.content
            return ExtractionResponse.model_validate_json(content)
        except Exception as e:
            return None

    async def classify_input(self, text: str) -> InputClassificationResponse | None:
        if self.provider_name == "demo":
            normalized = text.lower()
            technical_markers = (
                "traceback (most recent call last)",
                "exception in asgi application",
                "internal server error",
                "pydantic_core._pydantic_core.validationerror",
                "sqlalchemy.exc.",
            )
            is_technical = any(marker in normalized for marker in technical_markers)
            return InputClassificationResponse(
                is_quality_deviation=not is_technical,
                reason=(
                    "The pasted content is an application error or stack trace, not a manufacturing quality deviation."
                    if is_technical
                    else "The content describes a potential manufacturing or quality deviation."
                ),
            )

        try:
            prompt = (
                "Classify whether the content below describes a pharmaceutical manufacturing or quality deviation "
                "that belongs in a QMS deviation record. Manufacturing events, out-of-specification results, process "
                "excursions, complaints, audit observations, and non-conformances qualify. Software stack traces, "
                "HTTP access logs, source code, API errors, and debugging output do not qualify, even if they contain "
                "words such as deviation, severity, or batch inside copied application output. Return JSON with exactly "
                "two keys: is_quality_deviation (boolean) and reason (a concise explanation).\n\n"
                f"---\n{text[:12000]}\n---"
            )
            completion = await self._client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a strict QMS input classifier. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            return InputClassificationResponse.model_validate_json(completion.choices[0].message.content)
        except Exception:
            return None

    async def process_chat(self, text: str, current_state: dict) -> ChatUpdateResponse:
        if self.provider_name == "demo":
            raise RuntimeError("AI chat is unavailable while DEMO_MODE is enabled")

        try:
            prompt = (
                f"You are modifying a deviation report. The current state is:\n{json.dumps(current_state)}\n\n"
                f"The user says: '{text}'\n"
                "Return only fields the user explicitly requested to change. Allowed fields are site, occurrence_date "
                "(YYYY-MM-DD), title, source, product, batch, parameter, approved_min, approved_max, actual_value, "
                "duration_minutes, description, actions, initial_impact, and severity. Return valid JSON only."
                " Source must be one of Internal Deviation, Customer Complaint, Audit Observation, or Vendor Deviation."
                " Initial impact must be one of Minor Impact, Potential Quality Impact, Major Product Impact, or Critical Safety Risk."
            )
            completion = await self._client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a precise JSON state updater. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return ChatUpdateResponse.model_validate_json(completion.choices[0].message.content)
        except Exception as e:
            raise RuntimeError(f"AI chat update failed: {e}") from e
