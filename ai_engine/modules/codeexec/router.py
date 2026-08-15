"""Routeur code-exec — /v1/code-exec/{status,eval,run}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.config import get_settings
from ai_engine.modules.codeexec.safe_eval import SafeEvalError, safe_eval
from ai_engine.modules.codeexec.sandbox import available_languages, run_code

router = APIRouter(prefix="/v1/code-exec", tags=["code-exec"])


class EvalRequest(BaseModel):
    expression: str = Field(min_length=1)
    variables: dict = Field(default_factory=dict)


class RunRequest(BaseModel):
    code: str = Field(min_length=1)
    language: str = "python"
    stdin: str = ""


@router.get("/status")
def status() -> dict:
    s = get_settings()
    return {
        "safe_eval": True,
        "sandbox_enabled": s.ae_code_exec_enabled,
        "languages": available_languages() if s.ae_code_exec_enabled else [],
        "timeout_s": s.ae_code_exec_timeout,
        "max_output": s.ae_code_exec_max_output,
        "note": "Niveau 1 (sandbox) à activer uniquement sous isolation OS pour code non fiable",
    }


@router.post("/eval")
def eval_expr(req: EvalRequest) -> dict:
    try:
        return {"result": safe_eval(req.expression, req.variables)}
    except SafeEvalError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/run")
def run(req: RunRequest) -> dict:
    return run_code(req.code, req.language, stdin=req.stdin)
