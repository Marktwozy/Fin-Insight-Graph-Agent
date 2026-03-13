from fin_insight_graph_agent.graph.graph_retriever import GraphRetriever


class FakeNeo4jGraphClient:
    def expand_entities(self, entity_ids, batch_id, limit=5):
        return [
            {
                "entity_id": entity_ids[0],
                "content": (
                    "TSMC is linked to a fab maintenance event "
                    "affecting advanced packaging capacity."
                ),
                "source_type": "graph",
                "entity_refs": [entity_ids[0]],
                "time_refs": ["2026-03-13"],
                "market_refs": ["ticker:TSM"],
                "citation_payload": {
                    "entity_id": entity_ids[0],
                    "event_id": "event:maintenance",
                },
                "batch_id": batch_id,
                "score": 0.77,
            }
        ]


def test_graph_retriever_returns_event_neighbors():
    retriever = GraphRetriever(FakeNeo4jGraphClient())
    results = retriever.expand_entities(["company:tsmc"], batch_id="batch-20260313")
    assert results[0].retrieval_path == "neo4j.neighborhood"