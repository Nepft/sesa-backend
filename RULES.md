# RULES.md — Aturan Pengembangan SESA Backend

Aturan ini berlaku untuk setiap perubahan di repository backend SESA.

## 1. Prioritas
1. Jaga kesesuaian model dengan eksperimen Google Colab.
2. Jaga kontrak API konsisten untuk web dan Flutter.
3. Utamakan keamanan input dan stabilitas layanan.
4. Buat perubahan kecil, mudah diuji, dan terdokumentasi.

## 2. Integritas model — wajib
- **DILARANG** mengganti model final, algoritma, label, threshold, vectorizer, atau preprocessing tanpa instruksi eksplisit.
- **DILARANG** membuat prediksi hardcoded, acak, berbasis aturan, atau palsu untuk menggantikan model produksi.
- **DILARANG** mengarang metrik, akurasi, confidence, atau hasil pengujian.
- **DILARANG** mengubah urutan preprocessing tanpa bukti kesetaraan dengan eksperimen.
- Jika artefak model atau spesifikasi belum tersedia, jangan berpura-pura integrasi selesai. Jelaskan kebutuhan dan tandai bagian yang belum selesai.
- Test double hanya boleh dipakai untuk tes terisolasi dan harus jelas bukan model produksi.

## 3. Aturan API
- Setiap endpoint harus memiliki tujuan dan dokumentasi yang jelas.
- Validasi request/response menggunakan mekanisme yang sesuai dengan stack proyek.
- Gunakan kode status HTTP yang sesuai untuk input invalid, file tidak didukung, model belum siap, dan error internal.
- Respons error harus konsisten dan tidak mengandung stack trace.
- Jangan mengubah nama field, format JSON, label sentimen, atau bentuk hasil CSV secara diam-diam.
- Perubahan breaking harus dijelaskan dan dikoordinasikan dengan repository web serta Flutter.
- Jangan menambah endpoint yang tidak terkait tanpa kebutuhan jelas.
- Bedakan health check layanan dari kesiapan model jika model dapat gagal dimuat.

## 4. Aturan CSV
- Validasi format, struktur, encoding, kolom, ukuran file, dan jumlah baris.
- Jangan mengasumsikan nama kolom sebelum spesifikasi proyek diperiksa.
- Tetapkan penanganan delimiter, header, nilai kosong, dan baris invalid secara eksplisit.
- Jangan mengubah urutan baris tanpa alasan; sertakan nomor baris/ID agar hasil cocok dengan input.
- Satu baris invalid tidak boleh menggagalkan seluruh batch kecuali perilaku itu terdokumentasi.
- Jangan menyimpan unggahan lebih lama dari yang diperlukan.
- Batasi penggunaan memori untuk file besar dan jangan mengembalikan data yang tidak diperlukan.

## 5. Kualitas kode
- Ikuti gaya dan struktur repository yang ada.
- Gunakan nama fungsi dan variabel yang jelas.
- Pisahkan routing, validasi, konfigurasi, parsing, dan prediksi secara wajar.
- Hindari duplikasi preprocessing antara prediksi teks dan CSV.
- Tangani error secara eksplisit; jangan memakai catch/except luas tanpa alasan dan logging yang aman.
- Hindari dependency baru jika dependency yang ada cukup.
- Jangan mengubah file yang tidak relevan atau menonaktifkan tes/lint agar build terlihat berhasil.

## 6. Konfigurasi dan secret
- Gunakan environment variables atau sistem konfigurasi proyek.
- Commit `.env.example`, bukan `.env` dengan nilai asli.
- Abaikan secret, log sensitif, cache, virtual environment, unggahan, dan file sementara melalui `.gitignore` bila sesuai.
- Jangan menampilkan secret di log, dokumentasi, atau respons API.
- Hindari path absolut komputer developer; buat lokasi artefak dapat dikonfigurasi jika diperlukan.

## 7. Keamanan
- Validasi dan batasi semua input.
- Jangan mengeksekusi atau mengimpor kode dari file unggahan.
- Jangan membuka filesystem berdasarkan path yang dikirim klien.
- Konfigurasikan CORS untuk origin yang diperlukan; wildcard produksi membutuhkan alasan dan persetujuan.
- Jangan mengklaim autentikasi tersedia jika belum diimplementasikan.
- Jangan menambahkan database atau arsip ulasan tanpa kebutuhan jelas.
- Log harus membantu diagnosis tanpa membocorkan data pengguna atau detail internal.

## 8. Pengujian
Tambahkan/perbarui tes yang relevan untuk:
- Model berhasil dan gagal dimuat.
- Teks valid dan teks kosong.
- Label output sesuai pemetaan model final.
- CSV valid, file kosong, header/kolom salah, encoding bermasalah, dan nilai kosong.
- File atau jumlah baris melewati batas.
- Bentuk respons sukses dan error.
- Error internal tidak membocorkan stack trace.

Jalankan tes, lint, atau type check yang tersedia. Laporkan perintah dan hasilnya. Jika tes tidak dapat dijalankan, jelaskan alasannya.

## 9. Dokumentasi dan integrasi
- README menjelaskan prasyarat, instalasi, konfigurasi, cara menjalankan server, tes, dan endpoint.
- Contoh request/response harus sesuai implementasi aktual.
- Jelaskan cara menyiapkan artefak model tanpa membocorkan data sensitif.
- Dokumentasikan perubahan API yang memengaruhi web dan Flutter.
- Jangan menyebut fitur siap produksi sebelum diuji dan dikonfigurasi dengan benar.

## 10. Git dan perubahan
- Jangan menghapus/menimpa file penting tanpa memeriksa kegunaannya.
- Jangan melakukan reset, force push, atau menghapus riwayat tanpa instruksi eksplisit.
- Jangan commit dataset besar, cache, environment, hasil build, atau file sementara tanpa alasan.
- Periksa diff sebelum menyelesaikan tugas.
- Jika menemukan kebutuhan perubahan di repository lain, jelaskan sebagai tindak lanjut; jangan mengubahnya diam-diam.

## 11. Checklist sebelum selesai
- [ ] Struktur repository dan kebutuhan sudah diperiksa.
- [ ] Perubahan sesuai lingkup.
- [ ] Model/preprocessing tidak berubah tanpa izin.
- [ ] Validasi dan error handling diperiksa.
- [ ] Kontrak API dan dokumentasi konsisten.
- [ ] Tes relevan dijalankan atau keterbatasannya dilaporkan.
- [ ] Tidak ada secret/data/file sementara yang ikut ter-commit.
- [ ] Ringkasan perubahan, hasil tes, asumsi, dan tindak lanjut disampaikan.
