from __future__ import annotations

from hashlib import sha1

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord
from fin_insight_graph_agent.storage.models.market import MarketDailyBar


class MarketRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert_daily_bars(self, bars: list[DailyBarRecord], batch_id: str) -> None:
        with Session(self._engine) as session:
            for bar in bars:
                market_bar = MarketDailyBar(
                    id=sha1(f"{bar.ticker}:{bar.trade_date}:{batch_id}".encode()).hexdigest()[:16],
                    ticker=bar.ticker,
                    trade_date=bar.trade_date,
                    open_price=bar.open_price,
                    high_price=bar.high_price,
                    low_price=bar.low_price,
                    close_price=bar.close_price,
                    volume=bar.volume,
                    batch_id=batch_id,
                    version=1,
                )
                session.merge(market_bar)
            session.commit()