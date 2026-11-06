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

    # Dig block ikut diuji di sini supaya kemasan .exe terbukti membawa mesinnya dan ekspornya.
    # Tanpa pemeriksaan ini, tab Dig block baru ketahuan gagal di tangan pemakai -- dan kalau yang
    # gagal adalah ekspornya, yang dibawa ke lapangan adalah berkas kosong.
    from . import galian as GA
    from . import string_io as SIO

    try:
        _x0, _x1, _y0, _y1, _z0, z1 = k
        tebal = float(min(bm.sz))
        O = GA.Opsi(rl_atas=z1, rl_bawah=z1 - tebal, kadar=atribut or "", waste_on=False)
        # poligon seluruh hamparan model: seluruh blok flitch teratas harus ikut
        P = [(_x0, _y0), (_x1, _y0), (_x1, _y1), (_x0, _y1)]
        H = GA.bandingkan(bm, P, T, O)
        hasil["galian"] = {m: {"blok": v.n, "volume_m3": round(v.v, 2),
                               "tonase_t": round(v.t, 2),
                               "menutup_pct": round(v.cov * 100, 1)} for m, v in H.items()}
        # Volume metode Surpac = jumlah volume blok yang titik tengahnya ada di flitch teratas.
        # Dihitung sendiri di sini, bukan diambil dari mesinnya, supaya benar-benar memeriksa.
        import numpy as _np
        di_flitch = (_np.asarray(bm.z) > (z1 - tebal) + 1e-9) & (_np.asarray(bm.z) <= z1 + 1e-9)
        vol = float((_np.asarray(bm.sx) * _np.asarray(bm.sy)
                     * _np.asarray(bm.sz))[di_flitch].sum())
        if abs(H["surpac"].v - vol) > max(1e-6, 1e-9 * vol):
            hasil["ok"] = False
            hasil["galat"] = ("volume dig block Surpac %.3f tidak sama dengan volume blok flitch "
                              "%.3f" % (H["surpac"].v, vol))
        if H["clip"].n == 0 or H["surpac"].n == 0:
            hasil["ok"] = False
            hasil["galat"] = "dig block tidak kena satu blok pun: ruang koordinat tidak cocok"
        # ekspor: isi berkas harus benar-benar terbentuk, bukan hanya tidak melempar galat
        S = [SIO.String(no=1, ket="ORE", tertutup=True,
                        pts=[(p[0], p[1], z1 - tebal / 2) for p in P])]
        t_str = SIO.teks_str(S, bm.nama or "GCEX")
        t_dxf = SIO.teks_dxf(S)
        hasil["ekspor"] = {"str_baris": len(t_str.splitlines()),
                           "dxf_baris": len(t_dxf.splitlines())}
        if not t_str.rstrip().endswith("END") or "EOF" not in t_dxf:
            hasil["ok"] = False
            hasil["galat"] = "ekspor string tidak lengkap (.str tanpa END atau .dxf tanpa EOF)"
        # Penyimpanan ke folder proyek: tulis lalu baca lagi, dan koordinatnya harus kembali
        # TEPAT. Ini yang menyelamatkan pekerjaan satu shift, jadi tidak cukup "tidak melempar".
        import tempfile as _tf

        from . import simpan_galian as SG

        with _tf.TemporaryDirectory() as _td:
            SG.tulis(_td, S, 504000.0, 9011000.0, nama_proyek="uji kemasan")
            S2, _meta = SG.baca(_td)
            cocok = (len(S2) == len(S)
                     and all(abs(a - b) <= 1e-9
                             for p, q in zip(S[0].pts, S2[0].pts) for a, b in zip(p, q)))
            hasil["simpan"] = {"string": len(S2), "hash_kosong": SG.hash_fp(""), "cocok": cocok}
            if not cocok:
                hasil["ok"] = False
                hasil["galat"] = "simpan lalu baca string tidak memberi koordinat yang sama"
            # hash harus sama dengan FP.hash aplikasi HTML; nilai untuk teks kosong tetap
            if SG.hash_fp("") != "811c9dc5-1000193-0":
                hasil["ok"] = False
                hasil["galat"] = "hash berkas berbeda dari FP.hash aplikasi HTML"
    except Exception as e:                          # noqa: BLE001 -- sengaja ditangkap dan dilaporkan
        hasil["ok"] = False
        hasil["galat"] = "dig block gagal: %s: %s" % (type(e).__name__, e)

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
