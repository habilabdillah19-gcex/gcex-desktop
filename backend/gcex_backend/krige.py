# -*- coding: utf-8 -*-
"""Ordinary Kriging di Python (NumPy): pencarian tetangga + penyelesaian sistem per blok.

Tahap kedua pemindahan perhitungan dari JavaScript. Di sini untungnya struktural, bukan
sekadar bahasa: JS menyelesaikan sistem kriging SATU-SATU dengan eliminasi Gauss tulisan
tangan (okSolve), sedangkan blok yang jumlah sampelnya sama bisa diselesaikan BERKELOMPOK
dalam satu panggilan LAPACK (np.linalg.solve pada array (B, N, N)). Ukuran JS yang diukur
pada data latihan: 0,38 ms per blok (1.084 blok / 745 ms; 8.966 blok / 3.383 ms).

ATURAN YANG DIPEGANG (sama dengan geostat.py)
  Hasilnya harus SAMA dengan jalur JavaScript, karena angka inilah yang dipakai orang untuk
  menggali. Karena itu:
    * model (vM / vS / vN, c0, cs, A, B, Cn, R) dikirim apa adanya dari okModel di JS -- tidak
      dihitung ulang di sini, supaya tidak ada dua sumber kebenaran;
    * kovarians, diskretisasi blok, dan cbb memakai rumus yang sama persis (termasuk okCov yang
      mengembalikan 1 pada jarak nol, dan +1e-9 pada komponen z di sisi kanan sistem);
    * pencarian tetangga mengikuti okSearch sampai ke urutannya: sel dikumpulkan per sel grid
      dengan urutan i, j, k yang sama, diurutkan STABIL menurut jarak elipsoid kuadrat, lalu
      dibatasi "maksimal per lubang" dan jumlah maksimal.
  Yang berbeda hanya caranya dihitung.

Uji: backend/tests/test_krige.py (invarian) dan tools/uji/paritas_krige.py (mengadu angka
Python dengan angka JS pada data latihan, blok per blok).
"""
from __future__ import annotations

import math
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------- model & kovarians
class Model:
    """Pembungkus model dari okModel() di JS (sudah dinormalkan ke sill = 1)."""

    __slots__ = ("vM", "vS", "vN", "c0", "cs", "A", "B", "Cn", "R")

    def __init__(self, m: Dict[str, Any]):
        self.vM = np.asarray(m["vM"], dtype=np.float64)
        self.vS = np.asarray(m["vS"], dtype=np.float64)
        self.vN = np.asarray(m["vN"], dtype=np.float64)
        self.c0 = float(m["c0"])
        self.cs = np.asarray(m["cs"], dtype=np.float64)
        self.A = np.asarray(m["A"], dtype=np.float64)
        self.B = np.asarray(m["B"], dtype=np.float64)
        self.Cn = np.asarray(m["Cn"], dtype=np.float64)
        self.R = np.asarray(m["R"], dtype=np.float64)


def cov(m: Model, d: np.ndarray) -> np.ndarray:
    """Kovarians ternormalkan untuk selisih koordinat d[..., 3]; sama dengan okCov di JS.

    Jarak nol -> 1 (termasuk nugget). Struktur sferis: c * (1 - 1.5h + 0.5h^3) untuk h < 1.
    """
    p = d @ m.vM
    q = d @ m.vS
    r = d @ m.vN
    out = np.zeros(p.shape, dtype=np.float64)
    for i in range(m.cs.size):
        a = p / m.A[i]
        b = q / m.B[i]
        c = r / m.Cn[i]
        h = np.sqrt(a * a + b * b + c * c)
        dekat = h < 1.0
        if dekat.any():
            hh = h[dekat]
            out[dekat] += m.cs[i] * (1.0 - 1.5 * hh + 0.5 * hh * hh * hh)
    nol = (d[..., 0] == 0) & (d[..., 1] == 0) & (d[..., 2] == 0)
    if nol.any():
        out[nol] = 1.0
    return out


def disc(bs: Sequence[float], nd: Sequence[int]) -> np.ndarray:
    """Titik diskretisasi di dalam blok (okDisc), urutan i, j, k sama dengan JS."""
    o = []
    for i in range(int(nd[0])):
        for j in range(int(nd[1])):
            for k in range(int(nd[2])):
                o.append([((i + 0.5) / nd[0] - 0.5) * bs[0],
                          ((j + 0.5) / nd[1] - 0.5) * bs[1],
                          ((k + 0.5) / nd[2] - 0.5) * bs[2]])
    return np.asarray(o, dtype=np.float64)


def cbb_of(m: Model, D: np.ndarray) -> float:
    """Rata-rata kovarians blok-blok (okCbb)."""
    d = D[:, None, :] - D[None, :, :]
    return float(cov(m, d).sum() / (D.shape[0] * D.shape[0]))


# ---------------------------------------------------------------- indeks sel & pencarian
class Index:
    """Indeks sel grid komposit, sepadan dengan okIndex di JS (urutan sisip dipertahankan)."""

    def __init__(self, X: np.ndarray, Y: np.ndarray, Z: np.ndarray, cell: float):
        self.cell = float(cell)
        ix = np.floor(X / cell).astype(np.int64)
        iy = np.floor(Y / cell).astype(np.int64)
        iz = np.floor(Z / cell).astype(np.int64)
        self.m: Dict[Tuple[int, int, int], np.ndarray] = {}
        urut: Dict[Tuple[int, int, int], List[int]] = {}
        for i in range(X.size):
            urut.setdefault((int(ix[i]), int(iy[i]), int(iz[i])), []).append(i)
        for k, v in urut.items():
            self.m[k] = np.asarray(v, dtype=np.int64)


def kotak(m: Model, mult: float) -> np.ndarray:
    """Setengah-lebar kotak pembatas elipsoid pencarian (sama dengan e[] di okSearch)."""
    R = m.R * mult
    return np.sqrt((R[0] * m.vM) ** 2 + (R[1] * m.vS) ** 2 + (R[2] * m.vN) ** 2)


def kandidat(I: Index, e: np.ndarray, x: float, y: float, z: float) -> np.ndarray:
    """Indeks komposit dari sel-sel yang mungkin kena, dengan URUTAN seperti okSearch
    (i, j, k bersarang, isi sel menurut urutan sisip). Blok yang sel-nya sama menghasilkan
    daftar yang sama, jadi hasilnya bisa dipakai bersama (lihat tembolok di run())."""
    cl = I.cell
    i0 = int(math.floor((x - e[0]) / cl)); i1 = int(math.floor((x + e[0]) / cl))
    j0 = int(math.floor((y - e[1]) / cl)); j1 = int(math.floor((y + e[1]) / cl))
    k0 = int(math.floor((z - e[2]) / cl)); k1 = int(math.floor((z + e[2]) / cl))
    kumpul: List[np.ndarray] = []
    g = I.m.get
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                L = g((i, j, k))
                if L is not None:
                    kumpul.append(L)
    if not kumpul:
        return np.empty(0, dtype=np.int64)
    return kumpul[0] if len(kumpul) == 1 else np.concatenate(kumpul)


def kandidat_kotak(I: Index, e: np.ndarray, ks: Tuple[int, int, int]) -> np.ndarray:
    """Kandidat untuk SELURUH blok di dalam satu sel grid: kotak sel diperlebar e ke segala arah."""
    cl = I.cell
    i0 = int(math.floor((ks[0] * cl - e[0]) / cl)); i1 = int(math.floor(((ks[0] + 1) * cl + e[0]) / cl))
    j0 = int(math.floor((ks[1] * cl - e[1]) / cl)); j1 = int(math.floor(((ks[1] + 1) * cl + e[1]) / cl))
    k0 = int(math.floor((ks[2] * cl - e[2]) / cl)); k1 = int(math.floor(((ks[2] + 1) * cl + e[2]) / cl))
    kumpul: List[np.ndarray] = []
    g = I.m.get
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                L = g((i, j, k))
                if L is not None:
                    kumpul.append(L)
    if not kumpul:
        return np.empty(0, dtype=np.int64)
    return kumpul[0] if len(kumpul) == 1 else np.concatenate(kumpul)


