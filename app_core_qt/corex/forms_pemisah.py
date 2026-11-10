"""Garis pemisah lebar tetap untuk Transkrip (0.46.4, usul pemilik): seperti 'Text Import Wizard' Excel — teks salinan AI yang
rata kolom dengan spasi dipotong menjadi kolom pada garis yang ditarik pengguna.
  - klik pada penggaris / teks = buat garis; seret garis = pindahkan; klik ganda garis = hapus;
  - 'Usulkan otomatis' = garis di awal tiap pita karakter sesudah kolom yang kosong di (hampir) semua baris;
  - pratinjau kolom di bawah ikut berubah saat garis digeser.
Posisi garis = indeks karakter (tab dihitung 8 spasi), sama dengan core_transkrip.split_line(…, 'fixed', breaks)."""
from __future__ import annotations

import re

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontDatabase, QFontMetricsF, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QScrollArea, QTableWidget, QTableWidgetItem, QWidget

from . import api, theme  # noqa: F401  (api: path backend)
from .card import btn
from .dialogs import Dlg

from gcex_backend import core_transkrip as T  # noqa: E402

PREVIEW_ROWS = 8


def text_lines(teks: str) -> list[str]:
    """Baris teks persis seperti yang dipotong backend (indentasi dipertahankan, tab -> 8 spasi)."""
    return T.clean(teks or "", keep_indent=True).split("\n")


def is_label(ln: str) -> bool:
    t = ln.strip()
    return bool(T._LABEL.match(t)) and not re.search(r" {2,}", t)


class BreakRuler(QWidget):
    """Teks monospace + penggaris; garis pemisah biru bisa dibuat, digeser, dihapus dengan tetikus."""
    changed = Signal()
    GRAB = 5.0

    def __init__(self, lines: list[str], breaks: list[int]) -> None:
        super().__init__()
        self.lines = lines
        self.breaks = sorted({int(b) for b in breaks if int(b) > 0})
        f = theme.mono(9.5)  # font sendiri (stylesheet aplikasi menimpa setFont widget)
        if not QFontMetricsF(f).horizontalAdvance("i") == QFontMetricsF(f).horizontalAdvance("M"):
            f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
            f.setPointSizeF(9.5)
        self.mf = f
        fm = QFontMetricsF(f)
        self.cw = fm.horizontalAdvance("M")
        self.lh = fm.lineSpacing() + 2
        self.asc = fm.ascent()
        self.top, self.left = 24.0, 8.0
        self.width_ch = max([len(ln) for ln in lines] + [20]) + 10
        self.drag: int | None = None
        self.hover: int | None = None
        self.setMouseTracking(True)
        self.setCursor(Qt.IBeamCursor)
        self.setToolTip("Klik = buat garis pemisah · seret garis = pindahkan · klik ganda garis = hapus")

    def sizeHint(self) -> QSize:
        return QSize(int(self.left + self.cw * self.width_ch + 12), int(self.top + self.lh * max(1, len(self.lines)) + 10))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    # ---- geometri
    def x_of(self, p: int) -> float:
        return self.left + p * self.cw

    def pos_at(self, x: float) -> int:
        return max(1, min(self.width_ch, round((x - self.left) / self.cw)))

    def near(self, x: float) -> int | None:
        best, bd = None, self.GRAB + 1
        for i, b in enumerate(self.breaks):
            d = abs(self.x_of(b) - x)
            if d <= self.GRAB and d < bd:
                best, bd = i, d
        return best

    def set_breaks(self, bs: list[int]) -> None:
        self.breaks = sorted({int(b) for b in bs if int(b) > 0})
        self.update()
        self.changed.emit()

    # ---- tetikus
    def mousePressEvent(self, e) -> None:
        if e.button() != Qt.LeftButton:
            return
        x = e.position().x()
        i = self.near(x)
        if i is None:
            p = self.pos_at(x)
            if p in self.breaks:
                i = self.breaks.index(p)
            else:
                self.breaks = sorted(self.breaks + [p])
                i = self.breaks.index(p)
        self.drag = i
        self.update()

    def mouseMoveEvent(self, e) -> None:
        x = e.position().x()
        if self.drag is not None:
            p = self.pos_at(x)
            others = self.breaks[:self.drag] + self.breaks[self.drag + 1:]
            if p not in others:
                self.breaks[self.drag] = p
                order = sorted(range(len(self.breaks)), key=lambda k: self.breaks[k])
                self.drag = order.index(self.drag)
                self.breaks.sort()
                self.update()
            return
        h = self.near(x)
        if h != self.hover:
            self.hover = h
            self.setCursor(Qt.SplitHCursor if h is not None else Qt.IBeamCursor)
            self.update()

    def mouseReleaseEvent(self, e) -> None:
        if self.drag is not None:
            self.drag = None
            self.update()
            self.changed.emit()

    def mouseDoubleClickEvent(self, e) -> None:
        i = self.near(e.position().x())
        if i is not None:
            del self.breaks[i]
            self.drag = self.hover = None
            self.setCursor(Qt.IBeamCursor)
            self.update()
            self.changed.emit()

    def leaveEvent(self, e) -> None:
        if self.hover is not None:
            self.hover = None
            self.update()

    # ---- gambar
    def paintEvent(self, _e) -> None:
        c = theme.C
        p = QPainter(self)
        p.setFont(self.mf)
        W, H = float(self.width()), float(self.height())
        p.fillRect(self.rect(), QColor(c["pn"]))
        # pita kolom berselang (kolom genap diberi warna lembut)
        cuts = [0] + self.breaks + [self.width_ch + 10]
        band = QColor(c["acs"])
        for k, (a, b) in enumerate(zip(cuts, cuts[1:])):
            if k % 2:
                p.fillRect(QRectF(self.x_of(a), self.top, (b - a) * self.cw, H - self.top), band)
        # penggaris
        p.fillRect(QRectF(0, 0, W, self.top - 2), QColor(c["pn2"]))
        p.setPen(QPen(QColor(c["mu"]), 1))
        for i in range(self.width_ch + 1):
            x = self.x_of(i)
            h = 9 if i % 10 == 0 else (6 if i % 5 == 0 else 3)
            p.drawLine(QPointF(x, self.top - 2 - h), QPointF(x, self.top - 2))
            if i % 10 == 0 and i:
                p.drawText(QPointF(x + 2, 11), str(i))
        p.setFont(self.mf)
        # teks
        ink, mute = QColor(c["tx"]), QColor(c["mu"])
        for r, ln in enumerate(self.lines):
            y = self.top + r * self.lh + self.asc + 1
            p.setPen(mute if is_label(ln) else ink)
            p.drawText(QPointF(self.left, y), ln)
        # garis pemisah
        acc = QColor(c["ac2"])
        for i, b in enumerate(self.breaks):
            x = self.x_of(b)
            hot = i in (self.drag, self.hover)
            p.setPen(QPen(acc, 2.5 if hot else 1.6))
            p.drawLine(QPointF(x, self.top - 2), QPointF(x, H))
            p.setBrush(acc)
            p.setPen(Qt.NoPen)
            p.drawPolygon(QPolygonF([QPointF(x - 5, self.top - 10), QPointF(x + 5, self.top - 10), QPointF(x, self.top - 2)]))
        p.end()


