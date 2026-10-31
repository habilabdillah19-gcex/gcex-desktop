"""Tabel foto: model virtual (hanya baris yang terlihat digambar), sel bisa diedit, penanda AI / diedit / logging / nama file."""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QStyledItemDelegate, QTableView

from . import api, theme
from .theme import C
from .util import run_bg

# k, judul, lebar, bisa diedit, angka
COLS = [("_sel", "", 30, 0, 0), ("_no", "No", 46, 0, 1), ("_th", "Foto", 64, 0, 0), ("status", "Status", 118, 0, 0),
        ("name", "Nama file", 230, 0, 0), ("hole_id", "Hole ID", 100, 1, 0), ("box_no", "Box", 52, 1, 0),
        ("from_m", "From", 72, 1, 1), ("to_m", "To", 72, 1, 1), ("_iv", "Int.", 52, 0, 1), ("photo_date", "Tgl foto", 84, 1, 0),
        ("lithology", "Litologi", 150, 1, 0), ("color", "Warna", 170, 1, 0), ("weathering", "Pelapukan", 150, 1, 0),
        ("oxidation", "Oksidasi", 130, 1, 0), ("alteration", "Alterasi", 130, 1, 0), ("recovery_pct", "Rec %", 60, 1, 1),
        ("rqd_pct", "RQD %", 60, 1, 1), ("gsi", "GSI", 64, 1, 0), ("rmr", "RMR", 56, 1, 1), ("loss_m", "Loss m", 64, 0, 1),
        ("half_m", "Half m", 64, 0, 1), ("ai_conf", "Keyakinan", 80, 0, 0), ("notes", "Catatan", 260, 1, 0)]
BLUES = ["#dbe7f5", "#9fbfe6", "#5a8fd0", "#2a5ea8", "#141a26"]
ROW_H = 34


def fmt(v: Any, d: int | None = None) -> str:
    if v is None or v == "":
        return ""
    if isinstance(v, float):
        return f"{v:.{d}f}" if d is not None else f"{round(v, 3):g}"
    return str(v)


def status_text(r: dict) -> tuple[str, str]:
    """(teks, kunci warna)"""
    if r.get("missing"):
        return "File hilang", "mu"
    if r.get("verified"):
        return "diverifikasi", "ink"
    return {"done": ("AI selesai", "ac"), "error": ("AI gagal", "er")}.get(r.get("status"), ("belum AI", "bd2"))


def is_ai(r: dict, k: str) -> bool:
    return (r.get("status") == "done" and not r.get("verified") and k not in (r.get("edited") or []) and k not in (r.get("from_name") or [])
            and r.get(k) is not None and not (k == "recovery_pct" and r.get("rec_src") == "tanda"))


