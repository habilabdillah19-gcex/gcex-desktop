# -*- coding: utf-8 -*-
"""Menyimpan & memuat string dig block di folder proyek GC-Ex.

KEPUTUSAN RANCANGAN YANG DISENGAJA: penampil Qt **tidak menulis** ke `gcex_project.json`.

Berkas itu dijaga oleh protokol yang cukup rumit di aplikasi HTML: berkas kunci (`gcex.lock`)
yang menyatakan siapa sedang membuka proyek, nomor revisi `rev` untuk mendeteksi konflik antar
pemakai, cadangan otomatis ke `backup/` dan `backup/harian/`, serta hash isi. Kalau penampil Qt
— yang masih berstatus percobaan — menulis ke situ dan satu bagian protokol itu terlewat, yang
rusak adalah berkas proyek yang sedang dipakai orang lain. Harga kesalahan itu jauh lebih besar
daripada manfaat menulis langsung.

Karena itu:
  - BACA  `gcex_project.json` -> `body.work.dg` : mengambil string yang dibuat aplikasi HTML
                                                  (hanya baca, berkasnya tidak pernah disentuh);
  - TULIS `gcex_dig_qt.json`                    : berkas milik penampil Qt sendiri, di folder
                                                  proyek yang sama.

Akibatnya yang harus dikatakan terus-terang kepada pemakai: string yang dibuat di Qt **belum**
otomatis muncul di aplikasi HTML. Untuk itu aplikasi HTML perlu diajari membaca berkas pendamping
ini, dan itu perubahan pada aplikasi produksi yang menunggu keputusan pemilik.

RUANG KOORDINAT: `SIO.String.pts` di Qt selalu koordinat PENUH, sedangkan `DG.S[].pts` di
aplikasi HTML relatif terhadap `offX`/`offY` (lihat `Proyek.offset()`). Penambahan dan pengurangan
offset itu HANYA terjadi di modul ini, supaya tidak tersebar ke mana-mana.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .string_io import String

BERKAS_QT = "gcex_dig_qt.json"
BERKAS_PROYEK = "gcex_project.json"
FORMAT_QT = "gcex-dig-qt"
VERSI_QT = 1

# warna bawaan string, sama dengan DG.pal di aplikasi HTML
PALET = ["#e8590c", "#2f9e44", "#1971c2", "#c2255c", "#7048e8", "#0c8599", "#f08c00", "#5c940d"]

U32 = 0xFFFFFFFF


def hash_fp(s: str) -> str:
    """Salinan `FP.hash` di aplikasi HTML (dua jalur bergaya FNV + panjang dalam basis 36).

    Ditiru persis -- termasuk bahwa JavaScript bekerja pada satuan kode UTF-16 (`charCodeAt`,
    `s.length`), bukan titik kode Unicode. Satu aksara di luar BMP (mis. emoji di keterangan
    string) menjadi DUA satuan kode di JavaScript; Python harus menghitungnya sama, kalau tidak
    hash-nya berbeda dan berkasnya dianggap rusak oleh pihak lain yang membacanya.
    """
    unit = s.encode("utf-16-le")
    n = len(unit) // 2
    h1 = 0x811C9DC5
    h2 = 0x01000193 ^ n
    for i in range(0, len(unit), 2):
        c = unit[i] | (unit[i + 1] << 8)
        h1 = ((h1 ^ c) * 16777619) & U32
        h2 = ((h2 ^ c) * 2246822507) & U32
    return "%x-%x-%s" % (h1, h2, _basis36(n))


def _basis36(n: int) -> str:
    if n == 0:
        return "0"
    d = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while n:
        out = d[n % 36] + out
        n //= 36
    return out


def pack(meta: Dict[str, Any], body_json: str) -> Tuple[str, str]:
    """Salinan `FP.pack`: meta (dengan hash isi) + `,"body":` + isi. Kembalikan (teks, hash)."""
    m = dict(meta)
    m["hash"] = hash_fp(body_json)
    teks_meta = json.dumps(m, ensure_ascii=False, separators=(",", ":"))
    return (teks_meta[:-1] + ',"body":' + body_json + "}", m["hash"])


def unpack(teks: str) -> Tuple[Dict[str, Any], Any]:
    """Salinan `FP.unpack`: pisahkan meta dan isi, lalu periksa hash-nya."""
    i = teks.find(',"body":') if teks else -1
    if i < 0:
        raise ValueError("format berkas tidak dikenali (tidak ada bagian body)")
    meta = json.loads(teks[:i] + "}")
    body = teks[i + 8:len(teks) - 1].rstrip()
    if meta.get("hash") and hash_fp(body) != meta["hash"]:
        raise ValueError("hash isi tidak cocok: berkas kemungkinan rusak atau terpotong")
    return meta, json.loads(body)


# ---------------------------------------------------------------- konversi

def dari_html(d: Dict[str, Any], off_x: float, off_y: float, warna_ke: int = 0) -> String:
    """Satu string gaya `DG.S[]` (relatif offset) -> `String` Qt (koordinat penuh)."""
    pts = []
    for p in d.get("pts") or []:
        if p is None or len(p) < 3:
            continue
        pts.append((float(p[0]) + off_x, float(p[1]) + off_y, float(p[2])))
    return String(no=int(d.get("no") or 1), ket=str(d.get("d") or ""),
                  tertutup=bool(d.get("closed")), pts=pts,
                  warna=str(d.get("col") or PALET[warna_ke % len(PALET)]),
                  tampil=d.get("vis") is not False)


def ke_html(s: String, off_x: float, off_y: float) -> Dict[str, Any]:
    """`String` Qt (koordinat penuh) -> satu string gaya `DG.S[]` (relatif offset)."""
    return {"no": int(s.no), "d": s.ket, "closed": bool(s.tertutup),
            "pts": [[p[0] - off_x, p[1] - off_y, p[2]] for p in s.pts],
            "col": s.warna, "vis": bool(s.tampil)}


# ---------------------------------------------------------------- baca aplikasi HTML

def baca_string_html(folder, off_x: float, off_y: float) -> List[String]:
    """String dig block yang dibuat aplikasi HTML, dari `gcex_project.json` (HANYA BACA).

    Berkasnya tidak pernah ditulis maupun dikunci di sini. Bila tidak ada, kosong, atau rusak,
    kembalikan daftar kosong -- tidak melempar, sebab gagal membaca string orang lain tidak boleh
    menghalangi pemakai memakai penampilnya.
    """
    p = Path(folder) / BERKAS_PROYEK
    if not p.is_file():
        return []
    try:
        _meta, body = unpack(p.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return []
    dg = (((body or {}).get("work") or {}).get("dg")) or []
    out: List[String] = []
    for k, d in enumerate(dg):
        if not isinstance(d, dict):
            continue
        try:
            s = dari_html(d, off_x, off_y, k)
        except Exception:                           # noqa: BLE001
            continue
        if len(s.pts) >= 2:
            out.append(s)
    return out


# ---------------------------------------------------------------- berkas Qt

def jalur(folder) -> Path:
    return Path(folder) / BERKAS_QT


def tulis(folder, strings: Sequence[String], off_x: float, off_y: float,
          nama_proyek: str = "", oleh: str = "penampil Qt") -> Path:
    """Tulis string Qt ke `gcex_dig_qt.json`. Menulis ke berkas sementara dulu, lalu ganti nama.

    Penulisan dua tahap itu bukan kehati-hatian berlebihan: kalau aplikasi mati di tengah
    penulisan langsung, yang tertinggal adalah berkas separuh jadi -- dan string yang HILANG
    justru pekerjaan yang hendak diselamatkan berkas ini.
    """
    import datetime as _dt

    p = jalur(folder)
    body = json.dumps({"dg": [ke_html(s, off_x, off_y) for s in strings],
                       "offX": off_x, "offY": off_y},
                      ensure_ascii=False, separators=(",", ":"))
    meta = {"format": FORMAT_QT, "version": VERSI_QT, "name": nama_proyek,
            "savedAt": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "savedBy": oleh, "n": len(strings)}
    teks, _h = pack(meta, body)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(teks, encoding="utf-8")
    tmp.replace(p)
    return p


def baca(folder) -> Tuple[List[String], Dict[str, Any]]:
    """Baca `gcex_dig_qt.json`. Kembalikan (daftar string, meta); kosong bila belum ada.

    Offset yang TERSIMPAN di berkas yang dipakai, bukan yang dihitung ulang: kalau data bor
    proyek berubah sehingga offset ikut berubah, string lama tetap kembali ke tempat yang benar.
    """
    p = jalur(folder)
    if not p.is_file():
        return [], {}
    meta, body = unpack(p.read_text(encoding="utf-8"))
    off_x = float((body or {}).get("offX") or 0.0)
    off_y = float((body or {}).get("offY") or 0.0)
    out: List[String] = []
    for k, d in enumerate((body or {}).get("dg") or []):
        if isinstance(d, dict):
            s = dari_html(d, off_x, off_y, k)
            if len(s.pts) >= 2:
                out.append(s)
    return out, meta
