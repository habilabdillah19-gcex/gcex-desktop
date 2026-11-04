"""Ruang kerja QAQC Database DB-Ex: QAQC sampel lab (CRM, Blank, Duplikat) dan QAQC data bor (integritas Collar /
Survey / Assay / Geologi).

Rumus dan ambang mengikuti workbook QAQC pengguna (makro CRM_Run, Blank_Run, Duplicate_Run, Report_Run, Dashboard_Run)
apa adanya:
- CRM: Z = (Lab - Mean) / SD, dibulatkan 2 desimal. |Z| <= 2 PASS, 2 < |Z| <= 3 WARNING (>2SD), |Z| > 3 FAIL (>3SD).
- Blank: PASS bila hasil lab <= cut-off (bawaan 0,01), selain itu FAIL (>Cut-Off).
- Duplikat: HARD = |O - D| / (O + D); PASS bila HARD <= batas (bawaan 10 %). RPD = (O - D) / rata-rata; ARD = HARD.
  Pasangan dengan O atau D <= 0 tidak dinilai. Ringkasan per zona x kelas kadar rata-rata pasangan (<= 0,10; 0,10-0,30; > 0,30).
- Dashboard per zona: CRM >= 95 % Memuaskan, >= 90 % Memadai dengan catatan; Duplikat >= 90 % Memuaskan, >= 50 % Marginal;
  Blank >= 99 % Memuaskan, >= 95 % Memadai dengan catatan (< 30 blank & semua lolos: "Bersih, namun hanya n blank").
- Lampiran A (CRM WARNING / FAIL), B (Blank FAIL + kelipatan cut-off), C (duplikat FAIL dengan rasio maks/min >= 3 dan
  kadar maks >= 0,2).
Semua ambang dapat diubah di Panel kontrol (tersimpan per proyek).

Data per proyek: <proyek>/_GCEx_Core/qaqc/qaqc.db — tabel Master_CRM, Assay_Import, CRM_Data, Blank_Data, Duplicate_Data
(upsert per Sample_ID; duplikat per Duplicate_ID), pengaturan dan riwayat."""
from __future__ import annotations

import base64
import importlib
import io
import json
import math
import re
import sqlite3
import threading
import zipfile
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from . import core_dh, core_io

router = APIRouter(prefix="/core/qaqc")
SUB = "qaqc"

SETTINGS_DEFAULT: dict[str, Any] = {
    "zone": "ALL", "dup_type": "ALL", "element": "Au", "unit": "g/t",
    "blank_cutoff": 0.01, "hard_max": 10.0,
    "crm_good": 0.95, "crm_ok": 0.90,             # Memuaskan / Memadai dengan catatan (pass-rate CRM)
    "dup_good": 0.90, "dup_ok": 0.50,             # Memuaskan / Marginal (pass-rate duplikat)
    "blank_good": 0.99, "blank_ok": 0.95, "blank_min_n": 30,
    "class_lo": 0.10, "class_hi": 0.30,           # kelas kadar ringkasan duplikat
    "appc_ratio": 3.0, "appc_grade": 0.2,         # Lampiran C
    "dup_min_chart": 3,
    "dh_eoh_tol": 0.1, "dh_dip_jump": 10.0, "dh_azi_jump": 20.0, "dh_gap_min": 0.01,
}
SETTINGS_LABEL = {
    "zone": "Target zona (ALL = semua)", "dup_type": "Tipe duplikat (ALL / lapangan / coarse / pulp)",
    "element": "Unsur", "unit": "Satuan",
    "blank_cutoff": "Cut-off blank", "hard_max": "HARD maksimum (%)",
    "crm_good": "CRM Memuaskan bila pass-rate >=", "crm_ok": "CRM Memadai dengan catatan bila pass-rate >=",
    "dup_good": "Duplikat Memuaskan bila pass-rate >=", "dup_ok": "Duplikat Marginal bila pass-rate >=",
    "blank_good": "Blank Memuaskan bila pass-rate >=", "blank_ok": "Blank Memadai dengan catatan bila pass-rate >=",
    "blank_min_n": "Blank minimal (n) untuk dinilai penuh",
    "class_lo": "Kelas kadar duplikat: batas bawah", "class_hi": "Kelas kadar duplikat: batas atas",
    "appc_ratio": "Lampiran C: rasio maks/min >=", "appc_grade": "Lampiran C: kadar maks >=",
    "dup_min_chart": "Pasangan minimal untuk grafik duplikat",
    "dh_eoh_tol": "Data bor: toleransi kedalaman melewati EOH (m)", "dh_dip_jump": "Data bor: lompatan dip antar survey (°)",
    "dh_azi_jump": "Data bor: lompatan azimuth antar survey (°)", "dh_gap_min": "Data bor: celah interval minimum (m)",
}
TABLES = {  # nama sheet / tabel -> (tabel sqlite, kolom kunci)
    "Master_CRM": ("master_crm", "name"), "Assay_Import": ("assay_import", "sample_id"), "CRM_Data": ("crm_data", "sample_id"),
    "Blank_Data": ("blank_data", "sample_id"), "Duplicate_Data": ("dup_data", "dup_id"),
}
COLS = {  # kolom tabel (kunci, judul sheet, jenis)
    "master_crm": [("name", "Standard_Name", "s"), ("mean", "Certified_Mean", "n"), ("sd", "Certified_SD", "n"), ("supplier", "Supplier", "s"),
                   ("lot", "Lot_Number", "s")],
    "assay_import": [("batch", "Batch_ID", "s"), ("hole", "Hole_ID", "s"), ("sample_id", "Sample_ID", "s"), ("type", "Sample_Type", "s"),
                     ("grade", "Lab_Grade", "n"), ("zona", "Zona", "s")],
    "crm_data": [("sample_id", "Sample_ID", "s"), ("std", "Standard_Name", "s"), ("grade", "Lab_Grade", "n"), ("zona", "Zona", "s")],
    "blank_data": [("sample_id", "Sample_ID", "s"), ("std", "Standard_Name", "s"), ("grade", "Lab_Grade", "n"), ("zona", "Zona", "s")],
    "dup_data": [("orig_id", "Original_ID", "s"), ("dup_id", "Duplicate_ID", "s"), ("orig", "Original", "n"), ("dup", "Duplicate", "n"),
                 ("zona", "Zona", "s"), ("tipe", "Tipe", "s")],
}
ALIAS = {  # alias judul kolom (dinormalisasi) per kunci; yang lebih atas lebih diutamakan
    "name": ["standardname", "standard", "crm", "crmname", "name", "nama", "std"],
    "mean": ["certifiedmean", "certmean", "mean", "expected", "expectedvalue", "certified", "nilaisertifikat"],
    "sd": ["certifiedsd", "certsd", "sd", "stdev", "standarddeviation", "1sd"],
    "supplier": ["supplier", "pemasok", "vendor"], "lot": ["lotnumber", "lot", "lotno"],
    "batch": ["batchid", "batch", "jobno", "jobid", "labjob", "labbatch", "despatch", "dispatch"],
    "hole": ["holeid", "hole", "bhid", "dhid", "lubang"],
    "sample_id": ["sampleid", "sample", "sampleno", "samplenumber", "nosampel", "idsampel"],
    "type": ["sampletype", "type", "tipe", "qctype", "jenissampel", "jenis"],
    "grade": ["labauppm", "labgrade", "labaugt", "auppm", "augt", "au", "grade", "kadar", "result", "hasil", "lab"],
    "zona": ["zona", "zone", "pit"],
    "std": ["standardname", "standard", "crm", "crmname", "std", "name"],
    "orig_id": ["originalid", "origid", "parentid", "originalsample", "originalsampleid"],
    "dup_id": ["duplicateid", "dupid", "duplicatesampleid", "dupsampleid", "sampleid"],
    "orig": ["original", "orig", "originalgrade", "origgrade", "originalau"],
    "dup": ["duplicate", "dup", "duplicategrade", "dupgrade", "duplicateau"],
    "tipe": ["tipe", "type", "duptype", "jenis", "tipeduplikat", "duplicatetype"],
}
SHEET_ALIAS = {"master_crm": ["mastercrm", "crmmaster", "master"], "assay_import": ["assayimport", "assay", "importassay"],
               "crm_data": ["crmdata", "crm", "standard", "standards"], "blank_data": ["blankdata", "blank", "blanks"],
               "dup_data": ["duplicatedata", "dupdata", "duplicate", "duplicates", "duplikat"]}
DUP_TYPES = {"lapangan": "Lapangan", "field": "Lapangan", "fd": "Lapangan", "coarse": "Coarse", "crush": "Coarse", "crs": "Coarse",
             "pulp": "Pulp", "pd": "Pulp", "pul": "Pulp"}

_DDL = """
CREATE TABLE IF NOT EXISTS master_crm (name TEXT PRIMARY KEY, mean REAL, sd REAL, supplier TEXT, lot TEXT, seq INTEGER);
CREATE TABLE IF NOT EXISTS assay_import (sample_id TEXT PRIMARY KEY, batch TEXT, hole TEXT, type TEXT, grade REAL, zona TEXT, seq INTEGER);
CREATE TABLE IF NOT EXISTS crm_data (sample_id TEXT PRIMARY KEY, std TEXT, grade REAL, zona TEXT, seq INTEGER);
CREATE TABLE IF NOT EXISTS blank_data (sample_id TEXT PRIMARY KEY, std TEXT, grade REAL, zona TEXT, seq INTEGER);
CREATE TABLE IF NOT EXISTS dup_data (dup_id TEXT PRIMARY KEY, orig_id TEXT, orig REAL, dup REAL, zona TEXT, tipe TEXT, seq INTEGER);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, by TEXT, what TEXT, detail TEXT);
"""


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.db = root / "qaqc.db"
        self.lock = threading.RLock()
        self.cache: dict = {}

    @contextmanager
    def conn(self):
        c = sqlite3.connect(str(self.db), timeout=30)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()


_STORES: dict[str, Store] = {}
_SLOCK = threading.Lock()


def store(folder: str) -> Store:
    p = core_io.get_project(folder)
    root = p.db.parent / SUB
    key = str(root).lower()
    with _SLOCK:
        s = _STORES.get(key)
        if s and s.db.exists():
            return s
        root.mkdir(parents=True, exist_ok=True)
        s = Store(root)
        with s.conn() as c:
            c.executescript(_DDL)
        _STORES[key] = s
        return s


def _hist(c, what: str, detail: str, by: str) -> None:
    c.execute("INSERT INTO history (at, by, what, detail) VALUES (?,?,?,?)", (core_io.now(), by, what, detail[:4000]))


# ---------------------------------------------------------------- utilitas (setara Mod_Utils)
def norm(h: Any) -> str:
    return re.sub(r"[^0-9a-z]", "", str(h or "").lower())


def extract_zone(s: Any) -> str:
    """Kode zona (Z2, Z4, ...) dari Sample ID: huruf Z pertama yang diikuti angka. Tidak ada -> UNKNOWN."""
    m = re.search(r"Z\d+", str(s or "").upper())
    return m.group(0) if m else "UNKNOWN"


def round_js(x: float) -> float:
    return math.floor(x + 0.5)


def num(v: Any) -> Optional[float]:
    x, ok = core_dh._num(v)
    return x if ok else None


def txt(v: Any) -> str:
    t = core_dh._txt(v)
    return t or ""


def g(x: Optional[float], d: int = 4) -> str:
    return "" if x is None else f"{x:.{d}f}".rstrip("0").rstrip(".") if d else f"{x:.0f}"


def settings(s: Store) -> dict:
    out = dict(SETTINGS_DEFAULT)
    with s.conn() as c:
        for r in c.execute("SELECT key, value FROM settings"):
            if r["key"] in out:
                try:
                    out[r["key"]] = json.loads(r["value"])
                except ValueError:
                    pass
    return out


def save_settings(s: Store, values: dict, by: str) -> dict:
    cur = settings(s)
    with s.lock, s.conn() as c:
        for k, v in (values or {}).items():
            if k not in SETTINGS_DEFAULT:
                continue
            d = SETTINGS_DEFAULT[k]
            if isinstance(d, (int, float)) and not isinstance(d, bool):
                x = num(v)
                if x is None:
                    raise ValueError(f"{SETTINGS_LABEL.get(k, k)}: harus angka.")
                v = int(x) if isinstance(d, int) else float(x)
            else:
                v = str(v or "").strip() or d
                if k in ("zone", "dup_type"):
                    v = v.upper() if v.upper() in ("ALL", "SEMUA") else v
            if cur.get(k) != v:
                _hist(c, f"panel kontrol {k}", f"{cur.get(k)} -> {v}", by)
            c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (k, json.dumps(v)))
    s.cache.clear()
    return settings(s)


