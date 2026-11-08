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
def _slug(c: str) -> str:
    return c.lower().replace("-", "")


TYPES: dict[str, dict] = {
    "ore": {
        "name": "Ore Spotter: Loading Pit → ROM / Stockpile",
        "header": [("tanggal", "Tanggal", "date"), ("shift", "Shift (I / II)", "text"), ("crew", "Nama crew / spotter", "text"),
                   ("lokasi", "Lokasi (pit)", "text"), ("excavator", "Excavator (EX)", "text")],
        "rows": [("no", "No", "text"), ("start", "Start loading", "time"), ("finish", "Finish loading", "time"), ("pit", "Pit / blok", "text"),
                 ("elevasi", "Elevasi", "text"), ("kelas", "Kelas material", "text"), ("unit", "Truck", "text"), ("ton", "Tonnage", "num"),
                 ("tujuan", "Tujuan dumping", "text")],
        # 0.44.3: satu nilai per kolom besar; kelas = NAMA judul kolom berwarna tempat truk & tonase ditulis; sel kosong "-"
        "hint": ("Borang 'Form Loading (atau Rehandling) Ore dari Pit to ROM / Stockpile' (Ore Spotter di front loading), lanskap. "
                 "Header: NAMA CREW, LOKASI (pit), nomor excavator (mis. EX-123, ditulis tangan di dekat judul), TANGGAL, SHIFT (I / II). "
                 "Tabel bernomor, satu baris per ritase truk; tulis SEMUA baris bernomor yang ada tulisannya.\n"
                 "Tiap baris TEPAT 9 nilai: No|Start|Finish|PIT|Elevation|Kelas|Truck|Ton|Tujuan.\n"
                 "- Jam ditulis di Start atau Finish; baris berikutnya sering hanya MENIT (mis. 13) -> salin apa adanya.\n"
                 "- Kelas = NAMA judul kolom berwarna tempat nomor truk & tonase ditulis (OX-LG, SF-LG, OX-HG, SF-HG, OX-SG, SF-SG, OX-MO, "
                 "SF-MO); Truck = nomor truk (mis. H026, 26); Ton = tonase.\n- Tujuan Dumping (kolom paling kanan, mis. ROM 1, 〃).\n"
                 "Contoh: \"1|19.03|-|PIT A|100.0|OX-LG|T01|30|ROM 1\", \"2|09|-|〃|〃|SF-LG|T02|31|〃\". Baris yang hanya berisi PIT / "
                 "Elevation tanpa truk tetap ditulis (Kelas, Truck, Ton = -). Abaikan coretan.\n"
                 "TANDA ULANG: tanda \" 〃 = ,, (atau angka 4 / 11 kecil yang sebenarnya tanda ulang) atau garis tegak / miring dari baris "
                 "atas ditulis 〃 (bila diikuti tulisan, mis. \"〃 370\", tulis \"〃 370\")."),
    },
    "rom": {
        "name": "Ore ke Stockpile / Crusher (Rehandling / Direct)",
        "header": [("tanggal", "Tanggal", "date"), ("shift", "Shift (I / II)", "text"), ("crew", "Crew / spotter", "text"),
                   ("lokasi", "Lokasi", "text")],
        "rows": [("no", "No", "text"), ("unit", "Eq. No. Unit", "text"), ("start", "Start loading", "time"),
                 ("finish", "Finish loading", "time"), ("asal", "Asal material", "text"), ("tujuan", "Tujuan", "text"),
                 ("rehandling", "Rehandling tumpukan", "text"), ("kelas", "Kelas material", "text"), ("ton", "Ton", "num"),
                 ("status", "Status (Baru / Lama)", "text"), ("keterangan", "Keterangan", "text")],
        # 0.44.3: SATU nilai per kolom besar (bukan 21 sel per sub-kolom): model 2b melewati sel kosong -> seluruh baris bergeser.
        # Rehandling & kelas ditulis sebagai NAMA judul kolom tempat centang / angka berada; sel kosong wajib "-".
        "hint": ("Borang 'Form Ore to Stockpile / Crusher (Rehandling / Direct)' atau 'Form Untuk Rom to Crusher dan Rom to Rom' (spotter "
                 "di ROM / crusher), lanskap. Header: CREW, LOKASI, TANGGAL, SHIFT (I / II). Tabel bernomor 1-36, satu baris per ritase "
                 "truk; tulis SEMUA baris bernomor yang ada tulisannya.\n"
                 "Tiap baris TEPAT 11 nilai: No|Unit|Start|Finish|Asal|Tujuan|Rehandling|Kelas|Ton|Status|Keterangan.\n"
                 "- Unit = Eq. No. Unit (nomor truk, mis. 4028, 502, DT 501). Start Loading sering kosong (-). Finish = jam (19.02) atau "
                 "hanya menit (:57, 05) -> salin apa adanya.\n- Asal material (mis. 340, 418, OPP, SBG); Tujuan (mis. Crusher).\n"
                 "- Rehandling = NAMA sub-kolom Rehandling Tumpukan yang dicentang (judul kecil di atasnya, mis. SPR (Z2)), - bila tidak ada.\n"
                 "- Kelas = NAMA judul kolom berwarna tempat angka tonase berada (OX-LG, SF-LG, OX-HG, SF-HG, OX-SG, SF-SG, SCAT, OX-MO, "
                 "SF-MO); Ton = angka itu. Status = Baru atau Lama (sub-kolom yang dicentang).\n"
                 "Contoh: \"1|4011|-|18:57|340|Crusher|-|OX-LG|37|Baru|Direct\", \"2|402|-|:16|〃|〃|SPR (Z2)|OX-LG|36|〃|〃\".\n"
                 "TANDA ULANG: tanda \" = ,, atau garis tegak / miring yang menyambung dari baris atas ditulis 〃."),
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
        # jawaban AI cukup 2 kolom (rentang jam + uraian): model kecil (2b) sering menggeser 4 kolom (jam masuk uraian / kategori)
        "ai_rows": [("jam", "Rentang jam, mis. 0630-0700", "text"), ("aktivitas", "Uraian kegiatan", "text")],
        "tables": {"hole": {"name": "Meterage / lubang", "ai": "lubang",
                            "rows": [("from_m", "From (m)", "num"), ("to_m", "To (m)", "num"), ("hole_id", "Hole ID", "text"),
                                     ("az", "Az", "num"), ("dip", "Dip", "num")]}},
        "hint": ("Borang 'Daily Drilling Report' pemboran RC, portrait. Header kanan atas: Client, DHP_ID, Driller, Date, Drill Rig (nama "
                 "unit, mis. 'Hanjin SDR-07' -> tulis apa adanya), Shift (I / II). Tabel kiri METERAGE (From, To), Hole ID, Az, Dip -> isi 'lubang' (satu objek per lubang). Kolom kanan "
                 "'DRILLING DETAILS and FORMATION DESCRIPTION': tiap kegiatan diawali rentang jam, mis. 0650-0700 atau 07.00-07.05, lalu "
                 "uraian (boleh dua baris tulisan) -> satu teks per kegiatan: jam|uraian, mis. \"0630-0700|TRAVELING TO 370\" "
                 "(gabungkan baris lanjutan uraian ke kegiatan yang sama). Kotak bawah: BITS / REAMER (type, serial no., on, off, drilled), HM "
                 "ENGINE (start, finish, HM running), Geologist approval; catatan di bawah tabel: WH, DL, MNTC, BD, RAIN, STD (jam, "
                 "mis. 5hr -> 5) dan tulisan bebas -> 'catatan'. 'lokasi' (nama area / prospek) biasanya tidak tertulis: kosongkan bila "
                 "tidak ada."),
    },
    "rc": {
        "name": "RC Drill Logging / Chiptray Log",
        "header": [("hole_id", "Hole ID (bawaan)", "text"), ("tanggal", "Tanggal pengeboran (bawaan)", "date"),
                   ("no_awal", "No baris pertama (tercetak)", "text"), ("sample_awal", "Sample ID baris pertama (tercetak)", "text")],
        "rows": [("hole_id", "Hole ID", "text"), ("tanggal", "Tanggal", "date"), ("sample_id", "Sample ID", "text"),
                 ("from_m", "From (m)", "num"), ("to_m", "To (m)", "num"), ("lith", "Lith", "text"), ("alt", "Int_Alt", "text"),
                 ("min1", "Min1", "text"), ("vein", "Vein_Type", "text"), ("qt", "Qt_pct", "num"), ("remark", "Remark (QAQC)", "text")],
        # urutan jawaban AI = urutan kolom di borang; Sample ID tercetak TIDAK diminta per baris (dihitung program dari No,
        # lihat rc_fix_all): jawaban jauh lebih pendek, dan model kecil tidak lagi menggeser kolom (galat 0.42.11)
        "ai_rows": [("no", "No (tercetak)", "text"), ("hole_id", "Hole ID", "text"), ("tanggal", "Tanggal", "date"),
                    ("from_m", "From", "num"), ("to_m", "To", "num"), ("lith", "Lith", "text"), ("alt", "Int_Alt", "text"),
                    ("min1", "Min1", "text"), ("vein", "Vein_Type", "text"), ("qt", "Qt_pct", "num"), ("remark", "Remark2", "text")],
        "hint": ("Borang RC Drill Logging Form, biasanya lanskap. Kolom No dan Sample_ID TERCETAK (mis. 99937, DP_150137_Z4). "
                 "Header: hole_id & tanggal kosongkan, no_awal = No baris pertama, sample_awal = Sample_ID baris pertama. "
                 "Setiap baris: No|Hole_ID|Tanggal|From|To|Lith|Int_Alt|Min1|Vein_Type|Qt_pct|Remark2, mis. "
                 "\"10001|XX-100-01|05-11-26|0|1|VLT|IAR|cly\" lalu \"10002|||1|2|〃|〃|〃\" -> Sample_ID JANGAN ditulis di baris (program menghitungnya dari No). Remark2 tercetak pada baris QAQC (STD..., BLANK). Tulisan tangan: Hole_ID dan Tanggal Pengeboran HANYA di baris pertama tiap lubang "
                 "(kadang dua baris: Hole ID lalu Az/Dip, mis. 'AZ 64-60' -> abaikan baris Az/Dip), From, To, Lith, Int_Alt, Min1, "
                 "Vein_Type, Qt_pct. Tulis HANYA baris yang From/To-nya terisi atau berlabel STD / BLANK. Hole_ID & Tanggal: isi hanya "
                 "di baris tempat tertulis, baris lain kosong (program yang meneruskan). Garis bergelombang / kurung kurawal / garis tegak "
                 "panjang di kolom Lith, Int_Alt, Min1 = sama dengan baris di atas -> tulis \"〃\". Kode geologi disalin persis "
                 "(mis. VLT, QMN, ARG, IAR, PRO, SIL, ox, cly, chl-cly, Qz-Mn)."),
    },
}
KELAS = ["OX-LG", "SF-LG", "OX-HG", "SF-HG", "OX-SG", "SF-SG", "SCAT", "OX-MO", "SF-MO"]
# ---------------------------------------------------------------- jenis borang GENERIK (0.44)
# Satu mesin untuk jenis borang yang tidak butuh aturan khusus (Geological Mapping, Channel Sampling, Drill Progress Report)
# dan untuk template kustom buatan pengguna: header disebar ke tiap baris, nilai dinormalkan menurut tipe kolom
# (num / date / time), tanda ulang -> nilai baris atas, kolom 'carry' diteruskan ke bawah, validasi tipe / rentang /
# pilihan / wajib / unik / interval From-To, ekspor & pivot dari definisi. Kunci spesifikasi ada di 'gen'.
STATUS_DPR = ["Drilling", "Selesai", "Standby", "Batal", "Pindah"]
GEN_BUILTIN: dict[str, dict] = {
    "map": {
        "name": "Geological Mapping",
        "header": [("tanggal", "Tanggal", "date"), ("geologist", "Geologist", "text"), ("area", "Area / prospek", "text"),
                   ("koordinat", "Sistem koordinat / zona UTM", "text"), ("catatan", "Catatan", "text")],
        "rows": [("stasiun", "Stasiun", "text"), ("easting", "Easting (X)", "num"), ("northing", "Northing (Y)", "num"),
                 ("elevasi", "Elevasi (m)", "num"), ("litologi", "Litologi", "text"), ("alterasi", "Alterasi", "text"),
                 ("mineralisasi", "Mineralisasi", "text"), ("struktur", "Struktur (vein / sesar / kekar / kontak)", "text"),
                 ("strike", "Strike (°)", "num"), ("dip", "Dip (°)", "num"), ("sample_id", "Sample ID", "text"),
                 ("keterangan", "Keterangan", "text")],
        "hint": ("Borang pemetaan geologi lapangan (Geological Mapping / field mapping sheet). Header: tanggal, nama geologist, area / "
                 "prospek, sistem koordinat (mis. WGS84 UTM 50S), catatan. Tabel: satu baris per stasiun pengamatan: nomor stasiun, "
                 "koordinat Easting / Northing, elevasi, litologi, alterasi, mineralisasi, jenis struktur, strike & dip (derajat), "
                 "Sample ID bila diambil sampel, keterangan. Kode geologi disalin persis."),
        "gen": {"db": "GEO_MAPPING", "sheet": "Data_Mapping", "unique": "sample_id", "req": ["stasiun"],
                "ranges": {"strike": (0, 360), "dip": (0, 90)},
                "pivots": [("PIVOT_LITOLOGI", "Stasiun per litologi", ["litologi"], [("stasiun", "count", None)]),
                           ("PIVOT_STRUKTUR", "Struktur: jumlah & rata-rata dip", ["struktur"], [("stasiun", "count", None), ("dip_rata", "avg", "dip")])]},
    },
    "chn": {
        "name": "Channel Sampling",
        "header": [("tanggal", "Tanggal", "date"), ("geologist", "Geologist / sampler", "text"), ("lokasi", "Pit / lokasi", "text"),
                   ("bench", "Bench / elevasi", "text"), ("channel_id", "Channel ID (bawaan)", "text"), ("azimuth", "Azimuth channel (°)", "num"),
                   ("easting", "Easting awal (X)", "num"), ("northing", "Northing awal (Y)", "num")],
        "rows": [("channel_id", "Channel ID", "text"), ("sample_id", "Sample ID", "text"), ("from_m", "From (m)", "num"),
                 ("to_m", "To (m)", "num"), ("litologi", "Litologi", "text"), ("alterasi", "Alterasi", "text"),
                 ("mineralisasi", "Mineralisasi / vein", "text"), ("berat", "Berat (kg)", "num"), ("qaqc", "QAQC (STD / BLANK / DUP)", "text"),
                 ("keterangan", "Keterangan", "text")],
        "hint": ("Borang channel sampling (sampel alur di dinding pit / singkapan / parit). Header: tanggal, geologist / sampler, pit / "
                 "lokasi, bench / elevasi, Channel ID, azimuth channel, koordinat awal. Tabel: satu baris per sampel: Channel ID (biasanya "
                 "hanya di baris pertama tiap channel), Sample ID, From, To (meter sepanjang channel), litologi, alterasi, mineralisasi / "
                 "vein, berat sampel (kg), QAQC (STD / BLANK / DUP bila sampel kontrol), keterangan."),
        "gen": {"db": "CHANNEL_SAMPLE", "sheet": "Data_Channel", "unique": "sample_id", "req": ["sample_id"], "carry": ["channel_id"],
                "interval": ("channel_id", "from_m", "to_m"), "derived": [("panjang", "Panjang (m)", "num")],
                "ranges": {"berat": (0, 50)}, "enums": {"qaqc": ["", "STD", "BLANK", "DUP"]},
                "pivots": [("PIVOT_CHANNEL", "Per channel", ["channel_id"], [("sampel", "count", None), ("panjang", "sum", "panjang")]),
                           ("PIVOT_LITOLOGI", "Per litologi", ["litologi"], [("sampel", "count", None), ("panjang", "sum", "panjang")])]},
    },
    "dpr": {
        "name": "Drill Progress Report",
        "header": [("tanggal", "Tanggal", "date"), ("shift", "Shift (I / II)", "text"), ("rig", "Drill rig", "text"),
                   ("kontraktor", "Kontraktor", "text"), ("supervisor", "Supervisor / geologist", "text"), ("lokasi", "Lokasi / prospek", "text")],
        "rows": [("hole_id", "Hole ID", "text"), ("rencana", "Kedalaman rencana (m)", "num"), ("from_m", "From (m)", "num"),
                 ("to_m", "To (m)", "num"), ("status", "Status (" + " / ".join(STATUS_DPR) + ")", "text"), ("mulai", "Jam mulai", "time"),
                 ("selesai", "Jam selesai", "time"), ("keterangan", "Keterangan", "text")],
        "hint": ("Borang Drill Progress Report (laporan kemajuan pemboran harian per rig). Header: tanggal, shift (I / II), drill rig, "
                 "kontraktor, supervisor / geologist, lokasi / prospek. Tabel: satu baris per lubang yang dibor pada shift itu: Hole ID, "
                 "kedalaman rencana (m), kedalaman awal shift (From) dan akhir shift (To), status lubang (" + ", ".join(STATUS_DPR) + "), "
                 "jam mulai & selesai, keterangan (mis. kendala, ganti bit)."),
        "gen": {"db": "DRILL_PROGRESS", "sheet": "Data_Progress", "req": ["hole_id"], "enums": {"status": [""] + STATUS_DPR},
                "derived": [("meter", "Meter shift", "num"), ("progres_pct", "Progres (% rencana)", "num")],
                "pivots": [("PIVOT_RIG", "Meter per rig & shift", ["tanggal", "rig", "shift"], [("lubang", "count", None), ("meter", "sum", "meter")]),
                           ("PIVOT_LUBANG", "Meter per lubang", ["hole_id"], [("meter", "sum", "meter"), ("kedalaman", "max", "to_m")])]},
    },
}
ORE_TYPES = ("ore", "rom")
TYPES.update(GEN_BUILTIN)
BUILTIN_KEYS = set(TYPES)
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
            cols = {r[1] for r in c.execute("PRAGMA table_info(docs)")}
            if "auto" not in cols:  # Auto Detect (0.44): 1 = menunggu AI, 2 = dari nama file
                c.execute("ALTER TABLE docs ADD COLUMN auto INTEGER DEFAULT 0")
            if "crop" not in cols:  # area potong manual (0.44.4): [x0, y0, x1, y1] pecahan 0-1 gambar ASLI (sebelum diputar)
                c.execute("ALTER TABLE docs ADD COLUMN crop TEXT DEFAULT ''")
        _STORES[key] = s
        load_templates(s)
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


