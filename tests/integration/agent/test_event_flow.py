from fin_insight_graph_agent.agent.graphs.event import build_event_graph
from fin_insight_graph_agent.common.models import EvidenceBundle


class IntegrationTextRetriever:
    def search(self, query, batch_id, limit=5):
        return [
            EvidenceBundle(
                evidence_id="text-1",
                source_type="news",
                content=(
                    "A fab maintenance event may tighten advanced packaging "
                    "capacity for NVIDIA."
                ),
                score_raw=0.8,
                score_reranked=None,
                entity_refs=["company:nvda"],
                time_refs=["2026-03-13"],
                market_refs=["ticker:NVDA"],
                citation_payload={"doc_id": "doc-1", "chunk_id": "chunk-1"},
                batch_id=batch_id,
                retrieval_path="qdrant.hybrid",
            )
        ]


class IntegrationGraphRetriever:
    def expand_entities(self, entity_ids, batch_id, limit=5):
        return []


class IntegrationMarketRetriever:
    def search(self, tickers, batch_id, limit=5):
        return []


class PassThroughMerger:
    def merge(self, evidence_lists):
        merged = []
        for evidence_list in evidence_lists:
            merged.extend(evidence_list)
        return merged


class PassThroughReranker:
    def rank(self, query, bundles):
        return bundles


class IntegrationDependencies:
    text_retriever = IntegrationTextRetriever()
    graph_retriever = IntegrationGraphRetriever()
    market_retriever = IntegrationMarketRetriever()
    evidence_merger = PassThroughMerger()
    reranker = PassThroughReranker()


def test_event_flow_returns_uncertainty_aware_response():
    graph = build_event_graph(IntegrationDependencies())
    result = graph.invoke(
        {
            "event_input": "TSMC maintenance may affect advanced packaging for NVIDIA",
            "batch_id": "batch-20260313",
        }
    )

    assert result["citations"] == [{"doc_id": "doc-1", "chunk_id": "chunk-1"}]
    assert "may" in result["final_response"].lower()