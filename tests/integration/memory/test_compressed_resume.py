from fin_insight_graph_agent.memory.checkpointer import MemoryCheckpointer
from fin_insight_graph_agent.memory.compression import compress_state
from fin_insight_graph_agent.memory.repository import MemoryRepository


def test_compressed_resume(db_engine, sample_agent_state):
    repository = MemoryRepository(db_engine)
    checkpointer = MemoryCheckpointer(repository)

    compressed = compress_state(sample_agent_state, max_messages=8)
    sample_agent_state["short_term_memory"] = compressed

    checkpointer.save("session-compressed", sample_agent_state)
    restored = checkpointer.load("session-compressed")

    assert restored is not None
    assert restored["short_term_memory"].evidence_pointers == ["chunk-1", "chunk-2"]