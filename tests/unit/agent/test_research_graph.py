from fin_insight_graph_agent.agent.graphs.research import build_research_graph
from fin_insight_graph_agent.common.models import EvidenceBundle


class FakeTextRetriever:
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


class FakeGraphRetriever:
    def expand_entities(self, entity_ids, batch_id, limit=5):
        return []


class FakeMarketRetriever:
    def search(self, tickers, batch_id, limit=5):
        return []


class FakeEvidenceMerger:
    def merge(self, evidence_lists):
        merged = []
        for evidence_list in evidence_lists:
            merged.extend(evidence_list)
        return merged


class FakeReranker:
    def rank(self, query, bundles):
        return bundles


class FakeDependencies:
    text_retriever = FakeTextRetriever()
    graph_retriever = FakeGraphRetriever()
    market_retriever = FakeMarketRetriever()
    evidence_merger = FakeEvidenceMerger()
    reranker = FakeReranker()


def test_research_graph_returns_grounded_response():
    graph = build_research_graph(FakeDependencies())
    result = graph.invoke(
        {"question": "What are the key risks to NVIDIA supply?", "batch_id": "batch-20260313"}
    )
    assert "citations" in result
    assert result["citations"]