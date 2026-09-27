from datetime import datetime

from pydantic import BaseModel


class Message(BaseModel):
    message: str


class AuditEventOut(BaseModel):
    actor: str
    action: str
    detail: str
    created_at: datetime
