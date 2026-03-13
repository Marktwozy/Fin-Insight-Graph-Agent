from fin_insight_graph_agent.agent.state import AgentState
from fin_insight_graph_agent.memory.checkpointer import MemoryCheckpointer
from fin_insight_graph_agent.memory.models import ShortTermMemorySnapshot
from fin_insight_graph_agent.memory.repository import MemoryRepository


def test_checkpointer_roundtrip(db_engine):
    repository = MemoryRepository(db_engine)
    checkpointer = MemoryCheckpointer(repository)
    snapshot = ShortTermMemorySnapshot(
        confirmed_facts=["TSMC announced maintenance"],
        open_hypotheses=["NVIDIA lead times may increase"],
        entities=["company:tsmc", "company:nvda"],
        event_timeline=["2026-03-12 maintenance event"],
        market_snapshot={"ticker": "NVDA"},
        evidence_pointers=["chunk-1"],
        pending_questions=["Which customers depend on this fab?"],
        confidence_notes=["Secondary impact is not yet confirmed"],
    )
    state: AgentState = {
        "request_id": "req-1",
        "route": "research",
        "question": "What are the impacts?",
        "batch_id": "batch-20260313",
        "evidence": [],
        "short_term_memory": snapshot,
        "final_response": None,
    }

    checkpointer.save("session-1", state)
    restored = checkpointer.load("session-1")

    assert restored is not None
    assert restored["short_term_memory"].confirmed_facts == ["TSMC announced maintenance"]