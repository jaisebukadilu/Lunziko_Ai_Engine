"""NeuralRouter — routage d'intention par réseau neuronal (embeddings → classifieur).

Améliore la « réflexion » de l'AgentEngine : au lieu d'un simple comptage de mots-clés, on
projette la requête dans l'espace d'embeddings et un classifieur entraîné choisit la capacité.
Entraînement paresseux et hors-ligne (repli embeddings hash + softmax NumPy) ; utilise
scikit-learn si présent. Repli déterministe si l'entraînement échoue.
"""

from __future__ import annotations

import numpy as np

from ai_engine.modules.embeddings.manager import get_embedding_manager
from ai_engine.modules.neural.classifier import make_classifier
from ai_engine.modules.neural.intent_taxonomy import INTENT_EXAMPLES, keyword_scores

# Poids de fusion : part du signal neuronal dans la décision hybride (le reste = lexical).
NEURAL_WEIGHT = 0.65


def _l2norm(m: np.ndarray) -> np.ndarray:
    """Normalise chaque ligne (features unitaires → meilleure séparabilité du classifieur)."""
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.maximum(n, 1e-8)


def _to_distribution(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in scores.items()}


class NeuralRouter:
    def __init__(self) -> None:
        self._clf = None
        self._backend = "untrained"
        self._emb = get_embedding_manager()

    @property
    def trained(self) -> bool:
        return self._clf is not None

    @property
    def backend(self) -> str:
        return self._backend

    async def _embed(self, texts: list[str]) -> np.ndarray:
        vecs = (await self._emb.embed(texts)).vectors
        return _l2norm(np.asarray(vecs, dtype=np.float64))

    async def train(self) -> dict:
        texts: list[str] = []
        labels: list[str] = []
        for intent, examples in INTENT_EXAMPLES.items():
            texts += examples
            labels += [intent] * len(examples)
        X = await self._embed(texts)
        clf, backend = make_classifier("auto")
        clf.fit(X, labels)
        self._clf, self._backend = clf, backend
        return {"trained": True, "backend": backend, "classes": clf.classes,
                "examples": len(texts), "embedder": self._emb.active_name, "dim": X.shape[1]}

    async def route(self, query: str) -> dict:
        """Routage HYBRIDE : classifieur neuronal (embeddings L2) fusionné au signal lexical."""
        if self._clf is None:
            await self.train()
        x = (await self._embed([query]))[0]
        _, neural = self._clf.predict(x)                      # distribution neuronale
        kw_dist = _to_distribution(keyword_scores(query))     # distribution lexicale (ou {})

        fused = "neural"
        if kw_dist:
            final = {
                c: NEURAL_WEIGHT * neural.get(c, 0.0) + (1 - NEURAL_WEIGHT) * kw_dist.get(c, 0.0)
                for c in neural
            }
            fused = "hybrid"
        else:
            final = dict(neural)
        top = sorted(final.items(), key=lambda kv: kv[1], reverse=True)
        return {
            "capability": top[0][0],
            "confidence": round(top[0][1], 4),
            "scores": {k: round(v, 4) for k, v in top},
            "neural_scores": {k: round(v, 4) for k, v in sorted(neural.items(), key=lambda kv: kv[1], reverse=True)},
            "keyword_scores": {k: round(v, 4) for k, v in kw_dist.items()},
            "backend": self._backend,
            "fusion": fused,
        }


_ROUTER: NeuralRouter | None = None


def get_neural_router() -> NeuralRouter:
    global _ROUTER
    if _ROUTER is None:
        _ROUTER = NeuralRouter()
    return _ROUTER
