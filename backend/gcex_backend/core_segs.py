"""DB-Ex: segmen interpretasi per baris core (AI / manual) mengikuti batas geologi aktual.

- Satu segmen = potongan sepanjang box, disimpan sebagai pecahan panjang box f0..f1 (0 = awal baris 1, 1 = akhir baris
  terakhir). Kedalaman = From foto + f x (To - From), jadi segmen ikut benar bila From/To foto dikoreksi.
- AI mengembalikan segmen per baris core (row, start, end) dengan atribut geologi & geoteknik masing-masing.
- Segmen yang diedit geologist (atribut, batas, belah, gabung, tambah) tidak pernah ditimpa AI; analisis ulang hanya
  mengganti segmen AI yang belum diedit dan memotongnya di sekitar segmen yang diedit. Foto terverifikasi tidak disentuh.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from . import core_io

router = APIRouter(prefix="/core/segs", tags=["core-segs"])

# kolom per segmen: (key, tipe, label)
SEG_FIELDS: list[tuple[str, str, str]] = [
    ("lithology", "s", "Litologi"), ("alteration", "s", "Alterasi"), ("color", "s", "Warna"),
    ("weathering", "s", "Pelapukan"), ("oxidation", "s", "Oksidasi"), ("rqd_pct", "n", "RQD (%)"),
    ("recovery_pct", "n", "Recovery (%)"), ("ff_per_m", "n", "Rekahan / m"), ("gsi", "s", "GSI"), ("rmr", "n", "RMR"),
    ("notes", "s", "Catatan"),
]
SEG_TYPE = {k: t for k, t, _ in SEG_FIELDS}
EPS = 1e-4
_DDL = """
CREATE TABLE IF NOT EXISTS segs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, photo_id INTEGER NOT NULL, f0 REAL NOT NULL, f1 REAL NOT NULL,
  src TEXT DEFAULT 'ai', edited TEXT DEFAULT '[]', attrs TEXT DEFAULT '{}', model TEXT,
  by TEXT, at TEXT, edited_by TEXT, edited_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_segs_photo ON segs(photo_id);
