"""Model 3D dinding dari beberapa foto (fotogrametri / Structure-from-Motion) untuk DB-Ex Singkapan (Fase 2b).

Alur: 3–10 foto satu dinding (berjalan sejajar dinding, tumpang-tindih ±70 %) -> fitur SIFT & pencocokan antar foto
(diverifikasi matriks esensial) -> rekonstruksi bertahap (pasangan awal, PnP untuk foto berikutnya, triangulasi) ->
penghalusan bergantian kamera / titik (pengganti bundle adjustment ringan) -> awan titik 3D.

Skala & koordinat: titik cat RTK (nama, E, N, RL) yang diklik di >= 2 foto -> transformasi similaritas 7 parameter
(Umeyama) ke UTM; tanpa RTK dipakai posisi kamera dari GPS HP (kasar, ± beberapa meter). Pengukuran: titik-titik yang
diklik di foto (jejak vein / kekar yang melintasi permukaan tidak rata, atau sebaran titik di satu bidang tersingkap)
-> titik 3D di permukaan -> bidang terbaik (SVD) -> dip / arah dip / strike SEBENARNYA, dengan mutu (RMS, kerataan,
kelurusan). Semua offline (OpenCV + NumPy)."""
from __future__ import annotations

import base64
import importlib
import io
import json
import math
import shutil
import threading
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from . import core_io
from . import core_outcrop as O

router = APIRouter(prefix="/core/outcrop/m3d", tags=["core-outcrop-model3d"])
MAX_PHOTOS = 10
WORK_SIDE = 1600       # sisi panjang foto untuk fitur & rekonstruksi (koordinat disimpan dalam piksel ukuran ini)
_LOCK = threading.RLock()


def _cv2():
    try:
        return importlib.import_module("cv2")
    except ImportError:
        raise RuntimeError("OpenCV tidak terpasang di DB-Ex ini. Pasang ulang DB-Ex versi Qt terbaru.") from None


# ================================================================ penyimpanan
def root(s: O.Store) -> Path:
    d = s.root / "model3d"
    d.mkdir(exist_ok=True)
    return d


def _mdir(s: O.Store, mid: int) -> Path:
    d = root(s) / f"m{int(mid):03d}"
    if not d.is_dir():
        raise ValueError(f"Model 3D #{mid} tidak ada.")
    return d


def load(s: O.Store, mid: int) -> dict:
    return json.loads((_mdir(s, mid) / "model.json").read_text(encoding="utf-8"))


def save(s: O.Store, m: dict) -> None:
    with _LOCK:
        p = _mdir(s, m["id"]) / "model.json"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)


def models(s: O.Store) -> list[dict]:
    out = []
    for d in sorted(root(s).glob("m[0-9][0-9][0-9]")):
        try:
            m = json.loads((d / "model.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out.append({"id": m["id"], "name": m["name"], "n_photos": len(m["photos"]), "status": m.get("status"),
                    "georef": (m.get("georef") or {}).get("method"), "n_points": (m.get("recon") or {}).get("n_points", 0),
                    "n_measures": len(m.get("measures") or [])})
    return out


def create(s: O.Store, name: str, paths: list[str], by: str) -> dict:
    """Model baru: foto disalin ke _GCEx_Core/singkapan/model3d/mNNN/foto (maks. 10), metadata GPS HP ikut dibaca."""
    from . import core_oclokasi as L
    ps = [Path(p) for p in paths if Path(p).is_file()]
    if len(ps) < 3:
        raise ValueError("Model 3D butuh minimal 3 foto satu dinding yang saling tumpang-tindih.")
    if len(ps) > MAX_PHOTOS:
        raise ValueError(f"Maksimal {MAX_PHOTOS} foto per model (memori PC lapangan). Pilih {MAX_PHOTOS} foto terbaik.")
    with _LOCK:
        ids = [int(d.name[1:]) for d in root(s).glob("m[0-9][0-9][0-9]")]
        mid = max(ids, default=0) + 1
        d = root(s) / f"m{mid:03d}"
        (d / "foto").mkdir(parents=True)
    photos = []
    for i, p in enumerate(ps):
        dst = d / "foto" / f"{i + 1:02d}_{p.name}"
        shutil.copy2(p, dst)
        ex = L.read_exif(dst)
        from PIL import Image, ImageOps
        with Image.open(dst) as im:
            w, h = ImageOps.exif_transpose(im).size
        photos.append({"i": i, "file": dst.name, "name": p.name, "w": w, "h": h, "exif": ex})
    m = {"id": mid, "name": name.strip() or f"Model {mid}", "photos": photos, "status": "baru", "by": by, "at": core_io.now(),
         "gcps": [], "measures": [], "georef": None, "recon": None}
    save(s, m)
    return m


def delete(s: O.Store, mid: int) -> None:
    shutil.rmtree(_mdir(s, mid), ignore_errors=True)


def photo_path(s: O.Store, mid: int, i: int) -> Path:
    m = load(s, mid)
    return _mdir(s, mid) / "foto" / m["photos"][int(i)]["file"]


# ================================================================ rekonstruksi (SfM)
def _gray(path: Path) -> tuple[np.ndarray, float]:
    from PIL import Image, ImageOps
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("L")
        k = min(1.0, WORK_SIDE / max(im.size))
        if k < 1:
            im = im.resize((round(im.width * k), round(im.height * k)), Image.BILINEAR)
        return np.asarray(im), k


def _K(ph: dict, k: float) -> np.ndarray:
    """Matriks kamera dari panjang fokus ekuivalen 35 mm (EXIF); tanpa EXIF dianggap 26 mm (kamera utama HP)."""
    w, h = ph["w"] * k, ph["h"] * k
    f35 = (ph.get("exif") or {}).get("f35") or 26
    f = f35 / 36.0 * max(w, h)
    return np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1.0]])


def _triangulate(P_list: list[np.ndarray], uv_list: list[np.ndarray]) -> np.ndarray:
    """DLT banyak pandangan untuk satu titik."""
    A = []
    for P, (u, v) in zip(P_list, uv_list):
        A.append(u * P[2] - P[0])
        A.append(v * P[2] - P[1])
    _u, _s, vt = np.linalg.svd(np.array(A))
    X = vt[-1]
    return X[:3] / X[3] if abs(X[3]) > 1e-12 else np.array([np.nan] * 3)


