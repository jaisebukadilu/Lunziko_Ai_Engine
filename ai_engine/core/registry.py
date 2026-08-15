"""Câblage des ports selon la config. Change de backend sans toucher au cœur."""

from __future__ import annotations

from functools import lru_cache

from ai_engine.config import get_settings
from ai_engine.core.backends.fs_blob import FsBlob
from ai_engine.core.backends.local_vector import LocalVector
from ai_engine.core.backends.sqlite_storage import SqliteStorage
from ai_engine.core.ports import BlobPort, StoragePort, VectorPort


@lru_cache
def get_storage() -> StoragePort:
    s = get_settings()
    if s.ae_storage_backend == "postgres":
        # Import paresseux : psycopg (extra `postgres`) requis seulement dans ce mode.
        from ai_engine.core.backends.postgres_storage import PostgresStorage

        if not s.ae_postgres_dsn:
            raise RuntimeError("AE_STORAGE_BACKEND=postgres nécessite AE_POSTGRES_DSN")
        return PostgresStorage(s.ae_postgres_dsn)
    return SqliteStorage(s.db_path)


@lru_cache
def get_vector() -> VectorPort:
    s = get_settings()
    if s.ae_vector_backend == "pgvector":
        from ai_engine.core.backends.pg_vector import PgVector

        if not s.ae_postgres_dsn:
            raise RuntimeError("AE_VECTOR_BACKEND=pgvector nécessite AE_POSTGRES_DSN")
        return PgVector(s.ae_postgres_dsn)
    return LocalVector(s.home / "vectors")


@lru_cache
def get_blob() -> BlobPort:
    s = get_settings()
    if s.ae_blob_backend == "s3":
        raise NotImplementedError("BlobPort s3: adaptateur prévu")
    return FsBlob(s.blob_dir)
