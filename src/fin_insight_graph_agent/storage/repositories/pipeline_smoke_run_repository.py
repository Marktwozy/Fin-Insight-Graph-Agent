from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.storage.models.pipeline_smoke import PipelineSmokeRun


class PipelineSmokeRunRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_run(
        self,
        *,
        batch_id: str,
        target_count: int,
        tickers_payload: list[str],
        status: str = 'running',
        batch_status: str = 'running',
    ) -> PipelineSmokeRun:
        record = PipelineSmokeRun(
            id=uuid.uuid4().hex,
            batch_id=batch_id,
            status=status,
            batch_status=batch_status,
            target_count=target_count,
            tickers_payload=tickers_payload,
            research_payload=None,
            event_payload=None,
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
        batch_status: str,
        research_payload: dict[str, Any] | None,
        event_payload: dict[str, Any] | None,
        error_message: str | None,
        duration_seconds: float,
    ) -> PipelineSmokeRun:
        with Session(self._engine) as session:
            record = session.get(PipelineSmokeRun, run_id)
            if record is None:
                raise ValueError(f'Pipeline smoke run {run_id} not found')
            record.status = status
            record.batch_status = batch_status
            record.research_payload = research_payload
            record.event_payload = event_payload
            record.error_message = error_message
            record.duration_seconds = duration_seconds
            record.completed_at = datetime.now(UTC)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record

    def list_for_batch(self, batch_id: str) -> list[PipelineSmokeRun]:
        with Session(self._engine) as session:
            statement = (
                select(PipelineSmokeRun)
                .where(PipelineSmokeRun.batch_id == batch_id)
                .order_by(PipelineSmokeRun.created_at.asc())
            )
            records = list(session.scalars(statement))
            for record in records:
                session.expunge(record)
            return records