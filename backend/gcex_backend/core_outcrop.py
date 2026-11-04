"""DB-Ex: ruang kerja Singkapan (foto singkapan / trenching hasil mapping lapangan).

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
    ("orientasi", "Strike / dip terukur", "point", "#ffd43b", 12),
    ("label_zona", "Label zona (rentang)", "line", "#ffffff", 92),
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
    try:  # metadata HP: posisi kamera, arah hadap, tanggal pengambilan
        from . import core_oclokasi
        core_oclokasi.on_add(s, pid)
    except Exception:  # noqa: BLE001
        pass
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
def _ltr(kind: str, shape: str, pts: list, attrs: dict) -> list:
    """Garis channel / berinterval selalu kiri -> kanan foto: collar (0 m) di ujung kiri, EOH di ujung kanan."""
    if shape != "line" or len(pts) < 2:
        return pts
    if kind != "channel" and not any(isinstance(x, dict) and x.get("from") is not None for x in (attrs or {}).get("samples") or []):
        return pts
    a, b = pts[0], pts[-1]
    if a[0] > b[0] + 1e-9 or (abs(a[0] - b[0]) <= 1e-9 and a[1] > b[1]):
        return list(reversed(pts))
    return pts


def _feat(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["pts"] = json.loads(d["pts"])
    try:
        d["attrs"] = json.loads(d["attrs"] or "{}")
    except ValueError:
        d["attrs"] = {}
    d["pts"] = _ltr(d["kind"], d["shape"], d["pts"], d["attrs"])
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


ATTR_NUM = ("au_ppm", "ag_ppm", "sxs_pct", "length_m", "strike", "dip")


# ---------------------------------------------------------------- unsur assay & sampel per interval
# Kadar diisi manual / ditempel per sampel. Garis channel / trenching boleh dibagi menjadi beberapa interval
# (dari-ke meter dari ujung awal garis); poligon / garis tanpa interval memakai satu sampel tanpa dari-ke.
# Nilai: angka, atau teks "<0.01" / ">100" (di bawah / di atas batas deteksi); hitungan memakai setengah batas
# deteksi untuk "<" dan batasnya untuk ">".
UNITS = ["ppm", "ppb", "%", "g/t", "oz/t"]
DEFAULT_ELEMENTS = [
    {"key": "Au", "unit": "ppm", "dec": 2, "show": True, "classes": [0.2, 0.5, 1.0]},
    {"key": "Ag", "unit": "ppm", "dec": 1, "show": True, "classes": []},
    {"key": "Cu", "unit": "ppm", "dec": 0, "show": False, "classes": []},
    {"key": "Pb", "unit": "ppm", "dec": 0, "show": False, "classes": []},
    {"key": "Zn", "unit": "ppm", "dec": 0, "show": False, "classes": []},
    {"key": "As", "unit": "ppm", "dec": 0, "show": False, "classes": []},
    {"key": "S", "unit": "%", "dec": 2, "show": False, "classes": []},
    {"key": "SxS", "unit": "%", "dec": 2, "show": True, "classes": []},
    {"key": "C", "unit": "%", "dec": 2, "show": False, "classes": []},
]
LEGACY = {"au_ppm": "Au", "ag_ppm": "Ag", "sxs_pct": "SxS"}
MAX_SAMPLES = 300


def elements(s: Store) -> list[dict]:
    with s.conn() as c:
        r = c.execute("SELECT value FROM meta WHERE key='elements'").fetchone()
    if r:
        try:
            v = json.loads(r["value"])
            if isinstance(v, list) and v:
                return v
        except ValueError:
            pass
    return [dict(e) for e in DEFAULT_ELEMENTS]


def save_elements(s: Store, lst: list[dict], by: str) -> list[dict]:
    clean, seen = [], set()
    for e in lst:
        key = re.sub(r"[^A-Za-z0-9_]", "", str(e.get("key") or ""))[:10]
        if not key:
            continue
        if key.lower() in seen:
            raise ValueError(f"Unsur {key} tercantum dua kali.")
        seen.add(key.lower())
        unit = e.get("unit") if e.get("unit") in UNITS else "ppm"
        try:
            dec = max(0, min(4, int(e.get("dec", 2))))
        except (TypeError, ValueError):
            dec = 2
        cl = e.get("classes") or []
        if isinstance(cl, str):
            cl = [x for x in re.split(r"[;\s]+", cl.replace(",", ".")) if x]
        try:
            cl = [float(x) for x in cl]
        except (TypeError, ValueError):
            raise ValueError(f"Batas kelas {key} harus angka, dipisah titik koma (mis. 0.2; 0.5; 1).") from None
        if any(b <= a for a, b in zip(cl, cl[1:])):
            raise ValueError(f"Batas kelas {key} harus naik (mis. 0.2; 0.5; 1).")
        if len(cl) > 4:
            raise ValueError(f"Batas kelas {key} maksimal 4 (5 kelas warna).")
        clean.append({"key": key, "unit": unit, "dec": dec, "show": bool(e.get("show")), "classes": cl})
    if not clean:
        raise ValueError("Daftar unsur kosong.")
    with s.lock, s.conn() as c:
        old = c.execute("SELECT value FROM meta WHERE key='elements'").fetchone()
        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('elements', ?)", (json.dumps(clean, ensure_ascii=False),))
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (NULL,'daftar unsur',?,?, 'edit', ?, ?)",
                  (old["value"] if old else None, json.dumps(clean, ensure_ascii=False), by, core_io.now()))
    return elements(s)


def grade_num(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(",", ".")
    if t.startswith("<"):
        return float(t[1:]) / 2
    if t.startswith(">"):
        return float(t[1:])
    return float(t)


def _clean_grade(k: str, v: Any) -> Any:
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, (int, float)):
        x = float(v)
    else:
        t = str(v).strip().replace(",", ".").replace(" ", "")
        if t[:1] in "<>":
            try:
                if float(t[1:]) <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(f"Nilai {k} '{v}' tidak dikenal; pakai angka atau <batas deteksi (mis. <0.01).") from None
            return t
        try:
            x = float(t)
        except ValueError:
            raise ValueError(f"Nilai {k} '{v}' harus angka atau <batas deteksi (mis. <0.01).") from None
    if x < 0:
        raise ValueError(f"Nilai {k} tidak boleh negatif (pakai <batas deteksi untuk di bawah deteksi).")
    return x


def _clean_samples(lst: Any) -> list[dict]:
    if not isinstance(lst, list):
        raise ValueError("Data sampel harus berupa daftar.")
    if len(lst) > MAX_SAMPLES:
        raise ValueError(f"Maksimal {MAX_SAMPLES} sampel per fitur.")
    out = []
    for i, x in enumerate(lst):
        if not isinstance(x, dict):
            continue
        sid = str(x.get("id") or "").strip()[:40]
        lab = sid or f"baris {i + 1}"
        fr, to = x.get("from"), x.get("to")
        try:
            fr = None if fr in (None, "") else float(str(fr).replace(",", "."))
            to = None if to in (None, "") else float(str(to).replace(",", "."))
        except ValueError:
            raise ValueError(f"Sampel {lab}: dari / ke harus angka (meter).") from None
        if (fr is None) != (to is None):
            raise ValueError(f"Sampel {lab}: isi dari DAN ke (meter), atau kosongkan keduanya.")
        if fr is not None and (fr < 0 or to <= fr):
            raise ValueError(f"Sampel {lab}: 'ke' harus lebih besar dari 'dari' ({fr:g} - {to:g} m).")
        g = {}
        for k, v in (x.get("grades") or {}).items():
            k = re.sub(r"[^A-Za-z0-9_]", "", str(k))[:10]
            cv = _clean_grade(k, v)
            if k and cv is not None:
                g[k] = cv
        if not sid and fr is None and not g:
            continue  # baris kosong
        q: dict[str, Any] = {"id": sid, "from": fr, "to": to, "grades": g}
        for k in ("bu", "bv"):
            if isinstance(x.get(k), (int, float)):
                q[k] = max(0.0, min(1.0, round(float(x[k]), 4)))
        out.append(q)
    iv = sorted((q for q in out if q["from"] is not None), key=lambda q: q["from"])
    for a, b in zip(iv, iv[1:]):
        if b["from"] < a["to"] - 1e-6:
            raise ValueError(f"Interval {a['id'] or ''} ({a['from']:g}-{a['to']:g} m) dan {b['id'] or ''} ({b['from']:g}-{b['to']:g} m) tumpang-tindih.")
    ids = [q["id"] for q in out if q["id"]]
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        raise ValueError("Sample ID kembar: " + ", ".join(sorted(dup)))
    return iv + [q for q in out if q["from"] is None]


def samples_of(attrs: dict) -> list[dict]:
    """Sampel fitur; atribut lama (au_ppm / ag_ppm / sxs_pct) dibaca sebagai satu sampel."""
    sm = attrs.get("samples")
    if isinstance(sm, list) and sm:
        return sm
    g = {LEGACY[k]: attrs[k] for k in LEGACY if attrs.get(k) is not None}
    return [{"id": "", "from": None, "to": None, "grades": g}] if g else []


def composite(samples: list[dict]) -> dict:
    """Rata-rata tertimbang panjang per unsur untuk interval yang punya dari-ke (nilai <DL = setengah DL)."""
    iv = [x for x in samples if x.get("from") is not None]
    if not iv:
        return {}
    out: dict[str, Any] = {"from": min(x["from"] for x in iv), "to": max(x["to"] for x in iv), "length": sum(x["to"] - x["from"] for x in iv),
                           "n": len(iv), "grades": {}}
    keys = {k for x in iv for k in x["grades"]}
    for k in sorted(keys):
        num = den = 0.0
        for x in iv:
            v = grade_num(x["grades"].get(k))
            if v is not None:
                L = x["to"] - x["from"]
                num, den = num + v * L, den + L
        if den > 0:
            out["grades"][k] = num / den
    return out


def _clean_attrs(a: Any) -> dict:
    if not isinstance(a, dict):
        return {}
    out: dict[str, Any] = {}
    for k, v in a.items():
        k = str(k)[:40]
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        if k == "samples":
            v = _clean_samples(v)
            if not v:
                continue
            out[k] = v
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
    if "strike" in out and not 0 <= out["strike"] <= 360:
        raise ValueError("Strike harus 0-360°.")
    if "dip" in out and not 0 <= out["dip"] <= 90:
        raise ValueError("Dip harus 0-90°.")
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
    pts = _ltr(kind, shape, pts, attrs)
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
    return {"ok": True, "photos": photos(s), "kinds": kinds(s), "elements": elements(s), "desc_fields": [{"key": k, "label": l} for k, l in DESC],
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
    # arah pandang kamera (dinding) / arah atas foto (lantai), azimut derajat
    g0 = c + to_pl(cx, cy)[0] * e1 + to_pl(cx, cy)[1] * e2
    gx = c + to_pl(cx + 10, cy)[0] * e1 + to_pl(cx + 10, cy)[1] * e2
    gy = c + to_pl(cx, cy + 10)[0] * e1 + to_pl(cx, cy + 10)[1] * e2
    R, Uimg = gx - g0, gy - g0
    view_az = (math.degrees(math.atan2(-R[1], R[0])) + 360) % 360 if math.hypot(R[0], R[1]) > 1e-9 else None
    up_az = (math.degrees(math.atan2(Uimg[0], Uimg[1])) + 360) % 360 if math.hypot(Uimg[0], Uimg[1]) > 1e-9 else None
    out.update(ok=True, method=method, rms=rms, residuals=res, dip=dip, dip_dir=ddir, m_per_px=m_per_px, warn=warn,
               view_az=view_az, up_az=up_az,
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
        m["seg_m"] = [float(np.linalg.norm(P[i + 1] - P[i])) for i in range(len(P) - 1)]
        m["length_m"] = float(sum(m["seg_m"]))
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
NO_EXPORT = {"skala", "label_zona"}


def _clean_txt(t: Any) -> str:
    return re.sub(r"[,\r\n]+", " ", str(t or "")).strip()[:60]


# ---------------------------------------------------------------- sumber koordinat: georef (bawaan) atau tempel ke topografi
# Kebenaran posisi = georef (titik survey di bidang foto). "Tempel ke topografi" OPSIONAL: titik bidang diproyeksikan ke DTM
# as-built (lantai: vertikal; dinding: sepanjang normal bidang). Di luar DTM boleh diisi Depth Anything yang dikalibrasi ke
# meter (titik yang kena DTM / titik georef); sisanya tetap di bidang georef. Topografi survey bisa lebih tua dari foto,
# jadi QC melaporkan jarak titik survey ke DTM dan tanggal.
def _photo_date(r: dict) -> str:
    t = str(r.get("taken") or "")[:10].replace(":", "-")
    return t if re.match(r"^\d{4}-\d{2}-\d{2}$", t) else ""


def surface_ctx(s: Store, r: dict, sol: dict, opt: Optional[dict]) -> dict:
    """Konteks per foto untuk opsi koordinat; opt = {"coord": "georef"|"topo", "topo_id", "depth": bool, "maxd", "step"}."""
    from . import core_topo, core_vision
    opt = dict(opt or {})
    ctx: dict[str, Any] = {"mode": opt.get("coord") or "georef", "sol": sol, "w": r["w"], "h": r["h"], "warn": [], "r": r}
    if ctx["mode"] != "topo":
        return ctx
    kind = plane_kind(r)
    n = np.cross(np.array(sol["e1"]), np.array(sol["e2"]))
    n = n / np.linalg.norm(n)
    d = np.array([0.0, 0.0, 1.0]) if kind == "floor" else n
    ctx.update(d=d, maxd=float(opt.get("maxd") or 10.0), step=float(opt.get("step") or 0.5), V=None, T=None, fit=None, dm=None)
    tid = opt.get("topo_id")
    topo = None
    if tid:
        topo = next((t for t in core_topo.topo_list(s) if t["id"] == int(tid)), None)
        if not topo:
            raise ValueError(f"Topografi #{tid} tidak ada di proyek.")
        ctx["V"], ctx["T"] = core_topo.topo_tin(s, int(tid))
        ctx["topo"] = topo
        pd = _photo_date(r)
        if pd and pd > topo["survey_date"]:
            ctx["warn"].append(f"Foto ({pd}) lebih baru dari topografi \"{topo['name']}\" ({topo['survey_date']}): permukaan bisa sudah "
                               "berubah oleh penggalian; koordinat georef tetap acuan.")
    W, H = r["w"], r["h"]
    # grid kalibrasi & cakupan (20 x 15 titik di foto)
    gu, gv = np.meshgrid(np.linspace(0.03, 0.97, 20), np.linspace(0.03, 0.97, 15))
    guv = np.c_[gu.ravel(), gv.ravel()]
    G = np.array(to_world(sol, W, H, guv.tolist()))
    gt = np.full(len(G), np.nan)
    if ctx["V"] is not None:
        gt, _ok = core_topo.ray_tin(G, np.tile(d, (len(G), 1)), ctx["V"], ctx["T"], ctx["maxd"])
        ctx["coverage"] = float(np.mean(~np.isnan(gt)))
        if ctx["coverage"] < 0.5:
            ctx["warn"].append(f"Hanya {ctx['coverage'] * 100:.0f}% foto tercakup DTM (dalam {ctx['maxd']:g} m dari bidang georef).")
    # jarak titik survey (georef) ke DTM: indikator topografi belum diperbarui
    P = [p for p in ((r.get("georef") or {}).get("points") or []) if all(p.get(k) not in (None, "") for k in ("u", "v", "e", "n", "rl"))]
    cuv = np.array([[p["u"], p["v"]] for p in P]) if P else np.zeros((0, 2))
    cq = np.array([[p["e"], p["n"], p["rl"]] for p in P]) if P else np.zeros((0, 3))
    cg = np.array(to_world(sol, W, H, cuv.tolist())) if len(P) else np.zeros((0, 3))
    c_off = (cq - cg) @ d if len(P) else np.zeros(0)
    ctx["ctrl"] = []
    if ctx["V"] is not None and len(P):
        ct, _ok = core_topo.ray_tin(cq, np.tile(d, (len(cq), 1)), ctx["V"], ctx["T"], ctx["maxd"])
        ctx["ctrl"] = [{"name": p.get("name") or "", "dist": None if np.isnan(t) else float(abs(t))} for p, t in zip(P, ct)]
        ds = [c["dist"] for c in ctx["ctrl"] if c["dist"] is not None]
        if ds:
            ctx["ctrl_med"] = float(np.median(ds))
            if ctx["ctrl_med"] > 0.5:
                ctx["warn"].append(f"Titik survey berjarak median {ctx['ctrl_med']:.2f} m dari DTM: topografi kemungkinan belum memuat "
                                   "galian / permukaan terbaru.")
    # Depth Anything: isi di luar DTM, dikalibrasi t = a * kedalaman_relatif + b
    if opt.get("depth"):
        try:
            dm = core_vision.depth_map(s.photos / r["file"], s.root / "depth" / f"{r['id']}.npy")
        except Exception as e:  # noqa: BLE001
            ctx["warn"].append(f"Depth Anything tidak dipakai: {e}")
            dm = None
        if dm is not None:
            xs, ys = [], []
            ok = ~np.isnan(gt)
            if ok.any():
                xs += list(core_vision.sample(dm, guv[ok]))
                ys += list(gt[ok])
            if len(P):
                xs += list(core_vision.sample(dm, cuv))
                ys += list(c_off)
            X, Y = np.array(xs, float), np.array(ys, float)
            fit = None
            if len(X) >= 3 and X.std() > 0.02:
                keep = np.ones(len(X), bool)
                for _ in range(3):
                    A = np.c_[X[keep], np.ones(keep.sum())]
                    a, b = np.linalg.lstsq(A, Y[keep], rcond=None)[0]
                    res = Y - (a * X + b)
                    mad = np.median(np.abs(res[keep])) * 1.4826 + 1e-6
                    nk = np.abs(res) <= max(2.5 * mad, 0.05)
                    if nk.sum() < 3 or (nk == keep).all():
                        break
                    keep = nk
                rms = float(np.sqrt(np.mean((Y[keep] - (a * X[keep] + b)) ** 2)))
                fit = {"a": float(a), "b": float(b), "rms": rms, "n": int(keep.sum())}
            if fit:
                ctx["dm"], ctx["fit"] = dm, fit
                if fit["rms"] > 0.75:
                    ctx["warn"].append(f"Kalibrasi Depth Anything kurang baik (RMS {fit['rms']:.2f} m dari {fit['n']} titik).")
            else:
                ctx["warn"].append("Depth Anything tidak bisa dikalibrasi ke meter: perlu titik yang kena DTM atau >= 4 titik georef "
                                   "yang tidak sebidang. Area di luar DTM tetap di bidang georef.")
    return ctx


def surface_xyz(ctx: dict, uv: list, closed: bool = False, dense: bool = True) -> tuple[list[list[float]], list[str], list[list[float]]]:
    """Koordinat 3D titik-titik foto menurut opsi; kembalikan (xyz, sumber per titik 'georef'|'dtm'|'depth'|'bidang', uv dipakai)."""
    from . import core_topo, core_vision
    sol, W, H = ctx["sol"], ctx["w"], ctx["h"]
    if ctx["mode"] != "topo":
        return to_world(sol, W, H, uv), ["georef"] * len(uv), [list(p) for p in uv]
    U = [list(p) for p in uv]
    if dense and len(U) >= 2:  # rapatkan (langkah ~step m di bidang) agar garis mengikuti permukaan
        Q = U + ([U[0]] if closed else [])
        Wd = to_world(sol, W, H, Q)
        out = [Q[0]]
        for i in range(len(Q) - 1):
            L = float(np.linalg.norm(np.array(Wd[i + 1]) - np.array(Wd[i])))
            k = max(1, int(math.ceil(L / ctx["step"])))
            for j in range(1, k + 1):
                out.append([Q[i][0] + (Q[i + 1][0] - Q[i][0]) * j / k, Q[i][1] + (Q[i + 1][1] - Q[i][1]) * j / k])
        U = out[:-1] if closed else out
    G = np.array(to_world(sol, W, H, U))
    t = np.full(len(G), np.nan)
    if ctx.get("V") is not None:
        t, _ok = core_topo.ray_tin(G, np.tile(ctx["d"], (len(G), 1)), ctx["V"], ctx["T"], ctx["maxd"])
    src = np.where(np.isnan(t), "bidang", "dtm").astype(object)
    if ctx.get("fit") and np.isnan(t).any():
        m = np.isnan(t)
        rv = core_vision.sample(ctx["dm"], np.array(U)[m])
        t[m] = ctx["fit"]["a"] * rv + ctx["fit"]["b"]
        src[m] = "depth"
    t = np.nan_to_num(t, nan=0.0)
    X = G + t[:, None] * ctx["d"][None, :]
    return [[round(float(v), 3) for v in p] for p in X], list(src), U


def coord_report(s: Store, pid: int, opt: dict) -> dict:
    """QC tempel ke topografi untuk satu foto (tanpa menyimpan apa pun)."""
    r = photo(s, pid)
    sol = georef_solve(r.get("georef"), r["w"], r["h"], plane_kind(r))
    if not sol or not sol.get("ok"):
        raise ValueError("Foto belum digeoreferensi: tempel ke topografi butuh georef yang sah.")
    ctx = surface_ctx(s, r, sol, dict(opt, coord="topo"))
    cnt = {"dtm": 0, "depth": 0, "bidang": 0}
    off = []
    for f in features(s, pid):
        if (f.get("attrs") or {}).get(DRAFT) or f["kind"] in NO_EXPORT:
            continue
        xyz, src, U = surface_xyz(ctx, f["pts"], f["shape"] == "poly")
        G = np.array(to_world(sol, r["w"], r["h"], U))
        for p, g, sc in zip(xyz, G, src):
            cnt[sc] = cnt.get(sc, 0) + 1
            off.append(float(np.linalg.norm(np.array(p) - g)))
    tot = sum(cnt.values()) or 1
    return {"topo": ctx.get("topo"), "coverage": ctx.get("coverage"), "ctrl": ctx.get("ctrl"), "ctrl_med": ctx.get("ctrl_med"),
            "fit": ctx.get("fit"), "counts": cnt, "pct": {k: v / tot for k, v in cnt.items()},
            "offset_med": float(np.median(off)) if off else None, "offset_max": float(max(off)) if off else None,
            "photo_date": _photo_date(r), "warn": ctx["warn"]}


def export_items(s: Store, ids: list[int], opt: Optional[dict] = None) -> tuple[list[dict], list[str]]:
    """Fitur tergeoreferensi dari foto-foto terpilih; foto tanpa georef yang sah dilaporkan.
    opt["coord"] = "georef" (bawaan, di bidang foto) atau "topo" (tempel ke DTM, opsional)."""
    ks = {k["key"]: k for k in kinds(s)}
    items, skipped = [], []
    for pid in ids or [p["id"] for p in photos(s)]:
        r = photo(s, pid)
        sol = georef_solve(r.get("georef"), r["w"], r["h"], plane_kind(r))
        if not sol or not sol.get("ok"):
            skipped.append(f"{r.get('title') or r['name']}: {(sol or {}).get('msg') or 'belum digeoreferensi'}")
            continue
        ctx = surface_ctx(s, r, sol, opt)
        for w_ in ctx["warn"]:
            skipped.append(f"{r.get('title') or r['name']}: {w_}")
        for f in features(s, pid):
            if f["kind"] in NO_EXPORT or (f.get("attrs") or {}).get("_draft"):
                continue  # garis skala & usulan yang belum diterima tidak ikut
            k = ks.get(f["kind"]) or {"name": f["kind"], "string": 50, "color": "#7a5aa6"}
            xyz = surface_xyz(ctx, f["pts"], f["shape"] == "poly", dense=f["shape"] != "point")[0]
            base = {"photo": r.get("title") or r["name"], "kind": f["kind"], "kname": k["name"], "string": int(k["string"]),
                    "color": k["color"], "shape": f["shape"], "name": f.get("name") or "", "attrs": f["attrs"], "xyz": xyz, "fid": f["id"]}
            sm = samples_of(f["attrs"])
            iv = [x for x in sm if x.get("from") is not None]
            if f["shape"] == "line" and iv:
                # satu segmen per interval sampel (dari-ke diukur sepanjang garis 3D dari ujung awal)
                for x in iv:
                    seg = chain_slice(xyz, x["from"], x["to"])
                    if len(seg) >= 2:
                        items.append(dict(base, xyz=seg, sample=x))
            else:
                items.append(dict(base, sample=sm[0] if sm else None))
    return items, skipped


def to_str(items: list[dict], name: str = "singkapan") -> bytes:
    """Surpac STR teks: string, Y (northing), X (easting), Z, D1 jenis, D2 nama, D3 foto, D4.. kadar."""
    L = [f"{_clean_txt(name) or 'singkapan'},{time.strftime('%d-%b-%y')},DB-Ex singkapan,", "0, 0.000, 0.000, 0.000,"]
    for it in sorted(items, key=lambda x: x["string"]):
        pts = it["xyz"] + ([it["xyz"][0]] if it["shape"] == "poly" else [])
        sm = it.get("sample") or {}
        d = [_clean_txt(it["kname"]), _clean_txt(sm.get("id") or it["name"]), _clean_txt(it["photo"])]
        if sm.get("from") is not None:
            d.append(f"{sm['from']:g}-{sm['to']:g}m")
        if it["attrs"].get("strike") is not None:
            d.append(f"N{it['attrs']['strike']:03.0f}/{it['attrs'].get('dip', 0):.0f}")
        for k, v in (sm.get("grades") or {}).items():
            d.append(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}")
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
        lab = (it.get("sample") or {}).get("id") or it["name"]
        if lab:
            x, y, z = it["xyz"][len(it["xyz"]) // 2]
            o += ["0", "TEXT", "8", L, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", f"{z:.3f}", "40", "0.3", "1", _clean_txt(lab)]
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
    coord: str = "georef"  # bawaan: koordinat georef di bidang foto; "topo" = tempel ke DTM (opsional)
    topo_id: Optional[int] = None
    depth: bool = False


def _opt(b) -> dict:
    return {"coord": b.coord, "topo_id": b.topo_id, "depth": b.depth}


@router.post("/georef")
def api_georef(b: GeoBody) -> dict:
    return {"ok": True, **save_georef(store(b.folder), b.id, b.points, b.kind, b.by)}


@router.post("/georef/info")
def api_georef_info(b: PidBody) -> dict:
    return {"ok": True, **georef_info(store(b.folder), b.id)}


@router.post("/export/check")
def api_export_check(b: ExpBody) -> dict:
    items, skipped = export_items(store(b.folder), b.ids, _opt(b))
    return {"ok": True, "n": len(items), "skipped": skipped}


@router.post("/export")
def api_export(b: ExpBody):
    from fastapi.responses import Response
    items, skipped = export_items(store(b.folder), b.ids, _opt(b))
    if not items:
        raise ValueError("Tidak ada fitur tergeoreferensi untuk diekspor." + (" " + "; ".join(skipped) if skipped else ""))
    if b.fmt == "dxf":
        return Response(to_dxf(items), media_type="application/dxf")
    return Response(to_str(items, b.name), media_type="text/plain")


def chain_slice(xyz: list, a: float, b: float) -> list[list[float]]:
    """Potongan polyline 3D dari jarak a sampai b (meter, diukur dari titik pertama)."""
    P = [np.array(p, dtype=float) for p in xyz]
    L = [float(np.linalg.norm(P[i + 1] - P[i])) for i in range(len(P) - 1)]
    tot = sum(L)
    a, b = max(0.0, min(a, tot)), max(0.0, min(b, tot))
    if b - a < 1e-6:
        return []

    def at(c: float) -> np.ndarray:
        acc = 0.0
        for i, l in enumerate(L):
            if acc + l >= c - 1e-9 and l > 0:
                return P[i] + (P[i + 1] - P[i]) * ((c - acc) / l)
            acc += l
        return P[-1]
    out = [at(a)]
    acc = 0.0
    for i, l in enumerate(L):
        acc += l
        if a < acc < b:
            out.append(P[i + 1])
    out.append(at(b))
    return [[round(float(v), 3) for v in p] for p in out]


def samples_csv(s: Store, ids: list[int], opt: Optional[dict] = None) -> bytes:
    """Tabel sampel semua fitur (foto terpilih / semua): ID, dari, ke, panjang, koordinat awal-akhir (bila georef), kadar,
    plus baris komposit per garis berinterval."""
    import csv
    import io
    els = [e["key"] for e in elements(s)]
    rows = []
    extra: list[str] = []
    for pid in ids or [p["id"] for p in photos(s)]:
        r = photo(s, pid)
        sol = georef_solve(r.get("georef"), r["w"], r["h"], plane_kind(r))
        ok = bool(sol and sol.get("ok"))
        ctx = surface_ctx(s, r, sol, opt) if ok else None
        ks = {k["key"]: k for k in kinds(s)}
        for f in features(s, pid):
            if (f.get("attrs") or {}).get(DRAFT):
                continue
            sm = samples_of(f["attrs"])
            if not sm:
                continue
            xyz = surface_xyz(ctx, f["pts"], f["shape"] == "poly")[0] if ok else None
            kname = (ks.get(f["kind"]) or {}).get("name", f["kind"])
            for x in sm:
                for k in x["grades"]:
                    if k not in els and k not in extra:
                        extra.append(k)
                c0 = c1 = None
                if xyz and f["shape"] == "line" and x.get("from") is not None:
                    seg = chain_slice(xyz, x["from"], x["to"])
                    if seg:
                        c0, c1 = seg[0], seg[-1]
                rows.append((r.get("title") or r["name"], kname, f.get("name") or "", x, c0, c1))
            cp = composite(sm)
            if cp and len([x for x in sm if x.get("from") is not None]) > 1:
                rows.append((r.get("title") or r["name"], kname, f.get("name") or "",
                             {"id": "KOMPOSIT", "from": cp["from"], "to": cp["to"], "grades": cp["grades"], "_len": cp["length"]}, None, None))
    keys = els + extra
    b = io.StringIO()
    w = csv.writer(b)
    w.writerow(["Foto", "Jenis fitur", "Nama fitur", "Sample ID", "Dari (m)", "Ke (m)", "Panjang (m)", "E awal", "N awal", "RL awal",
                "E akhir", "N akhir", "RL akhir"] + keys)

    def num(v):
        return "" if v is None else (f"{v:.4g}" if isinstance(v, float) else str(v))
    for foto, kname, nm, x, c0, c1 in rows:
        ln = x.get("_len", (x["to"] - x["from"]) if x.get("from") is not None else None)
        w.writerow([foto, kname, nm, x.get("id") or "", num(x.get("from")), num(x.get("to")), num(ln)]
                   + ([f"{v:.3f}" for v in c0] if c0 else ["", "", ""]) + ([f"{v:.3f}" for v in c1] if c1 else ["", "", ""])
                   + [num(x["grades"].get(k)) for k in keys])
    if not rows:
        raise ValueError("Belum ada sampel / kadar yang diisi di fitur mana pun.")
    return ("﻿" + b.getvalue()).encode("utf-8")


class ElemBody(FBody):
    elements: list[dict[str, Any]]


@router.post("/elements")
def api_elements(b: ElemBody) -> dict:
    return {"ok": True, "elements": save_elements(store(b.folder), b.elements, b.by)}


@router.post("/export/samples")
def api_export_samples(b: ExpBody):
    from fastapi.responses import Response
    return Response(samples_csv(store(b.folder), b.ids, _opt(b)), media_type="text/csv")


# ---------------------------------------------------------------- channel / trenching -> database bor (Collar, Survey, Assay, Geologi)
# Satu garis Channel sampel (atau garis berinterval) = satu "lubang". Collar = ujung KIRI garis di foto, EOH = ujung kanan.
# Dip = 0 (mutlak, mendatar); azimuth = arah tiap segmen garis dari kiri ke kanan (koordinat georef). Kedalaman = jarak
# sepanjang garis 3D (sama dengan dari-ke sampel yang diukur pita dari ujung kiri).
GEO_COLS = [("zona_lito", "LITHOLOGY"), ("zona_alt", "ALTERATION"), ("zona_oks", "OXIDATION"), ("zona_vein", "VEIN"), ("breksi", "BRECCIA")]
STRUCT_KINDS = ("sesar", "kekar", "vein", "kontak_lito", "kontak_alt")
DL_MODES = ("half", "neg", "text")


def _seg_hits(a: tuple, b: tuple, P: list) -> list[float]:
    """Parameter t (0..1) perpotongan segmen a-b dengan sisi-sisi polyline / poligon P (koordinat piksel)."""
    out = []
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    for (cx, cy), (ex, ey) in zip(P, P[1:]):
        fx, fy = ex - cx, ey - cy
        den = dx * fy - dy * fx
        if abs(den) < 1e-12:
            continue
        t = ((cx - ax) * fy - (cy - ay) * fx) / den
        u = ((cx - ax) * dy - (cy - ay) * dx) / den
        if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
            out.append(min(1.0, max(0.0, t)))
    return out


def _inside(pt: tuple, poly: list) -> bool:
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _dl(v: Any, mode: str) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return f"{v:g}"
    t = str(v)
    if mode == "text" or not t.startswith("<"):
        return t[1:] if t.startswith(">") and mode != "text" else t
    x = float(t[1:])
    return f"{x / 2:g}" if mode == "half" else f"{-x:g}"


def drillhole_tables(s: Store, ids: list[int], dl_mode: str = "half", opt: Optional[dict] = None) -> dict:
    import csv
    import io
    if dl_mode not in DL_MODES:
        raise ValueError("Pilihan nilai di bawah deteksi tidak dikenal.")
    els = elements(s)
    ekeys = [e["key"] for e in els]
    units = {e["key"]: e["unit"] for e in els}
    ks = {k["key"]: k for k in kinds(s)}
    collar, survey, assay, geol, skipped, used = [], [], [], [], [], set()
    extra: list[str] = []
    for pid in ids or [p["id"] for p in photos(s)]:
        r = photo(s, pid)
        feats = [f for f in features(s, pid) if not (f.get("attrs") or {}).get(DRAFT)]
        holes = [f for f in feats if f["shape"] == "line" and (f["kind"] == "channel" or any(x.get("from") is not None for x in samples_of(f["attrs"])))]
        if not holes:
            continue
        title = r.get("title") or r["name"]
        sol = georef_solve(r.get("georef"), r["w"], r["h"], plane_kind(r))
        if not sol or not sol.get("ok"):
            skipped.append(f"{title}: {len(holes)} channel dilewati — {(sol or {}).get('msg') or 'foto belum digeoreferensi'}")
            continue
        W, H = r["w"], r["h"]
        desc = r.get("desc") or {}
        ctx = surface_ctx(s, r, sol, opt)
        for w_ in ctx["warn"]:
            skipped.append(f"{title}: {w_}")
        for n, f in enumerate(holes, 1):
            hid = re.sub(r"[^\w.-]+", "_", (f.get("name") or f"{title}_CH{n}").strip())[:40] or f"CH{f['id']}"
            base, k = hid, 2
            while hid in used:
                hid, k = f"{base}_{k}", k + 1
            used.add(hid)
            xyz_l, _src, U = surface_xyz(ctx, f["pts"])
            xyz = np.array(xyz_l)
            seg = [float(np.linalg.norm(xyz[i + 1] - xyz[i])) for i in range(len(xyz) - 1)]
            cum = [0.0]
            for L in seg:
                cum.append(cum[-1] + L)
            sm = samples_of(f["attrs"])
            iv = [x for x in sm if x.get("from") is not None]
            eoh = max([cum[-1]] + [x["to"] for x in iv])
            azs = []
            for i in range(len(seg)):
                d = xyz[i + 1] - xyz[i]
                azs.append((math.degrees(math.atan2(d[0], d[1])) + 360) % 360 if math.hypot(d[0], d[1]) > 1e-6 else (azs[-1] if azs else 0.0))
            collar.append([hid, f"{xyz[0][0]:.3f}", f"{xyz[0][1]:.3f}", f"{xyz[0][2]:.3f}", f"{eoh:.2f}", f"{azs[0]:.1f}", "0",
                           "CHANNEL", title, r.get("taken") or "", r.get("location") or "",
                           "GEOREF" if ctx["mode"] != "topo" else "TOPO:" + str((ctx.get("topo") or {}).get("name") or "-")])
            for i, a in enumerate(azs):
                if i == 0 or abs(((a - azs[i - 1]) + 180) % 360 - 180) > 0.05:
                    survey.append([hid, f"{cum[i]:.2f}", f"{a:.1f}", "0"])
            for x in (iv or sm):
                for kk in x.get("grades") or {}:
                    if kk not in ekeys and kk not in extra:
                        extra.append(kk)
            for x in iv:
                assay.append((hid, x, f))
            # ---- geologi: titik potong garis dengan zona / label zona / struktur, lalu isi tiap sub-interval
            Ppx = [(u * W, v * H) for u, v in U]

            def chain(i: int, t: float) -> float:
                return cum[i] + seg[i] * t
            zones = [g for g in feats if g["shape"] == "poly" and g["kind"] in dict(GEO_COLS)]
            cuts = {0.0, cum[-1]}
            for g in zones:
                Q = [(u * W, v * H) for u, v in g["pts"]]
                Q = Q + [Q[0]]
                for i in range(len(Ppx) - 1):
                    for t in _seg_hits(Ppx[i], Ppx[i + 1], Q):
                        cuts.add(round(chain(i, t), 4))
            # label zona (rentang): ujung-ujungnya diproyeksikan ke garis channel
            spans = []
            for g in feats:
                if g["kind"] != "label_zona" or len(g["pts"]) < 2 or not g.get("name"):
                    continue
                ends = []
                for u, v in (g["pts"][0], g["pts"][-1]):
                    best = None
                    for i in range(len(Ppx) - 1):
                        (ax, ay), (bx, by) = Ppx[i], Ppx[i + 1]
                        dx, dy = bx - ax, by - ay
                        L2 = dx * dx + dy * dy or 1e-12
                        t = max(0.0, min(1.0, ((u * W - ax) * dx + (v * H - ay) * dy) / L2))
                        dd = (ax + t * dx - u * W) ** 2 + (ay + t * dy - v * H) ** 2
                        if best is None or dd < best[0]:
                            best = (dd, chain(i, t))
                    ends.append(best[1])
                a0, a1 = sorted(ends)
                if a1 - a0 > 1e-3:
                    spans.append((a0, a1, g["name"]))
                    cuts.update((round(a0, 4), round(a1, 4)))
            structs = []
            for g in feats:
                if g["shape"] != "line" or g["kind"] not in STRUCT_KINDS or g["id"] == f["id"]:
                    continue
                Q = [(u * W, v * H) for u, v in g["pts"]]
                for i in range(len(Ppx) - 1):
                    for t in _seg_hits(Ppx[i], Ppx[i + 1], Q):
                        nm = (ks.get(g["kind"]) or {}).get("name", g["kind"]) + (f" {g['name']}" if g.get("name") else "")
                        structs.append((chain(i, t), nm))
            cuts = sorted(c for c in cuts if 0 <= c <= cum[-1] + 1e-6)
            rows = []
            for c0, c1 in zip(cuts, cuts[1:]):
                if c1 - c0 < 1e-3:
                    continue
                cm = (c0 + c1) / 2
                i = next((j for j in range(len(seg)) if cum[j + 1] >= cm - 1e-9), len(seg) - 1)
                t = (cm - cum[i]) / seg[i] if seg[i] > 0 else 0
                pm = (Ppx[i][0] + (Ppx[i + 1][0] - Ppx[i][0]) * t, Ppx[i][1] + (Ppx[i + 1][1] - Ppx[i][1]) * t)
                vals = {}
                for kind_, col in GEO_COLS:
                    hit = [g for g in zones if g["kind"] == kind_ and _inside(pm, [(u * W, v * H) for u, v in g["pts"]])]
                    vals[col] = " / ".join(g.get("name") or (ks.get(kind_) or {}).get("name", kind_) for g in hit)
                vals["ZONE"] = " / ".join(nm for a0, a1, nm in spans if a0 - 1e-6 <= cm <= a1 + 1e-6)
                vals["STRUCTURE"] = "; ".join(nm for c, nm in structs if c0 - 1e-6 <= c < c1 - 1e-6 or (c1 >= cum[-1] - 1e-6 and abs(c - c1) < 1e-6))
                rows.append([c0, c1, vals])
            # isi kolom yang tidak punya zona sama sekali dari deskripsi foto (satu nilai untuk seluruh lubang)
            for col, dk in (("LITHOLOGY", "lithology"), ("ALTERATION", "alteration"), ("OXIDATION", "oxidation"), ("VEIN", "veins")):
                if not any(rw[2][col] for rw in rows) and desc.get(dk):
                    for rw in rows:
                        rw[2][col] = desc[dk]
            # gabungkan sub-interval berurutan yang isinya sama
            merged = []
            for rw in rows:
                if merged and merged[-1][2] == rw[2] and abs(merged[-1][1] - rw[0]) < 1e-6:
                    merged[-1][1] = rw[1]
                else:
                    merged.append(rw)
            for c0, c1, vals in merged:
                geol.append([hid, f"{c0:.2f}", f"{c1:.2f}"] + [vals[c] for _k, c in GEO_COLS] + [vals["ZONE"], vals["STRUCTURE"],
                                                                                                desc.get("weathering") or ""])
    if not collar:
        raise ValueError("Tidak ada garis Channel sampel tergeoreferensi untuk diekspor." + (" " + "; ".join(skipped) if skipped else ""))
    keys = ekeys + extra

    def out(head: list, rows: list) -> str:
        b = io.StringIO()
        w = csv.writer(b, lineterminator="\r\n")
        w.writerow(head)
        w.writerows(rows)
        return b.getvalue()
    arows = [[hid, f"{x['from']:.2f}", f"{x['to']:.2f}", x.get("id") or ""] + [_dl((x.get("grades") or {}).get(k2), dl_mode) for k2 in keys]
             for hid, x, _f in assay]
    return {
        "collar": out(["HOLE_ID", "EAST", "NORTH", "RL", "MAX_DEPTH", "AZIMUTH", "DIP", "TYPE", "PHOTO", "DATE", "LOCATION", "COORD_SRC"], collar),
        "survey": out(["HOLE_ID", "DEPTH", "AZIMUTH", "DIP"], survey),
        "assay": out(["HOLE_ID", "FROM", "TO", "SAMPLE_ID"] + [f"{k2}_{units.get(k2, '').replace('/', '').replace('%', 'pct') or 'val'}" for k2 in keys], arows),
        "geology": out(["HOLE_ID", "FROM", "TO"] + [c for _k, c in GEO_COLS] + ["ZONE", "STRUCTURE", "WEATHERING"], geol),
        "holes": len(collar), "samples": len(arows), "geology_rows": len(geol), "skipped": skipped}


class DhBody(FBody):
    ids: list[int] = []
    dl: str = "half"
    coord: str = "georef"
    topo_id: Optional[int] = None
    depth: bool = False


@router.post("/export/drillhole")
def api_export_drillhole(b: DhBody) -> dict:
    return {"ok": True, **drillhole_tables(store(b.folder), b.ids, b.dl, _opt(b))}


# ================================================================ delineasi otomatis (usulan / draf)
# Usulan disimpan sebagai fitur biasa dengan attrs["_draft"] = sumbernya ("warna" atau "ai:<model>").
# Draf digambar putus-putus, tidak ikut ekspor STR / DXF / infografis sampai diterima geologist.
DRAFT = "_draft"
AUTO_SKIP = {"skala", "label", "channel", "orientasi", "label_zona"}


def is_draft(f: dict) -> bool:
    return bool((f.get("attrs") or {}).get(DRAFT))


def _load_rgb(f: Path, long_side: int) -> np.ndarray:
    from PIL import Image, ImageFilter, ImageOps
    with Image.open(f) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        k = long_side / max(im.size)
        im = im.resize((max(8, round(im.width * k)), max(8, round(im.height * k))), Image.BILINEAR)
        im = im.filter(ImageFilter.GaussianBlur(1.6))
        return np.asarray(im, dtype=np.float64) / 255.0


def _lab(rgb: np.ndarray) -> np.ndarray:
    c = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def _kmeans(X: np.ndarray, k: int, it: int = 20) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7)
    sample = X[rng.choice(len(X), min(len(X), 6000), replace=False)]
    C = [sample[0]]
    for _ in range(1, k):  # k-means++ deterministik
        d = np.min(((sample[:, None, :] - np.array(C)[None]) ** 2).sum(-1), axis=1)
        C.append(sample[int(np.argmax(d))] if d.sum() == 0 else sample[rng.choice(len(sample), p=d / d.sum())])
    C = np.array(C)
    for _ in range(it):
        lab = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(-1), axis=1)
        newC = np.array([X[lab == j].mean(0) if np.any(lab == j) else C[j] for j in range(k)])
        if np.allclose(newC, C, atol=1e-3):
            break
        C = newC
    return np.argmin(((X[:, None, :] - C[None]) ** 2).sum(-1), axis=1), C


def _majority(L: np.ndarray, k: int, r: int) -> np.ndarray:
    """Filter mayoritas (jendela (2r+1)^2) dengan integral image per kelas."""
    H, W = L.shape
    best = np.full((H, W), -1.0)
    out = L.copy()
    for j in range(k):
        m = np.pad((L == j).astype(np.float64), ((r + 1, r), (r + 1, r)), mode="edge")
        S = m.cumsum(0).cumsum(1)
        cnt = S[2 * r + 1:, 2 * r + 1:] - S[:-2 * r - 1, 2 * r + 1:] - S[2 * r + 1:, :-2 * r - 1] + S[:-2 * r - 1, :-2 * r - 1]
        upd = cnt > best
        best[upd], out[upd] = cnt[upd], j
    return out


def _components(L: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Label komponen terhubung-4 (union-find per baris, cukup cepat untuk ~250 x 250)."""
    H, W = L.shape
    comp = -np.ones((H, W), dtype=np.int64)
    sizes: list[int] = []
    for y in range(H):
        for x in range(W):
            if comp[y, x] >= 0:
                continue
            cid, v = len(sizes), L[y, x]
            stack, n = [(y, x)], 0
            comp[y, x] = cid
            while stack:
                cy, cx = stack.pop()
                n += 1
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < H and 0 <= nx < W and comp[ny, nx] < 0 and L[ny, nx] == v:
                        comp[ny, nx] = cid
                        stack.append((ny, nx))
            sizes.append(n)
    return comp, sizes


