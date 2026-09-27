from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AnalysisState:
    text: str
    fields: list[dict] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    recommendation: str = "Medium"
    similar_cases: list[dict] = field(default_factory=list)
    conflict_detected: bool = False
    trace: list[dict] = field(default_factory=list)
