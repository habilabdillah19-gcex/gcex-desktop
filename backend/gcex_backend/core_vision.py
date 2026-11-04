"""Visi komputer lokal (offline) untuk DB-Ex Singkapan: SAM (Segment Anything) & Depth Anything lewat ONNX Runtime,
OpenCV untuk kontur / penyederhanaan poligon.

- SAM (SlimSAM-77, Apache-2.0): klik titik positif / negatif di foto -> mask -> poligon (cv2.findContours + approxPolyDP).
  Embedding gambar dihitung sekali per foto (1-3 detik di CPU), klik berikutnya hanya decoder (< 0,2 detik).
- Depth Anything V2 Small (Apache-2.0): peta kedalaman RELATIF satu foto (bukan meter). Dipakai core_topo untuk mengisi
  area di luar DTM setelah dikalibrasi ke meter memakai titik yang kena DTM / titik georef.

Model dicari di: env DBEX_MODELS, <aplikasi>/models (installer), <repo>/models (pengembang: tools/ai_models/unduh_model.py).
Pustaka diimpor saat dipakai (importlib) agar backend Electron GC-Ex tidak ikut membundelnya."""
from __future__ import annotations

import importlib
import os
import sys
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

import numpy as np

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
FILES = {"sam_enc": "sam_encoder.onnx", "sam_dec": "sam_decoder.onnx", "depth": "depth_anything_v2_small.onnx"}
_LOCK = threading.RLock()
_SESS: dict[str, Any] = {}
_EMB: "OrderedDict[str, dict]" = OrderedDict()


def _mod(name: str):
    try:
        return importlib.import_module(name)
    except ImportError as e:
        raise RuntimeError(f"Pustaka {name} tidak terpasang di DB-Ex ini ({e}). Pasang ulang DB-Ex versi terbaru.") from None


def model_dir() -> Optional[Path]:
    here = Path(__file__).resolve()
    for c in (os.environ.get("DBEX_MODELS"), Path(getattr(sys, "_MEIPASS", "")) / "models" if getattr(sys, "_MEIPASS", None) else None,
              Path(sys.executable).resolve().parent / "models", here.parents[2] / "models"):
        if c and Path(c).is_dir() and any((Path(c) / f).exists() for f in FILES.values()):
            return Path(c)
    return None


def status() -> dict:
    d = model_dir()
    libs = {}
    for m in ("cv2", "onnxruntime", "shapely"):
        try:
            libs[m] = getattr(importlib.import_module(m), "__version__", "ok")
        except ImportError:
            libs[m] = None
    have = {k: bool(d and (d / f).exists()) for k, f in FILES.items()}
    return {"dir": str(d) if d else None, "models": have, "libs": libs,
            "sam": have["sam_enc"] and have["sam_dec"] and bool(libs["onnxruntime"]) and bool(libs["cv2"]),
            "depth": have["depth"] and bool(libs["onnxruntime"])}


def _session(key: str):
    with _LOCK:
        if key not in _SESS:
            d = model_dir()
            if not d or not (d / FILES[key]).exists():
                raise RuntimeError(f"Model {FILES[key]} tidak ditemukan. Pasang ulang DB-Ex (model AI ikut di installer).")
            ort = _mod("onnxruntime")
            so = ort.SessionOptions()
            so.log_severity_level = 3
            so.enable_cpu_mem_arena = False  # memori dikembalikan sesudah tiap run (PC lapangan 8 GB RAM)
            _SESS[key] = ort.InferenceSession(str(d / FILES[key]), sess_options=so, providers=["CPUExecutionProvider"])
        return _SESS[key]


def _load_rgb(path: Path, max_side: int = 0) -> np.ndarray:
    from PIL import Image, ImageOps
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if max_side and max(im.size) > max_side:
            k = max_side / max(im.size)
            im = im.resize((round(im.width * k), round(im.height * k)), Image.BILINEAR)
        return np.asarray(im)


# ================================================================ SAM
def sam_embed(path: Path, key: str) -> dict:
    """Embedding foto (cache 4 foto terakhir di memori)."""
    with _LOCK:
        if key in _EMB:
            _EMB.move_to_end(key)
            return _EMB[key]
    from PIL import Image
    rgb = _load_rgb(path)
    H, W = rgb.shape[:2]
    k = 1024 / max(H, W)
    nw, nh = int(W * k + 0.5), int(H * k + 0.5)
    im = np.asarray(Image.fromarray(rgb).resize((nw, nh), Image.BILINEAR), dtype=np.float32) / 255.0
    im = (im - MEAN) / STD
    pad = np.zeros((1024, 1024, 3), np.float32)
    pad[:nh, :nw] = im
    x = pad.transpose(2, 0, 1)[None]
    emb, pos = _session("sam_enc").run(None, {"pixel_values": x})
    e = {"emb": emb, "pos": pos, "W": W, "H": H, "k": k, "nw": nw, "nh": nh}
    with _LOCK:
        _EMB[key] = e
        while len(_EMB) > 4:
            _EMB.popitem(last=False)
    return e


