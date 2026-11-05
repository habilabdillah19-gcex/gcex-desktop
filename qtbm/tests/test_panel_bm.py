# -*- coding: utf-8 -*-
"""Uji panel tampilan block model (Qt) tanpa layar -- platform 'offscreen'.

Yang diperiksa di sini bukan rupa panelnya, melainkan APA YANG BERUBAH ketika kendalinya disentuh:
menukar atribut, melepas centang kategori, mengubah batas kelas, menyetel cut-off. Aturannya
sendiri sudah diuji di test_tampil_bm.py (dan dibandingkan dengan aplikasi HTML); di sini
dipastikan panel benar-benar meneruskan perubahan itu ke adegan, bukan hanya mengubah tampilan
kendalinya.
"""
from __future__ import annotations

import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication            # noqa: E402

from qtbm import adegan as AD                         # noqa: E402
from qtbm import tampil_bm as TB                      # noqa: E402
from qtbm.panel_bm import PanelBM                     # noqa: E402
from qtbm.proyek import BlockModel                    # noqa: E402


@pytest.fixture(scope="module")
def app():
    a = QApplication.instance() or QApplication([])
    yield a


@pytest.fixture
def bm() -> BlockModel:
    rng = np.random.default_rng(7)
    n = 400
    b = BlockModel(x=rng.uniform(0, 100, n), y=rng.uniform(0, 100, n), z=rng.uniform(0, 50, n),
                   sx=np.full(n, 2.5), sy=np.full(n, 2.5), sz=np.full(n, 2.5), nama="uji")
    b.angka["AU_GC"] = rng.lognormal(-1.0, 1.0, n)
    b.angka["SG"] = np.full(n, 2.6)
    b.kategori["DOM"] = (rng.integers(0, 2, n).astype(np.uint16), ["ORE", "WASTE"])
    return b


def test_panel_menyetel_keadaan_bawaan(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    assert p.T.atribut == "AU_GC"                 # atribut AU dipilih lebih dulu
    assert p.cmb_attr.currentText() == "AU_GC"
    assert p.T.f_atribut == "" and p.T.f_nilai == ""
    assert len(p.T.kelas_dari(bm, "AU_GC")) >= 2


def test_panel_memancarkan_sinyal_sekali_per_perubahan(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    n = []
    p.berubah.connect(lambda: n.append(1))
    p._ganti_atribut("SG")
    assert len(n) == 1 and p.T.atribut == "SG"


def test_membangun_ulang_daftar_tidak_memancarkan_sinyal_tambahan(app, bm):
    """Saat daftar kelas dibangun ulang, widget-nya ikut diubah; itu tidak boleh memicu susun
    ulang berkali-kali -- kalau iya, setiap klik akan menyusun adegan beberapa kali."""
    p = PanelBM()
    p.pasang_model(bm)
    n = []
    p.berubah.connect(lambda: n.append(1))
    p._tambah_kelas()
    assert len(n) == 1


def test_kategori_dilepas_mengurangi_blok_tampil(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    p._ganti_atribut("DOM")
    _, sebelum, _ = AD.susun_tampil(bm, p.T)
    p._set_kat("ORE", False)
    _, sesudah, _ = AD.susun_tampil(bm, p.T)
    assert sesudah.size < sebelum.size
    kode = bm.kategori["DOM"][0]
    assert sesudah.size == int(np.count_nonzero(kode == 1))


def test_cutoff_panel_sampai_ke_adegan(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    p.cmb_f.setCurrentIndex(p.cmb_f.findData("AU_GC"))
    p.cmb_op.setCurrentIndex(0)                    # >=
    p.spn_f.setValue(0.5)
    _, idx, _ = AD.susun_tampil(bm, p.T)
    assert idx.size == int(np.count_nonzero(bm.angka["AU_GC"] >= 0.5))


def test_cutoff_dikosongkan_kembali(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    p.cmb_f.setCurrentIndex(p.cmb_f.findData("AU_GC"))
    p.spn_f.setValue(0.5)
    p.spn_f.setValue(p.spn_f.minimum())            # nilai minimum = tanpa cut-off
    assert p.T.f_nilai == ""
    _, idx, _ = AD.susun_tampil(bm, p.T)
    assert idx.size == bm.n


def test_sunting_batas_kelas_mengubah_warna_blok(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    p.T.kelas["AU_GC"] = TB.kelas_dari_batas([0.5])
    p.T.kelas["AU_GC"][0].col = "#000000"
    p.T.kelas["AU_GC"][1].col = "#ffffff"
    A, idx, _ = AD.susun_tampil(bm, p.T)
    v = bm.angka["AU_GC"][idx]
    hitam = A.warna[:, :3].sum(axis=1) == 0
    assert np.array_equal(hitam, v < 0.5)


def test_opasitas_masuk_ke_alpha(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    p.spn_op.setValue(0.5)
    A, _, _ = AD.susun_tampil(bm, p.T)
    assert int(A.warna[0, 3]) == 128


def test_legenda_cocok_dengan_jumlah_blok_tampil(app, bm):
    p = PanelBM()
    p.pasang_model(bm)
    _, idx, lg = AD.susun_tampil(bm, p.T)
    assert sum(l[2] for l in lg) == idx.size
    p.lapor(int(idx.size), lg)
    assert "tampil" in p.ringkas.text()


def test_model_kosong_tidak_merusak_panel(app):
    p = PanelBM()
    p.pasang_model(None)
    assert p.T.atribut is None
    A, idx, lg = AD.susun_tampil(None, p.T)
    assert A.n_blok == 0 and idx.size == 0 and lg == []
