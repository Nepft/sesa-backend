"""Pengujian endpoint prediksi teks tunggal (/predict)."""
from __future__ import annotations


def test_predict_text_success(client_with_model):
    resp = client_with_model.post(
        "/predict", json={"text": "aplikasi ini sangat bagus dan mudah"}
    )
    assert resp.status_code == 200
    body = resp.json()
    # Kontrak: hanya boleh memuat text dan label.
    assert set(body.keys()) == {"text", "label"}
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


def test_predict_text_missing_field_rejected(client_with_model):
    resp = client_with_model.post("/predict", json={})
    assert resp.status_code == 422


def test_predict_text_no_confidence_field(client_with_model):
    """API tidak boleh mengembalikan confidence (SVM tanpa probabilitas)."""
    resp = client_with_model.post("/predict", json={"text": "bagus sekali"})
    assert resp.status_code == 200
    body = resp.json()
    assert "confidence" not in body
    assert "probability" not in body


def test_predict_text_model_not_ready(client_without_model):
    resp = client_without_model.post("/predict", json={"text": "bagus"})
    assert resp.status_code == 503
    # Tidak boleh membocorkan stack trace / path server.
    assert "traceback" not in resp.text.lower()
    assert "joblib" not in resp.text.lower()
