from fin_insight_graph_agent.agent.graphs.research import build_research_graph
from fin_insight_graph_agent.common.models import EvidenceBundle


class IntegrationTextRetriever:
    def search(self, query, batch_id, limit=5):
        return [
            EvidenceBundle(
                evidence_id="text-1",
                source_type="filing",
                content="NVIDIA disclosed supply constraints at advanced packaging partners.",
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


def test_research_flow_returns_citations_and_response():
    graph = build_research_graph(IntegrationDependencies())
    result = graph.invoke(
        {"question": "Summarize NVIDIA supply risks", "batch_id": "batch-20260313"}
    )

    assert result["citations"] == [{"doc_id": "doc-1", "chunk_id": "chunk-1"}]
    assert "NVIDIA" in result["final_response"]