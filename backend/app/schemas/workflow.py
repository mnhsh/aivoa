from pydantic import BaseModel


class WorkflowTraceOut(BaseModel):
    trace_id: str
    steps: list[dict]
