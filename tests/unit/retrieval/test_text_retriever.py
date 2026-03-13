from fin_insight_graph_agent.retrieval.text_retriever import TextRetriever


class FakeQdrantClient:
    def query(self, collection_name, dense_vector, sparse_vector, limit, batch_id):
        return [
            {
                "id": "chunk-1",
                "payload": {
                    "content": "Capacity constraints remain elevated.",
                    "entity_refs": ["company:nvda"],
                    "time_refs": ["2026-03-13"],
                    "market_refs": ["ticker:NVDA"],
                    "citation_payload": {"doc_id": "doc-1", "chunk_id": "chunk-1"},
                    "batch_id": batch_id,
                    "source_type": "filing",
                },
                "score": 0.81,
            }
        ]


def test_text_retriever_returns_evidence_bundles():
    retriever = TextRetriever(FakeQdrantClient())
    results = retriever.search(
        "Which companies mention capacity constraints?",
        batch_id="batch-20260313",
    )
    assert results[0].retrieval_path == "qdrant.hybrid"