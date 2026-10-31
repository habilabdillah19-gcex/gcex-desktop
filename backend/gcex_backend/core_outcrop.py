"""Core-Ex: ruang kerja Singkapan (foto singkapan / trenching hasil mapping lapangan).

- Foto dimasukkan satu per satu dan DISALIN ke <folder proyek>/_GCEx_Core/singkapan/foto, jadi rekan yang membuka
  folder yang sama melihat hasil yang sama (folder hanya-baca -> penyimpanan lokal, sama dengan Core box).
- Deskripsi singkapan dari AI lokal (Ollama, keluaran dikunci skema JSON, istilah ISRM). Isian yang diedit geologist
  tidak ditimpa AI.
- Fitur hasil digitasi (garis / poligon / titik) disimpan dalam koordinat gambar ternormalisasi 0..1
  (u = kiri->kanan, v = atas->bawah), tidak bergantung resolusi pratinjau.
- Jenis fitur (pustaka) per proyek: nama, bentuk, warna, nomor string Surpac (bisa diubah).
- Setiap perubahan tercatat di tabel history.
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from . import core_io

router = APIRouter(prefix="/core/outcrop", tags=["core-outcrop"])

SUB = "singkapan"
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".heic"}

# pustaka bawaan: key, nama, bentuk (line / poly / point), warna, nomor string Surpac (bawaan, bisa diubah per proyek)
DEFAULT_KINDS = [
    ("kontak_lito", "Kontak litologi", "line", "#1f4e8c", 1),
    ("kontak_alt", "Kontak alterasi", "line", "#7048e8", 2),
    ("zona_lito", "Zona litologi", "poly", "#4a7499", 3),
    ("zona_alt", "Zona alterasi", "poly", "#2f9e44", 4),
    ("zona_oks", "Zona oksida / gossan", "poly", "#c2551f", 5),
    ("sesar", "Sesar", "line", "#d6336c", 6),
    ("kekar", "Kekar", "line", "#f08c00", 7),
    ("vein", "Vein", "line", "#e8c547", 8),
    ("zona_vein", "Zona vein", "poly", "#e8c547", 9),
    ("breksi", "Breksi / diatrema", "poly", "#a61e4d", 10),
    ("channel", "Channel sampel", "line", "#ffd43b", 11),
    ("skala", "Garis skala", "line", "#ffffff", 90),
    ("label", "Label", "point", "#ffffff", 91),
]
SHAPES = {"line", "poly", "point"}

# isian deskripsi (key, label). Diisi AI, bisa diedit geologist.
DESC = [
    ("photo_type", "Jenis foto"), ("lithology", "Litologi"), ("alteration", "Alterasi"), ("weathering", "Pelapukan"),
    ("oxidation", "Oksidasi / gossan"), ("veins", "Vein"), ("structures", "Struktur"), ("gsi", "GSI"),
    ("joint_spacing", "Spasi kekar"), ("zones", "Pembagian zona"), ("notes", "Catatan"),
]
DESC_KEYS = [k for k, _ in DESC]
PHOTO_TYPES = ["wall", "floor"]

_DDL = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT, file TEXT UNIQUE NOT NULL, name TEXT, src TEXT, w INTEGER, h INTEGER,
  title TEXT, location TEXT, taken TEXT, desc_json TEXT DEFAULT '{}', edited TEXT DEFAULT '[]',
  ai_json TEXT, ai_model TEXT, ai_at TEXT, ai_secs REAL, ai_conf TEXT, status TEXT DEFAULT 'pending', error TEXT,
  info_json TEXT DEFAULT '{}', georef_json TEXT,
  by TEXT, at TEXT, edited_by TEXT, edited_at TEXT
);
CREATE TABLE IF NOT EXISTS features (
  id INTEGER PRIMARY KEY AUTOINCREMENT, photo_id INTEGER NOT NULL, kind TEXT NOT NULL, shape TEXT NOT NULL,
  pts TEXT NOT NULL, name TEXT, attrs TEXT DEFAULT '{}', src TEXT DEFAULT 'manual',
  by TEXT, at TEXT, edited_by TEXT, edited_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_feat_photo ON features(photo_id);
CREATE TABLE IF NOT EXISTS history (
  id INTEGER PRIMARY KEY AUTOINCREMENT, photo_id INTEGER, what TEXT, old TEXT, new TEXT, src TEXT, by TEXT, at TEXT
);
"""


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.db = root / "singkapan.db"
        self.photos = root / "foto"
        self.lock = threading.RLock()

    @contextmanager
    def conn(self):
        c = sqlite3.connect(str(self.db), timeout=30)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()


_STORES: dict[str, Store] = {}
_SLOCK = threading.Lock()


def store(folder: str) -> Store:
    p = core_io.get_project(folder)  # folder hanya-baca -> lokasi lokal, sama dengan Core box
    root = p.db.parent / SUB
    key = str(root).lower()
    with _SLOCK:
        s = _STORES.get(key)
        if s and s.db.exists():
            return s
        root.mkdir(parents=True, exist_ok=True)
        s = Store(root)
        s.photos.mkdir(exist_ok=True)
        with s.conn() as c:
            c.executescript(_DDL)
        _STORES[key] = s
        return s


# ---------------------------------------------------------------- pustaka jenis fitur
def kinds(s: Store) -> list[dict]:
    with s.conn() as c:
        r = c.execute("SELECT value FROM meta WHERE key='kinds'").fetchone()
    saved = {}
    if r:
        try:
            saved = {k["key"]: k for k in json.loads(r["value"])}
        except (ValueError, TypeError, KeyError):
            saved = {}
    out = []
    for key, name, shape, color, sn in DEFAULT_KINDS:
        k = {"key": key, "name": name, "shape": shape, "color": color, "string": sn, "builtin": True}
        if key in saved:
            k.update({x: saved[key][x] for x in ("name", "color", "string") if x in saved[key]})
        out.append(k)
    for key, k in saved.items():
        if key not in {x["key"] for x in out}:
            out.append({"key": key, "name": k.get("name") or key, "shape": k.get("shape") if k.get("shape") in SHAPES else "line",
                        "color": k.get("color") or "#7a5aa6", "string": int(k.get("string") or 50), "builtin": False})
    return out


