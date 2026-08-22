"""GitIntelligence — opérations Git sûres pour Code Intelligence.

Lecture libre (status/diff/branche/log) ; écriture (checkpoint/commit) sous garde-fous :
  * refus hors dépôt Git ;
  * commit/checkpoint exigent `confirm=True` ;
  * jamais de `push`, `reset --hard`, `clean`, `rebase` ni autre opération destructive.
Un « checkpoint » = créer une branche de sécurité + commit de l'état courant AVANT édition,
pour pouvoir revenir en arrière.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

_TIMEOUT = 30
# Sous-commandes autorisées (jamais push/reset/clean/rebase/rm…).
_ALLOWED = {"status", "diff", "rev-parse", "branch", "log", "add", "commit", "checkout", "stash"}


def _run(root: str, args: list[str]) -> dict:
    if args and args[0] not in _ALLOWED:
        return {"ok": False, "error": f"sous-commande git non autorisée : {args[0]}"}
    try:
        p = subprocess.run(["git", *args], cwd=root, capture_output=True,
                           text=True, timeout=_TIMEOUT)
        return {"ok": p.returncode == 0, "code": p.returncode,
                "out": p.stdout.strip(), "err": p.stderr.strip()}
    except FileNotFoundError:
        return {"ok": False, "error": "git introuvable sur ce système"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class GitIntelligence:
    def is_repo(self, root: str) -> bool:
        r = _run(root, ["rev-parse", "--is-inside-work-tree"])
        return r.get("ok") and r.get("out") == "true"

    def status(self, root: str) -> dict:
        if not self.is_repo(root):
            return {"repo": False}
        st = _run(root, ["status", "--short", "--branch"])
        br = _run(root, ["rev-parse", "--abbrev-ref", "HEAD"])
        return {"repo": True, "branch": br.get("out"), "status": st.get("out")}

    def diff(self, root: str, staged: bool = False) -> dict:
        if not self.is_repo(root):
            return {"repo": False}
        args = ["diff", "--cached"] if staged else ["diff"]
        r = _run(root, args)
        return {"repo": True, "diff": r.get("out", "")}

    def log(self, root: str, n: int = 10) -> dict:
        if not self.is_repo(root):
            return {"repo": False}
        r = _run(root, ["log", f"-{n}", "--oneline"])
        return {"repo": True, "log": r.get("out", "")}

    def checkpoint(self, root: str, *, label: str = "", confirm: bool = False) -> dict:
        """Crée une branche de sécurité + commit l'état courant AVANT édition."""
        if not self.is_repo(root):
            return {"repo": False, "error": "pas un dépôt Git"}
        branch = f"lunziko-checkpoint/{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        if label:
            branch += "-" + "".join(c for c in label if c.isalnum() or c in "-_")[:24]
        if not confirm:
            return {"repo": True, "dry_run": True, "would_create_branch": branch,
                    "note": "confirmez pour créer la branche de sécurité + commit"}
        co = _run(root, ["checkout", "-b", branch])
        if not co.get("ok"):
            return {"repo": True, "ok": False, "step": "checkout", **co}
        _run(root, ["add", "-A"])
        cm = _run(root, ["commit", "-m", f"checkpoint: {label or 'avant édition Code Intelligence'}"])
        return {"repo": True, "ok": True, "branch": branch,
                "committed": cm.get("ok"), "detail": cm.get("out") or cm.get("err")}

    def commit(self, root: str, message: str, *, add_all: bool = True,
               confirm: bool = False) -> dict:
        if not self.is_repo(root):
            return {"repo": False, "error": "pas un dépôt Git"}
        if not message.strip():
            return {"repo": True, "ok": False, "error": "message de commit requis"}
        if not confirm:
            st = _run(root, ["status", "--short"])
            return {"repo": True, "dry_run": True, "pending": st.get("out", ""),
                    "note": "confirmez pour committer (jamais de push automatique)"}
        if add_all:
            _run(root, ["add", "-A"])
        cm = _run(root, ["commit", "-m", message])
        return {"repo": True, "ok": cm.get("ok"), "detail": cm.get("out") or cm.get("err"),
                "note": "commit local uniquement — aucun push effectué"}


def get_git_intelligence() -> GitIntelligence:
    return GitIntelligence()
