"""Tests de l'Action Registry (déclaration + invocation d'actions d'app)."""


def test_register_and_list(client):
    client.post("/v1/actions/register", json={
        "app": "one", "action": "create_invoice", "description": "Créer une facture",
        "parameters": {"type": "object", "properties": {"client": {"type": "string"},
                                                        "montant": {"type": "number"}},
                       "required": ["client", "montant"]},
        "requires_confirmation": True})
    lst = client.get("/v1/actions", params={"app": "one"}).json()
    assert lst["count"] >= 1
    assert any(a["action"] == "create_invoice" for a in lst["actions"])


def test_invoke_valid(client):
    client.post("/v1/actions/register", json={
        "app": "docia", "action": "send_mail",
        "parameters": {"type": "object", "properties": {"to": {"type": "string"}},
                       "required": ["to"]}})
    r = client.post("/v1/actions/invoke", json={
        "app": "docia", "action": "send_mail", "arguments": {"to": "x@lunziko.app"}}).json()
    assert r["resolved"] is True
    inv = r["invocation"]
    assert inv["type"] == "action_invocation"
    assert inv["app"] == "docia" and inv["action"] == "send_mail"
    assert inv["deep_link"].startswith("lunziko://docia/action/")


def test_invoke_missing_arg(client):
    client.post("/v1/actions/register", json={
        "app": "one", "action": "post_entry",
        "parameters": {"type": "object", "properties": {"amount": {"type": "number"}},
                       "required": ["amount"]}})
    r = client.post("/v1/actions/invoke", json={"app": "one", "action": "post_entry", "arguments": {}})
    assert r.status_code == 422


def test_invoke_unknown(client):
    r = client.post("/v1/actions/invoke", json={"app": "x", "action": "nope", "arguments": {}})
    assert r.status_code == 404
