from __future__ import annotations

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.retrieval.embeddings import SimpleDenseEmbedder
from fin_insight_graph_agent.retrieval.sparse_encoder import SimpleSparseEncoder


class TextRetriever:
    def __init__(self, client, collection_name: str = "chunks") -> None:
        self._client = client
        self._collection_name = collection_name
        self._dense_embedder = getattr(client, "dense_embedder", SimpleDenseEmbedder())
        self._sparse_encoder = getattr(client, "sparse_encoder", SimpleSparseEncoder())

    def search(self, query: str, batch_id: str, limit: int = 5) -> list[EvidenceBundle]:
        results = self._client.query(
            collection_name=self._collection_name,
            dense_vector=self._dense_embedder.encode(query),
            sparse_vector=self._sparse_encoder.encode(query),
            limit=limit,
            batch_id=batch_id,
        )
        return [
            EvidenceBundle(
                evidence_id=str(item["id"]),
                source_type=item["payload"]["source_type"],
                content=item["payload"]["content"],
                score_raw=float(item["score"]),
                score_reranked=None,
                entity_refs=item["payload"].get("entity_refs", []),
                time_refs=item["payload"].get("time_refs", []),
                market_refs=item["payload"].get("market_refs", []),
                citation_payload=item["payload"]["citation_payload"],
                batch_id=item["payload"]["batch_id"],
                retrieval_path="qdrant.hybrid",
            )
            for item in results
        ]