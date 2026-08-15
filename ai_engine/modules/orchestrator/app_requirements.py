"""App Requirements — chaque app Lunziko déclare ses besoins en Brains/Engines/services.

Lie LAIA au registre écosystème : l'orchestrateur sait quels cerveaux/moteurs une app requiert
pour une tâche. Catalogue amorcé d'après les besoins connus (VidiaPub, CAD, BI, One, DociaPub,
Yekoli). Extensible via set(). L'app est vérifiée contre le registre écosystème (flag known).
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.core.registry import get_storage

NS = "app_requirements"

# Besoins par défaut (d'après le brief LAIA §27).
SEED = {
    "vidiapub": {"brains": ["image", "video", "audio", "vision"],
                 "engines": ["graphics", "image", "video", "audio", "inference"],
                 "services": ["ai", "platform", "design-system"]},
    "cad": {"brains": ["cad", "3d", "vision", "reasoning"],
            "engines": ["3d", "graphics", "validation"],
            "services": ["ai", "graphics-engine", "platform"]},
    "bi": {"brains": ["data", "reasoning", "research"],
           "engines": ["rag", "data", "inference"],
           "services": ["ai", "platform"]},
    "one": {"brains": ["data", "reasoning", "document"],
            "engines": ["data", "inference", "workflow"],
            "services": ["ai", "platform"]},
    "dociapub": {"brains": ["document", "text", "ui_ux"],
                 "engines": ["inference", "rag", "context"],
                 "services": ["ai", "platform", "graphics-engine"]},
    "yekoli": {"brains": ["language", "text", "voice"],
               "engines": ["inference", "rag", "voice"],
               "services": ["ai", "platform"]},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AppRequirements:
    def __init__(self) -> None:
        self._store = get_storage()
        self._seed()

    def _seed(self) -> None:
        if not self._store.list(NS):
            for app, req in SEED.items():
                self._store.put(NS, app, {"id": app, **req, "updated_at": _now()})

    def get(self, app: str) -> dict:
        rec = self._store.get(NS, app)
        if rec:
            return rec
        return {"id": app, "brains": [], "engines": [], "services": []}

    def set(self, app: str, *, brains=None, engines=None, services=None) -> dict:
        rec = self.get(app)
        rec["id"] = app
        if brains is not None:
            rec["brains"] = brains
        if engines is not None:
            rec["engines"] = engines
        if services is not None:
            rec["services"] = services
        rec["updated_at"] = _now()
        self._store.put(NS, app, rec)
        return rec

    def list(self) -> list[dict]:
        return sorted(self._store.list(NS), key=lambda r: r.get("id", ""))

    def resolve(self, app: str) -> dict:
        """Besoins de l'app + manifestes des Brains requis + vérif écosystème."""
        req = self.get(app)
        from ai_engine.modules.orchestrator.brains import get_brain_registry
        breg = get_brain_registry()
        brains = [breg.get(b) for b in req.get("brains", [])]
        brains = [b for b in brains if b]
        known = False
        try:
            from ai_engine.modules.ecosystem.engine import get_ecosystem_engine
            known = get_ecosystem_engine().get_app(app) is not None
        except Exception:
            known = False
        return {"app": app, "app_known": known,
                "required_brains": brains,
                "required_engines": req.get("engines", []),
                "required_services": req.get("services", [])}


def get_app_requirements() -> AppRequirements:
    return AppRequirements()
