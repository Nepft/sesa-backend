"""Dependensi FastAPI untuk mengakses layanan prediksi bersama.

Instance PredictionService dibuat satu kali (singleton) pada startup aplikasi
dan dibagikan ke semua request melalui `app.state`.
"""
from __future__ import annotations

from fastapi import Request

from app.services.predictor import PredictionService


def get_prediction_service(request: Request) -> PredictionService:
    """Ambil instance PredictionService dari state aplikasi."""
    service: PredictionService = request.app.state.prediction_service
    return service
