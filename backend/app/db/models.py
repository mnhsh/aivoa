from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120), default="text/plain")
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    text_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deviations: Mapped[list["Deviation"]] = relationship(back_populates="document")


class Deviation(Base):
    __tablename__ = "deviations"
    __table_args__ = (UniqueConstraint("code", name="uq_deviations_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(32), index=True)
    site: Mapped[str] = mapped_column(String(255), default="")
    occurrence_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(64), default="Internal Deviation")
    product: Mapped[str] = mapped_column(String(100), index=True)
    batch: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(32), default="Draft", index=True)
    owner: Mapped[str] = mapped_column(String(120), default="AIVOA AI")
    parameter: Mapped[str] = mapped_column(String(120), default="Unknown")
    approved_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    approved_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    actions: Mapped[str] = mapped_column(Text, default="")
    initial_impact: Mapped[str] = mapped_column(String(64), default="Potential Quality Impact")
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=True)
    analysis_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    conflict_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True)

    document: Mapped[Document | None] = relationship(back_populates="deviations")
    evidence_items: Mapped[list["Evidence"]] = relationship(back_populates="deviation", cascade="all, delete-orphan")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="deviation", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    deviation_id: Mapped[str] = mapped_column(ForeignKey("deviations.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(String(255))
    meta: Mapped[str] = mapped_column(String(255))
    relevance: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String(32))
    citation: Mapped[str] = mapped_column(String(255))

    deviation: Mapped[Deviation] = relationship(back_populates="evidence_items")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    deviation_id: Mapped[str] = mapped_column(ForeignKey("deviations.id"), index=True)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deviation: Mapped[Deviation] = relationship(back_populates="audit_events")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    external_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
