"""Konfigurasi logging yang aman untuk layanan API.

Logging di sini hanya mencatat kejadian operasional (status pemuatan model,
kode status request, ukuran batch). Isi ulasan pengguna, unggahan, secret,
dan stack trace tidak pernah ditulis ke log.
"""
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Atur format dan level logging dasar untuk seluruh proses."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Redam logger berisik dari pihak ketiga agar log tetap ringkas.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
