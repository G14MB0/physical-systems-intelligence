from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Protocol

import httpx

TOKEN_RE = re.compile(r"[a-zA-Z0-9-]+")
DEFAULT_HASH_DIMENSIONS = 64


class EmbeddingProvider(Protocol):
    name: str
    model_name: str
    dimensions: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class HashEmbeddingProvider:
    name = "hash"

    def __init__(self, dimensions: int = DEFAULT_HASH_DIMENSIONS) -> None:
        self.dimensions = dimensions
        self.model_name = f"hash-{dimensions}"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            digest = hashlib.sha1(token.encode()).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimensions
            vector[index] += 1.0
        return _normalize(vector)


class FastEmbedProvider:
    name = "fastembed"

    def __init__(self, model_name: str, dimensions: int) -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError(
                "fastembed is required for EMBEDDING_PROVIDER=fastembed. "
                "Install backend dependencies or use EMBEDDING_PROVIDER=hash for tests."
            ) from exc
        self.dimensions = dimensions
        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_coerce_vector(vector) for vector in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class OpenAIEmbeddingProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model_name: str,
        dimensions: int,
        post: Any | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for EMBEDDING_PROVIDER=openai.")
        self.dimensions = dimensions
        self.model_name = model_name
        self.api_key = api_key
        self.post = post or httpx.post
        self.timeout_seconds = timeout_seconds

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model_name, "input": texts, "dimensions": self.dimensions},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return [_coerce_vector(item["embedding"]) for item in data["data"]]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


def build_embedding_provider(
    *,
    provider_name: str,
    model_name: str,
    dimensions: int,
    openai_api_key: str = "",
    openai_model_name: str = "text-embedding-3-small",
) -> EmbeddingProvider:
    normalized = provider_name.lower().strip()
    if normalized == "hash":
        return HashEmbeddingProvider(dimensions=dimensions)
    if normalized == "fastembed":
        return FastEmbedProvider(model_name=model_name, dimensions=dimensions)
    if normalized == "openai":
        return OpenAIEmbeddingProvider(
            api_key=openai_api_key,
            model_name=openai_model_name,
            dimensions=dimensions,
        )
    raise ValueError(f"Unsupported embedding provider: {provider_name}")


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _coerce_vector(vector: Any) -> list[float]:
    return [float(value) for value in vector]
