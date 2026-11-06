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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QFileDialog,
                               QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
                               QSlider, QStackedWidget, QTabWidget, QVBoxLayout, QWidget)

from . import adegan as AD
from . import proyek as PR
from .panel_bm import PanelBM
from .kanvas2d import Kanvas2D
from .panel_galian import PanelGalian
from .panel_laporan import PanelLaporan
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
        sisi.setFixedWidth(340)
        L = QVBoxLayout(sisi)

        self.lbl = QLabel("Belum ada proyek dibuka.")
        self.lbl.setWordWrap(True)
        L.addWidget(self.lbl)

        b1 = QPushButton("Buka folder proyek…")
        b1.clicked.connect(self.buka_folder)
        L.addWidget(b1)
        b2 = QPushButton("Muat block model (CSV / .mdl)…")
        b2.clicked.connect(self.buka_bm)
        L.addWidget(b2)

        # Dua panel di tab terpisah: Tampilan (apa yang digambar) dan Laporan (angka tonase).
        # Dipisah karena keduanya dipakai pada saat berbeda dan laporan butuh ruang tabel.
        self.tab = QTabWidget()
        self.panel = PanelBM()
        self.panel.berubah.connect(self.susun_ulang)
        self.lap = PanelLaporan()
        self.lap.saringan_aktif = self._saringan_bool
        self.lap.sumber_sg = lambda: (self.panel.T.sg, self.panel.T.sg_kolom,
                                      self.panel.T.sg_nol, self.panel.T.sg_ganti)
        self.gal = PanelGalian()
        self.gal.sumber_sg = lambda: (self.panel.T.sg, self.panel.T.sg_kolom,
                                      self.panel.T.sg_nol, self.panel.T.sg_ganti)
        self.tab.addTab(self.panel, "Tampilan")
        self.tab.addTab(self.lap, "Laporan")
        self.tab.addTab(self.gal, "Dig block")
        self.tab.currentChanged.connect(self._tab_berubah)
        L.addWidget(self.tab, 1)

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

        # Dua kanvas bertumpuk: 3D untuk melihat, plan 2D untuk mendigit. Digitasi sengaja TIDAK
        # dilakukan di kanvas 3D yang bisa diputar -- mengklik titik di sana berarti menebak
        # kedalaman di balik piksel, dan satu derajat kemiringan kamera menggeser titiknya
        # beberapa meter tanpa ada yang tahu. Aplikasi HTML pun mengunci digitasi ke Sayatan 2D.
        self.kanvas2d = Kanvas2D()
        self.gal.pasang_kanvas(self.kanvas2d)
        self.gal.berubah.connect(self.kanvas2d.segarkan)
        self.tumpuk = QStackedWidget()
        self.tumpuk.addWidget(self.pemutar)
        self.tumpuk.addWidget(self.kanvas2d)

        pusat = QWidget()
        H = QHBoxLayout(pusat)
        H.setContentsMargins(0, 0, 0, 0)
        H.addWidget(self.tumpuk, 1)
        H.addWidget(sisi)
        self.setCentralWidget(pusat)

        self.jam = QTimer(self)
        self.jam.timeout.connect(self.perbarui_status)
        self.jam.start(500)

    # ---------- memuat ----------
    def closeEvent(self, e) -> None:
        """Peringatkan bila ada string dig block yang belum diekspor.

        Penyimpanan ke folder proyek belum ada, jadi menutup jendela MENGHILANGKAN string.
        Selama itu belum ada, setidaknya pemakai tidak kehilangannya tanpa diberi tahu.
        Dialog di sini aman: ini jalur penutupan, bukan jalur hitung (uji tanpa layar tidak
        pernah melewatinya), dan ia memang harus menghentikan penutupan sampai dijawab.
        """
        try:
            self.gal.simpan_otomatis()              # dengan folder proyek, ini menutup masalahnya
            if self.gal.ada_belum_diekspor():
                j = QMessageBox.warning(
                    self, "String belum diekspor",
                    "Ada %d string dig block yang belum tersimpan.\n\nTanpa folder proyek "
                    "yang terbuka, string ini akan HILANG kalau jendela ditutup sekarang. "
                    "Buka folder proyek, atau ekspor ke DXF / STR dulu?" % len(self.gal.strings),
                    QMessageBox.Cancel | QMessageBox.Discard, QMessageBox.Cancel)
                if j == QMessageBox.Cancel:
                    e.ignore()
                    self.tab.setCurrentWidget(self.gal)
                    return
        except Exception:                           # noqa: BLE001
            pass                                    # jangan pernah menghalangi penutupan
        super().closeEvent(e)

    def _tab_berubah(self, i: int) -> None:
        """Tab Dig block menampilkan plan 2D; tab lain kembali ke 3D."""
        dig = self.tab.widget(i) is self.gal
        self.tumpuk.setCurrentWidget(self.kanvas2d if dig else self.pemutar)
        if dig:
            self.kanvas2d.segarkan()
            self.kanvas2d.pas_ke_data()
        elif self.kanvas2d.digit_on:
            # keluar dari tab saat mendigit akan meninggalkan poligon setengah jadi yang tak
            # terlihat di mana pun; dibatalkan dan dikatakan, bukan disimpan diam-diam.
            self.kanvas2d.batal()
            self.gal.pesan.setText("Digitasi dibatalkan karena tab berpindah.")

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
        # String dig block yang pernah disimpan di folder ini dimuat kembali. Offset proyek
        # (offX/offY) diambil dari data bor proyek -- lihat Proyek.offset(); titik digitasi
        # aplikasi HTML relatif terhadapnya, jadi tanpa itu poligonnya pindah ratusan kilometer.
        self.gal.pasang_folder(self.P.folder, self.P.offset())
        self.susun_ulang(pas_kamera=True)

    def buka_bm(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Pilih berkas block model", "",
            "Block model (*.csv *.txt *.tsv *.mdl);;CSV / teks (*.csv *.txt *.tsv);;"
            "Surpac block model (*.mdl)")
        if not f:
            return

        def lapor(teks: str) -> None:
            # Membaca .mdl besar bisa beberapa menit pada berkas yang belum pernah dibuka
            # (cache kolom dibangun sekali). Kabarnya ditulis di panel supaya pemakai tidak
            # menyangka aplikasinya menggantung.
            self.lbl.setText(teks)
            QApplication.processEvents()

        try:
            bm = PR.baca_bm(Path(f), lapor=lapor)
        except Exception as e:
            QMessageBox.warning(self, "Gagal membaca block model", str(e))
            self.lbl.setText(self.P.ringkas() if self.P else "Belum ada proyek dibuka.")
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
        """Pasang block model ke semua panel; panel sendiri yang menyetel pilihan bawaannya."""
        bm = self.P.bm if self.P else None
        self.panel.pasang_model(bm)
        self.lap.pasang_model(bm)
        # Dig block memakai Tampilan YANG SAMA (objek, bukan salinan), supaya warna blok di plan
        # 2D dan SG yang dipakai tonase selalu ikut panel Tampilan tanpa perlu disalin ulang.
        self.gal.pasang_model(bm, self.panel.T)
        self.kanvas2d.pasang_model(bm, self.panel.T)

    def _saringan_bool(self):
        """Larik bool saringan GEOMETRIS yang sedang aktif (batas RL + sayatan).

        Sengaja TIDAK memuat cut-off dan kelas dari panel Tampilan: itu pengatur warna dan apa yang
        digambar, bukan batas perhitungan. Kalau keduanya dicampur, laporan akan berubah hanya
        karena seseorang mengganti warna -- dan tidak ada yang akan menduga sebabnya.
        """
        if not self.P or not self.P.bm or not self.P.bm.n:
            return None
        return self.saringan().terapkan(self.P.bm)

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
        t = time.perf_counter()
        A, idx, lg = AD.susun_tampil(self.P.bm, self.panel.T,
                                     self.P.bor if self.P.data else None,
                                     self.P.topo() if self.P.data else None,
                                     saringan=self.saringan())
        self._ms_susun = (time.perf_counter() - t) * 1000
        self.panel.lapor(int(idx.size), lg)
        self.pemutar.pasang(A, pas_kamera=pas_kamera)
        # Plan 2D dan tonase dig block ikut aturan warna & SG panel Tampilan, jadi keduanya
        # disegarkan di sini juga -- kalau tidak, warna di tab Dig block bisa tertinggal satu
        # langkah dari tab Tampilan dan dua tab menunjukkan model yang berbeda.
        self.kanvas2d.segarkan()
        self.gal.segarkan_sg()

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
