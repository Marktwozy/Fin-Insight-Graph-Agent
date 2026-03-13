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