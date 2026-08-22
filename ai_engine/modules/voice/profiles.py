"""Profils de rendu des 10 voix Lunziko + enregistrement de voix personnalisées (V-5).

Chaque voix canonique (`voices.py`) reçoit un PROFIL DE RENDU (base de genre, débit, hauteur,
registre) appliqué au-dessus d'un modèle TTS de base. Les 4 voix ENFANTS sont approximées par
un débit plus vif + une hauteur relevée sur une base adulte (les voix enfants OSS étant rares) —
en attendant des modèles enfants/fine-tunés dédiés, enregistrables via `register_custom_voice`.

Les voix FINE-TUNÉES (ex. lingála/swahili) sont des modèles `.onnx` locaux associés à un
(voice_id, langue) : dès que le fichier existe, la voix devient utilisable — sans changer le code.
"""

from __future__ import annotations

from pathlib import Path

from ai_engine.core.registry import get_storage
from ai_engine.modules.voice.voices import CANONICAL_VOICES, get_voice

CUSTOM_NS = "voice_custom_models"

# Profils par registre : (length_scale [<1 = plus rapide], pitch_semitones [approx]).
_REGISTER_PROFILE = {
    "high": (0.95, 2.0),
    "mid": (1.0, 0.0),
    "low": (1.06, -2.0),
    "child": (0.9, 5.0),  # enfant : plus vif + plus aigu (approximation sur base adulte)
}


def base_gender(voice_id: str) -> str:
    v = get_voice(voice_id)
    if v is None:
        return "female"
    return "male" if v.gender.value in ("male", "boy") else "female"


def render_profile(voice_id: str) -> dict:
    """Profil de rendu d'une voix canonique : genre de base, débit, hauteur, registre."""
    v = get_voice(voice_id)
    if v is None:
        return {"voice_id": voice_id, "known": False}
    length_scale, pitch = _REGISTER_PROFILE.get(v.register.value, (1.0, 0.0))
    return {
        "voice_id": voice_id,
        "known": True,
        "label": v.label,
        "base_gender": base_gender(voice_id),
        "register": v.register.value,
        "is_child": v.register.value == "child",
        "length_scale": length_scale,
        "pitch_semitones": pitch,
        "intonation": v.intonation,
    }


def all_profiles() -> list[dict]:
    return [render_profile(v.id) for v in CANONICAL_VOICES]


class CustomVoiceStore:
    """Registre des modèles TTS personnalisés/fine-tunés (voice_id + langue -> .onnx local)."""

    def __init__(self) -> None:
        self._store = get_storage()

    @staticmethod
    def _key(voice_id: str, lang: str) -> str:
        return f"{voice_id}:{lang}"

    def register(self, voice_id: str, lang: str, model_path: str, *,
                 quality: str = "alpha") -> dict:
        if get_voice(voice_id) is None:
            raise ValueError(f"voix canonique inconnue : {voice_id}")
        p = Path(model_path)
        exists = p.exists()
        rec = {
            "voice_id": voice_id, "lang": lang, "model_path": str(p),
            "exists": exists, "quality": quality,
        }
        self._store.put(CUSTOM_NS, self._key(voice_id, lang), rec)
        return rec

    def resolve(self, voice_id: str, lang: str) -> str | None:
        """Chemin du modèle personnalisé si enregistré ET présent sur disque."""
        rec = self._store.get(CUSTOM_NS, self._key(voice_id, lang))
        if rec and Path(rec["model_path"]).exists():
            return rec["model_path"]
        return None

    def list(self, lang: str | None = None) -> list[dict]:
        rows = self._store.list(CUSTOM_NS)
        if lang:
            rows = [r for r in rows if r["lang"] == lang]
        # rafraîchit le flag d'existence à la lecture
        for r in rows:
            r["exists"] = Path(r["model_path"]).exists()
        return rows

    def unregister(self, voice_id: str, lang: str) -> bool:
        return self._store.delete(CUSTOM_NS, self._key(voice_id, lang))


def get_custom_voice_store() -> CustomVoiceStore:
    return CustomVoiceStore()
