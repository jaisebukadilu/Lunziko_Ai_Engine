"""Routeur Lunziko Code Intelligence — /v1/code-intelligence.

Exposé aux éditeurs/outils (PowerShell, VS Code, Xcode, Cursor…) via ce REST, via
l'endpoint OpenAI-compatible et via le serveur MCP (outils code_* du ToolRegistry).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.codeintel.engine import get_code_intelligence
from ai_engine.modules.codeintel.languages import all_languages

router = APIRouter(prefix="/v1/code-intelligence", tags=["code-intelligence"])


class IndexRequest(BaseModel):
    root: str = Field(min_length=1)
    project: str = Field(min_length=1)


class SearchRequest(BaseModel):
    project: str
    query: str = Field(min_length=1)
    k: int = Field(default=8, ge=1, le=50)


class SymbolsRequest(BaseModel):
    content: str = Field(min_length=1)


@router.get("/languages")
def languages() -> dict:
    return {"meta": get_code_intelligence().languages_meta(), "languages": all_languages()}


@router.get("/detect")
def detect(path: str) -> dict:
    lang = get_code_intelligence().detect_language(path)
    if lang is None:
        return {"path": path, "language": None}
    return {"path": path, "language": lang}


@router.post("/index")
async def index(req: IndexRequest) -> dict:
    try:
        return await get_code_intelligence().index_repo(req.root, req.project)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dossier introuvable: {req.root}")


@router.post("/search")
async def search(req: SearchRequest) -> list[dict]:
    return await get_code_intelligence().search_code(req.project, req.query, k=req.k)


@router.get("/understand")
def understand(root: str) -> dict:
    try:
        return get_code_intelligence().understand(root)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dossier introuvable: {root}")


@router.get("/dependencies")
def dependencies(root: str) -> dict:
    return get_code_intelligence().dependencies(root)


@router.post("/symbols")
def symbols(req: SymbolsRequest) -> list[dict]:
    return get_code_intelligence().symbols(req.content)


@router.get("/projects")
def projects() -> list[dict]:
    return get_code_intelligence().indexed_projects()


@router.get("/project/{project}")
def project_context(project: str) -> dict:
    return get_code_intelligence().project_context(project)
