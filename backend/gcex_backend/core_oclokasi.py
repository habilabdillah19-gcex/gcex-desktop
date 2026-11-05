"""Lokasi kamera dari metadata foto (EXIF GPS HP, mis. iPhone) untuk ruang kerja Singkapan DB-Ex (Fase 2a).

- Baca EXIF: lintang / bujur / ketinggian, ketelitian posisi (GPSHPositioningError), arah hadap kamera
  (GPSImgDirection, utara sejati / magnetik), tanggal-jam + zona waktu, kamera & lensa (panjang fokus ekuivalen 35 mm).
- WGS84 -> UTM (proyeksi Transverse Mercator, deret Krüger, galat < 1 mm) tanpa pustaka tambahan. Sistem koordinat proyek:
  otomatis dari bujur (zona & belahan), atau ditetapkan (mis. UTM 50S) di pengaturan proyek.
- Posisi kamera per foto (E, N, RL ± ketelitian), lubang bor terdekat dari Collar yang sudah diimpor, pemeriksaan terhadap
  georef (jarak kamera ke bidang singkapan), dan peta posisi foto (PNG).

GPS HP hanya teliti beberapa meter (bukan RTK): dipakai untuk "di mana & menghadap ke mana" foto diambil, bukan untuk
mengukur geometri dinding. Koordinat georef dari titik survey tetap acuan."""
from __future__ import annotations

import base64
import io
import json
import math
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from . import core_io
from . import core_outcrop as O

router = APIRouter(prefix="/core/outcrop/loc", tags=["core-outcrop-lokasi"])


# ================================================================ EXIF
def _rat(v: Any) -> Optional[float]:
    try:
        if isinstance(v, tuple) and len(v) == 2:
            return float(v[0]) / float(v[1]) if float(v[1]) else None
        return float(v)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _dms(v: Any) -> Optional[float]:
    try:
        d, m, s = (_rat(x) for x in v)
        return d + m / 60.0 + s / 3600.0
    except (TypeError, ValueError):
        return None


def _txt(v: Any) -> str:
    if isinstance(v, bytes):
        v = v.decode("ascii", "ignore")
    return str(v or "").strip().strip("\x00")


DJI_KEYS = {"AbsoluteAltitude": "abs_alt", "RelativeAltitude": "rel_alt", "GimbalYawDegree": "gimbal_yaw",
            "GimbalPitchDegree": "gimbal_pitch", "GimbalRollDegree": "gimbal_roll", "FlightYawDegree": "flight_yaw",
            "RtkFlag": "rtk_flag", "RtkStdLon": "rtk_std_e", "RtkStdLat": "rtk_std_n", "RtkStdHgt": "rtk_std_h"}


