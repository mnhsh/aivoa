"""persist deviation form fields

Revision ID: 20261001_02
Revises: 20260926_01
Create Date: 2026-10-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261001_02"
down_revision = "20260926_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deviations", sa.Column("site", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("deviations", sa.Column("occurrence_date", sa.Date(), nullable=True))
    op.add_column(
        "deviations",
        sa.Column("source", sa.String(length=64), nullable=False, server_default="Internal Deviation"),
    )
    op.add_column(
        "deviations",
        sa.Column(
            "initial_impact",
            sa.String(length=64),
            nullable=False,
            server_default="Potential Quality Impact",
        ),
    )


def downgrade() -> None:
    op.drop_column("deviations", "initial_impact")
    op.drop_column("deviations", "source")
    op.drop_column("deviations", "occurrence_date")
    op.drop_column("deviations", "site")
