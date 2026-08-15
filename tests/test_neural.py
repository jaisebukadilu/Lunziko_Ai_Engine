"""Tests du système neuronal : backends, routeur d'intention, entraîneur ML."""


def test_backends_include_numpy(client):
    b = client.get("/v1/neural/backends").json()
    assert "numpy" in b["available"]


def test_intent_router_hybrid(client):
    r = client.post("/v1/neural/route", json={"query": "rédige une note de synthèse soignée"}).json()
    assert r["capability"] == "document"
    assert r["fusion"] in ("neural", "hybrid")


def test_ml_train_predict_persist(client):
    examples = [
        {"text": "la facture est en retard de paiement", "label": "finance"},
        {"text": "rembourse cette dépense fournisseur", "label": "finance"},
        {"text": "le solde bancaire est négatif", "label": "finance"},
        {"text": "planifie un entretien de recrutement", "label": "rh"},
        {"text": "gère les congés payés", "label": "rh"},
        {"text": "mets à jour le contrat de travail", "label": "rh"},
    ]
    t = client.post("/v1/neural/ml/train", json={"name": "tickets", "examples": examples}).json()
    assert set(t["classes"]) == {"finance", "rh"}
    p = client.post("/v1/neural/ml/predict", json={"name": "tickets", "text": "note de frais à rembourser"}).json()
    assert p["label"] == "finance"
    # persistance : le modèle apparaît dans la liste
    models = client.get("/v1/neural/ml/models").json()["models"]
    assert any(m["model"] == "tickets" for m in models)


def test_inference_catalog(client):
    inf = client.get("/v1/neural/inference").json()
    ids = {e["id"] for e in inf["engines"]}
    assert {"ollama", "vllm", "llamacpp", "lunziko"}.issubset(ids)
