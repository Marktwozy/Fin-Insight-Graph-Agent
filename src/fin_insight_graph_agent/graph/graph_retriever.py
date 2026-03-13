from __future__ import annotations

from fin_insight_graph_agent.common.models import EvidenceBundle


class GraphRetriever:
    def __init__(self, client) -> None:
        self._client = client

    def expand_entities(
        self,
        entity_ids: list[str],
        batch_id: str,
        limit: int = 5,
    ) -> list[EvidenceBundle]:
        results = self._client.expand_entities(entity_ids, batch_id=batch_id, limit=limit)
        return [
            EvidenceBundle(
                evidence_id=item["entity_id"],
                source_type=item["source_type"],
                content=item["content"],
                score_raw=float(item["score"]),
                score_reranked=None,
                entity_refs=item["entity_refs"],
                time_refs=item["time_refs"],
                market_refs=item["market_refs"],
                citation_payload=item["citation_payload"],
                batch_id=item["batch_id"],
                retrieval_path="neo4j.neighborhood",
            )
            for item in results
        ]