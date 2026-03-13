from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Any

from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.ingestion.connectors.http_transport import HttpTransport


class SimpleDenseEmbedder:
    def __init__(self, dimensions: int = 16) -> None:
        self.dimensions = dimensions

    def encode(self, text: str) -> list[float]:
        tokens = [token for token in _tokenize(text) if token]
        vector = [0.0] * self.dimensions
        for token, count in Counter(tokens).items():
            vector[hash(token) % self.dimensions] += float(count)

        norm = sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class OpenAICompatibleDenseEmbedder:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        dimensions: int,
        api_key: str = "",
        transport: HttpTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self.dimensions = dimensions
        self._api_key = api_key
        self._transport = transport or HttpTransport()

    def encode(self, text: str) -> list[float]:
        payload = {
            "model": self._model,
            "input": text,
        }
        response = self._transport.post_json(
            f"{self._base_url}/embeddings",
            payload=payload,
            headers=_authorization_headers(self._api_key),
        )
        data = response["data"][0]["embedding"]
        return [float(value) for value in data]


def build_dense_embedder(settings: AppSettings) -> Any:
    if settings.embedding_provider == "openai_compatible":
        return OpenAICompatibleDenseEmbedder(
            base_url=settings.model_api_base_url,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            api_key=settings.model_api_key,
        )
    return SimpleDenseEmbedder(dimensions=settings.embedding_dimensions)


def _authorization_headers(api_key: str) -> dict[str, str]:
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def _tokenize(text: str) -> list[str]:
    normalized = "".join(char.lower() if char.isalnum() else " " for char in text)
    return [token for token in normalized.split() if token]