def _proj(K, R, t, X):
    x = (X @ R.T + t) @ K.T
    return x[:, :2] / x[:, 2:3], x[:, 2]


def _rodrigues(w: np.ndarray) -> np.ndarray:
    th = float(np.linalg.norm(w))
    if th < 1e-12:
        return np.eye(3)
    k = w / th
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * Kx + (1 - math.cos(th)) * Kx @ Kx


def bundle_adjust(Ks: dict, cams: dict, X: np.ndarray, oc: np.ndarray, op: np.ndarray, uv: np.ndarray, fixed: int,
                  scale_cam: Optional[int] = None, iters: int = 15, huber: float = 2.0) -> tuple[dict, np.ndarray]:
    """Penyesuaian berkas (bundle adjustment) Levenberg-Marquardt dengan komplemen Schur, NumPy saja (tanpa SciPy).
    Kamera: rotasi (pembaruan sudut kecil) + translasi, K tetap; kamera `fixed` dikunci (datum) dan jarak kamera `scale_cam`
    ke kamera datum dijaga (skala), agar sistem tidak singular dan konvergensi cepat. Bobot Huber untuk pencilan.
    oc / op / uv: indeks kamera, indeks titik, piksel pengamatan."""
    cids = sorted(cams)
    free = [c for c in cids if c != fixed]
    ci = {c: k for k, c in enumerate(free)}
    nf, npnt = len(free), len(X)
    Rs = {c: np.array(cams[c][0], float) for c in cids}
    ts = {c: np.array(cams[c][1], float).ravel() for c in cids}
    Kf = np.array([[Ks[c][0, 0], Ks[c][1, 1], Ks[c][0, 2], Ks[c][1, 2]] for c in oc])
    X = X.copy()

    def resid(Rs, ts, X):
        Ra = np.stack([Rs[c] for c in oc])
        ta = np.stack([ts[c] for c in oc])
        xc = np.einsum("nij,nj->ni", Ra, X[op]) + ta
        z = np.where(np.abs(xc[:, 2]) < 1e-9, 1e-9, xc[:, 2])
        pr = np.c_[Kf[:, 0] * xc[:, 0] / z + Kf[:, 2], Kf[:, 1] * xc[:, 1] / z + Kf[:, 3]]
        return pr - uv, xc, Ra

    def cost(r):
        e = np.hypot(r[:, 0], r[:, 1])
        return float(np.sum(np.where(e <= huber, e * e, 2 * huber * e - huber * huber)))
    r, xc, Ra = resid(Rs, ts, X)
    c0 = cost(r)
    lam = 1e-3
    for _it in range(iters):
        e = np.hypot(r[:, 0], r[:, 1])
        wgt = np.where(e <= huber, 1.0, huber / np.maximum(e, 1e-12))
        x, y, z = xc[:, 0], xc[:, 1], xc[:, 2]
        fx, fy = Kf[:, 0], Kf[:, 1]
        Jpr = np.zeros((len(oc), 2, 3))
        Jpr[:, 0, 0] = fx / z
        Jpr[:, 0, 2] = -fx * x / z ** 2
        Jpr[:, 1, 1] = fy / z
        Jpr[:, 1, 2] = -fy * y / z ** 2
        RX = xc - np.stack([ts[c] for c in oc])
        skew = np.zeros((len(oc), 3, 3))  # d xc / d w = -[RX]x
        skew[:, 0, 1], skew[:, 0, 2], skew[:, 1, 0] = RX[:, 2], -RX[:, 1], -RX[:, 2]
        skew[:, 1, 2], skew[:, 2, 0], skew[:, 2, 1] = RX[:, 0], RX[:, 1], -RX[:, 0]
        Jc = np.concatenate([Jpr @ skew, Jpr], axis=2)  # 2x6
        Jp = Jpr @ Ra  # 2x3
        Jcw, Jpw = Jc * wgt[:, None, None], Jp * wgt[:, None, None]
        U = np.zeros((nf, 6, 6))
        gc = np.zeros((nf, 6))
        V = np.zeros((npnt, 3, 3))
        gp = np.zeros((npnt, 3))
        np.add.at(V, op, np.einsum("nki,nkj->nij", Jpw, Jp))
        np.add.at(gp, op, np.einsum("nki,nk->ni", Jpw, r))
        fm = np.array([c != fixed for c in oc])
        cidx = np.array([ci.get(c, -1) for c in oc])
        np.add.at(U, cidx[fm], np.einsum("nki,nkj->nij", Jcw[fm], Jc[fm]))
        np.add.at(gc, cidx[fm], np.einsum("nki,nk->ni", Jcw[fm], r[fm]))
        Wo = np.einsum("nki,nkj->nij", Jcw[fm], Jp[fm])  # 6x3 per pengamatan (satu pengamatan per pasangan kamera-titik)
        while True:
            Vd = V + lam * (np.einsum("nii->ni", V)[:, :, None] * np.eye(3) + 1e-9 * np.eye(3))
            Vinv = np.linalg.inv(Vd)
            Ud = U + lam * (np.einsum("nii->ni", U)[:, :, None] * np.eye(6) + 1e-9 * np.eye(6))
            S = np.zeros((nf * 6, nf * 6))
            for k in range(nf):
                S[k * 6:k * 6 + 6, k * 6:k * 6 + 6] = Ud[k]
            if scale_cam in ci:  # kunci skala: translasi kamera skala tidak boleh berubah searah vektor t-nya
                k = ci[scale_cam]
                u = ts[scale_cam] / max(np.linalg.norm(ts[scale_cam]), 1e-12)
                S[k * 6 + 3:k * 6 + 6, k * 6 + 3:k * 6 + 6] += 1e6 * (np.trace(U[k]) / 6 + 1.0) * np.outer(u, u)
            b = -gc.reshape(-1).copy()
            WVi = np.einsum("nij,njk->nik", Wo, Vinv[op[fm]])  # 6x3
            gpi = np.einsum("nij,nj->ni", Vinv, -gp)  # V^-1 (-gp)
            # kurangi W V^-1 W^T untuk tiap pasangan kamera yang melihat titik yang sama
            pf, cf = op[fm], cidx[fm]
            order = np.argsort(pf, kind="stable")
            pf_s, cf_s = pf[order], cf[order]
            WVi_s, Wo_s = WVi[order], Wo[order]
            starts = np.r_[0, np.flatnonzero(np.diff(pf_s)) + 1, len(pf_s)]
            np.add.at(b.reshape(nf, 6), cf_s, -np.einsum("nij,nj->ni", Wo_s, gpi[pf_s]))
            # semua pasangan pengamatan (a, b) dalam satu titik, tervektor
            sz = np.diff(starts)
            gid = np.repeat(np.arange(len(sz)), sz)
            rep = sz[gid]
            A = np.repeat(np.arange(len(pf_s)), rep)
            Bo = np.arange(len(A)) - np.repeat(np.cumsum(rep) - rep, rep)
            Bi = starts[gid[A]] + Bo
            S4 = np.zeros((nf * nf, 6, 6))
            for q0 in range(0, len(A), 200000):  # per potongan agar memori kecil
                a_, b_ = A[q0:q0 + 200000], Bi[q0:q0 + 200000]
                np.add.at(S4, cf_s[a_] * nf + cf_s[b_], np.einsum("nij,nkj->nik", WVi_s[a_], Wo_s[b_]))
            S -= S4.reshape(nf, nf, 6, 6).transpose(0, 2, 1, 3).reshape(nf * 6, nf * 6)
            try:
                dc = np.linalg.solve(S, b).reshape(nf, 6)
            except np.linalg.LinAlgError:
                lam *= 10
                if lam > 1e8:
                    break
                continue
            rhs = -gp.copy()
            np.add.at(rhs, pf, -np.einsum("nij,ni->nj", Wo, dc[cf]))
            dp = np.einsum("nij,nj->ni", Vinv, rhs)
            Rn, tn = dict(Rs), dict(ts)
            for c in free:
                d = dc[ci[c]]
                Rn[c] = _rodrigues(d[:3]) @ Rs[c]
                tn[c] = ts[c] + d[3:]
            Xn = X + dp
            rn, xcn, Ran = resid(Rn, tn, Xn)
            cn = cost(rn) if np.all(np.isfinite(rn)) else float("inf")
            if cn < c0:
                Rs, ts, X, r, xc, Ra = Rn, tn, Xn, rn, xcn, Ran
                done = (c0 - cn) < 1e-6 * c0
                c0 = cn
                lam = max(lam / 3, 1e-7)
                break
            lam *= 10
            if lam > 1e8:
                done = True
                break
        if lam > 1e8 or done:
            break
    return {c: (Rs[c], ts[c]) for c in cids}, X


