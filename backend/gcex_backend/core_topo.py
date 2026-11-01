"""Topografi / DTM as-built untuk DB-Ex Singkapan (OPSIONAL).

Kebenaran posisi tetap georeferensi (titik survey Pylox / pita). Topografi survey biasanya diperbarui seminggu sekali, jadi
foto bisa lebih baru dari DTM: menempel ke DTM hanya dilakukan bila pengguna memilihnya, dengan laporan QC (jarak titik
georef ke DTM, porsi fitur yang kena DTM, tanggal survey vs tanggal foto).

- Impor Surpac .dtm (teks / biner) + .str pasangannya (teks / biner), disimpan per proyek sebagai versi bertanggal
  (_GCEx_Core/singkapan/topo/<id>.npz + tabel topo).
- Tempel: titik di bidang georef diproyeksikan ke permukaan DTM — foto lantai tegak lurus (vertikal), foto dinding sepanjang
  normal bidang — dengan batas jarak. Garis dirapatkan dulu (langkah ~0,5 m) agar mengikuti bentuk permukaan.
- Di luar DTM (atau DTM lebih tua dari foto): opsional diisi Depth Anything (kedalaman relatif) yang dikalibrasi ke meter
  memakai titik yang kena DTM dan / atau titik georef (core_vision.depth_map)."""
from __future__ import annotations

import json
import math
import re
import struct
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np

from . import core_io

RXN = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


# ================================================================ pembaca Surpac
def parse_str(data: bytes, yx: bool = True) -> list[list[list[float]]]:
    """Segmen string Surpac [[x, y, z], ...]; record 0,0,0 = pemisah. Teks (sn, Y, X, Z, ...) atau biner (record 29 byte)."""
    nl, ds = 0, -1
    for i, b in enumerate(data):
        if b == 10:
            nl += 1
            if nl == 2:
                ds = i + 1
                break
    if ds < 0 or ds >= len(data):
        raise ValueError("format STR tidak dikenali")
    segs: list = []
    cur: list = []
    c = data[ds]
    if chr(c) in "0123456789 -\r\n\t+.":
        prev = None
        for ln in data.decode("utf-8", "replace").splitlines():
            ln = ln.replace("\t", " ").strip()
            if not ln:
                continue
            a = [v.strip() for v in (ln.split(",") if "," in ln else ln.split())]
            if len(a) >= 4 and all(RXN.match(v) for v in a[:4]):
                sn, p, q, z = a[0], float(a[1]), float(a[2]), float(a[3])
            elif len(a) == 3 and all(RXN.match(v) for v in a):
                sn, p, q, z = "1", float(a[0]), float(a[1]), float(a[2])
            else:
                continue
            x, y = (q, p) if yx else (p, q)
            if x == 0 and y == 0 and z == 0:
                if cur:
                    segs.append(cur)
                cur, prev = [], None
                continue
            if prev is not None and sn != prev and cur:
                segs.append(cur)
                cur = []
            prev = sn
            cur.append([x, y, z])
        if cur:
            segs.append(cur)
        return segs
    end = len(data)
    for k in range(len(data) - 3, max(ds, len(data) - 64) - 1, -1):
        if data[k:k + 3] == b"END":
            end = k
            break
    o, pn = ds + ((end - ds) % 29), -1
    while o + 29 <= end:
        no = int.from_bytes(data[o + 1:o + 5], "big")
        Y, X, Z = struct.unpack(">ddd", data[o + 5:o + 29])
        if not yx:
            X, Y = Y, X
        if X == 0 and Y == 0 and Z == 0:
            if cur:
                segs.append(cur)
            cur, pn = [], -1
        else:
            if pn >= 0 and no != pn and cur:
                segs.append(cur)
                cur = []
            pn = no
            cur.append([X, Y, Z])
        o += 29
    if cur:
        segs.append(cur)
    return segs


def _dtm_bin(u: bytes) -> Optional[tuple[list[int], int]]:
    hdr = u.find(b"END", 0, 4096)
    if hdr < 0:
        return None
    o = hdr + 3

    def I(p: int) -> int:  # noqa: E743
        return int.from_bytes(u[p:p + 4], "big", signed=True)
    tri: list[int] = []
    mx, nb, rs = 0, False, 0
    while o < len(u) and u[o] == 0:
        o += 1
    while o < len(u):
        t = u[o]
        if t == 1:
            o += 9
            while o < len(u) and u[o] == 0:
                o += 1
            continue
        if t == 2:
            j = o + 5
            while j < len(u) and u[j] != 0:
                j += 1
            nb = bool(re.search(rb"neighbours\s*=\s*yes", u[o + 5:j], re.I))
            o = j
            while o < len(u) and u[o] == 0:
                o += 1
            rs = 0
            continue
        if t == 3:
            if not rs:
                id0 = I(o + 1)
                for cnd in ([33] if nb else []) + [21, 33, 29, 25, 37, 41]:
                    q = o + cnd
                    if q >= len(u) or u[q] == 255 or (u[q] == 3 and I(q + 1) == id0 + 1) or u[q] in (1, 2):
                        rs = cnd
                        break
                if not rs:
                    raise ValueError("struktur record segitiga DTM biner tidak dikenali")
            a, b, c = I(o + 5), I(o + 9), I(o + 13)
            if a < 1 or b < 1 or c < 1:
                raise ValueError(f"indeks titik DTM biner tidak valid (byte {o})")
            tri += [a - 1, b - 1, c - 1]
            mx = max(mx, a, b, c)
            o += rs
            continue
        if t in (255, 0):
            break
        raise ValueError(f"record DTM biner tidak dikenali (tipe {t} di byte {o})")
    return tri, mx


