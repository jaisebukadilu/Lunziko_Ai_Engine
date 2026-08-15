"""Sandbox subprocess (Niveau 1) — exécution isolée du moteur, opt-in.

Isolation « soft » : sous-processus séparé, cwd temporaire jetable, env minimal, timeout,
sortie plafonnée. Pour du code non fiable, exiger une isolation OS (conteneur/firejail) en
amont — cf. CODE_EXECUTION_SANDBOX.md. DÉSACTIVÉ tant que AE_CODE_EXEC_ENABLED != true.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ai_engine.config import get_settings

# Langages -> commande d'exécution d'un fichier.
_RUNNERS = {
    "python": [sys.executable, "-I", "-S"],
}


def available_languages() -> list[str]:
    langs = ["python"]
    if shutil.which("node"):
        langs.append("node")
    return langs


def run_code(code: str, language: str = "python", *, stdin: str = "") -> dict:
    s = get_settings()
    if not s.ae_code_exec_enabled:
        return {"executed": False, "reason": "sandbox désactivé (AE_CODE_EXEC_ENABLED=false)",
                "hint": "activer uniquement dans un environnement OS isolé"}
    language = language.lower()
    if language not in ("python", "node"):
        return {"executed": False, "reason": f"langage non supporté: {language}"}
    if language == "node" and not shutil.which("node"):
        return {"executed": False, "reason": "node introuvable"}

    workdir = Path(tempfile.mkdtemp(prefix="ae_exec_"))
    try:
        ext = "py" if language == "python" else "js"
        src = workdir / f"main.{ext}"
        src.write_text(code, encoding="utf-8")
        cmd = (_RUNNERS["python"] if language == "python" else ["node"]) + [str(src)]
        start = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd, cwd=str(workdir), input=stdin, capture_output=True, text=True,
                timeout=s.ae_code_exec_timeout, env={"PATH": ""},  # env minimal
            )
            stdout, stderr, code_ = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            stdout, stderr, code_ = (e.stdout or ""), (e.stderr or ""), 124
        cap = s.ae_code_exec_max_output
        return {
            "executed": True, "language": language,
            "stdout": (stdout or "")[:cap], "stderr": (stderr or "")[:cap],
            "exit_code": code_, "timed_out": timed_out,
            "duration_ms": round((time.monotonic() - start) * 1000, 1),
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
