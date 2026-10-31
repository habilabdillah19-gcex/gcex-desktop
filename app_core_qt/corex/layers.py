"""Lapisan di foto (port dari app-core): overlay berlapis (assay, logging, segmen per baris, kartu foto), tanda interval
(half core / core loss / jenis lain), editor segmen per baris, kalibrasi area core box; plus kotak Data lab / Segmen / Tanda di kartu.

Geometri: area core box (tray) = pecahan foto x0..x1, y0..y1 dengan `rows` baris; baris dibaca kiri -> kanan, atas -> bawah.
Posisi sepanjang box f (0..1) -> kedalaman = from + f * (to - from)."""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QCompleter, QDoubleSpinBox, QFileDialog, QFrame, QGraphicsObject, QGridLayout, QSizePolicy,
                               QHBoxLayout, QInputDialog, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from . import api, theme
from .card import LISTS, _esc, btn
from .dialogs import ask, say
from .table import fmt
from .util import SET, run_bg

BLUES = ["#dbe7f5", "#9fbfe6", "#5a8fd0", "#2a5ea8", "#141a26"]
GEOC = ["#c9b48a", "#8fa3b8", "#b98a6a", "#7f9a86", "#a690b5", "#c7a0a0", "#6f7f99", "#b8b06d", "#8a8f96", "#d1a86a"]
RAMP = ["#b2182b", "#ef8a62", "#fddbc7", "#a6d96a", "#1a9850"]
WEA_P = ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027", "#7f0000"]
OXI_P = ["#4575b4", "#91bfdb", "#fee090", "#fc8d59", "#d73027"]
NUM_BRK = {"rqd_pct": [25, 50, 75, 90], "recovery_pct": [50, 75, 90, 95], "rmr": [21, 41, 61, 81], "ff_per_m": [2, 5, 10, 20]}
SRC_LBL = {"a": "Assay", "g": "Logging", "s": "Interpretasi per baris", "c": "Kartu foto"}
SEGF = [("lithology", "s", "Litologi"), ("alteration", "s", "Alterasi"), ("color", "s", "Warna"), ("weathering", "o", "Pelapukan"), ("oxidation", "o", "Oksidasi"),
        ("rqd_pct", "n", "RQD (%)"), ("recovery_pct", "n", "Recovery (%)"), ("ff_per_m", "n", "Rekahan / m"), ("gsi", "o", "GSI"), ("rmr", "n", "RMR"), ("notes", "s", "Catatan")]
CARDF = [("lithology", "s", "Litologi"), ("alteration", "s", "Alterasi"), ("color", "s", "Warna"), ("weathering", "o", "Pelapukan"), ("oxidation", "o", "Oksidasi"),
         ("recovery_pct", "n", "Recovery (%)"), ("rqd_pct", "n", "RQD (%)"), ("gsi", "o", "GSI"), ("rmr", "n", "RMR"), ("condition", "s", "Kondisi")]
MK_LBL = {"halfcore": "Half core", "coreloss": "Core loss"}
MK_COL = {"halfcore": "#d08a1e", "coreloss": "#b4462f"}
SEL = "#2a5ea8"
YEL = "#ffd43b"


def mk_label(k: str) -> str:
    return MK_LBL.get(k, k)


def mk_color(k: str) -> str:
    return MK_COL.get(k, "#7a5aa6")


def geo_color(code) -> str:
    h = 0
    for ch in str(code):
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return GEOC[h % len(GEOC)]


def idx_b(c: list, v: float) -> int:
    i = 0
    while i < len(c) and v >= c[i]:
        i += 1
    return i


def short_v(v) -> str:
    if isinstance(v, (int, float)):
        return fmt(v)
    s = str(v)
    m = re.match(r"^(W[1-6])", s, re.I)
    return m.group(1).upper() if m else re.sub(r"\s*\(.*\)$", "", s)


def ord_idx(col: str, v) -> int:
    s = str(v)
    if re.search("gsi", col, re.I):
        n = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
        return min(4, int(sum(n) / len(n) // 20)) if n else -1
    if re.search("oxi|oks", col, re.I):
        L = ["un", "slight", "moder", "strong", "complete"]
        i = next((i for i, w in enumerate(L) if s.lower().startswith(w)), -1)
        if i >= 0:
            return i
        m = re.search(r"(\d)", s)
        return min(4, int(m.group(1)) - 1) if m else -1
    m = re.search(r"W\s*([1-6])", s, re.I)
    if m:
        return int(m.group(1)) - 1
    L = ["fresh", "slight", "moder", "high", "complete", "residual"]
    return next((i for i, w in enumerate(L) if w in s.lower()), -1)


def depth_segs(a: float, b: float, f: float, t: float, rows: int) -> list[tuple[int, float, float]]:
    """Interval kedalaman f..t di box a..b -> potongan (baris, u0, u1) dengan u = pecahan lebar baris."""
    L = b - a
    if L <= 0:
        return []
    s0, s1 = max(0.0, (max(f, a) - a) / L * rows), min(float(rows), (min(t, b) - a) / L * rows)
    out = []
    while s0 < s1 - 1e-9:
        row = min(rows - 1, int(s0 + 1e-9))
        e = min(s1, row + 1)
        out.append((row, s0 - row, e - row))
        s0 = e
    return out


def frac_segs(f0: float, f1: float, rows: int):
    return depth_segs(0, 1, f0, f1, rows)


# ================================================================ status overlay
class Ov:
    def __init__(self, win) -> None:
        self.win = win
        self.on = bool(SET.get("ov", False))
        self.lbl = bool(SET.get("ovLbl", True))
        self.cls: dict = dict(SET.get("ovCls", {}) or {})
        self.colors: dict = {}
        self.layers: list[dict] | None = None
        self.auto = False

    def num_cols(self) -> list[str]:
        return [c["name"] for c in ((self.win.dh or {}).get("columns") or {}).get("assay", []) if c.get("type") == "n"]

    def geo_cols(self) -> list[str]:
        return [c["name"] for c in ((self.win.dh or {}).get("columns") or {}).get("geology", [])]

    def meta(self, k: str) -> dict:
        src, col = k[0], k[2:]
        kind, label = "s", col
        if src == "a":
            kind = "grade"
        elif src == "g":
            c = next((x for x in ((self.win.dh or {}).get("columns") or {}).get("geology", []) if x["name"] == col), None)
            if re.search(r"weath|lapuk|oxid|oks", col, re.I) or re.match(r"^gsi$", col, re.I):
                kind = "o"
            elif c and c.get("type") == "n":
                kind = "n" if re.search(r"rqd|rec|rmr|ff|frac", col, re.I) else "grade"
        else:
            f = next((x for x in (SEGF if src == "s" else CARDF) if x[0] == col), None)
            if f:
                kind, label = f[1], f[2]
        return {"src": src, "col": col, "kind": kind, "label": SRC_LBL[src] + " · " + label, "short": label}

    def avail(self) -> list[str]:
        return (["a:" + n for n in self.num_cols()] + ["g:" + n for n in self.geo_cols()] + ["s:" + f[0] for f in SEGF] + ["c:" + f[0] for f in CARDF])

    def presets(self) -> dict:
        nc, gc = self.num_cols(), self.geo_cols()
        au = next((n for n in nc if n.lower().startswith("au")), nc[0] if nc else None)
        lith = next((n for n in gc if re.search("lith|lito", n, re.I)), None)
        alt = next((n for n in gc if re.search("alt", n, re.I)), None)
        return {"Assay + logging": ["a:" + au if au else None, "g:" + (lith or (gc[0] if gc else "")) if (lith or gc) else None],
                "Geologi: AI vs logging": ["s:lithology", "g:" + lith if lith else None, "s:alteration", "g:" + alt if alt else None, "s:weathering"],
                "Geoteknik": ["s:rqd_pct", "s:recovery_pct", "s:ff_per_m", "s:weathering"],
                "Kartu foto (per box)": ["c:rqd_pct", "c:recovery_pct", "c:weathering", "c:lithology"]}

    def defaults(self) -> None:
        if self.layers is not None and not self.auto:
            av = set(self.avail())
            self.layers = [l for l in self.layers if l["k"] in av]
            return
        self.auto = True
        ks = [k for k in self.presets()["Assay + logging"] if k] + ["s:weathering", "s:rqd_pct"]
        self.layers = [{"k": k, "on": True} for k in ks]

    def load_cfg(self, meta: dict) -> None:
        c = None
        try:
            c = json.loads(meta.get("ov_layers") or "null")
        except (TypeError, ValueError):
            c = None
        c = c or SET.get("ovCfg")
        self.layers = c.get("layers") if c else None
        self.auto = False
        self.colors = (c or {}).get("colors") or {}
        if c and c.get("cls"):
            self.cls.update(c["cls"])
        self.defaults()

    def save(self) -> None:
        self.auto = False
        cfg = {"layers": self.layers, "colors": self.colors, "cls": self.cls}
        SET.set("ovCfg", cfg)
        SET.set("ovCls", self.cls)
        if self.win.folder:
            try:
                self.win.meta = api.call("/core/meta", {"folder": self.win.folder, "values": {"ov_layers": json.dumps(cfg)}})["meta"]
            except api.ApiError:
                pass

    def grade_classes(self, el: str) -> list[float]:
        if el in self.cls:
            return self.cls[el]
        if el.lower().startswith("au"):
            return [0.1, 0.5, 1, 3]
        if el.lower().startswith("ag"):
            return [5, 20, 50, 100]
        v = sorted(x for x in ((r.get("g") or {}).get(el) for r in self.win.rows) if x is not None)
        if len(v) < 5:
            return [0.1, 0.5, 1, 3]
        q = lambda f: float(f"{v[min(len(v) - 1, int(f * len(v)))]:.2g}")  # noqa: E731
        return sorted({q(.2), q(.4), q(.6), q(.8)})

    def breaks(self, k: str, m: dict) -> list[float]:
        if k in self.cls:
            return self.cls[k]
        if m["kind"] == "grade":
            return self.grade_classes(m["col"])
        c = m["col"]
        return NUM_BRK.get(c) or (NUM_BRK["rqd_pct"] if re.search("rqd|rec", c, re.I) else NUM_BRK["rmr"] if re.search("rmr", c, re.I)
                                  else NUM_BRK["ff_per_m"] if re.search("ff|frac", c, re.I) else [25, 50, 75, 90])

    def palette(self, m: dict) -> list[str]:
        if m["kind"] == "grade":
            return BLUES
        return RAMP[::-1] if re.search("ff|frac", m["col"], re.I) else RAMP

    def color(self, k: str, m: dict, v) -> str | None:
        if v is None or v == "":
            return None
        own = (self.colors.get(k) or {}).get(str(v))
        if own:
            return own
        if m["kind"] in ("grade", "n"):
            try:
                x = float(v)
            except (TypeError, ValueError):
                return geo_color(v)
            return self.palette(m)[min(idx_b(self.breaks(k, m), x), 5)]
        if m["kind"] == "o":
            i = ord_idx(m["col"], v)
            if i < 0:
                return geo_color(v)
            P = RAMP if re.search("gsi", m["col"], re.I) else OXI_P if re.search("oxi|oks", m["col"], re.I) else WEA_P
            return P[min(i, len(P) - 1)]
        return geo_color(v)

    def items(self, l: dict, r: dict, det: dict | None, segs: list[dict]) -> tuple[dict, list[dict]]:
        m = self.meta(l["k"])
        a, b = r.get("from_m"), r.get("to_m")
        out: list[dict] = []
        if m["src"] in ("a", "g") and det and a is not None and b is not None and b > a:
            for x in det.get("assay" if m["src"] == "a" else "geology") or []:
                v = x.get(m["col"])
                if v is None:
                    continue
                f0, f1 = max(0.0, (x["f"] - a) / (b - a)), min(1.0, (x["t"] - a) / (b - a))
                if f1 > f0:
                    out.append({"f0": f0, "f1": f1, "v": v})
        elif m["src"] == "s":
            for s in segs:
                v = s.get(m["col"])
                if v is None or v == "":
                    continue
                out.append({"f0": s["f0"], "f1": s["f1"], "v": v, "ai": s["src"] == "ai" and m["col"] not in s["edited"], "id": s["id"]})
        elif m["src"] == "c":
            log = r.get("log") or {}
            lg = log.get(m["col"]) is not None
            v = log[m["col"]] if lg else r.get(m["col"])
            if v is not None and v != "":
                out.append({"f0": 0.0, "f1": 1.0, "v": v, "box": True,
                            "ai": not lg and r.get("status") == "done" and not r.get("verified") and m["col"] not in (r.get("edited") or [])
                            and not (m["col"] == "recovery_pct" and r.get("rec_src") == "tanda")})
        return m, out


# ================================================================ kanvas di atas foto
class Canvas(QGraphicsObject):
    """Satu item (anak akar foto) yang menggambar overlay, tanda, editor segmen dan kalibrasi."""

    def __init__(self, it: "Interp"):
        super().__init__(it.viewer.root)
        self.it = it
        self.setZValue(5)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self) -> QRectF:  # noqa: N802
        v = self.it.viewer
        return QRectF(0, 0, max(1.0, v.w), max(1.0, v.h))

    def paint(self, p: QPainter, opt, w=None) -> None:
        it = self.it
        v = it.viewer
        if not v.w or not it.r or it.r.get("missing"):
            return
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        if it.cal_t:
            it.paint_cal(p)
            return
        if it.ov.on:
            it.paint_overlay(p)
        if it.sg_mode:
            it.paint_seg_edit(p)
        if it.mk_show or it.mk_mode:
            it.paint_marks(p)


def pen(c: str, w: float = 1.0, dash: bool = False, alpha: float = 1.0) -> QPen:
    q = QColor(c)
    q.setAlphaF(alpha)
    pe = QPen(q, w)
    pe.setCosmetic(True)
    if dash:
        pe.setDashPattern([4, 3])
    return pe


def halo_text(p: QPainter, x: float, y: float, text: str, size: float, fill: str, stroke: str, align: str = "c", bold: bool = True) -> None:
    f = QFont(theme.MONO)
    f.setPixelSize(max(1, int(size)))
    f.setBold(bold)
    path = QPainterPath()
    from PySide6.QtGui import QFontMetricsF
    fm = QFontMetricsF(f)
    tw = fm.horizontalAdvance(text)
    x0 = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)
    path.addText(QPointF(x0, y + fm.ascent() / 2 - fm.descent() / 2), f, text)
    pe = QPen(QColor(stroke), size * 0.22)
    pe.setJoinStyle(Qt.RoundJoin)
    p.strokePath(path, pe)
    p.fillPath(path, QBrush(QColor(fill)))


