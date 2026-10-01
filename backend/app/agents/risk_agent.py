from __future__ import annotations

from app.integrations.groq_client import GroqClient


class RiskAgent:
    def __init__(self, groq_client: GroqClient) -> None:
        self.groq_client = groq_client

    async def assess(
        self,
        *,
        approved_min: float | None,
        approved_max: float | None,
        actual_value: float | None,
        duration_minutes: int | None,
        rationale_input: str = "",
    ) -> dict:
        if actual_value is None or duration_minutes is None or (approved_min is None and approved_max is None):
            return {"severity": "Medium", "rationale": "Missing process parameters."}
        upper_delta = max(0.0, actual_value - approved_max) if approved_max is not None else 0.0
        lower_delta = max(0.0, approved_min - actual_value) if approved_min is not None else 0.0
        observed_delta = max(upper_delta, lower_delta)
        return await self.groq_client.recommend_severity(
            observed_delta=observed_delta,
            duration_minutes=duration_minutes,
            rationale_input=rationale_input,
        )
