"""Analisis foto singkapan DB-Ex (Fase 1): usulan otomatis yang diperiksa geologist.

1. Segmentasi SAM otomatis: grid titik -> SAM (SlimSAM, ONNX, CPU) -> mask stabil -> partisi zona tanpa tumpang-tindih
   -> poligon draf. Label dari warna & bentuk (oksida / vein kuarsa / litologi), atau dari AI vision lokal (Ollama) yang
   melihat foto bernomor zona.
2. Peta warna terukur: indeks oksida besi (merah-kuning-coklat) dan vein kuarsa (putih, lebih terang dari sekitarnya);
   % luas per foto dan per zona yang sudah didigitasi, m² bila foto bergeoreferensi / punya garis skala.
3. Struktur & geoteknik: deteksi jejak kekar / vein (Canny + Hough, segmen segaris digabung) sebagai garis draf,
   orientasi & set kekar, rose diagram, scanline (frekuensi, spasi per set, kelas spasi ISRM), Jv & RQD perkiraan
   (Palmström) dan bantuan GSI (tabel Hoek-Marinos). Semua angka geoteknik adalah BANTUAN, bukan pengganti penilaian.

Semua usulan disimpan sebagai fitur draf (attrs["_draft"]) di core_outcrop: tampil putus-putus, tidak ikut ekspor sampai
diterima. Pustaka berat (cv2, onnxruntime, matplotlib) diimpor saat dipakai."""
from __future__ import annotations

import base64
import importlib
import io
import math
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from . import core_io
from . import core_outcrop as O

router = APIRouter(prefix="/core/outcrop/an", tags=["core-outcrop-analisis"])

STRUCT_KINDS = ("kekar", "vein", "sesar")
GRID = {"kasar": 10, "sedang": 16, "halus": 22}
WORK = 768  # sisi panjang peta kerja segmentasi (piksel)


def _cv2():
    try:
        return importlib.import_module("cv2")
    except ImportError:
        raise RuntimeError("OpenCV tidak terpasang di DB-Ex ini. Pasang ulang DB-Ex versi Qt terbaru.") from None


def _rgb(path: Path, long_side: int) -> np.ndarray:
    from PIL import Image, ImageOps
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        k = long_side / max(im.size)
        if k < 1:
            im = im.resize((max(8, round(im.width * k)), max(8, round(im.height * k))), Image.BILINEAR)
        return np.asarray(im)


def _ctx(s: O.Store, pid: int) -> tuple[dict, Path, Optional[dict], Optional[float]]:
    """Foto, path, solusi georef (bila ok) dan meter per piksel ukuran asli (georef, atau garis skala)."""
    r = O.photo(s, pid)
    f = s.photos / r["file"]
    if not f.exists():
        raise ValueError("File foto singkapan hilang dari folder proyek.")
    sol = O.georef_solve(r.get("georef"), r["w"], r["h"], O.plane_kind(r))
    sol = sol if sol and sol.get("ok") else None
    mpp = sol["m_per_px"] if sol else ((O.scale_info(s, pid, r) or {}).get("m_per_px"))
    return r, f, sol, mpp


def _kind_ok(s: O.Store, want: str, fallback: str) -> str:
    ks = {k["key"] for k in O.kinds(s)}
    return want if want in ks else fallback


def _b64png(arr: np.ndarray) -> str:
    from PIL import Image
    b = io.BytesIO()
    Image.fromarray(arr).save(b, "PNG", optimize=True)
    return base64.b64encode(b.getvalue()).decode()


def _drafts_of(s: O.Store, pid: int, src: str) -> list[dict]:
    return [f for f in O.features(s, pid) if (f.get("attrs") or {}).get(O.DRAFT) == src]


# ================================================================ 1. segmentasi SAM otomatis
def sam_regions(path: Path, key: str, grid: int = 16, iou_min: float = 0.80, stab_min: float = 0.85) -> tuple[np.ndarray, list[dict]]:
    """Partisi foto dari mask SAM stabil. Kembalikan peta label (sisi panjang WORK, -1 = tanpa zona) dan daftar region."""
    from . import core_vision
    cv2 = _cv2()
    e = core_vision.sam_embed(path, key)
    dec = core_vision._session("sam_dec")
    g = max(4, min(32, int(grid)))
    us = (np.arange(g) + 0.5) / g
    P = np.array([[u * e["W"] * e["k"], v * e["H"] * e["k"]] for v in us for u in us], np.float32)
    hh, ww = max(1, round(e["nh"] / 4)), max(1, round(e["nw"] / 4))
    kk = WORK / max(e["W"], e["H"])
    Wk, Hk = max(8, round(e["W"] * kk)), max(8, round(e["H"] * kk))
    cand: list[tuple[float, np.ndarray]] = []
    for i in range(0, len(P), 8):  # 8 prompt per panggilan: memori puncak ~0,4 GB di atas embedding (64 prompt: >2,5 GB)
        p = P[i:i + 8][None, :, None, :]
        lab = np.ones(p.shape[:3], np.int64)
        iou, masks = dec.run(None, {"input_points": p, "input_labels": lab, "image_embeddings": e["emb"],
                                    "image_positional_embeddings": e["pos"]})
        for j in range(masks.shape[1]):
            for lv in range(3):
                sc = float(iou[0, j, lv])
                if sc < iou_min:
                    continue
                m = masks[0, j, lv, :hh, :ww]
                hi, lo = int((m > 1.0).sum()), int((m > -1.0).sum())
                if not lo or hi / lo < stab_min:
                    continue
                full = cv2.resize(m.astype(np.float32), (Wk, Hk), interpolation=cv2.INTER_LINEAR) > 0
                fr = float(full.mean())
                if fr < 0.004 or fr > 0.70:
                    continue
                cand.append((sc * hi / lo, full))
    cand.sort(key=lambda t: -t[0])
    kept: list[np.ndarray] = []
    for _sc, m in cand:  # NMS
        a = m.sum()
        if all((m & k).sum() / max(1, a + k.sum() - (m & k).sum()) < 0.6 for k in kept):
            kept.append(m)
        if len(kept) >= 40:
            break
    L = -np.ones((Hk, Wk), np.int32)
    for i, m in sorted(enumerate(kept), key=lambda t: -t[1].sum()):  # zona kecil di atas zona besar
        L[m] = i
    regions = []
    min_px = 0.003 * Hk * Wk
    for i in range(len(kept)):
        m = (L == i).astype(np.uint8)
        n, comp, stats, _c = cv2.connectedComponentsWithStats(m, connectivity=4)
        for c in range(1, n):
            if stats[c, cv2.CC_STAT_AREA] < min_px:
                L[comp == c] = -1
    out_L = -np.ones_like(L)
    rid = 0
    for i in range(len(kept)):
        m = (L == i).astype(np.uint8)
        n, comp, stats, _c = cv2.connectedComponentsWithStats(m, connectivity=4)
        for c in range(1, n):
            if stats[c, cv2.CC_STAT_AREA] < min_px:
                continue
            mk = comp == c
            out_L[mk] = rid
            regions.append({"id": rid + 1, "px": int(mk.sum()), "pct": round(100 * float(mk.mean()), 1)})
            rid += 1
    return out_L, regions


def merge_regions(L: np.ndarray, rgb: np.ndarray, de: float = 15.0, gap: int = 5) -> tuple[np.ndarray, list[dict]]:
    """Gabungkan zona SAM bertetangga yang warnanya mirip (ΔE Lab < de). SAM sering memecah satu zona geologi menjadi
    blok-blok di antara kekar; blok sewarna yang hanya dipisah jejak kekar tipis (<= gap piksel) disatukan, celahnya diisi."""
    cv2 = _cv2()
    ids = [i for i in np.unique(L) if i >= 0]
    if not ids:
        return L, []
    lab = O._lab(rgb.astype(np.float64) / 255.0)
    mean = {i: lab[L == i].mean(0) for i in ids}
    par = {i: i for i in ids}

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    k = np.ones((2 * gap + 1, 2 * gap + 1), np.uint8)
    dil = {i: cv2.dilate((L == i).astype(np.uint8), k).astype(bool) for i in ids}
    for a in ids:
        for b in ids:
            if b <= a or not (dil[a] & dil[b]).any():
                continue
            if float(np.linalg.norm(mean[a] - mean[b])) < de:
                ra, rb = find(a), find(b)
                if ra != rb:
                    par[rb] = ra
    groups: dict[int, list[int]] = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    out = -np.ones_like(L)
    regions = []
    for n, (_r, mem) in enumerate(sorted(groups.items(), key=lambda t: -sum(int((L == i).sum()) for i in t[1]))):
        m = np.isin(L, mem).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)  # isi jejak kekar di antara blok
        m = m.astype(bool) & (out < 0)
        out[m] = n
        regions.append({"id": n + 1, "px": int(m.sum()), "pct": round(100 * float(m.mean()), 1), "parts": len(mem)})
    return out, regions


def grow_regions(L: np.ndarray, rgb: np.ndarray, de: float = 18.0, it: int = 80) -> np.ndarray:
    """Tumbuhkan zona ke piksel yang belum ber-zona (tidak tercakup mask SAM) bila warnanya dekat dengan rata-rata zona."""
    cv2 = _cv2()
    ids = [i for i in np.unique(L) if i >= 0]
    if not ids:
        return L
    lab = O._lab(rgb.astype(np.float64) / 255.0)
    L = L.copy()
    mean = {i: lab[L == i].mean(0) for i in ids}
    dist = {i: np.linalg.norm(lab - mean[i], axis=-1) for i in ids}
    k = np.ones((3, 3), np.uint8)
    for _ in range(it):
        free = L < 0
        if not free.any():
            break
        changed = False
        best = np.full(L.shape, np.inf)
        cand = -np.ones_like(L)
        for i in ids:
            ring = cv2.dilate((L == i).astype(np.uint8), k).astype(bool) & free & (dist[i] < de)
            upd = ring & (dist[i] < best)
            best[upd], cand[upd] = dist[i][upd], i
        m = cand >= 0
        if m.any():
            L[m] = cand[m]
            changed = True
        if not changed:
            break
    return L


def _region_label(rgb: np.ndarray, mk: np.ndarray, ks: set) -> tuple[str, str]:
    """Jenis & nama dari warna rata-rata (Lab) dan bentuk (perbandingan sisi persegi panjang terkecil)."""
    cv2 = _cv2()
    lab = O._lab(rgb[mk].astype(np.float64) / 255.0).mean(0)
    nm, oxid = O._color_name(lab)
    L, C = float(lab[0]), math.hypot(float(lab[1]), float(lab[2]))
    cs, _h = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    elong = 1.0
    if cs:
        (_x, _y), (a, b), _ang = cv2.minAreaRect(max(cs, key=cv2.contourArea))
        elong = max(a, b) / max(1e-6, min(a, b))
    hue = (math.degrees(math.atan2(float(lab[2]), float(lab[1]))) + 360) % 360
    if float(lab[2]) < -6 and L > 55:
        return "abaikan", "langit"
    if 100 <= hue <= 170 and C > 14 and L < 60:
        return "abaikan", "vegetasi"
    if oxid and "zona_oks" in ks:
        return "zona_oks", f"oksida / gossan ({nm})"
    if L > 68 and C < 14 and elong > 3.0 and "zona_vein" in ks:
        return "zona_vein", f"vein kuarsa? ({nm})"
    if L > 66 and C < 16 and "zona_alt" in ks:
        return "zona_alt", f"alterasi pucat / argilik? ({nm})"
    return ("zona_lito" if "zona_lito" in ks else sorted(ks)[0]), nm


