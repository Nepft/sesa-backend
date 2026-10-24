"""Pipeline preprocessing teks ulasan.

Modul ini mereproduksi **urutan persis** pipeline eksperimen Google Colab:

1. Cleaning  : remove_URL -> remove_usernames -> remove_html -> remove_emoji
               -> remove_symbols -> remove_numbers
2. Case folding (lowercase)
3. Normalisasi kata (kamus kata tidak baku -> baku, dari berkas lokal)
4. Tokenisasi (split spasi)
5. Stopword removal (NLTK bahasa Indonesia + daftar noise khusus + kamus slang)
6. Stemming (Sastrawi)

Tidak ada langkah yang ditambah, dihilangkan, atau diubah urutannya tanpa
bukti kesetaraan dengan eksperimen (lihat RULES.md §2).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# 1. CLEANING — regex & urutan identik dengan notebook
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_HTML_RE = re.compile(r"<.*?>")
_USERNAME_RE = re.compile(r"@\w+")
_SYMBOL_RE = re.compile(r"[^a-zA-Z0-9\s]")
_NUMBER_RE = re.compile(r"\d")
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U0001F004-\U0001F0CF"  # Additional emoticons
    "\U0001F1E0-\U0001F1FF"  # flags
    "]+",
    flags=re.UNICODE,
)


def remove_url(text):
    if text is not None and isinstance(text, str):
        return _URL_RE.sub("", text)
    return text


def remove_usernames(text):
    if text is not None and isinstance(text, str):
        return _USERNAME_RE.sub("", text)
    return text


def remove_html(text):
    if text is not None and isinstance(text, str):
        return _HTML_RE.sub("", text)
    return text


def remove_emoji(text):
    if text is not None and isinstance(text, str):
        return _EMOJI_RE.sub("", text)
    return text


def remove_symbols(text):
    if text is not None and isinstance(text, str):
        return _SYMBOL_RE.sub("", text)
    return text


def remove_numbers(text):
    if text is not None and isinstance(text, str):
        return _NUMBER_RE.sub("", text)
    return text


def clean_text(text):
    """Terapkan seluruh tahap cleaning secara berurutan (persis notebook)."""
    text = remove_url(text)
    text = remove_usernames(text)
    text = remove_html(text)
    text = remove_emoji(text)
    text = remove_symbols(text)
    text = remove_numbers(text)
    return text


# ---------------------------------------------------------------------------
# 5a. Daftar noise khusus & kamus slang (identik dengan notebook)
# ---------------------------------------------------------------------------

# Kata-kata noise/interjeksi tambahan yang dibuang dari ulasan Steam.
HAPUS_KATA = [
    "ya", "tok", "deh", "wok", "we", "the", "loh", "sih", "up", "pas", "kak",
    "ai", "swt", "abang", "mbak", "idf", "roy", "not", "nih", "cs", "y",
    "bang", "gue", "a", "bu", "mas", "bpk", "dek", "allah", "fery", "fer",
    "omon", "wo", "lo", "kau", "sok", "ku", "tuh", "gua", "om", "ded", "gus",
    "mu", "you", "vid", "thank", "lu", "tau", "al", "si", "densu",
]

# Kamus slang teknologi / singkatan spesifik ulasan Steam.
KAMUS_SLANG = {
    "app": "aplikasi",
    "apk": "aplikasi",
    "score": "rating",
    "hp": "handphone",
    "log in": "masuk",
    "login": "masuk",
    "cant": "tidak bisa",
}


class TextPreprocessor:
    """Menjalankan pipeline preprocessing lengkap secara determinis.

    Resource (kamus normalisasi & daftar stopword) dimuat dari berkas lokal
    sehingga hasil preprocessing sama persis di setiap environment dan tidak
    bergantung pada koneksi internet saat runtime.
    """

    def __init__(
        self,
        kamus_path: Path,
        stopwords_path: Path,
    ) -> None:
        self.kamus = self._load_kamus(kamus_path)
        self.stop_words = self._load_stopwords(stopwords_path)
        # Stemmer Sastrawi diinisialisasi malas (mahal) saat pertama dipakai.
        self._stemmer = None

    # -- pemuatan resource -------------------------------------------------
    @staticmethod
    def _load_kamus(path: Path) -> dict:
        """Muas kamus kata tidak baku -> baku (format kolom ';' )."""
        kamus_df = pd.read_csv(path, sep=";")
        kamus_df = kamus_df.dropna(subset=["Kata Tidak Baku", "Kata Baku"])
        tidak_baku = kamus_df["Kata Tidak Baku"].astype(str).str.strip()
        baku = kamus_df["Kata Baku"].astype(str).str.strip()
        return dict(zip(tidak_baku, baku))

    @staticmethod
    def _load_stopwords(path: Path) -> set:
        """Muat daftar stopword bahasa Indonesia dari berkas lokal."""
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        return {w.strip() for w in lines if w.strip()}

    @property
    def stemmer(self):
        """Stemmer Sastrawi (dibuat sekali, dipakai ulang)."""
        if self._stemmer is None:
            from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

            self._stemmer = StemmerFactory().create_stemmer()
        return self._stemmer

    # -- tahapan pemrosesan ------------------------------------------------
    def _normalize_words(self, text: str) -> str:
        words = text.split()
        normalized = [self.kamus.get(word, word) for word in words]
        return " ".join(normalized)

    def _remove_stopwords(self, tokens: list) -> str:
        return " ".join(
            w for w in tokens if w not in self.stop_words and w not in HAPUS_KATA
        )

    def _fix_slang(self, text: str) -> str:
        return " ".join(KAMUS_SLANG.get(kata, kata) for kata in text.split())

    def preprocess(self, text: str) -> str:
        """Jalankan pipeline penuh dan kembalikan teks hasil stemming.

        Teks input asli tidak dimodifikasi; hanya teks hasil yang dikembalikan.
        """
        if text is None or not isinstance(text, str):
            return ""

        # 1. Cleaning
        cleaned = clean_text(text)
        # 2. Case folding
        folded = cleaned.lower()
        # 3. Normalisasi kata
        normalized = self._normalize_words(folded)
        # 4. Tokenisasi
        tokens = normalized.split()
        # 5. Stopword removal (+ noise khusus) lalu perbaikan slang
        no_stop = self._remove_stopwords(tokens)
        fixed_slang = self._fix_slang(no_stop)
        # 6. Stemming
        return self.stemmer.stem(fixed_slang)

    def preprocess_many(self, texts: list) -> list:
        """Pra-proses daftar teks secara berurutan (mempertahankan urutan input)."""
        return [self.preprocess(t) for t in texts]
