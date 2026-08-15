"""Tests de l'assistant scopé (zone de compétence, agents ≤5, WebSocket)."""


def test_scope_from_registry(client):
    sc = client.get("/v1/assistant/one/scope").json()
    assert sc["known"] is True
    assert sc["name"] == "Lunziko One"
    assert len(sc["competence"]) >= 1


def test_agent_cap_and_duplicate(client):
    for role in ["compta", "facturation", "tresorerie", "paie", "ventes"]:
        client.post("/v1/assistant/one/agents", json={"role": role})
    dup = client.post("/v1/assistant/one/agents", json={"role": "compta"})
    assert dup.status_code == 409
    over = client.post("/v1/assistant/one/agents", json={"role": "stocks"})
    assert over.status_code == 409
    agents = client.get("/v1/assistant/one/agents").json()["agents"]
    assert len(agents) == 5


def test_ui_contract(client):
    uc = client.get("/v1/assistant/bi/ui-contract").json()
    assert uc["connection"]["websocket"] == "/v1/assistant/bi/ws"
    assert "ready" in uc["connection"]["protocol"]["server_events"]


def test_websocket_ready(client):
    with client.websocket_connect("/v1/assistant/one/ws") as ws:
        evt = ws.receive_json()
        assert evt["type"] == "ready"
        assert evt["app"] == "one"
        assert evt["scope"]["known"] is True
