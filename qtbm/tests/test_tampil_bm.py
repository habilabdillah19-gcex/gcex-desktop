# -*- coding: utf-8 -*-
"""Uji aturan tampilan block model: pembulatan batas kelas, kelas, cut-off, warna, legenda.

Dua lapis:
  1. uji satuan atas hal-hal yang MUDAH salah kalau ditulis ulang -- pembulatan 2 angka berarti,
     batas kelas lo <= v < hi, nilai tak sah yang tidak digambar, kategori kosong;
  2. uji paritas atas berkas beku `data/tampil_bm_js.json` -- hasil `bxCls`/`bxClassOf`/`bxSel`
     aplikasi HTML sungguhan pada data latihan. Berkas itu dibuat
     `python tools/uji/paritas_tampil_bm.py --fixture`; ia ada di repo supaya CI menangkap
     pergeseran aturan tanpa perlu peramban.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from qtbm import tampil_bm as TB
from qtbm.proyek import BlockModel

BEKU = Path(__file__).parent / "data" / "tampil_bm_js.json"


def model(nilai, kat=None) -> BlockModel:
    v = np.asarray(nilai, dtype=float)
    n = v.size
    satu = np.ones(n)
    bm = BlockModel(x=np.arange(n, dtype=float), y=np.zeros(n), z=np.zeros(n),
                    sx=satu * 2, sy=satu * 2, sz=satu * 2, nama="uji")
    bm.angka["AU"] = v
    if kat is not None:
        kode, daftar = kat
        bm.kategori["DOM"] = (np.asarray(kode, dtype=np.uint16), list(daftar))
    return bm


# --------------------------------------------------------------- pembulatan
@pytest.mark.parametrize("v,harap", [
    (0.0123, 0.012), (1234, 1200.0), (0.9999, 1.0), (0.0, 0.0),
    # nilai tepat setengah: JavaScript membulatkan KE ATAS, bukan ke angka genap.
    # Di sinilah '%.1e' milik Python akan salah (menghasilkan 1.2 / 0.12 / 0.062).
    (1.25, 1.3), (0.125, 0.13), (0.0625, 0.063), (-1.25, -1.3),
])
def test_dua_angka_berarti(v, harap):
    assert TB.dua_angka_berarti(v) == pytest.approx(harap)


def test_kelas_otomatis_memakai_kuantil_cuplikan():
    v = np.arange(1, 101, dtype=float)          # 1..100
    L = TB.kelas_otomatis(v)
    # kuantil JS: v[floor(p*(n-1))] -> p=.5 -> v[49]=50, .75 -> v[74]=75, .9 -> v[89]=90,
    # .97 -> v[96]=97, masing-masing dibulatkan ke 2 angka berarti
    assert [c.hi for c in L[:-1]] == [50.0, 75.0, 90.0, 97.0]
    assert L[0].lo is None and L[-1].hi is None
    assert [c.col for c in L] == TB.PALET[:5]


def test_batas_kembar_dibuang():
    # seluruh nilai sama -> keempat kuantil sama -> hanya satu batas -> dua kelas
    L = TB.kelas_otomatis(np.full(50, 0.4))
    assert len(L) == 2 and L[0].hi == 0.4


# --------------------------------------------------------------- kelas & cut-off
def test_batas_atas_terbuka():
    """Nilai yang TEPAT sama dengan batas masuk kelas di atasnya (lo <= v < hi)."""
    bm = model([0.0, 0.5, 0.999, 1.0, 1.5])
    T = TB.Tampilan(atribut="AU")
    T.kelas["AU"] = TB.kelas_dari_batas([0.5, 1.0])
    k = TB.kelas_blok(bm, T)
    assert list(k) == [0, 1, 1, 2, 2]


def test_nilai_tak_sah_tidak_digambar():
    bm = model([0.2, np.nan, 0.8, np.inf])
    T = TB.Tampilan(atribut="AU")
    T.kelas["AU"] = TB.kelas_dari_batas([0.5])
    idx, cl = TB.pilih(bm, T)
    assert list(idx) == [0, 2] and list(cl) == [0, 1]


def test_nilai_di_luar_semua_kelas_tidak_digambar():
    """Kelas manual bisa menyisakan lubang; blok di lubang itu hilang dari tampilan."""
    bm = model([0.1, 5.0])
    T = TB.Tampilan(atribut="AU")
    T.kelas["AU"] = [TB.Kelas(0.0, 1.0, "#111111")]        # 5.0 tidak masuk kelas mana pun
    idx, _ = TB.pilih(bm, T)
    assert list(idx) == [0]


@pytest.mark.parametrize("op,nilai,harap", [
    ("ge", "0.5", [1, 2]), ("lt", "0.5", [0]), ("ge", "", [0, 1, 2]), ("none", "0.5", [0, 1, 2]),
])
def test_cutoff_tampilan(op, nilai, harap):
    bm = model([0.2, 0.5, 0.9])
    T = TB.Tampilan(atribut="AU", f_atribut="AU", f_op=op, f_nilai=nilai)
    T.kelas["AU"] = TB.kelas_dari_batas([1.0])
    idx, _ = TB.pilih(bm, T)
    assert list(idx) == harap


def test_cutoff_membuang_nilai_tak_sah():
    bm = model([np.nan, 0.9])
    T = TB.Tampilan(atribut="AU", f_atribut="AU", f_op="lt", f_nilai="99")
    T.kelas["AU"] = TB.kelas_dari_batas([1.0])
    assert list(TB.pilih(bm, T)[0]) == [1]


def test_saringan_luar_ikut_dipakai():
    bm = model([0.2, 0.5, 0.9])
    T = TB.Tampilan(atribut="AU")
    T.kelas["AU"] = TB.kelas_dari_batas([1.0])
    idx, _ = TB.pilih(bm, T, pakai=np.array([True, False, True]))
    assert list(idx) == [0, 2]


# --------------------------------------------------------------- kategori
def test_kategori_kosong_dan_centang():
    bm = model([0.1, 0.2, 0.3], kat=([0, 1, TB.KODE_KOSONG], ["ORE", "WASTE"]))
    T = TB.Tampilan(atribut="DOM")
    assert list(TB.pilih(bm, T)[0]) == [0, 1]              # kode kosong tidak digambar
    T.kat_on["DOM"] = {"ORE": False}
    assert list(TB.pilih(bm, T)[0]) == [1]
    # belum pernah disentuh = tampil (bukan tersembunyi)
    T.kat_on["DOM"] = {}
    assert list(TB.pilih(bm, T)[0]) == [0, 1]


def test_warna_kategori_tetap_setelah_dipilih():
    bm = model([0.1, 0.2], kat=([0, 1], ["ORE", "WASTE"]))
    T = TB.Tampilan(atribut="DOM")
    w = T.warna_kategori(bm, "DOM", 0)
    assert w == TB.PALET_KAT[0]
    T.warna_kat["DOM"]["ORE"] = "#ff0000"
    assert T.warna_kategori(bm, "DOM", 0) == "#ff0000"


# --------------------------------------------------------------- warna & legenda
def test_warna_per_blok_dan_opasitas():
    bm = model([0.2, 0.9])
    T = TB.Tampilan(atribut="AU", opasitas=0.5)
    T.kelas["AU"] = TB.kelas_dari_batas([0.5])
    idx, cl = TB.pilih(bm, T)
    W = TB.warna_per_blok(bm, T, cl)
    assert W.shape == (2, 4) and W[0, 3] == 128
    assert tuple(W[0, :3]) == TB.rgb(TB.PALET[0])
    assert tuple(W[1, :3]) == TB.rgb(TB.PALET[1])


def test_legenda_mencacah_blok_tampil():
    bm = model([0.2, 0.3, 0.9])
    T = TB.Tampilan(atribut="AU")
    T.kelas["AU"] = TB.kelas_dari_batas([0.5])
    idx, cl = TB.pilih(bm, T)
    lg = TB.legenda(bm, T, cl)
    assert [(l[0], l[2]) for l in lg] == [("< 0.5", 2), ("≥ 0.5", 1)]


def test_label_kelas():
    L = TB.kelas_dari_batas([0.5, 1.0])
    assert [c.label() for c in L] == ["< 0.5", "0.5 – 1", "≥ 1"]


def test_ui_awal_memilih_au_dan_menyalakan_cutoff_pada_model_besar():
    bm = model([0.1, 0.2])
    bm.angka["SG"] = np.array([2.6, 2.6])
    bm.angka["AU_GC"] = bm.angka.pop("AU")
    T = TB.ui_awal(bm)
    assert T.atribut == "AU_GC" and T.f_atribut == "" and T.f_nilai == ""
    # model besar: cut-off dinyalakan sendiri di 0,01
    bm.x = np.zeros(300_001)
    for a in ("SG", "AU_GC"):
        bm.angka[a] = np.zeros(300_001)
    T2 = TB.ui_awal(bm)
    assert T2.f_atribut == "AU_GC" and T2.f_nilai == "0.01"


# --------------------------------------------------------------- penyuntingan kelas
def test_sunting_batas_menggeser_kelas_sebelah():
    bm = model([0.1, 0.6, 2.0])
    T = TB.Tampilan(atribut="AU")
    T.kelas["AU"] = TB.kelas_dari_batas([0.5, 1.0])
    T.set_batas(bm, "AU", 1, "lo", 0.4)
    L = T.kelas["AU"]
    assert L[0].hi == 0.4 and L[1].lo == 0.4            # tanpa celah
    T.tambah_kelas(bm, "AU")
    assert len(L) == 4 and L[-1].hi is None
    T.hapus_kelas(bm, "AU", 0)
    assert T.kelas["AU"][0].lo is None                  # kelas pertama tetap terbuka ke bawah


# --------------------------------------------------------------- paritas berkas beku
@pytest.mark.skipif(not BEKU.exists(), reason="berkas paritas JS belum dibuat")
def test_paritas_dengan_js_beku():
    d = json.loads(BEKU.read_text(encoding="utf-8"))
    bm = BlockModel(
        x=np.array(d["x"], float), y=np.array(d["y"], float), z=np.array(d["z"], float),
        sx=np.array(d["sx"], float), sy=np.array(d["sy"], float), sz=np.array(d["sz"], float),
        nama=d.get("nama", ""))
    for a, v in d["num"].items():
        bm.angka[a] = np.array(v, float)
    for a, c in d["cat"].items():
        bm.kategori[a] = (np.array(c["kode"], dtype=np.uint16), list(c["dict"]))

    b = d["bawaan"]
    T0 = TB.ui_awal(bm)
    assert (T0.atribut, T0.f_atribut, str(T0.f_nilai)) == (b["attr"], b["fAttr"], str(b["fVal"]))

    for ks in d["kasus"]:
        T = TB.ui_awal(bm)
        T.atribut = ks["ui"]["attr"]
        T.f_atribut = ks["ui"]["fAttr"]
        T.f_op = ks["ui"]["fOp"]
        T.f_nilai = ks["ui"]["fVal"]
        if ks["nama"] == "kelas manual":
            T.kelas[T.atribut] = [TB.Kelas(c["lo"], c["hi"], c["col"]) for c in ks["kelas"]]
        elif ks.get("kelas"):
            L = T.kelas_dari(bm, T.atribut)
            assert len(L) == len(ks["kelas"]), ks["nama"]
            for p, j in zip(L, ks["kelas"]):
                assert p.lo == pytest.approx(j["lo"]) if j["lo"] is not None else p.lo is None
                assert p.hi == pytest.approx(j["hi"]) if j["hi"] is not None else p.hi is None
                assert p.col == j["col"] and p.label() == j["lab"], ks["nama"]
        if ks.get("lepas") is not None:
            T.kat_on[T.atribut] = {ks["lepas"]: False}

        assert np.array_equal(TB.kelas_blok(bm, T), np.array(ks["kelas_semua"], dtype=np.int32)), \
            "kelas per blok berbeda: %s" % ks["nama"]
        idx, cl = TB.pilih(bm, T)
        assert np.array_equal(idx, np.array(ks["idx"], dtype=np.int64)), ks["nama"]
        assert np.array_equal(cl, np.array(ks["cl"], dtype=np.int64)), ks["nama"]
