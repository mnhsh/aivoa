"""initial schema

Revision ID: 20260926_01
Revises:
Create Date: 2026-09-26 20:45:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260926_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"], unique=True)

    op.create_table(
        "deviations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("product", sa.String(length=100), nullable=False),
        sa.Column("batch", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("parameter", sa.String(length=120), nullable=False),
        sa.Column("approved_min", sa.Float(), nullable=True),
        sa.Column("approved_max", sa.Float(), nullable=True),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actions", sa.Text(), nullable=False),
        sa.Column("ai_assisted", sa.Boolean(), nullable=False),
        sa.Column("analysis_confidence", sa.Float(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("conflict_flag", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=True),
        sa.UniqueConstraint("code", name="uq_deviations_code"),
    )
    op.create_index("ix_deviations_code", "deviations", ["code"], unique=False)
    op.create_index("ix_deviations_product", "deviations", ["product"], unique=False)
    op.create_index("ix_deviations_batch", "deviations", ["batch"], unique=False)
    op.create_index("ix_deviations_severity", "deviations", ["severity"], unique=False)
    op.create_index("ix_deviations_status", "deviations", ["status"], unique=False)

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deviation_id", sa.String(length=36), sa.ForeignKey("deviations.id"), nullable=False),
        sa.Column("source_id", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.String(length=255), nullable=False),
        sa.Column("meta", sa.String(length=255), nullable=False),
        sa.Column("relevance", sa.Float(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("citation", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_evidence_deviation_id", "evidence", ["deviation_id"], unique=False)
    op.create_index("ix_evidence_source_id", "evidence", ["source_id"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deviation_id", sa.String(length=36), sa.ForeignKey("deviations.id"), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_events_deviation_id", "audit_events", ["deviation_id"], unique=False)

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_id", sa.String(length=80), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_knowledge_documents_external_id", "knowledge_documents", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_knowledge_documents_external_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_audit_events_deviation_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_evidence_source_id", table_name="evidence")
    op.drop_index("ix_evidence_deviation_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_deviations_status", table_name="deviations")
    op.drop_index("ix_deviations_severity", table_name="deviations")
    op.drop_index("ix_deviations_batch", table_name="deviations")
    op.drop_index("ix_deviations_product", table_name="deviations")
    op.drop_index("ix_deviations_code", table_name="deviations")
    op.drop_table("deviations")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_table("documents")
