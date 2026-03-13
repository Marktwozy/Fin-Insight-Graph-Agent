from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(slots=True)
class DailyBarRecord:
    ticker: str
    trade_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int


def load_daily_bars(path: Path) -> list[DailyBarRecord]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            DailyBarRecord(
                ticker=row["ticker"],
                trade_date=date.fromisoformat(row["trade_date"]),
                open_price=Decimal(row["open_price"]),
                high_price=Decimal(row["high_price"]),
                low_price=Decimal(row["low_price"]),
                close_price=Decimal(row["close_price"]),
                volume=int(row["volume"]),
            )
            for row in reader
        ]