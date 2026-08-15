"""Provider `lunziko` — modèle LLM natif Lunziko (paquet lunziko-llm), 100% local.

Charge un checkpoint entraîné avec `lunziko-llm` (architecture NumPy from scratch : GQA/RoPE/
SwiGLU) et génère localement, sans réseau. Import PARESSEUX : si le paquet n'est pas installé
ou le checkpoint absent, le provider est simplement `available() == False` (aucun impact).
"""

from __future__ import annotations

from pathlib import Path

from ai_engine.modules.provider.base import ChatMessage, ChatResult, ProviderError


class LunzikoNativeProvider:
    name = "lunziko"

    def __init__(self, ckpt_path: str, tokenizer_path: str) -> None:
        self._ckpt = ckpt_path
        self._tok = tokenizer_path
        self._model = None
        self._tokenizer = None

    def available(self) -> bool:
        if not (self._ckpt and self._tok):
            return False
        if not (Path(self._ckpt).is_file() and Path(self._tok).is_file()):
            return False
        try:
            import lunziko_llm  # noqa: F401
        except Exception:
            return False
        return True

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from lunziko_llm.tokenizer import BPETokenizer
            from lunziko_llm.train import load_checkpoint

            self._model = load_checkpoint(self._ckpt)
            self._tokenizer = BPETokenizer.load(self._tok)

    @staticmethod
    def _build_prompt(messages: list[ChatMessage], system: str | None) -> str:
        parts = []
        if system:
            parts.append(system.strip())
        for m in messages:
            parts.append(m.content.strip())
        parts.append("")  # amorce la suite
        return "\n".join(parts)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 256,
    ) -> ChatResult:
        try:
            self._ensure_loaded()
            from lunziko_llm.generate import generate

            prompt = self._build_prompt(messages, system)
            full = generate(
                self._model, self._tokenizer, prompt,
                max_new_tokens=min(max_tokens, 512), temperature=0.7, top_k=40,
            )
            completion = full[len(prompt):] if full.startswith(prompt) else full
            in_toks = len(self._tokenizer.encode(prompt))
            out_toks = len(self._tokenizer.encode(completion))
            return ChatResult(
                content=completion.strip(),
                provider=self.name,
                model=model or "lunziko-llm",
                input_tokens=in_toks,
                output_tokens=out_toks,
            )
        except Exception as e:  # erreur locale => non-retryable (pas de fallback réseau utile)
            raise ProviderError(f"lunziko: {e}", retryable=False)
