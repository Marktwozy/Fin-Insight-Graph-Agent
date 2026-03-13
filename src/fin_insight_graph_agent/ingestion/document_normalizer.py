from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1

from fin_insight_graph_agent.ingestion.document_loader import RawDocument


@dataclass(slots=True)
class NormalizedDocument:
    document_id: str
    source_uri: str
    source_type: str
    ticker_tags: list[str]
    publication_date: str
    language: str
    title: str
    text: str
    batch_id: str
    version: int


def normalize_document(raw_document: RawDocument, batch_id: str) -> NormalizedDocument:
    normalized_text = "\n".join(
        line.strip()
        for line in raw_document.text.splitlines()
        if line.strip()
    )
    document_id = sha1(f"{raw_document.source_uri}:{batch_id}".encode()).hexdigest()[:16]
    return NormalizedDocument(
        document_id=document_id,
        source_uri=raw_document.source_uri,
        source_type=raw_document.source_type,
        ticker_tags=[raw_document.ticker] if raw_document.ticker else [],
        publication_date=batch_id.removeprefix("batch-"),
        language="en",
        title=raw_document.title,
        text=normalized_text,
        batch_id=batch_id,
        version=1,
    )