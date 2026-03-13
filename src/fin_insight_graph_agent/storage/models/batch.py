from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from fin_insight_graph_agent.common.clock import utc_now
from fin_insight_graph_agent.storage.base import Base


class BatchPublication(Base):
    __tablename__ = "batch_publications"

    batch_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )