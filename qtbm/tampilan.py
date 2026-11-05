# -*- coding: utf-8 -*-
"""Jendela penampil Qt: block model 3D dari folder proyek GC-Ex.

Ini TAHAP 2 yang berjalan DI SAMPING aplikasi yang ada, bukan menggantinya. Aplikasi GC-Ex Block
Model dan Drill Hole tetap seperti sekarang; penampil ini hanya membuka folder proyek yang sama
untuk satu hal: melihat block model 3D dengan jumlah blok yang jauh lebih banyak daripada yang
nyaman di peramban. Sampai terbukti lebih nyaman dan lebih cepat pada pekerjaan sehari-hari,
tidak ada yang dipindahkan.

Yang ada di jendela ini: pemutar 3D (seret = putar, roda = dekat-jauh, seret kanan = geser),
pemilih atribut untuk warna, pembatas RL, pembatas sayatan, dan penghitung fps beserta jumlah blok
yang digambar -- supaya penilaian "lebih lancar atau tidak" memakai angka, bukan kesan.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                               QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
                               QSlider, QVBoxLayout, QWidget)

from . import adegan as AD
from . import proyek as PR
from .render import Kamera, Penggambar


def format_gl() -> QSurfaceFormat:
    f = QSurfaceFormat()
    f.setVersion(3, 3)
    f.setProfile(QSurfaceFormat.CoreProfile)
    f.setDepthBufferSize(24)
    f.setSamples(4)
    return f


class Pemutar(QOpenGLWidget):
    """Kanvas 3D: menggambar adegan dan menerima gerakan tetikus."""

    def __init__(self, induk=None) -> None:
        super().__init__(induk)
        self.pg = Penggambar()
        self.kam = Kamera()
        self.adegan: Optional[AD.Adegan] = None
        self._tunda: Optional[AD.Adegan] = None
        self._seret = None
        self.fps = 0.0
        self._t = time.perf_counter()
        self._n = 0
        self.topo_on = True
        self.bor_on = True
        self.setMouseTracking(True)

    # ---------- OpenGL ----------
    def initializeGL(self) -> None:
        if not self.pg.siapkan():
            print("Penggambar tidak siap:", self.pg.galat, file=sys.stderr)
            return
        if self._tunda is not None:
            self.pg.unggah(self._tunda)
            self.adegan = self._tunda
            self._tunda = None

    def paintGL(self) -> None:
        if not self.pg.siap:
            return
        r = self.devicePixelRatioF()
        self.pg.gambar(self.kam, int(self.width() * r), int(self.height() * r),
                       topo_on=self.topo_on, bor_on=self.bor_on)
        self._n += 1
        s = time.perf_counter() - self._t
        if s >= 0.5:
            self.fps = self._n / s
            self._n = 0
            self._t = time.perf_counter()

    # ---------- adegan ----------
    def pasang(self, A: AD.Adegan, pas_kamera: bool = True) -> None:
        if pas_kamera and (A.n_blok or A.garis.shape[0]):
            kotak = A.kotak if A.n_blok else (
                float(A.garis[:, 0].min()), float(A.garis[:, 0].max()),
                float(A.garis[:, 1].min()), float(A.garis[:, 1].max()),
                float(A.garis[:, 2].min()), float(A.garis[:, 2].max()))
            self.kam.pas_ke(kotak)
        if self.pg.siap:
            self.pg = Penggambar()          # buffer lama dilepas bersama penggambarnya
            self.makeCurrent()
            self.pg.siapkan()
            self.pg.unggah(A)
            self.doneCurrent()
            self.adegan = A
        else:
            self._tunda = A
        self.update()

    # ---------- tetikus ----------
    def mousePressEvent(self, e) -> None:
        self._seret = (e.position().x(), e.position().y(), e.buttons())

    def mouseMoveEvent(self, e) -> None:
        if not self._seret:
            return
        dx = e.position().x() - self._seret[0]
        dy = e.position().y() - self._seret[1]
        self._seret = (e.position().x(), e.position().y(), e.buttons())
        if e.buttons() & Qt.LeftButton:
            self.kam.azimut = (self.kam.azimut - dx * 0.4) % 360.0
            self.kam.tunduk = max(-89.0, min(89.0, self.kam.tunduk + dy * 0.3))
        elif e.buttons() & Qt.RightButton:
            # geser sejajar bidang layar
            a = np.radians(self.kam.azimut)
            kanan = np.array([np.cos(a), -np.sin(a), 0.0])
            atas = np.array([0.0, 0.0, 1.0])
            skala = self.kam.jarak * 0.0015
            self.kam.sasaran = self.kam.sasaran - kanan * dx * skala + atas * dy * skala
        self.update()

    def mouseReleaseEvent(self, e) -> None:
        self._seret = None

    def wheelEvent(self, e) -> None:
        d = e.angleDelta().y() / 120.0
        self.kam.jarak = max(1.0, self.kam.jarak * (0.88 ** d))
        self.update()


class Jendela(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GC-Ex Block Model 3D (Qt) — penampil")
        self.resize(1280, 800)
        self.P: Optional[PR.Proyek] = None

        self.pemutar = Pemutar(self)
        sisi = QWidget()
        sisi.setFixedWidth(300)
        L = QVBoxLayout(sisi)

        self.lbl = QLabel("Belum ada proyek dibuka.")
        self.lbl.setWordWrap(True)
        L.addWidget(self.lbl)

        b1 = QPushButton("Buka folder proyek…")
        b1.clicked.connect(self.buka_folder)
        L.addWidget(b1)
        b2 = QPushButton("Muat block model (CSV)…")
        b2.clicked.connect(self.buka_bm)
        L.addWidget(b2)

        L.addWidget(QLabel("Warna menurut atribut"))
        self.cmb = QComboBox()
        self.cmb.currentIndexChanged.connect(self.susun_ulang)
        L.addWidget(self.cmb)

        L.addWidget(QLabel("Batas RL"))
        baris = QHBoxLayout()
        self.rl0 = QDoubleSpinBox(); self.rl1 = QDoubleSpinBox()
        for s in (self.rl0, self.rl1):
            s.setRange(-99999, 99999)
            s.setDecimals(1)
            s.valueChanged.connect(self.susun_ulang)
            baris.addWidget(s)
        L.addLayout(baris)

        self.sayat_on = QCheckBox("Batasi sayatan (slab tegak)")
        self.sayat_on.stateChanged.connect(self.susun_ulang)
        L.addWidget(self.sayat_on)
        baris2 = QHBoxLayout()
        self.az = QDoubleSpinBox(); self.az.setRange(0, 359.9); self.az.setValue(90.0)
        self.tebal = QDoubleSpinBox(); self.tebal.setRange(0.5, 10000); self.tebal.setValue(40.0)
        for s in (self.az, self.tebal):
            s.valueChanged.connect(self.susun_ulang)
        baris2.addWidget(QLabel("azimut")); baris2.addWidget(self.az)
        baris2.addWidget(QLabel("tebal")); baris2.addWidget(self.tebal)
        L.addLayout(baris2)

        self.cb_bor = QCheckBox("Jalur bor"); self.cb_bor.setChecked(True)
        self.cb_bor.stateChanged.connect(self.tampil_lapis)
        L.addWidget(self.cb_bor)
        self.cb_topo = QCheckBox("Topografi"); self.cb_topo.setChecked(True)
        self.cb_topo.stateChanged.connect(self.tampil_lapis)
        L.addWidget(self.cb_topo)

        self.stat = QLabel("—")
        self.stat.setWordWrap(True)
        L.addWidget(self.stat)
        L.addStretch(1)

        pusat = QWidget()
        H = QHBoxLayout(pusat)
        H.setContentsMargins(0, 0, 0, 0)
        H.addWidget(self.pemutar, 1)
        H.addWidget(sisi)
        self.setCentralWidget(pusat)

        self.jam = QTimer(self)
        self.jam.timeout.connect(self.perbarui_status)
        self.jam.start(500)

    # ---------- memuat ----------
    def buka_folder(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Pilih folder proyek GC-Ex")
        if not d:
            return
        try:
            self.P = PR.buka_folder(Path(d))
        except Exception as e:
            QMessageBox.warning(self, "Gagal membuka", str(e))
            return
        self.lbl.setText(self.P.ringkas())
        self.isi_atribut()
        self.susun_ulang(pas_kamera=True)

    def buka_bm(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Pilih berkas block model",
                                           "", "Block model (*.csv *.txt *.tsv)")
        if not f:
            return
        try:
            bm = PR.baca_bm(Path(f))
        except Exception as e:
            QMessageBox.warning(self, "Gagal membaca block model", str(e))
            return
        if self.P is None:
            self.P = PR.Proyek()
        self.P.bm = bm
        k = bm.kotak()
        self.rl0.setValue(round(k[4], 1))
        self.rl1.setValue(round(k[5], 1))
        self.lbl.setText(self.P.ringkas())
        self.isi_atribut()
        self.susun_ulang(pas_kamera=True)

    def isi_atribut(self) -> None:
        self.cmb.blockSignals(True)
        self.cmb.clear()
        if self.P and self.P.bm:
            for a in sorted(self.P.bm.angka):
                self.cmb.addItem(a)
            for a in sorted(self.P.bm.kategori):
                self.cmb.addItem(a + "  (kategori)")
        self.cmb.blockSignals(False)

    # ---------- menyusun ----------
    def saringan(self) -> AD.Saringan:
        S = AD.Saringan()
        if self.P and self.P.bm and (self.rl1.value() > self.rl0.value()):
            S.rl = (self.rl0.value(), self.rl1.value())
        if self.sayat_on.isChecked() and self.P and self.P.bm and self.P.bm.n:
            k = self.P.bm.kotak()
            S.sayatan = ((k[0] + k[1]) / 2, (k[2] + k[3]) / 2, self.az.value(), self.tebal.value())
        return S

    def susun_ulang(self, *a, pas_kamera: bool = False) -> None:
        if not self.P:
            return
        nama = self.cmb.currentText().replace("  (kategori)", "") or None
        t = time.perf_counter()
        A = AD.susun(self.P.bm, self.P.bor if self.P.data else None,
                     self.P.topo() if self.P.data else None,
                     atribut=nama, saringan=self.saringan())
        self._ms_susun = (time.perf_counter() - t) * 1000
        self.pemutar.pasang(A, pas_kamera=pas_kamera)

    def tampil_lapis(self) -> None:
        self.pemutar.bor_on = self.cb_bor.isChecked()
        self.pemutar.topo_on = self.cb_topo.isChecked()
        self.pemutar.update()

    def perbarui_status(self) -> None:
        A = self.pemutar.adegan
        if A is None:
            return
        self.pemutar.update()
        self.stat.setText(
            "%s blok digambar · %.0f fps · susun %.0f ms\nasal lokal: %s"
            % (f"{A.n_blok:,}".replace(",", "."), self.pemutar.fps,
               getattr(self, "_ms_susun", 0.0), A.asal))


def jalankan(argv: Optional[list] = None) -> int:
    argv = list(argv if argv is not None else sys.argv)
    QSurfaceFormat.setDefaultFormat(format_gl())
    app = QApplication(argv)
    j = Jendela()
    j.show()
    # argumen baris perintah: [folder_proyek] [berkas_bm.csv]
    sisa = [a for a in argv[1:] if not a.startswith("-")]
    for s in sisa:
        p = Path(s)
        if p.is_dir():
            try:
                j.P = PR.buka_folder(p)
                j.lbl.setText(j.P.ringkas())
            except Exception as e:
                print("gagal membuka folder proyek:", e, file=sys.stderr)
        elif p.is_file():
            try:
                if j.P is None:
                    j.P = PR.Proyek()
                j.P.bm = PR.baca_bm(p)
                j.lbl.setText(j.P.ringkas())
            except Exception as e:
                print("gagal membaca block model:", e, file=sys.stderr)
    if j.P:
        j.isi_atribut()
        if j.P.bm:
            k = j.P.bm.kotak()
            j.rl0.setValue(round(k[4], 1))
            j.rl1.setValue(round(k[5], 1))
        j.susun_ulang(pas_kamera=True)
    return app.exec()
