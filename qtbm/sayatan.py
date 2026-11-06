# -*- coding: utf-8 -*-
"""Sayatan (slicing): bidang potong dan slab blok -- padanan `secGeom` / `sd` / `secK` / `inK`.

Lima mode, sama dengan aplikasi HTML:

  H  datar       bidang mendatar; `pos` = RL
  X  sumbu X     bidang tegak menghadap timur; `pos` = easting
  Y  sumbu Y     bidang tegak menghadap utara; `pos` = northing
  A  azimut      bidang miring: azimut + dip, berpusat di satu titik; `pos` = jarak dari pusat
  P  dua titik   bidang dari titik 1 ke titik 2 + dip; `pos` = jarak dari titik 1

SATU JEBAKAN OFFSET YANG PERLU DICATAT. Di aplikasi HTML, koordinat blok memakai ruang INTERNAL
(sudah dikurangi `offX`/`offY`), dan supaya `pos` pada mode X / Y tetap berupa easting / northing
PENUH, pusat bidangnya ditaruh di `c = [-offX, 0, 0]` dan `[0, -offY, 0]`. Jarak bertandanya
menjadi `(x - offX) + offX = x penuh`. Penampil Qt memakai koordinat PENUH sejak awal, jadi
pusatnya cukup `[0, 0, 0]` dan `pos` langsung berupa easting / northing penuh -- hasilnya sama,
representasinya saja yang lebih sederhana. Menyalin `c = [-offX, 0, 0]` ke sini akan menggeser
bidangnya dua kali.

Modul ini tidak memakai Qt dan tidak menghitung tonase apa pun: ia hanya menentukan blok mana
yang masuk slab, sehingga panel Tampilan, Laporan dan Dig block semuanya memakai satu definisi
sayatan yang sama.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .proyek import BlockModel

MODE = ("H", "X", "Y", "A", "P")
NAMA_MODE = {
    "H": "Datar (RL)",
    "X": "Tegak menghadap timur (easting)",
    "Y": "Tegak menghadap utara (northing)",
    "A": "Miring: azimut + dip",
    "P": "Miring: dua titik + dip",
}
SATUAN_POS = {"H": "RL", "X": "easting", "Y": "northing", "A": "offset", "P": "offset"}


@dataclass
class Bidang:
    """Bidang potong: normal `n`, sumbu dalam bidang `u` dan `w`, pusat `c`.

    `u` = arah "mendatar" di dalam bidang (sumbu mendatar penampang 2D),
    `w` = arah "tegak" di dalam bidang,
    `n` = normal bidang; jarak bertanda sebuah titik diukur sepanjang `n` dari `c`.
    `seg` = panjang ruas pada mode P (None bila tidak berlaku).
    """

    m: str = "H"
    az: float = 0.0
    dip: float = 0.0
    n: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    u: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    w: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    c: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    seg: Optional[float] = None


@dataclass
class Opsi:
    """Pilihan panel Sayatan."""

    mode: str = "H"
    pos: float = 0.0
    tebal: float = 5.0
    azimut: float = 0.0
    dip: float = 90.0
    pusat: Optional[Tuple[float, float, float]] = None   # mode A; None = tengah model
    titik1: Optional[Tuple[float, float]] = None         # mode P (easting, northing) PENUH
    titik2: Optional[Tuple[float, float]] = None
    pusat_z: Optional[float] = None                      # RL pusat bidang mode A / P; lihat di bawah
    batasi_ruas: bool = False                            # mode P: batasi sepanjang ruas saja
    perpanjang: float = 0.0                              # mode P: perpanjangan kedua ujung (m)
    potong: bool = True                                  # hanya tampilkan blok di dalam slab


def bidang(bm: BlockModel, O: Opsi) -> Bidang:
    """Padanan `secGeom`. Koordinat PENUH (lihat catatan offset di atas modul)."""
    x0, x1, y0, y1, z0, z1 = bm.kotak() if bm is not None and bm.n else (0, 0, 0, 0, 0, 0)
    m = O.mode if O.mode in MODE else "H"
    if m == "H":
        return Bidang(m="H", az=0.0, dip=0.0, n=(0.0, 0.0, 1.0), u=(0.0, 1.0, 0.0),
                      w=(1.0, 0.0, 0.0), c=(0.0, 0.0, 0.0))
    if m == "X":
        return Bidang(m="X", az=0.0, dip=90.0, n=(1.0, 0.0, 0.0), u=(0.0, 1.0, 0.0),
                      w=(0.0, 0.0, -1.0), c=(0.0, 0.0, 0.0))
    if m == "Y":
        return Bidang(m="Y", az=90.0, dip=90.0, n=(0.0, 1.0, 0.0), u=(1.0, 0.0, 0.0),
                      w=(0.0, 0.0, -1.0), c=(0.0, 0.0, 0.0))

    az = 0.0
    # RL PUSAT BIDANG. Jebakan paritas yang halus: `secGeom` di aplikasi HTML memakai
    # `zc = (G.z0 + G.z1) / 2`, yaitu tengah kotak DATA (bor, topografi, desain pit) -- BUKAN
    # tengah block model. Pada dip 90 ini tidak berpengaruh (normal bidang tidak punya komponen
    # z), tetapi pada dip lain bidangnya bergeser dan blok yang terpilih berbeda. Karena itu RL
    # pusat bisa diberikan tegas lewat `pusat_z`; bila tidak diberikan dipakai tengah block
    # model, dan panel menyebutkan nilai yang sedang dipakai supaya tidak ada yang menebak.
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    cz = float(O.pusat_z) if O.pusat_z is not None else (z0 + z1) / 2.0
    seg = None
    dip = min(90.0, max(0.0, float(O.dip)))
    if m == "A":
        az = float(O.azimut)
        if O.pusat:
            cx, cy, cz = (float(O.pusat[0]), float(O.pusat[1]), float(O.pusat[2]))
    else:                                   # mode P
        if O.titik1 and O.titik2:
            e1, n1 = float(O.titik1[0]), float(O.titik1[1])
            e2, n2 = float(O.titik2[0]), float(O.titik2[1])
            if (e1 != e2 or n1 != n2) and all(math.isfinite(v) for v in (e1, n1, e2, n2)):
                az = math.degrees(math.atan2(e2 - e1, n2 - n1))
                cx, cy = e1, n1
                seg = math.hypot(e2 - e1, n2 - n1)
    a = math.radians(az)
    d = math.radians(dip)
    sa, ca, sp, cp = math.sin(a), math.cos(a), math.sin(d), math.cos(d)
    return Bidang(m=m, az=az, dip=dip,
                  u=(sa, ca, 0.0), w=(ca * cp, -sa * cp, -sp), n=(ca * sp, -sa * sp, cp),
                  c=(cx, cy, cz), seg=seg)


def jarak(n: Sequence[float], c: Sequence[float], P: np.ndarray) -> np.ndarray:
    """Jarak bertanda tiap titik ke bidang (padanan `sd`). P berbentuk (m, 3)."""
    return (n[0] * (P[:, 0] - c[0]) + n[1] * (P[:, 1] - c[1]) + n[2] * (P[:, 2] - c[2]))


@dataclass
class Slab:
    """Daftar batas yang membentuk slab: tiap unsur (normal, pusat, lo, hi) -- padanan `secK().K`."""

    g: Bidang = field(default_factory=Bidang)
    pos: float = 0.0
    tebal: float = 5.0
    batas: List[Tuple[Tuple[float, float, float], Tuple[float, float, float],
                      float, float]] = field(default_factory=list)


def slab(bm: BlockModel, O: Opsi) -> Slab:
    """Padanan `secK`: slab setebal `tebal` di sekitar `pos`, plus batas ruas pada mode P."""
    g = bidang(bm, O)
    tebal = max(0.1, float(O.tebal) if math.isfinite(float(O.tebal)) else 5.0)
    pos = float(O.pos)
    K = [(g.n, g.c, pos - tebal / 2.0, pos + tebal / 2.0)]
    if g.m == "P" and g.seg and O.batasi_ruas:
        ex = float(O.perpanjang or 0.0)
        K.append((g.u, g.c, -ex, g.seg + ex))
    return Slab(g=g, pos=pos, tebal=tebal, batas=K)


def dalam_slab(bm: BlockModel, O: Opsi) -> np.ndarray:
    """Larik bool: blok yang KOTAKNYA bersinggungan dengan slab -- padanan `bxSlabHit`.

    BUKAN uji titik tengah. Aplikasi HTML menguji blok sebagai kotak: setengah rentang blok
    diproyeksikan ke normal bidang (`r = (sx·|nx| + sy·|ny| + sz·|nz|) / 2`), lalu blok ikut bila
    rentang [d−r, d+r] bersinggungan dengan [lo, hi]. Bedanya besar dan bukan soal selera: pada
    slab yang lebih tipis daripada satu blok, uji titik tengah hampir tidak memilih apa pun,
    sedangkan uji kotak memilih satu lapis blok penuh. Memakai uji titik tengah di sini akan
    membuat sayatan Qt menampilkan jauh lebih sedikit blok daripada aplikasi HTML pada pengaturan
    yang sama -- dan tidak ada yang akan menduga sebabnya.

    Perbandingan ketat / tidak ketatnya juga ditiru apa adanya, termasuk kasus bidang berketebalan
    nol (`lo == hi`) yang memakai toleransi 1e-9 dan perbandingan `<=`.
    """
    if bm is None or not bm.n:
        return np.zeros(0, dtype=bool)
    S = slab(bm, O)
    X = np.asarray(bm.x, dtype=np.float64)
    Y = np.asarray(bm.y, dtype=np.float64)
    Z = np.asarray(bm.z, dtype=np.float64)
    SX = np.asarray(bm.sx, dtype=np.float64)
    SY = np.asarray(bm.sy, dtype=np.float64)
    SZ = np.asarray(bm.sz, dtype=np.float64)
    P = np.column_stack([X, Y, Z])
    ok = np.ones(bm.n, dtype=bool)
    for n, c, lo, hi in S.batas:
        d = jarak(n, c, P)
        r = (SX * abs(n[0]) + SY * abs(n[1]) + SZ * abs(n[2])) / 2.0
        if lo == hi:
            buang = (d + r <= lo + 1e-9) | (d - r > hi)
        else:
            buang = (d + r < lo) | (d - r > hi)
        ok &= ~buang
    return ok


def dalam_slab_titik(bm: BlockModel, O: Opsi) -> np.ndarray:
    """Uji TITIK TENGAH saja (padanan `inK`), bukan uji kotak.

    Dipakai hanya di tempat aplikasi HTML sendiri memakai titik tengah -- misalnya metode tonase
    "seperti Surpac". Untuk menentukan blok mana yang DIGAMBAR, pakai `dalam_slab`.
    """
    if bm is None or not bm.n:
        return np.zeros(0, dtype=bool)
    S = slab(bm, O)
    P = np.column_stack([np.asarray(bm.x, dtype=np.float64),
                         np.asarray(bm.y, dtype=np.float64),
                         np.asarray(bm.z, dtype=np.float64)])
    ok = np.ones(bm.n, dtype=bool)
    for n, c, lo, hi in S.batas:
        d = jarak(n, c, P)
        ok &= (d >= lo) & (d <= hi)
    return ok


def rentang_pos(bm: BlockModel, O: Opsi) -> Tuple[float, float]:
    """Rentang `pos` yang masuk akal untuk mode ini -- padanan `updRange`.

    Untuk mode datar dipakai rentang RL model apa adanya; untuk mode lain dihitung dari jarak
    bertanda kedelapan sudut kotak model, lalu dibulatkan keluar 10 m seperti di aplikasi.
    """
    if bm is None or not bm.n:
        return (0.0, 0.0)
    x0, x1, y0, y1, z0, z1 = bm.kotak()
    g = bidang(bm, O)
    if g.m == "H":
        return (float(z0), float(z1))
    sudut = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)],
                     dtype=np.float64)
    d = jarak(g.n, g.c, sudut)
    return (math.floor(float(d.min())) - 10.0, math.ceil(float(d.max())) + 10.0)


def pos_awal(bm: BlockModel, O: Opsi) -> float:
    """Nilai `pos` bawaan saat mode diganti -- padanan `updRange(true)`.

    Mode A dan P bawaannya 0 (bidang lewat pusat / titik 1), bukan tengah rentang: pada mode itu
    `pos` adalah JARAK dari pusat, jadi nol berarti "tepat di bidang yang dipilih".
    """
    g = bidang(bm, O)
    if g.m in ("A", "P"):
        return 0.0
    lo, hi = rentang_pos(bm, O)
    return float(round((lo + hi) / 2.0))


def label(bm: BlockModel, O: Opsi) -> str:
    """Keterangan singkat sayatan yang aktif, untuk ditulis di panel dan judul gambar."""
    g = bidang(bm, O)
    t = max(0.1, float(O.tebal))
    if g.m == "H":
        return "Datar RL %.2f (tebal %.2f m)" % (O.pos, t)
    if g.m == "X":
        return "Tegak, easting %.2f (tebal %.2f m)" % (O.pos, t)
    if g.m == "Y":
        return "Tegak, northing %.2f (tebal %.2f m)" % (O.pos, t)
    s = "Miring azimut %.1f° dip %.1f°, offset %.2f (tebal %.2f m)" % (g.az, g.dip, O.pos, t)
    if g.m == "P" and g.seg:
        s += ", ruas %.1f m" % g.seg
        if O.batasi_ruas:
            s += " (dibatasi%s)" % (", perpanjangan %.1f m" % O.perpanjang
                                    if O.perpanjang else "")
    return s
