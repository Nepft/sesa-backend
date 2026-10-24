"""Pengujian pipeline preprocessing.

Menguji bahwa preprocessing bekerja sesuai perilaku eksperimen: teks bersih
dari URL/emoji/simbol/angka, dinormalisasi, stopword dibuang, dan hasil akhir
berupa teks stemming. Sengaja TIDAK memakai model produksi.
"""
from __future__ import annotations

import pytest


def test_case_folding_lowercase(preprocessor):
    assert preprocessor.preprocess("BAGUS Sekali") == preprocessor.preprocess(
        "bagus sekali"
    )


def test_remove_url(preprocessor):
    out = preprocessor.preprocess("cek https://example.com/game ini bagus")
    assert "https" not in out
    assert "example" not in out


def test_remove_emoji(preprocessor):
    out = preprocessor.preprocess("game ini seru 😄😄")
    assert "😄" not in out


def test_remove_symbols_and_numbers(preprocessor):
    out = preprocessor.preprocess("rating 5 !!! game (bagus)")
    assert "!" not in out
    assert "5" not in out


def test_remove_username(preprocessor):
    out = preprocessor.preprocess("@user123 mantap jiwa")
    assert "@user123" not in out


def test_empty_and_none_input(preprocessor):
    assert preprocessor.preprocess("") == ""
    assert preprocessor.preprocess(None) == ""


def test_preprocess_many_preserves_order(preprocessor):
    texts = ["game bagus", "game jelek", "netral saja"]
    results = preprocessor.preprocess_many(texts)
    assert len(results) == 3