def _trace(mask: np.ndarray) -> list[tuple[float, float]]:
    """Batas luar region terhubung-4, ditelusuri di grid sudut piksel dengan region di sisi kanan (searah jarum jam
    di layar). Hasil dalam koordinat sudut piksel (0..W, 0..H)."""
    H, W = mask.shape

    def inside(x: int, y: int) -> bool:
        return 0 <= x < W and 0 <= y < H and bool(mask[y, x])

    # piksel (kanan, kiri) dari tepi yang berangkat dari sudut (x, y) ke arah d (0 kanan, 1 bawah, 2 kiri, 3 atas)
    def sides(x: int, y: int, d: int) -> tuple[bool, bool]:
        if d == 0:
            return inside(x, y), inside(x, y - 1)
        if d == 1:
            return inside(x - 1, y), inside(x, y)
        if d == 2:
            return inside(x - 1, y - 1), inside(x - 1, y)
        return inside(x, y - 1), inside(x - 1, y - 1)

    D = ((1, 0), (0, 1), (-1, 0), (0, -1))
    ys, xs = np.nonzero(mask)
    i = np.lexsort((xs, ys))[0]
    start = (int(xs[i]), int(ys[i]), 0)
    x, y, d = start
    pts = []
    for _ in range(4 * (H + 1) * (W + 1)):
        pts.append((x, y))
        x, y = x + D[d][0], y + D[d][1]
        for nd in ((d + 1) % 4, d, (d + 3) % 4):  # belok kanan dulu: region diagonal tidak tergabung
            r, l_ = sides(x, y, nd)
            if r and not l_:
                d = nd
                break
        if (x, y, d) == start:
            break
    # buang titik kolinear
    out = [p for k, p in enumerate(pts) if not ((pts[k - 1][0] == p[0] == pts[(k + 1) % len(pts)][0]) or
                                                (pts[k - 1][1] == p[1] == pts[(k + 1) % len(pts)][1]))]
    return out or pts


