"""Test personnalité autonome/résiliente — boucle ReAct « ne renonce jamais » (offline)."""

import asyncio

from ai_engine.modules.autonomy.engine import ResilientAgent
from ai_engine.modules.autonomy.persona import RESILIENT_PERSONA, build_system_prompt
from ai_engine.modules.learning.engine import get_continuous_memory


def test_persona_forbids_giving_up():
    assert "n'abandonnes JAMAIS" in RESILIENT_PERSONA
    p = build_system_prompt([{"source": "error", "text": "échec X déjà vu"}])
    assert "échec X déjà vu" in p  # la mémoire est injectée avant d'agir


def test_solves_and_logs_solution():
    async def reason(*, goal, memories, history):
        if not history:
            return {"action": "web_search", "args": {"q": "x"}, "thought": "chercher"}
        return {"done": True, "answer": "trouvé la réponse"}

    async def execute(action, args):
        return {"ok": True, "result": "ok"}

    agent = ResilientAgent(reason_fn=reason, execute_fn=execute)
    res = asyncio.run(agent.solve("résoudre X", scope="ag1"))
    assert res["status"] == "solved" and res["gave_up"] is False
    # la solution est apprise dans la LTM
    hits = asyncio.run(get_continuous_memory().recall("ag1", "réponse X", k=5))
    assert any("SOLUTION" in h["text"] for h in hits)


def test_retries_on_failure_then_adapts():
    calls = {"n": 0}

    async def reason(*, goal, memories, history):
        # après 2 échecs observés, conclut
        errors = [h for h in history if not h["observation"]["ok"]]
        if len(errors) >= 2:
            return {"done": True, "answer": "adapté après échecs"}
        return {"action": "try", "args": {}, "thought": "tenter"}

    async def execute(action, args):
        calls["n"] += 1
        return {"ok": False, "error": "boom"}

    agent = ResilientAgent(reason_fn=reason, execute_fn=execute)
    res = asyncio.run(agent.solve("tâche difficile", scope="ag2", max_iterations=5))
    assert calls["n"] >= 2          # a réessayé
    assert res["status"] == "solved"
    # les erreurs sont journalisées dans la LTM
    errs = asyncio.run(get_continuous_memory().recall("ag2", "ERREUR tâche difficile", k=5))
    assert any(h["source"] == "error" for h in errs)


def test_never_gives_up_on_exhaustion():
    async def reason(*, goal, memories, history):
        return {"action": "try", "args": {}, "thought": "encore"}

    async def execute(action, args):
        return {"ok": False, "error": "toujours faux"}

    agent = ResilientAgent(reason_fn=reason, execute_fn=execute)
    res = asyncio.run(agent.solve("impossible", scope="ag3", max_iterations=3))
    assert res["status"] == "unresolved"
    assert res["gave_up"] is False and res["will_retry"] is True
    # un problème ouvert est mémorisé pour être retenté
    open_probs = asyncio.run(
        get_continuous_memory().recall("ag3", "PROBLÈME OUVERT impossible", k=5))
    assert any(h["source"] == "open_problem" for h in open_probs)


def test_endpoints(client):
    r = client.get("/v1/autonomy/persona").json()
    assert r["never_gives_up"] is True and r["learns_from_errors"] is True
