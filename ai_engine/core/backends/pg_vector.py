"""VectorPort — adaptateur pgvector (couplage optionnel à Platform).

Activé par `AE_VECTOR_BACKEND=pgvector` + `AE_POSTGRES_DSN`. Requiert l'extra `postgres`
(psycopg + extension `vector`). Colonne `vector` sans dimension fixe : tolère la dimension
de l'embedder actif (recherche exacte via l'opérateur cosinus `<=>`).
"""

from __future__ import annotations

import json
import threading

import psycopg


def _to_pgvector(vec: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in vec) + "]"


class PgVector:
    def __init__(self, dsn: str) -> None:
        self._lock = threading.Lock()
        self._conn = psycopg.connect(dsn, autocommit=True)
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                "CREATE TABLE IF NOT EXISTS ae_vectors ("
                " ns TEXT NOT NULL, id TEXT NOT NULL,"
                " embedding vector NOT NULL, meta JSONB NOT NULL,"
                " PRIMARY KEY (ns, id))"
            )

    def upsert(self, ns: str, id: str, vector: list[float], meta: dict) -> None:
        with self._lock, self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ae_vectors(ns,id,embedding,meta) VALUES(%s,%s,%s::vector,%s) "
                "ON CONFLICT (ns,id) DO UPDATE SET embedding=EXCLUDED.embedding, meta=EXCLUDED.meta",
                (ns, id, _to_pgvector(vector), json.dumps(meta, ensure_ascii=False)),
            )

    def search(self, ns: str, vector: list[float], k: int = 5) -> list[dict]:
        qv = _to_pgvector(vector)
        with self._lock, self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, meta, 1 - (embedding <=> %s::vector) AS score "
                "FROM ae_vectors WHERE ns=%s "
                "ORDER BY embedding <=> %s::vector LIMIT %s",
                (qv, ns, qv, k),
            )
            rows = cur.fetchall()
        return [{"id": r[0], "meta": r[1], "score": float(r[2])} for r in rows]

    def delete(self, ns: str, id: str) -> bool:
        with self._lock, self._conn.cursor() as cur:
            cur.execute("DELETE FROM ae_vectors WHERE ns=%s AND id=%s", (ns, id))
            return cur.rowcount > 0
