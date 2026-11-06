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
    # Jalur yang sama dengan jendela: keadaan panel bawaan (tampil_bm.ui_awal) lalu susun_tampil.
    # Sengaja BUKAN AD.susun() lagi, supaya .exe hasil kemasan benar-benar menguji aturan kelas dan
    # cut-off yang dipakai pemakai, bukan jalur sederhana yang hanya ada di uji.
    from . import tampil_bm as TB

    T = TB.ui_awal(bm)
    t1 = time.perf_counter()
    A, idx, lg = AD.susun_tampil(bm, T)
    ms_susun = (time.perf_counter() - t1) * 1000
    atribut = T.atribut
    k = bm.kotak()
    hasil = {
        "ok": bool(bm.n and A.n_blok == idx.size),
        "berkas": berkas.name,
        "blok": bm.n,
        "blok_digambar": A.n_blok,
        "atribut_warna": atribut,
        "kelas": [{"label": l, "warna": w, "blok": c} for l, w, c in lg],
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
    # Jumlah blok per kelas harus menjumlah tepat sama dengan blok yang digambar. Kalau tidak,
    # legenda di panel akan berbeda dari apa yang tampak di layar -- angka yang menyesatkan.
    if lg and sum(c for _l, _w, c in lg) != int(idx.size):
        hasil["ok"] = False
        hasil["galat"] = ("jumlah blok per kelas (%d) tidak sama dengan blok digambar (%d)"
                          % (sum(c for _l, _w, c in lg), int(idx.size)))
    # Laporan ikut diuji di sini supaya kemasan .exe terbukti membawa mesin hitungnya
    # (gcex_backend.laporan). Tanpa pemeriksaan ini, tab Laporan baru ketahuan kosong di tangan
    # pemakai -- modulnya ada di repo tetapi tidak ikut terkemas.
    from . import laporan_bm as LB

    try:
        PL = LB.Pilihan(kadar=atribut or "", cuts=[0.0], atribut=[atribut] if atribut else [],
                        sg=2.6, bandingkan=True)
        hl = LB.jalankan(bm, PL)
        tot = {m: LB._total((hl["metode"][m].get("rows") or [{}])[0].get("G") or {})
               for m in hl["urut"]}
        hasil["laporan"] = {m: {"blok": int(v["n"]), "volume_m3": round(v["v"], 2),
                                "tonase_t": round(v["t"], 2)} for m, v in tot.items()}
        # Volume laporan harus sama dengan volume seluruh blok yang dilaporkan; dan tonase =
        # volume x SG. Kalau tidak, pilihan salah diteruskan ke mesin hitungnya.
        v = tot["surpac"]["v"]
        if abs(tot["surpac"]["t"] - v * 2.6) > max(1.0, 1e-9 * abs(v * 2.6)):
            hasil["ok"] = False
            hasil["galat"] = "tonase laporan tidak sama dengan volume x SG"
        if tot["surpac"]["n"] != bm.n:
            hasil["ok"] = False
            hasil["galat"] = ("laporan metode Surpac melaporkan %d blok, model punya %d"
                              % (tot["surpac"]["n"], bm.n))
    except Exception as e:                      # noqa: BLE001 -- sengaja ditangkap dan dilaporkan
        hasil["ok"] = False
        hasil["galat"] = "laporan gagal: %s: %s" % (type(e).__name__, e)

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
