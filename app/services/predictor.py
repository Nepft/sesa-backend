"""Layanan prediksi sentimen.

Modul ini memuat artefak model final (bundle joblib dari Colab) yang berisi
vectorizer TF-IDF terlatih + model SVM + pemetaan label. Jika artefak gagal
dimuat, layanan menandai dirinya "tidak siap" dan permintaan prediksi akan
ditolak dengan status 503 — tidak pernah menghasilkan prediksi palsu
(lihat RULES.md §2).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib

from app.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)


class ModelNotReadyError(Exception):
    """Dipakai ketika artefak model belum tersedia / gagal dimuat."""


@dataclass(frozen=True)
class Prediction:
    """Satu hasil prediksi: label model beserta persentase confidence per label.

    `confidence` memetakan nama label ke persentase 0-100 (1 desimal) hasil
    `predict_proba`; `None` bila artefak tidak menyediakan probabilitas.
    """

    label: str
    confidence: dict[str, float] | None


class PredictionService:
    """Membungkus model + preprocessing serta menyediakan API prediksi."""

    def __init__(self, model_path: Path, preprocessor: TextPreprocessor) -> None:
        self.model_path = Path(model_path)
        self.preprocessor = preprocessor
        self._vectorizer = None
        self._model = None
        self._labels: list[str] = []
        # Nama kolom predict_proba (mengikuti model.classes_); None bila model
        # tidak menyediakan probabilitas.
        self._proba_labels: list[str] | None = None
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

        # Kolom predict_proba mengikuti classes_, bukan urutan labels bundle.
        classes = getattr(self._model, "classes_", None)
        if classes is not None and hasattr(self._model, "predict_proba"):
            self._proba_labels = [str(c) for c in classes]
            if set(self._proba_labels) != set(self._labels):
                logger.warning(
                    "classes_ %s berbeda dari labels bundle %s; kunci confidence "
                    "memakai classes_.",
                    self._proba_labels,
                    self._labels,
                )
        else:
            self._proba_labels = None

        self.ready = True
        logger.info("Model berhasil dimuat dari %s", self.model_path)

    # -- prediksi ----------------------------------------------------------
    def _predict_texts(self, texts: list[str]) -> list[Prediction]:
        """Pra-proses lalu prediksi daftar teks mentah."""
        if not self.ready:
            raise ModelNotReadyError("Model belum siap.")

        processed = self.preprocessor.preprocess_many(texts)
        # Teks hasil stemming kosong -> vektor nol; tetap diprediksi model,
        # namun hasil kosong ditandai agar klien paham.
        features = self._vectorizer.transform(processed)
        labels = [str(label) for label in self._model.predict(features)]

        proba = None
        if self._proba_labels is not None:
            proba = self._model.predict_proba(features)

        predictions: list[Prediction] = []
        mismatches = 0
        for index, label in enumerate(labels):
            confidence = None
            if proba is not None:
                row = proba[index]
                confidence = {
                    name: round(float(value) * 100, 1)
                    for name, value in zip(self._proba_labels, row)
                }
                if self._proba_labels[int(row.argmax())] != label:
                    mismatches += 1
            predictions.append(Prediction(label=label, confidence=confidence))

        if mismatches:
            # Label tetap hasil predict() (pipeline eksperimen); persentase proba
            # dikirim apa adanya tanpa disesuaikan (RULES.md §5).
            logger.warning(
                "%d/%d baris: label predict() berbeda dari proba tertinggi.",
                mismatches,
                len(labels),
            )
        return predictions

    def predict_one(self, text: str) -> Prediction:
        """Prediksi sentimen untuk satu teks ulasan."""
        return self._predict_texts([text])[0]

    def predict_many(self, texts: list[str]) -> list[Prediction]:
        """Prediksi sentimen untuk daftar teks (batch)."""
        return self._predict_texts(texts)

    @property
    def labels(self) -> list[str]:
        return list(self._labels)
