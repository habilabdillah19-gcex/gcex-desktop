"""Ruang kerja Borang: borang lapangan tulisan tangan (Ore Spotter loading pit, Ore ke ROM / crusher, RC Daily Drilling Report,
RC Drill / Chiptray Log).

Kiri: daftar borang (+ Borang: foto / scan / PDF, satu borang per halaman). Tengah: scan (zoom, putar). Kanan: tab Data
(header & tabel yang bisa diedit; sel ragu AI kuning, galat validasi merah; centang ✓ = baris diverifikasi), Pivot (Ore
Spotter) dan Ekspor (Excel, CSV, SQLite, MS Access). Data lewat rute /core/forms/* (backend core_forms)."""
from __future__ import annotations

import re
import time
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QImage, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QMenu, QProgressBar,
                               QLineEdit, QListWidget, QListWidgetItem, QRadioButton, QScrollArea, QSplitter, QStyledItemDelegate, QTableWidget,
                               QPushButton, QStackedWidget, QTableWidgetItem, QTabWidget, QToolButton, QVBoxLayout, QWidget)

from . import api, theme
from .card import _esc, btn
from .dialogs import ask, say
from .util import SET, log, run_bg, show_in_folder
from .viewer import Viewer

SHORT = {"ore": "Loading pit", "rom": "ROM / crusher", "ddr": "Daily Drilling Report", "rc": "RC Drill", "map": "Geological Mapping",
         "chn": "Channel Sampling", "dpr": "Drill Progress Report"}
FILE = {"ore": "Ore_Loading_Pit", "rom": "Ore_ROM_Crusher", "ddr": "RC_Daily_Drilling_Report", "rc": "RC_Drill", "map": "Geological_Mapping",
        "chn": "Channel_Sampling", "dpr": "Drill_Progress_Report"}
MULTI = {"ddr"}  # borang dengan beberapa tabel: ekspor CSV = ZIP berisi satu CSV per tabel
UNC_BG, BAD_BG, VER_BG = "#fff3bf", "#ffe3e3", "#e6f4ea"
TYPE_ICON = {"auto": "✦", "ore": "⛏", "rom": "⇄", "ddr": "▤", "rc": "▦", "map": "⌖", "chn": "┇", "dpr": "▲"}
TYPE_LABEL = {"auto": "Auto Detect (Rekomendasi)", "ore": "Ore Spotter (Loading Pit)", "rom": "Ore ke Stockpile / Crusher",
              "ddr": "Daily Drilling Report", "rc": "RC Drill Logging", "map": "Geological Mapping", "chn": "Channel Sampling",
              "dpr": "Drill Progress Report"}
NAV = [("Borang", "▣"), ("Riwayat", "↺"), ("Template", "▤"), ("Pengaturan", "⚙"), ("Bantuan", "?")]
EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".pdf")
# status di daftar file: (teks, warna titik)
ST = {"run": ("Memproses", "#2f6fd6"), "queue": ("Dalam antrean", "#8a94a3"), "err": ("AI gagal", "#c0392b"),
      "ok": ("Selesai", "#2e9d57"), "check": ("Perlu verifikasi", "#e09a1e"), "new": ("Belum dibaca", "#8a94a3")}
ROLE_D = Qt.UserRole + 1   # dict status untuk FileCard


class FileCard(QStyledItemDelegate):
    """Baris daftar file: miniatur, nama, jenis borang, status berwarna (+ bilah progres saat AI membaca)."""

    def sizeHint(self, option, index):  # noqa: N802
        return QSize(option.rect.width(), 66)

    def paint(self, p: QPainter, option, index) -> None:  # noqa: D401
        from PySide6.QtWidgets import QStyle
        info = index.data(ROLE_D) or {}
        r = option.rect.adjusted(4, 3, -4, -3)
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        sel = bool(option.state & QStyle.State_Selected)
        p.setPen(QPen(QColor(theme.C["ac"] if sel else theme.C["bd"]), 1.4 if sel else 1))
        p.setBrush(QColor(theme.C["acs"] if sel else theme.C["pn"]))
        p.drawRoundedRect(r, 5, 5)
        if sel:
            p.fillRect(r.x(), r.y() + 1, 3, r.height() - 2, QColor(theme.C["ac2"]))
        ic = index.data(Qt.DecorationRole)
        x = r.x() + 8
        if isinstance(ic, QIcon):
            ic.paint(p, x, r.y() + 4, 44, r.height() - 8)
        x += 52
        st, col = ST.get(info.get("st", "new"), ST["new"])
        if info.get("st") == "queue" and info.get("pos"):
            st = f"Antre #{info['pos']}"
        fm = option.fontMetrics
        tw = r.right() - x - 8
        f = QFont(option.font)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(theme.C["ink"]))
        p.drawText(x, r.y() + 4, tw, 18, Qt.AlignLeft | Qt.AlignVCenter, QFontMetrics(f).elidedText(info.get("name", ""), Qt.ElideMiddle, tw))
        p.setFont(option.font)
        sw = fm.horizontalAdvance(st) + 16
        p.setPen(QColor(theme.C["mu"]))
        p.drawText(x, r.y() + 22, tw - sw - 6, 17, Qt.AlignLeft | Qt.AlignVCenter, fm.elidedText(info.get("type", ""), Qt.ElideRight, tw - sw - 6))
        sx = r.right() - 8 - sw
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(col))
        p.drawEllipse(sx, r.y() + 26, 8, 8)
        p.setPen(QColor(col))
        p.drawText(sx + 13, r.y() + 22, sw - 13, 17, Qt.AlignLeft | Qt.AlignVCenter, st)
        if info.get("st") == "run":  # bilah progres (perkiraan dari lama baca rata-rata)
            pr = max(0.03, min(0.97, info.get("prog", 0.0)))
            by = r.y() + 45
            bw = tw - 80
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.C["pn2"]))
            p.drawRoundedRect(x, by, bw, 5, 2, 2)
            p.setBrush(QColor(col))
            p.drawRoundedRect(x, by, int(bw * pr), 5, 2, 2)
            p.setPen(QColor(theme.C["mu"]))
            p.drawText(x + bw + 6, by - 5, 74, 15, Qt.AlignLeft | Qt.AlignVCenter, info.get("el", ""))
        elif info.get("cnt"):
            p.setPen(QColor(theme.C["mu"]))
            p.drawText(x, r.y() + 39, tw, 17, Qt.AlignLeft | Qt.AlignVCenter, fm.elidedText(info["cnt"], Qt.ElideRight, tw))
        p.restore()


class ListDelegate(QStyledItemDelegate):
    """Sel dengan pilihan daftar (mis. kategori aktivitas Daily Drilling Report); tetap bisa diketik bebas."""

    def __init__(self, parent, items: list[str]):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):  # noqa: N802
        cb = QComboBox(parent)
        cb.setEditable(True)
        cb.addItems(self.items)
        return cb

    def setEditorData(self, ed, index):  # noqa: N802
        ed.setCurrentText(index.data() or "")

    def setModelData(self, ed, model, index):  # noqa: N802
        model.setData(index, ed.currentText())


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
            self.show_crop(self.pg.cur["doc"].get("crop") if self.pg.cur else None)

    def show_crop(self, cr) -> None:
        """Area potong: luar kotak diredupkan, tepi kuning putus-putus (anak item foto: ikut zoom / putar)."""
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QBrush, QPainterPath
        from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsRectItem
        if not hasattr(self, "cropShade"):
            self.cropShade = QGraphicsPathItem(self.root)
            self.cropShade.setBrush(QBrush(QColor(0, 0, 0, 120)))
            self.cropShade.setPen(Qt.NoPen)
            self.cropShade.setZValue(5)
            self.cropBox = QGraphicsRectItem(self.root)
            pen = QPen(QColor("#ffd43b"))
            pen.setCosmetic(True)
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            self.cropBox.setPen(pen)
            self.cropBox.setZValue(6)
        if not cr or not self.w:
            self.cropShade.hide()
            self.cropBox.hide()
            return
        r = QRectF(cr[0] * self.w, cr[1] * self.h, (cr[2] - cr[0]) * self.w, (cr[3] - cr[1]) * self.h)
        path = QPainterPath()
        path.addRect(QRectF(0, 0, self.w, self.h))
        path.addRect(r)
        self.cropShade.setPath(path)
        self.cropBox.setRect(r)
        self.cropShade.show()
        self.cropBox.show()


    def load_full(self) -> None:
        return

    def rotate90(self) -> None:
        if not self.w:
            return
        self.rot = (self.rot + 90) % 360
        self.root.setRotation(self.rot)
        self.fit()
        self.pg.save_rot(self.rot)


class CropTool:
    """Tarik kotak di scan -> area potong (pecahan gambar asli, sebelum diputar)."""

    def __init__(self, view: "ScanView", done) -> None:
        self.v, self.done, self.a = view, done, None

    def _frac(self, p) -> list[float]:
        return [min(1.0, max(0.0, p.x() / self.v.w)), min(1.0, max(0.0, p.y() / self.v.h))]

    def press(self, p, _e) -> bool:
        self.a = self._frac(p)
        return True

    def move(self, p) -> None:
        if self.a:
            b = self._frac(p)
            self.v.show_crop([min(self.a[0], b[0]), min(self.a[1], b[1]), max(self.a[0], b[0]), max(self.a[1], b[1])])

    def release(self, p) -> None:
        if self.a:
            b = self._frac(p)
            self.done([self.a[0], self.a[1], b[0], b[1]])
        self.a = None

    def hover(self, _p):
        return Qt.CrossCursor