def _dp(P: list, eps: float) -> list:
    """Douglas-Peucker untuk poligon tertutup."""
    if len(P) < 4:
        return P
    A = np.array(P, dtype=float)
    far = int(np.argmax(((A - A[0]) ** 2).sum(1)))

    def rec(a: np.ndarray) -> list:
        if len(a) < 3:
            return [tuple(a[0])]
        s, e = a[0], a[-1]
        d = e - s
        n = np.hypot(*d)
        dist = np.abs(d[0] * (a[:, 1] - s[1]) - d[1] * (a[:, 0] - s[0])) / n if n > 1e-9 else np.hypot(*(a - s).T)
        i = int(np.argmax(dist))
        if dist[i] <= eps:
            return [tuple(s)]
        return rec(a[:i + 1]) + rec(a[i:])
    out = rec(A[:far + 1]) + rec(np.vstack([A[far:], A[:1]]))
    return out


def _color_name(lab: np.ndarray) -> tuple[str, bool]:
    L, a, b = (float(x) for x in lab)
    C = math.hypot(a, b)
    h = (math.degrees(math.atan2(b, a)) + 360) % 360
    tone = "gelap" if L < 35 else ("terang" if L > 70 else "")
    if C < 8:
        base = "abu-abu"
    elif h < 45:
        base = "merah kecoklatan"
    elif h < 75:
        base = "coklat kekuningan"
    elif h < 110:
        base = "kuning"
    elif h < 200:
        base = "kehijauan"
    else:
        base = "kebiruan"
    oxid = C >= 10 and 15 <= h <= 95
    return (f"{base} {tone}".strip(), oxid)


def propose_color(s: Store, pid: int, k: int = 3, min_pct: float = 2.0, by: str = "") -> dict:
    """Usulan zona dari warna: k-means di ruang Lab (terang diberi bobot rendah agar bayangan tidak jadi zona),
    dihaluskan, region kecil digabung, batas tiap region jadi poligon. Zona merah-kuning-coklat (oksida / gossan)
    diberi jenis zona_oks, lainnya zona_lito."""
    r = photo(s, pid)
    f = s.photos / r["file"]
    if not f.exists():
        raise ValueError("File foto singkapan hilang dari folder proyek.")
    k = max(2, min(6, int(k)))
    rgb = _load_rgb(f, 220)
    H, W, _ = rgb.shape
    lab = _lab(rgb)
    X = (lab * np.array([0.45, 1.0, 1.0])).reshape(-1, 3)
    lbl, C = _kmeans(X, k)
    L = lbl.reshape(H, W)
    for rr in (3, 3, 2):
        L = _majority(L, k, rr)
    min_px = max(12, int(H * W * min_pct / 100))
    for _ in range(4):  # gabungkan region kecil ke tetangga dominan
        comp, sizes = _components(L)
        small = [c for c, n in enumerate(sizes) if n < min_px]
        if not small:
            break
        for c in small:
            mk = comp == c
            ring = np.zeros_like(mk)
            ring[1:] |= mk[:-1]
            ring[:-1] |= mk[1:]
            ring[:, 1:] |= mk[:, :-1]
            ring[:, :-1] |= mk[:, 1:]
            ring &= ~mk
            if ring.any():
                L[mk] = np.bincount(L[ring], minlength=k).argmax()
    comp, sizes = _components(L)
    meanlab = {j: lab[L == j].mean(0) for j in range(k) if np.any(L == j)}
    regions = sorted(((n, c) for c, n in enumerate(sizes) if n >= min_px), reverse=True)[:12]
    ks = {x["key"] for x in kinds(s)}
    clear_drafts(s, pid, "warna")
    made = []
    letters = "ABCDEFGHIJKL"
    i = -1
    for n, c in regions:
        mk = comp == c
        if n > 0.97 * H * W:
            continue  # seluruh foto satu zona: tidak ada batas
        poly = _dp(_trace(mk), 2.0)
        if len(poly) < 3:
            continue
        A = np.array(poly, dtype=float)
        if abs(np.dot(A[:, 0], np.roll(A[:, 1], -1)) - np.dot(A[:, 1], np.roll(A[:, 0], -1))) / 2 > 0.9 * H * W:
            continue  # zona latar (berlubang): batasnya sudah diwakili zona-zona di dalamnya
        pts = [[min(1.0, max(0.0, x / W)), min(1.0, max(0.0, y / H))] for x, y in poly]
        j = int(L[mk][0])
        nm, oxid = _color_name(meanlab[j])
        kind = "zona_oks" if oxid and "zona_oks" in ks else "zona_lito"
        try:
            i += 1
            res = save_feature(s, pid, None, {"kind": kind, "pts": pts, "name": f"Usulan zona {letters[i]} ({nm})", "src": "auto:warna",
                                              "attrs": {DRAFT: "warna", "_pct": round(100 * n / (H * W), 1)}}, by or "auto")
            made.append(res["id"])
        except ValueError:
            continue
    return {"made": made, "features": features(s, pid), "k": k}


