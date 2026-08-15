"""Test : l'orchestrateur route les Brains multimédias vers le Graphics Engine.

Offline (Graphics Engine non branché) : la sous-tâche graphique est 'deferred' mais porte
déjà `engine=graphics` + les groupes d'endpoints cibles (délégation prête)."""


def test_graphics_brain_delegation_offline(client):
    r = client.post("/v1/orchestrator/run", json={"goal": "conçois un modèle cad et génère une image"}).json()
    graphic = [res for res in r["results"] if res.get("engine") == "graphics"]
    assert graphic, "au moins une sous-tâche déléguée au Graphics Engine attendue"
    g = graphic[0]
    assert g["brain"] in {"3d", "cad", "image", "vision", "video", "document"}
    assert g["status"] == "deferred"  # non branché ici
    assert g["groups"], "les groupes d'endpoints cibles doivent être renseignés"
    assert "reason" in g and "non branché" in g["reason"]
