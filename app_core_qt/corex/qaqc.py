"""Ruang kerja QAQC Database (DB-Ex versi Qt): QAQC sampel lab (CRM, Blank, Duplikat) dan QAQC data bor.

Bilah atas: Impor (workbook QAQC lengkap atau satu tabel), Ekspor Excel + grafik PNG, Laporan PDF. Tab: Dashboard, CRM, Blank,
Duplikat, Batch lab, Lampiran, Data (semua tabel bisa diedit / ditempel dari Excel), Data bor, Panel kontrol. Data lewat rute /core/qaqc/* (backend
core_qaqc); laporan PDF dicetak dengan QTextDocument (qaqc_pdf.py)."""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QScrollArea, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from . import api, theme
from .card import _esc, btn
from .dialogs import ask, say
from .util import SET, log, run_bg, show_in_folder

NUM_RE = re.compile(r"^\s*[<>]?\s*[-+]?(\d+([.,]\d*)?|[.,]\d+)([eE][-+]?\d+)?\s*$")
LVL_BG = {0: "#F2F2F2", 1: "#E2EFDA", 2: "#FFF2CC", 3: "#F4CCCC"}
CAT_BG = {"PASS": "#E2EFDA", "WARN": "#FFF2CC", "WARNING": "#FFF2CC", "FAIL": "#F4CCCC", "MERAH": "#F4CCCC", "KUNING": "#FFF2CC", "INFO": "#EEF3F8"}
TARGETS = [("auto", "Workbook QAQC (semua sheet dikenali)"), ("master_crm", "Master_CRM"), ("assay_import", "Assay_Import"), ("crm_data", "CRM_Data"),
           ("blank_data", "Blank_Data"), ("dup_data", "Duplicate_Data")]
TABLE_NAMES = ["Master_CRM", "Assay_Import", "CRM_Data", "Blank_Data", "Duplicate_Data"]


def fmt(v, d: int = 4) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.{d}f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:g}"
    return str(v)


def fill(tw: QTableWidget, heads: list[str], rows: list[list], bg: list | None = None, edit: bool = False) -> None:
    tw.clear()
    tw.setColumnCount(len(heads))
    tw.setHorizontalHeaderLabels(heads)
    tw.setRowCount(len(rows))
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            it = QTableWidgetItem(fmt(v))
            if not edit:
                it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if bg and bg[i]:
                c = bg[i][j] if isinstance(bg[i], list) else bg[i]
                if c:
                    it.setBackground(QColor(c))
                    it.setForeground(QColor("#141a26"))
            tw.setItem(i, j, it)
    tw.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    tw.horizontalHeader().setStretchLastSection(True)


def table() -> QTableWidget:
    tw = QTableWidget(0, 0)
    tw.verticalHeader().setDefaultSectionSize(22)
    tw.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tw.setWordWrap(False)
    return tw


class Charts(QScrollArea):
    """Daftar grafik PNG dari backend (dimuat di latar belakang)."""

    def __init__(self, page: "QaqcPage"):
        super().__init__()
        self.pg = page
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        w = QWidget()
        self.v = QVBoxLayout(w)
        self.v.setContentsMargins(0, 4, 0, 4)
        self.v.addStretch(1)
        self.setWidget(w)
        self.labels: list[QLabel] = []
        self.gen = 0

    def show_charts(self, items: list[dict]) -> None:
        self.gen += 1
        gen = self.gen
        for lb in self.labels:
            lb.deleteLater()
        self.labels = []
        for c in items:
            lb = QLabel("Memuat grafik " + c["title"] + "…")
            lb.setAlignment(Qt.AlignCenter)
            lb.setObjectName("note")
            lb.setMinimumHeight(60)
            self.v.insertWidget(self.v.count() - 1, lb)
            self.labels.append(lb)
            folder = self.pg.folder
            run_bg(api.call, "/core/qaqc/chart", {"folder": folder, "kind": c["kind"], "key": c["key"]},
                   ok=lambda b, lb=lb, gen=gen: self._got(lb, b, gen), err=lambda e, lb=lb: lb.setText("Grafik gagal: " + e))

    def _got(self, lb: QLabel, b: bytes, gen: int) -> None:
        if gen != self.gen:
            return
        im = QImage.fromData(b, "PNG")
        w = max(400, self.viewport().width() - 12)
        pm = QPixmap.fromImage(im).scaledToWidth(min(w, im.width()), Qt.SmoothTransformation)
        lb.setPixmap(pm)
        lb.setFixedHeight(pm.height() + 8)  # jangan dipadatkan tata letak (grafik terpotong)
        lb.setProperty("png", b)


