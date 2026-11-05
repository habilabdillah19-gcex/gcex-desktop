# -*- coding: utf-8 -*-
"""Pembaca folder proyek GC-Ex untuk penampil Qt (tahap 2).

Folder proyek yang ditulis aplikasi GC-Ex berisi:
  gcex_data.json     data yang diimport: collar, survey, assay, geologi, topografi, desain pit
  gcex_project.json  keadaan pekerjaan: domain, string, dig block, rencana sayatan, tampilan,
                     dan `src` -- asal block model
  gcex_proyek.db     basis data SQLite (riwayat per baris) -- tidak dipakai penampil ini
  backup/            salinan otomatis

CATATAN PENTING YANG MENENTUKAN RANCANGAN: block model TIDAK tersimpan di folder proyek. Aplikasi
menyimpannya di IndexedDB peramban dan mencatat ASAL berkasnya di `work.src`. Jadi penampil Qt
membaca block model dari berkas sumbernya (CSV atau Surpac .mdl), bukan dari folder proyek. Itu
sebabnya modul ini menerima jalur berkas block model secara terpisah.

Larik angka di JSON itu memakai sandi khusus: {"__ta": "Float32Array", "b": "<base64>"} -- hasil
`encTA` di aplikasi. Modul ini membongkarnya kembali menjadi larik NumPy dengan tipe yang sama.

Modul ini TIDAK memakai Qt sama sekali, supaya bisa diuji tanpa layar maupun kartu grafis.
"""
from __future__ import annotations

import base64
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# nama berkas di folder proyek (lihat FP.MAINF / FP.DATAF di aplikasi)
BERKAS_KERJA = "gcex_project.json"
BERKAS_DATA = "gcex_data.json"

# padanan nama larik JavaScript -> tipe NumPy
TIPE_TA = {
    "Float64Array": np.float64, "Float32Array": np.float32,
    "Int32Array": np.int32, "Uint32Array": np.uint32,
    "Int16Array": np.int16, "Uint16Array": np.uint16,
    "Int8Array": np.int8, "Uint8Array": np.uint8,
    "Uint8ClampedArray": np.uint8, "BigInt64Array": np.int64, "BigUint64Array": np.uint64,
}

# nama kolom yang dikenali di CSV block model (huruf besar/kecil diabaikan).
# Urutannya = urutan prioritas; yang pertama ketemu dipakai.
KOLOM = {
    "x": ("x", "xc", "xcentre", "xcenter", "easting", "east"),
    "y": ("y", "yc", "ycentre", "ycenter", "northing", "north"),
    "z": ("z", "zc", "zcentre", "zcenter", "rl", "elev", "elevation"),
    "sx": ("xinc", "dx", "dimx", "x_dim", "xsize", "sx", "xlength"),
    "sy": ("yinc", "dy", "dimy", "y_dim", "ysize", "sy", "ylength"),
    "sz": ("zinc", "dz", "dimz", "z_dim", "zsize", "sz", "zlength"),
}