def _numbered(rgb: np.ndarray, L: np.ndarray, regions: list[dict]) -> np.ndarray:
    """Foto dengan batas zona & nomor besar di titik terdalam tiap zona (untuk AI vision)."""
    cv2 = _cv2()
    im = rgb.copy()
    for rg in regions:
        mk = (L == rg["id"] - 1).astype(np.uint8)
        cs, _h = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(im, cs, -1, (255, 255, 255), 3)
        cv2.drawContours(im, cs, -1, (230, 20, 60), 1)
    for rg in regions:
        mk = (L == rg["id"] - 1).astype(np.uint8)
        d = cv2.distanceTransform(mk, cv2.DIST_L2, 3)
        y, x = np.unravel_index(int(np.argmax(d)), d.shape)
        t = str(rg["id"])
        sc = 0.6 if max(L.shape) <= 800 else 0.9
        (tw, th), _b = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, sc, 2)
        cv2.rectangle(im, (x - tw // 2 - 3, y - th // 2 - 4), (x + tw // 2 + 3, y + th // 2 + 4), (255, 255, 255), -1)
        cv2.putText(im, t, (x - tw // 2, y + th // 2), cv2.FONT_HERSHEY_SIMPLEX, sc, (20, 20, 20), 2, cv2.LINE_AA)
    return im


def ai_schema(keys: list[str]) -> dict:
    return {"type": "object", "required": ["regions"], "properties": {
        "regions": {"type": "array", "items": {"type": "object", "required": ["id", "kind"], "properties": {
            "id": {"type": "integer"}, "kind": {"type": "string", "enum": keys + ["abaikan"]}, "name": {"type": "string"},
            "confidence": {"type": "string", "enum": ["tinggi", "sedang", "rendah"]}}}},
        "notes": {"type": "string"}}}


def ai_prompt(ks: list[dict], n: int, extra: str = "", desc: Optional[dict] = None) -> str:
    lst = "\n".join(f"- {k['key']}: {k['name']}" for k in ks)
    d = "; ".join(f"{k}: {v}" for k, v in (desc or {}).items() if v and k in ("lithology", "alteration", "oxidation", "veins", "weathering", "zones"))
    return ("Anda geologist lapangan tambang emas epitermal. Foto singkapan / dinding pit ini sudah dibagi menjadi zona bernomor "
            f"1 sampai {n} (batas merah-putih, nomor di dalam kotak putih).\n"
            "Untuk SETIAP nomor, tentukan jenis zona geologinya dari daftar berikut (kind):\n"
            f"{lst}\n- abaikan: bukan batuan (langit, vegetasi, bayangan, alat, air, pita ukur)\n"
            "Isi name dengan nama singkat yang menjelaskan (mis. 'Tuf lapili propilitik', 'Gossan limonit', 'Vein kuarsa'), "
            "dan confidence tinggi / sedang / rendah. Nilai hanya yang terlihat; bila ragu, pilih zona litologi dengan confidence rendah.\n"
            + (f"Deskripsi foto yang sudah ada: {d}\n" if d else "")
            + (f"Catatan tambahan dari geologist: {extra.strip()}\n" if extra and extra.strip() else "")
            + "Jawab hanya JSON sesuai skema.")


def propose_sam(s: O.Store, pid: int, grid: str | int = "sedang", ai: Optional[dict] = None, by: str = "") -> dict:
    """Usulan zona dari segmentasi SAM otomatis (draf "sam"). ai = {"host", "model", "extra", "max_px"} untuk label AI vision."""
    from . import core_vision
    if not core_vision.status()["sam"]:
        raise RuntimeError("SAM tidak tersedia di DB-Ex ini (model / ONNX Runtime / OpenCV tidak ditemukan). Pasang ulang DB-Ex versi Qt.")
    cv2 = _cv2()
    r, f, _sol, _mpp = _ctx(s, pid)
    g = GRID.get(str(grid), None) or int(grid)
    L, regions = sam_regions(f, f"{s.root}|{r['file']}", g)
    Hk, Wk = L.shape
    rgb = _rgb(f, max(Hk, Wk))
    if rgb.shape[:2] != (Hk, Wk):
        rgb = cv2.resize(rgb, (Wk, Hk), interpolation=cv2.INTER_AREA)
    ks_all = [k for k in O.kinds(s) if k["shape"] == "poly" and k["key"] not in O.AUTO_SKIP]
    ks = {k["key"] for k in ks_all}
    n_raw = len(regions)
    L, regions = merge_regions(L, rgb)
    L, regions = merge_regions(grow_regions(L, rgb), rgb)
    labels = {rg["id"]: _region_label(rgb, L == rg["id"] - 1, ks) + ("",) for rg in regions}
    notes, model = "", ""
    if ai and ai.get("model") and regions:
        model = ai["model"]
        im = _numbered(rgb, L, regions)
        from PIL import Image
        b = io.BytesIO()
        Image.fromarray(im).save(b, "JPEG", quality=88)
        body = {"model": model, "stream": False, "keep_alive": "15m", "options": {"temperature": 0, "num_ctx": 16384},
                "format": ai_schema(sorted(ks)),
                "messages": [{"role": "user", "content": ai_prompt(ks_all, len(regions), ai.get("extra") or "", r.get("desc")),
                              "images": [base64.b64encode(b.getvalue()).decode()]}]}
        j = core_io._http((ai.get("host") or core_io.DEFAULT_HOST).rstrip("/") + "/api/chat", body, timeout=float(ai.get("timeout") or 900))
        if j.get("error"):
            raise RuntimeError("Ollama: " + str(j["error"]))
        res = core_io._parse_json((j.get("message") or {}).get("content", ""))
        notes = str(res.get("notes") or "")
        for it in res.get("regions") or []:
            try:
                rid = int(it.get("id"))
            except (TypeError, ValueError):
                continue
            if rid in labels and (it.get("kind") in ks or it.get("kind") == "abaikan"):
                labels[rid] = (it["kind"], (it.get("name") or "").strip()[:60] or labels[rid][1], it.get("confidence") or "")
    O.clear_drafts(s, pid, "sam")
    made, dropped = [], 0
    for rg in regions:
        kind, nm, conf = labels[rg["id"]]
        if kind == "abaikan":
            dropped += 1
            continue
        poly = core_vision.mask_polygon(L == rg["id"] - 1, 60)
        if len(poly) < 3:
            continue
        try:
            j = O.save_feature(s, pid, None, {"kind": kind, "pts": poly, "name": f"Usulan {rg['id']}: {nm}",
                                              "src": "auto:sam" + (f"+ai:{model}" if model else ""),
                                              "attrs": {O.DRAFT: "sam", "_pct": rg["pct"], "_conf": conf}}, by or "auto")
            made.append(j["id"])
        except ValueError:
            continue
    with s.lock, s.conn() as c:
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                  (pid, "usulan segmentasi SAM", None, f"{len(made)} zona (grid {g}" + (f", label AI {model}" if model else ", label warna") + ")",
                   "auto:sam", by or "auto", core_io.now()))
    return {"made": made, "dropped": dropped, "regions": len(regions), "raw": n_raw, "notes": notes, "features": O.features(s, pid)}


# ================================================================ 2. peta warna terukur
INDEX = {"oks": ("Oksida besi (merah-kuning-coklat)", (232, 89, 12)), "kuarsa": ("Vein kuarsa (putih, lebih terang dari sekitar)", (34, 184, 207))}


def index_mask(rgb: np.ndarray, kind: str, sens: int = 5) -> np.ndarray:
    """Mask indeks warna. sens 1 (ketat) .. 10 (longgar)."""
    cv2 = _cv2()
    sens = max(1, min(10, int(sens)))
    lab = O._lab(rgb.astype(np.float64) / 255.0)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    h = (np.degrees(np.arctan2(b, a)) + 360) % 360
    if kind == "oks":
        c0 = 19.0 - sens          # kroma minimum
        m = (C >= c0) & (h >= 15) & (h <= 95) & (L > 12) & (L < 88)
    elif kind == "kuarsa":
        sig = max(3.0, 0.02 * max(rgb.shape[:2]))
        Lloc = L - cv2.GaussianBlur(L.astype(np.float32), (0, 0), sig)
        # putih / krem (vein kuarsa sering bernoda oksida tipis), lebih terang dari sekitarnya; langit (kebiruan) tidak ikut
        m = (L >= 80 - 1.6 * sens) & (C <= 10 + 1.0 * sens) & (b > -2.0) & (Lloc >= 9 - 0.6 * sens)
    else:
        raise ValueError("Jenis indeks tidak dikenal (oks / kuarsa).")
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, comp, stats, _c = cv2.connectedComponentsWithStats(m, connectivity=8)
    small = 0.0004 * m.size
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < small:
            m[comp == i] = 0
    return m.astype(bool)


def _poly_mask(pts: list, W: int, H: int) -> np.ndarray:
    cv2 = _cv2()
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.array([[round(u * W), round(v * H)] for u, v in pts], np.int32)], 1)
    return m.astype(bool)


def color_index(s: O.Store, pid: int, kind: str = "oks", sens: int = 5, propose: bool = False, by: str = "", long_side: int = 1200) -> dict:
    r, f, _sol, mpp = _ctx(s, pid)
    rgb = _rgb(f, long_side)
    H, W = rgb.shape[:2]
    m = index_mask(rgb, kind, sens)
    px_m2 = (mpp * r["w"] / W) ** 2 if mpp else None
    zones = []
    for ft in O.features(s, pid):
        if ft["shape"] != "poly" or O.is_draft(ft):
            continue
        zm = _poly_mask(ft["pts"], W, H)
        n = int(zm.sum())
        if not n:
            continue
        hit = int((m & zm).sum())
        zones.append({"id": ft["id"], "name": ft.get("name") or ft["kind"], "kind": ft["kind"], "pct": round(100 * hit / n, 1),
                      "m2": round(hit * px_m2, 2) if px_m2 else None, "zone_m2": round(n * px_m2, 2) if px_m2 else None})
    col = INDEX[kind][1]
    ov = np.zeros((H, W, 4), np.uint8)
    ov[m] = (*col, 165)
    made = []
    if propose:
        cv2 = _cv2()
        O.clear_drafts(s, pid, "indeks:" + kind)
        mm = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        n, comp, stats, _c = cv2.connectedComponentsWithStats(mm, connectivity=8)
        order = sorted(range(1, n), key=lambda i: -stats[i, cv2.CC_STAT_AREA])
        from . import core_vision
        want = _kind_ok(s, "zona_oks" if kind == "oks" else "zona_vein", "zona_lito")
        for i in order[:15]:
            if stats[i, cv2.CC_STAT_AREA] < 0.003 * m.size:
                break
            poly = core_vision.mask_polygon(comp == i, 50)
            if len(poly) < 3:
                continue
            pct = round(100 * stats[i, cv2.CC_STAT_AREA] / m.size, 1)
            try:
                j = O.save_feature(s, pid, None, {"kind": want, "pts": poly, "name": f"Usulan {INDEX[kind][0].split(' (')[0].lower()} {len(made) + 1}",
                                                  "src": "auto:indeks", "attrs": {O.DRAFT: "indeks:" + kind, "_pct": pct}}, by or "auto")
                made.append(j["id"])
            except ValueError:
                continue
    return {"kind": kind, "label": INDEX[kind][0], "sens": sens, "pct": round(100 * float(m.mean()), 2),
            "m2": round(float(m.sum()) * px_m2, 2) if px_m2 else None, "scaled": bool(px_m2), "zones": zones,
            "png": _b64png(ov), "w": W, "h": H, "made": made, "features": O.features(s, pid) if propose else None}


# ================================================================ 3. struktur & geoteknik
def _axial(a: float) -> float:
    return a % 180.0


def _adiff(a: float, b: float) -> float:
    d = abs(_axial(a) - _axial(b))
    return min(d, 180 - d)


def _line_mask(rgb: np.ndarray, sens: int) -> np.ndarray:
    """Peta jejak: celah / rekahan gelap (kekar, rekahan terisi oksida) lewat black-hat dan urat terang (kuarsa) lewat
    top-hat pada kecerahan. Bintik kecil (tekstur batuan / kerikil) dibuang."""
    cv2 = _cv2()
    H, W = rgb.shape[:2]
    ls = max(H, W)
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    g = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)
    g = cv2.GaussianBlur(g, (5, 5), 1.2)
    r = max(9, int(0.016 * ls) | 1)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r, r))
    pct = 100 - (3.0 + 0.8 * sens)  # porsi piksel terkuat yang dianggap jejak
    m = np.zeros((H, W), bool)
    for op in (cv2.MORPH_BLACKHAT, cv2.MORPH_TOPHAT):
        f = cv2.morphologyEx(g, op, ker)
        m |= f > max(16.0, float(np.percentile(f, pct)))
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, comp, stats, _c = cv2.connectedComponentsWithStats(m, connectivity=8)
    small = stats[:, cv2.CC_STAT_AREA] < 0.0002 * H * W
    small[0] = True
    return ~small[comp]


