"""Block model Surpac .mdl (Version 4.0, biner big-endian, octree) untuk file sangat besar.

Alur:
1. build_cache(): file .mdl dibaca SEKALI dari awal sampai akhir (per potongan 64 MB, tervektorisasi numpy)
   lalu disimpan sebagai kolom-kolom biner di folder cache + indeks urut RL (z).
2. subset(): blok yang beririsan rentang RL (dan kotak XY opsional) diambil dari cache dalam hitungan detik,
   lalu ditulis ulang sebagai file .mdl mini yang sah (header asli + record terpilih + penanda akhir).
   GC-Ex membaca .mdl mini itu dengan pembaca yang sama seperti biasa, sehingga hasilnya identik
   (atribut kalkulasi IIF, kategori, filter pit/topografi, ekspor .mdl tetap dikerjakan oleh GC-Ex).

Format record (sama dengan pembaca GC-Ex): kunci octree 2 x uint32 (hi, lo), lalu tiap atribut tersimpan:
float64 (tipe 2/4/5), int32 (tipe 1), int32 kode kategori (tipe 3; negatif = kemunculan pertama, diikuti teks
latin-1 berakhiran 0). Penanda akhir: FF FF FF E0 FF FF FF FF.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

CACHE_VER = 1
CHUNK = 64 * 1048576
END_MARK = bytes([255, 255, 255, 224, 255, 255, 255, 255])


# ---------------------------------------------------------------- header
def read_header(path: str | Path) -> dict:
    p = Path(path)
    N = p.stat().st_size
    ln = min(N, 1048576)
    while True:
        with open(p, "rb") as fh:
            u = fh.read(ln)
        try:
            return _parse_head(u, N, p.name)
        except _More:
            if ln >= N:
                raise ValueError(f"{p.name}: header .mdl terpotong.")
            ln = min(N, ln * 8)


class _More(Exception):
    pass


def _parse_head(u: bytes, N: int, fname: str) -> dict:
    L = len(u)

    def need(p, n):
        if p + n > L:
            raise _More()

    def cstr(p):
        e = u.find(b"\0", p)
        if e < 0:
            raise _More()
        return u[p:e].decode("latin1"), e + 1

    if u[:19].decode("latin1") != "### Block Model ###":
        raise ValueError(f"{fname}: bukan file block model Surpac (.mdl).")
    p = u.index(b"\n", 0) + 1
    p = u.index(b"\n", p) + 1
    ver = u[20:p - 1].decode("latin1")
    if "Version" not in ver or "4" not in ver:
        raise ValueError(f"{fname}: versi {ver} belum didukung (yang didukung: Version 4.0).")
    if u[p] == 0:
        p += 1
    nm0 = p
    nm, p = cstr(p)
    nmB = p - 1
    p += 1
    need(p, 12 + 72 + 8)
    p += 12
    D = struct.unpack(">9d", u[p:p + 72])
    p += 72
    rot, na = struct.unpack(">ii", u[p:p + 8])
    p += 8
    if not (0 < na < 500):
        raise ValueError(f"Header .mdl tidak dikenali (jumlah atribut {na}).")
    attrs = []
    for _ in range(na):
        name, p = cstr(p)
        need(p, 12)
        calc = struct.unpack(">i", u[p:p + 4])[0]
        p += 8
        a: dict[str, Any] = {"name": name, "calc": calc == 1}
        if a["calc"]:
            a["expr"], p = cstr(p)
        else:
            need(p, 4)
            ty = struct.unpack(">i", u[p:p + 4])[0]
            p += 4
            a["type"] = ty
            need(p, 16)
            # Sesudah nilai bawaan selalu ada TEKS DESKRIPSI atribut berakhiran 0 (kolom Description Surpac; kosong = satu
            # byte 0). Dulu dilompati satu byte saja, sehingga atribut berdeskripsi (mis. sg3 = "density") menggeser
            # pembacaan: 'Tipe atribut "" (24940) belum didukung' (12 Nov 2026; padanan web-src/mdlattr.js 'd8' / 'ds').
            if ty in (2, 4, 5):
                a["def"] = struct.unpack(">d", u[p:p + 8])[0]
                a["desc"], p = cstr(p + 8)
            elif ty == 3:
                a["def"], p = cstr(p)
                a["desc"], p = cstr(p)
            elif ty == 1:
                a["def"] = struct.unpack(">i", u[p:p + 4])[0]
                a["desc"], p = cstr(p + 4)
            else:
                raise ValueError(f'Tipe atribut "{name}" ({ty}) belum didukung.')
        attrs.append(a)
    p += 4
    need(p, 0)
    stored = [a for a in attrs if not a["calc"]]
    return {"name": nm[:-4] if nm.lower().endswith(".mdl") else nm, "fname": fname, "N": N,
            "origin": list(D[0:3]), "root": list(D[3:6]), "extent": list(D[6:9]), "rot": rot,
            "attrs": attrs, "stored": stored, "data": p, "hraw": u[:p], "nmA": nm0, "nmB": nmB}


def _dtype(stored: list[dict], endian: str = ">") -> np.dtype:
    f = [("hi", endian + "u4"), ("lo", endian + "u4")]
    for k, a in enumerate(stored):
        f.append((f"f{k}", endian + ("i4" if a["type"] in (1, 3) else "f8")))
    return np.dtype(f)


# ---------------------------------------------------------------- lokasi cache
def _cache_base() -> Path:
    r = os.environ.get("GCEX_CACHE")
    if not r:
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache")
        r = os.path.join(base, "GC-Ex", "cache")
    return Path(r)


def _cache_cfg() -> Path:
    """Pilihan folder cache pengguna (GC-Ex 14 Nov 2026: cache 10,7 GB tidak muat di C:). Disimpan di folder bawaan."""
    return _cache_base() / "cache_root.txt"


def cache_root() -> Path:
    r = _cache_base()
    try:
        cf = _cache_cfg()
        if cf.exists():
            c = cf.read_text(encoding="utf-8").strip()
            if c:
                r = Path(c)
    except OSError:
        pass
    p = Path(r) / ("mdl" if Path(r) == _cache_base() else CUSTOM_SUB)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError:  # drive pilihan tidak tersedia (mis. flashdisk dicabut) -> kembali ke bawaan
        p = _cache_base() / "mdl"
        p.mkdir(parents=True, exist_ok=True)
    return p


# folder pilihan pengguna (mis. D:\\) memakai subfolder khusus, supaya "Hapus cache" tidak pernah menyentuh folder lain
CUSTOM_SUB = "GC-Ex_cache_mdl"


def _is_cache_dir(d: Path) -> bool:
    return d.is_dir() and ((d / "meta.json").exists() or d.name.endswith(".tmp"))


def _dir_bytes(d: Path) -> int:
    n = 0
    for f in d.rglob("*"):
        try:
            if f.is_file():
                n += f.stat().st_size
        except OSError:
            pass
    return n


def cache_info() -> dict:
    root = cache_root()
    items = cache_list()
    try:
        free = shutil.disk_usage(root).free
    except OSError:
        free = None
    return {"root": str(root), "default": str(_cache_base() / "mdl"), "custom": root.name == CUSTOM_SUB,
            "items": items, "used": _dir_bytes(root), "free": free}


def set_cache_root(path: Optional[str], hapus_lama: bool = False) -> dict:
    """Ganti folder cache (None/'' = kembali ke bawaan). Folder diuji bisa ditulis; cache di folder lama dihapus bila diminta."""
    old = cache_root()
    if path:
        base = Path(path)
        if base.name == CUSTOM_SUB:
            base = base.parent
        tgt = base / CUSTOM_SUB
        try:
            tgt.mkdir(parents=True, exist_ok=True)
            t = tgt / ".uji_tulis"
            t.write_text("ok")
            t.unlink()
        except OSError as e:
            raise ValueError(f"Folder tidak bisa dipakai untuk cache: {base} ({e})")
        cf = _cache_cfg()
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_text(str(base), encoding="utf-8")
    else:
        try:
            _cache_cfg().unlink()
        except OSError:
            pass
    new = cache_root()
    removed = 0
    if hapus_lama and old.resolve() != new.resolve() and old.exists():
        for d in old.iterdir():
            if _is_cache_dir(d):
                shutil.rmtree(d, ignore_errors=True)
                removed += 1
    return {**cache_info(), "removed_old": removed}


def cache_key(path: str | Path) -> str:
    p = Path(path).resolve()
    st = p.stat()
    h = hashlib.sha1(f"{str(p).lower()}|{st.st_size}|{int(st.st_mtime)}|v{CACHE_VER}".encode("utf-8")).hexdigest()[:16]
    return f"{p.stem[:40]}_{h}"


def cache_dir(path: str | Path) -> Path:
    return cache_root() / cache_key(path)


def _meta(cd: Path) -> Optional[dict]:
    m = cd / "meta.json"
    if not m.exists():
        return None
    try:
        j = json.loads(m.read_text(encoding="utf-8"))
        return j if j.get("ver") == CACHE_VER and j.get("complete") else None
    except Exception:
        return None


# ---------------------------------------------------------------- baca seluruh file -> cache
def build_cache(path: str | Path, prog: Optional[Callable[[float, int], None]] = None,
                cancel: Optional[Callable[[], bool]] = None) -> dict:
    p = Path(path).resolve()
    H = read_header(p)
    if H["rot"]:
        pass  # sama dengan GC-Ex: rotasi belum diterapkan (dicatat di meta)
    cd = cache_dir(p)
    old = _meta(cd)
    if old:
        return old
    N = H["N"]
    free = shutil.disk_usage(cache_root()).free
    # cache per blok: hi, lo, x, y, z, lv (33 B) + kolom atribut + indeks RL (zord 4-8 B + zs 8 B)
    fb = sum(4 if a["type"] in (1, 3) else 8 for a in H["stored"])
    n_est = max(0, N - H["data"]) / (8 + fb)
    need = n_est * (33 + fb + 16) * 1.02 + 200e6
    if free < need:
        raise RuntimeError(f"Ruang disk untuk cache block model tidak cukup: butuh ±{need / 1e9:.1f} GB, "
                           f"tersedia {free / 1e9:.1f} GB di {cache_root()}. Kosongkan ruang atau hapus cache lama.")
    tmp = cd.with_name(cd.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    ST = H["stored"]
    dt = _dtype(ST)
    R = dt.itemsize
    cat_k = [k for k, a in enumerate(ST) if a["type"] == 3]
    O = np.array(H["origin"])
    RT = np.array(H["root"])
    LV = np.array([[RT[0] * 2.0 ** -l, RT[1] * 2.0 ** -l, RT[2] * 2.0 ** -l] for l in range(32)])
    files = {n: open(tmp / f"{n}.bin", "wb") for n in ["hi", "lo", "x", "y", "z", "lv"] + [f"f{k}" for k in range(len(ST))]}
    dicts: dict[int, dict[int, str]] = {k: {} for k in cat_k}
    n_tot = 0
    max_l = 0
    min_l = 31
    zmin, zmax = np.inf, -np.inf
    t0 = time.time()

    def emit(arr: np.ndarray):
        nonlocal n_tot, max_l, min_l, zmin, zmax
        if not len(arr):
            return
        hi = arr["hi"].astype(np.uint32)
        lo = arr["lo"].astype(np.uint32)
        fl = hi & 0x3FFF
        lv = (fl & 31).astype(np.int64)
        dg = (fl >> 5).astype(np.uint32)
        ix = (hi >> 14).astype(np.uint32)
        x = np.zeros(len(arr))
        y = np.zeros(len(arr))
        z = np.zeros(len(arr))
        ml = int(lv.max()) if len(lv) else 0
        for l in range(1, ml + 1):
            if l <= 3:
                d = (dg >> (3 * (l - 1))) & 7
            elif l <= 9:
                d = (ix >> (3 * (l - 4))) & 7
            else:
                d = (lo >> (3 * (l - 10))) & 7
            on = lv >= l
            x = np.where(on & ((d & 4) > 0), x + LV[l, 0], x)
            y = np.where(on & ((d & 2) > 0), y + LV[l, 1], y)
            z = np.where(on & ((d & 1) > 0), z + LV[l, 2], z)
        cx = O[0] + x + LV[lv, 0] / 2
        cy = O[1] + y + LV[lv, 1] / 2
        cz = O[2] + z + LV[lv, 2] / 2
        hi.astype("<u4").tofile(files["hi"])
        lo.astype("<u4").tofile(files["lo"])
        cx.astype("<f8").tofile(files["x"])
        cy.astype("<f8").tofile(files["y"])
        cz.astype("<f8").tofile(files["z"])
        lv.astype(np.uint8).tofile(files["lv"])
        for k, a in enumerate(ST):
            arr[f"f{k}"].astype("<i4" if a["type"] in (1, 3) else "<f8").tofile(files[f"f{k}"])
        n_tot += len(arr)
        max_l = max(max_l, ml)
        min_l = min(min_l, int(lv.min()))
        zmin = min(zmin, float(cz.min()))
        zmax = max(zmax, float(cz.max()))

    done = False
    tail_at = None
    with open(p, "rb") as fh:
        fh.seek(H["data"])
        off = H["data"]
        buf = b""
        while not done:
            if cancel and cancel():
                raise RuntimeError("Pembacaan dibatalkan.")
            chunk = fh.read(CHUNK)
            eof = not chunk
            buf = buf + chunk if buf else chunk
            pos = 0
            L = len(buf)
            while True:
                if L - pos >= 8 and buf[pos + 4] == 255 and buf[pos + 5] == 255 and \
                        struct.unpack_from(">I", buf, pos)[0] >= 0xFFFFFF00:
                    done = True
                    tail_at = off + pos + 8
                    break
                n = (L - pos) // R
                if n <= 0:
                    break
                a = np.frombuffer(buf, dtype=dt, count=n, offset=pos)
                hi = a["hi"]
                bad = (hi >= 0xFFFFFF00) & ((a["lo"] >> 16) == 0xFFFF)
                for k in cat_k:
                    bad |= a[f"f{k}"] < 0
                j = int(np.argmax(bad)) if bad.any() else n
                emit(a[:j])
                pos += j * R
                if j == n:
                    break
                # record khusus di posisi pos: penanda akhir atau kategori baru (teks mengikuti kodenya)
                h0, l0 = struct.unpack_from(">II", buf, pos)
                if buf[pos + 4] == 255 and buf[pos + 5] == 255 and h0 >= 0xFFFFFF00:
                    done = True
                    tail_at = off + pos + 8
                    break
                q = pos + 8
                vals = []
                ok = True
                for k, at in enumerate(ST):
                    if at["type"] in (1, 3):
                        if q + 4 > L:
                            ok = False
                            break
                        c = struct.unpack_from(">i", buf, q)[0]
                        q += 4
                        if at["type"] == 3 and c < 0:
                            e = buf.find(b"\0", q)
                            if e < 0:
                                ok = False
                                break
                            dicts[k][-c] = buf[q:e].decode("latin1")
                            q = e + 1
                            c = -c
                        vals.append(c)
                    else:
                        if q + 8 > L:
                            ok = False
                            break
                        vals.append(struct.unpack_from(">d", buf, q)[0])
                        q += 8
                if not ok:
                    break  # record terpotong: butuh potongan berikutnya
                one = np.zeros(1, dtype=dt)
                one["hi"], one["lo"] = h0, l0
                for k, v in enumerate(vals):
                    one[f"f{k}"] = v
                emit(one)
                pos = q
            off += pos
            buf = buf[pos:]
            if prog:
                prog(min(99.0, off / N * 100), n_tot)
            if eof:
                if not done and len(buf) >= 8:
                    raise ValueError("File .mdl terpotong atau rusak di akhir file.")
                break
    for f in files.values():
        f.close()
    # indeks urut RL (di luar RAM: memori tetap kecil walau model berisi ratusan juta blok)
    od = np.int64 if n_tot >= 2 ** 31 else np.int32
    if prog:
        prog(99.0, n_tot)
    _zsort(tmp, n_tot, zmin, zmax, RT[2] * 2.0 ** -(max_l + 1), od, cancel)
    (tmp / "head.bin").write_bytes(H["hraw"])
    # metadata Surpac setelah penanda akhir (disandikan); disalin apa adanya ke setiap potongan
    with open(p, "rb") as fh:
        fh.seek(tail_at if tail_at is not None else N)
        (tmp / "tail.bin").write_bytes(fh.read())
    meta = {"ver": CACHE_VER, "complete": True, "file": str(p), "fname": H["fname"], "size": N,
            "mtime": int(p.stat().st_mtime), "n": int(n_tot), "maxL": int(max_l), "minL": int(min_l if n_tot else 0),
            "zmin": zmin if n_tot else None, "zmax": zmax if n_tot else None,
            "origin": H["origin"], "root": H["root"], "extent": H["extent"], "rot": H["rot"],
            "attrs": [{k: v for k, v in a.items()} for a in H["attrs"]],
            "stored": [{"name": a["name"], "type": a["type"]} for a in ST],
            "dicts": {str(k): {str(c): s for c, s in d.items()} for k, d in dicts.items()},
            "ord_dtype": np.dtype(od).name, "build_s": round(time.time() - t0, 1), "data": H["data"]}
    (tmp / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    if cd.exists():
        shutil.rmtree(cd, ignore_errors=True)
    os.replace(tmp, cd)
    _touch(cd)
    prune_cache(keep=3, protect=cd)
    if prog:
        prog(100.0, n_tot)
    return meta


ZS_STEP = 8_000_000


def _zsort(tmp: Path, n: int, zmin: float, zmax: float, dq: float, od, cancel=None):
    """Tulis zord.bin (indeks blok urut RL, stabil) dan zs.bin (RL terurut) tanpa memuat seluruh kolom ke RAM.
    Titik tengah blok octree selalu di kisi dq = setengah ukuran sub-blok terkecil -> counting sort per kunci RL,
    dikerjakan per potongan ZS_STEP blok. Bila kisi tidak cocok (data aneh), kembali ke argsort biasa."""
    if not n:
        np.zeros(0, od).tofile(tmp / "zord.bin")
        np.zeros(0, "<f8").tofile(tmp / "zs.bin")
        return
    zm = np.memmap(tmp / "z.bin", dtype="<f8", mode="r", shape=(n,))
    nk = int(round((zmax - zmin) / dq)) + 1 if dq > 0 else 0
    ok = 0 < nk <= 20_000_000
    if ok:
        cnt = np.zeros(nk, np.int64)
        for s0 in range(0, n, ZS_STEP):
            if cancel and cancel():
                raise RuntimeError("Pembacaan dibatalkan.")
            zc = np.asarray(zm[s0:s0 + ZS_STEP])
            k = np.rint((zc - zmin) / dq).astype(np.int64)
            if np.any(np.abs(zc - (zmin + k * dq)) > 1e-6):
                ok = False  # RL tidak di kisi sub-blok -> argsort biasa
                break
            np.clip(k, 0, nk - 1, out=k)
            cnt += np.bincount(k, minlength=nk)
    if ok:
        ptr = np.zeros(nk, np.int64)
        np.cumsum(cnt[:-1], out=ptr[1:])
        del cnt
        om = np.memmap(tmp / "zord.bin", dtype=od, mode="w+", shape=(n,))
        zo = np.memmap(tmp / "zs.bin", dtype="<f8", mode="w+", shape=(n,))
        for s0 in range(0, n, ZS_STEP):
            if cancel and cancel():
                raise RuntimeError("Pembacaan dibatalkan.")
            zc = np.asarray(zm[s0:s0 + ZS_STEP])
            k = np.rint((zc - zmin) / dq).astype(np.int64)
            np.clip(k, 0, nk - 1, out=k)
            o = np.argsort(k, kind="stable")
            sk = k[o]
            c = np.bincount(sk, minlength=nk)
            first = np.zeros(nk, np.int64)
            np.cumsum(c[:-1], out=first[1:])
            pos = ptr[sk] + (np.arange(len(sk), dtype=np.int64) - first[sk])
            om[pos] = (o + s0).astype(od)
            zo[pos] = zc[o]
            ptr += c
        om.flush()
        zo.flush()
        # periksa urutan (kisi RL tidak cocok -> beberapa RL berbeda bisa jatuh ke kunci yang sama)
        last = -np.inf
        for s0 in range(0, n, ZS_STEP):
            a = np.asarray(zo[s0:s0 + ZS_STEP])
            if a[0] < last or (len(a) > 1 and bool(np.any(a[1:] < a[:-1]))):
                ok = False
                break
            last = a[-1]
        for mm in (om, zo):  # Windows: file yang masih dipetakan tidak bisa ditulis ulang
            try:
                mm._mmap.close()
            except Exception:
                pass
        del om, zo
    if not ok:
        zz = np.asarray(zm)
        order = np.argsort(zz, kind="stable").astype(od)
        order.tofile(tmp / "zord.bin")
        zz[order].tofile(tmp / "zs.bin")
        del zz, order
    del zm


def fit_window(c: "_Cache", z_min: Optional[float], z_max: Optional[float], max_n: Optional[int]):
    """Batas jumlah blok per pemuatan (RAM / VRAM komputer pengguna). Bila rentang RL yang diminta berisi lebih dari
    max_n blok, rentang dipersempit dari ATAS (RL tertinggi dulu, bench aktif biasanya di atas) dan dibulatkan ke kisi
    sub-blok terkecil. Hasil: (z_min, z_max, dipersempit?, perkiraan blok di rentang asli)."""
    if not c.n:
        return z_min, z_max, False, 0
    m = c.m
    hz = c.hz
    zs = c.col("zs", "<f8")
    lo = 0 if z_min is None else int(np.searchsorted(zs, z_min - hz - 1e-9, "left"))
    hi = c.n if z_max is None else int(np.searchsorted(zs, z_max + hz + 1e-9, "right"))
    tot = max(0, hi - lo)
    if not max_n or tot <= max_n:
        return z_min, z_max, False, tot
    dz = m["root"][2] * 2.0 ** -max(1, m["maxL"])
    oz = m["origin"][2]
    top = z_max if z_max is not None else float(m["zmax"]) + dz / 2
    zt = float(zs[hi - max_n]) + hz + 1e-6
    zn = oz + np.ceil((zt - oz) / dz) * dz
    if zn >= top:
        zn = top - dz
    zn = float(round(zn, 6))
    return zn, (z_max if z_max is not None else None), True, tot


def _touch(cd: Path):
    try:
        (cd / "last_used").write_text(str(time.time()))
    except OSError:
        pass


def prune_cache(keep: int = 3, protect: Optional[Path] = None) -> list[str]:
    """Simpan `keep` cache yang paling baru dipakai, hapus sisanya (dan sisa build yang gagal)."""
    root = cache_root()
    items = []
    removed = []
    for d in root.iterdir():
        if not d.is_dir():
            continue
        if d.name.endswith(".tmp") and time.time() - d.stat().st_mtime > 3600:
            shutil.rmtree(d, ignore_errors=True)
            removed.append(d.name)
            continue
        lu = d / "last_used"
        t = float(lu.read_text()) if lu.exists() else d.stat().st_mtime
        items.append((t, d))
    items.sort(reverse=True)
    for t, d in items[keep:]:
        if protect and d == protect:
            continue
        shutil.rmtree(d, ignore_errors=True)
        removed.append(d.name)
    return removed


def cache_list() -> list[dict]:
    out = []
    for d in cache_root().iterdir():
        m = _meta(d) if d.is_dir() else None
        if m:
            sz = sum(f.stat().st_size for f in d.iterdir() if f.is_file())
            out.append({"key": d.name, "file": m["file"], "n": m["n"], "bytes": sz})
    return out


def clear_cache() -> int:
    n = 0
    for d in cache_root().iterdir():
        if _is_cache_dir(d):
            shutil.rmtree(d, ignore_errors=True)
            n += 1
    return n


# ---------------------------------------------------------------- ambil potongan -> .mdl mini
class _Cache:
    def __init__(self, cd: Path, meta: dict):
        self.cd, self.m = cd, meta
        n = meta["n"]
        self.n = n
        self.ST = meta["stored"]
        self._hz = None

    @property
    def hz(self) -> float:
        """Setengah tinggi blok TERBESAR yang ada di model (bukan blok akar): batas cari indeks RL tetap sempit."""
        if self._hz is None:
            ml = self.m.get("minL")
            if ml is None:  # cache versi lama: hitung sekali dari kolom level
                ml, lv = 31, self.col("lv", "u1")
                for s0 in range(0, self.n, 50_000_000):
                    ml = min(ml, int(np.asarray(lv[s0:s0 + 50_000_000]).min()))
                if not self.n:
                    ml = 0
                self.m["minL"] = ml
                try:
                    (self.cd / "meta.json").write_text(json.dumps(self.m), encoding="utf-8")
                except OSError:
                    pass
            self._hz = self.m["root"][2] * 2.0 ** -int(ml) / 2
        return self._hz

    def col(self, name: str, dtype: str):
        return np.memmap(self.cd / f"{name}.bin", dtype=dtype, mode="r", shape=(self.n,)) if self.n else np.zeros(0, dtype)


def open_cache(path: str | Path) -> tuple[_Cache, dict]:
    cd = cache_dir(path)
    m = _meta(cd)
    if not m:
        raise RuntimeError("Cache block model belum ada; panggil /mdl/open dulu.")
    _touch(cd)
    return _Cache(cd, m), m


def select(c: _Cache, z_min: Optional[float] = None, z_max: Optional[float] = None,
           bbox: Optional[list[float]] = None, center: bool = False) -> np.ndarray:
    """Indeks blok (urut seperti di file) yang beririsan rentang RL dan kotak XY [x0,x1,y0,y1].
    center=True: blok dipilih menurut TITIK TENGAH di dalam rentang (batas inklusif, seperti filter GC-Ex Drillhole);
    nilai None di bbox = tanpa batas di sisi itu."""
    m = c.m
    if not c.n:
        return np.zeros(0, np.int64)
    hzmax = c.hz
    zs = c.col("zs", "<f8")
    zord = c.col("zord", "<" + ("i8" if m["ord_dtype"] == "int64" else "i4"))
    lo = 0 if z_min is None else int(np.searchsorted(zs, z_min - hzmax - 1e-9, "left"))
    hi = c.n if z_max is None else int(np.searchsorted(zs, z_max + hzmax + 1e-9, "right"))
    idx = np.sort(np.asarray(zord[lo:hi], dtype=np.int64))
    if not len(idx):
        return idx
    if center:
        eps = 1e-6  # sedikit longgar: GC-Ex menyaring ulang dengan batas persisnya
        keep = np.ones(len(idx), bool)
        if z_min is not None or z_max is not None:
            z = np.asarray(c.col("z", "<f8")[idx])
            if z_min is not None:
                keep &= z >= z_min - eps
            if z_max is not None:
                keep &= z <= z_max + eps
        if bbox:
            b = [None if v is None else float(v) for v in (list(bbox) + [None] * 4)[:4]]
            if b[0] is not None or b[1] is not None:
                x = np.asarray(c.col("x", "<f8")[idx])
                if b[0] is not None:
                    keep &= x >= b[0] - eps
                if b[1] is not None:
                    keep &= x <= b[1] + eps
            if b[2] is not None or b[3] is not None:
                y = np.asarray(c.col("y", "<f8")[idx])
                if b[2] is not None:
                    keep &= y >= b[2] - eps
                if b[3] is not None:
                    keep &= y <= b[3] + eps
        return idx[keep]
    lv = np.asarray(c.col("lv", "u1")[idx], dtype=np.int64)
    RT = m["root"]
    keep = np.ones(len(idx), bool)
    if z_min is not None or z_max is not None:
        z = np.asarray(c.col("z", "<f8")[idx])
        hz = RT[2] * np.power(2.0, -lv) / 2
        if z_min is not None:
            keep &= ~(z + hz <= z_min)
        if z_max is not None:
            keep &= ~(z - hz >= z_max)
    if bbox:
        x = np.asarray(c.col("x", "<f8")[idx])
        y = np.asarray(c.col("y", "<f8")[idx])
        hx = RT[0] * np.power(2.0, -lv) / 2
        hy = RT[1] * np.power(2.0, -lv) / 2
        keep &= (x + hx > bbox[0]) & (x - hx < bbox[1]) & (y + hy > bbox[2]) & (y - hy < bbox[3])
    return idx[keep]


def write_subset(c: _Cache, idx: np.ndarray, out) -> int:
    """Tulis .mdl mini (header asli + record idx + penanda akhir) ke objek file `out`. Hasil: jumlah byte."""
    ST = c.ST
    dt = _dtype(ST)
    head = (c.cd / "head.bin").read_bytes()
    out.write(head)
    nb = len(head)
    dicts = {int(k): {int(cc): s for cc, s in d.items()} for k, d in c.m["dicts"].items()}
    step = 2_000_000
    seen: dict[int, set] = {k: set() for k in dicts}
    for s0 in range(0, len(idx), step):
        ii = idx[s0:s0 + step]
        rec = np.empty(len(ii), dtype=dt)
        rec["hi"] = c.col("hi", "<u4")[ii]
        rec["lo"] = c.col("lo", "<u4")[ii]
        for k, a in enumerate(ST):
            rec[f"f{k}"] = c.col(f"f{k}", "<i4" if a["type"] in (1, 3) else "<f8")[ii]
        # kemunculan pertama tiap kode kategori di potongan ini -> tulis teksnya (kode negatif + teks + \0)
        firsts: dict[int, list[int]] = {}
        for k in dicts:
            codes = rec[f"f{k}"]
            u, fi = np.unique(codes, return_index=True)
            for code, r in zip(u.tolist(), fi.tolist()):
                if code > 0 and code not in seen[k] and code in dicts[k]:
                    seen[k].add(code)
                    firsts.setdefault(r, []).append(k)
        cur = 0
        for r in sorted(firsts):
            if r > cur:
                b = rec[cur:r].tobytes()
                out.write(b)
                nb += len(b)
            one = rec[r]
            parts = [struct.pack(">II", int(one["hi"]), int(one["lo"]))]
            for k, a in enumerate(ST):
                v = one[f"f{k}"]
                if a["type"] == 3 and k in firsts[r]:
                    parts.append(struct.pack(">i", -int(v)) + dicts[k][int(v)].encode("latin1") + b"\0")
                elif a["type"] in (1, 3):
                    parts.append(struct.pack(">i", int(v)))
                else:
                    parts.append(struct.pack(">d", float(v)))
            b = b"".join(parts)
            out.write(b)
            nb += len(b)
            cur = r + 1
        if cur < len(rec):
            b = rec[cur:].tobytes()
            out.write(b)
            nb += len(b)
    out.write(END_MARK)
    tail = (c.cd / "tail.bin").read_bytes() if (c.cd / "tail.bin").exists() else b""
    out.write(tail)
    return nb + len(END_MARK) + len(tail)


# ---------------------------------------------------------------- pekerjaan latar (progress untuk GC-Ex)
_JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()


def open_model(path: str | Path) -> dict:
    """Status cache untuk file ini; bila belum ada, mulai membangun di latar belakang."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File block model tidak ditemukan: {p}")
    cd = cache_dir(p)
    m = _meta(cd)
    if m:
        _touch(cd)
        return {"state": "ready", "info": _info(m)}
    key = cd.name
    with _LOCK:
        j = _JOBS.get(key)
        if j and j["state"] == "error":
            _JOBS.pop(key, None)
            return {"state": "error", "error": j["error"]}
        if not j:
            j = {"state": "building", "pct": 0.0, "n": 0, "t0": time.time(), "size": p.stat().st_size, "cancel": False}
            _JOBS[key] = j

            def run():
                try:
                    build_cache(p, prog=lambda pc, n: j.update(pct=pc, n=n), cancel=lambda: j["cancel"])
                    j["state"] = "ready"
                except Exception as e:  # noqa: BLE001
                    j["state"], j["error"] = "error", str(e)

            threading.Thread(target=run, daemon=True).start()
    if j["state"] == "ready":
        with _LOCK:
            _JOBS.pop(key, None)
        return open_model(p)
    el = time.time() - j["t0"]
    return {"state": j["state"], "pct": round(j["pct"], 1), "n": j["n"], "elapsed": round(el, 1),
            "mbps": round(j["size"] * j["pct"] / 100 / 1048576 / el, 1) if el > 0 else None,
            "error": j.get("error")}


def cancel_build(path: str | Path) -> bool:
    j = _JOBS.get(cache_dir(path).name)
    if j:
        j["cancel"] = True
        return True
    return False


def _info(m: dict) -> dict:
    return {k: m[k] for k in ("file", "fname", "size", "n", "zmin", "zmax", "origin", "root", "extent", "maxL", "build_s")} | \
        {"attrs": [a["name"] for a in m["attrs"]]}


# ---------------------------------------------------------------- ringkasan seluruh model per RL (tanpa memuat ke GC-Ex)
def bench_summary(path: str | Path, bench: float, ref: float, attrs: list[str], sg_col: Optional[str] = None,
                  sg: float = 2.6, sg_zero: str = "rep", sg_rep: Optional[float] = None,
                  cut_attr: Optional[str] = None, cut: Optional[float] = None,
                  z_min: Optional[float] = None, z_max: Optional[float] = None) -> dict:
    """Tonase & kadar (rata-rata tertimbang ton) per flitch/bench untuk SELURUH model.
    Blok masuk bench menurut titik tengahnya: bench k = (ref + k*bench, ref + (k+1)*bench], sama dengan
    metode "Seperti Surpac" di GC-Ex (titik tengah di atas RL bawah dan tidak di atas RL atas).
    Aturan SG sama dengan GC-Ex: kolom SG bila > 0; bila <= 0 / kosong -> SG pengganti (atau 0 = seperti Surpac)."""
    c, m = open_cache(path)
    names = {a["name"]: k for k, a in enumerate(c.ST)}
    num = {a["name"]: k for k, a in enumerate(c.ST) if a["type"] in (1, 2, 4, 5)}
    miss = [a for a in attrs + ([cut_attr] if cut_attr else []) + ([sg_col] if sg_col else []) if a and a not in num]
    if miss:
        raise ValueError("Atribut tidak ada / bukan angka tersimpan di .mdl (atribut kalkulasi IIF belum didukung di ringkasan ini): " + ", ".join(miss))
    if not bench or bench <= 0:
        raise ValueError("Tinggi bench harus > 0.")
    RT = m["root"]
    rep = sg_rep if (sg_rep is not None and sg_rep > 0) else sg
    nb_out: dict[int, dict] = {}
    step = 5_000_000
    # seluruh model: baca kolom berurutan per potongan (tanpa larik indeks raksasa di RAM)
    idx_all = select(c, z_min, z_max) if (z_min is not None or z_max is not None) else None
    for s0 in range(0, c.n if idx_all is None else len(idx_all), step):
        ii = slice(s0, min(c.n, s0 + step)) if idx_all is None else idx_all[s0:s0 + step]
        lv = np.asarray(c.col("lv", "u1")[ii], dtype=np.int64)
        f = np.power(2.0, -lv)
        vol = RT[0] * RT[1] * RT[2] * f * f * f
        z = np.asarray(c.col("z", "<f8")[ii])
        if sg_col:
            s = np.asarray(c.col(f"f{names[sg_col]}", "<f8" if c.ST[names[sg_col]]["type"] != 1 else "<i4")[ii], dtype=np.float64)
            good = np.isfinite(s) & (s > 0)
            s = np.where(good, s, 0.0 if sg_zero == "zero" else rep)
        else:
            s = np.full(len(z), float(sg))
        t = vol * s
        keep = np.ones(len(z), bool)
        if cut_attr is not None and cut is not None:
            ca = np.asarray(c.col(f"f{names[cut_attr]}", "<f8" if c.ST[names[cut_attr]]["type"] != 1 else "<i4")[ii], dtype=np.float64)
            keep &= np.isfinite(ca) & (ca >= cut)
        if z_min is not None:
            keep &= z > z_min  # rentang RL dipakai menurut titik tengah blok
        if z_max is not None:
            keep &= z <= z_max
        b = (np.ceil((z - ref) / bench - 1e-9) - 1).astype(np.int64)  # (bawah, atas] seperti Surpac & GC-Ex
        b, vol, t = b[keep], vol[keep], t[keep]
        vals = {}
        for a in attrs:
            k = names[a]
            v = np.asarray(c.col(f"f{k}", "<f8" if c.ST[k]["type"] != 1 else "<i4")[ii], dtype=np.float64)[keep]
            ok = np.isfinite(v) & (v > -1e20)
            vals[a] = (np.where(ok, v * t, 0.0), np.where(ok, t, 0.0))
        if not len(b):
            continue
        u, inv = np.unique(b, return_inverse=True)
        cnt = np.bincount(inv)
        sv = np.bincount(inv, vol)
        st = np.bincount(inv, t)
        sa = {a: (np.bincount(inv, vals[a][0]), np.bincount(inv, vals[a][1])) for a in attrs}
        for j, k in enumerate(u.tolist()):
            o = nb_out.setdefault(k, {"n": 0, "vol": 0.0, "ton": 0.0, "s": {a: 0.0 for a in attrs}, "w": {a: 0.0 for a in attrs}})
            o["n"] += int(cnt[j]); o["vol"] += float(sv[j]); o["ton"] += float(st[j])
            for a in attrs:
                o["s"][a] += float(sa[a][0][j]); o["w"][a] += float(sa[a][1][j])
    rows = []
    T = {"n": 0, "vol": 0.0, "ton": 0.0, "s": {a: 0.0 for a in attrs}, "w": {a: 0.0 for a in attrs}}
    for k in sorted(nb_out, reverse=True):
        o = nb_out[k]
        rows.append({"bot": ref + k * bench, "top": ref + (k + 1) * bench, "n": o["n"], "vol": o["vol"], "ton": o["ton"],
                     "grade": {a: (o["s"][a] / o["w"][a] if o["w"][a] else None) for a in attrs}})
        T["n"] += o["n"]; T["vol"] += o["vol"]; T["ton"] += o["ton"]
        for a in attrs:
            T["s"][a] += o["s"][a]; T["w"][a] += o["w"][a]
    tot = {"n": T["n"], "vol": T["vol"], "ton": T["ton"], "grade": {a: (T["s"][a] / T["w"][a] if T["w"][a] else None) for a in attrs}}
    return {"rows": rows, "total": tot, "n_model": c.n, "file": m["fname"]}
