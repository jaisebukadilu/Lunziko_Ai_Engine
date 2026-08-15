"""MLTrainer — apprentissage supervisé à partir d'exemples (pilier « algorithmes/modèles »).

« Programmes capables d'apprendre à partir des exemples sans être codés pour chaque cas » :
l'utilisateur fournit des paires (texte, label) ; le moteur entraîne un classifieur (embeddings
→ softmax NumPy) qu'il peut ensuite interroger. Le modèle est PERSISTÉ (StoragePort) et
rechargeable. Offline (repli embeddings hash + softmax NumPy) ; scikit-learn utilisé si présent.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from ai_engine.core.registry import get_storage
from ai_engine.modules.embeddings.manager import get_embedding_manager
from ai_engine.modules.neural.classifier import SoftmaxRegression

NS = "ml_models"


def _l2(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.maximum(n, 1e-8)


class MLTrainer:
    def __init__(self) -> None:
        self._store = get_storage()
        self._emb = get_embedding_manager()
        self._cache: dict[str, SoftmaxRegression] = {}

    async def _embed(self, texts: list[str]) -> np.ndarray:
        return _l2(np.asarray((await self._emb.embed(texts)).vectors, dtype=np.float64))

    async def train(self, name: str, examples: list[dict], *, epochs: int = 300) -> dict:
        texts = [str(e["text"]) for e in examples]
        labels = [str(e["label"]) for e in examples]
        if len(set(labels)) < 2:
            raise ValueError("au moins 2 classes distinctes sont requises")
        X = await self._embed(texts)
        clf = SoftmaxRegression()
        clf.fit(X, labels, epochs=epochs)
        rec = {
            "id": name,
            "classes": clf.classes,
            "dim": X.shape[1],
            "embedder": self._emb.active_name,
            "W": clf.W.tolist(),
            "b": clf.b.tolist(),
            "examples": len(examples),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        self._store.put(NS, name, rec)
        self._cache[name] = clf
        return {"model": name, "classes": clf.classes, "examples": len(examples),
                "dim": X.shape[1], "embedder": self._emb.active_name}

    def _load(self, name: str) -> SoftmaxRegression | None:
        if name in self._cache:
            return self._cache[name]
        rec = self._store.get(NS, name)
        if not rec:
            return None
        clf = SoftmaxRegression()
        clf.classes = rec["classes"]
        clf.W = np.asarray(rec["W"], dtype=np.float64)
        clf.b = np.asarray(rec["b"], dtype=np.float64)
        self._cache[name] = clf
        return clf

    async def predict(self, name: str, text: str) -> dict:
        clf = self._load(name)
        if clf is None:
            raise KeyError(f"modèle inconnu : {name}")
        x = (await self._embed([text]))[0]
        label, scores = clf.predict(x)
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return {"model": name, "label": label, "confidence": round(top[0][1], 4),
                "scores": {k: round(v, 4) for k, v in top}}

    def list_models(self) -> list[dict]:
        out = []
        for rec in self._store.list(NS):
            out.append({"model": rec.get("id"), "classes": rec.get("classes"),
                        "examples": rec.get("examples"), "trained_at": rec.get("trained_at")})
        return out

    def delete(self, name: str) -> bool:
        self._cache.pop(name, None)
        return self._store.delete(NS, name)


def get_ml_trainer() -> MLTrainer:
    return MLTrainer()