def _support(mask: np.ndarray, s_: list[float]) -> float:
    """Porsi titik di sepanjang segmen yang jatuh di peta jejak (yang sudah dilebarkan)."""
    H, W = mask.shape
    n = max(2, int(math.hypot(s_[2] - s_[0], s_[3] - s_[1]) / 2))
    xs = np.clip(np.linspace(s_[0], s_[2], n).round().astype(int), 0, W - 1)
    ys = np.clip(np.linspace(s_[1], s_[3], n).round().astype(int), 0, H - 1)
    return float(mask[ys, xs].mean())


def detect_traces(rgb: np.ndarray, sens: int = 5, min_len: float = 0.05) -> list[list[tuple[float, float]]]:
    """Jejak lurus kekar / vein / kontak (polyline 2 titik, piksel peta kerja): peta jejak gelap / terang -> HoughLinesP ->
    segmen segaris yang berdekatan digabung hanya bila hasil gabungan tetap didukung peta jejak di sepanjang panjangnya
    (mencegah garis panjang acak yang menyambung tekstur batuan)."""
    cv2 = _cv2()
    sens = max(1, min(10, int(sens)))
    H, W = rgb.shape[:2]
    ls = max(W, H)
    m = _line_mask(rgb, sens)
    k = max(3, int(0.004 * ls) | 1)
    md = cv2.dilate(m.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)
    seg = cv2.HoughLinesP(m.astype(np.uint8) * 255, 1, np.pi / 180, threshold=max(12, int(0.02 * ls)),
                          minLineLength=max(10, int(0.5 * min_len * ls)), maxLineGap=max(3, int(0.006 * ls)))
    if seg is None:
        return []
    S = [list(map(float, x)) for x in np.asarray(seg).reshape(-1, 4)]
    border = 0.012 * ls

    def ang(s_):
        return math.degrees(math.atan2(-(s_[3] - s_[1]), s_[2] - s_[0])) % 180

    S = [s_ for s_ in S if not ((max(s_[0], s_[2]) < border) or (max(s_[1], s_[3]) < border)
                                or (min(s_[0], s_[2]) > W - border) or (min(s_[1], s_[3]) > H - border))]
    need = 0.6 - 0.02 * sens
    merged = True
    while merged:
        merged = False
        S.sort(key=lambda s_: -math.hypot(s_[2] - s_[0], s_[3] - s_[1]))
        out: list[list[float]] = []
        for s_ in S:
            a = ang(s_)
            done = False
            for o in out:
                if _adiff(a, ang(o)) > 5:
                    continue
                d = np.array([o[2] - o[0], o[3] - o[1]])
                n_ = np.linalg.norm(d)
                if n_ < 1e-6:
                    continue
                d /= n_
                nrm = np.array([-d[1], d[0]])
                p0, p1 = np.array(s_[:2]), np.array(s_[2:])
                q0 = np.array(o[:2])
                if max(abs((p0 - q0) @ nrm), abs((p1 - q0) @ nrm)) > 0.006 * ls:
                    continue
                ts = sorted([float((p0 - q0) @ d), float((p1 - q0) @ d)])
                if ts[0] > n_ + 0.02 * ls or ts[1] < -0.02 * ls:
                    continue
                t = sorted([0.0, n_] + ts)
                a0, a1 = q0 + t[0] * d, q0 + t[-1] * d
                cand = [float(a0[0]), float(a0[1]), float(a1[0]), float(a1[1])]
                if _support(md, cand) < need:
                    continue
                o[:] = cand
                done = merged = True
                break
            if not done:
                out.append(list(s_))
        S = out
    S = [s_ for s_ in S if math.hypot(s_[2] - s_[0], s_[3] - s_[1]) >= min_len * ls and _support(md, s_) >= need]
    S.sort(key=lambda s_: -math.hypot(s_[2] - s_[0], s_[3] - s_[1]))
    return [[(s_[0], s_[1]), (s_[2], s_[3])] for s_ in S[:int(20 + 6 * sens)]]


