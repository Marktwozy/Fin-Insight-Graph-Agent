from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase

from fin_insight_graph_agent.graph.query_templates import EXPAND_ENTITY_NEIGHBORHOOD


@dataclass(slots=True)
class Neo4jGraphClient:
    driver: Any

    def reset_database(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def write_projection(self, record: dict[str, str]) -> None:
        query = """
        MERGE (company:Company {entity_id: $entity_id})
        SET company.name = $entity_name,
            company.batch_id = $batch_id,
            company.ticker = $ticker
        MERGE (event:Event {event_id: $related_event_id})
        SET event.name = $related_event_name,
            event.batch_id = $batch_id
        MERGE (topic:Topic {name: $related_topic})
        SET topic.batch_id = $batch_id
        MERGE (company)-[:AFFECTS]->(event)
        MERGE (event)-[:BELONGS_TO_TOPIC]->(topic)
        """
        with self.driver.session() as session:
            session.run(query, **record)

    def expand_entities(
        self,
        entity_ids: list[str],
        batch_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        with self.driver.session() as session:
            for entity_id in entity_ids:
                query_results = session.run(
                    EXPAND_ENTITY_NEIGHBORHOOD,
                    entity_id=entity_id,
                    batch_id=batch_id,
                    limit=limit,
                )
                for row in query_results:
                    topic_name = row.get("topic_name") or "unknown topic"
                    event_name = row["event_name"]
                    content = (
                        f"{row['entity_id']} is linked to "
                        f"{event_name} in {topic_name}."
                    )
                    results.append(
                        {
                            "entity_id": row["entity_id"],
                            "content": content,
                            "source_type": "graph",
                            "entity_refs": [row["entity_id"]],
                            "time_refs": [batch_id.removeprefix("batch-")],
                            "market_refs": [f"ticker:{row['ticker']}"]
                            if row.get("ticker")
                            else [],
                            "citation_payload": {
                                "entity_id": row["entity_id"],
                                "event_id": row["event_id"],
                                "event_name": event_name,
                                "topic": topic_name,
                            },
                            "batch_id": batch_id,
                            "score": 1.0,
                        }
                    )
        return results


def build_neo4j_client(
    uri: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> Neo4jGraphClient:
    graph_uri: str = uri if uri is not None else os.getenv(
        "FIGA_NEO4J_URI",
        "bolt://127.0.0.1:7687",
    )
    graph_user: str = username if username is not None else os.getenv(
        "FIGA_NEO4J_USERNAME",
        "neo4j",
    )
    graph_password: str = password if password is not None else os.getenv(
        "FIGA_NEO4J_PASSWORD",
        "password123",
    )
    driver = GraphDatabase.driver(graph_uri, auth=(graph_user, graph_password))
    return Neo4jGraphClient(driver=driver)