from __future__ import annotations

from typing import TypedDict

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.memory.models import ShortTermMemorySnapshot


class AgentState(TypedDict):
    request_id: str
    route: str
    question: str
    batch_id: str
    evidence: list[EvidenceBundle]
    short_term_memory: ShortTermMemorySnapshot | None
    final_response: str | None