def read_dji_xmp(path: Path) -> dict:
    """Metadata drone DJI (Mavic 3 / 3E, Phantom 4 RTK, Matrice) dari paket XMP di kepala JPEG: tinggi absolut & relatif
    terhadap titik lepas landas, yaw / pitch / roll gimbal, status & ketelitian RTK. {} bila bukan foto DJI."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(256 * 1024)
    except OSError:
        return {}
    i = head.find(b"<x:xmpmeta")
    if i < 0 or b"drone-dji" not in head:
        return {}
    j = head.find(b"</x:xmpmeta>", i)
    xmp = head[i:j if j > 0 else len(head)].decode("utf-8", "ignore")
    raw = dict(re.findall(r'drone-dji:(\w+)="([^"]*)"', xmp))
    raw.update(re.findall(r"<drone-dji:(\w+)>([^<]*)</drone-dji:\w+>", xmp))
    out: dict[str, Any] = {}
    for k, nk in DJI_KEYS.items():
        try:
            out[nk] = round(float(str(raw[k]).strip()), 3)
        except (KeyError, ValueError):
            pass
    return out


def read_exif(path: Path) -> dict:
    """Metadata lokasi & kamera dari file foto. Kunci yang tidak ada tidak diisi; {} bila tidak ada EXIF."""
    from PIL import Image
    out: dict[str, Any] = {}
    try:
        with Image.open(path) as im:
            ex = im.getexif()
            gps = ex.get_ifd(0x8825)
            sub = ex.get_ifd(0x8769)
    except Exception:  # noqa: BLE001  format tanpa EXIF / rusak
        return out
    mk, md = _txt(ex.get(271)), _txt(ex.get(272))
    if mk or md:
        out["camera"] = (md if md.startswith(mk) else f"{mk} {md}").strip()
    if sub.get(0xA434):
        out["lens"] = _txt(sub.get(0xA434))
    if sub.get(0xA405):
        out["f35"] = int(sub.get(0xA405))
    dt = _txt(sub.get(36867) or ex.get(306))
    m = re.match(r"(\d{4}):(\d{2}):(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?", dt)
    if m:
        out["taken"] = f"{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}"
        tz = _txt(sub.get(36881) or sub.get(36880))
        if re.match(r"[+-]\d{2}:\d{2}", tz):
            out["tz"] = tz
    if gps:
        lat, lon = _dms(gps.get(2)), _dms(gps.get(4))
        if lat is not None and lon is not None and not (lat == 0 and lon == 0):
            if _txt(gps.get(1)).upper() == "S":
                lat = -lat
            if _txt(gps.get(3)).upper() == "W":
                lon = -lon
            out["lat"], out["lon"] = round(lat, 8), round(lon, 8)
            alt = _rat(gps.get(6))
            if alt is not None:
                ref = gps.get(5)
                below = (ref == 1) or (isinstance(ref, bytes) and ref[:1] == b"\x01")
                out["alt"] = round(-alt if below else alt, 2)
            hacc = _rat(gps.get(31))
            if hacc is not None:
                out["hacc"] = round(hacc, 1)
            hd = _rat(gps.get(17))
            if hd is not None:
                out["heading"] = round(hd % 360, 1)
                out["heading_ref"] = "magnetik" if _txt(gps.get(16)).upper() == "M" else "sejati"
    dj = read_dji_xmp(path)
    if dj:
        out["drone"] = dj
        if out.get("heading") is None and dj.get("gimbal_yaw") is not None:
            out["heading"] = round(dj["gimbal_yaw"] % 360, 1)
            out["heading_ref"] = "gimbal"
        if dj.get("abs_alt") is not None:
            out["alt"] = dj["abs_alt"]
        if dj.get("rtk_flag") == 50 and dj.get("rtk_std_e") is not None:
            out["hacc"] = round(max(dj.get("rtk_std_e") or 0, dj.get("rtk_std_n") or 0), 3)
    return out


def drone_kind(ex: dict) -> Optional[str]:
    """Jenis foto dari sudut gimbal drone: menunduk tajam = lantai (floor), mendatar = dinding (wall)."""
    p = ((ex or {}).get("drone") or {}).get("gimbal_pitch")
    if p is None:
        return None
    return "floor" if p <= -60 else ("wall" if p >= -40 else None)


def drone_floor_scale(ex: dict, w: int, h: int, h_floor: Optional[float] = None) -> Optional[dict]:
    """Skala foto lantai dari drone yang menunduk tegak: meter per piksel = tinggi kamera di atas lantai x 36 mm /
    (fokus ekuivalen 35 mm x sisi panjang piksel). Tinggi = isian geologist, atau tinggi relatif drone (anggap lantai
    setinggi titik lepas landas). Perkiraan: lantai dianggap datar & tegak lurus sumbu kamera."""
    dj = (ex or {}).get("drone") or {}
    p, f35 = dj.get("gimbal_pitch"), (ex or {}).get("f35")
    H = h_floor if h_floor else dj.get("rel_alt")
    if p is None or p > -75 or not f35 or not H or H <= 0:
        return None
    mpp = H * 36.0 / (f35 * max(w, h))
    return {"m_per_px": mpp, "height_m": round(H, 2), "source": "isian" if h_floor else "tinggi relatif drone", "pitch": p}


# ================================================================ WGS84 -> UTM (Krüger)
_A, _F, _K0 = 6378137.0, 1 / 298.257223563, 0.9996


def utm_zone(lon: float) -> int:
    return int((lon + 180) // 6) % 60 + 1


def to_utm(lat: float, lon: float, zone: Optional[int] = None, south: Optional[bool] = None) -> tuple[float, float, int, bool]:
    """(E, N, zona, selatan). Zona / belahan bisa dipaksa (mis. titik dekat batas zona tetap di zona proyek)."""
    zone = zone or utm_zone(lon)
    south = (lat < 0) if south is None else south
    n = _F / (2 - _F)
    A = _A / (1 + n) * (1 + n ** 2 / 4 + n ** 4 / 64)
    al = [n / 2 - 2 * n ** 2 / 3 + 5 * n ** 3 / 16, 13 * n ** 2 / 48 - 3 * n ** 3 / 5, 61 * n ** 3 / 240]
    phi, lam = math.radians(lat), math.radians(lon - (zone * 6 - 183))
    e = 2 * math.sqrt(n) / (1 + n)
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi, eta = math.atan2(t, math.cos(lam)), math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    x = eta + sum(al[j] * math.cos(2 * (j + 1) * xi) * math.sinh(2 * (j + 1) * eta) for j in range(3))
    y = xi + sum(al[j] * math.sin(2 * (j + 1) * xi) * math.cosh(2 * (j + 1) * eta) for j in range(3))
    E = 500000 + _K0 * A * x
    N = _K0 * A * y + (10000000 if south else 0)
    return E, N, zone, south


# ================================================================ sistem koordinat proyek
def crs(s: O.Store) -> dict:
    """{"zone": int|None, "south": bool|None} — None = otomatis dari bujur / lintang foto."""
    with s.conn() as c:
        r = c.execute("SELECT value FROM meta WHERE key='crs'").fetchone()
    try:
        d = json.loads(r[0]) if r else {}
    except ValueError:
        d = {}
    return {"zone": d.get("zone"), "south": d.get("south")}


def crs_label(cr: dict) -> str:
    return f"UTM {cr['zone']}{'S' if cr['south'] else 'N'} (WGS84)" if cr.get("zone") else "UTM otomatis dari bujur (WGS84)"


def save_crs(s: O.Store, zone: Optional[int], south: Optional[bool], by: str) -> dict:
    if zone is not None and not 1 <= int(zone) <= 60:
        raise ValueError("Zona UTM harus 1–60.")
    val = {"zone": int(zone) if zone else None, "south": bool(south) if zone else None}
    with s.lock, s.conn() as c:
        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('crs', ?)", (json.dumps(val),))
        c.execute("INSERT INTO history (photo_id, what, old, new, src, by, at) VALUES (?,?,?,?,?,?,?)",
                  (None, "sistem koordinat proyek", None, crs_label(val), "edit", by, core_io.now()))
    return val


# ================================================================ lokasi kamera per foto
def _exif_of(s: O.Store, r: dict) -> dict:
    """EXIF tersimpan (kolom exif_json), dibaca sekali dari salinan foto di proyek bila belum ada."""
    _ensure_col(s)
    with s.conn() as c:
        v = c.execute("SELECT exif_json FROM photos WHERE id=?", (r["id"],)).fetchone()[0]
    if v is not None:
        try:
            return json.loads(v)
        except ValueError:
            pass
    ex = read_exif(s.photos / r["file"])
    with s.lock, s.conn() as c:
        c.execute("UPDATE photos SET exif_json=? WHERE id=?", (json.dumps(ex), r["id"]))
    return ex


def _ensure_col(s: O.Store) -> None:
    if getattr(s, "_exif_ok", False):
        return
    with s.lock, s.conn() as c:
        if "exif_json" not in {x[1] for x in c.execute("PRAGMA table_info(photos)")}:
            c.execute("ALTER TABLE photos ADD COLUMN exif_json TEXT")
    s._exif_ok = True


def on_add(s: O.Store, pid: int) -> None:
    """Dipanggil sesudah + Foto: simpan EXIF, isi tanggal foto dari waktu pengambilan bila kosong / format kamera mentah."""
    r = O.photo(s, pid)
    ex = _exif_of(s, r)
    if ex.get("taken") and (not r.get("taken") or re.match(r"^\d{4}:\d{2}:\d{2}", r.get("taken") or "")):
        with s.lock, s.conn() as c:
            c.execute("UPDATE photos SET taken=? WHERE id=?", (ex["taken"], pid))
    k = drone_kind(ex)
    if k and not (r.get("desc") or {}).get("photo_type"):
        desc = dict(r.get("desc") or {}, photo_type=k)
        with s.lock, s.conn() as c:  # isian otomatis (bukan suntingan geologist), AI / geologist boleh mengubah
            c.execute("UPDATE photos SET desc_json=? WHERE id=?", (json.dumps(desc, ensure_ascii=False), pid))


def _collars(folder: str) -> list[dict]:
    from . import core_dh
    try:
        p = core_io.get_project(folder)
        core_dh.ensure(p)
        with p.conn() as c:
            return [{"hole": h, "x": x, "y": y, "z": z} for h, x, y, z in c.execute("SELECT hole, x, y, z FROM dh_collar")
                    if x is not None and y is not None]
    except Exception:  # noqa: BLE001  proyek tanpa data bor
        return []


def camera(s: O.Store, r: dict, cr: Optional[dict] = None, cols: Optional[list] = None, folder: str = "") -> Optional[dict]:
    """Posisi kamera foto dalam sistem koordinat proyek, atau None bila foto tanpa GPS."""
    ex = _exif_of(s, r)
    if ex.get("lat") is None:
        return None
    cr = cr or crs(s)
    E, N, z, south = to_utm(ex["lat"], ex["lon"], cr.get("zone"), cr.get("south") if cr.get("zone") else None)
    cam = {"e": round(E, 2), "n": round(N, 2), "rl": ex.get("alt"), "hacc": ex.get("hacc"), "heading": ex.get("heading"),
           "heading_ref": ex.get("heading_ref"), "zone": f"{z}{'S' if south else 'N'}", "taken": ex.get("taken"), "tz": ex.get("tz"),
           "camera": ex.get("camera"), "f35": ex.get("f35"), "warn": []}
    dj = ex.get("drone")
    if dj:
        cam["drone"] = dj
        if dj.get("rtk_flag") is not None:
            cam["rtk"] = {50: "RTK fix", 34: "RTK float", 16: "GPS tunggal"}.get(int(dj["rtk_flag"]), f"status {int(dj['rtk_flag'])}")
        if dj.get("rtk_flag") != 50:
            cam["warn"].append("Posisi drone tanpa RTK fix: ±1–5 m (GPS biasa).")
    if utm_zone(ex["lon"]) != z:
        cam["warn"].append(f"Foto berada di zona UTM {utm_zone(ex['lon'])}, dihitung di zona proyek {z} (distorsi sedikit lebih besar).")
    if cam["hacc"] and cam["hacc"] > 15:
        cam["warn"].append(f"Ketelitian GPS rendah (±{cam['hacc']:g} m) — sinyal terhalang dinding pit?")
    if cam["heading_ref"] == "magnetik":
        cam["warn"].append("Arah hadap memakai utara magnetik (bukan utara sejati).")
    cols = _collars(folder or str(s.root.parents[1])) if cols is None else cols
    if cols:
        d, h = min((math.hypot(c["x"] - E, c["y"] - N), c["hole"]) for c in cols)
        cam["nearest"] = {"hole": h, "dist": round(d, 1)}
        if d > 20000:
            cam["warn"].append(f"Collar terdekat {h} berjarak {d / 1000:,.0f} km: collar mungkin memakai grid lokal / sistem koordinat lain.")
    sol = O.georef_solve(r.get("georef"), r["w"], r["h"], O.plane_kind(r))
    if sol and sol.get("ok"):
        c = sol["c"]
        dg = math.hypot(c[0] - E, c[1] - N)
        cam["georef_dist"] = round(dg, 1)
        if dg > max(150.0, 5 * (cam["hacc"] or 10)):
            cam["warn"].append(f"Kamera {dg:,.0f} m dari bidang georef: titik georef / foto mungkin tertukar.")
    return cam


def compass(cam: Optional[dict], kind: str) -> Optional[dict]:
    """Kompas infografis dari arah hadap kamera (bila tanpa georef): dinding = huruf arah pandang, lantai = panah utara."""
    if not cam or cam.get("heading") is None:
        return None
    if kind == "floor":
        return {"mode": "north", "rot": -cam["heading"]}
    return {"mode": "view", "az": cam["heading"]}


def locations(s: O.Store, folder: str = "") -> dict:
    cr = crs(s)
    cols = _collars(folder or str(s.root.parents[1]))
    rows = []
    for r in O.photos(s):
        cam = camera(s, r, cr, cols)
        rows.append({"id": r["id"], "title": r.get("title") or r["file"], "file": r["file"], "taken": r.get("taken"), "cam": cam})
    return {"crs": cr, "label": crs_label(cr), "photos": rows, "n_gps": sum(1 for x in rows if x["cam"]), "collars": len(cols)}


def map_png(s: O.Store, sel: Optional[int] = None, folder: str = "") -> Optional[str]:
    """Peta denah posisi kamera (segitiga + arah hadap + lingkaran ketelitian) dan collar bor di sekitarnya."""
    loc = locations(s, folder)
    pts = [x for x in loc["photos"] if x["cam"]]
    if not pts:
        return None
    from .core_qaqc import _CHART_LOCK, _plt
    xs = [x["cam"]["e"] for x in pts]
    ys = [x["cam"]["n"] for x in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 60.0)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    half = span * 0.65
    cols = [c for c in _collars(folder or str(s.root.parents[1])) if abs(c["x"] - cx) < half * 1.2 and abs(c["y"] - cy) < half * 1.2]
    with _CHART_LOCK:
        plt = _plt()
        fig, ax = plt.subplots(figsize=(6.4, 5.2))
        ar = span * 0.08
        for c in cols:
            ax.plot(c["x"], c["y"], "o", color="#141a26", ms=3.5)
            ax.annotate(c["hole"], (c["x"], c["y"]), xytext=(3, 3), textcoords="offset points", fontsize=6, color="#3d4654")
        for x in pts:
            k = x["cam"]
            on = x["id"] == sel
            col = "#C0392B" if on else "#1c7ed6"
            if k.get("hacc"):
                ax.add_patch(plt.Circle((k["e"], k["n"]), k["hacc"], color=col, alpha=0.10, lw=0))
            ax.plot(k["e"], k["n"], "^", color=col, ms=9 if on else 7, mec="white", mew=0.8, zorder=5)
            if k.get("heading") is not None:
                t = math.radians(k["heading"])
                ax.annotate("", xy=(k["e"] + ar * math.sin(t), k["n"] + ar * math.cos(t)), xytext=(k["e"], k["n"]),
                            arrowprops={"arrowstyle": "-|>", "color": col, "lw": 1.6}, zorder=4)
            ax.annotate(x["title"], (k["e"], k["n"]), xytext=(5, -10), textcoords="offset points", fontsize=7,
                        color=col, fontweight="bold" if on else "normal")
        ax.set_xlim(cx - half, cx + half)
        ax.set_ylim(cy - half, cy + half)
        ax.set_aspect("equal")
        ax.ticklabel_format(useOffset=False, style="plain")
        ax.tick_params(labelsize=6.5)
        ax.set_xlabel("Easting (m)", fontsize=7.5)
        ax.set_ylabel("Northing (m)", fontsize=7.5)
        ax.grid(alpha=0.25)
        ax.annotate("U", xy=(0.95, 0.95), xycoords="axes fraction", ha="center", fontsize=9, fontweight="bold")
        ax.annotate("", xy=(0.95, 0.93), xytext=(0.95, 0.84), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": "#141a26"})
        ax.set_title(f"Posisi kamera (GPS HP) · {loc['label']}" + (f" · {len(cols)} collar" if cols else ""), fontsize=8.5)
        b = io.BytesIO()
        fig.savefig(b, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    return base64.b64encode(b.getvalue()).decode()


# ================================================================ API
class FBody(BaseModel):
    folder: str
    by: str = ""


class PidBody(FBody):
    id: int


class CrsBody(FBody):
    zone: Optional[int] = None
    south: Optional[bool] = None


class MapBody(FBody):
    sel: Optional[int] = None


@router.post("/photo")
def api_photo(b: PidBody) -> dict:
    s = O.store(b.folder)
    r = O.photo(s, b.id)
    cr = crs(s)
    return {"ok": True, "cam": camera(s, r, cr, folder=b.folder), "crs": cr, "label": crs_label(cr)}


@router.post("/list")
def api_list(b: FBody) -> dict:
    return {"ok": True, **locations(O.store(b.folder), b.folder)}


@router.post("/map")
def api_map(b: MapBody) -> dict:
    s = O.store(b.folder)
    return {"ok": True, "png": map_png(s, b.sel, b.folder), **locations(s, b.folder)}


@router.post("/crs")
def api_crs(b: CrsBody) -> dict:
    s = O.store(b.folder)
    cr = save_crs(s, b.zone, b.south, b.by)
    return {"ok": True, "crs": cr, "label": crs_label(cr)}
