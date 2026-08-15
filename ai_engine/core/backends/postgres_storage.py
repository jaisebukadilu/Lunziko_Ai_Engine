"""StoragePort — adaptateur Postgres (couplage optionnel à Platform, sans le modifier).

Activé par `AE_STORAGE_BACKEND=postgres` + `AE_POSTGRES_DSN`. Requiert l'extra `postgres`
(`psycopg`). L'AI Engine écrit dans la base indiquée ; il n'impose aucune modif à Platform.
Table auto-créée : `ae_kv(ns, key, value jsonb)`.
"""

from __future__ import annotations

import json
import threading

import psycopg


class PostgresStorage:
    def __init__(self, dsn: str) -> None:
        self._lock = threading.Lock()
        self._conn = psycopg.connect(dsn, autocommit=True)
        with self._conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS ae_kv ("
                " ns TEXT NOT NULL, key TEXT NOT NULL, value JSONB NOT NULL,"
                " PRIMARY KEY (ns, key))"
            )

    def get(self, ns: str, key: str) -> dict | None:
        with self._lock, self._conn.cursor() as cur:
            cur.execute("SELECT value FROM ae_kv WHERE ns=%s AND key=%s", (ns, key))
            row = cur.fetchone()
        return row[0] if row else None

    def put(self, ns: str, key: str, value: dict) -> None:
        with self._lock, self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ae_kv(ns,key,value) VALUES(%s,%s,%s) "
                "ON CONFLICT (ns,key) DO UPDATE SET value=EXCLUDED.value",
                (ns, key, json.dumps(value, ensure_ascii=False)),
            )

    def delete(self, ns: str, key: str) -> bool:
        with self._lock, self._conn.cursor() as cur:
            cur.execute("DELETE FROM ae_kv WHERE ns=%s AND key=%s", (ns, key))
            return cur.rowcount > 0

    def list(self, ns: str) -> list[dict]:
        with self._lock, self._conn.cursor() as cur:
            cur.execute("SELECT value FROM ae_kv WHERE ns=%s", (ns,))
            rows = cur.fetchall()
        return [r[0] for r in rows]
