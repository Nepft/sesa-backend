# SESA Backend API

Backend analisis sentimen ulasan aplikasi **Steam**, dibangun dengan **Python + FastAPI**.
Menyediakan dua fitur utama yang dipakai bersama oleh aplikasi **web** dan **Flutter**:

1. Analisis sentimen **satu teks** ulasan.
2. Analisis **batch** dari file `.csv`.

Model menggunakan pipeline eksperimen Google Colab (TF-IDF + SVM) yang diekspor sebagai
artefak `.joblib`. Label output: **`Positif`** / **`Negatif`** (klasifikasi 2 kelas).

---

## Prasyarat

- Python **3.10+** (dikembangkan & diuji pada 3.10)
- Artefak model `model/sesa_model.joblib` (lihat [Menyiapkan Artefak Model](#menyiapkan-artefak-model))

---

## Instalasi

```bash
# 1. (Disarankan) buat virtual environment
python -m venv .venv

# 2. Aktifkan virtual environment
#    Windows:
.venv\Scripts\activate
#    macOS/Linux:
source .venv/bin/activate

# 3. Install dependency
pip install -r requirements.txt
```

> **Penting:** `scikit-learn` di-pin ke versi yang sama dengan yang dipakai saat mengekspor
> artefak (saat ini **1.6.1**) agar `joblib.load` tidak gagal karena ketidakcocokan versi.

---

## Konfigurasi

Salin `.env.example` menjadi `.env` lalu sesuaikan nilainya:

```bash
cp .env.example .env
```

| Variabel | Default | Keterangan |
|---|---|---|
| `MODEL_PATH` | `model/sesa_model.joblib` | Path artefak model final |
| `MAX_UPLOAD_SIZE_BYTES` | `5242880` (5 MiB) | Batas ukuran unggahan CSV |
| `MAX_CSV_ROWS` | `5000` | Batas jumlah baris CSV |
| `CSV_TEXT_COLUMN` | `content` | Nama kolom teks pada CSV |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Asal origin yang diizinkan (JSON list) |
| `LOG_LEVEL` | `INFO` | Tingkat log |

Satu variabel dibaca langsung dari environment proses (bukan dari `.env`,
karena dipakai untuk menemukan `.env` itu sendiri): `SESA_ENV_FILE` — lokasi
alternatif berkas `.env`, untuk deployment yang menyimpan konfigurasi di luar
tree repository. Bila tidak diset, memakai `.env` di root repository.

CORS dibatasi ke origin di `CORS_ORIGINS`. **Jangan** memakai wildcard (`*`) di produksi.

---

## Menyiapkan Artefak Model

Artefak model **tidak di-commit** ke repository (lihat `.gitignore`). Untuk menyiapkannya:

1. Buka notebook eksperimen di **Google Colab** dan jalankan hingga selesai (termasuk
   pelatihan SVM pada data seimbang SMOTE + Tomek).
2. Jalankan skrip `scripts/export_model_colab.py` di Colab (sesuaikan nama variabel dengan
   notebook Anda) untuk menghasilkan `sesa_model.joblib`.
3. Unduh berkas tersebut dan letakkan di folder `model/sesa_model.joblib`.

Artefak adalah `dict` berisi: `vectorizer` (TfidfVectorizer terlatih), `model`
(SVM terlatih), `labels` (pemetaan label), dan `sklearn_version`.

Jika artefak tidak ada atau gagal dimuat, layanan **tetap berjalan** tetapi endpoint
prediksi akan menolak permintaan dengan `503` — tidak pernah menghasilkan prediksi palsu.

---

## Menjalankan Server

```bash
uvicorn app.main:app --reload
```

Server berjalan di `http://127.0.0.1:8000`. Dokumentasi interaktif (Swagger) tersedia di
`http://127.0.0.1:8000/docs`.

---

## Menjalankan Pengujian

```bash
pytest
```

Pengujian memakai **test double** (model sintetis kecil yang ditandai jelas bukan model
produksi) untuk menguji plumbing API, serta menguji perilaku model gagal dimuat. Resource
preprocessing (kamus & stopword) memakai berkas lokal yang sama dengan produksi.

---

## Endpoint

Semua endpoint memakai JSON dan bersifat independen platform (dipakai bersama web &
Flutter).

### `GET /health`

Liveness check layanan. Selalu `200` selama proses berjalan (tidak tergantung model).

**Contoh respons**
```json
{ "status": "ok" }
```

### `GET /ready`

Readiness check model.

- `200` → `{"model": "ready"}`
- `503` → `{"model": "not_ready"}`

### `POST /predict`

Analisis sentimen satu teks ulasan.

**Request**
```json
{ "text": "aplikasinya bagus dan mudah dipakai" }
```

**Respons `200`**
```json
{ "text": "aplikasinya bagus dan mudah dipakai", "label": "Positif" }
```

> Output hanya berisi `label` (`Positif`/`Negatif`). Model SVM tanpa `probability=True`
> tidak menghasilkan nilai kepercayaan, sehingga confidence tidak ditampilkan.

**Error**
- `422` — teks kosong / field hilang / melebihi batas karakter.
- `503` — model belum siap.

### `POST /predict/batch`

Analisis sentimen banyak ulasan dari file CSV (multipart upload, field `file`).

**Syarat file CSV**
- Berformat CSV, memakai pemisah koma (`,`) atau titik-koma (`;`) — dideteksi otomatis dari baris header (gaya Colab memakai `;`).
- Memiliki kolom teks (nama kolom sesuai `CSV_TEXT_COLUMN`, default `content`); pencocokan tidak memandang huruf besar/kecil.
- Baris kosong/tidak valid **dilewati**, tidak menggagalkan seluruh batch.
- Nomor baris disertakan agar hasil mudah dicocokkan dengan input.
- Ukuran file dan jumlah baris dibatasi sebelum diproses (lihat `MAX_UPLOAD_SIZE_BYTES`, `MAX_CSV_ROWS`).

**Contoh file `ulasan.csv`**
```csv
content
aplikasi ini bagus sekali
jelek parah sering error
```

**Respons `200`**
```json
{
  "total": 2,
  "results": [
    { "row": 2, "label": "Positif" },
    { "row": 3, "label": "Negatif" }
  ],
  "skipped": []
}
```

Baris yang dilewati muncul di `skipped`:
```json
{ "row": 3, "reason": "baris tidak memiliki kolom teks yang valid" }
```

**Error**
- `400` — file kosong, bukan CSV valid, kolom teks tidak ditemukan, atau tanpa baris data.
- `413` — ukuran file / jumlah baris melebihi batas.
- `415` — tipe file bukan CSV.
- `503` — model belum siap.

---

## Struktur Proyek

```text
sesa_backend/
├── app/
│   ├── main.py                  # inisialisasi aplikasi, CORS, lifespan, router
│   ├── api/
│   │   ├── dependencies.py      # dependensi akses PredictionService
│   │   └── routes/
│   │       ├── health.py        # /health, /ready
│   │       └── predict.py       # /predict, /predict/batch
│   ├── schemas/                 # skema request & response (kontrak API)
│   ├── services/
│   │   ├── preprocessing.py     # pipeline preprocessing (urutan persis Colab)
│   │   └── predictor.py         # pemuatan model & prediksi
│   └── core/
│       ├── config.py            # konfigurasi via environment
│       └── logging.py           # logging aman
├── data/                        # resource preprocessing lokal (kamus & stopword)
├── model/                       # artefak model (di-gitignore, kecuali README)
├── scripts/
│   └── export_model_colab.py    # skrip export artefak dari Colab
├── tests/                       # pengujian (pytest)
├── requirements.txt
├── .env.example
├── .gitignore
├── AGENT.md
└── RULES.md
```

---

## Catatan Integritas Model

- Pipeline preprocessing mengikuti **urutan persis** eksperimen Colab:
  cleaning → case folding → normalisasi kata → tokenisasi → stopword removal → stemming.
- Resource preprocessing (kamus kata tidak baku & stopword bahasa Indonesia) dibundel
  secara **lokal** di folder `data/` agar determinis dan tidak bergantung internet saat
  runtime.
- Model, label, threshold, vectorizer, dan preprocessing **tidak diubah** tanpa instruksi
  eksplisit. Lihat `RULES.md` §2.