def reconstruct(paths: list[Path], photos: list[dict], progress=None) -> dict:
    """SfM bertahap. Hasil: kamera (K, R, t), titik 3D, warna, pengamatan per titik (indeks foto, u, v dalam piksel kerja)."""
    cv2 = _cv2()
    n = len(paths)
    sift = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.02)
    kps, descs, Ks, ks, colors = [], [], [], [], []
    for i, p in enumerate(paths):
        g, k = _gray(p)
        kp, de = sift.detectAndCompute(g, None)
        kps.append(np.array([q.pt for q in kp], np.float64) if kp else np.zeros((0, 2)))
        descs.append(de if de is not None else np.zeros((0, 128), np.float32))
        Ks.append(_K(photos[i], k))
        ks.append(k)
        if progress:
            progress(f"Fitur foto {i + 1}/{n}: {len(kp)} titik")
    from PIL import Image, ImageOps
    rgbs = []
    for p, k in zip(paths, ks):
        with Image.open(p) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            rgbs.append(np.asarray(im.resize((round(im.width * k), round(im.height * k)))))
    # pencocokan antar pasangan (urutan berjalan: tetangga dekat diutamakan, semua pasangan bila foto sedikit)
    bf = cv2.BFMatcher(cv2.NORM_L2)
    pairs: dict[tuple[int, int], np.ndarray] = {}
    for i in range(n):
        for j in range(i + 1, n):
            if j - i > 4 and n > 6:
                continue
            if len(descs[i]) < 20 or len(descs[j]) < 20:
                continue
            mm = bf.knnMatch(descs[i], descs[j], k=2)
            good = np.array([[a.queryIdx, a.trainIdx] for a, b in (x for x in mm if len(x) == 2) if a.distance < 0.75 * b.distance])
            if len(good) < 30:
                continue
            p1 = cv2.undistortPoints(kps[i][good[:, 0]].reshape(-1, 1, 2), Ks[i], None).reshape(-1, 2)
            p2 = cv2.undistortPoints(kps[j][good[:, 1]].reshape(-1, 1, 2), Ks[j], None).reshape(-1, 2)
            E, mask = cv2.findEssentialMat(p1, p2, np.eye(3), method=cv2.RANSAC, prob=0.999, threshold=1.0 / Ks[i][0, 0])
            if E is None or mask is None:
                continue
            inl = good[mask.ravel().astype(bool)]
            if len(inl) >= 30:
                pairs[(i, j)] = inl
        if progress:
            progress(f"Mencocokkan foto {i + 1}/{n}")
    if not pairs:
        raise ValueError("Foto tidak saling cocok. Pastikan foto dari dinding yang sama, tumpang-tindih ±70 %, tanpa zoom.")
    # jejak (track) dengan union-find atas (foto, fitur)
    par: dict = {}

    def find(a):
        while par.setdefault(a, a) != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for (i, j), inl in pairs.items():
        for a, b in inl:
            ra, rb = find((i, int(a))), find((j, int(b)))
            if ra != rb:
                par[rb] = ra
    groups: dict = {}
    for key in list(par):
        groups.setdefault(find(key), []).append(key)
    tracks = []
    for mem in groups.values():
        imgs = [q[0] for q in mem]
        if len(mem) >= 2 and len(set(imgs)) == len(imgs):  # satu fitur per foto
            tracks.append({q[0]: q[1] for q in mem})
    # pasangan awal: banyak inlier dan paralaks cukup
    best, best_score = None, -1
    for (i, j), inl in pairs.items():
        p1 = cv2.undistortPoints(kps[i][inl[:, 0]].reshape(-1, 1, 2), Ks[i], None).reshape(-1, 2)
        p2 = cv2.undistortPoints(kps[j][inl[:, 1]].reshape(-1, 1, 2), Ks[j], None).reshape(-1, 2)
        H, hm = cv2.findHomography(p1, p2, cv2.RANSAC, 2.0 / Ks[i][0, 0])
        hr = float(hm.mean()) if hm is not None else 1.0
        score = len(inl) * (1.0 - hr + 0.05)  # bidang datar (homografi menjelaskan semua) = paralaks buruk
        if score > best_score:
            best, best_score = (i, j), score
    i0, j0 = best
    inl = pairs[(i0, j0)]
    p1 = cv2.undistortPoints(kps[i0][inl[:, 0]].reshape(-1, 1, 2), Ks[i0], None).reshape(-1, 2)
    p2 = cv2.undistortPoints(kps[j0][inl[:, 1]].reshape(-1, 1, 2), Ks[j0], None).reshape(-1, 2)
    E, _m = cv2.findEssentialMat(p1, p2, np.eye(3), method=cv2.RANSAC, prob=0.999, threshold=1.0 / Ks[i0][0, 0])
    _n, R, t, _mm = cv2.recoverPose(E, p1, p2)
    cams: dict[int, tuple[np.ndarray, np.ndarray]] = {i0: (np.eye(3), np.zeros(3)), j0: (R, t.ravel())}
    pts: dict[int, np.ndarray] = {}

    def P(i):
        R_, t_ = cams[i]
        return Ks[i] @ np.c_[R_, t_]

    def tri_tracks(min_angle=1.5):
        for ti, tr in enumerate(tracks):
            if ti in pts:
                continue
            vis = [i for i in tr if i in cams]
            if len(vis) < 2:
                continue
            uv = [kps[i][tr[i]] for i in vis]
            X = _triangulate([P(i) for i in vis], uv)
            if not np.all(np.isfinite(X)):
                continue
            ok = True
            rays = []
            for i, q in zip(vis, uv):
                R_, t_ = cams[i]
                xc = R_ @ X + t_
                if xc[2] <= 0:
                    ok = False
                    break
                pr = Ks[i] @ xc
                if np.hypot(*(pr[:2] / pr[2] - q)) > 3.0:
                    ok = False
                    break
                C = -R_.T @ t_
                rays.append((X - C) / np.linalg.norm(X - C))
            if not ok:
                continue
            ang = max(math.degrees(math.acos(min(1.0, float(a @ b)))) for a in rays for b in rays)
            if ang >= min_angle:
                pts[ti] = X
    tri_tracks()
    # tambah foto lain satu per satu (PnP)
    while len(cams) < n:
        cand = []
        for i in range(n):
            if i in cams:
                continue
            obs = [(ti, tracks[ti][i]) for ti in pts if i in tracks[ti]]
            cand.append((len(obs), i, obs))
        cand.sort(reverse=True)
        if not cand or cand[0][0] < 12:
            break
        _c, i, obs = cand[0]
        X = np.array([pts[ti] for ti, _f in obs])
        uv = np.array([kps[i][f] for _ti, f in obs])
        ok, rv, tv, inl_ = cv2.solvePnPRansac(X, uv, Ks[i], None, reprojectionError=3.0, iterationsCount=300, confidence=0.999,
                                              flags=cv2.SOLVEPNP_EPNP)
        if not ok or inl_ is None or len(inl_) < 10:
            break
        rv, tv = cv2.solvePnPRefineLM(X[inl_.ravel()], uv[inl_.ravel()], Ks[i], None, rv, tv)
        cams[i] = (cv2.Rodrigues(rv)[0], tv.ravel())
        tri_tracks()
        if progress:
            progress(f"Kamera {len(cams)}/{n} terpasang, {len(pts)} titik 3D")
    # penghalusan bergantian: kamera (PnP-LM semua pengamatan) lalu titik (triangulasi ulang), buang titik dengan galat besar
    for it in range(4):
        for i in list(cams):
            if i == i0:
                continue
            obs = [(ti, tracks[ti][i]) for ti in pts if i in tracks[ti]]
            if len(obs) < 8:
                continue
            X = np.array([pts[ti] for ti, _f in obs])
            uv = np.array([kps[i][f] for _ti, f in obs])
            R_, t_ = cams[i]
            rv, tv = cv2.solvePnPRefineLM(X, uv, Ks[i], None, cv2.Rodrigues(R_)[0], t_.reshape(3, 1).copy())
            cams[i] = (cv2.Rodrigues(rv)[0], tv.ravel())
        for ti in list(pts):
            vis = [i for i in tracks[ti] if i in cams]
            X = _triangulate([P(i) for i in vis], [kps[i][tracks[ti][i]] for i in vis])
            errs = []
            for i in vis:
                R_, t_ = cams[i]
                xc = R_ @ X + t_
                pr = Ks[i] @ xc
                errs.append(np.hypot(*(pr[:2] / pr[2] - kps[i][tracks[ti][i]])) if xc[2] > 0 else 1e9)
            if not np.all(np.isfinite(X)) or max(errs) > (4.0 if it < 2 else 2.5):
                del pts[ti]
            else:
                pts[ti] = X
        tri_tracks()
    # penyesuaian berkas (bundle adjustment) penuh: semua kamera + titik bersama-sama, lalu buang pencilan dan ulangi sekali
    for rnd in range(2):
        if len(cams) < 3 or len(pts) < 50:
            break
        ids = sorted(pts)
        oc_, op_, uv_ = [], [], []
        for k, t_ in enumerate(ids):
            for i in tracks[t_]:
                if i in cams:
                    oc_.append(i)
                    op_.append(k)
                    uv_.append(kps[i][tracks[t_][i]])
        if progress:
            progress(f"Penyesuaian berkas {rnd + 1}/2: {len(cams)} kamera, {len(ids)} titik")
        cams, Xb = bundle_adjust(Ks, cams, np.array([pts[t_] for t_ in ids]), np.array(oc_), np.array(op_), np.array(uv_, float),
                                 i0, j0, iters=20 if rnd == 0 else 10)
        for k, t_ in enumerate(ids):
            X = Xb[k]
            errs = []
            for i in tracks[t_]:
                if i in cams:
                    xc = cams[i][0] @ X + cams[i][1]
                    pr = Ks[i] @ xc
                    errs.append(np.hypot(*(pr[:2] / pr[2] - kps[i][tracks[t_][i]])) if xc[2] > 0 else 1e9)
            if np.all(np.isfinite(X)) and max(errs) <= 2.0:
                pts[t_] = X
            else:
                del pts[t_]
    if len(cams) < 2 or len(pts) < 50:
        raise ValueError("Rekonstruksi gagal: terlalu sedikit titik 3D. Foto kurang tumpang-tindih / terlalu kabur / dinding terlalu polos.")
    ids = sorted(pts)
    Xs = np.array([pts[t_] for t_ in ids])
    cols = []
    err_all = []
    obs_out = []
    for t_ in ids:
        vis = [i for i in tracks[t_] if i in cams]
        i = vis[0]
        u, v = kps[i][tracks[t_][i]]
        cols.append(rgbs[i][min(rgbs[i].shape[0] - 1, int(v)), min(rgbs[i].shape[1] - 1, int(u))].tolist())
        obs_out.append([[int(i), round(float(kps[i][tracks[t_][i]][0]), 2), round(float(kps[i][tracks[t_][i]][1]), 2)] for i in vis])
        for i in vis:
            R_, t2 = cams[i]
            pr = Ks[i] @ (R_ @ pts[t_] + t2)
            err_all.append(float(np.hypot(*(pr[:2] / pr[2] - kps[i][tracks[t_][i]]))))
    return {"cams": {str(i): {"K": Ks[i].tolist(), "R": cams[i][0].tolist(), "t": cams[i][1].tolist(), "k": ks[i]} for i in cams},
            "points": Xs, "colors": np.array(cols, np.uint8), "obs": obs_out,
            "n_points": len(ids), "n_cams": len(cams), "n_photos": n, "reproj_px": round(float(np.sqrt(np.mean(np.square(err_all)))), 2),
            "pairs": len(pairs)}


