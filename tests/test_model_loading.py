"""Pengujian pemuatan model & endpoint health/ready.

Menguji perilaku saat model berhasil dimuat dan saat gagal dimuat. Layanan
tidak boleh menghasilkan prediksi palsu ketika model tidak tersedia
(lihat RULES.md §2 & AGENT.md §5).
"""
from __future__ import annotations


def test_health_always_ok(client_with_model):
    resp = client_with_model.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_ok_even_when_model_missing(client_without_model):
    """Liveness tidak tergantung kesiapan model (RULES.md §3)."""
    resp = client_without_model.get("/health")
    assert resp.status_code == 200


def test_ready_when_model_loaded(client_with_model):
    resp = client_with_model.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"model": "ready"}


def test_ready_not_ready_when_model_missing(client_without_model):
    resp = client_without_model.get("/ready")
    assert resp.status_code == 503
    assert resp.json() == {"model": "not_ready"}


def test_prediction_service_ready_flag(client_with_model, client_without_model):
    assert client_with_model.app.state.prediction_service.ready is True
    assert client_without_model.app.state.prediction_service.ready is False
