from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RawDocument:
    source_uri: str
    source_type: str
    ticker: str | None
    title: str
    text: str


def load_document(path: Path, source_type: str, ticker: str | None = None) -> RawDocument:
    return RawDocument(
        source_uri=str(path),
        source_type=source_type,
        ticker=ticker,
        title=path.stem,
        text=path.read_text(encoding="utf-8"),
    )