def parse_dtm(data: bytes) -> tuple[str, list[int], int, bool]:
    """(nama file string rujukan, indeks segitiga 0-based datar, indeks maks 1-based, biner?)."""
    nl = data.find(b"\n")
    nl = nl if 0 <= nl < 2000 else min(len(data), 2000)
    ref = data[:nl].decode("latin-1").split(",")[0].strip()
    binary = b"\x00" in data[nl + 1:nl + 400]
    tri: list[int] = []
    mx = 0
    if binary:
        r = _dtm_bin(data)
        if r:
            tri, mx = r
    else:
        for ln in data.decode("latin-1").splitlines()[1:]:
            a = ln.split(",")
            if len(a) < 4 or not a[0].strip().isdigit():
                continue
            try:
                p, q, r_ = int(float(a[1])), int(float(a[2])), int(float(a[3]))
            except ValueError:
                continue
            if p > 0 and q > 0 and r_ > 0:
                tri += [p - 1, q - 1, r_ - 1]
                mx = max(mx, p, q, r_)
    if not tri:
        raise ValueError("tidak ada segitiga di file DTM")
    return ref, tri, mx, binary


def build_tin(dtm_name: str, dtm: bytes, strs: dict[str, bytes]) -> tuple[np.ndarray, np.ndarray]:
    """Gabungkan .dtm dengan .str pasangannya -> (V [n,3], T [m,3]). Penomoran titik Surpac kadang ikut menghitung record
    pemisah string: dipilih penomoran yang konsisten (sama dengan GC-Ex)."""
    ref, tri, mx, _b = parse_dtm(dtm)
    low = ref.lower()

    def base(n: str) -> str:
        return re.sub(r"^.*[\\/]", "", n.lower())
    cand = [k for k in strs if low and (base(k) == low or base(k).endswith("_" + low) or base(k).endswith("-" + low) or base(k).endswith(low))]
    if not cand and len(strs) == 1:
        cand = list(strs)
    if not cand:
        raise ValueError(f"{dtm_name}: titik DTM tersimpan di file string \"{ref or '*.str'}\". Pilih file itu bersama .dtm-nya "
                         "(nama file jangan diubah).")
    segs = parse_str(strs[cand[0]])
    P: list = []
    PS: list = []
    for g in segs:
        P += g
        PS += g + [None]
    okP, okS = mx <= len(P), mx <= len(PS)
    if okS and any(PS[i] is None for i in tri):
        okS = False

    def med(A: list) -> float:
        L = []
        st = max(3, (len(tri) // 3 // 3000) * 3)
        for t in range(0, len(tri), st):
            p, q = A[tri[t]], A[tri[t + 1]]
            if p and q:
                L.append(math.hypot(p[0] - q[0], p[1] - q[1]))
        L.sort()
        return L[len(L) // 2] if L else math.inf
    if not okP and not okS:
        raise ValueError(f"{dtm_name}: DTM merujuk titik ke-{mx} tetapi {cand[0]} hanya berisi {len(P)} titik: file string tidak cocok.")
    useS = okS and (not okP or (len(segs) > 1 and med(PS) < med(P)))
    T = np.array(tri, dtype=np.int64).reshape(-1, 3)
    if useS:
        mp = np.full(len(PS), -1, dtype=np.int64)
        n = 0
        for k, p in enumerate(PS):
            if p is not None:
                mp[k] = n
                n += 1
        T = mp[T]
    V = np.array(P, dtype=np.float64)
    return V, T


# ================================================================ penyimpanan versi topografi per proyek
_DDL = """CREATE TABLE IF NOT EXISTS topo (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, survey_date TEXT, files TEXT, n_tri INTEGER, n_pts INTEGER,
  bbox TEXT, note TEXT, by TEXT, at TEXT)"""


def _dir(s) -> Path:
    d = s.root / "topo"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _init(s) -> None:
    with s.lock, s.conn() as c:
        c.execute(_DDL)


def topo_list(s) -> list[dict]:
    _init(s)
    with s.conn() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM topo ORDER BY survey_date DESC, id DESC")]
    for r in rows:
        r["bbox"] = json.loads(r["bbox"] or "null")
        r["files"] = json.loads(r["files"] or "[]")
    return rows


def topo_add(s, paths: list[str], survey_date: str, name: str, by: str) -> dict:
    """Impor satu DTM (.dtm + .str pasangannya) sebagai versi topografi bertanggal survey."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", survey_date or ""):
        raise ValueError("Isi tanggal survey topografi (YYYY-MM-DD).")
    fs = [Path(p) for p in paths]
    dtms = [f for f in fs if f.suffix.lower() == ".dtm"]
    strs = {f.name: f.read_bytes() for f in fs if f.suffix.lower() == ".str"}
    if len(dtms) != 1:
        raise ValueError("Pilih tepat satu file .dtm beserta file .str pasangannya.")
    V, T = build_tin(dtms[0].name, dtms[0].read_bytes(), strs)
    if not len(T):
        raise ValueError("DTM tidak berisi segitiga.")
    _init(s)
    bbox = [float(x) for x in (*V.min(axis=0), *V.max(axis=0))]
    with s.lock, s.conn() as c:
        tid = c.execute("INSERT INTO topo (name, survey_date, files, n_tri, n_pts, bbox, by, at) VALUES (?,?,?,?,?,?,?,?)",
                        ((name or dtms[0].stem)[:80], survey_date, json.dumps([f.name for f in fs]), int(len(T)), int(len(V)),
                         json.dumps(bbox), by, core_io.now())).lastrowid
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (NULL,'topografi',NULL,?, 'impor', ?, ?)",
                  (f"{name or dtms[0].stem} ({survey_date}) {len(T)} segitiga", by, core_io.now()))
    np.savez_compressed(_dir(s) / f"{tid}.npz", V=V, T=T)
    _CACHE.pop((str(s.root), tid), None)
    return next(t for t in topo_list(s) if t["id"] == tid)


def topo_delete(s, tid: int, by: str) -> list[dict]:
    _init(s)
    with s.lock, s.conn() as c:
        c.execute("DELETE FROM topo WHERE id=?", (tid,))
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (NULL,'topografi',?,NULL,'hapus',?,?)",
                  (f"#{tid}", by, core_io.now()))
    f = _dir(s) / f"{tid}.npz"
    if f.exists():
        f.unlink()
    _CACHE.pop((str(s.root), tid), None)
    return topo_list(s)


_CACHE: dict = {}


def topo_tin(s, tid: int) -> tuple[np.ndarray, np.ndarray]:
    k = (str(s.root), tid)
    if k not in _CACHE:
        f = _dir(s) / f"{tid}.npz"
        if not f.exists():
            raise ValueError(f"Topografi #{tid} tidak ada di proyek.")
        z = np.load(f)
        _CACHE.clear() if len(_CACHE) > 3 else None
        _CACHE[k] = (z["V"], z["T"])
    return _CACHE[k]


# ================================================================ tempel ke permukaan
def ray_tin(P: np.ndarray, D: np.ndarray, V: np.ndarray, T: np.ndarray, maxd: float) -> tuple[np.ndarray, np.ndarray]:
    """Perpotongan garis P + t*D (t di [-maxd, maxd]) dengan TIN. Kembalikan (t terdekat ke 0 atau nan, ok)."""
    n = len(P)
    tout = np.full(n, np.nan)
    if not n or not len(T):
        return tout, np.zeros(n, bool)
    # saring sekali ke kotak pembatas semua sinar (DTM as-built bisa jutaan segitiga, foto hanya puluhan meter)
    Q = np.vstack([P - D * maxd, P + D * maxd])
    gl, gh = Q.min(axis=0) - 1e-6, Q.max(axis=0) + 1e-6
    A0, B0, C0 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    keep = np.all((np.maximum(np.maximum(A0, B0), C0) >= gl) & (np.minimum(np.minimum(A0, B0), C0) <= gh), axis=1)
    if not keep.any():
        return tout, np.zeros(n, bool)
    A, B, C = A0[keep], B0[keep], C0[keep]
    lo = np.minimum(np.minimum(A, B), C)
    hi = np.maximum(np.maximum(A, B), C)
    E1, E2 = B - A, C - A
    for i in range(n):
        p, d = P[i], D[i]
        q0, q1 = p - d * maxd, p + d * maxd
        bl, bh = np.minimum(q0, q1) - 1e-6, np.maximum(q0, q1) + 1e-6
        m = np.all((hi >= bl) & (lo <= bh), axis=1)
        if not m.any():
            continue
        a, e1, e2 = A[m], E1[m], E2[m]
        h = np.cross(np.broadcast_to(d, e2.shape), e2)
        det = np.einsum("ij,ij->i", e1, h)
        ok = np.abs(det) > 1e-12
        if not ok.any():
            continue
        f = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        sv = p - a
        u = f * np.einsum("ij,ij->i", sv, h)
        qv = np.cross(sv, e1)
        v = f * (qv @ d)
        t = f * np.einsum("ij,ij->i", e2, qv)
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (np.abs(t) <= maxd)
        if hit.any():
            th = t[hit]
            tout[i] = th[np.argmin(np.abs(th))]
    return tout, ~np.isnan(tout)


def densify(xyz: np.ndarray, step: float, closed: bool = False) -> np.ndarray:
    P = np.vstack([xyz, xyz[:1]]) if closed else xyz
    out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        L = float(np.linalg.norm(b - a))
        k = max(1, int(math.ceil(L / step))) if step > 0 else 1
        for j in range(1, k + 1):
            out.append(a + (b - a) * j / k)
    R = np.array(out)
    return R[:-1] if closed else R
