from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_batch_publications"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_publications",
        sa.Column("batch_id", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_batch_publications_status", "batch_publications", ["status"])


def downgrade() -> None:
    op.drop_index("ix_batch_publications_status", table_name="batch_publications")
    op.drop_table("batch_publications")