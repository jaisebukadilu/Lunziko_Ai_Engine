"""Tests de la Couche de Contexte Unifié (A-14 profile, A-15 assembler, A-16 appstate)."""


def test_appstate_put_get(client):
    client.put("/v1/appstate", json={"user_id": "cu", "app": "one", "screen": "Facturation",
                                     "last_error": "champ TVA manquant"})
    st = client.get("/v1/appstate", params={"user_id": "cu", "app": "one"}).json()["state"]
    assert st["screen"] == "Facturation"
    assert st["last_error"] == "champ TVA manquant"
    assert "expires_at" not in st  # champ interne masqué


def test_appstate_ttl_expired(client):
    client.put("/v1/appstate", json={"user_id": "cu2", "app": "bi", "screen": "X", "ttl": 1})
    import time
    time.sleep(1.2)
    st = client.get("/v1/appstate", params={"user_id": "cu2", "app": "bi"}).json()["state"]
    assert st is None  # purgé à la lecture


def test_profile_set_get(client):
    client.put("/v1/profile", json={"user_id": "cu3", "role": "comptable", "language": "fr",
                                    "preferences": {"theme": "dark"}})
    p = client.get("/v1/profile/cu3").json()
    assert p["role"] == "comptable"
    assert p["preferences"]["theme"] == "dark"


def test_profile_habits_from_activity(client):
    for _ in range(3):
        client.post("/v1/activity/log", json={"user_id": "cu4", "app": "Lunziko One", "action": "invoice"})
    client.post("/v1/activity/log", json={"user_id": "cu4", "app": "Lunziko BI", "action": "dashboard"})
    h = client.get("/v1/profile/cu4/habits").json()
    assert h["events"] == 4
    assert h["top_apps"][0]["app"] == "Lunziko One"


def test_context_assemble(client):
    client.put("/v1/profile", json={"user_id": "cu5", "role": "manager", "language": "fr"})
    client.post("/v1/activity/log", json={"user_id": "cu5", "app": "Lunziko One", "action": "reconcile", "status": "error"})
    client.put("/v1/appstate", json={"user_id": "cu5", "app": "one", "screen": "Trésorerie"})
    ctx = client.post("/v1/context/assemble", json={"user_id": "cu5", "app": "one", "query": "aide"}).json()
    assert ctx["profile"]["role"] == "manager"
    assert ctx["temporal"]["moment"] in {"nuit", "matin", "après-midi", "soir"}
    assert "CONTEXTE UTILISATEUR" in ctx["system_block"]
    assert any(a["action"] == "reconcile" for a in ctx["recent_activity"])
