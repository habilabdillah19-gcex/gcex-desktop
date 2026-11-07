"""Jendela utama DB-Ex (Qt): bilah atas, filter, tabel foto, pratinjau, kartu, bilah status + progres AI."""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMainWindow,
                               QProgressBar, QPushButton, QSplitter, QStackedWidget, QVBoxLayout, QWidget)

from . import APP_NAME, COPYRIGHT, api, dialogs, lic, shell, theme
from .card import Card, _esc, btn
from .dialogs import ask, say
from .search import SearchBox
from .table import PhotoModel, PhotoTable, fmt
from .util import SET, alive, log, run_bg, show_in_folder
from .viewer import Viewer


def natural_key(s) -> list:
    return [(0, int(t), "") if t.isdigit() else (1, 0, t.lower()) for t in re.split(r"(\d+)", str(s or ""))]


class MainWindow(QMainWindow):
    def __init__(self, version: str, store: lic.Store | None = None):
        super().__init__()
        self.version, self.store = version, store
        self.setWindowTitle(APP_NAME)
        self.resize(1440, 900)
        self.folder = ""
        self.restart_after = False
        self.rows: list[dict] = []
        self.by_id: dict[int, dict] = {}
        self.view: list[dict] = []
        self.meta: dict = {}
        self.dh: dict | None = None
        self.labels: dict[str, str] = {}
        self.cur_id: int | None = None
        self._core_scanned: str | None = None  # folder yang fotonya sudah didaftarkan ke Core box di sesi ini
        self._last_sum: dict = {}
        self.last_done = -1
        self.model = PhotoModel()
        self._build()
        from .layers import Interp
        self.interp = Interp(self)
        self._menu()
        self.ai = dialogs.AiDlg(self)
        self.ai.status.connect(self._ai_pill)
        self.ai.run.connect(lambda scope: self.run_ai(scope))
        self.poll = QTimer(self)
        self.poll.setInterval(1500)
        self.poll.timeout.connect(self.poll_ai)
        # timer milik jendela (bukan QTimer.singleShot lepas): ikut berhenti saat jendela ditutup, sehingga
        # tidak ada callback yang menyentuh widget yang objek C++-nya sudah dihapus.
        self.boot = QTimer(self)
        self.boot.setSingleShot(True)
        self.boot.setInterval(50)
        self.boot.timeout.connect(lambda: (self.ai.check(), self.poll_ai()))
        self.boot.start()

    # ================================================================ tata letak
    def _build(self) -> None:
        cw = QWidget()
        cw.setObjectName("central")
        self.setCentralWidget(cw)
        v = QVBoxLayout(cw)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        # ---- bilah atas
        top = QFrame()
        top.setObjectName("top")
        h = QHBoxLayout(top)
        h.setContentsMargins(14, 8, 14, 9)
        h.setSpacing(8)
        br = QVBoxLayout()
        br.setSpacing(0)
        k = QLabel("DATABASE EXCELLENCE")
        k.setObjectName("kick")
        k.setToolTip("DB-Ex (Database Excellence) · keluarga GC-Ex")
        b = QLabel(f"DB<span style='color:{theme.C['sb']}'>-Ex</span>")
        b.setObjectName("brand")
        b.setTextFormat(Qt.RichText)
        self.prj = QLabel("Core box · Singkapan · Borang · QAQC · 100% offline")
        self.prj.setObjectName("prj")
        self.prj.setMaximumWidth(520)
        for x in (k, b, self.prj):
            br.addWidget(x)
        h.addLayout(br)
        h.addSpacing(18)
        self.topH = h
        h.addStretch(1)
        # ruang kerja: Core box (foto core) | Singkapan (foto singkapan / trenching hasil mapping)
        self.bModeCore = btn("Core box", "Interpretasi foto core box", sm=True)
        self.bModeOc = btn("Singkapan", "Foto singkapan / trenching hasil mapping: deskripsi AI, digitasi, infografis", sm=True)
        self.bModeForm = btn("Borang", "Borang lapangan tulisan tangan (Ore Spotter, RC Drill): AI membaca, Anda periksa, "
                             "ekspor ke Excel / CSV / SQLite / MS Access", sm=True)
        self.bModeQa = btn("QAQC", "QAQC Database: CRM, blank, duplikat per zona / batch lab dan integritas data bor; ekspor Excel, "
                           "grafik PNG dan laporan PDF", sm=True)
        for b_ in (self.bModeCore, self.bModeOc, self.bModeForm, self.bModeQa):
            b_.setCheckable(True)
            b_.setEnabled(False)
            h.addWidget(b_)
        self.bModeCore.setChecked(True)
        self.bModeCore.clicked.connect(lambda: self.set_mode("core"))
        self.bModeOc.clicked.connect(lambda: self.set_mode("oc"))
        self.bModeForm.clicked.connect(lambda: self.set_mode("form"))
        self.bModeQa.clicked.connect(lambda: self.set_mode("qa"))
        h.addSpacing(6)
        self.q = SearchBox()
        self.q.setEnabled(False)
        self.q.picked.connect(self.goto_result)
        h.addWidget(self.q, 2)
        h.addStretch(1)
        self.bOpen = btn("Buka folder", "Buka folder proyek untuk ruang kerja yang sedang aktif (Core box / Singkapan / Borang / QAQC)", pri=True)
        self.bRescan = btn("↻", "Cari foto baru / yang hilang di folder")
        self.bDH = btn("Data bor", "Import Collar, Survey, Assay, Geologi (CSV / Excel) dengan header bebas")
        self.bImport = btn("JSON", "Ambil hasil dari file .json dashboard lama (dicocokkan per nama file foto)")
        self.bExport = btn("Excel", "Simpan log ke Excel")
        self.bAI = btn("Jalankan AI", "Interpretasi foto dengan AI lokal (Ollama)", pri=True)
        self.pill = QPushButton("○  AI lokal: memeriksa…")
        self.pill.setObjectName("pill")
        self.pill.setToolTip("Status AI lokal (Ollama). Klik untuk pengaturan.")
        self.bDark = btn("☾", "Tema gelap / terang")
        for x in (self.bOpen, self.bRescan, self.bDH, self.bImport, self.bExport, self.bAI, self.pill, self.bDark):
            h.addWidget(x)
        v.addWidget(top)
        self.bOpen.clicked.connect(lambda: self.choose_folder())
        self.bRescan.clicked.connect(self.rescan)
        self.bExport.clicked.connect(self.export_xlsx)
        self.bImport.clicked.connect(self.import_json)
        self.bAI.clicked.connect(self.open_ai)
        self.pill.clicked.connect(self.open_ai)
        self.bDark.clicked.connect(self.toggle_dark)
        self.bDH.clicked.connect(self.open_dh)
        # ---- filter
        fb = QFrame()
        self.fbar = fb
        fb.setObjectName("fbar")
        f = QHBoxLayout(fb)
        f.setContentsMargins(14, 6, 14, 6)
        f.setSpacing(8)

        def lab(t):
            l = QLabel(t.upper())
            f.addWidget(l)
            return l

        lab("Hole ID")
        self.fHole = QComboBox()
        self.fHole.setMinimumWidth(130)
        f.addWidget(self.fHole)
        lab("Kedalaman")
        self.fFrom, self.fTo = QLineEdit(), QLineEdit()
        for x, ph in ((self.fFrom, "From"), (self.fTo, "To")):
            x.setPlaceholderText(ph)
            x.setFixedWidth(70)
            f.addWidget(x)
        f.addWidget(QLabel("m"))
        lab("Status")
        self.fStat = QComboBox()
        for d, t in (("", "Semua"), ("pending", "Belum dianalisis AI"), ("done", "Sudah dianalisis AI"), ("error", "AI gagal"),
                     ("unver", "Belum diverifikasi"), ("ver", "Sudah diverifikasi"), ("miss", "File hilang")):
            self.fStat.addItem(t, d)
        f.addWidget(self.fStat)
        self.gW = QWidget()
        g = QHBoxLayout(self.gW)
        g.setContentsMargins(0, 0, 0, 0)
        g.setSpacing(6)
        gl = QLabel("KADAR")
        self.fEl = QComboBox()
        self.fAgg = QComboBox()
        self.fAgg.addItem("rata2", "g")
        self.fAgg.addItem("maks", "gmax")
        self.fAgg.setToolTip("rata-rata tertimbang atau nilai interval tertinggi di foto")
        self.fMin = QLineEdit()
        self.fMin.setPlaceholderText("nilai")
        self.fMin.setFixedWidth(64)
        for x in (gl, self.fEl, self.fAgg, QLabel("≥"), self.fMin):
            g.addWidget(x)
        self.gW.hide()
        f.addWidget(self.gW)
        lab("Saring")
        self.fQ = QLineEdit()
        self.fQ.setPlaceholderText("nama file / catatan…")
        self.fQ.setFixedWidth(170)
        f.addWidget(self.fQ)
        clr = btn("Reset filter", sm=True)
        f.addWidget(clr)
        f.addStretch(1)
        self.cnt = QLabel()
        self.cnt.setObjectName("note")
        f.addWidget(self.cnt)
        v.addWidget(fb)
        fb.hide()  # bilah filter Core box tampil setelah folder dibuka
        self.ft = QTimer(self)
        self.ft.setSingleShot(True)
        self.ft.setInterval(250)
        self.ft.timeout.connect(self.apply_filter)
        for x in (self.fFrom, self.fTo, self.fQ, self.fMin):
            x.textChanged.connect(lambda *_: self.ft.start())
        for x in (self.fHole, self.fStat, self.fEl, self.fAgg):
            x.currentIndexChanged.connect(lambda *_: self.apply_filter())
        clr.clicked.connect(self.reset_filter)
        # ---- isi: mulai / kerja
        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)
        self.stack.addWidget(self._start_page())
        sp = QSplitter(Qt.Horizontal)
        sp.setHandleWidth(5)
        left = QSplitter(Qt.Vertical)
        left.setHandleWidth(5)
        self.viewer = Viewer()
        self.card = Card()
        self.panels = QWidget()  # panel overlay / tanda / kalibrasi (M2)
        self.panels.setLayout(QVBoxLayout())
        self.panels.layout().setContentsMargins(0, 0, 0, 0)
        lw = QWidget()
        lv = QVBoxLayout(lw)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(0)
        from PySide6.QtCore import QSize as _QS
        from PySide6.QtWidgets import QScrollArea, QSizePolicy

        class PanelArea(QScrollArea):  # tinggi mengikuti isi panel, maks. 340 px (sisanya untuk kartu)
            def sizeHint(self):  # noqa: N802
                w = self.widget()
                return _QS(200, min(420, w.sizeHint().height() + 2) if w and w.isVisible() else 0)

            def minimumSizeHint(self):  # noqa: N802
                return self.sizeHint()

        psa = PanelArea()
        psa.setWidgetResizable(True)
        psa.setFrameShape(QFrame.NoFrame)
        psa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        psa.setWidget(self.panels)
        psa.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._psa = psa
        lv.addWidget(psa)
        lv.addWidget(self.card, 1)
        left.addWidget(self.viewer)
        left.addWidget(lw)
        left.setSizes(SET.get("qt_vsplit", [380, 520]))
        left.splitterMoved.connect(lambda *_: SET.set("qt_vsplit", left.sizes()))
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(10, 10, 10, 10)
        rv.setSpacing(7)
        bk = QHBoxLayout()
        self.selInfo = QLabel("0 dipilih")
        self.bSelAll, self.bSelNone = btn("Pilih semua yang tampil", sm=True), btn("Kosongkan", sm=True)
        self.bSelVer, self.bSelUnver = btn("✓ Verifikasi terpilih", sm=True), btn("Batalkan verifikasi", sm=True)
        self.bSelAI = btn("AI untuk terpilih", sm=True)
        self.bSelDel = btn("Keluarkan dari daftar", sm=True)
        self.bSelDel.setToolTip("Keluarkan foto terpilih dari daftar Core box (tombol Delete).\n"
                                "File foto di folder TIDAK dihapus atau dipindah; hanya tidak dipakai di Core box.\n"
                                "Kembalikan lewat File → Kembalikan foto yang dikeluarkan.")
        for x in (self.selInfo, self.bSelAll, self.bSelNone, self.bSelVer, self.bSelUnver, self.bSelAI, self.bSelDel):
            bk.addWidget(x)
        hint = QLabel("↑ ↓ pindah foto · Ctrl+Enter verifikasi & lanjut · Delete keluarkan foto · klik ganda sel untuk mengedit")
        hint.setObjectName("note")
        from PySide6.QtWidgets import QSizePolicy as _SP
        hint.setSizePolicy(_SP.Ignored, _SP.Preferred)
        hint.setMinimumWidth(1)
        bk.addWidget(hint, 1)
        rv.addLayout(bk)
        self.table = PhotoTable(self.model)
        rv.addWidget(self.table, 1)
        sp.addWidget(left)
        sp.addWidget(right)
        sp.setStretchFactor(1, 1)
        sp.setSizes(SET.get("qt_hsplit", [520, 920]))
        sp.splitterMoved.connect(lambda *_: SET.set("qt_hsplit", sp.sizes()))
        self.stack.addWidget(sp)
        from .outcrop import OutcropPage
        self.outcrop = OutcropPage(self)
        self.stack.addWidget(self.outcrop)
        from .forms import FormsPage
        self.forms = FormsPage(self)
        self.stack.addWidget(self.forms)
        self.topH.insertWidget(2, self.forms.nav)  # Borang | Riwayat | Template | Pengaturan | Bantuan (hanya mode Borang)
        self.forms.nav.hide()
        from .qaqc import QaqcPage
        self.qaqc = QaqcPage(self)
        self.stack.addWidget(self.qaqc)
        self.mode = "core"
        self.bSelAll.clicked.connect(lambda: self._sel_all(True))
        self.bSelNone.clicked.connect(lambda: self._sel_all(False))
        self.bSelVer.clicked.connect(lambda: ask(self, f"Verifikasi {len(self.model.sel)} foto terpilih?\n\nVerifikasi berarti Anda sudah memeriksa isiannya.")
                                     and self.verify(list(self.model.sel), True))
        self.bSelUnver.clicked.connect(lambda: self.verify(list(self.model.sel), False))
        self.bSelAI.clicked.connect(lambda: self.run_ai("ids", list(self.model.sel)))
        self.bSelDel.clicked.connect(lambda: self.remove_photos())
        self.model.selChanged.connect(self._sel_changed)
        self.model.edited.connect(self.save_field)
        self.table.rowActivated.connect(self.select)
        self.table.sortRequested.connect(self._sort)
        self.card.edited.connect(self.save_field)
        self.card.verify.connect(lambda pid, v: self.verify([pid], v, nxt=v))
        self.card.analyze.connect(lambda pid: self.run_ai("ids", [pid]))
        self.card.showFile.connect(lambda pid: show_in_folder(Path(self.folder) / self.by_id[pid]["rel"]))
        self.card.nav.connect(lambda d: self.table.go_row(self._cur_index() + d))
        self.card.history.connect(self._history)
        # ---- bilah status
        sb = self.statusBar()
        self.sSum = QLabel("Belum ada proyek.")
        sb.addWidget(self.sSum, 1)
        self.pTxt = QLabel()
        self.pBar = QProgressBar()
        self.pBar.setFixedWidth(160)
        self.pBar.setTextVisible(False)
        self.pStop = btn("■ Hentikan", sm=True)
        self.pStop.clicked.connect(self.stop_ai)
        for x in (self.pTxt, self.pBar, self.pStop):
            sb.addPermanentWidget(x)
            x.hide()
        self.sBe = QLabel(f"Mesin lokal {self.version} · offline")
        sb.addPermanentWidget(self.sBe)
        self.wmark = QLabel(COPYRIGHT)
        self.wmark.setObjectName("wmark")
        self.wmark.setToolTip("DB-Ex (Database Excellence) · keluarga GC-Ex")
        sb.addPermanentWidget(self.wmark)
        self.toastL = QLabel(self)
        self.toastL.setStyleSheet(f"background:{theme.C['ink']};color:{theme.C['pn']};padding:8px 14px;border-radius:5px")
        self.toastL.hide()
        self.toastT = QTimer(self)
        self.toastT.setSingleShot(True)
        self.toastT.timeout.connect(self.toastL.hide)
        for b_ in (self.bRescan, self.bDH, self.bImport, self.bExport, self.bAI):
            b_.setEnabled(False)
        self._sel_changed()
        QShortcut(QKeySequence("Ctrl+K"), self, activated=lambda: (self.q.setFocus(), self.q.selectAll()) if self.q.isEnabled() else None)
        dk = QShortcut(QKeySequence.Delete, self.table, activated=lambda: self.remove_photos())
        dk.setContext(Qt.WidgetShortcut)  # hanya saat tabel fokus; editor sel tetap memakai Delete biasa
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.verify_current)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.verify_current)
        QShortcut(QKeySequence("Escape"), self, activated=lambda: self.outcrop.escape() if self.mode == "oc" else (self.forms.escape() if self.mode == "form"
                                                                                                        else self.interp.escape()))

    # ruang kerja DB-Ex: (mode, judul, isi kartu halaman depan, tombol, judul dialog pilih folder)
    MODES = (
        ("core", "Core box",
         "Foto core box per lubang bor. AI membaca papan label (Hole ID, box, kedalaman) dan menilai recovery, RQD, GSI, RMR; "
         "geologist melengkapi logging, memverifikasi, lalu ekspor Excel.",
         "Buka folder foto core box", "Pilih folder foto core box (boleh bersubfolder per lubang bor)"),
        ("oc", "Singkapan & Model 3D",
         "Foto singkapan, trenching, dinding / lantai bench dari iPhone atau drone DJI. Deskripsi AI, digitasi kontak, vein &amp; struktur, "
         "strike / dip, Model 3D sampai 100 foto, ekspor Surpac / DXF dan infografis.",
         "Buka folder singkapan", "Pilih folder proyek singkapan (foto singkapan / drone)"),
        ("form", "Borang lapangan",
         "Foto / scan / PDF borang tulisan tangan (Ore Spotter, Ore ke ROM, RC Daily Drilling, RC Drill / Chiptray Log). "
         "AI membaca, Anda periksa; ekspor Excel, CSV, SQLite, MS Access.",
         "Buka folder borang", "Pilih folder proyek borang lapangan"),
        ("qa", "QAQC Database",
         "CRM, blank dan duplikat per zona / batch lab, plus integritas data bor (collar, survey, assay). "
         "Dashboard, ekspor Excel, grafik PNG dan laporan PDF.",
         "Buka folder QAQC", "Pilih folder proyek QAQC"),
    )
    MODE_NAME = {m[0]: m[1] for m in MODES}

    def _start_page(self) -> QWidget:
        from PySide6.QtWidgets import QGridLayout, QScrollArea
        sa = QScrollArea()
        sa.setObjectName("start")
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        w = QWidget()
        w.setObjectName("start")
        sa.setWidget(w)
        o = QVBoxLayout(w)
        o.setAlignment(Qt.AlignCenter)
        c = QFrame()
        c.setObjectName("startCard")
        c.setMaximumWidth(940)
        from PySide6.QtWidgets import QSizePolicy
        c.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)  # kartu modul setinggi isinya, tidak ditarik memenuhi layar
        v = QVBoxLayout(c)
        v.setContentsMargins(28, 22, 28, 24)
        v.setSpacing(12)
        k = QLabel("DATABASE EXCELLENCE · DATA GEOLOGI GRADE CONTROL")
        k.setObjectName("kick")
        hd = QLabel(f"Data geologi diolah di komputer ini, <span style='color:{theme.C['sb']}'>bukan di cloud.</span>")
        hd.setObjectName("startH")
        hd.setWordWrap(True)
        hd.setTextFormat(Qt.RichText)
        p = QLabel("DB-Ex mengelola foto dan data lapangan geologist: foto core box, foto singkapan / dinding pit (iPhone atau drone), "
                   "borang tulisan tangan dan QAQC data assay. AI lokal (Ollama) membantu membaca dan mendeskripsikan; geologist memeriksa, "
                   "memverifikasi, lalu mengekspor ke Excel, Surpac atau laporan PDF. Pilih ruang kerja di bawah, lalu buka foldernya.")
        p.setWordWrap(True)
        g = QGridLayout()
        g.setSpacing(10)
        self.startBtns = {}
        for i, (m, t, d, bt, _dt_) in enumerate(self.MODES):
            f = QFrame()
            f.setObjectName("modCard")
            fv = QVBoxLayout(f)
            fv.setContentsMargins(14, 12, 14, 12)
            fv.setSpacing(8)
            ht = QLabel(f"<b>{t}</b>")
            ht.setObjectName("modH")
            dd = QLabel(d)
            dd.setWordWrap(True)
            dd.setTextFormat(Qt.RichText)
            dd.setObjectName("note")
            b = btn(bt, pri=True)
            b.clicked.connect(lambda _=False, m=m: self.choose_folder(m))
            self.startBtns[m] = b
            fv.addWidget(ht)
            fv.addWidget(dd)
            fv.addStretch(1)
            fv.addWidget(b, 0, Qt.AlignLeft)
            g.addWidget(f, i // 2, i % 2)
        tip = dialogs.box("Hasil kerja disimpan di subfolder <code>_GCEx_Core</code> di folder yang dibuka, jadi rekan yang membuka folder yang sama "
                          "bisa melanjutkan. Satu folder proyek boleh dipakai untuk beberapa ruang kerja; pindah lewat tombol "
                          "<b>Core box · Singkapan · Borang · QAQC</b> di bilah atas.")
        self.recentW = QVBoxLayout()
        self.sAi = dialogs.box("Memeriksa AI lokal…")
        for x in (k, hd, p):
            v.addWidget(x)
        v.addLayout(g)
        v.addWidget(tip)
        v.addLayout(self.recentW)
        v.addWidget(self.sAi)
        o.addWidget(c)
        self._recent()
        return sa

    def _recent(self) -> None:
        while self.recentW.count():
            x = self.recentW.takeAt(0).widget()
            if x:
                x.hide()
                x.setParent(None)
                x.deleteLater()
        rec = SET.get("recent", [])
        fm = SET.get("folder_mode", {}) or {}
        if rec:
            t = QLabel("<b>Folder terakhir</b>")
            self.recentW.addWidget(t)
        for f in rec:
            m = fm.get(f.lower())
            b = QPushButton(f"{Path(f).name}    {f}" + (f"    · {self.MODE_NAME[m]}".replace("&", "&&") if m in self.MODE_NAME else ""))
            b.setStyleSheet("text-align:left;border:0;border-bottom:1px dashed " + theme.C["bd2"])
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, f=f, m=m: self.open_folder(f, m))
            self.recentW.addWidget(b)

    def _menu(self) -> None:
        mb = self.menuBar()
        m = mb.addMenu("&File")
        for t, fn, sc in (("Buka folder…", lambda: self.choose_folder(), "Ctrl+O"), ("Pindai ulang", self.rescan, "F5"),
                          ("Export Excel…", self.export_xlsx, "Ctrl+S")):
            a = QAction(t, self)
            a.setShortcut(QKeySequence(sc))
            a.triggered.connect(fn)
            m.addAction(a)
            if sc == "Ctrl+O":
                om = m.addMenu("Buka folder untuk")
                for md, mt, *_r in self.MODES:
                    om.addAction(mt + "…", lambda md=md: self.choose_folder(md))
        m.addAction("Kembalikan foto yang dikeluarkan dari daftar…", self.restore_photos)
        a = QAction("Ekspor infografis foto (PNG / PDF)…", self)
        a.setShortcut(QKeySequence("Ctrl+E"))
        a.triggered.connect(lambda: self.outcrop.export("png") if self.mode == "oc" else self.interp.export_infographic())
        m.addAction(a)
        m.addSeparator()
        m.addAction("Keluar", self.close)
        v = mb.addMenu("&Tampilan")
        zm = v.addMenu("Ukuran tampilan")
        from PySide6.QtGui import QActionGroup
        self.zoomGrp = QActionGroup(self)
        for z in shell.ZOOMS:
            a = QAction(f"{round(z * 100)}%" + (" (bawaan)" if z == shell.ZOOM_DEF else ""), self, checkable=True)
            a.setChecked(abs(z - shell.zoom_now()) < 1e-3)
            a.triggered.connect(lambda _=False, z=z: self.set_zoom(z))
            self.zoomGrp.addAction(a)
            zm.addAction(a)
        for t, sc, fn in (("Perbesar", ("Ctrl+=", "Ctrl++"), lambda: self.set_zoom(shell.zoom_step(+1))),
                          ("Perkecil", ("Ctrl+-",), lambda: self.set_zoom(shell.zoom_step(-1))),
                          (f"Ukuran bawaan ({round(shell.ZOOM_DEF * 100)}%)", ("Ctrl+0",), lambda: self.set_zoom(shell.ZOOM_DEF))):
            a = QAction(t, self)
            a.setShortcuts([QKeySequence(x) for x in sc])
            a.triggered.connect(fn)
            v.addAction(a)
        v.addSeparator()
        self.aFull = QAction("Layar penuh", self, checkable=True)
        self.aFull.setShortcut(QKeySequence("F11"))
        self.aFull.triggered.connect(self.toggle_full)
        v.addAction(self.aFull)
        v.addSeparator()
        v.addAction("Tema gelap / terang", self.toggle_dark)
        v.addAction("Ganti nama pengguna…", lambda: self.user(True))
        h = mb.addMenu("&Bantuan")
        from .util import open_path, res_dir, user_dir
        guide = lambda: open_path(res_dir("docs") / "PANDUAN_CORE.html") if (res_dir("docs") / "PANDUAN_CORE.html").exists() else open_path(res_dir("docs"))  # noqa: E731
        h.addAction("Panduan DB-Ex", guide)
        h.addAction("Panduan AI lokal (Ollama)", guide)  # dirujuk pesan dialog AI: "Bantuan → Panduan AI lokal"
        h.addAction("Buka folder log", lambda: open_path(user_dir() / "logs"))
        h.addSeparator()
        h.addAction("Syarat penggunaan & penafian", lambda: open_path(res_dir("legal") / "SYARAT_PENGGUNAAN.txt"))
        h.addAction("Lisensi pihak ketiga (open source) & merek dagang", lambda: open_path(res_dir("legal")))
        if self.store:
            h.addAction("Lisensi GC-Ex…", lambda: dialogs.LicenseDlg(self, self.store, "info").exec())
        h.addAction("Tentang DB-Ex", lambda: dialogs.about(self, self.store, self.version))

    # ================================================================ util
    def toast(self, m: str, ms: int = 2600) -> None:
        self.toastL.setText(m)
        self.toastL.adjustSize()
        self.toastL.move((self.width() - self.toastL.width()) // 2, self.height() - self.toastL.height() - 46)
        self.toastL.show()
        self.toastL.raise_()
        self.toastT.start(ms)

    def user(self, force: bool = False) -> str:
        u = SET.get("user", "")
        if not u or force:
            t, ok = QInputDialog.getText(self, APP_NAME, "Nama Anda (dicatat pada editan & verifikasi):", text=u)
            u = (t.strip() if ok else u) or u or "Geologist"
            SET.set("user", u)
        return u

    def _cur_index(self) -> int:
        return next((i for i, r in enumerate(self.view) if r["id"] == self.cur_id), -1)

    def set_mode(self, mode: str) -> None:
        """Pindah ruang kerja Core box / Singkapan / Borang (folder proyek sama)."""
        self.mode = mode
        self.bModeCore.setChecked(mode == "core")
        self.bModeOc.setChecked(mode == "oc")
        self.bModeForm.setChecked(mode == "form")
        self.bModeQa.setChecked(mode == "qa")
        self.forms.nav.setVisible(mode == "form" and bool(self.folder))
        if not self.folder:
            return
        oc = mode != "core"
        self.fbar.setVisible(not oc)
        for b_ in (self.bRescan, self.bDH, self.bImport, self.bExport, self.bAI, self.q):
            b_.setVisible(not oc)
        if mode == "oc":
            if self.outcrop.folder != self.folder:
                self.outcrop.open(self.folder)
            self.stack.setCurrentWidget(self.outcrop)
        elif mode == "form":
            if self.forms.folder != self.folder:
                self.forms.open(self.folder)
            self.stack.setCurrentWidget(self.forms)
        elif mode == "qa":
            if self.qaqc.folder != self.folder:
                self.qaqc.open(self.folder)
            self.stack.setCurrentWidget(self.qaqc)
        else:
            self.stack.setCurrentIndex(1)
            if self._core_scanned != self.folder:
                QTimer.singleShot(0, self._core_first_scan)
        SET.set("qt_mode", mode)
        fm = dict(SET.get("folder_mode", {}) or {})
        fm[self.folder.lower()] = mode
        SET.set("folder_mode", dict(list(fm.items())[-30:]))

    def set_zoom(self, z: float) -> None:
        """Tampilan > Ukuran tampilan: skala seluruh antarmuka (Qt menetapkannya saat aplikasi mulai -> buka ulang)."""
        old = shell.zoom_now()
        for a in self.zoomGrp.actions():
            a.setChecked(a.text().startswith(f"{round(z * 100)}%"))
        if abs(z - old) < 1e-3:
            return
        SET.set("qt_zoom", z)
        log("[tampilan] ukuran", z)
        busy = self.poll.isActive()
        if ask(self, f"Ukuran tampilan {round(z * 100)}% dipakai setelah DB-Ex dibuka ulang.\n\nBuka ulang sekarang?"
               + (" Folder yang sedang dibuka akan dibuka lagi." if self.folder else "")
               + ("\n\nAI sedang berjalan dan akan berhenti; foto yang belum selesai bisa dianalisis lagi nanti." if busy else "")):
            self.restart_after = True
            self.close()
        else:
            self.toast(f"Ukuran tampilan {round(z * 100)}% dipakai saat DB-Ex dibuka berikutnya", 4000)

    def toggle_full(self) -> None:
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()
        self.aFull.setChecked(self.isFullScreen())

    def from_instance(self, msg: dict) -> None:
        """DB-Ex dibuka lagi saat sudah berjalan: tampilkan jendela ini, buka folder yang diminta."""
        if self.isMinimized():
            self.showMaximized()
        self.raise_()
        self.activateWindow()
        f = (msg or {}).get("folder") or ""
        if f and Path(f).is_dir() and Path(f).resolve() != (Path(self.folder).resolve() if self.folder else None):
            self.open_folder(f)

    def toggle_dark(self) -> None:
        d = not SET.get("dark", False)
        SET.set("dark", d)
        theme.apply(QApplication.instance(), d)
        self.viewer.setBackgroundBrush(Qt.black if d else Qt.black)
        self.model.refresh_all()

    # ================================================================ proyek
    def choose_folder(self, mode: str | None = None) -> None:
        """Buka folder untuk ruang kerja `mode` (core / oc / form / qa); tanpa mode = ruang kerja yang sedang aktif."""
        mode = mode if mode in self.MODE_NAME else self.mode
        title = next(x[4] for x in self.MODES if x[0] == mode)
        f = QFileDialog.getExistingDirectory(self, title, (SET.get("recent") or [""])[0])
        if f:
            self.open_folder(f, mode)

    def open_folder(self, folder: str, mode: str | None = None) -> None:
        if mode in self.MODE_NAME:
            self.mode = mode
        self.sSum.setText("Membuka folder & memindai foto…")
        by = self.user()
        run_bg(api.call, "/core/open", {"folder": folder, "by": by, "scan": self.mode == "core"}, ok=self._opened,
               err=lambda e: (self.sSum.setText("Gagal membuka folder."), say(self, "Gagal membuka folder:\n" + e, warn=True)))

    def _opened(self, j: dict) -> None:
        self.folder, self.meta = j["folder"], j.get("meta") or {}
        self._core_scanned = None if j["scan"].get("skipped") else self.folder
        self.labels = {f["key"]: f["label"] for f in j["fields"]}
        self.card.set_labels(self.labels)
        rec = [j["folder"]] + [x for x in SET.get("recent", []) if x.lower() != j["folder"].lower()]
        SET.set("recent", rec[:8])
        self._recent()
        self.prj.setText(j["folder"])
        self.setWindowTitle(f"{APP_NAME} — {Path(j['folder']).name}")
        for b_ in (self.bRescan, self.bDH, self.bImport, self.bExport, self.bAI, self.q, self.bModeCore, self.bModeOc, self.bModeForm, self.bModeQa):
            b_.setEnabled(True)
        self.outcrop.folder = ""
        self.forms.folder = ""
        self.qaqc.folder = ""
        self.set_mode(self.mode)
        self.q.folder = self.folder
        self.model.thumbs.reset(self.folder)
        self.model.sel.clear()
        self.cur_id = None
        self.ai.load_meta(self.meta)
        self.interp.ov.layers = None
        sc = j["scan"]
        self.load_rows(first=True)
        if self.mode == "core":
            self.toast(f"{sc['total']} foto" + (f" · {sc['added']} baru" if sc["added"] else "") + (f" · {sc['missing']} hilang" if sc["missing"] else ""), 3500)
        else:
            self.toast(f"Ruang kerja {self.MODE_NAME[self.mode]} · {Path(j['folder']).name}", 3000)
        if j.get("db_local"):
            say(self, "Folder ini tidak bisa ditulisi (mis. folder hanya-baca).\n\nHasil kerja disimpan di komputer ini saja:\n" + j["db"]
                + "\n\nRekan di komputer lain tidak akan melihat hasil ini. Salin folder foto ke lokasi yang bisa ditulisi bila ingin dikerjakan bersama.")
        log("[proyek] dibuka", j["folder"])

    def load_rows(self, first: bool = False, then=None) -> None:
        folder = self.folder
        self._rows_seq = seq = getattr(self, "_rows_seq", 0) + 1
        if getattr(self, "_rows_folder", None) != folder:
            self._rows_folder, self._rows_first, self._rows_then = folder, False, []
        self._rows_first = self._rows_first or first
        if then:
            self._rows_then.append(then)

        def ok(j):
            if folder != self.folder or seq != self._rows_seq:
                return  # jawaban lama tidak menimpa daftar yang lebih baru; first/then ikut jawaban terbaru
            first_, thens = self._rows_first, self._rows_then
            self._rows_first, self._rows_then = False, []
            self.rows = j["rows"]
            self.by_id = {r["id"]: r for r in self.rows}
            self.dh = j.get("dh") or self.dh
            self._dh_cols()
            self.interp.dh_changed()
            self._holes()
            self.apply_filter(keep=True)
            self.show_summary(j["summary"])
            if first_ and self.view:
                self.table.go_row(0)
            elif self.cur_id in self.by_id:
                self.card.show_row(self.by_id[self.cur_id])
                self.interp.row_changed(self.by_id[self.cur_id])
            for t in thens:
                t()

        run_bg(api.call, "/core/rows", {"folder": folder}, ok=ok, err=lambda e: say(self, e, warn=True))

    def show_summary(self, s: dict) -> None:
        self._last_sum = s
        self.sSum.setText(f"{s['total']} foto · {s['holes']} lubang · AI selesai {s['done']} · gagal {s['error']} · diverifikasi {s['verified']}"
                          + (f" · {s['missing']} file hilang" if s.get("missing") else "")
                          + (f" · {s['ignored']} dikeluarkan" if s.get("ignored") else ""))
        self.ai.set_pending(sum(1 for r in self.rows if not r.get("missing") and not r.get("verified") and r.get("status") != "done"))

    def _holes(self) -> None:
        cur = self.fHole.currentData()
        holes = sorted({r["hole_id"] for r in self.rows if r.get("hole_id")}, key=natural_key)
        self.fHole.blockSignals(True)
        self.fHole.clear()
        self.fHole.addItem(f"Semua ({len(holes)})", "")
        for x in holes:
            self.fHole.addItem(x, x)
        i = self.fHole.findData(cur) if cur else 0
        self.fHole.setCurrentIndex(max(i, 0))
        self.fHole.blockSignals(False)

    def _dh_cols(self) -> None:
        nc = [c["name"] for c in ((self.dh or {}).get("columns") or {}).get("assay", []) if c.get("type") == "n"]
        self.gW.setVisible(bool(nc))
        cur = self.fEl.currentData()
        self.fEl.blockSignals(True)
        self.fEl.clear()
        self.fEl.addItem("(tidak)", "")
        for n in nc:
            self.fEl.addItem(n, n)
        want = cur if cur in nc else next((n for n in nc if n.lower().startswith("au")), "")
        self.fEl.setCurrentIndex(max(0, self.fEl.findData(want)))
        self.fEl.blockSignals(False)

    def grade_classes(self, el: str) -> list[float]:
        return self.interp.ov.grade_classes(el)

    # ================================================================ filter & urutan
    def reset_filter(self) -> None:
        for w in (self.fFrom, self.fTo, self.fQ, self.fMin):
            w.blockSignals(True)
            w.clear()
            w.blockSignals(False)
        for c in (self.fHole, self.fStat):
            c.blockSignals(True)
            c.setCurrentIndex(0)
            c.blockSignals(False)
        self.model.sort = None
        self.apply_filter()

    def _num(self, w: QLineEdit):
        try:
            return float(w.text().replace(",", "."))
        except ValueError:
            return None

    def apply_filter(self, keep: bool = False) -> None:
        h, st, q = self.fHole.currentData() or "", self.fStat.currentData() or "", self.fQ.text().strip().lower()
        fa, fb, gmin = self._num(self.fFrom), self._num(self.fTo), self._num(self.fMin)
        el, agg = self.fEl.currentData() or "", self.fAgg.currentData() or "g"
        out = []
        for r in self.rows:
            if h and r.get("hole_id") != h:
                continue
            if fa is not None and not (r.get("to_m") is None or r["to_m"] >= fa):
                continue
            if fb is not None and not (r.get("from_m") is None or r["from_m"] <= fb):
                continue
            if st == "miss":
                if not r.get("missing"):
                    continue
            elif st and r.get("missing"):
                continue
            if st in ("pending", "done", "error") and r.get("status") != st:
                continue
            if st == "unver" and r.get("verified"):
                continue
            if st == "ver" and not r.get("verified"):
                continue
            if q:
                hay = " ".join(str(x) for x in (r["rel"], r.get("notes") or "", r.get("lithology") or "", r.get("alteration") or "",
                                                  *(r.get("log") or {}).values())).lower()
                if q not in hay:
                    continue
            if el and gmin is not None:
                v = (r.get(agg) or {}).get(el)
                if v is None or v < gmin:
                    continue
            out.append(r)
        s = self.model.sort
        if s:
            k, d = s

            def val(o):
                if k == "_g":
                    return (o.get("g") or {}).get(el)
                lg = (o.get("log") or {}).get(k)
                return lg if lg is not None else o.get(k)

            have = [r for r in out if val(r) is not None]
            none = [r for r in out if val(r) is None]
            have.sort(key=lambda r: (0, val(r), "") if isinstance(val(r), (int, float)) else (1, 0, natural_key(val(r))), reverse=d < 0)
            out = have + none
        elif h:
            out.sort(key=lambda r: (r.get("from_m") is None, r.get("from_m") or 0, natural_key(r["rel"])))
        self.view = out
        self.model.grade_el = el
        self.model.grade_cls = self.grade_classes(el) if el else []
        self.model.cur_id = self.cur_id
        self.model.set_view(out)
        self.cnt.setText(f"{len(out)} dari {len(self.rows)} foto")
        i = self._cur_index()
        if i >= 0:
            self.table.blockSignals(True)
            self.table.setCurrentIndex(self.model.index(i, 1))
            self.table.blockSignals(False)
            if not keep:
                self.table.scrollTo(self.model.index(i, 1))
        elif out and (fa is not None or fb is not None or h):
            self.table.go_row(0)

    def _sort(self, k: str) -> None:
        s = self.model.sort
        if k == "_no":
            self.model.sort = None
        else:
            self.model.sort = (k, -1) if s and s[0] == k and s[1] > 0 else (None if s and s[0] == k else (k, 1))
        self.apply_filter(keep=True)

    # ================================================================ pilih foto
    def select(self, i: int) -> None:
        if not 0 <= i < len(self.view):
            return
        r = self.view[i]
        prev = self.cur_id
        self.cur_id = r["id"]
        self.model.cur_id = r["id"]
        if prev is not None:
            self.model.refresh_row(prev)
        self.model.refresh_row(r["id"])
        self.card.show_row(r)
        if prev != r["id"]:
            self.viewer.show_photo(self.folder, r)
            self.on_photo(r)

    def on_photo(self, r: dict) -> None:
        self.interp.load(r)

    def on_grade_cls(self) -> None:
        el = self.model.grade_el
        self.model.grade_cls = self.interp.ov.grade_classes(el) if el else []
        self.model.refresh_all()

    def _sel_all(self, on: bool) -> None:
        for r in self.view:
            (self.model.sel.add if on else self.model.sel.discard)(r["id"])
        self.model.refresh_all()
        self._sel_changed()

    def _sel_changed(self) -> None:
        n = len(self.model.sel)
        self.selInfo.setText(f"{n} dipilih")
        for b_ in (self.bSelVer, self.bSelUnver, self.bSelAI, self.bSelDel):
            b_.setEnabled(bool(n))

    # ================================================================ simpan & verifikasi
    def save_field(self, pid: int, k: str, val) -> None:
        r = self.by_id.get(pid)
        if not r:
            return
        try:
            j = api.call("/core/update", {"folder": self.folder, "id": pid, "values": {k: val}, "by": self.user()})
        except api.ApiError as e:
            say(self, f"Gagal menyimpan {self.labels.get(k, k)}:\n{e}", warn=True)
            if pid == self.cur_id:
                self.card.show_row(r)
            return
        log_ = r.get("log")
        r.update(j["row"])
        if log_ is not None and "log" not in j["row"]:
            r["log"] = log_
        if k in ("hole_id", "from_m", "to_m") and self.dh and (self.dh.get("assay") or self.dh.get("geology")):
            self.load_rows()
        else:
            if k == "hole_id":
                self._holes()
            self.model.refresh_row(pid)
            if pid == self.cur_id:
                self.card.show_row(r)
        if pid == self.cur_id:
            if k in ("hole_id", "from_m", "to_m"):
                self.interp.load(r)
            else:
                self.interp.row_changed(r)

    def verify(self, ids: list[int], value: bool, nxt: bool = False) -> None:
        if not ids:
            return
        QApplication.focusWidget() and QApplication.focusWidget().clearFocus()
        try:
            j = api.call("/core/verify", {"folder": self.folder, "ids": ids, "value": value, "by": self.user()})
        except api.ApiError as e:
            say(self, "Gagal verifikasi:\n" + str(e), warn=True)
            return
        now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i in ids:
            r = self.by_id.get(i)
            if r:
                r.update(verified=1 if value else 0, verified_by=self.user() if value else None, verified_at=now if value else None)
        self.show_summary(j["summary"])
        self.model.refresh_all()
        if self.cur_id in self.by_id:
            self.card.show_row(self.by_id[self.cur_id])
        if nxt:
            i = self._cur_index()
            if 0 <= i < len(self.view) - 1:
                self.table.go_row(i + 1)

    def verify_current(self) -> None:
        if self.mode == "form":
            self.forms.verify_next()
            return
        if self.cur_id is not None and self.folder:
            w = QApplication.focusWidget()
            if w:
                w.clearFocus()  # simpan isian yang sedang diketik dulu
            QTimer.singleShot(0, self, lambda: self.verify([self.cur_id], True, nxt=True))

    def _history(self, pid: int) -> None:
        run_bg(api.call, "/core/history", {"folder": self.folder, "id": pid, "values": {}}, ok=lambda j: self.card.set_history(pid, j),
               err=lambda e: self.card.hTxt.setText(_esc(e)))

    # ================================================================ AI
    def _ai_pill(self, s: dict) -> None:
        if not alive(self.pill):  # hasil cek AI datang setelah jendela ditutup
            return
        dot = "◌" if s.get("wait") else ("●" if s.get("ok") else "○")
        self.pill.setText(f"{dot}  {s.get('text', '')}")
        col = theme.C["ac"] if s.get("ok") else theme.C["er"] if s.get("ok") is False else theme.C["mu"]
        self.pill.setStyleSheet(f"QPushButton#pill{{color:{theme.C['ink']}}}")
        self.pill.setToolTip("Status AI lokal (Ollama). Klik untuk pengaturan.")
        self.sAi.setText(self.ai.state.text())
        self.sAi.setProperty("k", self.ai.state.property("k"))
        theme.repolish(self.sAi)
        self.pill.setProperty("dot", col)

    def open_ai(self) -> None:
        self.ai.load_meta(self.meta)
        self.ai.check()
        self.ai.show()
        self.ai.raise_()

    def run_ai(self, scope: str, ids: list[int] | None = None) -> None:
        if not self.folder:
            return
        model = self.ai.model()
        if not self.ai.info or not self.ai.info.get("running") or not model:
            self.open_ai()
            return
        if scope == "ids":
            ids = [i for i in ids or [] if self.by_id.get(i) and not self.by_id[i].get("verified") and not self.by_id[i].get("missing")]
            if not ids:
                say(self, "Foto terpilih sudah diverifikasi / hilang. Batalkan verifikasi dulu bila ingin dianalisis ulang.")
                return
        if scope == "all" and not ask(self, "Analisis ulang SEMUA foto yang belum diverifikasi?\n\nIsian yang sudah Anda edit tetap tidak ditimpa."):
            return
        SET.set("model", model)
        body = {"folder": self.folder, "scope": scope, "ids": ids or [], "host": self.ai.host.text().strip(), "model": model,
                "extra": self.ai.extra.toPlainText(), "max_px": int(self.ai.px.currentData()), "by": self.user()}
        try:
            j = api.call("/core/ai/start", body)
        except api.ApiError as e:
            say(self, str(e))
            return
        self.meta.update(ai_model=model, ai_host=body["host"], ai_extra=body["extra"], ai_max_px=body["max_px"])
        self.ai.hide()
        self.toast(f"AI lokal mulai: {j['job']['total']} foto")
        self.last_done = -2
        self.poll_ai()

    def poll_ai(self) -> None:
        if not alive(self.pBar):
            return
        try:
            j = api.call("/core/ai/status")["job"]
        except api.ApiError:
            return
        on = bool(j.get("running"))
        for x in (self.pTxt, self.pBar, self.pStop):
            x.setVisible(on)
        self.bAI.setEnabled(not on and bool(self.folder))
        if on:
            if not self.poll.isActive():
                self.poll.start()
            k = j.get("done", 0) + j.get("failed", 0)
            self.pBar.setMaximum(max(1, j.get("total", 1)))
            self.pBar.setValue(k)
            eta = j.get("eta_secs")
            eta = f" · sisa ±{round(eta / 60)} menit" if eta and eta > 90 else (f" · sisa ±{eta} detik" if eta is not None else "")
            self.pTxt.setText(f"AI {k}/{j.get('total')}" + (f" ({j['failed']} gagal)" if j.get("failed") else "") + eta + f" · {j.get('current') or ''}")
            if k != self.last_done:
                self.last_done = k
                self.refresh_quiet()
        else:
            self.poll.stop()
            if self.last_done != -1:
                self.last_done = -1
                self.refresh_quiet()
                if j.get("total"):
                    self.toast(f"AI {j.get('message', '')}: {j.get('done', 0)} berhasil" + (f", {j['failed']} gagal (lihat status \"AI gagal\")" if j.get("failed") else ""), 6000)

    def refresh_quiet(self) -> None:
        if not self.folder:
            return
        fw = QApplication.focusWidget()
        if isinstance(fw, QLineEdit) and fw is not self.q and fw.parent() is not None and not fw.isReadOnly() and fw not in (self.fFrom, self.fTo, self.fQ, self.fMin):
            return  # jangan ganggu yang sedang mengetik
        self.load_rows()

    def stop_ai(self) -> None:
        if ask(self, "Hentikan AI setelah foto yang sedang dianalisis?"):
            api.call("/core/ai/cancel")
            self.toast("AI akan berhenti setelah foto ini")

    def remove_photos(self, ids: list[int] | None = None) -> None:
        """Keluarkan foto dari daftar Core box. Tanpa ids: foto yang dicentang, atau foto yang sedang dibuka
        bila tidak ada yang dicentang. File foto di folder tidak disentuh."""
        if not self.folder or self.mode != "core":
            return
        if ids is None:
            ids = list(self.model.sel) or ([self.cur_id] if self.cur_id in self.by_id else [])
        ids = [i for i in ids if i in self.by_id]
        if not ids:
            return
        nm = self.by_id[ids[0]]["rel"] if len(ids) == 1 else f"{len(ids)} foto"
        nver = sum(1 for i in ids if self.by_id[i].get("verified"))
        if not ask(self, f"Keluarkan {nm} dari daftar Core box?\n\n"
                         "• File foto di folder TIDAK dihapus dan tidak dipindah.\n"
                         "• Isian, segmen, dan tanda foto tersebut dihapus dari database Core box.\n"
                         + (f"• {nver} di antaranya sudah diverifikasi.\n" if nver else "")
                         + "\nBisa dikembalikan lewat File → Kembalikan foto yang dikeluarkan."):
            return
        try:
            j = api.call("/core/remove", {"folder": self.folder, "ids": ids, "by": self.user()})
        except api.ApiError as e:
            say(self, f"Gagal mengeluarkan foto:\n{e}", warn=True)
            return
        for i in ids:
            self.model.sel.discard(i)
        idx = self._cur_index()
        lost = self.cur_id in ids

        def after():
            self._sel_changed()
            if not lost:
                return
            self.cur_id = None
            if self.view:
                self.table.go_row(max(0, min(idx, len(self.view) - 1)))
            else:
                self.viewer.placeholder("Tidak ada foto core box.")
                self.card.clear()
        self.load_rows(then=after)
        self.toast(f"{j.get('removed', 0)} foto dikeluarkan dari daftar (file tetap di folder)", 5000)

    def restore_photos(self) -> None:
        if not self.folder:
            return
        n = (self._last_sum or {}).get("ignored", 0)
        if not n:
            say(self, "Tidak ada foto yang pernah dikeluarkan dari daftar di folder ini.")
            return
        if not ask(self, f"Kembalikan {n} foto yang pernah dikeluarkan ke daftar Core box?\n\nFoto masuk sebagai foto baru (isian lamanya sudah terhapus)."):
            return
        try:
            j = api.call("/core/restore", {"folder": self.folder})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self._core_scanned = self.folder
        if self.mode != "core":
            self.set_mode("core")
        self.load_rows()
        self.toast(f"{j['scan']['added']} foto dikembalikan ke daftar", 4000)

    def _core_first_scan(self) -> None:
        """Folder dibuka untuk ruang kerja lain lalu pindah ke Core box: foto baru didaftarkan sebagai foto
        core box hanya bila folder ini memang sudah dipakai Core box, atau setelah pengguna setuju."""
        if not self.folder or self.mode != "core" or self._core_scanned == self.folder:
            return
        self._core_scanned = self.folder
        if self.rows:
            self.rescan()
        elif ask(self, f"Folder {Path(self.folder).name} belum dipakai di Core box.\n\n"
                       "Daftarkan foto di folder ini sebagai foto core box?\n\n"
                       "Pilih Batal bila folder ini untuk Borang / Singkapan / QAQC."):
            self.rescan()
        else:
            self.viewer.placeholder("Folder ini belum dipakai di Core box.\nKlik ↻ untuk mendaftarkan foto di folder ini.")
            self.card.clear()

    # ================================================================ export / impor
    def rescan(self) -> None:
        if not self.folder or self.mode != "core":
            return  # foto hanya didaftarkan ke Core box dari ruang kerja Core box
        self._core_scanned = self.folder
        try:
            j = api.call("/core/rescan", {"folder": self.folder})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.load_rows()
        s = j["scan"]
        self.toast(f"{s['total']} foto · {s['added']} baru · {s['missing']} hilang")

    def export_xlsx(self) -> None:
        if not self.folder:
            return
        ids: list[int] = []
        if len(self.view) != len(self.rows) and ask(self, f"Export hanya {len(self.view)} foto yang tampil (sesuai filter)?\n\nOK = yang tampil saja · Batal = semua {len(self.rows)} foto"):
            ids = [r["id"] for r in self.view]
        holes = sorted({r["hole_id"] for r in (self.view if ids else self.rows) if r.get("hole_id")})
        base = holes[0] if len(holes) == 1 else Path(self.folder).name
        name = "Core_Log_" + re.sub(r"[^\w.-]+", "_", base) + "_" + _dt.date.today().isoformat() + ".xlsx"
        p, _ = QFileDialog.getSaveFileName(self, "Simpan log ke Excel", str(Path(SET.get("lastSaveDir", str(Path.home()))) / name), "Excel (*.xlsx)")
        if not p:
            return
        SET.set("lastSaveDir", str(Path(p).parent))
        self.sSum.setText("Menyusun Excel…")
        folder = self.folder

        def work():
            data = api.call("/core/export/xlsx", {"folder": folder, "ids": ids})
            Path(p).write_bytes(data)
            return p

        run_bg(work, ok=lambda path: (self.toast("Tersimpan: " + path, 5000), show_in_folder(path), self.load_rows()),
               err=lambda e: say(self, "Gagal export Excel:\n" + e, warn=True))

    def import_json(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Impor JSON dashboard lama", "", "JSON (*.json)")
        if not f:
            return
        try:
            payload = json.loads(Path(f).read_text(encoding="utf-8"))
            j = api.call("/core/import/json", {"folder": self.folder, "payload": payload, "by": self.user()})
        except Exception as e:  # noqa: BLE001
            say(self, "Gagal impor JSON:\n" + str(e), warn=True)
            return
        self.load_rows()
        say(self, f"Impor selesai: {j['matched']} foto cocok, {j['unmatched']} tidak ditemukan di folder."
            + ("\n\nContoh yang tidak cocok:\n" + "\n".join(j["unmatched_names"]) if j.get("unmatched_names") else ""))

    def open_dh(self) -> None:
        from .dh import DhDlg
        d = DhDlg(self, self.folder)
        d.changed.connect(lambda: self.load_rows())
        d.exec()

    # ================================================================ cari
    def goto_result(self, x: dict) -> None:
        if not x.get("photo_id"):
            self.toast(f"Interval {x.get('hole') or ''} {fmt(x.get('f'))}–{fmt(x.get('t'))} m belum punya foto core box di folder ini.", 4500)
            return
        i = next((i for i, r in enumerate(self.view) if r["id"] == x["photo_id"]), -1)
        if i < 0:
            self.reset_filter()
            i = next((i for i, r in enumerate(self.view) if r["id"] == x["photo_id"]), -1)
        if i >= 0:
            self.table.go_row(i)
            self.table.setFocus()
            if x.get("type") == "assay" and not self.interp.ov.on:
                self.interp.bOv.setChecked(True)
            if x.get("type") == "tanda":
                self.interp.mkShowCb.setChecked(True)
            if x.get("type") == "segmen" and not self.interp.ov.on:
                self.interp.bOv.setChecked(True)

    # ================================================================ keyboard
    def keyPressEvent(self, e) -> None:  # noqa: N802
        fw = QApplication.focusWidget()
        if e.key() in (Qt.Key_Down, Qt.Key_Up) and not isinstance(fw, (QLineEdit, QComboBox)) and fw is not self.table and self.view:
            self.table.go_row(self._cur_index() + (1 if e.key() == Qt.Key_Down else -1))
            return
        super().keyPressEvent(e)

    def closeEvent(self, e) -> None:  # noqa: N802
        w = QApplication.focusWidget()
        if w:
            w.clearFocus()  # simpan isian terakhir
        QApplication.processEvents()
        super().closeEvent(e)


__all__ = ["MainWindow", "QSize"]
