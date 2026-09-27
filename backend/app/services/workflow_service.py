from __future__ import annotations

import uuid


class WorkflowTraceService:
    def __init__(self) -> None:
        self._traces: dict[str, list[dict]] = {}

    def save_trace(self, steps: list[dict]) -> str:
        trace_id = str(uuid.uuid4())
        self._traces[trace_id] = steps
        return trace_id

    def get_trace(self, trace_id: str) -> list[dict]:
        return self._traces.get(trace_id, [])
