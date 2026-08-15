"""ActionRegistry — déclaration, découverte, validation et invocation d'actions d'app.

Une action = {app, action, description, parameters (schéma JSON), requires_confirmation}.
`invoke` valide les arguments (champs requis) et renvoie une **instruction structurée** que
l'app hôte exécute. L'AI Engine ne modifie jamais l'application lui-même.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.core.registry import get_storage

NS = "action_registry"


def _aid(app: str, action: str) -> str:
    return f"{app}:{action}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ActionRegistry:
    def __init__(self) -> None:
        self._store = get_storage()

    def register(self, app: str, action: str, description: str = "",
                 parameters: dict | None = None, requires_confirmation: bool = False,
                 executor: str = "host") -> dict:
        aid = _aid(app, action)
        rec = {"id": aid, "app": app, "action": action, "description": description,
               "parameters": parameters or {"type": "object", "properties": {}},
               "requires_confirmation": requires_confirmation, "executor": executor,
               "updated_at": _now()}
        self._store.put(NS, aid, rec)
        return {"id": aid, "app": app, "action": action}

    def list(self, app: str | None = None) -> list[dict]:
        rows = self._store.list(NS)
        if app:
            rows = [r for r in rows if r.get("app") == app]
        return sorted(rows, key=lambda r: r.get("id", ""))

    def get(self, app: str, action: str) -> dict | None:
        return self._store.get(NS, _aid(app, action))

    def delete(self, app: str, action: str) -> bool:
        return self._store.delete(NS, _aid(app, action))

    def invoke(self, app: str, action: str, arguments: dict | None = None,
               *, user_id: str | None = None) -> dict:
        rec = self.get(app, action)
        if rec is None:
            raise KeyError(f"action inconnue: {app}:{action}")
        arguments = arguments or {}
        required = (rec.get("parameters") or {}).get("required", [])
        missing = [r for r in required if r not in arguments]
        if missing:
            raise ValueError(f"arguments manquants: {', '.join(missing)}")
        invocation = {
            "type": "action_invocation",
            "app": app,
            "action": action,
            "arguments": arguments,
            "requires_confirmation": rec.get("requires_confirmation", False),
            "executor": rec.get("executor", "host"),
            "deep_link": f"lunziko://{app}/action/{action}",
        }
        self._log(user_id, app, action)
        return {"resolved": True, "invocation": invocation}

    def _log(self, user_id: str | None, app: str, action: str) -> None:
        if not user_id:
            return
        try:
            import asyncio

            from ai_engine.modules.activity.engine import get_activity_engine

            coro = get_activity_engine().log(
                user_id, app, f"action.{action}", target=action,
                detail=f"invocation d'action {app}:{action}", ts=_now())
            asyncio.get_event_loop().create_task(coro)
        except Exception:
            pass


def get_action_registry() -> ActionRegistry:
    return ActionRegistry()
