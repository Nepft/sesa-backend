"""Pengujian penanganan galat internal (M2).

Memastikan exception tak tertangani di luar route menghasilkan respons JSON
konsisten `{"detail": ...}` dengan status 500, tanpa membocorkan stack trace
atau pesan galat internal ke klien (RULES.md §3).
"""
from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


def test_unhandled_exception_returns_json_500():
    """Route yang melempar galat tak tertangani -> JSON 500 tanpa stack trace."""
    app = create_app()

    def _boom():
        raise RuntimeError("SECRET_PATH=/etc/secret pesan internal")

    @app.get("/boom")
    def _route(dep=Depends(_boom)):
        return {}

    # raise_server_exceptions=False meniru perilaku produksi (tanpa traceback).
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/boom")

    assert resp.status_code == 500
    # Respons harus JSON dengan field detail, bukan teks polos.
    body = resp.json()
    assert "detail" in body
    # Tidak boleh membocorkan stack trace, exception, atau path internal.
    text = resp.text
    assert "Traceback" not in text
    assert "SECRET_PATH" not in text
    assert "RuntimeError" not in text
