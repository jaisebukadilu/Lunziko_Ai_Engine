"""CodeEngine — raisonnement sur le code, priorité aux modèles LOCAUX (privé, hors-ligne).

Route en priorité vers le provider `local` (Ollama : Qwen-Coder / DeepSeek-Coder / CodeLlama,
API OpenAI-compatible) via `AE_LOCAL_BASE_URL` + `AE_CODE_MODEL`. Repli vers le provider
cloud le plus adapté au code (DeepSeek) puis la cascade générale. Cf. `CODE_LOGIC_MODELS.md`.
"""

from __future__ import annotations

from ai_engine.config import get_settings
from ai_engine.modules.provider.base import ChatMessage
from ai_engine.modules.provider.manager import get_provider_manager

_SYS = {
    "analyze": "Tu es un expert en architecture logicielle. Analyse la logique et la structure du code : "
               "rôle, flux d'exécution, dépendances, points de complexité. Sois précis et structuré.",
    "debug": "Tu es un expert en débogage. Diagnostique la cause de l'erreur puis propose un correctif "
             "minimal et sûr, avec le code corrigé et une brève justification.",
    "explain": "Tu es un pédagogue du code. Explique pas-à-pas l'algorithme et la logique, simplement, "
               "sans survoler les points délicats.",
}


class CodeEngine:
    def __init__(self) -> None:
        s = get_settings()
        self._has_local = bool(s.ae_local_base_url)
        self._code_model = s.ae_code_model or None

    def _order(self) -> tuple[str, str | None]:
        """(provider préféré, modèle). Local si dispo, sinon DeepSeek (bon en code)."""
        if self._has_local:
            return "local", self._code_model
        return "deepseek", None

    async def _run(self, task: str, prompt: str, provider: str | None, model: str | None, max_tokens: int) -> dict:
        pref, code_model = self._order()
        res = await get_provider_manager().chat(
            [ChatMessage(role="user", content=prompt)],
            provider=provider or pref,
            system=_SYS[task],
            model=model or code_model,
            max_tokens=max_tokens,
        )
        return {"task": task, "answer": res, "routed_to": provider or pref}

    async def analyze(self, code: str, question: str | None = None, **kw) -> dict:
        prompt = (f"{question}\n\n" if question else "") + f"```\n{code}\n```"
        return await self._run("analyze", prompt, kw.get("provider"), kw.get("model"), kw.get("max_tokens", 1500))

    async def debug(self, code: str, error: str, **kw) -> dict:
        prompt = f"ERREUR:\n{error}\n\nCODE:\n```\n{code}\n```"
        return await self._run("debug", prompt, kw.get("provider"), kw.get("model"), kw.get("max_tokens", 1500))

    async def explain(self, code: str, **kw) -> dict:
        return await self._run("explain", f"```\n{code}\n```", kw.get("provider"), kw.get("model"), kw.get("max_tokens", 1500))


def get_code_engine() -> CodeEngine:
    return CodeEngine()
