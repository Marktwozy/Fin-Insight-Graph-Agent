from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from fin_insight_graph_agent.common.clock import utc_now
from fin_insight_graph_agent.storage.base import Base


class BatchQualityGateRun(Base):
    __tablename__ = "batch_quality_gate_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    suite_name: Mapped[str] = mapped_column(String(128), index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    metrics_payload: Mapped[dict[str, float]] = mapped_column(JSON)
    thresholds_payload: Mapped[dict[str, float]] = mapped_column(JSON)
    threshold_failures_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )