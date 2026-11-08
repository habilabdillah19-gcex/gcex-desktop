"""Halaman tambahan ruang kerja Borang (0.44): Riwayat, Template, Pengaturan, Bantuan.

Dibuka dari bilah navigasi Borang | Riwayat | Template | Pengaturan | Bantuan di bilah atas (hanya di mode Borang).
Data lewat rute /core/forms/history_all, /templates, /template/save, /template/delete (backend core_forms)."""
from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QScrollArea, QSplitter, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from . import api, theme
from .card import _esc, btn
from .dialogs import ask, say
from .util import SET, open_path, res_dir, run_bg

COL_TYPE_LABEL = {"text": "Teks", "num": "Angka", "date": "Tanggal", "time": "Jam"}


def _title(text: str, sub: str = "") -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 4)
    v.setSpacing(2)
    a = QLabel(text)
    a.setObjectName("fmPageTitle")
    v.addWidget(a)
    if sub:
        b = QLabel(sub)
        b.setObjectName("note")
        b.setWordWrap(True)
        v.addWidget(b)
    return w


def _card() -> tuple[QFrame, QVBoxLayout]:
    f = QFrame()
    f.setObjectName("fmCard")
    v = QVBoxLayout(f)
    v.setContentsMargins(12, 10, 12, 12)
    v.setSpacing(6)
    return f, v


# ---------------------------------------------------------------- Riwayat
class HistoryPage(QWidget):
    """Semua perubahan di proyek (tambah / hapus borang, baca AI, edit sel, verifikasi, ekspor, template), terbaru dulu."""
    COLS = [("at", "Waktu"), ("by", "Pengguna"), ("doc_name", "Borang"), ("type_name", "Jenis"), ("what", "Perubahan"),
            ("old", "Nilai lama"), ("new", "Nilai baru"), ("src", "Sumber")]

    def __init__(self, pg) -> None:
        super().__init__()
        self.pg = pg
        self.data: list[dict] = []
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(8)
        v.addWidget(_title("Riwayat", "Jejak audit semua borang di proyek ini: siapa mengubah apa dan kapan. Klik ganda satu baris untuk "
                                      "membuka borangnya."))
        r = QHBoxLayout()
        self.q = QLineEdit()
        self.q.setPlaceholderText("Cari (nama borang, pengguna, nilai, perubahan)…")
        self.q.returnPressed.connect(self.refresh)
        r.addWidget(self.q, 2)
        self.cbType = QComboBox()
        r.addWidget(self.cbType)
        self.cThis = QCheckBox("Hanya borang yang dibuka")
        self.cThis.toggled.connect(lambda _on: self.refresh())
        r.addWidget(self.cThis)
        self.bRef = btn("Muat ulang", sm=True)
        self.bCsv = btn("⇩ CSV", "Simpan riwayat yang tampil ke CSV", sm=True)
        r.addWidget(self.bRef)
        r.addWidget(self.bCsv)
        v.addLayout(r)
        self.info = QLabel()
        self.info.setObjectName("note")
        v.addWidget(self.info)
        self.t = QTableWidget(0, len(self.COLS))
        self.t.setHorizontalHeaderLabels([lab for _k, lab in self.COLS])
        self.t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.t.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.t.setAlternatingRowColors(True)
        self.t.verticalHeader().hide()
        self.t.cellDoubleClicked.connect(self._open_doc)
        hh = self.t.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setStretchLastSection(True)
        v.addWidget(self.t, 1)
        self.cbType.currentIndexChanged.connect(lambda _i: self.refresh())
        self.bRef.clicked.connect(self.refresh)
        self.bCsv.clicked.connect(self.save_csv)

    def set_types(self, types: dict) -> None:
        cur = self.cbType.currentData()
        self.cbType.blockSignals(True)
        self.cbType.clear()
        self.cbType.addItem("Semua jenis", "")
        for k, t in types.items():
            self.cbType.addItem(t["name"], k)
        self.cbType.setCurrentIndex(max(0, self.cbType.findData(cur)))
        self.cbType.blockSignals(False)

    def refresh(self) -> None:
        if not self.pg.folder:
            return
        try:
            j = api.call("/core/forms/history_all", {"folder": self.pg.folder, "q": self.q.text().strip(), "type": self.cbType.currentData() or ""})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        rows = j["history"]
        if self.cThis.isChecked() and self.pg.cur:
            rows = [r for r in rows if r.get("doc_id") == self.pg.cur["doc"]["id"]]
        self.data = rows
        self.t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for jx, (k, _l) in enumerate(self.COLS):
                v = str(r.get(k) if r.get(k) is not None else "")
                it = QTableWidgetItem(v if len(v) < 160 else v[:157] + "…")
                it.setToolTip(v[:1500])
                self.t.setItem(i, jx, it)
        self.t.resizeColumnsToContents()
        for jx in (5, 6):
            self.t.setColumnWidth(jx, min(260, self.t.columnWidth(jx)))
        self.info.setText(f"{len(rows)} entri" + (" (dibatasi 2000 terbaru)" if len(rows) >= 2000 else ""))

    def _open_doc(self, row: int, _col: int) -> None:
        if not 0 <= row < len(self.data):
            return
        did = self.data[row].get("doc_id")
        if did is None or not self.pg.select_doc(did):
            say(self, "Borang ini sudah dihapus dari proyek.")
            return
        self.pg.show_page(0)

    def save_csv(self) -> None:
        if not self.data:
            return
        p, _ = QFileDialog.getSaveFileName(self, "Simpan riwayat", str(Path(SET.get("lastSaveDir", str(Path.home()))) / "Riwayat_Borang.csv"),
                                           "CSV (*.csv)")
        if not p:
            return
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([lab for _k, lab in self.COLS])
            for r in self.data:
                w.writerow([r.get(k) if r.get(k) is not None else "" for k, _l in self.COLS])
        self.pg.toast("Riwayat disimpan ke " + Path(p).name, 3000)


