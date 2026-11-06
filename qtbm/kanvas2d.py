# -*- coding: utf-8 -*-
"""Kanvas plan 2D untuk digitasi dig block.

MENGAPA 2D, BUKAN DI VIEWPORT 3D: dig block adalah poligon pada SATU bidang datar (flitch).
Mengklik titik di tampilan 3D yang bisa diputar berarti menebak kedalaman di balik piksel --
satu derajat kemiringan kamera menggeser titiknya beberapa meter, tanpa ada yang tahu. Aplikasi
HTML pun mengunci digitasi ke Sayatan 2D (`dgStart` memaksa `toggle2D`). Kanvas ini meniru itu:
RL-nya terkunci pada flitch yang aktif, dan satu piksel selalu berarti jarak yang sama di lapangan.

Kanvas ini hanya MENGGAMBAR dan menerima klik. Semua perhitungan tonase ada di `qtbm/galian.py`,
dan tidak satu pun angka dihitung di sini -- supaya tidak ada dua sumber angka yang bisa berbeda.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from . import galian as GA
from . import tampil_bm as TB
from .proyek import BlockModel
from .string_io import String

# tetikus: jarak piksel di mana klik dianggap "menutup poligon" / menempel ke titik
DEKAT_PX = 10.0


class Kanvas2D(QWidget):
    """Plan view satu flitch: blok berwarna, string tersimpan, dan poligon yang sedang didigit."""

    titik_ditambah = Signal()
    poligon_selesai = Signal()
    posisi_berubah = Signal(float, float)        # easting, northing di bawah kursor

    def __init__(self, induk=None) -> None:
        super().__init__(induk)
        self.bm: Optional[BlockModel] = None
        self.T: Optional[TB.Tampilan] = None
        self.B: Tuple[float, float] = (0.0, 0.0)       # (RL atas, RL bawah)
        self.mode_flitch = "comp"
        self.strings: List[String] = []
        self.digit_on = False
        self.titik: List[Tuple[float, float]] = []
        self.snap = True
        self._px_per_m = 1.0
        self._pusat = (0.0, 0.0)
        self._seret: Optional[Tuple[float, float]] = None
        self._kursor: Optional[Tuple[float, float]] = None
        self._petak: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
                                   List[str]]] = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(320, 240)
        self.setCursor(Qt.ArrowCursor)

    # ---------------------------------------------------------------- data

    def pasang_model(self, bm: Optional[BlockModel], T: Optional[TB.Tampilan]) -> None:
        self.bm = bm
        self.T = T
        self._petak = None
        if bm is not None and bm.n:
            x0, x1, y0, y1, z0, z1 = bm.kotak()
            self._pusat = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
            lebar = max(x1 - x0, y1 - y0, 1.0)
            self._px_per_m = max(self.width(), 200) / (lebar * 1.1)
        self.update()

    def set_flitch(self, atas: float, bawah: float, mode: str = "comp") -> None:
        self.B = GA.bench(atas, bawah)
        self.mode_flitch = mode
        self._petak = None
        self.update()

    def _hitung_petak(self):
        """Blok yang masuk flitch + warna kelasnya. Warnanya dari `tampil_bm`, bukan dari sini."""
        if self.bm is None or self.T is None or not self.bm.n:
            self._petak = (np.empty(0), np.empty(0), np.empty(0), np.empty(0), [])
            return self._petak
        bm, T = self.bm, self.T
        ov = GA.tebal_dalam_flitch(bm, self.B, self.mode_flitch)
        idx, kelas = TB.pilih(bm, T)
        topeng = np.zeros(bm.n, dtype=bool)
        topeng[idx] = True
        pakai = np.nonzero(topeng & (ov > 0))[0]
        W = TB.warna_per_blok(bm, T, kelas)         # warna untuk blok di `idx`, berurutan
        # peta indeks blok -> baris di W, dibuat sebagai larik (bukan dict): pada model 400 rb
        # blok, dict di jalur gambar membuat panel terasa menggantung tiap kali flitch diubah.
        peta = np.full(bm.n, -1, dtype=np.int64)
        peta[idx] = np.arange(idx.size)
        baris = peta[pakai]
        warna = [("#%02x%02x%02x" % tuple(int(c) for c in W[b][:3])) for b in baris]
        self._petak = (np.asarray(bm.x)[pakai], np.asarray(bm.y)[pakai],
                       np.asarray(bm.sx)[pakai], np.asarray(bm.sy)[pakai], warna)
        return self._petak

    def segarkan(self) -> None:
        self._petak = None
        self.update()

    # ---------------------------------------------------------------- koordinat

    def _w2p(self, x: float, y: float) -> QPointF:
        """dunia -> piksel. Northing naik ke ATAS layar (y piksel dibalik)."""
        k = self._px_per_m
        return QPointF(self.width() / 2.0 + (x - self._pusat[0]) * k,
                       self.height() / 2.0 - (y - self._pusat[1]) * k)

    def _p2w(self, px: float, py: float) -> Tuple[float, float]:
        k = self._px_per_m or 1.0
        return (self._pusat[0] + (px - self.width() / 2.0) / k,
                self._pusat[1] - (py - self.height() / 2.0) / k)

    def _tempel(self, x: float, y: float) -> Tuple[float, float]:
        """Tempel ke sudut blok terdekat bila `snap` -- supaya garis galian jatuh di batas blok."""
        if not self.snap or self.bm is None or not self.bm.n:
            return (x, y)
        P = self._petak or self._hitung_petak()
        if not len(P[0]):
            return (x, y)
        d = np.abs(P[0] - x) + np.abs(P[1] - y)
        i = int(np.argmin(d))
        hx, hy = float(P[2][i]) / 2.0, float(P[3][i]) / 2.0
        cx, cy = float(P[0][i]), float(P[1][i])
        kandidat = [(cx + sx * hx, cy + sy * hy) for sx in (-1, 1) for sy in (-1, 1)]
        kandidat.append((cx, cy))
        tdk = min(kandidat, key=lambda q: (q[0] - x) ** 2 + (q[1] - y) ** 2)
        if math.hypot(tdk[0] - x, tdk[1] - y) * self._px_per_m <= DEKAT_PX * 1.5:
            return tdk
        return (x, y)

    # ---------------------------------------------------------------- digitasi

    def mulai(self) -> None:
        self.digit_on = True
        self.titik = []
        self.setCursor(Qt.CrossCursor)
        self.update()

    def batal(self) -> None:
        self.digit_on = False
        self.titik = []
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def urungkan(self) -> None:
        if self.titik:
            self.titik.pop()
            self.update()
            self.titik_ditambah.emit()

    def tutup(self) -> bool:
        """Tutup poligon. False bila titiknya kurang dari 3 -- pemanggil yang memberi pesan."""
        if len(self.titik) < 3:
            return False
        self.digit_on = False
        self.setCursor(Qt.ArrowCursor)
        self.update()
        self.poligon_selesai.emit()
        return True

    def poligon(self) -> List[Tuple[float, float]]:
        return list(self.titik)

    # ---------------------------------------------------------------- tetikus

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.LeftButton and self.digit_on:
            x, y = self._tempel(*self._p2w(e.position().x(), e.position().y()))
            # klik di titik pertama = tutup poligon, sama dengan aplikasi HTML
            if len(self.titik) >= 3:
                p0 = self._w2p(*self.titik[0])
                if math.hypot(p0.x() - e.position().x(), p0.y() - e.position().y()) <= DEKAT_PX:
                    self.tutup()
                    return
            self.titik.append((x, y))
            self.update()
            self.titik_ditambah.emit()
            return
        self._seret = (e.position().x(), e.position().y())

    def mouseMoveEvent(self, e) -> None:
        w = self._p2w(e.position().x(), e.position().y())
        self._kursor = self._tempel(*w) if self.digit_on else w
        self.posisi_berubah.emit(self._kursor[0], self._kursor[1])
        if self._seret and (e.buttons() & (Qt.RightButton | Qt.MiddleButton)):
            dx = e.position().x() - self._seret[0]
            dy = e.position().y() - self._seret[1]
            self._seret = (e.position().x(), e.position().y())
            k = self._px_per_m or 1.0
            self._pusat = (self._pusat[0] - dx / k, self._pusat[1] + dy / k)
        self.update()

    def mouseReleaseEvent(self, e) -> None:
        self._seret = None

    def wheelEvent(self, e) -> None:
        """Zoom berpusat pada kursor, supaya yang dilihat tidak melompat saat memperbesar."""
        d = e.angleDelta().y() / 120.0
        if not d:
            return
        px, py = e.position().x(), e.position().y()
        sebelum = self._p2w(px, py)
        self._px_per_m = max(1e-4, self._px_per_m * (1.15 ** d))
        sesudah = self._p2w(px, py)
        self._pusat = (self._pusat[0] + sebelum[0] - sesudah[0],
                       self._pusat[1] + sebelum[1] - sesudah[1])
        self.update()

    def keyPressEvent(self, e) -> None:
        if not self.digit_on:
            super().keyPressEvent(e)
            return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.tutup()
        elif e.key() == Qt.Key_Backspace:
            self.urungkan()
        elif e.key() == Qt.Key_Escape:
            self.batal()
        else:
            super().keyPressEvent(e)

    def pas_ke_data(self) -> None:
        P = self._petak or self._hitung_petak()
        if not len(P[0]):
            return
        x0, x1 = float(P[0].min()), float(P[0].max())
        y0, y1 = float(P[1].min()), float(P[1].max())
        self._pusat = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        lebar = max(x1 - x0, 1.0)
        tinggi = max(y1 - y0, 1.0)
        self._px_per_m = min(self.width() / (lebar * 1.15), self.height() / (tinggi * 1.15))
        self.update()

    # ---------------------------------------------------------------- gambar

    def paintEvent(self, e) -> None:
        q = QPainter(self)
        q.fillRect(self.rect(), QColor("#11151c"))
        if self.bm is None or not self.bm.n:
            q.setPen(QPen(QColor("#8b97a8")))
            q.drawText(self.rect(), Qt.AlignCenter, "Muat block model dulu.")
            return
        P = self._petak or self._hitung_petak()
        q.setRenderHint(QPainter.Antialiasing, False)
        # blok flitch
        if len(P[0]):
            k = self._px_per_m
            # hanya blok yang benar-benar terlihat digambar: satu flitch model besar bisa berisi
            # puluhan ribu blok, dan menggambar yang di luar layar membuat panel terasa berat
            # tanpa menambah apa pun yang bisa dilihat.
            kiri, atas = self._p2w(0, 0)
            kanan, bawah = self._p2w(self.width(), self.height())
            tampak = np.nonzero((P[0] + P[2] / 2 >= kiri) & (P[0] - P[2] / 2 <= kanan)
                                & (P[1] + P[3] / 2 >= bawah) & (P[1] - P[3] / 2 <= atas))[0]
            for i in tampak:
                i = int(i)
                hx, hy = float(P[2][i]) / 2.0, float(P[3][i]) / 2.0
                a = self._w2p(float(P[0][i]) - hx, float(P[1][i]) + hy)
                q.fillRect(QRectF(a.x(), a.y(), float(P[2][i]) * k, float(P[3][i]) * k),
                           QColor(P[4][i]))
        q.setRenderHint(QPainter.Antialiasing, True)
        # string tersimpan
        for s in self.strings:
            if not s.tampil or len(s.pts) < 2:
                continue
            q.setPen(QPen(QColor(s.warna), 1.6))
            poly = QPolygonF([self._w2p(p[0], p[1]) for p in s.pts])
            if s.tertutup:
                q.drawPolygon(poly)
            else:
                q.drawPolyline(poly)
        # poligon yang sedang didigit
        if self.titik:
            pen = QPen(QColor("#ffd92f"), 2.0)
            q.setPen(pen)
            titik = [self._w2p(x, y) for x, y in self.titik]
            if self._kursor and self.digit_on:
                titik_hidup = titik + [self._w2p(*self._kursor)]
            else:
                titik_hidup = titik
            q.drawPolyline(QPolygonF(titik_hidup))
            for j, p in enumerate(titik):
                q.drawLine(QPointF(p.x() - 4, p.y()), QPointF(p.x() + 4, p.y()))
                q.drawLine(QPointF(p.x(), p.y() - 4), QPointF(p.x(), p.y() + 4))
                if j == 0 and len(self.titik) >= 3:
                    q.setPen(QPen(QColor("#ffffff"), 1.2))
                    q.drawEllipse(p, DEKAT_PX, DEKAT_PX)
                    q.setPen(pen)
        # keterangan: RL flitch selalu terlihat supaya tidak ada yang mendigit di bidang yang salah
        q.setPen(QPen(QColor("#dfe6f0")))
        f = QFont()
        f.setPointSize(9)
        q.setFont(f)
        teks = "Flitch RL %.2f – %.2f  ·  %d blok" % (self.B[0], self.B[1], len(P[0]))
        if self.digit_on:
            teks += "  ·  mendigit: %d titik (Enter tutup · Backspace urung · Esc batal)" \
                    % len(self.titik)
        if self._kursor:
            teks += "  ·  E %.1f  N %.1f" % (self._kursor[0], self._kursor[1])
        q.drawText(8, 16, teks)
        # skala: tanpa ini tidak ada cara menilai ukuran poligon dari gambar saja
        self._gambar_skala(q)

    def _gambar_skala(self, q: QPainter) -> None:
        k = self._px_per_m
        if k <= 0:
            return
        bagus = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]
        sasaran = 120.0 / k
        m = next((v for v in bagus if v >= sasaran), bagus[-1])
        px = m * k
        y = self.height() - 14
        q.setPen(QPen(QColor("#dfe6f0"), 1.4))
        q.drawLine(QPointF(12, y), QPointF(12 + px, y))
        q.drawLine(QPointF(12, y - 4), QPointF(12, y + 4))
        q.drawLine(QPointF(12 + px, y - 4), QPointF(12 + px, y + 4))
        q.drawText(QPointF(12 + px + 6, y + 4), "%g m" % m)
