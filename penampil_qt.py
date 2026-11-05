# -*- coding: utf-8 -*-
"""Titik masuk penampil block model 3D Qt untuk kemasan PyInstaller.

Berkas ini ada karena PyInstaller mengemas skrip yang ditunjuknya sebagai modul TINGKAT ATAS,
sehingga impor relatif di dalam qtbm/__main__.py (`from . import adegan`) tidak berlaku lagi.
Di sini impornya mutlak, jadi hasil kemasan berjalan sama seperti `python -m qtbm`.

Pemakaian sama:
    GC-Ex-BlockModel-3D.exe [folder_proyek] [block_model.csv]
    GC-Ex-BlockModel-3D.exe --periksa <block_model.csv> [hasil.json]
"""
import multiprocessing
import sys

if __name__ == "__main__":
    # wajib pada kemasan PyInstaller di Windows bila suatu saat memakai multiprocessing
    multiprocessing.freeze_support()
    if "--periksa" in sys.argv:
        from qtbm.__main__ import periksa
        raise SystemExit(periksa(sys.argv[1:]))
    from qtbm.tampilan import jalankan
    raise SystemExit(jalankan(sys.argv))