class FormsPage(QWidget):
    def __init__(self, win) -> None:
        super().__init__()
        self.win = win
        self.folder = ""
        self.rootp = ""
        self.types: dict = {}
        self.docs: list[dict] = []
        self.cur: dict | None = None      # {"doc", "rows", "valid", "recs", "pivot", "summary"}
        self.tbl = ""                     # tabel yang sedang ditampilkan ('' = utama, 'hole' = meterage DDR)
        self.kat: list[str] = []
        self.ai_busy = False
        self.ai_q: list[int] = []        # antrean baca AI (id borang); yang sedang dibaca = self.ai_did
        self.ai_did: int | None = None
        self.perf: dict[int, dict] = {}  # kecepatan baca AI terakhir per borang (sesi ini)
        self.ai_t0 = 0.0
        self.ai_clock = QTimer(self)
        self.ai_clock.setInterval(1000)
        self.ai_clock.timeout.connect(self._ai_tick)
        self._filling = False
        self._build()

    # ---------------------------------------------------------------- tata letak
    def _build(self) -> None:
        """Tata letak (0.43.0): kiri = jenis borang, tombol tambah, daftar file berstatus; tengah = scan dengan bilah zoom;
        kanan = tab Data (status ekstraksi, header, tabel, ringkasan) / Validasi / Pivot / Ekspor; bawah = antrean AI."""
        self.setAcceptDrops(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.pages = QStackedWidget()
        root.addWidget(self.pages)
        work = QWidget()
        self.pages.addWidget(work)
        # bilah navigasi (dipasang di bilah atas jendela oleh MainWindow, hanya tampil di mode Borang)
        self.nav = QFrame()
        self.nav.setObjectName("fmNav")
        nh = QHBoxLayout(self.nav)
        nh.setContentsMargins(0, 0, 0, 0)
        nh.setSpacing(2)
        self.navBtns: list[QPushButton] = []
        for i, (t_, ic) in enumerate(NAV):
            b_ = QPushButton(f"{ic}  {t_}")
            b_.setObjectName("fmNavBtn")
            b_.setCheckable(True)
            b_.setChecked(i == 0)
            b_.setCursor(Qt.PointingHandCursor)
            b_.clicked.connect(lambda _=False, i=i: self.show_page(i))
            nh.addWidget(b_)
            self.navBtns.append(b_)
        o = QVBoxLayout(work)
        o.setContentsMargins(0, 0, 0, 0)
        o.setSpacing(0)
        sp = QSplitter(Qt.Horizontal)
        sp.setHandleWidth(5)
        o.addWidget(sp, 1)
        o.addWidget(self._bottom_bar())
        # ---- kiri
        lw = QWidget()
        lw.setObjectName("fmLeft")
        lv = QVBoxLayout(lw)
        lv.setContentsMargins(10, 10, 6, 8)
        lv.setSpacing(6)
        hd = QLabel("BORANG LAPANGAN")
        hd.setObjectName("fmSect")
        lv.addWidget(hd)
        self.cbNew = QComboBox()  # sumber data jenis borang (disembunyikan; dipilih lewat daftar jenis di bawah)
        self.cbNew.hide()
        self.typeList = QListWidget()
        self.typeList.setObjectName("fmTypes")
        self.typeList.setFrameShape(QFrame.NoFrame)
        self.typeList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.typeList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.typeList.setTextElideMode(Qt.ElideRight)
        self.typeList.setToolTip("Jenis borang untuk file yang akan ditambahkan")
        self.typeList.currentRowChanged.connect(self._type_picked)
        self.cbNew.currentIndexChanged.connect(self._type_synced)
        lv.addWidget(self.typeList)
        self.bAdd = btn("＋  Tambah File", "Tambah foto / scan / PDF borang (disalin ke folder proyek; PDF: satu borang per halaman)", pri=True)
        self.bAddDir = btn("＋  Tambah Folder", "Tambahkan semua foto / scan / PDF di satu folder sebagai borang jenis terpilih")
        for b_ in (self.bAdd, self.bAddDir):
            b_.setMinimumHeight(32)
            lv.addWidget(b_)
        r = QHBoxLayout()
        self.lstHead = QLabel("DAFTAR FILE")
        self.lstHead.setObjectName("fmSect")
        r.addWidget(self.lstHead, 1)
        self.cbSort = QComboBox()
        for t_, k in (("Urut: Ditambahkan", "add"), ("Urut: Terbaru", "new"), ("Urut: Nama", "name"), ("Urut: Status", "status"),
                      ("Urut: Jenis", "type")):
            self.cbSort.addItem(t_, k)
        self.cbSort.setCurrentIndex(max(0, self.cbSort.findData(SET.get("fmSort", "add"))))
        self.cbSort.currentIndexChanged.connect(self._sort_changed)
        r.addWidget(self.cbSort)
        self.bDel = btn("🗑", "Hapus borang terpilih dari proyek (file asli di luar proyek tidak tersentuh) — juga tombol Delete", sm=True)
        r.addWidget(self.bDel)
        lv.addLayout(r)
        self.lst = QListWidget()
        self.lst.setObjectName("fmFiles")
        self.lst.setIconSize(QSize(46, 58))
        self.lst.setItemDelegate(FileCard(self.lst))
        self.lst.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst.customContextMenuRequested.connect(self._list_menu)
        lv.addWidget(self.lst, 1)
        drop = QLabel("⇪  Seret file ke sini atau klik tombol di atas\nJPG, PNG, TIFF, BMP, WEBP, PDF")
        drop.setObjectName("fmDrop")
        drop.setAlignment(Qt.AlignCenter)
        lv.addWidget(drop)
        self.sum = QLabel()
        self.sum.setObjectName("note")
        self.sum.setWordWrap(True)
        lv.addWidget(self.sum)
        sp.addWidget(lw)
        # ---- tengah
        cw = QWidget()
        cv = QVBoxLayout(cw)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        tb = QFrame()
        tb.setObjectName("fmVHead")
        tv = QVBoxLayout(tb)
        tv.setContentsMargins(10, 6, 10, 6)
        tv.setSpacing(5)
        th = QHBoxLayout()
        self.title = QLabel()
        self.title.setTextFormat(Qt.RichText)
        self.title.setObjectName("fmVTitle")
        from PySide6.QtWidgets import QSizePolicy as _SP
        self.title.setSizePolicy(_SP.Ignored, _SP.Preferred)  # judul panjang tidak memaksa lebar minimum jendela (layar 1366 px)
        self.title.setMinimumWidth(120)
        th.addWidget(self.title, 1)
        self.cbSpeed = QComboBox()
        for t_, px in (("Cepat", 1280), ("Seimbang", 1600), ("Teliti", 2000)):
            self.cbSpeed.addItem(t_, px)
        self.cbSpeed.setCurrentIndex(max(0, self.cbSpeed.findData(int(SET.get("fmPx", 1600)))))
        self.cbSpeed.setToolTip("Ukuran gambar yang dikirim ke AI.\nCepat = 1280 px (paling cepat; cukup untuk tulisan yang jelas)\n"
                                "Seimbang = 1600 px\nTeliti = 2000 px (paling lambat; untuk tulisan kecil / scan buram)")
        self.cbSpeed.currentIndexChanged.connect(lambda _i: SET.set("fmPx", self.cbSpeed.currentData()))
        th.addWidget(self.cbSpeed)
        self.bAI = btn("✦ Baca dengan AI", "AI vision lokal (Ollama) membaca header & tabel borang ini. Baris lama diganti.", pri=True, sm=True)
        th.addWidget(self.bAI)
        tv.addLayout(th)
        zh = QHBoxLayout()
        zh.setSpacing(4)
        self.vb: dict[str, QToolButton] = {}
        for k, t_, tip in (("zout", "−", "Perkecil"), ("pct", "100%", "Perbesaran (klik = pas layar)"), ("zin", "+", "Perbesar"),
                           ("sp", "", ""), ("rot", "↻", "Putar 90° (disimpan, dipakai juga saat AI membaca)"),
                           ("fit", "⤢", "Pas layar (klik ganda di scan)"), ("focus", "⛶", "Fokus scan: sembunyikan panel kiri & kanan"),
                           ("sp", "", ""), ("crop", "✂ Potong", "Potong area: tarik kotak di scan mengelilingi TABEL saja. AI hanya membaca area itu "
                                                               "(tulisan tampak lebih besar -> lebih teliti & lebih cepat). Klik lagi untuk batal."),
                           ("uncrop", "✕", "Hapus potongan (AI membaca seluruh foto lagi)"),
                           ("cropall", "⧉ ▾", "Pakai potongan ini untuk borang lain")):
            if k == "sp":
                zh.addSpacing(14)
                continue
            b_ = QToolButton()
            b_.setText(t_)
            b_.setToolTip(tip)
            b_.setObjectName("fmVBtn")
            if k in ("focus", "crop"):
                b_.setCheckable(True)
            zh.addWidget(b_)
            self.vb[k] = b_
        zh.addStretch(1)
        tv.addLayout(zh)
        cv.addWidget(tb)
        self.view = ScanView(self)
        self.view.tools.hide()  # diganti bilah zoom di atas
        self.view.placeholder("Tambahkan foto / scan / PDF borang dengan Tambah File, atau seret file ke sini.\n"
                              "Scroll = zoom, tarik = geser, ↻ = putar (juga untuk AI).")
        cv.addWidget(self.view, 1)
        self.vb["zout"].clicked.connect(lambda: (self.view.zoom(1 / 1.3), self._zoom_pct()))
        self.vb["zin"].clicked.connect(lambda: (self.view.zoom(1.3), self._zoom_pct()))
        self.vb["pct"].clicked.connect(lambda: (self.view.fit(), self._zoom_pct()))
        self.vb["fit"].clicked.connect(lambda: (self.view.fit(), self._zoom_pct()))
        self.vb["rot"].clicked.connect(lambda: self.view.btn["rot"].click())
        self.vb["focus"].toggled.connect(self._focus)
        self.vb["crop"].toggled.connect(self._crop_mode)
        self.vb["uncrop"].clicked.connect(lambda: self.save_crop(None))
        mc = QMenu(self.vb["cropall"])
        mc.addAction("Semua halaman dari file yang sama", lambda: self.crop_to_others("file"))
        mc.addAction("Semua borang jenis ini yang belum dipotong", lambda: self.crop_to_others("type"))
        self.vb["cropall"].setMenu(mc)
        self.vb["cropall"].setPopupMode(QToolButton.InstantPopup)
        self.vb["uncrop"].setEnabled(False)
        self.vb["cropall"].setEnabled(False)
        self.aiInfo = QLabel()
        self.aiInfo.setObjectName("note")
        self.aiInfo.setWordWrap(True)
        self.aiInfo.setContentsMargins(10, 4, 10, 4)
        cv.addWidget(self.aiInfo)
        sp.addWidget(cw)
        # ---- kanan
        self.tabs = QTabWidget()
        self.tabs.setObjectName("fmTabs")
        self.tabs.setMinimumWidth(420)  # 0.45.1: muat di layar 1280 px logis (1920 px @150%)
        self.tabs.addTab(self._tab_data(), "Data")
        self.tabs.addTab(self._tab_valid(), "Validasi")
        self.tabs.addTab(self._tab_pivot(), "Pivot")
        self.tabs.addTab(self._tab_export(), "Ekspor")
        from .forms_transkrip import TranscriptTab
        self.tr = TranscriptTab(self)
        self.tabs.addTab(self.tr, "✎ Transkrip")
        self.tabs.setTabToolTip(4, "Mode Transkrip: AI hanya menyalin tulisan menjadi teks; Anda yang menentukan pemisah & kolom, "
                                   "program menyusun tabel, validasi dan pivot. Untuk borang padat yang salah kolom bila dibaca langsung.")
        sp.addWidget(self.tabs)
        sp.setStretchFactor(1, 1)
        sp.setSizes(SET.get("qt_fm_split2", [260, 640, 660]))
        sp.splitterMoved.connect(lambda *_: SET.set("qt_fm_split2", sp.sizes()))
        self.split = sp
        self.left, self.right = lw, self.tabs
        self.bAdd.clicked.connect(self.add_files)
        self.bAddDir.clicked.connect(self.add_folder)
        self.bDel.clicked.connect(self.delete_doc)
        self.bAI.clicked.connect(self.run_ai)
        self.lst.currentRowChanged.connect(self._pick)
        QShortcut(QKeySequence(QKeySequence.Delete), self.lst, activated=self.delete_doc, context=Qt.WidgetShortcut)
        self.view.loaded.connect(lambda *_: self._zoom_pct())
        from .forms_pages import HelpPage, HistoryPage, SettingsPage, TemplatePage
        self.pgHist, self.pgTpl, self.pgSet, self.pgHelp = HistoryPage(self), TemplatePage(self), SettingsPage(self), HelpPage(self)
        for w_ in (self.pgHist, self.pgTpl, self.pgSet, self.pgHelp):
            self.pages.addWidget(w_)
        self.set_enabled(False)

    def _bottom_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("fmBottom")
        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(10)
        self.qInfo = QLabel("Antrean AI kosong")
        self.qInfo.setObjectName("note")
        h.addWidget(self.qInfo)
        self.qBar = QProgressBar()
        self.qBar.setRange(0, 1)
        self.qBar.setValue(0)
        self.qBar.setTextVisible(False)
        self.qBar.setFixedWidth(220)
        h.addWidget(self.qBar)
        self.qPct = QLabel("")
        self.qPct.setObjectName("note")
        h.addWidget(self.qPct)
        self.qDone = QLabel("")
        self.qDone.setObjectName("note")
        h.addWidget(self.qDone)
        h.addStretch(1)
        self.bAIAll = btn("Baca Semua dengan AI", "Antrekan semua borang yang belum dibaca (atau gagal) untuk dibaca AI satu per satu "
                          "di latar belakang. Selama itu Anda tetap bisa memeriksa & memverifikasi borang lain.", pri=True)
        self.bAIAll.setMinimumHeight(32)
        self.bAIAll.setMinimumWidth(190)
        self.bCancel = btn("Batal", "Kosongkan antrean AI (borang yang sedang dibaca tetap diselesaikan)")
        self.bCancel.setMinimumHeight(32)
        h.addWidget(self.bAIAll)
        h.addWidget(self.bCancel)
        self.bAIAll.clicked.connect(self.run_ai_all)
        self.bCancel.clicked.connect(self.cancel_ai)
        self.q_done, self.q_total, self.q_last = 0, 0, ""
        return bar

    def _section(self, v: QVBoxLayout, title: str, extra: list | None = None, open_: bool = True) -> tuple[QVBoxLayout, QToolButton]:
        """Bagian yang bisa dilipat (▾ judul) dengan tombol tambahan di kanan judul."""
        box = QFrame()
        box.setObjectName("fmCard")
        bv = QVBoxLayout(box)
        bv.setContentsMargins(10, 6, 10, 8)
        bv.setSpacing(6)
        hh = QHBoxLayout()
        tg = QToolButton()
        tg.setObjectName("fmFold")
        tg.setCheckable(True)
        tg.setChecked(open_)
        tg.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        tg.setArrowType(Qt.DownArrow if open_ else Qt.RightArrow)
        tg.setText(title)
        hh.addWidget(tg)
        hh.addStretch(1)
        for w_ in extra or []:
            hh.addWidget(w_)
        bv.addLayout(hh)
        body = QWidget()
        inner = QVBoxLayout(body)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(6)
        bv.addWidget(body, 1)
        body.setVisible(open_)

        def flip(on: bool) -> None:
            body.setVisible(on)
            tg.setArrowType(Qt.DownArrow if on else Qt.RightArrow)
        tg.toggled.connect(flip)
        v.addWidget(box, 1 if extra is not None else 0)
        return inner, tg

    def _tab_data(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(8)
        # status ekstraksi
        self.banner = QFrame()
        self.banner.setObjectName("fmBanner")
        bh = QHBoxLayout(self.banner)
        bh.setContentsMargins(10, 8, 10, 8)
        self.bnIcon = QLabel("•")
        self.bnIcon.setObjectName("fmBnIcon")
        self.bnIcon.setFixedWidth(26)
        self.bnIcon.setAlignment(Qt.AlignCenter)
        bh.addWidget(self.bnIcon)
        bt = QVBoxLayout()
        bt.setSpacing(0)
        self.bnTitle = QLabel()
        self.bnTitle.setObjectName("fmBnTitle")
        self.bnSub = QLabel()
        self.bnSub.setObjectName("note")
        self.bnSub.setWordWrap(True)
        bt.addWidget(self.bnTitle)
        bt.addWidget(self.bnSub)
        bh.addLayout(bt, 1)
        self.bnFix = QPushButton("Jenis salah? Ganti & baca ulang ▾")
        self.bnFix.setObjectName("fmBnFix")
        self.bnFix.setToolTip("Banyak galat sering berarti jenis borang salah terdeteksi (mis. Daily Drilling Report terbaca sebagai Drill "
                              "Progress Report). Pilih jenis yang benar: baris lama dibuang lalu dibaca ulang AI.")
        self.bnFixMenu = QMenu(self.bnFix)
        self.bnFix.setMenu(self.bnFixMenu)
        self.bnFix.hide()
        bh.addWidget(self.bnFix)
        cl = QVBoxLayout()
        cl.setSpacing(0)
        cap = QLabel("Keyakinan AI")
        cap.setObjectName("note")
        cap.setAlignment(Qt.AlignRight)
        self.bnConf = QLabel("–")
        self.bnConf.setObjectName("fmConf")
        self.bnConf.setAlignment(Qt.AlignCenter)
        self.bnConf.setToolTip("Persentase isian yang dibaca AI tanpa ragu (tidak kuning). Bukan jaminan benar — tetap cocokkan dengan scan.")
        cl.addWidget(cap)
        cl.addWidget(self.bnConf, 0, Qt.AlignRight)
        bh.addLayout(cl)
        v.addWidget(self.banner)
        # header (dua kolom)
        hv, self.hdrFold = self._section(v, "Informasi Header")
        self.hdrBox = QWidget()
        self.hdrGrid = QGridLayout(self.hdrBox)
        self.hdrGrid.setContentsMargins(0, 0, 0, 0)
        self.hdrGrid.setHorizontalSpacing(8)
        self.hdrGrid.setVerticalSpacing(4)
        self.hdrEd: dict[str, QLineEdit] = {}
        self.hdrScroll = QScrollArea()
        self.hdrScroll.setWidgetResizable(True)
        self.hdrScroll.setFrameShape(QFrame.NoFrame)
        self.hdrScroll.setWidget(self.hdrBox)
        hv.addWidget(self.hdrScroll)
        # tabel
        self.tblRow = QWidget()
        tr = QHBoxLayout(self.tblRow)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.addWidget(QLabel("Tabel:"))
        self.cbTbl = QComboBox()
        self.cbTbl.currentIndexChanged.connect(self._tbl_changed)
        tr.addWidget(self.cbTbl)
        self.tblRow.hide()
        tv_, self.tblFold = self._section(v, "Data", [self.tblRow])
        self.valInfo = QLabel()
        self.valInfo.setTextFormat(Qt.RichText)
        self.valInfo.setWordWrap(True)
        tv_.addWidget(self.valInfo)
        self.t = QTableWidget(0, 1)
        self.t.verticalHeader().setDefaultSectionSize(24)
        self.t.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.t.itemChanged.connect(self._cell)
        self._plain = QStyledItemDelegate(self.t)
        self._katDel = ListDelegate(self.t, [])
        tv_.addWidget(self.t, 1)
        r = QHBoxLayout()
        self.bRow = btn("+ Baris", sm=True)
        self.bIns = btn("Sisipkan", "Sisipkan baris di atas baris terpilih", sm=True)
        self.bRowDel = btn("Hapus baris", sm=True)
        self.bVerAll = btn("✓ Verifikasi semua", "Tandai semua baris sudah diperiksa terhadap scan", sm=True)
        self.bUnver = btn("Batal verifikasi", sm=True)
        for b in (self.bRow, self.bIns, self.bRowDel, self.bVerAll, self.bUnver):
            r.addWidget(b)
        r.addStretch(1)
        tv_.addLayout(r)
        # ringkasan
        sv, self.sumFold = self._section(v, "Ringkasan")
        self.kpiBox = QWidget()
        self.kpi = QGridLayout(self.kpiBox)
        self.kpi.setContentsMargins(0, 0, 0, 0)
        self.kpi.setSpacing(6)
        sv.addWidget(self.kpiBox)
        self.sumInfo = QLabel()
        self.sumInfo.setTextFormat(Qt.RichText)
        self.sumInfo.setWordWrap(True)
        self.sumInfo.setObjectName("note")
        self.sumInfo.hide()
        sv.addWidget(self.sumInfo)
        self.bRow.clicked.connect(lambda: self.add_row(None))
        self.bIns.clicked.connect(lambda: self.add_row(max(0, self.t.currentRow())))
        self.bRowDel.clicked.connect(self.del_row)
        self.bVerAll.clicked.connect(lambda: self.verify_all(True))
        self.bUnver.clicked.connect(lambda: self.verify_all(False))
        return w

    def _tab_valid(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)
        self.vSum = QLabel()
        self.vSum.setTextFormat(Qt.RichText)
        self.vSum.setWordWrap(True)
        v.addWidget(self.vSum)
        self.vList = QListWidget()
        self.vList.setObjectName("fmVList")
        self.vList.itemActivated.connect(self._goto_issue)
        self.vList.itemClicked.connect(self._goto_issue)
        v.addWidget(self.vList, 1)
        n = QLabel("Klik satu galat untuk melompat ke selnya di tab Data.<br>"
                   "<span style='background:%s'>&nbsp;kuning&nbsp;</span> = AI ragu / diisi program dari tanda ulang (〃, garis) atau dari "
                   "posisi kolom, <span style='background:%s'>&nbsp;merah&nbsp;</span> = galat validasi. Periksa tiap baris terhadap scan lalu "
                   "centang <b>✓</b> (Ctrl+Enter = verifikasi baris & lanjut). Ekspor bawaan hanya baris terverifikasi." % (UNC_BG, BAD_BG))
        n.setObjectName("note")
        n.setWordWrap(True)
        n.setTextFormat(Qt.RichText)
        v.addWidget(n)
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
        for _i in range(4):
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
        n = QLabel("Tabel database: <b>ORE_LOADING_PIT</b>, <b>ORE_ROM_CRUSHER</b>, <b>RC_INTERVAL</b>, atau untuk Daily Drilling Report "
                   "<b>DDR_DASHBOARD</b> (sheet Excel <i>Data_Dashboard</i>: kolom sama dengan sheet Data dashboard drilling, satu baris per lubang, "
                   "jam shift di baris pertama, Azimuth & Dip di kanan) + <b>DDR_AKTIVITAS</b> + <b>DDR_METERAGE</b> + <b>DDR_SHIFT</b> "
                   "(ringkasan jam, meter, HM, bit), dengan kolom VERIFIED, SRC_DOC dan SRC_KEY (borang:baris). "
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
        for b_ in self.navBtns[1:]:
            b_.setEnabled(bool(self.folder))
        for w_ in (self.bAdd, self.bAddDir, self.cbNew, self.typeList):
            w_.setEnabled(bool(self.folder))
        for w in (self.bDel, self.bAI, self.tabs):
            w.setEnabled(on)
        self.bAIAll.setEnabled(bool(self.folder))
        self._ai_buttons()

    def ftype(self) -> str:
        return (self.cur or {}).get("doc", {}).get("type") or self.cbNew.currentData() or "ore"

    def escape(self) -> bool:
        return False

    # ---------------------------------------------------------------- proyek & daftar
    def open(self, folder: str) -> None:
        self.folder = folder
        self.cur = None
        self.perf = {}
        self.ai_q = []  # jawaban AI yang masih berjalan untuk folder lama diabaikan (cek folder di _ai_next)
        try:
            j = api.call("/core/forms/open", {"folder": folder})
        except api.ApiError as e:
            say(self, "Gagal membuka data borang:\n" + str(e), warn=True)
            return
        self.types = j["types"]
        self.kat = j.get("kategori") or []
        self._katDel.items = self.kat
        self.rootp = j.get("root") or ""
        cur = self.cbNew.currentData() or SET.get("fmType", "auto")
        self.show_page(0)
        self.cbNew.blockSignals(True)
        self.cbNew.clear()
        self.cbNew.addItem(TYPE_LABEL["auto"], "auto")
        for k, t in self.types.items():
            self.cbNew.addItem(t["name"], k)
        self.cbNew.setCurrentIndex(max(0, self.cbNew.findData(cur)))
        self.cbNew.blockSignals(False)
        self.typeList.blockSignals(True)
        self.typeList.clear()
        for k, nm in [("auto", TYPE_LABEL["auto"])] + [(k, TYPE_LABEL.get(k, t["name"])) for k, t in self.types.items()]:
            it = QListWidgetItem(f"{TYPE_ICON.get(k, '◇')}   {nm}")
            it.setData(Qt.UserRole, k)
            it.setToolTip("Jenis ditebak dari nama file; bila tidak ada petunjuk, AI menentukannya sebelum membaca" if k == "auto"
                          else self.types[k]["name"] + ("" if self.types[k].get("builtin", True) else " (template kustom)"))
            self.typeList.addItem(it)
        self.typeList.setCurrentRow(self.cbNew.currentIndex())
        self.typeList.setFixedHeight(min(32 * 9, 30 * max(1, self.typeList.count()) + 8))
        self.typeList.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if self.typeList.count() > 9 else Qt.ScrollBarAlwaysOff)
        self.pgHist.set_types(self.types)
        self.typeList.blockSignals(False)
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
        t = self._tname(d["type"])
        st = {"done": "AI", "error": "AI gagal", "pending": "belum dibaca"}.get(d["status"], d["status"])
        if d["id"] == self.ai_did:
            st = "AI membaca…"
        elif d["id"] in self.ai_q:
            st = f"antre AI #{self.ai_q.index(d['id']) + 1}"
        s = f"{d['name']}\n{t} · {st}"
        if d.get("n_rows"):
            s += f" · {d['n_ver']}/{d['n_rows']} ✓" + (f" · {d['n_unc']} ragu" if d.get("n_unc") else "")
        return s

    def _info(self, d: dict) -> dict:
        """Data kartu daftar file (FileCard)."""
        n, nv = d.get("n_rows") or 0, d.get("n_ver") or 0
        if d["id"] == self.ai_did:
            st = "run"
        elif d["id"] in self.ai_q:
            st = "queue"
        elif d["status"] == "error" and not n:
            st = "err"
        elif n and nv >= n:
            st = "ok"
        elif n:
            st = "check"
        else:
            st = "new"
        cnt = f"{nv}/{n} ✓ terverifikasi" + (f" · {d['n_unc']} ragu" if d.get("n_unc") else "") if n else ""
        el, prog = "", 0.0
        if st == "run":
            sec = time.time() - self.ai_t0
            est = max(20.0, self._est_secs())
            prog, el = sec / est, f"{int(sec) // 60}:{int(sec) % 60:02d} · {round(min(0.99, sec / est) * 100)}%"
        ty = self._tname(d["type"])
        if d.get("auto") == 1:
            ty = "Auto Detect · jenis ditentukan AI"
        elif d.get("auto") == 2:
            ty += " · dari nama file"
        return {"name": d["name"], "type": ty, "st": st, "cnt": cnt,
                "pos": (self.ai_q.index(d["id"]) + 1) if st == "queue" else 0, "prog": prog, "el": el}

    def _est_secs(self) -> float:
        """Perkiraan lama baca satu borang = rata-rata lama baca AI yang tercatat di proyek ini."""
        xs = [d["ai_secs"] for d in self.docs if d.get("ai_secs")]
        return sum(xs) / len(xs) if xs else 90.0

    def _sorted(self, docs: list[dict]) -> list[dict]:
        k = self.cbSort.currentData() if hasattr(self, "cbSort") else "add"
        order = {"run": 0, "queue": 1, "err": 2, "check": 3, "new": 4, "ok": 5}
        if k == "new":
            return sorted(docs, key=lambda d: -d["id"])
        if k == "name":
            return sorted(docs, key=lambda d: d["name"].lower())
        if k == "status":
            return sorted(docs, key=lambda d: (order[self._info(d)["st"]], d["id"]))
        if k == "type":
            return sorted(docs, key=lambda d: (d["type"], d["id"]))
        return list(docs)

    def _sort_changed(self, _i: int) -> None:
        SET.set("fmSort", self.cbSort.currentData())
        if self.folder:
            self._fill_list()

    def _type_picked(self, i: int) -> None:
        if 0 <= i < self.cbNew.count() and self.cbNew.currentIndex() != i:
            self.cbNew.setCurrentIndex(i)
        if i >= 0:
            SET.set("fmType", self.cbNew.itemData(i))

    def _type_synced(self, i: int) -> None:
        if self.typeList.currentRow() != i:
            self.typeList.blockSignals(True)
            self.typeList.setCurrentRow(i)
            self.typeList.blockSignals(False)

    def _set_item(self, it: QListWidgetItem, d: dict) -> None:
        it.setText(self._line(d))
        it.setData(ROLE_D, self._info(d))

    def _counts(self) -> None:
        n = len(self.docs)
        rr = sum(d.get("n_rows") or 0 for d in self.docs)
        vv = sum(d.get("n_ver") or 0 for d in self.docs)
        self.sum.setText(f"{n} borang · {rr} baris · {vv} diverifikasi")
        self.lstHead.setText(f"DAFTAR FILE ({n})")

    def _fill_list(self) -> None:
        cur = self.cur["doc"]["id"] if self.cur else None
        self.docs = self._sorted(self.docs)
        self.lst.blockSignals(True)
        self.lst.clear()
        root = self._root()
        for d in self.docs:
            it = QListWidgetItem()
            self._set_item(it, d)
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
        self._counts()

    def _thumb(self, did: int, im: QImage) -> None:
        for i in range(self.lst.count()):
            if self.lst.item(i).data(Qt.UserRole) == did:
                self.lst.item(i).setIcon(QIcon(QPixmap.fromImage(im)))

    def _sync_list(self) -> None:
        if not self.cur:
            return
        try:
            docs = api.call("/core/forms/open", {"folder": self.folder})["docs"]
        except api.ApiError:
            return
        pos = {self.lst.item(i).data(Qt.UserRole): i for i in range(self.lst.count())}
        self.docs = sorted(docs, key=lambda d: pos.get(d["id"], 1 << 30))  # urutan = urutan daftar (indeks _pick)
        self._relabel()
        self._counts()

    def add_files(self) -> None:
        if not self.folder:
            return
        ft = self.cbNew.currentData()
        SET.set("fmType", ft)
        fs, _ = QFileDialog.getOpenFileNames(self, f"Tambah borang {self._tname(ft)}", SET.get("fmLastDir", str(Path.home())),
                                             "Borang (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp *.pdf)")
        if fs:
            SET.set("fmLastDir", str(Path(fs[0]).parent))
            self._add_paths(fs)

    def add_folder(self) -> None:
        """Semua foto / scan / PDF di satu folder (tidak termasuk subfolder) -> borang jenis terpilih."""
        if not self.folder:
            return
        d = QFileDialog.getExistingDirectory(self, f"Tambah folder borang {self._tname(self.cbNew.currentData())}",
                                             SET.get("fmLastDir", str(Path.home())))
        if not d:
            return
        SET.set("fmLastDir", d)
        fs = sorted(str(f) for f in Path(d).iterdir() if f.is_file() and f.suffix.lower() in EXTS)
        if not fs:
            say(self, "Tidak ada foto / scan / PDF di folder itu.", warn=True)
            return
        if len(fs) > 5 and not ask(self, f"Tambahkan {len(fs)} file dari folder ini sebagai borang "
                                         f"{self._tname(self.cbNew.currentData())}?"):
            return
        self._add_paths(fs)

    def dragEnterEvent(self, e) -> None:  # noqa: N802
        if self.folder and e.mimeData().hasUrls() and any(u.toLocalFile().lower().endswith(EXTS) for u in e.mimeData().urls()):
            e.acceptProposedAction()

    def dropEvent(self, e) -> None:  # noqa: N802
        fs = [u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile().lower().endswith(EXTS)]
        if fs:
            e.acceptProposedAction()
            self._add_paths(fs)

    def _add_paths(self, fs: list[str]) -> None:
        ft = self.cbNew.currentData()
        self.toast(f"Menyalin {len(fs)} borang ke proyek…", 3000)

        def ok(j):
            self.docs = j["docs"]
            self._fill_list()
            if j["errors"]:
                say(self, "Sebagian file dilewati:\n" + "\n".join(j["errors"]), warn=True)
            if j["added"]:
                did = j["added"][0]["id"]
                i = next(i for i in range(self.lst.count()) if self.lst.item(i).data(Qt.UserRole) == did)
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
        self.ai_q = [x for x in self.ai_q if x != d["id"]]
        self.cur = None
        self.docs = j["docs"]
        self._fill_list()
        self._ai_buttons()
        if self.docs:
            self.lst.setCurrentRow(0)
            self._pick(0)
        else:
            self._clear()
            self.view.placeholder("Belum ada borang di proyek ini.")

    def _clear(self) -> None:
        self.cur = None
        self.tr.set_doc(None)
        self.set_enabled(False)
        self.title.setText("")
        self.t.setRowCount(0)

    def _pick(self, i: int) -> None:
        if not 0 <= i < self.lst.count():
            return
        did = self.lst.item(i).data(Qt.UserRole)
        try:
            j = api.call("/core/forms/doc", {"folder": self.folder, "id": did})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        same = self.cur and self.cur["doc"]["id"] == did
        if not same:
            self.tbl = ""
        self.cur = j
        self.set_enabled(True)
        if not same:
            root = self._root()
            self.view.show_scan(root / "scan" / j["doc"]["file"] if root else Path(j["doc"]["file"]), did, j["doc"].get("rot") or 0)
            self.vb["crop"].setChecked(False)
            self._crop_buttons()
        self.refresh()

    def _list_menu(self, pos) -> None:
        it = self.lst.itemAt(pos)
        if not it:
            return
        self.lst.setCurrentItem(it)
        m = QMenu(self)
        m.addAction("✦ Baca dengan AI", self.run_ai)
        m.addAction("✎ Salin teks dengan AI (Mode Transkrip)", lambda: (self.tabs.setCurrentWidget(self.tr), self.tr.run_ai()))
        has_rows = bool(self.cur and self.cur["rows"])
        sub = m.addMenu("Ubah jenis borang & baca ulang" if has_rows else "Ubah jenis borang")
        for k, t in self.types.items():
            a = sub.addAction(t["name"], lambda k=k: self.change_type(k))
            a.setCheckable(True)
            a.setChecked(bool(self.cur) and self.cur["doc"]["type"] == k)
        m.addAction("Deteksi jenis dengan AI", self.detect_type).setEnabled(not has_rows)
        m.addSeparator()
        m.addAction("Hapus borang…", self.delete_doc)
        m.exec(self.lst.viewport().mapToGlobal(pos))

    def _tname(self, k: str) -> str:
        if k == "auto":
            return "Auto Detect"
        return SHORT.get(k) or (self.types.get(k) or {}).get("name") or k

    def change_type(self, k: str) -> None:
        """Ganti jenis. Bila sudah ada baris (jenis salah terdeteksi): baris lama dibuang lalu borang dibaca ulang AI."""
        if not self.cur or k == self.cur["doc"]["type"]:
            return
        n = len(self.cur["rows"])
        nv = sum(1 for r in self.cur["rows"] if r["verified"])
        if n and not ask(self, f"Ganti jenis menjadi {self.types[k]['name']}?\n\n{n} baris hasil baca sekarang"
                               + (f" (termasuk {nv} yang sudah diverifikasi)" if nv else "") + " akan dibuang, lalu borang dibaca ulang oleh AI "
                               "dengan kolom jenis yang benar."):
            return
        try:
            self.cur = api.call("/core/forms/update", {"folder": self.folder, "id": self.cur["doc"]["id"],
                                                       "values": {"type": k, "clear": bool(n)}, "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.tbl = ""
        self.refresh()
        self._sync_list()
        self.toast(f"Jenis borang diganti: {self.types[k]['name']}", 3000)
        if n:
            self.run_ai()

    def detect_type(self) -> None:
        """Tanya AI jenis borang yang dibuka (jawaban satu kata; tidak membaca isi)."""
        if not self.cur or not self._ai_ready():
            return
        ai = self.win.ai
        did, folder = self.cur["doc"]["id"], self.folder
        self.toast("AI menentukan jenis borang…", 4000)

        def ok(j):
            if folder != self.folder:
                return
            if self.cur and self.cur["doc"]["id"] == did:
                self.cur = j
                self.tbl = ""
                self.refresh()
            self._sync_list()
            self.toast(f"Jenis terdeteksi: {self.types[j['doc']['type']]['name']}", 4000)
        run_bg(api.call, "/core/forms/detect", {"folder": folder, "id": did, "host": ai.host.text().strip(), "model": ai.model(), "by": self.by()},
               ok=ok, err=lambda e: say(self, "Jenis tidak terdeteksi:\n" + e, warn=True))

    def reload_types(self) -> None:
        """Muat ulang daftar jenis (setelah template disimpan / dihapus) tanpa mengganti borang yang dibuka."""
        if not self.folder:
            return
        try:
            j = api.call("/core/forms/open", {"folder": self.folder})
        except api.ApiError:
            return
        cur = self.cur["doc"]["id"] if self.cur else None
        keep = self.cbNew.currentData()
        self.types = j["types"]
        self.cbNew.blockSignals(True)
        self.cbNew.clear()
        self.cbNew.addItem(TYPE_LABEL["auto"], "auto")
        for k, t in self.types.items():
            self.cbNew.addItem(t["name"], k)
        self.cbNew.setCurrentIndex(max(0, self.cbNew.findData(keep)))
        self.cbNew.blockSignals(False)
        self.typeList.blockSignals(True)
        self.typeList.clear()
        for k, nm in [("auto", TYPE_LABEL["auto"])] + [(k, TYPE_LABEL.get(k, t["name"])) for k, t in self.types.items()]:
            it = QListWidgetItem(f"{TYPE_ICON.get(k, '◇')}   {nm}")
            it.setData(Qt.UserRole, k)
            self.typeList.addItem(it)
        self.typeList.setCurrentRow(self.cbNew.currentIndex())
        self.typeList.setFixedHeight(min(32 * 9, 30 * max(1, self.typeList.count()) + 8))
        self.typeList.blockSignals(False)
        self.pgHist.set_types(self.types)
        self.docs = j["docs"]
        self._fill_list()
        if cur is not None:
            self.select_doc(cur)

    def select_doc(self, did: int) -> bool:
        for i in range(self.lst.count()):
            if self.lst.item(i).data(Qt.UserRole) == did:
                self.lst.setCurrentRow(i)
                self._pick(i)
                return True
        return False

    def show_page(self, i: int) -> None:
        """Navigasi Borang | Riwayat | Template | Pengaturan | Bantuan."""
        self.pages.setCurrentIndex(i)
        for j, b_ in enumerate(self.navBtns):
            b_.setChecked(j == i)
        if i == 1:
            self.pgHist.refresh()
        elif i == 2:
            self.pgTpl.refresh()
        elif i == 3:
            self.pgSet.refresh()

    def _crop_mode(self, on: bool) -> None:
        if on and (not self.cur or not self.view.w):
            self.vb["crop"].setChecked(False)
            return
        self.view.set_tool(CropTool(self.view, self._crop_done) if on else None)
        if on:
            self.toast("Tarik kotak mengelilingi TABEL borang (judul kolom ikut). Lepas tombol mouse = simpan.", 5000)

    def _crop_done(self, cr: list) -> None:
        self.vb["crop"].setChecked(False)
        self.save_crop(cr)

    def save_crop(self, cr) -> None:
        if not self.cur:
            return
        try:
            self.cur = api.call("/core/forms/update", {"folder": self.folder, "id": self.cur["doc"]["id"], "values": {"crop": cr}, "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        c = self.cur["doc"].get("crop")
        self.view.show_crop(c)
        self._crop_buttons()
        self._sync_list()
        self.toast("Area dipotong — AI hanya membaca bagian ini. Klik ✦ Baca dengan AI." if c else
                   ("Potongan dihapus — AI membaca seluruh foto." if not cr else "Kotak terlalu kecil — potongan tidak disimpan."), 4000)

    def _crop_buttons(self) -> None:
        has = bool(self.cur and self.cur["doc"].get("crop"))
        self.vb["uncrop"].setEnabled(has)
        self.vb["cropall"].setEnabled(has)
        self.vb["crop"].setText("✂ Potong ulang" if has else "✂ Potong")

    def crop_to_others(self, scope: str) -> None:
        """Potongan borang ini dipakai juga untuk halaman lain dari file yang sama, atau borang sejenis yang belum dipotong."""
        if not self.cur or not self.cur["doc"].get("crop"):
            return
        me = self.cur["doc"]
        if scope == "file":
            ids = [d["id"] for d in self.docs if d["id"] != me["id"] and d.get("src") and d.get("src") == me.get("src")]
        else:
            ids = [d["id"] for d in self.docs if d["id"] != me["id"] and d["type"] == me["type"] and not d.get("crop")]
        if not ids:
            say(self, "Tidak ada borang lain yang cocok.")
            return
        if not ask(self, f"Pakai potongan ini untuk {len(ids)} borang lain?\nPeriksa hasilnya per borang — posisi tabel di foto bisa berbeda."):
            return
        for i in ids:
            try:
                api.call("/core/forms/update", {"folder": self.folder, "id": i, "values": {"crop": me["crop"]}, "by": self.by()})
            except api.ApiError:
                pass
        self._sync_list()
        self.toast(f"Potongan dipakai di {len(ids)} borang lain", 3500)

    def _zoom_pct(self) -> None:
        self.vb["pct"].setText(f"{round(self.view.transform().m11() * 100)}%" if self.view.w else "–")

    def _focus(self, on: bool) -> None:
        """Fokus scan: panel kiri & kanan disembunyikan (tombol ⛶ lagi = kembali)."""
        self.left.setVisible(not on)
        self.right.setVisible(not on)
        QTimer.singleShot(0, lambda: (self.view.fit(), self._zoom_pct()))

    def _queue_bar(self) -> None:
        """Bilah bawah: jumlah antre / diproses / selesai di sesi ini, progres, jam selesai terakhir."""
        if not hasattr(self, "qInfo"):
            return
        run = 1 if self.ai_did is not None else 0
        nq = len(self.ai_q)
        tot = self.q_done + run + nq
        if not run and not nq:
            self.qInfo.setText(f"Antrean AI kosong · {self.q_done} borang selesai dibaca sesi ini" if self.q_done else "Antrean AI kosong")
            self.qBar.setRange(0, 1)
            self.qBar.setValue(1 if self.q_done else 0)
            self.qPct.setText("")
        else:
            self.qInfo.setText(f"{nq} file dalam antrean  |  {run} memproses  |  {self.q_done} selesai")
            part = 0.0
            if run:
                part = min(0.95, (time.time() - self.ai_t0) / max(20.0, self._est_secs()))
            pct = (self.q_done + part) / max(1, tot)
            self.qBar.setRange(0, 1000)
            self.qBar.setValue(int(pct * 1000))
            self.qPct.setText(f"{round(pct * 100)}%")
        self.qDone.setText(f"● Selesai: {self.q_last}" if self.q_last else "")
        self.bCancel.setEnabled(bool(nq))

    def cancel_ai(self) -> None:
        n = len(self.ai_q)
        self.ai_q = []
        self._ai_buttons()
        self._relabel()
        if n:
            self.toast(f"{n} borang dikeluarkan dari antrean AI" + (" — borang yang sedang dibaca tetap diselesaikan" if self.ai_did is not None else ""), 4000)

    def _goto_issue(self, it: QListWidgetItem) -> None:
        tgt = it.data(Qt.UserRole)
        if not tgt or not self.cur:
            return
        rid, k, tbl = tgt
        self.tabs.setCurrentIndex(0)
        if rid is None:
            e = self.hdrEd.get(k)
            if e:
                self.hdrFold.setChecked(True)
                e.setFocus()
            return
        if tbl != self.tbl:
            self.tbl = tbl
            self.refresh()
        self.tblFold.setChecked(True)
        cols = [c for c, _l in self.cols(self.types[self.cur["doc"]["type"]])]
        for i in range(self.t.rowCount()):
            ck = self.t.item(i, 0)
            if ck and ck.data(Qt.UserRole) == rid:
                self.t.setCurrentCell(i, 1 + cols.index(k) if k in cols else 1)
                self.t.setFocus()
                break

    # ---------------------------------------------------------------- tampil
    def refresh(self) -> None:
        c = self.cur
        if not c:
            return
        d = c["doc"]
        t = self.types[d["type"]]
        self.title.setText(f"<b>{_esc(d['name'])}</b> · {_esc(t['name'])}")
        if d["id"] == self.ai_did:
            self._ai_tick()
        elif d["id"] in self.ai_q:
            self.aiInfo.setText(f"Menunggu giliran AI (antre #{self.ai_q.index(d['id']) + 1}). Tabel akan diganti hasil AI.")
        elif d["status"] == "done":
            self.aiInfo.setText(f"Dibaca AI {_esc(d.get('ai_model') or '')} · {'-' if d.get('ai_secs') is None else round(d['ai_secs'])} dtk · {_esc(d.get('ai_at') or '')}"
                                + (f" · catatan AI: {_esc(d['ai_note'])}" if d.get("ai_note") else "") + self._perf_html(d["id"]))
        elif d["status"] == "error":
            self.aiInfo.setText(f"<span style='color:{theme.C['er']}'>AI gagal: {_esc(d.get('error') or '')}</span> — tabel tidak diisi.")
        else:
            self.aiInfo.setText("Belum dibaca AI. Putar scan bila perlu (↻), lalu ✦ Baca dengan AI — atau isi tabel manual.")
        self.aiInfo.setTextFormat(Qt.RichText)
        self._header(d, t)
        tbs = [("", "Aktivitas" if d["type"] == "ddr" else "Tabel utama")] + [(k, x["name"]) for k, x in (t.get("tables") or {}).items()]
        if self.tbl not in [k for k, _n in tbs]:
            self.tbl = ""
        self.cbTbl.blockSignals(True)
        self.cbTbl.clear()
        for k, n in tbs:
            self.cbTbl.addItem(f"{n} ({sum(1 for r in c['rows'] if (r.get('tbl') or '') == k)})", k)
        self.cbTbl.setCurrentIndex(max(0, self.cbTbl.findData(self.tbl)))
        self.cbTbl.blockSignals(False)
        self.tblRow.setVisible(len(tbs) > 1)
        rows_h = (len(t["header"]) + 1) // 2
        self.hdrScroll.setMaximumHeight(min(128, 8 + 30 * rows_h))
        self.hdrScroll.setMinimumHeight(min(128, 8 + 30 * rows_h))
        self._summary(c.get("summary"))
        self._table(d, t, [r for r in c["rows"] if (r.get("tbl") or "") == self.tbl], c["valid"])
        self._pivot(c.get("pivot"))
        self.tabs.setTabEnabled(2, bool(c.get("pivot")))
        self._banner(d, t, c)
        self._valid_list(d, t, c)
        self._kpis(d, c)
        self.tblFold.setText(f"Data {dict(tbs).get(self.tbl, 'Tabel')}"
                             f" ({sum(1 for r in c['rows'] if (r.get('tbl') or '') == self.tbl)} baris)")
        self.tr.set_doc(d)

    def _banner(self, d: dict, t: dict, c: dict) -> None:
        """Status ekstraksi + keyakinan AI (porsi isian yang tidak ditandai ragu)."""
        if d["id"] == self.ai_did:
            k, ic, ti = "run", "⟳", "AI sedang membaca borang ini"
        elif d["id"] in self.ai_q:
            k, ic, ti = "run", "…", f"Menunggu antrean AI (#{self.ai_q.index(d['id']) + 1})"
        elif d["status"] == "error":
            k, ic, ti = "er", "!", "AI gagal membaca"
        elif d["status"] == "done":
            k, ic, ti = "ok", "✓", "Ekstraksi selesai"
        else:
            k, ic, ti = "new", "○", "Belum dibaca AI" if not c["rows"] else "Diisi manual"
        sub = f"Jenis dokumen: {t['name']}"
        if d["status"] == "done" and d.get("ai_model"):
            sub += f" · {d['ai_model']}" + (f" · {round(d['ai_secs'])} dtk" if d.get("ai_secs") is not None else "")
        self.banner.setProperty("k", k)
        theme.repolish(self.banner)
        self.bnIcon.setText(ic)
        self.bnTitle.setText(ti)
        self.bnSub.setText(sub)
        nbad = len(c["valid"]["rows"]) + len(c["valid"]["header"])
        main = [r for r in c["rows"] if not r.get("tbl")]
        heavy = d["status"] == "done" and bool(main) and nbad >= max(3, 0.5 * len(main)) and not any(r["verified"] for r in main)
        if heavy:
            self.bnFixMenu.clear()
            for k_, t_ in self.types.items():
                if k_ != d["type"]:
                    self.bnFixMenu.addAction(t_["name"], lambda k_=k_: self.change_type(k_))
            self.bnSub.setText(sub + f" · {nbad} baris / isian bergalat — mungkin jenis borang salah")
        self.bnFix.setVisible(heavy)
        cells = sum(1 for r in c["rows"] for v in r["data"].values() if str(v or "").strip())
        cells += sum(1 for v in d["header"].values() if str(v or "").strip())
        unc = sum(len(r.get("unc") or []) for r in c["rows"]) + len(d.get("hdr_unc") or [])
        if d["status"] == "done" and cells:
            pc = max(0, round(100 * (1 - unc / cells)))
            self.bnConf.setText(f"{pc}%")
            self.bnConf.setProperty("k", "ok" if pc >= 90 else ("mid" if pc >= 70 else "lo"))
        else:
            self.bnConf.setText("–")
            self.bnConf.setProperty("k", "")
        theme.repolish(self.bnConf)

    def _valid_list(self, d: dict, t: dict, c: dict) -> None:
        """Tab Validasi: semua galat (header & baris, semua tabel) — klik = lompat ke sel."""
        v = c["valid"]
        labs = {k: lab for k, lab, _t in t["header"]}
        labr = {"": {k: lab for k, lab, _t in t["rows"]}}
        for tk, tt in (t.get("tables") or {}).items():
            labr[tk] = {k: lab for k, lab, _t in tt["rows"]}
        self.vList.clear()
        for k, m in v["header"].items():
            it = QListWidgetItem(f"⚠  Header · {labs.get(k, k)}: {m}")
            it.setData(Qt.UserRole, (None, k, ""))
            self.vList.addItem(it)
        pos: dict[str, int] = {}
        n_unc = 0
        for r in c["rows"]:
            tb = r.get("tbl") or ""
            pos[tb] = pos.get(tb, 0) + 1
            n_unc += 1 if r.get("unc") else 0
            for k, m in (v["rows"].get(r["id"]) or v["rows"].get(str(r["id"])) or {}).items():
                nm = "" if not tb else f"{(t.get('tables') or {}).get(tb, {}).get('name', tb)} · "
                it = QListWidgetItem(f"⚠  {nm}Baris {pos[tb]} · {labr.get(tb, {}).get(k, k)}: {m}")
                it.setData(Qt.UserRole, (r["id"], k, tb))
                self.vList.addItem(it)
        n = self.vList.count()
        er = theme.C["er"]
        nv = sum(1 for r in c["rows"] if r["verified"])
        self.vSum.setText((f"<span style='color:{er}'><b>{n}</b> galat validasi</span>" if n else "<b>Validasi bersih</b> — tidak ada galat")
                          + f" · {len(c['rows'])} baris · {nv} diverifikasi · {n_unc} baris ragu (kuning)")
        self.tabs.setTabText(1, f"Validasi ({n})" if n else "Validasi ✓")

    def _kpi_card(self, i: int, label: str, val: str, unit: str = "", warn: bool = False) -> None:
        f = QFrame()
        f.setObjectName("fmKpi")
        f.setProperty("warn", warn)
        lv = QVBoxLayout(f)
        lv.setContentsMargins(8, 5, 8, 5)
        lv.setSpacing(0)
        a = QLabel(label)
        a.setObjectName("fmKpiL")
        b = QLabel(val)
        b.setObjectName("fmKpiV")
        lv.addWidget(a)
        lv.addWidget(b)
        if unit:
            u = QLabel(unit)
            u.setObjectName("fmKpiL")
            lv.addWidget(u)
        self.kpi.addWidget(f, i // 5, i % 5)

    def _kpis(self, d: dict, c: dict) -> None:
        """Kartu ringkasan: Daily Drilling Report = jam & meter; Ore / ROM = ritase & tonase; RC = interval & meter."""
        while self.kpi.count():
            w_ = self.kpi.takeAt(0).widget()
            if w_:
                w_.deleteLater()
        rows = [r for r in c["rows"] if not (r.get("tbl") or "")]
        sm = c.get("summary") or {}
        cards: list[tuple] = []

        def num(x) -> float:
            try:
                return float(str(x).replace(",", "."))
            except (TypeError, ValueError):
                return 0.0
        if d["type"] == "ddr" and sm:
            cards = [("Total aktivitas", f"{len(rows)}", "baris"), ("Jam borang", f"{sm.get('jam_borang', 0):g}", "jam"),
                     ("Jam aktivitas", f"{sm.get('jam_aktivitas', 0):g}", "jam", abs((sm.get("jam_borang") or 0) - (sm.get("jam_aktivitas") or 0)) > 0.5),
                     ("Drilling", f"{sm.get('jam_drilling', 0):g}", "jam"), ("Meterage", f"{sm.get('meter', 0):g}", "m"),
                     ("Jumlah lubang", f"{sm.get('n_lubang', 0)}", "lubang"), ("Meter / jam drilling", f"{sm.get('m_per_jam') or 0:g}", "m/jam")]
        elif d["type"] in ("ore", "rom"):
            ton = sum(num(r["data"].get("ton")) for r in rows)
            kel: dict[str, float] = {}
            for r in rows:
                kk = str(r["data"].get("kelas") or "").strip()
                if kk:
                    kel[kk] = kel.get(kk, 0) + num(r["data"].get("ton"))
            cards = [("Ritase", f"{len(rows)}", "truk"), ("Total tonase", f"{ton:g}", "ton")]
            cards += [(f"Kelas {k}", f"{v:g}", "ton") for k, v in sorted(kel.items(), key=lambda x: -x[1])[:5]]
        elif d["type"] in ("map", "chn", "dpr") or not self.types.get(d["type"], {}).get("builtin", True):
            recs = [r for r in c.get("recs") or [] if not r.get("_tbl")]
            if d["type"] == "chn":
                chs = {r.get("channel_id") for r in recs} - {"", None}
                cards = [("Sampel", f"{len(recs)}", "baris"), ("Channel", f"{len(chs)}", "channel"),
                         ("Panjang", f"{sum(r.get('panjang') or 0 for r in recs):g}", "m"),
                         ("Sampel QAQC", f"{sum(1 for r in recs if r.get('qaqc'))}", "STD / BLANK / DUP")]
            elif d["type"] == "dpr":
                cards = [("Lubang", f"{len({r.get('hole_id') for r in recs} - {'', None})}", "hole"),
                         ("Meter shift", f"{sum(r.get('meter') or 0 for r in recs):g}", "m"),
                         ("Selesai", f"{sum(1 for r in recs if r.get('status') == 'Selesai')}", "lubang"),
                         ("Masih dibor", f"{sum(1 for r in recs if r.get('status') == 'Drilling')}", "lubang")]
            elif d["type"] == "map":
                cards = [("Stasiun", f"{len(recs)}", "titik"), ("Sampel", f"{sum(1 for r in recs if r.get('sample_id'))}", "diambil"),
                         ("Data struktur", f"{sum(1 for r in recs if r.get('strike') is not None)}", "strike / dip"),
                         ("Litologi", f"{len({r.get('litologi') for r in recs} - {'', None})}", "jenis")]
            else:
                cards = [("Baris", f"{len(recs)}", "baris")]
                if any("panjang" in r for r in recs):
                    cards.append(("Panjang", f"{sum(r.get('panjang') or 0 for r in recs):g}", "m"))
        elif d["type"] == "rc":
            holes = {str(r["data"].get("hole_id") or "").strip() for r in rows} - {""}
            met = sum(max(0.0, num(r["data"].get("to_m")) - num(r["data"].get("from_m"))) for r in rows)
            qa = sum(1 for r in rows if re.search(r"std|blank|dup", str(r["data"].get("remark") or ""), re.I))
            cards = [("Interval", f"{len(rows)}", "baris"), ("Lubang", f"{len(holes)}", "hole"), ("Meter dilog", f"{met:g}", "m"),
                     ("Sampel QAQC", f"{qa}", "STD / BLANK")]
        nv = sum(1 for r in c["rows"] if r["verified"])
        cards.append(("Terverifikasi", f"{nv}/{len(c['rows'])}", "baris", nv < len(c["rows"])))
        for i, cd in enumerate(cards):
            self._kpi_card(i, cd[0], cd[1], cd[2] if len(cd) > 2 else "", bool(cd[3]) if len(cd) > 3 else False)

    def _header(self, d: dict, t: dict) -> None:
        keys = [k for k, _l, _t in t["header"]]
        if list(self.hdrEd) != keys:
            while self.hdrGrid.count():
                w_ = self.hdrGrid.takeAt(0).widget()
                if w_:
                    w_.deleteLater()
            self.hdrEd = {}
            half = (len(t["header"]) + 1) // 2
            for i, (k, lab, _ty) in enumerate(t["header"]):
                row, col = (i, 0) if i < half else (i - half, 2)
                lb = QLabel(lab)
                lb.setObjectName("fmHLab")
                e = QLineEdit()
                e.editingFinished.connect(lambda k=k: self._hdr_save(k))
                self.hdrGrid.addWidget(lb, row, col)
                self.hdrGrid.addWidget(e, row, col + 1)
                self.hdrEd[k] = e
            self.hdrGrid.setColumnStretch(1, 1)
            self.hdrGrid.setColumnStretch(3, 1)
        v = self.cur["valid"]["header"]
        for k, e in self.hdrEd.items():
            if not e.hasFocus():
                e.setText(str(d["header"].get(k) or ""))
            bg = BAD_BG if k in v else (UNC_BG if k in d.get("hdr_unc", []) else "")
            e.setStyleSheet(f"background:{bg};color:#141a26" if bg else "")
            e.setToolTip(v.get(k) or ("AI ragu membaca isian ini" if k in d.get("hdr_unc", []) else ""))

    def cols(self, t: dict) -> list[tuple[str, str]]:
        spec = t["rows"] if not self.tbl else t["tables"][self.tbl]["rows"]
        return [(k, lab) for k, lab, _ty in spec]

    def _tbl_changed(self, _i: int) -> None:
        self.tbl = self.cbTbl.currentData() or ""
        self.refresh()

    def _summary(self, sm: dict | None) -> None:
        """Ringkasan Daily Drilling Report: jam di borang vs jumlah durasi aktivitas per kelompok, meter, m / jam drilling."""
        self.sumInfo.setVisible(bool(sm))
        if not sm:
            return
        er = theme.C["er"]
        cells = []
        for k in ("wh", "dl", "mntc", "bd", "rain", "std"):
            b, a = sm.get(k), sm.get(k + "_akt") or 0
            if b is None and not a:
                continue
            off = b is not None and abs(b - a) > 0.5
            cells.append(f"<b>{k.upper()}</b> {'' if b is None else f'{b:g}'} / {a:g}" if not off else
                         f"<span style='color:{er}'><b>{k.upper()}</b> {b:g} / {a:g}</span>")
        self.sumInfo.setText("Jam borang / dari aktivitas: " + " · ".join(cells)
                             + f"<br>Aktivitas {sm['jam_aktivitas']:g} jam · drilling {sm['jam_drilling']:g} jam · "
                             f"<b>{sm['n_lubang']}</b> lubang · <b>{sm['meter']:g} m</b>"
                             + (f" · {sm['m_per_jam']:g} m/jam" if sm.get("m_per_jam") else "")
                             + (f" · HM {sm['hm_running']:g}" if sm.get("hm_running") is not None else ""))

    def _table(self, d: dict, t: dict, rows: list[dict], valid: dict) -> None:
        self._filling = True
        cols = self.cols(t)
        derived = ([("tanggal_muat", "Tgl muat")] if d["type"] in ("ore", "rom") else
                   [("durasi", "Jam"), ("kelompok", "Kelompok")] if d["type"] == "ddr" and not self.tbl else
                   [("meter", "Meter")] if d["type"] == "ddr" else [])
        tb = self.t
        tb.clear()
        tb.setColumnCount(1 + len(cols) + len(derived))
        tb.setHorizontalHeaderLabels(["✓"] + [lab for _k, lab in cols] + [lab for _k, lab in derived])
        tb.setRowCount(len(rows))
        for j in range(tb.columnCount()):
            tb.setItemDelegateForColumn(j, self._plain)
        if "kategori" in [k for k, _l in cols]:
            tb.setItemDelegateForColumn(1 + [k for k, _l in cols].index("kategori"), self._katDel)
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
                dv = (recs.get(r["id"]) or {}).get(k)
                it = QTableWidgetItem("" if dv is None else (f"{dv:g}" if isinstance(dv, float) else str(dv)))
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
        self.pvNote.setText("Pivot dari borang ini (semua baris, terverifikasi maupun belum). Pivot gabungan semua borang ada di "
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
            j = api.call("/core/forms/rows", {"folder": self.folder, "id": self.cur["doc"]["id"], "rows": rows, "by": self.by(), "tbl": self.tbl})
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
            for k in ("hole_id", "tanggal"):  # lubang yang sama
                if ref["data"].get(k):
                    new["data"][k] = ref["data"][k]
            m = re.match(r"^(.*?)(\d+)(\D*)$", ref["data"].get("sample_id") or "")
            if m:
                new["data"]["sample_id"] = f"{m.group(1)}{int(m.group(2)) + 1:0{len(m.group(2))}d}{m.group(3)}"
        if self.cur["doc"]["type"] == "ddr" and not self.tbl and rows:  # kegiatan berikutnya mulai saat kegiatan sebelumnya selesai
            ref = rows[(at if at is not None else len(rows)) - 1] if (at or len(rows)) else rows[-1]
            new["data"] = {"mulai": ref["data"].get("selesai") or ""}
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
    def _ai_ready(self) -> bool:
        ai = self.win.ai
        if not ai.info or not ai.info.get("running") or not ai.model():
            self.win.open_ai()
            return False
        return True

    def run_ai(self) -> None:
        """Baca borang yang sedang dibuka (masuk antrean paling depan bila AI sedang membaca borang lain)."""
        if not self.cur or not self._ai_ready():
            return
        did = self.cur["doc"]["id"]
        if did == self.ai_did or did in self.ai_q:
            return
        n_ver = sum(1 for r in self.cur["rows"] if r["verified"])
        if self.cur["rows"] and not ask(self, f"Baca ulang dengan AI? {len(self.cur['rows'])} baris yang ada (termasuk {n_ver} terverifikasi) "
                                              "akan diganti hasil AI. Isian header yang Anda edit tetap."):
            return
        self.ai_q.insert(0, did)
        self._ai_next()

    def run_ai_all(self) -> None:
        """Antrekan semua borang yang belum dibaca / gagal; dibaca satu per satu di latar belakang."""
        if not self.folder or not self._ai_ready():
            return
        todo = [d["id"] for d in self.docs if d["status"] in ("pending", "error") and not d.get("n_rows")
                and d["id"] != self.ai_did and d["id"] not in self.ai_q]
        if not todo:
            say(self, "Semua borang sudah dibaca AI (atau sudah ada isinya).\nUntuk membaca ulang satu borang, buka borangnya lalu klik ✦ Baca dengan AI.")
            return
        if self.ai_did is None and not self.ai_q:
            self.q_done = 0
        self.ai_q += todo
        self.toast(f"{len(todo)} borang masuk antrean AI. Anda bisa memeriksa borang lain selama AI membaca.", 5000)
        self._ai_next()

    def _perf_html(self, did: int) -> str:
        """Ringkasan kecepatan baca terakhir + peringatan bila model tidak seluruhnya di GPU (penyebab utama baca lambat)."""
        p = self.perf.get(did)
        if not p:
            return ""
        t = (f"<br>{p['tokens']} token jawaban" + (f" · {p['tok_s']:g} token/dtk" if p.get("tok_s") else "")
             + f" · gambar {p['px']} px · konteks {p['num_ctx']}"
             + (f" · bagian kosong dibuang {round(p['trim'] * 100)}%" if p.get("trim") else "")
             + (" · header dari halaman lain PDF ini (kuning)" if p.get("hdr_prev") else ""))
        g = p.get("gpu")
        if g == 0:  # tanpa GPU NVIDIA / AMD yang didukung Ollama (mis. Intel Iris Xe): seluruhnya di CPU
            t += (f"<br><span style='color:{theme.C['half']}'><b>AI berjalan di CPU</b> (kartu grafis tidak dipakai Ollama). "
                  "Supaya lebih cepat: pilih <b>Cepat</b>, pakai model kecil <b>qwen3-vl:2b-instruct</b>, tutup aplikasi lain agar RAM lega, "
                  "atau arahkan alamat Ollama (dialog AI) ke komputer lain yang punya GPU NVIDIA.</span>")
        elif g is not None and g < 100:
            t += (f"<br><span style='color:{theme.C['er']}'><b>Model hanya {g:g}% di GPU, sisanya di CPU — inilah yang membuat lambat.</b> "
                  "Tutup aplikasi lain yang memakai GPU (browser, Leapfrog, Surpac 3D), pilih kecepatan <b>Cepat</b>, atau pakai model "
                  "yang lebih kecil (mis. qwen3-vl:2b-instruct) di dialog AI.</span>")
        elif g is not None:
            t += " · 100% di GPU"
        return t

    def _ai_buttons(self) -> None:
        n = len(self.ai_q) + (1 if self.ai_did is not None else 0)
        self.bAIAll.setText(f"Antrean AI: {n} borang" if n else "Baca Semua dengan AI")
        self._queue_bar()
        cur = self.cur["doc"]["id"] if self.cur else None
        busy = cur is not None and (cur == self.ai_did or cur in self.ai_q)
        self.bAI.setText("AI membaca borang…" if cur is not None and cur == self.ai_did else ("Menunggu antrean AI…" if busy else "✦ Baca dengan AI"))
        self.bAI.setEnabled(bool(self.cur) and not busy)

    def _ai_tick(self) -> None:
        if self.ai_did is None:
            return
        for i in range(self.lst.count()):
            it = self.lst.item(i)
            if it.data(Qt.UserRole) == self.ai_did:
                d = next((x for x in self.docs if x["id"] == self.ai_did), None)
                if d:
                    it.setData(ROLE_D, self._info(d))
        self._queue_bar()
        if self.cur and self.cur["doc"]["id"] == self.ai_did:
            sec = int(time.time() - self.ai_t0)
            self.aiInfo.setTextFormat(Qt.PlainText)
            self.aiInfo.setText(f"AI membaca borang ini… {sec // 60}:{sec % 60:02d}"
                                + (f" · {len(self.ai_q)} borang lagi di antrean" if self.ai_q else "")
                                + ". Anda bisa membuka borang lain sementara menunggu.")

    def _ai_next(self) -> None:
        if self.ai_did is not None or not self.ai_q or not self.folder:
            self._ai_buttons()
            self._relabel()
            return
        ai = self.win.ai
        did, folder = self.ai_q.pop(0), self.folder
        self.ai_did, self.ai_busy, self.ai_t0 = did, True, time.time()
        body = {"folder": folder, "id": did, "host": ai.host.text().strip(), "model": ai.model(), "extra": ai.extra.toPlainText(),
                "max_px": int(self.cbSpeed.currentData() or 1600), "by": self.by(),
                "trim": bool(SET.get("fmTrim", True)), "hdr_prev": bool(SET.get("fmHdrPrev", True))}
        self.ai_clock.start()
        self._ai_buttons()
        self._relabel()
        if self.cur and self.cur["doc"]["id"] == did:
            self.refresh()

        def fin():
            self.ai_did, self.ai_busy = None, False
            self.ai_clock.stop()
            self.q_done += 1
            self.q_last = time.strftime("%H:%M")
            if folder == self.folder:
                self._sync_list()
                QTimer.singleShot(0, self._ai_next)

        def ok(j):
            fin()
            if folder != self.folder:
                return
            if j.get("perf"):
                self.perf[did] = j["perf"]
            if self.cur and self.cur["doc"]["id"] == did:
                self.cur = j
                self.refresh()
            secs = j["doc"].get("ai_secs")
            self.toast(f"AI selesai: {j['doc']['name']} · {len(j['rows'])} baris"
                       + (f" · {round(secs)} dtk" if secs is not None else "") + " — periksa sel kuning / merah lalu verifikasi", 5000)

        def err(e):
            fin()
            if folder != self.folder:
                return
            if self.cur and self.cur["doc"]["id"] == did:
                self._pick(self.lst.currentRow())
            if self.ai_q:
                self.toast("AI gagal membaca satu borang; lanjut ke borang berikutnya. " + e[:120], 6000)
            else:
                say(self, "AI gagal membaca borang (tabel tidak diisi):\n" + e, warn=True)
        run_bg(api.call, "/core/forms/ai", body, ok=ok, err=err)

    def _relabel(self) -> None:
        for i in range(self.lst.count()):
            it = self.lst.item(i)
            d = next((x for x in self.docs if x["id"] == it.data(Qt.UserRole)), None)
            if d:
                self._set_item(it, d)
        self._queue_bar()

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
        ext, filt = {"xlsx": (".xlsx", "Excel (*.xlsx)"), "csv": ((".zip", "CSV dalam ZIP (*.zip)") if ft in MULTI else (".csv", "CSV (*.csv)")), "sqlite": (".db", "SQLite (*.db *.sqlite)"),
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

