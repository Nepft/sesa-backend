"""Skema response untuk endpoint prediksi.

Kontrak ini dipakai bersama oleh klien web dan Flutter. Jangan ubah nama
field atau bentuk JSON secara diam-diam (lihat RULES.md §3).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PredictTextResponse(BaseModel):
    """Hasil analisis sentimen satu teks ulasan."""

    text: str = Field(..., description="Teks ulasan seperti yang diterima.")
    label: str = Field(
        ..., description="Label sentimen hasil model: 'Positif' atau 'Negatif'."
    )


class BatchResultItem(BaseModel):
    """Satu baris hasil analisis batch, dicocokkan dengan nomor baris input."""

    row: int = Field(..., description="Nomor baris (1-based) pada file CSV.")
    label: str = Field(..., description="Label sentimen hasil model.")


class BatchSkippedItem(BaseModel):
    """Baris yang dilewati beserta alasannya."""

    row: int = Field(..., description="Nomor baris (1-based) pada file CSV.")
    reason: str = Field(..., description="Alasan baris dilewati.")


class BatchPredictResponse(BaseModel):
    """Hasil analisis batch dari file CSV."""

    total: int = Field(..., description="Jumlah baris valid yang berhasil diproses.")
    results: list[BatchResultItem] = Field(
        default_factory=list, description="Hasil prediksi per baris."
    )
    skipped: list[BatchSkippedItem] = Field(
        default_factory=list, description="Baris yang dilewati beserta alasannya."
    )


class HealthResponse(BaseModel):
    """Status kesehatan layanan (bukan kesiapan model)."""

    status: str = Field(default="ok", description="Selalu 'ok' bila layanan hidup.")


class ReadyResponse(BaseModel):
    """Status kesiapan model prediksi."""

    model: str = Field(
        ...,
        description="'ready' bila model termuat, 'not_ready' bila belum/gagal.",
    )


class ErrorResponse(BaseModel):
    """Respons error yang konsisten dan tidak membocorkan detail internal."""

    detail: str = Field(..., description="Pesan error yang aman untuk klien.")