_SAMPLE = re.compile(r"^[A-Za-z]{1,5}[_\-]?\d{4,}[_\-][A-Za-z]\w*$")
_RC_SHIFT = ("from_m", "to_m", "lith", "alt", "min1", "vein", "qt", "remark")


def _int(v: Any) -> Optional[int]:
    t = re.sub(r"\D", "", str(v or ""))
    return int(t) if t and len(t) <= 9 else None


def rc_fix_all(lst: list[dict], h: dict) -> list[dict]:
    """Jawaban AI RC logging -> baris tabel:
    - kolom bergeser karena model menyalin Sample_ID tercetak ([No, Sample_ID, From, To, ...]) -> dikembalikan ke tempatnya;
    - Sample_ID dihitung dari No tercetak: Sample = Sample baris pertama + (No - No baris pertama), mis. No 99940 dengan
      99937 = DP_150035_Z4 -> DP_150038_Z4 (ditandai kuning: periksa terhadap scan)."""
    out = []
    for r in lst:
        x = dict(r)
        x["ragu"] = list(r.get("ragu") or [])
        hid, tg = str(x.get("hole_id") or "").strip(), str(x.get("tanggal") or "").strip()
        if not x.get("sample_id") and _SAMPLE.match(hid) and (not tg or parse_num(tg) is not None):
            vals = [x.get("tanggal")] + [x.get(k) for k in _RC_SHIFT]
            x["sample_id"], x["hole_id"], x["tanggal"] = hid, "", ""
            for k, v in zip(_RC_SHIFT, vals):
                x[k] = v if v is not None else ""
        out.append(x)
    no0, s0 = _int(h.get("no_awal")), str(h.get("sample_awal") or "").strip()
    if not (no0 and re.search(r"\d{3,}", s0)):  # rujukan dari baris pertama yang No dan Sample_ID-nya terbaca
        ref = next((x for x in out if _int(x.get("no")) and _SAMPLE.match(str(x.get("sample_id") or "").strip())), None)
        no0, s0 = (_int(ref["no"]), str(ref["sample_id"]).strip()) if ref else (None, "")
    m = re.match(r"^(.*?)(\d{3,})(.*)$", s0) if no0 else None
    for x in out:
        n = _int(x.get("no"))
        if m and n and not str(x.get("sample_id") or "").strip() and abs(n - no0) < 10000:
            v = int(m.group(2)) + n - no0
            if v >= 0:
                x["sample_id"] = m.group(1) + str(v).zfill(len(m.group(2))) + m.group(3)
                x["ragu"].append("sample_id")
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
            mv = re.fullmatch(r"[.:,]?\s*(\d{1,2})", v)
            if mv and pt:
                v = mv.group(1)
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
    for k, dv in (("header_json", {}), ("hdr_unc", []), ("crop", None)):
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
    """Tambah scan / foto / PDF borang (disalin ke proyek). PDF dipecah: satu borang per halaman.
    ftype 'auto' (Auto Detect): jenis ditebak dari nama file (auto=2); bila tidak ada petunjuk, AI menentukannya saat membaca (auto=1)."""
    auto = 0
    if ftype == "auto":
        ftype = guess_type(src)
        auto = 2 if ftype else 1
        ftype = ftype or next(iter(TYPES))
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
    last = [x for x in docs(s) if x["type"] == ftype and x.get("rot")] if not auto == 1 else []
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
            if auto:
                c.execute("UPDATE docs SET auto=? WHERE id=?", (auto, did))
                if auto == 2:
                    _hist(c, did, "jenis (Auto Detect nama file)", None, ftype, "auto", by)
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
                if n and not values.get("clear"):
                    raise ValueError("Jenis borang tidak bisa diganti setelah ada baris; hapus baris dulu atau tambahkan ulang file-nya.")
                if n:  # 'clear': jenis salah terdeteksi -> baris hasil baca lama dibuang, lalu dibaca ulang dengan jenis yang benar
                    c.execute("DELETE FROM rows WHERE doc_id=?", (did,))
                    c.execute("UPDATE docs SET header_json='{}', hdr_unc='[]', status='pending' WHERE id=?", (did,))
                    _hist(c, did, "hapus semua baris (ganti jenis)", str(n), None, "edit", by)
                sets.append("type=?")
                vals.append(values["type"])
                _hist(c, did, "jenis", d["type"], values["type"], "edit", by)
            sets.append("auto=0")
        if "crop" in values:
            cr = norm_crop(values["crop"])
            sets.append("crop=?")
            vals.append(json.dumps(cr) if cr else "")
            if cr != d.get("crop"):
                _hist(c, did, "potong area", json.dumps(d.get("crop")) if d.get("crop") else None, json.dumps(cr) if cr else None, "edit", by)
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
    if is_gen(d["type"]) and not tbl:
        datas = [x for x, _f in gen_fill(d["type"], datas, d["header"], carry=False)]
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


