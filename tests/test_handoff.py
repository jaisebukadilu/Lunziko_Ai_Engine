"""Tests du module handoff (redirection / transfert / ouverture inter-apps)."""

import pytest


@pytest.mark.parametrize("filename,app,module", [
    ("budget.xlsx", "dociapub", "MySheet"),
    ("plan.dwg", "cad", "CAO"),
    ("photo.png", "vidiapub", "Photo"),
    ("slides.pptx", "dociapub", "MySlides"),
    ("model.ifc", "cad", "BIM"),
    ("contrat.docx", "dociapub", "MyWord"),
])
def test_open_with_by_filetype(client, filename, app, module):
    r = client.post("/v1/handoff/open-with", json={"from_app": "one", "filename": filename}).json()
    assert r["resolved"] is True
    assert r["action"]["to_app"] == app
    assert r["action"]["module"] == module


def test_transfer_file_and_folder(client):
    f = client.post("/v1/handoff/transfer", json={"from_app": "dociapub", "resource": "rapport.xlsx"}).json()
    assert f["action"]["to_app"] == "dociapub"
    assert f["action"]["kind"] == "file"
    d = client.post("/v1/handoff/transfer", json={
        "from_app": "one", "resource": "/projets/clientA", "to_app": "dociapub",
        "is_folder": True, "mode": "move"}).json()
    assert d["action"]["kind"] == "folder"
    assert d["action"]["mode"] == "move"


def test_redirect_to_competent_app(client):
    r = client.post("/v1/handoff/redirect", json={
        "from_app": "cad", "task": "analyser la trésorerie et les factures"}).json()
    assert r["resolved"] is True
    assert r["action"]["to_app"] in {"one", "bi"}
    assert r["action"]["deep_link"].startswith("lunziko://")
