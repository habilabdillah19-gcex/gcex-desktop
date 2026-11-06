"""DB-Ex: proyek foto core box, interpretasi AI lokal (Ollama), log geoteknik.

Semua berjalan di komputer sendiri (offline):
- Proyek = satu folder foto (boleh bersubfolder, mis. per lubang bor). Database SQLite disimpan di
  <folder>/_GCEx_Core/gcex_core.db sehingga geologist lain yang membuka folder yang sama melanjutkan
  pekerjaan yang sama. Bila folder tidak bisa ditulisi (mis. DVD / share hanya-baca), database disimpan
  di cache aplikasi dan hal itu dilaporkan.
- Foto tidak pernah dipindah / diubah. Path foto disimpan relatif terhadap folder proyek, jadi folder
  boleh dipindah ke drive lain.
- Thumbnail & pratinjau dibuat sekali lalu disimpan di cache (GCEX_CACHE/core_img).
- AI: model vision di Ollama (http://127.0.0.1:11434). Foto diperkecil dulu, dikirim satu per satu oleh
  satu thread latar belakang, hasilnya langsung ditulis ke database (aman bila aplikasi ditutup di tengah jalan).
- Isian yang sudah diedit / diverifikasi geologist TIDAK ditimpa oleh AI.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

log = logging.getLogger("gcex.core")
router = APIRouter(prefix="/core")

IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
PRJ_DIR = "_GCEx_Core"
DB_NAME = "gcex_core.db"
SCHEMA_VERSION = 1
DEFAULT_HOST = "http://127.0.0.1:11434"
RECOMMENDED_MODELS = ["qwen3-vl:8b", "qwen3-vl:4b", "qwen2.5vl:7b", "gemma3:12b", "llama3.2-vision:11b"]

# Kolom interpretasi (urutan = urutan di tabel & Excel). tipe: s = teks, n = angka
FIELDS: list[tuple[str, str, str]] = [
    ("hole_id", "s", "Hole ID"),
    ("box_no", "s", "Box No"),
    ("from_m", "n", "From (m)"),
    ("to_m", "n", "To (m)"),
    ("drill_start", "s", "Start Drill"),
    ("photo_date", "s", "Tanggal Foto"),
    ("lithology", "s", "Litologi"),
    ("color", "s", "Warna Batuan"),
    ("weathering", "s", "Tingkat Pelapukan"),
    ("oxidation", "s", "Tingkat Oksidasi"),
    ("alteration", "s", "Alterasi"),
    ("condition", "s", "Kondisi Foto"),
    ("recovery_pct", "n", "Core Recovery (%)"),
    ("rqd_pct", "n", "RQD (%)"),
    ("gsi", "s", "GSI"),
    ("rmr", "n", "RMR"),
    ("notes", "s", "Catatan Struktur / Alterasi"),
]
FIELD_TYPE = {k: t for k, t, _ in FIELDS}

WEATHERING = ["W1 (Fresh)", "W2 (Slightly Weathered)", "W3 (Moderately Weathered)", "W4 (Highly Weathered)",
              "W5 (Completely Weathered)", "W6 (Residual Soil)"]
OXIDATION = ["Unoxidized", "Slightly Oxidized", "Moderately Oxidized", "Strongly Oxidized", "Completely Oxidized"]


def cache_root() -> Path:
    p = Path(os.environ.get("GCEX_CACHE") or (Path.home() / ".gcex_cache"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def natural_key(s: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


# ---------------------------------------------------------------- nama file -> Hole / Box / kedalaman
_RX_BOX = re.compile(r"(?:^|[_\-\s.])(?:box|bx|kotak|b)[_\-\s.]?(\d{1,4})(?=$|[_\-\s.])", re.I)
_RX_NUM = re.compile(r"(?<![A-Za-z0-9.,])(\d{1,4}(?:[.,]\d{1,3})?)\s*(?:m(?![a-z]))?", re.I)
_RX_SEP = re.compile(r"^\s*(?:-|_|to|sd|s\.d\.?|~)\s*$", re.I)


def _depth_pair(s: str):
    """Pasangan angka 'a-b' terakhir yang masuk akal (a < b) sebagai From-To; angka yang menempel huruf (nomor lubang) dilewati."""
    nums = list(_RX_NUM.finditer(s))
    best = None
    for x, y in zip(nums, nums[1:]):
        if _RX_SEP.match(s[x.end():y.start()]):
            a, b = float(x.group(1).replace(",", ".")), float(y.group(1).replace(",", "."))
            if 0 <= a < b <= 3000 and b - a <= 50:
                best = (a, b, x.start(), y.end())
    return best
_RX_HOLE = re.compile(r"([A-Za-z]{1,6}[_\-]?\d{1,6}(?:[_\-]\d{1,6})*[A-Za-z]?)(?![A-Za-z0-9])")


def parse_filename(name: str) -> dict:
    """Tebak Hole ID, Box dan kedalaman dari nama file, mis. 'LTH-101_Box11_36.30-40.10.jpg'.
    Hanya mengisi yang yakin; sisanya dibiarkan kosong untuk AI / geologist."""
    stem = Path(name).stem
    out: dict[str, Any] = {}
    m = _RX_BOX.search(stem)
    rest = stem
    if m:
        out["box_no"] = str(int(m.group(1)))
        rest = stem[:m.start()] + " " + stem[m.end():]
    d = _depth_pair(rest)
    if d:
        out["from_m"], out["to_m"] = d[0], d[1]
        rest = rest[:d[2]] + " " + rest[d[3]:]
    h = _RX_HOLE.search(rest)
    if h and not re.fullmatch(r"(?i)(img|dsc|dscn|dcim|pxl|photo|foto|box|bx)[_\-]?\d+", h.group(1)):
        out["hole_id"] = h.group(1).upper()
    return out


# ---------------------------------------------------------------- proyek (SQLite)
class Project:
    def __init__(self, folder: Path, db: Path, local: bool):
        self.folder, self.db, self.local = folder, db, local
        self.lock = threading.RLock()

    @contextmanager
    def conn(self):
        """Koneksi singkat: commit bila berhasil (rollback bila galat) lalu SELALU ditutup, supaya file database
        tidak tetap terkunci (penting di Windows, OneDrive / drive jaringan, dan saat rekan membuka folder yang sama)."""
        c = sqlite3.connect(str(self.db), timeout=30)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()


_PROJECTS: dict[str, Project] = {}
_PLOCK = threading.Lock()

_DDL = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rel TEXT UNIQUE NOT NULL, name TEXT, size INTEGER, mtime REAL,
  status TEXT DEFAULT 'pending', missing INTEGER DEFAULT 0,
  ai_json TEXT, ai_model TEXT, ai_at TEXT, ai_secs REAL, ai_conf TEXT, error TEXT,
  edited TEXT DEFAULT '[]', from_name TEXT DEFAULT '[]', verified INTEGER DEFAULT 0, verified_by TEXT, verified_at TEXT,
  hole_id TEXT, box_no TEXT, from_m REAL, to_m REAL, drill_start TEXT, photo_date TEXT, lithology TEXT, color TEXT, weathering TEXT,
  oxidation TEXT, alteration TEXT, condition TEXT, recovery_pct REAL, rqd_pct REAL, gsi TEXT, rmr REAL, notes TEXT,
  edited_at TEXT, edited_by TEXT
);
CREATE TABLE IF NOT EXISTS history (
  id INTEGER PRIMARY KEY AUTOINCREMENT, photo_id INTEGER, field TEXT, old TEXT, new TEXT, src TEXT, by TEXT, at TEXT
);
CREATE INDEX IF NOT EXISTS ix_hole ON photos(hole_id);
"""


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _writable(d: Path) -> bool:
    try:
        d.mkdir(parents=True, exist_ok=True)
        t = d / ".tulis_uji"
        t.write_text("ok", encoding="utf-8")
        t.unlink()
        return True
    except OSError:
        return False


def get_project(folder: str) -> Project:
    f = Path(folder).expanduser().resolve()
    if not f.is_dir():
        raise ValueError(f"Folder foto tidak ditemukan: {folder}")
    key = str(f).lower()
    with _PLOCK:
        p = _PROJECTS.get(key)
        if p and p.db.exists():
            return p
        _PROJECTS.pop(key, None)  # folder _GCEx_Core dihapus / dipindah saat aplikasi terbuka: buat ulang
        d = f / PRJ_DIR
        local = not _writable(d)
        if local:
            d = cache_root() / "core_projects" / hashlib.sha1(key.encode()).hexdigest()[:16]
            d.mkdir(parents=True, exist_ok=True)
        p = Project(f, d / DB_NAME, local)
        with p.conn() as c:
            c.executescript(_DDL)
            have = {x[1] for x in c.execute("PRAGMA table_info(photos)")}
            for col, ddl in (("from_name", "TEXT DEFAULT '[]'"), ("drill_start", "TEXT"), ("photo_date", "TEXT"), ("rec_src", "TEXT")):
                if col not in have:
                    c.execute(f"ALTER TABLE photos ADD COLUMN {col} {ddl}")
            c.execute("INSERT OR IGNORE INTO meta VALUES ('schema', ?)", (str(SCHEMA_VERSION),))
            c.execute("INSERT OR IGNORE INTO meta VALUES ('created', ?)", (now(),))
        if not local:
            readme = f / PRJ_DIR / "BACA_SAYA.txt"
            if not readme.exists():
                readme.write_text("Folder ini dibuat oleh DB-Ex.\n"
                                  "gcex_core.db = hasil interpretasi & verifikasi semua foto di folder induknya.\n"
                                  "Jangan dihapus / diedit manual. Salin seluruh folder foto (termasuk folder ini)\n"
                                  "untuk memindahkan proyek ke komputer lain.\n", encoding="utf-8")
        _PROJECTS[key] = p
        return p


