"""Ruang kerja Borang DB-Ex: borang lapangan tulisan tangan (scan / foto / PDF) -> AI vision lokal (Ollama) -> tabel yang
diperiksa geologist berdampingan dengan scan -> Excel / CSV / SQLite / MS Access.

Jenis borang:
- "ore": Ore Spotter di front loading (Form Loading / Rehandling Ore dari Pit to ROM / Stockpile) — header (tanggal, shift I / II,
  crew, lokasi, excavator) + satu baris per ritase (jam, pit, elevasi, kelas material, truck, tonnage, tujuan dumping).
- "rom": Ore ke Stockpile / Crusher (Rehandling / Direct) — header (tanggal, shift, crew, lokasi) + baris (unit, jam, asal, tujuan,
  rehandling, kelas + ton, status Baru / Lama, keterangan).
  Keduanya: tanda ulang, jam "menit saja" dan nomor truk singkat diselesaikan program (ditandai kuning); kolom turunan tanggal
  muat (shift malam lewat tengah malam), oksida / sulfida, grade; pivot ritase & tonase.
- "rc": RC Drill / Chiptray Log — header (Hole ID, tanggal) + interval (Sample ID, From, To, Remark QAQC).

Prinsip: hasil AI = usulan. Sel yang diragukan AI ditandai, validasi otomatis menandai yang janggal, geologist mengedit dan
memverifikasi per baris; ekspor bawaan hanya baris terverifikasi. Tidak ada data contoh / tiruan bila AI gagal.
Data per proyek: <proyek>/_GCEx_Core/borang (borang.db + scan/)."""
from __future__ import annotations

import base64
import csv
import io
import json
import re
import shutil
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from . import core_io

router = APIRouter(prefix="/core/forms")
SUB = "borang"
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_ID = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7, "agu": 8, "ags": 8, "aug": 8, "sep": 9,
            "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12}

# ---------------------------------------------------------------- definisi jenis borang
TYPES: dict[str, dict] = {
    "ore": {
        "name": "Ore Spotter: Loading Pit → ROM / Stockpile",
        "header": [("tanggal", "Tanggal", "date"), ("shift", "Shift (I / II)", "text"), ("crew", "Nama crew / spotter", "text"),
                   ("lokasi", "Lokasi (pit)", "text"), ("excavator", "Excavator (EX)", "text")],
        "rows": [("no", "No", "text"), ("start", "Start loading", "time"), ("finish", "Finish loading", "time"), ("pit", "Pit / blok", "text"),
                 ("elevasi", "Elevasi", "text"), ("kelas", "Kelas material", "text"), ("unit", "Truck", "text"), ("ton", "Tonnage", "num"),
                 ("tujuan", "Tujuan dumping", "text")],
        "hint": ("Borang 'Form Loading (atau Rehandling) Ore dari Pit to ROM / Stockpile' (Ore Spotter di front loading), biasanya lanskap. "
                 "Header: NAMA CREW, LOKASI (pit), nomor excavator (mis. EX-123, ditulis tangan di dekat judul), TANGGAL, SHIFT (I / II). "
                 "Tabel bernomor, satu baris per ritase truk. Kolom dari kiri: NO; Start Loading; Finish Loading (jam ditulis di salah satu "
                 "dari dua kolom ini; baris berikutnya sering hanya menulis MENIT, mis. 13 -> salin apa adanya \"13\"); PIT; Elevation; lalu "
                 "kelompok kolom kelas material berwarna " + "OX-LG, SF-LG, OX-HG, SF-HG, OX-SG, SF-SG, OX-MO, SF-MO" + ", masing-masing dengan "
                 "sub-kolom TRUCK dan Tonnage: di setiap baris hanya SATU kelompok terisi -> isi 'kelas' dengan NAMA kelompok itu, 'unit' "
                 "dengan nomor truk persis seperti tertulis (boleh singkat, mis. 26) dan 'ton' dengan tonase; kolom terakhir Tujuan Dumping "
                 "(mis. ROM 418, kadang hanya angka atau \"〃 370\").\n"
                 "Baris yang hanya berisi PIT / Elevation tanpa truk tetap ditulis (unit & ton kosong). Abaikan coretan / tulisan yang dicoret.\n"
                 "TANDA ULANG: bila sel berisi tanda ulang (\" atau 〃 atau = atau ,, atau angka 4 / 11 kecil yang sebenarnya tanda ulang) atau "
                 "dilewati garis tegak / garis miring panjang dari baris di atas, tulis tepat \"〃\" (bila diikuti tulisan, mis. \"〃 370\", "
                 "tulis \"〃 370\")."),
    },
    "rom": {
        "name": "Ore ke Stockpile / Crusher (Rehandling / Direct)",
        "header": [("tanggal", "Tanggal", "date"), ("shift", "Shift (I / II)", "text"), ("crew", "Crew / spotter", "text"),
                   ("lokasi", "Lokasi", "text")],
        "rows": [("no", "No", "text"), ("unit", "Eq. No. Unit", "text"), ("start", "Start loading", "time"),
                 ("finish", "Finish loading", "time"), ("asal", "Asal material", "text"), ("tujuan", "Tujuan", "text"),
                 ("rehandling", "Rehandling tumpukan", "text"), ("kelas", "Kelas material", "text"), ("ton", "Ton", "num"),
                 ("status", "Status (Baru / Lama)", "text"), ("keterangan", "Keterangan", "text")],
        "hint": ("Borang 'Form Ore to Stockpile / Crusher (Rehandling / Direct)' (spotter di ROM / crusher), biasanya lanskap. Header: "
                 "CREW (nama spotter, boleh lebih dari satu), LOKASI, TANGGAL, SHIFT (I / II). Tabel bernomor, satu baris per ritase truk. "
                 "Kolom dari kiri: NO; Eq. No. Unit (nomor lambung truk, kadang diawali DT); Start Loading (sering kosong); Finish Loading "
                 "(jam, mis. 19.02; baris berikutnya sering hanya menulis MENIT, mis. 05 -> salin apa adanya \"05\"); Asal Material (mis. "
                 "Pit ..., ROM ..., OPP); Tujuan (mis. Crusher, ROM ...); Rehandling Tumpukan (tiga sub-kolom bernama tumpukan; isi "
                 "'rehandling' dengan NAMA sub-kolom yang dicentang, kosong bila tidak ada centang); lalu kolom kelas material berwarna "
                 "OX-LG, SF-LG, OX-HG, SF-HG, OX-SG, SF-SG, SCAT, OX-MO, SF-MO: di setiap baris hanya SATU kolom kelas berisi angka tonase "
                 "-> isi 'kelas' dengan NAMA kolom itu dan 'ton' dengan angkanya; Status Material (sub-kolom Baru / Lama yang dicentang -> "
                 "'Baru' atau 'Lama'); Keterangan (mis. Direct, Rehandling, OPP).\n"
                 "TANDA ULANG: bila sel berisi tanda ulang (\" atau = atau ,, ) atau dilewati garis tegak / garis miring yang menyambung "
                 "dari baris di atas, tulis tepat \"〃\" (jangan menyalin nilai di atas sendiri; program yang mengisinya)."),
    },
    "rc": {
        "name": "RC Drill / Chiptray Log",
        "header": [("hole_id", "Hole ID", "text"), ("tanggal", "Tanggal pengeboran", "date")],
        "rows": [("sample_id", "Sample ID", "text"), ("from_m", "From (m)", "num"), ("to_m", "To (m)", "num"), ("remark", "Remark (QAQC)", "text")],
        "hint": ("Borang RC Drill Logging / Chiptray: header berisi HOLE ID dan tanggal pengeboran. Tabel berisi satu baris per interval "
                 "sampel: Sample ID, From (m), To (m), dan Remark (QAQC: STD = standar / CRM, BLANK, DUP = duplikat; kosong bila sampel "
                 "biasa). Formulir mungkin difoto lanskap (berputar 90 derajat): baca sesuai arah tulisan."),
    },
}
KELAS = ["OX-LG", "SF-LG", "OX-HG", "SF-HG", "OX-SG", "SF-SG", "SCAT", "OX-MO", "SF-MO"]
ORE_TYPES = ("ore", "rom")
SHIFT_DS = (6, 18)  # shift I / siang (DS) 06:00-18:00, shift II / malam (NS) 18:00-06:00
# sel kosong hasil AI -> diisi dari baris atas (ditandai kuning); tanda ulang -> nilai baris atas
CARRY = {"ore": ("pit", "elevasi", "tujuan"), "rom": ("asal", "tujuan", "status", "keterangan")}
DITTO = {"ore": ("start", "finish", "pit", "elevasi", "kelas", "tujuan"),
         "rom": ("start", "finish", "asal", "tujuan", "rehandling", "kelas", "status", "keterangan")}