def clear_drafts(s: Store, pid: int, source: Optional[str] = None) -> int:
    n = 0
    with s.lock, s.conn() as c:
        for row in c.execute("SELECT id, attrs FROM features WHERE photo_id=?", (pid,)).fetchall():
            try:
                a = json.loads(row["attrs"] or "{}")
            except ValueError:
                continue
            src = a.get(DRAFT)
            if src and (source is None or src == source or (source == "ai" and str(src).startswith("ai:"))):
                c.execute("DELETE FROM features WHERE id=?", (row["id"],))
                n += 1
    return n


def accept_drafts(s: Store, pid: int, ids: Optional[list[int]], by: str) -> list[dict]:
    """Terima usulan (semua atau id terpilih): tanda draf dibuang, fitur menjadi fitur biasa."""
    for f in features(s, pid):
        if is_draft(f) and (not ids or f["id"] in ids):
            a = {k: v for k, v in f["attrs"].items() if k not in (DRAFT, "_pct", "_conf")}
            save_feature(s, pid, f["id"], {"kind": f["kind"], "pts": f["pts"], "name": f["name"], "attrs": a}, by)
    return features(s, pid)


def reject_drafts(s: Store, pid: int, ids: Optional[list[int]], by: str) -> list[dict]:
    if not ids:
        n = clear_drafts(s, pid)
        with s.lock, s.conn() as c:
            c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, "usulan dibuang", f"{n} fitur", None, "hapus", by, core_io.now()))
        return features(s, pid)
    for f in features(s, pid):
        if f["id"] in ids and is_draft(f):
            delete_feature(s, f["id"], by)
    return features(s, pid)


