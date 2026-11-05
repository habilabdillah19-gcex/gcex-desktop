# -*- coding: utf-8 -*-
"""Titik masuk penampil Qt.

    python -m qtbm [folder_proyek] [block_model.csv]       buka jendela
    python -m qtbm --periksa <block_model.csv> [hasil.json]  uji mandiri, tanpa jendela

Mode --periksa dipakai CI untuk menguji hasil kemasan .exe: ia memuat block model, menyusun
adegan, lalu menulis ringkasannya. Tidak membuka jendela dan tidak menyentuh OpenGL, karena
runner Windows tidak punya kartu grafis -- yang diuji di situ adalah bahwa .exe-nya utuh
(pustaka ikut terkemas, berkas terbaca, angka masuk akal).
"""
import json
import sys
import time
from pathlib import Path


def periksa(argv) -> int:
    from . import adegan as AD
    from . import proyek as PR

    sisa = [a for a in argv if not a.startswith("--")]
    if not sisa:
        print("pemakaian: --periksa <block_model.csv> [hasil.json]", file=sys.stderr)
        return 2
    berkas = Path(sisa[0])
    keluar = Path(sisa[1]) if len(sisa) > 1 else None
    t0 = time.perf_counter()
    bm = PR.baca_bm(berkas)
    ms_baca = (time.perf_counter() - t0) * 1000
    atribut = sorted(bm.angka)[0] if bm.angka else None
    t1 = time.perf_counter()
    A = AD.susun(bm, atribut=atribut)
    ms_susun = (time.perf_counter() - t1) * 1000
    k = bm.kotak()
    hasil = {
        "ok": bool(bm.n and A.n_blok == bm.n),
        "berkas": berkas.name,
        "blok": bm.n,
        "blok_digambar": A.n_blok,
        "atribut_angka": sorted(bm.angka),
        "atribut_kategori": sorted(bm.kategori),
        "kotak": [round(v, 2) for v in k],
        "volume_m3": round(bm.volume(), 1),
        "asal_lokal": list(A.asal),
        "ms_baca": round(ms_baca),
        "ms_susun": round(ms_susun),
    }
    # Pemeriksaan isi, bukan sekadar "tidak melempar galat": jumlah instans harus sama dengan
    # jumlah blok, dan koordinat yang sudah digeser harus kecil (bukti penggeseran bekerja).
    besar = max(abs(v) for v in A.kotak) if A.n_blok else 0.0
    hasil["koordinat_adegan_maks"] = round(besar, 2)
    if A.n_blok and besar > 1e5:
        hasil["ok"] = False
        hasil["galat"] = "koordinat adegan masih besar (%.0f): penggeseran ke asal lokal gagal" % besar
    if not bm.angka:
        hasil["ok"] = False
        hasil["galat"] = "block model tanpa atribut angka"
    teks = json.dumps(hasil, indent=2, ensure_ascii=False)
    print(teks)
    if keluar:
        keluar.write_text(teks, encoding="utf-8")
    return 0 if hasil["ok"] else 1


if __name__ == "__main__":
    if "--periksa" in sys.argv:
        raise SystemExit(periksa(sys.argv[1:]))
    from .tampilan import jalankan
    raise SystemExit(jalankan(sys.argv))
