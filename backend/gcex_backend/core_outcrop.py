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