class QaqcPage(QWidget):
    def __init__(self, win) -> None:
        super().__init__()
        self.win = win
        self.folder = ""
        self.res: dict | None = None
        self.st: dict = {}
        self.labels: dict = {}
        self.cur_table = "Master_CRM"
        self._build()

    # ---------------------------------------------------------------- tata letak
    def _build(self) -> None:
        o = QVBoxLayout(self)
        o.setContentsMargins(0, 0, 0, 0)
        o.setSpacing(0)
        tb = QFrame()
        tb.setObjectName("fbar")
        h = QHBoxLayout(tb)
        h.setContentsMargins(10, 6, 10, 6)
        hd = QLabel("<b>QAQC DATABASE</b>")
        hd.setObjectName("note")
        h.addWidget(hd)
        self.cbTarget = QComboBox()
        for k, t in TARGETS:
            self.cbTarget.addItem(t, k)
        self.cbTarget.setToolTip("Tujuan impor. Workbook QAQC: sheet Master_CRM, Assay_Import, CRM_Data, Blank_Data, Duplicate_Data dibaca sekaligus. "
                                 "Data lama diperbarui per Sample_ID (duplikat per Duplicate_ID).")
        h.addWidget(self.cbTarget)
        self.bImp = btn("⇪ Impor…", "Impor file Excel (.xlsx / .xlsm) atau CSV / TXT", pri=True, sm=True)
        h.addWidget(self.bImp)
        h.addSpacing(10)
        self.sum = QLabel()
        self.sum.setObjectName("note")
        h.addWidget(self.sum, 1)
        self.bX = btn("⇩ Excel + grafik PNG", "Workbook QAQC (CRM_Data, Duplicate_Data, Blank_Data, CRM_Summary, Duplicate Summary, "
                      "Report_Appendix, QAQC_Dashboard, …) dan folder grafik PNG", sm=True)
        self.bPdf = btn("⇩ Laporan PDF", "Laporan QAQC: ringkasan eksekutif, lampu lalu lintas, data bor, CRM, blank, duplikat, batch, "
                        "dashboard dan lampiran A/B/C", pri=True, sm=True)
        h.addWidget(self.bX)
        h.addWidget(self.bPdf)
        o.addWidget(tb)
        self.tabs = QTabWidget()
        o.addWidget(self.tabs, 1)
        self.tabs.addTab(self._tab_dash(), "Dashboard")
        self.tCrm, self.cCrm, self.nCrm = self._tab_charts("CRM")
        self.tBlk, self.cBlk, self.nBlk = self._tab_charts("Blank")
        self.tDup, self.cDup, self.nDup = self._tab_charts("Duplikat")
        self.tabs.addTab(self._tab_batch(), "Batch lab")
        self.tabs.addTab(self._tab_app(), "Lampiran")
        self.tabs.addTab(self._tab_data(), "Data")
        self.tabs.addTab(self._tab_dh(), "Data bor")
        self.tabs.addTab(self._tab_panel(), "Panel kontrol")
        self.bImp.clicked.connect(self.import_files)
        self.bX.clicked.connect(self.export_xlsx)
        self.bPdf.clicked.connect(self.export_pdf)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.set_enabled(False)

    def _page(self) -> tuple[QWidget, QVBoxLayout]:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(6)
        return w, v

    def _note(self, text: str = "") -> QLabel:
        n = QLabel(text)
        n.setObjectName("note")
        n.setWordWrap(True)
        n.setTextFormat(Qt.RichText)
        return n

    def _tab_dash(self) -> QWidget:
        w, v = self._page()
        self.dHead = self._note()
        v.addWidget(self.dHead)
        self.dT = table()
        self.dT.setWordWrap(True)
        self.dT.setMaximumHeight(220)
        v.addWidget(self.dT)
        self.dWarn = self._note()
        v.addWidget(self.dWarn)
        self.dChart = Charts(self)
        v.addWidget(self.dChart, 1)
        return w

    def _tab_charts(self, name: str):
        w, v = self._page()
        n = self._note()
        v.addWidget(n)
        t = table()
        t.setMaximumHeight(230)
        v.addWidget(t)
        c = Charts(self)
        v.addWidget(c, 1)
        self.tabs.addTab(w, name)
        return t, c, n

    def _tab_batch(self) -> QWidget:
        w, v = self._page()
        self.bNote = self._note("Ringkasan per batch lab (Batch_ID dari Assay_Import, dicocokkan per Sample_ID). FAIL = ada CRM &gt; 3 SD atau "
                                "blank di atas cut-off; WARNING = CRM &gt; 2 SD atau duplikat gagal.")
        v.addWidget(self.bNote)
        self.bT = table()
        v.addWidget(self.bT, 1)
        return w

    def _tab_app(self) -> QWidget:
        w, v = self._page()
        r = QHBoxLayout()
        self.cbApp = QComboBox()
        for k, t in (("app_a", "Lampiran A — CRM WARNING & FAIL"), ("app_b", "Lampiran B — Blank FAIL"), ("app_c", "Lampiran C — Duplikat gagal")):
            self.cbApp.addItem(t, k)
        r.addWidget(self.cbApp)
        r.addStretch(1)
        v.addLayout(r)
        self.aT = table()
        v.addWidget(self.aT, 1)
        self.cbApp.currentIndexChanged.connect(lambda *_: self.show_app())
        return w

    def _tab_data(self) -> QWidget:
        w, v = self._page()
        r = QHBoxLayout()
        self.cbTbl = QComboBox()
        for t in TABLE_NAMES:
            self.cbTbl.addItem(t, t)
        r.addWidget(QLabel("Tabel:"))
        r.addWidget(self.cbTbl)
        self.bAddM = btn("+ Baris", "Tambah baris di bawah baris terpilih", sm=True)
        self.bDelR = btn("Hapus baris", "Hapus baris yang dipilih (tersimpan setelah Simpan)", sm=True)
        self.bPaste = btn("Tempel dari Excel", "Tempel sel yang disalin di Excel mulai dari sel terpilih (Ctrl+V). Bila baris pertama "
                          "berisi judul kolom, kolom dicocokkan menurut judulnya.", sm=True)
        self.bSaveM = btn("Simpan tabel", pri=True, sm=True)
        self.bUndo = btn("Batal", "Buang perubahan yang belum disimpan", sm=True)
        self.bClr = btn("Kosongkan tabel…", sm=True)
        for b_ in (self.bAddM, self.bDelR, self.bPaste, self.bSaveM, self.bUndo):
            r.addWidget(b_)
        r.addStretch(1)
        r.addWidget(self.bClr)
        v.addLayout(r)
        self.dataNote = self._note()
        v.addWidget(self.dataNote)
        self.tT = table()
        self.tT._cols = []
        self.tT.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tT.setSelectionMode(QAbstractItemView.ExtendedSelection)
        v.addWidget(self.tT, 1)
        self.tDirty = False
        self._nbad = 0
        self._tblShown = None
        self._marking = False
        self.cbTbl.currentIndexChanged.connect(lambda *_: self._switch_table())
        self.bAddM.clicked.connect(self.add_row)
        self.bDelR.clicked.connect(self.del_rows)
        self.bPaste.clicked.connect(lambda: self.paste_rows())
        self.bSaveM.clicked.connect(self.save_table)
        self.bUndo.clicked.connect(lambda: (self._set_dirty(False), self.show_table()))
        self.bClr.clicked.connect(self.clear_table)
        self.tT.itemChanged.connect(self._cell_changed)
        sc = QShortcut(QKeySequence.Paste, self.tT)
        sc.setContext(Qt.WidgetShortcut)  # editor sel tetap memakai Ctrl+V biasa
        sc.activated.connect(lambda: self.paste_rows())
        sc2 = QShortcut(QKeySequence.Delete, self.tT)
        sc2.setContext(Qt.WidgetShortcut)
        sc2.activated.connect(self._clear_cells)
        return w

    def _tab_dh(self) -> QWidget:
        w, v = self._page()
        r = QHBoxLayout()
        self.bDh = btn("Periksa data bor", "Periksa Collar, Survey, Assay, Geologi yang sudah diimpor lewat tombol Data bor", pri=True, sm=True)
        r.addWidget(self.bDh)
        self.dhInfo = self._note()
        r.addWidget(self.dhInfo, 1)
        v.addLayout(r)
        self.dhS = table()
        self.dhS.setMaximumHeight(240)
        v.addWidget(self.dhS)
        self.dhT = table()
        v.addWidget(self.dhT, 1)
        self.bDh.clicked.connect(self.run_dh)
        return w

    def _tab_panel(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(14, 10, 14, 10)
        v.addWidget(self._note("Batas penilaian dipakai untuk semua tab, ekspor Excel dan laporan PDF (tersimpan di proyek). Nilai bawaan "
                               "mengikuti workbook QAQC: cut-off blank 0,01; HARD maksimum 10 %; CRM Memuaskan ≥ 95 %; duplikat Memuaskan ≥ 90 %, "
                               "Marginal ≥ 50 %; blank Memuaskan ≥ 99 %."))
        box = QFrame()
        box.setObjectName("fld")
        self.form = QFormLayout(box)
        self.form.setContentsMargins(10, 8, 10, 8)
        self.ed: dict[str, QWidget] = {}
        v.addWidget(box)
        r = QHBoxLayout()
        self.bSet = btn("Simpan && hitung ulang", pri=True, sm=True)
        self.bReset = btn("Kembalikan bawaan", sm=True)
        r.addWidget(self.bSet)
        r.addWidget(self.bReset)
        r.addStretch(1)
        v.addLayout(r)
        self.r2 = self._note()
        v.addWidget(self.r2)
        v.addStretch(1)
        w.setWidget(inner)
        self.bSet.clicked.connect(self.save_settings)
        self.bReset.clicked.connect(self.reset_settings)
        return w

    # ---------------------------------------------------------------- util
    def by(self) -> str:
        return self.win.user()

    def set_enabled(self, on: bool) -> None:
        for w in (self.bImp, self.cbTarget, self.tabs):
            w.setEnabled(bool(self.folder))
        for w in (self.bX, self.bPdf):
            w.setEnabled(on)

    def escape(self) -> bool:
        return False

    # ---------------------------------------------------------------- buka & hitung
    def open(self, folder: str) -> None:
        self.folder = folder
        try:
            j = api.call("/core/qaqc/open", {"folder": folder})
        except api.ApiError as e:
            say(self, "Gagal membuka data QAQC:\n" + str(e), warn=True)
            return
        self.st, self.labels = j["settings"], j["labels"]
        self._build_form()
        self.set_enabled(False)
        self.refresh()

    def refresh(self) -> None:
        if not self.folder:
            return
        self.sum.setText("Menghitung QAQC…")

        def ok(j):
            self.res = j
            self.st = j["settings"]
            self.show_all()
        run_bg(api.call, "/core/qaqc/analyze", {"folder": self.folder}, ok=ok,
               err=lambda e: (self.sum.setText("Analisis gagal."), say(self, "Analisis QAQC gagal:\n" + e, warn=True)))

    def show_all(self) -> None:
        j = self.res
        c = j["counts"]
        has = bool(c["crm_data"] or c["blank_data"] or c["dup_data"])
        self.sum.setText(f"Master_CRM {c['master_crm']} · Assay_Import {c['assay_import']:,} · CRM {c['crm_data']:,} · Blank {c['blank_data']:,} · "
                         f"Duplikat {c['dup_data']:,} · Zona: {_esc(self.st['zone'])}")
        self.set_enabled(has)
        self.show_dash()
        self.show_crm()
        self.show_blank()
        self.show_dup()
        self.show_batch()
        self.show_app()
        if not self.tDirty:
            self.show_table()
        self._fill_form()
        self._tab_changed(self.tabs.currentIndex())

    def _tab_changed(self, i: int) -> None:
        """Grafik dimuat saat tab dibuka (hemat waktu)."""
        if not self.res:
            return
        w = self.tabs.widget(i)
        ch = [c for c in self.res["charts"]]
        for chart, kind in ((self.dChart, "dash"), (self.cCrm, "crm"), (self.cBlk, "blank"), (self.cDup, "dup")):
            if chart.parent() and w.isAncestorOf(chart) and getattr(chart, "_for", None) is not self.res:
                chart._for = self.res
                chart.show_charts([c for c in ch if c["kind"] == kind])

    def show_dash(self) -> None:
        j = self.res
        d = j["dashboard"]
        if not d:
            self.dHead.setText("Belum ada data QAQC. Pilih <b>Workbook QAQC</b> lalu <b>⇪ Impor…</b> (sheet Master_CRM, Assay_Import, CRM_Data, "
                               "Blank_Data, Duplicate_Data), atau impor tabel satu per satu.")
            fill(self.dT, [], [])
            self.dWarn.setText("")
            return
        t = j["totals"]
        self.dHead.setText(f"<b>QAQC SUMMARY DASHBOARD</b> — kinerja Standard (CRM), Blank dan Duplikat per zona. CRM {sum(t['crm'].values())} · "
                           f"Blank {sum(t['blank'].values())} · Duplikat {sum(t['dup'].values())} pasangan.")
        fill(self.dT, ["Zona", "CRM (akurasi)", "Duplikat (presisi)", "Blank (kontaminasi)", "Penilaian keseluruhan"],
             [[x["zona"], x["crm"], x["dup"], x["blank"], x["overall"]] for x in d],
             [[None, LVL_BG[x["crm_lvl"]], LVL_BG[x["dup_lvl"]], LVL_BG[x["blank_lvl"]], LVL_BG[x["overall_lvl"]]] for x in d])
        self.dT.resizeRowsToContents()
        self.dT.setFixedHeight(min(260, self.dT.horizontalHeader().height() + sum(self.dT.rowHeight(i) for i in range(self.dT.rowCount())) + 6))
        self.dWarn.setText("".join(f"<span style='color:{theme.C['er']}'>⚠ {_esc(w)}</span><br>" for w in j["warnings"]))

    def show_crm(self) -> None:
        j = self.res
        rows = [[x["zona"], x["crm"], x["n"], x["mean_lab"], x["certified"], f"{x['bias'] * 100:+.2f}%", x["sd_text"], f"{x['cv'] * 100:.2f}%", x["pwf"]]
                for x in j["crm_summary"]]
        bg = [CAT_BG["FAIL"] if x["fail"] else (CAT_BG["WARN"] if x["warn"] else CAT_BG["PASS"]) for x in j["crm_summary"]]
        if j["crm_total"]:
            rows.append([j["crm_total"]["zona"], "Total", j["crm_total"]["n"], None, None, "", "", "", j["crm_total"]["pwf"]])
            bg.append(None)
        fill(self.tCrm, ["Zona", "CRM", "n", "Rata-rata lab", "Certified", "Bias", "SD lab vs SD sertifikat", "CV", "PASS / WARN / FAIL"], rows,
             [[None] * 8 + [b] for b in bg])
        self.nCrm.setText("Z = (Lab − Mean) / SD sertifikat (2 desimal). |Z| ≤ 2 PASS, 2–3 WARNING, &gt; 3 FAIL. Grafik kontrol per Zona × CRM "
                          "dengan garis ±2 SD dan ±3 SD, dalam urutan insersi.")

    def show_blank(self) -> None:
        j = self.res
        fill(self.tBlk, ["Zona", "n blank", "PASS", "FAIL", "Pass-rate", "Maksimum"],
             [[x["zona"], x["n"], x["pass_"], x["fail"], f"{x['rate'] * 100:.1f}%", x["max"]] for x in j["blank_summary"]],
             [CAT_BG["FAIL"] if x["fail"] else CAT_BG["PASS"] for x in j["blank_summary"]])
        self.nBlk.setText(f"Blank gagal bila hasil lab melebihi cut-off <b>{float(self.st['blank_cutoff']):g}</b> {_esc(self.st['unit'])}. "
                          "Grafik: urutan hasil blank terhadap cut-off per zona.")

    def show_dup(self) -> None:
        j = self.res
        rows = [[x["zona"], x["kelas"], x["n"], x["pass"], f"{x['rate'] * 100:.1f}%", f"{x['hard'] * 100:.2f}%"] for x in j["dup_summary"]]
        bg = [None if not x["n"] else LVL_BG[1 if x["rate"] >= 0.8 else (2 if x["rate"] >= 0.5 else 3)] for x in j["dup_summary"]]
        fill(self.tDup, ["Zona", "Kelas kadar rata-rata pasangan", "n pasangan", "PASS", "Pass-rate", "HARD rata-rata"], rows,
             [[None] * 4 + [b, None] for b in bg])
        for i, x in enumerate(j["dup_summary"]):
            if x["row"] != "kelas":
                for c in range(6):
                    f = self.tDup.item(i, c).font()
                    f.setBold(True)
                    self.tDup.item(i, c).setFont(f)
        ds = j["dup_stat"]
        self.nDup.setText(f"HARD = |O − D| / (O + D), lolos bila ≤ <b>{float(self.st['hard_max']):g}%</b>; RPD = (O − D) / rata-rata; ARD = HARD."
                          + (f" R² seluruh pasangan = <b>{ds['r2']:.4f}</b> → {_esc(ds['r2_label'])}; rata-rata RPD {ds['avg_rpd']:+.2f}%, "
                             f"rata-rata ARD/HARD {ds['avg_ard']:.2f}%." if ds else "")
                          + " Grafik per Zona × tipe duplikat: scatter 1:1 ±HARD, plot presisi, bias RPD.")
        self.r2.setText(("<b>Interpretasi R² (Precision):</b> " + f"R² = {ds['r2']:.4f} → {_esc(ds['r2_label'])}<br><b>Bias / Avg RPD &amp; ARD:</b> "
                         f"Avg RPD = {ds['avg_rpd']:.2f}% | Avg ARD/HARD = {ds['avg_ard']:.2f}%") if ds else "")

    def show_batch(self) -> None:
        b = self.res["batches"]
        fill(self.bT, ["Batch ID", "Zona", "CRM n", "CRM WARN", "CRM FAIL", "Blank n", "Blank FAIL", "Duplikat n", "Duplikat FAIL", "Status"],
             [[x["batch"], x["zones"], x["crm"], x["crm_warn"], x["crm_fail"], x["blank"], x["blank_fail"], x["dup"], x["dup_fail"], x["status"]] for x in b],
             [[None] * 9 + [CAT_BG.get(x["status"])] for x in b])

    def show_app(self) -> None:
        if not self.folder or not self.res:
            return
        k = self.cbApp.currentData()

        def ok(j):
            rows = j["rows"]
            if k == "app_a":
                fill(self.aT, ["Sample ID", "Batch ID", "CRM", "Lab", "Certified", "Z-score", "Status"],
                     [[r["sample_id"], r["batch"], r["std"], r["grade"], r["mean"], f"{r['z']:+.2f}", r["status"]] for r in rows],
                     [CAT_BG[r["cat"]] for r in rows])
            elif k == "app_b":
                fill(self.aT, ["Sample ID", "Batch ID", "Zona", "Hasil", f"Kelipatan cut-off ({float(self.st['blank_cutoff']):g})"],
                     [[r["sample_id"], r["batch"], r["zona"], r["grade"], f"{r['ratio']:.1f}×"] for r in rows],
                     [CAT_BG["FAIL"] if (r["ratio"] or 0) > 10 else CAT_BG["WARN"] for r in rows])
            else:
                fill(self.aT, ["Original ID", "Batch ID", "Zona", "Original", "Duplikat", "Rasio maks/min"],
                     [[r["orig_id"], r["batch"], r["zona"], round(r["orig"], 2), round(r["dup"], 2), f"{r['ratio']:.1f}×"] for r in rows])
        run_bg(api.call, "/core/qaqc/rows", {"folder": self.folder, "table": k}, ok=ok)

    def show_table(self) -> None:
        if not self.folder:
            return
        t = self.cbTbl.currentData()

        def ok(j):
            cols = [tuple(c) for c in j["cols"]]
            self._marking = True
            fill(self.tT, [h for _k, h, _t in cols], [[r.get(k) for k, _h, _t in cols] for r in j["rows"]], edit=True)
            self._marking = False
            self.tT.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)
            self.tT._cols = cols
            self._tblShown = t
            self._set_dirty(False)
            self._mark()
        run_bg(api.call, "/core/qaqc/table", {"folder": self.folder, "table": t}, ok=ok)

    # ---------------------------------------------------------------- edit manual tabel data
    def _note_data(self) -> None:
        t = self._tblShown or self.cbTbl.currentData()
        n = sum(1 for i in range(self.tT.rowCount()) if not self._row_empty(i))
        pk = "Duplicate_ID" if t == "Duplicate_Data" else "Standard_Name" if t == "Master_CRM" else "Sample_ID"
        bad = getattr(self, "_nbad", 0)
        msg = (f"<b>{t}</b>: {n:,} baris. Klik ganda sel untuk mengubah, <b>+ Baris</b> / <b>Hapus baris</b>, atau salin sel di Excel lalu "
               f"<b>Ctrl+V</b> di sini. {pk} tidak boleh ganda; sel <span style='background:#F4CCCC'>&nbsp;merah&nbsp;</span> = belum valid "
               "(arahkan kursor untuk alasannya). Urutan baris = urutan insersi di grafik kontrol.")
        if t == "Master_CRM":
            msg = (f"<b>{t}</b>: {n:,} CRM. Isi / ubah Standard_Name, Certified_Mean, Certified_SD (SD &gt; 0), lalu <b>Simpan tabel</b> — "
                   "semua hasil dihitung ulang.")
        if self.tDirty:
            msg += " <b style='color:#B7791F'>● Belum disimpan</b>" + (f" — <b style='color:#C0392B'>{bad} sel belum valid</b>" if bad else "")
        self.dataNote.setText(msg)

    def _set_dirty(self, on: bool) -> None:
        self.tDirty = on
        self.bSaveM.setEnabled(on)
        self.bUndo.setEnabled(on)
        self._note_data()

    def _switch_table(self) -> None:
        if self.tDirty and self._tblShown and self._tblShown != self.cbTbl.currentData():
            new = self.cbTbl.currentIndex()
            if ask(self, f"Perubahan di {self._tblShown} belum disimpan. Simpan sekarang?\n\nBatal = buang perubahan."):
                self.cbTbl.blockSignals(True)
                self.cbTbl.setCurrentIndex(self.cbTbl.findData(self._tblShown))
                self.cbTbl.blockSignals(False)
                if not self.save_table():
                    return
                self.cbTbl.blockSignals(True)
                self.cbTbl.setCurrentIndex(new)
                self.cbTbl.blockSignals(False)
        self._set_dirty(False)
        self.show_table()

    def _row_empty(self, i: int) -> bool:
        return not any((self.tT.item(i, j) and self.tT.item(i, j).text().strip()) for j in range(self.tT.columnCount()))

    def _rows(self) -> list[dict]:
        cols = self.tT._cols
        return [{k: (self.tT.item(i, j).text() if self.tT.item(i, j) else "") for j, (k, _h, _t) in enumerate(cols)}
                for i in range(self.tT.rowCount())]

    def _mark(self, server: list | None = None) -> None:
        """Tandai sel belum valid: kunci kosong / ganda, kolom wajib kosong, angka tidak valid (+ galat dari backend)."""
        cols = self.tT._cols
        if not cols:
            return
        t = self._tblShown
        keys = [k for k, _h, _t in cols]
        pk = keys.index("dup_id" if t == "Duplicate_Data" else "name" if t == "Master_CRM" else "sample_id")
        req = {"Master_CRM": ["name", "mean", "sd"], "Assay_Import": ["sample_id"], "CRM_Data": ["sample_id", "std", "grade"],
               "Blank_Data": ["sample_id", "grade"], "Duplicate_Data": ["orig_id", "orig", "dup"]}.get(t, [])
        msgs: dict[tuple[int, int], str] = {}
        seen: dict[str, int] = {}
        for i in range(self.tT.rowCount()):
            if self._row_empty(i):
                continue
            val = [(self.tT.item(i, j).text().strip() if self.tT.item(i, j) else "") for j in range(len(cols))]
            for j, (k, h, ty) in enumerate(cols):
                if ty == "n" and val[j] and not NUM_RE.match(val[j]):
                    msgs[(i, j)] = f"{h} bukan angka"
                elif k in req and not val[j]:
                    msgs[(i, j)] = f"{h} wajib diisi"
            key = val[pk] or (val[keys.index("orig_id")] + "|DUP" if t == "Duplicate_Data" and val[keys.index("orig_id")] else "")
            if key:
                key = key.upper()
                if key in seen:
                    msgs[(i, pk)] = f"{cols[pk][1]} ganda (juga di baris {seen[key] + 1})"
                    msgs.setdefault((seen[key], pk), f"{cols[pk][1]} ganda (juga di baris {i + 1})")
                else:
                    seen[key] = i
            elif pk not in [j for (ii, j) in msgs if ii == i]:
                msgs[(i, pk)] = f"{cols[pk][1]} wajib diisi"
        for e in server or []:
            if e["col"] in keys:
                msgs[(e["row"], keys.index(e["col"]))] = e["msg"]
        self._marking = True
        for i in range(self.tT.rowCount()):
            for j in range(len(cols)):
                it = self.tT.item(i, j)
                if it is None:
                    it = QTableWidgetItem("")
                    self.tT.setItem(i, j, it)
                m = msgs.get((i, j))
                if m:
                    it.setBackground(QColor("#F4CCCC"))
                    it.setForeground(QColor("#141a26"))
                    it.setToolTip(m)
                elif it.toolTip():
                    it.setData(Qt.BackgroundRole, None)
                    it.setData(Qt.ForegroundRole, None)
                    it.setToolTip("")
        self._marking = False
        self._nbad = len(msgs)
        self._note_data()

    def _cell_changed(self, _it) -> None:
        if self._marking:
            return
        self.tDirty = True
        self._mark()
        self._set_dirty(True)

    def add_row(self) -> None:
        i = self.tT.currentRow() + 1 if self.tT.currentRow() >= 0 else self.tT.rowCount()
        self._marking = True
        self.tT.insertRow(i)
        for j in range(self.tT.columnCount()):
            self.tT.setItem(i, j, QTableWidgetItem(""))
        self._marking = False
        self.tT.setCurrentCell(i, 0)
        self._set_dirty(True)
        self._mark()

    def del_rows(self) -> None:
        rows = sorted({ix.row() for ix in self.tT.selectedIndexes()} or ({self.tT.currentRow()} - {-1}), reverse=True)
        if not rows:
            return
        if len(rows) > 1 and not ask(self, f"Hapus {len(rows)} baris dari {self._tblShown}?\n\nBaru benar-benar terhapus setelah Simpan tabel."):
            return
        for i in rows:
            self.tT.removeRow(i)
        self._set_dirty(True)
        self._mark()

    def _clear_cells(self) -> None:
        self._marking = True
        for it in self.tT.selectedItems():
            it.setText("")
        self._marking = False
        self._set_dirty(True)
        self._mark()

    def paste_rows(self, text: str | None = None) -> int:
        """Tempel blok sel dari Excel (tab / baris baru) mulai dari sel terpilih; baris ditambah bila kurang. Bila baris pertama
        berisi judul kolom tabel ini, kolom dicocokkan menurut judul (urutan kolom di Excel boleh berbeda)."""
        if text is None:
            text = QGuiApplication.clipboard().text()
        lines = [ln for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines or not self.tT._cols:
            return 0
        grid = [ln.split("\t") for ln in lines]
        cols = self.tT._cols
        normh = {re.sub(r"[^0-9a-z]", "", h.lower()): j for j, (_k, h, _t) in enumerate(cols)}
        normh.update({re.sub(r"[^0-9a-z]", "", k.lower()): j for j, (k, _h, _t) in enumerate(cols)})
        hm = [normh.get(re.sub(r"[^0-9a-z]", "", c.lower())) for c in grid[0]]
        by_head = sum(x is not None for x in hm) >= 2
        if by_head:
            grid = grid[1:]
        r0 = self.tT.currentRow() if self.tT.currentRow() >= 0 else self.tT.rowCount()
        if by_head:
            r0 = self.tT.rowCount() if self.tT.currentRow() < 0 or not self._row_empty(r0) else r0
        c0 = 0 if by_head or self.tT.currentColumn() < 0 else self.tT.currentColumn()
        self._marking = True
        for n, row in enumerate(grid):
            i = r0 + n
            if i >= self.tT.rowCount():
                self.tT.insertRow(i)
            for m, v in enumerate(row):
                j = hm[m] if by_head and m < len(hm) else (None if by_head else c0 + m)
                if j is None or j >= len(cols):
                    continue
                it = self.tT.item(i, j)
                if it is None:
                    it = QTableWidgetItem("")
                    self.tT.setItem(i, j, it)
                it.setText(v.strip())
        self._marking = False
        self._set_dirty(True)
        self._mark()
        self.win.toast(f"{len(grid)} baris ditempel — periksa sel merah lalu Simpan tabel", 3000)
        return len(grid)

    def save_table(self) -> bool:
        t = self._tblShown or self.cbTbl.currentData()
        if t == "Master_CRM":
            return self.save_master()
        try:
            j = api.call("/core/qaqc/save", {"folder": self.folder, "table": t, "rows": self._rows(), "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return False
        if not j.get("ok"):
            self._mark(j["errors"])
            ee = j["errors"]
            say(self, f"{t} belum disimpan: {len(ee)} sel belum valid (ditandai merah).\n\n"
                + "\n".join(f"Baris {e['row'] + 1}: {e['msg']}" for e in ee[:8]) + ("\n…" if len(ee) > 8 else ""), warn=True)
            return False
        self._set_dirty(False)
        self.win.toast(f"{t} disimpan: {j['new']} baru, {j['updated']} diubah, {j['deleted']} dihapus — QAQC dihitung ulang", 3500)
        if j.get("warnings"):
            say(self, f"{t} disimpan.\n\nPerlu diperiksa:\n" + "\n".join("• " + w_ for w_ in j["warnings"]), warn=True)
        log("[qaqc] simpan", t, j["n"])
        self.refresh()
        return True

    # ---------------------------------------------------------------- aksi
    def import_files(self) -> None:
        if not self.folder:
            return
        tgt = self.cbTarget.currentData()
        fs, _ = QFileDialog.getOpenFileNames(self, "Impor data QAQC — " + self.cbTarget.currentText(), SET.get("qaLastDir", str(Path.home())),
                                             "Data QAQC (*.xlsx *.xlsm *.csv *.txt *.tsv)")
        if not fs:
            return
        SET.set("qaLastDir", str(Path(fs[0]).parent))
        self.sum.setText("Mengimpor…")

        def ok(j):
            lines = []
            for r in j["reports"]:
                t = next((n for n in TABLE_NAMES if n.lower().replace("_", "") == r["table"].replace("_", "").replace("dupdata", "duplicatedata")), r["table"])
                ln = f"{t}: {r['new']:,} baru, {r['updated']:,} diperbarui" + (f", {r['skipped']} dilewati" if r["skipped"] else "")
                if r.get("dup_keys"):
                    ln += f"\n   ⚠ {r['dup_keys']} ID ganda di file (baris terakhir dipakai), mis. {', '.join(r['dup_examples'][:4])}"
                if r.get("nokey_fixed"):
                    ln += f"\n   {r['nokey_fixed']} pasangan tanpa Duplicate_ID diberi kunci Original_ID|DUP"
                lines.append(ln)
            if j["errors"]:
                lines += ["", "Tidak diimpor:"] + j["errors"]
            say(self, "Impor QAQC selesai.\n\n" + "\n".join(lines), warn=bool(j["errors"]))
            log("[qaqc] impor", fs)
            self.refresh()
        run_bg(api.call, "/core/qaqc/import", {"folder": self.folder, "paths": fs, "target": tgt, "by": self.by()}, ok=ok,
               err=lambda e: (self.sum.setText(""), say(self, "Impor gagal:\n" + e, warn=True)))

    def save_master(self) -> bool:
        cols = getattr(self.tT, "_cols", [])
        rows = []
        for i in range(self.tT.rowCount()):
            rows.append({k: (self.tT.item(i, j).text() if self.tT.item(i, j) else "") for j, (k, _h, _t) in enumerate(cols)})
        try:
            api.call("/core/qaqc/master", {"folder": self.folder, "rows": rows, "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return False
        self._set_dirty(False)
        self.win.toast("Master_CRM disimpan — QAQC dihitung ulang", 3000)
        self.refresh()
        return True

    def clear_table(self) -> None:
        t = self.cbTbl.currentData()
        if not ask(self, f"Kosongkan seluruh tabel {t} di proyek ini?\n\nFile sumber tidak tersentuh; data bisa diimpor lagi."):
            return
        try:
            api.call("/core/qaqc/clear", {"folder": self.folder, "table": t, "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self._set_dirty(False)
        self.refresh()

    def run_dh(self) -> None:
        self.dhInfo.setText("Memeriksa data bor…")

        def ok(j):
            c = j["counts"]
            if j["empty"]:
                self.dhInfo.setText("Belum ada data bor di proyek ini. Impor Collar, Survey, Assay, Geologi lewat tombol <b>Data bor</b> di ruang kerja "
                                    "Core box, lalu periksa lagi.")
                fill(self.dhS, [], [])
                fill(self.dhT, [], [])
                return
            col = {"MERAH": theme.C["er"], "KUNING": "#B7791F", "HIJAU": "#2F6B3A"}.get(j["light"], theme.C["mu"])
            self.dhInfo.setText(f"<b style='color:{col}'>{j['light']}</b> — {c['holes']} lubang · {c['collar']} collar · {c['survey']} survey · "
                                f"{c['assay']:,} assay · {c['geology']:,} geologi. <b>{j['red']}</b> kesalahan (MERAH), <b>{j['yellow']}</b> perlu "
                                "diperiksa (KUNING).")
            fill(self.dhS, ["Kode", "Pemeriksaan", "Tingkat", "Temuan", "Lubang"],
                 [[x["code"], x["check"], x["severity"], x["n"], x["holes"]] for x in j["summary"]],
                 [[None, None, CAT_BG.get(x["severity"]), None, None] for x in j["summary"]])
            fill(self.dhT, ["Kode", "Pemeriksaan", "Tingkat", "Hole ID", "Kedalaman / item", "Keterangan"],
                 [[x["code"], x["check"], x["severity"], x["hole"], x["item"], x["detail"]] for x in j["issues"]],
                 [[None, None, CAT_BG.get(x["severity"]), None, None, None] for x in j["issues"]])
        run_bg(api.call, "/core/qaqc/dh", {"folder": self.folder}, ok=ok, err=lambda e: self.dhInfo.setText("Gagal: " + _esc(e)))

    # ---------------------------------------------------------------- panel kontrol
    def _build_form(self) -> None:
        if self.ed:
            return
        for k, lab in self.labels.items():
            if k in ("zone", "dup_type"):
                e = QComboBox()
                e.setEditable(True)
            else:
                e = QLineEdit()
            e.setMaximumWidth(320)
            self.form.addRow(lab, e)
            self.ed[k] = e

    def _fill_form(self) -> None:
        zones = ["ALL"] + (self.res or {}).get("zones", []) if self.res else ["ALL"]
        types = ["ALL"] + (self.res or {}).get("dup_types", []) if self.res else ["ALL"]
        for k, e in self.ed.items():
            v = self.st.get(k)
            if isinstance(e, QComboBox):
                e.blockSignals(True)
                e.clear()
                e.addItems(list(dict.fromkeys((zones if k == "zone" else types) + [str(v)])))
                e.setCurrentText(str(v))
                e.blockSignals(False)
            else:
                e.setText(f"{v:g}" if isinstance(v, float) else str(v))

    def save_settings(self) -> None:
        vals = {k: (e.currentText() if isinstance(e, QComboBox) else e.text()) for k, e in self.ed.items()}
        try:
            api.call("/core/qaqc/settings", {"folder": self.folder, "values": vals, "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.win.toast("Panel kontrol disimpan — QAQC dihitung ulang", 3000)
        self.refresh()

    def reset_settings(self) -> None:
        from gcex_backend.core_qaqc import SETTINGS_DEFAULT
        try:
            api.call("/core/qaqc/settings", {"folder": self.folder, "values": dict(SETTINGS_DEFAULT), "by": self.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.refresh()

    # ---------------------------------------------------------------- ekspor
    def _save_path(self, title: str, name: str, ext: str, filt: str) -> str:
        start = str(Path(SET.get("lastSaveDir", str(Path.home()))) / (name + ext))
        p, _ = QFileDialog.getSaveFileName(self, title, start, filt)
        if not p:
            return ""
        if not p.lower().endswith(ext):
            p += ext
        SET.set("lastSaveDir", str(Path(p).parent))
        return p

    def _name(self) -> str:
        z = self.st.get("zone") or "ALL"
        return re.sub(r"[^\w.-]+", "_", f"QAQC_{Path(self.folder).name}_{z}")[:80]

    def export_xlsx(self) -> None:
        p = self._save_path("Ekspor QAQC ke Excel", self._name(), ".xlsx", "Excel (*.xlsx)")
        if not p:
            return
        self.win.toast("Menyusun workbook QAQC & grafik…", 4000)
        folder = self.folder

        def work():
            b = api.call("/core/qaqc/export/xlsx", {"folder": folder, "by": self.by()})
            tmp = Path(p + ".tmp")
            tmp.write_bytes(b)
            tmp.replace(p)
            z = api.call("/core/qaqc/export/charts", {"folder": folder})
            d = Path(p).with_suffix("")
            d = d.parent / (d.name + "_grafik")
            d.mkdir(exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(z)) as zz:
                zz.extractall(d)
            return d

        def ok(d):
            self.win.toast(f"Ekspor selesai: {Path(p).name} + folder {d.name}", 5000)
            log("[qaqc] ekspor", p)
            show_in_folder(p)
        run_bg(work, ok=ok, err=lambda e: say(self, "Gagal ekspor:\n" + e, warn=True))

    def export_pdf(self) -> None:
        p = self._save_path("Laporan QAQC (PDF)", self._name() + "_Laporan", ".pdf", "PDF (*.pdf)")
        if not p:
            return
        title = f"Laporan QAQC Sampel & Data Bor — {Path(self.folder).name}"
        self.win.toast("Menyusun laporan QAQC…", 5000)

        def ok(rep):
            from .qaqc_pdf import write_pdf
            n = write_pdf(rep, p, f"{title} · DB-Ex")
            self.win.toast(f"Laporan PDF {n} halaman: {Path(p).name}", 5000)
            log("[qaqc] laporan", p, n)
            show_in_folder(p)
        run_bg(api.call, "/core/qaqc/report", {"folder": self.folder, "title": title, "author": self.by(), "project": Path(self.folder).name,
                                               "by": self.by()}, ok=ok, err=lambda e: say(self, "Gagal membuat laporan:\n" + e, warn=True))
