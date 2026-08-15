"""Tests du module ecosystem (ingestion du registre fixture)."""


def test_registry_synced(client):
    st = client.get("/v1/ecosystem/status").json()
    assert st["registry_found"] is True
    assert st["apps_indexed"] >= 5


def test_apps_listed(client):
    apps = client.get("/v1/ecosystem/apps").json()
    slugs = {a["slug"] for a in apps["apps"]}
    assert {"one", "bi", "dociapub", "cad"}.issubset(slugs)


def test_get_app_one(client):
    one = client.get("/v1/ecosystem/apps/one").json()
    assert one["name"] == "Lunziko One"
    assert len(one["functions"]) >= 1


def test_semantic_search(client):
    res = client.post("/v1/ecosystem/search", json={"query": "tableaux de bord et KPI", "k": 3}).json()
    assert res["results"], "au moins un résultat attendu"
    assert res["results"][0]["slug"] in {"bi", "one"}
