"""Cari cepat (Ctrl+K): Hole ID, kata di log / catatan / tanda / segmen, nama file, atau kueri kadar (Au>=1)."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from . import api, theme
from .table import fmt
from .util import run_bg

LAB = {"foto": "Foto", "assay": "Assay", "geologi": "Geologi", "tanda": "Tanda", "segmen": "Segmen"}


class SearchBox(QLineEdit):
    picked = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setPlaceholderText("Cari cepat (Ctrl+K): LTH-101, pyrite, QV, Au>=1…")
        self.setClearButtonEnabled(True)
        self.setMinimumWidth(320)
        self.folder = ""
        self.tok = 0
        self.pop = QFrame(None, Qt.ToolTip | Qt.FramelessWindowHint)
        self.pop.setObjectName("qres")
        v = QVBoxLayout(self.pop)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self.head = QLabel()
        self.head.setObjectName("note")
        self.head.setContentsMargins(8, 4, 8, 4)
        self.head.setWordWrap(True)
        self.lst = QListWidget()
        self.lst.setFrameShape(QFrame.NoFrame)
        self.lst.itemClicked.connect(self._go)
        v.addWidget(self.head)
        v.addWidget(self.lst)
        self.t = QTimer(self)
        self.t.setSingleShot(True)
        self.t.setInterval(220)
        self.t.timeout.connect(self.run)
        self.textEdited.connect(lambda *_: self.t.start())
        self.installEventFilter(self)

    def run(self, then_first: bool = False) -> None:
        q = self.text().strip()
        if not q or not self.folder:
            self.pop.hide()
            return
        self.tok += 1
        tok = self.tok
        run_bg(api.call, "/core/dh/search", {"folder": self.folder, "q": q, "limit": 80},
               ok=lambda j: self._show(tok, j, then_first), err=lambda e: self._err(tok, e))

    def _err(self, tok: int, e: str) -> None:
        if tok == self.tok:
            self.lst.clear()
            self.head.setText(f"<span style='color:{theme.C['er']}'>{e}</span>")
            self._place()

    def _show(self, tok: int, j: dict, then_first: bool) -> None:
        if tok != self.tok:
            return
        res = j.get("results") or []
        self.lst.clear()
        self.head.setText(f"{j.get('total', len(res))} HASIL" + (f" · tampil {len(res)}" if j.get("total", 0) > len(res) else "")
                          + (" · urut nilai tertinggi" if j.get("numeric") else "")
                          if res else "Tidak ditemukan. Coba Hole ID, kata di log (mis. pyrite, QV), nama file, atau Au>=1.")
        for x in res:
            dep = f"{fmt(x['f'])}–{fmt(x['t'])} m" if x.get("f") is not None else ""
            dest = "→ " + (x.get("photo") or "") if x.get("photo_id") else "tidak ada foto core box untuk interval ini"
            it = QListWidgetItem(f"{LAB.get(x['type'], x['type'])}   {x.get('hole') or ''} {dep} · {x.get('text') or ''}\n      {dest}")
            it.setData(Qt.UserRole, x)
            self.lst.addItem(it)
        if res:
            self.lst.setCurrentRow(0)
        self._place()
        if then_first and res:
            self._go(self.lst.item(0))

    def _place(self) -> None:
        w = max(self.width(), 460)
        self.pop.setFixedWidth(w)
        self.lst.setFixedHeight(min(360, max(0, self.lst.count()) * 40 + 4))
        self.pop.adjustSize()
        self.pop.move(self.mapToGlobal(QPoint(0, self.height() + 2)))
        self.pop.show()

    def _go(self, it) -> None:
        if it is None:
            return
        self.pop.hide()
        self.picked.emit(it.data(Qt.UserRole))

    def eventFilter(self, o, e) -> bool:  # noqa: N802
        if o is self and e.type() == QEvent.KeyPress:
            k = e.key()
            if k in (Qt.Key_Down, Qt.Key_Up) and self.pop.isVisible():
                self.lst.setCurrentRow(max(0, min(self.lst.count() - 1, self.lst.currentRow() + (1 if k == Qt.Key_Down else -1))))
                return True
            if k in (Qt.Key_Return, Qt.Key_Enter):
                self.t.stop()
                if self.pop.isVisible() and self.lst.currentItem():
                    self._go(self.lst.currentItem())
                else:
                    self.run(True)
                return True
            if k == Qt.Key_Escape:
                self.pop.hide()
                self.clearFocus()
                return True
        if o is self and e.type() == QEvent.FocusOut:
            QTimer.singleShot(150, lambda: self.pop.hide() if not self.lst.underMouse() else None)
        return False
