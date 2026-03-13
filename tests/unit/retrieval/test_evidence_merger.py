from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.retrieval.evidence_merger import EvidenceMerger


def test_evidence_merger_deduplicates_on_citation_payload():
    merger = EvidenceMerger()
    duplicated = EvidenceBundle(
        evidence_id="e-1",
        source_type="filing",
        content="NVIDIA described supply constraints.",
        score_raw=0.8,
        score_reranked=None,
        entity_refs=["company:nvda"],
        time_refs=["2026-03-13"],
        market_refs=["ticker:NVDA"],
        citation_payload={"doc_id": "doc-1", "chunk_id": "chunk-1"},
        batch_id="batch-20260313",
        retrieval_path="qdrant.hybrid",
    )
    duplicate_copy = duplicated.model_copy(update={"evidence_id": "e-2", "score_raw": 0.7})

    merged = merger.merge([[duplicated], [duplicate_copy]])

    assert len(merged) == 1
    assert merged[0].score_raw == 0.8