def pilih(m: Model, X: np.ndarray, Y: np.ndarray, Z: np.ndarray, HID: np.ndarray, idx: np.ndarray,
          x: float, y: float, z: float, mult: float, maxN: int, mph: int) -> np.ndarray:
    """Dari daftar kandidat: saring elipsoid, urutkan stabil menurut jarak, batasi per lubang
    dan jumlah maksimal. Terjemahan bagian kedua okSearch."""
    if idx.size == 0:
        return idx
    R = m.R * mult
    dx = X[idx] - x
    dy = Y[idx] - y
    dz = Z[idx] - z
    p = (dx * m.vM[0] + dy * m.vM[1] + dz * m.vM[2]) / R[0]
    q = (dx * m.vS[0] + dy * m.vS[1] + dz * m.vS[2]) / R[1]
    r = (dx * m.vN[0] + dy * m.vN[1] + dz * m.vN[2]) / R[2]
    d2 = p * p + q * q + r * r
    ok = d2 <= 1.0
    if not ok.any():
        return np.empty(0, dtype=np.int64)
    idx = idx[ok]
    d2 = d2[ok]
    urut = np.argsort(d2, kind="stable")          # stabil: seri tetap urut seperti JS
    idx = idx[urut]
    if mph > 0 and idx.size:
        # peringkat kemunculan tiap lubang pada urutan ini (vektor, tanpa perulangan kandidat)
        h = HID[idx]
        s = np.argsort(h, kind="stable")
        hs = h[s]
        batas = np.flatnonzero(np.r_[True, hs[1:] != hs[:-1]])
        cnt = np.diff(np.r_[batas, hs.size])
        peringkat = np.arange(hs.size) - np.repeat(batas, cnt)
        pr = np.empty(hs.size, dtype=np.int64)
        pr[s] = peringkat
        idx = idx[pr < mph]
    return idx[:maxN] if idx.size > maxN else idx


def search(m: Model, I: Index, X: np.ndarray, Y: np.ndarray, Z: np.ndarray, HID: np.ndarray,
           x: float, y: float, z: float, mult: float, maxN: int, mph: int) -> np.ndarray:
    """okSearch untuk satu blok (kumpulkan kandidat lalu pilih). Dipakai uji & pemanggilan tunggal;
    run() memakai kandidat_kotak() agar daftar kandidat dipakai bersama antar blok satu sel."""
    e = kotak(m, mult)
    idx = kandidat(I, e, x, y, z)
    return pilih(m, X, Y, Z, HID, idx, x, y, z, mult, maxN, mph)


