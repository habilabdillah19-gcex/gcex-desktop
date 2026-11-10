"""Tab Transkrip ruang kerja Borang (0.45-0.46, usul pemilik): AI hanya MENYALIN tulisan di kertas menjadi teks; PENGGUNA yang
memilih, menentukan dan memutuskan teks itu menjadi data apa:
  - teks bebas (panel 1) dirapikan langsung, atau lewat kisi (panel 3): sunting sel (klik ganda), klik kanan sel / judul kolom
    untuk geser sel kiri / kanan, gabung / pecah sel, gabung baris ke atas (uraian lanjutan), jadikan isian kop, hapus / sisipkan
    baris & kolom, tukar kolom — semua suntingan kisi ditulis balik ke teks;
  - baris dropdown (menempel di atas kisi) = tujuan tiap kolom: kolom tabel utama, tabel tambahan (DDR: Meterage / lubang),
    isian kop (nilai yang sama di tiap baris) atau — abaikan —; pilihan pengguna dipertahankan selama teks disunting;
  - panel 2: tiap 'Label: nilai' -> isian header (nilai bisa disunting);
  - Terapkan -> baris masuk tabel Data seperti hasil baca langsung (validasi, ringkasan, pivot, ekspor sama). Keputusan disimpan
    (per jumlah kolom + judul kolom yang dikenali) sehingga ✦ Baca dengan AI berikutnya langsung menyusun tabel sendiri;
    'Terapkan juga ke n borang lain' untuk borang jenis sama yang sudah tersalin tetapi menunggu pemetaan.
Rute /core/forms/transkrip, /transkrip/pratinjau, /transkrip/terapkan, /transkrip/terapkan_semua (backend core_transkrip)."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QMenu, QPlainTextEdit, QScrollArea, QSplitter,
                               QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from . import api
from .card import btn
from .dialogs import ask, say
from .util import SET, run_bg

SEP_ITEMS = (("Otomatis", "auto"), ("Garis tegak  |", "|"), ("Tab", "tab"), ("Koma  ,", ","), ("Titik koma  ;", ";"))
MAP_BG, SKIP_BG, UNC_BG = "#eef5ff", "#f1f3f5", "#fff3bf"
SEPCH = {"|": "|", "tab": "\t", ",": ",", ";": ";"}


def render(hdr: list, rows: list, sep: str) -> str:
    """Kisi -> teks (sama dengan core_transkrip.render)."""
    ch = SEPCH.get(sep, "|")
    j = f" {ch} " if ch in "|;" else ("\t" if ch == "\t" else ch + " ")
    return "\n".join([f"{a}: {b}" for a, b in hdr] + [j.join((str(c) if str(c).strip() else "-") for c in r) for r in rows])


class TranscriptTab(QWidget):
    """Panel kanan tab 'Transkrip'."""

    def __init__(self, page) -> None:
        super().__init__()
        self.page = page
        self.pv: dict | None = None      # pratinjau terakhir dari backend (kisi + usulan pemetaan + pilihan)
        self.did: int | None = None
        self.loaded = ""                 # teks yang terakhir dimuat dari borang (untuk memuat ulang bila berubah di belakang)
        self.skip: set[int] = set()
        self.choice: list[str] | None = None   # tujuan kolom yang DIPILIH pengguna (dipertahankan selama teks disunting)
        self.hchoice: dict[str, str] = {}       # label kop -> isian header pilihan pengguna
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
        self.cbMode.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cbMode.setMinimumContentsLength(7)
        for t, k in (("Ganti teks", "ganti"), ("+ kolom di kanan", "kanan"), ("+ di bawah", "bawah")):
            self.cbMode.addItem(t, k)
        self.cbMode.setToolTip("Hasil salinan AI:\n• Ganti teks — teks lama diganti.\n• + kolom di kanan — untuk scan KOLOM satu per "
                               "satu dari kiri ke kanan (✂ Potong kolom Meterage → salin, potong Hole ID → salin, …): baris ke-1 salinan baru "
                               "ditempel di kanan baris ke-1 teks, dst.\n• + di bawah — potongan / lembar berikutnya dari tabel yang sama.")
        self.cbMode.setCurrentIndex(max(0, self.cbMode.findData(SET.get("qt_fm_tr_mode", "ganti"))))
        self.cbMode.currentIndexChanged.connect(lambda _i: SET.set("qt_fm_tr_mode", self.cbMode.currentData()))
        top.addWidget(self.cbMode)
        top.addSpacing(6)
        top.addWidget(QLabel("Pemisah:"))
        self.cbSep = QComboBox()
        self.cbSep.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cbSep.setMinimumContentsLength(5)
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
        self.info.setTextFormat(Qt.RichText)
        v.addWidget(self.info)
        sp = QSplitter(Qt.Vertical)
        sp.setHandleWidth(5)
        # ---- teks
        tw = QWidget()
        tv = QVBoxLayout(tw)
        tv.setContentsMargins(0, 0, 0, 0)
        tv.setSpacing(3)
        lt = QLabel("1 · TEKS SALINAN AI  —  boleh disunting langsung; satu baris tabel = satu baris teks")
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
        lh = QLabel("2 · ISIAN KOP  —  tiap 'Label: nilai' masuk ke isian header mana (klik ganda nilai untuk menyunting)")
        lh.setObjectName("fmSect")
        lh.setWordWrap(True)
        hv.addWidget(lh)
        self.hdr = QTableWidget(0, 3)
        self.hdr.setHorizontalHeaderLabels(["Label di teks", "Nilai", "Masuk ke isian header"])
        self.hdr.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.hdr.verticalHeader().setVisible(False)
        self.hdr.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.hdr.itemChanged.connect(self._hdr_edited)
        self.hdr.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hdr.customContextMenuRequested.connect(self._hdr_menu)
        hv.addWidget(self.hdr, 1)
        sp.addWidget(hw)
        # ---- kisi
        gw = QWidget()
        gv = QVBoxLayout(gw)
        gv.setContentsMargins(0, 0, 0, 0)
        gv.setSpacing(3)
        lg = QLabel("3 · KISI  —  baris biru: tujuan tiap kolom. Klik ganda sel = sunting; klik kanan sel / judul kolom = geser, gabung, "
                    "pecah, jadikan kop, hapus; klik nomor baris = lewati / pakai.")
        lg.setObjectName("fmSect")
        lg.setWordWrap(True)
        gv.addWidget(lg)
        # halaman 0 = bantuan + daftar tujuan yang bisa dipilih (sebelum ada teks); halaman 1 = baris tujuan + kisi
        self.gstack = QStackedWidget()
        self.help = QLabel()
        self.help.setObjectName("fmTrHelp")
        self.help.setWordWrap(True)
        self.help.setTextFormat(Qt.RichText)
        self.help.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.help.setMargin(10)
        hs = QScrollArea()
        hs.setWidgetResizable(True)
        hs.setWidget(self.help)
        self.gstack.addWidget(hs)
        gpage = QWidget()
        gpv = QVBoxLayout(gpage)
        gpv.setContentsMargins(0, 0, 0, 0)
        gpv.setSpacing(0)
        self.gstack.addWidget(gpage)
        self.maprow = QTableWidget(1, 0)  # baris dropdown tujuan kolom: tabel 1 baris yang MENEMPEL di atas kisi (tidak ikut tergulir)
        self.maprow.setObjectName("fmMapRow")
        self.maprow.setVerticalHeaderLabels(["→ isian"])
        self.maprow.horizontalHeader().setVisible(False)
        self.maprow.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.maprow.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.maprow.setFixedHeight(34)
        self.maprow.setEditTriggers(QTableWidget.NoEditTriggers)
        gpv.addWidget(self.maprow)
        self.grid = QTableWidget(0, 0)
        self.grid.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.verticalHeader().sectionClicked.connect(self._toggle_skip)
        self.grid.horizontalScrollBar().valueChanged.connect(self.maprow.horizontalScrollBar().setValue)
        self.grid.horizontalHeader().sectionResized.connect(lambda i, _o, w: self.maprow.setColumnWidth(i, w))
        self.grid.verticalHeader().setFixedWidth(52)
        self.maprow.verticalHeader().setFixedWidth(52)
        self.grid.itemChanged.connect(self._cell_edited)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self._cell_menu)
        self.grid.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.horizontalHeader().customContextMenuRequested.connect(
            lambda p: self._col_menu(self.grid.horizontalHeader().logicalIndexAt(p), self.grid.horizontalHeader().mapToGlobal(p)))
        self.grid.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.verticalHeader().customContextMenuRequested.connect(
            lambda p: self._row_menu(self.grid.verticalHeader().logicalIndexAt(p), self.grid.verticalHeader().mapToGlobal(p)))
        gpv.addWidget(self.grid, 1)
        gv.addWidget(self.gstack, 1)
        bot = QHBoxLayout()
        self.bAll = btn("", "Terapkan pemetaan tersimpan ke borang jenis ini yang sudah tersalin tetapi belum punya baris "
                        "(status 'Perlu pemetaan kolom'). Borang yang jumlah / judul kolomnya berbeda dibiarkan untuk Anda.", sm=True)
        self.bAll.clicked.connect(self.apply_all)
        self.bAll.hide()
        bot.addWidget(self.bAll)
        bot.addStretch(1)
        self.bApply = btn("Terapkan ke tabel ▶", "Susun baris dari kisi sesuai pemetaan kolom, lalu isi tabel Data (baris lama diganti; "
                          "isian header yang Anda edit tetap). Keputusan Anda disimpan untuk borang jenis ini.", pri=True)
        self.bApply.clicked.connect(self.apply)
        self.bApply2 = self.bApply  # nama lama
        bot.addWidget(self.bApply)
        gv.addLayout(bot)
        sp.addWidget(gw)
        sp.setSizes(SET.get("qt_fm_tr_split", [230, 110, 360]))
        sp.splitterMoved.connect(lambda *_: SET.set("qt_fm_tr_split", sp.sizes()))
        v.addWidget(sp, 1)
        self.set_doc(None)

    # ---------------------------------------------------------------- data
    def set_doc(self, d: dict | None) -> None:
        """Dipanggil FormsPage saat borang dibuka / disegarkan: tampilkan teks tersimpan borang itu (muat ulang bila teks
        borang yang sama berubah di belakang, mis. selesai dibaca AI cara Transkrip)."""
        did = d["id"] if d else None
        teks = (d or {}).get("teks") or ""
        if d is not None and did == self.did and teks == self.loaded:
            self._waiting()
            return
        if did != self.did:
            self.choice, self.hchoice = None, {}
        self.did, self.loaded = did, teks
        self.skip = set()
        self._filling = True
        self.txt.setPlainText(teks)
        self._filling = False
        for b in (self.bAI, self.bApply):
            b.setEnabled(d is not None)
        self.txt.setEnabled(d is not None)
        if d is None:
            self.pv = None
            self.hdr.setRowCount(0)
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            self.maprow.setColumnCount(0)
            self.help.setText("Pilih borang di daftar kiri.")
            self.gstack.setCurrentIndex(0)
            self.info.setText("")
            self._waiting()
            return
        self.preview()

    def _waiting(self) -> None:
        """Tombol 'Terapkan juga ke n borang lain' untuk borang jenis sama yang tersalin & menunggu pemetaan."""
        cur = self.page.cur["doc"] if self.page.cur else None
        n = 0
        if cur:
            n = sum(1 for d in self.page.docs if d["type"] == cur["type"] and d["id"] != cur["id"] and (d.get("teks") or "").strip()
                    and not d.get("n_rows"))
        self.bAll.setText(f"Terapkan juga ke {n} borang lain ▶▶")
        self.bAll.setVisible(n > 0)

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
                      "Untuk scan kolom satu per satu, pilih '+ kolom di kanan'."):
            return
        ai = self.page.win.ai
        body = {**self._body(), "host": ai.host.text().strip(), "model": ai.model(), "extra": ai.extra.toPlainText(),
                "max_px": int(self.page.cbSpeed.currentData() or 1600), "trim": bool(SET.get("fmTrim", True)),
                "mode": mode, "base": self.txt.toPlainText(), "sep": (self.pv or {}).get("sep") or self.cbSep.currentData() or "auto"}
        did = self.did
        self.bAI.setEnabled(False)
        self.bAI.setText("AI menyalin…")
        self.info.setText("AI sedang menyalin tulisan di kertas… Anda bisa membuka borang lain sementara menunggu.")
        if self.pv is not None and not self.pv.get("ncol"):
            self.help.setText(self._help_html(self.pv))

        def done():
            self.bAI.setText("✦ Salin teks dengan AI")
            self.bAI.setEnabled(self.did is not None)
            if self.pv is not None and not self.pv.get("ncol"):
                self.help.setText(self._help_html(self.pv))

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
            if mode == "ganti":
                self.choice, self.skip = None, set()
            elif mode == "kanan" and self.choice is not None:
                self.choice = self.choice + [""] * max(0, int(j.get("ncol") or 0) - len(self.choice))
            self.loaded = j["teks"]
            self._filling = True
            self.txt.setPlainText(j["teks"])
            self._filling = False
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
        self._pseq = getattr(self, "_pseq", 0) + 1
        seq = self._pseq

        def ok(j):
            if self.did == did and seq == self._pseq:  # jawaban pratinjau lama yang datang terlambat diabaikan
                self._show(j)

        def err(e):
            if self.did == did:
                self.info.setText("Pratinjau gagal: " + e)
        run_bg(api.call, "/core/forms/transkrip/pratinjau", body, ok=ok, err=err)

    # ---------------------------------------------------------------- tampilan
    def _combo(self, opts: list[dict], key: str, on_change) -> QComboBox:
        cb = QComboBox()
        for o in opts:
            cb.addItem(o["label"], o["key"])
            if o["key"].startswith("kop:"):
                cb.setItemData(cb.count() - 1, QColor("#7048e8"), Qt.ForegroundRole)
            elif ":" in o["key"]:
                cb.setItemData(cb.count() - 1, QColor("#1c7ed6"), Qt.ForegroundRole)
        i = cb.findData(key or "")
        if i < 0 and key:  # tujuan tersimpan yang tidak ada lagi di jenis ini
            cb.addItem(f"? {key}", key)
            i = cb.count() - 1
        cb.setCurrentIndex(max(0, i))
        cb.currentIndexChanged.connect(lambda _i: on_change())
        return cb

    def _show(self, j: dict) -> None:
        self.pv = j
        g_rows, mp = j.get("rows") or [], j.get("map") or {}
        n = int(j.get("ncol") or 0)
        if self.choice is not None and len(self.choice) == n:
            cols = list(self.choice)  # keputusan pengguna menang atas usulan
        else:
            cols = (list(mp.get("cols") or []) + [""] * n)[:n]
            self.choice = None
        if mp.get("title_row", -1) >= 0 and not self.skip:
            self.skip.add(int(mp["title_row"]))
        self.skip = {i for i in self.skip if i < len(g_rows)}
        # kop
        self._filling = True
        self.hdr.setRowCount(len(j.get("hdr") or []))
        for i, (lbl, val) in enumerate(j.get("hdr") or []):
            a = QTableWidgetItem(lbl)
            a.setFlags(a.flags() & ~Qt.ItemIsEditable)
            self.hdr.setItem(i, 0, a)
            self.hdr.setItem(i, 1, QTableWidgetItem(val))
            k = self.hchoice.get(lbl, (mp.get("hdr") or [])[i] if i < len(mp.get("hdr") or []) else "")
            self.hdr.setCellWidget(i, 2, self._combo(j.get("hdr_options") or [], k, self._hdr_changed))
        # kisi
        self.grid.clear()
        self.grid.setColumnCount(n)
        self.grid.setRowCount(len(g_rows))
        self.grid.setHorizontalHeaderLabels([f"Kolom {i + 1}" for i in range(n)])
        self.grid.setVerticalHeaderLabels([str(i + 1) for i in range(len(g_rows))])
        self.maprow.setColumnCount(n)
        for c in range(n):
            self.maprow.setCellWidget(0, c, self._combo(j.get("options") or [], cols[c], self._col_changed))
        for r, row in enumerate(g_rows):
            for c in range(n):
                self.grid.setItem(r, c, QTableWidgetItem(row[c] if c < len(row) else ""))
        self._paint()
        self._filling = False
        self.grid.resizeColumnsToContents()
        for c in range(n):
            w = min(420, max(self.grid.columnWidth(c) + 12, 150))
            self.grid.setColumnWidth(c, w)
            self.maprow.setColumnWidth(c, w)
        self.gstack.setCurrentIndex(1 if n else 0)
        if not n:
            self.help.setText(self._help_html(j))
        self._mapped()
        self._waiting()

    def _help_html(self, j: dict) -> str:
        """Halaman kisi sebelum ada teks: apa yang akan bisa Anda putuskan + SEMUA tujuan yang tersedia untuk jenis borang ini."""
        main, tabs, kop = [], {}, []
        for o in j.get("options") or []:
            k, lbl = o["key"], o["label"]
            if not k:
                continue
            if k.startswith("kop:"):
                kop.append(lbl.split("·", 1)[-1].strip())
            elif ":" in k:
                t, _, f = lbl.partition("·")
                tabs.setdefault(t.strip(), []).append(f.strip())
            else:
                main.append(lbl)

        def chips(xs: list) -> str:
            return " ".join(f"<span style='background:#eef5ff;border:1px solid #c9d6e8;border-radius:3px;padding:1px 5px'>&nbsp;{x}&nbsp;</span>"
                            for x in xs)
        busy = not self.bAI.isEnabled() and self.did is not None
        h = [("<b>AI sedang menyalin tulisan…</b> Kisi akan muncul di sini begitu teks selesai." if busy else
              "<b>Belum ada teks.</b> Klik <b>✦ Salin teks dengan AI</b>, atau ketik / tempel teks di panel 1."),
             "<br><br>Begitu teks ada, setiap kolom teks mendapat <b>dropdown tujuan</b> di baris biru atas kisi. <b>Anda yang memutuskan</b> "
             f"tiap kelompok tulisan menjadi data apa. Tujuan yang tersedia untuk <b>{j.get('type_name') or 'borang ini'}</b>:",
             f"<p style='line-height:170%'><b>Tabel utama</b><br>{chips(main)}</p>"]
        for t, fs in tabs.items():
            h.append(f"<p style='line-height:170%'><b>Tabel {t}</b> — boleh dalam baris teks yang sama dengan tabel utama<br>{chips(fs)}</p>")
        if kop:
            h.append(f"<p style='line-height:170%'><b>Kop</b> — untuk kolom berisi nilai kop yang sama di tiap baris<br>{chips(kop)}</p>")
        h.append("<p><b>— abaikan —</b> untuk kolom yang tidak dipakai (keputusan ini juga diingat).</p>"
                 "<p><b>Alat di kisi:</b> klik ganda sel = sunting · klik kanan sel = sisipkan / hapus sel (geser), gabung / pecah sel, "
                 "gabungkan ke baris atas, jadikan isian kop, lewati baris · klik kanan judul kolom = pecah kolom (rentang jam │ uraian), "
                 "gabungkan semua baris lanjutan ke atas, tukar / sisipkan / hapus kolom. Isian <i>Label: nilai</i> di teks masuk panel 2.</p>"
                 "<p>Scan kolom satu per satu: pilih <b>+ kolom di kanan</b>, ✂ potong satu kolom, salin; ulangi untuk kolom berikutnya.</p>")
        return "".join(h)

    def _paint(self) -> None:
        cols = self._cols()
        was, self._filling = self._filling, True
        for r in range(self.grid.rowCount()):
            for c in range(self.grid.columnCount()):
                it = self.grid.item(r, c)
                if not it:
                    continue
                if r in self.skip:
                    it.setBackground(QColor(SKIP_BG))
                    it.setForeground(QColor("#868e96"))
                else:
                    it.setForeground(QColor("#111"))
                    it.setBackground(QColor(UNC_BG) if it.text().endswith("?") else (QColor(MAP_BG) if c < len(cols) and cols[c] else QColor("#ffffff")))
        self._filling = was

    def _cols(self) -> list[str]:
        return [(self.maprow.cellWidget(0, c).currentData() or "") if self.maprow.cellWidget(0, c) else "" for c in range(self.maprow.columnCount())]

    def _hdr_keys(self) -> list[str]:
        return [(self.hdr.cellWidget(i, 2).currentData() or "") if self.hdr.cellWidget(i, 2) else "" for i in range(self.hdr.rowCount())]

    def _col_changed(self) -> None:
        self.choice = self._cols()
        self._paint()
        self._mapped()

    def _hdr_changed(self) -> None:
        for i in range(self.hdr.rowCount()):
            if self.hdr.item(i, 0):
                self.hchoice[self.hdr.item(i, 0).text()] = self.hdr.cellWidget(i, 2).currentData() or ""
        self._mapped()

    def _mapped(self) -> None:
        if not self.pv:
            return
        cols = self._cols()
        n_rows = max(0, self.grid.rowCount() - len(self.skip))
        used = [c for c in cols if c]
        dup = sorted({c for c in used if used.count(c) > 1})
        hk = [k for k in self._hdr_keys() if k]
        mp = self.pv.get("map") or {}
        src = {"title": "dari judul kolom", "saved": "dari keputusan Anda sebelumnya", "default": "urutan bawaan — periksa!"}.get(mp.get("src"), "")
        s = (f"Pemisah «{self.pv.get('sep')}» · {n_rows} baris tabel · <b>{len(used)}/{len(cols)} kolom</b> dipetakan"
             + (f" ({src})" if src and self.choice is None else " (pilihan Anda)") + f" · {len(hk)} isian kop"
             + (f" · kolom bertujuan sama digabung: {', '.join(dup)}" if dup else "")
             + ("" if used or hk else " · <span style='color:#c0392b'>⚠ belum ada kolom yang dipetakan</span>"))
        if self.skip:
            s += f" · {len(self.skip)} baris dilewati"
        if (self.page.cur and self.page.cur["doc"]["id"] == self.did and str(self.page.cur["doc"].get("error") or "").startswith("PEMETAAN")):
            s = ("<span style='color:#7048e8'><b>AI sudah menyalin borang ini, kolomnya menunggu keputusan Anda</b></span> — "
                 + str(self.page.cur["doc"]["error"])[10:] + ".<br>" + s)
        self.info.setText(s)
        self.bApply.setEnabled(bool(used or hk))

    # ---------------------------------------------------------------- suntingan kisi -> teks
    def _model(self) -> tuple[list, list]:
        hdr = [[self.hdr.item(i, 0).text(), self.hdr.item(i, 1).text() if self.hdr.item(i, 1) else ""] for i in range(self.hdr.rowCount())
               if self.hdr.item(i, 0)]
        rows = [[(self.grid.item(r, c).text() if self.grid.item(r, c) else "") for c in range(self.grid.columnCount())]
                for r in range(self.grid.rowCount())]
        return hdr, rows

    def _commit(self, hdr: list, rows: list, choice: list | None = None, skip: set | None = None) -> None:
        """Tulis kisi hasil suntingan kembali ke teks, lalu pratinjau ulang (pilihan kolom & baris yang dilewati dipertahankan)."""
        if choice is not None:
            self.choice = choice
        elif self.choice is None:
            self.choice = self._cols()
        if skip is not None:
            self.skip = skip
        sep = (self.pv or {}).get("sep") or "|"
        if self.cbSep.currentData() == "auto" and sep != "auto":
            self.cbSep.blockSignals(True)
            self.cbSep.setCurrentIndex(max(0, self.cbSep.findData(sep)))
            self.cbSep.blockSignals(False)
        n = max((len(r) for r in rows), default=0)
        rows = [r + [""] * (n - len(r)) for r in rows]
        self.choice = (self.choice + [""] * n)[:n]
        self._filling = True
        self.txt.setPlainText(render(hdr, rows, sep))
        self._filling = False
        self.preview()

    def _cell_edited(self, it: QTableWidgetItem) -> None:
        if self._filling:
            return
        hdr, rows = self._model()
        self._commit(hdr, rows)

    def _hdr_edited(self, it: QTableWidgetItem) -> None:
        if self._filling:
            return
        hdr, rows = self._model()
        self._commit(hdr, rows)

    def _cell_menu(self, pos) -> None:
        it = self.grid.itemAt(pos)
        if not it:
            return
        r, c = it.row(), it.column()
        hdr, rows = self._model()
        ch = list(self.choice if self.choice is not None else self._cols())
        n = self.grid.columnCount()
        m = QMenu(self)
        m.addSection(f"Sel baris {r + 1}, kolom {c + 1}")

        def shift_right():
            rows[r].insert(c, "")
            if rows[r][-1].strip() == "" and len(rows[r]) > n:
                rows[r].pop()
            self._commit(hdr, rows, ch + [""] * (max(len(x) for x in rows) - len(ch)))

        def shift_left():
            rows[r].pop(c)
            rows[r].append("")
            self._commit(hdr, rows, ch)

        def join_right():
            if c + 1 < len(rows[r]):
                rows[r][c] = (rows[r][c] + " " + rows[r][c + 1]).strip()
                rows[r].pop(c + 1)
                rows[r].append("")
            self._commit(hdr, rows, ch)

        def split_cell():
            parts = it.text().split(None, 1)
            if len(parts) == 2:
                rows[r][c:c + 1] = parts
                if rows[r][-1].strip() == "" and len(rows[r]) > n:
                    rows[r].pop()
            self._commit(hdr, rows, ch + [""] * (max(len(x) for x in rows) - len(ch)))
        m.addAction("⇥ Sisipkan sel kosong di sini (sel kanan bergeser)", shift_right)
        m.addAction("⇤ Hapus sel ini (sel kanan bergeser ke kiri)", shift_left)
        a = m.addAction("⊕ Gabung dengan sel di kanannya", join_right)
        a.setEnabled(c + 1 < n)
        a = m.addAction("✂ Pecah sel di spasi pertama (sel kanan bergeser)", split_cell)
        a.setEnabled(len(it.text().split(None, 1)) == 2)
        m.addSeparator()
        self._row_actions(m, r, hdr, rows, ch)
        m.addSeparator()
        sub = m.addMenu(f"Kolom {c + 1}")
        self._col_actions(sub, c, hdr, rows, ch)
        m.exec(self.grid.viewport().mapToGlobal(pos))

    def _row_actions(self, m: QMenu, r: int, hdr: list, rows: list, ch: list) -> None:
        def up():
            if r > 0:
                for j, v in enumerate(rows[r]):
                    if v.strip() and v.strip() != "-":
                        rows[r - 1][j] = (rows[r - 1][j] + " " + v).strip() if rows[r - 1][j].strip() not in ("", "-") else v
                rows.pop(r)
            self._commit(hdr, rows, ch, {i - (1 if i > r else 0) for i in self.skip if i != r})

        def to_kop():
            vals = [v for v in rows[r] if v.strip() and v.strip() != "-"]
            if vals:
                hdr.append([vals[0].rstrip(":"), " ".join(vals[1:])])
            rows.pop(r)
            self._commit(hdr, rows, ch, {i - (1 if i > r else 0) for i in self.skip if i != r})

        def delete():
            rows.pop(r)
            self._commit(hdr, rows, ch, {i - (1 if i > r else 0) for i in self.skip if i != r})

        def insert():
            rows.insert(r, [""] * len(rows[r]))
            self._commit(hdr, rows, ch, {i + (1 if i >= r else 0) for i in self.skip})
        a = m.addAction("⤒ Gabungkan ke baris di atasnya (uraian lanjutan)", up)
        a.setEnabled(r > 0)
        m.addAction("☰ Jadikan isian kop (sel pertama = label, sisanya = nilai)", to_kop)
        m.addAction(("✓ Pakai baris ini" if r in self.skip else "⊘ Lewati baris ini (tidak diterapkan)"), lambda: self._toggle_skip(r))
        m.addAction("＋ Sisipkan baris kosong di atas", insert)
        m.addAction("✕ Hapus baris ini dari teks", delete)

    def _row_menu(self, r: int, gpos) -> None:
        if r < 0:
            return
        hdr, rows = self._model()
        ch = list(self.choice if self.choice is not None else self._cols())
        m = QMenu(self)
        m.addSection(f"Baris {r + 1}")
        self._row_actions(m, r, hdr, rows, ch)
        m.exec(gpos)

    def _col_actions(self, m: QMenu, c: int, hdr: list, rows: list, ch: list) -> None:
        n = self.grid.columnCount()

        def split_col():
            for row in rows:
                p = row[c].split(None, 1) if c < len(row) else []
                row[c:c + 1] = (p + [""])[:2] if p else ["", ""]
            self._commit(hdr, rows, ch[:c + 1] + [""] + ch[c + 1:])

        def split_time():  # "0645-0710 Travel to location" -> jam | uraian
            for row in rows:
                v = row[c] if c < len(row) else ""
                mm = re.match(r"^\s*([0-9.:]{3,5}\s*[-–]\s*[0-9.:]{3,5})\s*(.*)$", v)
                row[c:c + 1] = [mm.group(1), mm.group(2)] if mm else ["", v]
            self._commit(hdr, rows, ch[:c] + ["jam" if "jam" in {o["key"] for o in (self.pv or {}).get("options") or []} else ch[c]] + [ch[c]] + ch[c + 1:])

        def join_col():
            for row in rows:
                row[c] = " ".join(x for x in (row[c], row[c + 1]) if x.strip() and x.strip() != "-")
                row.pop(c + 1)
            self._commit(hdr, rows, ch[:c + 1] + ch[c + 2:])

        def swap():
            for row in rows:
                row[c], row[c + 1] = row[c + 1], row[c]
            ch2 = list(ch)
            ch2[c], ch2[c + 1] = ch2[c + 1], ch2[c]
            self._commit(hdr, rows, ch2)

        def ins():
            for row in rows:
                row.insert(c, "")
            self._commit(hdr, rows, ch[:c] + [""] + ch[c:])

        def drop():
            for row in rows:
                row.pop(c)
            self._commit(hdr, rows, ch[:c] + ch[c + 1:])
        def up_empty():  # semua baris yang kolom ini kosong = lanjutan baris di atasnya (mis. uraian dua baris tanpa jam)
            out, sk = [], set()
            for i, row in enumerate(rows):
                if out and not row[c].strip().strip("-").strip() and any(v.strip() not in ("", "-") for v in row):
                    for jj, v in enumerate(row):
                        if v.strip() not in ("", "-"):
                            out[-1][jj] = (out[-1][jj] + " " + v).strip() if out[-1][jj].strip() not in ("", "-") else v
                    continue
                if i in self.skip:
                    sk.add(len(out))
                out.append(row)
            self._commit(hdr, out, ch, sk)
        n_up = sum(1 for i, row in enumerate(rows) if i and c < len(row) and not row[c].strip().strip("-").strip()
                   and any(v.strip() not in ("", "-") for v in row))
        a = m.addAction(f"⤒ Gabungkan {n_up} baris yang kolom ini kosong ke baris di atasnya", up_empty)
        a.setEnabled(n_up > 0)
        m.addSeparator()
        m.addAction("✂ Pecah kolom di spasi pertama", split_col)
        m.addAction("✂ Pecah kolom: rentang jam | sisanya", split_time)
        a = m.addAction("⊕ Gabung dengan kolom di kanannya", join_col)
        a.setEnabled(c + 1 < n)
        a = m.addAction("⇄ Tukar dengan kolom di kanannya", swap)
        a.setEnabled(c + 1 < n)
        m.addAction("＋ Sisipkan kolom kosong di kiri", ins)
        m.addAction("✕ Hapus kolom ini dari teks", drop)

    def _col_menu(self, c: int, gpos) -> None:
        if c < 0:
            return
        hdr, rows = self._model()
        ch = list(self.choice if self.choice is not None else self._cols())
        m = QMenu(self)
        m.addSection(f"Kolom {c + 1}")
        self._col_actions(m, c, hdr, rows, ch)
        m.exec(gpos)

    def _hdr_menu(self, pos) -> None:
        it = self.hdr.itemAt(pos)
        if not it:
            return
        i = it.row()
        hdr, rows = self._model()

        def to_row():
            lbl, val = hdr.pop(i)
            n = max(1, self.grid.columnCount())
            rows.append(([lbl, val] + [""] * n)[:max(n, 2)])
            self._commit(hdr, rows)

        def delete():
            hdr.pop(i)
            self._commit(hdr, rows)
        m = QMenu(self)
        m.addAction("☷ Jadikan baris tabel", to_row)
        m.addAction("✕ Hapus isian kop ini dari teks", delete)
        m.exec(self.hdr.viewport().mapToGlobal(pos))

    def _toggle_skip(self, row: int) -> None:
        if row < 0 or not self.pv:
            return
        self.skip ^= {row}
        self._paint()
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
        tr_ = (self.pv.get("map") or {}).get("title_row", -1)
        body = {**self._body(), "teks": self.txt.toPlainText(), "sep": self.pv.get("sep") or "|", "cols": self._cols(),
                "hdr": self._hdr_keys(), "skip_rows": sorted(self.skip), "save_map": True,
                "title_row": tr_ if tr_ in self.skip else -1}
        did = self.did
        self.bApply.setEnabled(False)

        def ok(j):
            self.bApply.setEnabled(True)
            self.loaded = j["doc"].get("teks") or self.loaded
            if self.page.cur and self.page.cur["doc"]["id"] == did:
                self.page.cur = j
                self.page.refresh()
                self.page.tabs.setCurrentIndex(0)
            self.page._sync_list()
            self.page.toast(f"Transkrip diterapkan · {len(j['rows'])} baris — keputusan kolom disimpan untuk borang jenis ini. "
                            "Periksa sel kuning / merah di tab Data lalu verifikasi", 6000)

        def err(e):
            self.bApply.setEnabled(True)
            say(self, "Transkrip tidak bisa diterapkan:\n" + e, warn=True)
        run_bg(api.call, "/core/forms/transkrip/terapkan", body, ok=ok, err=err)

    def apply_all(self) -> None:
        cur = self.page.cur["doc"] if self.page.cur else None
        if not cur:
            return
        body = {"folder": self.page.folder, "by": self.page.by(), "type": cur["type"]}

        def ok(j):
            self.page._sync_list()
            left = j.get("left") or []
            msg = f"{len(j.get('done') or [])} borang diterapkan dengan pemetaan tersimpan."
            if left:
                msg += (f"\n{len(left)} borang masih menunggu (jumlah / judul kolom berbeda — buka tab Transkrip-nya): "
                        + ", ".join(x["name"] for x in left[:6]) + (" …" if len(left) > 6 else ""))
            say(self, msg)
            self._waiting()

        def err(e):
            say(self, "Gagal menerapkan ke borang lain:\n" + e, warn=True)
        run_bg(api.call, "/core/forms/transkrip/terapkan_semua", body, ok=ok, err=err)
