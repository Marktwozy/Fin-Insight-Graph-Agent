from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.storage.models.market import MarketDailyBar


class MarketContextRetriever:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def search(self, tickers: list[str], batch_id: str, limit: int = 5) -> list[EvidenceBundle]:
        statement = (
            select(MarketDailyBar)
            .where(MarketDailyBar.ticker.in_(tickers))
            .where(MarketDailyBar.batch_id == batch_id)
            .limit(limit)
        )
        with Session(self._engine) as session:
            rows = session.scalars(statement).all()
        return [
            EvidenceBundle(
                evidence_id=row.id,
                source_type="market",
                content=(
                    f"{row.ticker} traded on {row.trade_date} with open {row.open_price} "
                    f"and close {row.close_price}."
                ),
                score_raw=0.5,
                score_reranked=None,
                entity_refs=[f"company:{row.ticker.lower()}"] if row.ticker else [],
                time_refs=[str(row.trade_date)],
                market_refs=[f"ticker:{row.ticker}"],
                citation_payload={"ticker": row.ticker, "trade_date": str(row.trade_date)},
                batch_id=row.batch_id,
                retrieval_path="postgres.market",
            )
            for row in rows
        ]