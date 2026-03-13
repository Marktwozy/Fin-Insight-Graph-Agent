from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import Any

from fin_insight_graph_agent.ingestion.connectors.http_transport import HttpTransport
from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord


@dataclass(slots=True)
class NewsSentimentArticle:
    title: str
    url: str
    time_published: str
    summary: str
    source: str


@dataclass(slots=True)
class AlphaVantageClient:
    api_key: str
    base_url: str = "https://www.alphavantage.co/query"
    transport: HttpTransport | Any = HttpTransport()

    def fetch_daily_adjusted(
        self,
        symbol: str,
        outputsize: str = "compact",
    ) -> list[DailyBarRecord]:
        response_text = self.transport.get_text(
            self.base_url,
            params={
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "outputsize": outputsize,
                "datatype": "csv",
                "apikey": self.api_key,
            },
        )
        reader = csv.DictReader(StringIO(response_text))
        return [
            DailyBarRecord(
                ticker=symbol,
                trade_date=date.fromisoformat(row["timestamp"]),
                open_price=Decimal(row["open"]),
                high_price=Decimal(row["high"]),
                low_price=Decimal(row["low"]),
                close_price=Decimal(row["adjusted_close"]),
                volume=int(row["volume"]),
            )
            for row in reader
        ]

    def fetch_news_sentiment(
        self,
        tickers: list[str],
        limit: int = 20,
    ) -> list[NewsSentimentArticle]:
        payload = self.transport.get_json(
            self.base_url,
            params={
                "function": "NEWS_SENTIMENT",
                "tickers": ",".join(tickers),
                "sort": "LATEST",
                "limit": str(limit),
                "apikey": self.api_key,
            },
        )
        return [
            NewsSentimentArticle(
                title=item["title"],
                url=item["url"],
                time_published=item["time_published"],
                summary=item.get("summary", ""),
                source=item.get("source", "unknown"),
            )
            for item in payload.get("feed", [])
        ]