def scan(p: Project) -> dict:
    """Daftarkan foto baru, tandai foto yang hilang. Foto yang sudah ada tidak diubah."""
    found: dict[str, tuple[str, int, float]] = {}
    for root, dirs, files in os.walk(p.folder):
        dirs[:] = [d for d in dirs if d != PRJ_DIR and not d.startswith(".")]
        for fn in files:
            if Path(fn).suffix.lower() in IMG_EXT and not fn.startswith("._"):
                full = Path(root) / fn
                try:
                    st = full.stat()
                except OSError:
                    continue
                rel = full.relative_to(p.folder).as_posix()
                found[rel] = (fn, st.st_size, st.st_mtime)
    added = 0
    with p.lock, p.conn() as c:
        have = {r["rel"]: r["missing"] for r in c.execute("SELECT rel, missing FROM photos")}
        c.execute(_IGN_DDL)
        skip = {r[0] for r in c.execute("SELECT rel FROM ignored")}
        for rel in sorted(found, key=natural_key):
            if rel in skip:
                continue
            fn, sz, mt = found[rel]
            if rel in have:
                if have[rel]:
                    c.execute("UPDATE photos SET missing=0, size=?, mtime=? WHERE rel=?", (sz, mt, rel))
                continue
            guess = parse_filename(fn)
            cols = ["rel", "name", "size", "mtime", "from_name"] + list(guess)
            c.execute(f"INSERT INTO photos ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                      [rel, fn, sz, mt, json.dumps(sorted(guess))] + list(guess.values()))
            added += 1
        gone = [r for r, m in have.items() if r not in found and not m]
        for rel in gone:
            c.execute("UPDATE photos SET missing=1 WHERE rel=?", (rel,))
        total = c.execute("SELECT COUNT(*) FROM photos WHERE missing=0").fetchone()[0]
    return {"added": added, "missing": len(gone), "total": total}


_IGN_DDL = "CREATE TABLE IF NOT EXISTS ignored (rel TEXT PRIMARY KEY, name TEXT, by TEXT, at TEXT)"


def remove(p: Project, ids: list[int], by: str = "") -> dict:
    """Keluarkan foto dari daftar Core box. File foto TIDAK disentuh: namanya dicatat di tabel `ignored`
    supaya pemindaian berikutnya tidak memasukkannya lagi; baris foto beserta segmen & tandanya dihapus
    dari database. restore() mengembalikannya ke daftar (sebagai foto baru, isian lama tidak kembali)."""
    from . import core_marks, core_segs
    core_segs.ensure(p)
    core_marks.ensure(p)
    n = 0
    with p.lock, p.conn() as c:
        c.execute(_IGN_DDL)
        for pid in ids:
            r = c.execute("SELECT id, rel, name FROM photos WHERE id=?", (pid,)).fetchone()
            if not r:
                continue
            for tb in ("segs", "marks"):
                c.execute(f"DELETE FROM {tb} WHERE photo_id=?", (pid,))
            c.execute("DELETE FROM photos WHERE id=?", (pid,))
            c.execute("INSERT OR REPLACE INTO ignored VALUES (?,?,?,?)", (r["rel"], r["name"], by, now()))
            c.execute("INSERT INTO history (photo_id, field, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, "dikeluarkan", r["rel"], None, "keluarkan", by, now()))
            n += 1
    return {"removed": n, "ignored": n_ignored(p)}


def n_ignored(p: Project) -> int:
    with p.conn() as c:
        c.execute(_IGN_DDL)
        return c.execute("SELECT COUNT(*) FROM ignored").fetchone()[0]


def restore(p: Project) -> dict:
    """Kembalikan semua foto yang pernah dikeluarkan ke daftar, lalu pindai ulang."""
    with p.lock, p.conn() as c:
        c.execute(_IGN_DDL)
        c.execute("DELETE FROM ignored")
    return scan(p)


def _row_out(r: sqlite3.Row) -> dict:
    d = {k: r[k] for k in r.keys() if k not in ("ai_json",)}
    d["edited"] = json.loads(r["edited"] or "[]")
    d["from_name"] = json.loads(r["from_name"] or "[]")
    return d


def rows(p: Project) -> list[dict]:
    with p.conn() as c:
        rs = [_row_out(r) for r in c.execute("SELECT * FROM photos")]
    rs.sort(key=lambda r: natural_key(r["rel"]))
    return rs


def get_row(p: Project, pid: int) -> dict:
    """Satu baris foto lengkap (data bor + ringkasan tanda), sama seperti di /rows."""
    from . import core_dh, core_marks
    with p.conn() as c:
        r = c.execute("SELECT * FROM photos WHERE id=?", (pid,)).fetchone()
    if not r:
        raise KeyError(f"Foto id {pid} tidak ada")
    out = [_row_out(r)]
    core_dh.enrich(p, out)
    core_marks.enrich(p, out)
    _seg_count(p, out)
    return out[0]


def _seg_count(p: Project, rows_: list[dict]) -> None:
    from . import core_segs
    core_segs.ensure(p)
    with p.conn() as c:
        n = {r[0]: (r[1], r[2]) for r in c.execute("SELECT photo_id, COUNT(*), SUM(src='manual' OR edited<>'[]') FROM segs GROUP BY photo_id")}
    for r in rows_:
        r["n_segs"], r["n_segs_ed"] = n.get(r["id"], (0, 0))


def summary(p: Project) -> dict:
    with p.conn() as c:
        q = lambda s: c.execute(s).fetchone()[0]  # noqa: E731
        return {"total": q("SELECT COUNT(*) FROM photos WHERE missing=0"),
                "done": q("SELECT COUNT(*) FROM photos WHERE missing=0 AND status='done'"),
                "error": q("SELECT COUNT(*) FROM photos WHERE missing=0 AND status='error'"),
                "verified": q("SELECT COUNT(*) FROM photos WHERE missing=0 AND verified=1"),
                "missing": q("SELECT COUNT(*) FROM photos WHERE missing=1"),
                "ignored": (c.execute(_IGN_DDL), q("SELECT COUNT(*) FROM ignored"))[1],
                "holes": q("SELECT COUNT(DISTINCT hole_id) FROM photos WHERE missing=0 AND hole_id IS NOT NULL AND hole_id<>''")}


def _norm(field: str, v: Any) -> Any:
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    if FIELD_TYPE[field] == "n":
        if isinstance(v, str):
            v = v.replace(",", ".").replace("%", "").strip()
        f = float(v)
        if field in ("recovery_pct", "rqd_pct", "rmr"):
            f = max(0.0, min(100.0, f))
        return round(f, 3)
    return str(v).strip()


def update(p: Project, pid: int, values: dict, by: str) -> dict:
    with p.lock, p.conn() as c:
        r = c.execute("SELECT * FROM photos WHERE id=?", (pid,)).fetchone()
        if not r:
            raise KeyError(f"Foto id {pid} tidak ada")
        edited = set(json.loads(r["edited"] or "[]"))
        for k, v in values.items():
            if k not in FIELD_TYPE:
                raise ValueError(f"Kolom tidak dikenal: {k}")
            nv = _norm(k, v)
            if nv == r[k]:
                continue
            c.execute(f"UPDATE photos SET {k}=? WHERE id=?", (nv, pid))
            c.execute("INSERT INTO history (photo_id, field, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, k, None if r[k] is None else str(r[k]), None if nv is None else str(nv), "manual", by, now()))
            edited.add(k)
            if k == "recovery_pct":  # edit manual mengalahkan hitungan dari tanda core loss
                c.execute("UPDATE photos SET rec_src=NULL WHERE id=?", (pid,))
        c.execute("UPDATE photos SET edited=?, edited_at=?, edited_by=? WHERE id=?", (json.dumps(sorted(edited)), now(), by, pid))
        if ("from_m" in values or "to_m" in values) and "recovery_pct" not in values:
            from . import core_marks
            core_marks.ensure(p)
            core_marks.recompute_recovery(p, c, pid, by)
        return _row_out(c.execute("SELECT * FROM photos WHERE id=?", (pid,)).fetchone())


def set_verified(p: Project, ids: list[int], value: bool, by: str) -> int:
    with p.lock, p.conn() as c:
        n = 0
        for pid in ids:
            n += c.execute("UPDATE photos SET verified=?, verified_by=?, verified_at=? WHERE id=?",
                           (1 if value else 0, by if value else None, now() if value else None, pid)).rowcount
            c.execute("INSERT INTO history (photo_id, field, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                      (pid, "verified", None, "1" if value else "0", "manual", by, now()))
        return n


def get_meta(p: Project) -> dict:
    with p.conn() as c:
        return {r["key"]: r["value"] for r in c.execute("SELECT key, value FROM meta")}


def set_meta(p: Project, values: dict) -> None:
    with p.lock, p.conn() as c:
        for k, v in values.items():
            c.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (k, None if v is None else str(v)))


def photo_path(p: Project, pid: int) -> Path:
    with p.conn() as c:
        r = c.execute("SELECT rel FROM photos WHERE id=?", (pid,)).fetchone()
    if not r:
        raise KeyError(f"Foto id {pid} tidak ada")
    f = p.folder / r["rel"]
    if not f.exists():
        raise FileNotFoundError(f"File foto tidak ditemukan: {f}")
    return f


# ---------------------------------------------------------------- gambar
# foto panorama / gabungan core box bisa > 178 MP (batas bawaan Pillow); file lokal milik pengguna, bukan unggahan asing
_MAX_PX = 1_500_000_000


def _open_img(path: Path, max_px: int = 0):
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = _MAX_PX
    im = Image.open(path)
    if max_px and im.format == "JPEG":
        im.draft("RGB", (max_px, max_px))  # decode JPEG langsung di skala 1/2..1/8: lebih cepat & hemat memori
    im = ImageOps.exif_transpose(im)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    return im


def resized_jpeg(path: Path, max_px: int, quality: int = 88) -> bytes:
    im = _open_img(path, max_px)
    if max_px and max(im.size) > max_px:
        im.thumbnail((max_px, max_px))
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=quality, optimize=True)
    return b.getvalue()


def cached_image(path: Path, w: int) -> Path:
    st = path.stat()
    h = hashlib.sha1(f"{path}|{st.st_size}|{st.st_mtime}|{w}".encode()).hexdigest()
    d = cache_root() / "core_img" / h[:2]
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{h}.jpg"
    if not f.exists():
        tmp = f.with_suffix(".tmp")
        tmp.write_bytes(resized_jpeg(path, w, 82 if w <= 400 else 88))
        os.replace(tmp, f)
    return f


# ---------------------------------------------------------------- Ollama
def _http(url: str, body: Optional[dict] = None, timeout: float = 5.0) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST" if body is not None else "GET")
    # Ollama selalu di komputer sendiri: abaikan proxy kantor
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ollama_status(host: str) -> dict:
    host = (host or DEFAULT_HOST).rstrip("/")
    try:
        ver = _http(host + "/api/version", timeout=3).get("version")
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"ok": False, "host": host, "error": f"Ollama tidak berjalan di {host} ({e}).", "models": [], "recommended": RECOMMENDED_MODELS}
    models = []
    try:
        for m in _http(host + "/api/tags", timeout=5).get("models", []):
            name = m.get("name") or m.get("model")
            caps = None
            try:
                caps = _http(host + "/api/show", {"model": name}, timeout=10).get("capabilities")
            except (urllib.error.URLError, OSError, ValueError):
                pass
            fam = " ".join((m.get("details") or {}).get("families") or [])
            vision = ("vision" in caps) if isinstance(caps, list) else bool(re.search(r"vl|vision|llava|gemma3|clip|mllama", name + " " + fam, re.I))
            models.append({"name": name, "size": m.get("size"), "vision": vision,
                           "params": (m.get("details") or {}).get("parameter_size")})
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"ok": False, "host": host, "version": ver, "error": str(e), "models": [], "recommended": RECOMMENDED_MODELS}
    return {"ok": True, "host": host, "version": ver, "models": models, "recommended": RECOMMENDED_MODELS}


