from pydantic import BaseModel, Field


class KnowledgeDocIn(BaseModel):
    external_id: str
    title: str
    content: str
    metadata: dict = Field(default_factory=dict)


class KnowledgeDocOut(BaseModel):
    id: str
    external_id: str
    title: str
    content: str
    metadata: dict


class KnowledgeIndexRequest(BaseModel):
    docs: list[KnowledgeDocIn]
