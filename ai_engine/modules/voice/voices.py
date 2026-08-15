"""Les 10 voix Lunziko canoniques — identités stables, découplées de la langue."""

from __future__ import annotations

from ai_engine.modules.voice.schemas import Voice, VoiceGender, VoiceRegister

CANONICAL_VOICES: list[Voice] = [
    Voice(id="lz-m1-bright", label="Homme — aigu",   gender=VoiceGender.male,  register=VoiceRegister.high, intonation="Clair, jeune adulte"),
    Voice(id="lz-m2-warm",   label="Homme — médium", gender=VoiceGender.male,  register=VoiceRegister.mid,  intonation="Chaleureux, neutre"),
    Voice(id="lz-m3-deep",   label="Homme — grave",  gender=VoiceGender.male,  register=VoiceRegister.low,  intonation="Profond, posé"),
    Voice(id="lz-f1-bright", label="Femme — aigu",   gender=VoiceGender.female, register=VoiceRegister.high, intonation="Vif, énergique"),
    Voice(id="lz-f2-warm",   label="Femme — médium", gender=VoiceGender.female, register=VoiceRegister.mid,  intonation="Doux, narratif"),
    Voice(id="lz-f3-deep",   label="Femme — grave",  gender=VoiceGender.female, register=VoiceRegister.low,  intonation="Mature, assuré"),
    Voice(id="lz-b1-playful", label="Garçon — espiègle", gender=VoiceGender.boy,  register=VoiceRegister.child, intonation="Espiègle, rapide"),
    Voice(id="lz-b2-calm",    label="Garçon — calme",    gender=VoiceGender.boy,  register=VoiceRegister.child, intonation="Calme, curieux"),
    Voice(id="lz-g1-cheerful", label="Fille — joyeuse",  gender=VoiceGender.girl, register=VoiceRegister.child, intonation="Joyeux, chantant"),
    Voice(id="lz-g2-shy",      label="Fille — timide",   gender=VoiceGender.girl, register=VoiceRegister.child, intonation="Timide, doux"),
]

VOICE_IDS: set[str] = {v.id for v in CANONICAL_VOICES}


def get_voice(voice_id: str) -> Voice | None:
    return next((v for v in CANONICAL_VOICES if v.id == voice_id), None)
