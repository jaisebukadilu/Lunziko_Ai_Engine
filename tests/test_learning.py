"""Test mémoire persistante à apprentissage continu (« apprend toujours, n'oublie jamais »)."""

import asyncio

from ai_engine.modules.learning.engine import get_continuous_memory


def test_remember_and_recall():
    m = get_continuous_memory()
    asyncio.run(m.remember("u1", "Joe préfère le thème sombre Command Center", importance=0.8))
    asyncio.run(m.remember("u1", "Le lingála est une langue prioritaire pour Yekoli"))
    hits = asyncio.run(m.recall("u1", "quel thème préfère Joe ?", k=3))
    assert hits and "sombre" in hits[0]["text"]


def test_reinforce_on_duplicate_no_growth():
    m = get_continuous_memory()
    r1 = asyncio.run(m.remember("u2", "Le primary du HUB est #007AFF", importance=0.6))
    assert r1["action"] == "created"
    before = m.stats("u2")["total"]
    # réapprendre la même chose -> renforce, ne crée PAS de doublon
    r2 = asyncio.run(m.remember("u2", "Le primary du HUB est #007AFF", importance=0.9))
    assert r2["action"] == "reinforced"
    assert r2["reinforcement"] >= 1
    assert m.stats("u2")["total"] == before  # aucune nouvelle ligne


def test_never_forgets_archive_is_soft():
    m = get_continuous_memory()
    r = asyncio.run(m.remember("u3", "Décision D-001 : IA via gateway Platform"))
    mid = r["id"]
    assert m.archive("u3", mid) is True
    # archivé mais toujours présent en base
    ids = [x["id"] for x in m.timeline("u3", include_archived=True)]
    assert mid in ids
    # exclu du rappel par défaut, retrouvable si include_archived
    default = asyncio.run(m.recall("u3", "décision gateway Platform", include_archived=False))
    witharch = asyncio.run(m.recall("u3", "décision gateway Platform", include_archived=True))
    assert all(h["id"] != mid for h in default)
    assert any(h["id"] == mid for h in witharch)


def test_reinforcement_boosts_ranking():
    m = get_continuous_memory()
    asyncio.run(m.remember("u4", "alpha budget cantine", importance=0.5))
    r = asyncio.run(m.remember("u4", "beta budget cantine", importance=0.5))
    # renforcer beta plusieurs fois
    for _ in range(3):
        m.reinforce("u4", r["id"])
    hits = asyncio.run(m.recall("u4", "budget cantine", k=2))
    assert hits[0]["id"] == r["id"]  # le plus renforcé remonte


def test_consolidate_links_not_deletes():
    m = get_continuous_memory()
    asyncio.run(m.remember("u5", "La capitale du projet est Kinshasa", importance=0.5))
    asyncio.run(m.remember("u5", "La capitale du projet est Kinshasa", importance=0.5))
    res = asyncio.run(m.consolidate("u5"))
    # après consolidation : rien n'est supprimé (total inchangé)
    total = m.stats("u5")["total"]
    assert total >= 1
    # tout reste dans la timeline (superseded inclus)
    assert len(m.timeline("u5", include_archived=True)) == total


def test_endpoints(client):
    r = client.post("/v1/learning/remember",
                    json={"scope": "api", "text": "Le registre maître est la source de vérité"})
    assert r.status_code == 200 and r.json()["action"] in ("created", "reinforced")
    r = client.post("/v1/learning/recall", json={"scope": "api", "query": "source de vérité"})
    assert r.status_code == 200 and isinstance(r.json(), list)
    st = client.get("/v1/learning/stats/api").json()
    assert st["never_forgets"] is True
