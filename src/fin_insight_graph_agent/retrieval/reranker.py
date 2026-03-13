from __future__ import annotations

from time import perf_counter
from typing import Any

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.ingestion.connectors.http_transport import HttpTransport
from fin_insight_graph_agent.observability.metrics import RERANKER_LATENCY_SECONDS
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
        self._base_url = base_url.rstrip("/")
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
        return _parse_rerank_response(response, len(documents))


class DashScopeTextRerankerClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        instruct: str = "",
        transport: HttpTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._instruct = instruct.strip()
        self._transport = transport or HttpTransport()

    def score(self, query: str, documents: list[str]) -> list[float]:
        response = self._transport.post_json(
            self._request_url(),
            payload=self._build_payload(query, documents),
            headers=_authorization_headers(self._api_key),
        )
        if response.get("code") and response.get("message"):
            raise ValueError(
                f"DashScope reranker error {response['code']}: {response['message']}"
            )
        return _parse_rerank_response(response, len(documents))

    def _request_url(self) -> str:
        if self._base_url.endswith("/reranks") or self._base_url.endswith("/text-rerank"):
            return self._base_url
        if self._uses_qwen_compatible_api():
            return f"{self._base_url}/compatible-api/v1/reranks"
        return f"{self._base_url}/api/v1/services/rerank/text-rerank/text-rerank"

    def _build_payload(self, query: str, documents: list[str]) -> dict[str, Any]:
        if self._uses_qwen_compatible_api():
            payload: dict[str, Any] = {
                "model": self._model,
                "query": query,
                "documents": documents,
                "top_n": len(documents),
            }
            if self._instruct:
                payload["instruct"] = self._instruct
            return payload
        return {
            "model": self._model,
            "input": {
                "query": query,
                "documents": documents,
            },
            "parameters": {
                "top_n": len(documents),
                "return_documents": False,
            },
        }

    def _uses_qwen_compatible_api(self) -> bool:
        return self._model.startswith("qwen3-rerank")


class BGEReranker:
    def __init__(self, client=None) -> None:
        self._client = client

    def rank(self, query: str, bundles: list[EvidenceBundle]) -> list[EvidenceBundle]:
        if not bundles:
            return []

        started_at = perf_counter()
        if self._client is not None:
            scores = self._client.score(query, [bundle.content for bundle in bundles])
        else:
            query_terms = set(_tokenize(query))
            scores = [
                float(len(query_terms.intersection(_tokenize(bundle.content))))
                for bundle in bundles
            ]
        RERANKER_LATENCY_SECONDS.observe(perf_counter() - started_at)

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
    if settings.reranker_provider == "dashscope":
        reranker_url = settings.reranker_api_url
        if reranker_url == "http://127.0.0.1:8001/rerank":
            reranker_url = "https://dashscope.aliyuncs.com"
        reranker_key = settings.reranker_api_key or settings.model_api_key
        return BGEReranker(
            DashScopeTextRerankerClient(
                base_url=reranker_url,
                model=settings.reranker_model,
                api_key=reranker_key,
                instruct=settings.reranker_instruct,
            )
        )
    return BGEReranker()


def _parse_rerank_response(response: dict[str, Any], document_count: int) -> list[float]:
    if "scores" in response:
        scores = [float(value) for value in response["scores"]]
        if len(scores) != document_count:
            raise ValueError("Reranker returned score count that does not match documents")
        return scores

    results = _extract_results(response)
    if results is None:
        raise KeyError("Reranker response missing scores")
    return _scores_from_results(results, document_count)


def _extract_results(response: dict[str, Any]) -> list[dict[str, Any]] | None:
    if isinstance(response.get("results"), list):
        return response["results"]
    output = response.get("output")
    if isinstance(output, dict) and isinstance(output.get("results"), list):
        return output["results"]
    return None


def _scores_from_results(results: list[dict[str, Any]], document_count: int) -> list[float]:
    scores = [0.0] * document_count
    seen_indexes: set[int] = set()
    for position, item in enumerate(results):
        index_value = item.get("index", position)
        if isinstance(item.get("document"), dict) and "index" in item["document"]:
            index_value = item["document"]["index"]
        index = int(index_value)
        if index < 0 or index >= document_count:
            raise ValueError("Reranker returned document index out of range")

        score_value = item.get("relevance_score")
        if score_value is None:
            score_value = item.get("score", item.get("relevanceScore"))
        if score_value is None:
            raise KeyError("Reranker result missing score")

        scores[index] = float(score_value)
        seen_indexes.add(index)

    if not seen_indexes:
        raise ValueError("Reranker returned no scored results")
    return scores