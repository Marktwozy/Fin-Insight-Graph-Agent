from fin_insight_graph_agent.memory.models import ShortTermMemorySnapshot


def test_short_term_memory_snapshot_tracks_hypotheses_separately_from_facts():
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
    assert snapshot.open_hypotheses != snapshot.confirmed_facts