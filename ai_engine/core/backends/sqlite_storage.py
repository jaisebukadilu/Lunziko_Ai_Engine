"""StoragePort — backend SQLite local (défaut standalone). Zéro dépendance externe."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path


class SqliteStorage:
    """Clé-valeur namespacé sur SQLite. Thread-safe (lock simple)."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS kv ("
            " ns TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,"
            " PRIMARY KEY (ns, key))"
        )
        self._db.commit()

    def get(self, ns: str, key: str) -> dict | None:
        with self._lock:
            row = self._db.execute(
                "SELECT value FROM kv WHERE ns=? AND key=?", (ns, key)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, ns: str, key: str, value: dict) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO kv(ns,key,value) VALUES(?,?,?) "
                "ON CONFLICT(ns,key) DO UPDATE SET value=excluded.value",
                (ns, key, json.dumps(value, ensure_ascii=False)),
            )
            self._db.commit()

    def delete(self, ns: str, key: str) -> bool:
        with self._lock:
            cur = self._db.execute("DELETE FROM kv WHERE ns=? AND key=?", (ns, key))
            self._db.commit()
            return cur.rowcount > 0

    def list(self, ns: str) -> list[dict]:
        with self._lock:
            rows = self._db.execute("SELECT value FROM kv WHERE ns=?", (ns,)).fetchall()
        return [json.loads(r[0]) for r in rows]
