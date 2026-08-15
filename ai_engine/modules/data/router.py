"""Routeur data — /v1/data/{profile,clean,clean-text,prepare-rag,prepare-corpus,prepare-training}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.data.engine import get_data_engine

router = APIRouter(prefix="/v1/data", tags=["data"])


class RecordsRequest(BaseModel):
    records: list[dict] = Field(min_length=1)


class CleanRequest(RecordsRequest):
    trim: bool = True
    collapse_ws: bool = True
    coerce_types: bool = True
    drop_empty_rows: bool = True
    drop_duplicates: bool = True


class TextsRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    min_len: int = Field(default=1, ge=0)
    dedup: bool = True
    normalize: bool = True


class PrepareRagRequest(BaseModel):
    namespace: str = Field(min_length=1)
    texts: list[str] = Field(min_length=1)
    min_len: int = Field(default=1, ge=0)


class PrepareTrainingRequest(RecordsRequest):
    text_field: str = Field(min_length=1)
    label_field: str = Field(min_length=1)


@router.post("/profile")
def profile(req: RecordsRequest) -> dict:
    return get_data_engine().profile(req.records)


@router.post("/clean")
def clean(req: CleanRequest) -> dict:
    return get_data_engine().clean(
        req.records, trim=req.trim, collapse_ws=req.collapse_ws,
        coerce_types=req.coerce_types, drop_empty_rows=req.drop_empty_rows,
        drop_duplicates=req.drop_duplicates,
    )


@router.post("/clean-text")
def clean_text(req: TextsRequest) -> dict:
    return get_data_engine().clean_texts(
        req.texts, min_len=req.min_len, dedup=req.dedup, normalize=req.normalize
    )


@router.post("/prepare-rag")
async def prepare_rag(req: PrepareRagRequest) -> dict:
    try:
        return await get_data_engine().prepare_for_rag(req.namespace, req.texts, min_len=req.min_len)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"data.prepare_rag: {e}")


@router.post("/prepare-corpus")
def prepare_corpus(req: TextsRequest) -> dict:
    return get_data_engine().prepare_corpus(req.texts, min_len=req.min_len)


@router.post("/prepare-training")
def prepare_training(req: PrepareTrainingRequest) -> dict:
    return get_data_engine().prepare_training(
        req.records, text_field=req.text_field, label_field=req.label_field
    )
