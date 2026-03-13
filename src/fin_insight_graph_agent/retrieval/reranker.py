from __future__ import annotations

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.retrieval.embeddings import _tokenize


class BGEReranker:
    def __init__(self, client=None) -> None:
        self._client = client

    def rank(self, query: str, bundles: list[EvidenceBundle]) -> list[EvidenceBundle]:
        if not bundles:
            return []

        if self._client is not None:
            scores = self._client.score(query, [bundle.content for bundle in bundles])
        else:
            query_terms = set(_tokenize(query))
            scores = [
                float(len(query_terms.intersection(_tokenize(bundle.content))))
                for bundle in bundles
            ]

        reranked = [
            bundle.model_copy(update={"score_reranked": float(score)})
            for bundle, score in zip(bundles, scores, strict=True)
        ]
        return sorted(reranked, key=lambda bundle: bundle.score_reranked or 0.0, reverse=True)