QAQC = {"STD": "STD", "STANDARD": "STD", "CRM": "STD", "STANDAR": "STD", "BLANK": "BLANK", "BLK": "BLANK", "DUP": "DUP", "DUPLICATE": "DUP",
        "DUPLIKAT": "DUP", "FD": "DUP", "FIELD DUP": "DUP"}

_DDL = """
CREATE TABLE IF NOT EXISTS docs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, uid TEXT UNIQUE, file TEXT NOT NULL, name TEXT, src TEXT, page INTEGER DEFAULT 1,
  type TEXT NOT NULL, rot INTEGER DEFAULT 0, w INTEGER, h INTEGER, header_json TEXT DEFAULT '{}', hdr_unc TEXT DEFAULT '[]',
  status TEXT DEFAULT 'pending', error TEXT, ai_model TEXT, ai_at TEXT, ai_secs REAL, ai_note TEXT, ai_json TEXT,
  by TEXT, at TEXT, edited_by TEXT, edited_at TEXT
);
CREATE TABLE IF NOT EXISTS rows (
  id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER NOT NULL, idx INTEGER NOT NULL, data_json TEXT NOT NULL,
  unc_json TEXT DEFAULT '[]', edited_json TEXT DEFAULT '[]', verified INTEGER DEFAULT 0, verified_by TEXT, verified_at TEXT,
  src TEXT DEFAULT 'ai', by TEXT, at TEXT
);
CREATE INDEX IF NOT EXISTS ix_rows_doc ON rows(doc_id);
CREATE TABLE IF NOT EXISTS history (
  id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER, what TEXT, old TEXT, new TEXT, src TEXT, by TEXT, at TEXT
);
"""


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.db = root / "borang.db"
        self.scans = root / "scan"
        self.lock = threading.RLock()

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
        s.scans.mkdir(exist_ok=True)
        with s.conn() as c:
            c.executescript(_DDL)
        _STORES[key] = s
        return s


def _hist(c, doc_id, what, old, new, src, by) -> None:
    c.execute("INSERT INTO history (doc_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
              (doc_id, what, None if old is None else str(old)[:2000], None if new is None else str(new)[:2000], src, by, core_io.now()))