def save_kinds(s: Store, lst: list[dict], by: str) -> list[dict]:
    clean, seen_sn = [], {}
    for k in lst:
        key = str(k.get("key") or "").strip().lower().replace(" ", "_")
        if not key:
            continue
        try:
            sn = int(k.get("string"))
        except (TypeError, ValueError):
            raise ValueError(f"Nomor string untuk '{k.get('name') or key}' harus angka.") from None
        if not 1 <= sn <= 32000:
            raise ValueError(f"Nomor string '{k.get('name') or key}' harus 1-32000.")
        if sn in seen_sn:
            raise ValueError(f"Nomor string {sn} dipakai dua jenis fitur: {seen_sn[sn]} dan {k.get('name') or key}.")
        seen_sn[sn] = k.get("name") or key
        shape = k.get("shape") if k.get("shape") in SHAPES else "line"
        clean.append({"key": key, "name": str(k.get("name") or key)[:60], "shape": shape, "color": str(k.get("color") or "#7a5aa6")[:9], "string": sn})
    with s.lock, s.conn() as c:
        old = c.execute("SELECT value FROM meta WHERE key='kinds'").fetchone()
        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('kinds', ?)", (json.dumps(clean, ensure_ascii=False),))
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (NULL,'pustaka fitur',?,?, 'edit', ?, ?)",
                  (old["value"] if old else None, json.dumps(clean, ensure_ascii=False), by, core_io.now()))
    return kinds(s)


# ---------------------------------------------------------------- foto
def _row(r: sqlite3.Row, nfeat: int = 0) -> dict:
    d = dict(r)
    for k, dv in (("desc_json", {}), ("edited", []), ("info_json", {}), ("georef_json", None), ("ai_json", None)):
        try:
            d[k] = json.loads(d[k]) if d.get(k) else dv
        except (TypeError, ValueError):
            d[k] = dv
    d["desc"] = d.pop("desc_json")
    d["info"] = d.pop("info_json")
    d["georef"] = d.pop("georef_json")
    d["n_feat"] = nfeat
    return d


def photos(s: Store) -> list[dict]:
    with s.conn() as c:
        cnt = {r[0]: r[1] for r in c.execute("SELECT photo_id, COUNT(*) FROM features GROUP BY photo_id")}
        rows = [_row(r, cnt.get(r["id"], 0)) for r in c.execute("SELECT * FROM photos ORDER BY id")]
    for r in rows:
        r["missing"] = not (s.photos / r["file"]).exists()
    return rows


def photo(s: Store, pid: int) -> dict:
    with s.conn() as c:
        r = c.execute("SELECT * FROM photos WHERE id=?", (pid,)).fetchone()
        if not r:
            raise ValueError(f"Foto singkapan #{pid} tidak ada.")
        n = c.execute("SELECT COUNT(*) FROM features WHERE photo_id=?", (pid,)).fetchone()[0]
    d = _row(r, n)
    d["missing"] = not (s.photos / d["file"]).exists()
    return d


def photo_path(s: Store, pid: int) -> Path:
    return s.photos / photo(s, pid)["file"]


def add_photo(s: Store, src: str, by: str) -> dict:
    sp = Path(src)
    if not sp.is_file():
        raise ValueError(f"File foto tidak ditemukan: {src}")
    if sp.suffix.lower() not in IMG_EXT:
        raise ValueError(f"{sp.name}: format foto tidak dikenali (JPG, PNG, TIFF, BMP, WEBP).")
    try:
        im = core_io._open_img(sp, 0)
        w, h = im.size
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"{sp.name} tidak bisa dibuka sebagai foto: {e}") from e
    taken = None
    try:
        from PIL import Image
        with Image.open(sp) as raw:
            ex = raw.getexif()
            taken = (ex.get_ifd(0x8769).get(36867) or ex.get(306) or None)
    except Exception:  # noqa: BLE001
        pass
    with s.lock:
        name = sp.name
        dst = s.photos / name
        k = 2
        while dst.exists():
            dst = s.photos / f"{sp.stem}_{k}{sp.suffix}"
            k += 1
        shutil.copy2(sp, dst)
        with s.conn() as c:
            cur = c.execute("INSERT INTO photos (file, name, src, w, h, title, taken, by, at) VALUES (?,?,?,?,?,?,?,?,?)",
                            (dst.name, sp.name, str(sp), w, h, sp.stem, str(taken) if taken else None, by, core_io.now()))
            pid = cur.lastrowid
            c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, "foto", None, sp.name, "tambah", by, core_io.now()))
    return photo(s, pid)


def delete_photo(s: Store, pid: int, by: str) -> None:
    f = photo_path(s, pid)
    with s.lock, s.conn() as c:
        c.execute("DELETE FROM features WHERE photo_id=?", (pid,))
        c.execute("DELETE FROM photos WHERE id=?", (pid,))
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                  (pid, "foto", f.name, None, "hapus", by, core_io.now()))
    try:
        f.unlink()
    except OSError:
        pass


def update_photo(s: Store, pid: int, values: dict, by: str) -> dict:
    """values: title / location / taken (kolom), desc:<key> (deskripsi, ditandai diedit), info (dict infografis)."""
    r = photo(s, pid)
    desc, edited, info = dict(r["desc"]), set(r["edited"]), dict(r["info"])
    sets, vals, hist = [], [], []
    for k, v in values.items():
        if k in ("title", "location", "taken"):
            nv = (str(v).strip() or None) if v is not None else None
            if nv != r.get(k):
                sets.append(f"{k}=?")
                vals.append(nv)
                hist.append((k, r.get(k), nv))
        elif k.startswith("desc:"):
            key = k[5:]
            if key not in DESC_KEYS:
                raise ValueError(f"Isian deskripsi tidak dikenal: {key}")
            nv = (str(v).strip() or None) if v is not None else None
            if key == "photo_type" and nv is not None:
                nv = nv.lower()
                if nv not in PHOTO_TYPES:
                    raise ValueError("Jenis foto harus 'wall' (dinding) atau 'floor' (lantai).")
            if nv != desc.get(key):
                hist.append((key, desc.get(key), nv))
                desc[key] = nv
                edited.add(key)
        elif k == "info":
            if not isinstance(v, dict):
                raise ValueError("info harus objek.")
            info.update(v)
        else:
            raise ValueError(f"Isian tidak dikenal: {k}")
    sets += ["desc_json=?", "edited=?", "info_json=?", "edited_by=?", "edited_at=?"]
    vals += [json.dumps(desc, ensure_ascii=False), json.dumps(sorted(edited)), json.dumps(info, ensure_ascii=False), by, core_io.now()]
    with s.lock, s.conn() as c:
        c.execute(f"UPDATE photos SET {', '.join(sets)} WHERE id=?", vals + [pid])
        for what, o, n in hist:
            c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, what, None if o is None else str(o), None if n is None else str(n), "edit", by, core_io.now()))
    return photo(s, pid)