"""


def ensure(p: core_io.Project) -> None:
    with p.conn() as c:
        c.executescript(_DDL)


def _norm(k: str, v: Any) -> Any:
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    if SEG_TYPE[k] == "n":
        f = float(str(v).replace(",", ".").replace("%", "").strip())
        if k in ("rqd_pct", "recovery_pct", "rmr"):
            f = max(0.0, min(100.0, f))
        return round(max(0.0, f), 2)
    return str(v).strip()[:200]


def _clean_attrs(d: dict) -> dict:
    out = {}
    for k in SEG_TYPE:
        if k in d:
            try:
                out[k] = _norm(k, d[k])
            except (TypeError, ValueError):
                out[k] = None
    return out


def _photo(c, pid: int):
    r = c.execute("SELECT id, from_m, to_m, verified FROM photos WHERE id=?", (pid,)).fetchone()
    if not r:
        raise KeyError(f"Foto id {pid} tidak ada")
    return r


def _out(r, a: Optional[float], b: Optional[float]) -> dict:
    d = {"id": r["id"], "photo_id": r["photo_id"], "f0": r["f0"], "f1": r["f1"], "src": r["src"], "model": r["model"],
         "edited": json.loads(r["edited"] or "[]"), "by": r["edited_by"] or r["by"], "at": r["edited_at"] or r["at"], **json.loads(r["attrs"] or "{}")}
    if a is not None and b is not None and b > a:
        d["from_m"] = round(a + r["f0"] * (b - a), 3)
        d["to_m"] = round(a + r["f1"] * (b - a), 3)
    return d


def list_segs(p: core_io.Project, pid: int) -> list[dict]:
    ensure(p)
    with p.conn() as c:
        ph = _photo(c, pid)
        return [_out(r, ph["from_m"], ph["to_m"]) for r in c.execute("SELECT * FROM segs WHERE photo_id=? ORDER BY f0", (pid,))]


def _hist(c, pid: int, old: Optional[str], new: Optional[str], src: str, by: str) -> None:
    c.execute("INSERT INTO history (photo_id, field, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
              (pid, "segmen", old, new, src, by, core_io.now()))


def _desc(f0: float, f1: float, attrs: dict) -> str:
    v = ", ".join(f"{k}={attrs[k]}" for k in ("lithology", "weathering", "rqd_pct") if attrs.get(k) is not None)
    return f"{f0:.3f}-{f1:.3f}" + (f" ({v})" if v else "")


def _subtract(a: float, b: float, keep: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = [(a, b)]
    for k0, k1 in keep:
        nxt = []
        for x0, x1 in out:
            if k1 <= x0 + EPS or k0 >= x1 - EPS:
                nxt.append((x0, x1))
                continue
            if k0 > x0 + EPS:
                nxt.append((x0, k0))
            if k1 < x1 - EPS:
                nxt.append((k1, x1))
        out = nxt
    return [(x0, x1) for x0, x1 in out if x1 - x0 > 0.003]


def ai_to_fracs(segments: Any, rows: int) -> list[tuple[float, float, dict]]:
    """Segmen AI (row 1..n, start/end 0..1 di baris) -> (f0, f1, attrs) terurut, tanpa tumpang tindih."""
    rows = max(1, int(rows or 1))
    out = []
    for s in segments if isinstance(segments, list) else []:
        if not isinstance(s, dict):
            continue
        try:
            row = int(s.get("row") or 1)
            st, en = float(s.get("start", 0) or 0), float(s.get("end", 1) if s.get("end") is not None else 1)
        except (TypeError, ValueError):
            continue
        row = max(1, min(rows, row))
        st, en = max(0.0, min(1.0, st)), max(0.0, min(1.0, en))
        if en < st:
            st, en = en, st
        f0, f1 = (row - 1 + st) / rows, (row - 1 + en) / rows
        if f1 - f0 > 0.003:
            out.append((f0, f1, _clean_attrs(s)))
    out.sort(key=lambda x: x[0])
    clean, last = [], 0.0
    for f0, f1, at in out:
        f0 = max(f0, last)
        if f1 - f0 > 0.003:
            clean.append((round(f0, 5), round(f1, 5), at))
            last = f1
    return clean


def apply_ai_segments(p: core_io.Project, pid: int, segments: Any, rows: int, model: str) -> int:
    """Ganti segmen AI yang belum diedit; segmen yang diedit / manual dipertahankan dan tidak ditimpa."""
    ensure(p)
    fr = ai_to_fracs(segments, rows)
    with p.lock, p.conn() as c:
        ph = _photo(c, pid)
        if ph["verified"]:
            return 0
        keep = [(r["f0"], r["f1"]) for r in c.execute("SELECT f0, f1 FROM segs WHERE photo_id=? AND (src='manual' OR edited<>'[]')", (pid,))]
        c.execute("DELETE FROM segs WHERE photo_id=? AND src='ai' AND edited='[]'", (pid,))
        n = 0
        for f0, f1, at in fr:
            for x0, x1 in _subtract(f0, f1, sorted(keep)):
                c.execute("INSERT INTO segs (photo_id, f0, f1, src, attrs, model, by, at) VALUES (?,?,?,?,?,?,?,?)",
                          (pid, round(x0, 5), round(x1, 5), "ai", json.dumps(at, ensure_ascii=False), model, "AI", core_io.now()))
                n += 1
        if n:
            _hist(c, pid, None, f"{n} segmen AI", "ai:" + model, "AI")
        return n


def _depth_to_f(ph, d: Any) -> float:
    a, b = ph["from_m"], ph["to_m"]
    if a is None or b is None or not b > a:
        raise ValueError("Isi From dan To foto dulu agar kedalaman segmen bisa dihitung.")
    return max(0.0, min(1.0, (float(str(d).replace(",", ".")) - a) / (b - a)))


def save(p: core_io.Project, pid: int, data: dict, by: str, sid: Optional[int] = None) -> dict:
    """Simpan atribut / batas satu segmen (baru bila sid kosong). Batas: f0/f1 atau from_m/to_m."""
    ensure(p)
    with p.lock, p.conn() as c:
        ph = _photo(c, pid)
        old = c.execute("SELECT * FROM segs WHERE id=? AND photo_id=?", (sid, pid)).fetchone() if sid else None
        if sid and not old:
            raise KeyError(f"Segmen id {sid} tidak ada")
        f0 = data.get("f0") if data.get("f0") is not None else (_depth_to_f(ph, data["from_m"]) if data.get("from_m") not in (None, "") else (old["f0"] if old else None))
        f1 = data.get("f1") if data.get("f1") is not None else (_depth_to_f(ph, data["to_m"]) if data.get("to_m") not in (None, "") else (old["f1"] if old else None))
        if f0 is None or f1 is None:
            raise ValueError("Batas segmen belum diisi.")
        f0, f1 = round(max(0.0, min(1.0, float(f0))), 5), round(max(0.0, min(1.0, float(f1))), 5)
        if not f1 - f0 > 0.003:
            raise ValueError("Batas akhir segmen harus lebih besar dari batas awal.")
        attrs = json.loads(old["attrs"] or "{}") if old else {}
        new_attrs = _clean_attrs(data.get("attrs") or {})
        edited = set(json.loads(old["edited"] or "[]")) if old else set()
        for k, v in new_attrs.items():
            if attrs.get(k) != v:
                edited.add(k)
            attrs[k] = v
        if old and (abs(old["f0"] - f0) > EPS or abs(old["f1"] - f1) > EPS):
            edited.add("batas")
        if old:
            c.execute("UPDATE segs SET f0=?, f1=?, attrs=?, edited=?, edited_by=?, edited_at=? WHERE id=?",
                      (f0, f1, json.dumps(attrs, ensure_ascii=False), json.dumps(sorted(edited)), by, core_io.now(), sid))
            _hist(c, pid, _desc(old["f0"], old["f1"], json.loads(old["attrs"] or "{}")), _desc(f0, f1, attrs), "manual", by)
        else:
            sid = c.execute("INSERT INTO segs (photo_id, f0, f1, src, edited, attrs, by, at) VALUES (?,?,?,?,?,?,?,?)",
                            (pid, f0, f1, "manual", json.dumps(sorted(new_attrs)), json.dumps(attrs, ensure_ascii=False), by, core_io.now())).lastrowid
            _hist(c, pid, None, _desc(f0, f1, attrs), "manual", by)
        _resolve_overlap(c, pid, sid, f0, f1)
    return {"id": sid, "segs": list_segs(p, pid)}


def _resolve_overlap(c, pid: int, sid: int, f0: float, f1: float) -> None:
    """Segmen lain yang tertimpa dipotong (atau dihapus bila habis): segmen yang baru disimpan menang."""
    for r in c.execute("SELECT * FROM segs WHERE photo_id=? AND id<>? AND f1>? AND f0<?", (pid, sid, f0 + EPS, f1 - EPS)).fetchall():
        parts = _subtract(r["f0"], r["f1"], [(f0, f1)])
        if not parts:
            c.execute("DELETE FROM segs WHERE id=?", (r["id"],))
            continue
        c.execute("UPDATE segs SET f0=?, f1=? WHERE id=?", (parts[0][0], parts[0][1], r["id"]))
        for x0, x1 in parts[1:]:
            c.execute("INSERT INTO segs (photo_id, f0, f1, src, edited, attrs, model, by, at, edited_by, edited_at) "
                      "SELECT photo_id, ?, ?, src, edited, attrs, model, by, at, edited_by, edited_at FROM segs WHERE id=?", (x0, x1, r["id"]))


def move_bound(p: core_io.Project, sid: int, side: str, f: float, by: str) -> dict:
    """Geser batas awal / akhir segmen. Segmen tetangga yang berbagi batas ikut bergeser (tanpa celah / tumpang tindih)."""
    ensure(p)
    with p.lock, p.conn() as c:
        r = c.execute("SELECT * FROM segs WHERE id=?", (sid,)).fetchone()
        if not r:
            raise KeyError(f"Segmen id {sid} tidak ada")
        pid, k = r["photo_id"], ("f0" if side == "start" else "f1")
        old = r[k]
        nb = c.execute(f"SELECT * FROM segs WHERE photo_id=? AND id<>? AND abs({'f1' if k == 'f0' else 'f0'}-?)<?", (pid, sid, old, 2e-3)).fetchone()
        lo = (nb["f0"] + 0.004) if (nb and k == "f0") else 0.0
        hi = (nb["f1"] - 0.004) if (nb and k == "f1") else 1.0
        lo, hi = (max(lo, 0.0), min(r["f1"] - 0.004, hi)) if k == "f0" else (max(lo, r["f0"] + 0.004), min(hi, 1.0))
        f = round(max(lo, min(hi, float(f))), 5)
        for row, kk in ((r, k), (nb, "f1" if k == "f0" else "f0")):
            if row is None:
                continue
            ed = set(json.loads(row["edited"] or "[]")) | {"batas"}
            c.execute(f"UPDATE segs SET {kk}=?, edited=?, edited_by=?, edited_at=? WHERE id=?", (f, json.dumps(sorted(ed)), by, core_io.now(), row["id"]))
        _hist(c, pid, f"batas {old:.3f}", f"batas {f:.3f}", "manual", by)
        _resolve_overlap(c, pid, sid, *(sorted([f, r["f1"]]) if k == "f0" else sorted([r["f0"], f])))
    return {"photo_id": pid, "segs": list_segs(p, pid)}


def split(p: core_io.Project, sid: int, f: float, by: str) -> dict:
    ensure(p)
    with p.lock, p.conn() as c:
        r = c.execute("SELECT * FROM segs WHERE id=?", (sid,)).fetchone()
        if not r:
            raise KeyError(f"Segmen id {sid} tidak ada")
        f = round(float(f), 5)
        if not (r["f0"] + 0.004 < f < r["f1"] - 0.004):
            raise ValueError("Titik belah harus di dalam segmen.")
        ed = json.dumps(sorted(set(json.loads(r["edited"] or "[]")) | {"batas"}))
        c.execute("UPDATE segs SET f1=?, edited=?, edited_by=?, edited_at=? WHERE id=?", (f, ed, by, core_io.now(), sid))
        c.execute("INSERT INTO segs (photo_id, f0, f1, src, edited, attrs, model, by, at, edited_by, edited_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (r["photo_id"], f, r["f1"], r["src"], ed, r["attrs"], r["model"], r["by"], r["at"], by, core_io.now()))
        _hist(c, r["photo_id"], _desc(r["f0"], r["f1"], {}), f"dibelah di {f:.3f}", "manual", by)
    return {"photo_id": r["photo_id"], "segs": list_segs(p, r["photo_id"])}


def merge_next(p: core_io.Project, sid: int, by: str) -> dict:
    ensure(p)
    with p.lock, p.conn() as c:
        r = c.execute("SELECT * FROM segs WHERE id=?", (sid,)).fetchone()
        if not r:
            raise KeyError(f"Segmen id {sid} tidak ada")
        nx = c.execute("SELECT * FROM segs WHERE photo_id=? AND f0>=? AND id<>? ORDER BY f0 LIMIT 1", (r["photo_id"], r["f1"] - 2e-3, sid)).fetchone()
        if not nx:
            raise ValueError("Tidak ada segmen sesudahnya untuk digabung.")
        ed = json.dumps(sorted(set(json.loads(r["edited"] or "[]")) | {"batas"}))
        c.execute("UPDATE segs SET f1=?, edited=?, edited_by=?, edited_at=? WHERE id=?", (nx["f1"], ed, by, core_io.now(), sid))
        c.execute("DELETE FROM segs WHERE id=?", (nx["id"],))
        _hist(c, r["photo_id"], f"{r['f0']:.3f}-{r['f1']:.3f} + {nx['f0']:.3f}-{nx['f1']:.3f}", f"digabung {r['f0']:.3f}-{nx['f1']:.3f}", "manual", by)
    return {"photo_id": r["photo_id"], "segs": list_segs(p, r["photo_id"])}


def delete(p: core_io.Project, sid: int, by: str) -> dict:
    ensure(p)
    with p.lock, p.conn() as c:
        r = c.execute("SELECT * FROM segs WHERE id=?", (sid,)).fetchone()
        if not r:
            raise KeyError(f"Segmen id {sid} tidak ada")
        c.execute("DELETE FROM segs WHERE id=?", (sid,))
        _hist(c, r["photo_id"], _desc(r["f0"], r["f1"], json.loads(r["attrs"] or "{}")), None, "manual", by)
    return {"photo_id": r["photo_id"], "segs": list_segs(p, r["photo_id"])}


def all_rows(p: core_io.Project) -> list[dict]:
    ensure(p)
    with p.conn() as c:
        rs = c.execute("SELECT s.*, ph.hole_id, ph.name AS photo, ph.from_m AS pa, ph.to_m AS pb FROM segs s JOIN photos ph ON ph.id=s.photo_id "
                       "ORDER BY ph.hole_id, ph.from_m, s.f0").fetchall()
    out = []
    for r in rs:
        d = _out(r, r["pa"], r["pb"])
        d["hole_id"], d["photo"] = r["hole_id"], r["photo"]
        out.append(d)
    return out


def search(p: core_io.Project, q: str) -> list[dict]:
    ql = q.lower().strip()
    if not ql:
        return []
    out = []
    for s in all_rows(p):
        hit = [f"{lbl}: {s[k]}" for k, t, lbl in SEG_FIELDS if t == "s" and s.get(k) and ql in str(s[k]).lower()]
        if hit:
            out.append({"type": "segmen", "hole": s["hole_id"], "f": s.get("from_m"), "t": s.get("to_m"), "photo_id": s["photo_id"], "photo": s["photo"],
                        "text": ("AI " if s["src"] == "ai" and not s["edited"] else "") + "; ".join(hit[:2])})
    return out


HEAD = ["Hole ID", "From (m)", "To (m)", "Panjang (m)"] + [lbl for _k, _t, lbl in SEG_FIELDS] + ["Sumber", "Diedit", "File Foto", "Oleh", "Waktu"]


def table(p: core_io.Project) -> list[list[Any]]:
    out = []
    for s in all_rows(p):
        ln = round(s["to_m"] - s["from_m"], 3) if s.get("from_m") is not None else None
        out.append([s["hole_id"], s.get("from_m"), s.get("to_m"), ln] + [s.get(k) for k, _t, _l in SEG_FIELDS] +
                   ["AI" if s["src"] == "ai" else "manual", ", ".join(s["edited"]), s["photo"], s["by"], s["at"]])
    return out


# ---------------------------------------------------------------- API
class ListBody(BaseModel):
    folder: str
    id: int


class SaveBody(BaseModel):
    folder: str
    by: str = ""
    photo_id: int
    seg_id: Optional[int] = None
    seg: dict[str, Any]


class OpBody(BaseModel):
    folder: str
    by: str = ""
    seg_id: int
    side: str = "end"
    f: float = 0.0


def _ret(p, out: dict, pid: int) -> dict:
    return {"ok": True, **out, "row": core_io.get_row(p, pid)}


@router.post("/list")
def api_list(b: ListBody) -> dict:
    return {"ok": True, "segs": list_segs(core_io.get_project(b.folder), b.id), "fields": [{"key": k, "type": t, "label": l} for k, t, l in SEG_FIELDS]}


@router.post("/save")
def api_save(b: SaveBody) -> dict:
    p = core_io.get_project(b.folder)
    return _ret(p, save(p, b.photo_id, b.seg, b.by, b.seg_id), b.photo_id)


@router.post("/bound")
def api_bound(b: OpBody) -> dict:
    p = core_io.get_project(b.folder)
    out = move_bound(p, b.seg_id, b.side, b.f, b.by)
    return _ret(p, out, out["photo_id"])


@router.post("/split")
def api_split(b: OpBody) -> dict:
    p = core_io.get_project(b.folder)
    out = split(p, b.seg_id, b.f, b.by)
    return _ret(p, out, out["photo_id"])


@router.post("/merge")
def api_merge(b: OpBody) -> dict:
    p = core_io.get_project(b.folder)
    out = merge_next(p, b.seg_id, b.by)
    return _ret(p, out, out["photo_id"])


@router.post("/delete")
def api_delete(b: OpBody) -> dict:
    p = core_io.get_project(b.folder)
    out = delete(p, b.seg_id, b.by)
    return _ret(p, out, out["photo_id"])
