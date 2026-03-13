from __future__ import annotations

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.ingestion.connectors.http_transport import HttpTransport
from fin_insight_graph_agent.retrieval.embeddings import _authorization_headers, _tokenize


class HttpBGERerankerClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "",
        transport: HttpTransport | None = None,
    ) -> None:
        self._base_url = base_url
        self._model = model
        self._api_key = api_key
        self._transport = transport or HttpTransport()

    def score(self, query: str, documents: list[str]) -> list[float]:
        response = self._transport.post_json(
            self._base_url,
            payload={
                "model": self._model,
                "query": query,
                "documents": documents,
            },
            headers=_authorization_headers(self._api_key),
        )
        if "scores" in response:
            return [float(value) for value in response["scores"]]
        if "results" in response:
            return [float(item["score"]) for item in response["results"]]
        raise KeyError("Reranker response missing scores")


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


def build_reranker(settings: AppSettings) -> BGEReranker:
    if settings.reranker_provider == "http_bge":
        return BGEReranker(
            HttpBGERerankerClient(
                base_url=settings.reranker_api_url,
                model=settings.reranker_model,
                api_key=settings.reranker_api_key,
            )
        )
    return BGEReranker()