# ================================================================ alat edit di foto
class SegTool:
    def __init__(self, it: "Interp"):
        self.it = it
        self.drag: dict | None = None

    def _bound_at(self, pt: QPointF):
        it = self.it
        g = it.geo()
        if not g:
            return None
        tol = it.viewer.px(6)
        rows = g["rows"]
        for s in it.segs:
            for side, f in (("start", s["f0"]), ("end", s["f1"])):
                ff = f - 1e-6 if side == "end" and f > 0 and abs(f * rows - round(f * rows)) < 1e-6 else f
                sp = ff * rows
                row = min(rows - 1, int(sp + 1e-9))
                x = g["X0"] + (sp - row) * g["BW"]
                y0 = g["Y0"] + row * g["RH"]
                if abs(pt.x() - x) <= tol and y0 <= pt.y() <= y0 + g["RH"]:
                    return s, side
        return None

    def hover(self, pt):
        return Qt.SizeHorCursor if self._bound_at(pt) else Qt.CrossCursor

    def press(self, pt, e) -> bool:
        it = self.it
        f = it.pos_frac(pt, 0.05)
        if f is None:
            return False
        hit = self._bound_at(pt)
        if hit:
            s, side = hit
            old = s["f0"] if side == "start" else s["f1"]
            nb = next((x for x in it.segs if x["id"] != s["id"] and abs((x["f1"] if side == "start" else x["f0"]) - old) < 2e-3), None)
            self.drag = {"type": "bd", "s": s, "side": side, "nb": nb}
            return True
        sid = next((s["id"] for s in it.segs if s["f0"] <= f <= s["f1"] and it.in_tray(pt)), None)
        if sid is not None:
            it.sg_sel, it.sg_click = sid, it.pos_frac(pt, 0.05)
            it.seg_form(next(s for s in it.segs if s["id"] == sid))
            it.update()
            return True
        self.drag = {"type": "new", "a": f, "b": f}
        return True

    def move(self, pt) -> None:
        d, it = self.drag, self.it
        f = it.pos_frac(pt, 0.05)
        if not d or f is None:
            return
        if d["type"] == "bd":
            s, nb = d["s"], d["nb"]
            if d["side"] == "start":
                s["f0"] = min(f, s["f1"] - 0.005)
                if nb:
                    nb["f1"] = s["f0"]
            else:
                s["f1"] = max(f, s["f0"] + 0.005)
                if nb:
                    nb["f0"] = s["f1"]
        else:
            d["b"] = f
        it.update()

    def release(self, pt) -> None:
        d, it = self.drag, self.it
        self.drag = None
        if not d:
            return
        if d["type"] == "bd":
            s, side = d["s"], d["side"]
            f = s["f0"] if side == "start" else s["f1"]
            try:
                it.seg_apply(api.call("/core/segs/bound", {"folder": it.win.folder, "by": it.win.user(), "seg_id": s["id"], "side": side, "f": f}))
                it.win.toast(f"Batas digeser ke {fmt(it.depth(f))} m")
            except api.ApiError as e:
                say(it.win, str(e), warn=True)
                it.load_segs()
            return
        it.update()
        if abs(d["b"] - d["a"]) < 0.004:
            return
        it.sg_sel = None
        it.seg_form({"id": None, "f0": min(d["a"], d["b"]), "f1": max(d["a"], d["b"]), "edited": [], "src": "manual"})


class MarkTool:
    def __init__(self, it: "Interp"):
        self.it = it
        self.drag: dict | None = None

    def _hit(self, pt):
        it = self.it
        g = it.geo()
        r = it.r
        if not g:
            return None
        for m in it.marks:
            for row, u0, u1 in depth_segs(r["from_m"], r["to_m"], m["from_m"], m["to_m"], g["rows"]):
                x0 = g["X0"] + u0 * g["BW"]
                y = g["Y0"] + row * g["RH"] + g["RH"] * 0.22
                if QRectF(x0, y, max(it.viewer.px(4), (u1 - u0) * g["BW"]), g["RH"] * 0.56).contains(pt):
                    return m
        return None

    def hover(self, pt):
        return Qt.PointingHandCursor if self._hit(pt) else Qt.CrossCursor

    def press(self, pt, e) -> bool:
        it = self.it
        m = self._hit(pt)
        if m:
            it.mark_form(m)
            return True
        p = it.mark_pos(pt)
        if not p:
            return False
        self.drag = {"a": p, "b": p}
        it.mark_form_close()
        it.mk_drag = self.drag
        it.update()
        return True

    def move(self, pt) -> None:
        p = self.it.mark_pos(pt)
        if p and self.drag:
            self.drag["b"] = p
            self.it.update()

    def release(self, pt) -> None:
        it, d = self.it, self.drag
        self.drag = it.mk_drag = None
        if not d or abs(d["b"]["s"] - d["a"]["s"]) < 0.01:
            it.update()
            return
        p, q = (d["a"], d["b"]) if d["a"]["s"] <= d["b"]["s"] else (d["b"], d["a"])
        f, t = p["d"], q["d"]
        if t <= f:
            t = round(f + 0.05, 2)
        it.mark_form({"id": None, "kind": it.mk_kind, "from_m": f, "to_m": t, "sample_no": "", "note": "", "row0": p["row"], "x0": p["u"],
                      "row1": q["row"], "x1": q["u"]})