# ---------------------------------------------------------------- fitur (garis / poligon / titik)
def _feat(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["pts"] = json.loads(d["pts"])
    try:
        d["attrs"] = json.loads(d["attrs"] or "{}")
    except ValueError:
        d["attrs"] = {}
    return d


def features(s: Store, pid: int) -> list[dict]:
    with s.conn() as c:
        return [_feat(r) for r in c.execute("SELECT * FROM features WHERE photo_id=? ORDER BY id", (pid,))]


def _clean_pts(shape: str, pts: Any) -> list[list[float]]:
    try:
        P = [[max(0.0, min(1.0, round(float(p[0]), 6))), max(0.0, min(1.0, round(float(p[1]), 6)))] for p in pts]
    except (TypeError, ValueError, IndexError):
        raise ValueError("Titik fitur harus pasangan angka [u, v].") from None
    # titik kembar berurutan dibuang
    out = [p for i, p in enumerate(P) if i == 0 or abs(p[0] - P[i - 1][0]) + abs(p[1] - P[i - 1][1]) > 1e-6]
    if shape == "poly" and len(out) > 2 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    need = {"point": 1, "line": 2, "poly": 3}[shape]
    if len(out) < need:
        raise ValueError({"point": "Label perlu 1 titik.", "line": "Garis perlu minimal 2 titik.", "poly": "Poligon perlu minimal 3 titik."}[shape])
    return out[:1] if shape == "point" else out


ATTR_NUM = ("au_ppm", "ag_ppm", "sxs_pct", "length_m")


def _clean_attrs(a: Any) -> dict:
    if not isinstance(a, dict):
        return {}
    out: dict[str, Any] = {}
    for k, v in a.items():
        k = str(k)[:40]
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        if k in ATTR_NUM:
            try:
                v = float(str(v).replace(",", "."))
            except ValueError:
                raise ValueError(f"Nilai {k} harus angka.") from None
            if v < 0:
                raise ValueError(f"Nilai {k} tidak boleh negatif.")
        elif isinstance(v, (int, float)):
            pass
        else:
            v = str(v)[:400]
        out[k] = v
    if "length_m" in out and out["length_m"] <= 0:
        raise ValueError("Panjang garis skala harus lebih dari 0 m.")
    return out


def save_feature(s: Store, pid: int, fid: Optional[int], f: dict, by: str) -> dict:
    photo(s, pid)
    ks = {k["key"]: k for k in kinds(s)}
    kind = f.get("kind")
    if kind not in ks:
        raise ValueError(f"Jenis fitur tidak dikenal: {kind}")
    shape = ks[kind]["shape"]
    pts = _clean_pts(shape, f.get("pts") or [])
    attrs = _clean_attrs(f.get("attrs"))
    name = (str(f.get("name") or "").strip() or None)
    with s.lock, s.conn() as c:
        if fid:
            old = c.execute("SELECT * FROM features WHERE id=? AND photo_id=?", (fid, pid)).fetchone()
            if not old:
                raise ValueError(f"Fitur #{fid} tidak ada.")
            c.execute("UPDATE features SET kind=?, shape=?, pts=?, name=?, attrs=?, edited_by=?, edited_at=? WHERE id=?",
                      (kind, shape, json.dumps(pts), name, json.dumps(attrs, ensure_ascii=False), by, core_io.now(), fid))
            c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, f"fitur #{fid}", json.dumps(_feat(old), ensure_ascii=False)[:2000], f"{kind} {len(pts)} titik", "edit", by, core_io.now()))
        else:
            fid = c.execute("INSERT INTO features (photo_id, kind, shape, pts, name, attrs, src, by, at) VALUES (?,?,?,?,?,?,?,?,?)",
                            (pid, kind, shape, json.dumps(pts), name, json.dumps(attrs, ensure_ascii=False), f.get("src") or "manual", by, core_io.now())).lastrowid
            c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, f"fitur #{fid}", None, f"{kind} {len(pts)} titik", "tambah", by, core_io.now()))
    return {"id": fid, "features": features(s, pid)}


def delete_feature(s: Store, fid: int, by: str) -> list[dict]:
    with s.lock, s.conn() as c:
        r = c.execute("SELECT * FROM features WHERE id=?", (fid,)).fetchone()
        if not r:
            raise ValueError(f"Fitur #{fid} tidak ada.")
        c.execute("DELETE FROM features WHERE id=?", (fid,))
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                  (r["photo_id"], f"fitur #{fid}", json.dumps(_feat(r), ensure_ascii=False)[:2000], None, "hapus", by, core_io.now()))
    return features(s, r["photo_id"])


def split_line(s: Store, fid: int, at: int, by: str) -> dict:
    """Belah garis di titik ke-`at` (titik itu menjadi ujung kedua garis)."""
    with s.conn() as c:
        r = c.execute("SELECT * FROM features WHERE id=?", (fid,)).fetchone()
    if not r:
        raise ValueError(f"Fitur #{fid} tidak ada.")
    f = _feat(r)
    if f["shape"] != "line":
        raise ValueError("Hanya garis yang bisa dibelah.")
    if not 0 < at < len(f["pts"]) - 1:
        raise ValueError("Pilih titik di tengah garis (bukan ujung) untuk membelah.")
    a, b = f["pts"][:at + 1], f["pts"][at:]
    save_feature(s, f["photo_id"], fid, {"kind": f["kind"], "pts": a, "name": f["name"], "attrs": f["attrs"]}, by)
    j = save_feature(s, f["photo_id"], None, {"kind": f["kind"], "pts": b, "name": f["name"], "attrs": f["attrs"]}, by)
    return j