def build(s: O.Store, mid: int, progress=None) -> dict:
    m = load(s, mid)
    d = _mdir(s, mid)
    paths = [d / "foto" / ph["file"] for ph in m["photos"]]
    t0 = time.time()
    m["status"] = "membangun"
    save(s, m)
    try:
        res = reconstruct(paths, m["photos"], progress)
    except Exception as e:
        m = load(s, mid)
        m["status"] = "gagal"
        m["error"] = str(e)
        save(s, m)
        raise
    np.savez_compressed(d / "awan_titik.npz", points=res["points"], colors=res["colors"])
    (d / "pengamatan.json").write_text(json.dumps(res["obs"]), encoding="utf-8")
    m = load(s, mid)
    m["recon"] = {k: res[k] for k in ("cams", "n_points", "n_cams", "n_photos", "reproj_px", "pairs")}
    m["recon"]["secs"] = round(time.time() - t0, 1)
    m["status"] = "siap"
    m.pop("error", None)
    m["georef"] = solve_georef(s, m)
    for me in m.get("measures") or []:
        _measure_eval(s, m, me)
    save(s, m)
    return m


def cloud(s: O.Store, mid: int) -> tuple[np.ndarray, np.ndarray]:
    z = np.load(_mdir(s, mid) / "awan_titik.npz")
    return z["points"], z["colors"]


