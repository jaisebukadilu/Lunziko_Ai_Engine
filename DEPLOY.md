# Déploiement — Lunziko AI Engine

Image : **`jaisebukadilu/lunziko-ai-engine`**. Gateway FastAPI autonome sur le port **8770**.

## 1. Configuration
```bash
cp .env.example .env
# renseigner au minimum : une clé provider (ANTHROPIC_API_KEY…) OU un serveur local
# (AE_LOCAL_BASE_URL / provider lunziko), + AE_MEMORY_KEY pour la mémoire chiffrée.
python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())"  # -> AE_MEMORY_KEY
```

## 2. Docker Compose (recommandé)
```bash
docker compose up -d --build
curl http://localhost:8770/health
docker compose logs -f ai-engine
```
Le magasin local (SQLite / vecteurs / blobs) est persisté dans le volume `ai_engine_data` (`/data`).

## 3. Docker seul
```bash
docker build -t jaisebukadilu/lunziko-ai-engine:latest .
docker run -d --name lunziko-ai-engine -p 8770:8770 \
  --env-file .env -v ai_engine_data:/data \
  jaisebukadilu/lunziko-ai-engine:latest
```

## 4. Publier sur Docker Hub (compte `jaisebukadilu`)
```bash
docker login
docker build -t jaisebukadilu/lunziko-ai-engine:0.1.0 -t jaisebukadilu/lunziko-ai-engine:latest .
docker push jaisebukadilu/lunziko-ai-engine:0.1.0
docker push jaisebukadilu/lunziko-ai-engine:latest
```

## 5. Brancher le Graphics Engine (optionnel)
Le Graphics Engine est un dépôt séparé (serveur REST, port 8000). Lancer son conteneur, puis :
```env
AE_GRAPHICS_ENGINE_URL=http://graphics-engine:8000   # ou http://host.docker.internal:8000
AE_GRAPHICS_ENGINE_API_KEY=                            # si LUNZIKO_API_KEY côté moteur
```
Les Brains image/vision/video/3d/cad passent alors de `declared` à `active` et l'orchestrateur
LAIA leur délègue le travail. Voir `docker-compose.yml` (service `graphics-engine` commenté).

## 6. Extras d'image
Par défaut l'image installe `.[secure,neural]` (mémoire chiffrée + backend ML). Pour ajouter :
- **Postgres/pgvector** (couplage Platform) : ajouter `postgres` à la ligne `pip install` du `Dockerfile`.
- **LLM natif `lunziko`** : copier `../lunziko-llm` dans l'image + `pip install -e ./lunziko-llm`
  et définir `AE_LUNZIKO_LLM_CKPT` / `AE_LUNZIKO_LLM_TOKENIZER`.
- **Sandbox code (A-11)** : `AE_CODE_EXEC_ENABLED=true` **uniquement** dans un environnement isolé.

## Santé & endpoints
- `GET /health` — état des modules (24+ modules).
- `GET /docs` — documentation interactive OpenAPI.
