"""Moteur de traduction (V-3) — MT any-to-any sur les 18 langues.

Deux backends, sélectionnés selon la config `AE_MT_BACKEND` :
  - `madlad` : MADLAD-400 (Apache-2.0) on-device via `transformers`/`sentencepiece`
              (chargement paresseux, télécharge le modèle au 1er usage) ;
  - `llm`    : repli via le **Provider Manager propre à l'AI Engine** (Claude/GPT/…),
              excellent sur les langues majeures, sert de secours qualité.
  - `auto`   : MADLAD si le paquet est présent, sinon LLM.

100 % interne à l'AI Engine — aucune dépendance à Platform.
"""

from __future__ import annotations

import importlib.util
from typing import Awaitable, Callable

from ai_engine.config import get_settings
from ai_engine.modules.provider.base import ChatMessage

# 18 langues cibles (ISO 639) → nom courant (pour les prompts LLM et l'UI).
LANG_NAMES: dict[str, str] = {
    "fr": "français", "sw": "swahili", "ln": "lingála", "zh": "chinois (mandarin)",
    "en": "anglais", "es": "espagnol", "de": "allemand", "hi": "hindi",
    "ar": "arabe", "bn": "bengali", "pt": "portugais", "ru": "russe",
    "ur": "ourdou", "id": "indonésien", "it": "italien", "ja": "japonais",
    "he": "hébreu", "el": "grec",
}

# Jeton cible MADLAD-400 : le modèle attend un préfixe "<2xx> texte".
_MADLAD_TOKEN = {code: f"<2{code}>" for code in LANG_NAMES}

# Cache du modèle MADLAD chargé (lazy, coûteux).
_MADLAD: dict[str, object] = {}

ChatFn = Callable[..., Awaitable[object]]


def madlad_available() -> bool:
    """Vrai si la pile MADLAD on-device est installable (transformers + sentencepiece)."""
    return (
        importlib.util.find_spec("transformers") is not None
        and importlib.util.find_spec("sentencepiece") is not None
    )


def resolve_backend() -> str:
    """Backend effectif : respecte AE_MT_BACKEND, `auto` = madlad si dispo sinon llm."""
    pref = (get_settings().ae_mt_backend or "auto").lower()
    if pref == "madlad":
        return "madlad"
    if pref == "llm":
        return "llm"
    return "madlad" if madlad_available() else "llm"


def is_supported(code: str) -> bool:
    return code in LANG_NAMES


class TranslationEngine:
    """Traduit un texte d'une langue source vers une langue cible."""

    def __init__(self, chat_fn: ChatFn | None = None) -> None:
        # chat_fn injectable pour les tests (par défaut = Provider Manager de l'AI Engine).
        self._chat_fn = chat_fn

    # --- Backend MADLAD-400 (on-device) ---------------------------------
    def _load_madlad(self):
        model_id = get_settings().ae_mt_model or "google/madlad400-3b-mt"
        if model_id not in _MADLAD:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # lazy

            tok = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
            _MADLAD[model_id] = (tok, model)
        return _MADLAD[model_id]

    def _translate_madlad(self, text: str, target: str) -> str:
        tok, model = self._load_madlad()
        prompt = f"{_MADLAD_TOKEN.get(target, '<2' + target + '>')} {text}"
        inputs = tok(prompt, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=512)
        return tok.decode(out[0], skip_special_tokens=True).strip()

    # --- Backend LLM (fallback qualité, via Provider Manager) ------------
    async def _translate_llm(self, text: str, source: str, target: str) -> str:
        tgt = LANG_NAMES.get(target, target)
        if source in ("auto", "", None):
            system = (
                f"Tu es un traducteur professionnel. Détecte la langue source et traduis "
                f"fidèlement le texte en {tgt}. Réponds UNIQUEMENT avec la traduction, "
                f"sans explication, sans guillemets, sans préfixe."
            )
        else:
            src = LANG_NAMES.get(source, source)
            system = (
                f"Tu es un traducteur professionnel. Traduis fidèlement le texte du {src} "
                f"vers le {tgt}. Réponds UNIQUEMENT avec la traduction, sans explication, "
                f"sans guillemets, sans préfixe."
            )
        chat = self._chat_fn
        if chat is None:
            from ai_engine.modules.provider.manager import get_provider_manager
            chat = get_provider_manager().chat
        res = await chat([ChatMessage(role="user", content=text)], system=system)
        return (getattr(res, "content", None) or str(res)).strip()

    # --- API publique ----------------------------------------------------
    async def translate(self, text: str, source: str = "auto", target: str = "en") -> dict:
        if not is_supported(target):
            raise ValueError(f"langue cible non supportée : {target}")
        if source not in ("auto",) and not is_supported(source):
            raise ValueError(f"langue source non supportée : {source}")
        if source == target:
            raise ValueError("source et target identiques")

        backend = resolve_backend()
        if backend == "madlad":
            if not madlad_available():
                # config force madlad mais paquet absent → secours LLM explicite.
                translated = await self._translate_llm(text, source, target)
                used = "llm"
                model = "provider-manager"
            else:
                translated = self._translate_madlad(text, target)
                used = "madlad"
                model = get_settings().ae_mt_model or "google/madlad400-3b-mt"
        else:
            translated = await self._translate_llm(text, source, target)
            used = "llm"
            model = "provider-manager"

        return {
            "text": translated,
            "source": source,
            "target": target,
            "backend": used,
            "model": model,
        }


def get_translation_engine() -> TranslationEngine:
    return TranslationEngine()
