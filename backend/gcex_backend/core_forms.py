"""Ruang kerja Borang DB-Ex: borang lapangan tulisan tangan (scan / foto / PDF) -> AI vision lokal (Ollama) -> tabel yang
diperiksa geologist berdampingan dengan scan -> Excel / CSV / SQLite / MS Access.

Jenis borang:
- "ore": Ore Spotter di front loading (Form Loading / Rehandling Ore dari Pit to ROM / Stockpile) — header (tanggal, shift I / II,
  crew, lokasi, excavator) + satu baris per ritase (jam, pit, elevasi, kelas material, truck, tonnage, tujuan dumping).
- "rom": Ore ke Stockpile / Crusher (Rehandling / Direct) — header (tanggal, shift, crew, lokasi) + baris (unit, jam, asal, tujuan,
  rehandling, kelas + ton, status Baru / Lama, keterangan).
  Keduanya: tanda ulang, jam "menit saja" dan nomor truk singkat diselesaikan program (ditandai kuning); kolom turunan tanggal
  muat (shift malam lewat tengah malam), oksida / sulfida, grade; pivot ritase & tonase.
- "ddr": RC Drilling Daily Drilling Report — header (tanggal, shift, rig, driller, client, jam WH / DL / MNTC / BD / RAIN / STD, HM
  engine, bit, catatan) + tabel utama aktivitas (mulai, selesai, uraian, kategori otomatis dari kata kunci) + tabel kedua 'hole'
  (meterage: from, to, hole ID, az, dip). Ekspor tiga tabel: DDR_AKTIVITAS, DDR_METERAGE, DDR_SHIFT (ringkasan) + pivot jam & meter.
- "rc": RC Drill Logging / Chiptray Log — interval per baris (Hole ID, tanggal, Sample ID, From, To, Lith, Int_Alt, Min1,
  Vein_Type, Qt_pct, Remark QAQC); Hole ID & tanggal ditulis sekali per lubang lalu diteruskan ke baris di bawahnya.

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
import urllib.error
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
    "ddr": {
        "name": "RC Drilling: Daily Drilling Report",
        "header": [("tanggal", "Date", "date"), ("shift", "Shift (I / II)", "text"), ("rig", "Drill rig (EqType)", "text"),
                   ("lokasi", "Location", "text"), ("driller", "Driller", "text"), ("client", "Client", "text"), ("dhp_id", "DHP ID", "text"),
                   ("wh", "WH (jam kerja)", "num"), ("dl", "DL (delay)", "num"), ("mntc", "MNTC (maintenance)", "num"),
                   ("bd", "BD (breakdown)", "num"), ("rain", "RAIN (hujan)", "num"), ("std", "STD (standby)", "num"),
                   ("hm_start", "HM engine start", "num"), ("hm_finish", "HM engine finish", "num"), ("hm_running", "HM running", "num"),
                   ("bit_type", "Bit / reamer: type", "text"), ("bit_serial", "Bit: serial no.", "text"), ("bit_on", "Bit: on", "text"),
                   ("bit_off", "Bit: off", "text"), ("bit_drilled", "Bit: drilled (m)", "num"), ("catatan", "Catatan", "text"),
                   ("geologist", "Geologist approval", "text")],
        "rows": [("mulai", "Mulai", "time"), ("selesai", "Selesai", "time"), ("aktivitas", "Drilling details / formation description", "text"),
                 ("kategori", "Kategori", "text")],
        "tables": {"hole": {"name": "Meterage / lubang", "ai": "lubang",
                            "rows": [("from_m", "From (m)", "num"), ("to_m", "To (m)", "num"), ("hole_id", "Hole ID", "text"),
                                     ("az", "Az", "num"), ("dip", "Dip", "num")]}},
        "hint": ("Borang 'Daily Drilling Report' pemboran RC, portrait. Header kanan atas: Client, DHP_ID, Driller, Date, Drill Rig (nama "
                 "unit, mis. 'Hanjin SDR-07' -> tulis apa adanya), Shift (I / II). Tabel kiri METERAGE (From, To), Hole ID, Az, Dip -> isi 'lubang' (satu objek per lubang). Kolom kanan "
                 "'DRILLING DETAILS and FORMATION DESCRIPTION': tiap kegiatan diawali rentang jam, mis. 0650-0700 atau 07.00-07.05, lalu "
                 "uraian (boleh dua baris tulisan) -> isi 'rows' dengan satu objek per kegiatan: mulai, selesai, aktivitas (gabungkan "
                 "baris lanjutan uraian), kategori kosongkan (""). Kotak bawah: BITS / REAMER (type, serial no., on, off, drilled), HM "
                 "ENGINE (start, finish, HM running), Geologist approval; catatan di bawah tabel: WH, DL, MNTC, BD, RAIN, STD (jam, "
                 "mis. 5hr -> 5) dan tulisan bebas -> 'catatan'. 'lokasi' (nama area / prospek) biasanya tidak tertulis: kosongkan bila "
                 "tidak ada."),
    },
    "rc": {
        "name": "RC Drill Logging / Chiptray Log",
        "header": [("hole_id", "Hole ID (bawaan)", "text"), ("tanggal", "Tanggal pengeboran (bawaan)", "date")],
        "rows": [("hole_id", "Hole ID", "text"), ("tanggal", "Tanggal", "date"), ("sample_id", "Sample ID", "text"),
                 ("from_m", "From (m)", "num"), ("to_m", "To (m)", "num"), ("lith", "Lith", "text"), ("alt", "Int_Alt", "text"),
                 ("min1", "Min1", "text"), ("vein", "Vein_Type", "text"), ("qt", "Qt_pct", "num"), ("remark", "Remark (QAQC)", "text")],
        "hint": ("Borang RC Drill Logging Form, biasanya lanskap. Kolom No dan Sample_ID TERCETAK (mis. DP_150137_Z4); Remark2 tercetak "
                 "pada baris QAQC (STD..., BLANK). Tulisan tangan: Hole_ID dan Tanggal Pengeboran HANYA di baris pertama tiap lubang "
                 "(kadang dua baris: Hole ID lalu Az/Dip, mis. 'AZ 64-60' -> abaikan baris Az/Dip), From, To, Lith, Int_Alt, Min1, "
                 "Vein_Type, Qt_pct. Tulis HANYA baris yang From/To-nya terisi atau berlabel STD / BLANK. Hole_ID & Tanggal: isi hanya "
                 "di baris tempat tertulis, baris lain kosong (program yang meneruskan). Garis bergelombang / kurung kurawal / garis tegak "
                 "panjang di kolom Lith, Int_Alt, Min1 = sama dengan baris di atas -> tulis \"〃\". Kode geologi disalin persis "
                 "(mis. VLT, QMN, ARG, IAR, PRO, SIL, ox, cly, chl-cly, Qz-Mn)."),
    },
}
KELAS = ["OX-LG", "SF-LG", "OX-HG", "SF-HG", "OX-SG", "SF-SG", "SCAT", "OX-MO", "SF-MO"]
ORE_TYPES = ("ore", "rom")
SHIFT_DS = (6, 18)  # shift I / siang (DS) 06:00-18:00, shift II / malam (NS) 18:00-06:00
# sel kosong hasil AI -> diisi dari baris atas (ditandai kuning); tanda ulang -> nilai baris atas
CARRY = {"ore": ("pit", "elevasi", "tujuan"), "rom": ("asal", "tujuan", "status", "keterangan")}
DITTO = {"ore": ("start", "finish", "pit", "elevasi", "kelas", "tujuan"),
         "rom": ("start", "finish", "asal", "tujuan", "rehandling", "kelas", "status", "keterangan")}
# Daily Drilling Report: kategori aktivitas (urutan = prioritas kata kunci) dan kelompok jam di borang (WH / DL / MNTC / BD / RAIN / STD)
# sesuai aturan site: WH = drilling, traveling antar titik bor, persiapan, P2H, P5M; DL = istirahat, standby, wait blasting, traveling
# ke lokasi; MNTC / BD / RAIN = maintenance / breakdown / hujan; STD = standby tidak ada operator / tidak ada lokasi.
_TRV = r"(travel|moving|pindah|mobili|jalan|geser)"
DDR_KAT = [("P2H", r"\bp2h\b|pre.?start"), ("P5M", r"\bp5m\b|\bpsm\b|safety|toolbox"),
           ("ISTIRAHAT", r"\brest|istirahat|makan|ishoma|sholat|shalat"), ("HUJAN", r"hujan|\brain"),
           ("BREAKDOWN", r"break ?down|\bbd\b|rusak|perbaikan|repair"), ("MAINTENANCE", r"service|servis|maint|mntc|ganti|greas"),
           ("STANDBY TIDAK ADA OPERATOR", r"(tidak ada|tdk ada|tanpa|no|belum ada|kurang)\s*(operator|driller|helper|crew)"),
           ("STANDBY TIDAK ADA LOKASI", r"(tidak ada|tdk ada|tanpa|no|belum ada)\s*(lokasi|location|titik|area|drill ?pad|point)"),
           ("DRILLING", r"drilling|pemboran|ngebor|\bdrill\b|reaming"), ("WAIT BLASTING", r"blast|peledakan"),
           ("TRAVELING ANTAR TITIK BOR", _TRV + r".*(titik|antar|lubang|\bhole|next)|(titik|lubang|hole).*" + _TRV),
           ("TRAVELING KE LOKASI", _TRV),
           ("PERSIAPAN", r"start engine|clean|compres|kompres|set ?up|persiapan|pemanasan|rig up|leveling"),
           ("STANDBY", r"stand ?by|stamby|waiting|tunggu|menunggu|\bstd\b")]
DDR_KAT_NAMES = [k for k, _r in DDR_KAT] + ["LAIN-LAIN"]
DDR_GROUP = {"DRILLING": "WH", "TRAVELING ANTAR TITIK BOR": "WH", "PERSIAPAN": "WH", "P2H": "WH", "P5M": "WH",
             "ISTIRAHAT": "DL", "STANDBY": "DL", "WAIT BLASTING": "DL", "TRAVELING KE LOKASI": "DL", "LAIN-LAIN": "DL",
             "MAINTENANCE": "MNTC", "BREAKDOWN": "BD", "HUJAN": "RAIN", "STANDBY TIDAK ADA OPERATOR": "STD", "STANDBY TIDAK ADA LOKASI": "STD"}
KAT_ALIAS = {"SAFETY TALK": "P5M", "PSM": "P5M", "BLASTING": "WAIT BLASTING", "TRAVEL": "TRAVELING KE LOKASI",
             "TRAVELING": "TRAVELING KE LOKASI", "ANTAR TITIK": "TRAVELING ANTAR TITIK BOR", "TIDAK ADA OPERATOR": "STANDBY TIDAK ADA OPERATOR",
             "TIDAK ADA LOKASI": "STANDBY TIDAK ADA LOKASI", "MNTC": "MAINTENANCE", "BD": "BREAKDOWN", "RAIN": "HUJAN", "REST": "ISTIRAHAT"}
HOURS = ("wh", "dl", "mntc", "bd", "rain", "std")
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
            if "tbl" not in {r[1] for r in c.execute("PRAGMA table_info(rows)")}:  # tabel tambahan per borang (0.35)
                c.execute("ALTER TABLE rows ADD COLUMN tbl TEXT DEFAULT ''")
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


RC_CARRY = ("hole_id", "tanggal")  # ditulis sekali per lubang
RC_DITTO = ("lith", "alt", "min1", "vein", "qt")


def fill_rc(lst: list[dict]) -> list[tuple[dict, list[str]]]:
    """RC logging: Hole ID & tanggal diteruskan ke baris di bawahnya sampai ada Hole ID baru; tanda ulang (〃, garis
    bergelombang) di kolom geologi -> nilai baris atas. Kembalikan (data, field yang diisi program) per baris."""
    prev: dict[str, str] = {}
    out = []
    for d in lst:
        x, filled = dict(d), []
        for k in RC_CARRY:
            v = str(x.get(k) or "").strip()
            if (not v or is_ditto(v)) and prev.get(k):
                x[k] = prev[k]
                filled.append(k)
        if str(d.get("hole_id") or "").strip() and not is_ditto(d.get("hole_id")):
            x["hole_id"] = norm_bhid(x["hole_id"]) or x["hole_id"]
        for k in RC_DITTO:
            v = str(x.get(k) or "").strip()
            if (is_ditto(v) or re.fullmatch(r"[~{}()\[\]S§∫ʃ$]+", v or "x")) and prev.get(k):
                x[k] = prev[k]
                filled.append(k)
            elif is_ditto(v):
                x[k] = ""
        for k in RC_CARRY + RC_DITTO:
            if str(x.get(k) or "").strip():
                prev[k] = x[k]
        out.append((x, filled))
    return out


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


RIG_BRANDS = ["Hanjin", "Hanwa"]  # merek drill rig yang dikenal (penulisan tangan dirapikan ke "Hanjin 007")


def norm_bhid(v: Any) -> str:
    """Hole ID baku DB-Ex: huruf besar, pemisah garis bawah (Z2-265-S-05 / z4 270.56 -> Z2_265_S_05 / Z4_270_56)."""
    t = str(v or "").strip().upper()
    t = re.sub(r"[\s\-./\\]+", "_", t)
    return re.sub(r"_+", "_", t).strip("_")


def norm_rig(v: Any) -> str:
    """Drill rig -> 'Merek 00N' bila mereknya dikenal (hansin SDR-07 / Hanjin 7 -> Hanjin 007); selain itu dibiarkan."""
    t = str(v or "").strip()
    w = re.findall(r"[A-Za-z]+", t)
    n = re.findall(r"\d+", t)
    if not w or not n:
        return t
    import difflib
    m = difflib.get_close_matches(w[0].lower(), [b.lower() for b in RIG_BRANDS], n=1, cutoff=0.6)
    if not m:
        return t
    return f"{RIG_BRANDS[[b.lower() for b in RIG_BRANDS].index(m[0])]} {int(n[-1]):03d}"


def norm_header(ftype: str, k: str, v: Any) -> str:
    v = str(v or "").strip()
    if ftype == "ddr" and k == "rig":
        return norm_rig(v)
    if ftype == "rc" and k == "hole_id":
        return norm_bhid(v)
    return v


def tcols(ftype: str, tbl: str = "") -> list:
    """Kolom tabel borang: tabel utama ('') atau tabel tambahan (mis. 'hole' di Daily Drilling Report)."""
    t = TYPES[ftype]
    return t["rows"] if not tbl else t["tables"][tbl]["rows"]


def tables(ftype: str) -> list[str]:
    return [""] + list(TYPES[ftype].get("tables") or {})


def ddr_kat(text: Any) -> str:
    t = str(text or "").lower()
    for k, rx in DDR_KAT:
        if re.search(rx, t):
            return k
    return "LAIN-LAIN"


def kat_norm(v: Any) -> str:
    t = str(v or "").strip().upper()
    if not t:
        return ""
    t = KAT_ALIAS.get(t, t)
    return next((k for k in DDR_KAT_NAMES if k == t or k.replace(" ", "") == t.replace(" ", "")), t)


def ddr_dur(a: Any, b: Any) -> Optional[float]:
    """Durasi jam antara dua jam (melewati tengah malam bila selesai < mulai)."""
    ta, tb = parse_time(a), parse_time(b)
    if not ta or not tb:
        return None
    m = (int(tb[:2]) * 60 + int(tb[3:])) - (int(ta[:2]) * 60 + int(ta[3:]))
    return round((m + 1440 if m < 0 else m) / 60, 2)


def parse_hours(v: Any) -> Optional[float]:
    """'5hr', '7 hrs', '2,5 jam', '1:30' -> jam."""
    t = str(v or "").strip().lower()
    if not t:
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})$", t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60
    m = re.match(r"^(\d+(?:[.,]\d+)?)\s*(h|hr|hrs|jam|j)?\.?$", t)
    return float(m.group(1).replace(",", ".")) if m else parse_num(t)


def fill_ddr(lst: list[dict]) -> list[tuple[dict, list[str]]]:
    """Daily Drilling Report: jam dinormalisasi (0650 -> 06:50), kategori kosong diisi dari kata kunci uraian (ditandai kuning)."""
    out = []
    for d in lst:
        x = dict(d)
        f = []
        for k in ("mulai", "selesai"):
            if parse_time(x.get(k)):
                x[k] = parse_time(x.get(k))
        if not str(x.get("kategori") or "").strip() and str(x.get("aktivitas") or "").strip():
            x["kategori"] = ddr_kat(x.get("aktivitas"))
            f.append("kategori")
        elif x.get("kategori"):
            x["kategori"] = kat_norm(x["kategori"])
        out.append((x, f))
    return out


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
            d["tbl"] = d.get("tbl") or ""
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
    # foto borang jenis yang sama biasanya diambil dengan cara yang sama: putaran borang terakhir (bentuk foto sama:
    # tegak / rebah) dipakai lagi, jadi tidak perlu memutar tiap lembar sebelum dibaca AI
    last = [x for x in docs(s) if x["type"] == ftype and x.get("rot")]
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
            same = [x for x in last if (x.get("w", 0) > x.get("h", 0)) == (im.width > im.height)]
            if same:
                c.execute("UPDATE docs SET rot=? WHERE id=?", (int(same[-1]["rot"]) % 360, did))
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
                    v = norm_header(ftype, k, v)
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


def save_rows(s: Store, did: int, lst: list[dict], by: str, tbl: str = "") -> list[dict]:
    """Simpan seluruh satu tabel borang (urutan = urutan daftar; tbl '' = tabel utama). Baris: {id?, data, verified?}. Sel yang
    berubah dari isian AI ditandai 'diedit' dan tidak lagi ragu. Baris tabel itu yang tidak ada di daftar dihapus."""
    d = doc(s, did)
    if tbl not in tables(d["type"]):
        raise ValueError(f"Tabel '{tbl}' tidak ada di borang ini.")
    keys = [k for k, _l, _t in tcols(d["type"], tbl)]
    old = {r["id"]: r for r in rows(s, did) if r["tbl"] == tbl}
    keep = set()
    datas = [{k: ("" if (r.get("data") or {}).get(k) is None else str((r.get("data") or {}).get(k)).strip()) for k in keys} for r in lst]
    if d["type"] in ORE_TYPES:  # tanda ulang / jam menit saja / nomor truk singkat yang diketik pengguna -> nilai lengkap
        datas = [x for x, _f in fill_ore(d["type"], datas, False)]
    if d["type"] == "ddr" and not tbl:
        datas = [x for x, _f in fill_ddr(datas)]
    if "hole_id" in keys:
        for x in datas:
            x["hole_id"] = norm_bhid(x["hole_id"])
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
                nid = c.execute("INSERT INTO rows (doc_id, idx, data_json, edited_json, verified, verified_by, verified_at, src, by, at, tbl) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (did, i, json.dumps(data, ensure_ascii=False), json.dumps(keys), int(ver), by if ver else None,
                                 core_io.now() if ver else None, "manual", by, core_io.now(), tbl)).lastrowid
                keep.add(nid)
                _hist(c, did, f"baris {i + 1}" + (f" ({tbl})" if tbl else ""), None, json.dumps(data, ensure_ascii=False), "tambah", by)
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
    props = {"header": {"type": "object", "properties": {**hp, "ragu": {"type": "array", "items": {"type": "string", "enum": list(hp)}}}},
             "rows": {"type": "array", "items": {"type": "object", "properties": rp, "required": [k for k, _l, _t in t["rows"]]}},
             "catatan": {"type": "string"}}
    req = ["header", "rows"]
    for _tb, tt in (t.get("tables") or {}).items():
        xp = {k: {"type": "string"} for k, _l, _t in tt["rows"]}
        xp["ragu"] = {"type": "array", "items": {"type": "string", "enum": [k for k, _l, _t in tt["rows"]]}}
        props[tt["ai"]] = {"type": "array", "items": {"type": "object", "properties": xp, "required": [k for k, _l, _t in tt["rows"]]}}
        req.append(tt["ai"])
    return {"type": "object", "required": req, "properties": props}


def ai_prompt(ftype: str, extra: str = "") -> str:
    """Perintah baca borang dengan jawaban RINGKAS: satu baris teks per baris tabel, nilai dipisah '|'.
    Dibanding JSON (nama field diulang di setiap baris) jumlah token jawaban kira-kira 3-4x lebih sedikit, dan pada
    komputer tanpa GPU waktu baca terutama ditentukan oleh panjang jawaban."""
    t = TYPES[ftype]
    hk = [k for k, _l, _t in t["header"]]
    rk = [k for k, _l, _t in t["rows"]]
    lines = [f"Anda petugas data entry geologi tambang. Baca formulir tulisan tangan pada gambar.\n{t['hint']}\n",
             "JAWAB DALAM FORMAT RINGKAS INI SAJA (tanpa penjelasan, tanpa JSON):",
             "H|" + "|".join(hk) + "   <- SATU baris header: nilai sesuai urutan itu",
             "R|" + "|".join(rk) + "   <- SATU baris per baris tabel yang terisi, urut dari atas"]
    for tt in (t.get("tables") or {}).values():
        lines.append(f"{tt['ai'].upper()}|" + "|".join(k for k, _l, _t in tt["rows"]) + f"   <- satu baris per baris {tt['name']}")
    lines += ["C|catatan bebas (boleh tidak ada)",
              "Contoh baris: R|" + "|".join(["…"] * len(rk)),
              "Sel kosong = biarkan kosong di antara dua '|'. Jangan mengulang nama kolom. Jangan mengarang baris yang tidak ada.",
              "Salin angka & kode persis seperti tertulis. Bila satu sel tidak terbaca jelas, tulis tebakan terbaik diakhiri '?' (mis. VLT?)."]
    if ftype not in ORE_TYPES and ftype != "rc":
        lines.append("Bila tulisan sama dengan baris di atasnya (tanda ulang), tulis nilai baris di atasnya.")
    if extra and extra.strip():
        lines.append(f"Catatan pengguna: {extra.strip()}")
    return "\n".join(lines)


def parse_ai_text(ftype: str, txt: str) -> dict:
    """Jawaban ringkas (H|..., R|..., <TABEL>|..., C|...) -> bentuk yang sama dengan jawaban JSON lama
    ({header, rows, <tabel>, catatan}, sel bertanda '?' masuk 'ragu'). Jawaban JSON tetap diterima."""
    t = TYPES[ftype]
    raw = (txt or "").strip()
    js = re.sub(r"^```\w*\s*|\s*```$", "", raw)
    if js.startswith("{"):
        return json.loads(js)
    m = re.search(r"\{.*\}", raw, re.S)  # JSON di tengah penjelasan
    if m and '"rows"' in m.group(0):
        try:
            return json.loads(m.group(0))
        except ValueError:
            pass
    hk = [k for k, _l, _t in t["header"]]
    rk = [k for k, _l, _t in t["rows"]]
    tabs = {tt["ai"].upper(): (tt["ai"], [k for k, _l, _t in tt["rows"]]) for tt in (t.get("tables") or {}).values()}

    def cells(rest: str, keys: list[str]) -> dict:
        vs = [v.strip() for v in rest.split("|")]
        if len(vs) > len(keys):  # pemisah '|' di dalam uraian terakhir: gabungkan ke kolom terakhir
            vs = vs[:len(keys) - 1] + [" | ".join(vs[len(keys) - 1:])]
        o: dict[str, Any] = {"ragu": []}
        for k, v in zip(keys, vs):
            if v.endswith("?"):
                v = v[:-1].strip()
                o["ragu"].append(k)
            o[k] = "" if v in ("-", "…", "...") and k not in ("aktivitas",) else v
        return o
    out: dict[str, Any] = {"header": {}, "rows": [], "catatan": ""}
    for ln in raw.splitlines():
        ln = ln.strip().strip("`").strip()
        # variasi model: "- R|", "1. R|", "**R**|", "R:", "R |"
        ln = re.sub(r"^(?:[-*•]\s*|\d+[.)]\s*)", "", ln).replace("**", "")
        m = re.match(r"^([A-Za-z_]+)\s*[|:]\s*(.*)$", ln)
        if m and (m.group(1).upper() in ("H", "R", "C") or m.group(1).upper() in tabs) and ("|" in m.group(2) or m.group(1).upper() == "C"):
            tag, rest = m.group(1).upper(), m.group(2)
        elif ln.count("|") >= max(2, len(rk) // 2) and not re.fullmatch(r"[|:\-\s]+", ln):
            tag, rest = "R", ln.strip("|")  # baris tabel markdown tanpa tanda R
            if [v.strip().lower() for v in rest.split("|")][:1] == [rk[0]] or rest.split("|")[0].strip().lower() in [lbl.lower() for _k, lbl, _t in t["rows"]]:
                continue
        else:
            continue
        if [v.strip() for v in rest.split("|")][:2] == (hk if tag == "H" else rk)[:2]:
            continue  # model mengulang baris nama kolom
        if tag == "H":
            out["header"] = cells(rest, hk)
        elif tag == "R":
            out["rows"].append(cells(rest, rk))
        elif tag == "C":
            out["catatan"] = rest.strip()
        elif tag in tabs:
            out.setdefault(tabs[tag][0], []).append(cells(rest, tabs[tag][1]))
    for _k, (ai, _ks) in tabs.items():
        out.setdefault(ai, [])
    if not out["rows"] and not out["header"] and not any(out[a] for a, _ in tabs.values()):
        raise ValueError("jawaban AI tidak berformat H| / R| (tidak ada baris yang terbaca)"
                         + (f": «{raw[:160]}»" if raw else ": jawaban kosong"))
    return out


def _image_b64(s: Store, d: dict, max_px: int) -> tuple[str, tuple[int, int]]:
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
        size = im.size
    return base64.b64encode(b.getvalue()).decode(), size


_THINK: dict[tuple[str, str], bool] = {}


def _can_think(host: str, model: str) -> bool:
    """Model 'berpikir' (mis. qwen3-vl) menulis penalaran panjang sebelum menjawab: pada CPU itu memakan sebagian besar
    waktu baca borang. Membaca tabel tulisan tangan tidak butuh penalaran itu, jadi dimatikan (think=false) bila modelnya
    mendukung. Hasil /api/show disimpan per sesi."""
    k = (host, model)
    if k not in _THINK:
        try:
            caps = core_io._http(host + "/api/show", {"model": model}, timeout=10).get("capabilities") or []
            _THINK[k] = "thinking" in caps
        except Exception:  # noqa: BLE001 - Ollama lama / tanpa /api/show: kirim tanpa parameter think
            _THINK[k] = False
    return _THINK[k]


N_PREDICT = 2500


def ctx_for(size: tuple[int, int], prompt: str) -> int:
    """num_ctx secukupnya: token gambar (Qwen-VL: satu token per 32x32 px) + perintah + jawaban, dibulatkan ke 1024.
    Konteks yang terlalu besar (dulu 16384) memperbesar KV cache sampai model tidak muat di VRAM GPU dan sebagian
    berjalan di CPU -> waktu baca berlipat (laporan pengguna: >5-10 menit per lembar)."""
    img = -(-size[0] // 32) * -(-size[1] // 32)
    need = img + len(prompt) // 3 + N_PREDICT + 256
    return int(min(16384, max(4096, -(-need // 1024) * 1024)))


def gpu_share(host: str, model: str) -> Optional[float]:
    """Porsi model di VRAM GPU (0-100 %) menurut Ollama /api/ps; None bila tidak diketahui. < 100 % = sebagian di CPU (lambat)."""
    try:
        ms = core_io._http(host + "/api/ps", timeout=5).get("models") or []
    except Exception:  # noqa: BLE001
        return None
    for m in ms:
        if str(m.get("name") or m.get("model") or "").split(":")[0] == model.split(":")[0] and m.get("size"):
            return round(100.0 * float(m.get("size_vram") or 0) / float(m["size"]), 0)
    return None


def _save_raw(s: Store, did: int, msg: dict) -> None:
    """Simpan jawaban mentah AI terakhir per borang (_GCEx_Core/borang/ai_mentah/<id>.txt) untuk menelusuri galat."""
    try:
        p = s.root / "ai_mentah"
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{did}.txt").write_text(("[thinking]\n" + msg["thinking"] + "\n\n" if msg.get("thinking") else "")
                                      + "[content]\n" + str(msg.get("content") or ""), encoding="utf-8")
    except OSError:
        pass


def ai_read(s: Store, did: int, host: str, model: str, extra: str = "", max_px: int = 1600, by: str = "", timeout: float = 900) -> dict:
    d = doc(s, did)
    host = (host or core_io.DEFAULT_HOST).rstrip("/")
    prompt = ai_prompt(d["type"], extra)
    img, size = _image_b64(s, d, max_px)
    body = {"model": model, "messages": [{"role": "user", "content": prompt, "images": [img]}],
            "stream": False, "keep_alive": "30m",
            # num_predict membatasi jawaban: model kecil kadang mengulang baris tanpa henti sampai batas waktu habis (borang 'gagal')
            "options": {"temperature": 0, "num_ctx": ctx_for(size, prompt), "num_predict": N_PREDICT, "repeat_penalty": 1.05}}
    if _can_think(host, model):
        body["think"] = False
    t0 = time.time()
    try:
        try:
            j = core_io._http(host + "/api/chat", body, timeout=timeout)
        except urllib.error.HTTPError as e:
            if "think" not in body or e.code != 400:
                raise
            body.pop("think")  # Ollama versi lama menolak parameter think: ulangi tanpa itu (dan jangan kirim lagi sesi ini)
            _THINK[(host, model)] = False
            j = core_io._http(host + "/api/chat", body, timeout=timeout)
        if j.get("error"):
            raise RuntimeError("Ollama: " + str(j["error"]))
        msg = j.get("message") or {}
        _save_raw(s, did, msg)
        try:
            res = parse_ai_text(d["type"], msg.get("content") or "")
        except ValueError:
            try:  # model yang tetap 'berpikir': jawaban kadang tertulis di bagian thinking, content kosong / terpotong
                res = parse_ai_text(d["type"], (msg.get("thinking") or "") + "\n" + (msg.get("content") or ""))
            except ValueError:
                # cadangan: ulangi sekali dengan format JSON berskema (lebih lambat, tetapi bentuk jawabannya dipaksa Ollama)
                body2 = dict(body, format=ai_schema(d["type"]),
                             options=dict(body["options"], num_predict=N_PREDICT * 2, num_ctx=min(16384, body["options"]["num_ctx"] + N_PREDICT)))
                body2["messages"] = [dict(body["messages"][0], content=prompt.split("JAWAB DALAM FORMAT RINGKAS")[0]
                                          + "Jawab dalam JSON sesuai skema.")]
                j = core_io._http(host + "/api/chat", body2, timeout=timeout)
                if j.get("error"):
                    raise RuntimeError("Ollama: " + str(j["error"]))
                _save_raw(s, did, j.get("message") or {})
                res = core_io._parse_json((j.get("message") or {}).get("content", ""))
    except Exception as e:  # noqa: BLE001 - TIDAK ada data tiruan: borang tetap kosong & galat dicatat
        with s.lock, s.conn() as c:
            c.execute("UPDATE docs SET status='error', error=? WHERE id=?", (str(e)[:500], did))
        raise
    out = apply_ai(s, did, res, model, time.time() - t0, by)
    ev = j.get("eval_count") or 0
    out["perf"] = {"gpu": gpu_share(host, model), "secs": round(time.time() - t0, 1), "tokens": ev,
                   "tok_s": round(ev / (j["eval_duration"] / 1e9), 1) if j.get("eval_duration") else None,
                   "num_ctx": body["options"]["num_ctx"], "px": max(size)}
    return out


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
    hunc = [k for k in (rh.get("ragu") or []) if k in hk and k not in edited_hdr]
    for k in hk:
        if k not in edited_hdr and str(rh.get(k) or "").strip():
            raw = str(rh[k]).strip()
            h[k] = norm_header(d["type"], k, raw)
            if h[k] != raw and k not in hunc:  # dirapikan program (mis. rig, Hole ID) -> kuning, cek terhadap scan
                hunc.append(k)
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
    if d["type"] == "rc" and out_rows:
        out_rows = [(x, list(dict.fromkeys(u + f))) for (x, f), (_x, u) in zip(fill_rc([x for x, _u in out_rows]), out_rows)]
    if d["type"] == "ddr" and out_rows:
        out_rows = [(x, list(dict.fromkeys(u + f))) for (x, f), (_x, u) in zip(fill_ddr([x for x, _u in out_rows]), out_rows)]
    extra = []
    for tb, tt in (t.get("tables") or {}).items():
        xk = [k for k, _l, _tt in tt["rows"]]
        for r in (res or {}).get(tt["ai"]) or []:
            if isinstance(r, dict):
                data = {k: str(r.get(k) if r.get(k) is not None else "").strip() for k in xk}
                if any(data.values()):
                    unc = [k for k in (r.get("ragu") or []) if k in xk]
                    if "hole_id" in data and norm_bhid(data["hole_id"]) != data["hole_id"]:
                        data["hole_id"] = norm_bhid(data["hole_id"])
                    extra.append((tb, data, unc))
    with s.lock, s.conn() as c:
        c.execute("DELETE FROM rows WHERE doc_id=?", (did,))
        for i, (data, unc) in enumerate(out_rows):
            c.execute("INSERT INTO rows (doc_id, idx, data_json, unc_json, src, by, at, tbl) VALUES (?,?,?,?,?,?,?,'')",
                      (did, i, json.dumps(data, ensure_ascii=False), json.dumps(unc), "ai:" + model, by or "AI", core_io.now()))
        for i, (tb, data, unc) in enumerate(extra):
            c.execute("INSERT INTO rows (doc_id, idx, data_json, unc_json, src, by, at, tbl) VALUES (?,?,?,?,?,?,?,?)",
                      (did, i, json.dumps(data, ensure_ascii=False), json.dumps(unc), "ai:" + model, by or "AI", core_io.now(), tb))
        c.execute("UPDATE docs SET header_json=?, hdr_unc=?, status='done', error=NULL, ai_model=?, ai_at=?, ai_secs=?, ai_note=?, ai_json=? "
                  "WHERE id=?", (json.dumps(h, ensure_ascii=False), json.dumps(hunc), model, core_io.now(), round(secs, 1),
                                 str((res or {}).get("catatan") or "")[:500], json.dumps(res, ensure_ascii=False)[:200000], did))
        _hist(c, did, "AI membaca", None, f"{len(out_rows)} baris" + (f" + {len(extra)} baris tabel lain" if extra else ""), "ai:" + model,
              by or "AI")
    return {"doc": doc(s, did), "rows": rows(s, did)}


# ---------------------------------------------------------------- turunan, validasi, pivot
def ddr_common(d: dict) -> dict:
    h = d["header"]
    tg = parse_date(h.get("tanggal"))
    return {"tanggal": tg.isoformat() if tg else str(h.get("tanggal") or ""), "shift": h.get("shift") or "", "kode_shift": shift_code(h.get("shift")),
            "rig": norm_rig(h.get("rig")), "driller": str(h.get("driller") or "").strip(), "client": str(h.get("client") or "").strip(),
            "dhp_id": str(h.get("dhp_id") or "").strip()}


def ddr_summary(d: dict, rs: list[dict]) -> dict:
    """Satu baris ringkasan shift Daily Drilling Report: jam di borang (WH ... STD) vs jumlah durasi aktivitas per kelompok, meter, HM, bit."""
    h = d["header"]
    recs = records(d, rs)
    act = [r for r in recs if r["_tbl"] == ""]
    hole = [r for r in recs if r["_tbl"] == "hole"]
    out = {"_row": 0, "_idx": 0, "_verified": bool(rs) and all(r["verified"] for r in rs), "_doc": d["id"], "_uid": d["uid"],
           "_name": d["name"], "_key": f"{d['uid']}:shift", "_tbl": "_shift", **ddr_common(d)}
    for k in HOURS:
        out[k] = parse_hours(h.get(k))
        out[k + "_akt"] = round(sum(r["durasi"] or 0 for r in act if r["kelompok"] == k.upper()), 2)
    out.update({"jam_borang": round(sum(out[k] or 0 for k in HOURS), 2), "jam_aktivitas": round(sum(r["durasi"] or 0 for r in act), 2),
                "jam_drilling": round(sum(r["durasi"] or 0 for r in act if r["kategori"] == "DRILLING"), 2),
                "n_lubang": len({r["hole_id"] for r in hole if r["hole_id"]}), "meter": round(sum(r["meter"] or 0 for r in hole), 2),
                "hm_start": parse_num(h.get("hm_start")), "hm_finish": parse_num(h.get("hm_finish")), "hm_running": parse_num(h.get("hm_running")),
                "bit_type": h.get("bit_type") or "", "bit_serial": h.get("bit_serial") or "", "bit_on": h.get("bit_on") or "",
                "bit_off": h.get("bit_off") or "", "bit_drilled": parse_num(h.get("bit_drilled")), "catatan": h.get("catatan") or "",
                "geologist": h.get("geologist") or ""})
    if out["hm_running"] is None and out["hm_start"] is not None and out["hm_finish"] is not None:
        out["hm_running"] = round(out["hm_finish"] - out["hm_start"], 2)
    out["m_per_jam"] = round(out["meter"] / out["jam_drilling"], 2) if out["jam_drilling"] else None
    return out


def prospect_of(bhid: str) -> str:
    """Prospek dari awalan Hole ID: Z4_295_49 / Z2-265-S-05 -> Z4 / Z2."""
    return re.split(r"[_\-\s.]", str(bhid or "").strip(), maxsplit=1)[0].upper() if bhid else ""


def ddr_dashboard(d: dict, rs: list[dict], hole_ids: Optional[set] = None) -> list[dict]:
    """Baris sheet 'Data' dashboard drilling: satu baris per lubang (Date, EqType, Location, Shift S01 / S02, Prospect, BHID,
    Interval_m, WH, Maint, BD, Delay, Standby, Rain, Remarks, Azimuth, Dip). Jam shift (dari borang; bila kosong dari jumlah
    aktivitas per kelompok) hanya ditulis di baris pertama shift agar penjumlahan di dashboard tidak berlipat. Shift tanpa lubang
    -> satu baris berisi jam saja. hole_ids: baris meterage yang ikut diekspor (None = semua)."""
    sm = ddr_summary(d, rs)
    recs = records(d, rs)
    hole = [r for r in recs if r["_tbl"] == "hole" and (hole_ids is None or r["_row"] in hole_ids)]
    base = {"_doc": d["id"], "_uid": d["uid"], "_name": d["name"], "_tbl": "_dash", "tanggal": sm["tanggal"], "eqtype": sm["rig"],
            "location": str(d["header"].get("lokasi") or "").strip(), "shift_code": {"DS": "S01", "NS": "S02"}.get(sm["kode_shift"], sm["shift"])}
    hrs = {k: (sm[k] if sm[k] is not None else (sm[k + "_akt"] or None)) for k in HOURS}
    out = []
    for i, r in enumerate(hole):
        x = dict(base, _row=r["_row"], _idx=r["_idx"], _verified=r["_verified"], _key=f"{d['uid']}:dash:{r['_row']}", bhid=r["hole_id"],
                 prospect=prospect_of(r["hole_id"]), interval_m=r["meter"], az=r["az"], dip=r["dip"])
        if i == 0:
            x.update({k: hrs[k] for k in HOURS}, remarks=sm["catatan"])
        out.append(x)
    if not any(r["_tbl"] == "hole" for r in recs) and any(r["_tbl"] == "" for r in recs):
        out.append(dict(base, _row=0, _idx=0, _verified=sm["_verified"], _key=f"{d['uid']}:dash:jam", bhid="",
                        prospect="", interval_m=None, az=None, dip=None, remarks=sm["catatan"], **{k: hrs[k] for k in HOURS}))
    return out


def records(d: dict, rs: list[dict]) -> list[dict]:
    """Baris lengkap (header disebar ke tiap baris) + kolom turunan + nilai ternormalisasi."""
    h = d["header"]
    out = []
    for r in rs:
        x = dict(r["data"])
        rec: dict[str, Any] = {"_row": r["id"], "_idx": r["idx"], "_verified": r["verified"], "_doc": d["id"], "_uid": d["uid"],
                               "_name": d["name"], "_key": f"{d['uid']}:{r['id']}", "_tbl": r.get("tbl") or ""}
        if d["type"] == "ddr":
            rec.update(ddr_common(d))
            if rec["_tbl"] == "hole":
                f_, t_ = parse_num(x.get("from_m")), parse_num(x.get("to_m"))
                rec.update({"hole_id": norm_bhid(x.get("hole_id")), "from_m": f_, "to_m": t_,
                            "meter": round(t_ - f_, 2) if f_ is not None and t_ is not None else None,
                            "az": parse_num(x.get("az")), "dip": parse_num(x.get("dip"))})
            else:
                kat = kat_norm(x.get("kategori")) or ddr_kat(x.get("aktivitas"))
                rec.update({"mulai": parse_time(x.get("mulai")) or x.get("mulai") or "", "selesai": parse_time(x.get("selesai")) or x.get("selesai") or "",
                            "durasi": ddr_dur(x.get("mulai"), x.get("selesai")), "aktivitas": re.sub(r"\s+", " ", str(x.get("aktivitas") or "")).strip(),
                            "kategori": kat, "kelompok": DDR_GROUP.get(kat, "DL")})
        elif d["type"] in ORE_TYPES:
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
            tg = parse_date(x.get("tanggal")) or tg
            rec.update({"hole_id": norm_bhid(x.get("hole_id") or h.get("hole_id")),
                        "tanggal": tg.isoformat() if tg else str(x.get("tanggal") or h.get("tanggal") or ""),
                        "sample_id": (x.get("sample_id") or "").strip(), "from_m": parse_num(x.get("from_m")), "to_m": parse_num(x.get("to_m")),
                        "lith": (x.get("lith") or "").strip(), "alt": (x.get("alt") or "").strip(), "min1": (x.get("min1") or "").strip(),
                        "vein": (x.get("vein") or "").strip(), "qt": parse_num(x.get("qt")), "remark": qaqc(x.get("remark"))})
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
    if d["type"] == "ddr":
        ks = shift_code(h.get("shift"))
        if not ks:
            hdr["shift"] = "shift harus I / II (siang / malam)"
        if not str(h.get("rig") or "").strip():
            hdr["rig"] = "drill rig kosong"
        for k in HOURS + ("hm_start", "hm_finish", "hm_running", "bit_drilled"):
            if str(h.get(k) or "").strip() and (parse_hours(h.get(k)) if k in HOURS else parse_num(h.get(k))) is None:
                hdr[k] = "harus angka" + (" (jam)" if k in HOURS else "")
        hs, hf = parse_num(h.get("hm_start")), parse_num(h.get("hm_finish"))
        if hs is not None and hf is not None and hf < hs:
            hdr["hm_finish"] = "HM finish lebih kecil dari HM start"
        act = [r for r in rs if not r.get("tbl")]
        hole = [r for r in rs if r.get("tbl") == "hole"]
        prev = None
        for r in act:
            x = r["data"]
            for k in ("mulai", "selesai"):
                if not x.get(k):
                    bad(r, k, "jam kosong")
                elif not parse_time(x.get(k)):
                    bad(r, k, "jam tidak valid (HH:MM)")
            a, b = parse_time(x.get("mulai")), parse_time(x.get("selesai"))
            if a and b:
                dur = ddr_dur(a, b)
                if a == b:
                    bad(r, "selesai", "durasi nol")
                elif dur and dur > 12:
                    bad(r, "selesai", f"durasi {dur:g} jam — periksa jam")
                for k, t in (("mulai", a), ("selesai", b)):
                    hh, mm = int(t[:2]), int(t[3:])
                    inside = SHIFT_DS[0] <= hh < SHIFT_DS[1] or (hh == SHIFT_DS[1] and mm == 0)
                    if ks == "DS" and not inside and k not in out.get(r["id"], {}):
                        bad(r, k, f"di luar shift siang (I, {SHIFT_DS[0]:02d}:00-{SHIFT_DS[1]:02d}:00) — lembur / periksa jam")
                    elif ks == "NS" and SHIFT_DS[0] < hh < SHIFT_DS[1] and k not in out.get(r["id"], {}):
                        bad(r, k, f"di luar shift malam (II, {SHIFT_DS[1]:02d}:00-{SHIFT_DS[0]:02d}:00) — periksa jam")
                if prev and prev != a and "mulai" not in out.get(r["id"], {}):
                    bad(r, "mulai", f"tidak menyambung dengan kegiatan sebelumnya (selesai {prev})")
            prev = b or prev
            if not str(x.get("aktivitas") or "").strip():
                bad(r, "aktivitas", "uraian kegiatan kosong")
            if x.get("kategori") and kat_norm(x.get("kategori")) not in DDR_KAT_NAMES:
                bad(r, "kategori", "kategori bukan " + " / ".join(DDR_KAT_NAMES))
        seen: dict[str, int] = {}
        for r in hole:
            x = r["data"]
            f_, t_ = parse_num(x.get("from_m")), parse_num(x.get("to_m"))
            if f_ is None:
                bad(r, "from_m", "From harus angka")
            if t_ is None:
                bad(r, "to_m", "To harus angka")
            if f_ is not None and t_ is not None and t_ <= f_:
                bad(r, "to_m", "To harus lebih besar dari From")
            hid = norm_bhid(x.get("hole_id"))
            if not hid:
                bad(r, "hole_id", "Hole ID kosong")
            elif hid in seen and f_ is not None and seen[hid] is not None and f_ < seen[hid] - 1e-6:
                bad(r, "from_m", f"tumpang-tindih dengan baris {hid} sebelumnya (berakhir {seen[hid]:g} m)")
            if hid:
                seen[hid] = t_
            az, dp = parse_num(x.get("az")), parse_num(x.get("dip"))
            if x.get("az") and (az is None or not 0 <= az <= 360):
                bad(r, "az", "azimuth 0-360")
            if x.get("dip") and (dp is None or not -90 <= dp <= 90):
                bad(r, "dip", "dip -90..90")
        sm = ddr_summary(d, rs)
        for k in HOURS:
            if sm[k] is not None and act and abs(sm[k] - sm[k + "_akt"]) > 0.5 and k not in hdr:
                hdr[k] = f"{k.upper()} {sm[k]:g} jam, jumlah aktivitas kelompok {k.upper()} {sm[k + '_akt']:g} jam — periksa kategori / jam"
    elif d["type"] in ORE_TYPES:
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
        if not (h.get("hole_id") or "").strip() and not any((r["data"].get("hole_id") or "").strip() for r in rs):
            hdr["hole_id"] = "Hole ID kosong"
        seen: dict[str, int] = {}
        prev = None
        hole = None
        for r in rs:
            x = r["data"]
            f, t = parse_num(x.get("from_m")), parse_num(x.get("to_m"))
            hid = norm_bhid(x.get("hole_id") or h.get("hole_id"))
            if hid != hole:  # lubang baru: interval mulai dari awal
                hole, prev = hid, None
            if qaqc(x.get("remark")) in ("STD", "BLANK") and f is None and t is None:
                continue  # sampel QAQC sisipan tanpa interval: tidak memutus urutan From / To lubang
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
       "ritase": "Ritase", "tonase": "Tonase", "rig": "Drill rig", "kategori": "Kategori", "kelompok": "Kelompok jam", "jam": "Jam",
       "kegiatan": "Kegiatan", "hole_id": "Hole ID", "lubang": "Lubang", "meter": "Meter", "driller": "Driller", "interval": "Interval"}
# bagian ekspor per jenis borang: (nama bagian -> OUT / DB_TABLE / SHEET, tabel sumber: '' utama, 'hole', '_shift' ringkasan)
PARTS = {"ore": [("ore", "")], "rom": [("rom", "")], "rc": [("rc", "")],
         "ddr": [("ddr_dash", "_dash"), ("ddr", ""), ("ddr_hole", "hole"), ("ddr_shift", "_shift")]}
DERIVED_PARTS = ("_shift", "_dash")  # baris turunan (ringkasan / dashboard), tidak dihitung sebagai baris borang
_ORE_AGG = [("ritase", "count", None), ("tonase", "sum", "ton")]
PIVOTS = {
    "ore": [("PIVOT_PER_SHIFT", "Per shift", "ore", ["tanggal", "shift", "kode_shift"], _ORE_AGG),
            ("PIVOT_PER_FRONT", "Per front (pit · elevasi · excavator)", "ore", ["tanggal", "front", "excavator"], _ORE_AGG),
            ("PIVOT_TUJUAN_KELAS", "Per tujuan dumping × kelas material", "ore", ["tanggal", "tujuan", "kelas"], _ORE_AGG)],
    "rom": [("PIVOT_PER_SHIFT", "Per shift", "rom", ["tanggal", "shift", "kode_shift"], _ORE_AGG),
            ("PIVOT_ASAL_TUJUAN", "Per asal → tujuan (direct / rehandling)", "rom", ["tanggal", "asal", "tujuan", "jenis"], _ORE_AGG),
            ("PIVOT_TUJUAN_KELAS", "Per tujuan × kelas material", "rom", ["tanggal", "tujuan", "kelas"], _ORE_AGG)],
    "ddr": [("PIVOT_JAM_KELOMPOK", "Jam per kelompok (WH / DL / MNTC / BD / RAIN / STD)", "ddr", ["tanggal", "rig", "shift", "kelompok"],
             [("jam", "sum", "durasi"), ("kegiatan", "count", None)]),
            ("PIVOT_JAM_KATEGORI", "Jam per kategori aktivitas", "ddr", ["tanggal", "rig", "shift", "kategori"],
             [("jam", "sum", "durasi"), ("kegiatan", "count", None)]),
            ("PIVOT_METER_RIG", "Meter per rig & shift", "ddr_hole", ["tanggal", "rig", "shift", "driller"],
             [("lubang", "count", None), ("meter", "sum", "meter")]),
            ("PIVOT_METER_LUBANG", "Meter per lubang", "ddr_hole", ["hole_id", "rig"], [("meter", "sum", "meter"), ("interval", "count", None)])],
}


def part_tbl(part: str) -> str:
    return next(tb for ps in PARTS.values() for p, tb in ps if p == part)


def part_recs(recs: list[dict], part: str) -> list[dict]:
    tb = part_tbl(part)
    return [r for r in recs if (r.get("_tbl") or "") == tb]


def pivots(recs: list[dict], ftype: str = "ore") -> list[dict]:
    """Pivot -> [{"key", "title", "part", "cols": [[k, label]], "rows": [dict]}] (juga untuk sheet Excel & view SQLite)."""
    out = []
    for key, title, part, keys, aggs in PIVOTS.get(ftype, []):
        g: dict = {}
        for r in part_recs(recs, part):
            g.setdefault(tuple(r.get(k) for k in keys), []).append(r)
        rows_ = []
        for k, v in sorted(g.items(), key=lambda kv: [str(x) for x in kv[0]]):
            x = dict(zip(keys, k))
            for name, op, fld in aggs:
                x[name] = len(v) if op == "count" else round(sum(y.get(fld) or 0 for y in v), 2)
            rows_.append(x)
        out.append({"key": key, "title": title, "part": part, "cols": [[k, LAB.get(k, k)] for k in keys + [a[0] for a in aggs]], "rows": rows_})
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
    "ddr": [("TANGGAL", "Date", "tanggal", "DATE"), ("SHIFT", "Shift", "shift", "TEXT"), ("KODE_SHIFT", "Kode Shift", "kode_shift", "TEXT"),
            ("RIG", "Drill Rig", "rig", "TEXT"), ("DRILLER", "Driller", "driller", "TEXT"), ("CLIENT", "Client", "client", "TEXT"),
            ("DHP_ID", "DHP ID", "dhp_id", "TEXT"), ("MULAI", "Mulai", "mulai", "TEXT"), ("SELESAI", "Selesai", "selesai", "TEXT"),
            ("DURASI_JAM", "Durasi (jam)", "durasi", "NUM"), ("AKTIVITAS", "Drilling Details / Formation Description", "aktivitas", "TEXT"),
            ("KATEGORI", "Kategori", "kategori", "TEXT"), ("KELOMPOK", "Kelompok Jam", "kelompok", "TEXT")],
    "ddr_hole": [("TANGGAL", "Date", "tanggal", "DATE"), ("SHIFT", "Shift", "shift", "TEXT"), ("KODE_SHIFT", "Kode Shift", "kode_shift", "TEXT"),
                 ("RIG", "Drill Rig", "rig", "TEXT"), ("DRILLER", "Driller", "driller", "TEXT"), ("HOLE_ID", "Hole ID", "hole_id", "TEXT"),
                 ("FROM_M", "From (m)", "from_m", "NUM"), ("TO_M", "To (m)", "to_m", "NUM"), ("METER", "Meter", "meter", "NUM"),
                 ("AZ", "Az", "az", "NUM"), ("DIP", "Dip", "dip", "NUM")],
    "ddr_dash": [("DRILL_DATE", "Date", "tanggal", "DATE"), ("EQTYPE", "EqType", "eqtype", "TEXT"), ("LOCATION", "Location", "location", "TEXT"),
                 ("SHIFT", "Shift", "shift_code", "TEXT"), ("PROSPECT", "Prospect", "prospect", "TEXT"), ("BHID", "BHID", "bhid", "TEXT"),
                 ("INTERVAL_M", "Interval_m", "interval_m", "NUM"), ("WH", "WH", "wh", "NUM"), ("MAINT", "Maint", "mntc", "NUM"),
                 ("BD", "BD", "bd", "NUM"), ("DELAY", "Delay", "dl", "NUM"), ("STANDBY", "Standby", "std", "NUM"), ("RAIN", "Rain", "rain", "NUM"),
                 ("REMARKS", "Remarks", "remarks", "TEXT"), ("AZIMUTH", "Azimuth", "az", "NUM"), ("DIP", "Dip", "dip", "NUM")],
    "ddr_shift": [("TANGGAL", "Date", "tanggal", "DATE"), ("SHIFT", "Shift", "shift", "TEXT"), ("KODE_SHIFT", "Kode Shift", "kode_shift", "TEXT"),
                  ("RIG", "Drill Rig", "rig", "TEXT"), ("DRILLER", "Driller", "driller", "TEXT"), ("CLIENT", "Client", "client", "TEXT"),
                  ("DHP_ID", "DHP ID", "dhp_id", "TEXT")]
    + [(k.upper(), k.upper() + " (borang)", k, "NUM") for k in HOURS]
    + [(k.upper() + "_AKT", k.upper() + " dari aktivitas", k + "_akt", "NUM") for k in HOURS]
    + [("JAM_BORANG", "Total jam borang", "jam_borang", "NUM"), ("JAM_AKTIVITAS", "Total jam aktivitas", "jam_aktivitas", "NUM"),
       ("JAM_DRILLING", "Jam drilling", "jam_drilling", "NUM"), ("N_LUBANG", "Jumlah lubang", "n_lubang", "NUM"),
       ("METER", "Meter", "meter", "NUM"), ("M_PER_JAM", "Meter / jam drilling", "m_per_jam", "NUM"),
       ("HM_START", "HM Start", "hm_start", "NUM"), ("HM_FINISH", "HM Finish", "hm_finish", "NUM"), ("HM_RUNNING", "HM Running", "hm_running", "NUM"),
       ("BIT_TYPE", "Bit Type", "bit_type", "TEXT"), ("BIT_SERIAL", "Bit Serial No.", "bit_serial", "TEXT"), ("BIT_ON", "Bit On", "bit_on", "TEXT"),
       ("BIT_OFF", "Bit Off", "bit_off", "TEXT"), ("BIT_DRILLED", "Bit Drilled (m)", "bit_drilled", "NUM"), ("CATATAN", "Catatan", "catatan", "TEXT"),
       ("GEOLOGIST", "Geologist Approval", "geologist", "TEXT")],
    "rc": [("HOLE_ID", "HOLE_ID", "hole_id", "TEXT"), ("TANGGAL", "Tanggal", "tanggal", "DATE"), ("SAMPLE_ID", "Sample_ID", "sample_id", "TEXT"),
           ("FROM_M", "From (m)", "from_m", "NUM"), ("TO_M", "To (m)", "to_m", "NUM"), ("LITH", "Lith", "lith", "TEXT"),
           ("INT_ALT", "Int_Alt", "alt", "TEXT"), ("MIN1", "Min1", "min1", "TEXT"), ("VEIN_TYPE", "Vein_Type", "vein", "TEXT"),
           ("QT_PCT", "Qt_pct", "qt", "NUM"), ("REMARK", "Remark (QAQC)", "remark", "TEXT")],
}
DB_TABLE = {"ore": "ORE_LOADING_PIT", "rom": "ORE_ROM_CRUSHER", "rc": "RC_INTERVAL", "ddr": "DDR_AKTIVITAS", "ddr_hole": "DDR_METERAGE",
            "ddr_shift": "DDR_SHIFT", "ddr_dash": "DDR_DASHBOARD"}
SHEET = {"ore": "Data_Loading_Pit", "rom": "Data_ROM_Crusher", "rc": "Interval_Geodatabase", "ddr": "DDR_Aktivitas", "ddr_hole": "DDR_Meterage",
         "ddr_shift": "DDR_Ringkasan_Shift", "ddr_dash": "Data_Dashboard"}
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
        took = 0
        for rec in records(d, rs):
            if rec["_verified"] or unverified:
                recs.append(rec)
                took += 1
            else:
                skip += 1
        if ftype == "ddr" and took:
            recs.append(ddr_summary(d, rs))
            hids = {r["_row"] for r in recs if r["_doc"] == d["id"] and r["_tbl"] == "hole"}
            recs += ddr_dashboard(d, rs, hids)
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
    for i, (part, _tb) in enumerate(PARTS[ftype]):
        cols = OUT[part]
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = SHEET[part]
        sheet(ws, [c[1] for c in cols], [[_val(r, c[2], c[3]) for c in cols] for r in part_recs(recs, part)],
              {j: (("dd-mmm-yyyy" if part == "ddr_dash" else "d-mmm-yy") if c[3] == "DATE" else None) for j, c in enumerate(cols, 1)})
    for pv in pivots(recs, ftype):
        ks = [k for k, _l in pv["cols"]]
        sheet(wb.create_sheet(pv["key"].title()[:31]), [lab for _k, lab in pv["cols"]],
              [[(parse_date(x[k]) or x[k]) if k == "tanggal" else x[k] for k in ks] for x in pv["rows"]],
              {1: "d-mmm-yy"} if ks[0] == "tanggal" else None)
    sheet(wb.create_sheet("Audit"), ["Borang", "Tabel", "Baris", "Diverifikasi", "Kunci sumber"],
          [[r["_name"], {"": "utama", "hole": "meterage"}.get(r["_tbl"], r["_tbl"]), r["_idx"] + 1, "ya" if r["_verified"] else "BELUM", r["_key"]]
           for r in recs if r.get("_tbl") not in DERIVED_PARTS])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


def _csv_part(part: str, recs: list[dict]) -> bytes:
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\r\n")
    cols = OUT[part]
    w.writerow([c[1] if part == "ddr_dash" else c[0] for c in cols] + ["VERIFIED", "SRC_DOC"])
    for r in part_recs(recs, part):
        row = []
        for c in cols:
            v = _val(r, c[2], c[3])
            row.append(v.isoformat() if isinstance(v, date) else ("" if v is None else (f"{v:g}" if isinstance(v, float) else v)))
        w.writerow(row + ["1" if r["_verified"] else "0", r["_name"]])
    return ("\ufeff" + b.getvalue()).encode("utf-8")


def to_csv(ftype: str, recs: list[dict]) -> bytes:
    """Satu tabel -> file CSV; borang dengan beberapa tabel (Daily Drilling Report) -> ZIP berisi satu CSV per tabel."""
    if len(PARTS[ftype]) == 1:
        return _csv_part(PARTS[ftype][0][0], recs)
    import zipfile
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        for part, _tb in PARTS[ftype]:
            z.writestr(DB_TABLE[part] + ".csv", _csv_part(part, recs))
    return b.getvalue()


def _db_rows(part: str, recs: list[dict]) -> tuple[list[str], list[list]]:
    cols = OUT[part]
    names = [c[0] for c in cols] + [a for a, _t in AUDIT]
    data = [[_val(r, c[2], c[3]) for c in cols] + [bool(r["_verified"]), r["_name"], r["_key"]] for r in part_recs(recs, part)]
    return names, data


def to_sqlite(path: str, ftype: str, recs: list[dict]) -> dict:
    """Tambah / perbarui (kunci SRC_KEY = borang:baris) ke file SQLite, satu tabel per bagian borang; view pivot ikut dibuat."""
    tmap = {"TEXT": "TEXT", "NUM": "REAL", "DATE": "TEXT", "BOOL": "INTEGER"}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cn = sqlite3.connect(str(p))
    res = {"tables": [], "added": 0, "updated": 0, "total": 0}
    try:
        with cn:
            for part, _tb in PARTS[ftype]:
                cols = [(c[0], c[3]) for c in OUT[part]] + AUDIT
                names, data = _db_rows(part, recs)
                tb = DB_TABLE[part]
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
                res["tables"].append(tb)
                if part_tbl(part) not in DERIVED_PARTS:
                    res["added"] += after - before
                    res["updated"] += len(data) - (after - before)
                    res["total"] += after
            for key, _t, part, keys, aggs in PIVOTS.get(ftype, []):
                dbcol = {c[2]: c[0] for c in OUT[part]}
                tb = DB_TABLE[part]
                vn = f"{tb}_{key}"
                g = ", ".join(dbcol[k] for k in keys)
                ag = ", ".join(("COUNT(*)" if op == "count" else f"ROUND(SUM({dbcol[f]}), 2)") + f" AS {n.upper()}" for n, op, f in aggs)
                cn.execute(f"DROP VIEW IF EXISTS {vn}")
                cn.execute(f"CREATE VIEW {vn} AS SELECT {g}, {ag} FROM {tb} GROUP BY {g}")
    finally:
        cn.close()
    res["table"] = ", ".join(res["tables"])
    return res


def to_access(path: str, ftype: str, recs: list[dict]) -> dict:
    """Tambahkan ke database MS Access (dibuat bila belum ada; tabel dibuat bila belum ada). Baris dengan SRC_KEY yang sudah ada
    tidak diubah (dilaporkan)."""
    from . import access_io
    created = False
    if not Path(path).exists():
        access_io.create_db(path)
        created = True
    res = {"tables": [], "added": 0, "existing": 0, "db_created": created, "table_created": False}
    for part, _tb in PARTS[ftype]:
        tb = DB_TABLE[part]
        new_tb = access_io.ensure_table(path, tb, [(c[0], c[3]) for c in OUT[part]] + AUDIT, key="SRC_KEY")
        names, data = _db_rows(part, recs)
        if not data:
            continue
        r = access_io.insert(path, tb, names, data, key_column="SRC_KEY", skip_existing=True)
        res["tables"].append(tb)
        res["table_created"] = res["table_created"] or bool(new_tb)
        if part_tbl(part) not in DERIVED_PARTS:
            res["added"] += r["added"]
            res["existing"] += len(r["skipped_existing"])
    res["table"] = ", ".join(res["tables"])
    return {k: v for k, v in res.items() if k != "tables"}


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
    tbl: str = ""


class VerBody(FBody):
    id: int
    on: bool = True


class AiBody(FBody):
    id: int
    host: str = ""
    model: str
    extra: str = ""
    max_px: int = 1600


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
    return {"doc": d, "rows": rs, "valid": v, "recs": recs, "pivot": pivots(recs, d["type"]),
            "summary": ddr_summary(d, rs) if d["type"] == "ddr" else None}


@router.post("/open")
def api_open(b: FBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "docs": docs(s), "types": {k: {"name": t["name"], "header": t["header"], "rows": t["rows"],
                                     "tables": {tb: {"name": tt["name"], "rows": tt["rows"]} for tb, tt in (t.get("tables") or {}).items()}}
                                 for k, t in TYPES.items()},
            "kategori": DDR_KAT_NAMES,
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
    save_rows(s, b.id, b.rows, b.by, b.tbl)
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
    return {"ok": True, "n": sum(1 for r in c["recs"] if r.get("_tbl") not in DERIVED_PARTS), "docs": len(c["docs"]),
            "skipped_unverified": c["skipped_unverified"], "issues": c["issues"]}


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