def ai_schema() -> dict:
    num = {"type": ["number", "null"]}
    txt = {"type": ["string", "null"]}
    return {
        "type": "object",
        "properties": {
            "hole_id": txt, "box_no": txt, "from_m": num, "to_m": num, "drill_start": txt, "photo_date": txt,
            "lithology": txt, "color": txt,
            "weathering": {"type": ["string", "null"], "enum": WEATHERING + [None]},
            "oxidation": {"type": ["string", "null"], "enum": OXIDATION + [None]},
            "alteration": txt,
            "condition": {"type": ["string", "null"], "enum": ["WET", "DRY", None]},
            "recovery_pct": num, "rqd_pct": num, "gsi": txt, "rmr": num, "notes": txt,
            "confidence": {"type": "string", "enum": ["rendah", "sedang", "tinggi"]},
            "segments": {"type": "array", "items": {"type": "object", "properties": {
                "row": {"type": "integer"}, "start": {"type": "number"}, "end": {"type": "number"},
                "lithology": txt, "alteration": txt, "color": txt,
                "weathering": {"type": ["string", "null"], "enum": WEATHERING + [None]},
                "oxidation": {"type": ["string", "null"], "enum": OXIDATION + [None]},
                "rqd_pct": num, "recovery_pct": num, "ff_per_m": num, "gsi": txt, "rmr": num, "notes": txt},
                "required": ["row", "start", "end", "lithology", "weathering", "rqd_pct", "recovery_pct"]}},
        },
        "required": ["hole_id", "box_no", "from_m", "to_m", "drill_start", "photo_date", "lithology", "color", "weathering", "oxidation", "alteration",
                     "condition", "recovery_pct", "rqd_pct", "gsi", "rmr", "notes", "confidence", "segments"],
    }


GEO_LABEL = {"lithology": "Litologi", "alteration": "Alterasi", "oxidation": "Oksidasi", "color": "Warna", "weathering": "Pelapukan"}


# ---------------------------------------------------------------- legenda site (istilah resmi proyek untuk semua prompt AI geologi)
LEGEND_KEYS = [("lithology", "Litologi"), ("alteration", "Alterasi"), ("mineral", "Oksida, vein & mineralisasi"),
               ("structure", "Struktur"), ("ignore", "Bukan geologi (abaikan)"), ("notes", "Catatan lain")]


def legend_get(p: Project) -> dict:
    try:
        d = json.loads(get_meta(p).get("site_legend") or "{}")
    except ValueError:
        d = {}
    return {k: str(d.get(k) or "").strip() for k, _ in LEGEND_KEYS}


def legend_set(p: Project, d: dict) -> dict:
    clean = {k: str((d or {}).get(k) or "").strip()[:1500] for k, _ in LEGEND_KEYS}
    set_meta(p, {"site_legend": json.dumps(clean, ensure_ascii=False)})
    return clean


def legend_text(leg: dict) -> str:
    rows_ = [f"- {name}: {leg[k]}" for k, name in LEGEND_KEYS if (leg or {}).get(k)]
    if not rows_:
        return ""
    return ("LEGENDA SITE (istilah resmi proyek ini). Pakai nama dari legenda untuk name / deskripsi bila sesuai dengan yang terlihat; "
            "bila foto jelas memperlihatkan hal lain, tulis apa adanya dengan confidence rendah:\n" + "\n".join(rows_))


def with_legend(p: Optional[Project], extra: str = "") -> str:
    """Instruksi tambahan untuk prompt: legenda site proyek + catatan geologist (keduanya opsional)."""
    lt = legend_text(legend_get(p)) if p is not None else ""
    ex = (extra or "").strip()
    return "\n\n".join(x for x in (lt, ex) if x)


