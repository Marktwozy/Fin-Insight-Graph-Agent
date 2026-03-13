from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.storage.models.batch import BatchPublication


class BatchRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_batch(self, batch_id: str, status: str) -> BatchPublication:
        batch = BatchPublication(batch_id=batch_id, status=status)
        with Session(self._engine) as session:
            session.add(batch)
            session.commit()
            session.refresh(batch)
            return batch

    def update_status(self, batch_id: str, status: str) -> BatchPublication:
        with Session(self._engine) as session:
            batch = session.get(BatchPublication, batch_id)
            if batch is None:
                raise ValueError(f"Batch {batch_id} not found")
            batch.status = status
            session.commit()
            session.refresh(batch)
            return batch

    def get_batch(self, batch_id: str) -> BatchPublication:
        with Session(self._engine) as session:
            batch = session.get(BatchPublication, batch_id)
            if batch is None:
                raise ValueError(f"Batch {batch_id} not found")
            session.expunge(batch)
            return batch