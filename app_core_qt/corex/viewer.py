"""Pratinjau foto: QGraphicsView (scroll = zoom di titik kursor, tarik = geser, klik ganda = pas layar, putar 90 derajat,
resolusi penuh). Lapisan (overlay, tanda, segmen, kalibrasi) adalah anak item foto dalam koordinat gambar, jadi ikut zoom / putar."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (QFrame, QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView, QHBoxLayout,
                               QLabel, QToolButton, QWidget)

from . import api
from .theme import C
from .util import run_bg

PREVIEW_W = 2000


class Viewer(QGraphicsView):
    loaded = Signal(int)          # id foto selesai dimuat
    imageClicked = Signal(float, float, object)  # x, y (koordinat gambar), event

    def __init__(self) -> None:
        super().__init__()
        self.sc = QGraphicsScene(self)
        self.setScene(self.sc)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setBackgroundBrush(QColor(C["viewer"]))
        self.setMinimumHeight(160)
        # akar: kotak berukuran gambar pratinjau; foto & semua lapisan menjadi anaknya
        self.root = QGraphicsRectItem(0, 0, 1, 1)
        self.root.setPen(Qt.NoPen)
        self.sc.addItem(self.root)
        self.pix = QGraphicsPixmapItem(self.root)
        self.pix.setTransformationMode(Qt.SmoothTransformation)
        self.pix.setZValue(0)
        self.w = self.h = 0.0       # ukuran gambar (satuan pratinjau)
        self.pid: int | None = None
        self.folder = ""
        self.full = False
        self.rot = 0
        self.locked = False         # mode edit di foto: tarik tidak menggeser
        self.msg = QLabel(self)
        self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setStyleSheet("color:#9a978f;background:transparent")
        self.msg.setWordWrap(True)
        self.info = QLabel(self)
        self.info.setStyleSheet("background:rgba(246,245,241,.92);color:#141a26;padding:2px 8px;border-radius:4px;font-size:8.3pt")
        self.info.hide()
        self.tools = QWidget(self)
        self.tools.setObjectName("vtools")
        self.tools.setStyleSheet("#vtools{background:transparent}")
        lay = QHBoxLayout(self.tools)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.btn: dict[str, QToolButton] = {}
        for k, t, tip in (("zin", "+", "Perbesar"), ("zout", "−", "Perkecil"), ("fit", "⤢", "Pas layar (klik ganda)"),
                          ("rot", "↻", "Putar 90°"), ("full", "1:1", "Muat resolusi penuh (untuk membaca label kecil)")):
            b = QToolButton()
            b.setText(t)
            b.setToolTip(tip)
            lay.addWidget(b)
            self.btn[k] = b
        self.btn["zin"].clicked.connect(lambda: self.zoom(1.3))
        self.btn["zout"].clicked.connect(lambda: self.zoom(1 / 1.3))
        self.btn["fit"].clicked.connect(self.fit)
        self.btn["rot"].clicked.connect(self.rotate90)
        self.btn["full"].clicked.connect(self.load_full)
        self.placeholder("Pilih foto di tabel untuk melihat pratinjau.\nScroll = zoom, tarik = geser, klik ganda = pas layar.")

    def add_tool(self, k: str, text: str, tip: str, checkable: bool = False) -> QToolButton:
        b = QToolButton()
        b.setText(text)
        b.setToolTip(tip)
        b.setCheckable(checkable)
        self.tools.layout().addWidget(b)
        self.btn[k] = b
        self._place()
        return b

    # ---------------------------------------------------------------- tata letak label
    def resizeEvent(self, e) -> None:  # noqa: N802
        super().resizeEvent(e)
        self._place()
        if self.w and not getattr(self, "_zoomed", False):
            self.fit()

    def _place(self) -> None:
        self.msg.setGeometry(20, 20, self.width() - 40, self.height() - 40)
        self.tools.adjustSize()
        self.tools.move(self.width() - self.tools.width() - 8, 8)
        self.info.adjustSize()
        self.info.setMaximumWidth(self.width() - 16)
        self.info.move(8, self.height() - self.info.height() - 8)

    def placeholder(self, text: str) -> None:
        self.pix.setPixmap(QPixmap())
        self.w = self.h = 0
        self.msg.setText(text)
        self.msg.show()

    # ---------------------------------------------------------------- muat foto
    def show_photo(self, folder: str, r: dict) -> None:
        self.folder, self.pid, self.full, self.rot = folder, r["id"], False, 0
        self.root.setRotation(0)
        self.info.setText(r["rel"] + (" (file hilang)" if r.get("missing") else ""))
        self.info.show()
        self._place()
        if r.get("missing"):
            self.placeholder("File foto tidak ditemukan di folder.\nKlik Pindai ulang setelah file dikembalikan.")
            return
        pid = r["id"]
        run_bg(lambda: QImage(str(api.image_file(folder, pid, PREVIEW_W))), ok=lambda im: self._got(pid, im, False),
               err=lambda e: self.placeholder("Foto tidak bisa dibuka.\n" + e))

    def _got(self, pid: int, im: QImage, full: bool) -> None:
        if pid != self.pid or im.isNull():
            if im.isNull() and pid == self.pid:
                self.placeholder("Foto tidak bisa dibuka.")
            return
        self.msg.hide()
        pm = QPixmap.fromImage(im)
        if full and self.w:
            self.pix.setPixmap(pm)
            self.pix.setScale(self.w / pm.width())
            return
        self.pix.setScale(1)
        self.pix.setPixmap(pm)
        self.w, self.h = float(pm.width()), float(pm.height())
        self.root.setRect(0, 0, self.w, self.h)
        self.root.setTransformOriginPoint(self.w / 2, self.h / 2)
        self.sc.setSceneRect(QRectF(-self.w * 4, -self.h * 4, self.w * 9, self.h * 9))
        self._zoomed = False
        self.fit()
        self.loaded.emit(pid)

    def load_full(self) -> None:
        if self.pid is None or self.full or not self.w:
            return
        self.full = True
        pid, folder = self.pid, self.folder
        run_bg(lambda: QImage(str(api.image_file(folder, pid, 0))), ok=lambda im: self._got(pid, im, True))

    # ---------------------------------------------------------------- zoom / geser / putar
    def fit(self) -> None:
        if not self.w:
            return
        self.fitInView(self.root.mapRectToScene(self.root.rect()), Qt.KeepAspectRatio)
        self._zoomed = False

    def zoom(self, f: float) -> None:
        s = self.transform().m11() ** 2 + self.transform().m12() ** 2
        s = s ** 0.5
        if (s * f > 40 and f > 1) or (s * f < 0.02 and f < 1):
            return
        self.scale(f, f)
        self._zoomed = True

    def rotate90(self) -> None:
        if not self.w or self.locked:
            return
        self.rot = (self.rot + 90) % 360
        self.root.setRotation(self.rot)
        self.fit()

    def wheelEvent(self, e) -> None:  # noqa: N802
        if not self.w:
            return
        self.zoom(1.15 if e.angleDelta().y() > 0 else 1 / 1.15)

    def mouseDoubleClickEvent(self, e) -> None:  # noqa: N802
        if self.locked:
            return super().mouseDoubleClickEvent(e)
        self.fit()

    def set_locked(self, on: bool) -> None:
        self.locked = on
        self.setDragMode(QGraphicsView.NoDrag if on else QGraphicsView.ScrollHandDrag)
        self.btn["rot"].setEnabled(not on)

    def to_img(self, pos) -> QPointF:
        return self.root.mapFromScene(self.mapToScene(pos))

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if self.locked and e.button() == Qt.LeftButton and self.w:
            it = self.itemAt(e.position().toPoint())
            if it is None or it in (self.pix, self.root) or not (it.flags() & QGraphicsItem.ItemIsMovable or it.acceptHoverEvents()):
                p = self.to_img(e.position().toPoint())
                self.imageClicked.emit(p.x(), p.y(), e)
        super().mousePressEvent(e)

    def rotation_transform(self) -> QTransform:
        return self.root.sceneTransform()
