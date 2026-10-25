"""Pengujian endpoint prediksi batch CSV (/predict/batch)."""
from __future__ import annotations

from tests.conftest import csv_upload


def test_batch_success(client_with_model):
    csv_content = "content\naplikasi ini bagus\n game jelek sekali \n"
    resp = client_with_model.post(
        "/predict/batch", files=csv_upload(csv_content)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["results"]) == 2
    # Nomor baris harus 2 dan 3 (header = baris 1).
    assert [r["row"] for r in body["results"]] == [2, 3]
    for r in body["results"]:
        assert r["label"] in {"Positif", "Negatif"}


def test_batch_skips_empty_rows(client_with_model):
    csv_content = "content\nbagus sekali\n\njelek\n"
    resp = client_with_model.post(
        "/predict/batch", files=csv_upload(csv_content)
    )
    assert resp.status_code == 200
    body = resp.json()
    # 2 baris valid (baris 2 & 4), 1 baris kosong (baris 3) dilewati.
    assert body["total"] == 2
    assert len(body["skipped"]) == 1
    assert body["skipped"][0]["row"] == 3


def test_batch_empty_file_rejected(client_with_model):
    resp = client_with_model.post(
        "/predict/batch", files=csv_upload("")
    )
    assert resp.status_code == 400


def test_batch_wrong_header_rejected(client_with_model):
    csv_content = "id;review\n1;bagus\n"
    resp = client_with_model.post(
        "/predict/batch", files=csv_upload(csv_content)
    )
    assert resp.status_code == 400
    assert "content" in resp.json()["detail"]


def test_batch_column_match_is_case_insensitive(client_with_model):
    """Header kolom teks diterima tanpa memandang huruf besar/kecil (M4)."""
    for header in ["Content", "CONTENT", "cOnTeNt"]:
        csv_content = f"{header}\naplikasi bagus\n"
        resp = client_with_model.post(
            "/predict/batch", files=csv_upload(csv_content)
        )
        assert resp.status_code == 200, f"header {header!r} seharusnya diterima"
        assert resp.json()["total"] == 1


def test_batch_semicolon_delimiter_supported(client_with_model):
    """CSV dengan pemisah titik-koma (gaya Colab) tetap terbaca (L1)."""
    csv_content = "content;rating\naplikasi bagus;5\n"
    resp = client_with_model.post(
        "/predict/batch", files=csv_upload(csv_content)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["results"][0]["row"] == 2


def test_batch_header_only_rejected(client_with_model):
    csv_content = "content\n"
    resp = client_with_model.post(
        "/predict/batch", files=csv_upload(csv_content)
    )
    assert resp.status_code == 400


def test_batch_not_csv_rejected(client_with_model):
    resp = client_with_model.post(
        "/predict/batch",
        files={"file": ("foto.png", b"\x89PNGbinary", "image/png")},
    )
    assert resp.status_code == 415


def test_batch_too_many_rows_rejected(client_with_model, monkeypatch):
    from app.core.config import get_settings

    # Turunkan batas baris agar mudah diuji; monkeypatch mengembalikan nilai
    # aslinya otomatis setelah tes selesai.
    monkeypatch.setattr(get_settings(), "max_csv_rows", 2)
    csv_content = "content\nbagus\njelek\nnetral\n"
    resp = client_with_model.post(
        "/predict/batch", files=csv_upload(csv_content)
    )
    assert resp.status_code == 413


def test_batch_model_not_ready(client_without_model):
    csv_content = "content\nbagus\n"
    resp = client_without_model.post(
        "/predict/batch", files=csv_upload(csv_content)
    )
    assert resp.status_code == 503
    assert "traceback" not in resp.text.lower()
