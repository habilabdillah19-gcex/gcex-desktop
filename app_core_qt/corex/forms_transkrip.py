"""Tab Transkrip ruang kerja Borang (0.45, usul pemilik): AI hanya MENYALIN tulisan di kertas menjadi teks; pengguna merapikan
teks, memilih pemisah sel, menentukan tujuan tiap kolom (dropdown di baris pertama kisi) dan isian kop, lalu Terapkan ->
baris masuk tabel Data seperti hasil baca langsung (validasi, ringkasan, pivot, ekspor sama). Pemetaan tersimpan per jenis
borang. Rute /core/forms/transkrip, /transkrip/pratinjau, /transkrip/terapkan, /transkrip/simpan (backend core_transkrip)."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit, QSplitter, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from . import api
from .card import btn
from .dialogs import ask, say
from .util import SET, run_bg

SEP_ITEMS = (("Otomatis", "auto"), ("Garis tegak  |", "|"), ("Tab", "tab"), ("Koma  ,", ","), ("Titik koma  ;", ";"))
TITLE_BG, MAP_BG, SKIP_BG = "#e9ecef", "#eef5ff", "#f1f3f5"


class TranscriptTab(QWidget):
    """Panel kanan tab 'Transkrip'."""

    def __init__(self, page) -> None:
        super().__init__()
        self.page = page
        self.pv: dict | None = None      # pratinjau terakhir dari backend (kisi + usulan pemetaan + pilihan)
        self.did: int | None = None
        self.skip: set[int] = set()
        self._filling = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(600)
        self.timer.timeout.connect(self.preview)
        self._build()

    def _build(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(6)
        top = QHBoxLayout()
        self.bAI = btn("✦ Salin teks dengan AI", "AI hanya menyalin tulisan di kertas menjadi teks (tanpa menebak kolom). Baris tabel Data "
                       "TIDAK berubah sampai Anda menekan Terapkan.", pri=True, sm=True)
        self.bAI.clicked.connect(self.run_ai)
        top.addWidget(self.bAI)
        self.cbMode = QComboBox()
        for t, k in (("Ganti teks", "ganti"), ("+ kolom di kanan", "kanan"), ("+ di bawah", "bawah")):
            self.cbMode.addItem(t, k)
        self.cbMode.setToolTip("Hasil salinan AI:\n• Ganti teks — teks lama diganti.\n• Tambah sebagai kolom di kanan — untuk scan KOLOM satu per "
                               "satu dari kiri ke kanan (✂ Potong kolom Meterage → salin, potong Hole ID → salin, …): baris ke-1 salinan baru "
                               "ditempel di kanan baris ke-1 teks, dst.\n• Tambah di bawah — potongan / lembar berikutnya dari tabel yang sama.")
        self.cbMode.setCurrentIndex(max(0, self.cbMode.findData(SET.get("qt_fm_tr_mode", "ganti"))))
        self.cbMode.currentIndexChanged.connect(lambda _i: SET.set("qt_fm_tr_mode", self.cbMode.currentData()))
        top.addWidget(self.cbMode)
        top.addSpacing(10)
        top.addWidget(QLabel("Pemisah sel:"))
        self.cbSep = QComboBox()
        for t, k in SEP_ITEMS:
            self.cbSep.addItem(t, k)
        self.cbSep.setToolTip("Tanda yang memisahkan sel dalam satu baris teks. Otomatis = yang paling sering muncul.")
        self.cbSep.currentIndexChanged.connect(lambda _i: self.preview())
        top.addWidget(self.cbSep)
        top.addStretch(1)
        v.addLayout(top)
        self.info = QLabel()
        self.info.setObjectName("note")
        self.info.setWordWrap(True)
        v.addWidget(self.info)
        sp = QSplitter(Qt.Vertical)
        sp.setHandleWidth(5)
        # ---- teks
        tw = QWidget()
        tv = QVBoxLayout(tw)
        tv.setContentsMargins(0, 0, 0, 0)
        tv.setSpacing(3)
        lt = QLabel("1 · TEKS SALINAN  —  rapikan di sini: sambung baris lanjutan, hapus baris sampah, satu baris tabel = satu baris teks")
        lt.setObjectName("fmSect")
        lt.setWordWrap(True)
        tv.addWidget(lt)
        self.txt = QPlainTextEdit()
        self.txt.setObjectName("fmTranskrip")
        self.txt.setPlaceholderText("Klik ✦ Salin teks dengan AI, atau ketik / tempel teks di sini.\n"
                                    "Isian kop:  Label: nilai   (satu per baris)\n"
                                    "Baris tabel:  nilai | nilai | nilai   (pemisah bisa diganti di atas)")
        self.txt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.txt.textChanged.connect(self._text_changed)
        tv.addWidget(self.txt, 1)
        sp.addWidget(tw)
        # ---- kop
        hw = QWidget()
        hv = QVBoxLayout(hw)
        hv.setContentsMargins(0, 0, 0, 0)
        hv.setSpacing(3)
        lh = QLabel("2 · ISIAN KOP  —  tentukan isian header untuk tiap 'Label: nilai'")
        lh.setObjectName("fmSect")
        lh.setWordWrap(True)
        hv.addWidget(lh)
        self.hdr = QTableWidget(0, 3)
        self.hdr.setHorizontalHeaderLabels(["Label di teks", "Nilai", "Masuk ke isian header"])
        self.hdr.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.hdr.verticalHeader().setVisible(False)
        self.hdr.setEditTriggers(QTableWidget.NoEditTriggers)
        hv.addWidget(self.hdr, 1)
        sp.addWidget(hw)
        # ---- kisi
        gw = QWidget()
        gv = QVBoxLayout(gw)
        gv.setContentsMargins(0, 0, 0, 0)
        gv.setSpacing(3)
        lg = QLabel("3 · KISI TABEL  —  baris pertama: pilih tujuan tiap kolom (— abaikan — = tidak dipakai). Klik nomor baris untuk melewati baris itu.")
        lg.setObjectName("fmSect")
        lg.setWordWrap(True)
        gv.addWidget(lg)
        self.maprow = QTableWidget(1, 0)  # baris dropdown tujuan kolom: tabel 1 baris yang MENEMPEL di atas kisi (tidak ikut tergulir)
        self.maprow.setObjectName("fmMapRow")
        self.maprow.setVerticalHeaderLabels(["→ isian"])
        self.maprow.horizontalHeader().setVisible(False)
        self.maprow.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.maprow.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.maprow.setFixedHeight(34)
        self.maprow.setEditTriggers(QTableWidget.NoEditTriggers)
        gv.addWidget(self.maprow)
        self.grid = QTableWidget(0, 0)
        self.grid.setEditTriggers(QTableWidget.NoEditTriggers)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.verticalHeader().sectionClicked.connect(self._toggle_skip)
        self.grid.horizontalScrollBar().valueChanged.connect(self.maprow.horizontalScrollBar().setValue)
        self.grid.horizontalHeader().sectionResized.connect(lambda i, _o, w: self.maprow.setColumnWidth(i, w))
        self.grid.verticalHeader().setFixedWidth(52)
        self.maprow.verticalHeader().setFixedWidth(52)
        gv.addWidget(self.grid, 1)
        bot = QHBoxLayout()
        bot.addStretch(1)
        self.bApply = btn("Terapkan ke tabel ▶", "Susun baris dari kisi sesuai pemetaan kolom, lalu isi tabel Data (baris lama diganti; "
                          "isian header yang Anda edit tetap). Pemetaan disimpan untuk borang jenis ini.", pri=True)
        self.bApply.clicked.connect(self.apply)
        self.bApply2 = self.bApply  # nama lama (satu tombol, di bawah kisi — selalu terlihat, tidak memaksa lebar jendela)
        bot.addWidget(self.bApply)
        gv.addLayout(bot)
        sp.addWidget(gw)
        sp.setSizes(SET.get("qt_fm_tr_split", [260, 120, 320]))
        sp.splitterMoved.connect(lambda *_: SET.set("qt_fm_tr_split", sp.sizes()))
        v.addWidget(sp, 1)
        self.set_doc(None)

    # ---------------------------------------------------------------- data
    def set_doc(self, d: dict | None) -> None:
        """Dipanggil FormsPage saat borang lain dibuka: tampilkan teks tersimpan borang itu."""
        did = d["id"] if d else None
        if did == self.did and d is not None:
            return
        self.did = did
        self.skip = set()
        self._filling = True
        self.txt.setPlainText((d or {}).get("teks") or "")
        self._filling = False
        self.bAI.setEnabled(d is not None)
        self.bApply.setEnabled(d is not None)
        self.bApply2.setEnabled(d is not None)
        self.txt.setEnabled(d is not None)
        if d is None:
            self.pv = None
            self.hdr.setRowCount(0)
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            self.maprow.setColumnCount(0)
            self.info.setText("Pilih borang di daftar kiri.")
            return
        if (d.get("teks") or "").strip():
            self.preview()
        else:
            self.pv = None
            self.hdr.setRowCount(0)
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            self.info.setText("Mode Transkrip: AI menyalin kertas menjadi teks, Anda yang menentukan kolom. Cocok untuk borang padat yang "
                              "salah kolom bila dibaca langsung. Klik ✦ Salin teks dengan AI.")

    def _text_changed(self) -> None:
        if not self._filling:
            self.timer.start()

    def _body(self) -> dict:
        return {"folder": self.page.folder, "id": self.did, "by": self.page.by()}

    def run_ai(self) -> None:
        if self.did is None or not self.page._ai_ready():
            return
        mode = self.cbMode.currentData() or "ganti"
        if mode == "ganti" and self.txt.toPlainText().strip() and not ask(
                self, "Salin ulang dengan AI? Teks yang ada (termasuk suntingan Anda) akan diganti.\n\n"
                      "Untuk scan kolom satu per satu, pilih 'Tambah sebagai kolom di kanan'."):
            return
        ai = self.page.win.ai
        body = {**self._body(), "host": ai.host.text().strip(), "model": ai.model(), "extra": ai.extra.toPlainText(),
                "max_px": int(self.page.cbSpeed.currentData() or 1600), "trim": bool(SET.get("fmTrim", True)),
                "mode": mode, "base": self.txt.toPlainText(), "sep": (self.pv or {}).get("sep") or self.cbSep.currentData() or "auto"}
        did = self.did
        self.bAI.setEnabled(False)
        self.bAI.setText("AI menyalin…")
        self.info.setText("AI sedang menyalin tulisan di kertas… Anda bisa membuka borang lain sementara menunggu.")

        def done():
            self.bAI.setText("✦ Salin teks dengan AI")
            self.bAI.setEnabled(self.did is not None)

        def ok(j):
            done()
            for d in self.page.docs:
                if d["id"] == did:
                    d["teks"] = j["teks"]
            if self.page.cur and self.page.cur["doc"]["id"] == did:
                self.page.cur["doc"]["teks"] = j["teks"]
            if self.did != did:
                self.page.toast("AI selesai menyalin teks borang lain — buka borangnya, tab Transkrip.", 5000)
                return
            self._filling = True
            self.txt.setPlainText(j["teks"])
            self._filling = False
            self.skip = set()
            self._show(j)
            p = j.get("perf") or {}
            extra = {"kanan": " · ditempel sebagai kolom baru di kanan — potong kolom berikutnya lalu salin lagi",
                     "bawah": " · ditambah di bawah"}.get(mode, "")
            self.page.toast(f"AI selesai menyalin · {len(j.get('rows') or [])} baris tabel · {j.get('ncol') or 0} kolom · "
                            f"{round(p.get('secs') or 0)} dtk{extra} — periksa teks, atur kolom, lalu Terapkan", 7000)

        def err(e):
            done()
            say(self, "AI gagal menyalin teks:\n" + e, warn=True)
        run_bg(api.call, "/core/forms/transkrip", body, ok=ok, err=err)

    def preview(self) -> None:
        if self.did is None:
            return
        txt = self.txt.toPlainText()
        did = self.did
        body = {**self._body(), "teks": txt, "sep": self.cbSep.currentData() or "auto"}

        def ok(j):
            if self.did == did:
                self._show(j)

        def err(e):
            if self.did == did:
                self.info.setText("Pratinjau gagal: " + e)
        run_bg(api.call, "/core/forms/transkrip/pratinjau", body, ok=ok, err=err)

    # ---------------------------------------------------------------- tampilan
    def _combo(self, opts: list[dict], key: str) -> QComboBox:
        cb = QComboBox()
        for o in opts:
            cb.addItem(o["label"], o["key"])
        cb.setCurrentIndex(max(0, cb.findData(key or "")))
        cb.currentIndexChanged.connect(lambda _i: self._mapped())
        return cb

    def _show(self, j: dict) -> None:
        self.pv = j
        g_rows, mp = j.get("rows") or [], j.get("map") or {}
        if mp.get("title_row", -1) >= 0 and not self.skip:
            self.skip.add(int(mp["title_row"]))
        # kop
        self.hdr.setRowCount(len(j.get("hdr") or []))
        for i, (lbl, val) in enumerate(j.get("hdr") or []):
            self.hdr.setItem(i, 0, QTableWidgetItem(lbl))
            self.hdr.setItem(i, 1, QTableWidgetItem(val))
            self.hdr.setCellWidget(i, 2, self._combo(j.get("hdr_options") or [], (mp.get("hdr") or [""] * (i + 1))[i] if i < len(mp.get("hdr") or []) else ""))
        # kisi: baris 0 = dropdown tujuan kolom
        n = int(j.get("ncol") or 0)
        self.grid.clear()
        self.grid.setColumnCount(n)
        self.grid.setRowCount(len(g_rows))
        self.grid.setHorizontalHeaderLabels([f"Kolom {i + 1}" for i in range(n)])
        self.grid.setVerticalHeaderLabels([str(i + 1) for i in range(len(g_rows))])
        self.maprow.setColumnCount(n)
        cols = list(mp.get("cols") or []) + [""] * n
        for c in range(n):
            self.maprow.setCellWidget(0, c, self._combo(j.get("options") or [], cols[c]))
        for r, row in enumerate(g_rows):
            for c in range(n):
                it = QTableWidgetItem(row[c] if c < len(row) else "")
                if r in self.skip:
                    it.setBackground(QColor(SKIP_BG))
                    it.setForeground(QColor("#868e96"))
                elif cols[c]:
                    it.setBackground(QColor(MAP_BG))
                if str(row[c] if c < len(row) else "").endswith("?"):
                    it.setBackground(QColor("#fff3bf"))
                self.grid.setItem(r, c, it)
        self.grid.resizeColumnsToContents()
        for c in range(n):
            w = min(420, max(self.grid.columnWidth(c) + 12, 150))
            self.grid.setColumnWidth(c, w)
            self.maprow.setColumnWidth(c, w)
        self._mapped()

    def _cols(self) -> list[str]:
        return [(self.maprow.cellWidget(0, c).currentData() or "") if self.maprow.cellWidget(0, c) else "" for c in range(self.maprow.columnCount())]

    def _hdr_keys(self) -> list[str]:
        return [(self.hdr.cellWidget(i, 2).currentData() or "") if self.hdr.cellWidget(i, 2) else "" for i in range(self.hdr.rowCount())]

    def _mapped(self) -> None:
        if not self.pv:
            return
        cols = self._cols()
        n_rows = max(0, self.grid.rowCount() - len(self.skip))
        used = [c for c in cols if c]
        dup = {c for c in used if used.count(c) > 1 and ":" not in c}
        hk = [k for k in self._hdr_keys() if k]
        s = (f"Pemisah «{self.pv.get('sep')}» · {n_rows} baris tabel · {len(used)}/{len(cols)} kolom dipetakan · {len(hk)} isian kop"
             + (f" · ⚠ kolom ganda: {', '.join(sorted(dup))}" if dup else "")
             + ("" if used else " · ⚠ belum ada kolom yang dipetakan"))
        if self.pv.get("map", {}).get("title_row", -1) >= 0:
            s += " · baris judul kolom dilewati"
        self.info.setText(s)
        self.bApply.setEnabled(bool(used or hk))
        self.bApply2.setEnabled(bool(used or hk))

    def _toggle_skip(self, row: int) -> None:
        if row < 0 or not self.pv:
            return
        i = row
        self.skip ^= {i}
        for c in range(self.grid.columnCount()):
            it = self.grid.item(row, c)
            if it:
                it.setBackground(QColor(SKIP_BG) if i in self.skip else (QColor(MAP_BG) if self._cols()[c] else QColor("transparent")))
                it.setForeground(QColor("#868e96" if i in self.skip else "#111"))
        self._mapped()

    # ---------------------------------------------------------------- terapkan
    def apply(self) -> None:
        if self.did is None or not self.pv:
            return
        cur = self.page.cur
        if cur and cur["doc"]["id"] == self.did and cur["rows"]:
            n_ver = sum(1 for r in cur["rows"] if r["verified"])
            if not ask(self, f"Terapkan transkrip? {len(cur['rows'])} baris yang ada (termasuk {n_ver} terverifikasi) akan diganti. "
                             "Isian header yang Anda edit tetap."):
                return
        body = {**self._body(), "teks": self.txt.toPlainText(), "sep": self.pv.get("sep") or "|", "cols": self._cols(),
                "hdr": self._hdr_keys(), "skip_rows": sorted(self.skip), "save_map": True}
        did = self.did
        self.bApply.setEnabled(False)
        self.bApply2.setEnabled(False)

        def ok(j):
            self.bApply.setEnabled(True)
            self.bApply2.setEnabled(True)
            if self.page.cur and self.page.cur["doc"]["id"] == did:
                self.page.cur = j
                self.page.refresh()
                self.page.tabs.setCurrentIndex(0)
            self.page._sync_list()
            self.page.toast(f"Transkrip diterapkan · {len(j['rows'])} baris — periksa sel kuning / merah di tab Data lalu verifikasi", 6000)

        def err(e):
            self.bApply.setEnabled(True)
            self.bApply2.setEnabled(True)
            say(self, "Transkrip tidak bisa diterapkan:\n" + e, warn=True)
        run_bg(api.call, "/core/forms/transkrip/terapkan", body, ok=ok, err=err)