# ---------------------------------------------------------------- Template
class ColTable(QWidget):
    """Tabel kolom template: Kunci, Label, Tipe (+ tambah / hapus / naik / turun)."""

    def __init__(self, title: str) -> None:
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        h = QHBoxLayout()
        lab = QLabel(f"<b>{title}</b>")
        h.addWidget(lab, 1)
        self.bAdd = btn("+", "Tambah kolom", sm=True)
        self.bDel = btn("−", "Hapus kolom terpilih", sm=True)
        self.bUp = btn("↑", "Naikkan", sm=True)
        self.bDn = btn("↓", "Turunkan", sm=True)
        for b_ in (self.bAdd, self.bDel, self.bUp, self.bDn):
            h.addWidget(b_)
        v.addLayout(h)
        self.t = QTableWidget(0, 3)
        self.t.setHorizontalHeaderLabels(["Kunci", "Label (tertulis di borang)", "Tipe"])
        self.t.verticalHeader().setDefaultSectionSize(26)
        self.t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        v.addWidget(self.t, 1)
        self.bAdd.clicked.connect(lambda: self.add(["", "", "text"]))
        self.bDel.clicked.connect(lambda: self.t.removeRow(self.t.currentRow()) if self.t.currentRow() >= 0 else None)
        self.bUp.clicked.connect(lambda: self._move(-1))
        self.bDn.clicked.connect(lambda: self._move(1))

    def add(self, c: list, at: int | None = None) -> None:
        i = self.t.rowCount() if at is None else at
        self.t.insertRow(i)
        self.t.setItem(i, 0, QTableWidgetItem(str(c[0])))
        self.t.setItem(i, 1, QTableWidgetItem(str(c[1])))
        cb = QComboBox()
        for k, lab in COL_TYPE_LABEL.items():
            cb.addItem(lab, k)
        cb.setCurrentIndex(max(0, cb.findData(c[2] if len(c) > 2 else "text")))
        self.t.setCellWidget(i, 2, cb)

    def _move(self, d: int) -> None:
        i = self.t.currentRow()
        j = i + d
        if i < 0 or not 0 <= j < self.t.rowCount():
            return
        a, b = self.get_row(i), self.get_row(j)
        self.set_row(i, b)
        self.set_row(j, a)
        self.t.setCurrentCell(j, 1)

    def get_row(self, i: int) -> list:
        return [self.t.item(i, 0).text().strip() if self.t.item(i, 0) else "", self.t.item(i, 1).text().strip() if self.t.item(i, 1) else "",
                self.t.cellWidget(i, 2).currentData() if self.t.cellWidget(i, 2) else "text"]

    def set_row(self, i: int, c: list) -> None:
        self.t.item(i, 0).setText(c[0])
        self.t.item(i, 1).setText(c[1])
        self.t.cellWidget(i, 2).setCurrentIndex(max(0, self.t.cellWidget(i, 2).findData(c[2])))

    def load(self, cols: list) -> None:
        self.t.setRowCount(0)
        for c in cols:
            self.add(list(c))

    def value(self) -> list[list]:
        out = []
        for i in range(self.t.rowCount()):
            k, lab, ty = self.get_row(i)
            if k or lab:
                out.append([k or lab, lab or k, ty])
        return out

    def set_ro(self, ro: bool) -> None:
        self.t.setEditTriggers(QAbstractItemView.NoEditTriggers if ro else QAbstractItemView.AllEditTriggers)
        for b_ in (self.bAdd, self.bDel, self.bUp, self.bDn):
            b_.setEnabled(not ro)
        for i in range(self.t.rowCount()):
            if self.t.cellWidget(i, 2):
                self.t.cellWidget(i, 2).setEnabled(not ro)


