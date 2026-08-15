"""AutomationEngine — définition et exécution de flux de nœuds (outils chaînés).

Nœud = {id, tool, args}. Les valeurs d'`args` peuvent être littérales ou des références
`$input[.champ]` / `$<node_id>[.champ]` résolues au fil de l'exécution. Chaque nœud appelle
un outil du ToolRegistry ; sa sortie (JSON) est disponible pour les nœuds suivants.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from ai_engine.core.registry import get_storage
from ai_engine.modules.tools.registry import get_tool_registry

NS_FLOW = "automation_flows"
NS_RUN = "automation_runs"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve(value, ctx: dict):
    """Résout une référence `$path` dans le contexte, sinon renvoie la valeur littérale."""
    if not isinstance(value, str) or not value.startswith("$"):
        return value
    parts = value[1:].split(".")
    cur = ctx.get(parts[0])
    for p in parts[1:]:
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur


def _resolve_args(args: dict, ctx: dict) -> dict:
    out = {}
    for k, v in (args or {}).items():
        if isinstance(v, list):
            out[k] = [_resolve(x, ctx) for x in v]
        else:
            out[k] = _resolve(v, ctx)
    return out


class AutomationEngine:
    def __init__(self) -> None:
        self._store = get_storage()

    # --- Définition des flux ---
    def save_flow(self, name: str, nodes: list[dict], description: str = "") -> dict:
        reg = get_tool_registry()
        for n in nodes:
            if n.get("tool") not in reg.names():
                raise ValueError(f"nœud « {n.get('id')} » : outil inconnu « {n.get('tool')} »")
        rec = {"id": name, "name": name, "description": description, "nodes": nodes,
               "updated_at": _now()}
        self._store.put(NS_FLOW, name, rec)
        return {"flow": name, "nodes": len(nodes)}

    def get_flow(self, name: str) -> dict | None:
        return self._store.get(NS_FLOW, name)

    def list_flows(self) -> list[dict]:
        return [{"name": f["name"], "nodes": len(f.get("nodes", [])),
                 "description": f.get("description", "")} for f in self._store.list(NS_FLOW)]

    def delete_flow(self, name: str) -> bool:
        return self._store.delete(NS_FLOW, name)

    # --- Exécution ---
    async def run_flow(self, name: str, flow_input: dict | None = None) -> dict:
        flow = self.get_flow(name)
        if flow is None:
            raise KeyError(f"flux inconnu: {name}")
        reg = get_tool_registry()
        ctx: dict = {"input": flow_input or {}}
        steps: list[dict] = []
        status = "ok"
        for node in flow["nodes"]:
            nid, tool = node["id"], node["tool"]
            args = _resolve_args(node.get("args", {}), ctx)
            raw = await reg.execute(tool, args)
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                parsed = {"text": raw}
            ctx[nid] = parsed
            is_err = isinstance(parsed, dict) and "error" in parsed
            steps.append({"node": nid, "tool": tool, "args": args,
                          "output": parsed, "error": bool(is_err)})
            if is_err:
                status = "error"
                break
        run = {"id": uuid.uuid4().hex, "flow": name, "status": status,
               "steps": steps, "output": ctx.get(steps[-1]["node"]) if steps else None,
               "ran_at": _now()}
        self._store.put(NS_RUN, run["id"], run)
        return run

    def list_runs(self, flow: str | None = None, limit: int = 20) -> list[dict]:
        rows = self._store.list(NS_RUN)
        if flow:
            rows = [r for r in rows if r.get("flow") == flow]
        rows.sort(key=lambda r: r.get("ran_at", ""), reverse=True)
        return [{"id": r["id"], "flow": r["flow"], "status": r["status"],
                 "steps": len(r.get("steps", [])), "ran_at": r["ran_at"]} for r in rows[:limit]]


def get_automation_engine() -> AutomationEngine:
    return AutomationEngine()
