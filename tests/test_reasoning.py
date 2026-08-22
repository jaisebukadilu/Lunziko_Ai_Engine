"""Test raisonnement avancé — stratégies OSS clean-room, orchestration (chat injecté offline)."""

import asyncio

from ai_engine.modules.provider.base import ChatResult
from ai_engine.modules.reasoning.engine import ReasoningEngine


def _chat_returning(seq):
    """chat_fn qui renvoie successivement les éléments de `seq` (puis le dernier en boucle)."""
    calls = {"i": 0, "prompts": []}

    async def chat(messages, *, system=None, model=None, max_tokens=4096):
        calls["prompts"].append(messages[0].content)
        i = min(calls["i"], len(seq) - 1)
        calls["i"] += 1
        return ChatResult(content=seq[i], provider="fake", model="fake")

    return chat, calls


def test_catalog_lists_oss_strategies():
    from ai_engine.modules.reasoning.strategies import all_strategies
    ids = {s["id"] for s in all_strategies()}
    for expected in ("chain_of_thought", "self_consistency", "tree_of_thoughts",
                     "reflexion", "plan_and_solve", "step_back", "react", "debate"):
        assert expected in ids


def test_cot_extracts_final_answer():
    chat, _ = _chat_returning(["Étape 1...\nÉtape 2...\nRéponse: 42"])
    eng = ReasoningEngine(chat_fn=chat)
    out = asyncio.run(eng.cot("Quelle est la réponse ?"))
    assert out["answer"] == "42"


def test_self_consistency_majority_vote():
    # 3 réponses "paris", 2 "lyon" -> gagnant paris
    chat, calls = _chat_returning([
        "...\nRéponse: Paris", "...\nRéponse: Lyon", "...\nRéponse: Paris",
        "...\nRéponse: Paris", "...\nRéponse: Lyon"])
    eng = ReasoningEngine(chat_fn=chat)
    out = asyncio.run(eng.self_consistency("Capitale ?", n=5))
    assert out["answer"] == "paris" and out["votes"] == 3
    assert calls["i"] == 5  # N appels


def test_reflexion_three_calls_pipeline():
    chat, calls = _chat_returning(["brouillon", "critique: trop vague", "réponse révisée"])
    eng = ReasoningEngine(chat_fn=chat)
    out = asyncio.run(eng.reflexion("Rédige un résumé"))
    assert out["draft"] == "brouillon" and out["critique"].startswith("critique")
    assert out["answer"] == "réponse révisée"
    assert calls["i"] == 3


def test_plan_and_solve_two_calls():
    chat, calls = _chat_returning(["1. faire X\n2. faire Y", "résultat final"])
    eng = ReasoningEngine(chat_fn=chat)
    out = asyncio.run(eng.plan_and_solve("Construis un truc"))
    assert "faire X" in out["plan"] and out["answer"] == "résultat final"
    assert calls["i"] == 2


def test_auto_strategy_selection():
    chat, _ = _chat_returning(["Réponse: ok"])
    eng = ReasoningEngine(chat_fn=chat)
    assert eng._auto_strategy("Combien font 2+2 ?") == "self_consistency"
    assert eng._auto_strategy("Conçois un plan de migration") == "plan_and_solve"
    assert eng._auto_strategy("Améliore ce texte") == "reflexion"
    assert eng._auto_strategy("Pourquoi le ciel est bleu ?") == "step_back"
    assert eng._auto_strategy("Liste les fruits") == "chain_of_thought"


def test_reason_dispatch_and_unknown():
    chat, _ = _chat_returning(["Réponse: ok"])
    eng = ReasoningEngine(chat_fn=chat)
    out = asyncio.run(eng.reason("Liste des couleurs", strategy="chain_of_thought"))
    assert out["selected_strategy"] == "chain_of_thought"
    try:
        asyncio.run(eng.reason("x", strategy="bogus"))
        assert False
    except ValueError:
        pass


def test_endpoints(client):
    r = client.get("/v1/reasoning/strategies").json()
    assert len(r) >= 8
    assert client.get("/v1/reasoning/strategies/tree_of_thoughts").status_code == 200
    assert client.get("/v1/reasoning/strategies/nope").status_code == 404
