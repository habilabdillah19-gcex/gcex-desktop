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
from PySide6.QtGui import QColor, QFontMetricsF
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QMenu, QPlainTextEdit, QScrollArea, QSplitter,
                               QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from . import api
from .card import btn
from .dialogs import ask, say
from .forms_pemisah import BreakDialog
from .util import SET, run_bg

SEP_ITEMS = (("Otomatis", "auto"), ("Garis tegak  |", "|"), ("Tab", "tab"), ("Koma  ,", ","), ("Titik koma  ;", ";"),
             ("Spasi lebar (≥2 / tab)", "spasi2"), ("Setiap spasi", "spasi"), ("Garis pemisah (lebar tetap)…", "fixed"))
SEPNAME = {"|": "garis tegak |", "tab": "tab", ",": "koma", ";": "titik koma", "spasi2": "spasi lebar", "spasi": "setiap spasi",
           "fixed": "garis pemisah"}
MAP_BG, SKIP_BG, UNC_BG = "#eef5ff", "#f1f3f5", "#fff3bf"
SEPCH = {"|": "|", "tab": "\t", ",": ",", ";": ";"}


def render(hdr: list, rows: list, sep: str, grp: list | None = None) -> str:
    """Kisi -> teks (sama dengan core_transkrip.render): '# Kelompok n' memisahkan kelompok tulisan bila lebih dari satu."""
    ch = SEPCH.get(sep, "|")
    j = f" {ch} " if ch in "|;" else ("\t" if ch == "\t" else ch + " ")
    out = [f"{a}: {b}" for a, b in hdr]
    gs = [g_ for g_ in (grp or []) if g_[0] < g_[1]]
    starts = {a: k for k, (a, _b) in enumerate(gs)} if len(gs) > 1 else {}
    for i, r in enumerate(rows):
        if i in starts:
            if out:
                out.append("")
            out.append(f"# Kelompok {starts[i] + 1}")
        out.append(j.join((str(c) if str(c).strip() else "-") for c in r))
    return "\n".join(out)


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
        self.grp: list[list[int]] = []   # kelompok tulisan [awal, akhir) dalam baris kisi
        self.gw: list[int] = []          # lebar (jumlah kolom) tiap kelompok
        self.vmap: list[tuple[str, int]] = []  # baris tampilan -> ("map", kelompok) / ("row", indeks baris teks)
        self.breaks: list[int] | None = None   # garis pemisah lebar tetap (posisi karakter) pilihan pengguna
        self._sep_prev = 0
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
        self.cbSep.setToolTip("Tanda yang memisahkan sel dalam satu baris teks. Otomatis = yang paling konsisten di semua baris.\n"
                              "• Spasi lebar — teks rata kolom: 2 spasi atau lebih / tab = batas sel (spasi tunggal tetap di dalam sel).\n"
                              "• Setiap spasi — tiap spasi memisahkan sel.\n"
                              "• Garis pemisah — tarik garis batas kolom sendiri pada teks, seperti mengimpor teks di Excel.")
        self.cbSep.currentIndexChanged.connect(self._sep_changed)
        top.addWidget(self.cbSep)
        self.bLines = btn("┆ Atur garis…", "Buka lagi penggaris garis pemisah: klik = buat garis, seret = pindahkan, klik ganda = hapus", sm=True)
        self.bLines.clicked.connect(self.edit_breaks)
        self.bLines.hide()
        top.addWidget(self.bLines)
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
        self.txt.ensurePolished()
        self.txt.setTabStopDistance(QFontMetricsF(self.txt.font()).horizontalAdvance(" ") * 8)  # tab = 8 kolom (sama dengan garis pemisah)
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
        lg = QLabel("3 · KISI  —  tiap KELOMPOK tulisan (mis. tabel lubang dan tabel kegiatan) punya baris biru ▸ berisi tujuan tiap kolomnya. "
                    "Klik ganda sel = sunting; klik kanan sel / nomor baris / judul kolom = geser, gabung, pecah, pindah kelompok, jadikan kop, "
                    "hapus; klik nomor baris = lewati / pakai.")
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
        self.grid = QTableWidget(0, 0)
        self.grid.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.verticalHeader().sectionClicked.connect(self._toggle_skip)
        self.grid.verticalHeader().setFixedWidth(58)
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
            self.grp: list[list[int]] = []
            self.breaks = None
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
            elif mode == "kanan" and self.choice is not None and len(self.choice) == 1:
                self.choice = [self.choice[0] + [""] * max(0, int(j.get("ncol") or 0) - len(self.choice[0]))]
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

    def _sep_changed(self, i: int) -> None:
        """Pemisah diganti. 'Garis pemisah' langsung membuka penggaris (garis usulan otomatis) — Batal = kembali ke pemisah lama."""
        k = self.cbSep.itemData(i)
        if k == "fixed" and self.did is not None and self.txt.toPlainText().strip():
            if not self.edit_breaks(preview=False):
                self.cbSep.blockSignals(True)
                self.cbSep.setCurrentIndex(self._sep_prev if self._sep_prev != i else 0)
                self.cbSep.blockSignals(False)
                self.bLines.setVisible(self.cbSep.currentData() == "fixed")
                return
        self._sep_prev = self.cbSep.currentIndex()
        self.bLines.setVisible(k == "fixed")
        self.preview()

    def edit_breaks(self, preview: bool = True) -> bool:
        """Penggaris garis pemisah (lebar tetap). True bila pengguna memakai garisnya."""
        cur = self.breaks if self.breaks else ((self.pv or {}).get("breaks") or None)
        d = BreakDialog(self, self.txt.toPlainText(), cur)
        if not d.exec():
            return False
        self.breaks = list(d.breaks)
        if preview:
            self.preview()
        return True

    def preview(self) -> None:
        if self.did is None:
            return
        txt = self.txt.toPlainText()
        did = self.did
        sep = self.cbSep.currentData() or "auto"
        body = {**self._body(), "teks": txt, "sep": sep, "breaks": self.breaks if sep == "fixed" else None}
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
            elif o.get("grp") == "kelas":
                cb.setItemData(cb.count() - 1, QColor("#0c8599"), Qt.ForegroundRole)
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
        """Kisi = per KELOMPOK tulisan: satu baris biru ▸ berisi dropdown tujuan kolom kelompok itu, lalu baris-baris datanya."""
        self.pv = j
        g_rows, mp = j.get("rows") or [], j.get("map") or {}
        gs = j.get("groups") or ([{"start": 0, "end": len(g_rows), "cols": mp.get("cols") or [], "ncol": j.get("ncol") or 0,
                                   "title_row": mp.get("title_row", -1)}] if g_rows else [])
        n = int(j.get("ncol") or 0)
        self.grp = [[x["start"], x["end"]] for x in gs]
        self.gw = [int(x.get("ncol") or n) for x in gs]
        if self.choice is not None and len(self.choice) == len(gs) and all(len(c) == w for c, w in zip(self.choice, self.gw)):
            cols = [list(c) for c in self.choice]  # keputusan pengguna menang atas usulan
        else:
            old = self.choice or []
            cols = []
            for k, x in enumerate(gs):
                w = self.gw[k]
                cols.append(list(old[k]) if k < len(old) and len(old[k]) == w else (list(x.get("cols") or []) + [""] * w)[:w])
            self.choice = None if not old else cols
        if not self.skip:
            self.skip = {int(x["title_row"]) for x in gs if x.get("title_row", -1) >= 0}
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
        # kisi: [▸ K1 tujuan] [baris…] [▸ K2 tujuan] [baris…]
        self.vmap: list[tuple[str, int]] = []
        for k, (a, b) in enumerate(self.grp):
            self.vmap.append(("map", k))
            self.vmap += [("row", i) for i in range(a, b)]
        self.grid.clear()
        self.grid.setColumnCount(n)
        self.grid.setRowCount(len(self.vmap))
        self.grid.setHorizontalHeaderLabels([f"Kolom {i + 1}" for i in range(n)])
        multi = len(self.grp) > 1
        labels = []
        for vr, (kind, x) in enumerate(self.vmap):
            if kind == "map":
                labels.append(f"▸ K{x + 1}" if multi else "▸ isian")
                for c in range(n):
                    if c < self.gw[x]:
                        cb = self._combo(j.get("options") or [], cols[x][c], self._col_changed)
                        cb.setProperty("kel", x)
                        cb.setProperty("kol", c)
                        self.grid.setCellWidget(vr, c, cb)
                    else:
                        it = QTableWidgetItem("")
                        it.setFlags(Qt.NoItemFlags)
                        self.grid.setItem(vr, c, it)
                self.grid.setRowHeight(vr, 32)
            else:
                labels.append(str(x + 1))
                row = g_rows[x]
                for c in range(n):
                    self.grid.setItem(vr, c, QTableWidgetItem(row[c] if c < len(row) else ""))
        self.grid.setVerticalHeaderLabels(labels)
        for vr, (kind, x) in enumerate(self.vmap):
            if kind == "map":
                hi = self.grid.verticalHeaderItem(vr)
                if hi:
                    a, b = self.grp[x]
                    hi.setToolTip(f"Kelompok {x + 1}: baris {a + 1}–{b}, {self.gw[x]} kolom — pilih tujuan tiap kolom kelompok ini")
        self._paint()
        self._filling = False
        self.grid.resizeColumnsToContents()
        for c in range(n):
            self.grid.setColumnWidth(c, min(420, max(self.grid.columnWidth(c) + 12, 150)))
        self.gstack.setCurrentIndex(1 if n else 0)
        if not n:
            self.help.setText(self._help_html(j))
        self._mapped()
        self._waiting()

    def _help_html(self, j: dict) -> str:
        """Halaman kisi sebelum ada teks: apa yang akan bisa Anda putuskan + SEMUA tujuan yang tersedia untuk jenis borang ini."""
        main, tabs, kop, kls = [], {}, [], []
        for o in j.get("options") or []:
            k, lbl = o["key"], o["label"]
            if not k:
                continue
            if o.get("grp") == "kelas":
                kls.append(lbl.replace("Kolom kelas ", ""))
            elif k.startswith("kop:"):
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
        if kls:
            h.append("<p style='line-height:170%'><b>Kolom per kelas</b> — borang lama yang menulis angka di bawah kolom kelasnya; "
                     f"Kelas diisi dari kolom yang Anda pilih<br>{chips(kls)}</p>")
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
        kel = {}
        for k, (a, b) in enumerate(self.grp):
            for i in range(a, b):
                kel[i] = k
        for vr, (kind, x) in enumerate(getattr(self, "vmap", [])):
            for c in range(self.grid.columnCount()):
                it = self.grid.item(vr, c)
                if not it:
                    continue
                if kind == "map":
                    it.setBackground(QColor("#e9ecef"))
                    continue
                k = kel.get(x, 0)
                inside = c < (self.gw[k] if k < len(self.gw) else 0)
                if x in self.skip:
                    it.setBackground(QColor(SKIP_BG))
                    it.setForeground(QColor("#868e96"))
                elif not inside:
                    it.setBackground(QColor("#f8f9fa"))
                    it.setForeground(QColor("#adb5bd"))
                else:
                    it.setForeground(QColor("#111"))
                    mapped = k < len(cols) and c < len(cols[k]) and cols[k][c]
                    it.setBackground(QColor(UNC_BG) if it.text().endswith("?") else (QColor(MAP_BG) if mapped else QColor("#ffffff")))
        self._filling = was

    def combo(self, k: int, c: int) -> QComboBox | None:
        """Dropdown tujuan kolom c pada kelompok k."""
        for vr, (kind, x) in enumerate(getattr(self, "vmap", [])):
            if kind == "map" and x == k:
                w = self.grid.cellWidget(vr, c)
                return w if isinstance(w, QComboBox) else None
        return None

    def _cols(self) -> list[list[str]]:
        out = []
        for k in range(len(self.grp)):
            out.append([((self.combo(k, c).currentData() or "") if self.combo(k, c) else "") for c in range(self.gw[k])])
        return out

    def _hdr_keys(self) -> list[str]:
        return [(self.hdr.cellWidget(i, 2).currentData() or "") if self.hdr.cellWidget(i, 2) else "" for i in range(self.hdr.rowCount())]

    def _col_changed(self) -> None:
        self.choice = self._cols()
        self._paint()
        self._mapped()

    def _hdr_changed(self) -> None:
        for i in range(self.hdr.rowCount()):
            if self.hdr.item(i, 0):
                self.hdr_choice_set(self.hdr.item(i, 0).text(), self.hdr.cellWidget(i, 2).currentData() or "")
        self._mapped()

    def hdr_choice_set(self, lbl: str, k: str) -> None:
        self.hchoice[lbl] = k

    def _mapped(self) -> None:
        if not self.pv:
            return
        cols = self._cols()
        valid = {o["key"] for o in (self.pv.get("options") or []) if o["key"]}
        n_rows = max(0, sum(b - a for a, b in self.grp) - len(self.skip))
        parts = []
        all_used = []
        for k, cg in enumerate(cols):
            used = [c for c in cg if c in valid]
            all_used += used
            parts.append(f"{'K' + str(k + 1) + ': ' if len(cols) > 1 else ''}<b>{len(used)}/{len(cg)} kolom</b>")
        dup = sorted({c for cg in cols for c in cg if c and cg.count(c) > 1})
        hk = [k for k in self._hdr_keys() if k]
        mp = self.pv.get("map") or {}
        src = {"title": "dari judul kolom", "saved": "dari keputusan Anda sebelumnya", "default": "urutan bawaan — periksa!"}.get(mp.get("src"), "")
        sp_ = self.pv.get("sep")
        sn = SEPNAME.get(sp_, sp_) + (f" ({len(self.pv.get('breaks') or [])} garis)" if sp_ == "fixed" else "")
        s = (f"Pemisah «{sn}» · {len(self.grp)} kelompok · {n_rows} baris tabel · " + " · ".join(parts) + " dipetakan"
             + (f" ({src})" if src and self.choice is None else " (pilihan Anda)") + f" · {len(hk)} isian kop"
             + (f" · kolom bertujuan sama digabung: {', '.join(dup)}" if dup else "")
             + ("" if all_used or hk else " · <span style='color:#c0392b'>⚠ belum ada kolom yang dipetakan</span>"))
        if self.skip:
            s += f" · {len(self.skip)} baris dilewati"
        if (self.page.cur and self.page.cur["doc"]["id"] == self.did and str(self.page.cur["doc"].get("error") or "").startswith("PEMETAAN")):
            s = ("<span style='color:#7048e8'><b>AI sudah menyalin borang ini, kolomnya menunggu keputusan Anda</b></span> — "
                 + str(self.page.cur["doc"]["error"])[10:] + ".<br>" + s)
        self.info.setText(s)
        self.bApply.setEnabled(bool(all_used or hk))

    # ---------------------------------------------------------------- suntingan kisi -> teks
    def _kel(self, i: int) -> int:
        return next((k for k, (a, b) in enumerate(self.grp) if a <= i < b), max(0, len(self.grp) - 1))

    def _model(self) -> tuple[list, list]:
        hdr = [[self.hdr.item(i, 0).text(), self.hdr.item(i, 1).text() if self.hdr.item(i, 1) else ""] for i in range(self.hdr.rowCount())
               if self.hdr.item(i, 0)]
        rows = []
        for vr, (kind, x) in enumerate(getattr(self, "vmap", [])):
            if kind == "row":
                rows.append([(self.grid.item(vr, c).text() if self.grid.item(vr, c) else "") for c in range(self.grid.columnCount())])
        return hdr, rows

    def _commit(self, hdr: list, rows: list, choice: list | None = None, skip: set | None = None, grp: list | None = None) -> None:
        """Tulis kisi hasil suntingan kembali ke teks ('# Kelompok n' memisahkan kelompok), lalu pratinjau ulang; pilihan kolom
        dan baris yang dilewati dipertahankan."""
        self.choice = [list(c) for c in (choice if choice is not None else (self.choice if self.choice is not None else self._cols()))]
        if skip is not None:
            self.skip = set(skip)
        if grp is not None:
            self.grp = [list(g_) for g_ in grp]
        sep = (self.pv or {}).get("sep") or "|"
        if sep not in SEPCH:  # spasi / garis pemisah: sesudah kisi disunting, teks ditulis ulang dengan '|' (seperti data sudah di sel)
            sep = "|"
            self.breaks = None
        if self.cbSep.currentData() != sep:
            self.cbSep.blockSignals(True)
            self.cbSep.setCurrentIndex(max(0, self.cbSep.findData(sep)))
            self.cbSep.blockSignals(False)
            self._sep_prev = self.cbSep.currentIndex()
            self.bLines.setVisible(sep == "fixed")
        # baris dipotong ke lebar kelompoknya (sel kosong di kanan tidak ikut ditulis)
        out = []
        for i, r in enumerate(rows):
            k = self._kel(i)
            w = max(len(self.choice[k]) if k < len(self.choice) else 0, max((j + 1 for j, v in enumerate(r) if str(v).strip()), default=1))
            out.append(list(r[:w]) + [""] * max(0, w - len(r)))
        for k in range(len(self.grp)):
            if k < len(self.choice):
                a, b = self.grp[k]
                w = max([len(out[i]) for i in range(a, min(b, len(out)))] or [len(self.choice[k])])
                self.choice[k] = (self.choice[k] + [""] * w)[:w]
        self._filling = True
        self.txt.setPlainText(render(hdr, out, sep, self.grp))
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

    def _ctx(self) -> tuple[list, list, list, list]:
        hdr, rows = self._model()
        ch = [list(c) for c in (self.choice if self.choice is not None else self._cols())]
        return hdr, rows, ch, [list(g_) for g_ in self.grp]

    def _cell_menu(self, pos) -> None:
        vr = self.grid.rowAt(pos.y())
        c = self.grid.columnAt(pos.x())
        if vr < 0 or c < 0 or vr >= len(self.vmap):
            return
        kind, x = self.vmap[vr]
        if kind == "map":
            return self._col_menu(c, self.grid.viewport().mapToGlobal(pos), x)
        r = x
        it = self.grid.item(vr, c)
        hdr, rows, ch, grp = self._ctx()
        k = self._kel(r)
        n = self.gw[k]
        m = QMenu(self)
        m.addSection(f"Sel baris {r + 1}, kolom {c + 1}" + (f" · kelompok {k + 1}" if len(grp) > 1 else ""))

        def shift_right():
            rows[r].insert(c, "")
            if len(rows[r]) > n and not rows[r][-1].strip():
                rows[r].pop()
            self._commit(hdr, rows, ch)

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
            parts = (it.text() if it else "").split(None, 1)
            if len(parts) == 2:
                rows[r][c:c + 1] = parts
                if len(rows[r]) > n and not rows[r][-1].strip():
                    rows[r].pop()
            self._commit(hdr, rows, ch)
        m.addAction("⇥ Sisipkan sel kosong di sini (sel kanan bergeser)", shift_right)
        m.addAction("⇤ Hapus sel ini (sel kanan bergeser ke kiri)", shift_left)
        a = m.addAction("⊕ Gabung dengan sel di kanannya", join_right)
        a.setEnabled(c + 1 < n)
        a = m.addAction("✂ Pecah sel di spasi pertama (sel kanan bergeser)", split_cell)
        a.setEnabled(len((it.text() if it else "").split(None, 1)) == 2)
        m.addSeparator()
        self._row_actions(m, r, hdr, rows, ch, grp)
        m.addSeparator()
        sub = m.addMenu(f"Kolom {c + 1}" + (f" (kelompok {k + 1})" if len(grp) > 1 else ""))
        self._col_actions(sub, c, k, hdr, rows, ch, grp)
        m.exec(self.grid.viewport().mapToGlobal(pos))

    def _row_actions(self, m: QMenu, r: int, hdr: list, rows: list, ch: list, grp: list) -> None:
        k = self._kel(r)
        a0, b0 = grp[k]

        def shrink(at: int) -> list:  # baris 'at' dihapus -> batas kelompok sesudahnya bergeser
            return [[a - (1 if a > at else 0), b - (1 if b > at else 0)] for a, b in grp if not (a == at and b == at + 1)]

        def up():
            if r > a0:
                for j, v in enumerate(rows[r]):
                    if v.strip() and v.strip() != "-":
                        rows[r - 1][j] = (rows[r - 1][j] + " " + v).strip() if rows[r - 1][j].strip() not in ("", "-") else v
                rows.pop(r)
            self._commit(hdr, rows, ch, {i - (1 if i > r else 0) for i in self.skip if i != r}, shrink(r))

        def to_kop():
            vals = [v for v in rows[r] if v.strip() and v.strip() != "-"]
            if vals:
                hdr.append([vals[0].rstrip(":"), " ".join(vals[1:])])
            rows.pop(r)
            g2 = shrink(r)
            ch2 = ch if len(g2) == len(grp) else [c for i, c in enumerate(ch) if i != k]
            self._commit(hdr, rows, ch2, {i - (1 if i > r else 0) for i in self.skip if i != r}, g2)

        def delete():
            rows.pop(r)
            g2 = shrink(r)
            ch2 = ch if len(g2) == len(grp) else [c for i, c in enumerate(ch) if i != k]
            self._commit(hdr, rows, ch2, {i - (1 if i > r else 0) for i in self.skip if i != r}, g2)

        def insert():
            rows.insert(r, [""] * len(rows[r]))
            g2 = [[a + (1 if a > r else 0), b + (1 if b > r else 0)] for a, b in grp]
            self._commit(hdr, rows, ch, {i + (1 if i >= r else 0) for i in self.skip}, g2)

        def new_group():  # baris ini dan sesudahnya (dalam kelompok yang sama) menjadi kelompok baru
            g2 = grp[:k] + [[a0, r], [r, b0]] + grp[k + 1:]
            self._commit(hdr, rows, ch[:k + 1] + [[""] * len(ch[k])] + ch[k + 1:], None, g2)

        def join_group():  # kelompok ini digabung ke kelompok di atasnya (memakai tujuan kolom kelompok atas)
            g2 = grp[:k - 1] + [[grp[k - 1][0], b0]] + grp[k + 1:]
            self._commit(hdr, rows, ch[:k] + ch[k + 1:], None, g2)
        a = m.addAction("⤒ Gabungkan ke baris di atasnya (uraian lanjutan)", up)
        a.setEnabled(r > a0)
        m.addAction("☰ Jadikan isian kop (sel pertama = label, sisanya = nilai)", to_kop)
        m.addAction(("✓ Pakai baris ini" if r in self.skip else "⊘ Lewati baris ini (tidak diterapkan)"), lambda: self._toggle_skip_row(r))
        m.addAction("＋ Sisipkan baris kosong di atas", insert)
        m.addAction("✕ Hapus baris ini dari teks", delete)
        m.addSeparator()
        a = m.addAction("▸ Mulai KELOMPOK baru di baris ini (tabel lain, tujuan kolom sendiri)", new_group)
        a.setEnabled(r > a0)
        a = m.addAction(f"▴ Gabungkan kelompok {k + 1} ke kelompok di atasnya", join_group)
        a.setEnabled(k > 0)

    def _row_menu(self, vr: int, gpos) -> None:
        if vr < 0 or vr >= len(getattr(self, "vmap", [])):
            return
        kind, x = self.vmap[vr]
        if kind == "map":
            return
        hdr, rows, ch, grp = self._ctx()
        m = QMenu(self)
        m.addSection(f"Baris {x + 1}" + (f" · kelompok {self._kel(x) + 1}" if len(grp) > 1 else ""))
        self._row_actions(m, x, hdr, rows, ch, grp)
        m.exec(gpos)

    def _col_actions(self, m: QMenu, c: int, k: int, hdr: list, rows: list, ch: list, grp: list) -> None:
        a0, b0 = grp[k] if grp else (0, len(rows))
        n = len(ch[k]) if k < len(ch) else self.grid.columnCount()
        R = range(a0, b0)

        def setch(new_k: list) -> list:
            c2 = [list(x) for x in ch]
            c2[k] = new_k
            return c2

        def split_col():
            for i in R:
                p = rows[i][c].split(None, 1) if c < len(rows[i]) else []
                rows[i][c:c + 1] = (p + [""])[:2] if p else ["", ""]
            self._commit(hdr, rows, setch(ch[k][:c + 1] + [""] + ch[k][c + 1:]))

        def split_time():  # "0645-0710 Travel to location" -> jam | uraian
            opts = {o["key"] for o in (self.pv or {}).get("options") or []}
            for i in R:
                v = rows[i][c] if c < len(rows[i]) else ""
                mm = re.match(r"^\s*([0-9.:'’]{3,8}\s*[-–]\s*[0-9.:'’]{3,8})\s*(.*)$", v)
                rows[i][c:c + 1] = [mm.group(1), mm.group(2)] if mm else ["", v]
            self._commit(hdr, rows, setch(ch[k][:c] + ["jam" if "jam" in opts else ch[k][c]] + [ch[k][c]] + ch[k][c + 1:]))

        def join_col():
            for i in R:
                rows[i][c] = " ".join(x for x in (rows[i][c], rows[i][c + 1] if c + 1 < len(rows[i]) else "") if x.strip() and x.strip() != "-")
                if c + 1 < len(rows[i]):
                    rows[i].pop(c + 1)
            self._commit(hdr, rows, setch(ch[k][:c + 1] + ch[k][c + 2:]))

        def swap():
            for i in R:
                if c + 1 < len(rows[i]):
                    rows[i][c], rows[i][c + 1] = rows[i][c + 1], rows[i][c]
            c2 = list(ch[k])
            c2[c], c2[c + 1] = c2[c + 1], c2[c]
            self._commit(hdr, rows, setch(c2))

        def ins():
            for i in R:
                rows[i].insert(c, "")
            self._commit(hdr, rows, setch(ch[k][:c] + [""] + ch[k][c:]))

        def drop():
            for i in R:
                if c < len(rows[i]):
                    rows[i].pop(c)
            self._commit(hdr, rows, setch(ch[k][:c] + ch[k][c + 1:]))

        def up_empty():  # semua baris kelompok ini yang kolom ini kosong = lanjutan baris di atasnya (mis. uraian dua baris tanpa jam)
            out, sk, g2, removed = [], set(), [], []
            for i, row in enumerate(rows):
                if a0 < i < b0 and out and not row[c].strip().strip("-").strip() and any(v.strip() not in ("", "-") for v in row):
                    for jj, v in enumerate(row):
                        if v.strip() not in ("", "-"):
                            out[-1][jj] = (out[-1][jj] + " " + v).strip() if out[-1][jj].strip() not in ("", "-") else v
                    removed.append(i)
                    continue
                if i in self.skip:
                    sk.add(len(out))
                out.append(row)
            for a, b in grp:
                g2.append([a - sum(1 for x in removed if x < a), b - sum(1 for x in removed if x < b)])
            self._commit(hdr, out, ch, sk, g2)
        n_up = sum(1 for i in R if i > a0 and c < len(rows[i]) and not rows[i][c].strip().strip("-").strip()
                   and any(v.strip() not in ("", "-") for v in rows[i]))
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

    def _col_menu(self, c: int, gpos, k: int | None = None) -> None:
        if c < 0 or not self.grp:
            return
        if k is None:  # judul kolom: kelompok dari sel yang sedang dipilih
            cur = self.grid.currentRow()
            k = self._kel(self.vmap[cur][1]) if 0 <= cur < len(self.vmap) and self.vmap[cur][0] == "row" else \
                (self.vmap[cur][1] if 0 <= cur < len(self.vmap) else 0)
        hdr, rows, ch, grp = self._ctx()
        m = QMenu(self)
        m.addSection(f"Kolom {c + 1}" + (f" · kelompok {k + 1}" if len(grp) > 1 else ""))
        self._col_actions(m, c, k, hdr, rows, ch, grp)
        m.exec(gpos)

    def _hdr_menu(self, pos) -> None:
        it = self.hdr.itemAt(pos)
        if not it:
            return
        i = it.row()
        hdr, rows, ch, grp = self._ctx()

        def to_row():
            lbl, val = hdr.pop(i)
            w = len(ch[-1]) if ch else 2
            rows.append(([lbl, val] + [""] * w)[:max(w, 2)])
            g2 = [list(x) for x in grp]
            if g2:
                g2[-1][1] += 1
            else:
                g2 = [[0, len(rows)]]
            self._commit(hdr, rows, ch or [["", ""]], None, g2)

        def delete():
            hdr.pop(i)
            self._commit(hdr, rows)
        m = QMenu(self)
        m.addAction("☷ Jadikan baris tabel", to_row)
        m.addAction("✕ Hapus isian kop ini dari teks", delete)
        m.exec(self.hdr.viewport().mapToGlobal(pos))

    def _toggle_skip(self, vr: int) -> None:
        if vr < 0 or not self.pv or vr >= len(getattr(self, "vmap", [])) or self.vmap[vr][0] != "row":
            return
        self._toggle_skip_row(self.vmap[vr][1])

    def _toggle_skip_row(self, r: int) -> None:
        self.skip ^= {r}
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
        gs = self.pv.get("groups") or []
        trs = [x["title_row"] for x in gs if x.get("title_row", -1) >= 0 and x["title_row"] in self.skip]
        body = {**self._body(), "teks": self.txt.toPlainText(), "sep": self.pv.get("sep") or "|", "cols": self._cols(),
                "hdr": self._hdr_keys(), "skip_rows": sorted(self.skip), "save_map": True, "title_row": trs, "groups": self.grp,
                "breaks": self.pv.get("breaks") or None}
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
            n_t = sum(1 for r in j["rows"] if r.get("tbl"))
            self.page.toast(f"Transkrip diterapkan · {len(j['rows']) - n_t} baris" + (f" + {n_t} baris tabel tambahan" if n_t else "")
                            + " — keputusan kolom disimpan untuk borang jenis ini. Periksa sel kuning / merah di tab Data lalu verifikasi", 6000)

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
