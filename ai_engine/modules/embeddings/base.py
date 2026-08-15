"""Types & protocole d'un générateur d'embeddings."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class EmbedResult(BaseModel):
    vectors: list[list[float]]
    provider: str
    model: str
    dim: int


@runtime_checkable
class Embedder(Protocol):
    name: str

    def available(self) -> bool: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...