def join_lines(s: Store, a: int, b: int, by: str) -> dict:
    """Gabung dua garis yang ujungnya bersinggungan (toleransi 0,5% lebar foto)."""
    with s.conn() as c:
        ra = c.execute("SELECT * FROM features WHERE id=?", (a,)).fetchone()
        rb = c.execute("SELECT * FROM features WHERE id=?", (b,)).fetchone()
    if not ra or not rb or a == b:
        raise ValueError("Pilih dua garis yang berbeda.")
    fa, fb = _feat(ra), _feat(rb)
    if fa["shape"] != "line" or fb["shape"] != "line" or fa["photo_id"] != fb["photo_id"]:
        raise ValueError("Hanya dua garis di foto yang sama yang bisa digabung.")
    pa, pb = fa["pts"], fb["pts"]
    d = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1])  # noqa: E731
    tol = 0.005
    if d(pa[-1], pb[0]) < tol:
        pts = pa + pb[1:]
    elif d(pa[-1], pb[-1]) < tol:
        pts = pa + pb[::-1][1:]
    elif d(pa[0], pb[-1]) < tol:
        pts = pb + pa[1:]
    elif d(pa[0], pb[0]) < tol:
        pts = pb[::-1] + pa[1:]
    else:
        raise ValueError("Ujung kedua garis tidak bersinggungan. Seret ujung salah satu garis ke ujung garis lain (snap) dulu.")
    j = save_feature(s, fa["photo_id"], a, {"kind": fa["kind"], "pts": pts, "name": fa["name"] or fb["name"], "attrs": {**fb["attrs"], **fa["attrs"]}}, by)
    return {"id": a, "features": delete_feature(s, b, by), "joined": j["id"]}


def history(s: Store, pid: int) -> list[dict]:
    with s.conn() as c:
        return [dict(r) for r in c.execute("SELECT what, old, new, src, by, at FROM history WHERE photo_id=? ORDER BY id DESC LIMIT 200", (pid,))]


# ---------------------------------------------------------------- AI deskripsi singkapan
def ai_schema() -> dict:
    txt = {"type": ["string", "null"]}
    return {
        "type": "object",
        "properties": {
            "photo_type": {"type": ["string", "null"], "enum": PHOTO_TYPES + [None]},
            "lithology": txt, "alteration": txt,
            "weathering": txt, "oxidation": txt, "veins": txt, "structures": txt,
            "gsi": txt, "joint_spacing": txt, "zones": txt, "notes": txt,
            "confidence": {"type": "string", "enum": ["rendah", "sedang", "tinggi"]},
        },
        "required": DESC_KEYS + ["confidence"],
    }


def ai_prompt(extra: str = "", scale_m_per_px: Optional[float] = None, context: str = "") -> str:
    p = (
        "Anda geologist senior yang mendeskripsikan FOTO SINGKAPAN hasil mapping lapangan (dinding / lantai pit, "
        "trenching, tebing jalan) di tambang emas epitermal. Deskripsikan HANYA yang benar-benar terlihat di foto, "
        "dalam bahasa Indonesia dengan istilah teknis Inggris di dalam kurung bila lazim.\n\n"
        "ISIAN:\n"
        "- photo_type: 'wall' bila foto dinding / tebing (bidang tegak), 'floor' bila lantai / permukaan mendatar dilihat dari atas.\n"
        "- lithology: batuan dominan dan teksturnya (mis. 'Tuf lapili (lapilli tuff), fragmen andesit').\n"
        "- alteration: alterasi kasat mata dan petunjuknya (mis. 'propilitik klorit-epidot, hijau keabuan; argilik di sekitar vein').\n"
        "- weathering: tingkat pelapukan skala ISRM W1 (Fresh) sampai W6 (Residual Soil), per zona bila berbeda, "
        "mis. 'W4-W5 di bagian atas (saprolit), W2 di bagian bawah'.\n"
        "- oxidation: oksida besi (coklat / merah / kuning / jarosit / hematit / limonit), gossan, dan batas zona oksida bila terlihat.\n"
        "- veins: vein / urat (kuarsa, kalsit, oksida), kesan lebar, pola (tunggal, sheeted, stockwork, breksi hidrotermal), arah kemiringan relatif di foto.\n"
        "- structures: sesar, kekar, zona hancur, perlapisan, kontak; arah kemiringan relatif di foto (mis. 'kekar curam ke kanan'). "
        "Jangan memberi strike / dip derajat: foto tidak cukup untuk itu.\n"
        "- gsi: rentang perkiraan Geological Strength Index (mis. '35-45') dari blokiness dan kondisi bidang diskontinuitas.\n"
        + ("- joint_spacing: spasi kekar mayor menurut kelas ISRM (mis. 'Moderate 200-600 mm'). "
           f"Skala foto kira-kira {scale_m_per_px * 1000:.1f} mm per piksel gambar yang dikirim.\n" if scale_m_per_px else
           "- joint_spacing: foto belum berskala; isi kesan relatif saja (rapat / sedang / jarang) atau null.\n")
        + "- zones: pembagian zona dari atas ke bawah / kiri ke kanan beserta ciri tiap zona (mis. 'Atas: soil & saprolit oksida; Tengah: ...').\n"
        "- notes: ringkas (maks 3 kalimat): hal penting untuk grade control (vein termineralisasi, sulfida, zona oksida, potensi dilusi).\n"
        "- confidence: keyakinan Anda (rendah / sedang / tinggi).\n"
        "Bila tidak bisa dinilai dari foto, isi null. Jangan mengarang nilai kadar atau nama lokasi.\n"
        "Jawab HANYA dengan JSON sesuai skema."
    )
    if context:
        p += "\n\nKeterangan dari geologist (konteks, bukan untuk disalin mentah): " + context.strip()
    if extra and extra.strip():
        p += "\n\nInstruksi tambahan dari geologist proyek:\n" + extra.strip()
    return p


def ai_describe(s: Store, pid: int, host: str, model: str, extra: str = "", max_px: int = 1600, timeout: float = 900) -> dict:
    r = photo(s, pid)
    f = s.photos / r["file"]
    if not f.exists():
        raise ValueError("File foto singkapan hilang dari folder proyek.")
    img = core_io.resized_jpeg(f, max_px)
    scale = None
    sc = scale_info(s, pid, r)
    if sc:
        scale = sc["m_per_px"] * max(r["w"], r["h"]) / min(max_px, max(r["w"], r["h"]))
    ctx = "; ".join(x for x in (r.get("title") and f"judul: {r['title']}", r.get("location") and f"lokasi: {r['location']}") if x)
    body = {"model": model, "messages": [{"role": "user", "content": ai_prompt(extra, scale, ctx), "images": [base64.b64encode(img).decode()]}],
            "stream": False, "format": ai_schema(), "options": {"temperature": 0, "num_ctx": 16384}, "keep_alive": "15m"}
    t0 = time.time()
    try:
        j = core_io._http((host or core_io.DEFAULT_HOST).rstrip("/") + "/api/chat", body, timeout=timeout)
        if j.get("error"):
            raise RuntimeError("Ollama: " + str(j["error"]))
        res = core_io._parse_json((j.get("message") or {}).get("content", ""))
    except Exception as e:  # noqa: BLE001
        with s.lock, s.conn() as c:
            c.execute("UPDATE photos SET status='error', error=? WHERE id=?", (str(e)[:500], pid))
        raise
    return apply_ai(s, pid, res, model, time.time() - t0)


