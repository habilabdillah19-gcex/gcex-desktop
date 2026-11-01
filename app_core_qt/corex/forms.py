"""Ruang kerja Borang: borang lapangan tulisan tangan (Ore Spotter loading pit, Ore ke ROM / crusher, RC Drill / Chiptray Log).

Kiri: daftar borang (+ Borang: foto / scan / PDF, satu borang per halaman). Tengah: scan (zoom, putar). Kanan: tab Data
(header & tabel yang bisa diedit; sel ragu AI kuning, galat validasi merah; centang ✓ = baris diverifikasi), Pivot (Ore
Spotter) dan Ekspor (Excel, CSV, SQLite, MS Access). Data lewat rute /core/forms/* (backend core_forms)."""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QRadioButton, QSplitter, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from . import api, theme
from .card import _esc, btn
from .dialogs import ask, say
from .util import SET, log, run_bg, show_in_folder
from .viewer import Viewer

SHORT = {"ore": "Loading pit", "rom": "ROM / crusher", "rc": "RC Drill"}
FILE = {"ore": "Ore_Loading_Pit", "rom": "Ore_ROM_Crusher", "rc": "RC_Drill"}
UNC_BG, BAD_BG, VER_BG = "#fff3bf", "#ffe3e3", "#e6f4ea"


class ScanView(Viewer):
    """Scan borang (resolusi penuh); tombol ↻ menyimpan rotasi borang (dipakai juga saat AI membaca)."""

    def __init__(self, page: "FormsPage"):
        super().__init__()
        self.pg = page
        self.btn["full"].hide()

    def show_scan(self, path: Path, key: int, rot: int) -> None:
        self.folder, self.pid, self.full, self.rot = "", key, True, int(rot or 0)
        self.root.setRotation(0)
        self.info.setText(path.name)
        self.info.show()
        self._place()
        if not path.exists():
            self.placeholder("File scan tidak ditemukan di folder proyek (_GCEx_Core/borang/scan).")
            return
        run_bg(lambda: QImage(str(path)), ok=lambda im: self._loaded(key, im), err=lambda e: self.placeholder("Scan tidak bisa dibuka.\n" + e))

    def _loaded(self, key: int, im: QImage) -> None:
        self._got(key, im, False)
        if key == self.pid and self.w:
            self.root.setRotation(self.rot)
            self.fit()

    def load_full(self) -> None:
        return

    def rotate90(self) -> None:
        if not self.w:
            return
        self.rot = (self.rot + 90) % 360
        self.root.setRotation(self.rot)
        self.fit()
        self.pg.save_rot(self.rot)


