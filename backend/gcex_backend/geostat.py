# -*- coding: utf-8 -*-
"""Geostatistik di Python (NumPy): variogram eksperimental + fitting model.

Tahap pertama pemindahan perhitungan dari JavaScript ke Python. Yang dipindah di sini adalah
bagian paling berat dan paling murni hitungan: pasangan komposit untuk variogram eksperimental
(36 arah di bidang sayatan, omni, dan downhole) beserta pencocokan model sferis bersarangnya.

ATURAN YANG DIPEGANG DI SELURUH PEMINDAHAN INI
  Hasilnya harus SAMA dengan jalur JavaScript yang sudah dipakai dan sudah tercetak angkanya di
  buku tutorial. Karena itu fungsi di bawah ini adalah terjemahan harfiah dari gsVario / gsFitAuto
  di gcex_dh_base.html -- termasuk hal-hal yang kalau "diperbaiki" akan mengubah angka:
    * urutan penjumlahan pasangan per lag (gamma = sum(dv^2) / (2n), h = sum(h)/n),
    * aturan toleransi lag: k = round(h/lag), 1 <= k <= nl, |h - k*lag| <= lt*lag,
    * jendela sudut: jl = ceil((th-at)/5), jh = floor((th+at)/5), lalu bandwidth h*sin(da) <= bw,
    * deret kandidat pada fitting (lgrid 36/40/26 titik) dan langkah f yang dijumlahkan
      (0 += 0.025 dan 0.1 += 0.05) -- bukan np.arange, supaya galat pembulatannya sama.
  Yang berbeda hanyalah caranya dihitung: perulangan pasangan O(n^2) di JS menjadi operasi
  vektor NumPy per blok baris, sehingga 12 juta pasangan selesai dalam hitungan ratusan milidetik
  tanpa membekukan tampilan.

Lampiran uji: backend/tests/test_geostat.py (invarian + kasus yang diketahui jawabannya) dan
tools/uji/paritas_geostat.py (membandingkan angka Python dengan angka JS pada data latihan).
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

ND = 36          # jumlah arah di bidang sayatan (kelipatan 5 derajat, 0-175)
DBIN = 5.0       # lebar satu arah (derajat)


# ---------------------------------------------------------------- variogram eksperimental
def _fin(gsum: np.ndarray, hsum: np.ndarray, cnt: np.ndarray, m: int) -> List[Dict[str, float]]:
    """Samakan dengan fin() di JS: lag tanpa pasangan dibuang, gamma = sum/(2n), h = rata-rata."""
    out = []
    for q in range(1, m + 1):
        if cnt[q] > 0:
            out.append({"h": float(hsum[q] / cnt[q]), "g": float(gsum[q] / (2.0 * cnt[q])), "n": int(cnt[q])})
    return out


def vario(C: Sequence[Dict[str, Any]], z: Sequence[float], P: Dict[str, Any],
          u: Sequence[float], w: Sequence[float]) -> Dict[str, Any]:
    """Variogram eksperimental: 36 arah (D), omni (O), dan downhole (DH).

    C  : komposit [{x,y,z,id,d}, ...] dalam koordinat LOKAL (sama dengan yang dipakai JS)
    z  : nilai yang sudah ditransformasi (none / log / nscore) -- transformasinya tetap di pemanggil
    P  : {lag, nl, lt, at, bw, dlag, dnl}
    u,w: sumbu bidang sayatan (vektor satuan), sama dengan S.g.u / S.g.w di JS
    """
    n = len(C)
    nl = int(P["nl"])
    dnl = int(P["dnl"])
    lag = float(P["lag"])
    lt = float(P["lt"])
    at = float(P["at"])
    bw = float(P["bw"])
    dlag = float(P["dlag"])

    X = np.array([c["x"] for c in C], dtype=np.float64)
    Y = np.array([c["y"] for c in C], dtype=np.float64)
    Z = np.array([c["z"] for c in C], dtype=np.float64)
    V = np.asarray(z, dtype=np.float64)
    D = np.array([c.get("d", 0.0) for c in C], dtype=np.float64)
    # id hole -> bilangan, supaya perbandingan "satu lubang" bisa divektorkan
    peta: Dict[Any, int] = {}
    H = np.empty(n, dtype=np.int64)
    for i, c in enumerate(C):
        k = c.get("id")
        if k not in peta:
            peta[k] = len(peta)
        H[i] = peta[k]

    U = np.array([float(u[0]), float(u[1]), float(u[2])], dtype=np.float64)
    W = np.array([float(w[0]), float(w[1]), float(w[2])], dtype=np.float64)

    gD = np.zeros((ND, nl + 1)); hD = np.zeros((ND, nl + 1)); nD = np.zeros((ND, nl + 1))
    gO = np.zeros(nl + 1); hO = np.zeros(nl + 1); nO = np.zeros(nl + 1)
    gH = np.zeros(dnl + 1); hH = np.zeros(dnl + 1); nH = np.zeros(dnl + 1)

    # Proyeksi ke sumbu sayatan dihitung SEKALI per komposit: hu(i,j) = su[j]-su[i].
    # Secara matematis sama dengan dx*u0+dy*u1+dz*u2 di JS (hasil akhir bisa beda di bit terakhir,
    # dan karena gamma/h adalah rata-rata, selisihnya jauh di bawah 1e-12 relatif -- dijaga oleh
    # uji paritas), tetapi membuat tiap pasangan hanya perlu 2 pengurangan, bukan 9 operasi.
    SU = X * U[0] + Y * U[1] + Z * U[2]
    SW = X * W[0] + Y * W[1] + Z * W[2]

    jmax = int(math.ceil(at / DBIN))                      # jendela sudut maksimum (bin)
    blok = 512                                            # baris per blok: cukup kecil agar muat cache
    t0 = time.perf_counter()
    nlin = ND * (nl + 1)

    # Batas jarak yang mungkin masuk lag mana pun: dipakai sebagai saringan awal pada jarak
    # KUADRAT, supaya akar dan selisih nilai hanya dihitung untuk pasangan yang benar-benar dipakai.
    d_lo = max(0.0, lag * (1.0 - lt))
    d_hi = lag * nl + lt * lag
    lo2, hi2 = d_lo * d_lo, d_hi * d_hi

    for i0 in range(0, n, blok):
        i1 = min(n, i0 + blok)
        ii = np.arange(i0, i1)
        kol = np.arange(i0, n)
        hu = SU[i0:][None, :] - SU[ii, None]
        hw = SW[i0:][None, :] - SW[ii, None]
        hd2 = hu * hu + hw * hw
        awal = (kol[None, :] > ii[:, None]) & (hd2 >= max(lo2, 1e-12)) & (hd2 <= hi2)

        # ---- downhole: hanya pasangan di lubang yang sama (jumlahnya sedikit; dihitung sendiri)
        sama = (kol[None, :] > ii[:, None]) & (H[i0:][None, :] == H[ii, None])
        if sama.any():
            pi, pj = np.nonzero(sama)
            dd = np.abs(D[ii[pi]] - D[i0 + pj])
            kd = np.rint(dd / dlag)
            ok = (kd >= 1) & (kd <= dnl) & (np.abs(dd - kd * dlag) <= lt * dlag)
            if ok.any():
                ki = kd[ok].astype(np.int64)
                dvh = V[ii[pi[ok]]] - V[i0 + pj[ok]]
                gH += np.bincount(ki, weights=dvh * dvh, minlength=dnl + 1)[:dnl + 1]
                hH += np.bincount(ki, weights=dd[ok], minlength=dnl + 1)[:dnl + 1]
                nH += np.bincount(ki, minlength=dnl + 1)[:dnl + 1]

        if not awal.any():
            continue
        pi, pj = np.nonzero(awal)
        hh = np.sqrt(hd2[pi, pj])
        k = np.rint(hh / lag)
        sah = (k >= 1) & (k <= nl) & (np.abs(hh - k * lag) <= lt * lag)
        if not sah.any():
            continue
        pi, pj = pi[sah], pj[sah]
        hh = hh[sah]
        kk = k[sah].astype(np.int64)
        dv = V[ii[pi]] - V[i0 + pj]
        gg = dv * dv

        # ---- omni
        gO += np.bincount(kk, weights=gg, minlength=nl + 1)[:nl + 1]
        hO += np.bincount(kk, weights=hh, minlength=nl + 1)[:nl + 1]
        nO += np.bincount(kk, minlength=nl + 1)[:nl + 1]

        # ---- 36 arah.
        # Di JS tiap pasangan diuji ke setiap arah dalam jendela sudut, lalu dibuang bila
        # h*sin(da) > bandwidth. Karena da tumbuh menjauh dari arah pasangan itu, arah yang
        # LOLOS selalu satu rentang menerus. Jadi rentangnya dihitung sekali per pasangan:
        # da maksimum = at, dan bila h > bw juga dibatasi asin(bw/h). Hasilnya identik dengan JS
        # (dijaga uji paritas), tanpa 11 kali lintasan bertopeng + sinus per arah.
        th = np.degrees(np.arctan2(hw[pi, pj], hu[pi, pj]))
        th = np.where(th < 0, th + 180.0, th)
        th = np.where(th >= 180.0, th - 180.0, th)
        dmax = np.full(th.shape, at)
        jauh = hh > bw
        if jauh.any():
            dmax[jauh] = np.minimum(at, np.degrees(np.arcsin(np.minimum(1.0, bw / hh[jauh]))))
        jl = np.ceil((th - dmax) / DBIN)
        jh = np.floor((th + dmax) / DBIN)
        cnt = (jh - jl + 1).astype(np.int64)
        np.maximum(cnt, 0, out=cnt)
        tot = int(cnt.sum())
        if tot:
            idx = np.repeat(np.arange(cnt.size), cnt)
            mulai = np.repeat(jl, cnt)
            urut = np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt)
            bq = ((mulai + urut).astype(np.int64) % ND + ND) % ND
            lin = bq * (nl + 1) + kk[idx]
            gD += np.bincount(lin, weights=gg[idx], minlength=nlin)[:nlin].reshape(ND, nl + 1)
            hD += np.bincount(lin, weights=hh[idx], minlength=nlin)[:nlin].reshape(ND, nl + 1)
            nD += np.bincount(lin, minlength=nlin)[:nlin].reshape(ND, nl + 1)

    return {
        "D": [_fin(gD[j], hD[j], nD[j], nl) for j in range(ND)],
        "O": _fin(gO, hO, nO, nl),
        "DH": _fin(gH, hH, nH, dnl),
        "ms": int(round((time.perf_counter() - t0) * 1000)),
        "npair": int(nO.sum()),
    }


# ---------------------------------------------------------------- model & pencocokan
def sph(h: float, a: float) -> float:
    if a <= 0 or h >= a:
        return 1.0
    r = h / a
    return 1.5 * r - 0.5 * r * r * r


def gam(h: float, c0: float, cs: Sequence[float], a_s: Sequence[float]) -> float:
    if h <= 0:
        return 0.0
    g = c0
    for i in range(len(cs)):
        g += cs[i] * sph(h, a_s[i])
    return g


def lgrid(lo: float, hi: float, m: int) -> List[float]:
    return [lo * math.pow(hi / lo, i / (m - 1)) for i in range(m)]


def sse(E: Sequence[Dict[str, float]], c0: float, cs: Sequence[float], a_s: Sequence[float], minP: int) -> float:
    s = 0.0
    for e in E:
        if e["n"] < minP:
            continue
        m = gam(e["h"], c0, cs, a_s)
        s += e["n"] * (e["g"] - m) * (e["g"] - m) / max(m * m, 1e-12)
    return s


def n_valid(E: Sequence[Dict[str, float]], minP: int) -> int:
    return sum(1 for e in E if e["n"] >= minP)


def h1(E: Sequence[Dict[str, float]], minP: int) -> float:
    for e in E:
        if e["n"] >= minP:
            return e["h"]
    return float("nan")


def fit_r(E: Sequence[Dict[str, float]], c0: float, cs: Sequence[float], minP: int,
          B: Sequence[float]) -> Optional[List[float]]:
    if n_valid(E, minP) < 2:
        return None
    G1 = lgrid(B[0], B[1], 36)
    best = 1e300
    ba: Optional[List[float]] = None
    hf = h1(E, minP)

    def clip(r: List[float]) -> List[float]:
        return [hf if (hf == hf and a < hf) else a for a in r]

    if len(cs) == 1 or not (cs[1] > 0):
        for a in G1:
            e = sse(E, c0, [cs[0]], [a], minP)
            if e < best:
                best = e
                ba = [a]
        if ba and len(cs) > 1:
            ba.append(ba[0])
        return clip(ba) if ba else ba
    for i in range(len(G1)):
        for j in range(i, len(G1)):
            e = sse(E, c0, cs, [G1[i], G1[j]], minP)
            if e < best:
                best = e
                ba = [G1[i], G1[j]]
    return clip(ba) if ba else ba


def fit_nug(E: Sequence[Dict[str, float]], sill: float, minP: int, B: Sequence[float]) -> Optional[float]:
    if n_valid(E, minP) < 3:
        return None
    G1 = lgrid(B[0], B[1], 40)
    best = 1e300
    bc: Optional[float] = None
    f = 0.0
    while f <= 0.951:                      # dijumlahkan seperti di JS, bukan arange
        for a in G1:
            e = sse(E, f * sill, [sill - f * sill], [a], minP)
            if e < best:
                best = e
                bc = f * sill
        f += 0.025
    return bc


def fit_split(E: Sequence[Dict[str, float]], c0: float, sill: float, minP: int,
              B: Sequence[float]) -> Optional[Dict[str, Any]]:
    r = sill - c0
    best = 1e300
    bb = None
    G1 = lgrid(B[0], B[1], 26)
    if n_valid(E, minP) < 4:
        return None
    f = 0.1
    while f <= 0.901:
        for i in range(len(G1)):
            for j in range(i + 1, len(G1)):
                cs = [f * r, (1 - f) * r]
                e = sse(E, c0, cs, [G1[i], G1[j]], minP)
                if e < best:
                    best = e
                    bb = {"c": cs, "a": [G1[i], G1[j]], "e": e}
        f += 0.05
    return bb


def fit_auto(E: Dict[str, Any], sill: float, P: Dict[str, Any]) -> Dict[str, Any]:
    """Terjemahan gsFitAuto: nugget dari downhole, kipas 36 arah, arah mayor, lalu semi & downhole."""
    minP = int(P["minP"])
    B = [float(P["B"][0]), float(P["B"][1])]
    BD = [float(P["BD"][0]), float(P["BD"][1])]
    ns = int(P.get("ns", 0) or 0)

    c0 = fit_nug(E["DH"], sill, minP, BD)
    if c0 is None:
        c0 = fit_nug(E["O"], sill, minP, B)
    if c0 is None:
        c0 = 0.2 * sill
    # DH 0.24.65: nugget minimal = ekstrapolasi linier dua lag downhole pertama (gsNugDH)
    nx = nug_dh(E["DH"], minP)
    if nx is not None and nx > c0:
        c0 = min(nx, 0.95 * sill)

    fan: List[Optional[float]] = []
    for j in range(ND):
        r = fit_r(E["D"][j], c0, [sill - c0], minP, B)
        fan.append(r[0] if r else None)

    best = -1.0
    jm = 0
    for j in range(ND):
        a = fan[j]
        if a is None:
            continue
        b = fan[(j + 35) % ND]
        c = fan[(j + 1) % ND]
        sm = (a * 2 + (a if b is None else b) + (a if c is None else c)) / 4.0
        if sm > best:
            best = sm
            jm = j

    a1 = fan[jm] if fan[jm] else B[1]
    M: Dict[str, Any] = {"pitch": jm * 5, "c0": c0, "c": [sill - c0, 0.0], "a": [a1, a1]}
    if ns != 1:
        sp = fit_split(E["D"][jm], c0, sill, minP, B)
        e1 = sse(E["D"][jm], c0, [sill - c0], [a1], minP)
        if sp and (ns == 2 or sp["e"] < 0.8 * e1):
            M["c"] = sp["c"]
            M["a"] = sp["a"]

    dua = M["c"][1] > 0
    cs = M["c"] if dua else [M["c"][0]]
    bs = fit_r(E["D"][(jm + 18) % ND], c0, cs, minP, B)
    M["b"] = (bs if dua else [bs[0], bs[0]]) if bs else list(M["a"])
    ds = fit_r(E["DH"], c0, cs, minP, BD)
    M["d"] = (ds if dua else [ds[0], ds[0]]) if ds else list(M["b"])
    # DH 0.24.65: mayor >= semi-mayor (pitch diputar 90 bila struktur dominan lebih menerus tegak lurus pitch)
    wA = sum(c * M["a"][i] for i, c in enumerate(cs))
    wB = sum(c * M["b"][i] for i, c in enumerate(cs))
    if wB > wA * 1.0001:
        M["pitch"] = (M["pitch"] + 90) % 180
        M["a"], M["b"] = M["b"], M["a"]
    M["a"] = list(M["a"]); M["b"] = list(M["b"])
    for q in range(len(M["a"])):
        if M["b"][q] > M["a"][q]:
            M["a"][q], M["b"][q] = M["b"][q], M["a"][q]
    M["fan"] = fan
    return M


def nug_dh(E: Sequence[Dict[str, float]], minP: int) -> Optional[float]:
    L = sorted([e for e in (E or []) if e and e.get("g") is not None and math.isfinite(e["g"]) and e.get("n", 0) >= (minP or 10) and e.get("h", 0) > 0], key=lambda e: e["h"])
    if len(L) < 2:
        return None
    a, b = L[0], L[1]
    if not b["h"] > a["h"]:
        return None
    x = a["g"] - (b["g"] - a["g"]) * a["h"] / (b["h"] - a["h"])
    return max(0.0, min(a["g"], x))


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Satu panggilan dari aplikasi: komposit + nilai + parameter -> variogram + model.

    payload: {C:[{x,y,z,id,d}], z:[...], P:{...}, u:[3], w:[3], sill: float, fit: bool}
    Nilai z sudah ditransformasi di pemanggil (none / log / nscore) supaya transformasinya
    tetap satu sumber kebenaran di JS; sill juga dikirim apa adanya agar sama persis.
    """
    C = payload.get("C") or []
    z = payload.get("z") or []
    if len(C) != len(z):
        raise ValueError("jumlah komposit dan nilai tidak sama: %d vs %d" % (len(C), len(z)))
    if len(C) < 2:
        raise ValueError("komposit kurang dari 2")
    P = dict(payload.get("P") or {})
    u = payload.get("u") or [1.0, 0.0, 0.0]
    w = payload.get("w") or [0.0, 1.0, 0.0]
    E = vario(C, z, P, u, w)
    out: Dict[str, Any] = {"ok": True, "E": {"D": E["D"], "O": E["O"], "DH": E["DH"]},
                           "ms": E["ms"], "npair": E["npair"], "n": len(C)}
    if payload.get("fit", True):
        sill = float(payload.get("sill") or 0.0)
        if sill > 0:
            t0 = time.perf_counter()
            out["M"] = fit_auto({"D": E["D"], "O": E["O"], "DH": E["DH"]}, sill, P)
            out["msFit"] = int(round((time.perf_counter() - t0) * 1000))
    return out
