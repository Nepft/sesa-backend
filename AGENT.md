# AGENT.md — SESA Backend

## 1. Peran dan tujuan
Kamu adalah coding agent untuk repository backend **SESA (Steam Sentiment Analyzer)**. Backend terpisah ini menyediakan API yang dipakai bersama oleh aplikasi web SESA dan aplikasi mobile Flutter. Fokus utama: API stabil, aman, terdokumentasi, dan konsisten dengan model yang telah dilatih serta diuji di Google Colab.

Fitur utama backend:
1. Analisis sentimen dari satu teks ulasan.
2. Analisis batch dari file `.csv` berisi banyak ulasan.

Backend mengurus API, validasi, preprocessing, prediksi, dan respons. UI/navigasi merupakan tanggung jawab repository web dan Flutter.

## 2. Sumber kebenaran dan batasan
- Periksa struktur repository, dokumentasi, konfigurasi, artefak model, dan kode yang ada sebelum mengedit.
- Jangan menganggap nama endpoint, nama kolom CSV, label sentimen, format model, atau struktur respons sudah ditetapkan sebelum memeriksanya.
- Ikuti model final dan pipeline eksperimen Google Colab, termasuk preprocessing, vectorizer/transformasi fitur, urutan proses, pemetaan label, serta versi library yang diperlukan.
- Jangan mengarang akurasi, hasil evaluasi, jumlah data, label, atau klaim performa.
- Jangan melatih ulang, mengganti, atau mengoptimalkan model tanpa instruksi eksplisit.
- Jika artefak model atau detail eksperimen belum tersedia, jelaskan apa yang dibutuhkan. Jangan membuat model tiruan seolah-olah model final.
- Jelaskan asumsi yang belum terkonfirmasi sebelum menerapkannya.

## 3. Lingkup pekerjaan
Termasuk: API prediksi teks tunggal dan CSV, validasi input, respons konsisten, penanganan error, pemuatan model final, pengujian, dokumentasi API, konfigurasi environment, logging aman, serta konfigurasi CORS sesuai kebutuhan klien.

Di luar lingkup kecuali diminta: UI web/Flutter, scraping ulasan, perubahan dataset/eksperimen, pelatihan ulang model, fitur bisnis baru, atau penyimpanan permanen teks ulasan tanpa kebutuhan yang jelas.

## 4. Arsitektur dan teknologi
- Pertahankan stack yang sudah ada. Jika backend belum dibuat, Python + FastAPI dapat dipertimbangkan setelah memeriksa kebutuhan repository.
- Pisahkan routing, schema/validasi, service prediksi, dan konfigurasi secara wajar.
- Hindari menumpuk seluruh logika API, parsing CSV, dan prediksi dalam satu file besar.
- Web dan Flutter harus menggunakan backend yang sama; jangan menggandakan model di klien.
- Contoh struktur awal (sesuaikan dengan kondisi nyata):

```text
SESA-Backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── schemas/
│   ├── services/predictor.py
│   └── core/
├── model/              # artefak final jika disimpan di repository
├── tests/
├── requirements.txt    # atau pyproject.toml sesuai stack
├── .env.example
├── .gitignore
├── README.md
├── AGENT.md
└── RULES.md
```

Struktur tersebut hanya contoh, bukan alasan untuk merombak proyek yang sudah berjalan.

## 5. Integrasi model
Sebelum implementasi prediksi:
1. Temukan artefak model final dan format penyimpanannya.
2. Identifikasi preprocessing, vectorizer/transformasi fitur, pemetaan label, dan versi library.
3. Pastikan implementasi mengikuti eksperimen, bukan preprocessing baru yang dibuat berdasarkan asumsi.
4. Jika pipeline final sudah menyatukan preprocessing dan model, gunakan pipeline itu jika memang artefak yang benar.
5. Uji contoh yang diketahui dari eksperimen jika tersedia.
6. Jika model gagal dimuat, laporkan kegagalan secara aman; jangan beralih diam-diam ke prediksi palsu.

Jangan menampilkan probabilitas/confidence jika model atau kontrak output tidak mendukungnya.

## 6. Kontrak API untuk web dan Flutter
- API harus independen dari platform dan digunakan bersama oleh web serta Flutter.
- Dokumentasikan metode HTTP, path, request, response, kode status, batas ukuran, dan contoh yang benar-benar sesuai implementasi.
- Validasi teks kosong, file kosong, kolom tidak sesuai, baris invalid, serta ukuran unggahan.
- Untuk hasil CSV, sertakan nomor baris atau identitas yang dapat mencocokkan hasil dengan input.
- Jangan mengubah nama field atau struktur respons secara diam-diam. Perubahan breaking harus didokumentasikan untuk kedua klien.
- Jangan menganggap contoh endpoint lama sebagai kontrak final sebelum memeriksa kode aktual.

## 7. Keamanan dan privasi
- Validasi semua input dan batasi ukuran file serta jumlah baris.
- Jangan mempercayai ekstensi file saja; jangan mengeksekusi isi unggahan.
- Cegah path traversal dan akses file arbitrer.
- Jangan commit `.env`, secret, token, kredensial, atau data sensitif. Sediakan `.env.example` berisi placeholder.
- Batasi CORS sesuai origin yang diperlukan; jangan otomatis membuka semua origin untuk produksi.
- Hindari mencatat isi ulasan, data unggahan, secret, atau informasi pribadi ke log tanpa kebutuhan yang jelas.
- Pesan error untuk klien tidak boleh membocorkan stack trace, path server, atau secret.
- Jangan menambahkan database, autentikasi, atau penyimpanan permanen tanpa kebutuhan yang jelas.

## 8. Alur kerja agent
1. Inspeksi file dan konfigurasi yang relevan.
2. Rencanakan perubahan dan risiko integrasi.
3. Implementasikan perubahan terkecil yang memenuhi tugas.
4. Jalankan tes, lint, atau type check yang tersedia.
5. Pastikan kontrak API konsisten untuk kedua klien.
6. Perbarui README/API docs dan `.env.example` bila diperlukan.
7. Laporkan file yang berubah, tes yang dijalankan, asumsi, serta pekerjaan yang masih membutuhkan input.

Jangan mengklaim tes berhasil jika belum dijalankan. Jika tidak bisa menguji, jelaskan alasannya.

## 9. Kriteria selesai
- Perubahan sesuai kebutuhan dan lingkup.
- Prediksi menggunakan artefak serta preprocessing eksperimen yang benar.
- Input invalid ditangani dengan baik.
- Kontrak API terdokumentasi dan konsisten.
- Tes relevan lulus atau keterbatasannya dilaporkan.
- Tidak ada secret atau file sementara yang tidak sengaja ditambahkan.
