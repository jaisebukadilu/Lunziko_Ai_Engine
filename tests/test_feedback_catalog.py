"""Tests feedback (A-18) et catalog (A-17)."""


def test_feedback_record_and_stats(client):
    client.post("/v1/feedback", json={"rating": "up", "app": "fbapp", "query": "q1"})
    client.post("/v1/feedback", json={"rating": "down", "app": "fbapp", "query": "q2",
                                      "correction": "utiliser le taux de TVA 20%"})
    s = client.get("/v1/feedback/stats", params={"app": "fbapp"}).json()
    assert s["total"] == 2 and s["up"] == 1 and s["down"] == 1
    assert s["corrections"] == 1
    assert s["satisfaction"] == 0.5


def test_feedback_corrections_fewshot(client):
    client.post("/v1/feedback", json={"rating": "down", "app": "fbapp2", "query": "calcul marge",
                                      "correction": "la marge = (PV-PA)/PV"})
    c = client.get("/v1/feedback/corrections", params={"app": "fbapp2"}).json()["corrections"]
    assert c and c[0]["correction"].startswith("la marge")


def test_feedback_invalid_rating(client):
    r = client.post("/v1/feedback", json={"rating": "maybe"})
    assert r.status_code == 422


def test_catalog_register_and_resolve(client):
    client.post("/v1/catalog/register", json={
        "app": "one", "dataset": "factures",
        "fields": {"numero": "string", "montant_ht": "number", "tva": "number", "client": "string"},
        "description": "factures de vente avec montants et TVA"})
    client.post("/v1/catalog/register", json={
        "app": "one", "dataset": "employes",
        "fields": {"nom": "string", "poste": "string", "salaire": "number"},
        "description": "effectifs RH et rémunération"})
    schemas = client.get("/v1/catalog/schemas", params={"app": "one"}).json()
    assert schemas["count"] == 2
    one = client.get("/v1/catalog/schemas/one:factures").json()
    assert "montant_ht" in one["fields"]
    res = client.post("/v1/catalog/resolve", json={"query": "montant et TVA d'une facture", "k": 2}).json()
    assert res["matches"][0]["dataset"] == "factures"
