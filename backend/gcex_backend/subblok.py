# -*- coding: utf-8 -*-
"""Sub-blocking di batas solid & proporsi volume ore per blok (sb_frac) -- versi Python.

Padanan JavaScript: wfInside() di gcex_dh_base.html, lalu straddle() / SB.frac() / scan() di
web-src-dh/subblk_dh.js. Angkanya WAJIB sama; paritasnya diuji di backend/tests/test_subblok.py
terhadap keluaran JS asli yang dibekukan.

Kenapa dipindah ke Python: ini bagian paling berat di seluruh rangkaian. Satu blok perbatasan
diuji dengan 10^3 = 1.000 titik, dan sebuah model bisa punya puluhan ribu blok perbatasan --
puluhan juta uji "titik di dalam mesh". Di JavaScript tiap titik diuji satu per satu lewat
penafsir; di NumPy jutaan titik diuji dalam beberapa operasi larik. Di sinilah pemindahan
perhitungan benar-benar berbayar, bukan di kriging.

Cara ujinya sama persis dengan JS supaya angkanya tidak bergeser:
  - sinar vertikal ke atas (+Z): titik di dalam bila jumlah segitiga yang ditembus GANJIL
  - titik digeser 1,37e-6 / 2,71e-6 di X / Y supaya tidak jatuh tepat di sisi segitiga
  - segitiga dibucket ke kisi XY lebih dulu; satu titik hanya diuji terhadap segitiga di selnya
  - koordinat barisentrik; segitiga dengan determinan < 1e-12 dilewati
"""
from __future__ import annotations

import math
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

JX = 1.37e-6      # geseran X, sama dengan JS
JY = 2.71e-6      # geseran Y
MAXSEL = 2_000_000   # batas jumlah sel kisi, sama dengan JS (2e6)


