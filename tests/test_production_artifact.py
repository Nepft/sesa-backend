"""Pengujian integrasi dengan artefak model produksi (L3).

Tes ini memuat `model/sesa_model.joblib` sungguhan (bukan stub) untuk memastikan
artefak tetap kompatibel dengan versi scikit-learn yang terpasang dan labelnya
sesuai kontrak API. Otomatis dilewati bila artefak tidak ada di environment ini,
sehingga CI tetap hijau tanpa berkas model.
"""
from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.services.preprocessing import TextPreprocessor
from app.services.predictor import PredictionService

MODEL_PATH = get_settings().model_path

pytestmark = pytest.mark.skipif(
    not MODEL_PATH.is_file(),
    reason=f"Artefak model tidak ditemukan di {MODEL_PATH}",
)


@pytest.fixture(scope="module")
def production_service() -> PredictionService:
    """Muat model produksi sungguhan sekali per modul tes."""
    settings = get_settings()
    preprocessor = TextPreprocessor(settings.kamus_path, settings.stopwords_path)
    service = PredictionService(settings.model_path, preprocessor)
    service.load()
    return service


def test_production_artifact_loads(production_service):
    assert production_service.ready
    assert production_service.labels


def test_production_artifact_labels_match_contract(production_service):
    """Label harus persis {Negatif, Positif} (kontrak API §3)."""
    assert set(production_service.labels) == {"Negatif", "Positif"}


def test_production_artifact_predicts_known_sentiment(production_service):
    """Prediksi terhadap ulasan berlabel jelas harus konsisten."""
    pos = production_service.predict_one("game nya sangat bagus dan seru Recommended")
    neg = production_service.predict_one("aplikasi ini jelek buruk sekali payah")
    assert pos in {"Positif", "Negatif"}
    assert neg in {"Positif", "Negatif"}
    assert pos != neg


def test_production_artifact_batch_preserves_order(production_service):
    texts = ["bagus sekali", "jelek sekali", "penasaran dan mantap"]
    labels = production_service.predict_many(texts)
    assert len(labels) == len(texts)
    for label in labels:
        assert label in {"Negatif", "Positif"}
