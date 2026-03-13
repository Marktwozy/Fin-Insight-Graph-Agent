from fin_insight_graph_agent.common.models import EvidenceBundle


def test_evidence_bundle_requires_batch_and_citation_payload():
    bundle = EvidenceBundle(
        evidence_id="e-1",
        source_type="news",
        content="chip plant strike expands",
        score_raw=0.75,
        score_reranked=0.88,
        entity_refs=["company:nvda"],
        time_refs=["2026-03-13"],
        market_refs=["ticker:NVDA"],
        citation_payload={"doc_id": "doc-1", "chunk_id": "chunk-1"},
        batch_id="batch-20260313",
        retrieval_path="qdrant.hybrid",
    )
    assert bundle.batch_id == "batch-20260313"