class Mesh:
    """Mesh segitiga + kisi XY, padanan hasil wfInside(m).

    m: {x:[...], y:[...], z:[...], i:[...], j:[...], k:[...]} -- koordinat LOKAL (sudah
    dikurangi offset, seperti m._x/_y/_z sesudah mdLocal di JS) dan indeks simpul per segitiga.
    """

    def __init__(self, m: Dict[str, Any]) -> None:
        X = np.asarray(m["x"], dtype=np.float64)
        Y = np.asarray(m["y"], dtype=np.float64)
        Z = np.asarray(m["z"], dtype=np.float64)
        I = np.asarray(m["i"], dtype=np.int64)
        J = np.asarray(m["j"], dtype=np.int64)
        K = np.asarray(m["k"], dtype=np.int64)
        if not (I.size == J.size == K.size):
            raise ValueError("indeks segitiga tidak sama panjang")
        if I.size == 0 or X.size == 0:
            raise ValueError("mesh kosong")
        self.nt = int(I.size)
        self.nv = int(X.size)

        # ---- simpul per segitiga (disalin sekali; dipakai berulang) ----
        self.AX, self.AY, self.AZ = X[I], Y[I], Z[I]
        self.BX, self.BY, self.BZ = X[J], Y[J], Z[J]
        self.CX, self.CY, self.CZ = X[K], Y[K], Z[K]
        # determinan barisentrik per segitiga (tetap, tidak bergantung titik uji)
        self.den = ((self.BY - self.CY) * (self.AX - self.CX)
                    + (self.CX - self.BX) * (self.AY - self.CY))
        self.den_ok = np.abs(self.den) >= 1e-12

        # ---- kisi XY, rumus & urutan sama dengan JS ----
        self.x0, x1 = float(X.min()), float(X.max())
        self.y0, y1 = float(Y.min()), float(Y.max())
        cs = max(0.5, math.sqrt((x1 - self.x0) * (y1 - self.y0) / max(1, self.nt / 3)))
        nx = max(1, math.ceil((x1 - self.x0) / cs))
        ny = max(1, math.ceil((y1 - self.y0) / cs))
        while nx * ny > MAXSEL:
            cs *= 1.5
            nx = math.ceil((x1 - self.x0) / cs)
            ny = math.ceil((y1 - self.y0) / cs)
        self.cs, self.nx, self.ny = float(cs), int(nx), int(ny)

        # ---- bucket segitiga -> sel, disimpan gaya CSR (offset + daftar) ----
        gx0 = np.floor((np.minimum(np.minimum(self.AX, self.BX), self.CX) - self.x0) / cs).astype(np.int64)
        gx1 = np.floor((np.maximum(np.maximum(self.AX, self.BX), self.CX) - self.x0) / cs).astype(np.int64)
        gy0 = np.floor((np.minimum(np.minimum(self.AY, self.BY), self.CY) - self.y0) / cs).astype(np.int64)
        gy1 = np.floor((np.maximum(np.maximum(self.AY, self.BY), self.CY) - self.y0) / cs).astype(np.int64)
        gx0 = np.clip(gx0, 0, self.nx - 1); gx1 = np.clip(gx1, 0, self.nx - 1)
        gy0 = np.clip(gy0, 0, self.ny - 1); gy1 = np.clip(gy1, 0, self.ny - 1)
        lebar = (gx1 - gx0 + 1)
        tinggi = (gy1 - gy0 + 1)
        ulang = lebar * tinggi
        tri = np.repeat(np.arange(self.nt, dtype=np.int64), ulang)
        # posisi di dalam kotak masing-masing segitiga -> (gx, gy)
        pos = np.arange(ulang.sum(), dtype=np.int64) - np.repeat(np.cumsum(ulang) - ulang, ulang)
        lb = np.repeat(lebar, ulang)
        sel = (np.repeat(gy0, ulang) + pos // lb) * self.nx + (np.repeat(gx0, ulang) + pos % lb)
        urut = np.argsort(sel, kind="stable")
        self.sel_tri = tri[urut]
        self.sel_awal = np.searchsorted(sel[urut], np.arange(self.nx * self.ny + 1, dtype=np.int64))

        # ---- sisi terbuka (diagnosis "wireframe tertutup rapat?"), sama dengan JS ----
        e = np.concatenate([np.stack([I, J], 1), np.stack([J, K], 1), np.stack([K, I], 1)])
        e = np.sort(e, axis=1)
        _, hit = np.unique(e, axis=0, return_counts=True)
        self.ne = int(hit.size)
        self.open = int(np.count_nonzero(hit != 2))

        self.bb = (float(X.min()), float(X.max()), float(Y.min()), float(Y.max()),
                   float(Z.min()), float(Z.max()))

    # -----------------------------------------------------------------
    def tembusan(self, px: np.ndarray, py: np.ndarray):
        """Untuk tiap kolom vertikal (px, py): ketinggian semua segitiga yang ditembus sinar +Z.

        Mengembalikan (kid, zt): kid = indeks kolom, zt = ketinggian tembusan. Dipisah dari uji
        "di dalam?" karena di situlah penghematannya: satu kolom cuplikan blok berisi banyak
        ketinggian (10 pada cuplikan 10^3), dan semuanya bisa dijawab dari satu daftar tembusan
        ini. Kalau tiap titik diuji sendiri, segitiga yang sama diperiksa sepuluh kali.

        px, py sudah termasuk geseran JX / JY.
        """
        n = px.size
        kosong = (np.zeros(0, dtype=np.int64), np.zeros(0))
        if n == 0:
            return kosong
        gx = np.floor((px - self.x0) / self.cs).astype(np.int64)
        gy = np.floor((py - self.y0) / self.cs).astype(np.int64)
        di = (gx >= 0) & (gy >= 0) & (gx < self.nx) & (gy < self.ny)
        if not di.any():
            return kosong
        idx = np.flatnonzero(di)
        k = gy[idx] * self.nx + gx[idx]
        awal = self.sel_awal[k]
        cacah = self.sel_awal[k + 1] - awal              # jumlah segitiga di sel tiap kolom
        hidup = cacah > 0
        if not hidup.any():
            return kosong
        idx = idx[hidup]; awal = awal[hidup]; cacah = cacah[hidup]

        kum = np.cumsum(cacah)
        BATAS = 2_000_000                                # pasangan (kolom x segitiga) per potongan
        tepi = np.unique(np.concatenate(
            [[0], np.searchsorted(kum, np.arange(BATAS, int(kum[-1]), BATAS)) + 1, [idx.size]]))
        KID, ZT = [], []
        for a, b in zip(tepi[:-1], tepi[1:]):
            if b <= a:
                continue
            c = cacah[a:b]
            npas = int(c.sum())
            if npas == 0:
                continue
            pid = np.repeat(np.arange(a, b, dtype=np.int64), c)
            geser = np.arange(npas, dtype=np.int64) - np.repeat(np.cumsum(c) - c, c)
            T = self.sel_tri[np.repeat(awal[a:b], c) + geser]
            q = idx[pid]
            kena, zt = self._kena(px[q], py[q], T)
            if not kena.any():
                continue
            KID.append(idx[pid[kena]])
            ZT.append(zt[kena])
        if not KID:
            return kosong
        return np.concatenate(KID), np.concatenate(ZT)

    def _kena(self, px: np.ndarray, py: np.ndarray, T: np.ndarray):
        """Per pasangan (kolom, segitiga): apakah sinar vertikal jatuh di dalam segitiga, dan
        pada ketinggian berapa. Rumus barisentriknya sama dengan f() di wfInside, termasuk
        ambang determinan 1e-12."""
        ok = self.den_ok[T]
        # segitiga gepeng (determinan ~ 0) dilewati, sama dengan JS; penyebutnya diganti 1
        # supaya tidak ada pembagian nol -- pasangannya toh dibuang oleh topeng `ok`.
        den = np.where(ok, self.den[T], 1.0)
        cx = self.CX[T]; cy = self.CY[T]
        dx = px - cx
        dy = py - cy
        l1 = ((self.BY[T] - cy) * dx + (self.CX[T] - self.BX[T]) * dy) / den
        l2 = ((cy - self.AY[T]) * dx + (self.AX[T] - cx) * dy) / den
        l3 = 1.0 - l1 - l2
        kena = ok & (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if not kena.any():
            return kena, np.zeros(0)
        zt = l1 * self.AZ[T] + l2 * self.BZ[T] + l3 * self.CZ[T]
        return kena, zt

    def inside(self, P: np.ndarray) -> np.ndarray:
        """P: (n,3) koordinat lokal -> larik bool, True bila titik di dalam mesh."""
        n = P.shape[0]
        if n == 0:
            return np.zeros(0, dtype=bool)
        kid, zt = self.tembusan(P[:, 0] + JX, P[:, 1] + JY)
        out = np.zeros(n, dtype=bool)
        if kid.size == 0:
            return out
        atas = zt > P[kid, 2]
        if not atas.any():
            return out
        jml = np.bincount(kid[atas], minlength=n)
        return (jml & 1) == 1

    def inside_kolom(self, px: np.ndarray, py: np.ndarray, Z: np.ndarray) -> np.ndarray:
        """px, py: (nk,) kolom vertikal. Z: (nk, nz) ketinggian yang diuji di tiap kolom.
        Hasil: (nk, nz) bool. Segitiga diperiksa SEKALI per kolom, lalu dipakai untuk semua nz."""
        nk = px.size
        nz = Z.shape[1]
        out = np.zeros((nk, nz), dtype=bool)
        if nk == 0 or nz == 0:
            return out
        kid, zt = self.tembusan(px + JX, py + JY)
        if kid.size == 0:
            return out
        # jumlah tembusan di atas tiap ketinggian; ganjil = di dalam
        jml = np.zeros((nk, nz), dtype=np.int64)
        for m in range(nz):
            atas = zt > Z[kid, m]
            if atas.any():
                jml[:, m] = np.bincount(kid[atas], minlength=nk)
        return (jml & 1) == 1


class Solid:
    """Satu solid domain: mesh + kotak pembatas (bb dipakai untuk melewati solid yang jauh)."""

    def __init__(self, d: Dict[str, Any]) -> None:
        self.name = d.get("name") or ""
        self.mesh = Mesh(d["mesh"] if "mesh" in d else d)
        self.bb = list(d.get("bb") or self.mesh.bb)


def _dalam(solids: Sequence[Solid], P: np.ndarray, aktif: Optional[Sequence[int]] = None) -> np.ndarray:
    """True bila titik berada di dalam SALAH SATU solid (sama dengan perulangan `ins` di JS)."""
    out = np.zeros(P.shape[0], dtype=bool)
    daftar = range(len(solids)) if aktif is None else aktif
    for q in daftar:
        sisa = np.flatnonzero(~out)
        if sisa.size == 0:
            break
        out[sisa] = solids[q].mesh.inside(P[sisa])
    return out


def _dalam_kolom(solids: Sequence[Solid], px: np.ndarray, py: np.ndarray,
                 Z: np.ndarray) -> np.ndarray:
    """True bila titik (px, py, Z[:, m]) ada di dalam SALAH SATU solid. Segitiga diperiksa sekali
    per kolom vertikal per solid, bukan sekali per titik."""
    out = np.zeros(Z.shape, dtype=bool)
    for q in range(len(solids)):
        if out.all():
            break
        out |= solids[q].mesh.inside_kolom(px, py, Z)
    return out


def _aktif(solids: Sequence[Solid], cx: float, cy: float, cz: float,
           hx: float, hy: float, hz: float) -> List[int]:
    """Solid yang kotak pembatasnya bersinggungan dengan kotak blok (prafilter, sama dengan JS)."""
    a = []
    for q, s in enumerate(solids):
        b = s.bb
        if (cx + hx < b[0] or cx - hx > b[1] or cy + hy < b[2] or cy - hy > b[3]
                or cz + hz < b[4] or cz - hz > b[5]):
            continue
        a.append(q)
    return a


def _kisi27(cx: np.ndarray, cy: np.ndarray, cz: np.ndarray,
            hx: np.ndarray, hy: np.ndarray, hz: np.ndarray) -> np.ndarray:
    """27 titik uji per blok (kisi 3x3x3 pada +-0,98 setengah ukuran) -> (n, 27, 3).
    Faktor 0,98 dan urutannya mengikuti straddle() di JS."""
    o = np.array([-1.0, 0.0, 1.0])
    ox, oy, oz = np.meshgrid(o, o, o, indexing="ij")
    ox = ox.ravel(); oy = oy.ravel(); oz = oz.ravel()
    X = cx[:, None] + ox[None, :] * hx[:, None] * 0.98
    Y = cy[:, None] + oy[None, :] * hy[:, None] * 0.98
    Z = cz[:, None] + oz[None, :] * hz[:, None] * 0.98
    return np.stack([X, Y, Z], axis=2)


def straddle(solids: Sequence[Solid], cx: np.ndarray, cy: np.ndarray, cz: np.ndarray,
             sx: np.ndarray, sy: np.ndarray, sz: np.ndarray) -> np.ndarray:
    """0 = seluruhnya di luar, 1 = seluruhnya di dalam, 2 = menyeberang batas. Per blok."""
    n = cx.size
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    hasil = np.zeros(n, dtype=np.int64)
    if n == 0:
        return hasil
    # blok yang tidak bersinggungan dengan satu solid pun langsung 0 (prafilter kotak pembatas)
    bbs = np.array([s.bb for s in solids], dtype=np.float64)       # (ns, 6)
    singgung = ((cx[:, None] + hx[:, None] >= bbs[None, :, 0])
                & (cx[:, None] - hx[:, None] <= bbs[None, :, 1])
                & (cy[:, None] + hy[:, None] >= bbs[None, :, 2])
                & (cy[:, None] - hy[:, None] <= bbs[None, :, 3])
                & (cz[:, None] + hz[:, None] >= bbs[None, :, 4])
                & (cz[:, None] - hz[:, None] <= bbs[None, :, 5]))
    ada = singgung.any(axis=1)
    bi = np.flatnonzero(ada)
    if bi.size == 0:
        return hasil
    # 27 titik uji = 9 kolom (x,y) x 3 ketinggian; kolomnya diperiksa sekali saja
    o = np.array([-1.0, 0.0, 1.0])
    kx, ky = np.meshgrid(o, o, indexing="ij")
    kx = kx.ravel(); ky = ky.ravel()                               # 9 kolom
    PX = (cx[bi][:, None] + kx[None, :] * hx[bi][:, None] * 0.98).ravel()
    PY = (cy[bi][:, None] + ky[None, :] * hy[bi][:, None] * 0.98).ravel()
    ZB = cz[bi][:, None] + o[None, :] * hz[bi][:, None] * 0.98     # (nb, 3)
    Z = np.repeat(ZB, 9, axis=0)                                   # (nb*9, 3)
    masuk = np.zeros(Z.shape, dtype=bool)
    # per solid: hanya kolom dari blok yang bersinggungan dengan solid itu yang diuji
    for q in range(len(solids)):
        pakai = np.repeat(singgung[bi, q], 9)
        baris = np.flatnonzero(pakai & ~masuk.all(axis=1))
        if baris.size == 0:
            continue
        masuk[baris] |= solids[q].mesh.inside_kolom(PX[baris], PY[baris], Z[baris])
    nIn = masuk.reshape(bi.size, 27).sum(axis=1)
    hasil[bi] = np.where(nIn == 0, 0, np.where(nIn == 27, 1, 2))
    return hasil


def frac(solids: Sequence[Solid], cx: np.ndarray, cy: np.ndarray, cz: np.ndarray,
         sx: np.ndarray, sy: np.ndarray, sz: np.ndarray, nF: int = 10) -> Dict[str, Any]:
    """Proporsi volume tiap blok yang berada di dalam solid (atribut sb_frac, 0..1).

    Blok seluruhnya di luar -> 0, seluruhnya di dalam -> 1, menyeberang -> dicuplik N^3 titik
    tengah sel (bawaan 10^3 = 1.000 titik), sama dengan SB.frac di JS.
    """
    N = max(4, min(16, int(round(nF or 10))))
    n = cx.size
    F = np.zeros(n, dtype=np.float64)
    s = straddle(solids, cx, cy, cz, sx, sy, sz)
    F[s == 1] = 1.0
    tepi = np.flatnonzero(s == 2)
    nPart = int(tepi.size)
    if nPart:
        o = (2 * np.arange(N) + 1) / N - 1.0                       # titik tengah sel: -1..1
        kx, ky = np.meshgrid(o, o, indexing="ij")
        kx = kx.ravel(); ky = ky.ravel()                            # N^2 kolom per blok
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        # blok tepi dikerjakan berkelompok supaya memori terjaga (N^2 kolom per blok)
        per = max(1, int(200_000 // (N * N)))
        for a0 in range(0, tepi.size, per):
            bi = tepi[a0:a0 + per]
            PX = (cx[bi][:, None] + kx[None, :] * hx[bi][:, None]).ravel()
            PY = (cy[bi][:, None] + ky[None, :] * hy[bi][:, None]).ravel()
            ZB = cz[bi][:, None] + o[None, :] * hz[bi][:, None]     # (nb, N)
            Z = np.repeat(ZB, N * N, axis=0)                         # (nb*N^2, N)
            masuk = _dalam_kolom(solids, PX, PY, Z)                 # (nb*N^2, N)
            F[bi] = masuk.reshape(bi.size, -1).sum(axis=1) / float(N * N * N)
    return {"F": F, "N": N, "nPart": nPart,
            "nFull": int(np.count_nonzero(s == 1)), "nNol": int(np.count_nonzero(s == 0))}


def pecah(solids: Sequence[Solid], blok: Dict[str, np.ndarray], lv: int,
          lim: Sequence[float], cap: int = 4_000_000) -> Dict[str, Any]:
    """Pecah blok yang menyeberangi batas solid jadi 2 x 2 x 2, berulang sampai `lv` tingkat.

    Blok yang ukurannya sudah mencapai batas minimum `lim` tidak dipecah lagi (sub-blok bawaan
    Surpac dihormati). Pemecahan 2x2x2 serentak di ketiga sumbu dipertahankan supaya blok anak
    tetap jatuh di kisi octree .mdl. Semua blok pada satu tingkat diuji sekaligus (beda dengan
    JS yang memakai tumpukan per blok), hasilnya sama karena ujinya per blok dan tidak saling
    bergantung; urutan keluaran diurutkan ulang menurut indeks blok asal agar tetap tertib.
    """
    x = np.asarray(blok["x"], dtype=np.float64)
    y = np.asarray(blok["y"], dtype=np.float64)
    z = np.asarray(blok["z"], dtype=np.float64)
    sx = np.asarray(blok["sx"], dtype=np.float64)
    sy = np.asarray(blok["sy"], dtype=np.float64)
    sz = np.asarray(blok["sz"], dtype=np.float64)
    src = np.arange(x.size, dtype=np.int64)
    nAsal = int(x.size)
    nSplit = nSudah = 0
    str_asal = np.zeros(nAsal, dtype=bool)
    simpan: List[Tuple[np.ndarray, ...]] = []

    # blok tanpa ukuran dibiarkan apa adanya (sama dengan JS)
    nol = ~(sx > 0)
    if nol.any():
        k = np.flatnonzero(nol)
        simpan.append((x[k], y[k], z[k], sx[k], sy[k], sz[k], src[k]))
        hidup = np.flatnonzero(~nol)
        x, y, z, sx, sy, sz, src = (v[hidup] for v in (x, y, z, sx, sy, sz, src))

    for _ in range(int(max(1, lv)) + 1):
        if x.size == 0:
            break
        s = straddle(solids, x, y, z, sx, sy, sz)
        tetap = s != 2
        if tetap.any():
            k = np.flatnonzero(tetap)
            simpan.append((x[k], y[k], z[k], sx[k], sy[k], sz[k], src[k]))
        ts = np.flatnonzero(~tetap)
        if ts.size == 0:
            break
        str_asal[src[ts]] = True
        # anak hanya dibuat bila ukurannya masih >= batas minimum pada KETIGA sumbu
        bisa = ((sx[ts] / 2 >= lim[0] * (1 - 1e-9)) & (sy[ts] / 2 >= lim[1] * (1 - 1e-9))
                & (sz[ts] / 2 >= lim[2] * (1 - 1e-9)))
        mandek = ts[~bisa]
        if mandek.size:
            nSudah += int(mandek.size)
            simpan.append((x[mandek], y[mandek], z[mandek], sx[mandek], sy[mandek], sz[mandek], src[mandek]))
        ts = ts[bisa]
        if ts.size == 0:
            break
        nSplit += int(ts.size)
        hx, hy, hz = sx[ts] / 2, sy[ts] / 2, sz[ts] / 2
        t = np.array([-1.0, 1.0])
        ax, ay, az = np.meshgrid(t, t, t, indexing="ij")
        ax = ax.ravel(); ay = ay.ravel(); az = az.ravel()
        x = (x[ts][:, None] + ax[None, :] * hx[:, None] / 2).ravel()
        y = (y[ts][:, None] + ay[None, :] * hy[:, None] / 2).ravel()
        z = (z[ts][:, None] + az[None, :] * hz[:, None] / 2).ravel()
        sx = np.repeat(hx, 8); sy = np.repeat(hy, 8); sz = np.repeat(hz, 8)
        src = np.repeat(src[ts], 8)
        if sum(v[0].size for v in simpan) + x.size > cap:
            raise ValueError("hasil melebihi %d blok: kurangi tingkat pecah" % cap)

    X = np.concatenate([v[0] for v in simpan]) if simpan else np.zeros(0)
    Y = np.concatenate([v[1] for v in simpan]) if simpan else np.zeros(0)
    Z = np.concatenate([v[2] for v in simpan]) if simpan else np.zeros(0)
    SX = np.concatenate([v[3] for v in simpan]) if simpan else np.zeros(0)
    SY = np.concatenate([v[4] for v in simpan]) if simpan else np.zeros(0)
    SZ = np.concatenate([v[5] for v in simpan]) if simpan else np.zeros(0)
    SRC = np.concatenate([v[6] for v in simpan]).astype(np.int64) if simpan else np.zeros(0, np.int64)
    urut = np.argsort(SRC, kind="stable")
    return {"x": X[urut], "y": Y[urut], "z": Z[urut], "sx": SX[urut], "sy": SY[urut],
            "sz": SZ[urut], "src": SRC[urut], "n": int(X.size), "nAsal": nAsal,
            "nSplit": nSplit, "nSudah": nSudah, "nStr": int(np.count_nonzero(str_asal))}


def _inti(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Satu proses: hitung seluruh blok yang diberikan.

    payload: {solids:[{name, mesh:{x,y,z,i,j,k}, bb?}], blocks:{x,y,z,sx,sy,sz},
              mode:'frac'|'straddle'|'pecah', nF?, lv?, lim?}
    hasil  : frac     -> {F, N, nPart, nFull, nNol, vol}
             straddle -> {s, n0, n1, n2}
             pecah    -> {x,y,z,sx,sy,sz,src,n,nAsal,nSplit,nSudah,nStr}
    """
    t0 = time.perf_counter()
    S = payload.get("solids") or []
    if not S:
        raise ValueError("belum ada solid domain")
    solids = [Solid(d) for d in S]
    B = payload.get("blocks") or {}
    cx = np.asarray(B.get("x") or [], dtype=np.float64)
    cy = np.asarray(B.get("y") or [], dtype=np.float64)
    cz = np.asarray(B.get("z") or [], dtype=np.float64)
    sx = np.asarray(B.get("sx") or [], dtype=np.float64)
    sy = np.asarray(B.get("sy") or [], dtype=np.float64)
    sz = np.asarray(B.get("sz") or [], dtype=np.float64)
    if not (cx.size == cy.size == cz.size == sx.size == sy.size == sz.size):
        raise ValueError("panjang larik blok tidak sama")
    mode = (payload.get("mode") or "frac").lower()

    if mode == "straddle":
        s = straddle(solids, cx, cy, cz, sx, sy, sz)
        o: Dict[str, Any] = {"s": s.tolist(),
                             "n0": int(np.count_nonzero(s == 0)),
                             "n1": int(np.count_nonzero(s == 1)),
                             "n2": int(np.count_nonzero(s == 2))}
    elif mode == "pecah":
        lim = payload.get("lim")
        if not lim:
            lv = int(payload.get("lv") or 1)
            sd = payload.get("sd") or [float(sx[0]), float(sy[0]), float(sz[0])]
            lim = [sd[0] / 2 ** lv, sd[1] / 2 ** lv, sd[2] / 2 ** lv]
        r = pecah(solids, {"x": cx, "y": cy, "z": cz, "sx": sx, "sy": sy, "sz": sz},
                  int(payload.get("lv") or 1), [float(v) for v in lim])
        o = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in r.items()}
    else:
        r = frac(solids, cx, cy, cz, sx, sy, sz, int(payload.get("nF") or 10))
        F = r["F"]
        o = {"F": F.tolist(), "N": r["N"], "nPart": r["nPart"], "nFull": r["nFull"],
             "nNol": r["nNol"], "vol": float(np.sum(sx * sy * sz * F))}

    o["ok"] = True
    o["ms"] = int(round((time.perf_counter() - t0) * 1000))
    o["terbuka"] = [s.mesh.open for s in solids]
    return o


# ---------------------------------------------------------------------------
# Pembagian ke beberapa inti CPU
#
# Proporsi satu blok tidak bergantung pada blok lain -- yang dipakai hanya mesh solid, yang sama
# untuk semua. Jadi daftar blok boleh dipotong dan dikerjakan beberapa proses sekaligus, dan
# angkanya wajib tetap sama persis (diuji di test_subblok.py). Mode 'pecah' TIDAK dibagi karena
# keluarannya berurut menurut blok asal dan jumlahnya berubah-ubah per blok.
# ---------------------------------------------------------------------------

_BERSAMA: Dict[str, Any] = {}


def _siap_pekerja(dasar: Dict[str, Any]) -> None:
    """Dipanggil sekali per proses: mesh solid dibangun sekali, bukan per potongan blok."""
    _BERSAMA["dasar"] = dasar


def _kerja(args: Tuple[int, int]) -> Tuple[int, Dict[str, Any]]:
    i0, i1 = args
    d = _BERSAMA["dasar"]
    B = d["blocks"]
    p = dict(d)
    p["blocks"] = {k: list(B[k])[i0:i1] for k in ("x", "y", "z", "sx", "sy", "sz")}
    return i0, _inti(p)


def _jumlah_pekerja(minta: Any, nb: int) -> int:
    inti = os.cpu_count() or 1
    if minta in (None, 0, "auto", "otomatis"):
        w = min(inti, 8)
    else:
        try:
            w = int(minta)
        except (TypeError, ValueError):
            w = 1
    # pembagian baru berbayar bila bloknya banyak: mesh solid dibangun ulang di tiap pekerja
    return max(1, min(w, inti, nb // 5000 if nb >= 10000 else 1))


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Titik masuk HTTP.

    payload: {solids:[{name, mesh:{x,y,z,i,j,k}, bb?}], blocks:{x,y,z,sx,sy,sz},
              mode:'frac'|'straddle'|'pecah', nF?, lv?, lim?, workers?}
    hasil  : frac     -> {F, N, nPart, nFull, nNol, vol}
             straddle -> {s, n0, n1, n2}
             pecah    -> {x,y,z,sx,sy,sz,src,n,nAsal,nSplit,nSudah,nStr}
    """
    mode = (payload.get("mode") or "frac").lower()
    B = payload.get("blocks") or {}
    nb = len(B.get("x") or [])
    w = 1 if mode == "pecah" else _jumlah_pekerja(payload.get("workers"), nb)
    if w <= 1:
        return _inti(payload)

    t0 = time.perf_counter()
    potong = [(round(nb * i / w), round(nb * (i + 1) / w)) for i in range(w)]
    dasar = {k: v for k, v in payload.items() if k != "workers"}
    try:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=w, initializer=_siap_pekerja, initargs=(dasar,)) as ex:
            bagian = sorted(ex.map(_kerja, [(a, b) for a, b in potong if b > a]))
    except Exception:
        # pembagian proses bisa gagal di lingkungan tertentu: angka lebih penting daripada
        # kecepatan, jadi kembali ke satu proses.
        return _inti(payload)

    o: Dict[str, Any] = {"ok": True}
    if mode == "straddle":
        o["s"] = [v for _, r in bagian for v in r["s"]]
        for k in ("n0", "n1", "n2"):
            o[k] = sum(r[k] for _, r in bagian)
    else:
        o["F"] = [v for _, r in bagian for v in r["F"]]
        o["N"] = bagian[0][1]["N"]
        for k in ("nPart", "nFull", "nNol"):
            o[k] = sum(r[k] for _, r in bagian)
        o["vol"] = float(sum(r["vol"] for _, r in bagian))
    o["terbuka"] = bagian[0][1]["terbuka"]
    o["ms"] = int(round((time.perf_counter() - t0) * 1000))
    o["workers"] = w
    return o