def ai_rows(t: dict) -> list:
    """Kolom baris yang diminta dari AI (boleh lebih sedikit dari kolom tabel, mis. Daily Drilling Report: jam + uraian)."""
    return t.get("ai_rows") or t["rows"]


_RANGE = re.compile(r"(\d{1,2})\s*[.:°'`]?\s*(\d{2})\s*(?:-|–|—|~|/|s\.?d\.?|to|sampai)\s*(\d{1,2})\s*[.:°'`]?\s*(\d{2})(?!\d)", re.I)


def ddr_fix(r: dict) -> dict:
    """Satu baris aktivitas Daily Drilling Report dari AI -> mulai, selesai, aktivitas, kategori, apa pun urutan / kolom yang
    dipakai model. Rentang jam (0630-0700, 07.00-07.05, 0700 - 0705) dicari di SEMUA sel; teks lain = uraian; kategori hanya
    dipertahankan bila nama kategori yang dikenal (selain itu dikosongkan -> diisi program dari kata kunci uraian)."""
    keys = ("jam", "mulai", "selesai", "aktivitas", "kategori")
    vals = {k: str(r.get(k) if r.get(k) is not None else "").strip() for k in keys}
    ragu = list(r.get("ragu") or [])
    mulai, selesai = parse_time(vals["mulai"]), parse_time(vals["selesai"])
    texts, rng_key = [], None
    for k in keys:
        v = vals[k]
        if not v or (k in ("mulai", "selesai") and parse_time(v)):
            continue
        m = _RANGE.search(v)
        if m:
            a, b = parse_time(m.group(1) + m.group(2)), parse_time(m.group(3) + m.group(4))
            if a and b:
                if not (mulai and selesai):
                    mulai, selesai, rng_key = a, b, k
                v = (v[:m.start()] + " " + v[m.end():]).strip(" -:|,?")
        if k == "kategori":
            kn = kat_norm(v)
            if kn in DDR_KAT_NAMES:
                continue
        if v and v not in texts:
            texts.append(v)
    out = {k: v for k, v in r.items() if k not in keys and k != "ragu"}
    kn = kat_norm(vals["kategori"])
    out.update({"mulai": mulai or vals["mulai"], "selesai": selesai or vals["selesai"], "aktivitas": " ".join(texts),
                "kategori": kn if kn in DDR_KAT_NAMES else ""})
    rg = []
    for k in ragu:
        rg += ["mulai", "selesai"] if k in ("jam", rng_key) and k != "aktivitas" else [k]
    out["ragu"] = [k for k in dict.fromkeys(rg) if k in ("mulai", "selesai", "aktivitas", "kategori")]
    return out


def _ragu(r: dict, keys: Any) -> bool:
    return any(k in (r.get("ragu") or []) for k in keys)


ORE_CLS = ["OX-LG", "SF-LG", "OX-HG", "SF-HG", "OX-SG", "SF-SG", "OX-MO", "SF-MO"]
ROM_CLS = ["OX-LG", "SF-LG", "OX-HG", "SF-HG", "OX-SG", "SF-SG", "SCAT", "OX-MO", "SF-MO"]


def class_order(h: dict, default: list[str]) -> tuple[list[str], bool]:
    """Urutan kolom kelas yang TERCETAK di borang (header kelas_urut, dibaca AI) bila lengkap & sah; selain itu urutan baku.
    Ada versi borang dengan SCAT di tengah dan versi dengan SCAT paling kanan."""
    raw = str((h or {}).get("kelas_urut") or "")
    toks = [t for t in re.split(r"[,;|/\n]+", raw.upper()) if t.strip()]
    if len(toks) < len(default):  # dipisah spasi saja
        toks = [t for t in re.split(r"\s+", raw.upper()) if t]
    norm = {_slug(c).upper(): c for c in default}
    got = []
    for t in toks:
        c = norm.get(re.sub(r"[^A-Z]", "", t))
        if c and c not in got:
            got.append(c)
    return (got, True) if len(got) == len(default) else (list(default), False)


def ore_fix(r: dict, h: Optional[dict] = None) -> dict:
    """Ore Spotter: sel TRUCK / Tonnage per kelas (urutan kolom borang) -> kelas, unit, ton. Jawaban lama (kelas sudah
    ditulis model) dibiarkan. Lebih dari satu kelompok terisi -> kelompok pertama dipakai, kelas ditandai kuning."""
    if str(r.get("kelas") or "").strip() or str(r.get("unit") or "").strip():
        return r
    out = {k: v for k, v in r.items() if not re.match(r"^[a-z]{2,4}_(trk|ton)$", k)}
    ragu = [k for k in (r.get("ragu") or []) if not re.match(r"^[a-z]{2,4}_(trk|ton)$", k)]
    hits = []
    order, _ok = class_order(h or {}, ORE_CLS)
    for pos, c0 in enumerate(ORE_CLS):  # sel ke-i (kunci urutan baku) = kolom kelas ke-i yang tercetak
        trk, ton = (str(r.get(f"{_slug(c0)}_{x}") or "").strip() for x in ("trk", "ton"))
        if (trk or ton) and re.search(r"\d", trk + ton):  # titik / coretan saja bukan isian
            hits.append((order[pos], trk, ton, c0))
    if hits:
        c, trk, ton, c0 = hits[0]
        if not ton and re.match(r"^\S+\s+\d+(?:[.,]\d+)?$", trk):  # "H026 30" dalam satu sel
            trk, ton = trk.rsplit(None, 1)
        out.update({"kelas": c, "unit": trk, "ton": ton})
        sl = _slug(c0)
        ragu += (["unit"] if _ragu(r, [f"{sl}_trk"]) else []) + (["ton"] if _ragu(r, [f"{sl}_ton"]) else [])
        if len(hits) > 1:
            ragu.append("kelas")
    out["ragu"] = list(dict.fromkeys(ragu))
    return out


_CHECK = ("", "-")


def rom_fix(r: dict, h: dict) -> dict:
    """ROM / Crusher: sub-kolom rehandling (centang), kolom kelas (angka tonase) dan Baru / Lama (centang) menurut urutan
    kolom borang -> rehandling (nama tumpukan dari header), kelas + ton, status. Jawaban lama (kelas sudah ditulis) dibiarkan."""
    if str(r.get("kelas") or "").strip() or str(r.get("status") or "").strip() or str(r.get("rehandling") or "").strip():
        return r
    order, _ok = class_order(h, ROM_CLS)
    sl = {_slug(c0): order[i] for i, c0 in enumerate(ROM_CLS)}  # sel ke-i = kolom kelas ke-i yang tercetak
    drop = set(sl) | {"rh1", "rh2", "rh3", "baru", "lama"}
    out = {k: v for k, v in r.items() if k not in drop}
    ragu = [k for k in (r.get("ragu") or []) if k not in drop]
    val = {k: str(r.get(k) or "").strip() for k in drop}
    rh = [k for k in ("rh1", "rh2", "rh3") if val[k] not in _CHECK]
    if rh:
        k = rh[0]
        v = val[k]
        name = str(h.get(k) or "").strip()
        out["rehandling"] = "〃" if v == "〃" else (name or (v if len(v) > 2 else f"Tumpukan {k[-1]}"))
        if len(rh) > 1 or _ragu(r, [k]) or not name:
            ragu.append("rehandling")
    ks = [k for k in sl if val[k] not in _CHECK and (re.search(r"\d", val[k]) or is_ditto(val[k]))]  # titik / coretan bukan tonase
    if ks:
        out.update({"kelas": sl[ks[0]], "ton": val[ks[0]]})
        if len(ks) > 1:
            ragu.append("kelas")
        if _ragu(r, [ks[0]]):
            ragu.append("ton")
    b, l = val["baru"] not in _CHECK, val["lama"] not in _CHECK
    if b or l:
        out["status"] = "〃" if "〃" in (val["baru"], val["lama"]) else ("Baru" if b else "Lama")
        if b and l:
            ragu.append("status")
    out["ragu"] = list(dict.fromkeys(ragu))
    return out


def ai_schema_compact(ftype: str) -> dict:
    """Skema jawaban RINGKAS tetapi DIPAKSA Ollama (structured output): header & tiap baris berupa daftar nilai berurutan
    (tanpa nama kolom yang diulang di setiap baris). Model kecil (2b) tidak bisa lagi menulis penjelasan / format lain
    (galat 0.42.4-0.42.7: 'The user says…', 'TIME', 'From' masuk sebagai baris)."""
    t = TYPES[ftype]

    def arr(n: int) -> dict:
        return {"type": "array", "items": {"type": "string"}, "minItems": n, "maxItems": n}
    # 0.42.12: tiap baris tabel = SATU teks "nilai|nilai|…" (bukan daftar ["nilai", "nilai", …]): tanda kutip dan koma per sel
    # hilang, sel kosong cukup '||' -> jawaban kira-kira separuh token -> separuh waktu tulis di CPU
    # batas panjang per baris: model tidak bisa menumpuk seluruh tabel dalam satu teks (0.44.3: 1 baris, 450 detik)
    line = {"type": "string", "maxLength": max(120, min(400, 24 + 16 * len(ai_rows(t))))}
    props = {"h": arr(len(t["header"])), "r": {"type": "array", "items": line}, "c": {"type": "string", "maxLength": 200}}
    req = ["h", "r"]
    for tt in (t.get("tables") or {}).values():
        props[tt["ai"]] = {"type": "array", "items": {"type": "string", "maxLength": max(120, min(400, 24 + 16 * len(tt["rows"])))}}
        req.append(tt["ai"])
    return {"type": "object", "required": req, "properties": props}


