"""Skrip export artefak model final untuk Google Colab.

Cara pakai (jalankan di Colab setelah seluruh notebook eksperimen selesai,
tepat setelah model SVM pada data seimbang (SMOTE + Tomek) selesai dilatih):

    1. Sesuaikan nama variabel di bawah dengan variabel yang ada di notebook
       Anda (tfidf_vectorizer, model SVM balanced, dll).
    2. Jalankan sel ini. Artefak `sesa_model.joblib` akan tersimpan.
    3. Unduh artefak tersebut ke komputer, lalu letakkan di folder
       `model/` pada repository backend ini.

Artefak yang dihasilkan adalah dict berisi:
    - vectorizer : TfidfVectorizer terlatih (max_features=2500)
    - model      : SVC(kernel='linear') terlatih pada data seimbang
    - labels     : urutan pemetaan label model
    - sklearn_version : versi scikit-learn saat export (harus cocok dengan
                        requirements.txt agar joblib.load kompatibel)

Penting: versi scikit-learn yang dipakai mengekspor HARUS sama dengan yang
tercantum di requirements.txt (saat ini 1.6.1) untuk menghindari error
kompatibilitas joblib.
"""
from __future__ import annotations

import joblib
import sklearn


# ==== SESUAIKAN NAMA VARIABEL INI DENGAN NOTEBOOK ANDA ====
# tfidf_vectorizer : objek TfidfVectorizer yang sudah fit (max_features=2500)
# svm_balanced     : objek SVC(kernel='linear') yang sudah dilatih pada
#                    X_train_balanced / y_train_balanced (hasil SMOTE + Tomek)
# ==================================================================


def build_bundle(tfidf_vectorizer, svm_balanced, labels=("Negatif", "Positif")):
    """Kemas vectorizer + model + metadata menjadi satu bundle joblib."""
    return {
        "vectorizer": tfidf_vectorizer,
        "model": svm_balanced,
        "labels": list(labels),
        "sklearn_version": sklearn.__version__,
    }


def export(tfidf_vectorizer, svm_balanced, out_path="sesa_model.joblib"):
    """Bangun bundle lalu simpan ke `out_path`. Kembalikan path artefak."""
    bundle = build_bundle(tfidf_vectorizer, svm_balanced)
    joblib.dump(bundle, out_path)
    print(f"Artefak model tersimpan di: {out_path}")
    print(f"sklearn_version: {sklearn.__version__}")
    return out_path


# ---- Contoh pemakaian di Colab ( uncomment & sesuaikan ) ----
# from google.colab import files
# export(tfidf_vectorizer, svm_balanced, "sesa_model.joblib")
# files.download("sesa_model.joblib")