# ---------------------------------------------------------------- normalisasi nilai
def parse_date(t: Any) -> Optional[date]:
    """Tanggal tulisan lapangan: 30-Oct-26, 30 Okt 2026, 20/01/2026, 2026-01-20, 20.01.26 -> date (hari dulu)."""
    if t in (None, ""):
        return None
    if isinstance(t, (date, datetime)):
        return t if isinstance(t, date) else t.date()
    s = str(t).strip()
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    try:
        if m:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        m = re.match(r"^(\d{1,2})[-/. ]([A-Za-z]{3,9})[-/. ,]*(\d{2,4})$", s)
        if m:
            mo = MONTH_ID.get(m.group(2)[:3].lower())
            if mo:
                y = int(m.group(3))
                return date(y + 2000 if y < 100 else y, mo, int(m.group(1)))
        m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$", s)
        if m:
            y = int(m.group(3))
            return date(y + 2000 if y < 100 else y, int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None
    return None


def parse_time(t: Any) -> Optional[str]:
    s = re.sub(r"[.,;\-]", ":", str(t or "").strip()).replace(" ", "")
    m = re.match(r"^(\d{1,2}):?(\d{2})$", s)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return f"{h:02d}:{mi:02d}" if 0 <= h < 24 and 0 <= mi < 60 else None


def parse_num(t: Any) -> Optional[float]:
    if t in (None, ""):
        return None
    if isinstance(t, (int, float)):
        return float(t)
    s = str(t).strip().replace(" ", "")
    if re.match(r"^-?\d+,\d+$", s):
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def qaqc(t: Any) -> str:
    s = str(t or "").strip().upper()
    return QAQC.get(s, s)


def is_ditto(v: Any) -> bool:
    """Tanda ulang di borang: 〃 " '' = ,, | / (atau tulisan idem / dto)."""
    t = str(v or "").strip().lower()
    return bool(t) and (t in ("idem", "dto", "do", "sda") or re.fullmatch(r"[\"'=|/\\‖〃,`´“”]+", t) is not None)


def _prefix(v: str) -> str:
    """'ROM 418' / 'ROM-418' / 'ROM A1' -> 'ROM' (teks sebelum kata terakhir yang mengandung angka)."""
    t = str(v or "").strip()
    m = re.match(r"^(.*?)[\s\-:]+\S*\d\S*$", t)
    return (m.group(1) if m else re.sub(r"[\d.,]+$", "", t)).strip()


def fill_ore(ftype: str, lst: list[dict], carry_empty: bool) -> list[tuple[dict, list[str]]]:
    """Selesaikan tulisan singkat di borang ore spotter:
    - tanda ulang (〃 " = ,, | /) -> nilai baris atas; '〃 370' -> 'ROM 370' (awalan teks baris atas); tujuan hanya angka -> awalan atas;
    - jam yang hanya menulis menit (19.02 lalu 05 -> 19:05; menit lebih kecil -> jam berikutnya);
    - nomor truk singkat (4026 lalu 26 -> 4026; hanya borang loading pit);
    - carry_empty (hasil AI): sel kosong di kolom 'bawaan' (pit / elevasi / tujuan / asal / status / keterangan) diisi dari baris atas;
      baris AI tanpa truk & tonase (hanya mengubah pit / elevasi) tidak dijadikan baris, nilainya dibawa ke baris berikutnya.
    Kembalikan (data, field yang diisi program) per baris."""
    prev: dict[str, str] = {}
    out = []
    dit, car = DITTO[ftype], CARRY[ftype]
    for d in lst:
        x = dict(d)
        filled = []
        for k in dit:
            v = str(x.get(k) or "").strip()
            m = re.match(r"^[\"'=|/\\‖〃,`´“”]+\s*(\S.*)$", v)
            if m and k == "tujuan" and prev.get(k):
                x[k] = (_prefix(prev[k]) + " " + m.group(1)).strip()
                filled.append(k)
            elif is_ditto(v) or (carry_empty and not v and k in car and prev.get(k)):
                x[k] = prev.get(k, "")
                if x[k]:
                    filled.append(k)
            elif k == "tujuan" and re.fullmatch(r"\d{2,4}", v) and _prefix(prev.get(k, "")):
                x[k] = _prefix(prev[k]) + " " + v
                filled.append(k)
        for k in ("start", "finish"):
            v = str(x.get(k) or "").strip()
            pv = prev.get("start") if (k == "start" and prev.get("start")) else (prev.get("finish") or prev.get("start"))
            pt = parse_time(pv) if pv else None
            if re.fullmatch(r"\d{1,2}", v) and pt:
                h, m0 = int(pt[:2]), int(pt[3:])
                mi = int(v)
                if mi < 60:
                    x[k] = f"{(h + (1 if mi < m0 else 0)) % 24:02d}:{mi:02d}"
                    filled.append(k)
            elif parse_time(v):
                x[k] = parse_time(v)
        if ftype == "ore":
            u = re.sub(r"\s+", "", str(x.get("unit") or ""))
            pu = prev.get("unit", "")
            if re.fullmatch(r"\d{1,2}", u) and re.fullmatch(r"\d{3,}", pu):
                x["unit"] = pu[:len(pu) - len(u)] + u
                filled.append("unit")
            if carry_empty and not str(x.get("unit") or "").strip() and not str(x.get("ton") or "").strip():
                for k in ("pit", "elevasi", "tujuan", "start", "finish"):
                    if str(x.get(k) or "").strip():
                        prev[k] = str(x[k])
                continue
        for k, v in x.items():
            if str(v or "").strip():
                prev[k] = str(v)
        out.append((x, list(dict.fromkeys(filled))))
    return out


def shift_code(t: Any) -> str:
    """Siang / pagi / day / I / 1 -> DS; malam / night / II / 2 -> NS."""
    s = str(t or "").strip().lower()
    if s in ("i", "1", "l", "shift i", "shift 1"):
        return "DS"
    if s in ("ii", "2", "ll", "11", "shift ii", "shift 2"):
        return "NS"
    if s in ("ds", "day", "siang", "pagi") or "siang" in s or "pagi" in s or s.startswith("day"):
        return "DS"
    if s in ("ns", "night", "malam") or "malam" in s or s.startswith("night"):
        return "NS"
    return ""


# ---------------------------------------------------------------- dokumen
def docs(s: Store) -> list[dict]:
    with s.conn() as c:
        out = []
        for r in c.execute("SELECT * FROM docs ORDER BY id"):
            d = _doc(r)
            st = c.execute("SELECT COUNT(*) n, SUM(verified) v, SUM(CASE WHEN unc_json != '[]' THEN 1 ELSE 0 END) u FROM rows WHERE doc_id=?",
                           (r["id"],)).fetchone()
            d["n_rows"], d["n_ver"], d["n_unc"] = st["n"] or 0, st["v"] or 0, st["u"] or 0
            out.append(d)
        return out


def _doc(r: sqlite3.Row) -> dict:
    d = dict(r)
    for k, dv in (("header_json", {}), ("hdr_unc", [])):
        try:
            d[k] = json.loads(d.get(k) or json.dumps(dv))
        except ValueError:
            d[k] = dv
    d["header"] = d.pop("header_json")
    d.pop("ai_json", None)
    return d


def doc(s: Store, did: int) -> dict:
    with s.conn() as c:
        r = c.execute("SELECT * FROM docs WHERE id=?", (did,)).fetchone()
    if not r:
        raise ValueError(f"Borang #{did} tidak ada.")
    return _doc(r)


def rows(s: Store, did: int) -> list[dict]:
    with s.conn() as c:
        out = []
        for r in c.execute("SELECT * FROM rows WHERE doc_id=? ORDER BY idx, id", (did,)):
            d = dict(r)
            d["data"] = json.loads(d.pop("data_json") or "{}")
            d["unc"] = json.loads(d.pop("unc_json") or "[]")
            d["edited"] = json.loads(d.pop("edited_json") or "[]")
            d["verified"] = bool(d["verified"])
            out.append(d)
        return out


def _pdf_pages(src: Path) -> list:
    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise ValueError("Pembaca PDF (pypdfium2) tidak terpasang di DB-Ex ini. Pasang ulang DB-Ex versi terbaru, atau simpan "
                         "halaman borang sebagai JPG / PNG.") from None
    pdf = pdfium.PdfDocument(str(src))
    out = []
    try:
        for i in range(len(pdf)):
            pg = pdf[i]
            w, h = pg.get_size()
            scale = min(4.0, max(1.5, 2400 / max(w, h)))  # +- 2400 px sisi panjang (cukup untuk tulisan tangan)
            out.append(pg.render(scale=scale).to_pil().convert("RGB"))
    finally:
        pdf.close()
    return out


def add_file(s: Store, src: str, ftype: str, by: str) -> list[dict]:
    """Tambah scan / foto / PDF borang (disalin ke proyek). PDF dipecah: satu borang per halaman."""
    if ftype not in TYPES:
        raise ValueError(f"Jenis borang tidak dikenal: {ftype}")
    sp = Path(src)
    if not sp.is_file():
        raise ValueError(f"File tidak ditemukan: {src}")
    ext = sp.suffix.lower()
    from PIL import Image, ImageOps
    pages: list = []
    if ext == ".pdf":
        pages = _pdf_pages(sp)
        if not pages:
            raise ValueError(f"{sp.name}: PDF tanpa halaman.")
    elif ext in IMG_EXT:
        with Image.open(sp) as im:
            pages = [ImageOps.exif_transpose(im).convert("RGB")]
    else:
        raise ValueError(f"{sp.name}: format tidak dikenali (JPG, PNG, TIFF, BMP, WEBP, PDF).")
    made = []
    for i, im in enumerate(pages, 1):
        uid = uuid.uuid4().hex[:12]
        name = re.sub(r"[^\w.-]+", "_", sp.stem)[:60]
        fn = f"{name}_{uid}" + ("_hal%02d" % i if len(pages) > 1 else "") + ".jpg"
        im.save(s.scans / fn, "JPEG", quality=92)
        with s.lock, s.conn() as c:
            did = c.execute("INSERT INTO docs (uid, file, name, src, page, type, w, h, by, at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (uid, fn, sp.name + (f" hal {i}" if len(pages) > 1 else ""), str(sp), i, ftype, im.width, im.height, by,
                             core_io.now())).lastrowid
            _hist(c, did, "tambah", None, sp.name, "tambah", by)
        made.append(doc(s, did))
    return made


def delete_doc(s: Store, did: int, by: str) -> None:
    d = doc(s, did)
    with s.lock, s.conn() as c:
        c.execute("DELETE FROM rows WHERE doc_id=?", (did,))
        c.execute("DELETE FROM docs WHERE id=?", (did,))
        _hist(c, did, "hapus", d["name"], None, "hapus", by)
    try:
        (s.scans / d["file"]).unlink()
    except OSError:
        pass


def update_doc(s: Store, did: int, values: dict, by: str) -> dict:
    """values: type, rot (0/90/180/270), header (dict, field diedit tidak ditandai ragu lagi)."""
    d = doc(s, did)
    sets, vals = [], []
    with s.lock, s.conn() as c:
        if "type" in values:
            if values["type"] not in TYPES:
                raise ValueError("Jenis borang tidak dikenal.")
            if values["type"] != d["type"]:
                n = c.execute("SELECT COUNT(*) FROM rows WHERE doc_id=?", (did,)).fetchone()[0]
                if n:
                    raise ValueError("Jenis borang tidak bisa diganti setelah ada baris; hapus baris dulu atau tambahkan ulang file-nya.")
                sets.append("type=?")
                vals.append(values["type"])
        if "rot" in values:
            r = int(values["rot"]) % 360
            if r not in (0, 90, 180, 270):
                raise ValueError("Rotasi harus 0, 90, 180 atau 270.")
            sets.append("rot=?")
            vals.append(r)
        if "header" in values:
            ftype = values.get("type", d["type"])
            keys = {k for k, _l, _t in TYPES[ftype]["header"]}
            h = dict(d["header"])
            unc = [k for k in d["hdr_unc"]]
            for k, v in (values["header"] or {}).items():
                if k in keys:
                    v = str(v or "").strip()
                    if h.get(k) != v:
                        _hist(c, did, f"header {k}", h.get(k), v, "edit", by)
                        h[k] = v
                    if k in unc:
                        unc.remove(k)
            sets += ["header_json=?", "hdr_unc=?"]
            vals += [json.dumps(h, ensure_ascii=False), json.dumps(unc)]
        if sets:
            sets += ["edited_by=?", "edited_at=?"]
            vals += [by, core_io.now()]
            c.execute(f"UPDATE docs SET {', '.join(sets)} WHERE id=?", vals + [did])
    return doc(s, did)


