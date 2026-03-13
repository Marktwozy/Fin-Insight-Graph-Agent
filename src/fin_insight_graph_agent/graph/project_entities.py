from __future__ import annotations

from dataclasses import asdict, dataclass

from fin_insight_graph_agent.graph.neo4j_client import Neo4jGraphClient


@dataclass(slots=True)
class GraphProjectionRecord:
    entity_id: str
    entity_name: str
    entity_type: str
    batch_id: str
    related_event_id: str
    related_event_name: str
    related_topic: str
    ticker: str


class EntityProjector:
    def __init__(self, client: Neo4jGraphClient) -> None:
        self._client = client

    def reset_database(self) -> None:
        self._client.reset_database()

    def project(self, records: list[GraphProjectionRecord]) -> None:
        for record in records:
            self._client.write_projection(asdict(record))