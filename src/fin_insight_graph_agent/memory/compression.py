from __future__ import annotations

from fin_insight_graph_agent.agent.state import AgentState
from fin_insight_graph_agent.memory.models import ShortTermMemorySnapshot


def compress_state(state: AgentState, max_messages: int) -> ShortTermMemorySnapshot:
    if max_messages <= 0:
        raise ValueError("max_messages must be positive")

    existing = state.get("short_term_memory")
    if existing is None:
        evidence_pointers = [bundle.evidence_id for bundle in state.get("evidence", [])]
        return ShortTermMemorySnapshot(evidence_pointers=evidence_pointers)

    evidence_pointers = list(existing.evidence_pointers)
    if not evidence_pointers:
        evidence_pointers = [bundle.evidence_id for bundle in state.get("evidence", [])]

    return ShortTermMemorySnapshot(
        confirmed_facts=list(existing.confirmed_facts),
        open_hypotheses=list(existing.open_hypotheses),
        entities=list(existing.entities),
        event_timeline=list(existing.event_timeline[-max_messages:]),
        market_snapshot=dict(existing.market_snapshot),
        evidence_pointers=evidence_pointers,
        pending_questions=list(existing.pending_questions),
        confidence_notes=list(existing.confidence_notes),
    )