def save_rows(s: Store, did: int, lst: list[dict], by: str) -> list[dict]:
    """Simpan seluruh tabel borang (urutan = urutan daftar). Baris: {id?, data, verified?}. Sel yang berubah dari isian AI
    ditandai 'diedit' dan tidak lagi ragu. Baris yang tidak ada di daftar dihapus."""
    d = doc(s, did)
    keys = [k for k, _l, _t in TYPES[d["type"]]["rows"]]
    old = {r["id"]: r for r in rows(s, did)}
    keep = set()
    datas = [{k: ("" if (r.get("data") or {}).get(k) is None else str((r.get("data") or {}).get(k)).strip()) for k in keys} for r in lst]
    if d["type"] in ORE_TYPES:  # tanda ulang / jam menit saja / nomor truk singkat yang diketik pengguna -> nilai lengkap
        datas = [x for x, _f in fill_ore(d["type"], datas, False)]
    with s.lock, s.conn() as c:
        for i, r in enumerate(lst):
            data = datas[i]
            ver = bool(r.get("verified"))
            rid = r.get("id")
            if rid in old:
                o = old[rid]
                unc, ed = list(o["unc"]), list(o["edited"])
                for k in keys:
                    if str(o["data"].get(k, "") or "") != data[k]:
                        if k not in ed:
                            ed.append(k)
                        if k in unc:
                            unc.remove(k)
                        _hist(c, did, f"baris {i + 1} {k}", o["data"].get(k), data[k], "edit", by)
                vb, va = (o["verified_by"], o["verified_at"]) if ver == o["verified"] else ((by, core_io.now()) if ver else (None, None))
                c.execute("UPDATE rows SET idx=?, data_json=?, unc_json=?, edited_json=?, verified=?, verified_by=?, verified_at=? WHERE id=?",
                          (i, json.dumps(data, ensure_ascii=False), json.dumps(unc), json.dumps(ed), int(ver), vb, va, rid))
                keep.add(rid)
            else:
                nid = c.execute("INSERT INTO rows (doc_id, idx, data_json, edited_json, verified, verified_by, verified_at, src, by, at) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (did, i, json.dumps(data, ensure_ascii=False), json.dumps(keys), int(ver), by if ver else None,
                                 core_io.now() if ver else None, "manual", by, core_io.now())).lastrowid
                keep.add(nid)
                _hist(c, did, f"baris {i + 1}", None, json.dumps(data, ensure_ascii=False), "tambah", by)
        for rid in set(old) - keep:
            c.execute("DELETE FROM rows WHERE id=?", (rid,))
            _hist(c, did, "hapus baris", json.dumps(old[rid]["data"], ensure_ascii=False), None, "hapus", by)
        c.execute("UPDATE docs SET edited_by=?, edited_at=? WHERE id=?", (by, core_io.now(), did))
    return rows(s, did)


def verify_all(s: Store, did: int, on: bool, by: str) -> list[dict]:
    with s.lock, s.conn() as c:
        if on:
            c.execute("UPDATE rows SET verified=1, verified_by=?, verified_at=? WHERE doc_id=? AND verified=0", (by, core_io.now(), did))
        else:
            c.execute("UPDATE rows SET verified=0, verified_by=NULL, verified_at=NULL WHERE doc_id=?", (did,))
        _hist(c, did, "verifikasi semua" if on else "batal verifikasi", None, None, "edit", by)
    return rows(s, did)


def history(s: Store, did: int) -> list[dict]:
    with s.conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM history WHERE doc_id=? ORDER BY id DESC LIMIT 300", (did,))]


# ---------------------------------------------------------------- AI vision (Ollama)
def ai_schema(ftype: str) -> dict:
    t = TYPES[ftype]
    hp = {k: {"type": "string"} for k, _l, _t in t["header"]}
    rp = {k: {"type": "string"} for k, _l, _t in t["rows"]}
    rp["ragu"] = {"type": "array", "items": {"type": "string", "enum": [k for k, _l, _t in t["rows"]]}}
    if ftype in ORE_TYPES:
        rp["kelas"] = {"type": "string", "enum": [""] + KELAS + ["〃"]}
    if ftype == "rom":
        rp["status"] = {"type": "string", "enum": ["", "Baru", "Lama", "〃"]}
    return {"type": "object", "required": ["header", "rows"], "properties": {
        "header": {"type": "object", "properties": {**hp, "ragu": {"type": "array", "items": {"type": "string", "enum": list(hp)}}}},
        "rows": {"type": "array", "items": {"type": "object", "properties": rp, "required": [k for k, _l, _t in t["rows"]]}},
        "catatan": {"type": "string"}}}


def ai_prompt(ftype: str, extra: str = "") -> str:
    t = TYPES[ftype]
    h = ", ".join(f"{k} ({lab})" for k, lab, _ in t["header"])
    r = ", ".join(f"{k} ({lab})" for k, lab, _ in t["rows"])
    return (f"Anda petugas data entry geologi tambang. Baca formulir lapangan tulisan tangan pada gambar ini dengan teliti.\n{t['hint']}\n"
            f"Isi 'header' dengan field: {h}.\nIsi 'rows' dengan SATU objek per baris tabel yang terisi, field: {r}. Urutkan dari atas ke bawah. "
            "Lewati baris kosong; jangan mengarang baris yang tidak ada.\n"
            "Salin angka & kode persis seperti tertulis (jangan dibulatkan / diterjemahkan). "
            + ("" if ftype in ORE_TYPES else "Bila tulisan sama dengan baris di atasnya (tanda ulang \" atau ditto), isi dengan nilai baris di atasnya. ")
            + "Bila satu sel tidak terbaca jelas, tetap isi tebakan terbaik "
            "dan cantumkan nama field-nya di 'ragu' baris itu (header: di header.ragu). Sel kosong = \"\".\n"
            + (f"Catatan pengguna: {extra.strip()}\n" if extra and extra.strip() else "")
            + "Jawab hanya JSON sesuai skema.")


def _image_b64(s: Store, d: dict, max_px: int) -> str:
    from PIL import Image
    with Image.open(s.scans / d["file"]) as im:
        im = im.convert("RGB")
        if d.get("rot"):
            im = im.rotate(-int(d["rot"]), expand=True)  # rot searah jarum jam
        k = max_px / max(im.size)
        if k < 1:
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        b = io.BytesIO()
        im.save(b, "JPEG", quality=90)
    return base64.b64encode(b.getvalue()).decode()


