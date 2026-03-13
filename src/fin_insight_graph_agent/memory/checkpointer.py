from __future__ import annotations

from fin_insight_graph_agent.agent.state import AgentState
from fin_insight_graph_agent.memory.repository import MemoryRepository


class MemoryCheckpointer:
    def __init__(self, repository: MemoryRepository) -> None:
        self._repository = repository

    def save(self, session_id: str, state: AgentState) -> None:
        snapshot = state.get("short_term_memory")
        if snapshot is None:
            raise ValueError("short_term_memory is required for checkpointing")
        self._repository.save_snapshot(session_id, state["batch_id"], snapshot)

    def load(self, session_id: str) -> AgentState | None:
        snapshot = self._repository.load_snapshot(session_id)
        if snapshot is None:
            return None
        return {
            "request_id": session_id,
            "route": "restored",
            "question": "",
            "batch_id": "",
            "evidence": [],
            "short_term_memory": snapshot,
            "final_response": None,
        }