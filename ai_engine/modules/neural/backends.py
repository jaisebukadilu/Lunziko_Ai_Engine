"""Registre des backends neuronaux disponibles (détection par import paresseux).

« Importer les bibliothèques neuronales » = les détecter et les exposer quand elles sont
installées, sans jamais les imposer. NumPy est toujours présent (backend natif). Les autres
frameworks sont optionnels et n'affectent pas le démarrage s'ils sont absents.
"""

from __future__ import annotations

import importlib
import importlib.util

# module d'import -> (nom lisible, ce que le backend débloque)
_FRAMEWORKS: dict[str, tuple[str, str]] = {
    "numpy": ("NumPy", "backend natif (autograd from scratch, offline)"),
    "torch": ("PyTorch", "réseaux profonds + GPU/autograd à l'échelle"),
    "tensorflow": ("TensorFlow", "graphes + déploiement production"),
    "keras": ("Keras", "API haut niveau de modèles"),
    "jax": ("JAX", "autodiff + XLA/JIT + accélérateurs"),
    "sklearn": ("scikit-learn", "ML classique (classifieurs, clustering, reranking)"),
    "transformers": ("Transformers", "modèles pré-entraînés (embeddings, cross-encoders, LLM locaux)"),
}


def _version(mod_name: str) -> str | None:
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    return getattr(mod, "__version__", "?")


def _is_installed(mod_name: str) -> bool:
    try:
        return importlib.util.find_spec(mod_name) is not None
    except Exception:
        return False


def detect_backends() -> dict:
    """État de chaque backend : présence, version (si chargeable), capacité débloquée."""
    out: dict[str, dict] = {}
    for mod_name, (label, enables) in _FRAMEWORKS.items():
        installed = mod_name == "numpy" or _is_installed(mod_name)
        out[mod_name] = {
            "label": label,
            "available": installed,
            "version": _version(mod_name) if installed else None,
            "enables": enables,
        }
    return out


def available_backends() -> list[str]:
    return [name for name, info in detect_backends().items() if info["available"]]


def preferred_ml_backend() -> str:
    """Backend préféré pour le ML classique (classifieur d'intention) : sklearn sinon numpy."""
    return "sklearn" if "sklearn" in available_backends() else "numpy"
