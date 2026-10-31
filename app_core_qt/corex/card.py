"""Kartu interpretasi foto: isian geoteknik & geologi dengan penanda sumber (AI / diedit / nama file / logging / tanda),
verifikasi, analisis ulang, riwayat perubahan + jawaban asli AI."""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCompleter, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QScrollArea,
                               QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from . import theme
from .table import LISTS, OXI, WEA, fmt, status_text  # noqa: F401 (WEA / OXI dipakai modul lain)
NUM = {"from_m", "to_m", "recovery_pct", "rqd_pct", "rmr"}
TAG_TIP = {"mk": "Dihitung dari tanda core loss di foto: (interval - core loss) / interval. Edit manual mengalahkan nilai ini.",
           "lgt": "Dari logging geologist (tabel Geologi). Diutamakan di atas AI. Ubah di data Geologi.",
           "fn": "Dibaca dari nama file foto", "ai": "Isian AI, belum dicek geologist", "ed": "Diedit geologist (tidak ditimpa AI)"}
TAG_TXT = {"mk": "tanda", "lgt": "logging", "fn": "nama file", "ai": "AI", "ed": "diedit"}


def btn(text: str, tip: str = "", pri: bool = False, ok: bool = False, sm: bool = False) -> QPushButton:
    b = QPushButton(text)
    if tip:
        b.setToolTip(tip)
    b.setProperty("pri", pri)
    b.setProperty("ok", ok)
    b.setProperty("sm", sm)
    b.setCursor(Qt.PointingHandCursor)
    return b


class Field(QFrame):
    def __init__(self, k: str, label: str, multiline: bool = False):
        super().__init__()
        self.setObjectName("fld")
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.setMinimumWidth(60)
        self.k = k
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 4, 8, 5)
        v.setSpacing(1)
        h = QHBoxLayout()
        h.setSpacing(4)
        self.lbl = QLabel(label.upper())
        self.lbl.setObjectName("fl")
        self.lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lbl.setMinimumWidth(1)
        self.tag = QLabel()
        self.tag.setObjectName("tag")
        h.addWidget(self.lbl)
        h.addStretch(1)
        h.addWidget(self.tag)
        v.addLayout(h)
        if multiline:
            self.ed = QPlainTextEdit()
            self.ed.setFixedHeight(60)
        else:
            self.ed = QLineEdit()
            if k in LISTS:
                c = QCompleter(LISTS[k], self.ed)
                c.setCaseSensitivity(Qt.CaseInsensitive)
                c.setFilterMode(Qt.MatchContains)
                self.ed.setCompleter(c)
            if k in NUM or k in ("hole_id",):
                self.ed.setFont(theme.mono(10, True))
        v.addWidget(self.ed)

    def value(self) -> str:
        return self.ed.toPlainText() if isinstance(self.ed, QPlainTextEdit) else self.ed.text()

    def set(self, text: str, kind: str, readonly: bool, tip: str = "") -> None:
        if isinstance(self.ed, QPlainTextEdit):
            if self.ed.toPlainText() != text:
                self.ed.setPlainText(text)
        else:
            self.ed.setText(text)
            self.ed.setCursorPosition(0)
        self.ed.setReadOnly(readonly)
        self.ed.setToolTip(tip)
        self.tag.setVisible(bool(kind))
        self.tag.setText(TAG_TXT.get(kind, ""))
        self.tag.setToolTip(TAG_TIP.get(kind, ""))
        self.tag.setProperty("k", kind)
        self.setProperty("ai", kind == "ai")
        self.setProperty("lg", kind == "lgt")
        for w in (self, self.tag):
            theme.repolish(w)


