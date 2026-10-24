"""Layanan prediksi sentimen.

Modul ini memuat artefak model final (bundle joblib dari Colab) yang berisi
vectorizer TF-IDF terlatih + model SVM + pemetaan label. Jika artefak gagal
dimuat, layanan menandai dirinya "tidak siap" dan permintaan prediksi akan
ditolak dengan status 503 — tidak pernah menghasilkan prediksi palsu
(lihat RULES.md §2).
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib

from app.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)


class ModelNotReadyError(Exception):
    """Dipakai ketika artefak model belum tersedia / gagal dimuat."""


class PredictionService:
    """Membungkus model + preprocessing serta menyediakan API prediksi."""

    def __init__(self, model_path: Path, preprocessor: TextPreprocessor) -> None:
        self.model_path = Path(model_path)
        self.preprocessor = preprocessor
        self._vectorizer = None
        self._model = None
        self._labels: list[str] = []
        self.ready = False

    # -- pemuatan model ----------------------------------------------------
    def load(self) -> None:
        """Muat artefak model dari disk.

        Melempar OSError/FileNotFoundError/Exception bila gagal; pemanggil
        bertanggung jawab menangani dan menandai layanan tidak siap.
        """
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Artefak model tidak ditemukan di {self.model_path}"
            )

        bundle = joblib.load(self.model_path)

        # Validasi struktur bundle minimal.
        for key in ("vectorizer", "model", "labels"):
            if key not in bundle:
                raise ValueError(f"Artefak model tidak memiliki key '{key}'")

        self._vectorizer = bundle["vectorizer"]
        self._model = bundle["model"]
        self._labels = list(bundle["labels"])
        self.ready = True
        logger.info("Model berhasil dimuat dari %s", self.model_path)

    # -- prediksi ----------------------------------------------------------
    def _predict_texts(self, texts: list[str]) -> list[str]:
        """Pra-proses lalu prediksi daftar teks mentah."""
        if not self.ready:
            raise ModelNotReadyError("Model belum siap.")

        processed = self.preprocessor.preprocess_many(texts)
        # Teks hasil stemming kosong -> vektor nol; tetap diprediksi model,
        # namun hasil kosong ditandai agar klien paham.
        features = self._vectorizer.transform(processed)
        raw = self._model.predict(features)
        return [str(label) for label in raw]

    def predict_one(self, text: str) -> str:
        """Prediksi sentimen untuk satu teks ulasan."""
        return self._predict_texts([text])[0]

    def predict_many(self, texts: list[str]) -> list[str]:
        """Prediksi sentimen untuk daftar teks (batch)."""
        return self._predict_texts(texts)

    @property
    def labels(self) -> list[str]:
        return list(self._labels)
