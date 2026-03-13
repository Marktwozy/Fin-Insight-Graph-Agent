from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1

from qdrant_client.http import models

from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.retrieval.embeddings import build_dense_embedder
from fin_insight_graph_agent.retrieval.qdrant_client import QdrantSearchClient, build_qdrant_client
from fin_insight_graph_agent.retrieval.sparse_encoder import SimpleSparseEncoder


@dataclass(slots=True)
class ChunkIndexRecord:
    chunk_id: str
    doc_id: str
    content: str
    source_type: str
    ticker: str
    publish_date: str
    batch_id: str
    entity_refs: list[str]
    time_refs: list[str]
    market_refs: list[str]


class QdrantChunkIndexer:
    def __init__(
        self,
        client: QdrantSearchClient,
        dense_embedder=None,
        sparse_encoder=None,
    ) -> None:
        self._client = client
        self._dense_embedder = dense_embedder or client.dense_embedder
        self._sparse_encoder = sparse_encoder or client.sparse_encoder

    def recreate_collection(self, collection_name: str) -> None:
        self._client.recreate_collection(collection_name)

    def ensure_collection(self, collection_name: str) -> None:
        self._client.ensure_collection(collection_name)

    def index(self, collection_name: str, records: list[ChunkIndexRecord]) -> None:
        points: list[models.PointStruct] = []
        for record in records:
            point_id = int(sha1(record.chunk_id.encode()).hexdigest()[:15], 16)
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        'dense': self._dense_embedder.encode(record.content),
                        'sparse': self._sparse_encoder.encode(record.content),
                    },
                    payload={
                        'doc_id': record.doc_id,
                        'chunk_id': record.chunk_id,
                        'content': record.content,
                        'source_type': record.source_type,
                        'ticker': record.ticker,
                        'publish_date': record.publish_date,
                        'batch_id': record.batch_id,
                        'entity_refs': record.entity_refs,
                        'time_refs': record.time_refs,
                        'market_refs': record.market_refs,
                        'citation_payload': {
                            'doc_id': record.doc_id,
                            'chunk_id': record.chunk_id,
                        },
                    },
                )
            )
        self._client.upsert(collection_name, points)


def build_chunk_indexer(settings: AppSettings) -> QdrantChunkIndexer:
    dense_embedder = build_dense_embedder(settings)
    client = build_qdrant_client(
        dense_embedder=dense_embedder,
        sparse_encoder=SimpleSparseEncoder(),
    )
    return QdrantChunkIndexer(client)