def ai_prompt(extra: str = "", logged: Optional[dict] = None, rows: int = 4, box_len: Optional[float] = None) -> str:
    # Tata letak foto core box standar: papan label putih di atas kotak, 4 baris core di kotak besi/kayu,
    # blok penanda run, papan skala catur hitam-putih di bawah. Contoh nilai di bawah fiktif.
    p = (
        "Anda ahli geoteknik senior yang menilai foto core box hasil pemboran inti (diamond drilling) di tambang emas "
        "epitermal. TUJUAN UTAMA: parameter GEOTEKNIK dari foto "
        "(core recovery, RQD, GSI, RMR, pelapukan, kondisi, struktur). Deskripsi geologi hanya pelengkap bila "
        "logging geologist belum ada.\n\n"
        "TATA LETAK FOTO (standar proyek):\n"
        "- Papan label putih di BAGIAN ATAS, tulisan tangan / spidol hitam, berisi:\n"
        "  baris 1: nama perusahaan / proyek (abaikan);\n"
        "  'HOLE ID: LTH-101' -> hole_id;  'START DRILL: 05-03-25' -> drill_start;\n"
        "  'BOX: 11' -> box_no;  'DATE POTO: 12-03-25' -> photo_date;\n"
        "  'DEPTH: 36.30' -> from_m;  'M:TO: 40.10' -> to_m;  'M:CONDT: WET' -> condition (WET / DRY).\n"
        "  Tulisan tangan sering rapat: '050325' berarti 05-03-25. Tulis tanggal seperti tertulis (DD-MM-YY). "
        "Bedakan O/0, I/1, S/5, B/8 dari konteks (Hole ID berpola huruf-strip-angka, kedalaman berupa angka meter dengan 2 desimal).\n"
        "- Di bawah papan: kotak core berisi biasanya 4 BARIS core, dibaca kiri ke kanan, baris atas ke bawah "
        "(atas = lebih dangkal). Blok kecil putih bertulis di antara core = penanda kedalaman run / core block.\n"
        "- Papan catur hitam-putih di paling bawah = skala panjang (tiap kotak 20 cm); pakai untuk memperkirakan panjang potongan core.\n\n"
        "TUGAS:\n"
        "1. Baca papan label. Jangan menebak angka / huruf yang tidak terbaca: isi null. "
        "to_m harus lebih besar dari from_m; satu box umumnya berisi 3-5 m core.\n"
        "2. GEOTEKNIK (prioritas): core recovery (%) = panjang core yang ada dibanding interval box; "
        "RQD (%) = jumlah panjang potongan core utuh >= 10 cm dibagi panjang interval (pakai skala catur 20 cm); "
        "GSI (rentang, mis. '55-65') dari struktur blok & kondisi permukaan rekahan; RMR perkiraan (0-100); "
        "tingkat pelapukan skala ISRM W1-W6. Ini PERKIRAAN visual; bila tidak bisa dinilai isi null.\n"
        "3. Geologi pelengkap: litologi dominan, warna dominan (bahasa Indonesia + istilah Inggris dalam kurung, "
        "mis. 'Abu-abu gelap kehitaman (Dark Grey)'), tingkat oksidasi (oksida besi coklat / merah / kuning = teroksidasi), "
        "alterasi yang terlihat (mis. silisifikasi, argilik, propilitik, kuarsa vein / stockwork, sulfida).\n"
        "4. condition: dari papan (M:CONDT) bila terbaca; bila tidak, WET bila core basah / mengkilap, DRY bila kering.\n"
        "5. notes: ringkas (maks 2 kalimat) tentang struktur (rekahan, kekar, sesar, zona hancur / rubble), vein dan "
        "mineralisasi yang terlihat, sebut baris core bila perlu (mis. 'baris 3 zona hancur').\n"
        "6. confidence: seberapa yakin Anda atas pembacaan papan label dan deskripsi (rendah / sedang / tinggi).\n"
        f"7. segments: nilai PER BARIS CORE dan mengikuti BATAS GEOLOGI AKTUAL. Kotak berisi {rows} baris "
        "(row 1 = baris paling atas / paling dangkal). Untuk setiap baris, bagi core dari kiri ke kanan menjadi segmen "
        "di setiap perubahan nyata litologi, warna, pelapukan, oksidasi, alterasi, vein, atau zona rekahan / hancur. "
        "start dan end = posisi di sepanjang baris itu (0 = ujung kiri core, 1 = ujung kanan core); segmen satu baris "
        "harus menutup 0 sampai 1 tanpa celah dan tidak boleh menyeberang ke baris lain. "
        + (f"Panjang satu baris kira-kira {box_len / rows:.2f} m; " if box_len else "")
        + "segmen tidak lebih panjang dari ~1 m (bagi bila perlu). Tiap segmen: litologi, warna, pelapukan (W1-W6), "
        "oksidasi, alterasi, rqd_pct dan recovery_pct segmen itu, ff_per_m (jumlah rekahan alami per meter), gsi, "
        "rmr, notes singkat. Nilai geoteknik segmen boleh berbeda dari nilai box. Bila tidak bisa dinilai isi null.\n"
        "Jawab HANYA dengan JSON sesuai skema."
    )
    if logged:
        p += ("\n\nINTERVAL INI SUDAH DILOGGING GEOLOGIST (data resmi, jangan diubah): "
              + "; ".join(f"{GEO_LABEL.get(k, k)}: {v}" for k, v in logged.items())
              + ". Isi kolom " + ", ".join(sorted(logged)) + " dengan null. Pakai logging ini hanya sebagai konteks "
              "(mis. QV / silisifikasi umumnya keras dan RQD tinggi kecuali hancur), lalu fokus pada geoteknik.")
    if extra and extra.strip():
        p += "\n\nInstruksi tambahan dari geologist proyek:\n" + extra.strip()
    return p


