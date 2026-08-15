"""Routeur neural — /v1/neural/{status,backends,route,train}.

Expose le système neuronal : backends disponibles (bibliothèques importées) et routage
d'intention neuronal.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.neural.backends import detect_backends
from ai_engine.modules.neural.inference import inference_status
from ai_engine.modules.neural.ml import get_ml_trainer
from ai_engine.modules.neural.router_engine import get_neural_router

router = APIRouter(prefix="/v1/neural", tags=["neural"])


class RouteRequest(BaseModel):
    query: str = Field(min_length=1)


class MLExample(BaseModel):
    text: str = Field(min_length=1)
    label: str = Field(min_length=1)


class MLTrainRequest(BaseModel):
    name: str = Field(min_length=1)
    examples: list[MLExample] = Field(min_length=2)
    epochs: int = Field(default=300, ge=10, le=5000)


class MLPredictRequest(BaseModel):
    name: str = Field(min_length=1)
    text: str = Field(min_length=1)


@router.get("/backends")
def backends() -> dict:
    b = detect_backends()
    return {"available": [k for k, v in b.items() if v["available"]], "backends": b}


@router.get("/status")
def status() -> dict:
    rt = get_neural_router()
    b = detect_backends()
    return {
        "available_backends": [k for k, v in b.items() if v["available"]],
        "router_trained": rt.trained,
        "router_backend": rt.backend,
    }


@router.post("/train")
async def train() -> dict:
    try:
        return await get_neural_router().train()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"neural.train: {e}")


@router.post("/route")
async def route(req: RouteRequest) -> dict:
    try:
        return await get_neural_router().route(req.query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"neural.route: {e}")


@router.get("/inference")
def inference() -> dict:
    """Moteurs d'inférence locaux supportés (Ollama/llama.cpp/vLLM/LM Studio/Triton/lunziko)."""
    return inference_status()


@router.post("/ml/train")
async def ml_train(req: MLTrainRequest) -> dict:
    """Entraîne un classifieur supervisé à partir d'exemples (texte → label), persisté."""
    try:
        return await get_ml_trainer().train(
            req.name, [e.model_dump() for e in req.examples], epochs=req.epochs
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"neural.ml.train: {e}")


@router.post("/ml/predict")
async def ml_predict(req: MLPredictRequest) -> dict:
    try:
        return await get_ml_trainer().predict(req.name, req.text)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"neural.ml.predict: {e}")


@router.get("/ml/models")
def ml_models() -> dict:
    return {"models": get_ml_trainer().list_models()}


@router.delete("/ml/models/{name}")
def ml_delete(name: str) -> dict:
    return {"deleted": get_ml_trainer().delete(name)}