class TemplatePage(QWidget):
    """Jenis borang bawaan (lihat / duplikat) dan template kustom (buat, ubah, hapus): header, kolom tabel, petunjuk AI,
    nama tabel database, kolom unik / wajib / diteruskan ke bawah. Template disimpan di folder proyek."""

    def __init__(self, pg) -> None:
        super().__init__()
        self.pg = pg
        self.tpls: list[dict] = []
        self.key = ""            # template yang sedang diedit ('' = baru)
        self.ro = False
        o = QVBoxLayout(self)
        o.setContentsMargins(16, 12, 16, 12)
        o.addWidget(_title("Template borang", "Jenis borang bawaan bisa dilihat dan diduplikat; template kustom bisa dibuat untuk borang "
                                              "lain di site Anda. AI membaca borang menurut kolom & petunjuk di sini. Disimpan di folder proyek "
                                              "(_GCEx_Core/borang/template.json), jadi ikut bila folder proyek disalin."))
        sp = QSplitter(Qt.Horizontal)
        o.addWidget(sp, 1)
        lw = QWidget()
        lv = QVBoxLayout(lw)
        lv.setContentsMargins(0, 0, 6, 0)
        self.lst = QListWidget()
        self.lst.setObjectName("fmTypes")
        self.lst.currentRowChanged.connect(self._pick)
        lv.addWidget(self.lst, 1)
        r = QHBoxLayout()
        self.bNew = btn("＋ Template baru", pri=True, sm=True)
        self.bDup = btn("Duplikat", "Salin jenis / template terpilih menjadi template kustom baru", sm=True)
        r.addWidget(self.bNew)
        r.addWidget(self.bDup)
        lv.addLayout(r)
        sp.addWidget(lw)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        ew = QWidget()
        ev = QVBoxLayout(ew)
        ev.setContentsMargins(6, 0, 0, 0)
        ev.setSpacing(8)
        self.note = QLabel()
        self.note.setObjectName("box")
        self.note.setWordWrap(True)
        ev.addWidget(self.note)
        g = QGridLayout()
        g.addWidget(QLabel("Nama borang"), 0, 0)
        self.eName = QLineEdit()
        g.addWidget(self.eName, 0, 1, 1, 3)
        g.addWidget(QLabel("Tabel database / sheet"), 1, 0)
        self.eDb = QLineEdit()
        self.eDb.setPlaceholderText("mis. TRENCH_LOG (otomatis dari nama bila kosong)")
        g.addWidget(self.eDb, 1, 1)
        self.eSheet = QLineEdit()
        self.eSheet.setPlaceholderText("nama sheet Excel (opsional)")
        g.addWidget(self.eSheet, 1, 2, 1, 2)
        g.addWidget(QLabel("Kolom unik"), 2, 0)
        self.cbUniq = QComboBox()
        self.cbUniq.setToolTip("Nilai kolom ini tidak boleh kembar di semua borang jenis ini (mis. Sample ID)")
        g.addWidget(self.cbUniq, 2, 1)
        g.addWidget(QLabel("Diteruskan ke bawah"), 2, 2)
        self.eCarry = QLineEdit()
        self.eCarry.setPlaceholderText("kunci kolom, pisahkan koma (mis. hole_id)")
        self.eCarry.setToolTip("Kolom yang hanya ditulis di baris pertama (mis. Hole ID): sel kosong di bawahnya diisi program dari baris atas")
        g.addWidget(self.eCarry, 2, 3)
        g.addWidget(QLabel("Kolom wajib"), 3, 0)
        self.eReq = QLineEdit()
        self.eReq.setPlaceholderText("kunci kolom, pisahkan koma")
        g.addWidget(self.eReq, 3, 1, 1, 3)
        ev.addLayout(g)
        self.hdr = ColTable("Header (isian di atas tabel borang)")
        self.hdr.setMinimumHeight(170)
        ev.addWidget(self.hdr)
        self.col = ColTable("Kolom tabel (urut dari kiri ke kanan seperti di borang)")
        self.col.setMinimumHeight(230)
        ev.addWidget(self.col)
        ev.addWidget(QLabel("<b>Petunjuk untuk AI</b> — jelaskan judul borang, letak header, isi tiap kolom, singkatan khusus"))
        self.eHint = QPlainTextEdit()
        self.eHint.setMinimumHeight(110)
        ev.addWidget(self.eHint)
        ev.addWidget(QLabel("<b>Kamus site</b> — dipelajari otomatis dari baris yang sudah DIVERIFIKASI (muncul ≥ 2 kali)"))
        self.vocab = QLabel()
        self.vocab.setObjectName("box")
        self.vocab.setWordWrap(True)
        self.vocab.setTextFormat(Qt.RichText)
        self.vocab.setToolTip("Nilai ini disisipkan ke perintah AI, dan bacaan yang mirip (mis. 5BG → SBG, ROMS38 → ROM 338) dirapikan "
                              "ke ejaan ini lalu disorot kuning. Makin banyak baris diverifikasi, makin tepat. Disimpan hanya di proyek ini.")
        ev.addWidget(self.vocab)
        kk = QLabel("Kunci kolom khusus: <b>from_m</b> & <b>to_m</b> mengaktifkan cek interval (bolong / tumpang-tindih) per "
                    "<b>hole_id</b> / <b>channel_id</b> / <b>trench_id</b> dan kolom turunan Panjang. Kunci <b>shift</b> di header menambah Kode "
                    "Shift (DS / NS).")
        kk.setObjectName("note")
        kk.setWordWrap(True)
        kk.setTextFormat(Qt.RichText)
        ev.addWidget(kk)
        r2 = QHBoxLayout()
        self.bSave = btn("Simpan template", pri=True)
        self.bDel = btn("Hapus template")
        r2.addWidget(self.bSave)
        r2.addWidget(self.bDel)
        r2.addStretch(1)
        ev.addLayout(r2)
        ev.addStretch(1)
        sc.setWidget(ew)
        sp.addWidget(sc)
        sp.setSizes([280, 900])
        self.bNew.clicked.connect(self.new)
        self.bDup.clicked.connect(self.dup)
        self.bSave.clicked.connect(self.save)
        self.bDel.clicked.connect(self.delete)
        self.col.t.itemChanged.connect(lambda _it: self._uniq_opts())

    def refresh(self, select: str = "") -> None:
        if not self.pg.folder:
            return
        try:
            j = api.call("/core/forms/templates", {"folder": self.pg.folder})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.tpls = j["templates"]
        cur = select or self.key
        self.lst.blockSignals(True)
        self.lst.clear()
        for t in self.tpls:
            tag = "bawaan" if t["builtin"] else "kustom"
            it = QListWidgetItem(f"{t['name']}\n   {tag} · {len(t['rows'])} kolom · {t['docs']} borang")
            it.setData(Qt.UserRole, t["key"])
            self.lst.addItem(it)
        self.lst.blockSignals(False)
        i = next((i for i, t in enumerate(self.tpls) if t["key"] == cur), 0)
        self.lst.setCurrentRow(i)
        self._pick(i)

    def _pick(self, i: int) -> None:
        if not 0 <= i < len(self.tpls):
            return
        t = self.tpls[i]
        self.key = t["key"]
        self._load(t, ro=t["builtin"])
        self._vocab(t)

    def _vocab(self, t: dict) -> None:
        try:
            v = api.call("/core/forms/vocab", {"folder": self.pg.folder, "type": t["key"]})["vocab"]
        except api.ApiError:
            v = {}
        lab = {k: lab for k, lab, _ty in list(t["header"]) + list(t["rows"])}
        self.vocab.setText("<br>".join(f"<b>{_esc(lab.get(k, k))}</b>: {_esc(', '.join(xs))}" for k, xs in v.items())
                           or "Belum ada — verifikasi (✓) baris borang jenis ini; nilai yang muncul ≥ 2 kali otomatis menjadi kamus.")

    def _load(self, t: dict, ro: bool) -> None:
        self.ro = ro
        self.eName.setText(t["name"])
        self.hdr.load(t["header"])
        self.col.load(t["rows"])
        self.eHint.setPlainText(t.get("hint") or "")
        g = t.get("gen") or {}
        self.eDb.setText(g.get("db") or "")
        self.eSheet.setText(g.get("sheet") or "")
        self.eCarry.setText(", ".join(g.get("carry") or []))
        self.eReq.setText(", ".join(g.get("req") or []))
        self._uniq_opts(g.get("unique") or "")
        for w_ in (self.eName, self.eDb, self.eSheet, self.eCarry, self.eReq):
            w_.setReadOnly(ro)
        self.eHint.setReadOnly(ro)
        self.cbUniq.setEnabled(not ro)
        self.hdr.set_ro(ro)
        self.col.set_ro(ro)
        self.bSave.setEnabled(not ro)
        self.bDel.setEnabled(not ro and bool(self.key))
        if ro:
            self.note.setText("<b>Jenis borang bawaan</b> — tidak bisa diubah karena memakai aturan khusus (mis. kelas material, kategori jam). "
                              "Klik <b>Duplikat</b> untuk membuat template kustom berdasarkan jenis ini." if t.get("tables") or t["key"] in ("ore", "rom", "ddr", "rc")
                              else "<b>Jenis borang bawaan</b> — klik <b>Duplikat</b> untuk membuat versi kustom (mis. kolom tambahan khas site Anda).")
        else:
            self.note.setText("<b>Template kustom</b>" + (f" · dipakai {t.get('docs', 0)} borang" if t.get("docs") else " · belum dipakai")
                              if self.key else "<b>Template baru</b> — isi nama, kolom, lalu Simpan. Template muncul di daftar jenis borang.")
        self.note.setTextFormat(Qt.RichText)

    def _uniq_opts(self, cur: str | None = None) -> None:
        cur = self.cbUniq.currentData() if cur is None else cur
        self.cbUniq.blockSignals(True)
        self.cbUniq.clear()
        self.cbUniq.addItem("(tidak ada)", "")
        for k, lab, _t in self.col.value():
            self.cbUniq.addItem(f"{lab} ({k})", k)
        self.cbUniq.setCurrentIndex(max(0, self.cbUniq.findData(cur)))
        self.cbUniq.blockSignals(False)

    def new(self) -> None:
        self.key = ""
        self.lst.clearSelection()
        self._load({"name": "", "header": [["tanggal", "Tanggal", "date"], ["geologist", "Geologist", "text"], ["lokasi", "Lokasi", "text"]],
                    "rows": [["no", "No", "text"], ["keterangan", "Keterangan", "text"]], "hint": "", "gen": {}}, ro=False)
        self.eName.setFocus()

    def dup(self) -> None:
        i = self.lst.currentRow()
        if not 0 <= i < len(self.tpls):
            return
        t = dict(self.tpls[i])
        t["name"] = t["name"] + " (kustom)"
        self.key = ""
        self._load(t, ro=False)
        self.note.setText(f"<b>Template baru</b> dari <i>{_esc(self.tpls[i]['name'])}</i> — ubah lalu Simpan.")

    def spec(self) -> dict:
        def keys(e: QLineEdit) -> list[str]:
            return [x.strip() for x in e.text().replace(";", ",").split(",") if x.strip()]
        return {"name": self.eName.text().strip(), "header": self.hdr.value(), "rows": self.col.value(), "hint": self.eHint.toPlainText().strip(),
                "gen": {"db": self.eDb.text().strip(), "sheet": self.eSheet.text().strip(), "unique": self.cbUniq.currentData() or "",
                        "carry": keys(self.eCarry), "req": keys(self.eReq)}}

    def save(self) -> None:
        if self.ro or not self.pg.folder:
            return
        try:
            j = api.call("/core/forms/template/save", {"folder": self.pg.folder, "key": self.key, "spec": self.spec(), "by": self.pg.by()})
        except api.ApiError as e:
            say(self, "Template tidak disimpan:\n" + str(e), warn=True)
            return
        self.key = j["key"]
        self.refresh(self.key)
        self.pg.reload_types()
        self.pg.toast("Template disimpan — muncul di daftar jenis borang", 3500)

    def delete(self) -> None:
        if self.ro or not self.key or not ask(self, f"Hapus template \"{self.eName.text()}\"?"):
            return
        try:
            api.call("/core/forms/template/delete", {"folder": self.pg.folder, "key": self.key, "by": self.pg.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.key = ""
        self.refresh()
        self.pg.reload_types()


# ---------------------------------------------------------------- Pengaturan
class SettingsPage(QWidget):
    def __init__(self, pg) -> None:
        super().__init__()
        self.pg = pg
        o = QVBoxLayout(self)
        o.setContentsMargins(16, 12, 16, 12)
        o.setSpacing(10)
        o.addWidget(_title("Pengaturan", "Pengaturan ruang kerja Borang di komputer ini."))
        g = QGridLayout()
        g.setSpacing(10)
        c1, v1 = _card()
        v1.addWidget(QLabel("<b>AI lokal (Ollama)</b>"))
        self.aiInfo = QLabel()
        self.aiInfo.setWordWrap(True)
        self.aiInfo.setTextFormat(Qt.RichText)
        v1.addWidget(self.aiInfo)
        b = btn("Atur AI lokal…", "Alamat Ollama, model vision, catatan tambahan untuk AI", pri=True, sm=True)
        b.clicked.connect(lambda: (self.pg.win.open_ai(), self.refresh()))
        v1.addWidget(b, 0, Qt.AlignLeft)
        v1.addWidget(QLabel("Kecepatan baca bawaan"))
        self.cbSpeed = QComboBox()
        for i in range(self.pg.cbSpeed.count()):
            self.cbSpeed.addItem(self.pg.cbSpeed.itemText(i), self.pg.cbSpeed.itemData(i))
        self.cbSpeed.currentIndexChanged.connect(lambda i: self.pg.cbSpeed.setCurrentIndex(i))
        v1.addWidget(self.cbSpeed)
        n = QLabel("Model yang disarankan: <b>qwen3-vl:2b-instruct</b> (laptop tanpa GPU NVIDIA) atau <b>qwen3-vl:4b-instruct</b> (GPU NVIDIA). "
                   "Versi tanpa <i>-instruct</i> (thinking) lambat dan sering gagal di Borang.")
        n.setObjectName("note")
        n.setWordWrap(True)
        n.setTextFormat(Qt.RichText)
        v1.addWidget(n)
        v1.addStretch(1)
        g.addWidget(c1, 0, 0)
        c2, v2 = _card()
        v2.addWidget(QLabel("<b>Borang baru</b>"))
        v2.addWidget(QLabel("Jenis bawaan untuk file baru"))
        self.cbType = QComboBox()
        self.cbType.currentIndexChanged.connect(self._type)
        v2.addWidget(self.cbType)
        v2.addWidget(QLabel("Urutan daftar file"))
        self.cbSort = QComboBox()
        for i in range(self.pg.cbSort.count()):
            self.cbSort.addItem(self.pg.cbSort.itemText(i), self.pg.cbSort.itemData(i))
        self.cbSort.currentIndexChanged.connect(lambda i: self.pg.cbSort.setCurrentIndex(i))
        v2.addWidget(self.cbSort)
        v2.addWidget(QLabel("<b>Meringankan kerja AI</b>"))
        self.cTrim = QCheckBox("Buang bagian bawah tabel yang kosong sebelum dibaca AI")
        self.cTrim.setToolTip("Baris borang yang belum diisi (di bawah tulisan terakhir) tidak dikirim ke AI: lebih cepat & tulisan tampak lebih besar."
                              "\nTinta dikenali dari warna pena (biru / ungu). Tanda tangan di bawah tabel tidak menghalangi.")
        self.cTrim.toggled.connect(lambda on: SET.set("fmTrim", on))
        v2.addWidget(self.cTrim)
        self.cHdr = QCheckBox("Header ikut halaman lain dari PDF yang sama (AI baca tabel saja)")
        self.cHdr.setToolTip("PDF berhalaman banyak biasanya satu shift: tanggal, shift, crew, lokasi sama. Header disalin dari halaman yang "
                             "sudah terisi dan ditandai kuning; AI hanya membaca tabel -> lebih cepat.")
        self.cHdr.toggled.connect(lambda on: SET.set("fmHdrPrev", on))
        v2.addWidget(self.cHdr)
        n2 = QLabel("<b>Auto Detect</b>: jenis ditebak dari nama file (mis. DDR_…, Rom…, Channel…, RC_Log…, Progress…, Mapping…, nama "
                    "template kustom). Bila nama file tidak memberi petunjuk, AI menentukan jenisnya sebelum membaca (±10–30 detik tambahan).")
        n2.setObjectName("note")
        n2.setWordWrap(True)
        n2.setTextFormat(Qt.RichText)
        v2.addWidget(n2)
        v2.addStretch(1)
        g.addWidget(c2, 0, 1)
        c3, v3 = _card()
        v3.addWidget(QLabel("<b>Pengguna & tampilan</b>"))
        self.user = QLabel()
        v3.addWidget(self.user)
        r = QHBoxLayout()
        bu = btn("Ganti nama pengguna…", sm=True)
        bu.clicked.connect(lambda: (self.pg.win.user(True), self.refresh()))
        bd = btn("Tema gelap / terang", sm=True)
        bd.clicked.connect(self.pg.win.toggle_dark)
        r.addWidget(bu)
        r.addWidget(bd)
        r.addStretch(1)
        v3.addLayout(r)
        v3.addStretch(1)
        g.addWidget(c3, 1, 0)
        c4, v4 = _card()
        v4.addWidget(QLabel("<b>Data proyek</b>"))
        self.path = QLabel()
        self.path.setWordWrap(True)
        self.path.setObjectName("note")
        v4.addWidget(self.path)
        bo = btn("Buka folder data borang", sm=True)
        bo.clicked.connect(lambda: open_path(self.pg.rootp) if self.pg.rootp else None)
        v4.addWidget(bo, 0, Qt.AlignLeft)
        v4.addStretch(1)
        g.addWidget(c4, 1, 1)
        o.addLayout(g)
        o.addStretch(1)

    def _type(self, i: int) -> None:
        k = self.cbType.itemData(i)
        if k:
            self.pg.cbNew.setCurrentIndex(max(0, self.pg.cbNew.findData(k)))

    def refresh(self) -> None:
        ai = self.pg.win.ai
        run = bool(ai.info and ai.info.get("running"))
        self.aiInfo.setText(("● <b>Aktif</b>" if run else "○ <b>Tidak aktif</b>") + f" · model: <b>{_esc(ai.model() or '-')}</b>"
                            + f"<br>alamat: {_esc(ai.host.text().strip() or 'http://127.0.0.1:11434')}")
        self.cbSpeed.blockSignals(True)
        self.cbSpeed.setCurrentIndex(self.pg.cbSpeed.currentIndex())
        self.cbSpeed.blockSignals(False)
        self.cbSort.blockSignals(True)
        self.cbSort.setCurrentIndex(self.pg.cbSort.currentIndex())
        self.cbSort.blockSignals(False)
        self.cbType.blockSignals(True)
        self.cbType.clear()
        for i in range(self.pg.cbNew.count()):
            self.cbType.addItem(self.pg.cbNew.itemText(i), self.pg.cbNew.itemData(i))
        self.cbType.setCurrentIndex(self.pg.cbNew.currentIndex())
        self.cbType.blockSignals(False)
        self.cTrim.setChecked(bool(SET.get("fmTrim", True)))
        self.cHdr.setChecked(bool(SET.get("fmHdrPrev", True)))
        self.user.setText(f"Pengguna: <b>{_esc(self.pg.by() or '-')}</b> (dicatat di Riwayat & verifikasi)")
        self.user.setTextFormat(Qt.RichText)
        self.path.setText(f"Folder proyek: {self.pg.folder or '-'}<br>Data borang: {self.pg.rootp or '-'}")
        self.path.setTextFormat(Qt.RichText)


# ---------------------------------------------------------------- Bantuan
class HelpPage(QWidget):
    def __init__(self, pg) -> None:
        super().__init__()
        self.pg = pg
        o = QVBoxLayout(self)
        o.setContentsMargins(16, 12, 16, 12)
        o.setSpacing(10)
        o.addWidget(_title("Bantuan", "Cara cepat memakai ruang kerja Borang, dan dokumen lengkap."))
        g = QGridLayout()
        g.setSpacing(10)
        c1, v1 = _card()
        v1.addWidget(QLabel("<b>Langkah cepat</b>"))
        st = QLabel("1. Pilih jenis borang di kiri (atau <b>Auto Detect</b>).<br>"
                    "2. <b>Tambah File</b> / <b>Tambah Folder</b>, atau seret foto / PDF ke halaman Borang.<br>"
                    "3. Putar scan bila perlu (↻), pilih kecepatan, lalu <b>✦ Baca dengan AI</b> — atau <b>Baca Semua dengan AI</b> di bawah.<br>"
                    "4. Cocokkan tabel dengan scan: sel <span style='background:#fff3bf'>&nbsp;kuning&nbsp;</span> = AI ragu / diisi program, "
                    "<span style='background:#ffe3e3'>&nbsp;merah&nbsp;</span> = galat (tab <b>Validasi</b>).<br>"
                    "5. Centang ✓ tiap baris (Ctrl+Enter = verifikasi & lanjut).<br>"
                    "6. Tab <b>Ekspor</b>: Excel, CSV, SQLite, MS Access (bawaan hanya baris terverifikasi).")
        st.setWordWrap(True)
        st.setTextFormat(Qt.RichText)
        v1.addWidget(st)
        v1.addStretch(1)
        g.addWidget(c1, 0, 0, 2, 1)
        c2, v2 = _card()
        v2.addWidget(QLabel("<b>Dokumen</b>"))
        for t_, f in (("Tutorial penggunaan DB-Ex (PDF)", "DB-Ex_Tutorial_Penggunaan.pdf"), ("Panduan teknis DB-Ex (PDF)", "DB-Ex_Panduan_Teknis.pdf"),
                      ("Panduan DB-Ex (HTML)", "PANDUAN_CORE.html")):
            b = btn(t_, sm=True)
            p = res_dir("docs") / f
            b.setEnabled(p.exists())
            b.setToolTip(str(p) if p.exists() else "Dokumen tidak ada di instalasi ini — unduh dari Release (…_1_Dokumen.zip)")
            b.clicked.connect(lambda _=False, p=p: open_path(p))
            v2.addWidget(b, 0, Qt.AlignLeft)
        v2.addStretch(1)
        g.addWidget(c2, 0, 1)
        c3, v3 = _card()
        v3.addWidget(QLabel("<b>Pintasan</b>"))
        k = QLabel("Ctrl+Enter — verifikasi baris & lanjut<br>Delete (di daftar file) — hapus borang<br>Scroll di scan — zoom · tarik — geser"
                   "<br>Klik ganda scan — pas layar<br>Klik kanan file — baca AI, ubah jenis, deteksi jenis, hapus")
        k.setTextFormat(Qt.RichText)
        k.setWordWrap(True)
        v3.addWidget(k)
        v3.addStretch(1)
        g.addWidget(c3, 1, 1)
        o.addLayout(g)
        o.addStretch(1)
        f = QLabel(f"Data contoh di dokumen fiktif. Aplikasi 100% offline — tidak ada data yang dikirim ke internet. "
                   f"Tema: {theme.SANS}.")
        f.setObjectName("note")
        o.addWidget(f)