VOCAB_SKIP = {"sample_id", "hole_id", "no", "aktivitas", "stasiun", "channel_id", "trench_id", "catatan", "remark"}
_OCR = str.maketrans({"5": "S", "0": "O", "8": "B", "1": "I", "2": "Z", "6": "G", " ": "", "-": "", "_": "", ".": ""})


def site_vocab(s: "Store", ftype: str, per: int = 8, total: int = 60) -> dict[str, list[str]]:
    """Kamus site: nilai teks yang sudah DIVERIFIKASI geologist (>= 2 kali) per kolom, di semua borang jenis ini di proyek.
    Disuntikkan ke prompt AI dan dipakai merapikan salah baca yang mirip (5BG -> SBG). Hanya dari data proyek sendiri
    (tidak pernah disimpan di aplikasi / repo)."""
    t = TYPES.get(ftype)
    if not t:
        return {}
    keys = [k for k, _l, ty in list(t["rows"]) + list(t["header"]) if ty == "text" and k not in VOCAB_SKIP]
    cnt: dict[str, dict[str, int]] = {k: {} for k in keys}
    with s.conn() as c:
        q = ("SELECT r.data_json, d.header_json FROM rows r JOIN docs d ON d.id=r.doc_id WHERE d.type=? AND r.verified=1 "
             "AND COALESCE(r.tbl,'')='' ORDER BY r.id DESC LIMIT 5000")
        for rd, hd in c.execute(q, (ftype,)):
            try:
                x = {**json.loads(hd or "{}"), **json.loads(rd or "{}")}
            except ValueError:
                continue
            for k in keys:
                v = re.sub(r"\s+", " ", str(x.get(k) or "")).strip()
                if v and not is_ditto(v) and len(v) <= 30:
                    cnt[k][v] = cnt[k].get(v, 0) + 1
    out, n = {}, 0
    for k in keys:
        top = [v for v, m in sorted(cnt[k].items(), key=lambda z: -z[1]) if m >= 2][:per]
        if top and n < total:
            out[k] = top[:max(1, total - n)]
            n += len(out[k])
    return out


def snap(v: str, words: list[str]) -> Optional[str]:
    """Ejaan kamus site untuk bacaan yang mirip (spasi / huruf besar / salah baca 5-S 0-O 8-B 1-I), atau None."""
    import difflib
    v0 = str(v or "").strip()
    if len(v0) < 2 or is_ditto(v0) or not words:
        return None
    nv = v0.upper().translate(_OCR)
    best, score = None, 0.0
    for w in words:
        nw = w.upper().translate(_OCR)
        if nw == nv:
            return w if w != v0 else None
        r = difflib.SequenceMatcher(None, nv, nw).ratio()
        if r > score:
            best, score = w, r
    return best if best and score >= 0.84 and len(nv) >= 3 and best != v0 else None


RULES = [  # aturan umum dari borang-borang lapangan yang sudah dibaca (0.44.1)
    "Tanda | HANYA pemisah sel. Garis tegak / garis miring / tanda ulang (\" = ,, ‖) di borang ditulis 〃, jangan |.",
    "Centang (✓ √ v) ditulis v. Jam yang hanya ditulis menit (mis. .05 atau 23) salin apa adanya.",
    "Jangan ragu-ragu dan jangan menjelaskan: tulis bacaan terbaik untuk SETIAP sel; bila tidak yakin akhiri dengan ? "
    "(sel itu disorot kuning dan diperiksa geologist).",
]


def _vocab_lines(vocab: Optional[dict], t: dict) -> list[str]:
    if not vocab:
        return []
    lab = {k: lab for k, lab, _t in list(t["header"]) + list(t["rows"])}
    xs = [f"{lab.get(k, k)}: {', '.join(v)}" for k, v in vocab.items() if v]
    return ["Nilai yang biasa tertulis di proyek ini (pakai ejaan ini bila tulisan mirip): " + "; ".join(xs)] if xs else []


def ai_prompt(ftype: str, extra: str = "", mode: str = "json", vocab: Optional[dict] = None) -> str:
    """Perintah baca borang dengan jawaban RINGKAS: satu baris teks per baris tabel, nilai dipisah '|'.
    Dibanding JSON (nama field diulang di setiap baris) jumlah token jawaban kira-kira 3-4x lebih sedikit, dan pada
    komputer tanpa GPU waktu baca terutama ditentukan oleh panjang jawaban."""
    t = TYPES[ftype]
    hk = [k for k, _l, _t in t["header"]]
    rk = [k for k, _l, _t in ai_rows(t)]
    if mode == "teks":  # cadangan tanpa format Ollama: satu baris teks per baris tabel, nilai dipisah '|'
        lines = [f"Anda petugas data entry geologi tambang. Baca formulir tulisan tangan pada gambar.\n{t['hint']}\n",
                 "Jawab HANYA dengan baris-baris berikut, tanpa penjelasan:",
                 "H|" + "|".join(hk) + "   <- satu baris header",
                 "R|" + "|".join(rk) + "   <- satu baris per baris tabel yang terisi, urut dari atas"]
        for tt in (t.get("tables") or {}).values():
            lines.append(f"{tt['ai'].upper()}|" + "|".join(k for k, _l, _t in tt["rows"]) + f"   <- satu baris per baris {tt['name']}")
        lines += ["Ganti nama kolom dengan NILAI yang tertulis. Sel kosong dibiarkan kosong di antara dua '|'.",
                  "Sel yang tidak terbaca jelas: tebakan terbaik diakhiri '?'.", *RULES, *_vocab_lines(vocab, t)]
        if extra and extra.strip():
            lines.append(f"Catatan pengguna: {extra.strip()}")
        lines.append("/no_think")
        return "\n".join(lines)
    lines = [f"Anda petugas data entry geologi tambang. Baca formulir tulisan tangan pada gambar.\n{t['hint']}\n",
             "Jawab JSON ringkas, TANPA nama kolom.",
             '"h": [' + ", ".join(hk) + "]   <- nilai header sesuai urutan itu",
             '"r": ["' + "|".join(rk) + '", …]   <- SATU teks per baris tabel yang terisi, urut dari atas, nilai dipisah |']
    for tt in (t.get("tables") or {}).values():
        lines.append(f'"{tt["ai"]}": ["' + "|".join(k for k, _l, _t in tt["rows"]) + f'", …]   <- satu teks per baris {tt["name"]}, nilai dipisah |')
    lines += ['"c": catatan singkat (boleh "")',
              "Bila sebagian kolom tidak tampak di foto (terpotong), tulis - untuk kolom itu; tabel SELALU di 'r', bukan di 'c'.",
              "Isi nilai yang TERTULIS di formulir, bukan nama kolom / judul. Tiap baris TEPAT " + str(len(rk)) + " nilai; sel kosong "
              "ditulis - (JANGAN dilewati, supaya kolom tidak bergeser). SATU teks per baris tabel — jangan gabungkan beberapa baris. "
              "Jangan mengarang baris.",
              "Salin angka & kode persis. Sel yang tidak terbaca jelas: tebakan terbaik diakhiri '?' (mis. \"VLT?\").",
              *RULES[:2], RULES[2], *_vocab_lines(vocab, t)]
    if ftype not in ORE_TYPES and ftype != "rc":
        lines.append("Bila tulisan sama dengan baris di atasnya (tanda ulang), tulis nilai baris di atasnya.")
    if extra and extra.strip():
        lines.append(f"Catatan pengguna: {extra.strip()}")
    lines.append("/no_think")  # sakelar Qwen3: langsung menjawab tanpa penalaran (diabaikan model lain)
    return "\n".join(lines)


