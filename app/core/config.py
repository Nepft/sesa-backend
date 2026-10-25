"""Konfigurasi terpusat SESA Backend.

Semua nilai dibaca dari environment variable (atau berkas `.env`) sehingga
tidak ada path absolut maupun secret yang di-hardcode di kode sumber.
"""
import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root repository (dua tingkat di atas berkas konfigurasi ini: app/core/config.py)
BASE_DIR = Path(__file__).resolve().parents[2]

# Lokasi berkas .env dapat dioverride lewat SESA_ENV_FILE (mis. pada deployment
# yang menyimpan konfigurasi di luar tree repo). Bila tidak diset, memakai .env
# di root repository. Nilai ini dibaca dari environment proses, bukan dari .env,
# karena dibutuhkan untuk menemukan .env itu sendiri.
ENV_FILE = Path(os.environ.get("SESA_ENV_FILE") or (BASE_DIR / ".env"))


class Settings(BaseSettings):
    """Pengaturan layanan yang divisasi dari environment."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Model ---
    model_path: Path = Field(default=BASE_DIR / "model" / "sesa_model.joblib")

    # --- Batas input (keamanan & stabilitas) ---
    max_upload_size_bytes: int = 5 * 1024 * 1024  # 5 MiB
    max_csv_rows: int = 5000
    csv_text_column: str = "content"
    max_text_length: int = 10_000  # batas karakter per teks ulasan tunggal

    # --- CORS ---
    cors_origins: list[str] = Field(default=["http://localhost:5173"])

    # --- Logging ---
    log_level: str = "INFO"

    # --- Resource preprocessing (bundle lokal, determinis) ---
    kamus_path: Path = Field(
        default=BASE_DIR / "data" / "kamus_kata_tidak_baku.csv"
    )
    stopwords_path: Path = Field(
        default=BASE_DIR / "data" / "stopwords_indonesian.txt"
    )


@lru_cache
def get_settings() -> Settings:
    """Kembalikan instance Settings yang sudah di-cache."""
    return Settings()
