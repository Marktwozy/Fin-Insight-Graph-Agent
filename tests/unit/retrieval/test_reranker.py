from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.retrieval.reranker import BGEReranker


class FakeRerankerClient:
    def score(self, query, passages):
        return [0.2, 0.9]


def test_reranker_orders_results_by_relevance():
    reranker = BGEReranker(FakeRerankerClient())
    bundles = [
        EvidenceBundle(
            evidence_id="e-1",
            source_type="news",
            content="General AI demand remained stable.",
            score_raw=0.3,
            score_reranked=None,
            entity_refs=[],
            time_refs=[],
            market_refs=[],
            citation_payload={"doc_id": "doc-1", "chunk_id": "chunk-1"},
            batch_id="batch-20260313",
            retrieval_path="qdrant.hybrid",
        ),
        EvidenceBundle(
            evidence_id="e-2",
            source_type="filing",
            content="Advanced packaging constraints affected NVIDIA supply.",
            score_raw=0.4,
            score_reranked=None,
            entity_refs=["company:nvda"],
            time_refs=["2026-03-13"],
            market_refs=["ticker:NVDA"],
            citation_payload={"doc_id": "doc-2", "chunk_id": "chunk-2"},
            batch_id="batch-20260313",
            retrieval_path="neo4j.neighborhood",
        ),
    ]

    ranked = reranker.rank("Which suppliers are exposed?", bundles)

    assert ranked[0].score_reranked >= ranked[1].score_reranked
    assert ranked[0].evidence_id == "e-2"