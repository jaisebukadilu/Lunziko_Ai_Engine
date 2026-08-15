"""Tests du module data (pilier données) — fonctions pures, offline."""

from ai_engine.modules.data.cleaner import clean_records, clean_texts, profile_records


def test_profile_infers_types():
    rep = profile_records([{"age": "30", "nom": "Alice"}, {"age": "25", "nom": "Bob"}])
    assert rep["rows"] == 2
    assert rep["profile"]["age"]["dominant_type"] == "int"
    assert rep["profile"]["nom"]["dominant_type"] == "str"


def test_clean_records_dedup_and_empty():
    recs = [
        {"a": " 1 ", "b": "x"},
        {"a": "1", "b": "x"},      # doublon après trim + coercition
        {"a": "", "b": ""},        # ligne vide
    ]
    out = clean_records(recs)
    assert out["report"]["rows_out"] == 1
    assert out["report"]["empty_rows_removed"] == 1
    assert out["report"]["duplicates_removed"] == 1
    assert out["records"][0]["a"] == 1  # coercition en int


def test_clean_texts_dedup_and_minlen():
    out = clean_texts(["  Bonjour  ", "bonjour", "", "x", "Lunziko"], min_len=3)
    assert out["report"]["texts_out"] == 2
    assert "Bonjour" in out["texts"]
    assert out["report"]["duplicates_removed"] == 1