def _bongkar(v: Any) -> Any:
    """Ubah {"__ta":...,"b":...} menjadi larik NumPy; sisanya dibiarkan."""
    if isinstance(v, dict):
        if "__ta" in v and isinstance(v.get("b"), str):
            tipe = TIPE_TA.get(v["__ta"], np.uint8)
            return np.frombuffer(base64.b64decode(v["b"]), dtype=tipe)
        return {k: _bongkar(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_bongkar(x) for x in v]
    return v


def muat_json(p: Path) -> Any:
    """Baca JSON aplikasi, termasuk membongkar larik bersandi."""
    return _bongkar(json.loads(Path(p).read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
@dataclass
class BlockModel:
    """Block model sebagai larik sejajar. Semua panjangnya sama (n blok).

    x, y, z  : titik PUSAT blok, koordinat dunia
    sx,sy,sz : ukuran blok
    angka    : atribut angka per nama (kadar, SG, sb_frac, ...)
    kategori : atribut teks per nama -> (kode per blok, daftar nilai)
    """

    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    sx: np.ndarray
    sy: np.ndarray
    sz: np.ndarray
    angka: Dict[str, np.ndarray] = field(default_factory=dict)
    kategori: Dict[str, Tuple[np.ndarray, List[str]]] = field(default_factory=dict)
    nama: str = ""
    asal: str = ""

    @property
    def n(self) -> int:
        return int(self.x.size)

    def kotak(self) -> Tuple[float, float, float, float, float, float]:
        """Kotak pembatas termasuk tepi blok (bukan hanya titik pusatnya)."""
        if self.n == 0:
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return (float((self.x - self.sx / 2).min()), float((self.x + self.sx / 2).max()),
                float((self.y - self.sy / 2).min()), float((self.y + self.sy / 2).max()),
                float((self.z - self.sz / 2).min()), float((self.z + self.sz / 2).max()))

    def volume(self) -> float:
        return float(np.sum(self.sx * self.sy * self.sz))

    def ringkas(self) -> str:
        k = self.kotak()
        return ("%s: %s blok | X %.1f-%.1f  Y %.1f-%.1f  RL %.1f-%.1f | atribut angka: %s"
                % (self.nama or "block model", f"{self.n:,}".replace(",", "."),
                   k[0], k[1], k[2], k[3], k[4], k[5], ", ".join(sorted(self.angka)) or "-"))


def _cari_kolom(judul: Sequence[str], kunci: str) -> int:
    rapi = [str(h).strip().lower().replace(" ", "").replace("-", "_") for h in judul]
    for nama in KOLOM[kunci]:
        if nama in rapi:
            return rapi.index(nama)
    return -1


def baca_bm_csv(p: Path, maks: int = 0) -> BlockModel:
    """Baca block model dari CSV / TSV.

    Kolom pusat blok (X, Y, Z) wajib ada. Ukuran blok (XINC/YINC/ZINC atau DX/DY/DZ) dipakai bila
    ada; bila tidak, ukurannya DITAKSIR dari jarak terkecil antar titik pusat per sumbu -- cara
    yang sama dengan `bxInfer` di aplikasi -- dan itu dicatat di `asal` supaya pemakai tahu
    ukurannya taksiran, bukan dari berkas.

    maks > 0 membatasi jumlah baris yang dibaca (untuk mengintip berkas besar).
    """
    p = Path(p)
    teks = p.read_text(encoding="utf-8-sig", errors="replace")
    baris = [b for b in teks.splitlines() if b.strip()]
    if len(baris) < 2:
        raise ValueError("berkas block model kosong atau tanpa baris data: %s" % p.name)
    pemisah = "\t" if baris[0].count("\t") > baris[0].count(",") else ","
    judul = [h.strip() for h in baris[0].split(pemisah)]
    idx = {k: _cari_kolom(judul, k) for k in KOLOM}
    for k in ("x", "y", "z"):
        if idx[k] < 0:
            raise ValueError("kolom %s tidak ditemukan di %s (judul: %s)"
                             % (k.upper(), p.name, ", ".join(judul[:12])))
    isi = baris[1:maks + 1] if maks > 0 else baris[1:]
    n = len(isi)
    kolom = [[None] * n for _ in judul]
    for i, b in enumerate(isi):
        bagian = b.split(pemisah)
        for j in range(min(len(bagian), len(judul))):
            kolom[j][i] = bagian[j].strip()

    def angka(j: int) -> np.ndarray:
        a = np.full(n, np.nan)
        for i, s in enumerate(kolom[j]):
            if not s:
                continue
            try:
                a[i] = float(s.replace(",", ".")) if "," in s and "." not in s else float(s)
            except ValueError:
                pass
        return a

    X, Y, Z = angka(idx["x"]), angka(idx["y"]), angka(idx["z"])
    catatan = []
    ukuran = {}
    for k, sumbu in (("sx", X), ("sy", Y), ("sz", Z)):
        if idx[k] >= 0:
            ukuran[k] = angka(idx[k])
        else:
            ukuran[k] = np.full(n, _taksir_ukuran(sumbu))
            catatan.append("%s ditaksir %.3f" % (k.upper(), ukuran[k][0]))

    bm = BlockModel(x=X, y=Y, z=Z, sx=ukuran["sx"], sy=ukuran["sy"], sz=ukuran["sz"],
                    nama=p.stem, asal=str(p) + ((" (" + "; ".join(catatan) + ")") if catatan else ""))
    dipakai = {idx[k] for k in KOLOM if idx[k] >= 0}
    for j, nama in enumerate(judul):
        if j in dipakai:
            continue
        a = angka(j)
        if np.isfinite(a).sum() >= max(1, n * 0.5):
            bm.angka[nama] = a                     # mayoritas terbaca sebagai angka -> atribut kadar
        else:
            nilai = sorted({s for s in kolom[j] if s})
            peta = {s: i for i, s in enumerate(nilai)}
            kode = np.full(n, 65535, dtype=np.uint16)
            for i, s in enumerate(kolom[j]):
                if s:
                    kode[i] = peta[s]
            bm.kategori[nama] = (kode, nilai)      # sisanya atribut kategori (DOMAIN, dsb.)
    return bm


def _taksir_ukuran(a: np.ndarray) -> float:
    """Ukuran blok ditaksir dari jarak terkecil antar titik pusat yang berbeda pada satu sumbu."""
    u = np.unique(a[np.isfinite(a)])
    if u.size < 2:
        return 1.0
    d = np.diff(u)
    d = d[d > 1e-9]
    return float(d.min()) if d.size else 1.0


def baca_bm(p: Path, maks: int = 0) -> BlockModel:
    """Baca block model dari CSV/TSV atau Surpac .mdl (memakai modul backend yang sudah ada)."""
    p = Path(p)
    if p.suffix.lower() in (".csv", ".txt", ".tsv"):
        return baca_bm_csv(p, maks)
    if p.suffix.lower() == ".mdl":
        raise NotImplementedError(
            "block model Surpac .mdl dibaca lewat backend GC-Ex (gcex_backend.mdl_io); "
            "penampil Qt tahap ini baru membaca CSV. Export .mdl ke CSV dari aplikasi dulu.")
    raise ValueError("jenis berkas block model tidak dikenali: %s" % p.name)


# ---------------------------------------------------------------------------
@dataclass
class Bor:
    """Lubang bor: collar + survey, sudah dihitung jadi jalur 3D (polyline per lubang)."""

    id: List[str] = field(default_factory=list)
    titik: List[np.ndarray] = field(default_factory=list)      # tiap unsur (m, 3) koordinat dunia

    @property
    def n(self) -> int:
        return len(self.id)


def jalur_bor(collars: Sequence[Sequence[Any]], surveys: Sequence[Sequence[Any]],
              langkah: float = 2.0) -> Bor:
    """Hitung jalur 3D tiap lubang dari collar + survey (metode tangensial seimbang).

    collars: [id, easting, northing, rl, kedalaman]
    surveys: [id, kedalaman, dip, azimuth]   -- dip negatif = menunjam ke bawah, seperti di GC-Ex

    Metode tangensial seimbang dipakai karena itu yang lazim di basis data bor tambang: arah pada
    satu selang diambil rata-rata arah di kedua ujungnya, sehingga lubang melengkung tidak
    terpotong bersudut.
    """
    per: Dict[str, List[Tuple[float, float, float]]] = {}
    for s in surveys or []:
        if len(s) < 4:
            continue
        per.setdefault(str(s[0]), []).append((float(s[1]), float(s[2]), float(s[3])))
    B = Bor()
    for c in collars or []:
        if len(c) < 5:
            continue
        hid = str(c[0])
        x0, y0, z0, akhir = float(c[1]), float(c[2]), float(c[3]), float(c[4])
        sv = sorted(per.get(hid, []), key=lambda q: q[0])
        if not sv:
            sv = [(0.0, -90.0, 0.0)]
        if sv[0][0] > 0:
            sv.insert(0, (0.0, sv[0][1], sv[0][2]))
        if sv[-1][0] < akhir:
            sv.append((akhir, sv[-1][1], sv[-1][2]))
        P = [(x0, y0, z0)]
        for a, b in zip(sv[:-1], sv[1:]):
            L = b[0] - a[0]
            if L <= 0:
                continue
            bagi = max(1, int(math.ceil(L / max(0.1, langkah))))
            for q in range(bagi):
                t0 = q / bagi
                t1 = (q + 1) / bagi
                dip_a = math.radians(a[1] + (b[1] - a[1]) * t0)
                dip_b = math.radians(a[1] + (b[1] - a[1]) * t1)
                az_a = math.radians(a[2] + (b[2] - a[2]) * t0)
                az_b = math.radians(a[2] + (b[2] - a[2]) * t1)
                d = L / bagi
                # tangensial seimbang: rata-rata arah di kedua ujung selang
                dn = d / 2 * (math.cos(dip_a) * math.cos(az_a) + math.cos(dip_b) * math.cos(az_b))
                de = d / 2 * (math.cos(dip_a) * math.sin(az_a) + math.cos(dip_b) * math.sin(az_b))
                dz = d / 2 * (math.sin(dip_a) + math.sin(dip_b))
                x, y, z = P[-1]
                P.append((x + de, y + dn, z + dz))
        B.id.append(hid)
        B.titik.append(np.asarray(P, dtype=np.float64))
    return B


# ---------------------------------------------------------------------------
@dataclass
class Proyek:
    """Satu proyek GC-Ex yang sudah dibaca: data bor, topografi, keadaan kerja, block model."""

    folder: Optional[Path] = None
    nama: str = ""
    aplikasi: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    kerja: Dict[str, Any] = field(default_factory=dict)
    bm: Optional[BlockModel] = None

    @property
    def bor(self) -> Bor:
        if not hasattr(self, "_bor"):
            self._bor = jalur_bor(self.data.get("collars") or [], self.data.get("surveys") or [])
        return self._bor

    def topo(self) -> np.ndarray:
        """Titik topografi (n, 3); kosong bila tidak ada."""
        T = self.data.get("topoData") or []
        if not len(T):
            return np.zeros((0, 3))
        A = np.asarray([t[:3] for t in T if t and len(t) >= 3 and t[0] is not None],
                       dtype=np.float64)
        return A

    def asal_bm(self) -> str:
        """Nama berkas sumber block model yang dicatat proyek (bila ada)."""
        s = (self.kerja or {}).get("src") or {}
        return str(s.get("name") or "")

    def ringkas(self) -> str:
        b = ["proyek %s (%s)" % (self.nama or "-", self.aplikasi or "-")]
        b.append("%d collar, %d survey, %d assay"
                 % (len(self.data.get("collars") or []), len(self.data.get("surveys") or []),
                    len(self.data.get("assays") or [])))
        t = self.topo()
        if t.size:
            b.append("%d titik topografi" % t.shape[0])
        if self.bm:
            b.append(self.bm.ringkas())
        elif self.asal_bm():
            b.append("block model belum dimuat (asal tercatat: %s)" % self.asal_bm())
        return " | ".join(b)


def buka_folder(folder: Path, bm_path: Optional[Path] = None, maks_blok: int = 0) -> Proyek:
    """Buka folder proyek GC-Ex. `bm_path` = berkas sumber block model (CSV), bila mau ikut dimuat.

    Folder proyek tidak memuat block model (lihat catatan di atas berkas ini), jadi tanpa
    `bm_path` yang terbaca hanya data bor, topografi, dan keadaan pekerjaan.
    """
    folder = Path(folder)
    fd = folder / BERKAS_DATA
    fk = folder / BERKAS_KERJA
    if not fd.exists() and not fk.exists():
        raise FileNotFoundError("bukan folder proyek GC-Ex: %s tidak memuat %s maupun %s"
                                % (folder, BERKAS_DATA, BERKAS_KERJA))
    P = Proyek(folder=folder)
    if fd.exists():
        P.data = muat_json(fd) or {}
        P.nama = str(P.data.get("name") or "")
    if fk.exists():
        j = muat_json(fk) or {}
        meta = j.get("meta") or {}
        P.kerja = (j.get("body") or {}).get("work") or j.get("work") or {}
        P.aplikasi = str(meta.get("app") or "")
        P.nama = P.nama or str(meta.get("name") or "")
    if bm_path:
        P.bm = baca_bm(Path(bm_path), maks_blok)
    return P
