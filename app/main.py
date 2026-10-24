"""Entry point aplikasi FastAPI SESA Backend.

Aplikasi ini menyediakan API analisis sentimen ulasan Steam yang dipakai
bersama oleh klien web dan Flutter. Model final dimuat sekali saat startup;
bila gagal, layanan tetap berjalan namun endpoint prediksi akan menolak
permintaan dengan 503 (bukan menghasilkan prediksi palsu).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, predict
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.preprocessing import TextPreprocessor
from app.services.predictor import PredictionService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Muat konfigurasi, resource preprocessing, dan model saat startup."""
    settings = get_settings()
    setup_logging(settings.log_level)

    # Resource preprocessing bundle lokal (determinis, tanpa fetch runtime).
    preprocessor = TextPreprocessor(
        kamus_path=settings.kamus_path,
        stopwords_path=settings.stopwords_path,
    )

    service = PredictionService(
        model_path=settings.model_path,
        preprocessor=preprocessor,
    )
    try:
        service.load()
    except Exception:
        # Gagal memuat model tidak boleh menjatuhkan seluruh layanan.
        # Endpoint /ready akan melaporkan not_ready dan prediksi ditolak 503.
        logger.exception(
            "Model gagal dimuat; layanan berjalan dalam status tidak siap."
        )

    app.state.settings = settings
    app.state.prediction_service = service

    yield


def create_app() -> FastAPI:
    """Factory aplikasi FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title="SESA Backend API",
        description=(
            "API analisis sentimen ulasan aplikasi Steam. "
            "Digunakan bersama oleh aplikasi web dan Flutter."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS terbatas sesuai konfigurasi (bukan wildcard).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(predict.router)

    return app


app = create_app()
