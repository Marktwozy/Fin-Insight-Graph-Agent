from __future__ import annotations

from collections import defaultdict

from qdrant_client.http import models

from fin_insight_graph_agent.retrieval.embeddings import _tokenize


class SimpleSparseEncoder:
    def __init__(self, buckets: int = 2048) -> None:
        self.buckets = buckets

    def encode(self, text: str) -> models.SparseVector:
        bucket_totals: dict[int, float] = defaultdict(float)
        for token in _tokenize(text):
            bucket_index = hash(token) % self.buckets
            bucket_totals[bucket_index] += 1.0

        ordered_items = sorted(bucket_totals.items(), key=lambda item: item[0])
        indices = [index for index, _ in ordered_items]
        values = [value for _, value in ordered_items]
        return models.SparseVector(indices=indices, values=values)