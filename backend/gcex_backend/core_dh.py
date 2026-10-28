"""GC-Ex Core Interpretation: integrasi data bor (Collar, Survey, Assay, Geologi) dengan header dinamis.

- File CSV / TXT / Excel (.xlsx/.xlsm). Header TIDAK dipatok: GC-Ex menebak kolom dari nama header
  (Hole_ID / BHID / DHID, From, To, Easting / X, …), lalu pengguna menentukan sendiri kolom mana yang dipakai
  untuk tiap peran dan kolom lain mana yang ikut (dengan nama tampilan & jenis angka / teks).
  Pemetaan disimpan di proyek dan dipakai lagi otomatis saat format file sama.
- Data disimpan di database proyek yang sama (gcex_core.db) sehingga ikut terbawa bersama folder foto.
- Nilai di bawah limit deteksi '<0.01' dibaca setengahnya (0.005); '>10' dibaca 10; '-' / kosong = tidak ada nilai;
  koma desimal ('0,25') dibaca.
- Foto dicocokkan ke data bor lewat Hole ID (tanpa membedakan huruf besar, spasi, '-', '_') dan rentang From–To.
"""
from __future__ import annotations

import base64
import csv
import io
import json
import math
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from . import core_io

router = APIRouter(prefix="/core/dh")

KINDS = ("collar", "survey", "assay", "geology")
KIND_LABEL = {"collar": "Collar", "survey": "Survey", "assay": "Assay", "geology": "Geologi"}
# peran kolom wajib / penting per jenis tabel
ROLES: dict[str, list[tuple[str, str, bool]]] = {
    "collar": [("hole", "Hole ID", True), ("x", "Easting / X", True), ("y", "Northing / Y", True), ("z", "Elevasi / Z / RL", True),
               ("depth", "Total depth", False), ("dip", "Dip collar", False), ("azi", "Azimuth collar", False)],
    "survey": [("hole", "Hole ID", True), ("at", "Kedalaman survey", True), ("dip", "Dip", True), ("azi", "Azimuth", True)],
    "assay": [("hole", "Hole ID", True), ("from", "From", True), ("to", "To", True)],
    "geology": [("hole", "Hole ID", True), ("from", "From", True), ("to", "To", True)],
}
ALIAS = {
    "hole": ["holeid", "hole", "bhid", "dhid", "holename", "drillhole", "lubang", "idlubang", "idhole", "hole_id"],
    "from": ["from", "depthfrom", "fromm", "mfrom", "dari", "depthfromm", "start"],
    "to": ["to", "depthto", "tom", "mto", "sampai", "ke", "depthtom", "end"],
    "x": ["easting", "east", "x", "xcollar", "e", "utmx", "xcoord"],
    "y": ["northing", "north", "y", "ycollar", "n", "utmy", "ycoord"],
    "z": ["rl", "elevation", "elev", "z", "zcollar", "elevasi", "height"],
    "depth": ["totaldepth", "eoh", "maxdepth", "holedepth", "td", "depth", "kedalaman", "length"],
    "at": ["depth", "at", "distance", "surveydepth", "md", "kedalaman"],
    "dip": ["dip", "inclination", "incl", "inc"],
    "azi": ["azimuth", "azi", "bearing", "az", "brg"],
}
SKIP_DEFAULT = {"batchid", "labref", "labstat", "moisture", "weight", "berat", "comment", "comments", "remark", "remarks", "date", "tanggal"}


def norm_h(h: Any) -> str:
    return re.sub(r"[\s_\-().\[\]/%]+", "", str(h or "")).lower()


def hole_key(h: Any) -> str:
    return re.sub(r"[^0-9a-z]", "", str(h or "").lower())