# ---------------------------------------------------------------- usulan AI vision (Ollama)
def delin_schema(keys: list[str]) -> dict:
    return {"type": "object", "required": ["features"], "properties": {
        "features": {"type": "array", "items": {"type": "object", "required": ["kind", "points"], "properties": {
            "kind": {"type": "string", "enum": keys}, "name": {"type": "string"},
            "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
            "confidence": {"type": "string", "enum": ["tinggi", "sedang", "rendah"]}}}},
        "notes": {"type": "string"}}}


def delin_prompt(ks: list[dict], extra: str = "", desc: Optional[dict] = None) -> str:
    lst = "\n".join(f"- {k['key']}: {k['name']} ({ {'line': 'garis', 'poly': 'poligon'}[k['shape']] })" for k in ks)
    d = "; ".join(f"{k}: {v}" for k, v in (desc or {}).items() if v and k in ("photo_type", "lithology", "alteration", "oxidation", "veins", "structures", "zones"))
    return ("Anda geologist lapangan yang mendelineasi foto singkapan / dinding pit / trenching tambang emas epitermal.\n"
            "Gambarkan batas dan fitur geologi yang BENAR-BENAR terlihat di foto sebagai garis atau poligon.\n"
            f"Jenis fitur yang boleh dipakai (kind):\n{lst}\n"
            "Aturan:\n"
            "- Koordinat setiap titik [x, y] dalam skala 0-1000 relatif terhadap lebar dan tinggi foto; (0,0) = kiri atas, (1000,1000) = kanan bawah.\n"
            "- Garis: 2-12 titik mengikuti jejak fitur (kontak, sesar, kekar, vein) dari ujung ke ujung.\n"
            "- Poligon: 4-20 titik mengelilingi zona (zona oksida, alterasi, litologi, zona vein, breksi); zona yang menyentuh tepi foto memakai titik di tepi (0 atau 1000).\n"
            "- Maksimum 15 fitur; utamakan fitur terbesar dan paling jelas. Jangan menebak fitur yang tidak terlihat; daftar kosong boleh.\n"
            "- name: nama singkat (mis. 'Vein kuarsa-oksida', 'Zona oksida / gossan'); confidence: tinggi / sedang / rendah.\n"
            + (f"Deskripsi foto yang sudah ada: {d}\n" if d else "")
            + (f"Catatan tambahan: {extra.strip()}\n" if extra and extra.strip() else "")
            + "Jawab hanya JSON sesuai skema.")


