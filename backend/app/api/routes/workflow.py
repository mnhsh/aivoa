from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import workflow_traces
from app.schemas.workflow import WorkflowTraceOut

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/trace/{trace_id}", response_model=WorkflowTraceOut)
async def get_trace(trace_id: str) -> WorkflowTraceOut:
    steps = workflow_traces.get_trace(trace_id)
    if not steps:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return WorkflowTraceOut(trace_id=trace_id, steps=steps)
