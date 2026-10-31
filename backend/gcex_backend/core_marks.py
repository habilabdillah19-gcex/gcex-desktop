"""DB-Ex: tanda interval di foto core box (half core, core loss, jenis lain).

- Satu tanda = satu interval kedalaman (From-To) pada satu foto, opsional dengan posisi di foto
  (baris core awal/akhir + posisi 0..1 di sepanjang baris, mengikuti area core / tray foto itu).
- Half core wajib punya nomor sampel (dicocokkan dengan assay lewat kolom Sample bila ada).
- Core loss: Core Recovery (%) foto dihitung otomatis = (interval foto - total core loss) / interval foto.
  Isian ini bertanda sumber "tanda" (rec_src) dan tidak ditimpa AI. Edit manual Recovery mengalahkan tanda
  sampai tanda foto itu berubah lagi.
- Setiap perubahan tercatat di tabel history (field 'tanda' / 'recovery_pct', src 'tanda').
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from . import core_io

router = APIRouter(prefix="/core/marks", tags=["core-marks"])

KINDS = {"halfcore": "Half core", "coreloss": "Core loss"}
_DDL = """
CREATE TABLE IF NOT EXISTS marks (
  id INTEGER PRIMARY KEY AUTOINCREMENT, photo_id INTEGER NOT NULL, kind TEXT NOT NULL,
  from_m REAL NOT NULL, to_m REAL NOT NULL, sample_no TEXT, note TEXT,
  row0 INTEGER, x0 REAL, row1 INTEGER, x1 REAL,
  by TEXT, at TEXT, edited_by TEXT, edited_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_marks_photo ON marks(photo_id);
"""


def ensure(p: core_io.Project) -> None:
    with p.conn() as c:
        c.executescript(_DDL)


def kind_label(k: str) -> str:
    return KINDS.get(k, k)


def _clean(d: dict) -> dict:
    kind = str(d.get("kind") or "").strip().lower().replace(" ", "")
    kind = {"half": "halfcore", "half-core": "halfcore", "loss": "coreloss", "core-loss": "coreloss"}.get(kind, kind)
    if not kind:
        raise ValueError("Jenis tanda kosong.")
    if len(kind) > 30:
        raise ValueError("Nama jenis tanda terlalu panjang (maks. 30 huruf).")
    try:
        f = round(float(str(d.get("from_m")).replace(",", ".")), 3)
        t = round(float(str(d.get("to_m")).replace(",", ".")), 3)
    except (TypeError, ValueError):
        raise ValueError("From dan To tanda harus angka.") from None
    if not t > f:
        raise ValueError("To harus lebih besar dari From.")
    sample = str(d.get("sample_no") or "").strip() or None
    if kind == "halfcore" and not sample:
        raise ValueError("Interval half core wajib diisi nomor sampel.")
    pos: dict[str, Any] = {}
    for k, lo, hi in (("row0", 0, 12), ("row1", 0, 12)):
        v = d.get(k)
        pos[k] = None if v is None or v == "" else max(lo, min(hi, int(v)))
    for k in ("x0", "x1"):
        v = d.get(k)
        pos[k] = None if v is None or v == "" else max(0.0, min(1.0, round(float(v), 4)))
    return {"kind": kind, "from_m": f, "to_m": t, "sample_no": sample, "note": str(d.get("note") or "").strip() or None, **pos}


def _desc(m: dict) -> str:
    s = f"{kind_label(m['kind'])} {m['from_m']:g}-{m['to_m']:g} m"
    if m.get("sample_no"):
        s += f" sampel {m['sample_no']}"
    return s


def _hist(c, pid: int, old: Optional[str], new: Optional[str], by: str) -> None:
    c.execute("INSERT INTO history (photo_id, field, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
              (pid, "tanda", old, new, "tanda", by, core_io.now()))


def recompute_recovery(p: core_io.Project, c, pid: int, by: str) -> None:
    """Recovery foto dari tanda core loss. Dipanggil di dalam transaksi yang sama dengan perubahan tanda."""
    r = c.execute("SELECT from_m, to_m, recovery_pct, rec_src FROM photos WHERE id=?", (pid,)).fetchone()
    if not r:
        return
    ms = c.execute("SELECT kind, from_m, to_m FROM marks WHERE photo_id=?", (pid,)).fetchall()
    if not ms:
        if r["rec_src"] == "tanda":  # semua tanda dihapus: nilai tetap, sumbernya tidak lagi "tanda"
            c.execute("UPDATE photos SET rec_src=NULL WHERE id=?", (pid,))
        return
    a, b = r["from_m"], r["to_m"]
    if a is None or b is None or not b > a:
        return
    loss = sum(max(0.0, min(b, m["to_m"]) - max(a, m["from_m"])) for m in ms if m["kind"] == "coreloss")
    rec = round(max(0.0, min(100.0, (b - a - loss) / (b - a) * 100.0)), 1)
    if rec != r["recovery_pct"] or r["rec_src"] != "tanda":
        c.execute("UPDATE photos SET recovery_pct=?, rec_src='tanda' WHERE id=?", (rec, pid))
        if rec != r["recovery_pct"]:
            c.execute("INSERT INTO history (photo_id, field, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, "recovery_pct", None if r["recovery_pct"] is None else str(r["recovery_pct"]), str(rec), "tanda", by, core_io.now()))


def list_marks(p: core_io.Project, pid: Optional[int] = None) -> list[dict]:
    ensure(p)
    with p.conn() as c:
        q = "SELECT m.*, ph.hole_id, ph.name AS photo FROM marks m LEFT JOIN photos ph ON ph.id=m.photo_id"
        rs = c.execute(q + (" WHERE m.photo_id=? ORDER BY m.from_m" if pid else " ORDER BY ph.hole_id, m.from_m"), (pid,) if pid else ()).fetchall()
    return [{**dict(r), "label": kind_label(r["kind"]), "len_m": round(r["to_m"] - r["from_m"], 3)} for r in rs]


def save(p: core_io.Project, pid: int, data: dict, by: str, mid: Optional[int] = None) -> dict:
    ensure(p)
    m = _clean(data)
    with p.lock, p.conn() as c:
        if not c.execute("SELECT 1 FROM photos WHERE id=?", (pid,)).fetchone():
            raise KeyError(f"Foto id {pid} tidak ada")
        cols = list(m)
        if mid:
            old = c.execute("SELECT * FROM marks WHERE id=? AND photo_id=?", (mid, pid)).fetchone()
            if not old:
                raise KeyError(f"Tanda id {mid} tidak ada")
            c.execute(f"UPDATE marks SET {', '.join(k + '=?' for k in cols)}, edited_by=?, edited_at=? WHERE id=?",
                      [m[k] for k in cols] + [by, core_io.now(), mid])
            _hist(c, pid, _desc(dict(old)), _desc(m), by)
        else:
            mid = c.execute(f"INSERT INTO marks (photo_id, {', '.join(cols)}, by, at) VALUES (?, {', '.join('?' * len(cols))}, ?, ?)",
                            [pid] + [m[k] for k in cols] + [by, core_io.now()]).lastrowid
            _hist(c, pid, None, _desc(m), by)
        recompute_recovery(p, c, pid, by)
    return {"id": mid, "marks": list_marks(p, pid)}


def delete(p: core_io.Project, mid: int, by: str) -> dict:
    ensure(p)
    with p.lock, p.conn() as c:
        old = c.execute("SELECT * FROM marks WHERE id=?", (mid,)).fetchone()
        if not old:
            raise KeyError(f"Tanda id {mid} tidak ada")
        pid = old["photo_id"]
        c.execute("DELETE FROM marks WHERE id=?", (mid,))
        _hist(c, pid, _desc(dict(old)), None, by)
        recompute_recovery(p, c, pid, by)
    return {"photo_id": pid, "marks": list_marks(p, pid)}


def enrich(p: core_io.Project, rows: list[dict]) -> None:
    """Ringkasan tanda per foto untuk tabel: loss_m, half_m, half_samples, n_marks."""
    ensure(p)
    agg: dict[int, dict] = {}
    with p.conn() as c:
        for r in c.execute("SELECT photo_id, kind, from_m, to_m, sample_no FROM marks"):
            a = agg.setdefault(r["photo_id"], {"loss_m": 0.0, "half_m": 0.0, "half_samples": [], "n_marks": 0})
            a["n_marks"] += 1
            if r["kind"] == "coreloss":
                a["loss_m"] += r["to_m"] - r["from_m"]
            elif r["kind"] == "halfcore":
                a["half_m"] += r["to_m"] - r["from_m"]
                if r["sample_no"]:
                    a["half_samples"].append(r["sample_no"])
    for r in rows:
        a = agg.get(r["id"])
        r["loss_m"] = round(a["loss_m"], 2) if a and a["loss_m"] else None
        r["half_m"] = round(a["half_m"], 2) if a and a["half_m"] else None
        r["half_samples"] = ", ".join(a["half_samples"]) if a else ""
        r["n_marks"] = a["n_marks"] if a else 0


HEAD = ["Hole ID", "From (m)", "To (m)", "Panjang (m)", "Jenis", "No. Sampel", "Catatan", "File Foto", "Ditandai oleh", "Waktu"]


def table(p: core_io.Project) -> list[list[Any]]:
    return [[m["hole_id"], m["from_m"], m["to_m"], m["len_m"], m["label"], m["sample_no"], m["note"], m["photo"],
             m["edited_by"] or m["by"], m["edited_at"] or m["at"]] for m in list_marks(p)]


def to_csv(p: core_io.Project) -> bytes:
    b = io.StringIO()
    w = csv.writer(b)
    w.writerow(HEAD)
    w.writerows(table(p))
    return ("﻿" + b.getvalue()).encode("utf-8")


def search(p: core_io.Project, q: str) -> list[dict]:
    ql = q.lower().strip()
    out = []
    for m in list_marks(p):
        hay = f"{m['label']} {m['kind']} {m['sample_no'] or ''} {m['note'] or ''}".lower()
        if ql and (ql in hay or ql.replace(" ", "") in hay.replace(" ", "")):
            out.append({"type": "tanda", "hole": m["hole_id"], "f": m["from_m"], "t": m["to_m"], "photo_id": m["photo_id"], "photo": m["photo"],
                        "text": _desc(m) + (f" · {m['note']}" if m["note"] else "")})
    return out


# ---------------------------------------------------------------- API
class ListBody(BaseModel):
    folder: str
    id: Optional[int] = None


class SaveBody(BaseModel):
    folder: str
    by: str = ""
    photo_id: int
    mark_id: Optional[int] = None
    mark: dict[str, Any]


class DelBody(BaseModel):
    folder: str
    by: str = ""
    mark_id: int


@router.post("/list")
def api_list(b: ListBody) -> dict:
    return {"ok": True, "marks": list_marks(core_io.get_project(b.folder), b.id)}


@router.post("/save")
def api_save(b: SaveBody) -> dict:
    p = core_io.get_project(b.folder)
    out = save(p, b.photo_id, b.mark, b.by, b.mark_id)
    return {"ok": True, **out, "row": core_io.get_row(p, b.photo_id)}


@router.post("/delete")
def api_delete(b: DelBody) -> dict:
    p = core_io.get_project(b.folder)
    out = delete(p, b.mark_id, b.by)
    return {"ok": True, **out, "row": core_io.get_row(p, out["photo_id"])}


@router.post("/csv")
def api_csv(b: ListBody) -> Response:
    return Response(to_csv(core_io.get_project(b.folder)), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="DB-Ex_Interval_Tanda.csv"'})