def apply_delin(s: Store, pid: int, res: dict, model: str, size: tuple[int, int], by: str = "") -> dict:
    """Simpan jawaban AI sebagai draf. Koordinat 0-1000; bila model memakai piksel gambar (Qwen2.5-VL), dideteksi dari nilai > 1000."""
    ks = {k["key"]: k for k in kinds(s) if k["key"] not in AUTO_SKIP and k["shape"] != "point"}
    items = (res or {}).get("features") or []
    allv = [float(v) for it in items for p in (it.get("points") or []) if isinstance(p, (list, tuple)) and len(p) >= 2
            for v in p[:2] if isinstance(v, (int, float))]
    px = bool(allv) and max(allv) > 1000.5
    sw, sh = (size[0], size[1]) if px else (1000.0, 1000.0)
    clear_drafts(s, pid, "ai")
    made, skipped = [], 0
    for it in items[:30]:
        kind = it.get("kind")
        if kind not in ks:
            skipped += 1
            continue
        try:
            pts = [[float(p[0]) / sw, float(p[1]) / sh] for p in it.get("points") or [] if len(p) >= 2]
        except (TypeError, ValueError):
            skipped += 1
            continue
        try:
            j = save_feature(s, pid, None, {"kind": kind, "pts": pts, "name": (it.get("name") or "").strip()[:80] or None, "src": "ai:" + model,
                                            "attrs": {DRAFT: "ai:" + model, "_conf": it.get("confidence") or ""}}, by or "AI")
            made.append(j["id"])
        except ValueError:
            skipped += 1
    with s.lock, s.conn() as c:
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                  (pid, "usulan delineasi AI", None, f"{len(made)} fitur" + (f", {skipped} dilewati" if skipped else "")
                   + (f" · {str(res.get('notes'))[:200]}" if res.get("notes") else ""), "ai:" + model, by or "AI", core_io.now()))
    return {"made": made, "skipped": skipped, "features": features(s, pid), "notes": res.get("notes") or ""}


