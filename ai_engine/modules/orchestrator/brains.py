"""Brain Registry — catalogue des cerveaux spécialisés (manifestes) + résolution.

Un Brain = intelligence spécialisée servie par des Engines existants. Catalogue amorcé
(text/reasoning/code/data/research/document/ui_ux/language = actifs ; vision/image/video/audio/
music/voice/3d/cad = déclarés). Extensible via register(). Résolution par capacité/mots-clés.
"""

from __future__ import annotations

from ai_engine.core.registry import get_storage

NS = "brain_registry"


def _brain(bid, name, btype, capabilities, inputs, outputs, engines, tools, status="active"):
    return {"id": bid, "name": name, "type": btype, "capabilities": capabilities,
            "inputs": inputs, "outputs": outputs, "engines": engines, "tools": tools,
            "status": status}


# Catalogue officiel amorcé (manifestes).
SEED_BRAINS = [
    _brain("text", "Lunziko Text Brain", "language",
           ["conversation", "redaction", "resume", "traduction", "reformulation", "extraction"],
           ["text"], ["text"], ["inference", "rag", "memory", "context"], ["tools"]),
    _brain("reasoning", "Lunziko Reasoning Brain", "reasoning",
           ["raisonnement", "planification", "decomposition", "analyse", "decision", "verification"],
           ["text"], ["plan", "analysis"], ["inference", "knowledge", "memory", "rag", "workflow"], ["tools"]),
    _brain("code", "Lunziko Code Brain", "reasoning-specialist",
           ["code_generation", "code_review", "debugging", "testing", "refactoring", "explain"],
           ["text", "repository", "files"], ["source_code", "patches", "tests", "documentation"],
           ["inference", "code_execution", "validation", "memory"], ["filesystem", "git", "terminal"]),
    _brain("data", "Lunziko Data Brain", "analytics",
           ["data_understanding", "cleaning", "transformation", "statistics", "anomaly", "forecast", "classification"],
           ["data", "text"], ["dataset", "measures", "insights"],
           ["data", "inference", "rag"], ["data", "database"]),
    _brain("research", "Lunziko Research Brain", "reasoning-specialist",
           ["search", "retrieval", "compare", "verify", "synthesize", "cite"],
           ["text"], ["report", "citations"], ["rag", "search", "knowledge", "inference"], ["web", "tools"]),
    _brain("document", "Lunziko Document Brain", "document",
           ["ocr", "extraction", "layout", "resume", "doc_generation"],
           ["document", "pdf", "text"], ["document"], ["inference", "rag", "context"], ["documents"]),
    _brain("ui_ux", "Lunziko UI/UX Brain", "generation",
           ["ui", "ux", "design_system", "wireframe", "components", "responsive", "accessibility"],
           ["text", "spec"], ["ui_code", "design"], ["inference", "ui_generation", "validation"], ["app", "graphics"]),
    _brain("language", "Lunziko Language Brain", "language",
           ["comprehension", "translation", "grammar", "vocabulary", "pronunciation", "exercises"],
           ["text", "audio"], ["text", "feedback"], ["inference", "rag", "voice"], ["tools"]),
    # Déclarés (nécessitent des modèles/engines dédiés — activés plus tard).
    _brain("vision", "Lunziko Vision Brain", "perception",
           ["image_understanding", "ocr", "document_analysis", "screenshot_analysis"],
           ["image"], ["analysis"], ["vision", "inference"], ["files"], status="planned"),
    _brain("image", "Lunziko Image Brain", "generation",
           ["generation", "inpainting", "upscale", "compositing", "textures"],
           ["text", "image"], ["image"], ["image_generation", "graphics"], ["files"], status="planned"),
    _brain("video", "Lunziko Video Brain", "generation",
           ["video_generation", "editing", "storyboard", "subtitles"],
           ["text", "video"], ["video"], ["video", "vision", "audio", "graphics"], ["files"], status="planned"),
    _brain("audio", "Lunziko Audio Brain", "generation",
           ["audio_generation", "sound_design", "cleanup", "mastering"],
           ["audio", "text"], ["audio"], ["audio", "inference"], ["files"], status="planned"),
    _brain("music", "Lunziko Music Brain", "generation",
           ["composition", "harmony", "melody", "arrangement", "generation"],
           ["text", "audio"], ["music"], ["audio", "inference"], ["files"], status="planned"),
    _brain("voice", "Lunziko Voice Brain", "conversation",
           ["stt", "speech_understanding", "tts", "voice_conversation"],
           ["audio", "text"], ["audio", "text"], ["voice", "inference"], ["tools"], status="planned"),
    _brain("3d", "Lunziko 3D Brain", "generation",
           ["text_to_3d", "image_to_3d", "geometry", "scene_understanding", "materials"],
           ["text", "image"], ["mesh", "scene"], ["3d", "graphics"], ["files"], status="planned"),
    _brain("cad", "Lunziko CAD Brain", "generation-specialist",
           ["geometry", "constraints", "mechanical", "architecture", "bim", "parametric"],
           ["text", "spec"], ["cad_model"], ["3d", "graphics", "validation"], ["app"], status="planned"),
]


class BrainRegistry:
    def __init__(self) -> None:
        self._store = get_storage()
        self._seed()

    def _seed(self) -> None:
        if not self._store.list(NS):
            for b in SEED_BRAINS:
                self._store.put(NS, b["id"], b)

    @staticmethod
    def _effective(rec: dict) -> dict:
        """Statut effectif : un Brain 'declared' dépendant du Graphics Engine passe 'active'
        quand le moteur est branché (AE_GRAPHICS_ENGINE_URL)."""
        if rec.get("status") == "active":
            return rec
        try:
            from ai_engine.modules.graphics.client import graphics_brain_availability
            if graphics_brain_availability().get(rec["id"]) == "active":
                return {**rec, "status": "active", "backend": "graphics-engine"}
        except Exception:
            pass
        return rec

    def list(self, status: str | None = None) -> list[dict]:
        rows = [self._effective(r) for r in self._store.list(NS)]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return sorted(rows, key=lambda r: (r.get("status") != "active", r.get("id", "")))

    def get(self, bid: str) -> dict | None:
        rec = self._store.get(NS, bid)
        return self._effective(rec) if rec else None

    def register(self, manifest: dict) -> dict:
        bid = manifest["id"]
        self._store.put(NS, bid, {**manifest, "id": bid})
        return {"id": bid}

    def capabilities(self, bid: str) -> list[str]:
        rec = self.get(bid)
        return rec.get("capabilities", []) if rec else []

    def resolve(self, query: str, *, only_active: bool = False, k: int = 3) -> list[dict]:
        """Résout les Brains pertinents pour une requête (score sur capacités + nom)."""
        low = query.lower()
        scored = []
        for b in self.list():
            if only_active and b.get("status") != "active":
                continue
            hay = " ".join([b["id"], b["name"], *b.get("capabilities", [])]).lower()
            score = sum(1 for tok in set(low.replace("/", " ").split()) if len(tok) >= 3 and tok in hay)
            # bonus si une capacité apparaît dans la requête
            score += sum(1 for c in b.get("capabilities", []) if c.replace("_", " ") in low)
            if score > 0:
                scored.append((score, b))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [b for _, b in scored[:k]]


_REG: BrainRegistry | None = None


def get_brain_registry() -> BrainRegistry:
    global _REG
    if _REG is None:
        _REG = BrainRegistry()
    return _REG
