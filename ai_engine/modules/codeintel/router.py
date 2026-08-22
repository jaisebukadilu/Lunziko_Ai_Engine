"""Routeur Lunziko Code Intelligence — /v1/code-intelligence.

Exposé aux éditeurs/outils (PowerShell, VS Code, Xcode, Cursor…) via ce REST, via
l'endpoint OpenAI-compatible et via le serveur MCP (outils code_* du ToolRegistry).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.codeintel.editor import GuardrailError, get_safe_editor
from ai_engine.modules.codeintel.engine import get_code_intelligence
from ai_engine.modules.codeintel.git_tools import get_git_intelligence
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


# --- Écriture contrôlée (garde-fous : dry-run par défaut, confirm requis, backup) --------
class WriteRequest(BaseModel):
    root: str = Field(min_length=1)
    path: str = Field(min_length=1)
    content: str
    confirm: bool = False
    allow_overwrite: bool = False


class EditRequest(BaseModel):
    root: str
    path: str
    old_string: str = Field(min_length=1)
    new_string: str
    confirm: bool = False


class DeleteRequest(BaseModel):
    root: str
    path: str
    confirm: bool = False


class CommitRequest(BaseModel):
    root: str
    message: str = Field(min_length=1)
    confirm: bool = False


class CheckpointRequest(BaseModel):
    root: str
    label: str = ""
    confirm: bool = False


def _guard(fn):
    try:
        return fn()
    except GuardrailError as e:
        raise HTTPException(status_code=409, detail=f"garde-fou : {e}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/write")
def write(req: WriteRequest) -> dict:
    return _guard(lambda: get_safe_editor().write(
        req.root, req.path, req.content, confirm=req.confirm, allow_overwrite=req.allow_overwrite))


@router.post("/edit")
def edit(req: EditRequest) -> dict:
    return _guard(lambda: get_safe_editor().edit(
        req.root, req.path, req.old_string, req.new_string, confirm=req.confirm))


@router.post("/delete")
def delete(req: DeleteRequest) -> dict:
    return _guard(lambda: get_safe_editor().delete(req.root, req.path, confirm=req.confirm))


@router.post("/restore/{backup_id}")
def restore(backup_id: str) -> dict:
    return _guard(lambda: get_safe_editor().restore(backup_id))


@router.get("/backups")
def backups(root: str | None = None) -> list[dict]:
    return get_safe_editor().list_backups(root)


# --- Git (lecture libre ; checkpoint/commit sous confirm) --------------------------------
@router.get("/git/status")
def git_status(root: str) -> dict:
    return get_git_intelligence().status(root)


@router.get("/git/diff")
def git_diff(root: str, staged: bool = False) -> dict:
    return get_git_intelligence().diff(root, staged=staged)


@router.get("/git/log")
def git_log(root: str, n: int = 10) -> dict:
    return get_git_intelligence().log(root, n=n)


@router.post("/git/checkpoint")
def git_checkpoint(req: CheckpointRequest) -> dict:
    return get_git_intelligence().checkpoint(req.root, label=req.label, confirm=req.confirm)


@router.post("/git/commit")
def git_commit(req: CommitRequest) -> dict:
    return get_git_intelligence().commit(req.root, req.message, confirm=req.confirm)
