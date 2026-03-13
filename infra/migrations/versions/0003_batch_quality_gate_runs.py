from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_batch_quality_gate_runs"
down_revision = "0002_batch_publications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_quality_gate_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("batch_id", sa.String(length=64), nullable=False),
        sa.Column("suite_name", sa.String(length=128), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("metrics_payload", sa.JSON(), nullable=False),
        sa.Column("thresholds_payload", sa.JSON(), nullable=False),
        sa.Column("threshold_failures_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_batch_quality_gate_runs_batch_id",
        "batch_quality_gate_runs",
        ["batch_id"],
    )
    op.create_index(
        "ix_batch_quality_gate_runs_suite_name",
        "batch_quality_gate_runs",
        ["suite_name"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_batch_quality_gate_runs_suite_name",
        table_name="batch_quality_gate_runs",
    )
    op.drop_index(
        "ix_batch_quality_gate_runs_batch_id",
        table_name="batch_quality_gate_runs",
    )
    op.drop_table("batch_quality_gate_runs")