def apply_ai(s: Store, pid: int, res: dict, model: str, secs: float) -> dict:
    r = photo(s, pid)
    desc, edited = dict(r["desc"]), set(r["edited"])
    with s.lock, s.conn() as c:
        for k in DESC_KEYS:
            if k in edited or k not in res:
                continue
            v = res.get(k)
            if isinstance(v, (list, dict)):
                v = json.dumps(v, ensure_ascii=False)
            v = (str(v).strip() or None) if v is not None else None
            if k == "photo_type" and v not in PHOTO_TYPES:
                v = None
            if v is None and desc.get(k) is not None:
                continue
            if v != desc.get(k):
                c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                          (pid, k, desc.get(k), v, "ai:" + model, "AI", core_io.now()))
            desc[k] = v
        c.execute("UPDATE photos SET desc_json=?, status='done', error=NULL, ai_json=?, ai_model=?, ai_at=?, ai_secs=?, ai_conf=? WHERE id=?",
                  (json.dumps(desc, ensure_ascii=False), json.dumps(res, ensure_ascii=False), model, core_io.now(), round(secs, 1), res.get("confidence"), pid))
    return photo(s, pid)


# ---------------------------------------------------------------- skala (garis skala) -> meter per piksel
def scale_info(s: Store, pid: int, r: Optional[dict] = None) -> Optional[dict]:
    """Skala foto dari garis skala terakhir yang punya panjang (m). Dipakai bar skala infografis & spasi kekar AI."""
    r = r or photo(s, pid)
    best = None
    for f in features(s, pid):
        if f["kind"] != "skala" or not f["attrs"].get("length_m"):
            continue
        px = 0.0
        for a, b in zip(f["pts"], f["pts"][1:]):
            px += (((b[0] - a[0]) * r["w"]) ** 2 + ((b[1] - a[1]) * r["h"]) ** 2) ** 0.5
        if px > 1:
            best = {"feature": f["id"], "m_per_px": f["attrs"]["length_m"] / px, "length_m": f["attrs"]["length_m"], "px": px}
    return best


# ---------------------------------------------------------------- API
class FBody(BaseModel):
    folder: str
    by: str = ""


class AddBody(FBody):
    path: str


class PidBody(FBody):
    id: int


class UpdBody(FBody):
    id: int
    values: dict[str, Any]


class FeatBody(FBody):
    photo_id: int
    feat_id: Optional[int] = None
    feat: dict[str, Any]


class FidBody(FBody):
    feat_id: int


class SplitBody(FBody):
    feat_id: int
    at: int


class JoinBody(FBody):
    a: int
    b: int


class KindsBody(FBody):
    kinds: list[dict[str, Any]]


class AiOBody(FBody):
    id: int
    host: str = core_io.DEFAULT_HOST
    model: str
    extra: str = ""
    max_px: int = 1600


def _summary(s: Store) -> dict:
    ps = photos(s)
    return {"total": len(ps), "described": sum(1 for p in ps if p["status"] == "done"), "features": sum(p["n_feat"] for p in ps)}


@router.post("/open")
def api_open(b: FBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "photos": photos(s), "kinds": kinds(s), "desc_fields": [{"key": k, "label": l} for k, l in DESC],
            "summary": _summary(s), "root": str(s.root)}


@router.post("/add")
def api_add(b: AddBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "photo": add_photo(s, b.path, b.by), "summary": _summary(s)}


@router.post("/photo")
def api_photo(b: PidBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "photo": photo(s, b.id), "features": features(s, b.id), "scale": scale_info(s, b.id)}


@router.post("/update")
def api_update(b: UpdBody) -> dict:
    return {"ok": True, "photo": update_photo(store(b.folder), b.id, b.values, b.by)}


@router.post("/delete")
def api_delete(b: PidBody) -> dict:
    s = store(b.folder)
    delete_photo(s, b.id, b.by)
    return {"ok": True, "summary": _summary(s)}


@router.post("/feature/save")
def api_feat_save(b: FeatBody) -> dict:
    s = store(b.folder)
    j = save_feature(s, b.photo_id, b.feat_id, b.feat, b.by)
    return {"ok": True, **j, "scale": scale_info(s, b.photo_id)}


@router.post("/feature/delete")
def api_feat_delete(b: FidBody) -> dict:
    s = store(b.folder)
    with s.conn() as c:
        r = c.execute("SELECT photo_id FROM features WHERE id=?", (b.feat_id,)).fetchone()
    feats = delete_feature(s, b.feat_id, b.by)
    return {"ok": True, "features": feats, "scale": scale_info(s, r["photo_id"]) if r else None}


@router.post("/feature/split")
def api_feat_split(b: SplitBody) -> dict:
    return {"ok": True, **split_line(store(b.folder), b.feat_id, b.at, b.by)}


@router.post("/feature/join")
def api_feat_join(b: JoinBody) -> dict:
    return {"ok": True, **join_lines(store(b.folder), b.a, b.b, b.by)}


@router.post("/kinds")
def api_kinds(b: KindsBody) -> dict:
    return {"ok": True, "kinds": save_kinds(store(b.folder), b.kinds, b.by)}


@router.post("/history")
def api_history(b: PidBody) -> dict:
    s = store(b.folder)
    r = photo(s, b.id)
    return {"ok": True, "history": history(s, b.id), "ai": r.get("ai_json")}


@router.post("/ai")
def api_ai(b: AiOBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "photo": ai_describe(s, b.id, b.host, b.model, b.extra, b.max_px)}


# ================================================================ georeferensi (titik survey) & ekspor STR / DXF
# Titik kontrol: tanda Pylox / pita di foto yang diukur survey (E, N, RL). Foto dianggap memotret satu BIDANG
# (dinding = wall, lantai = floor). Bidang + transformasi piksel -> bidang dihitung dari jumlah titik:
#   2 titik : wall = bidang tegak melalui kedua titik, floor = bidang datar (RL rata-rata); similaritas (skala, rotasi)
#   3 titik : bidang melalui 3 titik (boleh miring); affine (tanpa koreksi perspektif)
#   >=4     : bidang terbaik (kuadrat terkecil) + homografi (koreksi perspektif)
# Galat tiap titik = jarak 3D antara posisi hasil hitung dan koordinat survey (meter).
import math  # noqa: E402

