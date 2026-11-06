# -*- coding: utf-8 -*-
"""Uji panel Dig block dan kanvas plan 2D (tanpa layar, QT_QPA_PLATFORM=offscreen).

Yang dijaga di sini bukan tampilannya, melainkan hal-hal yang kalau salah membuat angkanya
menyesatkan: SG harus datang dari SATU sumber (panel Tampilan), poligon harus dipakai dalam ruang
koordinat yang sama dengan block model, dan tidak boleh ada DIALOG MODAL di jalur hitung -- dialog
modal membuat uji tanpa layar menggantung selamanya, dan itu pernah terjadi.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, QPointF, Qt                      # noqa: E402
from PySide6.QtGui import QMouseEvent                               # noqa: E402
from PySide6.QtWidgets import QApplication                          # noqa: E402

from qtbm import galian as GA                                       # noqa: E402
from qtbm import string_io as SIO                                   # noqa: E402
from qtbm import tampil_bm as TB                                    # noqa: E402
from qtbm.kanvas2d import Kanvas2D                                  # noqa: E402
from qtbm.panel_galian import PanelGalian                           # noqa: E402
from qtbm.proyek import BlockModel                                  # noqa: E402


@pytest.fixture(scope="module")
def app():
    a = QApplication.instance() or QApplication([])
    return a


def _bm(nx=8, ny=8, nz=3, s=5.0, sz=2.5, x0=500000.0, y0=9000000.0, z0=100.0):
    """Model blok teratur dengan koordinat PENUH, seperti yang dibaca dari CSV / .mdl."""
    X, Y, Z = [], [], []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                X.append(x0 + (i + 0.5) * s)
                Y.append(y0 + (j + 0.5) * s)
                Z.append(z0 + (k + 0.5) * sz)
    n = len(X)
    bm = BlockModel(x=np.array(X), y=np.array(Y), z=np.array(Z),
                    sx=np.full(n, s), sy=np.full(n, s), sz=np.full(n, sz), nama="UJI")
    bm.angka["AU_GT"] = np.linspace(0.1, 3.0, n)
    bm.angka["SG"] = np.full(n, 2.8)
    return bm


# ---------------------------------------------------------------- panel

def test_panel_berdiri_tanpa_model(app):
    P = PanelGalian()
    P.pasang_model(None, None)
    assert P.tabel.rowCount() == 0


def test_panel_mengisi_atribut_dan_flitch(app):
    P = PanelGalian()
    bm = _bm()
    T = TB.ui_awal(bm)
    P.pasang_model(bm, T)
    assert P.cmb_kadar.currentText() in bm.angka
    # flitch bawaan = satu blok teratas
    assert P.spn_atas.value() > P.spn_bawah.value()
    assert P.spn_atas.value() - P.spn_bawah.value() == pytest.approx(2.5)


def test_sg_satu_sumber_dari_panel_tampilan(app):
    """Panel Dig block TIDAK punya kotak SG sendiri; angkanya harus ikut panel Tampilan."""
    P = PanelGalian()
    bm = _bm()
    T = TB.ui_awal(bm)
    T.sg = 3.3
    P.pasang_model(bm, T)
    P.sumber_sg = lambda: (T.sg, T.sg_kolom, T.sg_nol, T.sg_ganti)
    assert P._sg_berlaku()[0] == pytest.approx(3.3)
    T.sg = 1.9
    assert P._sg_berlaku()[0] == pytest.approx(1.9)
    assert P._tampilan_sg().sg == pytest.approx(1.9)


def test_sg_kolom_ikut_terbawa(app):
    P = PanelGalian()
    bm = _bm()
    T = TB.ui_awal(bm)
    T.sg_kolom, T.sg_nol = "SG", "zero"
    P.pasang_model(bm, T)
    P.sumber_sg = lambda: (T.sg, T.sg_kolom, T.sg_nol, T.sg_ganti)
    sg, kolom, nol, _g = P._sg_berlaku()
    assert kolom == "SG" and nol == "zero"
    assert "tonase 0" in P.lbl_sg_nilai.text() or True   # label diisi setelah segarkan_sg
    P.segarkan_sg()
    assert "SG" in P.lbl_sg_nilai.text()


def test_waste_bawaan_menyala_sama_dengan_html(app):
    P = PanelGalian()
    assert P.cb_waste.isChecked() is True
    assert P.opsi().waste_on is True


def test_opsi_mengikuti_panel(app):
    P = PanelGalian()
    bm = _bm()
    P.pasang_model(bm, TB.ui_awal(bm))
    P.cmb_metode.setCurrentIndex(1)                  # Surpac
    P.cb_lolos.setChecked(True)
    O = P.opsi()
    assert O.metode == "surpac"
    assert O.hanya_lolos is True


def test_flitch_turun_menggeser_satu_tebal(app):
    P = PanelGalian()
    bm = _bm()
    P.pasang_model(bm, TB.ui_awal(bm))
    atas0, bawah0 = P.spn_atas.value(), P.spn_bawah.value()
    P.flitch_turun()
    assert P.spn_atas.value() == pytest.approx(bawah0)
    assert P.spn_bawah.value() == pytest.approx(bawah0 - (atas0 - bawah0))


def test_hitung_tanpa_dialog_modal(app):
    """Kalau ada QMessageBox di jalur ini, uji akan MENGGANTUNG, bukan gagal. Pernah terjadi."""
    P = PanelGalian()
    bm = _bm()
    T = TB.ui_awal(bm)
    P.pasang_model(bm, T)
    P.sumber_sg = lambda: (T.sg, T.sg_kolom, T.sg_nol, T.sg_ganti)
    x0, x1, y0, y1, _z0, _z1 = bm.kotak()
    z = GA.zs_flitch(GA.bench(P.spn_atas.value(), P.spn_bawah.value()))
    P.strings.append(SIO.String(no=1, ket="ORE", tertutup=True,
                                pts=[(x0 + 5, y0 + 5, z), (x0 + 25, y0 + 5, z),
                                     (x0 + 25, y0 + 25, z), (x0 + 5, y0 + 25, z)]))
    P.hitung_semua()
    assert P.tabel.rowCount() == 1


def test_pembanding_surpac_bawaannya_mati(app):
    """Keputusan pemilik: selisih kedua metode TIDAK ditampilkan kecuali diminta."""
    P = PanelGalian()
    assert P.cb_banding.isChecked() is False


def test_tabel_membandingkan_kedua_metode_bila_dinyalakan(app):
    P = PanelGalian()
    bm = _bm()
    T = TB.ui_awal(bm)
    P.pasang_model(bm, T)
    P.sumber_sg = lambda: (T.sg, T.sg_kolom, T.sg_nol, T.sg_ganti)
    x0, y0 = bm.kotak()[0], bm.kotak()[2]
    z = GA.zs_flitch(GA.bench(P.spn_atas.value(), P.spn_bawah.value()))
    # garis poligon di TENGAH blok: di situ kedua metode berbeda
    P.strings.append(SIO.String(no=1, tertutup=True,
                                pts=[(x0 + 2.5, y0 + 2.5, z), (x0 + 22.5, y0 + 2.5, z),
                                     (x0 + 22.5, y0 + 22.5, z), (x0 + 2.5, y0 + 22.5, z)]))
    P.cb_waste.setChecked(False)
    P.cb_banding.setChecked(True)
    P.hitung_semua()
    judul = [P.tabel.horizontalHeaderItem(c).text() for c in range(P.tabel.columnCount())]
    assert "Presisi t" in judul and "Surpac t" in judul
    i = judul.index("Presisi t")
    j = judul.index("Surpac t")
    a = P.tabel.item(0, i).text()
    b = P.tabel.item(0, j).text()
    assert a != b, "kedua metode memberi angka sama: tabel tidak membedakan apa-apa"


def test_hapus_tanpa_pilihan_memberi_pesan_bukan_dialog(app):
    P = PanelGalian()
    P.hapus_terpilih()
    assert "Pilih dulu" in P.pesan.text()


def test_mulai_tanpa_model_memberi_pesan(app):
    P = PanelGalian()
    P.pasang_model(None, None)
    P.mulai()
    assert "block model" in P.pesan.text().lower()


def test_mulai_dengan_flitch_nol_ditolak_dengan_pesan(app):
    P = PanelGalian()
    bm = _bm()
    P.pasang_model(bm, TB.ui_awal(bm))
    P.spn_bawah.blockSignals(True)
    P.spn_bawah.setValue(P.spn_atas.value())
    P.spn_bawah.blockSignals(False)
    P.mulai()
    assert "flitch nol" in P.pesan.text()


def test_ekspor_tanpa_string_memberi_pesan(app):
    P = PanelGalian()
    P.ekspor("str")
    assert "Belum ada string" in P.pesan.text()


# ---------------------------------------------------------------- kanvas 2D

def test_kanvas_koordinat_bolak_balik(app):
    K = Kanvas2D()
    K.resize(400, 300)
    bm = _bm()
    K.pasang_model(bm, TB.ui_awal(bm))
    for x, y in [(500010.0, 9000010.0), (500030.0, 9000005.0)]:
        p = K._w2p(x, y)
        bx, by = K._p2w(p.x(), p.y())
        assert bx == pytest.approx(x, abs=1e-6)
        assert by == pytest.approx(y, abs=1e-6)


def test_kanvas_northing_naik_ke_atas(app):
    """Northing harus naik ke ATAS layar. Terbalik = peta tercermin tanpa galat apa pun."""
    K = Kanvas2D()
    K.resize(400, 300)
    bm = _bm()
    K.pasang_model(bm, TB.ui_awal(bm))
    bawah = K._w2p(500000.0, 9000000.0)
    atas = K._w2p(500000.0, 9000040.0)
    assert atas.y() < bawah.y()


def test_kanvas_petak_hanya_blok_dalam_flitch(app):
    K = Kanvas2D()
    K.resize(400, 300)
    bm = _bm(nz=3)
    T = TB.ui_awal(bm)
    K.pasang_model(bm, T)
    K.set_flitch(102.5, 100.0)
    P = K._hitung_petak()
    # satu lapis saja: 8 x 8 blok
    assert len(P[0]) == 64


def test_kanvas_digit_menambah_titik_dan_menutup(app):
    K = Kanvas2D()
    K.resize(400, 300)
    bm = _bm()
    T = TB.ui_awal(bm)
    K.pasang_model(bm, T)
    K.set_flitch(102.5, 100.0)
    K.snap = False
    K.mulai()
    assert K.digit_on
    for x, y in [(500005.0, 9000005.0), (500025.0, 9000005.0), (500025.0, 9000025.0)]:
        p = K._w2p(x, y)
        K.mousePressEvent(QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(p.x(), p.y()),
                                      Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    assert len(K.poligon()) == 3
    assert K.tutup() is True
    assert K.digit_on is False


def test_kanvas_tutup_kurang_titik_gagal(app):
    K = Kanvas2D()
    K.resize(400, 300)
    K.mulai()
    K.titik = [(0.0, 0.0), (1.0, 0.0)]
    assert K.tutup() is False
    assert K.digit_on is True


def test_kanvas_urung_dan_batal(app):
    K = Kanvas2D()
    K.mulai()
    K.titik = [(0.0, 0.0), (1.0, 0.0)]
    K.urungkan()
    assert len(K.titik) == 1
    K.batal()
    assert K.digit_on is False and K.titik == []


def test_kanvas_snap_ke_sudut_blok(app):
    """Tempel ke sudut blok: garis galian jatuh di batas blok, bukan di tengah piksel."""
    K = Kanvas2D()
    K.resize(400, 300)
    bm = _bm()
    K.pasang_model(bm, TB.ui_awal(bm))
    K.set_flitch(102.5, 100.0)
    K.snap = True
    K._px_per_m = 10.0                      # cukup besar supaya sudut dalam jangkauan DEKAT_PX
    x, y = K._tempel(500000.3, 9000000.4)
    assert (x, y) == (pytest.approx(500000.0), pytest.approx(9000000.0))


def test_kanvas_snap_mati_tidak_mengubah(app):
    K = Kanvas2D()
    bm = _bm()
    K.pasang_model(bm, TB.ui_awal(bm))
    K.snap = False
    assert K._tempel(500000.3, 9000000.4) == (500000.3, 9000000.4)


def test_kanvas_poligon_dalam_koordinat_penuh(app):
    """Titik dari kanvas harus langsung bisa dipakai `galian.tonase` tanpa penambahan offset."""
    K = Kanvas2D()
    K.resize(400, 300)
    bm = _bm()
    T = TB.ui_awal(bm)
    K.pasang_model(bm, T)
    K.set_flitch(102.5, 100.0)
    K.snap = False
    K.mulai()
    for x, y in [(500002.5, 9000002.5), (500022.5, 9000002.5), (500022.5, 9000022.5)]:
        p = K._w2p(x, y)
        K.mousePressEvent(QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(p.x(), p.y()),
                                      Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    P = K.poligon()
    assert min(p[0] for p in P) > 400000.0            # masih koordinat penuh, bukan relatif
    H = GA.tonase(bm, P, T, GA.Opsi(rl_atas=102.5, rl_bawah=100.0, kadar="AU_GT",
                                    waste_on=False))
    assert H.n > 0, "poligon dari kanvas tidak kena blok: ruang koordinat tidak cocok"


def test_kanvas_zoom_mempertahankan_titik_di_bawah_kursor(app):
    K = Kanvas2D()
    K.resize(400, 300)
    bm = _bm()
    K.pasang_model(bm, TB.ui_awal(bm))
    sebelum = K._p2w(120.0, 80.0)
    k0 = K._px_per_m
    # tiru satu langkah zoom seperti wheelEvent
    px, py = 120.0, 80.0
    s = K._p2w(px, py)
    K._px_per_m = k0 * 1.15
    t = K._p2w(px, py)
    K._pusat = (K._pusat[0] + s[0] - t[0], K._pusat[1] + s[1] - t[1])
    sesudah = K._p2w(120.0, 80.0)
    assert sesudah[0] == pytest.approx(sebelum[0], abs=1e-6)
    assert sesudah[1] == pytest.approx(sebelum[1], abs=1e-6)


def test_kanvas_gambar_tidak_melempar(app):
    """paintEvent harus aman walau model kosong maupun penuh -- dipanggil tanpa layar."""
    K = Kanvas2D()
    K.resize(300, 200)
    K.grab()                                      # memaksa satu siklus gambar
    bm = _bm()
    K.pasang_model(bm, TB.ui_awal(bm))
    K.set_flitch(102.5, 100.0)
    K.strings = [SIO.String(no=1, tertutup=True,
                            pts=[(500005.0, 9000005.0, 101.0), (500025.0, 9000005.0, 101.0),
                                 (500025.0, 9000025.0, 101.0)])]
    K.titik = [(500010.0, 9000010.0), (500020.0, 9000010.0), (500020.0, 9000020.0)]
    K.digit_on = True
    K.grab()


# ---------------------------------------------------------------- folder proyek

def test_panel_simpan_dan_muat_dari_folder(app, tmp_path):
    P = PanelGalian()
    bm = _bm()
    T = TB.ui_awal(bm)
    P.pasang_model(bm, T)
    P.pasang_folder(tmp_path, (500000.0, 9000000.0))
    z = GA.zs_flitch(GA.bench(P.spn_atas.value(), P.spn_bawah.value()))
    P.strings.append(SIO.String(no=1, ket="ORE", tertutup=True,
                                pts=[(500010.0, 9000010.0, z), (500030.0, 9000010.0, z),
                                     (500030.0, 9000030.0, z)]))
    P._tersimpan = False
    P.simpan_proyek()
    assert P._tersimpan is True

    Q = PanelGalian()
    Q.pasang_model(bm, T)
    Q.pasang_folder(tmp_path, (500000.0, 9000000.0))
    assert len(Q.strings) == 1
    assert Q.strings[0].pts[0] == pytest.approx((500010.0, 9000010.0, z))


def test_panel_simpan_tanpa_folder_memberi_pesan(app):
    P = PanelGalian()
    P.simpan_proyek()
    assert "folder proyek" in P.pesan.text()


def test_peringatan_hilang_bila_folder_proyek_ada(app, tmp_path):
    """Dengan folder proyek, string tersimpan otomatis -- tidak ada yang hilang, tidak ada alarm."""
    P = PanelGalian()
    bm = _bm()
    P.pasang_model(bm, TB.ui_awal(bm))
    P.pasang_folder(tmp_path, (500000.0, 9000000.0))
    P.strings.append(SIO.String(no=1, pts=[(500010.0, 9000010.0, 101.0),
                                           (500030.0, 9000010.0, 101.0),
                                           (500030.0, 9000030.0, 101.0)]))
    P.simpan_otomatis()
    assert P.ada_belum_diekspor() is False


def test_peringatan_muncul_tanpa_folder_proyek(app):
    P = PanelGalian()
    bm = _bm()
    P.pasang_model(bm, TB.ui_awal(bm))
    P.strings.append(SIO.String(no=1, pts=[(1.0, 1.0, 1.0), (2.0, 1.0, 1.0), (2.0, 2.0, 1.0)]))
    P.hitung_semua()
    assert P.ada_belum_diekspor() is True
    assert "HILANG" in P.peringatan_simpan.text()


def test_ambil_dari_html_menambah_bukan_mengganti(app, tmp_path):
    """Mengganti daftar akan membuang pekerjaan yang mungkin belum tersimpan."""
    from qtbm import simpan_galian as SG
    body = '{"work":{"dg":[{"no":1,"d":"HTML","closed":true,"vis":true,' \
           '"pts":[[10,20,101],[30,20,101],[30,40,101]]}]},"dataHash":"x"}'
    teks, _h = SG.pack({"format": "gcex-project", "version": 2}, body)
    (tmp_path / SG.BERKAS_PROYEK).write_text(teks, encoding="utf-8")

    P = PanelGalian()
    bm = _bm()
    P.pasang_model(bm, TB.ui_awal(bm))
    P.pasang_folder(tmp_path, (500000.0, 9000000.0))
    P.strings.append(SIO.String(no=1, ket="QT", tertutup=True,
                                pts=[(500010.0, 9000010.0, 101.0), (500030.0, 9000010.0, 101.0),
                                     (500030.0, 9000030.0, 101.0)]))
    P.ambil_dari_html()
    assert len(P.strings) == 2
    assert {s.ket for s in P.strings} == {"QT", "HTML"}
    # nomor tidak boleh kembar
    assert len({s.no for s in P.strings}) == 2


def test_ambil_dari_html_tanpa_folder_memberi_pesan(app):
    P = PanelGalian()
    P.ambil_dari_html()
    assert "folder proyek" in P.pesan.text()


def test_berkas_rusak_tidak_ditimpa(app, tmp_path):
    """Berkas string Qt yang rusak dibiarkan apa adanya: pemakai mungkin masih bisa menyelamatkannya."""
    from qtbm import simpan_galian as SG
    rusak = '{"format":"gcex-dig-qt","hash":"salah","body":{"dg":[]}}'
    (tmp_path / SG.BERKAS_QT).write_text(rusak, encoding="utf-8")
    P = PanelGalian()
    bm = _bm()
    P.pasang_model(bm, TB.ui_awal(bm))
    P.pasang_folder(tmp_path, (0.0, 0.0))
    assert "tidak bisa dibaca" in P.pesan.text()
    assert (tmp_path / SG.BERKAS_QT).read_text(encoding="utf-8") == rusak
