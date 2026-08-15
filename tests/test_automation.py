"""Tests du moteur d'automatisation (A-10) : flux de nœuds chaînant des outils."""


def test_save_flow_validates_tools(client):
    bad = client.post("/v1/automation/flows", json={
        "name": "bad", "nodes": [{"id": "n1", "tool": "outil_inexistant", "args": {}}]})
    assert bad.status_code == 422


def test_flow_run_chains_tools(client):
    # nœud 1 : nettoie un texte (référence l'entrée du flux)
    r = client.post("/v1/automation/flows", json={
        "name": "clean_then_search",
        "nodes": [
            {"id": "clean", "tool": "data_clean_text", "args": {"texts": "$input.texts"}},
            {"id": "find", "tool": "ecosystem_search", "args": {"query": "$input.query", "k": 2}},
        ]})
    assert r.json()["nodes"] == 2
    run = client.post("/v1/automation/flows/clean_then_search/run", json={
        "input": {"texts": ["a", "a", "b"], "query": "dashboards"}}).json()
    assert run["status"] == "ok"
    assert len(run["steps"]) == 2
    # le nœud clean a bien reçu la liste résolue depuis $input.texts
    assert run["steps"][0]["output"]["texts_out"] == 2


def test_flow_run_and_list(client):
    client.post("/v1/automation/flows", json={
        "name": "f2", "nodes": [{"id": "s", "tool": "ecosystem_search", "args": {"query": "$input.q"}}]})
    client.post("/v1/automation/flows/f2/run", json={"input": {"q": "finance"}})
    runs = client.get("/v1/automation/runs", params={"flow": "f2"}).json()["runs"]
    assert runs and runs[0]["flow"] == "f2"


def test_run_unknown_flow(client):
    r = client.post("/v1/automation/flows/nope/run", json={"input": {}})
    assert r.status_code == 404