def propose_traces(s: O.Store, pid: int, sens: int = 5, min_len: float = 0.05, by: str = "", long_side: int = 1400) -> dict:
    r, f, _sol, _mpp = _ctx(s, pid)
    rgb = _rgb(f, long_side)
    H, W = rgb.shape[:2]
    tr = detect_traces(rgb, sens, min_len)
    kind = _kind_ok(s, "kekar", "kontak_lito")
    O.clear_drafts(s, pid, "struktur")
    made = []
    for i, pl in enumerate(tr, 1):
        try:
            j = O.save_feature(s, pid, None, {"kind": kind, "pts": [[x / W, y / H] for x, y in pl], "name": f"Usulan jejak {i}",
                                              "src": "auto:struktur", "attrs": {O.DRAFT: "struktur"}}, by or "auto")
            made.append(j["id"])
        except ValueError:
            continue
    with s.lock, s.conn() as c:
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                  (pid, "usulan jejak struktur", None, f"{len(made)} garis (kepekaan {sens})", "auto:struktur", by or "auto", core_io.now()))
    return {"made": made, "features": O.features(s, pid)}


ISRM = [(0.02, "Sangat rapat sekali (extremely close) < 20 mm"), (0.06, "Sangat rapat (very close) 20–60 mm"),
        (0.2, "Rapat (close) 60–200 mm"), (0.6, "Sedang (moderate) 200–600 mm"), (2.0, "Lebar (wide) 600 mm–2 m"),
        (6.0, "Sangat lebar (very wide) 2–6 m"), (1e9, "Sangat lebar sekali (extremely wide) > 6 m")]
GSI_STRUCT = [(3, "Masif / blok besar (intact / massive)"), (10, "Blocky"), (30, "Very blocky"), (1e9, "Disintegrated")]
GSI_COND = ["Sangat baik", "Baik", "Sedang", "Buruk", "Sangat buruk"]
GSI_TAB = [[90, 80, 65, 50, 35], [80, 70, 55, 40, 25], [70, 60, 45, 30, 20], [55, 45, 30, 20, 10]]  # perkiraan tengah, ±5


def isrm(sp: Optional[float]) -> str:
    if not sp:
        return ""
    return next(t for lim, t in ISRM if sp < lim)


def _weather_cond(desc: dict) -> Optional[int]:
    """Kolom kondisi bidang GSI dari pelapukan di deskripsi (W1..W6)."""
    t = str((desc or {}).get("weathering") or "")
    ws = [int(x) for x in re.findall(r"W\s*([1-6])", t.upper())]
    if not ws:
        return None
    w = round(sum(ws) / len(ws))
    return {1: 0, 2: 1, 3: 2, 4: 3}.get(w, 4)


