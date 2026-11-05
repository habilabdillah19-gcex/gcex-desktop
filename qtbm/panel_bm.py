# -*- coding: utf-8 -*-
"""Panel "Tampilan block model" versi Qt -- susunan kendali yang sama dengan panel HTML.

Panel ini TIDAK menghitung apa pun sendiri. Seluruh aturan (batas kelas, cut-off, warna) ada di
`tampil_bm.py` yang sudah diuji sama persis dengan aplikasi HTML; panel ini hanya mengubah keadaan
`Tampilan` lalu memberi tahu pemanggil supaya adegan disusun ulang. Pembagian itu disengaja: kalau
aturannya ikut ditulis di dalam widget, uji paritas tidak lagi menjamin apa yang dilihat pemakai.

Urutan kendali mengikuti panel HTML supaya orang yang berpindah antar kedua aplikasi tidak perlu
mencari-cari: Warnai berdasarkan -> kelas / kategori -> cut-off tampilan -> opasitas -> SG.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFrame,
                               QGridLayout, QHBoxLayout, QInputDialog, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from . import tampil_bm as TB
from .proyek import BlockModel


def _kotak_warna(warna: str, lebar: int = 26, tinggi: int = 16) -> QLabel:
    k = QLabel()
    k.setFixedSize(lebar, tinggi)
    k.setStyleSheet("background:%s;border:1px solid rgba(0,0,0,.35);border-radius:3px" % warna)
    return k


class TombolWarna(QPushButton):
    """Tombol kecil berwarna; diklik membuka pemilih warna."""

    diubah = Signal(str)

    def __init__(self, warna: str, induk=None) -> None:
        super().__init__(induk)
        self.setFixedSize(26, 20)
        self._w = warna
        self._pasang()
        self.clicked.connect(self._pilih)

    def _pasang(self) -> None:
        self.setStyleSheet("background:%s;border:1px solid rgba(0,0,0,.4);border-radius:3px" % self._w)

    def warna(self) -> str:
        return self._w

    def _pilih(self) -> None:
        c = QColorDialog.getColor(QColor(self._w), self, "Warna kelas")
        if c.isValid():
            self._w = c.name()
            self._pasang()
            self.diubah.emit(self._w)


class PanelBM(QWidget):
    """Kendali tampilan block model. `berubah` dipancarkan setiap kali adegan perlu disusun ulang."""

    berubah = Signal()

    def __init__(self, induk=None) -> None:
        super().__init__(induk)
        self.bm: Optional[BlockModel] = None
        self.T = TB.Tampilan()
        self._diam = False                 # True = jangan pancarkan `berubah` saat panel dibangun

        L = QVBoxLayout(self)
        L.setContentsMargins(0, 0, 0, 0)
        L.setSpacing(6)

        self.info = QLabel("Belum ada block model.")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color:#8a93a6")
        L.addWidget(self.info)

        L.addWidget(QLabel("Warnai berdasarkan"))
        self.cmb_attr = QComboBox()
        self.cmb_attr.currentTextChanged.connect(self._ganti_atribut)
        L.addWidget(self.cmb_attr)

        # ---- kelas / kategori: isi berubah-ubah, jadi ditaruh di wadah yang dibangun ulang
        self.judul_kelas = QLabel("Kelas diskrit (batas bawah ≤ nilai < batas atas)")
        self.judul_kelas.setWordWrap(True)
        L.addWidget(self.judul_kelas)
        self.wadah = QWidget()
        self.wadah_L = QVBoxLayout(self.wadah)
        self.wadah_L.setContentsMargins(0, 0, 0, 0)
        self.wadah_L.setSpacing(2)
        gulir = QScrollArea()
        gulir.setWidgetResizable(True)
        gulir.setFrameShape(QFrame.NoFrame)
        gulir.setWidget(self.wadah)
        gulir.setMinimumHeight(140)
        gulir.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        L.addWidget(gulir, 1)

        baris = QHBoxLayout()
        self.b_tambah = QPushButton("+ Kelas")
        self.b_kuantil = QPushButton("Kuantil")
        self.b_cutoff = QPushButton("Pakai cut-off")
        self.b_tambah.clicked.connect(self._tambah_kelas)
        self.b_kuantil.clicked.connect(self._kuantil)
        self.b_cutoff.clicked.connect(self._batas_manual)
        for b in (self.b_tambah, self.b_kuantil, self.b_cutoff):
            baris.addWidget(b)
        L.addLayout(baris)

        # ---- cut-off tampilan
        L.addWidget(QLabel("Tampilkan bila (cut-off)"))
        b2 = QHBoxLayout()
        self.cmb_f = QComboBox()
        self.cmb_op = QComboBox()
        self.cmb_op.addItem("≥", "ge")
        self.cmb_op.addItem("<", "lt")
        self.spn_f = QDoubleSpinBox()
        self.spn_f.setRange(-1e12, 1e12)
        self.spn_f.setDecimals(4)
        self.spn_f.setSpecialValueText("")          # nilai minimum = tanpa cut-off
        self.spn_f.setMinimum(-1e12)
        self.cmb_f.currentIndexChanged.connect(self._ganti_cutoff)
        self.cmb_op.currentIndexChanged.connect(self._ganti_cutoff)
        self.spn_f.valueChanged.connect(self._ganti_cutoff)
        b2.addWidget(self.cmb_f, 2)
        b2.addWidget(self.cmb_op)
        b2.addWidget(self.spn_f, 1)
        L.addLayout(b2)

        # ---- opasitas & SG
        b3 = QGridLayout()
        b3.addWidget(QLabel("Opasitas kubus"), 0, 0)
        self.spn_op = QDoubleSpinBox()
        self.spn_op.setRange(0.1, 1.0)
        self.spn_op.setSingleStep(0.05)
        self.spn_op.setValue(self.T.opasitas)
        self.spn_op.valueChanged.connect(self._ganti_op)
        b3.addWidget(self.spn_op, 0, 1)
        b3.addWidget(QLabel("SG tetap"), 1, 0)
        self.spn_sg = QDoubleSpinBox()
        self.spn_sg.setRange(0.1, 20.0)
        self.spn_sg.setDecimals(3)
        self.spn_sg.setValue(self.T.sg)
        self.spn_sg.valueChanged.connect(self._ganti_sg)
        b3.addWidget(self.spn_sg, 1, 1)
        b3.addWidget(QLabel("Kolom SG"), 2, 0)
        self.cmb_sg = QComboBox()
        self.cmb_sg.currentIndexChanged.connect(self._ganti_sg)
        b3.addWidget(self.cmb_sg, 2, 1)
        L.addLayout(b3)

        self.ringkas = QLabel("")
        self.ringkas.setWordWrap(True)
        self.ringkas.setStyleSheet("color:#8a93a6")
        L.addWidget(self.ringkas)

    # ------------------------------------------------------------------ data
    def pasang_model(self, bm: Optional[BlockModel]) -> None:
        """Pasang block model baru dan setel panel ke keadaan bawaan (seperti bxDefUI)."""
        self.bm = bm
        self.T = TB.ui_awal(bm) if bm is not None and bm.n else TB.Tampilan()
        self._diam = True
        try:
            self._isi_combo()
            self._bangun_daftar()
            self._tulis_info()
        finally:
            self._diam = False
        self.berubah.emit()

    def _isi_combo(self) -> None:
        for c in (self.cmb_attr, self.cmb_f, self.cmb_sg):
            c.blockSignals(True)
            c.clear()
        if self.bm is not None:
            for a in list(self.bm.angka) + list(self.bm.kategori):
                self.cmb_attr.addItem(a)
            self.cmb_f.addItem("(semua blok)", "")
            self.cmb_sg.addItem("(tidak)", "")
            for a in self.bm.angka:
                self.cmb_f.addItem(a, a)
                self.cmb_sg.addItem(a, a)
        if self.T.atribut:
            self.cmb_attr.setCurrentText(self.T.atribut)
        i = self.cmb_f.findData(self.T.f_atribut or "")
        self.cmb_f.setCurrentIndex(max(0, i))
        self.cmb_op.setCurrentIndex(0 if self.T.f_op != "lt" else 1)
        self.spn_f.setValue(float(self.T.f_nilai) if str(self.T.f_nilai) else self.spn_f.minimum())
        for c in (self.cmb_attr, self.cmb_f, self.cmb_sg):
            c.blockSignals(False)

    def _tulis_info(self) -> None:
        if self.bm is None or not self.bm.n:
            self.info.setText("Belum ada block model.")
            return
        k = self.bm.kotak()
        self.info.setText("<b>%s</b> · %s blok<br>E %.0f–%.0f · N %.0f–%.0f "
                          "· Z %.1f–%.1f"
                          % (self.bm.nama or "block model",
                             f"{self.bm.n:,}".replace(",", "."),
                             k[0], k[1], k[2], k[3], k[4], k[5]))

    # ------------------------------------------------------------------ daftar kelas / kategori
    def _kosongkan(self) -> None:
        while self.wadah_L.count():
            it = self.wadah_L.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()

    def _bangun_daftar(self) -> None:
        self._kosongkan()
        bm, T = self.bm, self.T
        if bm is None or not T.atribut:
            self.judul_kelas.setText("")
            return
        kategori = T.atribut in bm.kategori
        self.judul_kelas.setText("Kategori (centang = tampil)" if kategori
                                 else "Kelas diskrit (batas bawah ≤ nilai < batas atas)")
        for b in (self.b_tambah, self.b_kuantil, self.b_cutoff):
            b.setVisible(not kategori)
        if kategori:
            self._baris_kategori()
        else:
            self._baris_kelas()

    def _baris_kategori(self) -> None:
        bm, T = self.bm, self.T
        kode, daftar = bm.kategori[T.atribut]
        cacah = np.bincount(np.asarray(kode)[np.asarray(kode) != TB.KODE_KOSONG].astype(np.int64),
                            minlength=len(daftar)) if kode.size else np.zeros(len(daftar), int)
        for i, nilai in enumerate(daftar):
            baris = QWidget()
            H = QHBoxLayout(baris)
            H.setContentsMargins(0, 0, 0, 0)
            H.setSpacing(4)
            cb = QCheckBox()
            cb.setChecked(T.kategori_aktif(T.atribut, nilai))
            cb.stateChanged.connect(lambda _s, v=nilai, c=cb: self._set_kat(v, c.isChecked()))
            tw = TombolWarna(T.warna_kategori(bm, T.atribut, i))
            tw.diubah.connect(lambda w, v=nilai: self._set_warna_kat(v, w))
            H.addWidget(cb)
            H.addWidget(tw)
            lab = QLabel(str(nilai))
            H.addWidget(lab, 1)
            n = QLabel(f"{int(cacah[i]):,}".replace(",", "."))
            n.setStyleSheet("color:#8a93a6")
            H.addWidget(n)
            self.wadah_L.addWidget(baris)
        self.wadah_L.addStretch(1)

    def _baris_kelas(self) -> None:
        bm, T = self.bm, self.T
        L = T.kelas_dari(bm, T.atribut)
        for i, c in enumerate(L):
            baris = QWidget()
            H = QHBoxLayout(baris)
            H.setContentsMargins(0, 0, 0, 0)
            H.setSpacing(4)
            tw = TombolWarna(c.col)
            tw.diubah.connect(lambda w, k=i: self._set_warna_kelas(k, w))
            H.addWidget(tw)
            for sisi in ("lo", "hi"):
                nilai = getattr(c, sisi)
                tetap = (sisi == "lo" and i == 0) or (sisi == "hi" and i == len(L) - 1)
                s = QDoubleSpinBox()
                s.setRange(-1e12, 1e12)
                s.setDecimals(4)
                if tetap:
                    s.setEnabled(False)
                    s.setSpecialValueText("min" if sisi == "lo" else "maks")
                    s.setValue(s.minimum())
                else:
                    s.setValue(float(nilai if nilai is not None else 0.0))
                    s.valueChanged.connect(
                        lambda v, k=i, sd=sisi: self._set_batas(k, sd, v))
                H.addWidget(s, 1)
                if sisi == "lo":
                    H.addWidget(QLabel("–"))
            if len(L) > 1:
                x = QPushButton("×")
                x.setFixedWidth(22)
                x.setToolTip("Hapus kelas")
                x.clicked.connect(lambda _c=False, k=i: self._hapus_kelas(k))
                H.addWidget(x)
            self.wadah_L.addWidget(baris)
        self.wadah_L.addStretch(1)

    # ------------------------------------------------------------------ penangan
    def _pancar(self, bangun_ulang: bool = False) -> None:
        if bangun_ulang:
            self._diam = True
            try:
                self._bangun_daftar()
            finally:
                self._diam = False
        if not self._diam:
            self.berubah.emit()

    def _ganti_atribut(self, nama: str) -> None:
        if self.bm is None or not nama:
            return
        self.T.atribut = nama
        self._pancar(bangun_ulang=True)

    def _ganti_cutoff(self, *_a) -> None:
        self.T.f_atribut = self.cmb_f.currentData() or ""
        self.T.f_op = self.cmb_op.currentData() or "ge"
        v = self.spn_f.value()
        self.T.f_nilai = "" if v <= self.spn_f.minimum() else repr(v)
        self._pancar()

    def _ganti_op(self, v: float) -> None:
        self.T.opasitas = float(v)
        self._pancar()

    def _ganti_sg(self, *_a) -> None:
        self.T.sg = float(self.spn_sg.value())
        self.T.sg_kolom = self.cmb_sg.currentData() or ""
        self._pancar()

    def _set_kat(self, nilai: str, on: bool) -> None:
        self.T.kat_on.setdefault(self.T.atribut, {})[nilai] = on
        self._pancar()

    def _set_warna_kat(self, nilai: str, warna: str) -> None:
        self.T.warna_kat.setdefault(self.T.atribut, {})[nilai] = warna
        self._pancar()

    def _set_warna_kelas(self, k: int, warna: str) -> None:
        self.T.kelas_dari(self.bm, self.T.atribut)[k].col = warna
        self._pancar()

    def _set_batas(self, k: int, sisi: str, nilai: float) -> None:
        self.T.set_batas(self.bm, self.T.atribut, k, sisi, nilai)
        self._pancar(bangun_ulang=True)

    def _tambah_kelas(self) -> None:
        if self.bm is None or not self.T.atribut:
            return
        self.T.tambah_kelas(self.bm, self.T.atribut)
        self._pancar(bangun_ulang=True)

    def _hapus_kelas(self, k: int) -> None:
        self.T.hapus_kelas(self.bm, self.T.atribut, k)
        self._pancar(bangun_ulang=True)

    def _kuantil(self) -> None:
        if self.bm is None or not self.T.atribut:
            return
        self.T.kelas_kuantil_ulang(self.bm, self.T.atribut)
        self._pancar(bangun_ulang=True)

    def _batas_manual(self) -> None:
        if self.bm is None or not self.T.atribut:
            return
        teks, ok = QInputDialog.getText(self, "Batas kelas",
                                        "Batas kelas (pisahkan dengan koma), mis. 0.3, 0.5, 1, 2",
                                        text="0.3,0.5,1,2")
        if not ok:
            return
        batas = TB.batas_dari_teks(teks)
        if not batas:
            return
        self.T.kelas[self.T.atribut] = TB.kelas_dari_batas(batas)
        self._pancar(bangun_ulang=True)

    # ------------------------------------------------------------------ keluaran
    def lapor(self, n_tampil: int, legenda: List[tuple]) -> None:
        """Tulis ringkasan di bawah panel: berapa blok tampil dan rincian per kelas."""
        if self.bm is None or not self.bm.n:
            self.ringkas.setText("")
            return
        bagian = ["%s dari %s blok tampil"
                  % (f"{n_tampil:,}".replace(",", "."), f"{self.bm.n:,}".replace(",", "."))]
        for lab, _w, cacah in legenda:
            bagian.append("&nbsp;&nbsp;%s: %s" % (lab, f"{cacah:,}".replace(",", ".")))
        self.ringkas.setText("<br>".join(bagian))