class Thumbs:
    """Gambar mini dimuat di latar (QImage di thread, QPixmap di GUI)."""

    def __init__(self, changed: Callable[[int], None]):
        self.pix: dict[int, QPixmap] = {}
        self.busy: set[int] = set()
        self.changed, self.folder = changed, ""

    def reset(self, folder: str) -> None:
        self.pix.clear()
        self.busy.clear()
        self.folder = folder

    def get(self, pid: int) -> QPixmap | None:
        p = self.pix.get(pid)
        if p is None and pid not in self.busy and self.folder:
            self.busy.add(pid)
            folder = self.folder

            def load():
                im = QImage(str(api.image_file(folder, pid, 160)))
                return im.scaled(58, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            def done(im, pid=pid, folder=folder):
                if folder == self.folder:
                    self.pix[pid] = QPixmap.fromImage(im)
                    self.busy.discard(pid)
                    self.changed(pid)

            run_bg(load, ok=done, err=lambda e, pid=pid: self.busy.discard(pid))
        return p


class PhotoModel(QAbstractTableModel):
    edited = Signal(int, str, object)  # id, field, nilai baru
    selChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.view: list[dict] = []
        self.sel: set[int] = set()
        self.cur_id: int | None = None
        self.grade_el = ""
        self.grade_cls: list[float] = []
        self.sort: tuple[str, int] | None = None
        self.thumbs = Thumbs(self._thumb_ready)
        self.labels: dict[str, str] = {}

    # ---------------------------------------------------------------- kolom
    def cols(self) -> list[tuple]:
        if not self.grade_el:
            return COLS
        i = next(i for i, c in enumerate(COLS) if c[0] == "_iv") + 1
        return COLS[:i] + [("_g", self.grade_el + " rata2", 92, 0, 1)] + COLS[i:]

    def set_view(self, view: list[dict]) -> None:
        self.beginResetModel()
        self.view = view
        self.endResetModel()

    def refresh_row(self, pid: int) -> None:
        for i, r in enumerate(self.view):
            if r["id"] == pid:
                self.dataChanged.emit(self.index(i, 0), self.index(i, self.columnCount() - 1))
                return

    def refresh_all(self) -> None:
        if self.view:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.view) - 1, self.columnCount() - 1))

    def _thumb_ready(self, pid: int) -> None:
        c = next((j for j, x in enumerate(self.cols()) if x[0] == "_th"), None)
        for i, r in enumerate(self.view):
            if r["id"] == pid and c is not None:
                self.dataChanged.emit(self.index(i, c), self.index(i, c), [Qt.DecorationRole])
                return

    # ---------------------------------------------------------------- Qt
    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.view)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.cols())

    def headerData(self, s, o, role=Qt.DisplayRole):  # noqa: N802
        if o != Qt.Horizontal:
            return None
        c = self.cols()[s]
        if role == Qt.DisplayRole:
            arrow = (" ▲" if self.sort[1] > 0 else " ▼") if self.sort and self.sort[0] == c[0] else ""
            return c[1] + arrow
        if role == Qt.ToolTipRole and (c[0] == "_no" or c[0][0] != "_"):
            return "Klik untuk mengurutkan"
        if role == Qt.TextAlignmentRole and c[4]:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def flags(self, ix):
        if not ix.isValid():
            return Qt.NoItemFlags
        k, e = self.cols()[ix.column()][0], self.cols()[ix.column()][3]
        r = self.view[ix.row()]
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if k == "_sel":
            f |= Qt.ItemIsUserCheckable
        if e and not (r.get("log") or {}).get(k) is not None:
            f |= Qt.ItemIsEditable
        return f

    def data(self, ix, role=Qt.DisplayRole):
        if not ix.isValid():
            return None
        r = self.view[ix.row()]
        k, _, _, _, num = self.cols()[ix.column()]
        log = r.get("log") or {}
        if role == Qt.CheckStateRole and k == "_sel":
            return Qt.Checked if r["id"] in self.sel else Qt.Unchecked
        if role == Qt.DecorationRole:
            if k == "_th" and not r.get("missing"):
                return self.thumbs.get(r["id"])
            if k == "status":
                return QColor(C[status_text(r)[1]])
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            if k == "_no":
                return ix.row() + 1
            if k in ("_sel", "_th"):
                return None
            if k == "status":
                return status_text(r)[0]
            if k == "_iv":
                return fmt(r["to_m"] - r["from_m"], 2) if r.get("from_m") is not None and r.get("to_m") is not None else ""
            if k == "_g":
                v = (r.get("g") or {}).get(self.grade_el)
                return fmt(v)
            if log.get(k) is not None and role == Qt.DisplayRole:
                return str(log[k])
            v = r.get(k)
            return fmt(v) if role == Qt.DisplayRole else ("" if v is None else v)
        if role == Qt.TextAlignmentRole:
            return int((Qt.AlignRight if num else Qt.AlignLeft) | Qt.AlignVCenter)
        if role == Qt.BackgroundRole:
            if k == "_g":
                v = (r.get("g") or {}).get(self.grade_el)
                if v is not None:
                    i = sum(1 for c in self.grade_cls if v >= c)
                    return QBrush(QColor(BLUES[min(i, 4)]))
            if r["id"] == self.cur_id:
                return QBrush(QColor(C["sel"]))
            if log.get(k) is None and k[0] != "_" and is_ai(r, k):
                return QBrush(QColor(C["ai"]))
            return None
        if role == Qt.ForegroundRole:
            if k == "_g":
                v = (r.get("g") or {}).get(self.grade_el)
                if v is not None and sum(1 for c in self.grade_cls if v >= c) >= 3:
                    return QBrush(QColor("#ffffff"))
            if k == "status":
                return QBrush(QColor(C[status_text(r)[1]] if status_text(r)[1] != "bd2" else C["tx"]))
            if k == "loss_m" and r.get("loss_m"):
                return QBrush(QColor(C["mk"]))
            if r.get("missing"):
                return QBrush(QColor(C["mu"]))
            return None
        if role == Qt.FontRole:
            if log.get(k) is not None or (k == "status" and r.get("verified")) or (k == "loss_m" and r.get("loss_m")):
                f = QFont(theme.SANS)
                f.setBold(True)
                return f
            if k in ("hole_id", "from_m", "to_m", "_iv", "_no", "recovery_pct", "rqd_pct", "rmr", "loss_m", "half_m", "_g", "box_no"):
                return theme.mono(9)
            return None
        if role == Qt.ToolTipRole:
            if log.get(k) is not None:
                return f"Logging geologist: {log[k]}"
            if k == "name":
                return r.get("rel")
            if k == "status":
                if r.get("verified"):
                    return f"Diverifikasi {r.get('verified_by') or ''} {r.get('verified_at') or ''}"
                if r.get("status") == "error":
                    return r.get("error")
            if k == "half_m" and r.get("half_m"):
                return "Sampel half core: " + (r.get("half_samples") or "")
            if k == "_g":
                return "maks " + fmt((r.get("gmax") or {}).get(self.grade_el))
            if k[0] != "_" and is_ai(r, k):
                return "Isian AI (belum dicek geologist)"
            if r.get("verified") and k[0] != "_":
                return "Sudah diverifikasi"
        return None

    def setData(self, ix, value, role=Qt.EditRole):  # noqa: N802
        if not ix.isValid():
            return False
        r = self.view[ix.row()]
        k = self.cols()[ix.column()][0]
        if role == Qt.CheckStateRole and k == "_sel":
            (self.sel.add if Qt.CheckState(value) == Qt.Checked else self.sel.discard)(r["id"])
            self.dataChanged.emit(ix, ix)
            self.selChanged.emit()
            return True
        if role == Qt.EditRole:
            old = fmt(r.get(k))
            if str(value).strip() == old:
                return False
            self.edited.emit(r["id"], k, value)
            return True
        return False


