"""ProviderManager — sélection + fallback en cascade, propre à l'AI Engine.

Aucune dépendance à Platform : clés lues dans la config de l'AI Engine.
"""

from __future__ import annotations

from functools import lru_cache

from ai_engine.config import get_settings
from ai_engine.modules.provider.base import ChatMessage, ChatResult, ProviderError, is_retryable
from ai_engine.modules.provider.providers.claude import ClaudeProvider
from ai_engine.modules.provider.providers.gemini import GeminiProvider
from ai_engine.modules.provider.providers.lunziko_native import LunzikoNativeProvider
from ai_engine.modules.provider.providers.openai_compat import OpenAICompatProvider


class ProviderManager:
    def __init__(self) -> None:
        s = get_settings()
        self._providers: dict[str, object] = {
            "claude": ClaudeProvider(s.anthropic_api_key),
            "chatgpt": OpenAICompatProvider("chatgpt", "https://api.openai.com/v1", s.openai_api_key, "gpt-4o-mini"),
            "gemini": GeminiProvider(s.gemini_api_key),
            "mistral": OpenAICompatProvider("mistral", "https://api.mistral.ai/v1", s.mistral_api_key, "mistral-small-latest"),
            "deepseek": OpenAICompatProvider("deepseek", "https://api.deepseek.com", s.deepseek_api_key, "deepseek-chat"),
        }
        if s.ae_local_base_url:
            self._providers["local"] = OpenAICompatProvider("local", s.ae_local_base_url, "", "local-model")
        if s.ae_lunziko_llm_ckpt:
            # LLM natif Lunziko (paquet lunziko-llm), 100% local, from scratch.
            self._providers["lunziko"] = LunzikoNativeProvider(s.ae_lunziko_llm_ckpt, s.ae_lunziko_llm_tokenizer)
        self._default = s.ae_default_provider
        self._fallback = s.fallback_order

    def list_available(self) -> list[str]:
        return [n for n, p in self._providers.items() if p.available()]  # type: ignore[attr-defined]

    def _order(self, preferred: str | None) -> list[str]:
        order: list[str] = []
        for name in [preferred or self._default, *self._fallback]:
            if name and name not in order:
                order.append(name)
        return order

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        provider: str | None = None,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> ChatResult:
        errors: list[str] = []
        for name in self._order(provider):
            p = self._providers.get(name)
            if p is None or not p.available():  # type: ignore[attr-defined]
                continue
            try:
                return await p.chat(messages, system=system, model=model, max_tokens=max_tokens)  # type: ignore[attr-defined]
            except ProviderError as e:
                errors.append(str(e))
                if e.retryable and is_retryable(str(e)):
                    continue  # provider suivant
                raise
            except Exception as e:  # réseau, etc. → fallback
                errors.append(f"{name}: {e}")
                continue
        raise ProviderError(
            "Aucun provider disponible n'a pu répondre. "
            + (" | ".join(errors) if errors else "Configurez au moins une clé d'API."),
            retryable=False,
        )


@lru_cache
def get_provider_manager() -> ProviderManager:
    return ProviderManager()