def ai_read(s: Store, did: int, host: str, model: str, extra: str = "", max_px: int = 2000, by: str = "", timeout: float = 900) -> dict:
    d = doc(s, did)
    body = {"model": model, "messages": [{"role": "user", "content": ai_prompt(d["type"], extra), "images": [_image_b64(s, d, max_px)]}],
            "stream": False, "format": ai_schema(d["type"]), "options": {"temperature": 0, "num_ctx": 16384}, "keep_alive": "15m"}
    t0 = time.time()
    try:
        j = core_io._http((host or core_io.DEFAULT_HOST).rstrip("/") + "/api/chat", body, timeout=timeout)
        if j.get("error"):
            raise RuntimeError("Ollama: " + str(j["error"]))
        res = core_io._parse_json((j.get("message") or {}).get("content", ""))
    except Exception as e:  # noqa: BLE001 - TIDAK ada data tiruan: borang tetap kosong & galat dicatat
        with s.lock, s.conn() as c:
            c.execute("UPDATE docs SET status='error', error=? WHERE id=?", (str(e)[:500], did))
        raise
    return apply_ai(s, did, res, model, time.time() - t0, by)


def apply_ai(s: Store, did: int, res: dict, model: str, secs: float, by: str = "") -> dict:
    """Tulis jawaban AI: header (field yang sudah diedit pengguna dipertahankan) + baris (MENGGANTI semua baris)."""
    d = doc(s, did)
    t = TYPES[d["type"]]
    hk = [k for k, _l, _tt in t["header"]]
    rk = [k for k, _l, _tt in t["rows"]]
    rh = (res or {}).get("header") or {}
    with s.conn() as c:
        edited_hdr = {r["what"][7:] for r in c.execute("SELECT what FROM history WHERE doc_id=? AND what LIKE 'header %' AND src='edit'", (did,))}
    h = dict(d["header"])
    for k in hk:
        if k not in edited_hdr and str(rh.get(k) or "").strip():
            h[k] = str(rh[k]).strip()
    hunc = [k for k in (rh.get("ragu") or []) if k in hk and k not in edited_hdr]
    out_rows = []
    for r in (res or {}).get("rows") or []:
        if not isinstance(r, dict):
            continue
        data = {k: str(r.get(k) if r.get(k) is not None else "").strip() for k in rk}
        if not any(v for k, v in data.items() if k != "no"):
            continue
        out_rows.append((data, [k for k in (r.get("ragu") or []) if k in rk]))
    if d["type"] in ORE_TYPES and out_rows:
        res_f = fill_ore(d["type"], [dict(x, _u=u) for x, u in out_rows], True)
        out_rows = [({k: v for k, v in x.items() if k != "_u"}, list(dict.fromkeys(x["_u"] + f))) for x, f in res_f]
    with s.lock, s.conn() as c:
        c.execute("DELETE FROM rows WHERE doc_id=?", (did,))
        for i, (data, unc) in enumerate(out_rows):
            c.execute("INSERT INTO rows (doc_id, idx, data_json, unc_json, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (did, i, json.dumps(data, ensure_ascii=False), json.dumps(unc), "ai:" + model, by or "AI", core_io.now()))
        c.execute("UPDATE docs SET header_json=?, hdr_unc=?, status='done', error=NULL, ai_model=?, ai_at=?, ai_secs=?, ai_note=?, ai_json=? "
                  "WHERE id=?", (json.dumps(h, ensure_ascii=False), json.dumps(hunc), model, core_io.now(), round(secs, 1),
                                 str((res or {}).get("catatan") or "")[:500], json.dumps(res, ensure_ascii=False)[:200000], did))
        _hist(c, did, "AI membaca", None, f"{len(out_rows)} baris", "ai:" + model, by or "AI")
    return {"doc": doc(s, did), "rows": rows(s, did)}


# ---------------------------------------------------------------- turunan, validasi, pivot
def records(d: dict, rs: list[dict]) -> list[dict]:
    """Baris lengkap (header disebar ke tiap baris) + kolom turunan + nilai ternormalisasi."""
    h = d["header"]
    out = []
    for r in rs:
        x = dict(r["data"])
        rec: dict[str, Any] = {"_row": r["id"], "_idx": r["idx"], "_verified": r["verified"], "_doc": d["id"], "_uid": d["uid"],
                               "_name": d["name"], "_key": f"{d['uid']}:{r['id']}"}
        if d["type"] in ORE_TYPES:
            tg = parse_date(h.get("tanggal"))
            ks = shift_code(h.get("shift"))
            jam = parse_time(x.get("finish")) or parse_time(x.get("start"))
            tm = tg
            if tg and jam and ks == "NS" and int(jam[:2]) < 12:  # shift malam melewati tengah malam -> tanggal kalender berikutnya
                tm = date.fromordinal(tg.toordinal() + 1)
            kl = str(x.get("kelas") or "").strip().upper().replace(" ", "")
            kl = next((k for k in KELAS if k.replace("-", "") == kl.replace("-", "")), kl)
            unit = str(x.get("unit") or "").strip().upper()
            rec.update({"tanggal": tg.isoformat() if tg else str(h.get("tanggal") or ""), "shift": h.get("shift") or "", "kode_shift": ks,
                        "crew": h.get("crew") or "", "lokasi": h.get("lokasi") or "", "no": x.get("no") or "",
                        "tanggal_muat": tm.isoformat() if tm else "", "start": parse_time(x.get("start")) or x.get("start") or "",
                        "finish": parse_time(x.get("finish")) or x.get("finish") or "", "jam": jam or "",
                        "unit": re.sub(r"^DT[\s.\-]*", "", unit).replace(" ", ""), "kelas": kl,
                        "material": {"OX": "OKSIDA", "SF": "SULFIDA"}.get(kl[:2], kl), "grade": kl[3:] if "-" in kl else "",
                        "ton": parse_num(x.get("ton")), "tujuan": re.sub(r"\s+", " ", str(x.get("tujuan") or "")).strip()})
            if d["type"] == "ore":
                rec.update({"excavator": re.sub(r"\s+", "", str(h.get("excavator") or "")).upper(),
                            "pit": x.get("pit") or h.get("lokasi") or "", "elevasi": parse_num(x.get("elevasi")),
                            "front": " · ".join(str(v) for v in (x.get("pit") or h.get("lokasi") or "", x.get("elevasi") or "") if v)})
            else:
                ket = str(x.get("keterangan") or "").strip()
                rec.update({"asal": x.get("asal") or "", "rehandling": x.get("rehandling") or "",
                            "status": (x.get("status") or "").strip().capitalize(), "keterangan": ket,
                            "jenis": "REHANDLING" if re.search(r"rehand", ket, re.I) else ("DIRECT" if re.search(r"dir", ket, re.I)
                                                                                          else ket.upper())})
        else:
            tg = parse_date(h.get("tanggal"))
            rec.update({"hole_id": (h.get("hole_id") or "").strip(), "tanggal": tg.isoformat() if tg else str(h.get("tanggal") or ""),
                        "sample_id": (x.get("sample_id") or "").strip(), "from_m": parse_num(x.get("from_m")), "to_m": parse_num(x.get("to_m")),
                        "remark": qaqc(x.get("remark"))})
        out.append(rec)
    return out


def validate(d: dict, rs: list[dict], others: Optional[list[dict]] = None) -> dict:
    """Pemeriksaan otomatis -> {"header": {field: pesan}, "rows": {row_id: {field: pesan}}, "n": jumlah}."""
    hdr: dict[str, str] = {}
    out: dict[int, dict[str, str]] = {}

    def bad(r, k, m):
        out.setdefault(r["id"], {})[k] = m
    h = d["header"]
    if h.get("tanggal") and not parse_date(h.get("tanggal")):
        hdr["tanggal"] = "tanggal tidak dikenali (mis. 30-Oct-26 atau 30/10/2026)"
    if d["type"] in ORE_TYPES:
        ks = shift_code(h.get("shift"))
        if not ks:
            hdr["shift"] = "shift harus I / II (siang / malam)"
        if d["type"] == "ore" and not str(h.get("excavator") or "").strip():
            hdr["excavator"] = "nomor excavator kosong"
        prev_no, prev_t = None, None
        tk = "finish" if d["type"] == "rom" else None
        for r in rs:
            x = r["data"]
            no = parse_num(x.get("no"))
            if no is not None and prev_no is not None and no <= prev_no:
                bad(r, "no", f"nomor tidak urut (sebelumnya {prev_no:g})")
            prev_no = no if no is not None else prev_no
            if not str(x.get("unit") or "").strip():
                bad(r, "unit", "nomor truk kosong")
            for k in ("start", "finish"):
                if x.get(k) and not parse_time(x.get(k)):
                    bad(r, k, "jam tidak valid (HH:MM)")
            k_jam = tk or ("finish" if parse_time(x.get("finish")) else "start")
            jam = parse_time(x.get(k_jam))
            if not x.get("start") and not x.get("finish"):
                bad(r, tk or "start", "jam loading kosong")
            elif jam:
                hh = int(jam[:2])
                if ks == "DS" and not SHIFT_DS[0] <= hh < SHIFT_DS[1]:
                    bad(r, k_jam, f"jam {jam} di luar shift siang (I, {SHIFT_DS[0]:02d}:00-{SHIFT_DS[1]:02d}:00) — periksa jam / shift")
                elif ks == "NS" and SHIFT_DS[0] <= hh < SHIFT_DS[1]:
                    bad(r, k_jam, f"jam {jam} di luar shift malam (II, {SHIFT_DS[1]:02d}:00-{SHIFT_DS[0]:02d}:00) — periksa jam / shift")
                mins = hh * 60 + int(jam[3:]) + (1440 if ks == "NS" and hh < 12 else 0)
                if prev_t is not None and mins < prev_t[0]:
                    bad(r, k_jam, f"jam mundur dari {prev_t[1]}")
                prev_t = (mins, jam)
            v = parse_num(x.get("ton"))
            if x.get("ton") in (None, ""):
                bad(r, "ton", "tonase kosong")
            elif v is None:
                bad(r, "ton", "tonase harus angka")
            elif v <= 0 or v > 400:
                bad(r, "ton", "tonase di luar 0-400 t")
            kl = str(x.get("kelas") or "").strip().upper().replace(" ", "").replace("-", "")
            if not kl:
                bad(r, "kelas", "kelas material kosong (kolom tempat tonase ditulis)")
            elif kl not in {k.replace("-", "") for k in KELAS}:
                bad(r, "kelas", "kelas bukan " + " / ".join(KELAS))
            if not str(x.get("tujuan") or "").strip():
                bad(r, "tujuan", "tujuan kosong")
            if d["type"] == "ore":
                if x.get("elevasi") and parse_num(x.get("elevasi")) is None:
                    bad(r, "elevasi", "elevasi harus angka")
                u = re.sub(r"\s+", "", str(x.get("unit") or ""))
                if u and re.fullmatch(r"\d{1,2}", u):
                    bad(r, "unit", "nomor truk singkat tanpa nomor lengkap di atasnya")
            else:
                if not str(x.get("asal") or "").strip():
                    bad(r, "asal", "asal material kosong")
                st = str(x.get("status") or "").strip().lower()
                if st and st not in ("baru", "lama"):
                    bad(r, "status", "status harus Baru / Lama")
    else:
        if not (h.get("hole_id") or "").strip():
            hdr["hole_id"] = "Hole ID kosong"
        seen: dict[str, int] = {}
        prev = None
        for r in rs:
            x = r["data"]
            f, t = parse_num(x.get("from_m")), parse_num(x.get("to_m"))
            if f is None:
                bad(r, "from_m", "From harus angka")
            if t is None:
                bad(r, "to_m", "To harus angka")
            if f is not None and t is not None and t <= f:
                bad(r, "to_m", "To harus lebih besar dari From")
            if prev is not None and f is not None and prev[0] is not None:
                if f > prev[0] + 1e-6:
                    bad(r, "from_m", f"interval bolong: baris sebelumnya berakhir di {prev[0]:g} m")
                elif f < prev[0] - 1e-6:
                    bad(r, "from_m", f"tumpang-tindih dengan baris sebelumnya (berakhir {prev[0]:g} m)")
            prev = (t, r)
            sid = (x.get("sample_id") or "").strip().upper()
            if not sid:
                bad(r, "sample_id", "Sample ID kosong")
            elif sid in seen:
                bad(r, "sample_id", f"Sample ID kembar (baris {seen[sid] + 1})")
            else:
                seen[sid] = r["idx"]
            rm = qaqc(x.get("remark"))
            if rm and rm not in ("STD", "BLANK", "DUP"):
                bad(r, "remark", f"remark '{x.get('remark')}' bukan STD / BLANK / DUP")
        # nomor sampel berurutan: angka terakhir di Sample ID naik 1 per baris
        nums = []
        for r in rs:
            m = re.search(r"(\d+)(?!.*\d)", str(r["data"].get("sample_id") or ""))
            nums.append((int(m.group(1)) if m else None, r))
        for (a, _ra), (b, rb) in zip(nums, nums[1:]):
            if a is not None and b is not None and b != a + 1 and "sample_id" not in out.get(rb["id"], {}):
                bad(rb, "sample_id", f"nomor sampel meloncat dari {a} ke {b}")
        for o in others or []:  # Sample ID sama di borang lain
            for r in rs:
                sid = (r["data"].get("sample_id") or "").strip().upper()
                if sid and sid in o["ids"] and "sample_id" not in out.get(r["id"], {}):
                    bad(r, "sample_id", f"Sample ID sudah ada di borang {o['name']}")
    return {"header": hdr, "rows": out, "n": len(hdr) + sum(len(v) for v in out.values())}


def other_ids(s: Store, did: int) -> list[dict]:
    out = []
    for d in docs(s):
        if d["id"] == did or d["type"] != "rc":
            continue
        out.append({"name": d["name"], "ids": {(r["data"].get("sample_id") or "").strip().upper() for r in rows(s, d["id"])}})
    return out


LAB = {"tanggal": "Tanggal", "shift": "Shift", "kode_shift": "Kode", "front": "Front (pit · elevasi)", "excavator": "Excavator",
       "tujuan": "Tujuan", "kelas": "Kelas material", "asal": "Asal material", "jenis": "Direct / Rehandling", "unit": "Truck",
       "ritase": "Ritase", "tonase": "Tonase"}
PIVOTS = {
    "ore": [("PIVOT_PER_SHIFT", "Per shift", ["tanggal", "shift", "kode_shift"]),
            ("PIVOT_PER_FRONT", "Per front (pit · elevasi · excavator)", ["tanggal", "front", "excavator"]),
            ("PIVOT_TUJUAN_KELAS", "Per tujuan dumping × kelas material", ["tanggal", "tujuan", "kelas"])],
    "rom": [("PIVOT_PER_SHIFT", "Per shift", ["tanggal", "shift", "kode_shift"]),
            ("PIVOT_ASAL_TUJUAN", "Per asal → tujuan (direct / rehandling)", ["tanggal", "asal", "tujuan", "jenis"]),
            ("PIVOT_TUJUAN_KELAS", "Per tujuan × kelas material", ["tanggal", "tujuan", "kelas"])],
}


def pivots(recs: list[dict], ftype: str = "ore") -> list[dict]:
    """Pivot ritase & tonase -> [{"key", "title", "cols": [[k, label]], "rows": [dict]}] (juga untuk sheet Excel & view SQLite)."""
    out = []
    for key, title, keys in PIVOTS.get(ftype, []):
        g: dict = {}
        for r in recs:
            g.setdefault(tuple(r.get(k) for k in keys), []).append(r)
        rows_ = [dict(zip(keys, k), ritase=len(v), tonase=round(sum(x["ton"] or 0 for x in v), 2))
                 for k, v in sorted(g.items(), key=lambda kv: [str(x) for x in kv[0]])]
        out.append({"key": key, "title": title, "cols": [[k, LAB.get(k, k)] for k in keys + ["ritase", "tonase"]], "rows": rows_})
    return out


# ---------------------------------------------------------------- ekspor
OUT = {
    "ore": [("TANGGAL", "Tanggal", "tanggal", "DATE"), ("SHIFT", "Shift", "shift", "TEXT"), ("KODE_SHIFT", "Kode Shift", "kode_shift", "TEXT"),
            ("CREW", "Nama Crew", "crew", "TEXT"), ("LOKASI", "Lokasi", "lokasi", "TEXT"), ("EXCAVATOR", "Excavator", "excavator", "TEXT"),
            ("NO", "No", "no", "TEXT"), ("TANGGAL_MUAT", "Tanggal Muat", "tanggal_muat", "DATE"),
            ("START_LOADING", "Start Loading", "start", "TEXT"), ("FINISH_LOADING", "Finish Loading", "finish", "TEXT"),
            ("JAM", "Jam", "jam", "TEXT"), ("PIT", "Pit", "pit", "TEXT"), ("ELEVASI", "Elevation", "elevasi", "NUM"),
            ("FRONT", "Front", "front", "TEXT"), ("KELAS", "Kelas Material", "kelas", "TEXT"), ("MATERIAL", "Oksida / Sulfida", "material", "TEXT"),
            ("GRADE", "Grade", "grade", "TEXT"), ("TRUCK", "Truck", "unit", "TEXT"), ("TON", "Tonnage", "ton", "NUM"),
            ("TUJUAN", "Tujuan Dumping", "tujuan", "TEXT")],
    "rom": [("TANGGAL", "Tanggal", "tanggal", "DATE"), ("SHIFT", "Shift", "shift", "TEXT"), ("KODE_SHIFT", "Kode Shift", "kode_shift", "TEXT"),
            ("CREW", "Crew", "crew", "TEXT"), ("LOKASI", "Lokasi", "lokasi", "TEXT"), ("NO", "No", "no", "TEXT"),
            ("UNIT", "Eq. No. Unit", "unit", "TEXT"), ("TANGGAL_MUAT", "Tanggal Muat", "tanggal_muat", "DATE"),
            ("START_LOADING", "Start Loading", "start", "TEXT"), ("FINISH_LOADING", "Finish Loading", "finish", "TEXT"),
            ("JAM", "Jam", "jam", "TEXT"), ("ASAL", "Asal Material", "asal", "TEXT"), ("TUJUAN", "Tujuan", "tujuan", "TEXT"),
            ("REHANDLING", "Rehandling Tumpukan", "rehandling", "TEXT"), ("KELAS", "Kelas Material", "kelas", "TEXT"),
            ("MATERIAL", "Oksida / Sulfida", "material", "TEXT"), ("GRADE", "Grade", "grade", "TEXT"), ("TON", "Ton", "ton", "NUM"),
            ("STATUS", "Status Material", "status", "TEXT"), ("KETERANGAN", "Keterangan", "keterangan", "TEXT"),
            ("JENIS", "Direct / Rehandling", "jenis", "TEXT")],
    "rc": [("HOLE_ID", "HOLE_ID", "hole_id", "TEXT"), ("TANGGAL", "Tanggal", "tanggal", "DATE"), ("SAMPLE_ID", "Sample_ID", "sample_id", "TEXT"),
           ("FROM_M", "From (m)", "from_m", "NUM"), ("TO_M", "To (m)", "to_m", "NUM"), ("REMARK", "Remark (QAQC)", "remark", "TEXT")],
}
DB_TABLE = {"ore": "ORE_LOADING_PIT", "rom": "ORE_ROM_CRUSHER", "rc": "RC_INTERVAL"}
SHEET = {"ore": "Data_Loading_Pit", "rom": "Data_ROM_Crusher", "rc": "Interval_Geodatabase"}
AUDIT = [("VERIFIED", "BOOL"), ("SRC_DOC", "TEXT"), ("SRC_KEY", "TEXT")]


def collect(s: Store, ids: list[int], ftype: str, unverified: bool = False) -> dict:
    """Baris untuk diekspor dari borang terpilih (kosong = semua borang jenis itu). Bawaan: hanya baris terverifikasi."""
    if ftype not in TYPES:
        raise ValueError("Jenis borang tidak dikenal.")
    sel = [d for d in docs(s) if d["type"] == ftype and (not ids or d["id"] in ids)]
    recs, skip, issues = [], 0, 0
    for d in sel:
        rs = rows(s, d["id"])
        v = validate(d, rs, other_ids(s, d["id"]) if ftype == "rc" else None)
        issues += v["n"]
        for rec in records(d, rs):
            if rec["_verified"] or unverified:
                recs.append(rec)
            else:
                skip += 1
    return {"recs": recs, "docs": sel, "skipped_unverified": skip, "issues": issues}


def _val(rec: dict, k: str, t: str):
    v = rec.get(k)
    if t == "DATE":
        return parse_date(v)
    if t == "NUM":
        return v if isinstance(v, (int, float)) else parse_num(v)
    return "" if v is None else str(v)


def to_xlsx(ftype: str, recs: list[dict]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    head_fill, head_font = PatternFill("solid", fgColor="1D4785"), Font(bold=True, color="FFFFFF")

    def sheet(ws, heads, data, fmts=None):
        ws.append(heads)
        for c in ws[1]:
            c.fill, c.font, c.alignment = head_fill, head_font, Alignment(horizontal="center", vertical="center", wrap_text=True)
        for r in data:
            ws.append(r)
        for i, hd in enumerate(heads, 1):
            ws.column_dimensions[get_column_letter(i)].width = max(10, min(40, len(str(hd)) + 4))
            if fmts and fmts.get(i):
                for c in ws.iter_rows(min_row=2, min_col=i, max_col=i):
                    c[0].number_format = fmts[i]
        ws.freeze_panes = "A2"
    cols = OUT[ftype]
    ws = wb.active
    ws.title = SHEET[ftype]
    sheet(ws, [c[1] for c in cols], [[_val(r, c[2], c[3]) for c in cols] for r in recs],
          {i: ("d-mmm-yy" if c[3] == "DATE" else None) for i, c in enumerate(cols, 1)})
    for pv in pivots(recs, ftype):
        ks = [k for k, _l in pv["cols"]]
        sheet(wb.create_sheet(pv["key"].title().replace("_", "_")[:31]), [lab for _k, lab in pv["cols"]],
              [[(parse_date(x[k]) or x[k]) if k == "tanggal" else x[k] for k in ks] for x in pv["rows"]], {1: "d-mmm-yy"})
    sheet(wb.create_sheet("Audit"), ["Borang", "Baris", "Diverifikasi", "Kunci sumber"],
          [[r["_name"], r["_idx"] + 1, "ya" if r["_verified"] else "BELUM", r["_key"]] for r in recs])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


def to_csv(ftype: str, recs: list[dict]) -> bytes:
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\r\n")
    cols = OUT[ftype]
    w.writerow([c[0] for c in cols] + ["VERIFIED", "SRC_DOC"])
    for r in recs:
        row = []
        for c in cols:
            v = _val(r, c[2], c[3])
            row.append(v.isoformat() if isinstance(v, date) else ("" if v is None else (f"{v:g}" if isinstance(v, float) else v)))
        w.writerow(row + ["1" if r["_verified"] else "0", r["_name"]])
    return ("﻿" + b.getvalue()).encode("utf-8")


def _db_rows(ftype: str, recs: list[dict]) -> tuple[list[str], list[list]]:
    cols = OUT[ftype]
    names = [c[0] for c in cols] + [a for a, _t in AUDIT]
    data = [[_val(r, c[2], c[3]) for c in cols] + [bool(r["_verified"]), r["_name"], r["_key"]] for r in recs]
    return names, data


def to_sqlite(path: str, ftype: str, recs: list[dict]) -> dict:
    """Tambah / perbarui (kunci SRC_KEY = borang:baris) ke file SQLite; view pivot dibuat untuk Ore Spotter."""
    tmap = {"TEXT": "TEXT", "NUM": "REAL", "DATE": "TEXT", "BOOL": "INTEGER"}
    cols = [(c[0], c[3]) for c in OUT[ftype]] + AUDIT
    names, data = _db_rows(ftype, recs)
    tb = DB_TABLE[ftype]
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cn = sqlite3.connect(str(p))
    try:
        with cn:
            cn.execute(f"CREATE TABLE IF NOT EXISTS {tb} (" + ", ".join(f"{n} {tmap[t]}" + (" PRIMARY KEY" if n == "SRC_KEY" else "")
                                                                      for n, t in cols) + ")")
            have = {r[1].upper() for r in cn.execute(f"PRAGMA table_info({tb})")}
            for n, t in cols:
                if n.upper() not in have:
                    cn.execute(f"ALTER TABLE {tb} ADD COLUMN {n} {tmap[t]}")
            before = cn.execute(f"SELECT COUNT(*) FROM {tb}").fetchone()[0]
            cn.executemany(f"INSERT OR REPLACE INTO {tb} ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
                           [[v.isoformat() if isinstance(v, date) else (int(v) if isinstance(v, bool) else v) for v in row] for row in data])
            after = cn.execute(f"SELECT COUNT(*) FROM {tb}").fetchone()[0]
            dbcol = {c[2]: c[0] for c in OUT[ftype]}
            for key, _t, keys in PIVOTS.get(ftype, []):
                vn = f"{tb}_{key}"
                g = ", ".join(dbcol[k] for k in keys)
                cn.execute(f"DROP VIEW IF EXISTS {vn}")
                cn.execute(f"CREATE VIEW {vn} AS SELECT {g}, COUNT(*) AS RITASE, ROUND(SUM(TON), 2) AS TONASE FROM {tb} GROUP BY {g}")
    finally:
        cn.close()
    return {"table": tb, "added": after - before, "updated": len(data) - (after - before), "total": after}


def to_access(path: str, ftype: str, recs: list[dict]) -> dict:
    """Tambahkan ke database MS Access (dibuat bila belum ada; tabel dibuat bila belum ada). Baris dengan SRC_KEY yang sudah ada
    tidak diubah (dilaporkan)."""
    from . import access_io
    created = False
    if not Path(path).exists():
        access_io.create_db(path)
        created = True
    tb = DB_TABLE[ftype]
    new_tb = access_io.ensure_table(path, tb, [(c[0], c[3]) for c in OUT[ftype]] + AUDIT, key="SRC_KEY")
    names, data = _db_rows(ftype, recs)
    r = access_io.insert(path, tb, names, data, key_column="SRC_KEY", skip_existing=True)
    return {"table": tb, "added": r["added"], "existing": len(r["skipped_existing"]), "db_created": created, "table_created": new_tb}


# ---------------------------------------------------------------- API
class FBody(BaseModel):
    folder: str
    by: str = ""


class AddBody(FBody):
    paths: list[str]
    type: str


class DidBody(FBody):
    id: int


class UpdBody(FBody):
    id: int
    values: dict[str, Any]


class RowsBody(FBody):
    id: int
    rows: list[dict[str, Any]]


class VerBody(FBody):
    id: int
    on: bool = True


class AiBody(FBody):
    id: int
    host: str = ""
    model: str
    extra: str = ""
    max_px: int = 2000


class ExpBody(FBody):
    ids: list[int] = []
    type: str
    fmt: str = "xlsx"
    path: str = ""
    unverified: bool = False


def _full(s: Store, did: int) -> dict:
    d = doc(s, did)
    rs = rows(s, did)
    v = validate(d, rs, other_ids(s, did) if d["type"] == "rc" else None)
    recs = records(d, rs)
    return {"doc": d, "rows": rs, "valid": v, "recs": recs, "pivot": pivots(recs, d["type"])}


@router.post("/open")
def api_open(b: FBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "docs": docs(s), "types": {k: {"name": t["name"], "header": t["header"], "rows": t["rows"]} for k, t in TYPES.items()},
            "root": str(s.root)}


@router.post("/add")
def api_add(b: AddBody) -> dict:
    s = store(b.folder)
    made, errs = [], []
    for p in b.paths:
        try:
            made += add_file(s, p, b.type, b.by)
        except ValueError as e:
            errs.append(str(e))
    if not made and errs:
        raise ValueError("\n".join(errs))
    return {"ok": True, "added": made, "errors": errs, "docs": docs(s)}


@router.post("/doc")
def api_doc(b: DidBody) -> dict:
    return {"ok": True, **_full(store(b.folder), b.id)}


@router.post("/update")
def api_update(b: UpdBody) -> dict:
    s = store(b.folder)
    update_doc(s, b.id, b.values, b.by)
    return {"ok": True, **_full(s, b.id)}


@router.post("/rows")
def api_rows(b: RowsBody) -> dict:
    s = store(b.folder)
    save_rows(s, b.id, b.rows, b.by)
    return {"ok": True, **_full(s, b.id)}


@router.post("/verify")
def api_verify(b: VerBody) -> dict:
    s = store(b.folder)
    verify_all(s, b.id, b.on, b.by)
    return {"ok": True, **_full(s, b.id)}


@router.post("/delete")
def api_delete(b: DidBody) -> dict:
    s = store(b.folder)
    delete_doc(s, b.id, b.by)
    return {"ok": True, "docs": docs(s)}


@router.post("/history")
def api_history(b: DidBody) -> dict:
    return {"ok": True, "history": history(store(b.folder), b.id)}


@router.post("/ai")
def api_ai(b: AiBody) -> dict:
    s = store(b.folder)
    ai_read(s, b.id, b.host, b.model, b.extra, b.max_px, b.by)
    return {"ok": True, **_full(s, b.id)}


@router.post("/export/check")
def api_export_check(b: ExpBody) -> dict:
    c = collect(store(b.folder), b.ids, b.type, b.unverified)
    return {"ok": True, "n": len(c["recs"]), "docs": len(c["docs"]), "skipped_unverified": c["skipped_unverified"], "issues": c["issues"]}


@router.post("/export")
def api_export(b: ExpBody):
    from fastapi.responses import Response
    s = store(b.folder)
    c = collect(s, b.ids, b.type, b.unverified)
    if not c["recs"]:
        raise ValueError("Tidak ada baris untuk diekspor" + (f" ({c['skipped_unverified']} baris belum diverifikasi)." if c["skipped_unverified"] else "."))
    with s.lock, s.conn() as cn:
        _hist(cn, None, f"ekspor {b.fmt}", None, f"{len(c['recs'])} baris {b.type} -> {b.path or '(file)'}", "ekspor", b.by)
    if b.fmt == "xlsx":
        return Response(to_xlsx(b.type, c["recs"]), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if b.fmt == "csv":
        return Response(to_csv(b.type, c["recs"]), media_type="text/csv")
    if not b.path:
        raise ValueError("Pilih file database tujuan.")
    if b.fmt == "sqlite":
        return {"ok": True, **to_sqlite(b.path, b.type, c["recs"])}
    if b.fmt == "access":
        return {"ok": True, **to_access(b.path, b.type, c["recs"])}
    raise ValueError(f"Format ekspor tidak dikenal: {b.fmt}")
