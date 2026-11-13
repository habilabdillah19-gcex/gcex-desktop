# -*- coding: utf-8 -*-
"""Pastikan cap versi DI DALAM berkas aplikasi sama dengan versi yang dinyatakan.

MENGAPA PERIKSAAN INI ADA. Nomor versi tiap aplikasi dinyatakan di `package.json` /
`builder-dh.json` / `builder-core.json`, tetapi yang dibaca aplikasi saat berjalan adalah
`window.GCEX_VER` yang tertanam di berkas HTML hasil `web-src/build.py`. CI **tidak** menjalankan
build itu -- berkas `app*/index.html` yang ada di repo itulah yang dikemas. Jadi menaikkan versi
tanpa membangun ulang berkas HTML-nya membuat aplikasi melaporkan versi LAMA, tanpa ada apa pun
yang menolak.

Itu bukan dugaan: pada commit d717474 Block Model dinaikkan ke 0.24.25 dan Drill Hole ke 0.24.35
tanpa membangun ulang, sehingga aplikasi yang beredar mencap dirinya 0.24.24 dan 0.24.34 selama
beberapa rilis. Tidak ada fitur yang rusak karena nomor itu hanya dipakai untuk tampilan dan
untuk kolom `versi` di tabel `sinkron` basis data proyek -- tetapi tabel itulah jejak resmi siapa
mengerjakan apa dengan versi apa, dan baris riwayat tidak pernah diperbaiki lagi. Pekerjaan grade
control yang jejaknya salah adalah pekerjaan yang sukar dipertanggungjawabkan.

Pemakaian:
    python tools/rilis/cek_cap_versi.py          # keluar 1 bila ada yang tidak cocok
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# (nama aplikasi, berkas HTML yang dikemas, cara mengambil versi yang dinyatakan)
APLIKASI = [
    ("GC-Ex Block Model", "app/index.html", ("package.json", ("version",))),
    ("GC-Ex Drillhole", "app-dh/index.html", ("builder-dh.json", ("extraMetadata", "version"))),
    ("DB-Ex", "app-core/index.html", ("builder-core.json", ("extraMetadata", "version"))),
    ("Ore Works", "app-ow/index.html", ("builder-ow.json", ("extraMetadata", "version"))),
]

POLA = re.compile(r"GCEX_VER\s*=\s*'([^']*)'")


def versi_dinyatakan(berkas: str, jalan) -> str:
    p = ROOT / berkas
    if not p.is_file():
        return ""
    d = json.loads(p.read_text(encoding="utf-8"))
    for k in jalan:
        if not isinstance(d, dict):
            return ""
        d = d.get(k)
        if d is None:
            return ""
    return str(d)


def cap_di_html(berkas: str) -> str:
    p = ROOT / berkas
    if not p.is_file():
        return ""
    m = POLA.search(p.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else ""


def main() -> int:
    salah = []
    diperiksa = 0
    for nama, html, (jb, jalan) in APLIKASI:
        p = ROOT / html
        if not p.is_file():
            continue
        cap = cap_di_html(html)
        if not cap:
            # Tidak semua aplikasi menanamkan cap; yang tidak punya tidak bisa diperiksa dan
            # itu dikatakan, bukan didiamkan seolah sudah lulus.
            print("  - %-22s %s: tidak ada GCEX_VER untuk diperiksa" % (nama, html))
            continue
        nyata = versi_dinyatakan(jb, jalan)
        if not nyata and jb == "builder-core.json":
            nyata = versi_dinyatakan("package.json", ("version",))   # DB-Ex ikut package.json
        diperiksa += 1
        tanda = "OK " if cap == nyata else "!! "
        print("  %s%-22s cap %-10s vs %s %s" % (tanda, nama, cap, jb, nyata or "(tidak ada)"))
        if nyata and cap != nyata:
            salah.append("%s: %s mencap dirinya %s, padahal %s menyatakan %s. "
                         "Jalankan pembangun web-src-nya lalu commit berkas HTML itu."
                         % (nama, html, cap, jb, nyata))
    if salah:
        print("\nCAP VERSI TIDAK COCOK (%d):" % len(salah))
        for s in salah:
            print("  ! %s" % s)
        print("\nAplikasi akan melaporkan versi yang salah, dan kolom `versi` di tabel `sinkron` "
              "basis data proyek akan mencatat jejak yang salah -- selamanya, karena baris "
              "riwayat tidak diperbaiki lagi.")
        return 1
    print("\ncap versi cocok di %d aplikasi." % diperiksa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
