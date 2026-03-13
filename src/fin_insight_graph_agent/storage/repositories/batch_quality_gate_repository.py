from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.storage.models.batch_quality_gate import BatchQualityGateRun


class BatchQualityGateRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_run(
        self,
        *,
        batch_id: str,
        suite_name: str,
        passed: bool,
        metrics_payload: dict[str, float],
        thresholds_payload: dict[str, float],
        threshold_failures_payload: list[dict[str, Any]],
    ) -> BatchQualityGateRun:
        record = BatchQualityGateRun(
            id=uuid.uuid4().hex,
            batch_id=batch_id,
            suite_name=suite_name,
            passed=passed,
            metrics_payload=metrics_payload,
            thresholds_payload=thresholds_payload,
            threshold_failures_payload=threshold_failures_payload,
        )
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def list_for_batch(self, batch_id: str) -> list[BatchQualityGateRun]:
        with Session(self._engine) as session:
            statement = (
                select(BatchQualityGateRun)
                .where(BatchQualityGateRun.batch_id == batch_id)
                .order_by(BatchQualityGateRun.created_at.asc())
            )
            records = list(session.scalars(statement))
            for record in records:
                session.expunge(record)
            return records