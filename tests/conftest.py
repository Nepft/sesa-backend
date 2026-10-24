"""Fixture & test double untuk pengujian SESA Backend.

Test double di bawah adalah model sklearn KECIL yang dilatih pada data
sintetis, dipakai HANYA untuk menguji plumbing API (validasi, format respons,
status code). Ini BUKAN model produksi dan tidak boleh dipakai untuk klaim
kinerja (lihat RULES.md §2).
"""
from __future__ import annotations

import csv
import io

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC

from app.main import create_app
from app.services.preprocessing import TextPreprocessor


# ---------------------------------------------------------------------------
# Test double: model sintetis (BUKAN model produksi)
# ---------------------------------------------------------------------------
def _build_test_double_bundle(tmp_path):
    """Bangun bundle tiruan yang meniru struktur artefak produksi."""
    # Data sintetis sangat kecil: 'bagus' cenderung Positif, 'jelek' Negatif.
    train_texts = [
        "bagus bagus bagus mantap",
        "jelek jelek buruk",
        "mantap keren bagus",
        "buruk jelek payah",
        "keren bagus mantap",
        "payah jelek buruk",
    ]
    train_labels = ["Positif", "Negatif", "Positif", "Negatif", "Positif", "Negatif"]

    vectorizer = TfidfVectorizer(max_features=50)
    X = vectorizer.fit_transform(train_texts)
    model = SVC(kernel="linear")
    model.fit(X, train_labels)

    bundle = {
        "vectorizer": vectorizer,
        "model": model,
        "labels": ["Negatif", "Positif"],
        "sklearn_version": "test-double",
    }
    path = tmp_path / "test_model.joblib"
    joblib.dump(bundle, path)
    return path


@pytest.fixture(scope="session")
def kamus_path():
    from app.core.config import get_settings

    return get_settings().kamus_path


@pytest.fixture(scope="session")
def stopwords_path():
    from app.core.config import get_settings

    return get_settings().stopwords_path


@pytest.fixture(scope="session")
def preprocessor(kamus_path, stopwords_path):
    """Preprocessor nyata (memakai resource lokal) untuk tes preprocessing."""
    return TextPreprocessor(kamus_path=kamus_path, stopwords_path=stopwords_path)


@pytest.fixture()
def test_model_path(tmp_path):
    """Path artefak tiruan (model sintetis, bukan model produksi)."""
    return _build_test_double_bundle(tmp_path)


@pytest.fixture()
def client_with_model(test_model_path, monkeypatch):
    """Client dengan model tiruan yang berhasil dimuat."""
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "model_path", test_model_path)

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client_without_model(tmp_path, monkeypatch):
    """Client dengan path model yang tidak ada (simulasi gagal dimuat)."""
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "model_path", tmp_path / "missing.joblib")

    app = create_app()
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper untuk membangun CSV di memori
# ---------------------------------------------------------------------------
def make_csv(content: str, encoding: str = "utf-8") -> bytes:
    return content.encode(encoding)


def csv_upload(content: str, filename: str = "ulasan.csv"):
    """Kembalikan tuple (files) untuk TestClient.post(..., files=...)."""
    return {"file": (filename, make_csv(content), "text/csv")}
