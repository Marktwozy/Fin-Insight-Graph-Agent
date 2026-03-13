from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.storage.models.daily_batch import DailyBatchRun


class DailyBatchRunRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_run(
        self,
        *,
        batch_id: str,
        target_count: int,
        tickers_payload: list[str],
        status: str = 'running',
    ) -> DailyBatchRun:
        record = DailyBatchRun(
            id=uuid.uuid4().hex,
            batch_id=batch_id,
            status=status,
            target_count=target_count,
            tickers_payload=tickers_payload,
            published=False,
            sync_summary_payload=None,
            validation_payload=None,
            error_message=None,
            duration_seconds=None,
            completed_at=None,
        )
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record

    def complete_run(
        self,
        run_id: str,
        *,
        status: str,
        published: bool,
        sync_summary_payload: dict[str, Any] | None,
        validation_payload: dict[str, Any] | None,
        error_message: str | None,
        duration_seconds: float,
    ) -> DailyBatchRun:
        with Session(self._engine) as session:
            record = session.get(DailyBatchRun, run_id)
            if record is None:
                raise ValueError(f'Daily batch run {run_id} not found')
            record.status = status
            record.published = published
            record.sync_summary_payload = sync_summary_payload
            record.validation_payload = validation_payload
            record.error_message = error_message
            record.duration_seconds = duration_seconds
            record.completed_at = datetime.now(UTC)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record

    def list_for_batch(self, batch_id: str) -> list[DailyBatchRun]:
        with Session(self._engine) as session:
            statement = (
                select(DailyBatchRun)
                .where(DailyBatchRun.batch_id == batch_id)
                .order_by(DailyBatchRun.created_at.asc())
            )
            records = list(session.scalars(statement))
            for record in records:
                session.expunge(record)
            return records