class BreakDialog(Dlg):
    """Dialog 'Garis pemisah' — hasil di .breaks (daftar posisi karakter) bila diterima."""

    def __init__(self, parent, teks: str, breaks: list[int] | None) -> None:
        super().__init__(parent, "Garis pemisah kolom", "<b>Garis pemisah kolom</b> &nbsp;·&nbsp; teks rata kolom (lebar tetap)", w=760)
        self.lines = text_lines(teks)
        self.data_lines = [ln for ln in self.lines if ln.strip() and not is_label(ln) and not ln.lstrip().startswith("#")]
        auto = T.auto_breaks(self.data_lines)
        self.breaks = list(breaks) if breaks else auto
        self.auto = auto
        note = QLabel("Garis biru = batas kolom, seperti saat membuka file teks di Excel.<br>"
                      "• <b>Klik</b> pada penggaris atau teks untuk membuat garis.<br>"
                      "• <b>Seret</b> garis untuk memindahkannya.&nbsp;&nbsp;• <b>Klik ganda</b> garis untuk menghapusnya.<br>"
                      "Baris abu-abu ('Label: nilai') tetap menjadi isian kop, tidak dipotong.")
        note.setObjectName("note")
        note.setTextFormat(Qt.RichText)
        note.setWordWrap(True)
        self.body.addWidget(note)
        self.ruler = BreakRuler(self.lines, self.breaks)
        sa = QScrollArea()
        sa.setWidget(self.ruler)
        sa.setWidgetResizable(False)
        sa.setMinimumHeight(220)
        self.body.addWidget(sa, 3)
        self.lbl = QLabel()
        self.lbl.setObjectName("note")
        self.body.addWidget(self.lbl)
        self.pv = QTableWidget(0, 0)
        self.pv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pv.verticalHeader().setVisible(False)
        self.pv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.pv.setMinimumHeight(150)
        self.body.addWidget(self.pv, 2)
        bAuto = btn("Usulkan otomatis", "Garis di awal tiap kolom karakter yang dipisah spasi kosong di (hampir) semua baris", sm=True)
        bAuto.clicked.connect(lambda: self.ruler.set_breaks(self.auto))
        bClr = btn("Hapus semua garis", sm=True)
        bClr.clicked.connect(lambda: self.ruler.set_breaks([]))
        self.foot.addWidget(bAuto)
        self.foot.addWidget(bClr)
        self.foot.addStretch(1)
        bNo = btn("Batal")
        bNo.clicked.connect(self.reject)
        self.bOk = btn("Pakai garis ini ▶", pri=True)
        self.bOk.clicked.connect(self._ok)
        self.foot.addWidget(bNo)
        self.foot.addWidget(self.bOk)
        self.ruler.changed.connect(self._refresh)
        self.resize(900, 600)
        self._refresh()

    def _refresh(self) -> None:
        bs = self.ruler.breaks
        rows = [T.split_line(ln, "fixed", bs) or [] for ln in self.data_lines[:PREVIEW_ROWS]]
        n = max([len(r) for r in rows] + [0])
        self.pv.clear()
        self.pv.setColumnCount(n)
        self.pv.setRowCount(len(rows))
        self.pv.setHorizontalHeaderLabels([f"Kolom {i + 1}" for i in range(n)])
        for r, cells in enumerate(rows):
            for c_, v in enumerate(cells):
                self.pv.setItem(r, c_, QTableWidgetItem(v))
        self.lbl.setText(f"{len(bs)} garis → <b>{len(bs) + 1} kolom</b> · pratinjau {len(rows)} dari {len(self.data_lines)} baris tabel"
                         if self.data_lines else "Belum ada baris tabel di teks.")
        self.lbl.setTextFormat(Qt.RichText)
        self.bOk.setEnabled(bool(bs))

    def _ok(self) -> None:
        self.breaks = list(self.ruler.breaks)
        self.accept()
