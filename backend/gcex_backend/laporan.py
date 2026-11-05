# -*- coding: utf-8 -*-
"""Agregasi laporan block model (tonase x kadar) -- versi Python.

Padanan JavaScript: rpRun() di web-src/rpbm.js (dipakai juga oleh rppit.js untuk laporan per
desain pit dan progres topo-ke-topo). Angkanya WAJIB sama; paritasnya diuji di
backend/tests/test_laporan.py terhadap keluaran JS asli yang dibekukan.

Yang dihitung: tiap blok disaring constraint berurutan, lalu tonase (volume x SG x proporsi
sb_frac) dan kadar rata-rata BERBOBOT TONASE dijumlahkan per cut-off dan per grup (total, bench
RL, atau kategori).

URUTAN PENYARINGAN DIPERTAHANKAN SAMA DENGAN JS, karena bukan hanya hasil akhirnya yang dipakai:
jumlah blok yang terbuang di tiap tahap (nOut) ditampilkan ke pemakai sebagai alasan "kenapa
tonasenya sekian". Urutannya: rentang RL -> poligon -> filter atribut -> permukaan atas/bawah ->
batas DTM tambahan -> domain -> kadar tidak sah -> SG tidak sah -> proporsi nol.

SATU HAL YANG MUDAH TERLEWAT: di JS nilai permukaan di-cache dengan kunci
Math.round(x*2)+'|'+Math.round(y*2), jadi blok-blok yang kuncinya sama memakai nilai permukaan
milik blok PERTAMA yang kuncinya itu -- bukan nilai di titik pusatnya sendiri. Itu ditiru di sini
(lihat _wakil); tanpa itu, tonase bisa berbeda tipis di blok-blok yang berdekatan.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

NEG = -90.0          # nilai <= -90 dianggap "tidak ada data" (sama dengan JS)


# ---------------------------------------------------------------------------
# Permukaan
# ---------------------------------------------------------------------------
class Idw:
    """Permukaan dari titik sebaran (topografi / desain pit), padanan rpSurf().

    IDW 1/d^2 pada sel 10 m: radius dilebarkan R = 1, 2, 3 sel sampai dapat >= 3 titik; bila
    tetap kurang, hasilnya None (di luar jangkauan data). Titik yang berjarak < 0,01 m dipakai
    apa adanya.
    """

    B = 10.0

    def __init__(self, o: Dict[str, Any]) -> None:
        x = np.asarray([v for v in o["x"]], dtype=np.float64)
        y = np.asarray([v for v in o["y"]], dtype=np.float64)
        z = np.asarray([v for v in o["z"]], dtype=np.float64)
        baik = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        self.x, self.y, self.z = x[baik], y[baik], z[baik]
        cx = np.floor(self.x / self.B).astype(np.int64)
        cy = np.floor(self.y / self.B).astype(np.int64)
        self.kode = (cx + 50000) * 100000 + cy + 50000
        urut = np.argsort(self.kode, kind="stable")
        self.urut = urut
        self.kode_urut = self.kode[urut]

    def nilai(self, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
        """Hasil: larik z; NaN berarti di luar jangkauan data (padanan null di JS).

        Radius dicoba R = 1, 2, 3 dengan urutan sel yang sama seperti JS, supaya titik yang
        "tepat di lokasi" (d < 0,01 m) yang dipakai juga titik yang sama.
        """
        out = np.full(X.size, np.nan)
        sisa = np.arange(X.size)
        for R in (1, 2, 3):
            if sisa.size == 0:
                break
            rm = (R * self.B) * (R * self.B)
            cx = np.floor(X[sisa] / self.B).astype(np.int64)
            cy = np.floor(Y[sisa] / self.B).astype(np.int64)
            sw = np.zeros(sisa.size)
            sz = np.zeros(sisa.size)
            npt = np.zeros(sisa.size, dtype=np.int64)
            tepat = np.full(sisa.size, np.nan)
            for da in range(-R, R + 1):
                for db in range(-R, R + 1):
                    kode = (cx + da + 50000) * 100000 + (cy + db) + 50000
                    aw = np.searchsorted(self.kode_urut, kode, side="left")
                    ak = np.searchsorted(self.kode_urut, kode, side="right")
                    cacah = ak - aw
                    tot = int(cacah.sum())
                    if tot == 0:
                        continue
                    pid = np.repeat(np.arange(sisa.size), cacah)
                    geser = np.arange(tot, dtype=np.int64) - np.repeat(np.cumsum(cacah) - cacah, cacah)
                    tid = self.urut[np.repeat(aw, cacah) + geser]
                    dx = self.x[tid] - X[sisa][pid]
                    dy = self.y[tid] - Y[sisa][pid]
                    d2 = dx * dx + dy * dy
                    pakai = d2 <= rm
                    if not pakai.any():
                        continue
                    pid = pid[pakai]; d2 = d2[pakai]; zt = self.z[tid[pakai]]
                    dekat = d2 < 1e-4
                    if dekat.any():
                        # JS langsung mengembalikan nilai titik itu; yang pertama ditemukan menang
                        for q, v in zip(pid[dekat], zt[dekat]):
                            if math.isnan(tepat[q]):
                                tepat[q] = v
                    jauh = ~dekat
                    if jauh.any():
                        w = 1.0 / d2[jauh]
                        np.add.at(sw, pid[jauh], w)
                        np.add.at(sz, pid[jauh], w * zt[jauh])
                        np.add.at(npt, pid[jauh], 1)
            ada = ~np.isnan(tepat)
            cukup = npt >= 3
            hasil = np.where(ada, tepat, np.where(cukup, sz / np.where(sw == 0, 1.0, sw), np.nan))
            siap = ada | cukup
            out[sisa[siap]] = hasil[siap]
            sisa = sisa[~siap]
        return out


class Tin:
    """DTM segitiga (koordinat dunia) -> [z minimum, z maksimum] di (x,y), padanan rpTinFn()."""

    def __init__(self, T: Dict[str, Any]) -> None:
        V = np.asarray(T["v"], dtype=np.float64).reshape(-1, 3)
        Tr = np.asarray(T["t"], dtype=np.int64).reshape(-1, 3)
        self.A = V[Tr[:, 0]]; self.Bv = V[Tr[:, 1]]; self.C = V[Tr[:, 2]]
        self.nt = Tr.shape[0]
        self.x0, self.x1 = float(V[:, 0].min()), float(V[:, 0].max())
        self.y0, self.y1 = float(V[:, 1].min()), float(V[:, 1].max())
        B = max(1.0, min(100.0, math.sqrt(max(1.0, (self.x1 - self.x0) * (self.y1 - self.y0))
                                          / max(1, self.nt)) * 2))
        self.B = B
        self.nx = int((self.x1 - self.x0) // B) + 1
        gx0 = np.floor((np.minimum.reduce([self.A[:, 0], self.Bv[:, 0], self.C[:, 0]]) - self.x0) / B).astype(np.int64)
        gx1 = np.floor((np.maximum.reduce([self.A[:, 0], self.Bv[:, 0], self.C[:, 0]]) - self.x0) / B).astype(np.int64)
        gy0 = np.floor((np.minimum.reduce([self.A[:, 1], self.Bv[:, 1], self.C[:, 1]]) - self.y0) / B).astype(np.int64)
        gy1 = np.floor((np.maximum.reduce([self.A[:, 1], self.Bv[:, 1], self.C[:, 1]]) - self.y0) / B).astype(np.int64)
        lebar = gx1 - gx0 + 1
        tinggi = gy1 - gy0 + 1
        ulang = lebar * tinggi
        tri = np.repeat(np.arange(self.nt, dtype=np.int64), ulang)
        pos = np.arange(int(ulang.sum()), dtype=np.int64) - np.repeat(np.cumsum(ulang) - ulang, ulang)
        lb = np.repeat(lebar, ulang)
        kode = (np.repeat(gy0, ulang) + pos // lb) * self.nx + (np.repeat(gx0, ulang) + pos % lb)
        urut = np.argsort(kode, kind="stable")
        self.kode = kode[urut]
        self.tri = tri[urut]

    def nilai(self, X: np.ndarray, Y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Hasil: (lo, hi); NaN berarti tidak ada segitiga di bawah / atas titik itu."""
        lo = np.full(X.size, np.nan)
        hi = np.full(X.size, np.nan)
        dalam = (X >= self.x0) & (X <= self.x1) & (Y >= self.y0) & (Y <= self.y1)
        idx = np.flatnonzero(dalam)
        if idx.size == 0:
            return lo, hi
        kode = np.floor((Y[idx] - self.y0) / self.B).astype(np.int64) * self.nx \
            + np.floor((X[idx] - self.x0) / self.B).astype(np.int64)
        a = np.searchsorted(self.kode, kode, side="left")
        b = np.searchsorted(self.kode, kode, side="right")
        n = b - a
        if n.sum() == 0:
            return lo, hi
        pid = np.repeat(np.arange(idx.size), n)
        geser = np.arange(int(n.sum()), dtype=np.int64) - np.repeat(np.cumsum(n) - n, n)
        T = self.tri[np.repeat(a, n) + geser]
        X1 = self.A[T, 0]; Y1 = self.A[T, 1]
        X2 = self.Bv[T, 0]; Y2 = self.Bv[T, 1]
        X3 = self.C[T, 0]; Y3 = self.C[T, 1]
        d = (Y2 - Y3) * (X1 - X3) + (X3 - X2) * (Y1 - Y3)
        ok = np.abs(d) >= 1e-12
        dd = np.where(ok, d, 1.0)
        px = X[idx][pid]; py = Y[idx][pid]
        l1 = ((Y2 - Y3) * (px - X3) + (X3 - X2) * (py - Y3)) / dd
        l2 = ((Y3 - Y1) * (px - X3) + (X1 - X3) * (py - Y3)) / dd
        l3 = 1.0 - l1 - l2
        e = -1e-9
        kena = ok & (l1 >= e) & (l2 >= e) & (l3 >= e)
        if not kena.any():
            return lo, hi
        z = l1 * self.A[T, 2] + l2 * self.Bv[T, 2] + l3 * self.C[T, 2]
        p = pid[kena]; zv = z[kena]
        L = np.full(idx.size, np.inf)
        H = np.full(idx.size, -np.inf)
        np.minimum.at(L, p, zv)
        np.maximum.at(H, p, zv)
        ada = np.isfinite(H)
        lo[idx[ada]] = L[ada]
        hi[idx[ada]] = H[ada]
        return lo, hi


