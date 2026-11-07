"""Dialog: syarat penggunaan, aktivasi / info lisensi, AI lokal (Ollama), tentang."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QVBoxLayout, QWidget)

from . import APP_NAME, COPYRIGHT, api, lic, theme
from .card import _esc, btn
from .util import SET, is_local, log, open_path, res_dir, run_bg, start_ollama

TERMS_VERSION = "2026-10-29"  # sama dengan electron/main.js: persetujuan lama tetap berlaku


class Dlg(QDialog):
    """Dialog bergaya DB-Ex: pita judul navy dengan tepi biru baja."""

    def __init__(self, parent, title: str, html_title: str | None = None, w: int = 620):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(w)
        o = QVBoxLayout(self)
        o.setContentsMargins(0, 0, 0, 0)
        o.setSpacing(0)
        hd = QFrame()
        hd.setObjectName("dlgHead")
        hl = QHBoxLayout(hd)
        hl.setContentsMargins(14, 10, 14, 10)
        t = QLabel(html_title or title)
        t.setTextFormat(Qt.RichText)
        hl.addWidget(t)
        o.addWidget(hd)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(16, 14, 16, 10)
        self.body.setSpacing(10)
        o.addLayout(self.body, 1)
        self.foot = QHBoxLayout()
        self.foot.setContentsMargins(16, 6, 16, 14)
        o.addLayout(self.foot)


def box(html: str = "", kind: str = "") -> QLabel:
    l = QLabel(html)
    l.setObjectName("box")
    l.setProperty("k", kind)
    l.setWordWrap(True)
    l.setTextFormat(Qt.RichText)
    l.setTextInteractionFlags(Qt.TextBrowserInteraction)
    return l


def set_box(l: QLabel, html: str, kind: str = "") -> None:
    l.setText(html)
    l.setProperty("k", kind)
    theme.repolish(l)


def say(parent, text: str, title: str = APP_NAME, warn: bool = False) -> None:
    (QMessageBox.warning if warn else QMessageBox.information)(parent, title, text)


def ask(parent, text: str, title: str = APP_NAME) -> bool:
    return QMessageBox.question(parent, title, text, QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok) == QMessageBox.Ok


# ---------------------------------------------------------------- syarat penggunaan
def ensure_terms() -> bool:
    if SET.get("termsAccepted") == TERMS_VERSION:
        return True
    while True:
        m = QMessageBox()
        m.setIcon(QMessageBox.Information)
        m.setWindowTitle(APP_NAME + " - Syarat Penggunaan")
        m.setText("<b>Syarat Penggunaan & Penafian GC-Ex</b>")
        m.setInformativeText(
            "Copyright © 2026 Habil Abdillah. GC-Ex dilindungi UU No. 28 Tahun 2014 tentang Hak Cipta dan dilisensikan, bukan dijual.\n\n"
            "• Dilarang menjual, membagikan ke pihak lain, membongkar, atau menghapus tanda hak cipta tanpa izin tertulis.\n"
            "• Disediakan \"apa adanya\" tanpa jaminan. Hasil pemodelan, estimasi dan nilai geoteknik dari AI adalah alat bantu / perkiraan, wajib "
            "diperiksa orang yang kompeten, dan tidak boleh menjadi satu-satunya dasar keputusan keselamatan.\n"
            "• Data diproses di komputer ini saja; tanggung jawab atas izin pemakaian data perusahaan ada pada pengguna.\n"
            "• Komponen open source tetap di bawah lisensinya masing-masing (menu Bantuan).\n\n"
            "Pilih \"Baca selengkapnya\" untuk teks lengkap (Bahasa Indonesia & English).")
        ok = m.addButton("Setuju", QMessageBox.AcceptRole)
        more = m.addButton("Baca selengkapnya", QMessageBox.HelpRole)
        no = m.addButton("Tidak setuju (keluar)", QMessageBox.RejectRole)
        m.setDefaultButton(ok)
        m.exec()
        c = m.clickedButton()
        if c is more:
            open_path(res_dir("legal") / "SYARAT_PENGGUNAAN.txt")
            continue
        if c is not ok:
            log("[syarat] tidak disetujui, keluar")
            return False
        import datetime
        SET.set("termsAccepted", TERMS_VERSION)
        SET.set("termsAcceptedAt", datetime.datetime.now(datetime.timezone.utc).isoformat())
        return True


# ---------------------------------------------------------------- lisensi
class LicenseDlg(Dlg):
    def __init__(self, parent, store: lic.Store, mode: str = "activate"):
        super().__init__(parent, ("Lisensi " if mode == "info" else "Aktivasi ") + APP_NAME,
                         f"{'Lisensi' if mode == 'info' else 'Aktivasi'} <span style='color:#a9c3dd'>{APP_NAME}</span>", 600)
        self.store, self.mode = store, mode
        b = self.body
        self.sub = QLabel("Ganti kunci bila menerima lisensi baru (mis. perpanjangan)." if mode == "info"
                          else "Aplikasi ini memerlukan kunci lisensi yang terikat ke komputer.")
        self.sub.setObjectName("note")
        b.addWidget(self.sub)
        self.stat = box()
        b.addWidget(self.stat)
        mid = QHBoxLayout()
        lab = QLabel("ID KOMPUTER INI")
        lab.setObjectName("fl")
        self.mid = QLabel(lic.machine_id())
        self.mid.setFont(theme.mono(13, True))
        self.mid.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cp = btn("Salin", sm=True)
        cp.clicked.connect(lambda: (QGuiApplication.clipboard().setText(self.mid.text()), cp.setText("Tersalin ✓"),
                                    QTimer.singleShot(1500, cp, lambda: cp.setText("Salin"))))
        mid.addWidget(self.mid)
        mid.addWidget(cp)
        mid.addStretch(1)
        b.addWidget(lab)
        b.addLayout(mid)
        hint = QLabel("Kirim ID ini ke penerbit lisensi GC-Ex. Anda akan menerima kunci lisensi (teks diawali <b>GCEX1.</b>) atau file <b>.gcexlic</b>.")
        hint.setObjectName("note")
        hint.setWordWrap(True)
        b.addWidget(hint)
        self.key = QPlainTextEdit()
        self.key.setPlaceholderText("Tempel kunci lisensi di sini (GCEX1....)")
        self.key.setFont(theme.mono(9))
        self.key.setFixedHeight(90)
        b.addWidget(self.key)
        self.msg = QLabel()
        self.msg.setWordWrap(True)
        self.msg.setTextFormat(Qt.RichText)
        b.addWidget(self.msg)
        self.bRm = btn("Hapus lisensi dari komputer ini")
        fb = btn("Buka file .gcexlic…")
        go = btn("Aktifkan", pri=True)
        cl = btn("Tutup" if mode == "info" else "Keluar")
        self.foot.addWidget(self.bRm)
        self.foot.addStretch(1)
        for x in (fb, cl, go):
            self.foot.addWidget(x)
        go.clicked.connect(self.activate)
        fb.clicked.connect(self.open_file)
        cl.clicked.connect(self.reject)
        self.bRm.clicked.connect(self.remove)
        self.refresh()

    def refresh(self) -> None:
        r = self.store.check(core_app())
        I = r.get("info") or {}
        if I and (r["ok"] or I.get("n")):
            apps = ", ".join("Semua aplikasi GC-Ex" if a == "*" else lic.APPS.get(a, a) for a in I.get("a") or [])
            until = (_esc(I["e"]) + (f" ({r['days_left']} hari lagi)" if r["ok"] and r.get("days_left") is not None else "")) if I.get("e") else "tanpa batas waktu"
            set_box(self.stat, f"<b>{'Lisensi aktif' if r['ok'] else 'Lisensi tersimpan (tidak berlaku)'}</b><br>Pemegang: <b>{_esc(I.get('n'))}</b>"
                    f"{'<br>' + _esc(I['o']) if I.get('o') else ''}<br>Aplikasi: {_esc(apps)}<br>Berlaku sampai: {until}<br>No. lisensi: {_esc(I.get('id') or '-')}",
                    "ok" if r["ok"] else "er")
            self.stat.show()
            self.bRm.show()
        else:
            self.stat.hide()
            self.bRm.hide()
        if not r["ok"] and not r.get("none"):
            self._msg("⚠ " + _esc(r["reason"]), True)

    def _msg(self, html: str, err: bool = False) -> None:
        self.msg.setText(f"<span style='color:{theme.C['er'] if err else theme.C['ac2']}'>{html}</span>")

    def activate(self) -> None:
        k = self.key.toPlainText().strip()
        if not k:
            self._msg("Tempel kunci lisensi dulu.", True)
            return
        r = self.store.activate(k, core_app())
        log("[lisensi] aktivasi", "OK " + str((r.get("info") or {}).get("id")) if r["ok"] else "gagal: " + r["reason"])
        if r["ok"]:
            I = r["info"]
            self._msg(f"✓ Lisensi aktif untuk <b>{_esc(I['n'])}</b>" + (f", berlaku sampai {_esc(I['e'])}" if I.get("e") else "") + ".")
            self.refresh()
            QTimer.singleShot(900, self, self.accept)
        else:
            self._msg("✖ " + _esc(r["reason"]), True)

    def open_file(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Buka file lisensi GC-Ex", "", "Lisensi GC-Ex (*.gcexlic *.txt)")
        if f:
            try:
                with open(f, encoding="utf-8", errors="replace") as h:
                    self.key.setPlainText(h.read(20000).strip())
            except OSError as e:
                self._msg(_esc(str(e)), True)
                return
            self.activate()

    def remove(self) -> None:
        if QMessageBox.warning(self, "Lisensi GC-Ex", "Hapus lisensi dari komputer ini?\n\nSemua aplikasi GC-Ex di komputer ini akan meminta kunci lisensi lagi saat dibuka berikutnya.",
                               QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel) != QMessageBox.Yes:
            return
        self.store.remove()
        log("[lisensi] dihapus")
        self.refresh()
        self._msg("Lisensi dihapus dari komputer ini.")

    def keyPressEvent(self, e) -> None:  # noqa: N802
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and e.modifiers() & Qt.ControlModifier:
            self.activate()
            return
        super().keyPressEvent(e)


def core_app() -> str:
    return "core"


# ---------------------------------------------------------------- AI lokal
class AiDlg(Dlg):
    run = Signal(str)  # 'pending' | 'all'
    status = Signal(object)  # hasil /core/ollama

    def __init__(self, parent):
        super().__init__(parent, "AI lokal · Ollama", "AI <span style='color:#a9c3dd'>lokal</span> · Ollama", 680)
        self.setMinimumHeight(760)
        b = self.body
        self.state = box("Memeriksa…")
        b.addWidget(self.state)
        self.bStart = btn("Jalankan Ollama", pri=True, sm=True)
        self.bStart.hide()
        self.bStart.clicked.connect(lambda: self.start(False))
        b.addWidget(self.bStart, 0, Qt.AlignLeft)
        r = QHBoxLayout()
        r.addWidget(QLabel("Alamat Ollama"))
        self.host = QLineEdit(api.DEFAULT_HOST)
        self.host.setFont(theme.mono(9.5))
        chk = btn("Periksa", sm=True)
        chk.clicked.connect(lambda: self.check())
        r.addWidget(self.host, 1)
        r.addWidget(chk)
        b.addLayout(r)
        self.auto = QCheckBox("Jalankan Ollama otomatis saat DB-Ex dibuka bila belum aktif")
        self.auto.setChecked(bool(SET.get("autoOllama", True)))
        self.auto.toggled.connect(lambda v: SET.set("autoOllama", v))
        b.addWidget(self.auto)
        b.addWidget(QLabel("<b>Model vision</b> <span style='color:%s'>(hanya model yang bisa melihat gambar)</span>" % theme.C["mu"]))
        self.mw = QWidget()
        self.ml = QVBoxLayout(self.mw)
        self.ml.setContentsMargins(6, 4, 6, 4)
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(self.mw)
        sa.setFixedHeight(120)
        b.addWidget(sa)
        self.grp = QButtonGroup(self)
        self.grp.buttonToggled.connect(lambda *_: self.model() and SET.set("model", self.model()))
        r = QHBoxLayout()
        r.addWidget(QLabel("Ukuran foto ke AI"))
        self.px = QComboBox()
        for v, t in ((1024, "1024 px (cepat)"), (1600, "1600 px (seimbang)"), (2048, "2048 px (label kecil, lambat)")):
            self.px.addItem(t, v)
        self.px.setCurrentIndex(1)
        r.addWidget(self.px)
        n = QLabel("foto asli tidak diubah")
        n.setObjectName("note")
        r.addWidget(n)
        r.addStretch(1)
        b.addLayout(r)
        b.addWidget(QLabel("<b>Instruksi tambahan</b> <span style='color:%s'>(opsional, mis. kode litologi proyek)</span>" % theme.C["mu"]))
        self.extra = QPlainTextEdit()
        self.extra.setPlaceholderText("Contoh: Pakai kode litologi AND (andesit), DAC (dasit), QV (quartz vein), BX (breksi).")
        self.extra.setFixedHeight(64)
        b.addWidget(self.extra)
        r = QHBoxLayout()
        self.bLeg = btn("Legenda site…", "Istilah resmi proyek (litologi, alterasi, oksida / vein, struktur) untuk semua prompt AI geologi", sm=True)
        self.bLeg.clicked.connect(lambda: open_legend(self, getattr(self.parent(), "folder", "")))
        r.addWidget(self.bLeg)
        n = QLabel("berlaku untuk core box & singkapan, tersimpan di folder proyek")
        n.setObjectName("note")
        r.addWidget(n)
        r.addStretch(1)
        b.addLayout(r)
        b.addWidget(box("<b>AI visual untuk parameter geoteknik</b> (recovery, RQD, GSI, RMR, pelapukan, kondisi, struktur) dan segmen per baris core. "
                        "Litologi, alterasi, oksidasi dan warna diambil dari <b>logging geologist</b> (Data bor › Geologi) bila ada; AI hanya mengisi bila "
                        "logging tidak ada dan tidak pernah menimpa editan Anda.", "ok"))
        b.addWidget(box("Nilai geoteknik dari foto hanyalah <b>perkiraan visual AI</b>, bukan pengukuran di core shed. Hasil wajib diperiksa dan diverifikasi "
                        "geologist sebelum dipakai."))
        self.bAll = btn("Analisis ulang semua yang belum diverifikasi")
        self.bRun = btn("Analisis foto yang belum (0)", pri=True)
        cl = btn("Tutup")
        self.foot.addWidget(self.bAll)
        self.foot.addStretch(1)
        self.foot.addWidget(cl)
        self.foot.addWidget(self.bRun)
        cl.clicked.connect(self.reject)
        self.bRun.clicked.connect(lambda: self.run.emit("pending"))
        self.bAll.clicked.connect(lambda: self.run.emit("all"))
        self.info: dict | None = None
        self.tried = self.busy = False
        self.want = ""

    def model(self) -> str:
        b = self.grp.checkedButton()
        return b.property("m") if b else ""

    def can_start(self) -> bool:
        return is_local(self.host.text())

    def set_pending(self, n: int) -> None:
        self.bRun.setText(f"Analisis foto yang belum ({n})")

    def check(self, no_auto: bool = False) -> None:
        host = self.host.text().strip() or api.DEFAULT_HOST
        self.status.emit({"wait": True, "text": "AI lokal: memeriksa…"})
        self._tok = getattr(self, "_tok", 0) + 1
        tok = self._tok
        run_bg(api.call, "/core/ollama", {"host": host}, ok=lambda j: tok == self._tok and self._got(j, no_auto),
               err=lambda e: (set_box(self.state, _esc(e), "er"), self.status.emit({"ok": False, "text": "AI lokal: ?"})))

    def _got(self, j: dict, no_auto: bool) -> None:
        self.info = j
        vis = [m for m in j["models"] if m.get("vision")]
        rec = (j.get("recommended") or ["qwen3-vl:8b"])[0]
        self.bStart.setVisible(False)
        if not j["running"]:
            self.status.emit({"ok": False, "text": "AI lokal: Ollama tidak aktif"})
            if not no_auto and not self.tried and SET.get("autoOllama", True) and self.can_start():
                self.start(True)
                return
            set_box(self.state, "<b>Ollama belum berjalan.</b> Klik <b>Jalankan Ollama</b> (atau buka Ollama dari Start menu). Rekomendasi model: "
                    f"<code>{_esc(rec)}</code>. Tanpa AI pun, Anda tetap bisa mengisi &amp; memverifikasi log secara manual.", "er")
            self.bStart.setVisible(self.can_start())
        elif not vis:
            self.status.emit({"ok": False, "text": "AI lokal: belum ada model vision"})
            set_box(self.state, f"Ollama {_esc(j.get('version') or '')} aktif, tetapi <b>belum ada model vision</b>. Cek di Command Prompt: <code>ollama list</code>. "
                    "Bila qwen3-vl sudah tercantum, perbarui Ollama ke versi 0.12.7 atau lebih baru (model tidak terhapus). Bila belum ada, jalankan "
                    f"<code>ollama pull {_esc(rec)}</code> saat ada internet, atau salin folder model dari komputer lain (lihat panduan).", "er")
        else:
            set_box(self.state, f"Ollama {_esc(j.get('version') or '')} aktif · {len(vis)} model vision siap. Tidak ada data yang keluar dari komputer ini.", "ok")
        want = self.want or SET.get("model", "")
        chosen = want if any(m["name"] == want for m in vis) else (vis[0]["name"] if vis else "")
        while self.ml.count():
            w = self.ml.takeAt(0).widget()
            if w:
                self.grp.removeButton(w) if isinstance(w, QRadioButton) else None
                w.hide()
                w.setParent(None)
                w.deleteLater()
        for m in j["models"]:
            size = f"{m['size'] / 1e9:.1f} GB" if m.get("size") else ""
            think = m["name"].startswith("qwen3-vl") and "instruct" not in m["name"]
            rb = QRadioButton(f"{m['name']}   · {m.get('params') or ''} · {size}" + ("" if m.get("vision") else " · tidak bisa melihat gambar")
                              + (" · versi 'thinking': lambat, sering gagal di Borang — pakai -instruct" if think else ""))
            rb.setProperty("m", m["name"])
            rb.setEnabled(bool(m.get("vision")))
            self.grp.addButton(rb)
            self.ml.addWidget(rb)
            if m["name"] == chosen:
                rb.setChecked(True)
        if not j["models"]:
            self.ml.addWidget(QLabel("Belum ada model."))
        if j["running"] and vis:
            self.status.emit({"ok": True, "text": "AI lokal: " + (chosen or vis[0]["name"])})

    def start(self, auto: bool) -> None:
        if self.busy or not self.can_start():
            return
        self.busy = self.tried = True
        set_box(self.state, "Menjalankan Ollama… (bisa 5–30 detik saat pertama)")
        self.status.emit({"wait": True, "text": "AI lokal: menjalankan Ollama…"})
        host = self.host.text().strip()

        def done(r):
            self.busy = False
            log("[ollama] start", r)
            self.check(True)
            if not r.get("ok") and (not auto or r.get("code") != "notfound"):
                QTimer.singleShot(400, self, lambda: (set_box(self.state, (
                    "<b>Ollama belum terpasang di komputer ini.</b> Pasang <code>OllamaSetup.exe</code> (lihat Bantuan → Panduan AI lokal), lalu klik "
                    "<b>Jalankan Ollama</b> lagi." if r.get("code") == "notfound" else "<b>Ollama belum bisa dijalankan.</b> " + _esc(r.get("msg") or "")
                    + " Coba buka Ollama dari Start menu."), "er"), self.bStart.setVisible(True)))

        run_bg(start_ollama, host, ok=done, err=lambda e: done({"ok": False, "msg": e}))

    def load_meta(self, meta: dict) -> None:
        if meta.get("ai_host"):
            self.host.setText(meta["ai_host"])
        if meta.get("ai_extra") is not None:
            self.extra.setPlainText(meta["ai_extra"] or "")
        if meta.get("ai_max_px"):
            i = self.px.findData(int(meta["ai_max_px"]))
            if i >= 0:
                self.px.setCurrentIndex(i)
        self.want = meta.get("ai_model") or ""


# ---------------------------------------------------------------- legenda site
LEGEND_HINT = {
    "lithology": "Contoh: andesit porfiri, tuf lapili, breksi hidrotermal, dasit",
    "alteration": "Contoh: propilitik (hijau klorit-epidot), argilik (putih pucat, lunak), silisifikasi (abu terang, keras)",
    "mineral": "Contoh: hematit merah tua, limonit / goetit kuning-coklat, vein kuarsa putih, vein kuarsa-hematit, stockwork",
    "structure": "Contoh: sesar utama berarah NW-SE dengan gouge lempung; kekar curam terisi oksida",
    "ignore": "Contoh: bekas lubang ledak tegak, pita ukur kuning, garis cat Pylox, kabel peledakan",
    "notes": "Contoh: kode litologi AND = andesit, TUF = tuf, QV = quartz vein",
}


class LegendDlg(Dlg):
    """Legenda site proyek: istilah resmi yang otomatis masuk ke semua prompt AI geologi (core box & singkapan)."""

    def __init__(self, parent, folder: str):
        super().__init__(parent, "Legenda site", "Legenda <span style='color:#a9c3dd'>site</span>", 640)
        self.folder = folder
        b = self.body
        self.setMinimumHeight(740)
        info = box("Istilah resmi proyek. <b>Otomatis masuk ke semua prompt AI geologi</b> (core box & singkapan) dan tersimpan di folder "
                   "proyek, jadi rekan yang membuka folder yang sama memakai legenda yang sama. Kosongkan bila tidak dipakai.")
        info.setMinimumHeight(64)
        b.addWidget(info)
        self.ed: dict[str, QPlainTextEdit] = {}
        j = api.call("/core/legend", {"folder": folder})
        for k in j["keys"]:
            b.addWidget(QLabel(f"<b>{_esc(k['name'])}</b>"))
            e = QPlainTextEdit(j["legend"].get(k["key"]) or "")
            e.setPlaceholderText(LEGEND_HINT.get(k["key"], ""))
            e.setFixedHeight(52)
            b.addWidget(e)
            self.ed[k["key"]] = e
        sv = btn("Simpan", pri=True)
        cl = btn("Batal")
        self.foot.addStretch(1)
        self.foot.addWidget(cl)
        self.foot.addWidget(sv)
        cl.clicked.connect(self.reject)
        sv.clicked.connect(self.save)

    def save(self) -> None:
        try:
            api.call("/core/legend", {"folder": self.folder, "legend": {k: e.toPlainText() for k, e in self.ed.items()}})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.accept()


def open_legend(parent, folder: str) -> bool:
    if not folder:
        say(parent, "Buka folder proyek dulu: legenda site disimpan di folder proyek.", warn=True)
        return False
    try:
        d = LegendDlg(parent, folder)
    except api.ApiError as e:
        say(parent, str(e), warn=True)
        return False
    return d.exec() == QDialog.Accepted


def about(parent, store: lic.Store | None, version: str) -> None:
    c = store.check(core_app()) if store else None
    I = c.get("info") if c else None
    m = QMessageBox(parent)
    m.setWindowTitle("Tentang DB-Ex")
    m.setIcon(QMessageBox.Information)
    m.setText(f"<b>{APP_NAME}</b> - Database Excellence (keluarga GC-Ex)")
    m.setInformativeText(
        f"Versi {version}\nCopyright © 2026 Habil Abdillah. Hak cipta dilindungi undang-undang."
        + (f"\n\nDilisensikan kepada: {I['n']}" + (f" ({I['o']})" if I.get("o") else "") + f"\nBerlaku sampai: {I.get('e') or 'tanpa batas waktu'}" if I and c["ok"] else "")
        + "\n\nMemakai komponen open source: Qt for Python / PySide6 (LGPL v3), Qt 6 (LGPL v3), Python (PSF), FastAPI, Pydantic, Pillow (MIT-CMU), "
          "openpyxl (MIT), font Inter & JetBrains Mono (SIL OFL 1.1).\nAI lokal memakai Ollama (MIT, dipasang terpisah); model AI mengikuti lisensi masing-masing."
        + "\nMicrosoft Excel, Ollama dan nama produk lain adalah merek dagang milik pemiliknya; GC-Ex tidak berafiliasi dengan mereka.")
    lb = m.addButton("Lisensi open source & merek", QMessageBox.HelpRole)
    tb = m.addButton("Syarat penggunaan", QMessageBox.HelpRole)
    m.addButton(QMessageBox.Ok)
    m.exec()
    if m.clickedButton() is lb:
        open_path(res_dir("legal"))
    elif m.clickedButton() is tb:
        open_path(res_dir("legal") / "SYARAT_PENGGUNAAN.txt")


__all__ = ["AiDlg", "LegendDlg", "LicenseDlg", "open_legend", "about", "ask", "box", "ensure_terms", "say", "set_box", "COPYRIGHT", "QPushButton"]
