"""Test LAIA : collaboration Brain-to-Brain (pipeline sur état de tâche partagé)."""


def test_collaboration_pipeline(client):
    r = client.post("/v1/orchestrator/plan", json={
        "goal": "analyse les ventes, rédige un rapport et prépare une présentation"}).json()
    collab = r["collaboration"]
    assert len(collab) == len(r["plan"]) >= 3
    # 1re étape ne consomme rien
    assert collab[0]["consumes"] == []
    # étape suivante consomme la précédente (collaboration séquentielle)
    assert collab[1]["consumes"] == [collab[0]["step"]]
    assert collab[-1]["consumes"][-1] == collab[-2]["step"]
    # chaque étape produit un artefact identifié
    assert all(c["produces"].startswith("artifact:") for c in collab)
    # la collaboration est consignée sur le blackboard
    task = client.get("/v1/blackboard/tasks/" + r["task_id"]).json()
    assert task["decisions"][0]["collaboration"]
