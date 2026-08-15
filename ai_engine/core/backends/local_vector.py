"""VectorPort — index vectoriel local. numpy si dispo, sinon pur Python (fallback).

Persisté en JSON sous <home>/vectors/<ns>.json. Suffisant pour du standalone ;
remplaçable par sqlite-vec/FAISS (extra `vector`) ou pgvector (couplage Platform).
"""

from __future__ import annotations

import json
import math
import threading
from pathlib import Path

try:  # accélération optionnelle
    import numpy as _np
except Exception:  # pragma: no cover
    _np = None


def _cosine(a: list[float], b: list[float]) -> float:
    if _np is not None:
        va, vb = _np.asarray(a, dtype=float), _np.asarray(b, dtype=float)
        denom = float(_np.linalg.norm(va) * _np.linalg.norm(vb)) or 1.0
        return float(va @ vb) / denom
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class LocalVector:
    def __init__(self, base_dir: Path) -> None:
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: dict[str, dict[str, dict]] = {}

    def _path(self, ns: str) -> Path:
        return self._dir / f"{ns}.json"

    def _load(self, ns: str) -> dict[str, dict]:
        if ns not in self._cache:
            p = self._path(ns)
            self._cache[ns] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        return self._cache[ns]

    def _flush(self, ns: str) -> None:
        self._path(ns).write_text(json.dumps(self._cache[ns], ensure_ascii=False), encoding="utf-8")

    def upsert(self, ns: str, id: str, vector: list[float], meta: dict) -> None:
        with self._lock:
            store = self._load(ns)
            store[id] = {"vector": vector, "meta": meta}
            self._flush(ns)

    def search(self, ns: str, vector: list[float], k: int = 5) -> list[dict]:
        with self._lock:
            store = self._load(ns)
        scored = [
            {"id": _id, "score": _cosine(vector, rec["vector"]), "meta": rec["meta"]}
            for _id, rec in store.items()
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]

    def delete(self, ns: str, id: str) -> bool:
        with self._lock:
            store = self._load(ns)
            if id in store:
                del store[id]
                self._flush(ns)
                return True
        return False
