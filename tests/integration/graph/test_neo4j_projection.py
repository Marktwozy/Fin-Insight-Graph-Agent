from uuid import uuid4

from fin_insight_graph_agent.graph.graph_retriever import GraphRetriever
from fin_insight_graph_agent.graph.neo4j_client import build_neo4j_client
from fin_insight_graph_agent.graph.project_entities import EntityProjector, GraphProjectionRecord


def test_neo4j_projection_and_retrieval_round_trip():
    client = build_neo4j_client()
    projector = EntityProjector(client)
    projector.reset_database()

    record = GraphProjectionRecord(
        entity_id=f"company:tsmc:{uuid4().hex[:8]}",
        entity_name="TSMC",
        entity_type="Company",
        batch_id="batch-20260313",
        related_event_id="event:fab_maintenance",
        related_event_name="Fab maintenance",
        related_topic="advanced_packaging",
        ticker="TSM",
    )
    projector.project([record])

    retriever = GraphRetriever(client)
    results = retriever.expand_entities([record.entity_id], batch_id="batch-20260313")

    assert results[0].citation_payload["event_id"] == "event:fab_maintenance"
    assert results[0].retrieval_path == "neo4j.neighborhood"