"""Tests activity (journal d'actions) + smoke gateway."""


def test_health_modules(client):
    m = client.get("/health").json()["modules"]
    for mod in ("ecosystem", "activity", "neural", "data", "assistant", "handoff"):
        assert m.get(mod) is True


def test_activity_log_timeline_search(client):
    client.post("/v1/activity/log", json={
        "user_id": "u1", "app": "Lunziko One", "action": "create_invoice", "target": "FA-1"})
    client.post("/v1/activity/log", json={
        "user_id": "u1", "app": "Lunziko One", "action": "reconcile", "status": "error",
        "detail": "rapprochement bancaire échoué"})
    tl = client.get("/v1/activity/timeline", params={"user_id": "u1"}).json()
    assert tl["count"] == 2
    # tri décroissant : la dernière action loggée en tête
    assert tl["events"][0]["action"] == "reconcile"
    s = client.post("/v1/activity/search", json={"user_id": "u1", "query": "rapprochement bancaire", "k": 2}).json()
    assert s["results"][0]["action"] == "reconcile"


def test_activity_clear(client):
    client.post("/v1/activity/log", json={"user_id": "u2", "app": "BI", "action": "open"})
    client.delete("/v1/activity/u2")
    tl = client.get("/v1/activity/timeline", params={"user_id": "u2"}).json()
    assert tl["count"] == 0
