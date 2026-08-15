"""Configuration globale de l'AI Engine + résolution du magasin local.

Autonomie : par défaut tout est local (SQLite/FS), aucune dépendance à Platform.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Magasin local (« mémoire interne »)
    ai_engine_home: str = ""

    # Gateway
    ae_host: str = "0.0.0.0"
    ae_port: int = 8770
    ae_cors_origins: str = "http://localhost:3000"
    ae_api_keys: str = ""  # CSV ; vide => accès libre (dev)

    # Persistance enfichable
    ae_storage_backend: Literal["sqlite", "postgres"] = "sqlite"
    ae_vector_backend: Literal["local", "pgvector"] = "local"
    ae_blob_backend: Literal["fs", "s3"] = "fs"
    ae_postgres_dsn: str = ""

    # Provider Manager (clés propres à l'AI Engine)
    ae_default_provider: str = "claude"
    ae_provider_fallback: str = "claude,chatgpt,gemini,mistral,deepseek"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    mistral_api_key: str = ""
    deepseek_api_key: str = ""
    ae_local_base_url: str = ""
    ae_code_model: str = ""  # modèle code local (Ollama) : qwen2.5-coder / deepseek-coder-v2 / codellama

    # Embeddings (RAG). "auto" => 1er cloud dispo, sinon repli local "hash" (offline).
    ae_embed_provider: str = "auto"  # auto | openai | mistral | gemini | local | hash
    ae_embed_model: str = ""         # override du modèle d'embedding
    ae_embed_dim: int = 256          # dimension du repli local "hash"

    # Mémoire chiffrée : clé AES-256-GCM en base64 (32 octets). Vide => mode dev en clair.
    ae_memory_key: str = ""

    # Écosystème : registre maître Lunziko (source de connaissance des applications).
    # Vide => découverte automatique (racine du dossier Lunziko). Sync au démarrage par défaut.
    ae_registry_path: str = ""
    ae_registry_autosync: bool = True

    # LLM natif Lunziko (paquet lunziko-llm) : checkpoint + tokenizer entraînés localement.
    # Vides => provider `lunziko` indisponible. Requiert `pip install -e ../lunziko-llm`.
    ae_lunziko_llm_ckpt: str = ""
    ae_lunziko_llm_tokenizer: str = ""

    # Code Execution Engine (A-11). Niveau 0 (safe eval) toujours ON ; Niveau 1 (sandbox
    # subprocess) DÉSACTIVÉ par défaut — n'activer que dans un environnement OS isolé.
    ae_code_exec_enabled: bool = False
    ae_code_exec_timeout: int = 10          # secondes (wall-clock) du sous-processus
    ae_code_exec_max_output: int = 20000    # caractères max capturés

    # Graphics Engine (moteur de rendu, dépôt séparé) : URL JSON-RPC. Vide => non branché
    # (les Brains image/vision/video/3d restent « déclarés »).
    ae_graphics_engine_url: str = ""

    # --- Dérivés ---------------------------------------------------------
    @property
    def home(self) -> Path:
        return Path(self.ai_engine_home).expanduser() if self.ai_engine_home else Path.home() / ".lunziko" / "ai-engine"

    @property
    def db_path(self) -> Path:
        return self.home / "store.db"

    @property
    def blob_dir(self) -> Path:
        return self.home / "blobs"

    @property
    def voice_home(self) -> Path:
        return self.home / "voice"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.ae_cors_origins.split(",") if o.strip()]

    @property
    def api_keys(self) -> set[str]:
        return {k.strip() for k in self.ae_api_keys.split(",") if k.strip()}

    @property
    def fallback_order(self) -> list[str]:
        return [p.strip() for p in self.ae_provider_fallback.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