# ---------------------------------------------------------------- baca file
def _decode(b: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def read_table(path: Optional[str], b64: Optional[str], name: str, sheet: Optional[str]) -> tuple[list[str], str, list[list[Any]]]:
    """Kembalikan (daftar sheet, sheet dipakai, semua baris mentah)."""
    raw = Path(path).read_bytes() if path else base64.b64decode(b64 or "")
    ext = Path(path or name).suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        sheets = wb.sheetnames
        ws = wb[sheet] if sheet in sheets else wb[sheets[0]]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        wb.close()
        return sheets, ws.title, rows
    if ext == ".xls":
        raise ValueError("Format .xls (Excel 97-2003) belum didukung. Simpan ulang sebagai .xlsx atau CSV.")
    txt = _decode(raw)
    first = txt[:5000]
    try:
        dialect = csv.Sniffer().sniff(first, delimiters=",;\t|")
        delim = dialect.delimiter
    except csv.Error:
        delim = max(",;\t", key=first.count)
    return [], "", [r for r in csv.reader(io.StringIO(txt), delimiter=delim)]


def guess_header_row(rows: list[list[Any]]) -> int:
    for i, r in enumerate(rows[:30]):
        txt = [c for c in r if isinstance(c, str) and c.strip() and not _num(c)[1]]
        if len(txt) >= 2:
            return i
    return 0


_BDL = re.compile(r"^\s*<\s*=?\s*([0-9]*[.,]?[0-9]+)\s*$")
_ODL = re.compile(r"^\s*>\s*=?\s*([0-9]*[.,]?[0-9]+)\s*$")


def _num(v: Any) -> tuple[Optional[float], bool]:
    """(nilai, apakah angka). Mengurus <LD, >UD, koma desimal."""
    if v is None:
        return None, False
    if isinstance(v, bool):
        return None, False
    if isinstance(v, (int, float)):
        return (None, False) if isinstance(v, float) and math.isnan(v) else (float(v), True)
    s = str(v).strip()
    if s in ("", "-", "--", "NA", "N/A", "na", "n/a", "NaN", "null", "NULL", "#N/A"):
        return None, False
    m = _BDL.match(s)
    if m:
        return float(m.group(1).replace(",", ".")) / 2, True
    m = _ODL.match(s)
    if m:
        return float(m.group(1).replace(",", ".")), True
    s2 = s.replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+,\d+", s2):  # 1.234,5
        s2 = s2.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d+,\d+", s2):
        s2 = s2.replace(",", ".")
    try:
        return float(s2), True
    except ValueError:
        return None, False


def _txt(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if isinstance(v, float) and v.is_integer():
        s = str(int(v))
    return s or None


def guess_mapping(kind: str, headers: list[str], rows: list[list[Any]]) -> dict:
    nh = [norm_h(h) for h in headers]
    roles: dict[str, Optional[int]] = {}
    used: set[int] = set()
    for role, _lbl, _req in ROLES[kind]:
        roles[role] = None
        for a in ALIAS.get(role, []):
            a = norm_h(a)
            hit = [i for i, h in enumerate(nh) if h == a and i not in used]
            if not hit:
                hit = [i for i, h in enumerate(nh) if (h.startswith(a) or h.endswith(a)) and len(a) >= 3 and i not in used]
            if hit:
                roles[role] = hit[0]
                used.add(hit[0])
                break
    cols = []
    if kind in ("assay", "geology", "collar"):
        for i, h in enumerate(headers):
            if i in used or not str(h or "").strip():
                continue
            vals = [r[i] for r in rows[:500] if i < len(r) and r[i] not in (None, "")]
            nnum = sum(1 for v in vals if _num(v)[1])
            typ = "n" if vals and nnum / len(vals) >= 0.8 else "s"
            cols.append({"i": i, "src": str(h), "name": str(h).strip(), "type": typ,
                         "use": norm_h(h) not in SKIP_DEFAULT and bool(vals)})
    return {"roles": roles, "cols": cols}


# ---------------------------------------------------------------- database
DDL = """
CREATE TABLE IF NOT EXISTS dh_collar (hole TEXT, hole_key TEXT PRIMARY KEY, x REAL, y REAL, z REAL, depth REAL, dip REAL, azi REAL, attrs TEXT);
CREATE TABLE IF NOT EXISTS dh_survey (hole TEXT, hole_key TEXT, at REAL, dip REAL, azi REAL);
CREATE TABLE IF NOT EXISTS dh_int (kind TEXT, hole TEXT, hole_key TEXT, f REAL, t REAL, attrs TEXT);
CREATE INDEX IF NOT EXISTS ix_dh_int ON dh_int(kind, hole_key, f);
CREATE INDEX IF NOT EXISTS ix_dh_sv ON dh_survey(hole_key, at);
"""


def ensure(p: core_io.Project) -> None:
    if getattr(p, "_dh_ok", False):
        return
    with p.conn() as c:
        c.executescript(DDL)
        have = {x[1] for x in c.execute("PRAGMA table_info(photos)")}
        if "tray" not in have:
            c.execute("ALTER TABLE photos ADD COLUMN tray TEXT")
    p._dh_ok = True


def columns(p: core_io.Project) -> dict:
    m = core_io.get_meta(p)
    return {k: json.loads(m.get("dh_cols_" + k) or "[]") for k in ("assay", "geology", "collar")}


def do_import(p: core_io.Project, kind: str, rows: list[list[Any]], header_row: int, roles: dict, cols: list[dict], mode: str) -> dict:
    ensure(p)
    if kind not in KINDS:
        raise ValueError("Jenis tabel tidak dikenal: " + kind)
    for role, lbl, req in ROLES[kind]:
        if req and roles.get(role) is None:
            raise ValueError(f"Kolom '{lbl}' belum dipilih.")
    body = rows[header_row + 1:]
    use = [c for c in cols if c.get("use")]
    names = [c["name"].strip() for c in use]
    if len(set(n.lower() for n in names)) != len(names):
        raise ValueError("Ada nama kolom tampilan yang sama. Beri nama berbeda (mis. Au_1, Au_2).")
    rep = {"rows": 0, "skipped": 0, "bdl": 0, "holes": 0, "reasons": {}, "warnings": []}

    def skip(why):
        rep["skipped"] += 1
        rep["reasons"][why] = rep["reasons"].get(why, 0) + 1

    def cell(r, i):
        return r[i] if i is not None and i < len(r) else None

    recs = []
    for r in body:
        if not any(v not in (None, "") for v in r):
            continue
        hole = _txt(cell(r, roles["hole"]))
        if not hole:
            skip("Hole ID kosong")
            continue
        attrs = {}
        for c in use:
            v = cell(r, c["i"])
            if c["type"] == "n":
                x, ok = _num(v)
                if ok and isinstance(v, str) and v.strip().startswith("<"):
                    rep["bdl"] += 1
                if x is not None:
                    attrs[c["name"]] = x
            else:
                t = _txt(v)
                if t is not None:
                    attrs[c["name"]] = t
        if kind in ("assay", "geology"):
            f, okf = _num(cell(r, roles["from"]))
            t, okt = _num(cell(r, roles["to"]))
            if not (okf and okt):
                skip("From / To bukan angka")
                continue
            if f >= t:
                skip("From ≥ To")
                continue
            recs.append((kind, hole, hole_key(hole), f, t, json.dumps(attrs, ensure_ascii=False)))
        elif kind == "survey":
            at, ok1 = _num(cell(r, roles["at"]))
            dip, ok2 = _num(cell(r, roles["dip"]))
            az, ok3 = _num(cell(r, roles["azi"]))
            if not (ok1 and ok2 and ok3) or abs(dip) > 90:
                skip("Survey tidak valid (depth / dip / azimuth)")
                continue
            recs.append((hole, hole_key(hole), at, dip, az % 360))
        else:
            x, ok1 = _num(cell(r, roles["x"]))
            y, ok2 = _num(cell(r, roles["y"]))
            z, ok3 = _num(cell(r, roles["z"]))
            if not (ok1 and ok2 and ok3):
                skip("Koordinat collar kosong / bukan angka")
                continue
            d = _num(cell(r, roles.get("depth")))[0]
            dp = _num(cell(r, roles.get("dip")))[0]
            az = _num(cell(r, roles.get("azi")))[0]
            recs.append((hole, hole_key(hole), x, y, z, d, dp, az, json.dumps(attrs, ensure_ascii=False)))
    if not recs:
        raise ValueError("Tidak ada baris yang bisa diimport. Periksa baris header dan pemetaan kolom."
                         + (" Alasan: " + ", ".join(f"{k} ({v})" for k, v in rep["reasons"].items()) if rep["reasons"] else ""))
    keys = sorted({x[1] if kind != "assay" and kind != "geology" else x[2] for x in recs})
    rep["holes"] = len(keys)
    with p.lock, p.conn() as c:
        if kind in ("assay", "geology"):
            if mode == "replace":
                c.execute("DELETE FROM dh_int WHERE kind=?", (kind,))
            else:
                c.executemany("DELETE FROM dh_int WHERE kind=? AND hole_key=?", [(kind, k) for k in keys])
            c.executemany("INSERT INTO dh_int VALUES (?,?,?,?,?,?)", recs)
            # peringatan interval tumpang tindih
            ov, last = 0, {}
            for _k, _h, hk, f, t, _a in sorted(recs, key=lambda x: (x[2], x[3])):
                if hk in last and f < last[hk] - 1e-6:
                    ov += 1
                last[hk] = max(t, last.get(hk, t))
            if ov:
                rep["warnings"].append(f"{ov} interval tumpang tindih dalam file (tetap dipakai).")
        elif kind == "survey":
            if mode == "replace":
                c.execute("DELETE FROM dh_survey")
            else:
                c.executemany("DELETE FROM dh_survey WHERE hole_key=?", [(k,) for k in keys])
            c.executemany("INSERT INTO dh_survey VALUES (?,?,?,?,?)", recs)
        else:
            if mode == "replace":
                c.execute("DELETE FROM dh_collar")
            c.executemany("INSERT OR REPLACE INTO dh_collar VALUES (?,?,?,?,?,?,?,?,?)", recs)
        rep["rows"] = len(recs)
        # kolom tampilan digabung dengan yang sudah ada (nama sama = kolom sama)
        if kind in ("assay", "geology", "collar"):
            old = json.loads((c.execute("SELECT value FROM meta WHERE key=?", ("dh_cols_" + kind,)).fetchone() or ["[]"])[0] or "[]")
            if mode == "replace":
                old = []
            have = {o["name"].lower() for o in old}
            for cc in use:
                if cc["name"].lower() not in have:
                    old.append({"name": cc["name"], "type": cc["type"]})
            c.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", ("dh_cols_" + kind, json.dumps(old, ensure_ascii=False)))
        # pemetaan disimpan per jenis + tanda tangan header, dipakai lagi saat format file sama
        c.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", ("dh_map_" + kind, json.dumps({"roles": roles, "cols": cols, "header_row": header_row}, ensure_ascii=False)))
        # hole tanpa collar
        if kind != "collar":
            ck = {r[0] for r in c.execute("SELECT hole_key FROM dh_collar")}
            if ck:
                miss = [k for k in keys if k not in ck]
                if miss:
                    rep["warnings"].append(f"{len(miss)} hole tidak ada di Collar (mis. {', '.join(miss[:5])}).")
        photo_keys = {hole_key(r[0]) for r in c.execute("SELECT hole_id FROM photos WHERE hole_id IS NOT NULL")}
    rep["matched_photo_holes"] = len([k for k in keys if k in photo_keys])
    return rep


def summary(p: core_io.Project) -> dict:
    ensure(p)
    with p.conn() as c:
        q = lambda s, a=(): c.execute(s, a).fetchone()[0]  # noqa: E731
        out = {"collar": q("SELECT COUNT(*) FROM dh_collar"), "survey": q("SELECT COUNT(*) FROM dh_survey"),
               "assay": q("SELECT COUNT(*) FROM dh_int WHERE kind='assay'"), "geology": q("SELECT COUNT(*) FROM dh_int WHERE kind='geology'"),
               "holes": q("SELECT COUNT(DISTINCT hole_key) FROM dh_int")}
    out["columns"] = columns(p)
    m = core_io.get_meta(p)
    out["maps"] = {k: json.loads(m["dh_map_" + k]) for k in KINDS if m.get("dh_map_" + k)}
    out["tray_default"] = json.loads(m.get("tray_default") or "null") or TRAY_DEFAULT
    return out


# ---------------------------------------------------------------- hubungan foto <-> data bor
def intervals_by_hole(p: core_io.Project, kind: str, keys: Optional[set] = None) -> dict[str, list[tuple[float, float, dict]]]:
    ensure(p)
    out: dict[str, list] = {}
    with p.conn() as c:
        for hk, f, t, a in c.execute("SELECT hole_key, f, t, attrs FROM dh_int WHERE kind=? ORDER BY hole_key, f", (kind,)):
            if keys is not None and hk not in keys:
                continue
            out.setdefault(hk, []).append((f, t, json.loads(a or "{}")))
    return out


def photo_grades(p: core_io.Project, rows: list[dict]) -> None:
    """Tambahkan ke tiap baris foto: rata-rata tertimbang panjang & maksimum tiap unsur assay di rentang foto."""
    num = [c["name"] for c in columns(p)["assay"] if c["type"] == "n"]
    if not num:
        return
    keys = {hole_key(r["hole_id"]) for r in rows if r.get("hole_id")}
    by = intervals_by_hole(p, "assay", keys)
    for r in rows:
        ivs = by.get(hole_key(r.get("hole_id")))
        if not ivs or r.get("from_m") is None or r.get("to_m") is None:
            continue
        a, b = r["from_m"], r["to_m"]
        g, mx = {}, {}
        for el in num:
            sw = sv = 0.0
            m = None
            for f, t, at in ivs:
                if t <= a or f >= b or el not in at:
                    continue
                w = min(t, b) - max(f, a)
                sw += w
                sv += w * at[el]
                m = at[el] if m is None else max(m, at[el])
            if sw > 0:
                g[el] = round(sv / sw, 4)
                mx[el] = m
        if g:
            r["g"] = g
            r["gmax"] = mx


def _dirvec(dip: float, azi: float, down_negative: bool) -> tuple[float, float, float]:
    d = -dip if down_negative else dip  # d = sudut ke bawah dari horizontal (positif)
    rd, ra = math.radians(d), math.radians(azi)
    return (math.cos(rd) * math.sin(ra), math.cos(rd) * math.cos(ra), -math.sin(rd))


def xyz_at(p: core_io.Project, hk: str, depth: float) -> Optional[dict]:
    """Koordinat di kedalaman tertentu (metode tangen rata-rata antar stasiun survey)."""
    with p.conn() as c:
        col = c.execute("SELECT x, y, z, dip, azi FROM dh_collar WHERE hole_key=?", (hk,)).fetchone()
        if not col:
            return None
        sv = [(a, d, z) for a, d, z in c.execute("SELECT at, dip, azi FROM dh_survey WHERE hole_key=? ORDER BY at", (hk,))]
    if not sv:
        dip0 = col[3] if col[3] is not None else -90.0
        sv = [(0.0, dip0, col[4] if col[4] is not None else 0.0)]
    neg = sum(1 for _a, d, _z in sv if d < 0) >= sum(1 for _a, d, _z in sv if d > 0)
    if sv[0][0] > 0:
        sv.insert(0, (0.0, sv[0][1], sv[0][2]))
    x, y, z = col[0], col[1], col[2]
    for i in range(len(sv)):
        a0, d0, z0 = sv[i]
        a1 = sv[i + 1][0] if i + 1 < len(sv) else max(depth, a0)
        d1, z1 = (sv[i + 1][1], sv[i + 1][2]) if i + 1 < len(sv) else (d0, z0)
        if depth <= a0:
            break
        seg = min(depth, a1) - a0
        v0, v1 = _dirvec(d0, z0, neg), _dirvec(d1, z1, neg)
        v = [(v0[k] + v1[k]) / 2 for k in range(3)]
        n = math.sqrt(sum(t * t for t in v)) or 1
        x, y, z = x + seg * v[0] / n, y + seg * v[1] / n, z + seg * v[2] / n
        if depth <= a1:
            break
    return {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)}


TRAY_DEFAULT = {"x0": 0.02, "y0": 0.38, "x1": 0.98, "y1": 0.92, "rows": 4}  # cocok dengan foto standar proyek (papan label di atas)


def photo_detail(p: core_io.Project, pid: int) -> dict:
    ensure(p)
    with p.conn() as c:
        r = c.execute("SELECT hole_id, from_m, to_m, tray FROM photos WHERE id=?", (pid,)).fetchone()
        if not r:
            raise KeyError(f"Foto id {pid} tidak ada")
        hk = hole_key(r["hole_id"])
        col = c.execute("SELECT hole, x, y, z, depth, attrs FROM dh_collar WHERE hole_key=?", (hk,)).fetchone() if hk else None
    out: dict[str, Any] = {"hole_key": hk, "collar": None, "assay": [], "geology": [], "xyz_from": None, "xyz_to": None}
    m = core_io.get_meta(p)
    out["tray"] = json.loads(r["tray"]) if r["tray"] else (json.loads(m.get("tray_default") or "null") or TRAY_DEFAULT)
    out["tray_own"] = bool(r["tray"])
    if col:
        out["collar"] = {"hole": col["hole"], "x": col["x"], "y": col["y"], "z": col["z"], "depth": col["depth"], **json.loads(col["attrs"] or "{}")}
    if not hk or r["from_m"] is None or r["to_m"] is None:
        return out
    a, b = r["from_m"], r["to_m"]
    with p.conn() as c:
        for kind in ("assay", "geology"):
            out[kind] = [{"f": f, "t": t, **json.loads(at or "{}")} for f, t, at in
                         c.execute("SELECT f, t, attrs FROM dh_int WHERE kind=? AND hole_key=? AND t>? AND f<? ORDER BY f", (kind, hk, a, b))]
    if col:
        out["xyz_from"], out["xyz_to"] = xyz_at(p, hk, a), xyz_at(p, hk, b)
    return out


def set_tray(p: core_io.Project, pid: Optional[int], tray: Optional[dict], scope: str) -> None:
    ensure(p)
    if tray is not None:
        t = {k: float(tray[k]) for k in ("x0", "y0", "x1", "y1")}
        if not (0 <= t["x0"] < t["x1"] <= 1 and 0 <= t["y0"] < t["y1"] <= 1):
            raise ValueError("Area core box tidak valid.")
        t["rows"] = max(1, min(12, int(tray.get("rows", 4))))
        tray = t
    js = None if tray is None else json.dumps(tray)
    with p.lock, p.conn() as c:
        if scope == "default":
            c.execute("INSERT OR REPLACE INTO meta VALUES ('tray_default', ?)", (js,))
        elif scope == "hole":
            h = c.execute("SELECT hole_id FROM photos WHERE id=?", (pid,)).fetchone()
            c.execute("UPDATE photos SET tray=? WHERE hole_id=?", (js, h[0]))
        else:
            c.execute("UPDATE photos SET tray=? WHERE id=?", (js, pid))


# ---------------------------------------------------------------- cari cepat
_RX_Q = re.compile(r"^\s*([A-Za-z][\w.%]*)\s*(>=|<=|>|<|=)\s*(-?[0-9]*[.,]?[0-9]+)\s*$")


def search(p: core_io.Project, q: str, limit: int = 60) -> dict:
    ensure(p)
    q = (q or "").strip()
    if not q:
        return {"results": []}
    photos = core_io.rows(p)
    by_hole: dict[str, list[dict]] = {}
    for r in photos:
        by_hole.setdefault(hole_key(r.get("hole_id")), []).append(r)

    def photos_for(hk, f, t):
        return [r for r in by_hole.get(hk, []) if r["from_m"] is not None and r["to_m"] is not None and r["to_m"] > f and r["from_m"] < t]

    res: list[dict] = []
    m = _RX_Q.match(q)
    if m:  # kueri angka, mis. Au>=1
        el, op, val = m.group(1), m.group(2), float(m.group(3).replace(",", "."))
        cols = {c["name"].lower(): c["name"] for c in columns(p)["assay"] if c["type"] == "n"}
        name = cols.get(el.lower())
        if not name:
            raise ValueError(f"Unsur '{el}' tidak ada di data assay. Ada: {', '.join(cols.values()) or '-'}")
        cmp = {">=": lambda x: x >= val, "<=": lambda x: x <= val, ">": lambda x: x > val, "<": lambda x: x < val, "=": lambda x: abs(x - val) < 1e-9}[op]
        for hk, ivs in intervals_by_hole(p, "assay").items():
            for f, t, at in ivs:
                v = at.get(name)
                if v is not None and cmp(v):
                    ph = photos_for(hk, f, t)
                    res.append({"type": "assay", "hole": hk, "f": f, "t": t, "text": f"{name} = {v:g}",
                                "photo_id": ph[0]["id"] if ph else None, "photo": ph[0]["name"] if ph else None, "v": v})
        res.sort(key=lambda x: -x["v"])
        return {"results": res[:limit], "total": len(res), "numeric": True}
    ql = q.lower()
    LBL = {k: l for k, _t, l in core_io.FIELDS}
    LBL["name"] = "File"
    for r in photos:
        hay = " ".join(str(r.get(k) or "") for k in ("name", "rel", "hole_id", "lithology", "color", "alteration", "weathering", "oxidation", "notes", "photo_date", "drill_start"))
        if ql in hay.lower() or (hole_key(q) and hole_key(q) == hole_key(r.get("hole_id"))):
            hit = next((k for k in ("hole_id", "name", "lithology", "alteration", "notes", "color") if ql in str(r.get(k) or "").lower()), "hole_id")
            res.append({"type": "foto", "hole": r.get("hole_id"), "f": r.get("from_m"), "t": r.get("to_m"), "photo_id": r["id"], "photo": r["name"],
                        "text": f"{LBL.get(hit, 'File')}: {str(r.get(hit))[:90]}"})
    for kind in ("geology", "assay"):
        with p.conn() as c:
            for hole, hk, f, t, at in c.execute("SELECT hole, hole_key, f, t, attrs FROM dh_int WHERE kind=? AND (lower(attrs) LIKE ? OR hole_key=?) ORDER BY hole_key, f",
                                                (kind, "%" + ql.replace("%", "") + "%", hole_key(q))):
                d = json.loads(at or "{}")
                hit = [f"{k}: {v}" for k, v in d.items() if ql in str(v).lower() or ql in k.lower()]
                ph = photos_for(hk, f, t)
                res.append({"type": "geologi" if kind == "geology" else "assay", "hole": hole, "f": f, "t": t,
                            "text": "; ".join(hit[:3]) or ", ".join(f"{k}: {v}" for k, v in list(d.items())[:3]),
                            "photo_id": ph[0]["id"] if ph else None, "photo": ph[0]["name"] if ph else None})
                if len(res) > limit * 3:
                    break
    return {"results": res[:limit], "total": len(res)}


# ---------------------------------------------------------------- API
class SrcBody(BaseModel):
    folder: str
    kind: str
    path: Optional[str] = None
    b64: Optional[str] = None
    name: str = ""
    sheet: Optional[str] = None
    header_row: Optional[int] = None  # 0-based


class ImportBody(SrcBody):
    roles: dict[str, Optional[int]]
    cols: list[dict] = []
    mode: str = "upsert"  # upsert (ganti per hole) | replace (ganti semua)


class FolderBody(BaseModel):
    folder: str


class PhotoBody(BaseModel):
    folder: str
    id: int


class TrayBody(BaseModel):
    folder: str
    id: Optional[int] = None
    tray: Optional[dict] = None
    scope: str = "photo"  # photo | hole | default


class SearchBody(BaseModel):
    folder: str
    q: str
    limit: int = 60


class ClearBody(BaseModel):
    folder: str
    kind: str


@router.post("/preview")
def api_preview(b: SrcBody) -> dict:
    p = core_io.get_project(b.folder)
    ensure(p)
    sheets, sheet, rows = read_table(b.path, b.b64, b.name, b.sheet)
    if not rows:
        raise ValueError("File kosong.")
    hr = b.header_row if b.header_row is not None else guess_header_row(rows)
    hr = max(0, min(hr, len(rows) - 1))
    headers = [str(h).strip() if h is not None else "" for h in rows[hr]]
    body = rows[hr + 1:]
    guess = guess_mapping(b.kind, headers, body)
    # pakai pemetaan tersimpan bila header file sama
    saved = core_io.get_meta(p).get("dh_map_" + b.kind)
    reused = False
    if saved:
        sv = json.loads(saved)
        src = [c.get("src") for c in sv.get("cols", [])]
        if all(c is None or (c["i"] < len(headers) and headers[c["i"]] == c.get("src")) for c in sv.get("cols", [])) and src:
            guess = {"roles": sv["roles"], "cols": sv["cols"] + [c for c in guess["cols"] if c["src"] not in src]}
            reused = True
    sample = [[("" if v is None else (v if isinstance(v, (int, float)) else str(v))) for v in r] for r in body[:12]]
    return {"ok": True, "kind": b.kind, "sheets": sheets, "sheet": sheet, "header_row": hr, "headers": headers, "sample": sample,
            "nrows": len(body), "guess": guess, "reused": reused,
            "roles": [{"key": k, "label": l, "req": q} for k, l, q in ROLES[b.kind]]}


@router.post("/import")
def api_import(b: ImportBody) -> dict:
    p = core_io.get_project(b.folder)
    _s, _sh, rows = read_table(b.path, b.b64, b.name, b.sheet)
    hr = b.header_row if b.header_row is not None else guess_header_row(rows)
    rep = do_import(p, b.kind, rows, hr, b.roles, b.cols, b.mode)
    return {"ok": True, "report": rep, "summary": summary(p)}


@router.post("/summary")
def api_summary(b: FolderBody) -> dict:
    return {"ok": True, **summary(core_io.get_project(b.folder))}


@router.post("/clear")
def api_clear(b: ClearBody) -> dict:
    p = core_io.get_project(b.folder)
    ensure(p)
    with p.lock, p.conn() as c:
        if b.kind in ("assay", "geology"):
            c.execute("DELETE FROM dh_int WHERE kind=?", (b.kind,))
        elif b.kind == "survey":
            c.execute("DELETE FROM dh_survey")
        elif b.kind == "collar":
            c.execute("DELETE FROM dh_collar")
        else:
            raise ValueError("Jenis tabel tidak dikenal")
        c.execute("DELETE FROM meta WHERE key IN (?, ?)", ("dh_cols_" + b.kind, "dh_map_" + b.kind))
    return {"ok": True, "summary": summary(p)}


@router.post("/photo")
def api_photo(b: PhotoBody) -> dict:
    return {"ok": True, **photo_detail(core_io.get_project(b.folder), b.id)}


@router.post("/tray")
def api_tray(b: TrayBody) -> dict:
    p = core_io.get_project(b.folder)
    set_tray(p, b.id, b.tray, b.scope)
    return {"ok": True}


@router.post("/search")
def api_search(b: SearchBody) -> dict:
    return {"ok": True, **search(core_io.get_project(b.folder), b.q, b.limit)}
