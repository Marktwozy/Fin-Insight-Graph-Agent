from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from fin_insight_graph_agent.retrieval.embeddings import SimpleDenseEmbedder
from fin_insight_graph_agent.retrieval.sparse_encoder import SimpleSparseEncoder


@dataclass(slots=True)
class QdrantSearchClient:
    client: QdrantClient
    dense_embedder: Any
    sparse_encoder: SimpleSparseEncoder

    def recreate_collection(self, collection_name: str) -> None:
        if self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)
        self._create_collection(collection_name)

    def ensure_collection(self, collection_name: str) -> None:
        if self.client.collection_exists(collection_name):
            return
        self._create_collection(collection_name)

    def _create_collection(self, collection_name: str) -> None:
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config={
                'dense': models.VectorParams(
                    size=self.dense_embedder.dimensions,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={'sparse': models.SparseVectorParams()},
        )

    def upsert(self, collection_name: str, points: list[models.PointStruct]) -> None:
        self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def query(
        self,
        collection_name: str,
        dense_vector: list[float],
        sparse_vector: models.SparseVector,
        limit: int,
        batch_id: str,
    ) -> list[dict[str, Any]]:
        batch_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key='batch_id',
                    match=models.MatchValue(value=batch_id),
                )
            ]
        )
        response = self.client.query_points(
            collection_name=collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_vector,
                    using='dense',
                    limit=limit,
                    filter=batch_filter,
                ),
                models.Prefetch(
                    query=sparse_vector,
                    using='sparse',
                    limit=limit,
                    filter=batch_filter,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            with_payload=True,
            limit=limit,
        )
        return [
            {'id': point.id, 'payload': point.payload, 'score': point.score}
            for point in response.points
        ]


def build_qdrant_client(
    url: str | None = None,
    *,
    dense_embedder: Any | None = None,
    sparse_encoder: SimpleSparseEncoder | None = None,
) -> QdrantSearchClient:
    qdrant_url = url or os.getenv('FIGA_QDRANT_URL', 'http://127.0.0.1:6333')
    return QdrantSearchClient(
        client=QdrantClient(url=qdrant_url, check_compatibility=False),
        dense_embedder=dense_embedder or SimpleDenseEmbedder(),
        sparse_encoder=sparse_encoder or SimpleSparseEncoder(),
    )