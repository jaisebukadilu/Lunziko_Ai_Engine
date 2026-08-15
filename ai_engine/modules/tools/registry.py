"""ToolRegistry — enregistrement et exécution des outils appelables par le modèle."""

from __future__ import annotations

import json
from typing import Awaitable, Callable

from ai_engine.modules.provider.base import ToolSpec

Handler = Callable[[dict], Awaitable[object]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolSpec, Handler]] = {}

    def register(self, spec: ToolSpec, handler: Handler) -> None:
        self._tools[spec.name] = (spec, handler)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self, names: list[str] | None = None) -> list[ToolSpec]:
        if names is None:
            return [s for s, _ in self._tools.values()]
        return [self._tools[n][0] for n in names if n in self._tools]

    async def execute(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"outil inconnu: {name}"})
        try:
            result = await self._tools[name][1](arguments or {})
        except Exception as e:  # l'erreur est renvoyée au modèle, pas propagée
            return json.dumps({"error": str(e)})
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)


_REGISTRY: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ToolRegistry()
        from ai_engine.modules.tools.builtins import register_builtins

        register_builtins(_REGISTRY)
    return _REGISTRY
