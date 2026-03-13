from __future__ import annotations

from collections import Counter

from qdrant_client.http import models

from fin_insight_graph_agent.retrieval.embeddings import _tokenize


class SimpleSparseEncoder:
    def __init__(self, buckets: int = 2048) -> None:
        self.buckets = buckets

    def encode(self, text: str) -> models.SparseVector:
        counts = Counter(_tokenize(text))
        ordered_items = sorted(
            counts.items(),
            key=lambda item: hash(item[0]) % self.buckets,
        )
        indices = [hash(token) % self.buckets for token, _ in ordered_items]
        values = [float(count) for _, count in ordered_items]
        return models.SparseVector(indices=indices, values=values)