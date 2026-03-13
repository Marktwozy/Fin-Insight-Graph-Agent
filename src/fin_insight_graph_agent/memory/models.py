from __future__ import annotations

from pydantic import BaseModel, Field


class ShortTermMemorySnapshot(BaseModel):
    confirmed_facts: list[str] = Field(default_factory=list)
    open_hypotheses: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    event_timeline: list[str] = Field(default_factory=list)
    market_snapshot: dict[str, str] = Field(default_factory=dict)
    evidence_pointers: list[str] = Field(default_factory=list)
    pending_questions: list[str] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)