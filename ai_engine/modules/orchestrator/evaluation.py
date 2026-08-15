"""Evaluation Engine — note la qualité d'une sortie (heuristiques offline + LLM-as-judge option).

Complète la Validation (checks binaires) par un **score** [0,1] et des métriques. Offline :
pertinence (recouvrement lexical avec la tâche), longueur adéquate, structure. Un juge LLM
(provider) peut raffiner ultérieurement — non requis.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[a-zà-ÿ0-9]{3,}")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def evaluate(task: str, output: str, *, min_len: int = 20) -> dict:
    out = (output or "").strip()
    task_tokens = _tokens(task)
    out_tokens = _tokens(out)

    relevance = (len(task_tokens & out_tokens) / len(task_tokens)) if task_tokens else 0.0
    length_ok = 1.0 if len(out) >= min_len else (len(out) / min_len if min_len else 0.0)
    has_structure = 1.0 if any(c in out for c in ("\n", ".", ":", "-")) else 0.5
    non_empty = 1.0 if out else 0.0

    metrics = {
        "relevance": round(relevance, 3),
        "length_adequacy": round(length_ok, 3),
        "structure": has_structure,
        "non_empty": non_empty,
    }
    # score pondéré
    score = 0.45 * relevance + 0.25 * length_ok + 0.15 * has_structure + 0.15 * non_empty
    grade = "A" if score >= 0.8 else "B" if score >= 0.6 else "C" if score >= 0.4 else "D"
    return {"score": round(score, 3), "grade": grade, "metrics": metrics}


def get_evaluation_engine():
    return None  # API fonctionnelle (evaluate) ; placeholder pour homogénéité
