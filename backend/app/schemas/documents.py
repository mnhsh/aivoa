from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    file_name: str
    mime_type: str
    content_hash: str
    created_at: datetime
    idempotent_reuse: bool = False
