"""Schémas Pydantic du module voix — contrats stables (indépendants des modèles)."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# 18 langues cibles (ISO 639). Voir VOICE_ARCHITECTURE §1.2
LangCode = Literal[
    "fr", "sw", "ln", "zh", "en", "es", "de", "hi", "ar",
    "bn", "pt", "ru", "ur", "id", "it", "ja", "he", "el",
]
SourceLang = Literal[
    "auto", "fr", "sw", "ln", "zh", "en", "es", "de", "hi", "ar",
    "bn", "pt", "ru", "ur", "id", "it", "ja", "he", "el",
]

AudioFormat = Literal["mp3", "wav", "ogg", "pcm16"]


class VoiceGender(str, Enum):
    male = "male"
    female = "female"
    boy = "boy"
    girl = "girl"


class VoiceRegister(str, Enum):
    high = "high"
    mid = "mid"
    low = "low"
    child = "child"


class Voice(BaseModel):
    id: str = Field(examples=["lz-f2-warm"])
    label: str
    gender: VoiceGender
    register: VoiceRegister
    intonation: str


class PackQuality(BaseModel):
    stt: Literal["planned", "alpha", "beta", "stable"]
    tts: Literal["planned", "alpha", "beta", "stable"]
    mt: Literal["planned", "alpha", "beta", "stable"]


class LanguagePack(BaseModel):
    id: str = Field(examples=["ln"])
    name: str
    installed: bool = False
    version: str | None = None
    size_mb: int
    stt_model: str
    tts_model: str
    mt_engine: str
    license: str
    quality: PackQuality


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    voice: str = Field(examples=["lz-m2-warm"])
    lang: LangCode
    format: AudioFormat = "mp3"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=16000)
    source: SourceLang = "auto"
    target: LangCode


class STTResponse(BaseModel):
    text: str
    lang: str
    duration_s: float | None = None
