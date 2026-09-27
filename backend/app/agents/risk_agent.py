from __future__ import annotations

from app.integrations.groq_client import GroqClient


class RiskAgent:
    def __init__(self, groq_client: GroqClient) -> None:
        self.groq_client = groq_client

    async def assess(self, *, approved_max: float | None, actual_value: float | None, duration_minutes: int | None) -> str:
        if approved_max is None or actual_value is None or duration_minutes is None:
            return "Medium"
        observed_delta = max(0.0, actual_value - approved_max)
        return await self.groq_client.recommend_severity(observed_delta=observed_delta, duration_minutes=duration_minutes)
