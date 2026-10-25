"""Rute analisis sentimen: teks tunggal dan batch CSV.

Kontrak API ini dipakai bersama oleh aplikasi web dan Flutter. Perubahan bentuk
respons yang bersifat breaking harus dikoordinasikan dengan kedua klien
(lihat RULES.md §3).
"""
from __future__ import annotations

import csv
import io
import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import get_prediction_service
from app.schemas.request import PredictTextRequest
from app.schemas.response import (
    BatchPredictResponse,
    BatchResultItem,
    BatchSkippedItem,
    PredictTextResponse,
)
from app.services.predictor import ModelNotReadyError, PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["predict"])

# Alasan baris dilewati (dikembalikan ke klien agar mudah didebug).
_REASON_INVALID_ROW = "baris tidak memiliki kolom teks yang valid"


def _ensure_model_ready(service: PredictionService) -> None:
    """Tolak request bila model belum siap (tanpa membocorkan detail internal)."""
    if not service.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model belum siap. Coba lagi nanti.",
        )


@router.post("", response_model=PredictTextResponse)
def predict_text(
    body: PredictTextRequest,
    service: PredictionService = Depends(get_prediction_service),
) -> PredictTextResponse:
    """Analisis sentimen satu teks ulasan.

    Mengembalikan label 'Positif' atau 'Negatif' sesuai pemetaan model final.
    """
    logger.info("Request POST /predict diterima dari Flutter atau klien API")
    _ensure_model_ready(service)
    try:
        label = service.predict_one(body.text)
    except ModelNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model belum siap. Coba lagi nanti.",
        )
    except Exception:
        # Log untuk diagnosis internal; jangan bocorkan stack trace ke klien.
        logger.exception("Kesalahan internal saat prediksi teks tunggal")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan internal.",
        )
    return PredictTextResponse(text=body.text, label=label)


def _detect_delimiter(header_line: str) -> str:
    """Tentukan pemisah kolom dari baris header (koma atau titik-koma).

    Eksperimen Colab memakai ';' sementara unggahan web umumnya memakai ','.
    Mendeteksi dari baris header agar keduanya diterima tanpa menebak-nebak.
    """
    return ";" if header_line.count(";") > header_line.count(",") else ","


def _parse_csv_text(
    raw: bytes,
    settings,
    service: PredictionService,
) -> BatchPredictResponse:
    """Decode, parse, dan prediksi CSV. Berjalan di threadpool (blocking).

    Menaikkan HTTPException untuk galat validasi; pemanggil memastikan ini
    tidak menabrak event loop.
    """
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File bukan CSV yang valid (encoding tidak didukung).",
        )

    # Deteksi pemisah dari baris pertama sebelum parse penuh.
    first_line = text.splitlines()[0] if text.splitlines() else ""
    delimiter = _detect_delimiter(first_line)

    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    except csv.Error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File bukan CSV yang valid.",
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File tidak berisi data.",
        )

    header = [h.strip() for h in rows[0]]
    # Pencocokan tanpa memandang huruf besar/kecil, konsisten dengan parser CSV
    # pada klien Flutter.
    text_col = settings.csv_text_column.lower()
    header_lower = [h.lower() for h in header]
    if text_col not in header_lower:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kolom '{settings.csv_text_column}' tidak ditemukan pada file CSV.",
        )
    col_index = header_lower.index(text_col)

    data_rows = rows[1:]
    if len(data_rows) > settings.max_csv_rows:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Jumlah baris melebihi batas maksimal {settings.max_csv_rows}.",
        )
    if not data_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File tidak berisi baris data.",
        )

    valid_texts: list[str] = []
    valid_rows: list[int] = []
    skipped: list[BatchSkippedItem] = []

    for offset, row in enumerate(data_rows):
        row_number = offset + 2  # +2: header = baris 1, data mulai baris 2
        value = row[col_index].strip() if col_index < len(row) else ""
        if not value:
            skipped.append(
                BatchSkippedItem(row=row_number, reason=_REASON_INVALID_ROW)
            )
            continue
        valid_texts.append(value)
        valid_rows.append(row_number)

    results: list[BatchResultItem] = []
    if valid_texts:
        labels = service.predict_many(valid_texts)
        for row_number, label in zip(valid_rows, labels):
            results.append(BatchResultItem(row=row_number, label=label))

    return BatchPredictResponse(
        total=len(results), results=results, skipped=skipped
    )


@router.post("/batch", response_model=BatchPredictResponse)
async def predict_batch(
    request: Request,
    file: UploadFile = File(...),
    service: PredictionService = Depends(get_prediction_service),
) -> BatchPredictResponse:
    """Analisis sentimen banyak ulasan dari file CSV.

    File CSV wajib memiliki kolom teks (nama kolom dikonfigurasi lewat
    `CSV_TEXT_COLUMN`, default `content`). Setiap baris valid menghasilkan satu
    prediksi, dilengkapi nomor baris agar mudah dicocokkan dengan input. Baris
    yang kosong/tidak valid dilewati tanpa menggagalkan seluruh batch.
    """
    _ensure_model_ready(service)

    settings = request.app.state.settings

    # --- Validasi tipe file (jangan percaya ekstensi saja) ---
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    if not (
        filename.endswith(".csv")
        or content_type in {"text/csv", "application/vnd.ms-excel", "text/plain"}
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File harus berformat CSV.",
        )

    # --- Baca isi file per-blok, berhenti begitu melewati batas ukuran ---
    # Membaca bertahap agar file besar tidak sempat ter-buffer penuh di memori
    # sebelum ditolak (batas keamanan).
    max_size = settings.max_upload_size_bytes
    buffer = bytearray()
    too_large = False
    while True:
        chunk = await file.read(1024 * 1024)  # blok 1 MiB
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_size:
            too_large = True
            break
    if too_large:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Ukuran file melebihi batas maksimal {max_size} byte.",
        )
    raw = bytes(buffer)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File kosong.",
        )

    # --- Decode, parse, dan prediksi di threadpool agar tidak memblokir loop ---
    try:
        return await run_in_threadpool(
            _parse_csv_text, raw, settings, service
        )
    except ModelNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model belum siap. Coba lagi nanti.",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Kesalahan internal saat prediksi batch")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan internal.",
        )
