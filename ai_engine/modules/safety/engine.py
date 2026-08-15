"""SafetyEngine — redaction PII, détection d'injection de prompt, modération (heuristique).

Offline, sans modèle. `check(text, direction)` agrège les garde-fous ; `redact(text)` masque
les données personnelles. Conçu comme filtre avant/après l'exécution d'un Brain.
"""

from __future__ import annotations

import re

# --- PII ---
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s.\-]?){9,14}\d(?!\d)")
_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")

# --- Injection de prompt ---
_INJECTION = [
    r"ignore (?:all |the )?(?:previous|above|prior) (?:instructions|prompts?)",
    r"disregard (?:the |your )?(?:above|previous|instructions|rules)",
    r"forget (?:your|the|all) (?:instructions|rules|prompt)",
    r"(?:reveal|show|print|repeat) (?:your |the )?(?:system )?(?:prompt|instructions)",
    r"you are now (?:a|an|in)",
    r"(?:developer|god|dan) mode",
    r"do anything now",
    r"jailbreak",
    r"oublie (?:tes|les) (?:instructions|règles|consignes)",
    r"ignore (?:les |tes )?(?:instructions|consignes) (?:précédentes|ci-dessus)",
]
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in _INJECTION]

# --- Modération (heuristique minimale, à raffiner par modèle) ---
_MODERATION = {
    "violence": ["tuer", "massacre", "attentat", "bombe artisanale", "kill someone"],
    "self_harm": ["suicide", "me suicider", "self-harm", "automutilation"],
    "hate": [],  # volontairement vide (les listes de mots sont trop imprécises)
}


def _luhn(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    if not (13 <= len(digits) <= 19):
        return False
    checksum, parity = 0, len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def redact(text: str) -> dict:
    findings: dict[str, int] = {}
    out = text

    def _sub(pattern, label, s, *, validator=None):
        count = 0

        def repl(m):
            nonlocal count
            if validator and not validator(m.group(0)):
                return m.group(0)
            count += 1
            return f"[{label}]"

        s2 = pattern.sub(repl, s)
        if count:
            findings[label] = findings.get(label, 0) + count
        return s2

    out = _sub(_EMAIL, "EMAIL", out)
    out = _sub(_IBAN, "IBAN", out)
    out = _sub(_CARD, "CARD", out, validator=_luhn)
    out = _sub(_PHONE, "PHONE", out)
    return {"redacted": out, "findings": findings, "pii_found": bool(findings)}


def detect_injection(text: str) -> list[str]:
    return [rx.pattern for rx in _INJECTION_RE if rx.search(text)]


def moderate(text: str) -> list[str]:
    low = text.lower()
    return [cat for cat, kws in _MODERATION.items() if any(k in low for k in kws)]


def check(text: str, *, direction: str = "input") -> dict:
    pii = redact(text)
    injection = detect_injection(text) if direction == "input" else []
    moderation = moderate(text)
    safe = not injection and not moderation
    return {
        "direction": direction,
        "safe": safe,
        "pii": {"found": pii["pii_found"], "findings": pii["findings"]},
        "injection": {"detected": bool(injection), "flags": injection},
        "moderation": {"flagged": bool(moderation), "categories": moderation},
        "redacted": pii["redacted"],
    }


def get_safety_engine():
    return None  # API fonctionnelle (check/redact) ; placeholder d'homogénéité
