from __future__ import annotations

from collections import Counter
from math import sqrt


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


def _tokenize(text: str) -> list[str]:
    normalized = "".join(char.lower() if char.isalnum() else " " for char in text)
    return [token for token in normalized.split() if token]