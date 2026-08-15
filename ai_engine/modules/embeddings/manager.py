"""EmbeddingManager — résout UN embedder actif selon la config, repli hors-ligne garanti.

Un seul embedder actif => dimension cohérente pour tout un namespace du VectorPort.
"""

from __future__ import annotations

from functools import lru_cache

from ai_engine.config import get_settings
from ai_engine.modules.embeddings.base import EmbedResult
from ai_engine.modules.embeddings.providers.gemini_embed import GeminiEmbedder
from ai_engine.modules.embeddings.providers.local_hash import HashEmbedder
from ai_engine.modules.embeddings.providers.openai_compat_embed import OpenAICompatEmbedder

# Ordre de préférence en mode "auto".
_AUTO_ORDER = ["openai", "mistral", "gemini", "local", "hash"]


class EmbeddingManager:
    def __init__(self) -> None:
        s = get_settings()
        self._model_override = s.ae_embed_model
        self._embedders: dict[str, object] = {
            "openai": OpenAICompatEmbedder("openai", "https://api.openai.com/v1", s.openai_api_key, s.ae_embed_model or "text-embedding-3-small"),
            "mistral": OpenAICompatEmbedder("mistral", "https://api.mistral.ai/v1", s.mistral_api_key, s.ae_embed_model or "mistral-embed"),
            "gemini": GeminiEmbedder(s.gemini_api_key, s.ae_embed_model or "text-embedding-004"),
            "hash": HashEmbedder(s.ae_embed_dim),
        }
        if s.ae_local_base_url:
            self._embedders["local"] = OpenAICompatEmbedder("local", s.ae_local_base_url, "", s.ae_embed_model or "nomic-embed-text")

        self._active_name = self._resolve(s.ae_embed_provider)

    def _resolve(self, choice: str) -> str:
        if choice and choice != "auto":
            e = self._embedders.get(choice)
            if e is not None and e.available():  # type: ignore[attr-defined]
                return choice
            # choix indisponible -> repli hash (jamais d'échec hors-ligne)
            return "hash"
        for name in _AUTO_ORDER:
            e = self._embedders.get(name)
            if e is not None and e.available():  # type: ignore[attr-defined]
                return name
        return "hash"

    @property
    def active_name(self) -> str:
        return self._active_name

    async def embed(self, texts: list[str]) -> EmbedResult:
        emb = self._embedders[self._active_name]
        vectors = await emb.embed(texts)  # type: ignore[attr-defined]
        dim = len(vectors[0]) if vectors else 0
        model = getattr(emb, "_model", self._active_name)
        return EmbedResult(vectors=vectors, provider=self._active_name, model=model, dim=dim)


@lru_cache
def get_embedding_manager() -> EmbeddingManager:
    return EmbeddingManager()
