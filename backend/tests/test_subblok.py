# -*- coding: utf-8 -*-
"""Uji sub-blocking & sb_frac Python: sifat yang tidak boleh dilanggar + paritas angka JS.

Proporsi volume dipakai orang untuk menghitung tonase blok perbatasan, jadi yang diuji di sini
adalah hal yang bisa dihitung dengan tangan: kubus yang diketahui volumenya, blok yang jelas
seluruhnya di dalam atau di luar, blok yang tepat separuh, dan jumlah volume yang harus kekal
sesudah blok dipecah. Sesudah itu paritas terhadap keluaran JS yang dibekukan.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from gcex_backend import subblok

FIX = Path(__file__).parent / "data" / "subblok_js.json"


def kubus(x0=0.0, x1=10.0, y0=0.0, y1=10.0, z0=0.0, z1=10.0):
    """Mesh kubus tertutup (12 segitiga). Volumenya diketahui, jadi proporsinya bisa dihitung tangan."""
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    T = [(0, 2, 1), (0, 3, 2),            # bawah
         (4, 5, 6), (4, 6, 7),            # atas
         (0, 1, 5), (0, 5, 4),            # y0
         (2, 3, 7), (2, 7, 6),            # y1
         (1, 2, 6), (1, 6, 5),            # x1
         (3, 0, 4), (3, 4, 7)]            # x0
    return {"name": "kubus",
            "mesh": {"x": [v[0] for v in V], "y": [v[1] for v in V], "z": [v[2] for v in V],
                     "i": [t[0] for t in T], "j": [t[1] for t in T], "k": [t[2] for t in T]}}


def solid(**kw):
    return [subblok.Solid(kubus(**kw))]


def blok(daftar):
    """daftar: [(x,y,z,sx,sy,sz), ...] -> dict larik."""
    a = np.asarray(daftar, dtype=np.float64)
    return {"x": a[:, 0], "y": a[:, 1], "z": a[:, 2], "sx": a[:, 3], "sy": a[:, 4], "sz": a[:, 5]}


def test_titik_di_dalam_dan_di_luar_kubus():
    m = subblok.Mesh(kubus()["mesh"])
    P = np.array([[5.0, 5.0, 5.0], [5.0, 5.0, 9.9], [5.0, 5.0, 0.1],
                  [-1.0, 5.0, 5.0], [5.0, 5.0, 11.0], [5.0, 5.0, -1.0]])
    assert m.inside(P).tolist() == [True, True, True, False, False, False]


def test_kubus_tertutup_rapat():
    """Tiap sisi kubus dipakai dua segitiga, jadi tidak ada sisi terbuka."""
    assert subblok.Mesh(kubus()["mesh"]).open == 0


def test_straddle_tiga_keadaan():
    W = solid()
    s = subblok.straddle(W, *[np.asarray(v, dtype=np.float64) for v in (
        [5.0, 5.0, 50.0, 0.0],      # x: di tengah, di tengah, jauh, di tepi
        [5.0, 5.0, 50.0, 5.0],
        [5.0, 5.0, 50.0, 5.0],
        [2.0, 40.0, 2.0, 4.0],      # ukuran
        [2.0, 40.0, 2.0, 4.0],
        [2.0, 40.0, 2.0, 4.0])])
    assert s.tolist() == [1, 2, 0, 2]      # dalam, menyeberang, luar, menyeberang di tepi


def test_proporsi_blok_utuh_dan_kosong():
    W = solid()
    o = subblok.frac(W, *[np.asarray(v, dtype=np.float64) for v in (
        [5.0, 50.0], [5.0, 50.0], [5.0, 50.0], [2.0, 2.0], [2.0, 2.0], [2.0, 2.0])])
    assert o["F"].tolist() == [1.0, 0.0]
    assert o["nFull"] == 1 and o["nNol"] == 1 and o["nPart"] == 0


def test_proporsi_blok_separuh():
    """Blok 4 m berpusat tepat di bidang x = 10 (sisi kubus): separuh volumenya di dalam.
    Dengan cuplikan titik tengah, jawabannya tepat 0,5 -- bukan hampir."""
    W = solid()
    o = subblok.frac(W, np.array([10.0]), np.array([5.0]), np.array([5.0]),
                     np.array([4.0]), np.array([2.0]), np.array([2.0]), nF=10)
    assert o["nPart"] == 1
    assert o["F"][0] == pytest.approx(0.5, abs=1e-12)


def test_proporsi_sudut_seperdelapan():
    """Blok berpusat di sudut kubus (10,10,10): seperdelapan volumenya di dalam."""
    W = solid()
    o = subblok.frac(W, np.array([10.0]), np.array([10.0]), np.array([10.0]),
                     np.array([2.0]), np.array([2.0]), np.array([2.0]), nF=10)
    assert o["F"][0] == pytest.approx(0.125, abs=1e-12)


def test_volume_berbobot_mendekati_volume_kubus():
    """Kisi blok 2 m menutupi kubus 10 m: jumlah volume berbobot harus = 1.000 m3."""
    W = solid()
    g = np.arange(-1.0, 13.0, 2.0) + 1.0
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    n = X.size
    o = subblok.frac(W, X.ravel(), Y.ravel(), Z.ravel(),
                     np.full(n, 2.0), np.full(n, 2.0), np.full(n, 2.0), nF=12)
    vol = float(np.sum(2.0 * 2.0 * 2.0 * o["F"]))
    assert vol == pytest.approx(1000.0, rel=2e-3)


def test_dua_solid_digabung():
    """Titik di dalam SALAH SATU solid dihitung di dalam (sama dengan perulangan di JS)."""
    W = [subblok.Solid(kubus()), subblok.Solid(kubus(x0=20.0, x1=30.0))]
    o = subblok.frac(W, np.array([5.0, 25.0, 15.0]), np.array([5.0, 5.0, 5.0]),
                     np.array([5.0, 5.0, 5.0]), *[np.full(3, 2.0)] * 3)
    assert o["F"].tolist() == [1.0, 1.0, 0.0]


def test_pecah_hanya_blok_perbatasan_dan_volume_kekal():
    W = solid()
    B = blok([(5.0, 5.0, 5.0, 2.0, 2.0, 2.0),      # seluruhnya di dalam -> tidak dipecah
              (50.0, 50.0, 50.0, 2.0, 2.0, 2.0),   # jauh di luar -> tidak dipecah
              (10.0, 5.0, 5.0, 4.0, 4.0, 4.0)])    # di perbatasan -> dipecah
    v0 = float(np.sum(B["sx"] * B["sy"] * B["sz"]))
    r = subblok.pecah(W, B, lv=2, lim=[1.0, 1.0, 1.0])
    assert r["nAsal"] == 3 and r["nStr"] == 1
    assert r["n"] > 3                                          # ada yang dipecah
    v1 = float(np.sum(r["sx"] * r["sy"] * r["sz"]))
    assert v1 == pytest.approx(v0, rel=1e-12)                  # volume total kekal
    # blok anak tetap tercatat berasal dari blok induknya
    assert sorted(set(r["src"].tolist())) == [0, 1, 2]


def test_pecah_menghormati_blok_yang_sudah_halus():
    """Blok yang sudah lebih kecil dari batas minimum tidak dipecah lagi (sub-blok Surpac)."""
    W = solid()
    B = blok([(10.0, 5.0, 5.0, 1.0, 1.0, 1.0)])
    r = subblok.pecah(W, B, lv=1, lim=[5.0, 5.0, 5.0])
    assert r["n"] == 1 and r["nSplit"] == 0 and r["nSudah"] == 1


def test_masukan_salah_ditolak():
    with pytest.raises(ValueError):
        subblok.run({"solids": [], "blocks": {"x": [0], "y": [0], "z": [0],
                                              "sx": [1], "sy": [1], "sz": [1]}})
    with pytest.raises(ValueError):
        subblok.run({"solids": [kubus()], "blocks": {"x": [0, 1], "y": [0], "z": [0],
                                                     "sx": [1], "sy": [1], "sz": [1]}})
    with pytest.raises(ValueError):
        subblok.Mesh({"x": [], "y": [], "z": [], "i": [], "j": [], "k": []})


@pytest.mark.skipif(not FIX.exists(), reason="berkas paritas JS belum dibuat")
def test_paritas_dengan_javascript():
    """Mesh solid & blok asli dari aplikasi: proporsi sb_frac tiap blok harus sama dengan JS.
    Toleransi 1e-6 karena JS menyimpan sb_frac sebagai Float32Array."""
    d = json.loads(FIX.read_text(encoding="utf-8"))
    o = subblok.run({"solids": d["solids"], "blocks": d["blocks"], "mode": "frac", "nF": d["N"]})
    FJ = np.asarray(d["F"], dtype=np.float64)
    FP = np.asarray(o["F"], dtype=np.float64)
    assert FJ.size == FP.size
    assert np.allclose(FP, FJ, rtol=1e-6, atol=1e-6)
    # penggolongan blok (seluruhnya di luar / seluruhnya di dalam / perbatasan) harus sama pula;
    # dihitung dari kedua larik dengan cara yang sama supaya setara walau berkasnya cuplikan
    for nama, a, b in (("di luar", np.count_nonzero(FJ == 0), np.count_nonzero(FP == 0)),
                       ("utuh", np.count_nonzero(FJ == 1), np.count_nonzero(FP == 1)),
                       ("perbatasan", np.count_nonzero((FJ > 0) & (FJ < 1)),
                        np.count_nonzero((FP > 0) & (FP < 1)))):
        assert a == b, "jumlah blok %s beda: JS %d, Python %d" % (nama, a, b)
    # volume ore berbobot atas blok yang sama
    B = d["blocks"]
    v = np.asarray(B["sx"]) * np.asarray(B["sy"]) * np.asarray(B["sz"])
    assert float(np.sum(v * FP)) == pytest.approx(float(np.sum(v * FJ)), rel=1e-6)


@pytest.mark.skipif(not FIX.exists(), reason="berkas paritas JS belum dibuat")
def test_beberapa_inti_cpu_memberi_angka_sama():
    """Blok dibagi ke beberapa proses: proporsi tiap blok dan cacahnya harus sama persis."""
    d = json.loads(FIX.read_text(encoding="utf-8"))
    B = d["blocks"]
    besar = {k: list(B[k]) * 4 for k in ("x", "y", "z", "sx", "sy", "sz")}   # > 10.000 blok
    p = {"solids": d["solids"], "blocks": besar, "mode": "frac", "nF": d["N"]}
    satu = subblok.run(dict(p, workers=1))
    banyak = subblok.run(dict(p, workers="auto"))
    assert np.array_equal(np.asarray(banyak["F"]), np.asarray(satu["F"]))
    for k in ("nPart", "nFull", "nNol"):
        assert banyak[k] == satu[k], k
    assert banyak["vol"] == pytest.approx(satu["vol"], rel=0, abs=0)
