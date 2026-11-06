# -*- coding: utf-8 -*-
"""Ekspor string (poligon galian) ke DXF dan Surpac .str -- padanan `dgExport` di aplikasi HTML.

Dua hal yang gampang salah dan sengaja ditulis di sini, bukan di komentar singkat:

1. .str Surpac memakai urutan **Y, X, Z** (northing dulu, baru easting). Menukarnya akan
   menghasilkan berkas yang tetap terbaca Surpac tetapi poligonnya tercermin -- kesalahan yang
   baru ketahuan setelah ada yang menggali di tempat yang salah.
2. Di aplikasi HTML ada DUA ruang koordinat sekaligus: `BX.m.x/y` (block model) memakai koordinat
   PENUH, sedangkan `DG.S[].pts` (hasil digitasi) tersimpan RELATIF terhadap `offX`/`offY`.
   Karena itu `lyItems()` menambahkan offset dulu sebelum memanggil `lyTon()`, dan `dgExport()`
   menambahkannya lagi saat menulis berkas. Tertukar satu kali saja, berkasnya tetap terbaca
   Surpac dan tidak memunculkan galat apa pun -- poligonnya saja yang berada beberapa ratus
   kilometer dari tempatnya.

   Penampil Qt sengaja TIDAK menyalin pembagian itu: `String.pts` di sini selalu koordinat PENUH,
   ruang yang sama dengan `BlockModel.x/y`, jadi `off_x`/`off_y` biasanya 0. Penggeseran ke asal
   lokal untuk kebutuhan gambar sudah ditangani `qtbm/adegan.py` dan tidak pernah menyentuh data.
   Argumen `off_x`/`off_y` tetap ada hanya supaya berkas dari kedua aplikasi bisa dibandingkan
   baris per baris pada uji paritas.

Akhiran baris CRLF dan tiga desimal mengikuti berkas yang dihasilkan aplikasi HTML, supaya
berkas dari kedua aplikasi bisa dibandingkan baris per baris.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

BULAN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass
class String:
    """Satu string hasil digitasi. `pts` = [(x, y, z), ...] dalam koordinat internal."""

    no: int = 1
    ket: str = ""                        # keterangan / material -- `s.d` di aplikasi
    tertutup: bool = True                # poligon tertutup (dig block) atau polyline terbuka
    pts: List[Tuple[float, float, float]] = field(default_factory=list)
    warna: str = "#e8590c"
    tampil: bool = True

    def xy(self) -> List[Tuple[float, float]]:
        return [(p[0], p[1]) for p in self.pts]

    def panjang(self) -> float:
        L = 0.0
        for a, b in zip(self.pts, self.pts[1:]):
            L += ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2) ** 0.5
        return L


def _f3(v: float) -> str:
    return "%.3f" % float(v)


def _aman(s: str, ganti: str = "_") -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", ganti, str(s))


def teks_str(daftar: Sequence[String], zona: str = "GCEX",
             off_x: float = 0.0, off_y: float = 0.0,
             tanggal: Optional[_dt.date] = None) -> str:
    """Isi berkas Surpac .str. Perhatikan urutan Y, X, Z (lihat catatan modul)."""
    d = tanggal or _dt.date.today()
    dasar = "String_" + _aman(zona)
    r: List[str] = []
    r.append("%s,%02d-%s-%s,,SSI_STYLES:styles.ssi"
             % (dasar, d.day, BULAN[d.month - 1], str(d.year)[-2:]))
    r.append("0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000")
    for s in daftar:
        pts = list(s.pts)
        if s.tertutup and pts:
            pts.append(pts[0])          # titik pertama diulang supaya poligon benar-benar tertutup
        for q in pts:
            baris = "%d, %s, %s, %s" % (s.no, _f3(q[1] + off_y), _f3(q[0] + off_x), _f3(q[2]))
            if s.ket:
                baris += ", " + s.ket.replace(",", " ")
            r.append(baris)
        r.append("0, 0.000, 0.000, 0.000,")
    r.append("0, 0.000, 0.000, 0.000, END")
    return "\r\n".join(r) + "\r\n"


def teks_dxf(daftar: Sequence[String], off_x: float = 0.0, off_y: float = 0.0) -> str:
    """Isi berkas DXF (AC1009, POLYLINE per string) -- sama dengan `dgExport('dxf')`."""
    r: List[str] = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009",
                    "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    for s in daftar:
        ly = _aman((s.ket or "STRING") + "_" + str(s.no))
        r += ["0", "POLYLINE", "8", ly, "66", "1", "70", "9" if s.tertutup else "8",
              "10", "0.0", "20", "0.0", "30", "0.0"]
        for q in s.pts:
            r += ["0", "VERTEX", "8", ly, "10", _f3(q[0] + off_x), "20", _f3(q[1] + off_y),
                  "30", _f3(q[2]), "70", "32"]
        r += ["0", "SEQEND", "8", ly]
    r += ["0", "ENDSEC", "0", "EOF"]
    return "\r\n".join(r) + "\r\n"


def tulis(jalur, daftar: Sequence[String], zona: str = "GCEX",
          off_x: float = 0.0, off_y: float = 0.0) -> str:
    """Tulis ke berkas; format ditentukan akhiran nama berkas (.str / .dxf)."""
    from pathlib import Path
    p = Path(jalur)
    akhiran = p.suffix.lower()
    if akhiran == ".str":
        teks = teks_str(daftar, zona, off_x, off_y)
    elif akhiran == ".dxf":
        teks = teks_dxf(daftar, off_x, off_y)
    else:
        raise ValueError("format tidak dikenal: %s (pakai .str atau .dxf)" % akhiran)
    # newline='' supaya CRLF tidak berubah jadi CRCRLF di Windows
    p.write_text(teks, encoding="utf-8", newline="")
    return teks
