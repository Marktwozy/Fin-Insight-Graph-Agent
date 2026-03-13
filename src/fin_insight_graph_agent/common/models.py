from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvidenceBundle(BaseModel):
    evidence_id: str
    source_type: str
    content: str
    score_raw: float
    score_reranked: float | None = None
    entity_refs: list[str] = Field(default_factory=list)
    time_refs: list[str] = Field(default_factory=list)
    market_refs: list[str] = Field(default_factory=list)
    citation_payload: dict[str, Any]
    batch_id: str
    retrieval_path: str