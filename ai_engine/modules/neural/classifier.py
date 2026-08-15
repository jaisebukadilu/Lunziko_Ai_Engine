"""Classifieur neuronal léger : régression softmax NumPy native (+ option scikit-learn).

Entrée = vecteurs d'embedding (features denses) ; sortie = distribution sur des classes
d'intention. Le backend NumPy (descente de gradient) fonctionne hors-ligne et sans dépendance ;
si scikit-learn est installé, on l'utilise (LogisticRegression) — « importer les bibliothèques ».
"""

from __future__ import annotations

import numpy as np

from ai_engine.modules.neural.backends import available_backends


class SoftmaxRegression:
    """Régression logistique multinomiale (softmax) en NumPy pur, from scratch."""

    def __init__(self, l2: float = 1e-3) -> None:
        self.W: np.ndarray | None = None
        self.b: np.ndarray | None = None
        self.classes: list[str] = []
        self.l2 = l2

    def fit(self, X: np.ndarray, labels: list[str], *, epochs: int = 300, lr: float = 0.5) -> None:
        self.classes = sorted(set(labels))
        idx = {c: i for i, c in enumerate(self.classes)}
        y = np.array([idx[l] for l in labels])
        n, d = X.shape
        k = len(self.classes)
        Y = np.eye(k)[y]
        self.W = np.zeros((d, k))
        self.b = np.zeros(k)
        for _ in range(epochs):
            P = self._softmax(X @ self.W + self.b)
            gW = X.T @ (P - Y) / n + self.l2 * self.W
            gb = (P - Y).mean(axis=0)
            self.W -= lr * gW
            self.b -= lr * gb

    def predict(self, x: np.ndarray) -> tuple[str, dict[str, float]]:
        p = self._softmax(x @ self.W + self.b)
        scores = {c: float(p[i]) for i, c in enumerate(self.classes)}
        best = max(scores, key=scores.get)
        return best, scores

    @staticmethod
    def _softmax(z: np.ndarray) -> np.ndarray:
        z = z - z.max(axis=-1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=-1, keepdims=True)


class SklearnClassifier:
    """Adaptateur scikit-learn (LogisticRegression) — utilisé si la lib est installée."""

    def __init__(self) -> None:
        from sklearn.linear_model import LogisticRegression  # import paresseux

        self._clf = LogisticRegression(max_iter=1000, C=10.0)
        self.classes: list[str] = []

    def fit(self, X: np.ndarray, labels: list[str], **_: object) -> None:
        self._clf.fit(X, labels)
        self.classes = list(self._clf.classes_)

    def predict(self, x: np.ndarray) -> tuple[str, dict[str, float]]:
        probs = self._clf.predict_proba(x[None, :])[0]
        scores = {c: float(p) for c, p in zip(self._clf.classes_, probs)}
        best = max(scores, key=scores.get)
        return best, scores


def make_classifier(prefer: str = "auto") -> tuple[object, str]:
    """Retourne (classifieur, backend_utilisé). `auto` : sklearn si dispo, sinon NumPy natif."""
    if prefer in ("auto", "sklearn") and "sklearn" in available_backends():
        try:
            return SklearnClassifier(), "sklearn"
        except Exception:
            pass
    return SoftmaxRegression(), "numpy"
