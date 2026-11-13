# Folder artefak model

Artefak model final `sesa_model.joblib` (hasil ekspor dari Colab) berada di
folder ini dan **ikut ter-commit** ke repository. Pola `model/*.joblib` di
`.gitignore` hanya mengabaikan berkas `.joblib` baru agar tidak masuk tanpa
sengaja.

Cara menghasilkan ulang artefak: jalankan `scripts/export_model_colab.py` di
Colab, lalu unduh hasilnya ke `model/sesa_model.joblib`. Pelatihan dengan
`SVC(probability=True)` diperlukan agar API menghasilkan field `confidence`.
