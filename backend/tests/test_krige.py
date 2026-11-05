# -*- coding: utf-8 -*-
"""Uji Ordinary Kriging Python: invarian yang harus benar menurut teorinya + paritas angka JS.

Invarian dipakai karena kriging mudah "jalan" tetapi salah: nilai tetap keluar walau bobotnya
keliru. Yang diuji di sini adalah sifat yang tidak bisa dilanggar -- jumlah bobot satu (tidak
bias), medan tetap menghasilkan nilai yang sama, estimasi tepat di lokasi data, batas jumlah
sampel dan batas per lubang -- lalu paritas terhadap keluaran JS yang dibekukan.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from gcex_backend import krige

FIX = Path(__file__).parent / "data" / "krige_js.json"


def model(c0=0.2, a=30.0):
    """Model isotropik ternormalkan: nugget c0 + satu struktur sferis range a."""
    return {"vM": [1, 0, 0], "vS": [0, 1, 0], "vN": [0, 0, 1],
            "c0": c0, "cs": [1.0 - c0], "A": [a], "B": [a], "Cn": [a], "R": [a, a, a]}


def komposit(n=200, lebar=50.0, seed=5, per_hole=5):
    rng = np.random.default_rng(seed)
    P = rng.uniform(-lebar, lebar, (n, 3))
    C = [{"x": float(p[0]), "y": float(p[1]), "z": float(p[2]), "id": "H%d" % (i // per_hole)}
         for i, p in enumerate(P)]
    return C


def test_kovarians_nol_dan_jauh():
    m = krige.Model(model())
    assert krige.cov(m, np.zeros((1, 3)))[0] == 1.0
    assert krige.cov(m, np.array([[1000.0, 0, 0]]))[0] == 0.0


def test_medan_tetap_menghasilkan_nilai_yang_sama():
    """Jumlah bobot kriging = 1, jadi data yang seluruhnya 7,25 harus diestimasi 7,25."""
    C = komposit()
    o = krige.run({"C": C, "z": [7.25] * len(C), "m": model(), "blocks": [[0.0, 0.0, 0.0], [10.0, -5.0, 3.0]],
                   "passes": [{"mult": 1, "min": 4, "max": 12, "mph": 0}], "bs": [5, 5, 5], "nd": [3, 3, 2]})
    assert o["n"] == 2
    for v in o["est"]:
        assert v == pytest.approx(7.25, rel=1e-9, abs=1e-9)


def test_estimasi_tepat_di_lokasi_data():
    """Dukungan titik (diskretisasi 1 x 1 x 1, blok kecil) tepat di satu komposit:
    kriging harus mengembalikan nilai komposit itu."""
    C = komposit(n=120, seed=11)
    z = list(np.linspace(1.0, 9.0, len(C)))
    i = 7
    b = [C[i]["x"], C[i]["y"], C[i]["z"]]
    o = krige.run({"C": C, "z": z, "m": model(c0=0.0), "blocks": [b],
                   "passes": [{"mult": 1, "min": 4, "max": 12, "mph": 0}],
                   "bs": [0.001, 0.001, 0.001], "nd": [1, 1, 1]})
    assert o["n"] == 1
    assert o["est"][0] == pytest.approx(z[i], rel=1e-6, abs=1e-6)
    assert o["kv"][0] == pytest.approx(0.0, abs=1e-6)       # tidak ada ketidakpastian di titik data


def test_batas_jumlah_sampel_dan_per_lubang():
    C = komposit(n=300, lebar=25.0, seed=3, per_hole=10)
    z = list(np.random.default_rng(1).normal(3, 1, len(C)))
    o = krige.run({"C": C, "z": z, "m": model(), "blocks": [[0.0, 0.0, 0.0]],
                   "passes": [{"mult": 1, "min": 4, "max": 8, "mph": 0}], "bs": [5, 5, 5], "nd": [3, 3, 2]})
    assert o["ns"][0] == 8                                   # dibatasi maks 8
    # mph = 1: tiap lubang paling banyak satu sampel -> indeks terpilih harus dari lubang berbeda
    X = np.array([c["x"] for c in C]); Y = np.array([c["y"] for c in C]); Z = np.array([c["z"] for c in C])
    H = np.array([int(c["id"][1:]) for c in C])
    m = krige.Model(model())
    I = krige.Index(X, Y, Z, 20.0)
    sel = krige.search(m, I, X, Y, Z, H, 0.0, 0.0, 0.0, 1.0, 8, 1)
    assert sel.size == len(set(H[sel].tolist()))


def test_pass_berikutnya_dipakai_bila_sampel_kurang():
    """Blok jauh dari data: pass 1 (radius kecil, min 4) gagal, pass 2 (radius besar) berhasil."""
    C = komposit(n=80, lebar=20.0, seed=9)
    z = list(np.random.default_rng(2).normal(2, 0.5, len(C)))
    jauh = [[70.0, 0.0, 0.0]]
    o = krige.run({"C": C, "z": z, "m": model(a=40.0), "blocks": jauh,
                   "passes": [{"mult": 0.5, "min": 4, "max": 8, "mph": 0},
                              {"mult": 2.5, "min": 2, "max": 12, "mph": 0}],
                   "bs": [5, 5, 5], "nd": [3, 3, 2]})
    assert o["n"] == 1
    assert o["ps"][0] == 2
    assert o["cnt"] == [0, 1]


def test_blok_tanpa_sampel_tidak_diestimasi():
    C = komposit(n=60, lebar=10.0, seed=4)
    z = [3.0] * len(C)
    o = krige.run({"C": C, "z": z, "m": model(a=20.0), "blocks": [[0.0, 0.0, 0.0], [5000.0, 0.0, 0.0]],
                   "passes": [{"mult": 1, "min": 4, "max": 12, "mph": 0}], "bs": [5, 5, 5], "nd": [3, 3, 2]})
    assert o["i"] == [0]                                     # blok kedua gagal, tidak dilaporkan
    assert o["nblok"] == 2 and o["n"] == 1


def test_masukan_salah_ditolak():
    with pytest.raises(ValueError):
        krige.run({"C": komposit(n=2), "z": [1.0, 2.0], "m": model(), "blocks": [[0, 0, 0]],
                   "passes": [{"mult": 1, "min": 1, "max": 4}]})
    with pytest.raises(ValueError):
        krige.run({"C": komposit(n=10), "z": [1.0] * 9, "m": model(), "blocks": [[0, 0, 0]],
                   "passes": [{"mult": 1, "min": 1, "max": 4}]})
    with pytest.raises(ValueError):
        krige.run({"C": komposit(n=10), "z": [1.0] * 10, "m": model(), "blocks": [[0, 0, 0]], "passes": []})


@pytest.mark.skipif(not FIX.exists(), reason="berkas paritas JS belum dibuat")
def test_paritas_dengan_javascript():
    """Masukan & keluaran asli okSearch + okKrige: pass, jumlah sampel, kadar, KV, SoR, KE,
    dan bobot negatif harus sama blok per blok."""
    d = json.loads(FIX.read_text(encoding="utf-8"))
    o = krige.run({"C": d["C"], "z": d["z"], "m": d["m"], "blocks": d["blocks"],
                   "passes": d["passes"], "bs": d["bs"], "nd": d["nd"], "cell": d["cell"]})
    assert o["cbb"] == pytest.approx(d["cbb"], rel=1e-12, abs=1e-12)
    py = {i: k for k, i in enumerate(o["i"])}
    js = {r["i"]: r for r in d["out"]}
    assert set(py) == set(js), "blok yang berhasil diestimasi tidak sama"
    for i, r in js.items():
        k = py[i]
        assert r["ps"] == o["ps"][k], "blok %d: pass" % i
        assert r["ns"] == o["ns"][k], "blok %d: jumlah sampel" % i
        for kunci in ("est", "kv", "sor", "ke", "neg"):
            assert float(r[kunci]) == pytest.approx(float(o[kunci][k]), rel=1e-9, abs=1e-9), \
                "blok %d: %s" % (i, kunci)


@pytest.mark.skipif(not FIX.exists(), reason="berkas paritas JS belum dibuat")
def test_beberapa_inti_cpu_memberi_angka_sama():
    """Blok dibagi ke beberapa proses; hasilnya harus sama persis dengan satu proses.
    Diuji karena kecepatan tidak ada gunanya kalau angkanya bergeser."""
    d = json.loads(FIX.read_text(encoding="utf-8"))
    blocks = list(d["blocks"]) * 3                      # > 2000 blok supaya pembagian aktif
    p = {"C": d["C"], "z": d["z"], "m": d["m"], "blocks": blocks,
         "passes": d["passes"], "bs": d["bs"], "nd": d["nd"], "cell": d["cell"]}
    satu = krige.run(dict(p, workers=1))
    banyak = krige.run(dict(p, workers="auto"))
    assert banyak["i"] == satu["i"]
    assert banyak["cnt"] == satu["cnt"]
    assert banyak["ns"] == satu["ns"] and banyak["ps"] == satu["ps"]
    for kunci in ("est", "kv", "sor", "ke", "neg"):
        assert np.allclose(banyak[kunci], satu[kunci], rtol=0, atol=0), kunci
