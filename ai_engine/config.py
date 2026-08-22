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
    ae_local_base_url: str = ""   # ex Ollama : http://localhost:11434/v1
    ae_local_model: str = ""      # modèle de chat local par défaut (ex Ollama : qwen2.5:7b / glm4)
    ae_code_model: str = ""  # modèle code local (Ollama) : qwen2.5-coder / deepseek-coder-v2 / codellama
    # Qwen 3.8-Max (Alibaba) — compatible OpenAI/Anthropic. Provider optionnel activé si clé présente.
    qwen_api_key: str = ""
    ae_qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    ae_qwen_model: str = "qwen3.8-max"

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

    # Voix — STT (Whisper via faster-whisper). Modèle : tiny|base|small|medium|large-v3.
    # Actif si le paquet `faster-whisper` est installé (extra `voice-stt`). Modèle téléchargé au 1er usage.
    ae_stt_model: str = "base"

    # Voix — TTS (Piper). Actif si `piper-tts` installé (extra `voice-tts`) ET une voix .onnx présente.
    # Télécharger une voix : python -m piper.download_voices fr_FR-siwis-medium --data-dir <dir>
    ae_tts_voices_dir: str = ""        # vide => <home>/voice/piper
    ae_tts_default_voice: str = ""     # vide => 1re voix .onnx trouvée

    # Code Intelligence — écriture contrôlée. Workspace autorisé optionnel (fige la sandbox
    # de chemin) : vide => le `root` fourni par la requête fait foi. Les écritures exigent
    # toujours confirm=True + produisent une sauvegarde réversible.
    ae_codeintel_workspace: str = ""

    # Voix — MT (traduction). Backend `auto` = MADLAD si `transformers`+`sentencepiece`
    # installés (extra `voice-mt`), sinon repli LLM via le Provider Manager.
    ae_mt_backend: str = "auto"        # auto | madlad | llm
    ae_mt_model: str = "google/madlad400-3b-mt"  # modèle MADLAD-400 (Apache-2.0)

    # Serveur MCP Hugging Face (outils modèles/datasets) — consommé par le client MCP.
    # Token HF (scope read) requis ; vide => intégration inactive. Bearer envoyé en en-tête.
    ae_hf_mcp_url: str = "https://huggingface.co/mcp"
    ae_hf_mcp_token: str = ""

    # Search Engine (web). Backend `duckduckgo` sans clé par défaut ; `google` (CSE) si clé+cx.
    ae_search_backend: str = "auto"   # auto | duckduckgo | google
    ae_google_api_key: str = ""
    ae_google_cse_id: str = ""

    # Graphics Engine (moteur de rendu, dépôt séparé) : API REST FastAPI (défaut 127.0.0.1:8000).
    # Vide => non branché (les Brains image/vision/video/3d restent « déclarés »).
    # ex : http://127.0.0.1:8000 . Auth optionnelle via X-API-Key (LUNZIKO_API_KEY côté moteur).
    ae_graphics_engine_url: str = ""
    ae_graphics_engine_api_key: str = ""

    # Génération multimédia (image/vidéo/audio/3D) — backends OPTIONNELS (GPU/modèles dédiés).
    # Absents => génération `deferred` (jamais simulée). Voir GENERATIVE_BRAINS.md.
    ae_comfyui_url: str = ""            # serveur ComfyUI (ex http://127.0.0.1:8188) : image/vidéo
    ae_fal_api_key: str = ""           # Fal.ai (hébergé) : image/vidéo
    ae_replicate_api_token: str = ""   # Replicate (hébergé) : image/vidéo/audio

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