# ---------------------------------------------------------------- kriging berkelompok
def _krige_batch(m: Model, SX: np.ndarray, SY: np.ndarray, SZ: np.ndarray, SV: np.ndarray,
                 blk: np.ndarray, D: np.ndarray, cbb: float) -> Dict[str, np.ndarray]:
    """Selesaikan B blok yang masing-masing punya n sampel, sekaligus.

    SX/SY/SZ/SV : (B, n) koordinat & nilai sampel terpilih
    blk         : (B, 3) titik pusat blok
    """
    Bn, n = SX.shape
    N = n + 1
    S = np.stack([SX, SY, SZ], axis=-1)                      # (B, n, 3)
    d = S[:, :, None, :] - S[:, None, :, :]                   # (B, n, n, 3)
    A = np.zeros((Bn, N, N), dtype=np.float64)
    A[:, :n, :n] = cov(m, d)
    A[:, :n, n] = 1.0
    A[:, n, :n] = 1.0
    # sisi kanan: rata-rata kovarians sampel terhadap titik diskretisasi blok (+1e-9 pada z, seperti JS)
    tit = blk[:, None, :] + D[None, :, :]                     # (B, nd, 3)
    dd = S[:, :, None, :] - tit[:, None, :, :]                # (B, n, nd, 3)
    dd = dd.copy()
    dd[..., 2] += 1e-9
    b = np.empty((Bn, N), dtype=np.float64)
    b[:, :n] = cov(m, dd).mean(axis=2)
    b[:, n] = 1.0
    rhs = b.copy()
    try:
        # NumPy 2: sisi kanan bertumpuk harus (B, N, 1), lalu diambil kolomnya
        w = np.linalg.solve(A, b[..., None])[..., 0]
    except np.linalg.LinAlgError:
        w = np.empty((Bn, N), dtype=np.float64)
        for q in range(Bn):
            try:
                w[q] = np.linalg.solve(A[q], b[q])
            except np.linalg.LinAlgError:
                w[q] = np.nan
    est = (w[:, :n] * SV).sum(axis=1)
    sl = (w[:, :n] * rhs[:, :n]).sum(axis=1)
    mu = w[:, n]
    kv = cbb - sl - mu
    am = np.abs(mu)
    sor = (cbb - kv + am) / (cbb - kv + 2 * am)
    ke = (cbb - kv) / cbb
    neg = -np.minimum(w[:, :n], 0.0).sum(axis=1)
    return {"est": est, "kv": kv, "sor": sor, "ke": ke, "neg": neg, "mu": mu}


