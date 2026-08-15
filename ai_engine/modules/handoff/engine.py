"""HandoffEngine — résout l'app cible et produit des actions inter-applications.

Trois actions structurées (instructions, exécutées par l'app hôte / le HUB / Platform) :
  - redirect   : rediriger l'utilisateur vers une autre app pour poursuivre sa tâche ;
  - transfer   : transférer un fichier/dossier vers une autre app ;
  - open_with  : ouvrir un fichier dans l'app la plus adaptée.

La cible est validée contre le registre écosystème ; le fichier est résolu par type
(table filetypes) puis, à défaut, par recherche sémantique dans le registre.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.modules.ecosystem.engine import get_ecosystem_engine
from ai_engine.modules.handoff.filetypes import resolve_extension


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HandoffEngine:
    def __init__(self) -> None:
        self._eco = get_ecosystem_engine()

    def _app_name(self, slug: str) -> str:
        rec = self._eco.get_app(slug)
        return rec["name"] if rec else slug

    def _validate(self, slug: str) -> bool:
        return self._eco.get_app(slug) is not None

    async def _resolve_target_for_task(self, from_app: str, task: str) -> dict | None:
        try:
            hits = await self._eco.search(task, 4)
        except Exception:
            return None
        for h in hits:
            if h["slug"] != from_app:
                return {"app": h["slug"], "name": h.get("name", h["slug"]),
                        "score": h["score"], "via": "ecosystem-search"}
        return None

    async def _resolve_target_for_file(self, filename: str, hint: str = "") -> dict | None:
        byext = resolve_extension(filename)
        if byext:
            return {"app": byext["app"], "name": self._app_name(byext["app"]),
                    "module": byext["module"], "reason": byext["reason"],
                    "alternatives": byext["alternatives"], "via": "file-type"}
        # repli : recherche sémantique sur nom de fichier + indice
        try:
            hits = await self._eco.search(f"{filename} {hint}".strip(), 3)
        except Exception:
            hits = []
        if hits:
            h = hits[0]
            return {"app": h["slug"], "name": h.get("name", h["slug"]),
                    "module": None, "reason": "correspondance sémantique",
                    "alternatives": [], "via": "ecosystem-search"}
        return None

    # --- Actions ----------------------------------------------------------
    async def redirect(self, from_app: str, task: str, *, user_id: str | None = None) -> dict:
        target = await self._resolve_target_for_task(from_app, task)
        action = None
        if target:
            action = {
                "type": "redirect",
                "from_app": from_app,
                "to_app": target["app"],
                "to_name": target["name"],
                "task": task,
                "reason": f"« {target['name']} » est plus compétente pour cette tâche.",
                "confidence": round(target.get("score", 0.0), 4),
                "deep_link": f"lunziko://{target['app']}/continue",
                "executor": "host|hub",
                "target_known": self._validate(target["app"]),
            }
            self._log(user_id, from_app, "redirect", target["app"], task)
        return {"resolved": action is not None, "action": action, "from_app": from_app}

    async def open_with(self, from_app: str, filename: str, *, hint: str = "",
                        user_id: str | None = None) -> dict:
        target = await self._resolve_target_for_file(filename, hint)
        action = None
        if target:
            action = {
                "type": "open_with",
                "from_app": from_app,
                "to_app": target["app"],
                "to_name": target["name"],
                "module": target.get("module"),
                "resource": filename,
                "reason": f"{filename} s'ouvre mieux dans {target['name']}"
                          + (f" ({target['module']})" if target.get("module") else ""),
                "alternatives": target.get("alternatives", []),
                "resolved_via": target["via"],
                "deep_link": f"lunziko://{target['app']}/open?resource={filename}",
                "executor": "host|hub",
                "target_known": self._validate(target["app"]),
            }
            self._log(user_id, from_app, "open_with", target["app"], filename)
        return {"resolved": action is not None, "action": action, "resource": filename}

    async def transfer(self, from_app: str, resource: str, *, to_app: str | None = None,
                       mode: str = "copy", is_folder: bool = False,
                       hint: str = "", user_id: str | None = None) -> dict:
        if to_app:
            target = {"app": to_app, "name": self._app_name(to_app), "module": None, "via": "explicit"}
        else:
            target = await self._resolve_target_for_file(resource, hint) if not is_folder else None
            if target is None:
                # dossier ou type inconnu : tenter une résolution sémantique large
                t = await self._resolve_target_for_task(from_app, hint or resource)
                target = {"app": t["app"], "name": t["name"], "module": None, "via": "ecosystem-search"} if t else None
        if target is None:
            return {"resolved": False, "action": None, "resource": resource}
        action = {
            "type": "transfer",
            "from_app": from_app,
            "to_app": target["app"],
            "to_name": target["name"],
            "resource": resource,
            "kind": "folder" if is_folder else "file",
            "mode": mode if mode in ("copy", "move") else "copy",
            "module": target.get("module"),
            "resolved_via": target["via"],
            "deep_link": f"lunziko://{target['app']}/import?resource={resource}",
            "executor": "host|hub|platform",
            "target_known": self._validate(target["app"]),
        }
        self._log(user_id, from_app, "transfer", target["app"], resource)
        return {"resolved": True, "action": action, "resource": resource}

    # --- Journalisation (best-effort) -------------------------------------
    def _log(self, user_id: str | None, from_app: str, action: str, to_app: str, target: str) -> None:
        if not user_id:
            return
        try:
            import asyncio

            from ai_engine.modules.activity.engine import get_activity_engine

            coro = get_activity_engine().log(
                user_id, from_app, f"handoff.{action}", target=f"{to_app}:{target}"[:120],
                detail=f"handoff {action} → {to_app}", ts=_now(),
            )
            loop = asyncio.get_event_loop()
            loop.create_task(coro)  # non bloquant ; journalisation opportuniste
        except Exception:
            pass


def get_handoff_engine() -> HandoffEngine:
    return HandoffEngine()
