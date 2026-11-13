"""Pengujian endpoint prediksi teks tunggal (/predict)."""
from __future__ import annotations

import pytest


def test_predict_text_success(client_with_model):
    resp = client_with_model.post(
        "/predict", json={"text": "aplikasi ini sangat bagus dan mudah"}
    )
    assert resp.status_code == 200
    body = resp.json()
    # Kontrak: hanya boleh memuat text, label, dan confidence.
    assert set(body.keys()) == {"text", "label", "confidence"}
    assert body["label"] in {"Positif", "Negatif"}


def test_predict_text_returns_input_text(client_with_model):
    text = "game seru Recommended"
    resp = client_with_model.post("/predict", json={"text": text})
    assert resp.status_code == 200
    assert resp.json()["text"] == text


def test_predict_text_empty_rejected(client_with_model):
    resp = client_with_model.post("/predict", json={"text": ""})
    # Pydantic min_length=1 -> 422 unprocessable.
    assert resp.status_code == 422


def test_predict_text_whitespace_only_rejected(client_with_model):
    """Teks yang hanya spasi/tab/newline dianggap kosong dan ditolak (H1)."""
    for blank in ["   ", "\t\t", "\n \n", " \t \n "]:
        resp = client_with_model.post("/predict", json={"text": blank})
        assert resp.status_code == 422, f"input {blank!r} seharusnya ditolak"


def test_predict_text_missing_field_rejected(client_with_model):
    resp = client_with_model.post("/predict", json={})
    assert resp.status_code == 422


def test_predict_text_confidence_percentages(client_with_model):
    """Confidence = persentase per label (0-100, 1 desimal) berjumlah ~100."""
    resp = client_with_model.post(
        "/predict", json={"text": "aplikasi ini sangat bagus dan mudah"}
    )
    assert resp.status_code == 200
    confidence = resp.json()["confidence"]
    assert set(confidence.keys()) == {"Negatif", "Positif"}
    for value in confidence.values():
        assert 0.0 <= value <= 100.0
        assert round(value, 1) == value
    # Pembulatan dilakukan independen per label, jadi total boleh 99.9/100.1.
    assert sum(confidence.values()) == pytest.approx(100, abs=0.15)


def test_predict_text_confidence_null_without_proba(client_with_model_no_proba):
    """Artefak tanpa predict_proba -> confidence null, bukan angka karangan."""
    resp = client_with_model_no_proba.post(
        "/predict", json={"text": "bagus sekali"}
    )
    assert resp.status_code == 200
    assert resp.json()["confidence"] is None


def test_predict_text_model_not_ready(client_without_model):
    resp = client_without_model.post("/predict", json={"text": "bagus"})
    assert resp.status_code == 503
    # Tidak boleh membocorkan stack trace / path server.
    assert "traceback" not in resp.text.lower()
    assert "joblib" not in resp.text.lower()
