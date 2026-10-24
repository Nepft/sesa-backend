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
    # logger.info("Request POST /predict diterima dari Flutter atau klien API")
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

    # --- Baca isi file dengan batas ukuran ---
    raw = await file.read()
    max_size = settings.max_upload_size_bytes
    if len(raw) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Ukuran file melebihi batas maksimal {max_size} byte.",
        )
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File kosong.",
        )

    # --- Decode teks (toleran terhadap BOM UTF-8) ---
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File bukan CSV yang valid (encoding tidak didukung).",
        )

    # --- Parse CSV ---
    reader = csv.reader(io.StringIO(text))
    try:
        rows = list(reader)
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
    text_col = settings.csv_text_column
    if text_col not in header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kolom '{text_col}' tidak ditemukan pada file CSV.",
        )
    col_index = header.index(text_col)

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

    # --- Kumpulkan teks valid & catat baris yang dilewati ---
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

    # --- Prediksi seluruh baris valid sekaligus (batch) ---
    results: list[BatchResultItem] = []
    if valid_texts:
        try:
            labels = service.predict_many(valid_texts)
        except ModelNotReadyError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model belum siap. Coba lagi nanti.",
            )
        except Exception:
            logger.exception("Kesalahan internal saat prediksi batch")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Terjadi kesalahan internal.",
            )

        for row_number, label in zip(valid_rows, labels):
            results.append(BatchResultItem(row=row_number, label=label))

    return BatchPredictResponse(
        total=len(results), results=results, skipped=skipped
    )