def _sets(angles: list[float]) -> list[dict]:
    """Set orientasi (sumbu, 0-180°) dari histogram 10° yang dihaluskan; puncak >= 15 % jejak, minimal 2 jejak."""
    if not angles:
        return []
    h = np.zeros(18)
    for a in angles:
        h[int(_axial(a) // 10) % 18] += 1
    hs = (np.roll(h, 1) + 2 * h + np.roll(h, -1)) / 4
    peaks = [i for i in range(18) if hs[i] >= hs[i - 1] and hs[i] > hs[(i + 1) % 18] and h[i] + h[i - 1] + h[(i + 1) % 18] >= max(2, 0.15 * len(angles))]
    peaks = sorted(peaks, key=lambda i: -hs[i])[:3]
    sets = []
    for n, pk in enumerate(sorted(peaks), 1):
        c = pk * 10 + 5
        mem = [a for a in angles if _adiff(a, c) <= 20]
        if len(mem) < 2:
            continue
        # rata-rata sumbu (sudut ganda)
        mx = sum(math.cos(math.radians(2 * a)) for a in mem)
        my = sum(math.sin(math.radians(2 * a)) for a in mem)
        mean = (math.degrees(math.atan2(my, mx)) / 2) % 180
        sets.append({"set": f"S{n}", "mean": round(mean, 1), "n": len(mem)})
    return sets


def _seg_x(p: np.ndarray, q: np.ndarray, a: np.ndarray, b: np.ndarray) -> Optional[tuple[float, np.ndarray]]:
    """Perpotongan segmen p-q dengan a-b: (t sepanjang p-q, titik)."""
    r, s_ = q - p, b - a
    den = r[0] * s_[1] - r[1] * s_[0]
    if abs(den) < 1e-12:
        return None
    t = ((a[0] - p[0]) * s_[1] - (a[1] - p[1]) * s_[0]) / den
    u = ((a[0] - p[0]) * r[1] - (a[1] - p[1]) * r[0]) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return t, p + t * r
    return None


def structure(s: O.Store, pid: int, scan_fid: Optional[int] = None, drafts: bool = True) -> dict:
    """Orientasi jejak, set, rose diagram, scanline (frekuensi, spasi, kelas ISRM), Jv & RQD perkiraan, bantuan GSI."""
    r, _f, sol, mpp = _ctx(s, pid)
    W, H = r["w"], r["h"]
    feats = O.features(s, pid)
    tr = [f for f in feats if f["kind"] in STRUCT_KINDS and f["shape"] == "line" and (drafts or not O.is_draft(f)) and f["id"] != scan_fid]
    lines = []
    for f in tr:
        P = np.array([[u * W, v * H] for u, v in f["pts"]])
        d = P[-1] - P[0]
        a = math.degrees(math.atan2(-d[1], d[0])) % 180  # sudut di bidang foto dari horizontal, berlawanan jarum jam
        m = O.measure(sol, W, H, f) if sol else {}
        lines.append({"id": f["id"], "kind": f["kind"], "draft": O.is_draft(f), "ang": round(a, 1), "len_px": round(float(np.linalg.norm(d)), 1),
                      "len_m": round(m["length_m"], 2) if m.get("length_m") else (round(float(np.linalg.norm(d)) * mpp, 2) if mpp else None),
                      "app_dip": round(m["apparent_dip"], 1) if m.get("apparent_dip") is not None else None,
                      "trend": round(m["trend"], 1) if m.get("trend") is not None else None})
    sets = _sets([x["ang"] for x in lines])
    for x in lines:
        x["set"] = next((st["set"] for st in sets if _adiff(x["ang"], st["mean"]) <= 20), "")
    for st in sets:
        mem = [x for x in lines if x["set"] == st["set"]]
        dips = [x["app_dip"] for x in mem if x["app_dip"] is not None]
        st["app_dip"] = round(sum(dips) / len(dips), 1) if dips else None
    # scanline
    sc_feat = next((f for f in feats if f["id"] == scan_fid and f["shape"] == "line"), None) if scan_fid else None
    sl = sc_feat["pts"] if sc_feat else [[0.02, 0.5], [0.98, 0.5]]
    SL = np.array([[u * W, v * H] for u, v in sl])
    hits = []
    for f in tr:
        x_ = next((x for x in lines if x["id"] == f["id"]), None)
        P = np.array([[u * W, v * H] for u, v in f["pts"]])
        for i in range(len(SL) - 1):
            seg_len0 = sum(float(np.linalg.norm(SL[k + 1] - SL[k])) for k in range(i))
            for j in range(len(P) - 1):
                h = _seg_x(SL[i], SL[i + 1], P[j], P[j + 1])
                if h:
                    hits.append({"s_px": seg_len0 + h[0] * float(np.linalg.norm(SL[i + 1] - SL[i])), "uv": [h[1][0] / W, h[1][1] / H],
                                 "set": x_["set"] if x_ else "", "ang": x_["ang"] if x_ else None, "seg": i})
    hits.sort(key=lambda h: h["s_px"])
    L_px = float(sum(np.linalg.norm(SL[k + 1] - SL[k]) for k in range(len(SL) - 1)))

    def to_m(uvs: list) -> Optional[list[float]]:
        """Jarak kumulatif sepanjang scanline (m) untuk titik-titik uv, lewat georef (3D) atau skala."""
        if sol:
            Pw = np.array(O.to_world(sol, W, H, uvs))
            return [0.0] + list(np.cumsum(np.linalg.norm(np.diff(Pw, axis=0), axis=1)))
        return None
    unit = "m" if (sol or mpp) else "px"
    if sol:
        pts_uv = [list(sl[0])] + [h["uv"] for h in hits] + [list(sl[-1])]
        cum = to_m(pts_uv)
        L_len = float(cum[-1])
        pos = [float(c) for c in cum[1:-1]]
    else:
        k_ = mpp or 1.0
        L_len = L_px * k_
        pos = [h["s_px"] * k_ for h in hits]
    for h, p_ in zip(hits, pos):
        h["s"] = round(p_, 3)
    sp = [b - a for a, b in zip(pos, pos[1:])]
    scan = {"n": len(hits), "length": round(L_len, 2), "unit": unit, "auto": sc_feat is None, "line": sl,
            "hits": [{"uv": h["uv"], "s": h["s"], "set": h["set"]} for h in hits]}
    if hits and L_len > 0:
        scan["freq"] = round(len(hits) / L_len, 2)
        if sp:
            scan["spacing_mean"] = round(float(sum(sp) / len(sp)), 3)
            scan["spacing_median"] = round(float(sorted(sp)[len(sp) // 2]), 3)
            if unit == "m":
                scan["isrm"] = isrm(scan["spacing_mean"])
    # spasi per set (dikoreksi sudut terhadap scanline) & Jv
    d_sc = SL[-1] - SL[0]
    a_sc = math.degrees(math.atan2(-d_sc[1], d_sc[0])) % 180
    jv = 0.0
    for st in sets:
        ps = [p_ for h, p_ in zip(hits, pos) if h["set"] == st["set"]]
        st["hits"] = len(ps)
        if len(ps) >= 2:
            app = (ps[-1] - ps[0]) / (len(ps) - 1)
            ang = math.radians(_adiff(st["mean"], a_sc))
            st["spacing"] = round(float(app * abs(math.sin(ang))), 3) if abs(math.sin(ang)) > 0.17 else None
            if st["spacing"] and unit == "m":
                st["isrm"] = isrm(st["spacing"])
                jv += 1.0 / max(st["spacing"], 1e-3)
    geo: dict[str, Any] = {"unit_ok": unit == "m"}
    if unit == "m" and jv > 0:
        cond = _weather_cond(r.get("desc") or {})
        si = next(i for i, (lim, _t) in enumerate(GSI_STRUCT) if jv < lim)
        geo.update(jv=round(jv, 1), rqd=round(max(0.0, min(100.0, 110 - 2.5 * jv))), structure=GSI_STRUCT[si][1],
                   condition=GSI_COND[cond] if cond is not None else None)
        if cond is not None:
            g = GSI_TAB[si][cond]
            geo["gsi"] = f"{max(5, g - 5)}–{min(100, g + 5)}"
        else:
            geo["gsi"] = f"{GSI_TAB[si][-1]}–{GSI_TAB[si][0]} (kondisi bidang belum diketahui: isi Pelapukan W1–W6 di Deskripsi)"
    return {"lines": lines, "sets": sets, "scan": scan, "geo": geo, "georef": bool(sol), "m_per_px": mpp,
            "rose": rose_png(lines, sets, bool(sol))}


def rose_png(lines: list[dict], sets: list[dict], georef: bool) -> Optional[str]:
    if not lines:
        return None
    try:
        from .core_qaqc import _CHART_LOCK, _plt
    except ImportError:
        return None
    try:
        with _CHART_LOCK:
            plt = _plt()
            fig = plt.figure(figsize=(3.6, 2.4))
            ax = fig.add_subplot(111, projection="polar")
            ax.set_thetamin(0)
            ax.set_thetamax(180)
            bins = np.radians(np.arange(0, 181, 10))
            angs = np.radians([x["ang"] for x in lines])
            wts = [x["len_px"] for x in lines]
            hist, _e = np.histogram(angs, bins=bins, weights=wts)
            ax.bar(bins[:-1] + np.radians(5), hist / max(hist.max(), 1e-9), width=np.radians(10), color="#E8A33D", edgecolor="#5d4a1f", lw=0.6)
            for st in sets:
                t = math.radians(st["mean"])
                ax.plot([t, t], [0, 1.05], color="#C0392B", lw=1.4)
                ax.text(t, 1.18, st["set"], ha="center", va="center", fontsize=7, color="#C0392B", fontweight="bold")
            ax.set_yticklabels([])
            ax.set_xticks(np.radians([0, 30, 60, 90, 120, 150, 180]))
            ax.set_title("Orientasi jejak di bidang foto (0° = mendatar)", fontsize=7.5, pad=2)
            fig.text(0.5, 0.02, f"{len(lines)} jejak, diberi bobot panjang" + (" · apparent dip dari georef di tabel" if georef else ""),
                     ha="center", fontsize=6.5, color="#5d6773")
            b = io.BytesIO()
            fig.savefig(b, format="png", dpi=150, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            return base64.b64encode(b.getvalue()).decode()
    except Exception:  # noqa: BLE001  grafik opsional (matplotlib tidak ada)
        return None


# ================================================================ API
class FBody(BaseModel):
    folder: str
    by: str = ""


class SamBody(FBody):
    id: int
    grid: str = "sedang"
    host: str = ""
    model: str = ""
    extra: str = ""


class IdxBody(FBody):
    id: int
    kind: str = "oks"
    sens: int = 5
    propose: bool = False


class TrBody(FBody):
    id: int
    sens: int = 5
    min_len: float = 0.05


class StBody(FBody):
    id: int
    scan_fid: Optional[int] = None
    drafts: bool = True


@router.post("/sam")
def api_sam(b: SamBody) -> dict:
    ai = {"host": b.host, "model": b.model, "extra": b.extra} if b.model else None
    return {"ok": True, **propose_sam(O.store(b.folder), b.id, b.grid, ai, b.by)}


@router.post("/index")
def api_index(b: IdxBody) -> dict:
    return {"ok": True, **color_index(O.store(b.folder), b.id, b.kind, b.sens, b.propose, b.by)}


@router.post("/traces")
def api_traces(b: TrBody) -> dict:
    return {"ok": True, **propose_traces(O.store(b.folder), b.id, b.sens, b.min_len, b.by)}


@router.post("/struct")
def api_struct(b: StBody) -> dict:
    return {"ok": True, **structure(O.store(b.folder), b.id, b.scan_fid, b.drafts)}