def _wakil(X: np.ndarray, Y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Tiru cache permukaan di JS: kunci Math.round(x*2)+'|'+Math.round(y*2), dan nilai dipakai
    dari blok PERTAMA yang memegang kunci itu. Hasil: (indeks wakil, peta blok -> wakil, kunci)."""
    kx = np.rint(X * 2).astype(np.int64)
    ky = np.rint(Y * 2).astype(np.int64)
    kunci = kx * 4_000_003 + ky                      # gabungan dua bilangan bulat
    _, awal, balik = np.unique(kunci, return_index=True, return_inverse=True)
    # np.unique mengembalikan kemunculan pertama pada larik terurut; untuk "pertama menurut
    # indeks blok" cukup ambil minimum indeks per kelompok
    pertama = np.full(awal.size, X.size, dtype=np.int64)
    np.minimum.at(pertama, balik, np.arange(X.size, dtype=np.int64))
    return pertama, balik, kunci


def _pip(P: np.ndarray, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Titik di dalam poligon (ray crossing), padanan rpPip() termasuk aturan tepinya."""
    c = np.zeros(X.size, dtype=bool)
    n = P.shape[0]
    for i in range(n):
        j = (i - 1) % n
        ax, ay = float(P[i, 0]), float(P[i, 1])
        bx, by = float(P[j, 0]), float(P[j, 1])
        if ay == by:
            continue                      # sisi mendatar: (a[1]>y) !== (b[1]>y) tidak mungkin benar
        silang = (ay > Y) != (by > Y)
        if not silang.any():
            continue
        xx = (bx - ax) * (Y - ay) / (by - ay) + ax
        c ^= silang & (X < xx)
    return c


def _poligon(rings: Sequence[Sequence[Sequence[float]]], X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Di dalam SALAH SATU ring (tiap ring punya kotak pembatas sendiri, sama dengan rpPoly)."""
    out = np.zeros(X.size, dtype=bool)
    for ring in rings:
        P = np.asarray(ring, dtype=np.float64)
        if P.shape[0] < 3:
            continue
        kotak = ((X >= P[:, 0].min()) & (X <= P[:, 0].max())
                 & (Y >= P[:, 1].min()) & (Y <= P[:, 1].max()))
        sisa = np.flatnonzero(kotak & ~out)
        if sisa.size == 0:
            continue
        out[sisa] = _pip(P, X[sisa], Y[sisa])
    return out


# ---------------------------------------------------------------------------
def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Titik masuk HTTP.

    payload:
      blocks : {x, y, z, sx, sy, sz}           -- koordinat dunia
      off    : [offX, offY]                     -- geseran ke koordinat lokal
      num    : {nama_atribut: [nilai per blok]}
      cat    : {nama: {codes: [...], dict: [...]}}   (opsional, untuk grup kategori / domain)
      opsi   : {cuts:[...], gr, atts:[...], unit:{}, grp:'none'|'bench'|'cat', bh, bref,
                catAttr, z0, z1, frac, fA, fOp, fV, sg, sgCol, sgZero, sgRep,
                poly:[[[x,y],...]], polyOut, dom:{mode:'all'|'cat'|'wf', attr, pilih:[...]},
                surf:{atas:{idw|tin}, bawah:{idw|tin}, atasTegas, bawahTegas},
                sx:[{tin:{v,t}, side:'above'|'below'}]}
    hasil   : {rows:[{c, G:{grup:{n, v, t, s:{att:{tw, w}}}}}], nb, nOut, nPart, ms}
    """
    t0 = time.perf_counter()
    B = payload.get("blocks") or {}
    X = np.asarray(B.get("x") or [], dtype=np.float64)
    Y = np.asarray(B.get("y") or [], dtype=np.float64)
    Z = np.asarray(B.get("z") or [], dtype=np.float64)
    SXb = np.asarray(B.get("sx") or [], dtype=np.float64)
    SYb = np.asarray(B.get("sy") or [], dtype=np.float64)
    SZb = np.asarray(B.get("sz") or [], dtype=np.float64)
    n = X.size
    if not (n == Y.size == Z.size == SXb.size == SYb.size == SZb.size):
        raise ValueError("panjang larik blok tidak sama")
    if n == 0:
        raise ValueError("tidak ada blok")
    o = payload.get("opsi") or {}
    num = payload.get("num") or {}
    cat = payload.get("cat") or {}
    off = payload.get("off") or [0.0, 0.0]
    xl = X - float(off[0])
    yl = Y - float(off[1])

    gr = o.get("gr")
    if not gr or gr not in num:
        raise ValueError("atribut kadar untuk cut-off tidak ada")
    atts = [a for a in (o.get("atts") or []) if a in num]
    if gr not in atts:
        atts.insert(0, gr)
    cuts = sorted(float(c) for c in (o.get("cuts") or [0]) if np.isfinite(float(c)))
    if not cuts:
        cuts = [0.0]
    G = np.asarray(num[gr], dtype=np.float64)

    hidup = np.ones(n, dtype=bool)
    nOut: Dict[str, int] = {"dom": 0, "surf": 0, "ext": 0, "z": 0, "poly": 0, "f": 0,
                            "nan": 0, "sg": 0, "frac": 0}

    def buang(kunci: str, buruk: np.ndarray) -> None:
        """Buang blok (di antara yang masih hidup) dan catat alasannya, seperti `continue` di JS."""
        k = np.flatnonzero(hidup)
        bad = k[buruk]
        nOut[kunci] += int(bad.size)
        hidup[bad] = False

    # 1. rentang RL
    z0 = o.get("z0")
    z1 = o.get("z1")
    buruk = np.zeros(int(hidup.sum()), dtype=bool)
    zz = Z[hidup]
    if z0 not in (None, ""):
        buruk |= zz < float(z0)
    if z1 not in (None, ""):
        buruk |= zz > float(z1)
    buang("z", buruk)

    # 2. poligon area
    rings = o.get("poly")
    if rings:
        luar = bool(o.get("polyOut"))
        k = np.flatnonzero(hidup)
        di = _poligon(rings, xl[k], yl[k])
        buang("poly", di == luar)

    # 3. filter atribut
    fA = o.get("fA")
    if fA and fA in num:
        fv = float(o.get("fV"))
        op = o.get("fOp") or "ge"
        k = np.flatnonzero(hidup)
        fa = np.asarray(num[fA], dtype=np.float64)[k]
        if op == "ge":
            buruk = ~np.isfinite(fa) | (fa < fv)
        elif op == "le":
            buruk = ~np.isfinite(fa) | (fa > fv)
        elif op == "eq":
            buruk = ~np.isfinite(fa) | (np.abs(fa - fv) > 1e-9)
        else:
            buruk = ~np.isfinite(fa)
        buang("f", buruk)

    # 4. permukaan atas (topografi / topo progres) & bawah (desain pit)
    #    Prioritas alasan dipertahankan seperti JS: permukaan atas diperiksa lebih dulu, dan satu
    #    blok hanya dicatat pada alasan PERTAMA yang mengenainya.
    S = o.get("surf") or {}
    atas, bawah = S.get("atas"), S.get("bawah")
    if atas or bawah:
        k = np.flatnonzero(hidup)
        pertama, balik, _ = _wakil(xl[k], yl[k])
        wx, wy = xl[k][pertama], yl[k][pertama]          # titik wakil, koordinat lokal
        wxw, wyw = X[k][pertama], Y[k][pertama]          # titik wakil, koordinat dunia (DTM)

        def permukaan(spek, ambil):
            """ambil: 'hi' untuk permukaan atas, 'lo' untuk bawah -- sama dengan zf() di rppit.js."""
            if not spek:
                return None
            if spek.get("tin"):
                lo, hi = Tin(spek["tin"]).nilai(wxw, wyw)
                return (hi if ambil == "hi" else lo)[balik]
            return Idw(spek["idw"]).nilai(wx, wy)[balik]

        zat = permukaan(atas, "hi")
        zbw = permukaan(bawah, "lo")
        zz = Z[k]
        alasan = np.zeros(k.size, dtype=np.int64)        # 0 = lolos, 1 = ext, 2 = surf
        if zat is not None:
            kosong = np.isnan(zat)
            if atas.get("tegas"):
                alasan = np.where(kosong, 1, alasan)
            # kalau nilainya kosong dan batasnya tidak tegas, blok diteruskan (sama dengan JS)
            alasan = np.where((alasan == 0) & ~kosong & (zz > zat), 2, alasan)
        if zbw is not None:
            kosong = np.isnan(zbw)
            tegas = bool(bawah.get("tegas"))
            alasan = np.where((alasan == 0) & kosong, 1 if tegas else 2, alasan)
            alasan = np.where((alasan == 0) & ~kosong & (zz < zbw), 2, alasan)
        nOut["ext"] += int(np.count_nonzero(alasan == 1))
        nOut["surf"] += int(np.count_nonzero(alasan == 2))
        hidup[k[alasan != 0]] = False

    # 5. batas DTM tambahan (bisa beberapa; di JS yang pertama mengenai langsung memutus)
    daftar_sx = o.get("sx") or []
    if daftar_sx:
        k = np.flatnonzero(hidup)
        if k.size:
            alasan = np.zeros(k.size, dtype=np.int64)
            zz = Z[k]
            for q in daftar_sx:
                pertama, balik, _ = _wakil(xl[k], yl[k])
                lo, hi = Tin(q["tin"]).nilai(X[k][pertama], Y[k][pertama])
                LO, HI = lo[balik], hi[balik]
                kosong = np.isnan(HI)
                alasan = np.where((alasan == 0) & kosong, 1, alasan)
                if (q.get("side") or "below") == "above":
                    lewat = ~kosong & (zz <= LO)
                else:
                    lewat = ~kosong & (zz >= HI)
                alasan = np.where((alasan == 0) & lewat, 2, alasan)
            nOut["ext"] += int(np.count_nonzero(alasan == 1))
            nOut["surf"] += int(np.count_nonzero(alasan == 2))
            hidup[k[alasan != 0]] = False

    # 6. domain
    dom = o.get("dom") or {}
    mode = dom.get("mode") or "all"
    lab = "semua blok"
    if mode == "cat":
        C = cat.get(dom.get("attr"))
        if not C:
            raise ValueError("atribut kategori domain tidak ada")
        pilih = set(dom.get("pilih") or C["dict"])
        kode = np.asarray(C["codes"], dtype=np.int64)
        ikut = np.array([s in pilih for s in C["dict"]], dtype=bool)
        k = np.flatnonzero(hidup)
        kd = kode[k]
        baik = (kd != 65535) & ikut[np.clip(kd, 0, len(C["dict"]) - 1)]
        buang("dom", ~baik)
        lab = "%s = %s" % (dom.get("attr"), ", ".join(s for s in C["dict"] if s in pilih))
    elif mode == "wf":
        from . import subblok
        W = subblok.Mesh(dom["mesh"])
        k = np.flatnonzero(hidup)
        P = np.stack([xl[k], yl[k], Z[k]], axis=1)
        buang("dom", ~W.inside(P))
        lab = "di dalam wireframe %s" % (dom.get("name") or "")

    # 7. kadar tidak sah
    k = np.flatnonzero(hidup)
    g = G[k]
    buang("nan", ~np.isfinite(g) | (g <= NEG))

    # 8. SG
    sgCol = o.get("sgCol")
    sg_tetap = float(o.get("sg") or 2.6)
    k = np.flatnonzero(hidup)
    if sgCol and sgCol in num:
        v = np.asarray(num[sgCol], dtype=np.float64)[k]
        baik = np.isfinite(v) & (v > 0)
        if (o.get("sgZero") or "") == "zero":
            ganti = 0.0
        else:
            r = float(o.get("sgRep") or 0)
            ganti = r if r > 0 else sg_tetap
        SG = np.where(baik, v, ganti)
    else:
        SG = np.full(k.size, sg_tetap)
    buang("sg", ~(SG > 0))
    SG = SG[SG > 0]

    # 9. proporsi volume sub-blok (sb_frac)
    k = np.flatnonzero(hidup)
    nPart = 0
    if o.get("frac") is not False and "sb_frac" in num:
        fr = np.asarray(num["sb_frac"], dtype=np.float64)[k]
        fr = np.where(np.isfinite(fr) & (fr >= 0) & (fr <= 1), fr, 1.0)
        nol = fr <= 0
        buang("frac", nol)
        FR = fr[~nol]
        SG = SG[~nol]
        nPart = int(np.count_nonzero(FR < 0.999))
    else:
        FR = np.ones(k.size)

    # ---- agregasi ----
    k = np.flatnonzero(hidup)
    vol = SXb[k] * SYb[k] * SZb[k] * FR
    ton = SXb[k] * SYb[k] * SZb[k] * SG * FR
    grp = o.get("grp") or "none"
    bh = max(0.1, float(o.get("bh") or 5))
    br = float(o.get("bref") or 0)
    if grp == "bench":
        kunci = np.floor((Z[k] - br) / bh + 1e-9).astype(np.int64).astype(str)
    elif grp == "cat":
        C = cat.get(o.get("catAttr")) or {}
        if C:
            kode = np.asarray(C["codes"], dtype=np.int64)[k]
            nama = np.array(list(C["dict"]) + ["(kosong)"], dtype=object)
            kunci = nama[np.where(kode == 65535, len(C["dict"]), np.clip(kode, 0, len(C["dict"]) - 1))]
            kunci = np.asarray([str(s) for s in kunci])
        else:
            kunci = np.full(k.size, "Total")
    else:
        kunci = np.full(k.size, "Total")

    A = {a: np.asarray(num[a], dtype=np.float64)[k] for a in atts}
    gk = G[k]
    grup_unik, gidx = np.unique(kunci, return_inverse=True)
    rows = []
    for c in cuts:
        pakai = gk >= c
        Gd: Dict[str, Any] = {}
        if pakai.any():
            gi = gidx[pakai]
            cacah = np.bincount(gi, minlength=grup_unik.size)
            v = np.bincount(gi, weights=vol[pakai], minlength=grup_unik.size)
            t = np.bincount(gi, weights=ton[pakai], minlength=grup_unik.size)
            S2 = {}
            for a, va in A.items():
                av = va[pakai]
                sah = np.isfinite(av) & (av > NEG)
                tw = np.bincount(gi[sah], weights=(ton[pakai] * av)[sah], minlength=grup_unik.size)
                w = np.bincount(gi[sah], weights=ton[pakai][sah], minlength=grup_unik.size)
                S2[a] = (tw, w)
            for j, nama in enumerate(grup_unik):
                if cacah[j] == 0:
                    continue
                Gd[str(nama)] = {
                    "n": int(cacah[j]), "v": float(v[j]), "t": float(t[j]),
                    "s": {a: {"tw": float(S2[a][0][j]), "w": float(S2[a][1][j])}
                          for a in atts if S2[a][1][j] > 0 or S2[a][0][j] != 0},
                }
        rows.append({"c": c, "G": Gd})

    return {"ok": True, "rows": rows, "cuts": cuts, "atts": atts, "nb": int(k.size),
            "nOut": nOut, "nPart": nPart, "lab": lab, "grp": grp, "bh": bh, "br": br,
            "nTot": int(n), "ms": int(round((time.perf_counter() - t0) * 1000))}