class FormsPage(QWidget):
    def __init__(self, win) -> None:
        super().__init__()
        self.win = win
        self.folder = ""
        self.rootp = ""
        self.types: dict = {}
        self.docs: list[dict] = []
        self.cur: dict | None = None      # {"doc", "rows", "valid", "recs", "pivot"}
        self.ai_busy = False
        self._filling = False
        self._build()

    # ---------------------------------------------------------------- tata letak
    def _build(self) -> None:
        o = QHBoxLayout(self)
        o.setContentsMargins(0, 0, 0, 0)
        sp = QSplitter(Qt.Horizontal)
        sp.setHandleWidth(5)
        o.addWidget(sp)
        # kiri
        lw = QWidget()
        lv = QVBoxLayout(lw)
        lv.setContentsMargins(10, 10, 6, 10)
        hd = QLabel("<b>BORANG LAPANGAN</b>")
        hd.setObjectName("note")
        lv.addWidget(hd)
        self.cbNew = QComboBox()
        self.cbNew.setToolTip("Jenis borang untuk file yang akan ditambahkan")
        lv.addWidget(self.cbNew)
        r = QHBoxLayout()
        self.bAdd = btn("+ Borang", "Tambah foto / scan / PDF borang (disalin ke folder proyek; PDF: satu borang per halaman)", pri=True, sm=True)
        self.bDel = btn("Hapus", sm=True)
        r.addWidget(self.bAdd)
        r.addWidget(self.bDel)
        r.addStretch(1)
        lv.addLayout(r)
        self.lst = QListWidget()
        self.lst.setIconSize(QSize(64, 84))
        self.lst.setWordWrap(True)
        self.lst.setTextElideMode(Qt.ElideMiddle)
        lv.addWidget(self.lst, 1)
        self.sum = QLabel()
        self.sum.setObjectName("note")
        self.sum.setWordWrap(True)
        lv.addWidget(self.sum)
        sp.addWidget(lw)
        # tengah
        cw = QWidget()
        cv = QVBoxLayout(cw)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        tb = QFrame()
        tb.setObjectName("fbar")
        th = QHBoxLayout(tb)
        th.setContentsMargins(10, 5, 10, 5)
        self.title = QLabel()
        self.title.setTextFormat(Qt.RichText)
        th.addWidget(self.title, 1)
        self.bAI = btn("✦ Baca dengan AI", "AI vision lokal (Ollama) membaca header & tabel borang. Baris lama diganti.", pri=True, sm=True)
        th.addWidget(self.bAI)
        cv.addWidget(tb)
        self.view = ScanView(self)
        self.view.placeholder("Tambahkan foto / scan / PDF borang dengan + Borang.\nScroll = zoom, tarik = geser, ↻ = putar (juga untuk AI).")
        cv.addWidget(self.view, 1)
        self.aiInfo = QLabel()
        self.aiInfo.setObjectName("note")
        self.aiInfo.setWordWrap(True)
        self.aiInfo.setContentsMargins(10, 4, 10, 4)
        cv.addWidget(self.aiInfo)
        sp.addWidget(cw)
        # kanan
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(460)
        self.tabs.addTab(self._tab_data(), "Data")
        self.tabs.addTab(self._tab_pivot(), "Pivot")
        self.tabs.addTab(self._tab_export(), "Ekspor")
        sp.addWidget(self.tabs)
        sp.setStretchFactor(1, 1)
        sp.setSizes(SET.get("qt_fm_split", [230, 700, 620]))
        sp.splitterMoved.connect(lambda *_: SET.set("qt_fm_split", sp.sizes()))
        self.bAdd.clicked.connect(self.add_files)
        self.bDel.clicked.connect(self.delete_doc)
        self.bAI.clicked.connect(self.run_ai)
        self.lst.currentRowChanged.connect(self._pick)
        self.set_enabled(False)

    def _tab_data(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)
        self.hdrBox = QFrame()
        self.hdrBox.setObjectName("fld")
        self.hdrForm = QFormLayout(self.hdrBox)
        self.hdrForm.setContentsMargins(8, 6, 8, 6)
        self.hdrEd: dict[str, QLineEdit] = {}
        v.addWidget(self.hdrBox)
        self.valInfo = QLabel()
        self.valInfo.setTextFormat(Qt.RichText)
        self.valInfo.setWordWrap(True)
        v.addWidget(self.valInfo)
        self.t = QTableWidget(0, 1)
        self.t.verticalHeader().setDefaultSectionSize(24)
        self.t.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.t.itemChanged.connect(self._cell)
        v.addWidget(self.t, 1)
        r = QHBoxLayout()
        self.bRow = btn("+ Baris", sm=True)
        self.bIns = btn("Sisipkan", "Sisipkan baris di atas baris terpilih", sm=True)
        self.bRowDel = btn("Hapus baris", sm=True)
        self.bVerAll = btn("✓ Verifikasi semua", "Tandai semua baris sudah diperiksa terhadap scan", sm=True)
        self.bUnver = btn("Batal verifikasi", sm=True)
        for b in (self.bRow, self.bIns, self.bRowDel, self.bVerAll, self.bUnver):
            r.addWidget(b)
        r.addStretch(1)
        v.addLayout(r)
        n = QLabel("<span style='background:%s'>&nbsp;kuning&nbsp;</span> = AI ragu / diisi program dari tanda ulang (〃, garis), <span style='background:%s'>&nbsp;merah&nbsp;</span> = "
                   "galat validasi (arahkan kursor untuk alasannya). Periksa tiap baris terhadap scan lalu centang <b>✓</b> "
                   "(Ctrl+Enter = verifikasi baris & lanjut). Ekspor bawaan hanya baris terverifikasi." % (UNC_BG, BAD_BG))
        n.setObjectName("note")
        n.setWordWrap(True)
        n.setTextFormat(Qt.RichText)
        v.addWidget(n)
        self.bRow.clicked.connect(lambda: self.add_row(None))
        self.bIns.clicked.connect(lambda: self.add_row(max(0, self.t.currentRow())))
        self.bRowDel.clicked.connect(self.del_row)
        self.bVerAll.clicked.connect(lambda: self.verify_all(True))
        self.bUnver.clicked.connect(lambda: self.verify_all(False))
        return w

    def _tab_pivot(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 12)
        self.pvNote = QLabel()
        self.pvNote.setObjectName("note")
        self.pvNote.setWordWrap(True)
        v.addWidget(self.pvNote)
        self.pv: list[QTableWidget] = []
        self.pvLab: list[QLabel] = []
        for _i in range(3):
            lab = QLabel()
            v.addWidget(lab)
            tw = QTableWidget(0, 0)
            tw.verticalHeader().hide()
            tw.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tw.setMaximumHeight(200)
            v.addWidget(tw)
            self.pv.append(tw)
            self.pvLab.append(lab)
        v.addStretch(1)
        return w

    def _tab_export(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)
        self.rThis = QRadioButton("Borang ini")
        self.rAll = QRadioButton("Semua borang jenis ini di proyek")
        self.rAll.setChecked(True)
        v.addWidget(self.rThis)
        v.addWidget(self.rAll)
        self.cUnver = QCheckBox("Sertakan baris yang belum diverifikasi (ditandai VERIFIED = 0)")
        v.addWidget(self.cUnver)
        g = QHBoxLayout()
        self.eX = btn("⇩ Excel (.xlsx)", "Sheet data siap tempel + pivot (borang ore) + Audit", pri=True, sm=True)
        self.eC = btn("⇩ CSV", sm=True)
        g.addWidget(self.eX)
        g.addWidget(self.eC)
        g.addStretch(1)
        v.addLayout(g)
        g2 = QHBoxLayout()
        self.eS = btn("→ SQLite (.db)", "Tambah / perbarui ke file SQLite (dibuat bila belum ada); borang ore: view pivot ikut dibuat", sm=True)
        self.eA = btn("→ MS Access (.accdb)", "Tambahkan ke database Access (dibuat bila belum ada; tabel dibuat otomatis). "
                      "Butuh driver Access 64-bit (MS Office 64-bit / Access Database Engine).", sm=True)
        g2.addWidget(self.eS)
        g2.addWidget(self.eA)
        g2.addStretch(1)
        v.addLayout(g2)
        self.expInfo = QLabel()
        self.expInfo.setTextFormat(Qt.RichText)
        self.expInfo.setWordWrap(True)
        self.expInfo.setObjectName("fld")
        self.expInfo.setMargin(8)
        self.expInfo.hide()
        v.addWidget(self.expInfo)
        n = QLabel("Tabel database: <b>ORE_LOADING_PIT</b>, <b>ORE_ROM_CRUSHER</b> atau <b>RC_INTERVAL</b> dengan kolom VERIFIED, SRC_DOC dan SRC_KEY (borang:baris). "
                   "Ekspor ulang tidak menggandakan baris: SQLite memperbarui baris yang sama, MS Access melewati baris yang sudah ada.")
        n.setObjectName("note")
        n.setWordWrap(True)
        n.setTextFormat(Qt.RichText)
        v.addWidget(n)
        v.addStretch(1)
        for b_, f in ((self.eX, "xlsx"), (self.eC, "csv"), (self.eS, "sqlite"), (self.eA, "access")):
            b_.clicked.connect(lambda _=False, f=f: self.export(f))
        return w

    # ---------------------------------------------------------------- util
    def by(self) -> str:
        return self.win.user()

    def toast(self, m: str, ms: int = 2600) -> None:
        self.win.toast(m, ms)

    def set_enabled(self, on: bool) -> None:
        self.bAdd.setEnabled(bool(self.folder))
        self.cbNew.setEnabled(bool(self.folder))
        for w in (self.bDel, self.bAI, self.tabs):
            w.setEnabled(on)

    def ftype(self) -> str:
        return (self.cur or {}).get("doc", {}).get("type") or self.cbNew.currentData() or "ore"

    def escape(self) -> bool:
        return False

    # ---------------------------------------------------------------- proyek & daftar
    def open(self, folder: str) -> None:
        self.folder = folder
        self.cur = None
        try:
            j = api.call("/core/forms/open", {"folder": folder})
        except api.ApiError as e:
            say(self, "Gagal membuka data borang:\n" + str(e), warn=True)
            return
        self.types = j["types"]
        self.rootp = j.get("root") or ""
        cur = self.cbNew.currentData() or SET.get("fmType", "ore")
        self.cbNew.blockSignals(True)
        self.cbNew.clear()
        for k, t in self.types.items():
            self.cbNew.addItem(t["name"], k)
        self.cbNew.setCurrentIndex(max(0, self.cbNew.findData(cur)))
        self.cbNew.blockSignals(False)
        self.docs = j["docs"]
        self._fill_list()
        self.set_enabled(False)
        if self.docs:
            self.lst.setCurrentRow(0)
        else:
            self.view.placeholder("Belum ada borang di proyek ini.\nPilih jenis borang lalu klik + Borang (foto, scan atau PDF).")
            self._clear()

    def _root(self) -> Path | None:
        return Path(self.rootp) if self.rootp else None

    def _line(self, d: dict) -> str:
        t = SHORT.get(d["type"], d["type"])
        st = {"done": "AI", "error": "AI gagal", "pending": "belum dibaca"}.get(d["status"], d["status"])
        s = f"{d['name']}\n{t} · {st}"
        if d.get("n_rows"):
            s += f" · {d['n_ver']}/{d['n_rows']} ✓" + (f" · {d['n_unc']} ragu" if d.get("n_unc") else "")
        return s

    def _fill_list(self) -> None:
        cur = self.cur["doc"]["id"] if self.cur else None
        self.lst.blockSignals(True)
        self.lst.clear()
        root = self._root()
        for d in self.docs:
            it = QListWidgetItem(self._line(d))
            it.setData(Qt.UserRole, d["id"])
            f = root / "scan" / d["file"] if root else None
            if f and f.exists():
                did = d["id"]
                run_bg(lambda f=f: QImage(str(f)).scaled(96, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation),
                       ok=lambda im, did=did: self._thumb(did, im))
            self.lst.addItem(it)
        if cur is not None:
            for i in range(self.lst.count()):
                if self.lst.item(i).data(Qt.UserRole) == cur:
                    self.lst.setCurrentRow(i)
        self.lst.blockSignals(False)
        n = len(self.docs)
        rr = sum(d.get("n_rows") or 0 for d in self.docs)
        vv = sum(d.get("n_ver") or 0 for d in self.docs)
        self.sum.setText(f"{n} borang · {rr} baris · {vv} diverifikasi")

    def _thumb(self, did: int, im: QImage) -> None:
        for i in range(self.lst.count()):
            if self.lst.item(i).data(Qt.UserRole) == did:
                self.lst.item(i).setIcon(QIcon(QPixmap.fromImage(im)))

    def _sync_list(self) -> None:
        if not self.cur:
            return
        try:
            self.docs = api.call("/core/forms/open", {"folder": self.folder})["docs"]
        except api.ApiError:
            return
        for i in range(self.lst.count()):
            it = self.lst.item(i)
            d = next((x for x in self.docs if x["id"] == it.data(Qt.UserRole)), None)
            if d:
                it.setText(self._line(d))
        rr = sum(d.get("n_rows") or 0 for d in self.docs)
        vv = sum(d.get("n_ver") or 0 for d in self.docs)
        self.sum.setText(f"{len(self.docs)} borang · {rr} baris · {vv} diverifikasi")

    def add_files(self) -> None:
        if not self.folder:
            return
        ft = self.cbNew.currentData()
        SET.set("fmType", ft)
        fs, _ = QFileDialog.getOpenFileNames(self, f"Tambah borang {self.types[ft]['name']}", SET.get("fmLastDir", str(Path.home())),
                                             "Borang (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp *.pdf)")
        if not fs:
            return
        SET.set("fmLastDir", str(Path(fs[0]).parent))
        self.toast("Menyalin borang ke proyek…", 3000)

        def ok(j):
            self.docs = j["docs"]
            self._fill_list()
            if j["errors"]:
                say(self, "Sebagian file dilewati:\n" + "\n".join(j["errors"]), warn=True)
            if j["added"]:
                did = j["added"][0]["id"]
                i = next(i for i, d in enumerate(self.docs) if d["id"] == did)
                self.lst.setCurrentRow(i)
                self._pick(i)
                self.toast(f"{len(j['added'])} borang ditambahkan — klik ✦ Baca dengan AI", 4000)
        run_bg(api.call, "/core/forms/add", {"folder": self.folder, "paths": fs, "type": ft, "by": self.by()}, ok=ok,
               err=lambda e: say(self, "Borang tidak ditambahkan:\n" + e, warn=True))

    def delete_doc(self) -> None:
        if not self.cur:
            return
        d = self.cur["doc"]
        if not ask(self, f"Hapus borang \"{d['name']}\" beserta {len(self.cur['rows'])} baris dari proyek?\n\nFile asli di luar proyek tidak tersentuh."):
            return
        try:
            j = api.call("/core/forms/delete", {"folder": self.folder, "id": d["id"], "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.cur = None
        self.docs = j["docs"]
        self._fill_list()
        if self.docs:
            self.lst.setCurrentRow(0)
            self._pick(0)
        else:
            self._clear()
            self.view.placeholder("Belum ada borang di proyek ini.")

    def _clear(self) -> None:
        self.cur = None
        self.set_enabled(False)
        self.title.setText("")
        self.t.setRowCount(0)

    def _pick(self, i: int) -> None:
        if not 0 <= i < len(self.docs):
            return
        did = self.docs[i]["id"]
        try:
            j = api.call("/core/forms/doc", {"folder": self.folder, "id": did})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        same = self.cur and self.cur["doc"]["id"] == did
        self.cur = j
        self.set_enabled(True)
        if not same:
            root = self._root()
            self.view.show_scan(root / "scan" / j["doc"]["file"] if root else Path(j["doc"]["file"]), did, j["doc"].get("rot") or 0)
        self.refresh()

    # ---------------------------------------------------------------- tampil
    def refresh(self) -> None:
        c = self.cur
        if not c:
            return
        d = c["doc"]
        t = self.types[d["type"]]
        self.title.setText(f"<b>{_esc(d['name'])}</b> · {_esc(t['name'])}")
        if d["status"] == "done":
            self.aiInfo.setText(f"Dibaca AI {_esc(d.get('ai_model') or '')} · {'-' if d.get('ai_secs') is None else round(d['ai_secs'])} dtk · {_esc(d.get('ai_at') or '')}"
                                + (f" · catatan AI: {_esc(d['ai_note'])}" if d.get("ai_note") else ""))
        elif d["status"] == "error":
            self.aiInfo.setText(f"<span style='color:{theme.C['er']}'>AI gagal: {_esc(d.get('error') or '')}</span> — tabel tidak diisi.")
        else:
            self.aiInfo.setText("Belum dibaca AI. Putar scan bila perlu (↻), lalu ✦ Baca dengan AI — atau isi tabel manual.")
        self.aiInfo.setTextFormat(Qt.RichText)
        self._header(d, t)
        self._table(d, t, c["rows"], c["valid"])
        self._pivot(c.get("pivot"))
        self.tabs.setTabEnabled(1, bool(c.get("pivot")))

    def _header(self, d: dict, t: dict) -> None:
        keys = [k for k, _l, _t in t["header"]]
        if list(self.hdrEd) != keys:
            while self.hdrForm.rowCount():
                self.hdrForm.removeRow(0)
            self.hdrEd = {}
            for k, lab, _ty in t["header"]:
                e = QLineEdit()
                e.editingFinished.connect(lambda k=k: self._hdr_save(k))
                self.hdrForm.addRow(lab, e)
                self.hdrEd[k] = e
        v = self.cur["valid"]["header"]
        for k, e in self.hdrEd.items():
            if not e.hasFocus():
                e.setText(str(d["header"].get(k) or ""))
            bg = BAD_BG if k in v else (UNC_BG if k in d.get("hdr_unc", []) else "")
            e.setStyleSheet(f"background:{bg};color:#141a26" if bg else "")
            e.setToolTip(v.get(k) or ("AI ragu membaca isian ini" if k in d.get("hdr_unc", []) else ""))

    def cols(self, t: dict) -> list[tuple[str, str]]:
        c = [(k, lab) for k, lab, _ty in t["rows"]]
        return c

    def _table(self, d: dict, t: dict, rows: list[dict], valid: dict) -> None:
        self._filling = True
        cols = self.cols(t)
        derived = [("tanggal_muat", "Tgl muat")] if d["type"] in ("ore", "rom") else []
        tb = self.t
        tb.clear()
        tb.setColumnCount(1 + len(cols) + len(derived))
        tb.setHorizontalHeaderLabels(["✓"] + [lab for _k, lab in cols] + [lab for _k, lab in derived])
        tb.setRowCount(len(rows))
        recs = {r["_row"]: r for r in self.cur["recs"]}
        bad = valid["rows"]
        for i, r in enumerate(rows):
            ck = QTableWidgetItem()
            ck.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            ck.setCheckState(Qt.Checked if r["verified"] else Qt.Unchecked)
            ck.setData(Qt.UserRole, r["id"])
            if r["verified"]:
                ck.setBackground(QColor(VER_BG))
                ck.setToolTip(f"diverifikasi {r.get('verified_by') or ''} {r.get('verified_at') or ''}")
            tb.setItem(i, 0, ck)
            for j, (k, _lab) in enumerate(cols, 1):
                it = QTableWidgetItem(str(r["data"].get(k) or ""))
                msg = (bad.get(r["id"]) or bad.get(str(r["id"])) or {}).get(k)
                if msg:
                    it.setBackground(QColor(BAD_BG))
                    it.setToolTip(msg)
                elif k in r["unc"]:
                    it.setBackground(QColor(UNC_BG))
                    it.setToolTip("AI ragu membaca sel ini, atau diisi program dari tanda ulang / baris di atas — cocokkan dengan scan")
                tb.setItem(i, j, it)
            for j, (k, _lab) in enumerate(derived, 1 + len(cols)):
                it = QTableWidgetItem(str((recs.get(r["id"]) or {}).get(k) or ""))
                it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                it.setForeground(QColor(theme.C["mu"]))
                tb.setItem(i, j, it)
        hh = tb.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        self._filling = False
        n_ver = sum(1 for r in rows if r["verified"])
        n_unc = sum(1 for r in rows if r["unc"])
        nb = valid["n"]
        er = theme.C["er"]
        self.valInfo.setText(f"{len(rows)} baris · <b>{n_ver}</b> diverifikasi · {n_unc} baris ragu · "
                             + (f"<span style='color:{er}'><b>{nb}</b> galat validasi</span>" if nb else "validasi bersih")
                             + "".join(f"<br><span style='color:{er}'>⚠ {_esc(m)}</span>" for m in valid["header"].values()))

    def _pivot(self, pv: list | None) -> None:
        """Pivot dari backend: [{key, title, cols: [[k, label]], rows}] (Ore Spotter: per shift, per front / asal, per tujuan x kelas)."""
        self.pvNote.setText("Ritase & tonase dari borang ini (semua baris, terverifikasi maupun belum). Pivot gabungan semua borang ada di "
                            "ekspor Excel dan view SQLite.")
        pv = pv or []
        for i, (lab, tw) in enumerate(zip(self.pvLab, self.pv)):
            p = pv[i] if i < len(pv) else None
            lab.setVisible(bool(p))
            tw.setVisible(bool(p))
            tw.clear()
            if not p:
                continue
            lab.setText(f"<b>{_esc(p['title'])}</b>")
            tw.setColumnCount(len(p["cols"]))
            tw.setHorizontalHeaderLabels([h for _k, h in p["cols"]])
            tw.setRowCount(len(p["rows"]))
            for r, x in enumerate(p["rows"]):
                for j, (kk, _h) in enumerate(p["cols"]):
                    v = x.get(kk)
                    tw.setItem(r, j, QTableWidgetItem("" if v is None else (f"{v:g}" if isinstance(v, float) else str(v))))
            tw.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    # ---------------------------------------------------------------- edit
    def _rows_from_table(self) -> list[dict]:
        t = self.types[self.cur["doc"]["type"]]
        cols = self.cols(t)
        out = []
        for i in range(self.t.rowCount()):
            ck = self.t.item(i, 0)
            rid = ck.data(Qt.UserRole) if ck else None
            data = {k: (self.t.item(i, j).text() if self.t.item(i, j) else "") for j, (k, _l) in enumerate(cols, 1)}
            out.append({"id": rid, "data": data, "verified": bool(ck and ck.checkState() == Qt.Checked)})
        return out

    def _save_rows(self, rows: list[dict], keep_cell=None) -> None:
        if not self.cur:
            return
        try:
            j = api.call("/core/forms/rows", {"folder": self.folder, "id": self.cur["doc"]["id"], "rows": rows, "by": self.by()})
        except api.ApiError as e:
            say(self, "Perubahan tidak disimpan:\n" + str(e), warn=True)
            return
        self.cur = j
        self.refresh()
        if keep_cell:
            r, c = keep_cell
            if 0 <= r < self.t.rowCount():
                self.t.setCurrentCell(r, c)
        self._sync_list()

    def _cell(self, it: QTableWidgetItem) -> None:
        if self._filling or not self.cur:
            return
        r, c = it.row(), it.column()
        QTimer.singleShot(0, self, lambda: self._save_rows(self._rows_from_table(), (r, c)))

    def add_row(self, at: int | None) -> None:
        if not self.cur:
            return
        rows = self._rows_from_table()
        new = {"id": None, "data": {}, "verified": False}
        if self.cur["doc"]["type"] == "rc" and rows:  # lanjutkan interval & nomor sampel
            ref = rows[(at if at is not None else len(rows)) - 1] if (at or len(rows)) else rows[-1]
            to = ref["data"].get("to_m") or ""
            try:
                f, t = float(ref["data"].get("from_m") or 0), float(to)
                new["data"] = {"from_m": f"{t:g}", "to_m": f"{t + (t - f):g}"}
            except ValueError:
                new["data"] = {"from_m": to}
            m = re.match(r"^(.*?)(\d+)(\D*)$", ref["data"].get("sample_id") or "")
            if m:
                new["data"]["sample_id"] = f"{m.group(1)}{int(m.group(2)) + 1:0{len(m.group(2))}d}{m.group(3)}"
        if at is None:
            rows.append(new)
            pos = len(rows) - 1
        else:
            rows.insert(at, new)
            pos = at
        self._save_rows(rows, (pos, 1))

    def del_row(self) -> None:
        r = self.t.currentRow()
        if r < 0 or not self.cur:
            return
        rows = self._rows_from_table()
        rows.pop(r)
        self._save_rows(rows, (min(r, len(rows) - 1), 1))

    def verify_next(self) -> None:
        if self.t.state() == QAbstractItemView.EditingState:  # simpan isian sel yang sedang diketik dulu
            w = QApplication.focusWidget()
            if w:
                w.clearFocus()
            QTimer.singleShot(0, self, self.verify_next)
            return
        r = self.t.currentRow()
        if r < 0 or not self.cur:
            return
        rows = self._rows_from_table()
        rows[r]["verified"] = True
        self._save_rows(rows, (min(r + 1, len(rows) - 1), max(1, self.t.currentColumn())))

    def verify_all(self, on: bool) -> None:
        if not self.cur:
            return
        if on and self.cur["valid"]["n"] and not ask(self, f"Masih ada {self.cur['valid']['n']} galat validasi. Tetap tandai semua baris "
                                                          "sudah diverifikasi?"):
            return
        try:
            self.cur = api.call("/core/forms/verify", {"folder": self.folder, "id": self.cur["doc"]["id"], "on": on, "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.refresh()
        self._sync_list()

    def _hdr_save(self, k: str) -> None:
        if not self.cur:
            return
        v = self.hdrEd[k].text().strip()
        if str(self.cur["doc"]["header"].get(k) or "") == v and k not in self.cur["doc"].get("hdr_unc", []):
            return
        try:
            self.cur = api.call("/core/forms/update", {"folder": self.folder, "id": self.cur["doc"]["id"], "values": {"header": {k: v}},
                                                       "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.refresh()

    def save_rot(self, rot: int) -> None:
        if not self.cur:
            return
        try:
            self.cur = api.call("/core/forms/update", {"folder": self.folder, "id": self.cur["doc"]["id"], "values": {"rot": rot}, "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)

    # ---------------------------------------------------------------- AI
    def run_ai(self) -> None:
        if not self.cur or self.ai_busy:
            return
        ai = self.win.ai
        model = ai.model()
        if not ai.info or not ai.info.get("running") or not model:
            self.win.open_ai()
            return
        n_ver = sum(1 for r in self.cur["rows"] if r["verified"])
        if self.cur["rows"] and not ask(self, f"Baca ulang dengan AI? {len(self.cur['rows'])} baris yang ada (termasuk {n_ver} terverifikasi) "
                                              "akan diganti hasil AI. Isian header yang Anda edit tetap."):
            return
        did, folder = self.cur["doc"]["id"], self.folder
        body = {"folder": folder, "id": did, "host": ai.host.text().strip(), "model": model, "extra": ai.extra.toPlainText(),
                "max_px": max(1600, int(ai.px.currentData())), "by": self.by()}
        self.ai_busy = True
        self.bAI.setEnabled(False)
        self.bAI.setText("AI membaca borang…")
        self.aiInfo.setText(f"Membaca borang dengan {model}… (tulisan tangan: biasanya 30–180 detik)")

        def done():
            self.ai_busy = False
            self.bAI.setEnabled(bool(self.cur))
            self.bAI.setText("✦ Baca dengan AI")

        def ok(j):
            done()
            if self.cur and self.cur["doc"]["id"] == did:
                self.cur = j
                self.refresh()
            self._sync_list()
            self.toast(f"AI selesai: {len(j['rows'])} baris — periksa sel kuning / merah lalu verifikasi", 5000)

        def err(e):
            done()
            say(self, "AI gagal membaca borang (tabel tidak diisi):\n" + e, warn=True)
            if self.cur and self.cur["doc"]["id"] == did:
                self._pick(self.lst.currentRow())
        run_bg(api.call, "/core/forms/ai", body, ok=ok, err=err)

    # ---------------------------------------------------------------- ekspor
    def export(self, fmt: str) -> None:
        if not self.folder:
            return
        ft = self.ftype()
        ids = [self.cur["doc"]["id"]] if (self.rThis.isChecked() and self.cur) else []
        body = {"folder": self.folder, "ids": ids, "type": ft, "fmt": fmt, "unverified": self.cUnver.isChecked(), "by": self.by()}
        try:
            chk = api.call("/core/forms/export/check", body)
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        if not chk["n"]:
            say(self, f"Tidak ada baris untuk diekspor. {chk['skipped_unverified']} baris belum diverifikasi — verifikasi dulu, atau centang "
                      "'Sertakan baris yang belum diverifikasi'.", warn=True)
            return
        if chk["issues"] and not ask(self, f"Masih ada {chk['issues']} galat validasi di borang yang diekspor. Tetap ekspor?"):
            return
        nm = re.sub(r"[^\w.-]+", "_", FILE.get(ft, ft) + (("_" + self.cur["doc"]["name"]) if ids else ""))[:80]
        ext, filt = {"xlsx": (".xlsx", "Excel (*.xlsx)"), "csv": (".csv", "CSV (*.csv)"), "sqlite": (".db", "SQLite (*.db *.sqlite)"),
                     "access": (".accdb", "MS Access (*.accdb)")}[fmt]
        start = str(Path(SET.get(f"fmDb_{fmt}") or (Path(SET.get("lastSaveDir", str(Path.home()))) / (nm + ext))))
        p, _ = QFileDialog.getSaveFileName(self, "Ekspor borang" if fmt in ("xlsx", "csv") else "Pilih / buat file database", start, filt,
                                           options=QFileDialog.DontConfirmOverwrite if fmt in ("sqlite", "access") else QFileDialog.Options())
        if not p:
            return
        if not p.lower().endswith(ext) and not (fmt == "sqlite" and p.lower().endswith(".sqlite")):
            p += ext
        SET.set("lastSaveDir", str(Path(p).parent))
        if fmt in ("sqlite", "access"):
            SET.set(f"fmDb_{fmt}", p)
        body["path"] = p

        def ok(res):
            if isinstance(res, (bytes, bytearray)):
                tmp = Path(p + ".tmp")
                tmp.write_bytes(res)
                tmp.replace(p)
                msg = f"{chk['n']} baris → <b>{_esc(Path(p).name)}</b>"
                show_in_folder(p)
            else:
                msg = (f"<b>{_esc(res['table'])}</b> di {_esc(Path(p).name)}: {res['added']} baris baru"
                       + (f", {res['updated']} diperbarui" if res.get("updated") else "")
                       + (f", {res['existing']} sudah ada (tidak diubah)" if res.get("existing") else "")
                       + (" · database baru dibuat" if res.get("db_created") else ""))
            if chk["skipped_unverified"] and not self.cUnver.isChecked():
                msg += f"<br>{chk['skipped_unverified']} baris belum diverifikasi tidak ikut."
            self.expInfo.setText(msg)
            self.expInfo.show()
            self.toast("Ekspor selesai", 3000)
            log("[borang] ekspor", fmt, p)
        run_bg(api.call, "/core/forms/export", body, ok=ok, err=lambda e: say(self, "Gagal ekspor:\n" + e, warn=True))