class StatusDelegate(QStyledItemDelegate):
    def paint(self, p: QPainter, opt, ix) -> None:
        m: PhotoModel = ix.model()
        k = m.cols()[ix.column()][0]
        if k != "status":
            return super().paint(p, opt, ix)
        r = m.view[ix.row()]
        bg = m.data(ix, Qt.BackgroundRole)
        if bg:
            p.fillRect(opt.rect, bg)
        txt, ck = status_text(r)
        col = QColor(C[ck])
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = opt.rect.left() + 12, opt.rect.center().y()
        if ck in ("ac", "er", "ink"):
            p.setBrush(col)
            p.setPen(Qt.NoPen if ck != "ink" else QColor(C["ac"]))
        else:
            p.setBrush(Qt.NoBrush)
            p.setPen(QColor(C["ink"] if ck == "bd2" else C["mu"]))
        p.drawEllipse(cx - 4, cy - 4, 9, 9)
        p.setPen(QColor(C["er"] if ck == "er" else C["ac2"] if ck == "ink" else C["tx"] if ck != "mu" else C["mu"]))
        f = QFont(theme.SANS)
        f.setPointSizeF(8.8)
        f.setBold(ck == "ink")
        p.setFont(f)
        p.drawText(opt.rect.adjusted(22, 0, -2, 0), Qt.AlignVCenter | Qt.AlignLeft, txt)
        p.restore()


class PhotoTable(QTableView):
    rowActivated = Signal(int)  # indeks di view
    sortRequested = Signal(str)

    def __init__(self, model: PhotoModel):
        super().__init__()
        self.setModel(model)
        self.m = model
        self.setItemDelegate(StatusDelegate(self))
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(ROW_H)
        self.setIconSize(QSize(58, 30))
        self.setWordWrap(False)
        self.setShowGrid(True)
        h = self.horizontalHeader()
        h.setHighlightSections(False)
        h.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h.sectionClicked.connect(self._hdr)
        model.modelReset.connect(self.relayout)
        self.relayout()

    def relayout(self) -> None:
        for i, c in enumerate(self.m.cols()):
            self.setColumnWidth(i, c[2])

    def _hdr(self, i: int) -> None:
        k = self.m.cols()[i][0]
        if k == "_sel":
            on = not all(r["id"] in self.m.sel for r in self.m.view)
            for r in self.m.view:
                (self.m.sel.add if on else self.m.sel.discard)(r["id"])
            self.m.refresh_all()
            self.m.selChanged.emit()
            return
        if k == "_no" or k[0] != "_" or k == "_g":
            self.sortRequested.emit(k)

    def currentChanged(self, cur, prev) -> None:  # noqa: N802
        super().currentChanged(cur, prev)
        if cur.isValid() and (not prev.isValid() or cur.row() != prev.row()):
            self.rowActivated.emit(cur.row())

    def go_row(self, i: int) -> None:
        if 0 <= i < self.m.rowCount():
            c = max(self.currentIndex().column(), 0)
            self.setCurrentIndex(self.m.index(i, c))
            self.scrollTo(self.m.index(i, c))
