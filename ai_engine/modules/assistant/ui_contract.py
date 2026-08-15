"""Contrat UI — descripteur stable qu'une future interface visuelle peut consommer.

Décrit, pour une app donnée : titre, zone de compétence (→ actions rapides), agents actifs,
prompts suggérés et points de connexion (REST + WebSocket). Le frontend se construit contre CE
contrat, sans coupler à l'implémentation interne.
"""

from __future__ import annotations

from ai_engine.modules.assistant import MAX_AGENTS_PER_APP
from ai_engine.modules.assistant.engine import get_app_assistant


def ui_contract(app: str) -> dict:
    a = get_app_assistant()
    sc = a.scope(app)
    agents = a.list_agents(app)
    functions = sc.get("competence", [])
    # Actions rapides = 6 premières fonctions de la zone de compétence.
    quick_actions = [{"id": f"act-{i}", "label": f[:60]} for i, f in enumerate(functions[:6])]
    suggested = [
        f"Que peux-tu faire dans {sc.get('name', app)} ?",
        "Aide-moi à corriger une erreur.",
        "Résume ce que j'ai fait récemment ici.",
    ]
    return {
        "app": sc["app"],
        "title": f"Assistant {sc.get('name', app)}",
        "scope_known": sc["known"],
        "competence": functions,
        "quick_actions": quick_actions,
        "suggested_prompts": suggested,
        "agents": {"max": MAX_AGENTS_PER_APP, "active": len(agents),
                   "list": [{"id": g["id"], "role": g["role"]} for g in agents]},
        "connection": {
            "rest": {
                "ask": f"POST /v1/assistant/{sc['app']}/ask",
                "team": f"POST /v1/assistant/{sc['app']}/team",
                "scope": f"GET /v1/assistant/{sc['app']}/scope",
                "sessions": "POST /v1/assistant/sessions",
            },
            "websocket": f"/v1/assistant/{sc['app']}/ws",
            "protocol": {
                "server_events": ["ready", "answer", "error"],
                "client_events": ["message"],
                "message_shape": {"type": "message", "content": "…", "user_id": "optional",
                                  "session_id": "optional"},
            },
        },
        "branding_hint": {"design_system": "Lunziko Design System (charte de l'app)"},
    }
