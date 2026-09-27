from __future__ import annotations

from app.core.config import get_settings


class GroqClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        if self.settings.demo_mode or not self.settings.groq_api_key:
            return "demo"
        return "groq"

    async def recommend_severity(self, *, observed_delta: float, duration_minutes: int, rationale: str = "") -> str:
        if self.provider_name == "demo":
            if observed_delta >= 3.0 and duration_minutes >= 10:
                return "High"
            if observed_delta >= 2.0:
                return "Medium"
            return "Low"
        # Deterministic local heuristic fallback while preserving provider identity.
        if observed_delta >= 4.0 or duration_minutes >= 20:
            return "Critical"
        if observed_delta >= 3.0:
            return "High"
        if observed_delta >= 1.5:
            return "Medium"
        return "Low"
