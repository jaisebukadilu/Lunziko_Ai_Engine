"""Test Lunziko Code Intelligence — langages, détection, index/recherche, architecture, symboles."""

import asyncio
from pathlib import Path


def test_language_catalog_broad():
    from ai_engine.modules.codeintel.languages import all_languages, language_count
    assert language_count() >= 60  # couverture large « tous les langages »
    ids = {l["id"] for l in all_languages()}
    for expected in ("python", "javascript", "typescript", "rust", "go", "swift", "kotlin",
                     "csharp", "cpp", "powershell", "sql", "haskell", "cobol", "solidity"):
        assert expected in ids, f"{expected} manquant"


def test_detect_by_extension():
    from ai_engine.modules.codeintel.engine import get_code_intelligence
    ci = get_code_intelligence()
    assert ci.detect_language("scripts/deploy.ps1")["id"] == "powershell"
    assert ci.detect_language("src/App.tsx")["id"] == "typescript"
    assert ci.detect_language("main.swift")["id"] == "swift"
    assert ci.detect_language("Dockerfile")["id"] == "dockerfile"
    assert ci.detect_language("weird.zzz") is None


def test_symbols_multilang():
    from ai_engine.modules.codeintel.engine import get_code_intelligence
    ci = get_code_intelligence()
    code = "def foo():\n    pass\nclass Bar:\n    pass\nfunc baz() {}\nfn qux() {}\n"
    names = {s["name"] for s in ci.symbols(code)}
    assert {"foo", "Bar", "baz", "qux"} <= names


def test_understand_and_index(tmp_path):
    from ai_engine.modules.codeintel.engine import get_code_intelligence
    ci = get_code_intelligence()
    (tmp_path / "app.py").write_text("def hello():\n    return 'facturation client'\n", encoding="utf-8")
    (tmp_path / "util.ts").write_text("export function sum(a:number,b:number){return a+b}\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("fastapi==0.115\npydantic>=2\n", encoding="utf-8")

    arch = ci.understand(str(tmp_path))
    assert arch["files_scanned"] >= 3
    assert "python" in arch["languages"]

    deps = ci.dependencies(str(tmp_path))
    assert "pip" in deps and "fastapi" in deps["pip"]

    meta = asyncio.run(ci.index_repo(str(tmp_path), project="proj_test"))
    assert meta["files_indexed"] >= 2
    hits = asyncio.run(ci.search_code("proj_test", "facturation client", k=3))
    assert hits and hits[0]["path"] == "app.py"


def test_endpoints(client):
    r = client.get("/v1/code-intelligence/languages").json()
    assert r["meta"]["count"] >= 60
    d = client.get("/v1/code-intelligence/detect", params={"path": "x.rs"}).json()
    assert d["language"]["id"] == "rust"
    r = client.post("/v1/code-intelligence/symbols", json={"content": "def a():\n pass\n"})
    assert any(s["name"] == "a" for s in r.json())


def test_tools_registered():
    from ai_engine.modules.tools.registry import get_tool_registry
    names = get_tool_registry().names()
    for t in ("code_detect_language", "code_understand", "code_search",
              "code_dependencies", "code_project_context"):
        assert t in names