# ---------------------------------------------------------------- impor
def _find_cols(headers: list, keys: list[str]) -> dict[str, int]:
    """Kolom per kunci dari judul (alias persis dulu, lalu awalan)."""
    hn = [norm(h) for h in headers]
    out: dict[str, int] = {}
    used: set[int] = set()
    for k in keys:
        for a in ALIAS[k]:
            i = next((j for j, h in enumerate(hn) if h == a and j not in used), None)
            if i is not None:
                out[k] = i
                used.add(i)
                break
    for k in keys:
        if k in out:
            continue
        for a in ALIAS[k]:
            if len(a) < 4:
                continue
            i = next((j for j, h in enumerate(hn) if h.startswith(a) and j not in used), None)
            if i is not None:
                out[k] = i
                used.add(i)
                break
    return out


def _header_row(rows: list[list], keys: list[str]) -> int:
    best, bi = 0, 0
    for i, r in enumerate(rows[:15]):
        n = len(_find_cols(list(r), keys))
        if n > best:
            best, bi = n, i
    return bi


REQUIRED = {"master_crm": ["name", "mean", "sd"], "assay_import": ["sample_id"], "crm_data": ["sample_id", "std", "grade"],
            "blank_data": ["sample_id", "grade"], "dup_data": ["orig_id", "dup_id", "orig", "dup"]}


def guess_table(name: str, headers: list) -> Optional[str]:
    """Jenis tabel dari nama sheet / file, atau dari judul kolom."""
    n = norm(Path(name).stem)
    for t, al in SHEET_ALIAS.items():
        if n in al or any(n.startswith(a) for a in al if len(a) >= 6):
            return t
    hn = {norm(h) for h in headers}
    if hn & {"originalid", "duplicateid"}:
        return "dup_data"
    if hn & {"certifiedmean", "certmean"}:
        return "master_crm"
    if hn & {"batchid"} and hn & {"sampletype"}:
        return "assay_import"
    return None


def upsert(s: Store, table: str, rows: list[list], header_row: int, by: str, label: str = "") -> dict:
    keys = [k for k, _h, _t in COLS[table]]
    cols = _find_cols(list(rows[header_row]), keys)
    miss = [k for k in REQUIRED[table] if k not in cols]
    if miss:
        lab = {k: h for k, h, _t in COLS[table]}
        raise ValueError(f"{label or table}: kolom {', '.join(lab[m] for m in miss)} tidak ditemukan di baris judul.")
    pk = dict((v[0], v[1]) for v in TABLES.values())[table]
    typ = {k: t for k, _h, t in COLS[table]}
    rep = {"table": table, "rows": 0, "new": 0, "updated": 0, "skipped": 0, "reasons": {}}
    recs = []
    for r in rows[header_row + 1:]:
        if not any(v not in (None, "") for v in r):
            continue
        rec = {}
        for k in keys:
            i = cols.get(k)
            v = r[i] if i is not None and i < len(r) else None
            rec[k] = num(v) if typ[k] == "n" else txt(v)
        if table == "dup_data" and not rec.get("dup_id") and rec.get("orig_id"):
            rec["dup_id"] = rec["orig_id"] + "|DUP"  # duplikat tanpa Duplicate_ID: kunci dari Original_ID
            rep["nokey_fixed"] = rep.get("nokey_fixed", 0) + 1
        if not rec.get(pk):
            rep["skipped"] += 1
            rep["reasons"]["kunci kosong"] = rep["reasons"].get("kunci kosong", 0) + 1
            continue
        if table == "assay_import" and not rec.get("zona"):
            rec["zona"] = (rec.get("hole") or "")[:2].upper() if re.match(r"^Z\d", rec.get("hole") or "", re.I) else ""
        if table == "dup_data" and rec.get("tipe"):
            rec["tipe"] = DUP_TYPES.get(norm(rec["tipe"]), rec["tipe"])
        recs.append(rec)
    seen: dict[str, int] = {}
    for rec in recs:
        seen[rec[pk]] = seen.get(rec[pk], 0) + 1
    dups = {k: v for k, v in seen.items() if v > 1}
    if dups:  # ID ganda di file: baris terakhir yang dipakai (upsert per ID)
        rep["dup_keys"] = sum(v - 1 for v in dups.values())
        rep["dup_examples"] = sorted(dups)[:8]
    with s.lock, s.conn() as c:
        have = {r[0] for r in c.execute(f"SELECT {pk} FROM {table}")}
        old_keys = set(have)
        upd: set = set()
        seq = (c.execute(f"SELECT MAX(seq) FROM {table}").fetchone()[0] or 0)
        for rec in recs:
            if rec[pk] in have:
                if rec[pk] in old_keys and rec[pk] not in upd:
                    rep["updated"] += 1  # ID sama dalam file yang sama dihitung sekali
                upd.add(rec[pk])
                sets = ", ".join(f"{k}=?" for k in keys if k != pk and k in cols)
                if sets:
                    c.execute(f"UPDATE {table} SET {sets} WHERE {pk}=?", [rec[k] for k in keys if k != pk and k in cols] + [rec[pk]])
            else:
                seq += 1
                c.execute(f"INSERT INTO {table} ({', '.join(keys)}, seq) VALUES ({', '.join('?' for _ in keys)}, ?)",
                          [rec.get(k) for k in keys] + [seq])
                have.add(rec[pk])
                rep["new"] += 1
        rep["rows"] = len(recs)
        _hist(c, f"impor {table}", f"{label}: {rep['new']} baru, {rep['updated']} diperbarui, {rep['skipped']} dilewati"
              + (f", {rep['dup_keys']} ID ganda dalam file" if rep.get("dup_keys") else ""), by)
    s.cache.clear()
    return rep


def import_file(s: Store, path: str, target: str, by: str, sheet: Optional[str] = None) -> list[dict]:
    """Impor file: workbook QAQC (semua sheet yang dikenali: Master_CRM, Assay_Import, CRM_Data, Blank_Data,
    Duplicate_Data) bila target 'auto', atau satu tabel ke target tertentu. Upsert per Sample_ID / Duplicate_ID."""
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"File tidak ditemukan: {path}")
    out = []
    if p.suffix.lower() in (".xlsx", ".xlsm") and target == "auto" and not sheet:
        from openpyxl import load_workbook
        wb = load_workbook(str(p), read_only=True, data_only=True)
        try:
            order = ["master_crm", "assay_import", "crm_data", "blank_data", "dup_data"]
            found: dict[str, str] = {}
            for name in wb.sheetnames:
                t = guess_table(name, [])
                if t and t not in found and norm(name) in SHEET_ALIAS[t]:
                    found[t] = name
            if not found:
                ws = wb[wb.sheetnames[0]]
                rows = [list(r) for r in ws.iter_rows(values_only=True)]
                t = guess_table(p.name, rows[0] if rows else [])
                if not t:
                    raise ValueError("Sheet Master_CRM / Assay_Import / CRM_Data / Blank_Data / Duplicate_Data tidak ditemukan. "
                                     "Pilih jenis tabel tujuan secara manual.")
                found[t] = ws.title
            for t in order:
                if t not in found:
                    continue
                rows = [list(r) for r in wb[found[t]].iter_rows(values_only=True)]
                if not rows:
                    continue
                keys = [k for k, _h, _t in COLS[t]]
                out.append(dict(upsert(s, t, rows, _header_row(rows, keys), by, f"{p.name} › {found[t]}"), sheet=found[t]))
        finally:
            wb.close()
        return out
    _sheets, used, rows = core_dh.read_table(str(p), None, p.name, sheet)
    if not rows:
        raise ValueError(f"{p.name}: file kosong.")
    t = target if target in COLS else guess_table(used or p.name, rows[_header_row(rows, sum((v for v in ALIAS.values()), []))] if rows else [])
    if t not in COLS:
        raise ValueError(f"{p.name}: jenis tabel tidak dikenali. Pilih tabel tujuan (Master_CRM, Assay_Import, CRM_Data, Blank_Data, "
                         "Duplicate_Data).")
    keys = [k for k, _h, _t in COLS[t]]
    return [dict(upsert(s, t, rows, _header_row(rows, keys), by, p.name + (f" › {used}" if used else "")), sheet=used)]


def table_rows(s: Store, table: str) -> list[dict]:
    pk = dict((v[0], v[1]) for v in TABLES.values())[table]
    with s.conn() as c:
        return [dict(r) for r in c.execute(f"SELECT * FROM {table} ORDER BY seq, {pk}")]


def counts(s: Store) -> dict:
    with s.conn() as c:
        return {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t, _k in TABLES.values()}


def save_master(s: Store, rows: list[dict], by: str) -> list[dict]:
    """Simpan seluruh Master_CRM dari tabel di layar (nama kosong dibuang)."""
    clean = []
    for i, r in enumerate(rows, 1):
        nm = str(r.get("name") or "").strip()
        if not nm:
            continue
        m, sd = num(r.get("mean")), num(r.get("sd"))
        if m is None or sd is None or sd <= 0:
            raise ValueError(f"Master_CRM baris {i} ({nm}): Certified_Mean dan Certified_SD harus angka, SD > 0.")
        clean.append((nm, m, sd, str(r.get("supplier") or "").strip(), str(r.get("lot") or "").strip(), i))
    if len({x[0] for x in clean}) != len(clean):
        raise ValueError("Ada Standard_Name ganda di Master_CRM.")
    with s.lock, s.conn() as c:
        c.execute("DELETE FROM master_crm")
        c.executemany("INSERT INTO master_crm VALUES (?,?,?,?,?,?)", clean)
        _hist(c, "Master_CRM disimpan", f"{len(clean)} CRM", by)
    s.cache.clear()
    return table_rows(s, "master_crm")


EDITABLE = ("assay_import", "crm_data", "blank_data", "dup_data")


def save_table(s: Store, table: str, rows: list[dict], by: str) -> dict:
    """Simpan seluruh isi satu tabel data mentah dari tabel di layar (input manual / tempel dari Excel).

    Baris kosong dibuang. Kunci (Sample_ID; Duplicate_ID untuk duplikat) wajib dan tidak boleh ganda; kolom angka wajib angka
    (koma desimal dan "<0.01" diterima seperti saat impor). Bila ada galat, TIDAK ada yang disimpan dan galat per sel
    dikembalikan (ok False). Urutan baris di layar menjadi urutan insersi (seq) untuk grafik kontrol."""
    if table not in EDITABLE:
        raise ValueError("Tabel ini tidak bisa diedit di sini.")
    keys = [k for k, _h, _t in COLS[table]]
    head = {k: h for k, h, _t in COLS[table]}
    typ = {k: t for k, _h, t in COLS[table]}
    pk = dict((v[0], v[1]) for v in TABLES.values())[table]
    req = REQUIRED[table]
    errs: list[dict] = []
    recs: list[tuple[int, dict]] = []
    for i, r in enumerate(rows):
        raw = {k: r.get(k) for k in keys}
        if not any(str(v if v is not None else "").strip() for v in raw.values()):
            continue
        rec = {}
        for k in keys:
            v = raw[k]
            if typ[k] == "n":
                sv = str(v if v is not None else "").strip()
                x = num(sv) if sv else None
                if sv and x is None:
                    errs.append({"row": i, "col": k, "msg": f"{head[k]} bukan angka: {sv}"})
                rec[k] = x
            else:
                rec[k] = txt(v)
        if table == "dup_data" and not rec.get("dup_id") and rec.get("orig_id"):
            rec["dup_id"] = rec["orig_id"] + "|DUP"
        if table == "dup_data" and rec.get("tipe"):
            rec["tipe"] = DUP_TYPES.get(norm(rec["tipe"]), rec["tipe"])
        for k in req:
            if rec.get(k) in (None, "") and not any(e["row"] == i and e["col"] == k for e in errs):
                errs.append({"row": i, "col": k, "msg": f"{head[k]} wajib diisi"})
        recs.append((i, rec))
    first: dict[str, int] = {}
    for i, rec in recs:
        key = rec.get(pk)
        if not key:
            continue
        ku = key.upper()  # Z7-001 dan z7-001 dianggap sama
        if ku in first:
            errs.append({"row": i, "col": pk, "msg": f"{head[pk]} {key} ganda (juga di baris {first[ku] + 1})"})
        else:
            first[ku] = i
    if errs:
        return {"ok": False, "errors": errs}
    warns = []
    with s.lock, s.conn() as c:
        old = {r[pk]: dict(r) for r in c.execute(f"SELECT * FROM {table}")}
        if table in ("crm_data", "blank_data"):  # satu sampel tidak mungkin sekaligus CRM dan blank
            other = "blank_data" if table == "crm_data" else "crm_data"
            ids = {rec["sample_id"].upper(): rec["sample_id"] for _i, rec in recs}
            both = sorted(ids[u] for u in set(ids) & {str(r[0]).upper() for r in c.execute(f"SELECT sample_id FROM {other}")})
            if both:
                warns.append(f"{len(both)} Sample_ID juga ada di {'Blank_Data' if other == 'blank_data' else 'CRM_Data'}: "
                             + ", ".join(both[:5]) + (" …" if len(both) > 5 else ""))
        if table == "crm_data":
            ms = {r[0] for r in c.execute("SELECT name FROM master_crm")}
            nomaster = sorted({rec["std"] for _i, rec in recs if rec.get("std") and rec["std"] not in ms})
            if nomaster:
                warns.append("Standard_Name belum ada di Master_CRM (tidak dinilai): " + ", ".join(nomaster[:6]))
        new = sum(1 for _i, rec in recs if rec[pk] not in old)
        upd = sum(1 for _i, rec in recs if rec[pk] in old and any(_diff(old[rec[pk]].get(k), rec.get(k)) for k in keys))
        dele = len({k.upper() for k in old} - set(first))
        c.execute(f"DELETE FROM {table}")
        c.executemany(f"INSERT INTO {table} ({', '.join(keys)}, seq) VALUES ({', '.join('?' for _ in keys)}, ?)",
                      [[rec.get(k) for k in keys] + [n] for n, (_i, rec) in enumerate(recs, 1)])
        _hist(c, f"edit manual {table}", f"{len(recs)} baris: {new} baru, {upd} diubah, {dele} dihapus", by)
    s.cache.clear()
    return {"ok": True, "n": len(recs), "new": new, "updated": upd, "deleted": dele, "warnings": warns, "counts": counts(s)}


