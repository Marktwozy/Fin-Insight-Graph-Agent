from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = '0006_pipeline_smoke_runs'
down_revision = '0005_daily_batch_runs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pipeline_smoke_runs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('batch_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('batch_status', sa.String(length=32), nullable=False),
        sa.Column('target_count', sa.Integer(), nullable=False),
        sa.Column('tickers_payload', sa.JSON(), nullable=False),
        sa.Column('research_payload', sa.JSON(), nullable=True),
        sa.Column('event_payload', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(length=2048), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        'ix_pipeline_smoke_runs_batch_id',
        'pipeline_smoke_runs',
        ['batch_id'],
    )
    op.create_index(
        'ix_pipeline_smoke_runs_status',
        'pipeline_smoke_runs',
        ['status'],
    )
    op.create_index(
        'ix_pipeline_smoke_runs_batch_status',
        'pipeline_smoke_runs',
        ['batch_status'],
    )


def downgrade() -> None:
    op.drop_index('ix_pipeline_smoke_runs_batch_status', table_name='pipeline_smoke_runs')
    op.drop_index('ix_pipeline_smoke_runs_status', table_name='pipeline_smoke_runs')
    op.drop_index('ix_pipeline_smoke_runs_batch_id', table_name='pipeline_smoke_runs')
    op.drop_table('pipeline_smoke_runs')