class Card(QScrollArea):
    edited = Signal(int, str, object)
    verify = Signal(int, bool)
    analyze = Signal(int)
    showFile = Signal(int)
    nav = Signal(int)
    history = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setObjectName("card")
        self.labels: dict[str, str] = {}
        w = QWidget()
        w.setObjectName("card")
        self.setWidget(w)
        self.v = QVBoxLayout(w)
        self.v.setContentsMargins(14, 12, 14, 16)
        self.v.setSpacing(8)
        self.empty = QLabel("Belum ada foto dipilih.")
        self.empty.setObjectName("note")
        self.v.addWidget(self.empty)
        self.body = QWidget()
        self.v.addWidget(self.body)
        self.v.addStretch(1)
        self.body.hide()
        b = QVBoxLayout(self.body)
        b.setContentsMargins(0, 0, 0, 0)
        b.setSpacing(8)
        hd = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("cardTitle")
        self.title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.badge = QLabel()
        self.bPrev, self.bNext = btn("↑", "Foto sebelumnya (↑)", sm=True), btn("↓", "Foto berikutnya (↓)", sm=True)
        self.bPrev.clicked.connect(lambda: self.nav.emit(-1))
        self.bNext.clicked.connect(lambda: self.nav.emit(1))
        hd.addWidget(self.title, 1)
        hd.addWidget(self.badge)
        hd.addWidget(self.bPrev)
        hd.addWidget(self.bNext)
        b.addLayout(hd)
        self.g = QGridLayout()
        self.g.setSpacing(7)
        b.addLayout(self.g)
        self.f: dict[str, Field] = {}
        self.row = 0
        self._pair("hole_id", "box_no")
        self._pair("from_m", "to_m")
        self._pair("drill_start", "photo_date")
        self.iv = QLabel()
        self.iv.setObjectName("note")
        self.iv.setWordWrap(True)
        self.g.addWidget(self.iv, self.row, 0, 1, 2)
        self.row += 1
        self._sect("Geoteknik", "AI visual")
        self._pair("recovery_pct", "rqd_pct")
        self._pair("gsi", "rmr")
        self._pair("weathering", "condition")
        self._full("notes", multiline=True)
        self.conf = QLabel()
        self.conf.setObjectName("note")
        self.conf.setWordWrap(True)
        self.g.addWidget(self.conf, self.row, 0, 1, 2)
        self.row += 1
        self.geoSect = self._sect("Geologi", "")
        self._full("lithology")
        self._full("alteration")
        self._pair("oxidation", "color")
        self.err = QLabel()
        self.err.setObjectName("err")
        self.err.setWordWrap(True)
        b.addWidget(self.err)
        act = QGridLayout()
        act.setSpacing(6)
        self.bVer = btn("✓  Verifikasi && lanjut", "Ctrl+Enter", ok=True)
        self.bUnver = btn("Batalkan verifikasi")
        self.bAI = btn("Analisis foto ini")
        self.bShow = btn("Tampilkan file")
        act.addWidget(self.bVer, 0, 0)
        act.addWidget(self.bUnver, 0, 0)
        act.addWidget(self.bAI, 0, 1)
        act.addWidget(self.bShow, 1, 0)
        act.setColumnStretch(2, 1)
        b.addLayout(act)
        self.note = QLabel()
        self.note.setObjectName("note")
        self.note.setWordWrap(True)
        self.note.setTextFormat(Qt.RichText)
        b.addWidget(self.note)
        self.extra = QVBoxLayout()  # data lab, tanda, segmen (diisi modul lain)
        self.extra.setSpacing(8)
        b.addLayout(self.extra)
        self.hBtn = QToolButton()
        self.hBtn.setText("▸  Riwayat perubahan && jawaban asli AI")
        self.hBtn.setCheckable(True)
        self.hBtn.setStyleSheet("border:0;background:transparent;text-align:left")
        self.hTxt = QLabel()
        self.hTxt.setWordWrap(True)
        self.hTxt.setTextFormat(Qt.RichText)
        self.hTxt.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.hTxt.hide()
        b.addWidget(self.hBtn)
        b.addWidget(self.hTxt)
        self.hBtn.toggled.connect(self._hist)
        self.bVer.clicked.connect(lambda: self.verify.emit(self.r["id"], True))
        self.bUnver.clicked.connect(lambda: self.verify.emit(self.r["id"], False))
        self.bAI.clicked.connect(lambda: self.analyze.emit(self.r["id"]))
        self.bShow.clicked.connect(lambda: self.showFile.emit(self.r["id"]))
        self.r: dict = {}

    # ---------------------------------------------------------------- tata letak
    def _mk(self, k: str, multiline: bool = False) -> Field:
        f = Field(k, k, multiline)
        self.f[k] = f
        if multiline:
            f.ed.focusOutEvent = self._wrap_focus(f, f.ed.focusOutEvent)
        else:
            f.ed.editingFinished.connect(lambda f=f: self._commit(f))
        return f

    def _wrap_focus(self, f, orig):
        def h(e):
            orig(e)
            self._commit(f)
        return h

    def _pair(self, a: str, b: str) -> None:
        self.g.addWidget(self._mk(a), self.row, 0)
        self.g.addWidget(self._mk(b), self.row, 1)
        self.row += 1

    def _full(self, k: str, multiline: bool = False) -> None:
        self.g.addWidget(self._mk(k, multiline), self.row, 0, 1, 2)
        self.row += 1

    def _sect(self, t: str, em: str) -> QLabel:
        l = QLabel()
        l.setObjectName("sect")
        l.setTextFormat(Qt.RichText)
        l.setText(self._sect_html(t, em))
        self.g.addWidget(l, self.row, 0, 1, 2)
        self.row += 1
        return l

    @staticmethod
    def _sect_html(t: str, em: str) -> str:
        return f"{t} <span style='font-weight:400;font-size:7.6pt;letter-spacing:2px;color:{theme.C['mu']}'>{('· ' + em.upper()) if em else ''}</span>"

    def set_labels(self, labels: dict[str, str]) -> None:
        self.labels = labels
        for k, f in self.f.items():
            f.lbl.setText(labels.get(k, k).upper())

    # ---------------------------------------------------------------- isi
    def clear(self) -> None:
        self.r = {}
        self.body.hide()
        self.empty.show()

    def show_row(self, r: dict, logged_note: bool = True) -> None:
        same = self.r.get("id") == r["id"]
        self.r = r
        self.empty.hide()
        self.body.show()
        self.title.setText(r["name"])
        self.title.setToolTip(r["rel"])
        st, ck = status_text(r)
        self.badge.setText(st)
        self.badge.setStyleSheet(f"color:{theme.C['er' if ck == 'er' else 'ac2' if ck == 'ink' else 'mu']};font-weight:{700 if ck == 'ink' else 500}")
        log = r.get("log") or {}
        for k, f in self.f.items():
            if same and f.ed.hasFocus():
                continue
            lg = log.get(k) is not None
            mk = k == "recovery_pct" and r.get("rec_src") == "tanda"
            ed = not lg and not mk and k in (r.get("edited") or [])
            fn = not lg and not mk and not ed and k in (r.get("from_name") or [])
            ai = not lg and not mk and not ed and not fn and r.get("status") == "done" and not r.get("verified") and r.get(k) is not None
            kind = "mk" if mk else "lgt" if lg else "ed" if ed else "fn" if fn else "ai" if ai else ""
            if lg:
                f.set(str(log[k]), kind, True, ("Isian AI / manual (tidak dipakai): " + fmt(r.get(k))) if r.get(k) is not None else "Dari logging geologist")
            else:
                f.set(fmt(r.get(k)), kind, False)
        iv = f"{r['to_m'] - r['from_m']:.2f} m" if r.get("from_m") is not None and r.get("to_m") is not None else "–"
        self.iv.setText(f"INTERVAL  <b style='font-family:\"{theme.MONO}\"'>{iv}</b>  <span>{_esc(r['rel'])}</span>")
        self.iv.setTextFormat(Qt.RichText)
        conf = r.get("ai_conf") or "–"
        model = f" · {r['ai_model']}" + (f" · {r['ai_secs']} dtk" if r.get("ai_secs") else "") if r.get("ai_model") else ""
        self.conf.setText(f"KEYAKINAN AI  <b>{_esc(conf)}</b>{_esc(model)}")
        self.conf.setTextFormat(Qt.RichText)
        self.geoSect.setText(self._sect_html("Geologi", "logging geologist" if log else "belum ada logging, isian AI / manual"))
        self.err.setText("AI gagal: " + r["error"] if r.get("error") and r.get("status") == "error" else "")
        self.err.setVisible(bool(self.err.text()))
        self.bVer.setVisible(not r.get("verified"))
        self.bUnver.setVisible(bool(r.get("verified")))
        self.bAI.setEnabled(not r.get("missing") and not r.get("verified"))
        self.bAI.setText("Analisis ulang" if r.get("status") == "done" else "Analisis foto ini")
        n = ("Isian bertanda <b>logging</b> berasal dari logging geologist dan diutamakan; AI tidak menimpanya. " if log else "")
        n += (f"Diverifikasi oleh <b>{_esc(r.get('verified_by') or '-')}</b> · {_esc(r.get('verified_at') or '')}" if r.get("verified")
              else "Sel biru muda = isian AI yang belum dicek. Isian yang Anda edit tidak akan ditimpa AI.")
        if r.get("edited_by"):
            n += f"<br>Terakhir diedit: {_esc(r['edited_by'])} · {_esc(r.get('edited_at') or '')}"
        self.note.setText(n)
        if not same:
            self.hBtn.setChecked(False)
        elif self.hBtn.isChecked():
            self.history.emit(r["id"])

    def _commit(self, f: Field) -> None:
        if not self.r or f.ed.isReadOnly():
            return
        if f.value().strip() != fmt(self.r.get(f.k)).strip():
            self.edited.emit(self.r["id"], f.k, f.value())

    def _hist(self, on: bool) -> None:
        self.hBtn.setText(("▾" if on else "▸") + "  Riwayat perubahan && jawaban asli AI")
        self.hTxt.setVisible(on)
        if on and self.r:
            self.hTxt.setText("Memuat…")
            self.history.emit(self.r["id"])

    def set_history(self, pid: int, j: dict) -> None:
        if pid != self.r.get("id"):
            return
        mu = theme.C["mu"]
        h = "".join(f"<div><b>{_esc(self.labels.get(x['field'], x['field']))}</b>: {_esc(x['old'] if x['old'] is not None else '–')} → "
                    f"{_esc(x['new'] if x['new'] is not None else '–')} <span style='color:{mu}'>· {_esc(x.get('by') or '')} · {_esc(x['src'])} · {_esc(x['at'])}</span></div>"
                    for x in j.get("history") or []) or "<div>Belum ada perubahan.</div>"
        if j.get("ai"):
            h += (f"<div style='margin-top:6px'><b>Jawaban asli AI:</b><pre style='font-family:\"{theme.MONO}\";font-size:8pt;white-space:pre-wrap'>"
                  + _esc(json.dumps(j["ai"], indent=1, ensure_ascii=False)) + "</pre></div>")
        self.hTxt.setText(h)


def _esc(s) -> str:
    return str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