def _diff(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) or isinstance(b, (int, float)):
        if a is None or b is None:
            return a is not b
        return abs(float(a) - float(b)) > 1e-12
    return (a or "") != (b or "")


def clear_table(s: Store, table: str, by: str) -> None:
    if table not in COLS:
        raise ValueError("Tabel tidak dikenal.")
    with s.lock, s.conn() as c:
        n = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        c.execute(f"DELETE FROM {table}")
        _hist(c, f"kosongkan {table}", f"{n} baris dihapus", by)
    s.cache.clear()


# ---------------------------------------------------------------- analisis (setara Mod_CRM, Mod_Blank, Mod_Duplicate,
# Mod_Report, Mod_Dashboard)
def _sd(xs: list[float]) -> float:
    n = len(xs)
    if n == 0:
        return 0.0
    m = sum(xs) / n
    ss = sum((x - m) ** 2 for x in xs)
    return math.sqrt(ss / (n - 1)) if n > 1 else math.sqrt(ss)


def r_squared(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n == 0:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    num_ = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = sum((a - mx) ** 2 for a in x)
    dy = sum((b - my) ** 2 for b in y)
    return 0.0 if dx == 0 or dy == 0 else (num_ / math.sqrt(dx * dy)) ** 2


def r2_label(r2: float) -> str:
    if r2 >= 0.95:
        return "Sangat Baik (Korelasi Kuat / Presisi Tinggi)"
    if r2 >= 0.85:
        return "Baik (Korelasi Cukup Kuat)"
    if r2 >= 0.7:
        return "Cukup (Presisi Sedang)"
    return "Kurang (Presisi Rendah)"


def _pct(p: float) -> str:
    return f"{p * 100:.1f}%"


def assess(kind: str, p: int, w: int, f: int, st: dict) -> tuple[str, int]:
    """Penilaian per zona -> (teks, level 0 tidak ada / 1 memuaskan / 2 catatan / 3 tidak memuaskan)."""
    nn = p + w + f
    lab = {"crm": "CRM", "dup": "duplikat", "blank": "blank"}[kind]
    if nn == 0:
        return f"Tidak ada data {lab}", 0
    q = p / nn
    tail = f" — {_pct(q)} PASS ({p}/{nn})"
    if kind == "crm":
        if q >= st["crm_good"]:
            return "Memuaskan" + tail, 1
        if q >= st["crm_ok"]:
            return "Memadai dengan catatan" + tail, 2
        return "Tidak memuaskan" + tail, 3
    if kind == "dup":
        if q >= st["dup_good"]:
            return "Memuaskan" + tail, 1
        if q >= st["dup_ok"]:
            return "Marginal" + tail, 2
        return "Tidak memuaskan" + tail, 3
    if nn < st["blank_min_n"] and q == 1:
        return f"Bersih, namun hanya {nn} blank", 2
    if q >= st["blank_good"]:
        return "Memuaskan" + tail, 1
    if q >= st["blank_ok"]:
        return "Memadai dengan catatan" + tail, 2
    return "Tidak memuaskan" + tail, 3


def overall(crm_lvl: int, dup_lvl: int, blk_lvl: int) -> tuple[str, int]:
    if 3 in (crm_lvl, dup_lvl, blk_lvl):
        return "Perlu tindakan korektif", 3
    if crm_lvl == 0 or dup_lvl == 0:
        return "Tidak dapat dinilai", 0
    if 2 in (crm_lvl, dup_lvl, blk_lvl):
        return "Memadai dengan catatan", 2
    return "Memuaskan", 1


def _zone_ok(z: str, st: dict) -> bool:
    t = str(st.get("zone") or "ALL").upper()
    return t in ("ALL", "SEMUA", "") or z.upper() == t


def analyze(s: Store) -> dict:
    """Hitung seluruh QAQC dari tabel tersimpan + panel kontrol. Hasil disimpan di cache sampai data / pengaturan berubah."""
    if "res" in s.cache:
        return s.cache["res"]
    st = settings(s)
    master = {r["name"]: r for r in table_rows(s, "master_crm")}
    batch = {r["sample_id"]: (r["batch"] or "") for r in table_rows(s, "assay_import")}
    batch_of = lambda sid: batch.get(sid) or "N/A"  # noqa: E731
    warn: list[str] = []

    # ---- CRM
    crm = []
    no_master: dict[str, int] = {}
    for r in table_rows(s, "crm_data"):
        sid, std, lab = r["sample_id"], (r["std"] or "").strip(), r["grade"]
        z_ = extract_zone(sid)
        if z_ == "UNKNOWN" and r["zona"]:
            z_ = r["zona"].upper()
        if not _zone_ok(z_, st):
            continue
        rec = {"sample_id": sid, "std": std, "grade": lab, "zona": z_, "seq": r["seq"], "batch": batch_of(sid),
               "mean": None, "sd": None, "status": "", "cat": "", "z": None}
        m = master.get(std)
        if m is None:
            no_master[std or "(kosong)"] = no_master.get(std or "(kosong)", 0) + 1
        else:
            rec["mean"], rec["sd"] = m["mean"], m["sd"]
            if lab is not None and m["sd"] and m["sd"] > 0:
                z = round_js(((lab - m["mean"]) / m["sd"]) * 100) / 100
                az = abs(z)
                rec["z"] = z
                rec["status"], rec["cat"] = ("FAIL (>3SD)", "FAIL") if az > 3 else (("WARNING (>2SD)", "WARN") if az > 2 else ("PASS", "PASS"))
        crm.append(rec)
    if no_master:
        warn.append("CRM tanpa data di Master_CRM (tidak dinilai): " + ", ".join(f"{k} ({v})" for k, v in sorted(no_master.items())))
    crm.sort(key=lambda r: (r["zona"], r["seq"]))  # setara sort CRM_Data per Zona
    groups: dict[str, dict] = {}
    for r in sorted((r for r in crm if r["cat"]), key=lambda r: r["seq"]):
        k = f"{r['zona']}||{r['std']}"
        gg = groups.setdefault(k, {"key": k, "zona": r["zona"], "std": r["std"], "mean": r["mean"], "sd": r["sd"], "rows": []})
        gg["rows"].append(r)
    crm_sum = []
    tot = {"n": 0, "P": 0, "W": 0, "F": 0}
    for k in sorted(groups):
        gg = groups[k]
        labs = [r["grade"] for r in gg["rows"]]
        n = len(labs)
        mean_lab = sum(labs) / n
        sdl = _sd(labs)
        c = {x: sum(1 for r in gg["rows"] if r["cat"] == y) for x, y in (("P", "PASS"), ("W", "WARN"), ("F", "FAIL"))}
        crm_sum.append({"zona": gg["zona"], "crm": gg["std"], "n": n, "mean_lab": round(mean_lab, 4), "certified": gg["mean"],
                        "bias": (mean_lab - gg["mean"]) / gg["mean"] if gg["mean"] else None,
                        "sd_text": f"{sdl:.4f} vs {gg['sd']:g}", "sd_lab": sdl, "cert_sd": gg["sd"], "cv": sdl / mean_lab if mean_lab else None,
                        "pass": c["P"], "warn": c["W"], "fail": c["F"],
                        "pwf": f"{c['P']} / {c['W']} / {c['F']} ({c['P'] / n * 100:.1f}% PASS)"})
        gg["n"], gg["pass"], gg["warn"], gg["fail"] = n, c["P"], c["W"], c["F"]
        tot["n"] += n
        for x in "PWF":
            tot[x] += c[x]
    crm_total = ({"zona": "ALL ZONES", "crm": "Total", "n": tot["n"], "pass": tot["P"], "warn": tot["W"], "fail": tot["F"],
                  "pwf": f"{tot['P']} / {tot['W']} / {tot['F']} ({tot['P'] / tot['n'] * 100:.1f}% PASS)"} if tot["n"] else None)

    # ---- Blank
    cut = float(st["blank_cutoff"])
    blank = []
    for r in table_rows(s, "blank_data"):
        sid, lab = r["sample_id"], r["grade"]
        z_ = extract_zone(sid)
        if z_ == "UNKNOWN" and r["zona"]:
            z_ = r["zona"].upper()
        if not sid or lab is None or not _zone_ok(z_, st):
            continue
        ok = lab <= cut
        blank.append({"sample_id": sid, "std": r["std"] or "Blank", "grade": lab, "zona": z_, "seq": r["seq"], "batch": batch_of(sid),
                      "status": "PASS" if ok else "FAIL (>Cut-Off)", "cat": "PASS" if ok else "FAIL", "ratio": lab / cut if cut > 0 else None})
    bzones: dict[str, dict] = {}
    for r in blank:
        b = bzones.setdefault(r["zona"], {"zona": r["zona"], "n": 0, "fail": 0, "max": 0.0})
        b["n"] += 1
        b["fail"] += r["cat"] == "FAIL"
        b["max"] = max(b["max"], r["grade"])
    blank_sum = [dict(v, pass_=v["n"] - v["fail"], rate=(v["n"] - v["fail"]) / v["n"]) for _k, v in sorted(bzones.items())]

    # ---- Duplikat
    hmax = float(st["hard_max"]) if num(st["hard_max"]) and float(st["hard_max"]) > 0 else 10.0
    ttype = str(st.get("dup_type") or "ALL").upper()
    dup, invalid = [], 0
    for r in table_rows(s, "dup_data"):
        zz = (r["zona"] or "").strip().upper()
        if zz in ("", "N/A"):
            zz = extract_zone(r["orig_id"])
            if zz == "UNKNOWN":
                zz = "ALL"
        tp = (r["tipe"] or "").strip() or "Tidak Ditentukan"
        if not _zone_ok(zz, st) or (ttype not in ("ALL", "SEMUA") and tp.upper() != ttype):
            continue
        o, d = r["orig"], r["dup"]
        rec = {"orig_id": r["orig_id"], "dup_id": r["dup_id"], "orig": o, "dup": d, "zona": zz, "tipe": tp, "seq": r["seq"],
               "batch": batch.get(r["dup_id"]) or batch.get(r["orig_id"]) or "N/A", "status": "", "cat": "",
               "hard": None, "rpd": None, "mean": None}
        if o is not None and d is not None and o > 0 and d > 0:
            mg = (o + d) / 2
            hard = abs(o - d) / (o + d) * 100
            rpd = (o - d) / mg * 100
            ok = hard <= hmax
            rec.update({"mean": mg, "hard": hard / 100, "rpd": rpd / 100, "ard": hard / 100,
                        "status": "PASS" if ok else f"FAIL (>{hmax:g}%)", "cat": "PASS" if ok else "FAIL"})
        else:
            invalid += 1
        dup.append(rec)
    if invalid:
        warn.append(f"{invalid} pasangan duplikat tidak dinilai (Original / Duplicate kosong atau <= 0).")
    valid = [r for r in dup if r["cat"]]
    dstat = None
    if valid:
        r2 = r_squared([r["orig"] for r in valid], [r["dup"] for r in valid])
        dstat = {"n": len(valid), "r2": r2, "r2_label": r2_label(r2), "avg_rpd": sum(r["rpd"] for r in valid) / len(valid) * 100,
                 "avg_ard": sum(r["hard"] for r in valid) / len(valid) * 100}
    dgroups = []
    keys = sorted({f"{r['zona']}||{r['tipe']}" for r in valid})
    for k in keys:
        rows = [r for r in valid if f"{r['zona']}||{r['tipe']}" == k]
        if len(rows) < int(st["dup_min_chart"]):
            continue
        ok = sum(1 for r in rows if r["cat"] == "PASS")
        dgroups.append({"key": k, "zona": rows[0]["zona"], "tipe": rows[0]["tipe"], "n": len(rows), "pass": ok,
                        "r2": r_squared([r["orig"] for r in rows], [r["dup"] for r in rows]),
                        "avg_rpd": sum(r["rpd"] for r in rows) / len(rows), "rows": rows})
    lo, hi = float(st["class_lo"]), float(st["class_hi"])
    cname = [f"≤ {lo:.2f} {st['unit']}", f"{lo:.2f} – {hi:.2f} {st['unit']}", f"> {hi:.2f} {st['unit']}"]
    dsum = []
    for zz in sorted({r["zona"] for r in valid}):
        rows = [r for r in valid if r["zona"] == zz]
        for ci in range(3):
            cr = [r for r in rows if (r["mean"] <= lo if ci == 0 else (lo < r["mean"] <= hi if ci == 1 else r["mean"] > hi))]
            n_ = len(cr)
            p_ = sum(1 for r in cr if r["cat"] == "PASS")
            dsum.append({"zona": zz, "kelas": cname[ci], "n": n_, "pass": p_, "rate": p_ / n_ if n_ else 0.0,
                         "hard": sum(r["hard"] for r in cr) / n_ if n_ else 0.0, "row": "kelas"})
        p_ = sum(1 for r in rows if r["cat"] == "PASS")
        dsum.append({"zona": zz, "kelas": f"Total Zona {zz}", "n": len(rows), "pass": p_, "rate": p_ / len(rows),
                     "hard": sum(r["hard"] for r in rows) / len(rows), "row": "zona"})
    if valid:
        p_ = sum(1 for r in valid if r["cat"] == "PASS")
        dsum.append({"zona": "ALL ZONES", "kelas": "Total Semua Pair", "n": len(valid), "pass": p_, "rate": p_ / len(valid),
                     "hard": sum(r["hard"] for r in valid) / len(valid), "row": "total"})

    # ---- Dashboard per zona
    zones = sorted({r["zona"] for r in crm if r["cat"]} | {r["zona"] for r in blank} | {r["zona"] for r in valid})
    dash = []
    for zz in zones:
        cp = [r for r in crm if r["zona"] == zz and r["cat"]]
        bp = [r for r in blank if r["zona"] == zz]
        dp = [r for r in valid if r["zona"] == zz]
        ct, cl = assess("crm", sum(r["cat"] == "PASS" for r in cp), sum(r["cat"] == "WARN" for r in cp), sum(r["cat"] == "FAIL" for r in cp), st)
        dt, dl = assess("dup", sum(r["cat"] == "PASS" for r in dp), 0, sum(r["cat"] == "FAIL" for r in dp), st)
        bt, bl = assess("blank", sum(r["cat"] == "PASS" for r in bp), 0, sum(r["cat"] == "FAIL" for r in bp), st)
        ot, ol = overall(cl, dl, bl)
        dash.append({"zona": zz, "crm": ct, "crm_lvl": cl, "dup": dt, "dup_lvl": dl, "blank": bt, "blank_lvl": bl, "overall": ot, "overall_lvl": ol})
    totals = {"crm": {k: sum(r["cat"] == k for r in crm) for k in ("PASS", "WARN", "FAIL")},
              "blank": {k: sum(r["cat"] == k for r in blank) for k in ("PASS", "FAIL")},
              "dup": {k: sum(r["cat"] == k for r in valid) for k in ("PASS", "FAIL")}}

    # ---- Lampiran
    app_a = [r for r in crm if r["cat"] in ("WARN", "FAIL")]
    app_b = [r for r in blank if r["cat"] == "FAIL"]
    app_c = []
    for r in valid:
        if r["cat"] != "FAIL":
            continue
        mx, mn = max(r["orig"], r["dup"]), min(r["orig"], r["dup"])
        ratio = mx / mn if mn > 0 else 0
        if ratio >= float(st["appc_ratio"]) and mx >= float(st["appc_grade"]):
            app_c.append(dict(r, ratio=ratio, batch=batch.get(r["orig_id"]) or "N/A"))

    # ---- Ringkasan per batch lab
    bt: dict[str, dict] = {}

    def b(k):
        return bt.setdefault(k, {"batch": k, "crm": 0, "crm_warn": 0, "crm_fail": 0, "blank": 0, "blank_fail": 0, "dup": 0, "dup_fail": 0, "zones": set()})
    for r in crm:
        if r["cat"]:
            x = b(r["batch"])
            x["crm"] += 1
            x["crm_warn"] += r["cat"] == "WARN"
            x["crm_fail"] += r["cat"] == "FAIL"
            x["zones"].add(r["zona"])
    for r in blank:
        x = b(r["batch"])
        x["blank"] += 1
        x["blank_fail"] += r["cat"] == "FAIL"
        x["zones"].add(r["zona"])
    for r in valid:
        x = b(r["batch"])
        x["dup"] += 1
        x["dup_fail"] += r["cat"] == "FAIL"
        x["zones"].add(r["zona"])
    batches = []
    for k in sorted(bt, key=lambda k: (k == "N/A", k)):
        x = bt[k]
        stt = "FAIL" if x["crm_fail"] or x["blank_fail"] else ("WARNING" if x["crm_warn"] or x["dup_fail"] else "PASS")
        batches.append(dict(x, zones=", ".join(sorted(x["zones"])), status=stt))

    res = {"settings": st, "crm": crm, "crm_groups": [{k: v for k, v in gg.items()} for _k, gg in sorted(groups.items())],
           "crm_summary": crm_sum, "crm_total": crm_total, "blank": blank, "blank_summary": blank_sum, "dup": dup, "dup_valid": len(valid),
           "dup_groups": dgroups, "dup_summary": dsum, "dup_stat": dstat, "dashboard": dash, "totals": totals,
           "app_a": app_a, "app_b": app_b, "app_c": app_c, "batches": batches, "warnings": warn, "counts": counts(s),
           "zones": zones, "dup_types": sorted({(r["tipe"] or "").strip() for r in table_rows(s, "dup_data") if (r["tipe"] or "").strip()})}
    s.cache["res"] = res
    return res


def light(lvl: int) -> str:
    return {1: "HIJAU", 2: "KUNING", 3: "MERAH"}.get(lvl, "ABU-ABU")


# ---------------------------------------------------------------- QAQC data bor (integritas Collar / Survey / Assay / Geologi)
SEV_ORDER = {"MERAH": 0, "KUNING": 1, "INFO": 2}


def dh_checks(folder: str, st: Optional[dict] = None) -> dict:
    """Pemeriksaan struktur data bor yang sudah diimpor DB-Ex (tombol Data bor). Kesalahan keras (MERAH) harus diperbaiki di
    database sumber sebelum komposit / estimasi; KUNING perlu diperiksa; INFO sebagai catatan."""
    p = core_io.get_project(folder)
    core_dh.ensure(p)
    st = st or dict(SETTINGS_DEFAULT)
    tol, djump, ajump, gapmin = (float(st[k]) for k in ("dh_eoh_tol", "dh_dip_jump", "dh_azi_jump", "dh_gap_min"))
    with p.conn() as c:
        col = {r[1]: {"hole": r[0], "x": r[2], "y": r[3], "z": r[4], "depth": r[5], "dip": r[6], "azi": r[7]}
               for r in c.execute("SELECT hole, hole_key, x, y, z, depth, dip, azi FROM dh_collar")}
        sv: dict[str, list] = {}
        for h, hk, at, dip, azi in c.execute("SELECT hole, hole_key, at, dip, azi FROM dh_survey ORDER BY hole_key, at"):
            sv.setdefault(hk, []).append((h, at, dip, azi))
        iv: dict[str, dict[str, list]] = {"assay": {}, "geology": {}}
        for kind, h, hk, f, t, a in c.execute("SELECT kind, hole, hole_key, f, t, attrs FROM dh_int ORDER BY kind, hole_key, f, t"):
            iv.setdefault(kind, {}).setdefault(hk, []).append((h, f, t, json.loads(a or "{}")))
    issues: list[dict] = []

    def add(code, check, sev, hole, item, detail):
        issues.append({"code": code, "check": check, "severity": sev, "hole": hole, "item": item, "detail": detail})
    for hk, cc in col.items():
        if cc["depth"] is None:
            add("C2", "Collar tanpa EOH (total depth)", "KUNING", cc["hole"], "", "Kedalaman akhir lubang kosong; batas EOH tidak bisa diperiksa")
        if cc["x"] == 0 or cc["y"] == 0:
            add("C1", "Koordinat collar nol", "MERAH", cc["hole"], "", f"X={cc['x']}, Y={cc['y']}")
    for hk, rows in sv.items():
        hole = rows[0][0]
        cc = col.get(hk)
        if cc is None:
            add("S1", "Survey tanpa collar", "MERAH", hole, "", f"{len(rows)} stasiun survey, Hole ID tidak ada di Collar")
        neg = sum(1 for r in rows if r[2] < 0) >= sum(1 for r in rows if r[2] > 0)
        for i, (_h, at, dip, azi) in enumerate(rows):
            if dip != 0 and (dip > 0) == neg:
                add("S2", "Tanda dip terbalik", "MERAH", hole, f"{at:g} m", f"Dip = {dip:+g} sementara stasiun lain {'negatif' if neg else 'positif'}")
            if cc and cc["depth"] is not None and at > cc["depth"] + tol:
                add("S3", "Survey melewati EOH", "KUNING", hole, f"{at:g} m", f"EOH {cc['depth']:g} m")
            if i:
                pa, pd, pz = rows[i - 1][1], rows[i - 1][2], rows[i - 1][3]
                if abs(at - pa) < 1e-6:
                    add("S4", "Stasiun survey ganda", "KUNING", hole, f"{at:g} m", "Dua stasiun pada kedalaman yang sama")
                dz = abs((azi - pz + 180) % 360 - 180)
                if abs(dip - pd) > djump or dz > ajump:
                    add("S5", "Lompatan survey besar", "KUNING", hole, f"{pa:g}–{at:g} m",
                        f"Δdip {dip - pd:+.1f}°, Δazimuth {dz:.1f}° (batas {djump:g}° / {ajump:g}°)")
    samp_keys = [k for k in (o["name"] for o in core_dh.columns(p).get("assay", [])) if norm(k) in ALIAS["sample_id"]]
    for kind, lab in (("assay", "Assay"), ("geology", "Geologi")):
        sids: dict[str, str] = {}
        for hk, rows in iv.get(kind, {}).items():
            hole = rows[0][0]
            cc = col.get(hk)
            if col and cc is None:
                add(f"{lab[0]}1", f"{lab} tanpa collar", "MERAH", hole, "", f"{len(rows)} interval, Hole ID tidak ada di Collar")
            last = None
            for h, f, t, a in rows:
                if last is not None and f < last[2] - 1e-6:
                    add(f"{lab[0]}2", f"Interval {lab.lower()} tumpang-tindih", "MERAH", hole, f"{last[1]:g}–{last[2]:g} / {f:g}–{t:g} m",
                        "Interval saling menutup; komposit akan menghitung ganda")
                elif last is not None and f - last[2] > gapmin:
                    add(f"{lab[0]}3", f"Celah interval {lab.lower()}", "INFO" if kind == "assay" else "KUNING", hole,
                        f"{last[2]:g}–{f:g} m", f"Celah {f - last[2]:g} m tanpa {'sampel' if kind == 'assay' else 'logging'}")
                if cc and cc["depth"] is not None and t > cc["depth"] + tol:
                    add(f"{lab[0]}4", f"{lab} melewati EOH", "KUNING", hole, f"{f:g}–{t:g} m", f"EOH {cc['depth']:g} m")
                if kind == "assay":
                    for k, v in a.items():
                        if isinstance(v, (int, float)) and v < 0:
                            add("A5", "Nilai assay negatif", "KUNING", hole, f"{f:g}–{t:g} m", f"{k} = {v:g}")
                    for k in samp_keys:
                        sid = str(a.get(k) or "").strip()
                        if sid:
                            if sid in sids:
                                add("A6", "Sample ID ganda di assay", "MERAH", hole, sid, f"juga di {sids[sid]}")
                            else:
                                sids[sid] = f"{hole} {f:g}–{t:g} m"
                last = (h, f, t) if last is None or t >= last[2] else last
    if col:
        noa = [cc["hole"] for hk, cc in col.items() if hk not in iv.get("assay", {})]
        if noa:
            add("C3", "Collar tanpa assay", "INFO", ", ".join(noa[:12]) + (" …" if len(noa) > 12 else ""), f"{len(noa)} lubang",
                "Belum ada interval assay untuk lubang ini")
        nos = [rows[0][0] for hk, rows in iv.get("assay", {}).items() if hk in col and hk not in sv]
        if nos:
            add("C4", "Assay tanpa survey", "INFO", ", ".join(nos[:12]) + (" …" if len(nos) > 12 else ""), f"{len(nos)} lubang",
                "Desurvey memakai dip / azimuth collar saja")
    issues.sort(key=lambda x: (SEV_ORDER[x["severity"]], x["code"], x["hole"], x["item"]))
    summ: dict[str, dict] = {}
    for x in issues:
        k = x["code"]
        sm = summ.setdefault(k, {"code": k, "check": x["check"], "severity": x["severity"], "n": 0, "holes": set()})
        sm["n"] += 1
        sm["holes"].add(x["hole"])
    summary = [dict(v, holes=len(v["holes"])) for _k, v in sorted(summ.items(), key=lambda kv: (SEV_ORDER[kv[1]["severity"]], kv[0]))]
    red = sum(1 for x in issues if x["severity"] == "MERAH")
    yel = sum(1 for x in issues if x["severity"] == "KUNING")
    n_holes = len(set(col) | set(sv) | set(iv.get("assay", {})) | set(iv.get("geology", {})))
    return {"counts": {"collar": len(col), "survey": sum(len(v) for v in sv.values()), "assay": sum(len(v) for v in iv.get("assay", {}).values()),
                       "geology": sum(len(v) for v in iv.get("geology", {}).values()), "holes": n_holes},
            "issues": issues, "summary": summary, "red": red, "yellow": yel,
            "light": "MERAH" if red else ("KUNING" if yel else ("HIJAU" if n_holes else "ABU-ABU")),
            "empty": n_holes == 0}


# ---------------------------------------------------------------- grafik (matplotlib, PNG)
C_PASS, C_WARN, C_FAIL, C_NAVY, C_LINE = "#3E7C59", "#E0A21E", "#C0392B", "#1F3A5F", "#7F8C8D"


def _plt():
    mpl = importlib.import_module("matplotlib")
    mpl.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    plt.rcParams.update({"text.usetex": False, "font.size": 8.5, "axes.titlesize": 9.5, "axes.titleweight": "bold", "axes.edgecolor": "#5d6773",
                         "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 110})
    return plt


def _png(fig) -> bytes:
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    importlib.import_module("matplotlib.pyplot").close(fig)
    return b.getvalue()


def chart_list(res: dict) -> list[dict]:
    out = [{"kind": "dash", "key": "", "title": "Ringkasan status CRM, Blank, Duplikat"}]
    out += [{"kind": "crm", "key": gg["key"], "title": f"CRM {gg['zona']} — {gg['std']}"} for gg in res["crm_groups"]]
    out += [{"kind": "blank", "key": z["zona"], "title": f"Blank {z['zona']}"} for z in res["blank_summary"]]
    out += [{"kind": "dup", "key": gg["key"], "title": f"Duplikat {gg['zona']} — {gg['tipe']}"} for gg in res["dup_groups"]]
    return out


_CHART_LOCK = threading.Lock()  # pyplot tidak aman dipakai beberapa thread sekaligus (grafik dimuat paralel di aplikasi)


def chart_png(res: dict, kind: str, key: str) -> bytes:
    with _CHART_LOCK:
        return _chart_png(res, kind, key)


def _chart_png(res: dict, kind: str, key: str) -> bytes:
    plt = _plt()
    st = res["settings"]
    el = f"{st['element']} ({st['unit']})"
    if kind == "crm":
        gg = next(x for x in res["crm_groups"] if x["key"] == key)
        rows = gg["rows"]
        x = list(range(1, len(rows) + 1))
        fig, ax = plt.subplots(figsize=(8.2, 3.0))
        m, sd = gg["mean"], gg["sd"]
        ax.axhline(m, color=C_NAVY, lw=1.3, label=f"Certified {m:g}")
        for k, ls, lab in ((2, ":", "±2 SD"), (3, "--", "±3 SD")):
            ax.axhline(m + k * sd, color=C_FAIL, lw=1, ls=ls, label=lab)
            ax.axhline(m - k * sd, color=C_FAIL, lw=1, ls=ls)
        for cat, colr in (("PASS", C_PASS), ("WARN", C_WARN), ("FAIL", C_FAIL)):
            pts = [(i, r["grade"]) for i, r in zip(x, rows) if r["cat"] == cat]
            if pts:
                ax.scatter([a for a, _b in pts], [b for _a, b in pts], s=12, color=colr, zorder=3, label=f"{cat} ({len(pts)})")
        ax.plot(x, [r["grade"] for r in rows], color="#9fb3c8", lw=0.6, zorder=2)
        lo, hi = m - 4 * sd, m + 4 * sd
        ys = [r["grade"] for r in rows]
        ax.set_ylim(min(lo, min(ys) - sd * 0.5), max(hi, max(ys) + sd * 0.5))
        ax.set_title(f"{gg['zona']} — {gg['std']}   (n = {len(rows)}, PASS {gg['pass']} / WARN {gg['warn']} / FAIL {gg['fail']})")
        ax.set_xlabel("urutan insersi")
        ax.set_ylabel(el)
        ax.legend(fontsize=7, ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
        return _png(fig)
    if kind == "blank":
        rows = sorted((r for r in res["blank"] if r["zona"] == key), key=lambda r: r["seq"])
        cut = float(st["blank_cutoff"])
        fig, ax = plt.subplots(figsize=(8.2, 2.8))
        x = list(range(1, len(rows) + 1))
        for cat, colr in (("PASS", C_PASS), ("FAIL", C_FAIL)):
            pts = [(i, r["grade"]) for i, r in zip(x, rows) if r["cat"] == cat]
            if pts:
                ax.scatter([a for a, _b in pts], [b for _a, b in pts], s=9 if cat == "PASS" else 16, color=colr, zorder=3, label=f"{cat} ({len(pts)})")
        ax.axhline(cut, color=C_FAIL, ls="--", lw=1.1, label=f"cut-off {cut:g}")
        ax.set_ylim(0, max(cut * 3, max((r["grade"] for r in rows), default=cut) * 1.1))
        nf = sum(r["cat"] == "FAIL" for r in rows)
        ax.set_title(f"Blank {key} — urutan hasil terhadap cut-off (n = {len(rows)}, FAIL {nf})")
        ax.set_xlabel("urutan insersi")
        ax.set_ylabel(el)
        ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22), frameon=False)
        return _png(fig)
    if kind == "dup":
        gg = next(x for x in res["dup_groups"] if x["key"] == key)
        rows = gg["rows"]
        hmax = float(st["hard_max"])
        h = min(max(hmax / 100, 0.001), 0.99)
        up = (1 + h) / (1 - h)
        fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
        o = [r["orig"] for r in rows]
        d = [r["dup"] for r in rows]
        lo = 10 ** math.floor(math.log10(min(o + d)))
        hi = 10 ** math.ceil(math.log10(max(o + d)))
        ax = axs[0]
        for cat, colr in (("PASS", "#4C6E91"), ("FAIL", C_FAIL)):
            pts = [(r["orig"], r["dup"]) for r in rows if r["cat"] == cat]
            if pts:
                ax.scatter([a for a, _b in pts], [b for _a, b in pts], s=14, color=colr, zorder=3,
                           label=f"{'PASS (≤' if cat == 'PASS' else 'FAIL (>'} {hmax:g}%)")
        ax.plot([lo, hi], [lo, hi], color="black", lw=1, label="1:1")
        ax.plot([lo, hi], [lo * up, hi * up], color=C_LINE, ls="--", lw=1, label=f"±HARD {hmax:g}%")
        ax.plot([lo, hi], [lo / up, hi / up], color=C_LINE, ls="--", lw=1)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_title(f"Scatter 1:1  [R² = {gg['r2']:.4f}]")
        ax.set_xlabel(f"Original {el}")
        ax.set_ylabel(f"Duplicate {el}")
        ax.legend(fontsize=6.5, loc="upper left")
        mlo = 10 ** math.floor(math.log10(min(r["mean"] for r in rows)))
        mhi = 10 ** math.ceil(math.log10(max(r["mean"] for r in rows)))
        ax = axs[1]
        for cat, colr in (("PASS", "#4C6E91"), ("FAIL", C_FAIL)):
            pts = [(r["mean"], r["hard"] * 100) for r in rows if r["cat"] == cat]
            if pts:
                ax.scatter([a for a, _b in pts], [b for _a, b in pts], s=14, color=colr, zorder=3)
        ax.axhline(hmax, color=C_FAIL, ls="--", lw=1.2, label=f"HARD {hmax:g}%")
        ax.set_xscale("log")
        ax.set_xlim(mlo, mhi)
        ax.set_ylim(bottom=0)
        ax.set_title("Plot presisi")
        ax.set_xlabel(f"Kadar rata-rata {el}")
        ax.set_ylabel("HARD (%)")
        ax.legend(fontsize=6.5)
        ax = axs[2]
        for cat, colr in (("PASS", "#4C6E91"), ("FAIL", C_FAIL)):
            pts = [(r["mean"], r["rpd"] * 100) for r in rows if r["cat"] == cat]
            if pts:
                ax.scatter([a for a, _b in pts], [b for _a, b in pts], s=14, color=colr, zorder=3)
        ax.axhline(0, color="black", lw=1)
        ax.axhline(gg["avg_rpd"] * 100, color="#E08A1E", ls="--", lw=1.4, label=f"rata-rata RPD {gg['avg_rpd'] * 100:+.1f}%")
        ax.axhline(2 * h * 100, color=C_LINE, ls="--", lw=1, label=f"±{2 * h * 100:g}%")
        ax.axhline(-2 * h * 100, color=C_LINE, ls="--", lw=1)
        ax.set_xscale("log")
        ax.set_xlim(mlo, mhi)
        ax.set_title("Bias RPD")
        ax.set_xlabel(f"Kadar rata-rata {el}")
        ax.set_ylabel("RPD (%)")
        ax.legend(fontsize=6.5)
        fig.suptitle(f"Duplikat {gg['zona']} — {gg['tipe']}   n = {gg['n']}, PASS {gg['pass']} / FAIL {gg['n'] - gg['pass']}", fontsize=10,
                     fontweight="bold", color=C_NAVY)
        fig.tight_layout()
        return _png(fig)
    if kind == "dash":
        t = res["totals"]
        fig, axs = plt.subplots(1, 3, figsize=(10, 3.2))
        for ax, (title, dd) in zip(axs, (("Total CRM", t["crm"]), ("Total Blank", t["blank"]), ("Total Duplikat", t["dup"]))):
            vals = [(k, v) for k, v in dd.items() if v]
            if not vals:
                ax.axis("off")
                ax.set_title(title + "\n(tidak ada data)")
                continue
            colr = {"PASS": C_PASS, "WARN": C_WARN, "FAIL": C_FAIL}
            ax.pie([v for _k, v in vals], labels=[f"{k}\n{v}" for k, v in vals], colors=[colr[k] for k, _v in vals], startangle=90,
                   wedgeprops={"width": 0.38, "edgecolor": "white"}, textprops={"fontsize": 8})
            ax.set_title(f"{title} ({sum(dd.values())})")
        return _png(fig)
    raise ValueError(f"Grafik tidak dikenal: {kind}")


def charts_zip(res: dict) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        for i, c in enumerate(chart_list(res), 1):
            nm = re.sub(r"[^\w.-]+", "_", f"{i:02d}_{c['title']}").strip("_")[:90] + ".png"
            z.writestr(nm, chart_png(res, c["kind"], c["key"]))
    return b.getvalue()


# ---------------------------------------------------------------- ekspor Excel (struktur sheet sama dengan workbook QAQC)
FILL = {"PASS": "B6D7A8", "WARN": "FFE599", "FAIL": "EA9999", 1: "E2EFDA", 2: "FFF2CC", 3: "F4CCCC", 0: "F2F2F2", "MERAH": "F4CCCC",
        "KUNING": "FFF2CC", "INFO": "EEF3F8", "HIJAU": "E2EFDA"}


def to_xlsx(s: Store, folder: Optional[str] = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    res = analyze(s)
    st = res["settings"]
    wb = Workbook()
    hf, hfont = PatternFill("solid", fgColor="1F3A5F"), Font(bold=True, color="FFFFFF")

    def fill(c, k):
        if k in FILL:
            c.fill = PatternFill("solid", fgColor=FILL[k])

    def sheet(title, heads, rows, fmts=None, first=False, widths=None):
        ws = wb.active if first else wb.create_sheet()
        ws.title = title[:31]
        ws.append(heads)
        for c in ws[1]:
            c.fill, c.font, c.alignment = hf, hfont, Alignment(horizontal="center", vertical="center", wrap_text=True)
        for r in rows:
            ws.append(r)
        for i, h in enumerate(heads, 1):
            ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(i, max(10, min(36, len(str(h)) + 4)))
            if fmts and fmts.get(i):
                for (cc,) in ws.iter_rows(min_row=2, min_col=i, max_col=i):
                    cc.number_format = fmts[i]
        ws.freeze_panes = "A2"
        return ws

    def status_fill(ws, col):
        for (cc,) in ws.iter_rows(min_row=2, min_col=col, max_col=col):
            v = str(cc.value or "").upper()
            fill(cc, "FAIL" if "FAIL" in v else ("WARN" if "WARN" in v else ("PASS" if "PASS" in v else "")))

    # QAQC_Dashboard
    ws = wb.active
    ws.title = "QAQC_Dashboard"
    ws["B2"] = "QAQC SUMMARY DASHBOARD"
    ws["B2"].font = Font(bold=True, size=18, color="1F3A5F")
    ws["B3"] = "Analisis Kinerja Standard (CRM), Blank, dan Duplicate per Zona"
    hd = ["Zona", "CRM (akurasi)", "Duplikat (presisi)", "Blank (kontaminasi)", "Penilaian keseluruhan"]
    for j, h in enumerate(hd, 2):
        c = ws.cell(6, j, h)
        c.fill, c.font, c.alignment = hf, hfont, Alignment(horizontal="center", vertical="center")
    for i, d in enumerate(res["dashboard"], 7):
        for j, (k, lv) in enumerate((("zona", None), ("crm", "crm_lvl"), ("dup", "dup_lvl"), ("blank", "blank_lvl"), ("overall", "overall_lvl")), 2):
            c = ws.cell(i, j, d[k])
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            if lv:
                fill(c, d[lv])
            if k == "overall":
                c.font = Font(bold=True)
    ws.column_dimensions["B"].width = 12
    for col_ in "CDEF":
        ws.column_dimensions[col_].width = 34
    r0 = 8 + len(res["dashboard"])
    ws.cell(r0, 2, "Status").font = Font(bold=True)
    for j, (lab, dd) in enumerate((("CRM", res["totals"]["crm"]), ("Blank", res["totals"]["blank"]), ("Duplicate", res["totals"]["dup"]))):
        ws.cell(r0 + 1 + j, 2, lab)
        ws.cell(r0 + 1 + j, 3, " · ".join(f"{k} {v}" for k, v in dd.items()))
    try:
        img = XLImage(io.BytesIO(chart_png(res, "dash", "")))
        img.width, img.height = img.width * 0.55, img.height * 0.55
        ws.add_image(img, f"B{r0 + 5}")
    except Exception:  # noqa: BLE001 - grafik opsional bila matplotlib tidak ada
        pass
    # CRM_Data (kolom A..S seperti makro CRM_Run) + Batch_ID
    rows = []
    for r in res["crm"]:
        ok = r["z"] is not None
        rows.append([r["sample_id"], r["std"], r["grade"], r["mean"], r["sd"], r["zona"], r["status"], r["z"], 0, 2, -2, 3, -3,
                     r["grade"], r["mean"], r["mean"] + 2 * r["sd"] if ok else None, r["mean"] - 2 * r["sd"] if ok else None,
                     r["mean"] + 3 * r["sd"] if ok else None, r["mean"] - 3 * r["sd"] if ok else None, r["batch"]])
    ws = sheet("CRM_Data", ["Sample_ID", "Standard_Name", "Lab_Grade", "Cert_Mean", "Cert_SD", "Zona", "Status", "Z_Score", "Mean (0)", "+2SD",
                            "-2SD", "+3SD", "-3SD", "Lab_Grade", "Cert_Mean_Limit", "+2SD_Val", "-2SD_Val", "+3SD_Val", "-3SD_Val", "Batch_ID"],
               rows, {8: "+0.00;-0.00;0.00"})
    status_fill(ws, 7)
    # CRM_Summary
    rows = [[x["zona"], x["crm"], x["n"], x["mean_lab"], x["certified"], x["bias"], x["sd_text"], x["cv"], x["pwf"]] for x in res["crm_summary"]]
    if res["crm_total"]:
        t = res["crm_total"]
        rows.append([t["zona"], t["crm"], t["n"], None, None, None, None, None, t["pwf"]])
    ws = sheet("CRM_Summary", ["Zona", "CRM", "n", "Rata-rata lab", "Certified", "Bias", "SD lab vs SD sertifikat", "CV", "PASS / WARN / FAIL"],
               rows, {6: "+0.00%;-0.00%;0.00%", 8: "0.00%"}, widths={7: 22, 9: 28})
    for i, x in enumerate(res["crm_summary"], 2):
        fill(ws.cell(i, 9), "FAIL" if x["fail"] else ("WARN" if x["warn"] else "PASS"))
    # Duplicate_Data (A..J seperti makro Duplicate_Run) + Tipe + Batch
    rows = [[r["orig_id"], r["dup_id"], r["orig"], r["dup"], r["hard"], r["status"], r["zona"], r["mean"], r["rpd"], r["hard"], r["tipe"], r["batch"]]
            for r in res["dup"]]
    ws = sheet("Duplicate_Data", ["Original_ID", "Duplicate_ID", "Original", "Duplicate", "HARD_Result", "Status", "Zona", "Mean_Grade", "RPD (%)",
                                  "ARD (%)", "Tipe", "Batch_ID"], rows, {5: "0.00%", 9: "+0.00%;-0.00%;0.00%", 10: "0.00%"})
    status_fill(ws, 6)
    # Duplicate Summary
    rows = [[x["zona"], x["kelas"], x["n"], x["pass"], x["rate"], x["hard"]] for x in res["dup_summary"]]
    ws = sheet("Duplicate Summary", ["Zona", "Kelas kadar rata-rata pasangan", "n pasangan", "PASS", "Pass-rate", "HARD rata-rata"], rows,
               {5: "0.0%", 6: "0.00%"}, widths={2: 30})
    for i, x in enumerate(res["dup_summary"], 2):
        if x["row"] != "kelas":
            for cc in ws[i]:
                cc.font = Font(bold=True)
        if x["n"]:
            fill(ws.cell(i, 5), 1 if x["rate"] >= 0.8 else (2 if x["rate"] >= 0.5 else 3))
    # Blank_Data (A..G seperti makro Blank_Run) + Batch
    cut = float(st["blank_cutoff"])
    rows = [[r["sample_id"], r["std"], r["grade"], r["status"], r["zona"], cut, cut, r["batch"]] for r in res["blank"]]
    ws = sheet("Blank_Data", ["Sample_ID", "Standard_Name", "Lab_Grade", "Status", "Zona", "Limit Deteksi", "Cut-Off Limit", "Batch_ID"], rows)
    status_fill(ws, 4)
    # Report_Appendix (Lampiran A / B / C seperti makro Report_Run)
    ws = wb.create_sheet("Report_Appendix")
    rr = 1

    def table(title, heads, body, fmts=None, colr=None):
        nonlocal rr
        if not body:
            return
        ws.cell(rr, 1, title).font = Font(bold=True, size=14, color="1F3A5F")
        for j, h in enumerate(heads, 1):
            c = ws.cell(rr + 1, j, h)
            c.fill, c.font, c.alignment = hf, hfont, Alignment(horizontal="center")
        for i, row in enumerate(body, rr + 2):
            for j, v in enumerate(row, 1):
                c = ws.cell(i, j, v)
                if fmts and fmts.get(j):
                    c.number_format = fmts[j]
                if colr:
                    k = colr(row)
                    if k:
                        fill(c, k)
        rr += len(body) + 4
    table("Lampiran A. CRM berstatus WARNING dan FAIL", ["Sample ID", "Batch ID", "CRM", "Lab (g/t)", "Certified", "Z-score", "Status"],
          [[r["sample_id"], r["batch"], r["std"], r["grade"], r["mean"], r["z"], r["status"].upper()] for r in res["app_a"]],
          {4: "0.00", 5: "0.000", 6: "+0.00;-0.00;0.00"}, lambda row: "FAIL" if "FAIL" in row[6] else "WARN")
    table("Lampiran B. Blank berstatus FAIL (Contamination)", ["Sample ID", "Batch ID", "Zona", "Hasil (g/t)", f"Kelipatan cut-off ({cut:g})"],
          [[r["sample_id"], r["batch"], r["zona"], r["grade"], r["ratio"]] for r in res["app_b"]], {4: "0.000", 5: '0.0"×"'},
          lambda row: "FAIL" if (row[4] or 0) > 10 else "WARN")
    table(f"Lampiran C. Pasangan duplikat gagal (Selisih ≥{float(st['appc_ratio']):g}×, Kadar ≥{float(st['appc_grade']):g} g/t)",
          ["Original ID", "Batch ID", "Zona", "Original", "Duplikat", "Rasio maks/min"],
          [[r["orig_id"], r["batch"], r["zona"], round(r["orig"], 2), round(r["dup"], 2), r["ratio"]] for r in res["app_c"]], {4: "0.00", 5: "0.00", 6: '0.0"×"'})
    if rr == 1:
        ws["A1"] = "Tidak ada data WARNING / FAIL untuk dilaporkan."
    for i, w in enumerate((18, 14, 14, 12, 12, 16, 18), 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    # Batch_Summary
    ws = sheet("Batch_Summary", ["Batch ID", "Zona", "CRM n", "CRM WARN", "CRM FAIL", "Blank n", "Blank FAIL", "Duplikat n", "Duplikat FAIL", "Status"],
               [[b["batch"], b["zones"], b["crm"], b["crm_warn"], b["crm_fail"], b["blank"], b["blank_fail"], b["dup"], b["dup_fail"], b["status"]]
                for b in res["batches"]])
    status_fill(ws, 10)
    # Data bor
    if folder:
        try:
            dh = dh_checks(folder, st)
        except Exception:  # noqa: BLE001
            dh = None
        if dh and not dh["empty"]:
            ws = sheet("Data_Bor_QAQC", ["Kode", "Pemeriksaan", "Tingkat", "Hole ID", "Kedalaman / item", "Keterangan"],
                       [[x["code"], x["check"], x["severity"], x["hole"], x["item"], x["detail"]] for x in dh["issues"]], widths={2: 30, 4: 18, 5: 18, 6: 50})
            for (cc,) in ws.iter_rows(min_row=2, min_col=3, max_col=3):
                fill(cc, cc.value)
    # Master_CRM, Assay_Import, Control_Panel
    sheet("Master_CRM", [h for _k, h, _t in COLS["master_crm"]], [[r[k] for k, _h, _t in COLS["master_crm"]] for r in table_rows(s, "master_crm")])
    sheet("Assay_Import", [h for _k, h, _t in COLS["assay_import"]], [[r[k] for k, _h, _t in COLS["assay_import"]] for r in table_rows(s, "assay_import")])
    cp = [[SETTINGS_LABEL.get(k, k), st[k]] for k in SETTINGS_DEFAULT]
    if res["dup_stat"]:
        ds = res["dup_stat"]
        cp += [["Interpretasi R² (Precision):", f"R² = {ds['r2']:.4f} -> {ds['r2_label']}"],
               ["Bias / Avg RPD & ARD:", f"Avg RPD = {ds['avg_rpd']:.2f}% | Avg ARD/HARD = {ds['avg_ard']:.2f}%"]]
    cp += [["Peringatan", w] for w in res["warnings"]]
    sheet("Control_Panel", ["Parameter", "Nilai"], cp, widths={1: 48, 2: 60})
    # grafik
    try:
        for title, kinds in (("CRM_Charts", "crm"), ("Blank_Charts", "blank"), ("Duplicate_Charts", "dup")):
            items = [c for c in chart_list(res) if c["kind"] == kinds]
            if not items:
                continue
            ws = wb.create_sheet(title)
            row = 1
            for c in items:
                img = XLImage(io.BytesIO(chart_png(res, c["kind"], c["key"])))
                sc = 0.5
                img.width, img.height = img.width * sc, img.height * sc
                ws.add_image(img, f"A{row}")
                row += int(img.height / 20) + 2
    except ImportError:
        pass
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


# ---------------------------------------------------------------- laporan (HTML untuk QTextDocument -> PDF di aplikasi Qt)
def _e(t: Any) -> str:
    return str("" if t is None else t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


LIGHT_COLOR = {"HIJAU": "#2F6B3A", "KUNING": "#B7791F", "MERAH": "#C0392B", "ABU-ABU": "#5d6773"}


def report(s: Store, folder: str, title: str = "", author: str = "", project: str = "") -> dict:
    """Isi laporan QAQC (HTML sederhana yang dirender QTextDocument) + grafik PNG (base64) yang dirujuk lewat <img src='img:NAMA'>."""
    res = analyze(s)
    st = res["settings"]
    try:
        dh = dh_checks(folder, st)
    except Exception:  # noqa: BLE001
        dh = None
    imgs: dict[str, str] = {}

    def img(kind, key, width=640):
        nm = f"{kind}_{len(imgs)}"
        try:
            imgs[nm] = base64.b64encode(chart_png(res, kind, key)).decode()
        except ImportError:
            return ""
        return f'<p align="center"><img src="img:{nm}" width="{width}"></p>'

    def tbl(heads, rows, widths=None, aligns=None):
        h = '<table width="100%" cellspacing="0" cellpadding="4" border="0" style="border-collapse:collapse">'
        h += "<tr>" + "".join(f'<th bgcolor="#1F3A5F" align="left"{f" width={chr(34)}{widths[i]}{chr(34)}" if widths and widths[i] else ""}>'
                              f'<font color="white">{_e(x)}</font></th>' for i, x in enumerate(heads)) + "</tr>"
        for i, r in enumerate(rows):
            bg = "#F6F8FB" if i % 2 else "#FFFFFF"
            h += f'<tr bgcolor="{bg}">' + "".join(f'<td{" align=" + chr(34) + aligns[j] + chr(34) if aligns and aligns[j] else ""}>{x}</td>'
                                                   for j, x in enumerate(r)) + "</tr>"
        return h + "</table>"

    def lt(lv):
        k = light(lv) if isinstance(lv, int) else lv
        return f'<b><font color="{LIGHT_COLOR.get(k, "#5d6773")}">{k}</font></b>'

    def h2(n, t):
        return f'<h2 style="color:#1F3A5F; background-color:#EEF3F8">&nbsp;{n}. {_e(t)}</h2>'

    def h3(t):
        return f'<h3 style="color:#2A5EA8">{_e(t)}</h3>'
    dash = res["dashboard"]
    lv_crm = max((d["crm_lvl"] for d in dash), default=0)
    lv_dup = max((d["dup_lvl"] for d in dash), default=0)
    lv_blk = max((d["blank_lvl"] for d in dash), default=0)
    lv_dh = {"MERAH": 3, "KUNING": 2, "HIJAU": 1}.get(dh["light"], 0) if dh else 0
    worst = max([d["overall_lvl"] for d in dash] + [lv_dh], default=0)
    health = {3: "MERAH — PERLU TINDAKAN KOREKTIF", 2: "KUNING — MEMADAI DENGAN CATATAN", 1: "HIJAU — MEMUASKAN", 0: "ABU-ABU — DATA BELUM CUKUP"}[worst]
    hcol = {3: ("#F4CCCC", "#8E1B10"), 2: ("#FFF2CC", "#8A5A00"), 1: ("#E2EFDA", "#2F6B3A"), 0: ("#F2F2F2", "#5d6773")}[worst]
    t = res["totals"]
    ncrm, nblk, ndup = sum(t["crm"].values()), sum(t["blank"].values()), sum(t["dup"].values())
    el = f"{st['element']} ({st['unit']})"
    o = []
    o.append(f'<h1 style="color:#1F3A5F">{_e(title or "Laporan QAQC Sampel & Data Bor")}</h1>')
    o.append(f'<p style="color:#5d6773">Dibuat: <b>{date.today().isoformat()}</b> &nbsp;&nbsp; Disiapkan oleh: <b>{_e(author or "DB-Ex QAQC")}</b>'
             f' &nbsp;&nbsp; Proyek: <b>{_e(project)}</b> &nbsp;&nbsp; Zona: <b>{_e(st["zone"])}</b> &nbsp;&nbsp; Unsur: <b>{_e(el)}</b></p><hr>')
    o.append(f'<table width="100%" cellpadding="10" cellspacing="0"><tr><td bgcolor="{hcol[0]}"><b><font size="+1" color="{hcol[1]}">'
             f'KESEHATAN DATA: {health}</font></b></td></tr></table>')
    # 1. ringkasan eksekutif
    o.append(h2(1, "Ringkasan Eksekutif"))
    sent = []
    if res["crm_total"]:
        ct = res["crm_total"]
        sent.append(f"{ncrm} insersi CRM dinilai: {ct['pass']} PASS, {ct['warn']} WARNING (>2 SD) dan {ct['fail']} FAIL (>3 SD) "
                    f"({ct['pass'] / ct['n'] * 100:.1f}% PASS).")
    if nblk:
        sent.append(f"{nblk} blank dinilai terhadap cut-off {float(st['blank_cutoff']):g}: {t['blank']['FAIL']} melebihi cut-off.")
    if res["dup_stat"]:
        ds = res["dup_stat"]
        sent.append(f"{ds['n']} pasangan duplikat: {t['dup']['PASS']} lolos HARD ≤ {float(st['hard_max']):g}% "
                    f"({t['dup']['PASS'] / ds['n'] * 100:.1f}%); R² = {ds['r2']:.4f} ({ds['r2_label']}); rata-rata RPD {ds['avg_rpd']:+.2f}%, "
                    f"rata-rata HARD {ds['avg_ard']:.2f}%.")
    if dh and not dh["empty"]:
        sent.append(f"Pemeriksaan data bor ({dh['counts']['holes']} lubang): {dh['red']} kesalahan struktur (MERAH) dan {dh['yellow']} hal perlu "
                    f"diperiksa (KUNING).")
    o.append("<p>" + " ".join(_e(x) for x in sent) + "</p>")
    o.append(h3("1.1 Ringkasan lampu lalu lintas"))
    rows = [["Akurasi CRM", lt(lv_crm), _e(res["crm_total"]["pwf"] if res["crm_total"] else "tidak ada data")],
            ["Kontaminasi blank", lt(lv_blk), _e(f"{t['blank']['FAIL']} dari {nblk} melebihi cut-off" if nblk else "tidak ada data")],
            ["Presisi duplikat", lt(lv_dup), _e(f"{t['dup']['PASS']}/{ndup} lolos HARD ≤ {float(st['hard_max']):g}%" if ndup else "tidak ada data")]]
    if dh:
        rows.append(["Integritas data bor", lt(dh["light"]), _e(f"{dh['red']} MERAH, {dh['yellow']} KUNING" if not dh["empty"] else "belum ada data bor")])
    o.append(tbl(["Pemeriksaan", "Status", "Metrik utama"], rows, ["28%", "14%", None]))
    o.append(h3("1.2 Angka utama"))
    rows = [["Insersi CRM", f"{ncrm:,}"], ["Insersi blank", f"{nblk:,}"], ["Pasangan duplikat", f"{ndup:,}"],
            ["Batch lab", f"{len([b for b in res['batches'] if b['batch'] != 'N/A']):,}"], ["Zona", ", ".join(res["zones"]) or "-"],
            ["CRM gagal kasar (>3 SD)", f"{t['crm']['FAIL']}"], ["Blank di atas cut-off", f"{t['blank']['FAIL']}"]]
    if dh and not dh["empty"]:
        rows += [["Lubang bor", f"{dh['counts']['holes']:,}"], ["Interval assay", f"{dh['counts']['assay']:,}"]]
    o.append(tbl(["Item", "Nilai"], rows, ["50%", None]))
    acts = []
    if dh and dh["red"]:
        acts.append(f"<b>Perbaiki {dh['red']} kesalahan struktur data bor</b> di database sumber sebelum komposit (lihat bagian 2).")
    if t["crm"]["FAIL"]:
        acts.append(f"<b>Telusuri {t['crm']['FAIL']} CRM FAIL (>3 SD)</b>: cocokkan nama standar dengan daftar insersi, re-assay batch terkait (Lampiran A).")
    if t["blank"]["FAIL"]:
        acts.append(f"<b>Periksa {t['blank']['FAIL']} blank di atas cut-off</b>: cek sampel kadar tinggi sebelum blank dan prosedur pembersihan "
                    "alat preparasi (Lampiran B).")
    for d in dash:
        if d["dup_lvl"] == 3:
            acts.append(f"<b>Presisi duplikat zona {_e(d['zona'])} tidak memuaskan</b>: evaluasi pembagian sampel / splitter dan prosedur duplikat.")
    if res["app_c"]:
        acts.append(f"<b>Tinjau {len(res['app_c'])} pasangan duplikat dengan selisih ≥{float(st['appc_ratio']):g}×</b> (Lampiran C).")
    if acts:
        o.append(h3("1.3 Tindakan prioritas"))
        o.append("<ol>" + "".join(f"<li>{a}</li>" for a in acts) + "</ol>")
    n = 2
    # 2. data bor
    if dh and not dh["empty"]:
        o.append(h2(n, "Integritas Data Bor"))
        cc = dh["counts"]
        o.append(f"<p>{cc['holes']} lubang, {cc['collar']} collar, {cc['survey']} stasiun survey, {cc['assay']} interval assay dan {cc['geology']} "
                 "interval geologi diperiksa. Kesalahan MERAH adalah kesalahan keras: komposit di atas interval tumpang-tindih atau survey bertanda "
                 "salah ikut masuk ke model blok, jadi harus diperbaiki di database sumber.</p>")
        if dh["summary"]:
            o.append(tbl(["Kode", "Pemeriksaan", "Tingkat", "Temuan", "Lubang"],
                         [[x["code"], _e(x["check"]), lt(x["severity"]), str(x["n"]), str(x["holes"])] for x in dh["summary"]],
                         ["8%", "46%", "14%", "14%", None]))
            det = [x for x in dh["issues"] if x["severity"] != "INFO"][:60]
            if det:
                o.append(h3(f"{n}.1 Rincian (maks. 60 baris; daftar lengkap di Excel, sheet Data_Bor_QAQC)"))
                o.append(tbl(["Kode", "Hole ID", "Kedalaman / item", "Keterangan"],
                             [[x["code"], _e(x["hole"]), _e(x["item"]), _e(x["detail"])] for x in det], ["8%", "18%", "20%", None]))
        else:
            o.append("<p><b>Tidak ada temuan.</b></p>")
        n += 1
    # 3. CRM
    o.append(h2(n, "Akurasi CRM"))
    if res["crm_summary"]:
        o.append(f"<p>Z = (Lab − Mean) / SD sertifikat. |Z| ≤ 2 PASS, 2–3 WARNING, &gt; 3 FAIL. Rata-rata dan SD lab dihitung dari semua insersi "
                 f"termasuk yang gagal.</p>")
        o.append(tbl(["Zona", "CRM", "n", "Rata-rata lab", "Certified", "Bias", "SD lab vs sertifikat", "PASS / WARN / FAIL"],
                     [[x["zona"], _e(x["crm"]), str(x["n"]), f"{x['mean_lab']:.4f}", f"{x['certified']:g}", f"{x['bias'] * 100:+.2f}%",
                       _e(x["sd_text"]), _e(x["pwf"])] for x in res["crm_summary"]]))
        for gg in res["crm_groups"]:
            o.append(img("crm", gg["key"]))
        o.append('<p align="center"><font color="#5d6773" size="-1">Grafik kontrol CRM per zona × standar dalam urutan insersi. Garis tegas: nilai '
                 'sertifikat; titik-titik: ±2 SD; putus-putus: ±3 SD.</font></p>')
    else:
        o.append("<p>Tidak ada data CRM yang bisa dinilai (periksa Master_CRM).</p>")
    n += 1
    # 4. Blank
    o.append(h2(n, "Kontaminasi Blank"))
    if res["blank_summary"]:
        o.append(f"<p>Blank gagal bila hasil lab melebihi cut-off {float(st['blank_cutoff']):g} {_e(st['unit'])}.</p>")
        o.append(tbl(["Zona", "n blank", "FAIL", "Pass-rate", "Maksimum"],
                     [[x["zona"], str(x["n"]), str(x["fail"]), f"{x['rate'] * 100:.1f}%", f"{x['max']:g}"] for x in res["blank_summary"]]))
        for z in res["blank_summary"]:
            o.append(img("blank", z["zona"]))
    else:
        o.append("<p>Tidak ada data blank.</p>")
    n += 1
    # 5. Duplikat
    o.append(h2(n, "Presisi Duplikat"))
    if res["dup_summary"]:
        ds = res["dup_stat"]
        o.append(f"<p>HARD = |O − D| / (O + D), lolos bila ≤ {float(st['hard_max']):g}%. RPD = (O − D) / rata-rata (bias bertanda); ARD = HARD. "
                 f"R² seluruh pasangan = <b>{ds['r2']:.4f}</b> ({_e(ds['r2_label'])}); rata-rata RPD {ds['avg_rpd']:+.2f}%, rata-rata HARD "
                 f"{ds['avg_ard']:.2f}%.</p>")
        o.append(tbl(["Zona", "Kelas kadar rata-rata pasangan", "n", "PASS", "Pass-rate", "HARD rata-rata"],
                     [[("<b>%s</b>" % _e(x["zona"])) if x["row"] != "kelas" else _e(x["zona"]), _e(x["kelas"]), str(x["n"]), str(x["pass"]),
                       f"{x['rate'] * 100:.1f}%", f"{x['hard'] * 100:.2f}%"] for x in res["dup_summary"]]))
        for gg in res["dup_groups"]:
            o.append(img("dup", gg["key"], 680))
    else:
        o.append("<p>Tidak ada pasangan duplikat yang valid.</p>")
    n += 1
    # 6. per batch
    o.append(h2(n, "Ringkasan per Batch Lab"))
    flag = [b for b in res["batches"] if b["status"] != "PASS"]
    o.append(f"<p>{len(res['batches'])} batch; {sum(1 for b in flag if b['status'] == 'FAIL')} batch FAIL (CRM &gt; 3 SD atau blank di atas "
             f"cut-off) dan {sum(1 for b in flag if b['status'] == 'WARNING')} batch WARNING (CRM &gt; 2 SD atau duplikat gagal). Tabel memuat batch "
             "yang perlu ditinjau; daftar lengkap di Excel (Batch_Summary).</p>")
    if flag:
        o.append(tbl(["Batch", "Zona", "CRM n / WARN / FAIL", "Blank n / FAIL", "Duplikat n / FAIL", "Status"],
                     [[_e(b["batch"]), _e(b["zones"]), f"{b['crm']} / {b['crm_warn']} / {b['crm_fail']}", f"{b['blank']} / {b['blank_fail']}",
                       f"{b['dup']} / {b['dup_fail']}", lt(3 if b["status"] == "FAIL" else 2)] for b in flag[:80]]))
    n += 1
    # 7. dashboard
    o.append(h2(n, "Dashboard per Zona"))
    o.append(tbl(["Zona", "CRM (akurasi)", "Duplikat (presisi)", "Blank (kontaminasi)", "Penilaian keseluruhan"],
                 [[f"<b>{_e(d['zona'])}</b>", f'<font color="{LIGHT_COLOR[light(d["crm_lvl"])]}">{_e(d["crm"])}</font>',
                   f'<font color="{LIGHT_COLOR[light(d["dup_lvl"])]}">{_e(d["dup"])}</font>',
                   f'<font color="{LIGHT_COLOR[light(d["blank_lvl"])]}">{_e(d["blank"])}</font>', f"<b>{_e(d['overall'])}</b>"] for d in dash]))
    o.append(img("dash", "", 560))
    # lampiran
    if res["app_a"]:
        o.append(h2("A", "Lampiran A. CRM berstatus WARNING dan FAIL"))
        o.append(tbl(["Sample ID", "Batch ID", "CRM", "Lab", "Certified", "Z-score", "Status"],
                     [[_e(r["sample_id"]), _e(r["batch"]), _e(r["std"]), f"{r['grade']:.2f}", f"{r['mean']:.3f}", f"{r['z']:+.2f}",
                       f'<font color="{C_FAIL if r["cat"] == "FAIL" else "#B7791F"}">{_e(r["status"])}</font>'] for r in res["app_a"]]))
    if res["app_b"]:
        o.append(h2("B", "Lampiran B. Blank berstatus FAIL (Contamination)"))
        o.append(tbl(["Sample ID", "Batch ID", "Zona", "Hasil", f"Kelipatan cut-off ({float(st['blank_cutoff']):g})"],
                     [[_e(r["sample_id"]), _e(r["batch"]), _e(r["zona"]), f"{r['grade']:.3f}", f"{r['ratio']:.1f}×"] for r in res["app_b"]]))
    if res["app_c"]:
        o.append(h2("C", f"Lampiran C. Pasangan duplikat gagal (Selisih ≥{float(st['appc_ratio']):g}×, Kadar ≥{float(st['appc_grade']):g})"))
        o.append(tbl(["Original ID", "Batch ID", "Zona", "Original", "Duplikat", "Rasio maks/min"],
                     [[_e(r["orig_id"]), _e(r["batch"]), _e(r["zona"]), f"{r['orig']:.2f}", f"{r['dup']:.2f}", f"{r['ratio']:.1f}×"] for r in res["app_c"]]))
    o.append(h2("D", "Lampiran D. Parameter penilaian"))
    o.append(tbl(["Parameter", "Nilai"], [[_e(SETTINGS_LABEL.get(k, k)), _e(st[k])] for k in SETTINGS_DEFAULT]))
    if res["warnings"]:
        o.append("<p><b>Catatan data:</b> " + "; ".join(_e(w) for w in res["warnings"]) + "</p>")
    o.append('<p><font color="#5d6773" size="-1">Dibuat dengan DB-Ex (ruang kerja QAQC). Rumus mengikuti workbook QAQC proyek: Z-score CRM, '
             'cut-off blank, HARD / RPD / ARD duplikat. Hasil wajib ditinjau Competent Person sebelum dipakai untuk pelaporan.</font></p>')
    html = ('<html><head><meta charset="utf-8"><style>body{font-family:"Segoe UI",Arial,sans-serif;font-size:9.5pt;color:#1e2a38}'
            'h1{font-size:20pt}h2{font-size:14pt;margin-top:14px}h3{font-size:11pt}th{font-size:9pt}td{font-size:9pt}</style></head><body>'
            + "\n".join(o) + "</body></html>")
    return {"html": html, "images": imgs, "health": health, "title": title or "Laporan QAQC Sampel & Data Bor"}


# ---------------------------------------------------------------- API
class FBody(BaseModel):
    folder: str
    by: str = ""


class ImpBody(FBody):
    paths: list[str]
    target: str = "auto"
    sheet: Optional[str] = None


class TblBody(FBody):
    table: str


class MasterBody(FBody):
    rows: list[dict[str, Any]]


class SetBody(FBody):
    values: dict[str, Any]


class ChartBody(FBody):
    kind: str
    key: str = ""


class RepBody(FBody):
    title: str = ""
    author: str = ""
    project: str = ""


def _brief(res: dict) -> dict:
    """Hasil analisis tanpa daftar baris besar (untuk tampilan)."""
    return {k: v for k, v in res.items() if k not in ("crm", "blank", "dup", "crm_groups", "dup_groups")} | {
        "crm_groups": [{k: v for k, v in gg.items() if k != "rows"} for gg in res["crm_groups"]],
        "dup_groups": [{k: v for k, v in gg.items() if k != "rows"} for gg in res["dup_groups"]],
        "charts": chart_list(res), "n_crm_rows": len(res["crm"]), "n_blank_rows": len(res["blank"]), "n_dup_rows": len(res["dup"])}


@router.post("/open")
def api_open(b: FBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "counts": counts(s), "settings": settings(s), "labels": SETTINGS_LABEL, "root": str(s.root),
            "tables": {k: {"table": v[0], "cols": COLS[v[0]]} for k, v in TABLES.items()}}


@router.post("/import")
def api_import(b: ImpBody) -> dict:
    s = store(b.folder)
    reps, errs = [], []
    for pth in b.paths:
        try:
            reps += import_file(s, pth, b.target, b.by, b.sheet)
        except ValueError as e:
            errs.append(str(e))
    if not reps and errs:
        raise ValueError("\n".join(errs))
    return {"ok": True, "reports": reps, "errors": errs, "counts": counts(s)}


@router.post("/table")
def api_table(b: TblBody) -> dict:
    s = store(b.folder)
    t = TABLES.get(b.table, (b.table,))[0]
    if t not in COLS:
        raise ValueError("Tabel tidak dikenal.")
    return {"ok": True, "cols": COLS[t], "rows": table_rows(s, t)}


@router.post("/master")
def api_master(b: MasterBody) -> dict:
    return {"ok": True, "rows": save_master(store(b.folder), b.rows, b.by)}


class SaveBody(TblBody):
    rows: list[dict[str, Any]]


@router.post("/save")
def api_save(b: SaveBody) -> dict:
    return save_table(store(b.folder), TABLES.get(b.table, (b.table,))[0], b.rows, b.by)


@router.post("/clear")
def api_clear(b: TblBody) -> dict:
    s = store(b.folder)
    clear_table(s, TABLES.get(b.table, (b.table,))[0], b.by)
    return {"ok": True, "counts": counts(s)}


@router.post("/settings")
def api_settings(b: SetBody) -> dict:
    return {"ok": True, "settings": save_settings(store(b.folder), b.values, b.by)}


@router.post("/analyze")
def api_analyze(b: FBody) -> dict:
    return {"ok": True, **_brief(analyze(store(b.folder)))}


@router.post("/rows")
def api_rows(b: TblBody) -> dict:
    """Baris hasil analisis: crm / blank / dup / app_a / app_b / app_c / batches."""
    res = analyze(store(b.folder))
    if b.table not in ("crm", "blank", "dup", "app_a", "app_b", "app_c", "batches"):
        raise ValueError("Daftar tidak dikenal.")
    return {"ok": True, "rows": res[b.table]}


@router.post("/chart")
def api_chart(b: ChartBody):
    from fastapi.responses import Response
    return Response(chart_png(analyze(store(b.folder)), b.kind, b.key), media_type="image/png")


@router.post("/dh")
def api_dh(b: FBody) -> dict:
    return {"ok": True, **dh_checks(b.folder, settings(store(b.folder)))}


@router.post("/export/xlsx")
def api_xlsx(b: FBody):
    from fastapi.responses import Response
    s = store(b.folder)
    with s.conn() as c:
        _hist(c, "ekspor xlsx", "", b.by)
    return Response(to_xlsx(s, b.folder), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/export/charts")
def api_charts(b: FBody):
    from fastapi.responses import Response
    return Response(charts_zip(analyze(store(b.folder))), media_type="application/zip")


@router.post("/report")
def api_report(b: RepBody) -> dict:
    s = store(b.folder)
    with s.conn() as c:
        _hist(c, "laporan PDF", b.title, b.by)
    return {"ok": True, **report(s, b.folder, b.title, b.author, b.project)}
