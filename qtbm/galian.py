# -*- coding: utf-8 -*-
"""Dig block: tonase & kadar satu poligon galian pada satu flitch.

Padanan `lyTon` (presisi GC-Ex) dan `lyTonS` (seperti Surpac) di aplikasi HTML. Modul ini tidak
memakai Qt sama sekali supaya bisa diuji tanpa layar.

DUA METODE, DUA ANGKA YANG BERBEDA -- dan bedanya bukan galat:

  presisi ('clip')  : setiap blok dipotong di garis poligon dan di bidang atas/bawah flitch.
                      Volume = luas potongan x tebal bagian blok yang masuk flitch. Blok yang
                      hanya tersentuh ujungnya ikut, sebesar bagiannya saja.
  surpac ('surpac') : blok ikut UTUH bila titik tengahnya ada di dalam poligon dan di dalam
                      flitch; kalau tidak, tidak ikut sama sekali. Ini cara Surpac menghitung,
                      dan angkanya dipakai untuk mencocokkan laporan dengan sistem resmi tambang.

RUANG KOORDINAT: poligon `P` harus dalam ruang koordinat YANG SAMA dengan `BlockModel.x/y`,
yaitu koordinat penuh (easting / northing sebenarnya). Di aplikasi HTML titik hasil digitasi
tersimpan relatif terhadap `offX`/`offY` sehingga `lyItems()` harus menambahkannya dulu; penampil
Qt tidak menyalin pembagian itu dan menyimpan satu ruang saja (lihat `qtbm/string_io.py`).

Satu asimetri yang WAJIB diketahui pemakai: waste pengisi (dilusi sisa luas poligon yang tidak
tertutup blok) hanya ditambahkan pada metode presisi. Di aplikasi HTML, `lyTonS` memang tidak
pernah menambahkannya -- jadi baris waste hilang begitu metode diganti ke Surpac. Itu perilaku
aplikasi resmi dan sengaja ditiru, bukan kelupaan; `hasil.waste_didukung` menyatakannya supaya
panel bisa mengatakannya terus-terang.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .proyek import BlockModel
from .tampil_bm import Tampilan

Titik = Tuple[float, float]
EPS = 1e-6


# ====================== geometri bidang datar ======================

def luas(P: Sequence[Titik]) -> float:
    """Luas poligon (shoelace, tanda diabaikan) -- `lyArea`."""
    a = 0.0
    n = len(P)
    for i in range(n):
        j = i - 1
        a += (P[j][0] + P[i][0]) * (P[j][1] - P[i][1])
    return abs(a / 2.0)


def di_dalam(P: Sequence[Titik], x: float, y: float) -> bool:
    """Uji titik di dalam poligon (ray crossing) -- `lyIn`, termasuk kuirknya.

    Perbandingannya `P[i][1] > y`, bukan `>=`: titik yang tepat di garis bisa terbaca di dalam
    atau di luar tergantung arah ruas. Itu sebabnya metode Surpac memakai `di_dalam_atau_tepi`.
    """
    c = False
    n = len(P)
    for i in range(n):
        j = i - 1
        if (P[i][1] > y) != (P[j][1] > y):
            xx = (P[j][0] - P[i][0]) * (y - P[i][1]) / (P[j][1] - P[i][1]) + P[i][0]
            if x < xx:
                c = not c
    return c


def di_tepi(P: Sequence[Titik], x: float, y: float) -> bool:
    """Titik tepat di salah satu ruas poligon -- `lyOnEdge`."""
    n = len(P)
    for i in range(n):
        a, b = P[i - 1], P[i]
        cr = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
        panjang = max(1.0, math.hypot(b[0] - a[0], b[1] - a[1]))
        if abs(cr) > EPS * panjang:
            continue
        if (min(a[0], b[0]) - EPS <= x <= max(a[0], b[0]) + EPS
                and min(a[1], b[1]) - EPS <= y <= max(a[1], b[1]) + EPS):
            return True
    return False


def di_dalam_atau_tepi(P: Sequence[Titik], x: float, y: float) -> bool:
    """`lyInS`: blok yang titik tengahnya tepat di garis poligon ikut dihitung."""
    return di_tepi(P, x, y) or di_dalam(P, x, y)


def kotak(P: Sequence[Titik]) -> Tuple[float, float, float, float]:
    """[xmin, xmaks, ymin, ymaks] -- `lyBB`."""
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    return (min(xs), max(xs), min(ys), max(ys))


def luas_terpotong(P: Sequence[Titik], r: Sequence[float]) -> float:
    """Luas bagian poligon P yang masuk persegi r = [x0, x1, y0, y1] -- `lyClip`.

    Sutherland-Hodgman terhadap empat sisi persegi, urutan sisi sama dengan aslinya.
    """
    o = [(float(p[0]), float(p[1])) for p in P]
    sisi = ((0, r[0], 1.0), (0, r[1], -1.0), (1, r[2], 1.0), (1, r[3], -1.0))
    for a, v, sg in sisi:
        if not o:
            break
        n: List[Titik] = []
        m = len(o)
        for i in range(m):
            p = o[i]
            q = o[(i + 1) % m]
            pi = (p[a] - v) * sg >= 0
            qi = (q[a] - v) * sg >= 0
            if pi:
                n.append(p)
            if pi != qi:
                d = q[a] - p[a]
                t = (v - p[a]) / d if d else 0.0
                n.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
        o = n
    return luas(o) if len(o) > 2 else 0.0


# ====================== flitch ======================

def bench(atas: float, bawah: float) -> Tuple[float, float]:
    """(atas, bawah) terurut -- `lyBench` sudah menukarnya bila terbalik."""
    return (max(atas, bawah), min(atas, bawah))


def tebal_dalam_flitch(bm: BlockModel, B: Tuple[float, float], mode: str = "comp") -> np.ndarray:
    """Tebal bagian tiap blok yang masuk flitch B -- `lyOv`, untuk seluruh blok sekaligus.

    mode 'comp' : tumpang tindih sebenarnya antara blok dan flitch (composite).
    mode 'mid'  : hanya blok yang terpotong bidang TENGAH flitch, dan dihitung setebal flitch
                  penuh. Ini meniru cara sebagian sistem mengambil "satu lapis" dan membuat
                  volume blok tipis membengkak ke tebal flitch -- bukan galat, pilihan.
    """
    h = np.asarray(bm.sz, dtype=np.float64) / 2.0
    lo = np.asarray(bm.z, dtype=np.float64) - h
    hi = np.asarray(bm.z, dtype=np.float64) + h
    if mode == "mid":
        zs = round((B[0] + B[1]) / 2.0 * 1000.0) / 1000.0
        kena = (lo <= zs + 1e-9) & (zs < hi - 1e-9)
        return np.where(kena, B[0] - B[1], 0.0)
    o = np.minimum(hi, B[0]) - np.maximum(lo, B[1])
    return np.where(o > EPS, o, 0.0)


def zs_flitch(B: Tuple[float, float]) -> float:
    """RL bidang tengah flitch -- `lyZs` (dibulatkan ke 3 desimal seperti aslinya)."""
    return round((B[0] + B[1]) / 2.0 * 1000.0) / 1000.0


# ====================== pilihan & hasil ======================

@dataclass
class Opsi:
    """Pilihan panel Dig block -- padanan `lyU()` yang dipakai `lyTon` / `lyTonS`."""

    rl_atas: float = 0.0
    rl_bawah: float = 0.0
    kadar: str = ""                      # atribut kadar; kosong = tanpa kadar
    metode: str = "clip"                 # 'clip' (presisi) atau 'surpac'
    mode_flitch: str = "comp"            # 'comp' atau 'mid'
    hanya_lolos: bool = False            # ikut cut-off tampilan -- `lyU().onlyPass`
    # Waste pengisi (hanya metode presisi, lihat catatan modul).
    # BAWAANNYA MENYALA, bukan selera: di aplikasi HTML `dbU()` menyetel `U.wOn = true` bila
    # belum pernah disentuh. Kalau di sini dibuat mati, tonase dig block bawaan Qt akan lebih
    # kecil daripada aplikasi HTML untuk poligon yang sama -- selisih yang tidak akan dicari
    # siapa pun karena tidak ada yang merasa mengubah apa-apa.
    waste_on: bool = True
    waste_sg: float = 0.0                # <= 0 = pakai SG tunggal panel tampilan
    waste_kadar: float = 0.0

    def bench(self) -> Tuple[float, float]:
        return bench(self.rl_atas, self.rl_bawah)


@dataclass
class Hasil:
    """Hasil satu poligon. Nama ruas mengikuti `lyTon` supaya mudah dicocokkan."""

    n: int = 0                           # jumlah blok yang ikut
    v: float = 0.0                       # volume (m3), termasuk waste pengisi
    t: float = 0.0                       # tonase (t), termasuk waste pengisi
    a: float = 0.0                       # luas setara (m2) = volume blok / tebal flitch
    kadar: float = float("nan")
    luas_poligon: float = 0.0
    cov: float = 0.0                     # bagian luas poligon yang tertutup blok (0..1)
    waste_a: float = 0.0
    waste_t: float = 0.0
    waste_didukung: bool = True
    metode: str = "clip"
    atribut: str = ""
    fh: float = 0.0
    zs: float = 0.0
    g: float = 0.0                       # sum(kadar x tonase)
    gt: float = 0.0                      # sum(tonase berkadar sah)

    @property
    def logam(self) -> float:
        """sum(kadar x tonase) -- satuannya ikut satuan kadar, panel yang memberi labelnya."""
        return self.g


# ====================== mesin hitung ======================

def _siapkan(bm: BlockModel, T: Tampilan, O: Opsi):
    B = O.bench()
    fh = B[0] - B[1]
    if not (fh > 0):
        raise ValueError("tinggi flitch harus lebih besar dari nol (RL atas = RL bawah)")
    G = bm.angka.get(O.kadar) if O.kadar else None
    SG = T.sg_larik(bm)
    return B, fh, G, SG


def _lolos(bm: BlockModel, T: Tampilan, O: Opsi) -> Optional[np.ndarray]:
    """Topeng cut-off tampilan bila `hanya_lolos` -- `bxPass`."""
    if not O.hanya_lolos:
        return None
    from . import tampil_bm as TB
    return TB.lolos(bm, T)


def tonase(bm: BlockModel, P: Sequence[Titik], T: Tampilan, O: Opsi,
           kecuali: Optional[Sequence[Sequence[Titik]]] = None) -> Hasil:
    """Tonase & kadar poligon P pada flitch O, metode sesuai `O.metode`.

    `kecuali` = poligon dalam (lubang) yang dikeluarkan, seperti argumen `excl` di aplikasi HTML.
    """
    if len(P) < 3:
        raise ValueError("poligon galian butuh minimal 3 titik")
    if O.metode == "surpac":
        return _tonase_surpac(bm, P, T, O, kecuali or [])
    return _tonase_presisi(bm, P, T, O, kecuali or [])


def _tonase_presisi(bm, P, T, O, kecuali) -> Hasil:
    B, fh, G, SG = _siapkan(bm, T, O)
    ov = tebal_dalam_flitch(bm, B, O.mode_flitch)
    pass_ = _lolos(bm, T, O)
    x0, x1, y0, y1 = kotak(P)
    kk = [(list(Q), kotak(Q)) for Q in kecuali]

    R = Hasil(metode="clip", atribut=O.kadar or "", fh=fh, zs=zs_flitch(B))
    X = np.asarray(bm.x, dtype=np.float64)
    Y = np.asarray(bm.y, dtype=np.float64)
    HX = np.asarray(bm.sx, dtype=np.float64) / 2.0
    HY = np.asarray(bm.sy, dtype=np.float64) / 2.0
    # calon: hanya blok yang menyentuh flitch dan kotak pembatas poligon. Tanpa penyaringan ini
    # setiap blok model akan dipotong satu per satu -- lambat, hasilnya sama.
    calon = np.nonzero((ov > 0)
                       & (X + HX >= x0) & (X - HX <= x1)
                       & (Y + HY >= y0) & (Y - HY <= y1))[0]
    for i in calon:
        i = int(i)
        if pass_ is not None and not pass_[i]:
            continue
        rc = (X[i] - HX[i], X[i] + HX[i], Y[i] - HY[i], Y[i] + HY[i])
        ar = luas_terpotong(P, rc)
        if ar <= EPS:
            continue
        for Q, qb in kk:
            if rc[1] < qb[0] or rc[0] > qb[1] or rc[3] < qb[2] or rc[2] > qb[3]:
                continue
            ar -= luas_terpotong(Q, rc)
        if ar <= EPS:
            continue
        v = ar * float(ov[i])
        t = v * float(SG[i])
        R.n += 1
        R.a += ar * float(ov[i]) / fh
        R.v += v
        R.t += t
        if G is not None:
            gv = float(G[i])
            if math.isfinite(gv):
                R.g += gv * t
                R.gt += t

    PA = luas(P)
    for Q, _qb in kk:
        PA -= luas(Q)
    R.luas_poligon = PA
    if O.waste_on:
        wa = PA - R.a
        if wa > 1e-3:
            wsg = float(O.waste_sg)
            if not (wsg > 0):
                wsg = float(T.sg)
            R.waste_a = wa
            R.waste_t = wa * fh * wsg
            R.t += R.waste_t
            R.v += wa * fh
            R.g += float(O.waste_kadar) * R.waste_t
            R.gt += R.waste_t
    R.kadar = (R.g / R.gt) if R.gt else float("nan")
    R.cov = R.a / max(1e-9, PA)
    return R


def _tonase_surpac(bm, P, T, O, kecuali) -> Hasil:
    B, fh, G, SG = _siapkan(bm, T, O)
    pass_ = _lolos(bm, T, O)
    b = kotak(P)
    kk = [list(Q) for Q in kecuali]

    R = Hasil(metode="surpac", atribut=O.kadar or "", fh=fh, zs=zs_flitch(B),
              waste_didukung=False)
    X = np.asarray(bm.x, dtype=np.float64)
    Y = np.asarray(bm.y, dtype=np.float64)
    Z = np.asarray(bm.z, dtype=np.float64)
    SZ = np.asarray(bm.sz, dtype=np.float64)
    # lyCandZ lalu syarat titik tengah di dalam flitch: (bawah, atas].
    calon = np.nonzero((Z + SZ / 2.0 > B[1]) & (Z - SZ / 2.0 < B[0])
                       & (Z > B[1] + 1e-9) & (Z <= B[0] + 1e-9)
                       & (X >= b[0] - EPS) & (X <= b[1] + EPS)
                       & (Y >= b[2] - EPS) & (Y <= b[3] + EPS))[0]
    SX = np.asarray(bm.sx, dtype=np.float64)
    SY = np.asarray(bm.sy, dtype=np.float64)
    for i in calon:
        i = int(i)
        if pass_ is not None and not pass_[i]:
            continue
        x, y = float(X[i]), float(Y[i])
        if not di_dalam_atau_tepi(P, x, y):
            continue
        buang = False
        for Q in kk:
            if di_dalam(Q, x, y) and not di_tepi(Q, x, y):
                buang = True
                break
        if buang:
            continue
        v = float(SX[i]) * float(SY[i]) * float(SZ[i])
        t = v * float(SG[i])
        R.n += 1
        R.v += v
        R.t += t
        R.a += v / fh
        if G is not None:
            gv = float(G[i])
            if math.isfinite(gv):
                R.g += gv * t
                R.gt += t

    PA = luas(P)
    for Q in kk:
        PA -= luas(Q)
    R.luas_poligon = PA
    R.kadar = (R.g / R.gt) if R.gt else float("nan")
    R.cov = R.a / max(1e-9, PA)
    return R


def bandingkan(bm: BlockModel, P: Sequence[Titik], T: Tampilan, O: Opsi,
               kecuali=None) -> Dict[str, Hasil]:
    """Kedua metode berdampingan, supaya selisihnya terlihat dan bukan dugaan."""
    out: Dict[str, Hasil] = {}
    for m in ("clip", "surpac"):
        Om = Opsi(**{**O.__dict__, "metode": m})
        out[m] = tonase(bm, P, T, Om, kecuali)
    return out


NAMA_METODE = {"clip": "Presisi GC-Ex", "surpac": "Seperti Surpac"}


def catatan(bm: BlockModel, hasil: Dict[str, Hasil], O: Opsi) -> List[str]:
    """Peringatan yang ikut ditampilkan bersama angkanya, bukan di bantuan terpisah."""
    out: List[str] = []
    H = hasil.get("clip") or next(iter(hasil.values()), None)
    if H is None:
        return out
    if H.cov < 0.999:
        out.append("Blok hanya menutup %.1f%% luas poligon. Sisanya tidak punya blok sama sekali: "
                   "tonasenya TIDAK terhitung kecuali waste pengisi dinyalakan."
                   % (H.cov * 100.0))
    if O.waste_on and "surpac" in hasil:
        out.append("Waste pengisi hanya ditambahkan pada metode presisi; aplikasi HTML pun tidak "
                   "menambahkannya pada metode Surpac. Jadi selisih kedua kolom di bawah sudah "
                   "memuat perbedaan itu, bukan hanya perbedaan cara memotong blok.")
    if O.mode_flitch == "mid":
        out.append("Mode flitch 'bidang tengah': blok yang terpotong bidang tengah dihitung "
                   "SETEBAL flitch penuh, walau bloknya lebih tipis. Volume bisa lebih besar "
                   "daripada volume blok sebenarnya.")
    if not O.kadar:
        out.append("Atribut kadar belum dipilih: kolom kadar dan logam kosong, tonase tetap sah.")
    elif H.gt and H.t and abs(H.gt - H.t) > max(1e-6, 1e-9 * H.t):
        out.append("%.1f%% tonase tidak punya kadar sah (kosong / NaN) dan tidak ikut rata-rata "
                   "kadar. Tonasenya tetap dilaporkan." % ((1.0 - H.gt / H.t) * 100.0))
    if "clip" in hasil and "surpac" in hasil:
        a, b = hasil["clip"].t, hasil["surpac"].t
        if b > 0 and abs(a - b) <= max(1e-6, 1e-9 * b):
            out.append("Kedua metode memberi tonase yang sama persis di poligon ini. Itu bisa "
                       "terjadi bila poligon jatuh tepat di garis blok; bukan bukti umum bahwa "
                       "kedua cara selalu cocok.")
    return out
