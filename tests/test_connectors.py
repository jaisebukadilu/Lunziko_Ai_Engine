"""Tests des connecteurs RAG (ingestion multi-sources + recherche unifiée cross-namespace)."""


def test_connector_types(client):
    t = client.get("/v1/connectors/types").json()["connectors"]
    assert {"document", "chat", "email", "file"}.issubset(set(t))


def test_ingest_and_registry(client):
    r = client.post("/v1/connectors/ingest", json={
        "connector": "document", "namespace": "u1:docs",
        "items": [{"id": "d1", "title": "Trésorerie", "content": "Le solde de trésorerie est positif ce mois."},
                  {"id": "d2", "title": "Facture", "content": "La facture FA-001 est en attente de paiement."}]}).json()
    assert r["documents"] == 2 and r["chunks_indexed"] >= 2
    ns = client.get("/v1/connectors/namespaces").json()["namespaces"]
    assert any(n["id"] == "u1:docs" and "document" in n["connectors"] for n in ns)


def test_ingest_invalid_connector(client):
    r = client.post("/v1/connectors/ingest", json={
        "connector": "telepathy", "namespace": "x", "items": [{"content": "y"}]})
    assert r.status_code == 422


def test_unified_search_cross_namespace(client):
    client.post("/v1/connectors/ingest", json={
        "connector": "email", "namespace": "u1:mail",
        "items": [{"id": "m1", "content": "Réunion budget prévue jeudi avec l'équipe finance."}]})
    client.post("/v1/connectors/ingest", json={
        "connector": "chat", "namespace": "u1:chat",
        "items": [{"id": "c1", "content": "On a parlé du rapprochement bancaire hier."}]})
    # recherche unifiée sur toutes les sources connues (namespaces=None)
    res = client.post("/v1/connectors/search", json={"query": "budget finance réunion", "k": 3}).json()
    assert res["results"], "au moins un résultat attendu"
    # chaque résultat porte son namespace + sa source
    assert all("namespace" in h and "source" in h for h in res["results"])
    top = res["results"][0]
    assert top["source"] in {"document", "email", "chat"}
