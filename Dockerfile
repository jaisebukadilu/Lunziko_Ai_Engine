# Lunziko AI Engine — image de production (gateway FastAPI, autonome).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AE_HOST=0.0.0.0 \
    AE_PORT=8770 \
    AI_ENGINE_HOME=/data

WORKDIR /app

# Dépendances d'abord (cache Docker). Cœur + extras `secure` (AES-GCM) et `neural` (numpy/sklearn).
COPY pyproject.toml README.md ./
COPY ai_engine ./ai_engine
RUN pip install --no-cache-dir ".[secure,neural]"

# Persistance du magasin local (store.db / vectors / blobs) dans un volume.
VOLUME ["/data"]
EXPOSE 8770

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8770/health').status==200 else 1)"

CMD ["uvicorn", "ai_engine.gateway.main:app", "--host", "0.0.0.0", "--port", "8770"]
