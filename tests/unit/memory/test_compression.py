from fin_insight_graph_agent.memory.compression import compress_state


def test_compress_state_preserves_facts_hypotheses_and_evidence_refs(sample_agent_state):
    snapshot = compress_state(sample_agent_state, max_messages=8)
    assert snapshot.confirmed_facts
    assert snapshot.open_hypotheses
    assert snapshot.evidence_pointers