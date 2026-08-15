"""Validation Engine — vérifie les artefacts produits (generate → validate → ok?/repair).

Validateurs heuristiques par type (offline, sans modèle). Extensible : 1 type = 1 fonction
renvoyant une liste de checks {name, ok, detail}. `valid` = tous les checks passent.
"""

from __future__ import annotations


def _validate_text(content: str) -> list[dict]:
    return [
        {"name": "non_empty", "ok": bool(content.strip()), "detail": "le texte n'est pas vide"},
        {"name": "min_length", "ok": len(content.strip()) >= 3, "detail": "longueur suffisante"},
    ]


def _validate_code(content: str) -> list[dict]:
    balanced = all(content.count(o) == content.count(c) for o, c in [("(", ")"), ("[", "]"), ("{", "}")])
    return [
        {"name": "non_empty", "ok": bool(content.strip()), "detail": "le code n'est pas vide"},
        {"name": "balanced_brackets", "ok": balanced, "detail": "parenthèses/accolades équilibrées"},
        {"name": "has_structure", "ok": any(k in content for k in ("def ", "class ", "function", "=>", "fun ", "func ")),
         "detail": "contient une structure de code"},
    ]


def _validate_data(content) -> list[dict]:
    ok = isinstance(content, (list, dict))
    return [{"name": "structured", "ok": ok, "detail": "structure liste/objet"},
            {"name": "non_empty", "ok": bool(content), "detail": "non vide"}]


def _validate_ui(content: str) -> list[dict]:
    low = content.lower()
    return [
        {"name": "non_empty", "ok": bool(content.strip()), "detail": "non vide"},
        {"name": "uses_tokens", "ok": any(t in low for t in ("token", "var(--", "theme", "color")),
         "detail": "référence des tokens/thème (Design System)"},
    ]


_VALIDATORS = {
    "text": _validate_text,
    "code": _validate_code,
    "data": _validate_data,
    "ui": _validate_ui,
}


def validate(artifact_type: str, content) -> dict:
    validator = _VALIDATORS.get(artifact_type, _validate_text)
    checks = validator(content)
    return {"type": artifact_type, "valid": all(c["ok"] for c in checks), "checks": checks}


def supported_types() -> list[str]:
    return sorted(_VALIDATORS)
