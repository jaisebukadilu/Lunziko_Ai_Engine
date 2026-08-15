"""Ports de persistance — le cœur ne connaît QUE ces interfaces (jamais Supabase en dur).

C'est le mécanisme d'indépendance : backend local par défaut, adaptateur Postgres/Supabase
optionnel quand l'AI Engine est déployé avec Platform (sans modifier Platform).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StoragePort(Protocol):
    """Stockage clé-valeur namespacé (mémoire, knowledge, registres…)."""

    def get(self, ns: str, key: str) -> dict | None: ...
    def put(self, ns: str, key: str, value: dict) -> None: ...
    def delete(self, ns: str, key: str) -> bool: ...
    def list(self, ns: str) -> list[dict]: ...


@runtime_checkable
class VectorPort(Protocol):
    """Index vectoriel pour embeddings / recherche sémantique."""

    def upsert(self, ns: str, id: str, vector: list[float], meta: dict) -> None: ...
    def search(self, ns: str, vector: list[float], k: int = 5) -> list[dict]: ...
    def delete(self, ns: str, id: str) -> bool: ...


@runtime_checkable
class BlobPort(Protocol):
    """Stockage d'objets binaires (audio, images, documents)."""

    def write(self, key: str, data: bytes) -> str: ...
    def read(self, key: str) -> bytes | None: ...
    def delete(self, key: str) -> bool: ...
