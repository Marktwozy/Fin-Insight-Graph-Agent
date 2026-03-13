from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from fin_insight_graph_agent.common.clock import utc_now
from fin_insight_graph_agent.storage.base import Base


class MarketDailyBar(Base):
    __tablename__ = "market_daily_bars"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    trade_date: Mapped[date] = mapped_column(Date)
    open_price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    high_price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    low_price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    close_price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    volume: Mapped[int] = mapped_column()
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )