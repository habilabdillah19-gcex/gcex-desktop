"""Ruang kerja Singkapan: foto singkapan / trenching hasil mapping lapangan.

Kiri: daftar foto (+ Foto). Tengah: foto dengan garis / poligon / label (editor). Kanan: tab Deskripsi (AI lokal + edit),
Fitur (gambar, atribut, belah / gabung, pustaka jenis fitur) dan Infografis (template, judul, kotak komposit, ekspor PNG / PDF).
Data lewat rute /core/outcrop/* (backend yang sama dengan Core box)."""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QColorDialog, QComboBox, QFileDialog, QFormLayout, QFrame, QGraphicsObject,
                               QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit,
                               QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from . import api, oc_paint, theme
from .card import _esc, btn
from .dialogs import Dlg, ask, say
from .util import SET, log, run_bg, show_in_folder
from .viewer import Viewer

PREVIEW = 2400


def _f(v) -> str:
    return "" if v is None else oc_paint.fmtv(v)


def _num(t: str):
    t = (t or "").strip().replace(",", ".")
    if not t:
        return None
    return float(t)


# ================================================================ pratinjau foto singkapan
class OcView(Viewer):
    """Viewer yang memuat file foto langsung (bukan foto core box)."""

    def show_file(self, path: Path, key: int) -> None:
        self.folder, self.pid, self.full, self.rot = "", key, False, 0
        self.root.setRotation(0)
        self.info.setText(path.name)
        self.info.show()
        self._place()
        if not path.exists():
            self.placeholder("File foto tidak ditemukan di folder proyek (_GCEx_Core/singkapan/foto).")
            return
        self._path = path
        run_bg(lambda: oc_paint.load_image(path, PREVIEW), ok=lambda im: self._got(key, im, False),
               err=lambda e: self.placeholder("Foto tidak bisa dibuka.\n" + e))

    def load_full(self) -> None:
        if self.pid is None or self.full or not self.w or not getattr(self, "_path", None):
            return
        self.full = True
        pid, path = self.pid, self._path
        run_bg(lambda: oc_paint.load_image(path, 0), ok=lambda im: self._got(pid, im, True))

    def mouseDoubleClickEvent(self, e) -> None:  # noqa: N802
        t = self.tool
        if t is not None and self.w and hasattr(t, "dbl"):
            t.dbl(self.to_img(e.position().toPoint()))
            e.accept()
            return
        super().mouseDoubleClickEvent(e)

    def keyPressEvent(self, e) -> None:  # noqa: N802
        t = self.tool
        if t is not None and hasattr(t, "key") and t.key(e.key()):
            e.accept()
            return
        super().keyPressEvent(e)


class OcCanvas(QGraphicsObject):
    def __init__(self, page: "OutcropPage"):
        super().__init__(page.view.root)
        self.pg = page
        self.setZValue(5)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self) -> QRectF:  # noqa: N802
        v = self.pg.view
        return QRectF(0, 0, max(1.0, v.w), max(1.0, v.h))

    def paint(self, p: QPainter, opt, w=None) -> None:
        pg, v = self.pg, self.pg.view
        if not v.w or not pg.cur:
            return
        t = pg.tool
        boxes: list = []
        oc_paint.paint_scene(p, v.w, v.h, pg.feats, pg.kmap, pg.info(), desc=pg.cur.get("desc"), m_per_unit=pg.m_per_unit(),
                             sel=t.sel, sel_vertex=t.vsel, handle=v.px(5), draft=t.draft_pts(), draft_kind=pg.kmap.get(t.kind),
                             boxes_out=boxes, show_info=pg.cbInfo.isChecked())
        pg.boxes = boxes


# ================================================================ alat edit
class OcTool:
    """mode: 'select' | 'draw'. Titik disimpan ternormalisasi 0..1; snap ke titik / garis fitur lain."""

    def __init__(self, page: "OutcropPage"):
        self.pg = page
        self.mode = "select"
        self.kind = ""
        self.pts: list[list[float]] = []
        self.hover_pt: list[float] | None = None
        self.sel: int | None = None
        self.vsel: int | None = None
        self.drag: dict | None = None

    # ---- konversi
    def norm(self, pt: QPointF) -> list[float]:
        v = self.pg.view
        return [max(0.0, min(1.0, pt.x() / v.w)), max(0.0, min(1.0, pt.y() / v.h))]

    def tol(self) -> float:
        v = self.pg.view
        return v.px(10)

    def snap(self, q: list[float], skip: int | None = None) -> list[float]:
        """Snap ke titik fitur lain lalu ke garis fitur lain (agar kontak antarfitur tidak bercelah)."""
        if not self.pg.cbSnap.isChecked():
            return q
        v = self.pg.view
        x, y, tol = q[0] * v.w, q[1] * v.h, self.tol()
        best, bd = None, tol
        for f in self.pg.feats:
            if f["id"] == skip:
                continue
            for u, w_ in f["pts"]:
                d = ((u * v.w - x) ** 2 + (w_ * v.h - y) ** 2) ** 0.5
                if d < bd:
                    best, bd = [u, w_], d
        if best:
            return best
        for f in self.pg.feats:
            if f["id"] == skip or f["shape"] == "point":
                continue
            P = f["pts"] + ([f["pts"][0]] if f["shape"] == "poly" else [])
            for a, b in zip(P, P[1:]):
                ax, ay, bx, by = a[0] * v.w, a[1] * v.h, b[0] * v.w, b[1] * v.h
                dx, dy = bx - ax, by - ay
                L2 = dx * dx + dy * dy
                if L2 < 1e-9:
                    continue
                t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
                px, py = ax + t * dx, ay + t * dy
                d = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
                if d < bd:
                    best, bd = [px / v.w, py / v.h], d
        return best or q

    def draft_pts(self):
        if self.mode != "draw" or not self.pts:
            return None
        return self.pts + ([self.hover_pt] if self.hover_pt else [])

    # ---- hit test
    def _feat_at(self, pt: QPointF) -> int | None:
        v, tol = self.pg.view, self.tol()
        for fid, r, _k in reversed(self.pg.boxes):
            if r.contains(pt) and fid > 0:
                return fid
        best, bd = None, tol
        for f in reversed(self.pg.feats):
            P = [QPointF(u * v.w, w_ * v.h) for u, w_ in f["pts"]]
            if f["shape"] == "point":
                d = ((P[0].x() - pt.x()) ** 2 + (P[0].y() - pt.y()) ** 2) ** 0.5
                if d < bd:
                    best, bd = f["id"], d
                continue
            Q = P + ([P[0]] if f["shape"] == "poly" else [])
            for a, b in zip(Q, Q[1:]):
                d = _seg_dist(pt, a, b)
                if d < bd:
                    best, bd = f["id"], d
        if best is None:
            for f in reversed(self.pg.feats):
                if f["shape"] == "poly":
                    from PySide6.QtGui import QPolygonF
                    if QPolygonF([QPointF(u * v.w, w_ * v.h) for u, w_ in f["pts"]]).containsPoint(pt, Qt.OddEvenFill):
                        return f["id"]
        return best

    def _vertex_at(self, pt: QPointF) -> int | None:
        f = self.pg.feat(self.sel)
        if not f:
            return None
        v, tol = self.pg.view, self.tol()
        for i, (u, w_) in enumerate(f["pts"]):
            if ((u * v.w - pt.x()) ** 2 + (w_ * v.h - pt.y()) ** 2) ** 0.5 < tol:
                return i
        return None

    # ---- peristiwa mouse
    def hover(self, pt):
        if self.mode == "draw":
            self.hover_pt = self.snap(self.norm(pt))
            self.pg.canvas.update()
            return Qt.CrossCursor
        if self._vertex_at(pt) is not None:
            return Qt.SizeAllCursor
        if any(r.contains(pt) for _f, r, _k in self.pg.boxes):
            return Qt.OpenHandCursor
        return Qt.PointingHandCursor if self._feat_at(pt) is not None else None

    def press(self, pt, e) -> bool:
        if self.mode == "draw":
            self.pts.append(self.snap(self.norm(pt)))
            shape = (self.pg.kmap.get(self.kind) or {}).get("shape")
            if shape == "point":
                self.finish()
            self.pg.canvas.update()
            return True
        vi = self._vertex_at(pt)
        if vi is not None:
            self.vsel = vi
            self.drag = {"type": "v", "i": vi, "moved": False}
            self.pg.canvas.update()
            self.pg.sel_changed()
            return True
        for fid, r, k in reversed(self.pg.boxes):
            if r.contains(pt):
                self.drag = {"type": k, "fid": fid, "off": QPointF(pt.x() - r.center().x(), pt.y() - r.center().y()), "moved": False}
                if fid > 0:
                    self.select(fid)
                return True
        fid = self._feat_at(pt)
        self.select(fid)
        return fid is not None

    def move(self, pt) -> None:
        d = self.drag
        if not d:
            return
        v = self.pg.view
        d["moved"] = True
        if d["type"] == "v":
            f = self.pg.feat(self.sel)
            if f:
                f["pts"][d["i"]] = self.snap(self.norm(pt), skip=f["id"])
        elif d["type"] in ("box", "pt"):
            f = self.pg.feat(d["fid"])
            c = QPointF(pt.x() - d["off"].x(), pt.y() - d["off"].y())
            if f and d["type"] == "box":
                f["attrs"]["box_u"], f["attrs"]["box_v"] = round(c.x() / v.w, 4), round(c.y() / v.h, 4)
            elif f:
                f["pts"][0] = self.norm(c)
        elif d["type"] == "comp":
            c = QPointF(pt.x() - d["off"].x(), pt.y() - d["off"].y())
            self.pg.comp_pos = (round(c.x() / v.w, 4), round(c.y() / v.h, 4))
        self.pg.canvas.update()

    def release(self, pt) -> None:
        d, self.drag = self.drag, None
        if not d or not d.get("moved"):
            return
        if d["type"] == "comp":
            u, v = self.pg.comp_pos
            self.pg.save_info({"comp_u": u, "comp_v": v})
            return
        f = self.pg.feat(self.sel if d["type"] == "v" else d["fid"])
        if f:
            self.pg.save_feat(f)

    def dbl(self, pt) -> None:
        if self.mode == "draw":
            if self.pts and len(self.pts) > 1 and self.pts[-1] == self.pts[-2]:
                self.pts.pop()
            self.finish()
            return
        f = self.pg.feat(self.sel)
        if not f or f["shape"] == "point":
            return
        v = self.pg.view
        P = [QPointF(u * v.w, w_ * v.h) for u, w_ in f["pts"]]
        Q = P + ([P[0]] if f["shape"] == "poly" else [])
        best, bd = None, self.tol()
        for i, (a, b) in enumerate(zip(Q, Q[1:])):
            dd = _seg_dist(pt, a, b)
            if dd < bd:
                best, bd = i, dd
        if best is not None:  # klik ganda di garis fitur terpilih: sisipkan titik
            f["pts"].insert(best + 1, self.norm(pt))
            self.vsel = best + 1
            self.pg.save_feat(f)

    def key(self, k) -> bool:
        if self.mode == "draw":
            if k in (Qt.Key_Return, Qt.Key_Enter):
                self.finish()
                return True
            if k == Qt.Key_Backspace and self.pts:
                self.pts.pop()
                self.pg.canvas.update()
                return True
            if k == Qt.Key_Escape:
                self.cancel()
                return True
            return False
        if k == Qt.Key_Delete:
            self.pg.delete_selected()
            return True
        if k == Qt.Key_Escape and self.sel is not None:
            self.select(None)
            return True
        return False

    # ---- aksi
    def start_draw(self, kind: str) -> None:
        self.mode, self.kind, self.pts, self.hover_pt = "draw", kind, [], None
        self.select(None)
        self.pg.view.setFocus()
        self.pg.hint()

    def cancel(self) -> None:
        self.mode, self.pts, self.hover_pt = "select", [], None
        self.pg.draw_done()

    def finish(self) -> None:
        kind = self.kind
        shape = (self.pg.kmap.get(kind) or {}).get("shape", "line")
        need = {"point": 1, "line": 2, "poly": 3}[shape]
        pts = self.pts
        self.mode, self.pts, self.hover_pt = "select", [], None
        if len(pts) >= need:
            name = ""
            if shape == "point":
                name = self.pg.ask_text("Teks label:", "")
                if not name:
                    self.pg.draw_done()
                    return
            self.pg.new_feat(kind, pts, name)
        self.pg.draw_done()

    def select(self, fid) -> None:
        if fid != self.sel:
            self.vsel = None
        self.sel = fid
        self.pg.sel_changed()
        self.pg.canvas.update()


def _seg_dist(p: QPointF, a: QPointF, b: QPointF) -> float:
    dx, dy = b.x() - a.x(), b.y() - a.y()
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / L2))
    x, y = a.x() + t * dx, a.y() + t * dy
    return ((p.x() - x) ** 2 + (p.y() - y) ** 2) ** 0.5


# ================================================================ dialog pustaka jenis fitur
class KindsDlg(Dlg):
    def __init__(self, parent, kinds: list[dict]):
        super().__init__(parent, "Jenis fitur & nomor string Surpac", "Jenis fitur <span style='color:#a9c3dd'>&amp; nomor string Surpac</span>", 640)
        self.kinds = [dict(k) for k in kinds]
        n = QLabel("Nomor string dipakai saat ekspor STR Surpac (satu nomor untuk satu jenis). Warna dipakai di foto, legenda dan DXF. "
                   "Jenis bawaan tidak bisa dihapus; tambahkan jenis sendiri bila perlu (mis. dike, kontak perlapisan).")
        n.setWordWrap(True)
        n.setObjectName("note")
        self.body.addWidget(n)
        self.t = QTableWidget(0, 4)
        self.t.setHorizontalHeaderLabels(["Nama", "Bentuk", "Warna", "No. string"])
        self.t.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.t.verticalHeader().hide()
        self.t.setMinimumHeight(360)
        self.body.addWidget(self.t)
        add = btn("+ Jenis baru", sm=True)
        add.clicked.connect(self._add)
        self.body.addWidget(add, 0, Qt.AlignLeft)
        ok, cl = btn("Simpan", pri=True), btn("Batal")
        self.foot.addStretch(1)
        self.foot.addWidget(cl)
        self.foot.addWidget(ok)
        ok.clicked.connect(self.accept)
        cl.clicked.connect(self.reject)
        self._fill()

    def _fill(self) -> None:
        self.t.setRowCount(0)
        for k in self.kinds:
            r = self.t.rowCount()
            self.t.insertRow(r)
            it = QTableWidgetItem(k["name"])
            self.t.setItem(r, 0, it)
            sh = QComboBox()
            for v, l in (("line", "garis"), ("poly", "poligon"), ("point", "titik / label")):
                sh.addItem(l, v)
            sh.setCurrentIndex(max(0, sh.findData(k["shape"])))
            sh.setEnabled(not k.get("builtin"))
            self.t.setCellWidget(r, 1, sh)
            cb = QPushButton(k["color"])
            cb.setStyleSheet(f"background:{k['color']};color:{'#141a26' if QColor(k['color']).lightness() > 140 else '#ffffff'}")
            cb.clicked.connect(lambda _=False, r=r: self._color(r))
            self.t.setCellWidget(r, 2, cb)
            sp = QSpinBox()
            sp.setRange(1, 32000)
            sp.setValue(int(k["string"]))
            self.t.setCellWidget(r, 3, sp)

    def _color(self, r: int) -> None:
        self._read()
        c = QColorDialog.getColor(QColor(self.kinds[r]["color"]), self, "Warna " + self.kinds[r]["name"])
        if c.isValid():
            self.kinds[r]["color"] = c.name()
            self._fill()

    def _add(self) -> None:
        self._read()
        used = {k["string"] for k in self.kinds}
        sn = next(i for i in range(20, 32000) if i not in used)
        self.kinds.append({"key": f"jenis_{len(self.kinds) + 1}", "name": "Jenis baru", "shape": "line", "color": "#7a5aa6", "string": sn, "builtin": False})
        self._fill()

    def _read(self) -> None:
        for r, k in enumerate(self.kinds):
            k["name"] = self.t.item(r, 0).text().strip() or k["name"]
            k["shape"] = self.t.cellWidget(r, 1).currentData()
            k["string"] = self.t.cellWidget(r, 3).value()

    def result_kinds(self) -> list[dict]:
        self._read()
        for k in self.kinds:
            if not k.get("builtin") and k["key"].startswith("jenis_"):
                k["key"] = re.sub(r"[^a-z0-9]+", "_", k["name"].lower()).strip("_") or k["key"]
        return self.kinds


# ================================================================ halaman Singkapan
class OutcropPage(QWidget):
    changed = Signal()

    def __init__(self, win) -> None:
        super().__init__()
        self.win = win
        self.folder = ""
        self.photos: list[dict] = []
        self.kinds: list[dict] = []
        self.kmap: dict[str, dict] = {}
        self.desc_fields: list[dict] = []
        self.cur: dict | None = None
        self.feats: list[dict] = []
        self.scale: dict | None = None
        self.boxes: list = []
        self.comp_pos: tuple | None = None
        self.ai_busy = False
        self._build()

    # ---------------------------------------------------------------- tata letak
    def _build(self) -> None:
        o = QHBoxLayout(self)
        o.setContentsMargins(0, 0, 0, 0)
        sp = QSplitter(Qt.Horizontal)
        sp.setHandleWidth(5)
        o.addWidget(sp)
        # kiri: daftar foto
        lw = QWidget()
        lv = QVBoxLayout(lw)
        lv.setContentsMargins(10, 10, 6, 10)
        hd = QLabel("<b>FOTO SINGKAPAN</b>")
        hd.setObjectName("note")
        lv.addWidget(hd)
        r = QHBoxLayout()
        self.bAdd = btn("+ Foto", "Tambah foto singkapan / trenching (disalin ke folder proyek)", pri=True, sm=True)
        self.bDel = btn("Hapus", "Hapus foto singkapan terpilih dari proyek", sm=True)
        r.addWidget(self.bAdd)
        r.addWidget(self.bDel)
        r.addStretch(1)
        lv.addLayout(r)
        self.lst = QListWidget()
        self.lst.setIconSize(QSize(92, 60))
        self.lst.setSelectionMode(QAbstractItemView.SingleSelection)
        lv.addWidget(self.lst, 1)
        self.sum = QLabel()
        self.sum.setObjectName("note")
        self.sum.setWordWrap(True)
        lv.addWidget(self.sum)
        sp.addWidget(lw)
        # tengah: foto + bilah alat
        cw = QWidget()
        cv = QVBoxLayout(cw)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        tb = QFrame()
        tb.setObjectName("fbar")
        th = QHBoxLayout(tb)
        th.setContentsMargins(10, 5, 10, 5)
        th.setSpacing(6)
        self.bSel = btn("Pilih / edit", "Pilih fitur, geser titik (snap), geser kotak kadar. Klik ganda di garis = sisipkan titik. Delete = hapus.", sm=True)
        self.bSel.setCheckable(True)
        self.bSel.setChecked(True)
        th.addWidget(self.bSel)
        th.addWidget(QLabel("GAMBAR"))
        self.cbKind = QComboBox()
        self.cbKind.setMinimumWidth(190)
        self.cbKind.setToolTip("Jenis fitur yang akan digambar")
        th.addWidget(self.cbKind)
        self.bDraw = btn("✎ Gambar", "Klik titik demi titik di foto. Klik ganda / Enter = selesai, Backspace = hapus titik terakhir, Esc = batal.", pri=True, sm=True)
        th.addWidget(self.bDraw)
        self.cbSnap = QCheckBox("Snap")
        self.cbSnap.setChecked(True)
        self.cbSnap.setToolTip("Tempelkan titik ke titik / garis fitur lain agar kontak tidak bercelah")
        th.addWidget(self.cbSnap)
        self.cbInfo = QCheckBox("Infografis")
        self.cbInfo.setChecked(True)
        self.cbInfo.setToolTip("Tampilkan judul, kotak kadar, legenda, bar skala seperti hasil ekspor")
        th.addWidget(self.cbInfo)
        th.addStretch(1)
        self.hintL = QLabel()
        self.hintL.setObjectName("note")
        self.hintL.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        th.addWidget(self.hintL, 2)
        cv.addWidget(tb)
        self.view = OcView()
        self.view.placeholder("Tambahkan foto singkapan / trenching dengan + Foto.\nScroll = zoom, tarik = geser, klik ganda = pas layar.")
        cv.addWidget(self.view, 1)
        sp.addWidget(cw)
        self.canvas = OcCanvas(self)
        self.tool = OcTool(self)
        self.view.set_tool(self.tool)
        self.view.set_locked(False)
        self.view.loaded.connect(lambda *_: self.canvas.update())
        # kanan: tab
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(340)
        self.tabs.addTab(self._tab_desc(), "Deskripsi")
        self.tabs.addTab(self._tab_feat(), "Fitur")
        self.tabs.addTab(self._tab_info(), "Infografis")
        sp.addWidget(self.tabs)
        sp.setStretchFactor(1, 1)
        sp.setSizes(SET.get("qt_oc_split", [240, 900, 380]))
        sp.splitterMoved.connect(lambda *_: SET.set("qt_oc_split", sp.sizes()))
        self.bAdd.clicked.connect(self.add_photo)
        self.bDel.clicked.connect(self.delete_photo)
        self.lst.currentRowChanged.connect(self._pick)
        self.bDraw.clicked.connect(lambda: self.tool.start_draw(self.cbKind.currentData()) if self.cur else None)
        self.bSel.clicked.connect(lambda: (self.tool.cancel(), self.bSel.setChecked(True)))
        self.cbInfo.toggled.connect(lambda *_: self.canvas.update())
        self.set_enabled(False)
        self.hint()

    def _scroll(self, w: QWidget) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sa.setWidget(w)
        return sa

    def _tab_desc(self) -> QWidget:
        w = QWidget()
        w.setObjectName("card")
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)
        g = QFormLayout()
        g.setLabelAlignment(Qt.AlignLeft)
        self.eTitle, self.eLoc, self.eTaken = QLineEdit(), QLineEdit(), QLineEdit()
        self.eTitle.setPlaceholderText("mis. Trenching Sebunga Pit RL256 Blok 11")
        self.eLoc.setPlaceholderText("pit / RL / blok / koordinat kasar")
        self.eTaken.setPlaceholderText("tanggal foto")
        for lab, e, k in (("Judul", self.eTitle, "title"), ("Lokasi", self.eLoc, "location"), ("Tanggal", self.eTaken, "taken")):
            g.addRow(lab, e)
            e.editingFinished.connect(lambda k=k, e=e: self._save_col(k, e.text()))
        v.addLayout(g)
        r = QHBoxLayout()
        self.bAI = btn("Deskripsikan dengan AI", "AI lokal (Ollama) mendeskripsikan singkapan: litologi, alterasi, pelapukan ISRM, vein, struktur, GSI", pri=True, sm=True)
        self.bAI.clicked.connect(self.run_ai)
        r.addWidget(self.bAI)
        r.addStretch(1)
        v.addLayout(r)
        self.aiInfo = QLabel()
        self.aiInfo.setObjectName("note")
        self.aiInfo.setWordWrap(True)
        v.addWidget(self.aiInfo)
        self.dw: dict[str, QWidget] = {}
        self.dTag: dict[str, QLabel] = {}
        self.descBox = QVBoxLayout()
        self.descBox.setSpacing(5)
        v.addLayout(self.descBox)
        self.histBtn = QToolButton()
        self.histBtn.setText("▸  Riwayat perubahan && jawaban asli AI")
        self.histBtn.setCheckable(True)
        self.histBtn.setStyleSheet("border:0;background:transparent;text-align:left")
        self.histTxt = QLabel()
        self.histTxt.setWordWrap(True)
        self.histTxt.setTextFormat(Qt.RichText)
        self.histTxt.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.histTxt.hide()
        self.histBtn.toggled.connect(self._hist)
        v.addWidget(self.histBtn)
        v.addWidget(self.histTxt)
        n = QLabel("Isian biru muda = isian AI yang belum dicek. Isian yang Anda edit tidak ditimpa saat AI dijalankan ulang. "
                   "Nilai dari foto hanyalah perkiraan visual; tetap diperiksa geologist.")
        n.setObjectName("note")
        n.setWordWrap(True)
        v.addWidget(n)
        v.addStretch(1)
        return self._scroll(w)

    def _build_desc(self) -> None:
        while self.descBox.count():
            it = self.descBox.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
                it.widget().deleteLater()
        self.dw, self.dTag = {}, {}
        for d in self.desc_fields:
            k = d["key"]
            fr = QFrame()
            fr.setObjectName("fld")
            fv = QVBoxLayout(fr)
            fv.setContentsMargins(8, 4, 8, 5)
            fv.setSpacing(1)
            h = QHBoxLayout()
            l = QLabel(d["label"].upper())
            l.setObjectName("fl")
            tag = QLabel()
            tag.setObjectName("tag")
            h.addWidget(l)
            h.addStretch(1)
            h.addWidget(tag)
            fv.addLayout(h)
            if k == "photo_type":
                e = QComboBox()
                for val, t in (("", "—"), ("wall", "Dinding (wall)"), ("floor", "Lantai (floor)")):
                    e.addItem(t, val)
                e.activated.connect(lambda *_, k=k, e=e: self._save_desc(k, e.currentData()))
            elif k in ("lithology", "gsi", "joint_spacing", "weathering"):
                e = QLineEdit()
                e.editingFinished.connect(lambda k=k, e=e: self._save_desc(k, e.text()))
            else:
                e = QPlainTextEdit()
                e.setFixedHeight(54)
                orig = e.focusOutEvent

                def fo(ev, k=k, e=e, orig=orig):
                    orig(ev)
                    self._save_desc(k, e.toPlainText())
                e.focusOutEvent = fo
            fv.addWidget(e)
            self.descBox.addWidget(fr)
            self.dw[k], self.dTag[k] = e, tag
            fr.setProperty("k", k)

    def _tab_feat(self) -> QWidget:
        w = QWidget()
        w.setObjectName("card")
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)
        self.fList = QListWidget()
        self.fList.setMinimumHeight(170)
        v.addWidget(self.fList)
        self.fList.currentRowChanged.connect(lambda i: self.tool.select(self.feats[i]["id"]) if 0 <= i < len(self.feats) and
                                             self.tool.sel != self.feats[i]["id"] else None)
        self.fForm = QFrame()
        self.fForm.setObjectName("fld")
        g = QGridLayout(self.fForm)
        g.setContentsMargins(8, 6, 8, 8)
        g.setVerticalSpacing(5)
        self.fHead = QLabel()
        self.fHead.setTextFormat(Qt.RichText)
        g.addWidget(self.fHead, 0, 0, 1, 4)
        g.addWidget(QLabel("Jenis"), 1, 0)
        self.fKind = QComboBox()
        g.addWidget(self.fKind, 1, 1, 1, 3)
        g.addWidget(QLabel("Nama"), 2, 0)
        self.fName = QLineEdit()
        self.fName.setPlaceholderText("mis. PROPYLITIC (CHL-SME) PYRITIC TUFF")
        g.addWidget(self.fName, 2, 1, 1, 3)
        self.fAu, self.fAg, self.fSxs, self.fLen = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit()
        for i, (lab, e) in enumerate((("Au ppm", self.fAu), ("Ag ppm", self.fAg), ("SxS %", self.fSxs))):
            g.addWidget(QLabel(lab), 3 + i // 2, (i % 2) * 2)
            g.addWidget(e, 3 + i // 2, (i % 2) * 2 + 1)
        self.lenL = QLabel("Panjang m")
        g.addWidget(self.lenL, 4, 2)
        g.addWidget(self.fLen, 4, 3)
        g.addWidget(QLabel("Teks lain"), 5, 0)
        self.fTxt = QPlainTextEdit()
        self.fTxt.setFixedHeight(46)
        self.fTxt.setPlaceholderText("baris tambahan di kotak kadar / catatan (mis. Cu: 120 ppm)")
        g.addWidget(self.fTxt, 5, 1, 1, 3)
        r = QHBoxLayout()
        self.bFSave = btn("Simpan", pri=True, sm=True)
        self.bSplit = btn("Belah di titik", "Belah garis di titik terpilih (kotak kuning)", sm=True)
        self.bJoin = btn("Gabung", "Gabung dengan garis lain yang ujungnya bersinggungan", sm=True)
        self.bVDel = btn("Hapus titik", "Hapus titik terpilih", sm=True)
        self.bFDel = btn("Hapus fitur", sm=True)
        for b in (self.bFSave, self.bSplit, self.bJoin, self.bVDel, self.bFDel):
            r.addWidget(b)
        r.addStretch(1)
        g.addLayout(r, 6, 0, 1, 4)
        self.fErr = QLabel()
        self.fErr.setObjectName("err")
        self.fErr.setWordWrap(True)
        g.addWidget(self.fErr, 7, 0, 1, 4)
        v.addWidget(self.fForm)
        self.bFSave.clicked.connect(self.save_form)
        self.bSplit.clicked.connect(self.split_sel)
        self.bJoin.clicked.connect(self.join_sel)
        self.bVDel.clicked.connect(self.delete_vertex)
        self.bFDel.clicked.connect(self.delete_selected)
        for e in (self.fName, self.fAu, self.fAg, self.fSxs, self.fLen):
            e.returnPressed.connect(self.save_form)
        kb = btn("Atur jenis fitur & nomor string…", sm=True)
        kb.clicked.connect(self.edit_kinds)
        v.addWidget(kb, 0, Qt.AlignLeft)
        n = QLabel("Gambar: pilih jenis di bilah atas lalu ✎ Gambar, klik titik demi titik, klik ganda / Enter untuk selesai. "
                   "Edit: klik fitur, tarik kotak putih untuk menggeser titik (snap ke fitur lain), klik ganda di garis untuk "
                   "menyisipkan titik, Delete untuk menghapus. <b>Garis skala</b> (isi panjang m) memberi skala foto untuk bar skala "
                   "dan spasi kekar AI.")
        n.setObjectName("note")
        n.setWordWrap(True)
        n.setTextFormat(Qt.RichText)
        v.addWidget(n)
        v.addStretch(1)
        self.fForm.hide()
        return self._scroll(w)

    def _tab_info(self) -> QWidget:
        w = QWidget()
        w.setObjectName("card")
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)
        g = QFormLayout()
        self.iTpl = QComboBox()
        for k, t in oc_paint.TEMPLATES.items():
            self.iTpl.addItem(t, k)
        self.iTitle, self.iSub = QLineEdit(), QLineEdit()
        self.iTitle.setPlaceholderText("judul pita (kosong = judul foto)")
        self.iSub.setPlaceholderText("opsional, mis. tanggal / geologist")
        self.iComp = QPlainTextEdit()
        self.iComp.setFixedHeight(46)
        self.iComp.setPlaceholderText("mis. Composite Sample Block Digging @0.29 ppm Au")
        g.addRow("Template", self.iTpl)
        g.addRow("Judul", self.iTitle)
        g.addRow("Sub judul", self.iSub)
        g.addRow("Kotak komposit", self.iComp)
        self.iLegPos = QComboBox()
        for k, t in (("bl", "kiri bawah"), ("br", "kanan bawah"), ("tl", "kiri atas"), ("tr", "kanan atas")):
            self.iLegPos.addItem(t, k)
        g.addRow("Posisi legenda", self.iLegPos)
        v.addLayout(g)
        self.iLegPos.activated.connect(lambda *_: self.save_info({"legend_pos": self.iLegPos.currentData()}))
        self.iLeg, self.iScale, self.iNames, self.iDesc = (QCheckBox("Legenda"), QCheckBox("Bar skala (perlu garis skala)"),
                                                            QCheckBox("Nama fitur di foto"), QCheckBox("Deskripsi ringkas (template dinding)"))
        self.iFill = QCheckBox("Isi poligon (warna tipis)")
        for c in (self.iLeg, self.iScale, self.iNames, self.iDesc, self.iFill):
            c.setChecked(True)
            v.addWidget(c)
        self.iTpl.activated.connect(lambda *_: self.save_info({"template": self.iTpl.currentData()}))
        self.iTitle.editingFinished.connect(lambda: self.save_info({"title": self.iTitle.text().strip()}))
        self.iSub.editingFinished.connect(lambda: self.save_info({"subtitle": self.iSub.text().strip()}))
        orig = self.iComp.focusOutEvent

        def fo(ev):
            orig(ev)
            self.save_info({"composite": self.iComp.toPlainText().strip()})
        self.iComp.focusOutEvent = fo
        for c, k in ((self.iLeg, "show_legend"), (self.iScale, "show_scale"), (self.iNames, "show_names"), (self.iDesc, "show_desc"), (self.iFill, "fill")):
            c.toggled.connect(lambda on, k=k: self.save_info({k: on}))
        r = QHBoxLayout()
        self.bPng = btn("⇩ Ekspor PNG", pri=True, sm=True)
        self.bPdf = btn("⇩ Ekspor PDF", sm=True)
        r.addWidget(self.bPng)
        r.addWidget(self.bPdf)
        r.addStretch(1)
        v.addLayout(r)
        self.bPng.clicked.connect(lambda: self.export("png"))
        self.bPdf.clicked.connect(lambda: self.export("pdf"))
        n = QLabel("Kotak kadar muncul untuk fitur yang punya Au / Ag / SxS / teks lain (tab Fitur) pada template Trenching; "
                   "tarik kotaknya di foto untuk memindahkan. Kotak komposit juga bisa ditarik. Ekspor memakai foto resolusi penuh "
                   "(maks. 6000 px), sama persis dengan tampilan di layar.")
        n.setObjectName("note")
        n.setWordWrap(True)
        v.addWidget(n)
        v.addStretch(1)
        return self._scroll(w)

    # ---------------------------------------------------------------- util
    def by(self) -> str:
        return self.win.user()

    def toast(self, m: str, ms: int = 2600) -> None:
        self.win.toast(m, ms)

    def ask_text(self, q: str, d: str = "") -> str:
        from PySide6.QtWidgets import QInputDialog
        t, ok = QInputDialog.getText(self, "Core-Ex", q, text=d)
        return t.strip() if ok else ""

    def feat(self, fid) -> dict | None:
        return next((f for f in self.feats if f["id"] == fid), None) if fid is not None else None

    def info(self) -> dict:
        i = dict((self.cur or {}).get("info") or {})
        i.setdefault("template", "trench")
        if not i.get("title"):
            i["title"] = (self.cur or {}).get("title") or ""
        if self.comp_pos:
            i["comp_u"], i["comp_v"] = self.comp_pos
        return i

    def m_per_unit(self) -> float | None:
        if not self.scale or not self.cur or not self.view.w:
            return None
        return self.scale["m_per_px"] * self.cur["w"] / self.view.w

    def set_enabled(self, on: bool) -> None:
        for w in (self.bAdd,):
            w.setEnabled(bool(self.folder))
        for w in (self.bDel, self.bDraw, self.cbKind, self.bAI, self.tabs, self.bSel):
            w.setEnabled(on)

    def hint(self) -> None:
        t = self.tool
        if t.mode == "draw":
            k = self.kmap.get(t.kind, {})
            s = {"line": "Klik titik demi titik; klik ganda / Enter = selesai", "poly": "Klik sudut poligon; klik ganda / Enter = tutup",
                 "point": "Klik posisi label"}.get(k.get("shape"), "")
            self.hintL.setText(f"<b>{_esc(k.get('name', ''))}</b>: {s} · Backspace = hapus titik terakhir · Esc = batal")
        else:
            self.hintL.setText("Klik fitur untuk mengedit · tarik titik / kotak · klik ganda di garis = sisipkan titik · Delete = hapus")

    # ---------------------------------------------------------------- proyek
    def open(self, folder: str) -> None:
        self.folder = folder
        self.cur, self.feats = None, []
        self.tool.select(None)
        try:
            j = api.call("/core/outcrop/open", {"folder": folder})
        except api.ApiError as e:
            say(self, "Gagal membuka data singkapan:\n" + str(e), warn=True)
            return
        self.desc_fields = j["desc_fields"]
        self._build_desc()
        self._kinds(j["kinds"])
        self.photos = j["photos"]
        self._fill_list()
        self._summary(j["summary"])
        self.set_enabled(False)
        if self.photos:
            self.lst.setCurrentRow(0)
        else:
            self.view.placeholder("Belum ada foto singkapan di proyek ini.\nKlik + Foto untuk menambah foto mapping / trenching.")

    def _kinds(self, ks: list[dict]) -> None:
        self.kinds = ks
        self.kmap = {k["key"]: k for k in ks}
        cur = self.cbKind.currentData()
        for cb in (self.cbKind, self.fKind):
            cb.blockSignals(True)
            cb.clear()
        for k in ks:
            pm = QPixmap(14, 14)
            pm.fill(QColor(k["color"]))
            ic = QIcon(pm)
            sh = {"line": "garis", "poly": "poligon", "point": "label"}[k["shape"]]
            self.cbKind.addItem(ic, f"{k['name']}  ({sh})", k["key"])
            self.fKind.addItem(ic, k["name"], k["key"])
        self.cbKind.setCurrentIndex(max(0, self.cbKind.findData(cur)))
        for cb in (self.cbKind, self.fKind):
            cb.blockSignals(False)

    def _summary(self, s: dict) -> None:
        self.sum.setText(f"{s['total']} foto · {s['described']} dideskripsikan AI · {s['features']} fitur")

    def _fill_list(self) -> None:
        cur = self.cur["id"] if self.cur else None
        self.lst.blockSignals(True)
        self.lst.clear()
        root = None
        for p in self.photos:
            it = QListWidgetItem(f"{p.get('title') or p['name']}\n{p['n_feat']} fitur" + (" · AI" if p["status"] == "done" else "")
                                 + (" · file hilang" if p.get("missing") else ""))
            it.setData(Qt.UserRole, p["id"])
            it.setToolTip(p["name"])
            self.lst.addItem(it)
            root = root or self._root()
            f = root / "foto" / p["file"] if root else None
            if f and f.exists():
                pid = p["id"]
                run_bg(lambda f=f: oc_paint.load_image(f, 160), ok=lambda im, pid=pid: self._thumb(pid, im))
        if cur is not None:
            for i in range(self.lst.count()):
                if self.lst.item(i).data(Qt.UserRole) == cur:
                    self.lst.setCurrentRow(i)
        self.lst.blockSignals(False)

    def _root(self) -> Path | None:
        try:
            from gcex_backend import core_outcrop
            return core_outcrop.store(self.folder).root
        except Exception:  # noqa: BLE001
            return None

    def _thumb(self, pid: int, im: QImage) -> None:
        for i in range(self.lst.count()):
            it = self.lst.item(i)
            if it.data(Qt.UserRole) == pid:
                it.setIcon(QIcon(QPixmap.fromImage(im)))

    def add_photo(self) -> None:
        if not self.folder:
            return
        fs, _ = QFileDialog.getOpenFileNames(self, "Tambah foto singkapan / trenching", SET.get("ocLastDir", str(Path.home())),
                                             "Foto (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp)")
        if not fs:
            return
        SET.set("ocLastDir", str(Path(fs[0]).parent))
        last = None
        for f in fs:
            try:
                last = api.call("/core/outcrop/add", {"folder": self.folder, "path": f, "by": self.by()})
            except api.ApiError as e:
                say(self, f"{Path(f).name}:\n{e}", warn=True)
        if last:
            self.reload(select=last["photo"]["id"])
            self.toast(f"{len(fs)} foto ditambahkan ke proyek")

    def delete_photo(self) -> None:
        if not self.cur:
            return
        if not ask(self, f"Hapus foto singkapan \"{self.cur.get('title') or self.cur['name']}\" beserta {len(self.feats)} fitur dari proyek?\n\n"
                         "File asli di luar proyek tidak tersentuh."):
            return
        try:
            api.call("/core/outcrop/delete", {"folder": self.folder, "id": self.cur["id"], "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.cur = None
        self.reload()

    def reload(self, select: int | None = None) -> None:
        j = api.call("/core/outcrop/open", {"folder": self.folder})
        self.photos = j["photos"]
        self._kinds(j["kinds"])
        self._summary(j["summary"])
        want = select if select is not None else (self.cur["id"] if self.cur else None)
        self._fill_list()
        idx = next((i for i, p in enumerate(self.photos) if p["id"] == want), 0 if self.photos else -1)
        if idx >= 0:
            self.lst.setCurrentRow(idx)
            if self.cur and self.cur["id"] == self.photos[idx]["id"] and select is None:
                return
            self._pick(idx)
        else:
            self.cur, self.feats = None, []
            self.set_enabled(False)
            self.view.placeholder("Belum ada foto singkapan di proyek ini.\nKlik + Foto untuk menambah foto mapping / trenching.")
            self.canvas.update()

    def _pick(self, i: int) -> None:
        if not 0 <= i < len(self.photos):
            return
        pid = self.photos[i]["id"]
        try:
            j = api.call("/core/outcrop/photo", {"folder": self.folder, "id": pid})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        same = self.cur and self.cur["id"] == pid
        self.cur, self.feats, self.scale = j["photo"], j["features"], j.get("scale")
        self.comp_pos = None
        self.tool.cancel()
        self.tool.select(None)
        self.set_enabled(True)
        if not same:
            root = self._root()
            self.view.show_file(root / "foto" / self.cur["file"] if root else Path(self.cur["file"]), pid)
            self.histBtn.setChecked(False)
        self.show_photo()

    def show_photo(self) -> None:
        r = self.cur
        if not r:
            return
        for e, k in ((self.eTitle, "title"), (self.eLoc, "location"), (self.eTaken, "taken")):
            if not e.hasFocus():
                e.setText(r.get(k) or "")
        desc, edited = r.get("desc") or {}, set(r.get("edited") or [])
        for k, e in self.dw.items():
            v = desc.get(k)
            if isinstance(e, QComboBox):
                e.setCurrentIndex(max(0, e.findData(v or "")))
            elif isinstance(e, QLineEdit):
                if not e.hasFocus():
                    e.setText(v or "")
            elif not e.hasFocus():
                e.setPlainText(v or "")
            ai = r.get("status") == "done" and k not in edited and v
            kind = "ed" if k in edited else ("ai" if ai else "")
            tag = self.dTag[k]
            tag.setText({"ed": "diedit", "ai": "AI"}.get(kind, ""))
            tag.setVisible(bool(kind))
            tag.setProperty("k", kind)
            fr = e.parentWidget()
            fr.setProperty("ai", bool(ai) and kind == "ai")
            for x in (tag, fr):
                theme.repolish(x)
        if r.get("status") == "done":
            self.aiInfo.setText(f"KEYAKINAN AI <b>{_esc(r.get('ai_conf') or '–')}</b> · {_esc(r.get('ai_model') or '')}"
                                + (f" · {r['ai_secs']} dtk" if r.get("ai_secs") else "") + f" · {_esc(r.get('ai_at') or '')}")
        elif r.get("status") == "error":
            self.aiInfo.setText(f"<span style='color:{theme.C['er']}'>AI gagal: {_esc(r.get('error') or '')}</span>")
        else:
            self.aiInfo.setText("Belum dideskripsikan AI.")
        self.aiInfo.setTextFormat(Qt.RichText)
        i = self.info()
        self.iTpl.setCurrentIndex(max(0, self.iTpl.findData(i.get("template"))))
        if not self.iTitle.hasFocus():
            self.iTitle.setText((r.get("info") or {}).get("title") or "")
            self.iTitle.setPlaceholderText(r.get("title") or "judul pita")
        if not self.iSub.hasFocus():
            self.iSub.setText(i.get("subtitle") or "")
        if not self.iComp.hasFocus():
            self.iComp.setPlainText(i.get("composite") or "")
        self.iLegPos.setCurrentIndex(max(0, self.iLegPos.findData(i.get("legend_pos") or "bl")))
        for c, k in ((self.iLeg, "show_legend"), (self.iScale, "show_scale"), (self.iNames, "show_names"), (self.iDesc, "show_desc"), (self.iFill, "fill")):
            c.blockSignals(True)
            c.setChecked(i.get(k, True))
            c.blockSignals(False)
        self.iComp.setEnabled(i.get("template") == "trench")
        self.iDesc.setEnabled(i.get("template") == "wall")
        self.feat_list()
        self.canvas.update()
        if self.histBtn.isChecked():
            self._hist(True)

    def _save_col(self, k: str, val: str) -> None:
        if not self.cur or (self.cur.get(k) or "") == val.strip():
            return
        self._update({k: val})

    def _save_desc(self, k: str, val) -> None:
        if not self.cur or ((self.cur.get("desc") or {}).get(k) or "") == (val or "").strip():
            return
        self._update({"desc:" + k: val})

    def save_info(self, d: dict) -> None:
        if not self.cur:
            return
        if all((self.cur.get("info") or {}).get(k) == v for k, v in d.items()):
            return
        self._update({"info": d})
        if "comp_u" in d:
            self.comp_pos = None

    def _update(self, values: dict) -> None:
        try:
            j = api.call("/core/outcrop/update", {"folder": self.folder, "id": self.cur["id"], "values": values, "by": self.by()})
        except api.ApiError as e:
            say(self, "Gagal menyimpan:\n" + str(e), warn=True)
            self.show_photo()
            return
        self.cur = j["photo"]
        self._sync_photo()
        self.show_photo()

    def _sync_photo(self) -> None:
        for i, p in enumerate(self.photos):
            if p["id"] == self.cur["id"]:
                self.photos[i] = dict(self.cur)
                self._summary({"total": len(self.photos), "described": sum(1 for x in self.photos if x["status"] == "done"),
                               "features": sum(x["n_feat"] for x in self.photos)})
                it = self.lst.item(i)
                if it:
                    it.setText(f"{p.get('title') or p['name']}\n{self.cur['n_feat']} fitur" + (" · AI" if self.cur["status"] == "done" else ""))

    def _hist(self, on: bool) -> None:
        self.histBtn.setText(("▾" if on else "▸") + "  Riwayat perubahan && jawaban asli AI")
        self.histTxt.setVisible(on)
        if not on or not self.cur:
            return
        import json as _json
        try:
            j = api.call("/core/outcrop/history", {"folder": self.folder, "id": self.cur["id"]})
        except api.ApiError as e:
            self.histTxt.setText(_esc(e))
            return
        mu = theme.C["mu"]
        h = "".join(f"<div><b>{_esc(x['what'])}</b>: {_esc((x['old'] or '–')[:120])} → {_esc((x['new'] or '–')[:160])} "
                    f"<span style='color:{mu}'>· {_esc(x.get('by') or '')} · {_esc(x['src'])} · {_esc(x['at'])}</span></div>" for x in j["history"]) or "<div>Belum ada perubahan.</div>"
        if j.get("ai"):
            h += (f"<div style='margin-top:6px'><b>Jawaban asli AI:</b><pre style='font-family:\"{theme.MONO}\";font-size:8pt;white-space:pre-wrap'>"
                  + _esc(_json.dumps(j["ai"], indent=1, ensure_ascii=False)) + "</pre></div>")
        self.histTxt.setText(h)

    # ---------------------------------------------------------------- AI
    def run_ai(self) -> None:
        if not self.cur or self.ai_busy:
            return
        ai = self.win.ai
        model = ai.model()
        if not ai.info or not ai.info.get("running") or not model:
            self.win.open_ai()
            return
        pid, folder = self.cur["id"], self.folder
        body = {"folder": folder, "id": pid, "host": ai.host.text().strip(), "model": model, "extra": ai.extra.toPlainText(),
                "max_px": int(ai.px.currentData()), "by": self.by()}
        self.ai_busy = True
        self.bAI.setEnabled(False)
        self.bAI.setText("AI menganalisis…")
        self.aiInfo.setText(f"Menganalisis foto dengan {model}… (biasanya 20–120 detik)")
        t0 = _dt.datetime.now()

        def ok(j):
            self._ai_done()
            if self.cur and self.cur["id"] == pid:
                self.cur = j["photo"]
                self._sync_photo()
                self.show_photo()
            self.toast(f"Deskripsi AI selesai ({(_dt.datetime.now() - t0).seconds} dtk)")

        def err(e):
            self._ai_done()
            say(self, "AI gagal mendeskripsikan foto:\n" + e, warn=True)
            if self.cur and self.cur["id"] == pid:
                self._pick(self.lst.currentRow())

        run_bg(api.call, "/core/outcrop/ai", body, ok=ok, err=err)

    def _ai_done(self) -> None:
        self.ai_busy = False
        self.bAI.setEnabled(bool(self.cur))
        self.bAI.setText("Deskripsikan dengan AI")

    # ---------------------------------------------------------------- fitur
    def feat_list(self) -> None:
        self.fList.blockSignals(True)
        self.fList.clear()
        for f in self.feats:
            k = self.kmap.get(f["kind"], {"name": f["kind"], "color": "#7a5aa6"})
            pm = QPixmap(14, 14)
            pm.fill(QColor(k["color"]))
            g = oc_paint.grade_lines(f["attrs"])
            it = QListWidgetItem(QIcon(pm), f"{k['name']}" + (f" · {f['name']}" if f.get("name") else "")
                                 + (f" · {', '.join(g[:2])}" if g else "") + (f" · {_f(f['attrs'].get('length_m'))} m" if f['attrs'].get('length_m') else ""))
            self.fList.addItem(it)
        i = next((i for i, f in enumerate(self.feats) if f["id"] == self.tool.sel), -1)
        self.fList.setCurrentRow(i)
        self.fList.blockSignals(False)
        self.sel_changed()

    def sel_changed(self) -> None:
        f = self.feat(self.tool.sel)
        self.fForm.setVisible(bool(f))
        i = next((i for i, x in enumerate(self.feats) if x["id"] == self.tool.sel), -1)
        if self.fList.currentRow() != i:
            self.fList.blockSignals(True)
            self.fList.setCurrentRow(i)
            self.fList.blockSignals(False)
        if not f:
            return
        self.fHead.setText(f"<b>Fitur #{f['id']}</b> · {len(f['pts'])} titik" + (f" · titik terpilih: {self.tool.vsel + 1}" if self.tool.vsel is not None else ""))
        self.fKind.blockSignals(True)
        # jenis hanya bisa diganti ke jenis dengan bentuk yang sama
        for j in range(self.fKind.count()):
            kk = self.kmap.get(self.fKind.itemData(j), {})
            self.fKind.model().item(j).setEnabled(kk.get("shape") == f["shape"])
        self.fKind.setCurrentIndex(max(0, self.fKind.findData(f["kind"])))
        self.fKind.blockSignals(False)
        a = f["attrs"]
        self.fName.setText(f.get("name") or "")
        self.fAu.setText(_f(a.get("au_ppm")))
        self.fAg.setText(_f(a.get("ag_ppm")))
        self.fSxs.setText(_f(a.get("sxs_pct")))
        self.fLen.setText(_f(a.get("length_m")))
        self.fTxt.setPlainText(a.get("teks") or "")
        sk = f["kind"] == "skala"
        self.lenL.setVisible(sk)
        self.fLen.setVisible(sk)
        self.bSplit.setVisible(f["shape"] == "line")
        self.bJoin.setVisible(f["shape"] == "line")
        self.bVDel.setVisible(f["shape"] != "point")
        self.bSplit.setEnabled(self.tool.vsel is not None)
        self.bVDel.setEnabled(self.tool.vsel is not None)
        self.fErr.setText("")

    def new_feat(self, kind: str, pts: list, name: str = "") -> None:
        f = {"kind": kind, "pts": pts, "name": name, "attrs": {}}
        try:
            j = api.call("/core/outcrop/feature/save", {"folder": self.folder, "photo_id": self.cur["id"], "feat": f, "by": self.by()})
        except api.ApiError as e:
            say(self, "Fitur tidak disimpan:\n" + str(e), warn=True)
            return
        self._feats(j)
        self.tool.select(j["id"])
        self.tabs.setCurrentIndex(1)
        if kind == "skala" and not (self.feat(j["id"]) or {}).get("attrs", {}).get("length_m"):
            self.fLen.setFocus()
            self.toast("Isi panjang garis skala (m), lalu Simpan", 4000)

    def save_feat(self, f: dict) -> None:
        try:
            j = api.call("/core/outcrop/feature/save", {"folder": self.folder, "photo_id": self.cur["id"], "feat_id": f["id"],
                                                         "feat": {k: f[k] for k in ("kind", "pts", "name", "attrs")}, "by": self.by()})
        except api.ApiError as e:
            say(self, "Perubahan tidak disimpan:\n" + str(e), warn=True)
            self._pick(self.lst.currentRow())
            return
        self._feats(j)

    def _feats(self, j: dict) -> None:
        self.feats = j["features"]
        if "scale" in j:
            self.scale = j["scale"]
        if self.cur:
            self.cur["n_feat"] = len(self.feats)
            self._sync_photo()
        self.feat_list()
        self.canvas.update()

    def save_form(self) -> None:
        f = self.feat(self.tool.sel)
        if not f:
            return
        a = dict(f["attrs"])
        try:
            for k, e in (("au_ppm", self.fAu), ("ag_ppm", self.fAg), ("sxs_pct", self.fSxs), ("length_m", self.fLen)):
                v = _num(e.text())
                if v is None:
                    a.pop(k, None)
                else:
                    a[k] = v
        except ValueError:
            self.fErr.setText("Au, Ag, SxS dan panjang harus angka (koma atau titik desimal).")
            return
        t = self.fTxt.toPlainText().strip()
        if t:
            a["teks"] = t
        else:
            a.pop("teks", None)
        g = dict(f, kind=self.fKind.currentData() or f["kind"], name=self.fName.text().strip(), attrs=a)
        try:
            j = api.call("/core/outcrop/feature/save", {"folder": self.folder, "photo_id": self.cur["id"], "feat_id": f["id"],
                                                         "feat": {k: g[k] for k in ("kind", "pts", "name", "attrs")}, "by": self.by()})
        except api.ApiError as e:
            self.fErr.setText(str(e))
            return
        self._feats(j)
        self.toast("Fitur disimpan")

    def delete_selected(self) -> None:
        f = self.feat(self.tool.sel)
        if not f:
            return
        if self.tool.vsel is not None and f["shape"] != "point" and len(f["pts"]) > (3 if f["shape"] == "poly" else 2):
            self.delete_vertex()
            return
        k = self.kmap.get(f["kind"], {}).get("name", f["kind"])
        if not ask(self, f"Hapus {k}" + (f" \"{f['name']}\"" if f.get("name") else "") + "?"):
            return
        try:
            j = api.call("/core/outcrop/feature/delete", {"folder": self.folder, "feat_id": f["id"], "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.tool.select(None)
        self._feats(j)

    def delete_vertex(self) -> None:
        f, i = self.feat(self.tool.sel), self.tool.vsel
        if not f or i is None:
            return
        if len(f["pts"]) <= (3 if f["shape"] == "poly" else 2):
            self.fErr.setText("Titik tidak bisa dihapus: " + ("poligon minimal 3 titik." if f["shape"] == "poly" else "garis minimal 2 titik."))
            return
        f["pts"].pop(i)
        self.tool.vsel = None
        self.save_feat(f)

    def split_sel(self) -> None:
        f, i = self.feat(self.tool.sel), self.tool.vsel
        if not f or i is None:
            return
        try:
            j = api.call("/core/outcrop/feature/split", {"folder": self.folder, "feat_id": f["id"], "at": i, "by": self.by()})
        except api.ApiError as e:
            self.fErr.setText(str(e))
            return
        self.tool.vsel = None
        self._feats(j)
        self.toast("Garis dibelah menjadi dua")

    def join_sel(self) -> None:
        f = self.feat(self.tool.sel)
        if not f or f["shape"] != "line":
            return
        ends = (f["pts"][0], f["pts"][-1])
        cand = [g for g in self.feats if g["id"] != f["id"] and g["shape"] == "line" and
                any(abs(e[0] - q[0]) + abs(e[1] - q[1]) < 0.005 for e in ends for q in (g["pts"][0], g["pts"][-1]))]
        if not cand:
            self.fErr.setText("Tidak ada garis lain yang ujungnya bersinggungan. Seret ujung garis ke ujung garis lain (snap) dulu.")
            return
        try:
            j = api.call("/core/outcrop/feature/join", {"folder": self.folder, "a": f["id"], "b": cand[0]["id"], "by": self.by()})
        except api.ApiError as e:
            self.fErr.setText(str(e))
            return
        self._feats(j)
        self.tool.select(f["id"])
        self.toast("Garis digabung")

    def draw_done(self) -> None:
        self.bSel.setChecked(True)
        self.hint()
        self.canvas.update()

    def edit_kinds(self) -> None:
        d = KindsDlg(self, self.kinds)
        if d.exec() != Dlg.Accepted:
            return
        try:
            j = api.call("/core/outcrop/kinds", {"folder": self.folder, "kinds": d.result_kinds(), "by": self.by()})
        except api.ApiError as e:
            say(self, "Pustaka fitur tidak disimpan:\n" + str(e), warn=True)
            return
        self._kinds(j["kinds"])
        self.feat_list()
        self.canvas.update()

    # ---------------------------------------------------------------- ekspor
    def export(self, fmt: str) -> None:
        if not self.cur:
            return
        root = self._root()
        src = root / "foto" / self.cur["file"]
        base = re.sub(r"[^\w.-]+", "_", (self.info().get("title") or self.cur.get("title") or self.cur["name"]))[:80]
        p, _ = QFileDialog.getSaveFileName(self, "Ekspor infografis", str(Path(SET.get("lastSaveDir", str(Path.home()))) / f"{base}.{fmt}"),
                                           "PNG (*.png)" if fmt == "png" else "PDF (*.pdf)")
        if not p:
            return
        if Path(p).suffix.lower() != "." + fmt:
            p += "." + fmt
        SET.set("lastSaveDir", str(Path(p).parent))
        feats, kmap, info, desc = [dict(f) for f in self.feats], dict(self.kmap), self.info(), dict(self.cur.get("desc") or {})
        mpp = self.scale["m_per_px"] if self.scale else None
        w0 = self.cur["w"]
        title = info.get("title") or ""
        self.toast("Menyusun infografis…", 6000)

        def work():
            im = oc_paint.render(src, feats, kmap, info, desc, mpp, w0)
            (oc_paint.save_png if fmt == "png" else lambda i, o: oc_paint.save_pdf(i, o, title))(im, p)
            return p

        run_bg(work, ok=lambda path: (self.toast("Tersimpan: " + path, 5000), show_in_folder(path), log("[singkapan] ekspor", path)),
               err=lambda e: say(self, "Gagal ekspor:\n" + e, warn=True))

    def escape(self) -> bool:
        if self.tool.mode == "draw":
            self.tool.cancel()
            return True
        if self.tool.sel is not None:
            self.tool.select(None)
            return True
        return False


__all__ = ["OutcropPage", "QLabel"]
