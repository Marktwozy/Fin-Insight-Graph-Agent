from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = '0004_eval_run_model_version'
down_revision = '0003_batch_quality_gate_runs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'eval_runs',
        sa.Column('model_version', sa.String(length=128), nullable=False, server_default='heuristic'),
    )


def downgrade() -> None:
    op.drop_column('eval_runs', 'model_version')