class CalTool:
    def __init__(self, it: "Interp"):
        self.it = it
        self.drag: dict | None = None

    def _handle(self, pt):
        it = self.it
        t, W, H = it.cal_t, it.viewer.w, it.viewer.h
        hs = it.viewer.px(9)
        for k, x, y in (("nw", t["x0"], t["y0"]), ("ne", t["x1"], t["y0"]), ("sw", t["x0"], t["y1"]), ("se", t["x1"], t["y1"])):
            if abs(pt.x() - x * W) <= hs and abs(pt.y() - y * H) <= hs:
                return k
        if t["x0"] * W <= pt.x() <= t["x1"] * W and t["y0"] * H <= pt.y() <= t["y1"] * H:
            return "move"
        return None

    def hover(self, pt):
        h = self._handle(pt)
        return {"nw": Qt.SizeFDiagCursor, "se": Qt.SizeFDiagCursor, "ne": Qt.SizeBDiagCursor, "sw": Qt.SizeBDiagCursor, "move": Qt.SizeAllCursor}.get(h)

    def press(self, pt, e) -> bool:
        h = self._handle(pt)
        if not h:
            return False
        self.drag = {"h": h, "t0": dict(self.it.cal_t), "p0": QPointF(pt)}
        return True

    def move(self, pt) -> None:
        d = self.drag
        if not d:
            return
        it = self.it
        dx, dy = (pt.x() - d["p0"].x()) / it.viewer.w, (pt.y() - d["p0"].y()) / it.viewer.h
        t, t0, h = it.cal_t, d["t0"], d["h"]
        cl = lambda v: max(0.0, min(1.0, v))  # noqa: E731
        if h == "move":
            w, hh = t0["x1"] - t0["x0"], t0["y1"] - t0["y0"]
            t["x0"] = cl(min(1 - w, t0["x0"] + dx))
            t["y0"] = cl(min(1 - hh, t0["y0"] + dy))
            t["x1"], t["y1"] = t["x0"] + w, t["y0"] + hh
        else:
            if "w" in h:
                t["x0"] = cl(min(t0["x1"] - .02, t0["x0"] + dx))
            if "e" in h:
                t["x1"] = cl(max(t0["x0"] + .02, t0["x1"] + dx))
            if "n" in h:
                t["y0"] = cl(min(t0["y1"] - .02, t0["y0"] + dy))
            if "s" in h:
                t["y1"] = cl(max(t0["y0"] + .02, t0["y1"] + dy))
        it.update()

    def release(self, pt) -> None:
        self.drag = None


# ================================================================ pengendali
def _row(*ws, stretch: bool = True) -> QHBoxLayout:
    h = QHBoxLayout()
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(6)
    for w in ws:
        if isinstance(w, str):
            l = QLabel(w)
            h.addWidget(l)
        else:
            h.addWidget(w)
    if stretch:
        h.addStretch(1)
    return h


def _panel() -> QFrame:
    f = QFrame()
    f.setObjectName("panel")
    f.setStyleSheet(f"QFrame#panel{{background:{theme.C['pn2']};border-bottom:1px solid {theme.C['bd']};}}")
    return f


def _html_label() -> QLabel:
    l = QLabel()
    l.setWordWrap(True)
    l.setTextFormat(Qt.RichText)
    l.setTextInteractionFlags(Qt.TextBrowserInteraction)
    l.setOpenExternalLinks(False)
    return l


