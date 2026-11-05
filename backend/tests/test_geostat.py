# -*- coding: utf-8 -*-
"""Uji geostatistik Python: invarian yang jawabannya diketahui + paritas terhadap angka JS.

Dua lapis:
  1. Invarian -- hal yang bisa dihitung tangan (gamma satu pasangan, jendela lag & sudut,
     downhole hanya satu lubang, pemulihan range dari data sintetis).
  2. Paritas -- berkas contoh berisi MASUKAN dan KELUARAN JS yang diambil dari aplikasi
     sungguhan (tools/uji/paritas_geostat.py --fixture). Dipakai agar pemindahan perhitungan
     ke Python tidak pernah mengubah angka yang sudah tercetak di buku tutorial, tanpa perlu
     menjalankan browser di CI.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from gcex_backend import geostat

FIX = Path(__file__).parent / "data" / "geostat_js.json"


def P(**kw):
    p = {"lag": 10.0, "nl": 5, "lt": 0.5, "at": 22.5, "bw": 1e9, "dlag": 1.0, "dnl": 5,
         "minP": 1, "ns": 0, "B": [2.5, 60.0], "BD": [0.5, 6.0]}
    p.update(kw)
    return p


def test_satu_pasangan():
    """gamma = (dv^2)/2 untuk satu pasangan, h = jaraknya."""
    C = [{"x": 0, "y": 0, "z": 0, "id": "A", "d": 0}, {"x": 10, "y": 0, "z": 0, "id": "B", "d": 0}]
    o = geostat.run({"C": C, "z": [1.0, 3.0], "P": P(), "u": [1, 0, 0], "w": [0, 1, 0], "fit": False})
    assert o["E"]["O"] == [{"h": 10.0, "g": 2.0, "n": 1}]
    assert o["E"]["D"][0] == [{"h": 10.0, "g": 2.0, "n": 1}]      # arah 0 derajat
    assert o["E"]["DH"] == []                                      # lubang berbeda


def test_toleransi_lag_membuang_pasangan():
    """|h - k*lag| <= lt*lag: jarak 16 m dengan lag 10 dan lt 0,5 masih masuk lag 2 (|16-20|=4<=5),
    tetapi jarak 15,5 m dengan lt 0,4 (toleransi 4 m) tidak masuk."""
    C = [{"x": 0, "y": 0, "z": 0, "id": "A", "d": 0}, {"x": 16, "y": 0, "z": 0, "id": "B", "d": 0}]
    o = geostat.run({"C": C, "z": [0.0, 2.0], "P": P(), "u": [1, 0, 0], "w": [0, 1, 0], "fit": False})
    assert [e["n"] for e in o["E"]["O"]] == [1]
    C2 = [{"x": 0, "y": 0, "z": 0, "id": "A", "d": 0}, {"x": 15.5, "y": 0, "z": 0, "id": "B", "d": 0}]
    o2 = geostat.run({"C": C2, "z": [0.0, 2.0], "P": P(lt=0.4), "u": [1, 0, 0], "w": [0, 1, 0], "fit": False})
    assert o2["E"]["O"] == []


def test_jendela_sudut_dan_bandwidth():
    """Pasangan pada 20 derajat masuk arah 0,5,10,15,20,25,30,35,40 (toleransi 22,5),
    dan tidak masuk arah 45 derajat ke atas."""
    h = 20.0
    a = math.radians(20.0)
    C = [{"x": 0, "y": 0, "z": 0, "id": "A", "d": 0},
         {"x": h * math.cos(a), "y": h * math.sin(a), "z": 0, "id": "B", "d": 0}]
    o = geostat.run({"C": C, "z": [0.0, 1.0], "P": P(lag=20.0), "u": [1, 0, 0], "w": [0, 1, 0], "fit": False})
    isi = [j for j in range(36) if o["E"]["D"][j]]
    assert isi == [0, 1, 2, 3, 4, 5, 6, 7, 8]                      # 0..40 derajat
    # bandwidth 1 m: hanya arah yang hampir tepat yang lolos (h*sin(da) <= 1)
    o2 = geostat.run({"C": C, "z": [0.0, 1.0], "P": P(lag=20.0, bw=1.0), "u": [1, 0, 0], "w": [0, 1, 0], "fit": False})
    isi2 = [j for j in range(36) if o2["E"]["D"][j]]
    assert isi2 == [4]                                             # 20 derajat saja


def test_downhole_hanya_lubang_sama():
    C = [{"x": 0, "y": 0, "z": 0, "id": "A", "d": 0}, {"x": 0, "y": 0, "z": -1, "id": "A", "d": 1},
         {"x": 50, "y": 0, "z": 0, "id": "B", "d": 0}]
    o = geostat.run({"C": C, "z": [1.0, 2.0, 5.0], "P": P(dlag=1.0), "u": [1, 0, 0], "w": [0, 1, 0], "fit": False})
    assert [e["n"] for e in o["E"]["DH"]] == [1]
    assert o["E"]["DH"][0]["g"] == pytest.approx(0.5)              # (2-1)^2 / 2


def test_fit_memulihkan_range_sferis():
    """Data sintetis dari model sferis murni (nugget 0): fitting harus menemukan range
    yang dekat dengan range sebenarnya."""
    E = [{"h": h, "g": geostat.gam(h, 0.0, [1.0], [60.0]), "n": 100} for h in range(5, 101, 5)]
    r = geostat.fit_r(E, 0.0, [1.0], 10, [2.5, 150.0])
    assert r is not None
    assert r[0] == pytest.approx(60.0, rel=0.06)


def test_sph_dan_gam():
    assert geostat.sph(0.0, 10.0) == 0.0
    assert geostat.sph(10.0, 10.0) == 1.0
    assert geostat.sph(5.0, 10.0) == pytest.approx(1.5 * 0.5 - 0.5 * 0.125)
    assert geostat.gam(0.0, 0.3, [0.7], [50.0]) == 0.0              # h = 0 -> 0, bukan nugget
    assert geostat.gam(1e9, 0.3, [0.7], [50.0]) == pytest.approx(1.0)


def test_komposit_kurang_dari_dua_ditolak():
    with pytest.raises(ValueError):
        geostat.run({"C": [{"x": 0, "y": 0, "z": 0, "id": "A", "d": 0}], "z": [1.0], "P": P()})
    with pytest.raises(ValueError):
        geostat.run({"C": [{"x": 0, "y": 0, "z": 0, "id": "A", "d": 0}], "z": [1.0, 2.0], "P": P()})


@pytest.mark.skipif(not FIX.exists(), reason="berkas paritas JS belum dibuat")
def test_paritas_dengan_javascript():
    """Masukan & keluaran asli dari aplikasi: tiap lag (36 arah + omni + downhole) dan seluruh
    parameter model harus sama."""
    d = json.loads(FIX.read_text(encoding="utf-8"))
    out = geostat.run({"C": d["C"], "z": d["z"], "P": d["P"], "u": d["u"], "w": d["w"],
                       "sill": d["sill"], "fit": True})

    def sama(js, py, nama):
        assert len(js) == len(py), "%s: jumlah lag %d != %d" % (nama, len(js), len(py))
        for i, (a, b) in enumerate(zip(js, py)):
            assert int(a[2]) == b["n"], "%s lag %d: pasangan %s != %s" % (nama, i + 1, a[2], b["n"])
            assert a[0] == pytest.approx(b["h"], rel=1e-9, abs=1e-9), "%s lag %d: h" % (nama, i + 1)
            assert a[1] == pytest.approx(b["g"], rel=1e-9, abs=1e-9), "%s lag %d: gamma" % (nama, i + 1)

    sama(d["E"]["O"], out["E"]["O"], "omni")
    sama(d["E"]["DH"], out["E"]["DH"], "downhole")
    for j in range(36):
        sama(d["E"]["D"][j], out["E"]["D"][j], "arah %d" % (j * 5))

    M, Mp = d["M"], out["M"]
    assert M["pitch"] == Mp["pitch"]
    assert M["c0"] == pytest.approx(Mp["c0"], rel=1e-9, abs=1e-12)
    for k in ("c", "a", "b", "d"):
        for i in (0, 1):
            assert M[k][i] == pytest.approx(Mp[k][i], rel=1e-9, abs=1e-12), "model %s[%d]" % (k, i)
