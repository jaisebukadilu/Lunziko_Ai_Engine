"""Nettoyage et profilage de données (pur Python, from scratch, clean-room).

Opérations façon data-wrangling : profilage de colonnes (type, nuls, distincts), nettoyage
tabulaire (trim, normalisation d'espaces, coercition de types, valeurs manquantes, doublons,
lignes vides) et nettoyage de corpus texte (normalisation, dédup, filtre de longueur).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

_WS = re.compile(r"\s+")
_INT = re.compile(r"^[+-]?\d+$")
_FLOAT = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
_TRUE = {"true", "vrai", "oui", "yes", "1"}
_FALSE = {"false", "faux", "non", "no", "0"}


def _guess_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    s = str(value).strip()
    if s == "":
        return "null"
    if _INT.match(s):
        return "int"
    if _FLOAT.match(s):
        return "float"
    if s.lower() in _TRUE or s.lower() in _FALSE:
        return "bool"
    return "str"


def _coerce(value):
    """Convertit une chaîne vers int/float/bool si possible, sinon la trim."""
    if not isinstance(value, str):
        return value
    s = value.strip()
    if s == "":
        return None
    if _INT.match(s):
        return int(s)
    if _FLOAT.match(s):
        return float(s)
    low = s.lower()
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    return s


def profile_records(records: list[dict]) -> dict:
    """Profil par colonne : types observés, nuls, distincts, exemples."""
    columns: dict[str, dict] = {}
    keys: list[str] = []
    for r in records:
        for k in r:
            if k not in columns:
                columns[k] = {"types": Counter(), "nulls": 0, "values": []}
                keys.append(k)
    for r in records:
        for k in keys:
            v = r.get(k, None)
            t = _guess_type(v)
            columns[k]["types"][t] += 1
            if t == "null":
                columns[k]["nulls"] += 1
            elif len(columns[k]["values"]) < 1000:
                columns[k]["values"].append(v)
    report = {}
    for k in keys:
        c = columns[k]
        report[k] = {
            "dominant_type": (c["types"].most_common(1)[0][0] if c["types"] else "null"),
            "types": dict(c["types"]),
            "nulls": c["nulls"],
            "distinct": len(set(map(str, c["values"]))),
            "examples": c["values"][:3],
        }
    return {"rows": len(records), "columns": keys, "profile": report}


def clean_records(
    records: list[dict],
    *,
    trim: bool = True,
    collapse_ws: bool = True,
    coerce_types: bool = True,
    drop_empty_rows: bool = True,
    drop_duplicates: bool = True,
) -> dict:
    """Nettoie des enregistrements tabulaires et renvoie {rows, report}."""
    cleaned: list[dict] = []
    seen: set[tuple] = set()
    stats = {"rows_in": len(records), "cells_trimmed": 0, "empty_rows_removed": 0,
             "duplicates_removed": 0, "values_coerced": 0}
    for r in records:
        row: dict = {}
        for k, v in r.items():
            if isinstance(v, str):
                nv = v.strip() if trim else v
                if collapse_ws:
                    nv = _WS.sub(" ", nv)
                if nv != v:
                    stats["cells_trimmed"] += 1
                v = nv
            if coerce_types:
                cv = _coerce(v)
                if cv != v and not (cv is None and v == ""):
                    stats["values_coerced"] += 1
                v = cv
            row[k] = v
        non_empty = any(v not in (None, "") for v in row.values())
        if drop_empty_rows and not non_empty:
            stats["empty_rows_removed"] += 1
            continue
        if drop_duplicates:
            sig = tuple(sorted((k, str(v)) for k, v in row.items()))
            if sig in seen:
                stats["duplicates_removed"] += 1
                continue
            seen.add(sig)
        cleaned.append(row)
    stats["rows_out"] = len(cleaned)
    return {"records": cleaned, "report": stats}


def _norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return _WS.sub(" ", s).strip()


def clean_texts(
    texts: list[str],
    *,
    min_len: int = 1,
    dedup: bool = True,
    normalize: bool = True,
) -> dict:
    """Nettoie un corpus texte : normalisation, filtre de longueur, déduplication."""
    out: list[str] = []
    seen: set[str] = set()
    stats = {"texts_in": len(texts), "empty_removed": 0, "too_short_removed": 0,
             "duplicates_removed": 0}
    for t in texts:
        s = _norm_text(t) if normalize else t
        if not s:
            stats["empty_removed"] += 1
            continue
        if len(s) < min_len:
            stats["too_short_removed"] += 1
            continue
        if dedup:
            key = s.lower()
            if key in seen:
                stats["duplicates_removed"] += 1
                continue
            seen.add(key)
        out.append(s)
    stats["texts_out"] = len(out)
    return {"texts": out, "report": stats}