def ai_delineate(s: Store, pid: int, host: str, model: str, extra: str = "", max_px: int = 1600, by: str = "", timeout: float = 900) -> dict:
    r = photo(s, pid)
    f = s.photos / r["file"]
    if not f.exists():
        raise ValueError("File foto singkapan hilang dari folder proyek.")
    img = core_io.resized_jpeg(f, max_px)
    from io import BytesIO

    from PIL import Image
    with Image.open(BytesIO(img)) as im:
        size = im.size
    ks = [k for k in kinds(s) if k["key"] not in AUTO_SKIP and k["shape"] != "point"]
    body = {"model": model, "messages": [{"role": "user", "content": delin_prompt(ks, extra, r.get("desc")), "images": [base64.b64encode(img).decode()]}],
            "stream": False, "format": delin_schema([k["key"] for k in ks]), "options": {"temperature": 0, "num_ctx": 16384}, "keep_alive": "15m"}
    j = core_io._http((host or core_io.DEFAULT_HOST).rstrip("/") + "/api/chat", body, timeout=timeout)
    if j.get("error"):
        raise RuntimeError("Ollama: " + str(j["error"]))
    res = core_io._parse_json((j.get("message") or {}).get("content", ""))
    return apply_delin(s, pid, res, model, size, by)


class ColorBody(FBody):
    id: int
    k: int = 3
    min_pct: float = 2.0


class DraftBody(FBody):
    id: int
    ids: list[int] = []


class DelinBody(FBody):
    id: int
    host: str = ""
    model: str
    extra: str = ""
    max_px: int = 1600


@router.post("/auto/color")
def api_auto_color(b: ColorBody) -> dict:
    return {"ok": True, **propose_color(store(b.folder), b.id, b.k, b.min_pct, b.by)}


@router.post("/auto/ai")
def api_auto_ai(b: DelinBody) -> dict:
    return {"ok": True, **ai_delineate(store(b.folder), b.id, b.host, b.model, b.extra, b.max_px, b.by)}


@router.post("/auto/accept")
def api_auto_accept(b: DraftBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "features": accept_drafts(s, b.id, b.ids, b.by), "scale": scale_info(s, b.id)}


@router.post("/auto/reject")
def api_auto_reject(b: DraftBody) -> dict:
    s = store(b.folder)
    return {"ok": True, "features": reject_drafts(s, b.id, b.ids, b.by), "scale": scale_info(s, b.id)}


# ---------------------------------------------------------------- API topografi & visi (SAM / Depth Anything)
class TopoAddBody(FBody):
    paths: list[str]
    survey_date: str
    name: str = ""


class TopoIdBody(FBody):
    tid: int


class TopoCheckBody(FBody):
    id: int
    topo_id: Optional[int] = None
    depth: bool = False


class SamBody(FBody):
    id: int
    points: list[list[float]] = []
    level: int = 1


@router.post("/topo/list")
def api_topo_list(b: FBody) -> dict:
    from . import core_topo
    return {"ok": True, "topo": core_topo.topo_list(store(b.folder))}


@router.post("/topo/add")
def api_topo_add(b: TopoAddBody) -> dict:
    from . import core_topo
    s = store(b.folder)
    t = core_topo.topo_add(s, b.paths, b.survey_date, b.name, b.by)
    return {"ok": True, "added": t, "topo": core_topo.topo_list(s)}


@router.post("/topo/delete")
def api_topo_delete(b: TopoIdBody) -> dict:
    from . import core_topo
    return {"ok": True, "topo": core_topo.topo_delete(store(b.folder), b.tid, b.by)}


@router.post("/topo/check")
def api_topo_check(b: TopoCheckBody) -> dict:
    return {"ok": True, **coord_report(store(b.folder), b.id, {"topo_id": b.topo_id, "depth": b.depth})}


@router.post("/vision/status")
def api_vision_status(b: FBody) -> dict:
    from . import core_vision
    return {"ok": True, **core_vision.status()}


@router.post("/sam/embed")
def api_sam_embed(b: PidBody) -> dict:
    from . import core_vision
    s = store(b.folder)
    r = photo(s, b.id)
    t0 = time.time()
    core_vision.sam_embed(s.photos / r["file"], f"{s.root}|{r['file']}")
    return {"ok": True, "secs": round(time.time() - t0, 2)}


@router.post("/sam/mask")
def api_sam_mask(b: SamBody) -> dict:
    """Mask SAM dari titik klik -> poligon ternormalisasi (belum disimpan)."""
    from . import core_vision
    s = store(b.folder)
    r = photo(s, b.id)
    if not b.points:
        raise ValueError("Klik minimal satu titik di dalam zona.")
    e = core_vision.sam_embed(s.photos / r["file"], f"{s.root}|{r['file']}")
    m, sc, areas = core_vision.sam_mask(e, [[float(u), float(v), int(l)] for u, v, l in b.points], b.level)
    poly = core_vision.mask_polygon(m)
    return {"ok": True, "poly": poly, "score": sc, "areas": areas, "area": float(m.mean())}


@router.post("/depth")
def api_depth(b: PidBody) -> dict:
    from . import core_vision
    s = store(b.folder)
    r = photo(s, b.id)
    t0 = time.time()
    d = core_vision.depth_map(s.photos / r["file"], s.root / "depth" / f"{r['id']}.npy")
    return {"ok": True, "shape": list(d.shape), "secs": round(time.time() - t0, 2)}