def _parse_json(text: str) -> dict:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?|```$", "", t, flags=re.M).strip()
    try:
        return json.loads(t)
    except ValueError:
        m = re.search(r"\{.*\}", t, re.S)
        if not m:
            raise ValueError("Jawaban model bukan JSON: " + t[:200])
        return json.loads(m.group(0))


def ollama_analyze(host: str, model: str, img: bytes, extra: str = "", timeout: float = 900, logged: Optional[dict] = None,
                   rows: int = 4, box_len: Optional[float] = None) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": ai_prompt(extra, logged, rows, box_len), "images": [base64.b64encode(img).decode()]}],
        "stream": False,
        "format": ai_schema(),
        "options": {"temperature": 0, "num_ctx": 16384},
        "keep_alive": "15m",
    }
    j = _http((host or DEFAULT_HOST).rstrip("/") + "/api/chat", body, timeout=timeout)
    if j.get("error"):
        raise RuntimeError("Ollama: " + str(j["error"]))
    return _parse_json((j.get("message") or {}).get("content", ""))


def apply_ai(p: Project, pid: int, res: dict, model: str, secs: float, protect: Optional[set] = None) -> None:
    """Isi kolom dari hasil AI, kecuali kolom yang sudah diedit geologist, diambil dari nama file
    (Hole / Box / kedalaman), sudah ada di logging geologist (protect), atau foto sudah diverifikasi.
    Bacaan AI tetap tersimpan utuh di ai_json."""
    with p.lock, p.conn() as c:
        r = c.execute("SELECT * FROM photos WHERE id=?", (pid,)).fetchone()
        if not r:
            return
        edited = set(json.loads(r["edited"] or "[]")) | set(json.loads(r["from_name"] or "[]")) | set(protect or ())
        if r["rec_src"] == "tanda":  # recovery dihitung dari tanda core loss: tidak ditimpa AI
            edited.add("recovery_pct")
        sets, vals = [], []
        if not r["verified"]:
            for k, _t, _l in FIELDS:
                if k in edited or k not in res:
                    continue
                try:
                    nv = _norm(k, res[k])
                except (TypeError, ValueError):
                    nv = None
                # nilai yang sudah ada tidak dihapus oleh null dari AI
                if nv is None and r[k] is not None:
                    continue
                sets.append(f"{k}=?")
                vals.append(nv)
                if nv != r[k]:
                    c.execute("INSERT INTO history (photo_id, field, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                              (pid, k, None if r[k] is None else str(r[k]), None if nv is None else str(nv), "ai:" + model, "AI", now()))
        sets += ["status='done'", "error=NULL", "ai_json=?", "ai_model=?", "ai_at=?", "ai_secs=?", "ai_conf=?"]
        vals += [json.dumps(res, ensure_ascii=False), model, now(), round(secs, 1), res.get("confidence")]
        c.execute(f"UPDATE photos SET {', '.join(sets)} WHERE id=?", vals + [pid])


# ---------------------------------------------------------------- antrean AI (satu thread)
class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.state: dict[str, Any] = {"running": False}
        self.cancel = False
        self.thread: Optional[threading.Thread] = None


JOB = Job()


def ai_start(p: Project, ids: list[int], host: str, model: str, extra: str, max_px: int) -> dict:
    with JOB.lock:
        if JOB.state.get("running"):
            raise RuntimeError("Interpretasi AI masih berjalan. Tunggu selesai atau klik Hentikan.")
        JOB.cancel = False
        JOB.state = {"running": True, "folder": str(p.folder), "total": len(ids), "done": 0, "failed": 0,
                     "current": None, "current_id": None, "started": time.time(), "last_secs": None, "model": model,
                     "message": "Memulai…", "finished": None}

    extra = with_legend(p, extra)

    def work():
        st = JOB.state
        try:
            for pid in ids:
                if JOB.cancel:
                    st["message"] = "Dihentikan pengguna"
                    break
                t0 = time.time()
                try:
                    f = photo_path(p, pid)
                    st["current"], st["current_id"] = f.name, pid
                    st["message"] = f"Menganalisis {f.name}"
                    from . import core_dh, core_segs
                    logged = core_dh.logged_for_photo(p, pid)  # logging geologist diutamakan; AI fokus geoteknik
                    rows_n, box_len = core_dh.tray_info(p, pid)
                    res = ollama_analyze(host, model, resized_jpeg(f, max_px), extra, logged=logged, rows=rows_n, box_len=box_len)
                    apply_ai(p, pid, res, model, time.time() - t0, protect=set(logged))
                    core_segs.apply_ai_segments(p, pid, res.get("segments"), rows_n, model)
                    st["done"] += 1
                except Exception as e:  # noqa: BLE001 - satu foto gagal tidak menghentikan antrean
                    log.warning("AI gagal untuk id %s: %s", pid, e)
                    st["failed"] += 1
                    with p.lock, p.conn() as c:
                        c.execute("UPDATE photos SET status='error', error=? WHERE id=?", (str(e)[:500], pid))
                    if isinstance(e, (urllib.error.URLError, ConnectionError)) and "refused" in str(e).lower():
                        st["message"] = "Ollama berhenti / tidak bisa dihubungi"
                        break
                st["last_secs"] = round(time.time() - t0, 1)
            else:
                st["message"] = "Selesai"
        finally:
            st["running"] = False
            st["current"] = st["current_id"] = None
            st["finished"] = time.time()

    JOB.thread = threading.Thread(target=work, name="gcex-core-ai", daemon=True)
    JOB.thread.start()
    return dict(JOB.state)


# ---------------------------------------------------------------- Excel & impor proyek lama
def export_xlsx(p: Project, ids: Optional[list[int]] = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    from . import core_dh, core_marks
    data = rows(p)
    core_dh.enrich(p, data)
    core_marks.enrich(p, data)
    els = [c["name"] for c in core_dh.columns(p)["assay"] if c["type"] == "n"]
    if ids:
        s = set(ids)
        data = [r for r in data if r["id"] in s]
    wb = Workbook()
    ws = wb.active
    ws.title = "Core Log"
    head = ["No", "File Foto", "Subfolder"] + [l for _k, _t, l in FIELDS] + [f"{e} rata-rata" for e in els] + [f"{e} maks" for e in els] + ["Interval (m)", "Core loss (m)", "Half core (m)", "Sampel half core", "Sumber isian geologi", "Status AI", "Model AI", "Keyakinan AI", "Diverifikasi", "Diverifikasi oleh", "Tanggal verifikasi", "Diedit oleh"]
    ws.append(head)
    hf = PatternFill("solid", fgColor="141A26")
    for i, _ in enumerate(head, 1):
        cell = ws.cell(row=1, column=i)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = hf
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ai_fill = PatternFill("solid", fgColor="E2EAF6")
    for n, r in enumerate(data, 1):
        iv = round(r["to_m"] - r["from_m"], 2) if r["from_m"] is not None and r["to_m"] is not None else None
        sub = str(Path(r["rel"]).parent).replace("\\", "/")
        g, gm, lg = r.get("g") or {}, r.get("gmax") or {}, r.get("log") or {}
        src = []
        for k in ("lithology", "alteration", "oxidation", "color", "weathering"):
            s_ = "logging" if k in lg else "manual" if k in r["edited"] else "AI" if r["status"] == "done" and r[k] is not None else None
            if s_:
                src.append(f"{GEO_LABEL[k]}: {s_}")
        if r.get("rec_src") == "tanda":
            src.append("Recovery: tanda core loss")
        line = [n, r["name"], "" if sub == "." else sub] + [lg.get(k, r[k]) for k, _t, _l in FIELDS] + [g.get(e) for e in els] + [gm.get(e) for e in els] + [
            iv, r.get("loss_m"), r.get("half_m"), r.get("half_samples") or None, "; ".join(src), {"done": "Selesai", "error": "Gagal", "pending": "Belum"}.get(r["status"], r["status"]), r["ai_model"], r["ai_conf"],
            "Ya" if r["verified"] else "Belum", r["verified_by"], r["verified_at"], r["edited_by"]]
        ws.append(line)
        c = ws.cell(row=n + 1, column=2)
        c.hyperlink = (p.folder / r["rel"]).as_uri()
        c.font = Font(color="1F5FA8", underline="single")
        if not r["verified"]:  # isian AI yang belum diverifikasi diberi warna
            for j, (k, _t, _l) in enumerate(FIELDS):
                if k not in r["edited"] and k not in r["from_name"] and k not in lg and r["status"] == "done" and r[k] is not None \
                        and not (k == "recovery_pct" and r.get("rec_src") == "tanda"):
                    ws.cell(row=n + 1, column=4 + j).fill = ai_fill
    # No, File, Subfolder, Hole, Box, From, To, Start Drill, Tgl Foto, Litologi, Warna, Pelapukan, Oksidasi, Alterasi, Kondisi,
    # Recovery, RQD, GSI, RMR, Catatan, Interval, Status, Model, Keyakinan, Diverifikasi, oleh, tanggal, Diedit oleh
    widths = [5, 30, 14, 12, 7, 9, 9, 12, 12, 18, 26, 24, 20, 22, 9, 10, 9, 9, 8, 50, 10, 10, 16, 10, 11, 14, 18, 14]
    widths = widths[:3 + len(FIELDS)] + [11] * (2 * len(els)) + widths[3 + len(FIELDS):3 + len(FIELDS) + 1] + [11, 11, 18, 34] + widths[3 + len(FIELDS) + 1:]
    for i, w in enumerate(widths[:len(head)], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions
    marks = core_marks.table(p)
    names = {r["name"] for r in data}
    if ids:
        marks = [m for m in marks if m[7] in names]
    mw = wb.create_sheet("Interval")
    mw.append(core_marks.HEAD)
    for i, _ in enumerate(core_marks.HEAD, 1):
        cell = mw.cell(row=1, column=i)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = hf
    for m in marks:
        mw.append(m)
    for i, w in enumerate([12, 9, 9, 11, 12, 14, 40, 34, 14, 18], 1):
        mw.column_dimensions[get_column_letter(i)].width = w
    mw.freeze_panes = "A2"
    if marks:
        mw.auto_filter.ref = mw.dimensions
    from . import core_segs
    sg = core_segs.table(p)
    if ids:
        sg = [x for x in sg if x[-3] in names]
    sw = wb.create_sheet("Segmen")
    sw.append(core_segs.HEAD)
    for i, _ in enumerate(core_segs.HEAD, 1):
        cell = sw.cell(row=1, column=i)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = hf
    for x in sg:
        sw.append(x)
        if x[-5] == "AI" and not x[-4]:
            for j in range(5, 5 + len(core_segs.SEG_FIELDS)):
                if sw.cell(row=sw.max_row, column=j).value is not None:
                    sw.cell(row=sw.max_row, column=j).fill = ai_fill
    sw.freeze_panes = "B2"
    if sg:
        sw.auto_filter.ref = sw.dimensions
    from .legal_mark import COPYRIGHT, mark_workbook
    info = wb.create_sheet("Keterangan")
    for line in [["DB-Ex — log foto core box"], [COPYRIGHT], ["Folder proyek", str(p.folder)], ["Dibuat", now()],
                 [], ["Sel biru muda = isian AI yang belum diedit / diverifikasi geologist."],
                 ["Litologi, alterasi, oksidasi, warna, pelapukan: diambil dari LOGGING GEOLOGIST (tabel Geologi) bila ada di rentang foto; AI visual hanya mengisi bila logging tidak ada. Lihat kolom 'Sumber isian geologi'."],
                 ["RQD, GSI, RMR dan recovery dari AI adalah perkiraan visual dari foto, bukan pengukuran. Wajib diverifikasi."],
                 ["Sheet 'Segmen' = interpretasi per baris core / batas geologi (AI dan editan geologist). Sel biru muda = nilai AI yang belum diedit."],
                 ["Sheet 'Interval' = tanda half core (dengan nomor sampel) dan core loss yang digambar geologist di foto. Bila foto punya tanda, Core Recovery (%) = (interval foto - total core loss) / interval foto."],
                 ["Kolom '<unsur> rata-rata' = rata-rata tertimbang panjang assay lab di rentang From-To foto; 'maks' = nilai interval tertinggi."]]:
        info.append(line)
    info.column_dimensions["A"].width = 24
    info.column_dimensions["B"].width = 80
    mark_workbook(wb, "DB-Ex")
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


_OLD_MAP = {"holeId": "hole_id", "boxNo": "box_no", "fromM": "from_m", "toM": "to_m", "color": "color", "weathering": "weathering",
            "oxidation": "oxidation", "condition": "condition", "recoveryPct": "recovery_pct", "rqdPct": "rqd_pct", "gsi": "gsi",
            "rmr": "rmr", "notes": "notes", "lithology": "lithology", "alteration": "alteration"}


def import_old_json(p: Project, payload: dict, by: str) -> dict:
    """Impor file proyek .json dari dashboard lama (Gemini) berdasarkan nama file foto."""
    items = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("Format JSON tidak dikenali (butuh daftar 'data').")
    with p.conn() as c:
        by_name: dict[str, list[int]] = {}
        for r in c.execute("SELECT id, name FROM photos"):
            by_name.setdefault(r["name"].lower(), []).append(r["id"])
    hit, miss = 0, []
    for it in items:
        ids = by_name.get(str(it.get("fileName", "")).lower())
        if not ids:
            miss.append(it.get("fileName"))
            continue
        vals = {}
        for k_old, k in _OLD_MAP.items():
            v = it.get(k_old)
            if v in (None, "", "-"):
                continue
            try:
                vals[k] = _norm(k, v)
            except (TypeError, ValueError):
                continue
        for pid in ids:
            if it.get("status") == "done":  # hasil AI lama: diperlakukan sebagai isian AI (belum diverifikasi)
                apply_ai(p, pid, {**vals, "confidence": None}, "impor-json", 0)
            else:
                update(p, pid, vals, by)
        hit += 1
    return {"matched": hit, "unmatched": len(miss), "unmatched_names": miss[:20]}


# ---------------------------------------------------------------- API
class FolderBody(BaseModel):
    folder: str
    by: str = ""


class UpdateBody(FolderBody):
    id: int
    values: dict[str, Any]


class VerifyBody(FolderBody):
    ids: list[int]
    value: bool = True


class MetaBody(FolderBody):
    values: dict[str, Any]


class AiBody(FolderBody):
    ids: list[int] = []
    scope: str = "pending"  # pending | all | ids
    host: str = DEFAULT_HOST
    model: str
    extra: str = ""
    max_px: int = 1600


class HostBody(BaseModel):
    host: str = DEFAULT_HOST


class ExportBody(FolderBody):
    ids: list[int] = []


class ImportBody(FolderBody):
    payload: Any


class OpenBody(FolderBody):
    scan: bool = True  # False: folder dibuka untuk ruang kerja lain (Singkapan / Borang / QAQC) -> foto tidak didaftarkan ke Core box


@router.post("/open")
def api_open(b: OpenBody) -> dict:
    p = get_project(b.folder)
    sc = scan(p) if b.scan else {"added": 0, "missing": 0, "total": summary(p)["total"], "skipped": True}
    return {"ok": True, "folder": str(p.folder), "db": str(p.db), "db_local": p.local, "scan": sc,
            "summary": summary(p), "meta": get_meta(p), "fields": [{"key": k, "type": t, "label": l} for k, t, l in FIELDS],
            "weathering": WEATHERING, "oxidation": OXIDATION}


@router.post("/rescan")
def api_rescan(b: FolderBody) -> dict:
    p = get_project(b.folder)
    return {"ok": True, "scan": scan(p), "summary": summary(p)}


class RemoveBody(FolderBody):
    ids: list[int]


@router.post("/remove")
def api_remove(b: RemoveBody) -> dict:
    p = get_project(b.folder)
    return {"ok": True, **remove(p, b.ids, b.by), "summary": summary(p)}


@router.post("/restore")
def api_restore(b: FolderBody) -> dict:
    p = get_project(b.folder)
    return {"ok": True, "scan": restore(p), "summary": summary(p)}


@router.post("/rows")
def api_rows(b: FolderBody) -> dict:
    from . import core_dh, core_marks  # data bor: kadar per foto; tanda half core / core loss
    p = get_project(b.folder)
    rs = rows(p)
    core_dh.enrich(p, rs)
    core_marks.enrich(p, rs)
    _seg_count(p, rs)
    return {"ok": True, "rows": rs, "summary": summary(p), "dh": core_dh.summary(p)}


@router.post("/update")
def api_update(b: UpdateBody) -> dict:
    return {"ok": True, "row": update(get_project(b.folder), b.id, b.values, b.by)}


@router.post("/verify")
def api_verify(b: VerifyBody) -> dict:
    p = get_project(b.folder)
    return {"ok": True, "n": set_verified(p, b.ids, b.value, b.by), "summary": summary(p)}


@router.post("/meta")
def api_meta(b: MetaBody) -> dict:
    p = get_project(b.folder)
    set_meta(p, b.values)
    return {"ok": True, "meta": get_meta(p)}


@router.post("/history")
def api_history(b: UpdateBody) -> dict:
    p = get_project(b.folder)
    with p.conn() as c:
        h = [dict(r) for r in c.execute("SELECT field, old, new, src, by, at FROM history WHERE photo_id=? ORDER BY id DESC LIMIT 200", (b.id,))]
        r = c.execute("SELECT ai_json FROM photos WHERE id=?", (b.id,)).fetchone()
    return {"ok": True, "history": h, "ai": json.loads(r["ai_json"]) if r and r["ai_json"] else None}


@router.get("/img")
def api_img(folder: str, id: int, w: int = 320):
    p = get_project(folder)
    f = photo_path(p, id)
    if w <= 0:
        return FileResponse(f)
    return FileResponse(cached_image(f, max(64, min(w, 4000))), media_type="image/jpeg",
                        headers={"Cache-Control": "max-age=86400"})


@router.post("/ollama")
def api_ollama(b: HostBody) -> dict:
    s = ollama_status(b.host)
    s["running"] = s.pop("ok")
    return {"ok": True, **s}


class LegendBody(BaseModel):
    folder: str
    legend: Optional[dict] = None


@router.post("/legend")
def api_legend(b: LegendBody) -> dict:
    """Baca (legend = None) atau simpan legenda site proyek."""
    p = get_project(b.folder)
    leg = legend_get(p) if b.legend is None else legend_set(p, b.legend)
    return {"ok": True, "legend": leg, "keys": [{"key": k, "name": n} for k, n in LEGEND_KEYS], "prompt": legend_text(leg)}


@router.post("/ai/start")
def api_ai_start(b: AiBody) -> dict:
    p = get_project(b.folder)
    if not b.model:
        raise ValueError("Pilih model AI dulu.")
    with p.conn() as c:
        if b.scope == "all":
            ids = [r[0] for r in c.execute("SELECT id FROM photos WHERE missing=0 AND verified=0")]
        elif b.scope == "ids":
            ids = list(b.ids)
        else:
            ids = [r[0] for r in c.execute("SELECT id FROM photos WHERE missing=0 AND verified=0 AND status<>'done'")]
    rel = {r["id"]: r["rel"] for r in rows(p)}
    ids = sorted(set(i for i in ids if i in rel), key=lambda i: natural_key(rel[i]))
    if not ids:
        raise ValueError("Tidak ada foto yang perlu dianalisis (semua sudah selesai / diverifikasi).")
    set_meta(p, {"ai_model": b.model, "ai_host": b.host, "ai_extra": b.extra, "ai_max_px": b.max_px})
    return {"ok": True, "job": ai_start(p, ids, b.host, b.model, b.extra, b.max_px)}


@router.get("/ai/status")
def api_ai_status() -> dict:
    s = dict(JOB.state)
    if s.get("running") and s.get("done", 0) + s.get("failed", 0) > 0:
        el = time.time() - s["started"]
        k = s["done"] + s["failed"]
        s["eta_secs"] = round(el / k * (s["total"] - k))
    return {"ok": True, "job": s}


@router.post("/ai/cancel")
def api_ai_cancel() -> dict:
    JOB.cancel = True
    return {"ok": True}


@router.post("/export/xlsx")
def api_export(b: ExportBody) -> Response:
    return Response(content=export_xlsx(get_project(b.folder), b.ids or None),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/import/json")
def api_import(b: ImportBody) -> dict:
    p = get_project(b.folder)
    return {"ok": True, **import_old_json(p, b.payload, b.by), "summary": summary(p)}
