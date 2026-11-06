# -*- coding: utf-8 -*-
"""Uji sayatan (qtbm/sayatan.py) dan panelnya.

Paritas terhadap `secK()` + `bxSlabHit()` ASLI aplikasi HTML dijalankan ulang dari hasil JS yang
dibekukan di `data/sayatan_bm_js.json`, jadi CI memeriksanya tanpa peramban.

Yang paling dijaga di sini: uji KOTAK vs uji TITIK TENGAH. Aplikasi HTML menguji blok sebagai
kotak; memakai titik tengah membuat sayatan Qt menampilkan jauh lebih sedikit blok pada slab tipis,
tanpa galat apa pun dan tanpa ada yang menduga sebabnya.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from qtbm import sayatan as SY
from qtbm.proyek import BlockModel, Bor, Proyek

BEKU = Path(__file__).parent / "data" / "sayatan_bm_js.json"


def _bm(nx=6, ny=6, nz=4, s=5.0, sz=2.5, x0=500000.0, y0=9000000.0, z0=100.0):
    X, Y, Z = [], [], []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                X.append(x0 + (i + 0.5) * s)
                Y.append(y0 + (j + 0.5) * s)
                Z.append(z0 + (k + 0.5) * sz)
    n = len(X)
    return BlockModel(x=np.array(X), y=np.array(Y), z=np.array(Z),
                      sx=np.full(n, s), sy=np.full(n, s), sz=np.full(n, sz), nama="UJI")


# ---------------------------------------------------------------- bidang

def test_bidang_h():
    g = SY.bidang(_bm(), SY.Opsi(mode="H"))
    assert g.m == "H" and g.n == (0.0, 0.0, 1.0)


def test_bidang_x_pusat_nol():
    """Qt memakai koordinat PENUH, jadi pusat bidang nol -- bukan [-offX, 0, 0] seperti HTML."""
    g = SY.bidang(_bm(), SY.Opsi(mode="X"))
    assert g.c == (0.0, 0.0, 0.0)
    assert g.n == (1.0, 0.0, 0.0)


def test_bidang_p_menghitung_azimut_dan_ruas():
    O = SY.Opsi(mode="P", titik1=(0.0, 0.0), titik2=(100.0, 0.0), dip=90.0)
    g = SY.bidang(_bm(), O)
    assert g.az == pytest.approx(90.0)          # ke timur
    assert g.seg == pytest.approx(100.0)


def test_bidang_p_meneruskan_panjang_ruas():
    """Penjaga bug nyata: panjang ruas pernah dihitung lalu tidak diteruskan ke hasil."""
    O = SY.Opsi(mode="P", titik1=(0.0, 0.0), titik2=(30.0, 40.0))
    assert SY.bidang(_bm(), O).seg == pytest.approx(50.0)


def test_bidang_p_dua_titik_sama_tidak_memberi_ruas():
    O = SY.Opsi(mode="P", titik1=(10.0, 10.0), titik2=(10.0, 10.0))
    assert SY.bidang(_bm(), O).seg is None


def test_bidang_dip_dijepit():
    assert SY.bidang(_bm(), SY.Opsi(mode="A", dip=200.0)).dip == 90.0
    assert SY.bidang(_bm(), SY.Opsi(mode="A", dip=-5.0)).dip == 0.0


def test_pusat_z_diambil_dari_opsi():
    O = SY.Opsi(mode="A", pusat_z=777.0)
    assert SY.bidang(_bm(), O).c[2] == pytest.approx(777.0)


def test_pusat_z_bawaan_tengah_model():
    bm = _bm(nz=4, sz=2.5, z0=100.0)             # blok 100..110, tengah 105
    g = SY.bidang(bm, SY.Opsi(mode="A"))
    _x0, _x1, _y0, _y1, z0, z1 = bm.kotak()
    assert g.c[2] == pytest.approx((z0 + z1) / 2.0)


# ---------------------------------------------------------------- slab

def test_slab_satu_batas_pada_mode_h():
    assert len(SY.slab(_bm(), SY.Opsi(mode="H", pos=105.0, tebal=5.0)).batas) == 1


def test_slab_dua_batas_bila_ruas_dibatasi():
    O = SY.Opsi(mode="P", titik1=(0.0, 0.0), titik2=(100.0, 0.0), batasi_ruas=True)
    assert len(SY.slab(_bm(), O).batas) == 2


def test_slab_tanpa_ruas_tidak_menambah_batas():
    O = SY.Opsi(mode="P", titik1=(0.0, 0.0), titik2=(0.0, 0.0), batasi_ruas=True)
    assert len(SY.slab(_bm(), O).batas) == 1


def test_tebal_minimum_dijaga():
    assert SY.slab(_bm(), SY.Opsi(tebal=0.0)).tebal == pytest.approx(0.1)


def test_tebal_tidak_sah_jadi_lima():
    assert SY.slab(_bm(), SY.Opsi(tebal=float("nan"))).tebal == pytest.approx(5.0)


# ---------------------------------------------------------------- pemilihan blok

def test_uji_kotak_memilih_lebih_banyak_daripada_titik_tengah():
    """Inti perbedaan: slab lebih tipis daripada satu blok."""
    bm = _bm(nz=4, sz=2.5, z0=100.0)             # bidang tengah blok lapis pertama = 101,25
    O = SY.Opsi(mode="H", pos=102.5, tebal=0.2)  # tepat di batas dua lapis
    kotak = int(SY.dalam_slab(bm, O).sum())
    titik = int(SY.dalam_slab_titik(bm, O).sum())
    assert kotak > titik
    assert titik == 0


def test_uji_kotak_satu_lapis():
    bm = _bm(nx=4, ny=4, nz=4, sz=2.5, z0=100.0)
    O = SY.Opsi(mode="H", pos=101.25, tebal=0.1)
    assert int(SY.dalam_slab(bm, O).sum()) == 16      # satu lapis 4x4


def test_slab_di_luar_model_kosong():
    bm = _bm()
    assert int(SY.dalam_slab(bm, SY.Opsi(mode="H", pos=99999.0, tebal=5.0)).sum()) == 0


def test_mode_x_memilih_satu_kolom():
    bm = _bm(nx=6, ny=6, nz=1, s=5.0, x0=500000.0)
    # kolom pertama berpusat di 500002,5; slab tipis di situ harus memilih 6 blok (satu baris y)
    O = SY.Opsi(mode="X", pos=500002.5, tebal=0.1)
    assert int(SY.dalam_slab(bm, O).sum()) == 6


def test_batas_ruas_memotong_ujung():
    bm = _bm(nx=10, ny=3, nz=1, s=5.0, x0=0.0, y0=0.0)
    # ruas sengaja LEBIH PENDEK daripada modelnya; kalau sepanjang model, batas ruas tidak
    # memotong apa pun dan ujinya lulus tanpa menguji apa pun
    P = dict(mode="P", pos=0.0, tebal=100.0, dip=90.0,
             titik1=(12.5, 7.5), titik2=(27.5, 7.5))
    tanpa = int(SY.dalam_slab(bm, SY.Opsi(**P, batasi_ruas=False)).sum())
    dengan = int(SY.dalam_slab(bm, SY.Opsi(**P, batasi_ruas=True)).sum())
    assert dengan < tanpa, "batas ruas tidak memotong apa pun: ujinya hampa"


def test_perpanjangan_menambah_blok():
    bm = _bm(nx=10, ny=3, nz=1, s=5.0, x0=0.0, y0=0.0)
    P = dict(mode="P", pos=0.0, tebal=100.0, dip=90.0,
             titik1=(10.0, 7.5), titik2=(30.0, 7.5), batasi_ruas=True)
    a = int(SY.dalam_slab(bm, SY.Opsi(**P, perpanjang=0.0)).sum())
    b = int(SY.dalam_slab(bm, SY.Opsi(**P, perpanjang=20.0)).sum())
    assert b > a


def test_model_kosong_tidak_melempar():
    bm = BlockModel(x=np.zeros(0), y=np.zeros(0), z=np.zeros(0),
                    sx=np.zeros(0), sy=np.zeros(0), sz=np.zeros(0))
    assert SY.dalam_slab(bm, SY.Opsi()).size == 0


# ---------------------------------------------------------------- rentang & label

def test_rentang_pos_mode_h_adalah_rl_model():
    bm = _bm()
    _x0, _x1, _y0, _y1, z0, z1 = bm.kotak()
    assert SY.rentang_pos(bm, SY.Opsi(mode="H")) == (pytest.approx(z0), pytest.approx(z1))


def test_pos_awal_nol_pada_mode_miring():
    assert SY.pos_awal(_bm(), SY.Opsi(mode="P", titik1=(0, 0), titik2=(1, 1))) == 0.0
    assert SY.pos_awal(_bm(), SY.Opsi(mode="A")) == 0.0


def test_pos_awal_tengah_pada_mode_h():
    bm = _bm()
    lo, hi = SY.rentang_pos(bm, SY.Opsi(mode="H"))
    assert SY.pos_awal(bm, SY.Opsi(mode="H")) == pytest.approx(round((lo + hi) / 2.0))


def test_label_menyebut_tebal():
    t = SY.label(_bm(), SY.Opsi(mode="H", pos=105.0, tebal=2.5))
    assert "105" in t and "2.5" in t


def test_label_mode_p_menyebut_ruas():
    O = SY.Opsi(mode="P", titik1=(0.0, 0.0), titik2=(100.0, 0.0), batasi_ruas=True)
    t = SY.label(_bm(), O)
    assert "ruas" in t and "dibatasi" in t


# ---------------------------------------------------------------- RL data bor

def test_rl_data_dari_collar_dan_ujung():
    P = Proyek()
    P._bor = Bor(id=["h1", "h2"],
                 titik=[np.array([[0.0, 0.0, 300.0], [0.0, 0.0, 250.0]]),
                        np.array([[5.0, 5.0, 310.0], [5.0, 5.0, 200.0]])])
    assert P.rl_data() == (pytest.approx(200.0), pytest.approx(310.0))


def test_rl_data_none_tanpa_bor():
    P = Proyek()
    P.data = {}
    assert P.rl_data() is None


# ---------------------------------------------------------------- panel

def test_panel_hanya_menawarkan_mode_yang_ada_di_aplikasi():
    """Penjaga: menambah mode memaksa keputusan paritas lebih dulu, bukan diam-diam."""
    pytest.importorskip("PySide6")
    from qtbm.panel_sayatan import MODE_PANEL
    assert MODE_PANEL == ("H", "P"), (
        "aplikasi Block Model hanya menawarkan mode H dan P; mode lain di secGeom tidak bisa "
        "dicapai dari antarmukanya sehingga tidak ada perilaku yang bisa dicocokkan")


def test_panel_berdiri_dan_memberi_topeng():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from qtbm.panel_sayatan import PanelSayatan

    QApplication.instance() or QApplication([])
    bm = _bm()
    Pn = PanelSayatan()
    Pn.pasang_model(bm, (200.0, 300.0))
    t = Pn.topeng()
    assert t is not None and t.size == bm.n
    Pn.cb_potong.setChecked(False)
    assert Pn.topeng() is None


def test_panel_memakai_rl_data_sebagai_pusat():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from qtbm.panel_sayatan import PanelSayatan

    QApplication.instance() or QApplication([])
    Pn = PanelSayatan()
    Pn.pasang_model(_bm(), (200.0, 300.0))
    assert Pn.opsi().pusat_z == pytest.approx(250.0)
    assert "data bor" in Pn.lbl_pusat.text()


def test_panel_tanpa_rl_data_mengatakannya():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from qtbm.panel_sayatan import PanelSayatan

    QApplication.instance() or QApplication([])
    Pn = PanelSayatan()
    Pn.pasang_model(_bm(), None)
    assert Pn.opsi().pusat_z is None
    assert "tanpa data bor" in Pn.lbl_pusat.text()


# ---------------------------------------------------------------- paritas JS

def _muat():
    if not BEKU.exists():
        pytest.skip("hasil JS belum dibekukan; jalankan tools/uji/paritas_sayatan_bm.py")
    return json.loads(BEKU.read_text(encoding="utf-8"))


def test_fixture_memuat_kedua_mode():
    d = _muat()
    mode = {k["set"].get("sMode") for k in d["kasus"]}
    assert mode == {"H", "P"}
    assert d.get("modeTersedia") == ["H", "P"], (
        "daftar mode di aplikasi berubah: %r — putuskan paritasnya sebelum menambah mode di panel"
        % (d.get("modeTersedia"),))


def test_fixture_membedakan_kotak_dan_titik_tengah():
    """Penjaga: tanpa kasus yang membedakan keduanya, uji kotak tidak teruji."""
    d = _muat()
    beda = [k for k in d["kasus"]
            if len(k.get("kotak") or []) != len(k.get("titik") or [])]
    assert beda, "tidak ada kasus di mana uji kotak dan uji titik tengah berbeda"


def test_paritas_dengan_bxslabhit_aplikasi_html():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "uji"))
    import paritas_sayatan_bm as PS

    d = _muat()
    salah = PS.bandingkan(d)
    assert not salah, "sayatan Qt berbeda dari aplikasi HTML:\n" + "\n".join(salah)