class Interp:
    def __init__(self, win) -> None:
        self.win = win
        self.viewer = win.viewer
        self.ov = Ov(win)
        self.r: dict | None = None
        self.det: dict | None = None
        self.segs: list[dict] = []
        self.marks: list[dict] = []
        self.tok = 0
        self.sg_mode = False
        self.sg_sel = None
        self.sg_click = None
        self.sg_cur: dict | None = None
        self.mk_open = False
        self.mk_mode = False
        self.mk_show = bool(SET.get("mkShow", True))
        self.mk_kind = SET.get("mkKind", "halfcore")
        self.mk_edit: dict | None = None
        self.mk_drag: dict | None = None
        self.cal_t: dict | None = None
        self.canvas = Canvas(self)
        self.seg_tool, self.mark_tool, self.cal_tool = SegTool(self), MarkTool(self), CalTool(self)
        self.bOv = self.viewer.add_tool("ov", "≡", "Overlay hasil assay, logging & interpretasi di foto", True)
        self.bMk = self.viewer.add_tool("mk", "▧", "Tandai interval half core / core loss di foto", True)
        self.bOv.setChecked(self.ov.on)
        self.bOv.toggled.connect(self.toggle_ov)
        self.bMk.toggled.connect(self.mark_open)
        self.viewer.loaded.connect(lambda pid: self.update())
        self._build_panels()
        self._build_boxes()

    # ---------------------------------------------------------------- panel
    def _build_panels(self) -> None:
        host = self.win.panels.layout()
        # overlay
        self.pOv = _panel()
        v = QVBoxLayout(self.pOv)
        v.setContentsMargins(10, 6, 10, 6)
        v.setSpacing(4)
        self.ovPre = QComboBox()
        self.ovAdd = QComboBox()
        self.ovLbl = QCheckBox("nilai")
        self.ovLbl.setChecked(self.ov.lbl)
        self.bSg = btn("Edit segmen", "Edit segmen interpretasi per baris (AI / manual) langsung di foto", sm=True)
        self.bCal = btn("Atur area core", "Atur kotak area core box & jumlah baris", sm=True)
        t = QLabel("<b>OVERLAY</b>")
        for cb in (self.ovPre, self.ovAdd):
            cb.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            cb.setMinimumContentsLength(4)
        v.addLayout(_row(t, self.ovPre, self.ovAdd, self.ovLbl, stretch=True))
        self.ovL = QVBoxLayout()
        self.ovL.setSpacing(2)
        v.addLayout(self.ovL)
        self.sgHint = QLabel("Klik segmen untuk mengedit nilainya · tarik <b>garis batas</b> kuning untuk menggeser · tarik di area kosong untuk segmen baru · Esc = selesai.")
        self.sgHint.setObjectName("note")
        self.sgHint.setWordWrap(True)
        self.sgHint.hide()
        v.addWidget(self.sgHint)
        self.sgForm = QWidget()
        self.sgForm.hide()
        v.addWidget(self.sgForm)
        self.ovInfo = QLabel()
        self.ovInfo.setObjectName("note")
        self.ovInfo.setWordWrap(True)
        self.ovInfo.setMinimumWidth(1)
        self.ovInfo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        v.addLayout(_row(self.ovInfo, self.bSg, self.bCal, stretch=False))
        self.pOv.setVisible(self.ov.on)
        host.addWidget(self.pOv)
        self.ovPre.activated.connect(self._preset)
        self.ovAdd.activated.connect(self._add)
        self.ovLbl.toggled.connect(lambda on: (setattr(self.ov, "lbl", on), SET.set("ovLbl", on), self.update()))
        self.bSg.clicked.connect(lambda: self.seg_mode(not self.sg_mode))
        self.bCal.clicked.connect(self.cal_start)
        # kalibrasi
        self.pCal = _panel()
        v = QVBoxLayout(self.pCal)
        v.setContentsMargins(10, 6, 10, 6)
        h = QLabel("<b>AREA CORE BOX</b> Tarik kotak biru menutupi semua baris core (sudut = ukuran, tengah = geser). Baris 1 = paling dangkal, kiri → kanan.")
        h.setWordWrap(True)
        v.addWidget(h)
        self.calRows = QSpinBox()
        self.calRows.setRange(1, 12)
        self.calRows.valueChanged.connect(lambda n: self.cal_t and (self.cal_t.__setitem__("rows", n), self.update()))
        b1, b2, b3, bx = btn("Foto ini", pri=True, sm=True), btn("Semua foto lubang ini", sm=True), btn("Bawaan proyek", sm=True), btn("Batal", sm=True)
        b1.clicked.connect(lambda: self.cal_save("photo"))
        b2.clicked.connect(lambda: self.cal_save("hole"))
        b3.clicked.connect(lambda: self.cal_save("default"))
        bx.clicked.connect(self.cal_end)
        v.addLayout(_row("Jumlah baris", self.calRows, bx))
        v.addLayout(_row("Simpan untuk:", b1, b2, b3))
        self.pCal.hide()
        host.addWidget(self.pCal)
        # tanda
        self.pMk = _panel()
        v = QVBoxLayout(self.pMk)
        v.setContentsMargins(10, 6, 10, 6)
        v.setSpacing(4)
        self.mkKind = QComboBox()
        self.bMkMode = btn("Mulai menandai", sm=True)
        self.mkShowCb = QCheckBox("tampil")
        self.mkShowCb.setChecked(self.mk_show)
        bcsv, bcl = btn("CSV", "Semua tanda di proyek (CSV)", sm=True), btn("Tutup", sm=True)
        v.addLayout(_row(QLabel("<b>TANDA INTERVAL</b>"), "Jenis", self.mkKind, self.bMkMode, self.mkShowCb, bcsv, bcl))
        self.mkHint = QLabel()
        self.mkHint.setObjectName("note")
        self.mkHint.setWordWrap(True)
        self.mkHint.setTextFormat(Qt.RichText)
        v.addWidget(self.mkHint)
        self.mkForm = QWidget()
        g = QHBoxLayout(self.mkForm)
        g.setContentsMargins(0, 0, 0, 0)
        g.setSpacing(6)
        self.mkFT = QLabel()
        self.mkF, self.mkT = QDoubleSpinBox(), QDoubleSpinBox()
        for x in (self.mkF, self.mkT):
            x.setDecimals(2)
            x.setRange(0, 100000)
            x.setSingleStep(0.05)
            x.setFixedWidth(84)
            x.valueChanged.connect(self._mk_range)
        self.mkS = QLineEdit()
        self.mkS.setFixedWidth(100)
        self.mkSL = QLabel("No. sampel")
        self.mkN = QLineEdit()
        self.mkN.setMinimumWidth(120)
        bs, self.bMkDel, bc = btn("Simpan", pri=True, sm=True), btn("Hapus", sm=True), btn("Batal", sm=True)
        for x in (self.mkFT, QLabel("From"), self.mkF, QLabel("To"), self.mkT, self.mkSL, self.mkS, QLabel("Catatan"), self.mkN, bs, self.bMkDel, bc):
            g.addWidget(x)
        self.mkErr = QLabel()
        self.mkErr.setObjectName("err")
        self.mkErr.setWordWrap(True)
        v.addWidget(self.mkForm)
        v.addWidget(self.mkErr)
        self.mkForm.hide()
        self.pMk.hide()
        host.addWidget(self.pMk)
        self.mkKind.activated.connect(self._mk_kind)
        self.bMkMode.clicked.connect(lambda: self.mark_mode(not self.mk_mode))
        self.mkShowCb.toggled.connect(lambda on: (setattr(self, "mk_show", on), SET.set("mkShow", on), self.update()))
        bcsv.clicked.connect(self.mark_csv)
        bcl.clicked.connect(lambda: self.bMk.setChecked(False))
        bs.clicked.connect(self.mark_save)
        bc.clicked.connect(lambda: (self.mark_form_close(), self.update()))
        self.bMkDel.clicked.connect(lambda: self.mk_edit and self.mk_edit.get("id") and self.mark_delete(self.mk_edit["id"]))
        for w in (self.mkS, self.mkN):
            w.returnPressed.connect(self.mark_save)
        self._mk_hint()

    def _build_boxes(self) -> None:
        ex = self.win.card.extra
        self.boxSeg, self.boxMk, self.boxLab = _html_label(), _html_label(), _html_label()
        for b in (self.boxSeg, self.boxMk, self.boxLab):
            ex.addWidget(b)
        self.boxSeg.linkActivated.connect(self._link)
        self.boxMk.linkActivated.connect(self._link)

    def _link(self, href: str) -> None:
        k, _, v = href.partition(":")
        if k == "sgo":
            self.seg_mode(True)
        elif k == "sgr":
            self.seg_mode(True)
            if self.sg_mode:
                self.sg_sel, self.sg_click = int(v), None
                self.seg_form(next(s for s in self.segs if s["id"] == int(v)))
                self.update()
        elif k == "mgo":
            self.bMk.setChecked(True)
            self.mark_mode(True)
        elif k == "mke":
            self.bMk.setChecked(True)
            self.mark_form(next(m for m in self.marks if m["id"] == int(v)))
        elif k == "mkd":
            self.mark_delete(int(v))

    # ---------------------------------------------------------------- muat data foto
    def load(self, r: dict) -> None:
        self.r = r
        self.tok += 1
        tok = self.tok
        self.det, self.segs, self.marks = None, [], []
        self.sg_sel = None
        self.seg_form_close()
        self.mark_form_close()
        if self.cal_t:
            self.cal_end()
        self.render_boxes()
        self.update()
        folder, pid = self.win.folder, r["id"]

        def work():
            out = {"det": api.call("/core/dh/photo", {"folder": folder, "id": pid})}
            try:
                out["segs"] = api.call("/core/segs/list", {"folder": folder, "id": pid})["segs"]
            except api.ApiError:
                out["segs"] = []
            out["marks"] = api.call("/core/marks/list", {"folder": folder, "id": pid})["marks"]
            return out

        def ok(j):
            if tok != self.tok:
                return
            self.det, self.segs, self.marks = j["det"], j["segs"], j["marks"]
            self._mk_kinds()
            self.render_boxes()
            self.ov_panel()
            self.update()

        run_bg(work, ok=ok, err=lambda e: tok == self.tok and self.boxLab.setText(f"<span style='color:{theme.C['er']}'>{_esc(e)}</span>"))

    def row_changed(self, r: dict) -> None:
        """Baris foto diperbarui (mis. setelah AI): muat ulang segmen bila jumlahnya berubah."""
        if not self.r or r["id"] != self.r["id"]:
            return
        self.r = r
        if r.get("n_segs", 0) != len(self.segs) and not self.sg_cur and not self.sg_mode:
            try:
                self.segs = api.call("/core/segs/list", {"folder": self.win.folder, "id": r["id"]})["segs"]
            except api.ApiError:
                pass
        self.render_boxes()
        self.ov_panel()
        self.update()

    def load_segs(self) -> None:
        if self.r:
            self.segs = api.call("/core/segs/list", {"folder": self.win.folder, "id": self.r["id"]})["segs"]
            self.render_boxes()
            self.update()

    def dh_changed(self) -> None:
        if self.ov.layers is None:
            self.ov.load_cfg(self.win.meta)
        else:
            self.ov.defaults()
        self.ov_panel()

    def relayout(self) -> None:
        a = getattr(self.win, "_psa", None)
        if a:
            self.win.panels.adjustSize()
            a.updateGeometry()
            a.setFixedHeight(a.sizeHint().height())

    def update(self) -> None:
        QTimer.singleShot(0, self.relayout)
        self.canvas.prepareGeometryChange()
        self.canvas.update()
        self._ov_info()

    # ---------------------------------------------------------------- geometri
    def tray(self) -> dict | None:
        return self.cal_t or (self.det or {}).get("tray")

    def geo(self) -> dict | None:
        t, v = self.tray(), self.viewer
        if not t or not v.w:
            return None
        return {"X0": t["x0"] * v.w, "Y0": t["y0"] * v.h, "BW": (t["x1"] - t["x0"]) * v.w, "RH": (t["y1"] - t["y0"]) * v.h / t["rows"], "rows": int(t["rows"])}

    def has_iv(self) -> bool:
        r = self.r
        return bool(r and r.get("from_m") is not None and r.get("to_m") is not None and r["to_m"] > r["from_m"])

    def in_tray(self, pt) -> bool:
        g = self.geo()
        return bool(g) and g["X0"] <= pt.x() <= g["X0"] + g["BW"] and g["Y0"] <= pt.y() <= g["Y0"] + g["RH"] * g["rows"]

    def _rowu(self, pt):
        g = self.geo()
        if not g:
            return None
        row = max(0, min(g["rows"] - 1, int((pt.y() - g["Y0"]) // g["RH"])))
        u = max(0.0, min(1.0, (pt.x() - g["X0"]) / g["BW"]))
        return g, row, u

    def pos_frac(self, pt, snap_m: float = 0.05):
        x = self._rowu(pt)
        if not x or not self.has_iv():
            return None
        g, row, u = x
        L = self.r["to_m"] - self.r["from_m"]
        f = (row + u) / g["rows"]
        f = round(f * L / snap_m) * snap_m / L
        return max(0.0, min(1.0, f))

    def depth(self, f: float) -> float:
        return round((self.r["from_m"] + f * (self.r["to_m"] - self.r["from_m"])) * 100) / 100

    def mark_pos(self, pt):
        x = self._rowu(pt)
        if not x or not self.has_iv():
            return None
        g, row, u = x
        s = row + u
        d = self.r["from_m"] + s / g["rows"] * (self.r["to_m"] - self.r["from_m"])
        return {"row": row, "u": u, "s": s, "d": round(d * 20) / 20}

    # ---------------------------------------------------------------- gambar overlay
    def paint_overlay(self, p: QPainter) -> None:
        r, g = self.r, self.geo()
        if not g or not self.has_iv() or not self.det:
            return
        v = self.viewer
        X0, Y0, BW, RH, rows = g["X0"], g["Y0"], g["BW"], g["RH"], g["rows"]
        lay = [l for l in (self.ov.layers or []) if l["on"]]
        n = len(lay)
        lh = min(RH * 0.2, RH * 0.72 / max(1, n))
        fs = max(9.0, min(lh * 0.62, v.w / 50))
        p.setBrush(Qt.NoBrush)
        p.setPen(pen("#ffffff", 1, True, .5))
        for i in range(rows):
            p.drawRect(QRectF(X0, Y0 + i * RH, BW, RH))
        for li, l in enumerate(lay):
            m, items = self.ov.items(l, r, self.det, self.segs)
            for it in items:
                col = self.ov.color(l["k"], m, it["v"])
                if not col:
                    continue
                for si, (row, u0, u1) in enumerate(frac_segs(it["f0"], it["f1"], rows)):
                    x0, w = X0 + u0 * BW, max(v.px(1), (u1 - u0) * BW)
                    y = Y0 + row * RH + li * lh
                    c = QColor(col)
                    c.setAlphaF(0.85 if m["kind"] == "s" else 0.9)
                    p.setBrush(c)
                    p.setPen(pen("#ffffff", 1.4, True) if it.get("ai") else pen("#141a26", 0.9))
                    p.drawRect(QRectF(x0, y, w, lh * 0.92))
                    if self.ov.lbl and w > fs * 1.6 and (si == 0 or it.get("box")):
                        t = short_v(it["v"])[: max(2, int(w / (fs * 0.62)))]
                        halo_text(p, x0 + w / 2, y + lh * 0.46, t, fs, "#141a26", "#ffffff")
        a, b = r["from_m"], r["to_m"]
        ds = max(9.0, min(RH * 0.16, v.w / 45)) * 0.8
        for i in range(rows):
            d0, d1 = a + (b - a) * i / rows, a + (b - a) * (i + 1) / rows
            y = Y0 + i * RH + RH * 0.97 - ds * 0.6
            halo_text(p, X0 + v.px(4), y, f"{d0:.2f}", ds, "#ffffff", "#141a26", "l")
            halo_text(p, X0 + BW - v.px(4), y, f"{d1:.2f}", ds, "#ffffff", "#141a26", "r")

    def _ov_info(self) -> None:
        if not self.ov.on:
            return
        if self.r and not self.has_iv():
            self.ovInfo.setText("Isi Hole / From / To foto agar overlay bisa ditempatkan.")
            return
        lay = [l for l in (self.ov.layers or []) if l["on"]]
        if not lay:
            self.ovInfo.setText("Tambahkan lapisan.")
            return
        if self.r:
            self.ovInfo.setText(" · ".join(f"{self.ov.meta(l['k'])['short']} {len(self.ov.items(l, self.r, self.det, self.segs)[1])}" for l in lay))

    def paint_seg_edit(self, p: QPainter) -> None:
        g = self.geo()
        if not g:
            return
        X0, Y0, BW, RH, rows = g["X0"], g["Y0"], g["BW"], g["RH"], g["rows"]
        lst = list(self.segs)
        d = self.seg_tool.drag
        if d and d["type"] == "new":
            lst.append({"id": "n", "f0": min(d["a"], d["b"]), "f1": max(d["a"], d["b"])})
        for s in lst:
            sel = self.sg_sel == s["id"] or s["id"] == "n" or (self.sg_cur and self.sg_cur.get("id") is None and s["id"] == "n")
            for row, u0, u1 in frac_segs(s["f0"], s["f1"], rows):
                c = QColor(SEL if sel else "#ffffff")
                c.setAlphaF(0.22 if sel else 0.04)
                p.setBrush(c)
                p.setPen(pen(SEL if sel else "#ffffff", 2.2 if sel else 1, alpha=1 if sel else .6))
                p.drawRect(QRectF(X0 + u0 * BW, Y0 + row * RH, (u1 - u0) * BW, RH))
        if self.sg_cur and self.sg_cur.get("id") is None and not d:
            s = self.sg_cur
            for row, u0, u1 in frac_segs(s["f0"], s["f1"], rows):
                c = QColor(SEL)
                c.setAlphaF(0.22)
                p.setBrush(c)
                p.setPen(pen(SEL, 2.2, True))
                p.drawRect(QRectF(X0 + u0 * BW, Y0 + row * RH, (u1 - u0) * BW, RH))
        seen = set()
        hw, hh = self.viewer.px(3), self.viewer.px(7)
        for s in self.segs:
            for side, f in (("start", s["f0"]), ("end", s["f1"])):
                key = f"{f:.4f}"
                if key in seen and side == "end":
                    continue
                seen.add(key)
                ff = f - 1e-6 if side == "end" and f > 0 and abs(f * rows - round(f * rows)) < 1e-6 else f
                sp = ff * rows
                row = min(rows - 1, int(sp + 1e-9))
                x = X0 + (sp - row) * BW
                y0 = Y0 + row * RH
                p.setPen(pen(YEL, 2.4))
                p.drawLine(QPointF(x, y0), QPointF(x, y0 + RH))
                p.setBrush(QColor(YEL))
                p.setPen(pen("#141a26", 1))
                p.drawRoundedRect(QRectF(x - hw, y0 + RH / 2 - hh, hw * 2, hh * 2), hw / 2, hw / 2)

    def paint_marks(self, p: QPainter) -> None:
        g, r = self.geo(), self.r
        if not g or not self.has_iv():
            return
        X0, Y0, BW, RH, rows = g["X0"], g["Y0"], g["BW"], g["RH"], g["rows"]
        a, b = r["from_m"], r["to_m"]
        fs = max(10.0, min(RH * 0.2, self.viewer.w / 45))

        def band(m, sel, tmp):
            c = mk_color(m["kind"])
            for i, (row, u0, u1) in enumerate(depth_segs(a, b, m["from_m"], m["to_m"], rows)):
                x0, w = X0 + u0 * BW, max(self.viewer.px(2), (u1 - u0) * BW)
                y, hh = Y0 + row * RH + RH * 0.22, RH * 0.56
                fill = QColor(c)
                fill.setAlphaF(0.22)
                p.setBrush(fill)
                p.setPen(Qt.NoPen)
                rect = QRectF(x0, y, w, hh)
                p.drawRect(rect)
                hb = QBrush(QColor(c), Qt.BDiagPattern)
                p.save()
                p.setBrush(hb)
                p.setBrushOrigin(0, 0)
                p.drawRect(rect)
                p.restore()
                p.setBrush(Qt.NoBrush)
                p.setPen(pen(c, 3.5 if sel else 2, tmp))
                p.drawRect(rect)
                if i == 0:
                    t = ("HC" if m["kind"] == "halfcore" else "LOSS" if m["kind"] == "coreloss" else mk_label(m["kind"])) + \
                        f" {fmt(m['from_m'])}–{fmt(m['to_m'])}" + (f" {m['sample_no']}" if m.get("sample_no") else "")
                    halo_text(p, x0 + self.viewer.px(3), y + hh / 2, t, fs * 0.85, "#ffffff", c, "l")

        for m in self.marks:
            if not (self.mk_edit and self.mk_edit.get("id") == m["id"]):
                band(m, False, False)
        if self.mk_edit:
            e = dict(self.mk_edit)
            e["from_m"], e["to_m"] = self.mkF.value() or e["from_m"], self.mkT.value() or e["to_m"]
            band(e, True, not e.get("id"))
        if self.mk_drag:
            d = self.mk_drag
            q0, q1 = sorted((d["a"]["s"], d["b"]["s"]))
            band({"kind": self.mk_kind, "from_m": a + q0 / rows * (b - a), "to_m": a + q1 / rows * (b - a)}, True, True)

    def paint_cal(self, p: QPainter) -> None:
        t, W, H, v = self.cal_t, self.viewer.w, self.viewer.h, self.viewer
        x0, y0, x1, y1 = t["x0"] * W, t["y0"] * H, t["x1"] * W, t["y1"] * H
        c = QColor(SEL)
        c.setAlphaF(0.14)
        p.setBrush(c)
        p.setPen(pen(SEL, 3))
        p.drawRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        p.setPen(pen("#ffffff", 1.5, True))
        for i in range(1, t["rows"]):
            y = y0 + (y1 - y0) * i / t["rows"]
            p.drawLine(QPointF(x0, y), QPointF(x1, y))
        fs = v.px(18)
        for i in range(t["rows"]):
            halo_text(p, x0 + v.px(8), y0 + (y1 - y0) * (i + .5) / t["rows"], f"{i + 1} →", fs, "#ffffff", "#141a26", "l")
        hs = v.px(12)
        p.setBrush(QColor("#ffffff"))
        p.setPen(pen(SEL, 2.5))
        for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            p.drawRect(QRectF(x - hs / 2, y - hs / 2, hs, hs))

    # ---------------------------------------------------------------- panel overlay
    def toggle_ov(self, on: bool) -> None:
        self.ov.on = on
        SET.set("ov", on)
        if not on and self.sg_mode:
            self.seg_mode(False)
        self.pOv.setVisible(on and not self.cal_t)
        self.ov_panel()
        self.update()

    def ov_panel(self) -> None:
        ov = self.ov
        if ov.layers is None:
            return
        used = {l["k"] for l in ov.layers}
        self.ovAdd.blockSignals(True)
        self.ovAdd.clear()
        self.ovAdd.addItem("+ Lapisan…", "")
        for src in "agsc":
            ks = [k for k in ov.avail() if k[0] == src and k not in used]
            if ks:
                self.ovAdd.addItem(f"— {SRC_LBL[src]} —", "")
                self.ovAdd.model().item(self.ovAdd.count() - 1).setEnabled(False)
                for k in ks:
                    self.ovAdd.addItem("   " + ov.meta(k)["short"], k)
        self.ovAdd.blockSignals(False)
        self.ovPre.blockSignals(True)
        self.ovPre.clear()
        self.ovPre.addItem("Preset…", "")
        for k in ov.presets():
            self.ovPre.addItem(k, k)
        self.ovPre.blockSignals(False)
        while self.ovL.count():
            w = self.ovL.takeAt(0).widget()
            if w:
                w.deleteLater()
        if not ov.layers:
            l = QLabel("Belum ada lapisan. Pilih <b>+ Lapisan</b> atau <b>Preset</b>.")
            l.setObjectName("note")
            self.ovL.addWidget(l)
        for i, l in enumerate(ov.layers):
            self.ovL.addWidget(self._layer_row(i, l))

    def _layer_row(self, i: int, l: dict) -> QWidget:
        ov, m = self.ov, self.ov.meta(l["k"])
        w = QWidget()
        vv = QVBoxLayout(w)
        vv.setContentsMargins(0, 2, 0, 2)
        vv.setSpacing(2)
        top = QHBoxLayout()
        top.setSpacing(4)
        h = QHBoxLayout()
        h.setContentsMargins(22, 0, 0, 0)
        h.setSpacing(4)
        vv.addLayout(top)
        vv.addLayout(h)
        cb = QCheckBox(m["label"])
        cb.setChecked(l["on"])
        cb.setStyleSheet("font-weight:700" if l["on"] else f"color:{theme.C['mu']}")
        cb.toggled.connect(lambda on, l=l: (l.__setitem__("on", on), ov.save(), self.ov_panel(), self.update(), self.win.on_grade_cls()))
        cb.setToolTip(m["label"])
        cb.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        cb.setMinimumWidth(80)
        top.addWidget(cb, 1)
        if m["kind"] in ("grade", "n"):
            b = ov.breaks(l["k"], m)
            P = ov.palette(m)
            for j in range(len(b) + 1):
                t = f"<{fmt(b[0])}" if j == 0 else (f"≥{fmt(b[j - 1])}" if j == len(b) else f"{fmt(b[j - 1])}–{fmt(b[j])}")
                s = QLabel(t)
                s.setStyleSheet(f"background:{P[min(j, len(P) - 1)]};color:{'#fff' if (m['kind'] == 'grade' and j >= 3) else '#141a26'};padding:0 3px;border-radius:2px;font-size:7.6pt")
                h.addWidget(s)
            e = QLineEdit(", ".join(fmt(x) for x in b))
            e.setToolTip("batas kelas, dipisah koma")
            e.setFixedWidth(84)
            e.editingFinished.connect(lambda e=e, l=l: self._set_cls(l, e.text()))
            top.addWidget(e)
        else:
            vals: list[str] = []
            if self.r:
                for it in ov.items(l, self.r, self.det, self.segs)[1]:
                    if str(it["v"]) not in vals:
                        vals.append(str(it["v"]))
            if m["kind"] == "o" and re.search("weath|lapuk", m["col"], re.I) and not vals:
                vals = ["W1", "W2", "W3", "W4", "W5"]
            for val in vals[:14]:
                bt = QPushButton(short_v(val))
                col = ov.color(l["k"], m, val) or "#888"
                bt.setStyleSheet(f"QPushButton{{border:1px solid #141a26;border-left:12px solid {col};padding:0 5px;font-size:8pt;border-radius:2px}}")
                bt.setToolTip(f"ubah warna {val}")
                bt.clicked.connect(lambda _=False, l=l, val=val, col=col: self._pick_color(l, val, col))
                h.addWidget(bt)
            if not vals:
                n = QLabel("tidak ada nilai di foto ini")
                n.setObjectName("note")
                h.addWidget(n)
        h.addStretch(1)
        for t, tip, fn in (("↑", "naik", lambda i=i: self._move(i, -1)), ("↓", "turun", lambda i=i: self._move(i, 1)),
                           ("×", "hapus lapisan", lambda i=i: self._remove(i))):
            b = btn(t, tip, sm=True)
            b.setFixedWidth(26)
            b.clicked.connect(fn)
            h.addWidget(b)
        return w

    def _set_cls(self, l: dict, text: str) -> None:
        v = sorted(float(x) for x in re.split(r"[,;\s]+", text.strip()) if re.match(r"^-?\d+(\.\d+)?$", x))[:4]
        key = l["k"][2:] if l["k"][0] == "a" else l["k"]
        if v:
            self.ov.cls[key] = v
        else:
            self.ov.cls.pop(key, None)
        self.ov.save()
        self.ov_panel()
        self.update()
        if l["k"][0] == "a":
            self.win.on_grade_cls()
            self.render_boxes()

    def _pick_color(self, l: dict, val: str, cur: str) -> None:
        c = QColorDialog.getColor(QColor(cur), self.win, f"Warna {val}")
        if c.isValid():
            self.ov.colors.setdefault(l["k"], {})[val] = c.name()
            self.ov.save()
            self.ov_panel()
            self.update()

    def _move(self, i: int, d: int) -> None:
        L = self.ov.layers
        j = i + d
        if 0 <= j < len(L):
            L[i], L[j] = L[j], L[i]
            self.ov.save()
            self.ov_panel()
            self.update()

    def _remove(self, i: int) -> None:
        self.ov.layers.pop(i)
        self.ov.save()
        self.ov_panel()
        self.update()
        self.win.on_grade_cls()

    def _add(self, *_) -> None:
        k = self.ovAdd.currentData()
        if k:
            self.ov.layers.append({"k": k, "on": True})
            self.ov.save()
            self.ov_panel()
            self.update()

    def _preset(self, *_) -> None:
        name = self.ovPre.currentData()
        if not name:
            return
        av = set(self.ov.avail())
        self.ov.layers = [{"k": k, "on": True} for k in self.ov.presets()[name] if k and k in av]
        self.ov.save()
        self.ov_panel()
        self.update()

    # ---------------------------------------------------------------- segmen
    def seg_mode(self, on: bool) -> None:
        if on and (not self.has_iv() or not self.det):
            self.win.toast("Isi From dan To foto dulu, lalu tunggu data foto dimuat.", 4000)
            on = False
        if on and self.mk_mode:
            self.mark_mode(False)
        if on and not self.ov.on:
            self.bOv.setChecked(True)
        if on and self.viewer.rot:
            self.viewer.rot = 0
            self.viewer.root.setRotation(0)
            self.viewer.fit()
        self.sg_mode = on
        self.bSg.setText("Selesai edit segmen" if on else "Edit segmen")
        self.bSg.setProperty("pri", on)
        theme.repolish(self.bSg)
        self.sgHint.setVisible(on)
        self.viewer.set_tool(self.seg_tool if on else None)
        if not on:
            self.seg_form_close()
            self.sg_sel = None
        self.update()

    def seg_apply(self, j: dict) -> None:
        self.segs = j["segs"]
        if self.r and j.get("row"):
            self.r.update(j["row"])
            self.win.model.refresh_row(self.r["id"])
        self.render_boxes()
        self.ov_panel()
        self.update()

    def seg_form_close(self) -> None:
        self.sg_cur = None
        lay = self.sgForm.layout()
        if lay:
            while lay.count():
                it = lay.takeAt(0)
                w = it.widget()
                if w:
                    w.deleteLater()
                elif it.layout():
                    _clear(it.layout())
        self.sgForm.hide()

    def seg_form(self, s: dict) -> None:
        if not s:
            return
        self.seg_form_close()
        self.sg_cur = s
        lay = self.sgForm.layout() or QVBoxLayout(self.sgForm)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(4)
        ai_seg = s.get("src") == "ai" and not s.get("edited")
        head = QLabel(("Segmen " + ("<span style='background:%s;color:#fff;padding:0 4px'>AI</span>" % theme.C["ac"] if ai_seg else "<span style='border:1px solid;padding:0 4px'>diedit</span>"))
                      if s.get("id") else "<b>Segmen baru</b>")
        self.sgF, self.sgT = QDoubleSpinBox(), QDoubleSpinBox()
        for x, f in ((self.sgF, s["f0"]), (self.sgT, s["f1"])):
            x.setDecimals(2)
            x.setRange(-1e6, 1e6)
            x.setSingleStep(0.05)
            x.setValue(self.depth(f))
            x.setFixedWidth(84)
        lay.addLayout(_row(head, "From", self.sgF, "To", self.sgT))
        g = QGridLayout()
        g.setSpacing(4)
        self.sgEd: dict[str, QLineEdit] = {}
        for i, (k, t, lbl) in enumerate(SEGF):
            ai = s.get("id") and s.get("src") == "ai" and k not in (s.get("edited") or []) and s.get(k) is not None
            e = QLineEdit("" if s.get(k) is None else fmt(s[k]))
            if k in LISTS:
                c = QCompleter(LISTS[k], e)
                c.setCaseSensitivity(Qt.CaseInsensitive)
                c.setFilterMode(Qt.MatchContains)
                e.setCompleter(c)
            if ai:
                e.setStyleSheet(f"background:{theme.C['ai']}")
                e.setToolTip("Nilai AI (belum diedit)")
            e.returnPressed.connect(self.seg_save)
            self.sgEd[k] = e
            ll = QLabel(lbl)
            ll.setObjectName("note")
            g.addWidget(ll, i // 3, (i % 3) * 2)
            g.addWidget(e, i // 3, (i % 3) * 2 + 1)
        lay.addLayout(g)
        bs = btn("Simpan", pri=True, sm=True)
        bs.clicked.connect(self.seg_save)
        bts = [bs]
        if s.get("id"):
            cf = self.sg_click if self.sg_click is not None and s["f0"] < self.sg_click < s["f1"] else (s["f0"] + s["f1"]) / 2
            b1 = btn(f"Belah di {fmt(self.depth(cf))} m", "Belah di titik yang diklik", sm=True)
            b1.clicked.connect(lambda: self._seg_op("split", {"f": cf}, close=True))
            b2 = btn("Gabung dengan berikutnya", sm=True)
            b2.clicked.connect(lambda: self._seg_op("merge", {}, close=False))
            b3 = btn("Hapus", sm=True)
            b3.clicked.connect(lambda: ask(self.win, f"Hapus segmen {fmt(self.depth(s['f0']))}–{fmt(self.depth(s['f1']))} m?") and self._seg_op("delete", {}, close=True))
            bts += [b1, b2, b3]
        bc = btn("Tutup", sm=True)
        bc.clicked.connect(lambda: (self.seg_form_close(), setattr(self, "sg_sel", None), self.update()))
        self.sgErr = QLabel()
        self.sgErr.setObjectName("err")
        lay.addLayout(_row(*bts, bc, self.sgErr))
        self.sgForm.show()
        self.update()

    def _seg_op(self, op: str, extra: dict, close: bool) -> None:
        s = self.sg_cur
        try:
            self.seg_apply(api.call(f"/core/segs/{op}", {"folder": self.win.folder, "by": self.win.user(), "seg_id": s["id"], **extra}))
        except api.ApiError as e:
            self.sgErr.setText(str(e))
            return
        if close:
            self.seg_form_close()
            self.sg_sel = None
        else:
            self.seg_form(next((x for x in self.segs if x["id"] == s["id"]), None))
        self.update()

    def seg_save(self) -> None:
        s, r = self.sg_cur, self.r
        if not s or not r:
            return
        attrs = {}
        for k, e in self.sgEd.items():
            old = "" if s.get(k) is None else fmt(s[k])
            if (e.text() != "") if not s.get("id") else (e.text() != old):
                attrs[k] = e.text()
        seg: dict[str, Any] = {"attrs": attrs}
        F, T = self.sgF.value(), self.sgT.value()
        if not s.get("id") or abs(F - self.depth(s["f0"])) > 0.004 or abs(T - self.depth(s["f1"])) > 0.004:
            seg["from_m"], seg["to_m"] = F, T
        if s.get("id") and not attrs and "from_m" not in seg:
            self.seg_form_close()
            return
        try:
            j = api.call("/core/segs/save", {"folder": self.win.folder, "by": self.win.user(), "photo_id": r["id"], "seg_id": s.get("id"), "seg": seg})
        except api.ApiError as e:
            self.sgErr.setText(str(e))
            return
        self.seg_apply(j)
        self.sg_sel = j.get("id")
        self.seg_form(next((x for x in self.segs if x["id"] == j.get("id")), None))
        self.win.toast("Segmen disimpan")

    # ---------------------------------------------------------------- tanda
    def mark_open(self, on: bool) -> None:
        self.mk_open = on
        self.pMk.setVisible(on)
        if not on:
            self.mark_mode(False)
            self.mark_form_close()
        self._mk_kinds()
        self._mk_hint()
        self.update()

    def mark_mode(self, on: bool) -> None:
        if on and not self.has_iv():
            self.win.toast("Isi From dan To foto ini dulu: kedalaman tanda dihitung dari interval box.", 4000)
            on = False
        if on and not self.det:
            self.win.toast("Tunggu data foto dimuat…")
            on = False
        if on and self.sg_mode:
            self.seg_mode(False)
        self.mk_mode = on
        self.bMkMode.setText("Selesai menandai" if on else "Mulai menandai")
        self.bMkMode.setProperty("pri", on)
        theme.repolish(self.bMkMode)
        if on and self.viewer.rot:
            self.viewer.rot = 0
            self.viewer.root.setRotation(0)
            self.viewer.fit()
        if on:
            self.mkShowCb.setChecked(True)
        self.viewer.set_tool(self.mark_tool if on else None)
        self._mk_hint()
        self.update()

    def _mk_hint(self) -> None:
        self.mkHint.setText("Tarik di sepanjang baris core dari awal sampai akhir interval (boleh menyambung ke baris berikutnya). Klik tanda yang ada untuk mengedit. "
                            "Esc = berhenti. Kedalaman dibulatkan 0,05 m dan bisa diketik ulang." if self.mk_mode
                            else "Klik <b>Mulai menandai</b>. Half core wajib nomor sampel; core loss otomatis menghitung Core Recovery foto.")

    def _mk_kinds(self) -> None:
        ks = list(dict.fromkeys(["halfcore", "coreloss"] + list(SET.get("mkKinds", [])) + [m["kind"] for m in self.marks]))
        self.mkKind.blockSignals(True)
        self.mkKind.clear()
        for k in ks:
            self.mkKind.addItem(mk_label(k), k)
        self.mkKind.addItem("+ Jenis lain…", "__new")
        self.mkKind.setCurrentIndex(max(0, self.mkKind.findData(self.mk_kind if self.mk_kind in ks else "halfcore")))
        self.mkKind.blockSignals(False)

    def _mk_kind(self, *_) -> None:
        k = self.mkKind.currentData()
        if k == "__new":
            t, ok = QInputDialog.getText(self.win, "Jenis tanda", "Nama jenis tanda baru (mis. Rusak pengangkutan, Duplikat, Sampel geotek):")
            t = t.strip() if ok else ""
            if t:
                SET.set("mkKinds", list(dict.fromkeys(list(SET.get("mkKinds", [])) + [t])))
                k = t
            else:
                k = self.mk_kind
        self.mk_kind = k
        SET.set("mkKind", k)
        self._mk_kinds()
        if self.mk_edit and not self.mk_edit.get("id"):
            self.mk_edit["kind"] = k
            self.mark_form(self.mk_edit)

    def samples(self, f: float, t: float) -> tuple[str, list[str]]:
        rows = (self.det or {}).get("assay") or []
        keys = list(dict.fromkeys(k for x in rows for k in x))
        key = next((k for k in keys if re.match(r"^(sample|sampel|samp)([ _.-]?(no|id|number|nomor))?$", k, re.I)), None)
        if not key:
            return "", []
        best, ov = "", 0.0
        for x in rows:
            o = min(t, x["t"]) - max(f, x["f"])
            if x.get(key) is not None and o > ov:
                ov, best = o, str(x[key])
        return best, list(dict.fromkeys(str(x[key]) for x in rows if x.get(key) is not None))

    def mark_form(self, m: dict) -> None:
        if not m:
            return
        if not self.mk_open:
            self.bMk.setChecked(True)
        self.mk_edit = dict(m)
        half = m["kind"] == "halfcore"
        best, allv = self.samples(m["from_m"], m["to_m"])
        self.mkFT.setText(f"<span style='background:{mk_color(m['kind'])};color:#fff;padding:1px 6px;font-weight:700'>{_esc(mk_label(m['kind']))}</span>")
        for x, v in ((self.mkF, m["from_m"]), (self.mkT, m["to_m"])):
            x.blockSignals(True)
            x.setValue(float(v))
            x.blockSignals(False)
        self.mkN.setText(m.get("note") or "")
        self.mkSL.setVisible(half)
        self.mkS.setVisible(half)
        self.mkS.setText(m.get("sample_no") or (best if half else ""))
        c = QCompleter(allv, self.mkS)
        c.setCaseSensitivity(Qt.CaseInsensitive)
        self.mkS.setCompleter(c)
        self.bMkDel.setVisible(bool(m.get("id")))
        self.mkErr.setText("")
        self.mkForm.show()
        self.update()
        QTimer.singleShot(0, lambda: (self.mkS if half and not self.mkS.text() else self.mkN).setFocus())

    def _mk_range(self, *_) -> None:
        if self.mk_edit:
            best, _ = self.samples(self.mkF.value(), self.mkT.value())
            if self.mk_edit["kind"] == "halfcore" and not self.mk_edit.get("id") and best:
                self.mkS.setText(best)
            self.update()

    def mark_form_close(self) -> None:
        self.mk_edit = None
        self.mkForm.hide()
        self.mkErr.setText("")

    def _mk_after(self, j: dict) -> None:
        self.marks = j["marks"]
        if self.r and j.get("row"):
            self.r.update(j["row"])
            self.win.model.refresh_row(self.r["id"])
            self.win.card.show_row(self.r)
        self.render_boxes()
        self.update()

    def mark_save(self) -> None:
        r, m = self.r, self.mk_edit
        if not r or not m:
            return
        body = {"folder": self.win.folder, "by": self.win.user(), "photo_id": r["id"], "mark_id": m.get("id"),
                "mark": {"kind": m["kind"], "from_m": self.mkF.value(), "to_m": self.mkT.value(), "sample_no": self.mkS.text().strip() if m["kind"] == "halfcore" else "",
                         "note": self.mkN.text().strip(), "row0": m.get("row0"), "x0": m.get("x0"), "row1": m.get("row1"), "x1": m.get("x1")}}
        try:
            j = api.call("/core/marks/save", body)
        except api.ApiError as e:
            self.mkErr.setText(str(e))
            return
        self.mark_form_close()
        self._mk_after(j)
        self.win.toast(mk_label(m["kind"]) + " disimpan" + (f" · Core Recovery {fmt(r.get('recovery_pct'))}%" if r.get("rec_src") == "tanda" else ""))

    def mark_delete(self, mid: int) -> None:
        m = next((x for x in self.marks if x["id"] == mid), None)
        if not m or not ask(self.win, f"Hapus tanda {mk_label(m['kind'])} {fmt(m['from_m'])}–{fmt(m['to_m'])} m?"):
            return
        try:
            j = api.call("/core/marks/delete", {"folder": self.win.folder, "by": self.win.user(), "mark_id": mid})
        except api.ApiError as e:
            say(self.win, str(e), warn=True)
            return
        self.mark_form_close()
        self._mk_after(j)
        self.win.toast("Tanda dihapus")

    def mark_csv(self) -> None:
        if not self.win.folder:
            return
        name = f"Core-Ex_Interval_Tanda_{_dt.date.today().isoformat()}.csv"
        p, _ = QFileDialog.getSaveFileName(self.win, "Simpan tanda interval (CSV)", str(Path(SET.get("lastSaveDir", str(Path.home()))) / name), "CSV (*.csv)")
        if not p:
            return
        try:
            Path(p).write_bytes(api.call("/core/marks/csv", {"folder": self.win.folder}))
        except (api.ApiError, OSError) as e:
            say(self.win, "Gagal export CSV:\n" + str(e), warn=True)
            return
        SET.set("lastSaveDir", str(Path(p).parent))
        self.win.toast("Disimpan: " + p)

    # ---------------------------------------------------------------- kalibrasi
    def cal_start(self) -> None:
        if not self.r or not self.viewer.w:
            return
        if not self.det:
            self.win.toast("Tunggu data foto dimuat…")
            return
        if self.sg_mode:
            self.seg_mode(False)
        if self.mk_mode:
            self.mark_mode(False)
        self.cal_t = dict(self.det["tray"])
        self.viewer.rot = 0
        self.viewer.root.setRotation(0)
        self.viewer.fit()
        self.calRows.blockSignals(True)
        self.calRows.setValue(int(self.cal_t["rows"]))
        self.calRows.blockSignals(False)
        self.pCal.show()
        self.pOv.hide()
        self.viewer.set_tool(self.cal_tool)
        self.update()

    def cal_end(self) -> None:
        self.cal_t = None
        self.pCal.hide()
        self.pOv.setVisible(self.ov.on)
        self.viewer.set_tool(None)
        self.update()

    def cal_save(self, scope: str) -> None:
        r = self.r
        if not r or not self.cal_t:
            return
        try:
            api.call("/core/dh/tray", {"folder": self.win.folder, "id": r["id"], "tray": self.cal_t, "scope": scope})
        except api.ApiError as e:
            say(self.win, str(e), warn=True)
            return
        self.win.toast({"photo": "Area core disimpan untuk foto ini", "hole": "Area core disimpan untuk semua foto " + (r.get("hole_id") or ""),
                        "default": "Area core bawaan proyek disimpan (foto yang belum diatur sendiri)"}[scope])
        self.cal_end()
        self.load(r)

    # ---------------------------------------------------------------- kotak di kartu
    def render_boxes(self) -> None:
        r = self.r
        if not r:
            return
        mu, C = theme.C["mu"], theme.C
        h4 = lambda t, em, extra="": f"<div style='font-weight:800;font-size:11pt;color:{C['hd']};border-bottom:2px solid {C['nv']}'>{t} <span style='font-weight:400;font-size:7.6pt;letter-spacing:2px;color:{mu}'>{em.upper()}</span>{extra}</div>"  # noqa: E731
        tbl = f"<table cellspacing='0' cellpadding='3' style='font-size:8.4pt;border-collapse:collapse' width='100%'>"
        th = lambda cs: "<tr>" + "".join(f"<th align='left' style='background:{C['pn2']}'>{_esc(c)}</th>" for c in cs) + "</tr>"  # noqa: E731
        mono = f"font-family:\"{theme.MONO}\""
        # segmen
        if not self.segs:
            self.boxSeg.setText(h4("Interpretasi", "per baris") + f"<div style='color:{mu}'>Belum ada segmen. Jalankan AI (menilai tiap baris core mengikuti batas geologi) "
                                "atau tambahkan sendiri: <a href='sgo:'>Edit segmen</a> → tarik di foto.</div>")
        else:
            ai = sum(1 for s in self.segs if s["src"] == "ai" and not s["edited"])
            rows = ""
            for s in self.segs:
                wc = self.ov.color("s:weathering", self.ov.meta("s:weathering"), s.get("weathering")) if s.get("weathering") else None
                tag = (f"<span style='background:{C['ac']};color:#fff'>&nbsp;AI&nbsp;</span>" if s["src"] == "ai" and not s["edited"] else "<span style='border:1px solid'>&nbsp;diedit&nbsp;</span>")
                rows += (f"<tr><td style='{mono}'><a href='sgr:{s['id']}'>{fmt(s.get('from_m'))}</a></td><td style='{mono}'>{fmt(s.get('to_m'))}</td><td>{_esc(s.get('lithology') or '')}</td>"
                         f"<td>{('<span style=\"color:' + wc + '\">&#9632;</span> ' + _esc(short_v(s['weathering']))) if wc else ''}</td>"
                         f"<td align='right' style='{mono}'>{fmt(s.get('rqd_pct'))}</td><td align='right' style='{mono}'>{fmt(s.get('recovery_pct'))}</td>"
                         f"<td align='right' style='{mono}'>{fmt(s.get('ff_per_m'))}</td><td>{tag}</td></tr>")
            self.boxSeg.setText(h4("Interpretasi", f"per baris · {len(self.segs)} segmen", " &nbsp; <a href='sgo:'>Edit di foto</a>") + tbl
                                + th(["From", "To", "Litologi", "Pelapukan", "RQD", "Rec", "FF/m", ""]) + rows + "</table>"
                                + f"<div style='color:{mu}'>{ai} segmen masih nilai AI (garis putus-putus di overlay). Segmen yang diedit tidak ditimpa saat AI dijalankan ulang. Klik From untuk mengedit.</div>")
        # tanda
        ms = self.marks
        h = h4("Tanda", "interval" + (f" · {len(ms)}" if ms else ""), " &nbsp; <a href='mgo:'>Tandai di foto</a>")
        if not ms:
            h += f"<div style='color:{mu}'>Belum ada tanda. Klik <b>Tandai di foto</b>, pilih jenis (half core / core loss), lalu tarik di sepanjang baris core.</div>"
        else:
            h += tbl
            for m in ms:
                h += (f"<tr><td><span style='background:{mk_color(m['kind'])};color:#fff'>&nbsp;{_esc(m['label'])}&nbsp;</span></td>"
                      f"<td style='{mono}'><b>{fmt(m['from_m'])}–{fmt(m['to_m'])} m</b> ({fmt(m['len_m'])} m)</td>"
                      f"<td>{('sampel <b>' + _esc(m['sample_no']) + '</b> ') if m.get('sample_no') else ''}{_esc(m.get('note') or '')} <span style='color:{mu}'>· {_esc(m.get('edited_by') or m.get('by') or '')}</span></td>"
                      f"<td><a href='mke:{m['id']}'>Edit</a> · <a href='mkd:{m['id']}'>Hapus</a></td></tr>")
            h += "</table>"
            if self.has_iv():
                loss = round(sum(m["len_m"] for m in ms if m["kind"] == "coreloss"), 2)
                h += (f"<div style='color:{mu}'>Core loss total <b>{fmt(loss)} m</b> dari interval {fmt(round(r['to_m'] - r['from_m'], 3))} m → Core Recovery "
                      f"<b>{fmt(r.get('recovery_pct'))}%</b>{' (dihitung dari tanda)' if r.get('rec_src') == 'tanda' else ' (diisi manual, mengalahkan tanda)'}.</div>")
        self.boxMk.setText(h)
        # data lab
        dh, d = self.win.dh or {}, self.det
        if not (dh.get("assay") or dh.get("geology") or dh.get("collar")):
            self.boxLab.setText(h4("Data", "lab") + f"<div style='color:{mu}'>Belum ada data bor. Klik <b>Data bor</b> untuk import Collar, Survey, Assay, Geologi (CSV / Excel).</div>")
            return
        if not d:
            self.boxLab.setText(h4("Data", "lab") + f"<div style='color:{mu}'>Memuat…</div>")
            return
        if not r.get("hole_id") or not self.has_iv():
            self.boxLab.setText(h4("Data", "lab") + f"<div style='color:{mu}'>Isi Hole ID, From dan To foto ini agar data lab bisa dicocokkan.</div>")
            return
        xyz = lambda q: f"{q['x']:.1f}, {q['y']:.1f}, {q['z']:.1f}" if q else "–"  # noqa: E731
        h = h4("Data", f"lab · {_esc(r['hole_id'])} {fmt(r['from_m'])}–{fmt(r['to_m'])} m")
        if d.get("collar"):
            c = d["collar"]
            h += (f"<div style='{mono};font-size:8.4pt'><b>Collar X, Y, Z</b> {xyz(c)}{(' · EOH ' + fmt(c['depth']) + ' m') if c.get('depth') is not None else ''}<br>"
                  f"<b>From →</b> {xyz(d.get('xyz_from'))}<br><b>To →</b> {xyz(d.get('xyz_to'))}</div>")
        else:
            h += f"<div style='color:{mu}'>Hole tidak ada di Collar.</div>"
        on = [l for l in (self.ov.layers or []) if l["on"]]
        el = next((l["k"][2:] for l in on if l["k"][0] == "a"), next((n for n in self.ov.num_cols() if n.lower().startswith("au")), ""))
        geo = next((l["k"][2:] for l in on if l["k"][0] == "g"), next((n for n in self.ov.geo_cols() if re.search("lith|lito", n, re.I)), ""))

        def table(rows_, color_key, is_geo):
            if not rows_:
                return f"<div style='color:{mu}'>Tidak ada interval di rentang foto ini.</div>"
            keys = [k for k in dict.fromkeys(k for x in rows_ for k in x) if k not in ("f", "t")]
            out = tbl + th(["From", "To"] + keys)
            for x in rows_:
                out += f"<tr><td style='{mono}'>{fmt(x['f'])}</td><td style='{mono}'>{fmt(x['t'])}</td>"
                for k in keys:
                    v = x.get(k)
                    if v is None:
                        out += "<td></td>"
                    elif isinstance(v, (int, float)):
                        st = ""
                        if k == color_key:
                            i = idx_b(self.ov.grade_classes(k), v)
                            st = f"background:{BLUES[min(i, 4)]};color:{'#fff' if i >= 3 else '#141a26'};"
                        out += f"<td align='right' style='{mono}'><span style='{st}'>&nbsp;{fmt(v)}&nbsp;</span></td>"
                    else:
                        sw = f"<span style='color:{geo_color(v)}'>&#9632;</span> " if k == color_key and is_geo else ""
                        out += f"<td>{sw}{_esc(v)}</td>"
                out += "</tr>"
            return out + "</table>"

        if dh.get("assay"):
            g = " · ".join(f"{_esc(k)} <b>{fmt(v)}</b>" for k, v in (r.get("g") or {}).items())
            h += f"<div style='margin-top:4px'><b>Assay</b> ({len(d['assay'])} interval){(' · rata-rata tertimbang: ' + g) if g else ''}</div>" + table(d["assay"], el, False)
        if dh.get("geology"):
            h += f"<div style='margin-top:4px'><b>Geologi</b> ({len(d['geology'])} interval)</div>" + table(d["geology"], geo, True)
        self.boxLab.setText(h)

    # ---------------------------------------------------------------- keyboard
    def escape(self) -> bool:
        if self.cal_t:
            self.cal_end()
            return True
        if self.mk_edit:
            self.mark_form_close()
            self.update()
            return True
        if self.sg_cur:
            self.seg_form_close()
            self.sg_sel = None
            self.update()
            return True
        if self.mk_mode:
            self.mark_mode(False)
            return True
        if self.sg_mode:
            self.seg_mode(False)
            return True
        return False


def _clear(lay) -> None:
    while lay.count():
        it = lay.takeAt(0)
        if it.widget():
            it.widget().deleteLater()
        elif it.layout():
            _clear(it.layout())


__all__ = ["Interp", "Ov", "depth_segs", "QPainterPath", "QBrush"]
