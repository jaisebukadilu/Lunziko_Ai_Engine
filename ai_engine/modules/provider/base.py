"""Types communs et protocole d'un provider LLM."""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

Role = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatResult(BaseModel):
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


# --- Tool-calling (A-4b) : types neutres, convertis par chaque adaptateur ---
class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict = Field(default_factory=lambda: {"type": "object", "properties": {}})


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict = Field(default_factory=dict)


class ToolChatResult(BaseModel):
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    provider: str
    model: str
    stop_reason: str = "end"  # "tool_use" quand le modèle demande un outil


@runtime_checkable
class Provider(Protocol):
    name: str

    def available(self) -> bool:
        """True si le provider a de quoi fonctionner (clé ou base URL locale)."""
        ...

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> ChatResult: ...


# Mots-clés d'erreur déclenchant le fallback vers le provider suivant.
FALLBACK_ERROR_KEYWORDS = (
    "quota", "rate_limit", "rate limit", "billing", "insufficient_quota",
    "credit", "overloaded", "429", "402", "503",
)


class ProviderError(RuntimeError):
    """Erreur d'un provider ; `retryable` déclenche le fallback."""

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


def is_retryable(message: str) -> bool:
    low = message.lower()
    return any(k in low for k in FALLBACK_ERROR_KEYWORDS)