import numpy as np  # noqa: E402


def _basis(pts3: np.ndarray, kind: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Titik asal c, sumbu bidang e1 (mendatar), e2 (ke atas untuk wall / ke utara untuk floor), normal n."""
    c = pts3.mean(axis=0)
    n_pts = len(pts3)
    if n_pts == 2:
        if kind == "floor":
            n = np.array([0.0, 0.0, 1.0])
        else:
            d = pts3[1] - pts3[0]
            h = np.array([d[0], d[1], 0.0])
            if np.linalg.norm(h) < 0.05:
                raise ValueError("Dua titik georef hampir tegak lurus satu di atas yang lain: arah dinding tidak bisa ditentukan. Tambah titik ketiga.")
            h /= np.linalg.norm(h)
            n = np.array([-h[1], h[0], 0.0])
    else:
        q = pts3 - c
        _u, s, vt = np.linalg.svd(q)
        if s[1] < 1e-3 * max(1.0, s[0]) or s[0] < 0.05:
            raise ValueError("Titik georef hampir segaris: bidang foto tidak bisa ditentukan. Pakai titik yang menyebar (kiri, kanan, atas, bawah).")
        n = vt[2]
    n = n / np.linalg.norm(n)
    if kind == "floor":
        if n[2] < 0:
            n = -n
        e2 = np.array([0.0, 1.0, 0.0]) - n * n[1]  # utara diproyeksikan ke bidang
        if np.linalg.norm(e2) < 1e-6:
            e2 = np.array([1.0, 0.0, 0.0]) - n * n[0]
        e2 /= np.linalg.norm(e2)
        e1 = np.cross(e2, n)
    else:
        e1 = np.cross(np.array([0.0, 0.0, 1.0]), n)
        if np.linalg.norm(e1) < 1e-6:  # bidang hampir datar padahal disebut wall
            e1 = np.array([1.0, 0.0, 0.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        if e2[2] < 0:
            e1, e2 = -e1, -e2
        e2 /= np.linalg.norm(e2)
    return c, e1 / np.linalg.norm(e1), e2, n


def _fit(img: np.ndarray, pl: np.ndarray, n: int) -> tuple[str, np.ndarray]:
    """Matriks 3x3 H: [s, t, w] = H @ [x, y, 1] (koordinat bidang dari piksel)."""
    x, y = img[:, 0], img[:, 1]
    if n == 2:  # similaritas: s = a x - b y + c ; t = b x + a y + d  (y gambar dibalik dulu: ke atas positif)
        A = np.zeros((4, 4))
        r = np.zeros(4)
        for i in range(2):
            A[2 * i] = [x[i], -y[i], 1, 0]
            A[2 * i + 1] = [y[i], x[i], 0, 1]
            r[2 * i], r[2 * i + 1] = pl[i, 0], pl[i, 1]
        a, b, c, d = np.linalg.solve(A, r)
        return "similaritas (2 titik)", np.array([[a, -b, c], [b, a, d], [0, 0, 1.0]])
    if n == 3:
        A = np.c_[x, y, np.ones(3)]
        s = np.linalg.solve(A, pl[:, 0])
        t = np.linalg.solve(A, pl[:, 1])
        return "affine (3 titik)", np.array([s, t, [0, 0, 1.0]])
    # homografi DLT dengan normalisasi (Hartley)
    def norm_t(P):
        m = P.mean(axis=0)
        d = np.sqrt(((P - m) ** 2).sum(axis=1)).mean() or 1.0
        k = math.sqrt(2) / d
        return np.array([[k, 0, -k * m[0]], [0, k, -k * m[1]], [0, 0, 1.0]])
    T1, T2 = norm_t(img), norm_t(pl)
    a = (T1 @ np.c_[img, np.ones(len(img))].T).T
    b = (T2 @ np.c_[pl, np.ones(len(pl))].T).T
    rows = []
    for (x1, y1, _), (x2, y2, _) in zip(a, b):
        rows.append([-x1, -y1, -1, 0, 0, 0, x2 * x1, x2 * y1, x2])
        rows.append([0, 0, 0, -x1, -y1, -1, y2 * x1, y2 * y1, y2])
    _u, _s, vt = np.linalg.svd(np.array(rows))
    Hn = vt[-1].reshape(3, 3)
    H = np.linalg.inv(T2) @ Hn @ T1
    return f"homografi / koreksi perspektif ({n} titik)", H / H[2, 2]


def georef_solve(gr: Optional[dict], w: int, h: int, kind: str) -> Optional[dict]:
    """Hasil georeferensi foto: metode, galat per titik & RMS (m), orientasi bidang, skala (m / piksel)."""
    if not gr:
        return None
    P = [p for p in gr.get("points") or [] if all(p.get(k) not in (None, "") for k in ("u", "v", "e", "n", "rl"))]
    out: dict[str, Any] = {"n": len(P), "kind": kind, "ok": False}
    if len(P) < 2:
        out["msg"] = "Perlu minimal 2 titik georef lengkap (posisi di foto + E, N, RL). Disarankan 4 titik atau lebih."
        return out
    img = np.array([[float(p["u"]) * w, -float(p["v"]) * h] for p in P])  # y dibalik: ke atas positif
    pts3 = np.array([[float(p["e"]), float(p["n"]), float(p["rl"])] for p in P])
    try:
        c, e1, e2, nrm = _basis(pts3, kind)
        pl = np.c_[(pts3 - c) @ e1, (pts3 - c) @ e2]
        if len(P) >= 3 and np.linalg.matrix_rank(np.c_[img, np.ones(len(P))], tol=1e-6) < 3:
            raise ValueError("Titik georef di foto hampir segaris; pilih titik yang menyebar.")
        method, H = _fit(img, pl, len(P))
    except (ValueError, np.linalg.LinAlgError) as e:
        out["msg"] = str(e) if isinstance(e, ValueError) else "Titik georef tidak bisa dipakai (susunan titik terlalu sempit / segaris)."
        return out
    res = []
    for p, xy, q in zip(P, img, pts3):
        s, t, ww = H @ np.array([xy[0], xy[1], 1.0])
        g = c + (s / ww) * e1 + (t / ww) * e2
        res.append({"name": p.get("name") or "", "de": float(g[0] - q[0]), "dn": float(g[1] - q[1]), "drl": float(g[2] - q[2]),
                    "err": float(np.linalg.norm(g - q))})
    rms = math.sqrt(sum(r["err"] ** 2 for r in res) / len(res))
    dip = math.degrees(math.acos(min(1.0, abs(nrm[2]))))
    up = nrm if nrm[2] >= 0 else -nrm
    ddir = (math.degrees(math.atan2(up[0], up[1])) + 360) % 360 if dip > 0.5 else None
    # skala di tengah foto: panjang 1 piksel (rata-rata arah x & y) dalam meter
    def to_pl(x, y):
        v_ = H @ np.array([x, y, 1.0])
        return v_[:2] / v_[2]
    cx, cy = w / 2, -h / 2
    m_per_px = float((np.linalg.norm(to_pl(cx + 1, cy) - to_pl(cx, cy)) + np.linalg.norm(to_pl(cx, cy - 1) - to_pl(cx, cy))) / 2)
    warn = []
    if len(P) == 2:
        warn.append("2 titik: tanpa koreksi perspektif dan tanpa pemeriksaan galat. Hanya teliti bila foto diambil tegak lurus bidang.")
    elif len(P) == 3:
        warn.append("3 titik: tanpa koreksi perspektif dan tanpa pemeriksaan galat (selalu pas). Tambah titik ke-4 untuk koreksi perspektif.")
    elif len(P) == 4:
        warn.append("4 titik: perspektif dikoreksi, tetapi galat posisi di bidang selalu nol; titik ke-5 atau lebih memberi pemeriksaan galat.")
    off = max(abs(float((q - c) @ nrm)) for q in pts3)
    if len(P) >= 4 and off > 0.5:
        warn.append(f"Titik survey menyimpang hingga {off:.2f} m dari bidang terbaik: permukaan tidak rata / foto mencakup lebih dari satu bidang.")
    if kind == "wall" and dip < 45:
        warn.append(f"Bidang hasil hitung landai (dip {dip:.0f}°) padahal jenis foto 'dinding'. Periksa jenis foto / koordinat titik.")
    if kind == "floor" and dip > 45:
        warn.append(f"Bidang hasil hitung curam (dip {dip:.0f}°) padahal jenis foto 'lantai'. Periksa jenis foto / koordinat titik.")
    out.update(ok=True, method=method, rms=rms, residuals=res, dip=dip, dip_dir=ddir, m_per_px=m_per_px, warn=warn,
               H=H.tolist(), c=c.tolist(), e1=e1.tolist(), e2=e2.tolist())
    return out


def to_world(sol: dict, w: int, h: int, pts: list) -> list[list[float]]:
    H, c, e1, e2 = np.array(sol["H"]), np.array(sol["c"]), np.array(sol["e1"]), np.array(sol["e2"])
    out = []
    for u, v in pts:
        s, t, ww = H @ np.array([u * w, -v * h, 1.0])
        g = c + (s / ww) * e1 + (t / ww) * e2
        out.append([round(float(g[0]), 3), round(float(g[1]), 3), round(float(g[2]), 3)])
    return out


def measure(sol: dict, w: int, h: int, f: dict) -> dict:
    """Panjang 3D, luas (di bidang), apparent dip garis lurus ujung-ke-ujung."""
    P = np.array(to_world(sol, w, h, f["pts"]))
    m: dict[str, Any] = {}
    if f["shape"] == "line" and len(P) >= 2:
        m["length_m"] = float(sum(np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)))
        d = P[-1] - P[0]
        hz = math.hypot(d[0], d[1])
        if hz > 1e-6 or abs(d[2]) > 1e-6:
            if d[2] > 0:
                d = -d
            m["apparent_dip"] = math.degrees(math.atan2(-d[2], hz))
            m["trend"] = (math.degrees(math.atan2(d[0], d[1])) + 360) % 360 if hz > 1e-6 else None
    elif f["shape"] == "poly" and len(P) >= 3:
        c, e1, e2 = np.array(sol["c"]), np.array(sol["e1"]), np.array(sol["e2"])
        q = np.c_[(P - c) @ e1, (P - c) @ e2]
        x, y = q[:, 0], q[:, 1]
        m["area_m2"] = float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2)
        m["perimeter_m"] = float(sum(np.linalg.norm(P[(i + 1) % len(P)] - P[i]) for i in range(len(P))))
    return m


def save_georef(s: Store, pid: int, points: list[dict], kind: Optional[str], by: str) -> dict:
    clean = []
    for i, p in enumerate(points):
        q: dict[str, Any] = {"name": str(p.get("name") or f"G{i + 1}")[:30]}
        for k in ("u", "v"):  # kosong = koordinat sudah ada, posisi di foto belum diklik
            v = p.get(k)
            q[k] = None if v in (None, "") else max(0.0, min(1.0, round(float(v), 6)))
        for k in ("e", "n", "rl"):
            v = p.get(k)
            if v in (None, ""):
                q[k] = None
                continue
            try:
                q[k] = round(float(str(v).replace(",", ".")), 4)
            except ValueError:
                raise ValueError(f"Titik {q['name']}: {k.upper()} harus angka.") from None
        clean.append(q)
    names = [q["name"] for q in clean]
    if len(names) != len(set(names)):
        raise ValueError("Nama titik georef tidak boleh kembar.")
    if kind not in (None, "", "wall", "floor"):
        raise ValueError("Jenis bidang harus 'wall' atau 'floor'.")
    r = photo(s, pid)
    gr = {"points": clean, "kind": kind or None}
    with s.lock, s.conn() as c:
        c.execute("UPDATE photos SET georef_json=?, edited_by=?, edited_at=? WHERE id=?", (json.dumps(gr), by, core_io.now(), pid))
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                  (pid, "georef", json.dumps(r.get("georef"))[:2000] if r.get("georef") else None, f"{len(clean)} titik", "edit", by, core_io.now()))
    return georef_info(s, pid)


def plane_kind(r: dict) -> str:
    g = r.get("georef") or {}
    return g.get("kind") or (r.get("desc") or {}).get("photo_type") or "wall"


def georef_info(s: Store, pid: int) -> dict:
    r = photo(s, pid)
    kind = plane_kind(r)
    sol = georef_solve(r.get("georef"), r["w"], r["h"], kind)
    meas = {}
    if sol and sol.get("ok"):
        meas = {f["id"]: measure(sol, r["w"], r["h"], f) for f in features(s, pid) if f["shape"] != "point"}
    return {"georef": r.get("georef") or {"points": [], "kind": None}, "kind": kind, "solution": sol, "measure": meas}


# ---------------------------------------------------------------- ekspor STR / DXF (koordinat 3D E, N, RL)
NO_EXPORT = {"skala"}


def _clean_txt(t: Any) -> str:
    return re.sub(r"[,\r\n]+", " ", str(t or "")).strip()[:60]


def export_items(s: Store, ids: list[int]) -> tuple[list[dict], list[str]]:
    """Fitur tergeoreferensi dari foto-foto terpilih; foto tanpa georef yang sah dilaporkan."""
    ks = {k["key"]: k for k in kinds(s)}
    items, skipped = [], []
    for pid in ids or [p["id"] for p in photos(s)]:
        r = photo(s, pid)
        sol = georef_solve(r.get("georef"), r["w"], r["h"], plane_kind(r))
        if not sol or not sol.get("ok"):
            skipped.append(f"{r.get('title') or r['name']}: {(sol or {}).get('msg') or 'belum digeoreferensi'}")
            continue
        for f in features(s, pid):
            if f["kind"] in NO_EXPORT:
                continue
            k = ks.get(f["kind"]) or {"name": f["kind"], "string": 50, "color": "#7a5aa6"}
            items.append({"photo": r.get("title") or r["name"], "kind": f["kind"], "kname": k["name"], "string": int(k["string"]),
                          "color": k["color"], "shape": f["shape"], "name": f.get("name") or "", "attrs": f["attrs"],
                          "xyz": to_world(sol, r["w"], r["h"], f["pts"])})
    return items, skipped


def to_str(items: list[dict], name: str = "singkapan") -> bytes:
    """Surpac STR teks: string, Y (northing), X (easting), Z, D1 jenis, D2 nama, D3 foto, D4.. kadar."""
    L = [f"{_clean_txt(name) or 'singkapan'},{time.strftime('%d-%b-%y')},Core-Ex singkapan,", "0, 0.000, 0.000, 0.000,"]
    for it in sorted(items, key=lambda x: x["string"]):
        pts = it["xyz"] + ([it["xyz"][0]] if it["shape"] == "poly" else [])
        a = it["attrs"]
        d = [_clean_txt(it["kname"]), _clean_txt(it["name"]), _clean_txt(it["photo"])]
        for k in ("au_ppm", "ag_ppm", "sxs_pct"):
            if a.get(k) is not None:
                d.append(f"{k[:-4] if k != 'sxs_pct' else 'sxs'}={a[k]:g}")
        for x, y, z in pts:
            L.append(f"{it['string']}, {y:.3f}, {x:.3f}, {z:.3f}, " + ", ".join(d))
        L.append("0, 0.000, 0.000, 0.000,")
    L.append("0, 0.000, 0.000, 0.000, END")
    return ("\r\n".join(L) + "\r\n").encode("utf-8")


_ACI = [(1, (255, 0, 0)), (2, (255, 255, 0)), (3, (0, 255, 0)), (4, (0, 255, 255)), (5, (0, 0, 255)), (6, (255, 0, 255)), (7, (255, 255, 255)),
        (8, (128, 128, 128)), (30, (255, 127, 0)), (40, (255, 191, 0)), (140, (0, 127, 255)), (170, (0, 0, 127)), (220, (255, 0, 127)),
        (94, (0, 127, 0)), (14, (127, 0, 0)), (32, (165, 82, 0))]


def _aci(hexc: str) -> int:
    try:
        r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    except (ValueError, IndexError):
        return 7
    return min(_ACI, key=lambda t: (t[1][0] - r) ** 2 + (t[1][1] - g) ** 2 + (t[1][2] - b) ** 2)[0]


def to_dxf(items: list[dict]) -> bytes:
    """DXF R12 ASCII: satu layer per jenis fitur, 3D POLYLINE (poligon tertutup), TEXT untuk label & nama."""
    def lay(it):
        return re.sub(r"[^A-Za-z0-9_-]+", "_", it["kname"]).strip("_").upper()[:31] or "FITUR"
    layers = {}
    for it in items:
        layers.setdefault(lay(it), _aci(it["color"]))
    o = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "0", "ENDSEC", "0", "SECTION", "2", "TABLES",
         "0", "TABLE", "2", "LAYER", "70", str(len(layers))]
    for n, c in layers.items():
        o += ["0", "LAYER", "2", n, "70", "0", "62", str(c), "6", "CONTINUOUS"]
    o += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    for it in items:
        L = lay(it)
        if it["shape"] == "point":
            x, y, z = it["xyz"][0]
            o += ["0", "TEXT", "8", L, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", f"{z:.3f}", "40", "0.5", "1", _clean_txt(it["name"]) or it["kname"]]
            continue
        o += ["0", "POLYLINE", "8", L, "66", "1", "10", "0", "20", "0", "30", "0", "70", str(8 | (1 if it["shape"] == "poly" else 0))]
        for x, y, z in it["xyz"]:
            o += ["0", "VERTEX", "8", L, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", f"{z:.3f}", "70", "32"]
        o += ["0", "SEQEND", "8", L]
        if it["name"]:
            x, y, z = it["xyz"][len(it["xyz"]) // 2]
            o += ["0", "TEXT", "8", L, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", f"{z:.3f}", "40", "0.3", "1", _clean_txt(it["name"])]
    o += ["0", "ENDSEC", "0", "EOF"]
    return ("\r\n".join(o) + "\r\n").encode("ascii", "replace")


class GeoBody(FBody):
    id: int
    points: list[dict[str, Any]]
    kind: Optional[str] = None


class ExpBody(FBody):
    ids: list[int] = []
    fmt: str = "str"
    name: str = "singkapan"


@router.post("/georef")
def api_georef(b: GeoBody) -> dict:
    return {"ok": True, **save_georef(store(b.folder), b.id, b.points, b.kind, b.by)}


@router.post("/georef/info")
def api_georef_info(b: PidBody) -> dict:
    return {"ok": True, **georef_info(store(b.folder), b.id)}


@router.post("/export/check")
def api_export_check(b: ExpBody) -> dict:
    items, skipped = export_items(store(b.folder), b.ids)
    return {"ok": True, "n": len(items), "skipped": skipped}


@router.post("/export")
def api_export(b: ExpBody):
    from fastapi.responses import Response
    items, skipped = export_items(store(b.folder), b.ids)
    if not items:
        raise ValueError("Tidak ada fitur tergeoreferensi untuk diekspor." + (" " + "; ".join(skipped) if skipped else ""))
    if b.fmt == "dxf":
        return Response(to_dxf(items), media_type="application/dxf")
    return Response(to_str(items, b.name), media_type="text/plain")
