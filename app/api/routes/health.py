"""Rute health check layanan dan kesiapan model.

`/health` selalu hidup selama proses berjalan (liveness).
`/ready` mencerminkan apakah model final berhasil dimuat (readiness).
Dipisah sesuai RULES.md §3 agar gangguan model tidak dianggap matinya layanan.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_prediction_service
from app.schemas.response import HealthResponse, ReadyResponse
from app.services.predictor import PredictionService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Liveness check: layanan berjalan."""
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": "not_ready"}},
)
def get_ready(
    response: Response,
    service: PredictionService = Depends(get_prediction_service),
) -> ReadyResponse:
    """Readiness check: apakah model final sudah termuat."""
    if not service.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(model="not_ready")
    return ReadyResponse(model="ready")
