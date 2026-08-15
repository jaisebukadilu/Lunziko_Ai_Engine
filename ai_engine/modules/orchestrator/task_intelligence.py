"""Task Intelligence — décompose un objectif en sous-tâches et assigne un Brain à chacune.

Décomposition heuristique offline (séparateurs « et / puis / , / then ») + résolution du Brain
via le Brain Registry. Un raffinement par LLM (provider) est possible ultérieurement.
"""

from __future__ import annotations

import re

from ai_engine.modules.orchestrator.brains import get_brain_registry

_SPLIT = re.compile(r"\s*(?:,|;| puis | et ensuite | et | then | and )\s*", re.IGNORECASE)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" .")


def decompose(goal: str) -> list[dict]:
    parts = [p for p in (_clean(x) for x in _SPLIT.split(goal)) if len(p) >= 3]
    if not parts:
        parts = [_clean(goal)]
    reg = get_brain_registry()
    subtasks = []
    for i, desc in enumerate(parts):
        brains = reg.resolve(desc, k=1)
        brain = brains[0] if brains else reg.get("text")
        subtasks.append({
            "id": f"st{i + 1}",
            "description": desc,
            "brain": brain["id"] if brain else "text",
            "brain_status": brain["status"] if brain else "active",
            "engines": brain.get("engines", []) if brain else [],
        })
    return subtasks
