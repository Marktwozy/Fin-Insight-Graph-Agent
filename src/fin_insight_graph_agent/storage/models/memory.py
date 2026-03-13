from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from fin_insight_graph_agent.common.clock import utc_now
from fin_insight_graph_agent.storage.base import Base


class MemoryShortSnapshot(Base):
    __tablename__ = "memory_short_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_payload: Mapped[dict] = mapped_column(JSON)
    trace_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )