# -*- coding: utf-8 -*-
"""Panel Sayatan (slicing) penampil Qt.

HANYA DUA MODE, SENGAJA: **Horizontal** dan **Garis manual**. Fungsi `secGeom` di aplikasi HTML
juga memuat mode X, Y dan A, tetapi pilihan arah potongan di aplikasi **Block Model** hanya
menawarkan 'H' dan 'P' -- ketiga mode lainnya tidak bisa dicapai dari antarmukanya, jadi tidak ada
perilaku aplikasi yang bisa dicocokkan dengan ketiganya. Menawarkannya di sini berarti memberi
pemakai angka yang tidak bisa diperiksa terhadap apa pun. Ada uji yang menjaga daftar mode panel
ini tetap H dan P, supaya menambah mode baru memaksa keputusan paritas lebih dulu.

Panel ini tidak menghitung tonase apa pun: ia hanya menentukan blok mana yang masuk slab lewat
`qtbm/sayatan.py`, dan hasilnya dipakai bersama oleh panel Tampilan, Laporan dan Dig block --
satu definisi sayatan, bukan tiga.

Tidak ada dialog modal: pesan masuk ke label `self.pesan`.
"""
from __future__ import annotations

import math
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget)

from . import sayatan as SY
from .proyek import BlockModel

# Mode yang ditawarkan panel = mode yang bisa dicapai di aplikasi Block Model. Jangan ditambah
# tanpa lebih dulu memastikan mode itu benar-benar ada di antarmuka aplikasi HTML dan diuji
# paritasnya; lihat catatan di atas modul.
MODE_PANEL = ("H", "P")


class PanelSayatan(QWidget):
    """Panel Sayatan. Tidak menggambar apa pun sendiri; jendela yang menyusun ulang adegan."""

    berubah = Signal()

    def __init__(self, induk=None) -> None:
        super().__init__(induk)
        self.bm: Optional[BlockModel] = None
        self.rl_data: Optional[Tuple[float, float]] = None   # dari Proyek.rl_data()
        self._diam = False                                   # menahan sinyal saat mengisi ulang

        L = QVBoxLayout(self)
        L.setContentsMargins(8, 8, 8, 8)
        L.setSpacing(8)

        gb = QGroupBox("Bidang potong")
        f = QFormLayout(gb)
        self.cmb_mode = QComboBox()
        for m in MODE_PANEL:
            self.cmb_mode.addItem(SY.NAMA_MODE[m], m)
        f.addRow("Arah potongan", self.cmb_mode)

        self.cb_potong = QCheckBox("Potong data (hanya blok di dalam slab)")
        self.cb_potong.setChecked(True)
        f.addRow(self.cb_potong)

        self.lbl_pos = QLabel("Posisi")
        baris = QHBoxLayout()
        self.sld_pos = QSlider(Qt.Horizontal)
        self.sld_pos.setRange(0, 1000)
        self.spn_pos = QDoubleSpinBox()
        self.spn_pos.setRange(-1e7, 1e7)
        self.spn_pos.setDecimals(3)
        baris.addWidget(self.sld_pos, 1)
        baris.addWidget(self.spn_pos)
        f.addRow(self.lbl_pos, baris)

        self.spn_tebal = QDoubleSpinBox()
        self.spn_tebal.setRange(0.1, 1e6)
        self.spn_tebal.setDecimals(3)
        self.spn_tebal.setValue(5.0)
        f.addRow("Tebal slab (m)", self.spn_tebal)
        L.addWidget(gb)

        # ---------- garis manual ----------
        self.gb_p = QGroupBox("Garis manual (mode P)")
        fp = QFormLayout(self.gb_p)
        self.spn_dip = QDoubleSpinBox()
        self.spn_dip.setRange(0.0, 90.0)
        self.spn_dip.setDecimals(2)
        self.spn_dip.setValue(90.0)
        fp.addRow("Dip (°)", self.spn_dip)
        self.t1e = QDoubleSpinBox(); self.t1n = QDoubleSpinBox()
        self.t2e = QDoubleSpinBox(); self.t2n = QDoubleSpinBox()
        for w in (self.t1e, self.t1n, self.t2e, self.t2n):
            w.setRange(-1e9, 1e9)
            w.setDecimals(3)
        b1 = QHBoxLayout(); b1.addWidget(self.t1e); b1.addWidget(self.t1n)
        b2 = QHBoxLayout(); b2.addWidget(self.t2e); b2.addWidget(self.t2n)
        fp.addRow("Titik 1 (E, N)", b1)
        fp.addRow("Titik 2 (E, N)", b2)
        self.cb_ruas = QCheckBox("Batasi sepanjang ruas saja")
        fp.addRow(self.cb_ruas)
        self.spn_ext = QDoubleSpinBox()
        self.spn_ext.setRange(0.0, 1e6)
        self.spn_ext.setDecimals(2)
        fp.addRow("Perpanjangan ujung (m)", self.spn_ext)
        self.lbl_pusat = QLabel("—")
        self.lbl_pusat.setWordWrap(True)
        self.lbl_pusat.setStyleSheet("color:#8b97a8")
        fp.addRow("RL pusat bidang", self.lbl_pusat)
        L.addWidget(self.gb_p)

        b3 = QHBoxLayout()
        self.btn_pas = QPushButton("Pas ke tengah model")
        self.btn_sb = QPushButton("Geser satu tebal ke bawah")
        b3.addWidget(self.btn_pas); b3.addWidget(self.btn_sb)
        L.addLayout(b3)

        self.lbl_info = QLabel("—")
        self.lbl_info.setWordWrap(True)
        L.addWidget(self.lbl_info)
        self.pesan = QLabel("")
        self.pesan.setWordWrap(True)
        self.pesan.setStyleSheet("color:#ffd92f")
        L.addWidget(self.pesan)
        L.addStretch(1)

        self.cmb_mode.currentIndexChanged.connect(self._mode_berubah)
        self.sld_pos.valueChanged.connect(self._dari_slider)
        self.spn_pos.valueChanged.connect(self._dari_angka)
        for w in (self.spn_tebal, self.spn_dip, self.t1e, self.t1n, self.t2e, self.t2n,
                  self.spn_ext):
            w.valueChanged.connect(self._kirim)
        for w in (self.cb_potong, self.cb_ruas):
            w.toggled.connect(self._kirim)
        self.btn_pas.clicked.connect(self.pas_tengah)
        self.btn_sb.clicked.connect(self.geser_bawah)
        self._mode_berubah()

    # ---------------------------------------------------------------- model

    def pasang_model(self, bm: Optional[BlockModel],
                     rl_data: Optional[Tuple[float, float]] = None) -> None:
        self.bm = bm
        self.rl_data = rl_data
        self._diam = True
        try:
            if bm is not None and bm.n:
                x0, x1, y0, y1, _z0, _z1 = bm.kotak()
                self.t1e.setValue(round(x0 + (x1 - x0) * 0.25, 3))
                self.t1n.setValue(round(y0 + (y1 - y0) * 0.25, 3))
                self.t2e.setValue(round(x0 + (x1 - x0) * 0.75, 3))
                self.t2n.setValue(round(y0 + (y1 - y0) * 0.75, 3))
                tebal = float(min(bm.sz)) if len(bm.sz) else 5.0
                self.spn_tebal.setValue(max(0.1, round(tebal, 3)))
                self._pasang_rentang()
                self.spn_pos.setValue(SY.pos_awal(bm, self.opsi()))
        finally:
            self._diam = False
        self._segarkan()
        self.berubah.emit()

    # ---------------------------------------------------------------- pilihan

    def opsi(self) -> SY.Opsi:
        m = self.cmb_mode.currentData() or "H"
        O = SY.Opsi(mode=m, pos=float(self.spn_pos.value()),
                    tebal=float(self.spn_tebal.value()),
                    dip=float(self.spn_dip.value()),
                    batasi_ruas=self.cb_ruas.isChecked(),
                    perpanjang=float(self.spn_ext.value()),
                    potong=self.cb_potong.isChecked())
        if m == "P":
            O.titik1 = (float(self.t1e.value()), float(self.t1n.value()))
            O.titik2 = (float(self.t2e.value()), float(self.t2n.value()))
        # RL pusat bidang: tengah kotak DATA bor bila ada, sama dengan `(G.z0+G.z1)/2` di
        # aplikasi HTML. Tanpa data bor dipakai tengah block model, dan itu disebutkan di panel.
        if self.rl_data:
            O.pusat_z = (float(self.rl_data[0]) + float(self.rl_data[1])) / 2.0
        return O

    def topeng(self):
        """Larik bool blok yang masuk slab, atau None bila 'Potong data' dimatikan."""
        if self.bm is None or not self.bm.n or not self.cb_potong.isChecked():
            return None
        return SY.dalam_slab(self.bm, self.opsi())

    # ---------------------------------------------------------------- isi ulang

    def _mode_berubah(self, *a) -> None:
        m = self.cmb_mode.currentData() or "H"
        self.gb_p.setVisible(m == "P")
        self.lbl_pos.setText("Posisi (%s)" % SY.SATUAN_POS.get(m, "offset"))
        self.btn_sb.setVisible(m == "H")
        if self.bm is not None and self.bm.n and not self._diam:
            self._diam = True
            try:
                self._pasang_rentang()
                self.spn_pos.setValue(SY.pos_awal(self.bm, self.opsi()))
            finally:
                self._diam = False
        self._segarkan()
        if not self._diam:
            self.berubah.emit()

    def _pasang_rentang(self) -> None:
        """Slider memakai seperseribu rentang; kotak angkanya tetap bisa di luar rentang itu.

        Slider sengaja TIDAK menjepit kotak angkanya: di aplikasi HTML `pos` adalah slider yang
        menjepit nilainya, dan itu sempat membuat uji paritas saya menyetel 0 lalu mendapat 127
        tanpa tanda apa pun. Di sini kotak angkanya yang berlaku, slider hanya alat geser.
        """
        if self.bm is None or not self.bm.n:
            return
        lo, hi = SY.rentang_pos(self.bm, self.opsi())
        self._lo, self._hi = lo, hi
        self.sld_pos.blockSignals(True)
        self.sld_pos.setRange(0, 1000)
        self.sld_pos.blockSignals(False)

    def _dari_slider(self, v: int) -> None:
        if self._diam or self.bm is None or not self.bm.n:
            return
        lo = getattr(self, "_lo", 0.0)
        hi = getattr(self, "_hi", 0.0)
        if hi <= lo:
            return
        self._diam = True
        try:
            self.spn_pos.setValue(lo + (hi - lo) * (v / 1000.0))
        finally:
            self._diam = False
        self._kirim()

    def _dari_angka(self, v: float) -> None:
        if self._diam:
            return
        lo = getattr(self, "_lo", 0.0)
        hi = getattr(self, "_hi", 0.0)
        if hi > lo:
            self.sld_pos.blockSignals(True)
            self.sld_pos.setValue(int(round(max(0.0, min(1.0, (v - lo) / (hi - lo))) * 1000)))
            self.sld_pos.blockSignals(False)
        self._kirim()

    def _kirim(self, *a) -> None:
        if self._diam:
            return
        self._segarkan()
        self.berubah.emit()

    def pas_tengah(self) -> None:
        if self.bm is None or not self.bm.n:
            self.pesan.setText("Muat block model dulu.")
            return
        self.pesan.setText("")
        self._diam = True
        try:
            self._pasang_rentang()
            self.spn_pos.setValue(SY.pos_awal(self.bm, self.opsi()))
        finally:
            self._diam = False
        self._dari_angka(self.spn_pos.value())

    def geser_bawah(self) -> None:
        """Mode H: turun satu tebal slab, untuk menyusuri bench satu per satu."""
        self.spn_pos.setValue(self.spn_pos.value() - float(self.spn_tebal.value()))

    def _segarkan(self) -> None:
        O = self.opsi()
        if self.rl_data:
            self.lbl_pusat.setText(
                "%.2f (tengah kotak data bor RL %.2f–%.2f, sama dengan aplikasi HTML)"
                % (O.pusat_z, self.rl_data[0], self.rl_data[1]))
        else:
            self.lbl_pusat.setText(
                "tengah block model — aplikasi HTML memakai tengah kotak data BOR; tanpa data bor "
                "di proyek ini keduanya bisa berbeda, dan sayatan miring akan bergeser")
        if self.bm is None or not self.bm.n:
            self.lbl_info.setText("—")
            return
        teks = SY.label(self.bm, O)
        if self.cb_potong.isChecked():
            t = self.topeng()
            n = int(t.sum()) if t is not None else self.bm.n
            teks += " · %d blok di dalam slab" % n
            if n == 0:
                teks += " — tidak ada blok di posisi ini"
        else:
            teks += " · potong data MATI (semua blok tetap digambar)"
        self.lbl_info.setText(teks)
