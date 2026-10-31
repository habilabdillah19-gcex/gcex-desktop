"""Gambar fitur singkapan + infografis (judul, label zona, kotak kadar, kotak komposit, legenda, bar skala, deskripsi).

Satu fungsi paint_scene() dipakai untuk pratinjau di layar DAN untuk ekspor PNG / PDF resolusi penuh, jadi yang
terlihat = yang diekspor. Semua ukuran relatif terhadap sisi terpanjang gambar (unit U = sisi terpanjang / 1000).
Koordinat fitur ternormalisasi 0..1 (u kiri->kanan, v atas->bawah)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QImage, QImageReader, QPageSize, QPainter, QPainterPath, QPdfWriter,
                           QPen, QPolygonF)

from . import theme

TEMPLATES = {
    "trench": "Trenching / channel (dengan kadar)",
    "wall": "Mapping dinding (tanpa kadar)",
    "overlay": "Overlay saja (tanpa judul)",
}
BAND = {"trench": ("#f2c230", "#141a26"), "wall": ("#232f45", "#ffffff")}
GRADE_KEYS = (("au_ppm", "Au", "ppm"), ("ag_ppm", "Ag", "ppm"), ("sxs_pct", "SxS", "%"))
NO_LEGEND = {"skala", "label"}


def fmtv(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".") if abs(v) < 100 else f"{v:.1f}".rstrip("0").rstrip(".")
    return str(v)


def grade_lines(a: dict) -> list[str]:
    out = [f"{lbl}: {fmtv(a[k])} {unit}".replace(" %", "%") for k, lbl, unit in GRADE_KEYS if a.get(k) is not None]
    if a.get("teks"):
        out += [x for x in str(a["teks"]).splitlines() if x.strip()]
    return out


# ---------------------------------------------------------------- kadar multi-unsur & interval sampel
# warna kelas kadar menurut jumlah kelas (rendah -> tinggi); kuning dihindari agar tidak tertukar dengan garis channel
CLASS_SETS = {1: ["#2f9e44"], 2: ["#2f9e44", "#e03131"], 3: ["#2f9e44", "#f76707", "#e03131"],
              4: ["#1971c2", "#2f9e44", "#f76707", "#e03131"], 5: ["#1971c2", "#2f9e44", "#f76707", "#e03131", "#9c36b5"]}
LEGACY = {"au_ppm": "Au", "ag_ppm": "Ag", "sxs_pct": "SxS"}
DEFAULT_ELEMENTS = [{"key": "Au", "unit": "ppm", "dec": 2, "show": True, "classes": [0.2, 0.5, 1.0]},
                    {"key": "Ag", "unit": "ppm", "dec": 1, "show": True, "classes": []},
                    {"key": "SxS", "unit": "%", "dec": 2, "show": True, "classes": []}]


def samples_of(a: dict) -> list[dict]:
    sm = a.get("samples")
    if isinstance(sm, list) and sm:
        return sm
    g = {LEGACY[k]: a[k] for k in LEGACY if a.get(k) is not None}
    return [{"id": "", "from": None, "to": None, "grades": g}] if g else []


def intervals(a: dict) -> list[tuple[int, dict]]:
    return [(i, x) for i, x in enumerate(samples_of(a)) if x.get("from") is not None]


def gnum(v) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(",", ".")
    try:
        return float(t[1:]) / 2 if t.startswith("<") else float(t[1:] if t.startswith(">") else t)
    except ValueError:
        return None


def fmt_grade(v, e: dict | None) -> str:
    if isinstance(v, str):
        return v
    d = int((e or {}).get("dec", 2))
    t = f"{v:.{d}f}"
    return t


def unit_txt(v: str, unit: str) -> str:
    return f"{v}%" if unit == "%" else f"{v} {unit}"


def class_color(e: dict | None, v) -> str | None:
    cl = (e or {}).get("classes") or []
    x = gnum(v)
    if not cl or x is None:
        return None
    i = sum(1 for t in cl if x >= t)
    return CLASS_SETS[min(5, len(cl) + 1)][min(i, 4)]


def class_labels(e: dict) -> list[tuple[str, str]]:
    cl = e.get("classes") or []
    if not cl:
        return []
    cols = CLASS_SETS[min(5, len(cl) + 1)]
    f = lambda x: f"{x:g}"  # noqa: E731
    labs = [f"< {f(cl[0])}"] + [f"{f(a)} – {f(b)}" for a, b in zip(cl, cl[1:])] + [f"≥ {f(cl[-1])}"]
    return list(zip(labs, cols))


def sample_lines(x: dict, elements: list[dict], show_ids: bool = True) -> list[str]:
    out = []
    if show_ids and (x.get("id") or x.get("from") is not None):
        h = x.get("id") or ""
        if x.get("from") is not None:
            h = (h + "  " if h else "") + f"{x['from']:g}–{x['to']:g} m"
        out.append(h)
    g = x.get("grades") or {}
    for e in elements:
        if e.get("show") and g.get(e["key"]) is not None:
            out.append(f"{e['key']}: " + unit_txt(fmt_grade(g[e["key"]], e), e["unit"]))
    return out


def composite(samples: list[dict]) -> dict:
    iv = [x for x in samples if x.get("from") is not None]
    if not iv:
        return {}
    out = {"from": min(x["from"] for x in iv), "to": max(x["to"] for x in iv), "length": sum(x["to"] - x["from"] for x in iv), "grades": {}}
    for k in {k for x in iv for k in (x.get("grades") or {})}:
        num = den = 0.0
        for x in iv:
            v = gnum((x.get("grades") or {}).get(k))
            if v is not None:
                num, den = num + v * (x["to"] - x["from"]), den + (x["to"] - x["from"])
        if den > 0:
            out["grades"][k] = num / den
    return out


def chainer(P: list[QPointF], seg_m: list[float] | None, total_hint: float):
    """Fungsi jarak (m dari titik pertama) -> (titik, sudut segmen). seg_m = panjang tiap segmen dalam meter (georef /
    garis skala); tanpa itu garis dianggap sepanjang interval terjauh (total_hint)."""
    import math
    px = [((P[i + 1].x() - P[i].x()) ** 2 + (P[i + 1].y() - P[i].y()) ** 2) ** 0.5 for i in range(len(P) - 1)]
    if not seg_m or len(seg_m) != len(px) or sum(seg_m) <= 0:
        k = (total_hint or 1.0) / (sum(px) or 1.0)
        seg_m = [l * k for l in px]

    def at(c: float):
        acc = 0.0
        for i, l in enumerate(seg_m):
            if (acc + l >= c or i == len(seg_m) - 1) and l > 0:
                t = max(0.0, min(1.0, (c - acc) / l))
                a, b = P[i], P[i + 1]
                return QPointF(a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t), math.atan2(b.y() - a.y(), b.x() - a.x())
            acc += l
        return P[-1], 0.0

    def sub(c0: float, c1: float) -> list[QPointF]:
        out = [at(c0)[0]]
        acc = 0.0
        for i, l in enumerate(seg_m):
            acc += l
            if c0 < acc < c1 and i + 1 < len(P) - 1:
                out.append(P[i + 1])
        out.append(at(c1)[0])
        return out
    return at, sub, sum(seg_m)


def centroid(pts: list[QPointF]) -> QPointF:
    if len(pts) < 3:
        return QPointF(sum(p.x() for p in pts) / len(pts), sum(p.y() for p in pts) / len(pts))
    a = cx = cy = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        c = p.x() * q.y() - q.x() * p.y()
        a += c
        cx += (p.x() + q.x()) * c
        cy += (p.y() + q.y()) * c
    if abs(a) < 1e-9:
        return QPointF(sum(p.x() for p in pts) / len(pts), sum(p.y() for p in pts) / len(pts))
    return QPointF(cx / (3 * a), cy / (3 * a))


def midpoint(pts: list[QPointF]) -> QPointF:
    if len(pts) == 1:
        return pts[0]
    L = [((pts[i + 1].x() - pts[i].x()) ** 2 + (pts[i + 1].y() - pts[i].y()) ** 2) ** 0.5 for i in range(len(pts) - 1)]
    half, acc = sum(L) / 2, 0.0
    for i, l in enumerate(L):
        if acc + l >= half and l > 0:
            t = (half - acc) / l
            return QPointF(pts[i].x() + (pts[i + 1].x() - pts[i].x()) * t, pts[i].y() + (pts[i + 1].y() - pts[i].y()) * t)
        acc += l
    return pts[-1]


def anchor(f: dict, W: float, H: float) -> QPointF:
    P = [QPointF(u * W, v * H) for u, v in f["pts"]]
    return centroid(P) if f["shape"] == "poly" else midpoint(P)


def _font(px: float, bold: bool = True, mono: bool = False) -> QFont:
    f = QFont(theme.MONO if mono else theme.SANS)
    f.setPixelSize(max(1, int(px)))
    f.setBold(bold)
    return f


def _halo(p: QPainter, x: float, y: float, text: str, px: float, fill: str = "#ffffff", stroke: str = "#141a26", align: str = "c") -> QRectF:
    f = _font(px)
    fm = QFontMetricsF(f)
    tw = fm.horizontalAdvance(text)
    x0 = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)
    path = QPainterPath()
    path.addText(QPointF(x0, y + fm.ascent() / 2 - fm.descent() / 2), f, text)
    pe = QPen(QColor(stroke), px * 0.24)
    pe.setJoinStyle(Qt.RoundJoin)
    p.strokePath(path, pe)
    p.fillPath(path, QBrush(QColor(fill)))
    return QRectF(x0, y - fm.height() / 2, tw, fm.height())


def _box(p: QPainter, c: QPointF, lines: list[str], px: float, bg: str = "#f2c230", fg: str = "#141a26", align=Qt.AlignRight) -> QRectF:
    f = _font(px)
    fm = QFontMetricsF(f)
    tw = max(fm.horizontalAdvance(t) for t in lines)
    pad = px * 0.55
    w, h = tw + 2 * pad, fm.height() * len(lines) + 2 * pad * 0.8
    r = QRectF(c.x() - w / 2, c.y() - h / 2, w, h)
    p.setPen(QPen(QColor("#141a26"), max(1.0, px * 0.08), Qt.DashLine))
    p.setBrush(QColor(bg))
    p.drawRect(r)
    p.setFont(f)
    p.setPen(QColor(fg))
    for i, t in enumerate(lines):
        p.drawText(QRectF(r.left() + pad, r.top() + pad * 0.8 + i * fm.height(), tw, fm.height()), align | Qt.AlignVCenter, t)
    return r


def _line_label(p: QPainter, P: list[QPointF], text: str, px: float) -> None:
    """Nama garis sejajar segmen terpanjang, digeser sedikit ke samping agar tidak menimpa garis."""
    import math
    i = max(range(len(P) - 1), key=lambda k: (P[k + 1].x() - P[k].x()) ** 2 + (P[k + 1].y() - P[k].y()) ** 2)
    a, b = P[i], P[i + 1]
    ang = math.degrees(math.atan2(b.y() - a.y(), b.x() - a.x()))
    if ang > 90:
        ang -= 180
    elif ang < -90:
        ang += 180
    c = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
    p.save()
    p.translate(c)
    p.rotate(ang)
    _halo(p, 0, -px * 1.1, text, px)
    p.restore()


def nice_len(m: float) -> float:
    for v in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500):
        if v >= m:
            return v
    return 1000.0


def paint_scene(p: QPainter, W: float, H: float, feats: list[dict], kinds: dict, info: dict, *, desc: dict | None = None,
                m_per_unit: float | None = None, sel: int | None = None, sel_vertex: int | None = None, handle: float = 0,
                hide: set | None = None, draft: list | None = None, draft_kind: dict | None = None, boxes_out: list | None = None,
                show_info: bool = True, elements: list | None = None, chains: dict | None = None) -> None:
    """Gambar seluruh lapisan dalam koordinat gambar W x H.
    m_per_unit: meter per satuan gambar ini (untuk bar skala), sel / sel_vertex / handle / draft: hanya untuk editor.
    boxes_out: diisi [(fid, QRectF)] kotak kadar / label agar bisa digeser di editor."""
    U = max(W, H) / 1000.0
    tpl = info.get("template") or "trench"
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    hide = hide or set()
    elements = elements or DEFAULT_ELEMENTS
    emap = {e["key"]: e for e in elements}
    ckey = info.get("grade_color") or ""
    cel = emap.get(ckey)
    show_ids = info.get("show_ids", True)
    later: list = []  # kotak kadar digambar setelah semua garis agar tidak tertimpa
    # ---- fitur
    for f in feats:
        if f["id"] in hide:
            continue
        k = kinds.get(f["kind"]) or {"color": "#7a5aa6", "name": f["kind"]}
        col = QColor(k["color"])
        P = [QPointF(u * W, v * H) for u, v in f["pts"]]
        is_sel = f["id"] == sel
        if (f.get("attrs") or {}).get("_draft"):  # usulan otomatis: titik-titik, tanpa label / kotak kadar
            Q = QPolygonF(P + ([P[0]] if f["shape"] == "poly" else []))
            if f["shape"] == "poly":
                fill = QColor(col)
                fill.setAlphaF(0.16)
                p.setBrush(fill)
                p.setPen(Qt.NoPen)
                p.drawPolygon(QPolygonF(P))
                p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(255, 255, 255, 220), (4.2 if is_sel else 3.4) * U, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPolyline(Q)
            p.setPen(QPen(col, (2.6 if is_sel else 2.0) * U, Qt.DotLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPolyline(Q)
            if is_sel and f.get("name"):
                a = anchor(f, W, H) if f["shape"] == "poly" else P[len(P) // 2]
                _halo(p, a.x(), a.y(), "usulan: " + f["name"], 12 * U)
            continue
        if f["shape"] == "poly":
            fill = QColor(col)
            fill.setAlphaF(0.10 if info.get("fill", True) else 0.0)
            p.setBrush(fill)
            pe = QPen(QColor("#ffffff"), 2.2 * U, Qt.DashLine)
            p.setPen(pe)
            p.drawPolygon(QPolygonF(P))
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(col, (3.2 if is_sel else 2.0) * U, Qt.DashLine))
            p.drawPolygon(QPolygonF(P))
        elif f["shape"] == "line":
            wmul = 4.0 if f["kind"] in ("vein", "sesar") else (3.0 if f["kind"] == "channel" else 2.4)
            if f["kind"] == "skala":
                p.setPen(QPen(QColor("#141a26"), 4.6 * U, Qt.SolidLine, Qt.RoundCap))
                p.drawPolyline(QPolygonF(P))
            p.setPen(QPen(QColor("#141a26"), (wmul + 2.2) * U, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPolyline(QPolygonF(P))
            pe = QPen(col, (wmul + (1.6 if is_sel else 0)) * U, Qt.DashLine if f["kind"] in ("kekar", "kontak_alt") else Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pe)
            p.drawPolyline(QPolygonF(P))
        # nama / label
        if f["shape"] == "point":
            t = f.get("name") or ""
            if t:
                r = _halo(p, P[0].x(), P[0].y(), t, 15 * U)
                if boxes_out is not None:
                    boxes_out.append((f["id"], r, "pt"))
            else:
                p.setPen(QPen(QColor("#141a26"), 2 * U))
                p.setBrush(QColor("#ffffff"))
                p.drawEllipse(P[0], 5 * U, 5 * U)
        elif f.get("name") and info.get("show_names", True) and f["kind"] != "skala":
            if f["shape"] == "poly":
                a = anchor(f, W, H)
                _halo(p, a.x(), a.y(), f["name"], 15 * U)
            else:
                _line_label(p, P, f["name"], 12.5 * U)
        if f["kind"] == "skala" and f["attrs"].get("length_m"):
            a = anchor(f, W, H)
            _halo(p, a.x(), a.y() - 14 * U, f"{fmtv(f['attrs']['length_m'])} m", 12 * U)
        # kadar per interval di garis channel / trenching
        iv = intervals(f["attrs"]) if f["shape"] == "line" else []
        if show_info and tpl == "trench" and iv:
            import math
            at, sub, _tot = chainer(P, (chains or {}).get(f["id"]), max(x["to"] for _i, x in iv))
            if cel:  # warnai segmen interval menurut kelas kadar
                for _i, x in iv:
                    cc = class_color(cel, (x.get("grades") or {}).get(ckey))
                    if cc:
                        seg = QPolygonF(sub(x["from"], x["to"]))
                        p.setPen(QPen(QColor("#141a26"), 10.0 * U, Qt.SolidLine, Qt.FlatCap, Qt.RoundJoin))
                        p.drawPolyline(seg)
                        p.setPen(QPen(QColor(cc), 6.4 * U, Qt.SolidLine, Qt.FlatCap, Qt.RoundJoin))
                        p.drawPolyline(seg)
            for c in sorted({x["from"] for _i, x in iv} | {x["to"] for _i, x in iv}):
                q, ang = at(c)
                n = QPointF(-math.sin(ang), math.cos(ang))
                a, b = QPointF(q.x() - n.x() * 11 * U, q.y() - n.y() * 11 * U), QPointF(q.x() + n.x() * 11 * U, q.y() + n.y() * 11 * U)
                p.setPen(QPen(QColor("#141a26"), 4.6 * U, Qt.SolidLine, Qt.FlatCap))
                p.drawLine(a, b)
                p.setPen(QPen(QColor("#ffffff"), 2.2 * U, Qt.SolidLine, Qt.FlatCap))
                p.drawLine(a, b)
            for j, (i, x) in enumerate(iv):
                lines = sample_lines(x, elements, show_ids)
                if not lines:
                    continue
                q, ang = at((x["from"] + x["to"]) / 2)
                n = QPointF(-math.sin(ang), math.cos(ang))
                if n.y() > 0:
                    n = QPointF(-n.x(), -n.y())  # sisi atas garis lebih dulu
                if j % 2:
                    n = QPointF(-n.x(), -n.y())
                if x.get("bu") is not None and x.get("bv") is not None:
                    c = QPointF(x["bu"] * W, x["bv"] * H)
                else:
                    d = 0.15 * H
                    c = QPointF(min(W * 0.93, max(W * 0.07, q.x() + n.x() * d)), min(H * 0.88, max(H * 0.14, q.y() + n.y() * d)))
                cc = class_color(cel, (x.get("grades") or {}).get(ckey)) if cel else None

                def draw_box(q=q, c=c, lines=lines, cc=cc, fid=f["id"], key=f"s{i}"):
                    p.setPen(QPen(QColor("#141a26"), 3.6 * U, Qt.DashLine))
                    p.drawLine(q, c)
                    p.setPen(QPen(QColor("#f2c230"), 2.0 * U, Qt.DashLine))
                    p.drawLine(q, c)
                    r = _box(p, c, lines, 13 * U, align=Qt.AlignLeft)
                    if cc:
                        p.setPen(QPen(QColor(cc), 3.2 * U))
                        p.setBrush(Qt.NoBrush)
                        p.drawRect(r.adjusted(-1.6 * U, -1.6 * U, 1.6 * U, 1.6 * U))
                    if boxes_out is not None:
                        boxes_out.append((fid, r, key))
                later.append(draw_box)
        # kotak kadar satu sampel (template trenching)
        elif show_info and tpl == "trench" and f["shape"] != "point":
            sm = samples_of(f["attrs"])
            lines = (sample_lines(sm[0], elements, show_ids) if sm else []) + \
                [t for t in str(f["attrs"].get("teks") or "").splitlines() if t.strip()]
            if lines:
                a = anchor(f, W, H)
                bu, bv = f["attrs"].get("box_u"), f["attrs"].get("box_v")
                c = QPointF(bu * W, bv * H) if bu is not None and bv is not None else QPointF(a.x(), min(H * 0.86, a.y() + 0.16 * H))

                def draw_one(a=a, c=c, lines=lines, fid=f["id"]):
                    p.setPen(QPen(QColor("#f2c230"), 2.0 * U, Qt.DashLine))
                    p.drawLine(a, c)
                    r = _box(p, c, lines, 14 * U)
                    if boxes_out is not None:
                        boxes_out.append((fid, r, "box"))
                later.append(draw_one)
    for fn in later:
        fn()
    # ---- garis yang sedang digambar
    if draft:
        k = draft_kind or {"color": "#ffd43b", "shape": "line"}
        P = [QPointF(u * W, v * H) for u, v in draft]
        p.setPen(QPen(QColor("#141a26"), 4.4 * U, Qt.SolidLine, Qt.RoundCap))
        p.drawPolyline(QPolygonF(P + ([P[0]] if k.get("shape") == "poly" and len(P) > 2 else [])))
        p.setPen(QPen(QColor(k["color"]), 2.4 * U, Qt.DashLine, Qt.RoundCap))
        p.drawPolyline(QPolygonF(P + ([P[0]] if k.get("shape") == "poly" and len(P) > 2 else [])))
    # ---- titik edit fitur terpilih
    if sel is not None and handle:
        f = next((x for x in feats if x["id"] == sel), None)
        if f:
            for i, (u, v) in enumerate(f["pts"]):
                c = QPointF(u * W, v * H)
                p.setPen(QPen(QColor("#141a26"), handle * 0.35))
                p.setBrush(QColor("#ffd43b") if i == sel_vertex else QColor("#ffffff"))
                p.drawRect(QRectF(c.x() - handle, c.y() - handle, 2 * handle, 2 * handle))
    if not show_info or tpl == "overlay":
        return
    # ---- pita judul
    title = info.get("title") or ""
    if title:
        bg, fg = BAND.get(tpl, BAND["trench"])
        bh = 46 * U if not info.get("subtitle") else 64 * U
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(bg))
        p.drawRect(QRectF(0, 0, W, bh))
        p.setPen(QColor(fg))
        p.setFont(_font(24 * U))
        p.drawText(QRectF(0, 4 * U, W, 38 * U), Qt.AlignCenter, title)
        if info.get("subtitle"):
            p.setFont(_font(14 * U, bold=False))
            p.drawText(QRectF(0, 40 * U, W, 22 * U), Qt.AlignCenter, info["subtitle"])
    # ---- kotak komposit
    comp = [x for x in str(info.get("composite") or "").splitlines() if x.strip()]
    if tpl == "trench" and info.get("auto_comp", True):
        for f in feats:
            if f["shape"] != "line" or (f.get("attrs") or {}).get("_draft") or f["id"] in hide:
                continue
            cp = composite(samples_of(f["attrs"]))
            if not cp or len(intervals(f["attrs"])) < 2:
                continue
            g = [f"{e['key']} " + unit_txt(fmt_grade(cp["grades"][e["key"]], e), e["unit"]) for e in elements
                 if e.get("show") and e["key"] in cp["grades"]]
            nm = f.get("name") or (kinds.get(f["kind"]) or {}).get("name", "")
            comp.append(f"Komposit {nm} {cp['length']:g} m" + (": " + " · ".join(g) if g else ""))
    if tpl == "trench" and comp:
        cu, cv = info.get("comp_u", 0.5), info.get("comp_v", 0.92)
        r = _box(p, QPointF(cu * W, cv * H), comp, 16 * U, align=Qt.AlignHCenter)
        if boxes_out is not None:
            boxes_out.append((-1, r, "comp"))
    # ---- deskripsi ringkas (template dinding)
    bottom = H
    if tpl == "wall" and info.get("show_desc", True) and desc:
        parts = [(lbl, desc.get(k)) for k, lbl in (("lithology", "Litologi"), ("alteration", "Alterasi"), ("weathering", "Pelapukan"),
                                                   ("veins", "Vein"), ("structures", "Struktur"), ("gsi", "GSI"))]
        txt = "   ·   ".join(f"{l}: {v}" for l, v in parts if v)
        if txt:
            fh = 13 * U
            f = _font(fh, bold=False)
            fm = QFontMetricsF(f)
            rect = QRectF(14 * U, 0, W - 28 * U, 10000)
            br = fm.boundingRect(rect, Qt.TextWordWrap, txt)
            hh = min(br.height(), fm.height() * 4) + 14 * U
            bottom = H - hh
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(35, 47, 69, 225))
            p.drawRect(QRectF(0, bottom, W, hh))
            p.setPen(QColor("#ffffff"))
            p.setFont(f)
            p.drawText(QRectF(14 * U, bottom + 7 * U, W - 28 * U, hh - 14 * U), Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, txt)
    # ---- legenda
    if info.get("show_legend", True):
        used = []
        for f in feats:
            if f["kind"] not in NO_LEGEND and f["kind"] not in used and not (f.get("attrs") or {}).get("_draft"):
                used.append(f["kind"])
        names = [(kinds.get(k) or {"name": k, "color": "#7a5aa6", "shape": "line"}) for k in used]
        if tpl == "trench" and cel and cel.get("classes") and any(
                (x.get("grades") or {}).get(ckey) is not None for f in feats if not (f.get("attrs") or {}).get("_draft")
                for _i, x in (intervals(f["attrs"]) if f["shape"] == "line" else [])):
            names = names + [{"name": f"{ckey} ({cel['unit']})", "shape": "head"}] + \
                [{"name": lab, "color": col, "shape": "class"} for lab, col in class_labels(cel)]
        if names:
            fh = 12.5 * U
            fnt = _font(fh, bold=False)
            fm = QFontMetricsF(fnt)
            w = max(fm.horizontalAdvance(n["name"]) for n in names) + 44 * U
            h = fm.height() * 1.25 * len(names) + 14 * U
            pos = info.get("legend_pos") or "bl"
            top = 52 * U if (info.get("title") and tpl != "overlay") else 14 * U
            x0 = 14 * U if pos[1] == "l" else W - w - 14 * U
            y0 = bottom - h - (44 * U if pos == "br" and m_per_unit and info.get("show_scale", True) else 14 * U) if pos[0] == "b" else top + (16 * U if info.get("subtitle") else 0)
            p.setPen(QPen(QColor("#141a26"), 1.2 * U))
            p.setBrush(QColor(255, 255, 255, 225))
            p.drawRect(QRectF(x0, y0, w, h))
            p.setFont(fnt)
            for i, n in enumerate(names):
                y = y0 + 7 * U + i * fm.height() * 1.25 + fm.height() * 0.62
                if n.get("shape") == "head":
                    p.setFont(_font(fh))
                    p.setPen(QColor("#141a26"))
                    p.drawText(QRectF(x0 + 8 * U, y - fm.height() / 2, w, fm.height()), Qt.AlignVCenter | Qt.AlignLeft, n["name"])
                    p.setFont(fnt)
                    continue
                if n.get("shape") == "class":
                    p.setPen(QPen(QColor(n["color"]), 7 * U, Qt.SolidLine, Qt.FlatCap))
                    p.drawLine(QPointF(x0 + 8 * U, y), QPointF(x0 + 30 * U, y))
                elif n.get("shape") == "poly":
                    c = QColor(n["color"])
                    c.setAlphaF(0.45)
                    p.setBrush(c)
                    p.setPen(QPen(QColor(n["color"]), 1.6 * U, Qt.DashLine))
                    p.drawRect(QRectF(x0 + 8 * U, y - 6 * U, 22 * U, 12 * U))
                else:
                    p.setPen(QPen(QColor(n["color"]), 4 * U, Qt.DashLine if n.get("key") in ("kekar", "kontak_alt") else Qt.SolidLine))
                    p.drawLine(QPointF(x0 + 8 * U, y), QPointF(x0 + 30 * U, y))
                p.setPen(QColor("#141a26"))
                p.drawText(QRectF(x0 + 36 * U, y - fm.height() / 2, w, fm.height()), Qt.AlignVCenter | Qt.AlignLeft, n["name"])
    # ---- bar skala
    if info.get("show_scale", True) and m_per_unit:
        L = nice_len(0.18 * W * m_per_unit)
        bw = L / m_per_unit
        x1, y = W - 20 * U, bottom - 22 * U
        x0 = x1 - bw
        hh = 9 * U
        for i in range(4):
            p.setPen(QPen(QColor("#141a26"), 1.2 * U))
            p.setBrush(QColor("#141a26") if i % 2 else QColor("#ffffff"))
            p.drawRect(QRectF(x0 + bw * i / 4, y, bw / 4, hh))
        _halo(p, x1, y - 12 * U, f"{fmtv(float(L))} Meter", 17 * U, align="r")


# ---------------------------------------------------------------- ekspor
def load_image(path: str | Path, max_side: int = 0) -> QImage:
    r = QImageReader(str(path))
    r.setAutoTransform(True)  # orientasi EXIF, sama dengan backend (exif_transpose)
    if max_side:
        s = r.size()
        if s.isValid() and max(s.width(), s.height()) > max_side:
            k = max_side / max(s.width(), s.height())
            r.setScaledSize(s * k)
    im = r.read()
    if im.isNull():
        raise ValueError(f"Foto tidak bisa dibuka: {r.errorString()}")
    return im


def render(path: str | Path, feats: list[dict], kinds: dict, info: dict, desc: dict | None, m_per_px: float | None,
           orig_w: int, max_side: int = 6000, elements: list | None = None, chains: dict | None = None) -> QImage:
    im = load_image(path, max_side).convertToFormat(QImage.Format_RGB32)
    W, H = im.width(), im.height()
    p = QPainter(im)
    try:
        paint_scene(p, W, H, feats, kinds, info, desc=desc, m_per_unit=(m_per_px * orig_w / W) if m_per_px else None,
                    elements=elements, chains=chains)
    finally:
        p.end()
    return im


def _atomic(out: str | Path, write) -> None:
    """Tulis ke file sementara lalu ganti nama: file tujuan tidak pernah setengah jadi."""
    import os
    out = Path(out)
    tmp = out.with_name(out.stem + ".tmp_corex" + out.suffix)
    try:
        write(str(tmp))
        os.replace(tmp, out)
    finally:
        if tmp.exists():
            tmp.unlink()


def save_png(im: QImage, out: str | Path) -> None:
    def w(f):
        if not im.save(f, "PNG"):
            raise OSError(f"Gagal menyimpan {out}")
    _atomic(out, w)


def save_pdf(im: QImage, out: str | Path, title: str = "") -> None:
    _atomic(out, lambda f: _pdf(im, f, title))


def _pdf(im: QImage, out: str, title: str) -> None:
    w = QPdfWriter(str(out))
    w.setTitle(title or "Core-Ex Singkapan")
    w.setCreator("Core-Ex (GC-Ex)")
    wmm = 297.0 if im.width() >= im.height() else 210.0
    w.setPageSize(QPageSize(QSizeF(wmm, wmm * im.height() / im.width()), QPageSize.Millimeter))
    w.setPageMargins(__import__("PySide6.QtCore", fromlist=["QMarginsF"]).QMarginsF(0, 0, 0, 0))
    w.setResolution(300)
    p = QPainter(w)
    try:
        r = p.viewport()
        p.drawImage(QRectF(0, 0, r.width(), r.height()), im)
    finally:
        p.end()