def _split_giant(rs: list, n: int, numbered: bool, starter: Optional["re.Pattern"] = None) -> list:
    """Model kadang menulis beberapa / seluruh baris tabel dalam SATU teks. Pecah lagi: di baris baru, atau (borang bernomor)
    di setiap nomor urut berikutnya (1, 2, 3 …)."""
    out: list = []
    for v in rs:
        if not isinstance(v, str) or (v.count("|") < 2 * n and not (starter is not None and len(starter.findall(v)) > 1)):
            out.append(v)
            continue
        parts = [p for p in re.split(r"\s*[\r\n]+\s*", v) if p.strip()]
        if len(parts) > 1:
            out += parts
            continue
        cells = v.split("|")
        if starter is not None:  # mis. Daily Drilling Report: tiap kegiatan diawali rentang jam
            cut = [i for i, c in enumerate(cells) if starter.search(c)]
            if len(cut) > 1:
                cut = [0] + [i for i in cut if i > 0]
                out += ["|".join(cells[a:b]) for a, b in zip(cut, cut[1:] + [len(cells)])]
                continue
        if numbered and re.fullmatch(r"\d{1,3}", cells[0].strip()):
            cut, nxt = [0], int(cells[0]) + 1
            for i in range(1, len(cells)):
                if cells[i].strip() == str(nxt) and i - cut[-1] >= max(3, n // 2):
                    cut.append(i)
                    nxt += 1
            if len(cut) > 1:
                out += ["|".join(cells[a:b]) for a, b in zip(cut, cut[1:] + [len(cells)])]
                continue
        out.append(v)
    return out


def _from_compact(ftype: str, o: dict) -> dict:
    """{h:[…], r:[[…]], <tabel>:[[…]], c} -> {header, rows, <tabel>, catatan}; sel diakhiri '?' masuk ragu;
    baris yang isinya nama / judul kolom (model menyalin kepala tabel) dibuang."""
    t = TYPES[ftype]
    names = {x.lower() for k, lbl, _t in t["rows"] + ai_rows(t) + t["header"] for x in (k, lbl)}
    names |= {x.lower() for tt in (t.get("tables") or {}).values() for k, lbl, _t in tt["rows"] for x in (k, lbl)}
    names |= {"time", "from", "to", "no", "meterage", "hole id", "azimuth", "dip"}

    def one(vals: Any, keys: list[str], tail: int = 0) -> Optional[dict]:
        miss = False
        if isinstance(vals, str):  # "nilai|nilai|…" (0.42.12)
            vals = vals.split("|")
            if not tail and len(vals) != len(keys) and len(keys) > 3 and any(v.strip() for v in vals[1:]):
                miss = True  # jumlah sel meleset: posisi kolom tidak pasti -> seluruh isian baris ditandai kuning
            if tail and len(vals) != len(keys) and vals[-1].strip():
                # jumlah sel meleset (model salah hitung '|' di kolom kosong): kolom ujung kanan (Tujuan / Keterangan ...)
                # diambil dari kanan, sisanya dari kiri; posisi kelas jadi tidak pasti -> ditandai kuning
                head = (vals[:-tail] + [""] * len(keys))[:len(keys) - tail]
                vals, miss = head + vals[-tail:], True
            elif len(vals) > len(keys):  # '|' di dalam uraian terakhir
                vals = vals[:len(keys) - 1] + ["|".join(vals[len(keys) - 1:])]
        vals = [str(v if v is not None else "").strip() for v in (vals if isinstance(vals, list) else [])]
        vals = ["" if v in ("-", "–", "—", "--") else v for v in vals]  # '-' = sel kosong (0.44.3)
        x: dict[str, Any] = {"ragu": (["kelas"] if tail else []) if miss else []}
        for k, v in zip(keys, vals):
            if v.endswith("?"):
                v = v[:-1].strip()
                x["ragu"].append(k)
            x[k] = v
        if miss and not tail:
            x["ragu"] = list(dict.fromkeys(x["ragu"] + [k for k in keys if x.get(k)]))
        filled = [v for k, v in x.items() if k != "ragu" and v]
        if not filled or sum(v.lower() in names for v in filled) >= max(1, len(filled) // 2):
            return None  # kosong / salinan kepala tabel
        if any(len(v) > 60 and v.count(" ") > 8 and re.search(r"\b(the|user|form|image|I|we|this|is|are)\b", v) for v in filled[:2]):
            return None  # kalimat penjelasan model (bahasa Inggris), bukan isian borang
        return x
    hk = [k for k, _l, _t in t["header"]]
    rk = [k for k, _l, _t in ai_rows(t)]
    # nama kolom -> kunci (untuk baris judul kolom yang ditulis model sendiri, mis. "Sample_ID|From|To|Lith")
    alias: dict[str, str] = {}
    for k, lbl, _t in list(t["rows"]) + list(ai_rows(t)):
        for x in (k, lbl, re.sub(r"\s*\(.*?\)", "", lbl)):
            alias[re.sub(r"[^a-z0-9]", "", x.lower())] = k
    alias.update({"from": "from_m", "to": "to_m", "intalt": "alt", "vein": "vein", "veintype": "vein", "qtpct": "qt", "remark2": "remark",
                  "holeid": "hole_id", "sampleid": "sample_id", "lith": "lith"})

    def colmap(v: Any) -> Optional[list[str]]:
        """Baris judul kolom -> daftar kunci (sebagian besar sel = nama kolom yang dikenal), atau None."""
        cells = v.split("|") if isinstance(v, str) else (v if isinstance(v, list) else [])
        ks = [alias.get(re.sub(r"[^a-z0-9]", "", str(c).lower()), "") for c in cells]
        return ks if len(cells) >= 3 and sum(1 for k in ks if k) >= max(3, int(0.7 * len(cells))) else None
    raw = list(o.get("r") or [])
    c_txt = str(o.get("c") or "")
    if not raw and c_txt.count("|") >= 2 * len(rk):  # model menulis tabel di 'catatan' (mis. sebagian kolom terpotong di foto)
        raw, c_txt = [ln for ln in re.split(r"\s*[\r\n]+\s*", c_txt) if "|" in ln] or [c_txt], ""
    out: dict[str, Any] = {"header": one(o.get("h"), hk) or {}, "rows": [], "catatan": c_txt}
    cur_map: Optional[list[str]] = None
    for v in _split_giant(raw, len(rk), rk[:1] == ["no"], _RANGE if ftype == "ddr" else None):
        cm = colmap(v)
        if cm:  # model menulis kepala tabelnya sendiri: baris berikutnya dipetakan menurut kepala itu
            cur_map = cm
            continue
        if cur_map and isinstance(v, str) and len(v.split("|")) == len(cur_map):
            x = one(v, [k or f"_x{i}" for i, k in enumerate(cur_map)])
            if x:
                x = {k: val for k, val in x.items() if not k.startswith("_x")}
                x["ragu"] = [k for k in x["ragu"] if not k.startswith("_x")]
        else:
            x = one(v, rk, t.get("ai_tail", 0))
        if x:
            out["rows"].append(x)
    for tt in (t.get("tables") or {}).values():
        ks = [k for k, _l, _t in tt["rows"]]
        out[tt["ai"]] = [x for x in (one(v, ks) for v in o.get(tt["ai"]) or []) if x]
    return out


def parse_ai_text(ftype: str, txt: str) -> dict:
    """Jawaban ringkas (H|..., R|..., <TABEL>|..., C|...) -> bentuk yang sama dengan jawaban JSON lama
    ({header, rows, <tabel>, catatan}, sel bertanda '?' masuk 'ragu'). Jawaban JSON tetap diterima."""
    t = TYPES[ftype]
    raw = (txt or "").strip()
    js = re.sub(r"^```\w*\s*|\s*```$", "", raw)
    if js.startswith("{"):
        o = json.loads(js)
        return _from_compact(ftype, o) if "r" in o or "h" in o else o
    m = re.search(r"\{.*\}", raw, re.S)  # JSON di tengah penjelasan
    if m and '"rows"' in m.group(0):
        try:
            return json.loads(m.group(0))
        except ValueError:
            pass
    hk = [k for k, _l, _t in t["header"]]
    rk = [k for k, _l, _t in ai_rows(t)]
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
        else:  # baris tanpa tanda (tabel markdown, penjelasan) tidak dipakai: sumber baris sampah di 0.42.7
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


def norm_crop(v: Any) -> Optional[list[float]]:
    """[x0, y0, x1, y1] pecahan 0-1 (urutan bebas) -> kotak sah, atau None (kosong / terlalu kecil = tanpa potongan)."""
    if not v:
        return None
    try:
        x0, y0, x1, y1 = (min(1.0, max(0.0, float(z))) for z in list(v)[:4])
    except (TypeError, ValueError):
        raise ValueError("Area potong harus 4 angka [x0, y0, x1, y1].")
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    if x1 - x0 < 0.05 or y1 - y0 < 0.05:
        return None
    return [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]


def crop_paper(im: Any) -> Any:
    """Potong foto ke lembar kertas (putih / abu muda, tidak berwarna): papan klip, meja dan latar tidak lagi dikirim ke AI.
    Gambar lebih kecil = AI lebih cepat (token gambar berkurang), dan pada resolusi yang sama tulisan tampak lebih besar.
    Bila kertas tidak jelas terdeteksi, gambar dikembalikan utuh."""
    try:
        import numpy as np
        t = im.copy()
        t.thumbnail((400, 400))
        hsv = np.asarray(t.convert("HSV"), dtype=np.int16)
        paper = (hsv[..., 1] < 70) & (hsv[..., 2] > 120)
        rows = np.where(paper.mean(axis=1) > 0.35)[0]
        cols = np.where(paper.mean(axis=0) > 0.35)[0]
        if len(rows) < 10 or len(cols) < 10:
            return im
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        area = (y1 - y0) * (x1 - x0) / (paper.shape[0] * paper.shape[1])
        if not 0.2 < area < 0.9:
            return im
        fx, fy = im.width / paper.shape[1], im.height / paper.shape[0]
        mx, my = 0.02 * im.width, 0.02 * im.height
        return im.crop((max(0, int(x0 * fx - mx)), max(0, int(y0 * fy - my)),
                        min(im.width, int(x1 * fx + mx)), min(im.height, int(y1 * fy + my))))
    except Exception:  # noqa: BLE001 - pemotongan hanya penghematan; gagal -> gambar utuh
        return im


def _image_b64(s: Store, d: dict, max_px: int) -> tuple[str, tuple[int, int]]:
    from PIL import Image
    with Image.open(s.scans / d["file"]) as im:
        im = im.convert("RGB")
        cr = norm_crop(d.get("crop"))
        if cr:  # potongan manual pengguna (area tabel) menggantikan pemotongan otomatis ke tepi kertas
            im = im.crop((round(cr[0] * im.width), round(cr[1] * im.height), round(cr[2] * im.width), round(cr[3] * im.height)))
        if d.get("rot"):
            im = im.rotate(-int(d["rot"]), expand=True)  # rot searah jarum jam
        if not cr:
            im = crop_paper(im)
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
    # Selalu dikirim (kecuali Ollama pernah menolaknya, lihat ai_read): daftar 'capabilities' Ollama tidak selalu
    # mencantumkan 'thinking' untuk qwen3-vl, padahal model tetap berpikir dan menghabiskan batas token -> jawaban kosong.
    return _THINK.get((host, model), True)


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


def _try_parse(ftype: str, msg: dict) -> Optional[dict]:
    """Isi borang dari jawaban Ollama (content, lalu content + thinking); None bila tidak ada baris / header terbaca."""
    for txt in (msg.get("content") or "", (msg.get("thinking") or "") + "\n" + (msg.get("content") or "")):
        try:
            res = parse_ai_text(ftype, txt)
        except ValueError:
            continue
        if res.get("rows") or any(v for k, v in (res.get("header") or {}).items() if k != "ragu") \
                or any(isinstance(v, list) and v for k, v in res.items() if k not in ("rows", "header")):
            return res
    return None


def thinking_alt(model: str) -> str:
    """qwen3-vl:2b / qwen3-vl:4b-thinking -> qwen3-vl:2b-instruct (versi tanpa penalaran)."""
    base, _, tag = model.partition(":")
    size = re.match(r"\d+b", tag or "")
    return f"{base}:{size.group(0) if size else '4b'}-instruct" if base.startswith("qwen3-vl") else "qwen3-vl:4b-instruct"


def _why_empty(j: dict) -> str:
    m = j.get("message") or {}
    c = (m.get("content") or "").strip()
    return (("jawaban kosong" if not c else f"«{c[:80]}»") + f" (selesai: {j.get('done_reason') or '?'}, "
            f"{j.get('eval_count') or 0} token" + (f", berpikir {len(m['thinking'])} karakter" if m.get("thinking") else "") + ")")


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
    if d.get("auto") == 1:  # Auto Detect: jenis belum diketahui -> tanya AI dulu (jawaban satu kata, cepat)
        try:
            ai_detect(s, did, host, model, by)
        except Exception as e:  # noqa: BLE001
            with s.lock, s.conn() as c:
                c.execute("UPDATE docs SET status='error', error=? WHERE id=?", (str(e)[:500], did))
            raise
        d = doc(s, did)
    host = (host or core_io.DEFAULT_HOST).rstrip("/")
    vocab = site_vocab(s, d["type"])
    prompt = ai_prompt(d["type"], extra, vocab=vocab)
    img, size = _image_b64(s, d, max_px)
    body = {"model": model, "messages": [{"role": "user", "content": prompt, "images": [img]}],
            "stream": False, "keep_alive": "30m", "format": ai_schema_compact(d["type"]),
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
        res = _try_parse(d["type"], msg)
        if res is None:
            # Jawaban kosong / tak terbaca dengan format JSON yang dipaksa (sebagian model + versi Ollama mengembalikan
            # content kosong bila 'format' dipakai): ulangi SEKALI tanpa format, perintah baris teks H| / R|.
            why = _why_empty(j)
            body2 = {k: v for k, v in body.items() if k != "format"}
            body2["messages"] = [dict(body["messages"][0], content=ai_prompt(d["type"], extra, "teks", vocab=vocab))]
            j = core_io._http(host + "/api/chat", body2, timeout=timeout)
            if j.get("error"):
                raise RuntimeError("Ollama: " + str(j["error"]))
            msg = j.get("message") or {}
            _save_raw(s, did, msg)
            res = _try_parse(d["type"], msg)
            if res is None:
                if any((x or "").strip() for x in (msg.get("thinking"), why if "berpikir" in why else "")) and "instruct" not in model:
                    raise ValueError(f"Model {model} adalah versi 'thinking': ia menulis penalaran panjang (sering berputar-putar) "
                                     "sampai batas token habis sebelum sempat menjawab. Pakai versi -instruct, mis. "
                                     f"{thinking_alt(model)} (Command Prompt: ollama pull {thinking_alt(model)}), lalu pilih di dialog AI. "
                                     "Detail: " + why + " · jawaban mentah: _GCEx_Core\\borang\\ai_mentah\\" + f"{did}.txt")
                raise ValueError("AI tidak memberi isian borang yang bisa dibaca. Percobaan 1 (JSON): " + why
                                 + " · percobaan 2 (teks): " + _why_empty(j)
                                 + ". Jawaban mentah: _GCEx_Core\\borang\\ai_mentah\\" + f"{did}.txt")
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
    vocab = site_vocab(s, d["type"])
    for k, words in vocab.items():
        if k in hk and k not in edited_hdr:
            w = snap(h.get(k, ""), words)
            if w:
                h[k] = w
                hunc.append(k)
    rows_in = [r for r in (res or {}).get("rows") or [] if isinstance(r, dict)]
    if d["type"] == "rc":
        rows_in = rc_fix_all(rows_in, {**d["header"], **{k: v for k, v in rh.items() if v}})
    for r in rows_in:
        if not isinstance(r, dict):
            continue
        if d["type"] == "ddr":
            r = ddr_fix(r)
        elif d["type"] == "ore":
            r = ore_fix(r, {**d["header"], **{k: v for k, v in rh.items() if v}})
        elif d["type"] == "rom":
            r = rom_fix(r, {**d["header"], **{k: v for k, v in rh.items() if v}})
        data = {k: str(r.get(k) if r.get(k) is not None else "").strip() for k in rk}
        if not any(v for k, v in data.items() if k != "no"):
            continue
        rg = [k for k in (r.get("ragu") or []) if k in rk]
        for k, words in vocab.items():  # kamus site: 5BG -> SBG, ROMS38 -> ROM 338 (kuning: cek terhadap scan)
            w = snap(data.get(k, ""), words) if k in data else None
            if w:
                data[k] = w
                rg.append(k)
        out_rows.append((data, rg))
    if d["type"] in ORE_TYPES and out_rows:
        res_f = fill_ore(d["type"], [dict(x, _u=u) for x, u in out_rows], True)
        out_rows = [({k: v for k, v in x.items() if k != "_u"}, list(dict.fromkeys(x["_u"] + f))) for x, f in res_f]
    if d["type"] == "rc" and out_rows:
        out_rows = [(x, list(dict.fromkeys(u + f))) for (x, f), (_x, u) in zip(fill_rc([x for x, _u in out_rows]), out_rows)]
    if is_gen(d["type"]) and out_rows:
        out_rows = [(x, list(dict.fromkeys(u + f))) for (x, f), (_x, u) in zip(gen_fill(d["type"], [x for x, _u in out_rows], h), out_rows)]
    if d["type"] == "ddr" and out_rows:  # baris tanpa jam = lanjutan uraian kegiatan di atasnya
        merged: list = []
        for x, u in out_rows:
            if merged and not x.get("mulai") and not x.get("selesai") and x.get("aktivitas"):
                px, pu = merged[-1]
                px["aktivitas"] = (str(px.get("aktivitas") or "") + " " + x["aktivitas"]).strip()
                merged[-1] = (px, list(dict.fromkeys(pu + [k for k in u if k == "aktivitas"])))
            else:
                merged.append((x, u))
        out_rows = merged
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
        if is_gen(d["type"]):
            rec.update(gen_rec(d, x))
            out.append(rec)
            continue
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
    if is_gen(d["type"]):
        return gen_validate(d, rs, others, hdr)
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


def uniq_key(ftype: str) -> str:
    """Kolom yang harus unik di seluruh borang jenis itu (RC: Sample ID; generik: 'unique' di spesifikasi)."""
    return "sample_id" if ftype == "rc" else ((TYPES.get(ftype) or {}).get("gen") or {}).get("unique") or ""


def other_ids(s: Store, did: int) -> list[dict]:
    me = doc(s, did)
    k = uniq_key(me["type"])
    out = []
    if not k:
        return out
    for d in docs(s):
        if d["id"] == did or d["type"] != me["type"]:
            continue
        out.append({"name": d["name"], "ids": {(r["data"].get(k) or "").strip().upper() for r in rows(s, d["id"]) if not r.get("tbl")}})
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


# ---------------------------------------------------------------- mesin jenis borang generik (0.44)
def is_gen(ftype: str) -> bool:
    return "gen" in (TYPES.get(ftype) or {})


def _g(ftype: str) -> dict:
    return TYPES[ftype].get("gen") or {}


def gen_fill(ftype: str, lst: list[dict], h: dict, carry: bool = True) -> list[tuple[dict, list[str]]]:
    """Tanda ulang (〃 " = ,,) -> nilai baris atas; kolom 'carry' (mis. Channel ID) yang kosong -> nilai baris atas / header
    (hanya hasil AI). Sel yang diisi program ditandai kuning."""
    g = _g(ftype)
    keys = [k for k, _l, _t in TYPES[ftype]["rows"]]
    out, prev = [], {}
    for d in lst:
        x, f = dict(d), []
        for k in keys:
            v = str(x.get(k) if x.get(k) is not None else "").strip()
            if is_ditto(v) and prev.get(k):
                x[k] = prev[k]
                f.append(k)
            elif carry and not v and k in (g.get("carry") or []):
                src = prev.get(k) or str(h.get(k) or "").strip()
                if src:
                    x[k] = src
                    f.append(k)
        for k in keys:
            if str(x.get(k) or "").strip():
                prev[k] = str(x[k]).strip()
        out.append((x, f))
    return out


def _norm(t: str, v: Any) -> Any:
    if t == "num":
        return parse_num(v)
    if t == "date":
        dt = parse_date(v)
        return dt.isoformat() if dt else str(v or "").strip()
    if t == "time":
        return parse_time(v) or str(v or "").strip()
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()


def gen_rec(d: dict, x: dict) -> dict:
    """Rekaman ekspor generik: header (disebar) + kolom baris (dinormalkan menurut tipe) + kolom turunan."""
    t = TYPES[d["type"]]
    g = t.get("gen") or {}
    h = d["header"]
    rec: dict[str, Any] = {}
    for k, _l, ty in t["header"]:
        rec[k] = _norm(ty, h.get(k))
    for k, _l, ty in t["rows"]:
        v = x.get(k)
        if (v is None or str(v).strip() == "") and k in rec:  # kolom sama di header (mis. Channel ID bawaan)
            continue
        rec[k] = _norm(ty, v)
    if "shift" in rec:
        rec["kode_shift"] = shift_code(rec["shift"])
    for k in ("hole_id", "channel_id"):
        if rec.get(k):
            rec[k] = norm_bhid(rec[k])
    if "qaqc" in rec:
        rec["qaqc"] = qaqc(rec["qaqc"])
    f_, t_ = rec.get("from_m"), rec.get("to_m")
    ln = round(t_ - f_, 3) if isinstance(f_, (int, float)) and isinstance(t_, (int, float)) else None
    for k, _l, _t in g.get("derived") or []:
        if k in ("panjang", "meter"):
            rec[k] = ln
        elif k == "progres_pct":
            rp = rec.get("rencana")
            rec[k] = round(100 * t_ / rp, 1) if isinstance(t_, (int, float)) and isinstance(rp, (int, float)) and rp > 0 else None
    if "status" in rec and (g.get("enums") or {}).get("status"):
        st = str(rec["status"]).strip().lower()
        rec["status"] = next((e for e in g["enums"]["status"] if e and (e.lower() == st or (st and e.lower().startswith(st[:4])))), rec["status"])
    return rec


def gen_validate(d: dict, rs: list[dict], others: Optional[list[dict]], hdr: dict) -> dict:
    t = TYPES[d["type"]]
    g = t.get("gen") or {}
    out: dict[int, dict[str, str]] = {}

    def bad(r, k, m):
        out.setdefault(r["id"], {}).setdefault(k, m)
    h = d["header"]
    for k, lab, ty in t["header"]:
        v = str(h.get(k) or "").strip()
        if not v:
            continue
        if ty == "num" and parse_num(v) is None:
            hdr[k] = f"{lab} harus angka"
        elif ty == "date" and not parse_date(v):
            hdr[k] = "tanggal tidak dikenali (mis. 30-Oct-26 atau 30/10/2026)"
        elif ty == "time" and not parse_time(v):
            hdr[k] = "jam tidak dikenali (mis. 07:30 atau 0730)"
    if "shift" in h and str(h.get("shift") or "").strip() and not shift_code(h.get("shift")):
        hdr["shift"] = "shift harus I / II (siang / malam)"
    rng, enums, req = g.get("ranges") or {}, g.get("enums") or {}, g.get("req") or []
    uk = g.get("unique") or ""
    seen: dict[str, int] = {}
    iv = g.get("interval")
    grp_prev: dict[str, Any] = {}
    grp_cur = None
    for i, r in enumerate(rs):
        if r.get("tbl"):
            continue
        x = r["data"]
        for k, lab, ty in t["rows"]:
            v = str(x.get(k) or "").strip()
            if not v:
                if k in req:
                    bad(r, k, f"{lab} kosong")
                continue
            if ty == "num":
                n = parse_num(v)
                if n is None:
                    bad(r, k, f"{lab} harus angka")
                elif k in rng and not rng[k][0] <= n <= rng[k][1]:
                    bad(r, k, f"{lab} di luar {rng[k][0]:g}-{rng[k][1]:g}")
            elif ty == "date" and not parse_date(v):
                bad(r, k, "tanggal tidak dikenali")
            elif ty == "time" and not parse_time(v):
                bad(r, k, "jam tidak dikenali (mis. 07:30 atau 0730)")
            if k in enums:
                ok = [e.lower() for e in enums[k] if e]
                vv = (qaqc(v) if k == "qaqc" else v).lower()
                if vv not in ok and not any(e.startswith(vv[:4]) for e in ok if len(vv) >= 4):
                    bad(r, k, f"{lab}: harus " + " / ".join(e for e in enums[k] if e))
        if uk:
            sid = str(x.get(uk) or "").strip().upper()
            if sid:
                if sid in seen:
                    bad(r, uk, f"kembar dengan baris {seen[sid] + 1}")
                else:
                    seen[sid] = i
                for o in others or []:
                    if sid in o["ids"]:
                        bad(r, uk, f"sudah ada di borang {o['name']}")
                        break
        f_, t_ = parse_num(x.get("from_m")), parse_num(x.get("to_m"))
        if f_ is not None and t_ is not None and t_ <= f_:
            bad(r, "to_m", "To harus lebih besar dari From")
        if d["type"] == "dpr":
            rp = parse_num(x.get("rencana"))
            if rp is not None and t_ is not None and t_ > rp + 0.01:
                bad(r, "to_m", f"melewati kedalaman rencana {rp:g} m — periksa angka / rencana")
        if iv:
            gk, fk, tk = iv
            gv = norm_bhid(x.get(gk) or h.get(gk))
            if gv != grp_cur:
                grp_cur = gv
            if qaqc(x.get("qaqc")) in ("STD", "BLANK") and f_ is None and t_ is None:
                continue
            pv = grp_prev.get(gv)
            if pv is not None and f_ is not None:
                if f_ > pv + 1e-6:
                    bad(r, fk, f"interval bolong: baris sebelumnya berakhir di {pv:g} m")
                elif f_ < pv - 1e-6:
                    bad(r, fk, f"tumpang-tindih dengan baris sebelumnya (berakhir {pv:g} m)")
            if t_ is not None:
                grp_prev[gv] = t_
    return {"header": hdr, "rows": out, "n": len(hdr) + sum(len(v) for v in out.values())}


def gen_out(ftype: str) -> list[tuple]:
    t = TYPES[ftype]
    tm = {"num": "NUM", "date": "DATE"}
    cols, seen = [], set()
    for k, lab, ty in list(t["header"]) + list(t["rows"]) + list((t.get("gen") or {}).get("derived") or []):
        if k in seen:
            continue
        seen.add(k)
        cols.append((re.sub(r"\W+", "_", k).upper(), re.sub(r"\s*\(bawaan\)", "", lab), k, tm.get(ty, "TEXT")))
        if k == "shift":
            cols.append(("KODE_SHIFT", "Kode Shift", "kode_shift", "TEXT"))
    return cols


def register_gen(ftype: str) -> None:
    """Daftarkan jenis generik ke tabel ekspor / pivot (bawaan saat impor modul, template kustom saat dimuat)."""
    g = _g(ftype)
    PARTS[ftype] = [(ftype, "")]
    OUT[ftype] = gen_out(ftype)
    DB_TABLE[ftype] = g.get("db") or ("BORANG_" + re.sub(r"\W+", "_", ftype).upper())
    SHEET[ftype] = (g.get("sheet") or ("Data_" + re.sub(r"\W+", "_", TYPES[ftype]["name"])))[:31]
    PIVOTS[ftype] = [(key, title, ftype, keys, aggs) for key, title, keys, aggs in g.get("pivots") or []]
    for _k, _t, _p, keys, aggs in PIVOTS[ftype]:
        for k in keys + [a[0] for a in aggs]:
            LAB.setdefault(k, next((lab for kk, lab, _ty in TYPES[ftype]["header"] + TYPES[ftype]["rows"] if kk == k), k.replace("_", " ").capitalize()))


for _k in GEN_BUILTIN:
    register_gen(_k)


def unregister(ftype: str) -> None:
    for dct in (PARTS, OUT, DB_TABLE, SHEET, PIVOTS, TYPES):
        dct.pop(ftype, None)


# ---------------------------------------------------------------- template kustom (0.44)
# Disimpan per proyek: _GCEx_Core/borang/template.json = {"x_kunci": {name, header, rows, hint, gen}}. Kunci kustom
# selalu berawalan 'x_' sehingga tidak bentrok dengan jenis bawaan. Jenis bawaan bisa dijadikan dasar (duplikat).
TEMPLATE_FILE = "template.json"
COL_TYPES = ("text", "num", "date", "time")
_LOADED: dict[str, set] = {}


def _tpl_path(s: Store) -> Path:
    return s.root / TEMPLATE_FILE


def load_templates(s: Store) -> dict:
    p = _tpl_path(s)
    try:
        tpl = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        tpl = {}
    for k in [k for k in TYPES if k.startswith("x_") and k not in tpl]:  # template proyek lain / yang dihapus
        unregister(k)
    for k, spec in tpl.items():
        if not k.startswith("x_"):
            continue
        try:
            TYPES[k] = _clean_spec(spec)
            register_gen(k)
        except ValueError:
            continue
    _LOADED[str(s.root)] = {k for k in tpl if k.startswith("x_")}
    return tpl


def _cols(lst: Any, what: str) -> list[tuple[str, str, str]]:
    out, seen = [], set()
    for c in lst or []:
        k, lab, ty = (list(c) + ["", "", "text"])[:3] if isinstance(c, (list, tuple)) else (c.get("key"), c.get("label"), c.get("type"))
        k = re.sub(r"[^a-z0-9_]", "_", str(k or lab or "").strip().lower()).strip("_")[:40]
        if not k:
            continue
        if k in seen:
            raise ValueError(f"Kunci {what} '{k}' dipakai dua kali.")
        seen.add(k)
        out.append((k, str(lab or k).strip()[:80], ty if ty in COL_TYPES else "text"))
    return out


def _clean_spec(spec: dict) -> dict:
    name = str(spec.get("name") or "").strip()
    if not name:
        raise ValueError("Nama template kosong.")
    rows_ = _cols(spec.get("rows"), "kolom")
    if not rows_:
        raise ValueError("Template perlu minimal satu kolom tabel.")
    hdr = _cols(spec.get("header"), "header")
    g = dict(spec.get("gen") or {})
    keys = {k for k, _l, _t in rows_}
    gen = {"db": re.sub(r"\W+", "_", str(g.get("db") or "").upper())[:60] or None, "sheet": str(g.get("sheet") or "")[:31] or None,
           "unique": g.get("unique") if g.get("unique") in keys else "", "req": [k for k in g.get("req") or [] if k in keys],
           "carry": [k for k in g.get("carry") or [] if k in keys]}
    if {"from_m", "to_m"} <= keys:
        grp = next((k for k in ("hole_id", "channel_id", "trench_id") if k in keys), "")
        gen["interval"] = (grp, "from_m", "to_m") if grp else None
        gen["derived"] = [("panjang", "Panjang (m)", "num")]
    return {"name": name[:80], "header": hdr, "rows": rows_, "hint": str(spec.get("hint") or "").strip()[:2000]
            or f"Borang '{name}'. Baca header dan tabel apa adanya.", "gen": gen, "custom": True}


def templates(s: Store) -> list[dict]:
    load_templates(s)
    used: dict[str, int] = {}
    for d in docs(s):
        used[d["type"]] = used.get(d["type"], 0) + 1
    out = []
    for k, t in TYPES.items():
        out.append({"key": k, "name": t["name"], "builtin": k in BUILTIN_KEYS, "header": t["header"], "rows": t["rows"],
                    "hint": t.get("hint", ""), "gen": {kk: vv for kk, vv in (t.get("gen") or {}).items() if kk in ("db", "sheet", "unique", "req", "carry")},
                    "tables": list((t.get("tables") or {}).keys()), "docs": used.get(k, 0)})
    return out


def save_template(s: Store, key: str, spec: dict, by: str) -> str:
    tpl = load_templates(s)
    clean = _clean_spec(spec)
    if not key:
        base = "x_" + (re.sub(r"[^a-z0-9]+", "_", clean["name"].lower()).strip("_")[:30] or "borang")
        key, i = base, 2
        while key in TYPES:
            key, i = f"{base}_{i}", i + 1
    if not key.startswith("x_"):
        raise ValueError("Jenis borang bawaan tidak bisa diubah; buat duplikatnya sebagai template kustom.")
    if key in TYPES and key in tpl:  # kolom yang sudah berisi data tidak boleh hilang diam-diam
        old = {k for k, _l, _t in TYPES[key]["rows"]}
        gone = old - {k for k, _l, _t in clean["rows"]}
        if gone:
            n = sum(1 for d in docs(s) if d["type"] == key for r in rows(s, d["id"]) if any(str(r["data"].get(k) or "").strip() for k in gone))
            if n:
                raise ValueError(f"Kolom {', '.join(sorted(gone))} masih berisi data di {n} baris borang; kosongkan dulu atau ganti labelnya saja.")
    tpl[key] = {"name": clean["name"], "header": [list(c) for c in clean["header"]], "rows": [list(c) for c in clean["rows"]],
                "hint": clean["hint"], "gen": {k: v for k, v in clean["gen"].items() if k in ("db", "sheet", "unique", "req", "carry")}}
    _tpl_path(s).write_text(json.dumps(tpl, ensure_ascii=False, indent=1), encoding="utf-8")
    load_templates(s)
    with s.lock, s.conn() as c:
        _hist(c, None, "template", None, f"{key}: {clean['name']}", "template", by)
    return key


def delete_template(s: Store, key: str, by: str) -> None:
    tpl = load_templates(s)
    if key not in tpl:
        raise ValueError("Hanya template kustom yang bisa dihapus.")
    n = sum(1 for d in docs(s) if d["type"] == key)
    if n:
        raise ValueError(f"Template dipakai {n} borang; hapus / ganti jenis borang itu dulu.")
    tpl.pop(key)
    _tpl_path(s).write_text(json.dumps(tpl, ensure_ascii=False, indent=1), encoding="utf-8")
    load_templates(s)
    with s.lock, s.conn() as c:
        _hist(c, None, "hapus template", key, None, "template", by)


# ---------------------------------------------------------------- deteksi jenis otomatis (0.44)
NAME_RULES = [("dpr", r"progress|\bdpr\b|kemajuan"), ("ddr", r"\bddr|daily.?drill|drilling.?report|laporan.?harian"),
              ("chn", r"channel|\bchn\b|alur"), ("map", r"mapping|pemetaan|\bmap\b|geol.?map"),
              ("rc", r"\brc\b|rc.?log|chip.?tray|chiptray|logging"), ("rom", r"\brom\b|crusher|stockpile|rehand"),
              ("ore", r"loading|spotter|\bpit\b|\bore\b")]


def guess_type(name: str) -> str:
    """Jenis borang dari nama file (kata kunci); '' bila tidak ada yang cocok."""
    n = re.sub(r"[_\-.]+", " ", Path(name).stem.lower())
    for k, rx in NAME_RULES:
        if k in TYPES and re.search(rx, n):
            return k
    for k, t in TYPES.items():  # template kustom: nama template ada di nama file
        if k.startswith("x_") and t["name"].lower() in n:
            return k
    return ""


# Ciri tercetak tiap jenis bawaan (judul & kolom pembeda) — dari borang lapangan yang sudah dibaca. Judul paling menentukan.
TITLE_CUES = {
    "ore": (r"loading\s*ore|form\s*loading|pit\s*to\s*rom", "judul 'FORM LOADING ORE DARI PIT TO ROM / STOCKPILE'; kolom Start / Finish "
            "Loading, PIT, Elevation, kelompok kelas OX-LG… masing-masing TRUCK & Tonnage, Tujuan Dumping"),
    "rom": (r"stockpile\s*/?\s*crusher|rom\s*to\s*(crusher|rom)|ore\s*to\s*stockpile", "judul 'FORM ORE TO STOCKPILE / CRUSHER' atau "
            "'Form Untuk Rom to Crusher'; kolom Eq. No. Unit, Asal Material, Rehandling Tumpukan, kolom kelas, Status Material Baru / Lama"),
    "ddr": (r"daily\s*drill", "judul 'DAILY DRILLING REPORT'; kolom TIME, METERAGE From / To, Hole ID, Azimuth, Dip, DRILLING DETAILS "
            "(jam + uraian kegiatan); bagian bawah BITS / REAMER, HM ENGINE"),
    "rc": (r"rc\s*drill|logging\s*form|chip\s*tray", "judul 'RC Drill Logging Form'; kolom No, Hole_ID, Tanggal, Sample_ID tercetak, From, "
           "To, Lith, Int_Alt, Min1, Vein_Type, Qt_pct"),
    "map": (r"mapping|pemetaan", "judul 'GEOLOGICAL MAPPING' / pemetaan; kolom stasiun, Easting, Northing, litologi, strike, dip"),
    "chn": (r"channel", "judul 'CHANNEL SAMPLING'; kolom Channel ID, Sample ID, From, To, berat"),
    "dpr": (r"progress", "judul 'DRILL PROGRESS REPORT' (BUKAN Daily Drilling Report); kolom kedalaman rencana, status lubang; "
            "TIDAK ada uraian kegiatan per jam"),
}


def _cue(k: str) -> tuple[str, str]:
    t = TYPES[k]
    return TITLE_CUES.get(k) or (re.escape(t["name"].lower()).replace("\\ ", r"\s*"), f"judul '{t['name']}'; {t.get('hint', '')[:150]}")


def type_from_title(title: str) -> str:
    """Jenis dari judul tercetak yang disalin AI ('' bila tidak cocok / cocok ke lebih dari satu jenis)."""
    tl = re.sub(r"\s+", " ", str(title or "").lower())
    hit = [k for k in TYPES if tl and re.search(_cue(k)[0], tl)]
    if "ddr" in hit and "dpr" in hit:
        hit.remove("dpr")
    return hit[0] if len(hit) == 1 else ""


def detect_prompt() -> str:
    lines = ["Gambar ini foto satu formulir lapangan tambang. Salin JUDUL formulir yang tercetak paling besar di bagian atas ke 'judul', "
             "lalu pilih jenisnya di 'jenis'. Judul tercetak paling menentukan.", "Pilihan:"]
    for k, t in TYPES.items():
        lines.append(f"- {t['name']}: {_cue(k)[1]}")
    lines += ['Jawab JSON {"judul": "...", "jenis": "<nama jenis>"} saja.', "/no_think"]
    return "\n".join(lines)


def ai_detect(s: Store, did: int, host: str, model: str, by: str = "", timeout: float = 300) -> str:
    """Tanya model jenis borang (gambar kecil 896 px, jawaban satu kata) lalu ganti jenis borang (hanya bila belum ada baris)."""
    d = doc(s, did)
    host = (host or core_io.DEFAULT_HOST).rstrip("/")
    img, size = _image_b64(s, d, 896)
    prompt = detect_prompt()
    body = {"model": model, "messages": [{"role": "user", "content": prompt, "images": [img]}], "stream": False, "keep_alive": "30m",
            "format": {"type": "object", "required": ["judul", "jenis"], "properties": {
                "judul": {"type": "string", "maxLength": 120}, "jenis": {"type": "string", "enum": [t["name"] for t in TYPES.values()]}}},
            "options": {"temperature": 0, "num_ctx": ctx_for(size, prompt), "num_predict": 90}}
    if _can_think(host, model):
        body["think"] = False
    try:
        j = core_io._http(host + "/api/chat", body, timeout=timeout)
    except urllib.error.HTTPError as e:
        if "think" not in body or e.code != 400:
            raise
        body.pop("think")
        _THINK[(host, model)] = False
        j = core_io._http(host + "/api/chat", body, timeout=timeout)
    txt = ((j.get("message") or {}).get("content") or "").strip()
    try:
        o = json.loads(txt[txt.find("{"):txt.rfind("}") + 1]) if "{" in txt else {}
    except ValueError:
        o = {}
    by_name = {t["name"].lower(): k for k, t in TYPES.items()}
    # judul tercetak yang disalin AI lebih bisa dipercaya daripada pilihan jenisnya (2b sering tertukar DDR <-> Progress)
    k = type_from_title(o.get("judul", "")) or by_name.get(str(o.get("jenis") or o.get("type") or "").strip().lower(), "")
    if not k:
        m = re.search(r"\b(" + "|".join(map(re.escape, TYPES)) + r")\b", txt)
        k = m.group(1) if m else ""
    if not k:
        raise ValueError("AI tidak bisa menentukan jenis borang; pilih jenisnya manual (klik kanan → Ubah jenis).")
    with s.lock, s.conn() as c:
        if k != d["type"]:
            if c.execute("SELECT COUNT(*) FROM rows WHERE doc_id=?", (did,)).fetchone()[0]:
                raise ValueError("Borang sudah berisi baris; jenis tidak diganti otomatis.")
            c.execute("UPDATE docs SET type=? WHERE id=?", (k, did))
            _hist(c, did, "jenis (Auto Detect AI)", d["type"], k, "ai", by)
        c.execute("UPDATE docs SET auto=0 WHERE id=?", (did,))
    return k


# ---------------------------------------------------------------- riwayat semua borang (0.44)
def history_all(s: Store, q: str = "", ftype: str = "", limit: int = 2000) -> list[dict]:
    """Riwayat seluruh proyek (terbaru dulu), dengan nama & jenis borang (borang terhapus: nama dari catatan hapus)."""
    names: dict[int, tuple[str, str]] = {d["id"]: (d["name"], d["type"]) for d in docs(s)}
    with s.conn() as c:
        rs = [dict(r) for r in c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (max(1, min(20000, limit * 3)),))]
    for r in rs:
        if r["what"] == "hapus" and r["doc_id"] not in names and r["doc_id"] is not None:
            names[r["doc_id"]] = (str(r["old"] or ""), "")
    out = []
    ql = q.strip().lower()
    for r in rs:
        nm, ty = names.get(r["doc_id"], ("", "")) if r["doc_id"] is not None else ("(proyek)", "")
        r["doc_name"], r["doc_type"] = nm, ty
        r["type_name"] = (TYPES.get(ty) or {}).get("name", "")
        if ftype and ty != ftype:
            continue
        if ql and ql not in " ".join(str(r.get(k) or "") for k in ("what", "old", "new", "by", "doc_name", "src")).lower():
            continue
        out.append(r)
        if len(out) >= limit:
            break
    return out


def collect(s: Store, ids: list[int], ftype: str, unverified: bool = False) -> dict:
    """Baris untuk diekspor dari borang terpilih (kosong = semua borang jenis itu). Bawaan: hanya baris terverifikasi."""
    if ftype not in TYPES:
        raise ValueError("Jenis borang tidak dikenal.")
    sel = [d for d in docs(s) if d["type"] == ftype and (not ids or d["id"] in ids)]
    recs, skip, issues = [], 0, 0
    for d in sel:
        rs = rows(s, d["id"])
        v = validate(d, rs, other_ids(s, d["id"]) if uniq_key(ftype) else None)
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
    v = validate(d, rs, other_ids(s, did) if uniq_key(d["type"]) else None)
    recs = records(d, rs)
    return {"doc": d, "rows": rs, "valid": v, "recs": recs, "pivot": pivots(recs, d["type"]),
            "summary": ddr_summary(d, rs) if d["type"] == "ddr" else None}


@router.post("/open")
def api_open(b: FBody) -> dict:
    s = store(b.folder)
    load_templates(s)
    return {"ok": True, "docs": docs(s), "types": {k: {"name": t["name"], "header": t["header"], "rows": t["rows"], "builtin": k in BUILTIN_KEYS,
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


class HistBody(FBody):
    q: str = ""
    type: str = ""
    limit: int = 2000


class TplBody(FBody):
    key: str = ""
    spec: dict[str, Any] = {}


class DetBody(FBody):
    id: int
    host: str = ""
    model: str


class VocabBody(FBody):
    type: str


@router.post("/vocab")
def api_vocab(b: VocabBody) -> dict:
    return {"ok": True, "vocab": site_vocab(store(b.folder), b.type)}


@router.post("/history_all")
def api_history_all(b: HistBody) -> dict:
    return {"ok": True, "history": history_all(store(b.folder), b.q, b.type, b.limit)}


@router.post("/templates")
def api_templates(b: FBody) -> dict:
    return {"ok": True, "templates": templates(store(b.folder)), "col_types": list(COL_TYPES)}


@router.post("/template/save")
def api_template_save(b: TplBody) -> dict:
    s = store(b.folder)
    k = save_template(s, b.key, b.spec, b.by)
    return {"ok": True, "key": k, "templates": templates(s)}


@router.post("/template/delete")
def api_template_delete(b: TplBody) -> dict:
    s = store(b.folder)
    delete_template(s, b.key, b.by)
    return {"ok": True, "templates": templates(s)}


@router.post("/detect")
def api_detect(b: DetBody) -> dict:
    s = store(b.folder)
    ai_detect(s, b.id, b.host, b.model, b.by)
    return {"ok": True, **_full(s, b.id)}


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
