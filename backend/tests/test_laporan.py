# -*- coding: utf-8 -*-
"""Uji agregasi laporan Python: angka yang bisa dihitung tangan + paritas angka JS.

Laporan tonase dipakai untuk keputusan penambangan, jadi yang diuji bukan "programnya jalan"
melainkan angkanya: tonase dua blok yang diketahui ukuran dan SG-nya, kadar rata-rata yang harus
berbobot TONASE (bukan rata-rata biasa), pengaruh sb_frac, cut-off, pengelompokan per bench, dan
alasan blok terbuang.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from gcex_backend import laporan

FIX = Path(__file__).parent / "data" / "laporan_js.json"


def model(nz=2, kadar=(1.0, 3.0), sg=(2.0, 4.0), z=(100.0, 105.0), frac=None):
    """Dua blok 10 x 10 x 5 m. Angka dipilih supaya tonase & kadar berbobot mudah dihitung tangan."""
    n = len(kadar)
    B = {"x": [0.0, 20.0][:n], "y": [0.0, 0.0][:n], "z": list(z)[:n],
         "sx": [10.0] * n, "sy": [10.0] * n, "sz": [5.0] * n}
    num = {"AU": list(kadar), "SGK": list(sg)}
    if frac is not None:
        num["sb_frac"] = list(frac)
    return {"blocks": B, "off": [0.0, 0.0], "num": num}


def test_tonase_dan_kadar_berbobot_tonase():
    """Blok 500 m3: SG 2 -> 1.000 t kadar 1; SG 4 -> 2.000 t kadar 3.
    Kadar rata-rata berbobot tonase = (1000*1 + 2000*3) / 3000 = 2,3333 -- bukan 2,0."""
    d = model()
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sgCol": "SGK",
                                  "sg": 2.6, "grp": "none"}))
    r = o["rows"][0]["G"]["Total"]
    assert r["n"] == 2
    assert r["v"] == pytest.approx(1000.0)
    assert r["t"] == pytest.approx(3000.0)
    q = r["s"]["AU"]
    assert q["tw"] / q["w"] == pytest.approx(7000.0 / 3000.0, rel=1e-12)


def test_sg_tetap_dipakai_bila_tidak_ada_kolom():
    d = model(sg=(np.nan, np.nan))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.5,
                                  "grp": "none"}))
    assert o["rows"][0]["G"]["Total"]["t"] == pytest.approx(1000.0 * 2.5)


def test_sg_tidak_sah_diganti_nilai_pengganti():
    """Kolom SG berisi 0: dengan sgRep 3,0 blok itu dihitung memakai 3,0, bukan dibuang."""
    d = model(sg=(0.0, 4.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sgCol": "SGK",
                                  "sgRep": 3.0, "sg": 2.6, "grp": "none"}))
    assert o["rows"][0]["G"]["Total"]["t"] == pytest.approx(500 * 3.0 + 500 * 4.0)
    assert o["nOut"]["sg"] == 0
    # sgZero='zero' menjadikan SG 0 -> blok dibuang karena tonasenya nol
    o2 = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sgCol": "SGK",
                                   "sgZero": "zero", "sg": 2.6, "grp": "none"}))
    assert o2["nOut"]["sg"] == 1
    assert o2["rows"][0]["G"]["Total"]["n"] == 1


def test_sb_frac_menimbang_volume_dan_tonase():
    """Blok perbatasan dengan proporsi 0,25 hanya dihitung seperempat."""
    d = model(frac=(0.25, 1.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sgCol": "SGK",
                                  "sg": 2.6, "grp": "none", "frac": True}))
    r = o["rows"][0]["G"]["Total"]
    assert r["v"] == pytest.approx(500 * 0.25 + 500 * 1.0)
    assert r["t"] == pytest.approx(500 * 0.25 * 2.0 + 500 * 4.0)
    assert o["nPart"] == 1
    # pembobotan dimatikan -> blok perbatasan dihitung utuh (cara Surpac)
    o2 = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sgCol": "SGK",
                                   "sg": 2.6, "grp": "none", "frac": False}))
    assert o2["rows"][0]["G"]["Total"]["v"] == pytest.approx(1000.0)


def test_sb_frac_nol_dibuang():
    d = model(frac=(0.0, 1.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                  "grp": "none", "frac": True}))
    assert o["nOut"]["frac"] == 1 and o["nb"] == 1


def test_cut_off_menyaring_blok():
    d = model(kadar=(1.0, 3.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0, 2, 5], "sg": 2.6,
                                  "grp": "none"}))
    assert o["rows"][0]["G"]["Total"]["n"] == 2
    assert o["rows"][1]["G"]["Total"]["n"] == 1          # hanya kadar 3
    assert o["rows"][2]["G"] == {}                        # tidak ada yang >= 5


def test_kelompok_per_bench():
    """bh 5 m, bref 0: blok RL 100 dan RL 105 jatuh di bench berbeda."""
    d = model(z=(100.0, 107.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                  "grp": "bench", "bh": 5, "bref": 0}))
    G = o["rows"][0]["G"]
    assert sorted(G) == ["20", "21"]
    assert all(g["n"] == 1 for g in G.values())


def test_kadar_tidak_sah_dibuang():
    """Nilai <= -90 adalah penanda "tidak ada data" di GC-Ex, bukan kadar negatif."""
    d = model(kadar=(-99.0, 3.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                  "grp": "none"}))
    assert o["nOut"]["nan"] == 1 and o["nb"] == 1


def test_rentang_rl_dan_filter_atribut():
    d = model(z=(100.0, 200.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                  "grp": "none", "z0": 150, "z1": 250}))
    assert o["nOut"]["z"] == 1 and o["nb"] == 1
    o2 = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                   "grp": "none", "fA": "SGK", "fOp": "ge", "fV": 3.0}))
    assert o2["nOut"]["f"] == 1 and o2["nb"] == 1


def test_poligon_dalam_dan_luar():
    d = model()                                   # blok di x = 0 dan x = 20
    kotak = [[[-5.0, -5.0], [5.0, -5.0], [5.0, 5.0], [-5.0, 5.0]]]
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                  "grp": "none", "poly": kotak}))
    assert o["nb"] == 1 and o["nOut"]["poly"] == 1
    o2 = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                   "grp": "none", "poly": kotak, "polyOut": True}))
    assert o2["nb"] == 1 and o2["nOut"]["poly"] == 1      # yang terambil blok yang lain


def test_permukaan_idw_membatasi_dari_atas():
    """Topografi datar RL 102: blok pusat RL 100 tersisa, blok RL 105 di atas topografi."""
    g = np.arange(-30.0, 51.0, 5.0)
    X, Y = np.meshgrid(g, g, indexing="ij")
    topo = {"x": X.ravel().tolist(), "y": Y.ravel().tolist(),
            "z": [102.0] * X.size}
    d = model(z=(100.0, 105.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                  "grp": "none", "surf": {"atas": {"idw": topo}}}))
    assert o["nb"] == 1 and o["nOut"]["surf"] == 1


def test_dtm_tegas_membuang_blok_di_luar_jangkauan():
    """Permukaan DTM hanya menutupi satu blok; dengan batas tegas, blok di luarnya dibuang."""
    tin = {"v": [-5.0, -5.0, 102.0, 5.0, -5.0, 102.0, 5.0, 5.0, 102.0, -5.0, 5.0, 102.0],
           "t": [0, 1, 2, 0, 2, 3]}
    d = model(z=(100.0, 100.0))
    o = laporan.run(dict(d, opsi={"gr": "AU", "atts": ["AU"], "cuts": [0], "sg": 2.6,
                                  "grp": "none", "surf": {"atas": {"tin": tin, "tegas": True}}}))
    assert o["nb"] == 1 and o["nOut"]["ext"] == 1


def test_masukan_salah_ditolak():
    with pytest.raises(ValueError):
        laporan.run({"blocks": {"x": [], "y": [], "z": [], "sx": [], "sy": [], "sz": []},
                     "num": {}, "opsi": {"gr": "AU"}})
    with pytest.raises(ValueError):
        laporan.run(dict(model(), opsi={"gr": "TIDAK_ADA", "cuts": [0]}))


@pytest.mark.skipif(not FIX.exists(), reason="berkas paritas JS belum dibuat")
def test_paritas_dengan_javascript():
    """Masukan & keluaran rpRun() asli: tonase, volume, jumlah blok, kadar berbobot, dan alasan
    blok terbuang harus sama di setiap susunan constraint yang diuji."""
    d = json.loads(FIX.read_text(encoding="utf-8"))
    for ks in d["kasus"]:
        se = ks["opsi"]
        o = {"cuts": [float(c) for c in str(se.get("cuts", "0")).replace(";", ",").split(",")
                      if c.strip()],
             "gr": d["gr"], "atts": d["atts"], "grp": se.get("grp") or "none",
             "bh": se.get("bh") or 5, "bref": se.get("bref") or 0,
             "z0": se.get("z0", ""), "z1": se.get("z1", ""),
             "sg": d["sg"], "sgCol": d["sgCol"], "sgZero": d["sgZero"], "sgRep": d["sgRep"],
             "frac": se.get("frac") is not False}
        if ks.get("ovr"):
            o["surf"] = {"atas": {"tin": ks["ovr"]["atas"], "tegas": True},
                         "bawah": {"tin": ks["ovr"]["bawah"], "tegas": True}}
        if ks.get("sxT"):
            o["sx"] = [{"tin": q["tin"], "side": q["side"]} for q in ks["sxT"]]
        r = laporan.run({"blocks": d["blocks"], "off": d["off"], "num": d["num"], "opsi": o})

        assert r["nb"] == ks["nb"], "%s: jumlah blok terhitung" % ks["nama"]
        for kunci, v in ks["nOut"].items():
            assert int(v) == int(r["nOut"].get(kunci, 0)), "%s: nOut.%s" % (ks["nama"], kunci)
        assert len(r["rows"]) == len(ks["rows"]), "%s: jumlah baris cut-off" % ks["nama"]
        for rj, rp in zip(ks["rows"], r["rows"]):
            assert set(rj["G"]) == set(rp["G"]), "%s cut-off %s: grup" % (ks["nama"], rj["c"])
            for g, aj in rj["G"].items():
                ap = rp["G"][g]
                assert aj["n"] == ap["n"], "%s/%s/%s: blok" % (ks["nama"], rj["c"], g)
                assert float(ap["v"]) == pytest.approx(float(aj["v"]), rel=1e-9, abs=1e-6)
                assert float(ap["t"]) == pytest.approx(float(aj["t"]), rel=1e-9, abs=1e-6)
                for at in d["atts"]:
                    qj, qp = aj["s"].get(at), ap["s"].get(at)
                    if not qj or not qj["w"]:
                        continue
                    assert qp and qp["w"], "%s/%s/%s: kadar %s hilang" % (ks["nama"], rj["c"], g, at)
                    assert qp["tw"] / qp["w"] == pytest.approx(qj["tw"] / qj["w"], rel=1e-9,
                                                               abs=1e-9), \
                        "%s/%s/%s: kadar %s" % (ks["nama"], rj["c"], g, at)
