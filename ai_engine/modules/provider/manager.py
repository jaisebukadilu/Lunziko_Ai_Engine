"""ProviderManager — sélection + fallback en cascade, propre à l'AI Engine.

Aucune dépendance à Platform : clés lues dans la config de l'AI Engine.
"""

from __future__ import annotations

from functools import lru_cache

from ai_engine.config import get_settings
from ai_engine.modules.provider.base import (
    ChatMessage, ChatResult, ProviderError, ToolChatResult, ToolSpec, is_retryable,
)
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
            self._providers["local"] = OpenAICompatProvider(
                "local", s.ae_local_base_url, "", s.ae_local_model or "local-model")
            # Modèles Ollama additionnels comme providers `ollama-<nom>` (ex second modèle Mistral).
            for m in s.ollama_models_list:
                pname = "ollama-" + m.split(":")[0]
                self._providers[pname] = OpenAICompatProvider(pname, s.ae_local_base_url, "", m)
        if s.ae_lmstudio_base_url:
            # LM Studio — serveur local OpenAI-compatible (distinct d'Ollama).
            self._providers["lmstudio"] = OpenAICompatProvider(
                "lmstudio", s.ae_lmstudio_base_url, "", s.ae_lmstudio_model or "local-model")
        if s.qwen_api_key:
            # Qwen 3.8-Max (Alibaba) — endpoint compatible OpenAI.
            self._providers["qwen"] = OpenAICompatProvider(
                "qwen", s.ae_qwen_base_url, s.qwen_api_key, s.ae_qwen_model)
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

    def tool_capable(self) -> list[str]:
        out = []
        for name in self._order(None):
            p = self._providers.get(name)
            if p is None or not p.available():  # type: ignore[attr-defined]
                continue
            if getattr(p, "supports_tools", lambda: False)():
                out.append(name)
        return out

    async def chat_with_tools(
        self, messages: list[dict], tools: list[ToolSpec], *,
        provider: str | None = None, system: str | None = None,
        model: str | None = None, max_tokens: int = 4096,
    ) -> ToolChatResult:
        errors: list[str] = []
        for name in self._order(provider):
            p = self._providers.get(name)
            if p is None or not p.available():  # type: ignore[attr-defined]
                continue
            if not getattr(p, "supports_tools", lambda: False)():
                continue
            try:
                return await p.chat_with_tools(messages, tools, system=system, model=model, max_tokens=max_tokens)  # type: ignore[attr-defined]
            except ProviderError as e:
                errors.append(str(e))
                if e.retryable and is_retryable(str(e)):
                    continue
                raise
            except Exception as e:
                errors.append(f"{name}: {e}")
                continue
        raise ProviderError(
            "Aucun provider compatible tool-calling disponible. " + " | ".join(errors), retryable=False)


@lru_cache
def get_provider_manager() -> ProviderManager:
    return ProviderManager()