def _inti(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Estimasi sejumlah blok dalam satu proses; pass dicoba berurutan seperti okStep di JS.

    payload: {C:[{x,y,z,id}], z:[...], m:{...okModel...}, blocks:[[x,y,z],...],
              passes:[{mult,min,max,mph}], bs:[3], nd:[3], cell: float|None}
    hasil  : {i, est, kv, sor, ke, ns, ps, neg, cnt, ms, cbb} -- i = indeks blok yang
             berhasil diestimasi (blok yang gagal di semua pass tidak muncul, seperti JS).
    """
    C = payload.get("C") or []
    zv = payload.get("z") or []
    if len(C) != len(zv):
        raise ValueError("jumlah komposit dan nilai tidak sama: %d vs %d" % (len(C), len(zv)))
    if len(C) < 3:
        raise ValueError("komposit terlalu sedikit")
    blocks = np.asarray(payload.get("blocks") or [], dtype=np.float64)
    if blocks.ndim != 2 or blocks.shape[1] != 3:
        raise ValueError("blocks harus daftar [x, y, z]")
    passes = payload.get("passes") or []
    if not passes:
        raise ValueError("minimal satu pass")
    m = Model(payload["m"])
    bs = [float(v) for v in (payload.get("bs") or [5, 5, 5])]
    nd = [int(v) for v in (payload.get("nd") or [3, 3, 2])]

    X = np.array([c["x"] for c in C], dtype=np.float64)
    Y = np.array([c["y"] for c in C], dtype=np.float64)
    Z = np.array([c["z"] for c in C], dtype=np.float64)
    V = np.asarray(zv, dtype=np.float64)
    peta: Dict[Any, int] = {}
    HID = np.empty(X.size, dtype=np.int64)
    for i, c in enumerate(C):
        k = c.get("id")
        if k not in peta:
            peta[k] = len(peta)
        HID[i] = peta[k]

    cell = payload.get("cell")
    if not cell:
        cell = max(bs[0], bs[1], bs[2], m.R[0] * float(passes[0]["mult"]) / 2)
    I = Index(X, Y, Z, float(cell))
    D = disc(bs, nd)
    cbb = cbb_of(m, D)

    t0 = time.perf_counter()
    nb = blocks.shape[0]
    hasil = {k: np.full(nb, np.nan) for k in ("est", "kv", "sor", "ke", "neg")}
    ns = np.zeros(nb, dtype=np.int64)
    ps = np.zeros(nb, dtype=np.int64)
    sisa = np.arange(nb)
    cnt = [0] * len(passes)

    for pi, P in enumerate(passes):
        if sisa.size == 0:
            break
        mult = float(P["mult"]); mn = int(P["min"]); mx = int(P["max"]); mph = int(P.get("mph") or 0)
        # 1. pencarian tetangga per blok (murah; yang mahal sistemnya)
        kel: Dict[int, List[int]] = {}
        selmap: Dict[int, List[np.ndarray]] = {}
        e = kotak(m, mult)
        cl = I.cell
        tembolok: Dict[Tuple[int, int, int], np.ndarray] = {}
        for bi in sisa:
            bx, by, bz = blocks[bi, 0], blocks[bi, 1], blocks[bi, 2]
            # daftar kandidat hanya bergantung pada SEL tempat blok berada: blok lain di sel yang
            # sama memakai daftar yang sama (ukuran sel pencarian jauh lebih besar dari ukuran blok,
            # jadi satu sel bisa memuat ratusan blok).
            ks = (int(math.floor(bx / cl)), int(math.floor(by / cl)), int(math.floor(bz / cl)))
            idx = tembolok.get(ks)
            if idx is None:
                # kotak sel DIPERLEBAR e: mencakup kotak pencarian blok mana pun di dalam sel itu,
                # jadi tidak ada komposit di dalam elipsoid yang terlewat. Kandidat tambahan tetap
                # disaring elipsoid di pilih(), sehingga himpunan akhirnya sama dengan JS.
                idx = tembolok[ks] = kandidat_kotak(I, e, ks)
            sel = pilih(m, X, Y, Z, HID, idx, bx, by, bz, mult, mx, mph)
            if sel.size < mn:
                continue
            kel.setdefault(sel.size, []).append(int(bi))
            selmap.setdefault(sel.size, []).append(sel)
        if not kel:
            continue
        # 2. sistem kriging diselesaikan BERKELOMPOK per jumlah sampel
        selesai: List[int] = []
        for n, daftar in kel.items():
            idxb = np.asarray(daftar, dtype=np.int64)
            SEL = np.stack(selmap[n])                      # (B, n)
            for q0 in range(0, idxb.size, 4096):           # potong agar memori terjaga
                q1 = min(idxb.size, q0 + 4096)
                ib = idxb[q0:q1]
                sl = SEL[q0:q1]
                r = _krige_batch(m, X[sl], Y[sl], Z[sl], V[sl], blocks[ib], D, cbb)
                baik = np.isfinite(r["est"])
                for k in ("est", "kv", "sor", "ke", "neg"):
                    hasil[k][ib[baik]] = r[k][baik]
                ns[ib[baik]] = n
                ps[ib[baik]] = pi + 1
                selesai.extend(ib[baik].tolist())
        cnt[pi] = len(selesai)
        if selesai:
            sisa = np.setdiff1d(sisa, np.asarray(selesai, dtype=np.int64), assume_unique=False)

    jadi = np.flatnonzero(ps > 0)
    return {
        "ok": True,
        "i": jadi.tolist(),
        "est": hasil["est"][jadi].tolist(),
        "kv": hasil["kv"][jadi].tolist(),
        "sor": hasil["sor"][jadi].tolist(),
        "ke": hasil["ke"][jadi].tolist(),
        "neg": hasil["neg"][jadi].tolist(),
        "ns": ns[jadi].tolist(),
        "ps": ps[jadi].tolist(),
        "cnt": cnt,
        "n": int(jadi.size),
        "nblok": int(nb),
        "cbb": cbb,
        "ms": int(round((time.perf_counter() - t0) * 1000)),
    }


# ---------------------------------------------------------------------------
# Pembagian ke beberapa inti CPU
#
# Hasil satu blok TIDAK bergantung pada blok lain: tetangganya dicari dari komposit, bukan dari
# blok yang sudah diestimasi. Karena itu daftar blok boleh dipotong dan dikerjakan beberapa proses
# sekaligus, dan angkanya wajib tetap sama persis -- itu yang diuji di test_krige.py.
# Proses dipakai (bukan thread) karena GIL Python membuat thread tidak menambah kecepatan di sini.
# ---------------------------------------------------------------------------

_BERSAMA: Dict[str, Any] = {}


def _siap_pekerja(dasar: Dict[str, Any]) -> None:
    """Dipanggil sekali per proses pekerja: komposit & model dikirim satu kali, bukan per potongan."""
    _BERSAMA["dasar"] = dasar


def _kerja(args: Tuple[int, List[List[float]]]) -> Tuple[int, Dict[str, Any]]:
    i0, blk = args
    p = dict(_BERSAMA["dasar"])
    p["blocks"] = blk
    return i0, _inti(p)


def _jumlah_pekerja(minta: Any, nb: int) -> int:
    """Berapa proses yang dipakai. 'auto' / 0 = sebanyak inti CPU (maksimal 8), dibatasi agar
    tiap pekerja masih dapat cukup blok -- memecah 50 blok ke 8 proses hanya menambah ongkos."""
    inti = os.cpu_count() or 1
    if minta in (None, 0, "auto", "otomatis"):
        w = min(inti, 8)
    else:
        try:
            w = int(minta)
        except (TypeError, ValueError):
            w = 1
    w = max(1, min(w, inti, nb // 1000 if nb >= 2000 else 1))
    return w


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Estimasi sejumlah blok. Bila bloknya banyak, pekerjaan dibagi ke beberapa inti CPU;
    hasilnya identik dengan satu proses (dibuktikan uji paritas).

    payload: {C:[{x,y,z,id}], z:[...], m:{...okModel...}, blocks:[[x,y,z],...],
              passes:[{mult,min,max,mph}], bs:[3], nd:[3], cell: float|None,
              workers: int|'auto'|None}
    hasil  : {i, est, kv, sor, ke, ns, ps, neg, cnt, ms, cbb} -- i = indeks blok yang berhasil
             diestimasi (blok yang gagal di semua pass tidak muncul, seperti JS).
    """
    blocks = payload.get("blocks") or []
    w = _jumlah_pekerja(payload.get("workers"), len(blocks))
    if w <= 1:
        return _inti(payload)

    dasar = {k: v for k, v in payload.items() if k not in ("blocks", "workers")}
    nb = len(blocks)
    potong = [(round(nb * i / w), round(nb * (i + 1) / w)) for i in range(w)]
    tugas = [(a, list(blocks[a:b])) for a, b in potong if b > a]
    t0 = time.perf_counter()
    try:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=w, initializer=_siap_pekerja, initargs=(dasar,)) as ex:
            bagian = list(ex.map(_kerja, tugas))
    except Exception:
        # pembagian proses bisa gagal di lingkungan tertentu (mis. terbungkus tanpa
        # freeze_support). Angka lebih penting daripada kecepatan: kembali ke satu proses.
        return _inti(payload)

    o: Dict[str, Any] = {"ok": True, "i": [], "est": [], "kv": [], "sor": [], "ke": [],
                         "neg": [], "ns": [], "ps": []}
    cnt: List[int] = []
    cbb = 0.0
    for i0, r in bagian:
        o["i"].extend(i + i0 for i in r["i"])           # indeks dikembalikan ke penomoran asli
        for k in ("est", "kv", "sor", "ke", "neg", "ns", "ps"):
            o[k].extend(r[k])
        if len(cnt) < len(r["cnt"]):
            cnt += [0] * (len(r["cnt"]) - len(cnt))
        for j, v in enumerate(r["cnt"]):
            cnt[j] += v
        cbb = r["cbb"]
    urut = sorted(range(len(o["i"])), key=lambda k: o["i"][k])
    for k in ("i", "est", "kv", "sor", "ke", "neg", "ns", "ps"):
        o[k] = [o[k][j] for j in urut]
    o.update({"cnt": cnt, "n": len(o["i"]), "nblok": nb, "cbb": cbb,
              "ms": int(round((time.perf_counter() - t0) * 1000)), "workers": w})
    return o