def sam_mask(e: dict, points: list, level: int = 1) -> tuple[np.ndarray, float, list[float]]:
    """points: [[u, v, label], ...] (u, v 0..1; label 1 = bagian zona, 0 = bukan). level: 0 kecil, 1 sedang, 2 besar
    (SAM memberi 3 tingkat mask untuk satu klik: mis. pita gossan / zona alterasi di sekitarnya / seluruh dinding).
    Kembalikan mask bool ukuran foto asli, skor IoU tingkat itu, dan luas relatif ketiga tingkat (kecil, sedang, besar)."""
    cv2 = _mod("cv2")
    P = np.array([[[[u * e["W"] * e["k"], v * e["H"] * e["k"]] for u, v, _l in points]]], np.float32)
    L = np.array([[[1 if int(lab) else 0 for _u, _v, lab in points]]], np.int64)
    iou, masks = _session("sam_dec").run(None, {"input_points": P, "input_labels": L, "image_embeddings": e["emb"],
                                                 "image_positional_embeddings": e["pos"]})
    sc = iou[0, 0]
    area = [float((masks[0, 0, i] > 0).mean()) for i in range(3)]
    order = sorted(range(3), key=lambda i: area[i])  # kecil -> besar
    i = order[max(0, min(2, int(level)))]
    lo = masks[0, 0, i].astype(np.float32)
    up = cv2.resize(lo, (1024, 1024), interpolation=cv2.INTER_LINEAR)[:e["nh"], :e["nw"]]
    full = cv2.resize(up, (e["W"], e["H"]), interpolation=cv2.INTER_LINEAR)
    return full > 0.0, float(sc[i]), [area[j] for j in order]


def mask_polygon(mask: np.ndarray, max_pts: int = 80) -> list[list[float]]:
    """Kontur luar terbesar -> poligon ternormalisasi, disederhanakan (approxPolyDP) sampai <= max_pts titik."""
    cv2 = _mod("cv2")
    H, W = mask.shape
    m = mask.astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cs, _h = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    c = max(cs, key=cv2.contourArea)
    if cv2.contourArea(c) < 0.0005 * W * H:
        return []
    per = cv2.arcLength(c, True)
    eps = max(1.0, 0.002 * per)
    ap = cv2.approxPolyDP(c, eps, True)
    while len(ap) > max_pts:
        eps *= 1.4
        ap = cv2.approxPolyDP(c, eps, True)
    pts = [(float(x), float(y)) for x, y in ap[:, 0, :]]
    try:  # Shapely: perbaiki poligon yang memotong dirinya sendiri, ambil bagian terbesar
        geom = importlib.import_module("shapely.geometry")
        pg = geom.Polygon(pts).buffer(0)
        if pg.geom_type == "MultiPolygon":
            pg = max(pg.geoms, key=lambda g: g.area)
        if not pg.is_empty and pg.geom_type == "Polygon":
            pts = list(pg.exterior.coords)[:-1]
    except (ImportError, ValueError):
        pass
    return [[round(min(1.0, max(0.0, x / W)), 6), round(min(1.0, max(0.0, y / H)), 6)] for x, y in pts]


# ================================================================ Depth Anything
def depth_map(path: Path, cache: Optional[Path] = None, side: int = 518) -> np.ndarray:
    """Kedalaman relatif (disparitas: besar = dekat kamera), ukuran ~518 px sisi pendek, dinormalisasi 0..1. Cache .npy."""
    if cache and cache.exists():
        try:
            return np.load(cache).astype(np.float32)
        except (OSError, ValueError):
            pass
    from PIL import Image
    rgb = _load_rgb(path)
    H, W = rgb.shape[:2]
    k = side / min(H, W)
    nw, nh = max(14, int(round(W * k / 14)) * 14), max(14, int(round(H * k / 14)) * 14)
    im = np.asarray(Image.fromarray(rgb).resize((nw, nh), Image.BICUBIC), dtype=np.float32) / 255.0
    x = ((im - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    d = _session("depth").run(None, {"pixel_values": x})[0][0]
    lo, hi = np.percentile(d, 1), np.percentile(d, 99)
    d = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1).astype(np.float32)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache, d.astype(np.float16))
    return d


def sample(d: np.ndarray, uv: np.ndarray) -> np.ndarray:
    """Nilai peta (bilinear) di koordinat ternormalisasi uv [n,2]."""
    h, w = d.shape
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001)
    y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    a, b = d[y0, x0], d[y0, x0 + 1]
    c, e = d[y0 + 1, x0], d[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + e * fx) * fy
