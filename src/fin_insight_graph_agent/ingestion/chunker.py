from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1

from fin_insight_graph_agent.ingestion.document_normalizer import NormalizedDocument


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    chunk_text: str
    start_offset: int
    end_offset: int
    citation_label: str
    batch_id: str
    version: int


def chunk_document(
    document: NormalizedDocument,
    chunk_size: int,
    overlap: int,
) -> list[DocumentChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[DocumentChunk] = []
    start = 0
    text = document.text

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        chunk_id = sha1(
            f"{document.document_id}:{document.version}:{start}:{end}".encode()
        ).hexdigest()[:16]
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                chunk_text=chunk_text,
                start_offset=start,
                end_offset=end,
                citation_label=f"{document.title}:{start}-{end}",
                batch_id=document.batch_id,
                version=document.version,
            )
        )
        if end == len(text):
            break
        start = end - overlap

    return chunks