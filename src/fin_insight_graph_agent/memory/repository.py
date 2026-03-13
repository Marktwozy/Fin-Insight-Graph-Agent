from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.memory.models import ShortTermMemorySnapshot
from fin_insight_graph_agent.storage.models.memory import MemoryShortSnapshot


class MemoryRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_snapshot(
        self,
        session_id: str,
        batch_id: str,
        snapshot: ShortTermMemorySnapshot,
    ) -> None:
        with Session(self._engine) as session:
            record = MemoryShortSnapshot(
                id=session_id,
                session_id=session_id,
                snapshot_payload=snapshot.model_dump(),
                trace_summary=None,
                batch_id=batch_id,
                version=1,
            )
            session.merge(record)
            session.commit()

    def load_snapshot(self, session_id: str) -> ShortTermMemorySnapshot | None:
        with Session(self._engine) as session:
            record = session.get(MemoryShortSnapshot, session_id)
            if record is None:
                return None
            return ShortTermMemorySnapshot.model_validate(record.snapshot_payload)