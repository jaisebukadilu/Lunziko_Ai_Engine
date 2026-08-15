"""AgentEngine — sélectionne une capacité, assemble le contexte (mémoire + knowledge),
répond via le Provider Manager, et peut mémoriser l'échange.

Sélection par mots-clés (fiable, extensible). Le tool-calling natif cross-provider est
une amélioration ultérieure (A-4b) — nécessite d'exposer les schémas d'outils par provider.
"""

from __future__ import annotations

from ai_engine.modules.activity.engine import get_activity_engine
from ai_engine.modules.ecosystem.engine import get_ecosystem_engine
from ai_engine.modules.knowledge.engine import get_knowledge_engine
from ai_engine.modules.memory.engine import get_memory_engine
from ai_engine.modules.provider.base import ChatMessage
from ai_engine.modules.provider.manager import get_provider_manager

ECOSYSTEM_THRESHOLD = 0.25  # score mini pour injecter une app Lunziko dans le contexte

CAPABILITIES: dict[str, list[str]] = {
    "document": ["document", "texte", "rapport", "résume", "résumé", "corrige", "rédige"],
    "research": ["cherche", "trouve", "recherche", "information", "source"],
    "data": ["données", "statistiques", "analyse", "chiffres", "calcul"],
    "crm": ["client", "crm", "contact", "vente", "prospect", "membre"],
    "creative": ["crée", "génère", "imagine", "design", "idée", "brainstorm"],
}

_PERSONA = {
    "document": "Tu es un assistant bureautique : résumé, correction, rédaction claire.",
    "research": "Tu es un assistant de recherche : synthèse factuelle et sourcée.",
    "data": "Tu es un analyste de données : raisonnement chiffré, prudent et explicite.",
    "crm": "Tu es un assistant relation/CRM : orienté personnes et suivi.",
    "creative": "Tu es un assistant créatif : idées originales et concrètes.",
    "general": "Tu es un assistant IA utile, honnête et concis.",
}


def select_capability(query: str) -> str:
    """Routage par mots-clés (repli déterministe, toujours disponible).

    Utilise la taxonomie partagée (racines normalisées sans accent, préfixes tolérant les
    conjugaisons) ; repli sur les mots-clés locaux si le module neural est indisponible.
    """
    try:
        from ai_engine.modules.neural.intent_taxonomy import keyword_best

        return keyword_best(query)[0]
    except Exception:
        low = query.lower()
        best, score = "general", 0
        for cap, kws in CAPABILITIES.items():
            s = sum(1 for k in kws if k in low)
            if s > score:
                best, score = cap, s
        return best


async def select_capability_neural(query: str) -> tuple[str, float, str]:
    """Routage neuronal (embeddings → classifieur) ; repli mots-clés si indisponible.

    Retourne (capacité, confiance, backend). Améliore la « réflexion » sur les formulations
    sans mot-clé littéral.
    """
    try:
        from ai_engine.modules.neural.router_engine import get_neural_router

        r = await get_neural_router().route(query)
        return r["capability"], r["confidence"], r["backend"]
    except Exception:
        return select_capability(query), 0.0, "keyword"


class AgentEngine:
    async def run(
        self,
        query: str,
        *,
        agent: str = "auto",
        user_id: str | None = None,
        org: str | None = None,
        provider: str | None = None,
        save_memory: bool = False,
        use_ecosystem: bool = True,
        use_activity: bool = True,
        use_neural_router: bool = True,
        max_tokens: int = 1024,
    ) -> dict:
        routing = {"method": "explicit", "confidence": 1.0}
        if agent != "auto":
            cap = agent
        elif use_neural_router:
            cap, conf, backend = await select_capability_neural(query)
            routing = {"method": f"neural:{backend}", "confidence": conf}
        else:
            cap = select_capability(query)
            routing = {"method": "keyword", "confidence": 1.0}
        context: list[str] = []
        used = {"memory": 0, "knowledge": 0, "ecosystem": 0, "activity": 0}
        if user_id:
            mem = await get_memory_engine().recall(user_id, query, 3)
            used["memory"] = len(mem)
            context += [f"[mémoire] {m['key']}: {m['value']}" for m in mem]
        if user_id and use_activity:
            # Contexte comportemental : dernières actions de l'utilisateur dans la suite.
            recent = get_activity_engine().timeline(user_id, limit=5)
            used["activity"] = len(recent)
            context += [
                f"[activité] {a['app']}/{a['action']}"
                + (f" → {a['target']}" if a["target"] else "")
                + (" [erreur]" if a["status"] == "error" else "")
                for a in recent
            ]
        if org:
            kn = await get_knowledge_engine().search(org, query, 3)
            used["knowledge"] = len(kn)
            context += [f"[connaissance] {k['title']}: {k.get('content', '')}" for k in kn]
        if use_ecosystem:
            # Connaissance des applications Lunziko (registre maître) pour accompagner l'utilisateur.
            try:
                apps = await get_ecosystem_engine().search(query, 2)
            except Exception:
                apps = []
            relevant = [a for a in apps if a.get("score", 0) >= ECOSYSTEM_THRESHOLD]
            used["ecosystem"] = len(relevant)
            context += [
                f"[app Lunziko] {a['name']} — {a.get('category', '')} | "
                f"fonctions : {'; '.join(a.get('functions', [])[:6])}"
                for a in relevant
            ]

        system = _PERSONA.get(cap, _PERSONA["general"])
        if context:
            system += "\n\nCONTEXTE:\n" + "\n".join(context)

        answer = await get_provider_manager().chat(
            [ChatMessage(role="user", content=query)],
            provider=provider,
            system=system,
            max_tokens=max_tokens,
        )
        if save_memory and user_id:
            await get_memory_engine().save(user_id, "general", query[:60], answer.content[:500])
        return {"capability": cap, "routing": routing, "answer": answer, "used": used}


def get_agent_engine() -> AgentEngine:
    return AgentEngine()
