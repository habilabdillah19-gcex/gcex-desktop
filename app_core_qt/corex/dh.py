"""Dialog Data bor: import Collar / Survey / Assay / Geologi dari CSV / Excel dengan header bebas (pemetaan kolom),
plus pemetaan kolom logging -> isian kartu foto."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QTableWidget,
                               QTableWidgetItem, QTabBar, QWidget)

from . import api, theme
from .card import _esc, btn
from .dialogs import Dlg, ask, box, say, set_box
from .util import SET

KIND_L = {"collar": "Collar", "survey": "Survey", "assay": "Assay", "geology": "Geologi"}
HINT = {"collar": "Hole ID + X, Y, Z wajib; total depth, dip & azimuth collar opsional.",
        "survey": "Hole ID, kedalaman, dip, azimuth. Dip negatif = ke bawah (Surpac / Leapfrog) dikenali otomatis.",
        "assay": "Hole ID, From, To + kolom unsur apa pun (Au, Ag, Cu, …). <0.01 dibaca setengah limit deteksi.",
        "geology": "Hole ID, From, To + kolom apa pun (Lith, Alteration, Mineralogy, Vein, …)."}
GEO_F = {"lithology": "Litologi", "alteration": "Alterasi", "oxidation": "Oksidasi", "color": "Warna", "weathering": "Pelapukan"}


def _n(v) -> str:
    return f"{int(v or 0):,}".replace(",", ".")


class DhDlg(Dlg):
    changed = Signal()

    def __init__(self, parent, folder: str):
        super().__init__(parent, "Data bor", "Data <span style='color:#a9c3dd'>bor</span> · Collar, Survey, Assay, Geologi", 900)
        self.resize(980, 760)
        self.folder, self.kind, self.src, self.pv, self.sumj = folder, "assay", None, None, {}
        b = self.body
        self.tabs = QTabBar()
        self.tabs.currentChanged.connect(self._tab)
        b.addWidget(self.tabs)
        r = QHBoxLayout()
        self.bFile = btn("Pilih file CSV / Excel…", pri=True)
        self.bFile.clicked.connect(self.pick)
        self.fname = QLabel("belum ada file")
        self.fname.setObjectName("note")
        self.sheet = QComboBox()
        self.sheet.hide()
        self.sheet.activated.connect(lambda *_: self.preview(None, self.sheet.currentText()))
        self.hr = QSpinBox()
        self.hr.setRange(1, 999)
        self.hr.setToolTip("nomor baris yang berisi nama kolom")
        self.hr.editingFinished.connect(lambda: self.src and self.preview(self.hr.value() - 1))
        for x in (self.bFile, self.fname):
            r.addWidget(x)
        r.addStretch(1)
        r.addWidget(self.sheet)
        r.addWidget(QLabel("baris header"))
        r.addWidget(self.hr)
        b.addLayout(r)
        self.wBody = QWidget()
        v = QGridLayout(self.wBody)
        v.setContentsMargins(0, 0, 0, 0)
        self.nlab = QLabel()
        self.nlab.setObjectName("note")
        v.addWidget(QLabel("<b>Pratinjau</b>"), 0, 0)
        v.addWidget(self.nlab, 0, 1)
        self.pvT = QTableWidget()
        self.pvT.setMaximumHeight(170)
        self.pvT.verticalHeader().hide()
        v.addWidget(self.pvT, 1, 0, 1, 2)
        v.addWidget(QLabel("<b>Kolom utama</b> <span style='color:%s'>— pilih kolom file untuk tiap isian; nama header bebas</span>" % theme.C["mu"]), 2, 0, 1, 2)
        self.rolesW = QWidget()
        self.rolesL = QGridLayout(self.rolesW)
        self.rolesL.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.rolesW, 3, 0, 1, 2)
        self.colsLab = QLabel("<b>Kolom lain yang ikut</b> <span style='color:%s'>— centang, beri nama tampilan (mis. Au_ppm → Au), pilih angka / teks</span>" % theme.C["mu"])
        v.addWidget(self.colsLab, 4, 0, 1, 2)
        self.colsT = QTableWidget(0, 5)
        self.colsT.setHorizontalHeaderLabels(["Pakai", "Kolom di file", "Nama di DB-Ex", "Jenis", "Contoh"])
        self.colsT.verticalHeader().hide()
        self.colsT.setMaximumHeight(200)
        v.addWidget(self.colsT, 5, 0, 1, 2)
        m = QHBoxLayout()
        m.addWidget(QLabel("Cara import"))
        self.mode = QComboBox()
        self.mode.addItem("Tambah / perbarui per hole (hole di file diganti, hole lain tetap)", "upsert")
        self.mode.addItem("Ganti semua data tabel ini", "replace")
        m.addWidget(self.mode, 1)
        v.addLayout(m, 6, 0, 1, 2)
        b.addWidget(self.wBody, 1)
        self.rep = box("", "ok")
        self.rep.hide()
        b.addWidget(self.rep)
        self.sumL = box()
        b.addWidget(self.sumL)
        self.glW = QWidget()
        self.glL = QGridLayout(self.glW)
        self.glL.setContentsMargins(0, 0, 0, 0)
        b.addWidget(self.glW)
        clr = btn("Kosongkan tabel ini")
        clr.clicked.connect(self.clear)
        self.go = btn("Import", pri=True)
        self.go.clicked.connect(self.do_import)
        cl = btn("Tutup")
        cl.clicked.connect(self.accept)
        self.foot.addWidget(clr)
        self.foot.addStretch(1)
        self.foot.addWidget(cl)
        self.foot.addWidget(self.go)
        for k in KIND_L:
            self.tabs.addTab(KIND_L[k])
            self.tabs.setTabData(self.tabs.count() - 1, k)
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(list(KIND_L).index("assay"))
        self.tabs.blockSignals(False)
        self.reset()
        self.summary()

    # ---------------------------------------------------------------- ringkasan & tab
    def summary(self, j: dict | None = None) -> None:
        try:
            self.sumj = j or api.call("/core/dh/summary", {"folder": self.folder})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        n = self.sumj
        for i, k in enumerate(KIND_L):
            self.tabs.setTabText(i, f"{KIND_L[k]}  {_n(n.get(k))}")
        cols = (n.get("columns") or {}).get(self.kind) or []
        set_box(self.sumL, f"<b>{KIND_L[self.kind]}</b> di proyek: {_n(n.get(self.kind))} baris"
                + (" · kolom: " + ", ".join(_esc(c["name"]) + ("" if c["type"] == "n" else " (teks)") for c in cols) if cols else "")
                + f"<br><span style='color:{theme.C['mu']}'>{_esc(HINT[self.kind])}</span>")
        self._geolink(cols)

    def _geolink(self, cols: list[dict]) -> None:
        while self.glL.count():
            w = self.glL.takeAt(0).widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        self.glW.setVisible(self.kind == "geology" and bool(cols))
        if self.kind != "geology" or not cols:
            return
        gl = self.sumj.get("geo_link") or {}
        auto = self.sumj.get("geo_link_auto")
        self.glL.addWidget(QLabel("<b>Logging → isian kartu foto</b> <span style='color:%s'>(diutamakan di atas AI%s)</span>"
                                  % (theme.C["mu"], "; tebakan otomatis dari nama kolom" if auto else "")), 0, 0, 1, 6)
        self.gl: dict[str, QComboBox] = {}
        for i, (k, l) in enumerate(GEO_F.items()):
            cb = QComboBox()
            cb.addItem("— tidak dari logging —", "")
            for c in cols:
                cb.addItem(c["name"], c["name"])
            cb.setCurrentIndex(max(0, cb.findData(gl.get(k) or "")))
            cb.activated.connect(lambda *_: self._save_link(False))
            self.gl[k] = cb
            self.glL.addWidget(QLabel(l), 1 + i // 3, (i % 3) * 2)
            self.glL.addWidget(cb, 1 + i // 3, (i % 3) * 2 + 1)
        if not auto:
            ab = btn("Kembali ke tebakan otomatis", sm=True)
            ab.clicked.connect(lambda: self._save_link(True))
            self.glL.addWidget(ab, 3, 0, 1, 2)

    def _save_link(self, reset: bool) -> None:
        link = None if reset else {k: (cb.currentData() or None) for k, cb in self.gl.items()}
        try:
            j = api.call("/core/dh/geolink", {"folder": self.folder, "link": link})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.summary(j["summary"])
        self.changed.emit()

    def _tab(self, i: int) -> None:
        self.kind = self.tabs.tabData(i) or "assay"
        self.src = self.pv = None
        self.reset()
        self.summary(self.sumj)

    def reset(self) -> None:
        self.wBody.hide()
        self.rep.hide()
        self.go.setEnabled(False)
        self.fname.setText("belum ada file")
        self.sheet.hide()

    # ---------------------------------------------------------------- file & pratinjau
    def pick(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Pilih file " + KIND_L[self.kind], SET.get("dhDir", ""), "CSV / Excel (*.csv *.txt *.tsv *.xlsx *.xlsm)")
        if not f:
            return
        SET.set("dhDir", str(Path(f).parent))
        self.src = {"path": f, "name": Path(f).name}
        self.preview()

    def preview(self, hr: int | None = None, sheet: str | None = None) -> None:
        self.fname.setText(self.src["name"] + " · membaca…")
        try:
            j = api.call("/core/dh/preview", {"folder": self.folder, "kind": self.kind, "header_row": hr,
                                              "sheet": sheet or (self.pv or {}).get("sheet"), **self.src})
        except api.ApiError as e:
            self.fname.setText(self.src["name"])
            say(self, "Gagal membaca file:\n" + str(e), warn=True)
            return
        self.pv = j
        self.fname.setText(self.src["name"] + (" · pemetaan terakhir dipakai lagi" if j.get("reused") else ""))
        self.hr.blockSignals(True)
        self.hr.setValue(j["header_row"] + 1)
        self.hr.blockSignals(False)
        self.sheet.blockSignals(True)
        self.sheet.clear()
        self.sheet.addItems(j.get("sheets") or [])
        self.sheet.setCurrentText(j.get("sheet") or "")
        self.sheet.setVisible(len(j.get("sheets") or []) > 1)
        self.sheet.blockSignals(False)
        self.nlab.setText(_n(j["nrows"]) + " baris data" + (" · sheet " + j["sheet"] if j.get("sheet") else ""))
        # peran utama
        while self.rolesL.count():
            w = self.rolesL.takeAt(0).widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        self.roles: dict[str, QComboBox] = {}
        for i, r in enumerate(j["roles"]):
            cb = QComboBox()
            cb.addItem("— tidak ada —", None)
            for k, h in enumerate(j["headers"]):
                cb.addItem(h or f"(kolom {k + 1})", k)
            g = j["guess"]["roles"].get(r["key"])
            cb.setCurrentIndex(cb.findData(g) if g is not None else 0)
            cb.currentIndexChanged.connect(lambda *_: self._pv_table())
            self.roles[r["key"]] = cb
            lab = QLabel(_esc(r["label"]) + (" <b style='color:%s'>*</b>" % theme.C["er"] if r.get("req") else ""))
            self.rolesL.addWidget(lab, i // 3, (i % 3) * 2)
            self.rolesL.addWidget(cb, i // 3, (i % 3) * 2 + 1)
        # kolom tambahan
        show_cols = self.kind != "survey"
        self.colsLab.setVisible(show_cols)
        self.colsT.setVisible(show_cols)
        cols = j["guess"]["cols"]
        self.colsT.setRowCount(len(cols))
        self.cw: list[tuple] = []
        for k, c in enumerate(cols):
            use = QCheckBox()
            use.setChecked(bool(c.get("use")))
            name = QLineEdit(c.get("name") or "")
            ty = QComboBox()
            ty.addItem("angka", "n")
            ty.addItem("teks", "s")
            ty.setCurrentIndex(0 if c.get("type") == "n" else 1)
            ex = " · ".join(str(r[c["i"]]) for r in j["sample"][:3] if c["i"] < len(r) and r[c["i"]] not in ("", None))[:40]
            self.colsT.setCellWidget(k, 0, use)
            self.colsT.setItem(k, 1, QTableWidgetItem(str(c.get("src") or "")))
            self.colsT.setCellWidget(k, 2, name)
            self.colsT.setCellWidget(k, 3, ty)
            it = QTableWidgetItem(ex)
            it.setForeground(QBrush(QColor(theme.C["mu"])))
            self.colsT.setItem(k, 4, it)
            for w in (use,):
                w.toggled.connect(lambda *_: self._pv_table())
            name.editingFinished.connect(self._pv_table)
            self.cw.append((use, name, ty))
        self.colsT.resizeColumnsToContents()
        self.colsT.setColumnWidth(2, 160)
        self._pv_table()
        self.wBody.show()
        self.go.setEnabled(True)
        self.rep.hide()

    def mapping(self) -> dict:
        roles = {k: cb.currentData() for k, cb in self.roles.items()}
        cols = []
        for c, (use, name, ty) in zip(self.pv["guess"]["cols"], self.cw):
            d = dict(c)
            d.update(use=use.isChecked(), name=name.text(), type=ty.currentData())
            cols.append(d)
        used = {v for v in roles.values() if v is not None}
        for c in cols:
            if c["i"] in used:
                c["use"] = False
        return {"roles": roles, "cols": cols}

    def _pv_table(self) -> None:
        j, m = self.pv, self.mapping()
        role_of = {v: next((r["label"] for r in j["roles"] if r["key"] == k), k) for k, v in m["roles"].items() if v is not None}
        col_of = {c["i"]: c for c in m["cols"]}
        t = self.pvT
        t.clear()
        t.setColumnCount(len(j["headers"]))
        t.setRowCount(len(j["sample"]))
        for i, h in enumerate(j["headers"]):
            r, c = role_of.get(i), col_of.get(i)
            lab = (h or "(kosong)") + (f"\n→ {r}" if r else (f"\n→ {c['name']}" if c and c["use"] and c["name"] != h else ""))
            it = QTableWidgetItem(lab)
            it.setToolTip(f"dipakai sebagai {r}" if r else f"ikut sebagai {c['name']}" if c and c["use"] else "tidak dipakai")
            if r:
                it.setForeground(QBrush(QColor(theme.C["hd"])))
            elif not (c and c["use"]):
                it.setForeground(QBrush(QColor(theme.C["bd2"])))
            t.setHorizontalHeaderItem(i, it)
        for ri, row in enumerate(j["sample"]):
            for ci in range(len(j["headers"])):
                t.setItem(ri, ci, QTableWidgetItem("" if ci >= len(row) or row[ci] is None else str(row[ci])))
        t.resizeColumnsToContents()

    # ---------------------------------------------------------------- import / hapus
    def do_import(self) -> None:
        if not self.pv:
            return
        m = self.mapping()
        miss = [r["label"] for r in self.pv["roles"] if r.get("req") and m["roles"].get(r["key"]) is None]
        if miss:
            say(self, "Pilih kolom untuk: " + ", ".join(miss))
            return
        mode = self.mode.currentData()
        if mode == "replace" and self.sumj.get(self.kind) and not ask(self, f"Ganti SEMUA {self.sumj[self.kind]} baris {KIND_L[self.kind]} di proyek dengan isi file ini?"):
            return
        self.go.setEnabled(False)
        try:
            j = api.call("/core/dh/import", {"folder": self.folder, "kind": self.kind, "header_row": self.pv["header_row"], "sheet": self.pv.get("sheet"),
                                             "roles": m["roles"], "cols": m["cols"], "mode": mode, **self.src})
        except api.ApiError as e:
            say(self, "Import gagal:\n" + str(e), warn=True)
            self.go.setEnabled(True)
            return
        self.go.setEnabled(True)
        r = j["report"]
        h = f"<b>{KIND_L[self.kind]}: {_n(r['rows'])} baris diimport</b> · {r['holes']} hole"
        if r.get("matched_photo_holes") is not None and self.kind != "collar":
            h += f" · {r['matched_photo_holes']} hole cocok dengan foto"
        if r.get("skipped"):
            h += f"<br>Dilewati {r['skipped']}: " + ", ".join(f"{_esc(k)} ({v})" for k, v in (r.get("reasons") or {}).items())
        if r.get("bdl"):
            h += f"<br>{r['bdl']} nilai di bawah limit deteksi (&lt;) dibaca setengah nilainya."
        h += "".join("<br>⚠ " + _esc(w) for w in r.get("warnings") or [])
        set_box(self.rep, h, "ok")
        self.rep.show()
        self.summary(j["summary"])
        self.changed.emit()

    def clear(self) -> None:
        if not self.sumj.get(self.kind):
            say(self, f"Tabel {KIND_L[self.kind]} sudah kosong.")
            return
        if not ask(self, f"Hapus semua data {KIND_L[self.kind]} ({self.sumj[self.kind]} baris) dari proyek ini? File sumber tidak terpengaruh."):
            return
        try:
            j = api.call("/core/dh/clear", {"folder": self.folder, "kind": self.kind})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.summary(j["summary"])
        self.changed.emit()


__all__ = ["DhDlg", "Qt"]
