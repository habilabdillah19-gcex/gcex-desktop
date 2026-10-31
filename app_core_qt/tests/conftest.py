"""Penyiapan bersama uji Qt Core-Ex.

Tugas latar (mis. pemeriksaan Ollama lewat util.run_bg) bisa selesai SETELAH jendela uji ditutup.
Kalau hasilnya tiba saat uji berikutnya sedang menjalankan event loop, slot-nya menyentuh widget yang
objek C++-nya sudah dihapus -> RuntimeError "Internal C++ object already deleted" ditangkap pytest-qt
sebagai SETUP ERROR uji berikutnya. Karena itu setiap uji ditutup dengan menguras thread pool dan
memproses sisa event, supaya uji tidak saling mengganggu.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtCore import QCoreApplication, QThreadPool  # noqa: E402


@pytest.fixture(autouse=True)
def _tiriskan_tugas_latar():
    yield
    QThreadPool.globalInstance().waitForDone(5000)
    app = QCoreApplication.instance()
    if app is not None:
        for _ in range(3):
            app.processEvents()
            app.sendPostedEvents(None, 0)