# ================================================================ georeferensi (similaritas 7 parameter)
def umeyama(src: np.ndarray, dst: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """dst ≈ s R src + t (kuadrat terkecil, Umeyama 1991)."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    a, b = src - mu_s, dst - mu_d
    U, S, Vt = np.linalg.svd(b.T @ a / len(src))
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    var = (a ** 2).sum() / len(src)
    sc = float(np.trace(np.diag(S) @ D) / var)
    return sc, R, mu_d - sc * R @ mu_s


def cam_center(c: dict) -> np.ndarray:
    R, t = np.array(c["R"]), np.array(c["t"])
    return -R.T @ t


def _uv_work(m: dict, i: int, uv_norm) -> np.ndarray:
    """uv ternormalisasi (0..1, dari layar) -> piksel kerja foto i."""
    ph = m["photos"][int(i)]
    k = m["recon"]["cams"][str(i)]["k"] if str(i) in (m.get("recon") or {}).get("cams", {}) else min(1.0, WORK_SIDE / max(ph["w"], ph["h"]))
    return np.array([uv_norm[0] * ph["w"] * k, uv_norm[1] * ph["h"] * k])


def gcp_model_xyz(m: dict, g: dict) -> Optional[np.ndarray]:
    cams = (m.get("recon") or {}).get("cams") or {}
    obs = [(int(i), uv) for i, uv in (g.get("obs") or {}).items() if str(i) in cams]
    if len(obs) < 2:
        return None
    Ps, uvs = [], []
    for i, uv in obs:
        c = cams[str(i)]
        Ps.append(np.array(c["K"]) @ np.c_[np.array(c["R"]), np.array(c["t"])])
        uvs.append(_uv_work(m, i, uv))
    X = _triangulate(Ps, uvs)
    return X if np.all(np.isfinite(X)) else None


def solve_georef(s: O.Store, m: dict) -> Optional[dict]:
    """Titik RTK (>= 3, masing-masing diklik di >= 2 foto) -> georef teliti; kalau tidak, posisi kamera GPS HP (>= 3) -> kasar."""
    from . import core_oclokasi as L
    rec = m.get("recon")
    if not rec:
        return None
    src, dst, names = [], [], []
    for g in m.get("gcps") or []:
        X = gcp_model_xyz(m, g)
        if X is not None and all(g.get(k) not in (None, "") for k in ("e", "n", "rl")):
            src.append(X)
            dst.append([float(g["e"]), float(g["n"]), float(g["rl"])])
            names.append(g["name"])
    out: dict[str, Any] = {}
    if len(src) >= 3:
        out["method"] = "rtk"
    else:
        cr = L.crs(s)
        src, dst, names = [], [], []
        for i, c in rec["cams"].items():
            ex = m["photos"][int(i)].get("exif") or {}
            if ex.get("lat") is None:
                continue
            E, N, _z, _s = L.to_utm(ex["lat"], ex["lon"], cr.get("zone"), cr.get("south") if cr.get("zone") else None)
            src.append(cam_center(c))
            dst.append([E, N, ex.get("alt") if ex.get("alt") is not None else 0.0])
            names.append(m["photos"][int(i)]["name"])
        if len(src) < 3:
            return {"method": None, "msg": "Belum berskala: klik minimal 3 titik RTK (masing-masing di >= 2 foto), atau pakai foto ber-GPS."}
        out["method"] = "gps"
    src, dst = np.array(src), np.array(dst)
    o = dst.mean(0)
    sc, R, t = umeyama(src, dst - o)
    fit = (sc * src @ R.T + t) + o
    res = fit - dst
    if out["method"] == "gps":  # tinggi GPS HP sangat kasar: hanya E, N yang dipercaya untuk skala; RL tetap ikut rata-rata
        pass
    out.update(scale=sc, R=R.tolist(), t=(t + o).tolist(), rms=round(float(np.sqrt((res ** 2).sum(1).mean())), 3),
               residuals=[{"name": nm, "de": round(float(r[0]), 3), "dn": round(float(r[1]), 3), "drl": round(float(r[2]), 3),
                           "err": round(float(np.linalg.norm(r)), 3)} for nm, r in zip(names, res)], n=len(names))
    if out["method"] == "gps":
        out["msg"] = (f"Skala & arah dari posisi kamera GPS HP ({len(names)} foto, RMS {out['rms']:.1f} m): KASAR. "
                      "Strike / dip bisa melenceng beberapa derajat; klik titik RTK untuk hasil teliti.")
    return out


def to_world(m: dict, X: np.ndarray) -> np.ndarray:
    g = m.get("georef") or {}
    if not g.get("method"):
        return X
    return g["scale"] * X @ np.array(g["R"]).T + np.array(g["t"])


# ================================================================ titik permukaan & pengukuran bidang
def surface_points(s: O.Store, m: dict, i: int, uvs: list, k_nn: int = 10) -> tuple[np.ndarray, list[bool]]:
    """Titik 3D (koordinat model) di permukaan untuk klik di foto i: kedalaman dari titik awan terdekat di foto itu."""
    rec = m["recon"]
    c = rec["cams"].get(str(i))
    if not c:
        raise ValueError("Foto ini tidak ikut terpasang di model 3D; pilih foto lain.")
    K, R, t = np.array(c["K"]), np.array(c["R"]), np.array(c["t"])
    X, _col = cloud(s, m["id"])
    pr, z = _proj(K, R, t, X)
    ph = m["photos"][int(i)]
    W, H = ph["w"] * c["k"], ph["h"] * c["k"]
    ok = (z > 0) & (pr[:, 0] >= 0) & (pr[:, 0] < W) & (pr[:, 1] >= 0) & (pr[:, 1] < H)
    pr, z = pr[ok], z[ok]
    out, good = [], []
    Kinv = np.linalg.inv(K)
    for uvn in uvs:
        q = _uv_work(m, i, uvn)
        d = np.hypot(pr[:, 0] - q[0], pr[:, 1] - q[1])
        nn = np.argsort(d)[:k_nn]
        if not len(nn):
            out.append(np.array([np.nan] * 3))
            good.append(False)
            continue
        w = 1.0 / (d[nn] + 2.0)
        zz = float((z[nn] * w).sum() / w.sum())
        good.append(bool(d[nn[0]] < 0.04 * max(W, H)))
        ray = Kinv @ np.array([q[0], q[1], 1.0])
        Xc = ray * zz
        out.append(R.T @ (Xc - t))
    return np.array(out), good


def plane_fit(P: np.ndarray) -> dict:
    """Bidang terbaik (SVD) di koordinat dunia (E, N, RL): dip, arah dip, strike (aturan tangan kanan), mutu."""
    c = P.mean(0)
    _u, sv, vt = np.linalg.svd(P - c)
    n = vt[2]
    if n[2] < 0:
        n = -n
    dip = math.degrees(math.acos(min(1.0, abs(float(n[2])))))
    ddir = (math.degrees(math.atan2(float(n[0]), float(n[1]))) + 360) % 360 if dip > 0.05 else 0.0
    rms = float(np.sqrt(np.mean(((P - c) @ n) ** 2)))
    span = float(sv[0] / math.sqrt(len(P)))
    lin = float(sv[1] / sv[0]) if sv[0] > 0 else 0.0           # 0 = titik segaris (orientasi tak tentu)
    flat = float(sv[2] / sv[1]) if sv[1] > 0 else 1.0          # 0 = sangat rata
    if lin < 0.04:  # derau titik permukaan sendiri ~0,03 pada garis lurus
        q, note = "tidak pasti", "Titik hampir segaris: jejak harus melintasi permukaan yang tidak rata (sudut / tonjolan dinding)."
    elif flat > 0.5:
        q, note = "lemah", "Titik tidak membentuk bidang yang jelas (sebaran 3D besar)."
    elif lin < 0.12:
        q, note = "sedang", "Jejak hanya sedikit melengkung di permukaan: arah dip bisa melenceng beberapa derajat. Tambah titik di bagian dinding yang menghadap arah lain."
    else:
        q, note = "baik", ""
    return {"dip": round(dip, 1), "ddir": round(ddir, 1), "strike": round((ddir - 90) % 360, 1), "rms": round(rms, 3),
            "n": int(len(P)), "center": [round(float(x), 3) for x in c], "lin": round(lin, 3), "flat": round(flat, 3),
            "span": round(span, 2), "quality": q, "note": note, "normal": [round(float(x), 5) for x in n]}


def _measure_eval(s: O.Store, m: dict, me: dict) -> None:
    if not (m.get("recon") and (m.get("georef") or {}).get("method")):
        me["result"] = None
        return
    Pm, good = surface_points(s, m, me["img"], me["pts"])
    Pm = Pm[np.array(good) & np.all(np.isfinite(Pm), axis=1)]
    if len(Pm) < 3:
        me["result"] = {"error": "Titik di luar awan titik model (klik di bagian dinding yang terekonstruksi)."}
        return
    me["result"] = plane_fit(to_world(m, Pm))
    me["result"]["georef"] = m["georef"]["method"]


def add_measure(s: O.Store, mid: int, name: str, kind: str, img: int, pts: list, by: str) -> dict:
    m = load(s, mid)
    if not m.get("recon"):
        raise ValueError("Bangun model 3D dulu.")
    if len(pts) < 3:
        raise ValueError("Klik minimal 3 titik di sepanjang jejak / di bidang (disarankan 6+ melintasi permukaan tidak rata).")
    me = {"id": max((x["id"] for x in m["measures"]), default=0) + 1, "name": name.strip() or f"Bidang {len(m['measures']) + 1}",
          "kind": kind if kind in ("vein", "kekar", "sesar", "kontak", "lain") else "lain", "img": int(img),
          "pts": [[round(float(u), 6), round(float(v), 6)] for u, v in pts], "by": by, "at": core_io.now()}
    _measure_eval(s, m, me)
    m["measures"].append(me)
    save(s, m)
    return me


def del_measure(s: O.Store, mid: int, meid: int) -> None:
    m = load(s, mid)
    m["measures"] = [x for x in m["measures"] if x["id"] != meid]
    save(s, m)


def detect_targets(path: Path, max_n: int = 30) -> list[dict]:
    """Usulan posisi titik cat di foto: bercak kecil berwarna mencolok (pink / magenta, merah terang, oranye, kuning
    neon) yang jarang ada di batuan. Hasil uv ternormalisasi (0..1) + warna; nama titik dipilih geologist."""
    cv2 = _cv2()
    from PIL import Image, ImageOps
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        k = min(1.0, 1600 / max(im.size))
        if k < 1:
            im = im.resize((round(im.width * k), round(im.height * k)))
        a = np.asarray(im)
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    h, sat, val = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    out = []
    for name, m in (("pink / magenta", ((h >= 140) & (h <= 172))), ("kuning neon", ((h >= 25) & (h <= 38)))):
        mk = (m & (sat > 140) & (val > 140)).astype(np.uint8)
        mk = cv2.morphologyEx(mk, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, comp, stats, cen = cv2.connectedComponentsWithStats(mk, connectivity=8)
        H, W = mk.shape
        for i in range(1, n):
            ar = stats[i, cv2.CC_STAT_AREA]
            w_, h_ = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            if ar < 6 or ar > 0.002 * H * W or max(w_, h_) > 4 * min(w_, h_) + 2:
                continue
            out.append({"u": round(float(cen[i][0]) / W, 6), "v": round(float(cen[i][1]) / H, 6), "color": name, "px": int(ar)})
    out.sort(key=lambda d: -d["px"])
    return out[:max_n]


def save_gcps(s: O.Store, mid: int, gcps: list[dict]) -> dict:
    m = load(s, mid)
    clean = []
    for g in gcps:
        nm = str(g.get("name") or "").strip()
        if not nm:
            continue
        def f(v):
            try:
                return float(str(v).replace(",", ".")) if v not in (None, "") else None
            except ValueError:
                raise ValueError(f"Titik {nm}: E / N / RL harus angka.") from None
        obs = {str(int(k)): [round(float(a), 6), round(float(b), 6)] for k, (a, b) in (g.get("obs") or {}).items()}
        clean.append({"name": nm, "e": f(g.get("e")), "n": f(g.get("n")), "rl": f(g.get("rl")), "obs": obs})
    if len({g["name"] for g in clean}) != len(clean):
        raise ValueError("Nama titik RTK ganda.")
    m["gcps"] = clean
    m["georef"] = solve_georef(s, m)
    for me in m["measures"]:
        _measure_eval(s, m, me)
    save(s, m)
    return m


# ================================================================ tampilan & ekspor
def views_png(s: O.Store, mid: int) -> Optional[str]:
    """Denah & tampak dinding awan titik (koordinat dunia) dengan kamera dan bidang terukur (simbol strike / dip)."""
    m = load(s, mid)
    if not m.get("recon"):
        return None
    X, col = cloud(s, mid)
    W = to_world(m, X)
    o = W.mean(0)
    cams = np.array([to_world(m, cam_center(c)[None])[0] for c in m["recon"]["cams"].values()])
    from .core_qaqc import _CHART_LOCK, _plt
    with _CHART_LOCK:
        plt = _plt()
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(5.2, 7.4), gridspec_kw={"height_ratios": [1.1, 1]})
        c = col / 255.0
        a1.scatter(W[:, 0] - o[0], W[:, 1] - o[1], s=2.0, c=c, lw=0)
        a1.scatter(cams[:, 0] - o[0], cams[:, 1] - o[1], marker="^", s=30, c="#1c7ed6", edgecolors="white", lw=0.6, zorder=4)
        a1.set_aspect("equal")
        a1.set_title("Denah (U ke atas)", fontsize=8.5)
        # tampak: sumbu mendatar = arah utama dinding
        _u, _s, vt = np.linalg.svd((W - o)[:, :2], full_matrices=False)
        ax_h = np.r_[vt[0], 0.0]
        a2.scatter((W - o) @ ax_h, W[:, 2], s=2.0, c=c, lw=0)
        a2.set_aspect("equal")
        a2.set_title("Tampak dinding (RL)", fontsize=8.5)
        for me in m.get("measures") or []:
            r = me.get("result") or {}
            if not r or r.get("error"):
                continue
            p = np.array(r["center"])
            a1.plot(p[0] - o[0], p[1] - o[1], "o", color="#C0392B", ms=4, zorder=5)
            st = math.radians(r["strike"])
            L = 1.5
            a1.plot([p[0] - o[0] - L * math.sin(st), p[0] - o[0] + L * math.sin(st)], [p[1] - o[1] - L * math.cos(st), p[1] - o[1] + L * math.cos(st)],
                    color="#C0392B", lw=1.6, zorder=5)
            dd = math.radians(r["ddir"])
            a1.plot([p[0] - o[0], p[0] - o[0] + 0.6 * math.sin(dd)], [p[1] - o[1], p[1] - o[1] + 0.6 * math.cos(dd)], color="#C0392B", lw=1.6, zorder=5)
            a1.annotate(f"{me['name']} {r['dip']:.0f}/{r['ddir']:03.0f}", (p[0] - o[0], p[1] - o[1]), xytext=(4, 4), textcoords="offset points",
                        fontsize=6.5, color="#C0392B")
            a2.plot(p @ ax_h - o @ ax_h, p[2], "o", color="#C0392B", ms=4)
        for a in (a1, a2):
            a.tick_params(labelsize=6.5)
            a.grid(alpha=0.25)
        geo = m.get("georef") or {}
        fig.suptitle(f"{m['name']} — {m['recon']['n_points']:,} titik 3D, {m['recon']['n_cams']}/{m['recon']['n_photos']} foto\n"
                     + ({"rtk": f"georef RTK, RMS {geo.get('rms', 0):.3f} m", "gps": f"georef GPS HP (kasar), RMS {geo.get('rms', 0):.1f} m"}
                        .get(geo.get("method"), "belum berskala")) + f"\nsumbu (m) relatif terhadap E {o[0]:,.1f} · N {o[1]:,.1f}",
                     fontsize=8)
        fig.tight_layout()
        b = io.BytesIO()
        fig.savefig(b, format="png", dpi=140, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    return base64.b64encode(b.getvalue()).decode()


def export(s: O.Store, mid: int, fmt: str) -> bytes:
    m = load(s, mid)
    if fmt == "csv":  # bidang terukur
        rows = ["Model,Nama,Jenis,E,N,RL,Dip,Arah_dip,Strike_RHR,RMS_m,Jumlah_titik,Mutu,Georef,Catatan"]
        for me in m.get("measures") or []:
            r = me.get("result") or {}
            if not r or r.get("error"):
                continue
            e, n, z = r["center"]
            rows.append(f"{m['name']},{me['name']},{me['kind']},{e:.3f},{n:.3f},{z:.3f},{r['dip']},{r['ddir']},{r['strike']},{r['rms']},"
                        f"{r['n']},{r['quality']},{r['georef']},\"{r['note']}\"")
        return ("\n".join(rows) + "\n").encode("utf-8-sig")
    if fmt == "str":  # Surpac: satu titik per bidang (D1 jenis, D2 nama, D3 dip, D4 arah dip, D5 strike) + jejak 3D
        lines = [f"{m['name']},{time.strftime('%d-%b-%y')},,", "0, 0.000, 0.000, 0.000,"]
        for me in m.get("measures") or []:
            r = me.get("result") or {}
            if not r or r.get("error"):
                continue
            e, n, z = r["center"]
            lines.append(f"{12}, {n:.3f}, {e:.3f}, {z:.3f}, {me['kind']}, {me['name']}, {r['dip']}, {r['ddir']}, {r['strike']}")
            lines.append("0, 0.000, 0.000, 0.000,")
        lines.append("0, 0.000, 0.000, 0.000, END")
        return ("\n".join(lines) + "\n").encode("ascii", "replace")
    if fmt == "ply":
        X, col = cloud(s, mid)
        W = to_world(m, X)
        b = io.StringIO()
        b.write(f"ply\nformat ascii 1.0\ncomment DB-Ex model 3D {m['name']}\nelement vertex {len(W)}\n"
                "property double x\nproperty double y\nproperty double z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n")
        for p, c in zip(W, col):
            b.write(f"{p[0]:.3f} {p[1]:.3f} {p[2]:.3f} {c[0]} {c[1]} {c[2]}\n")
        return b.getvalue().encode("ascii")
    raise ValueError("Format ekspor tidak dikenal (csv / str / ply).")


# ================================================================ API
class FBody(BaseModel):
    folder: str
    by: str = ""


class NewBody(FBody):
    name: str = ""
    paths: list[str]


class MidBody(FBody):
    id: int


class GcpBody(FBody):
    id: int
    gcps: list[dict[str, Any]]


class MeasBody(FBody):
    id: int
    name: str = ""
    kind: str = "vein"
    img: int
    pts: list[list[float]]


class MeDelBody(FBody):
    id: int
    measure: int


class ExpBody(FBody):
    id: int
    fmt: str


class ImgBody(FBody):
    id: int
    img: int


@router.post("/list")
def api_list(b: FBody) -> dict:
    return {"ok": True, "models": models(O.store(b.folder))}


@router.post("/create")
def api_create(b: NewBody) -> dict:
    return {"ok": True, "model": create(O.store(b.folder), b.name, b.paths, b.by)}


@router.post("/get")
def api_get(b: MidBody) -> dict:
    return {"ok": True, "model": load(O.store(b.folder), b.id)}


@router.post("/build")
def api_build(b: MidBody) -> dict:
    return {"ok": True, "model": build(O.store(b.folder), b.id)}


@router.post("/gcps")
def api_gcps(b: GcpBody) -> dict:
    return {"ok": True, "model": save_gcps(O.store(b.folder), b.id, b.gcps)}


@router.post("/measure")
def api_measure(b: MeasBody) -> dict:
    s = O.store(b.folder)
    me = add_measure(s, b.id, b.name, b.kind, b.img, b.pts, b.by)
    return {"ok": True, "measure": me, "model": load(s, b.id)}


@router.post("/measure/delete")
def api_measure_del(b: MeDelBody) -> dict:
    s = O.store(b.folder)
    del_measure(s, b.id, b.measure)
    return {"ok": True, "model": load(s, b.id)}


@router.post("/views")
def api_views(b: MidBody) -> dict:
    return {"ok": True, "png": views_png(O.store(b.folder), b.id)}


@router.post("/export")
def api_export(b: ExpBody):
    from fastapi.responses import Response
    return Response(export(O.store(b.folder), b.id, b.fmt), media_type="application/octet-stream")


@router.post("/delete")
def api_delete(b: MidBody) -> dict:
    s = O.store(b.folder)
    delete(s, b.id)
    return {"ok": True, "models": models(s)}


@router.post("/targets")
def api_targets(b: ImgBody) -> dict:
    return {"ok": True, "targets": detect_targets(photo_path(O.store(b.folder), b.id, b.img))}


@router.post("/photo")
def api_photo(b: ImgBody) -> dict:
    return {"ok": True, "path": str(photo_path(O.store(b.folder), b.id, b.img))}
