# -*- coding: utf-8 -*-
"""Penyusun adegan 3D penampil Qt: block model, lubang bor, dan topografi menjadi larik siap-GPU.

Modul ini tidak memakai Qt maupun OpenGL, hanya NumPy, supaya bisa diuji tanpa layar dan tanpa
kartu grafis. Yang dihasilkan: larik instans blok (pusat, ukuran, warna), simpul garis untuk jalur
bor, dan jaring segitiga untuk permukaan topografi.

SATU HAL YANG WAJIB BENAR: koordinat tambang di Indonesia bernilai besar -- northing di data
latihan ~9.011.700. Di sekitar nilai itu, jarak antar bilangan `float32` yang berdekatan tepat
1 METER (periksa sendiri: numpy.spacing(numpy.float32(9011700)) = 1,0). Artinya koordinat
berkoma -- mis. pusat blok di 9.011.697,5 pada model berblok 2,5 m, atau northing UTM yang tidak
bulat -- akan DIBULATKAN ke meter terdekat oleh GPU: blok tampak bergeser setengah meter dan
sisinya bergerigi. (Pada data latihan kebetulan semua pusat blok bilangan bulat, jadi di situ
kesalahannya nol; itu kebetulan, bukan jaminan.)

Karena GPU bekerja dengan float32, SELURUH koordinat di modul ini digeser dulu ke titik asal lokal
(tengah model) dalam float64, baru diubah ke float32. Setelah digeser, nilainya hanya ratusan
meter, dan di sana ketelitian float32 sekitar 3 per 100.000 meter -- jauh lebih halus daripada
ukuran blok terkecil. Pergeserannya dicatat di `Adegan.asal` supaya angka yang ditampilkan ke
pemakai tetap koordinat dunia. Uji `test_adegan.py` memperlihatkan selisih keduanya.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .proyek import BlockModel, Bor

# ---------------------------------------------------------------------------
# Tangga warna. Ditulis langsung di sini (bukan memakai matplotlib) supaya penampil tetap ringan
# dan warnanya tidak berubah bila pustaka luar berubah versi.
# Masing-masing: daftar simpul (posisi 0..1, R, G, B).
TANGGA: Dict[str, List[Tuple[float, int, int, int]]] = {
    # biru -> hijau -> kuning -> merah: tangga kadar yang lazim di tambang
    "kadar": [(0.00, 44, 62, 110), (0.25, 33, 145, 140), (0.50, 94, 201, 98),
              (0.75, 253, 231, 37), (1.00, 189, 36, 34)],
    # abu-abu: untuk atribut yang bukan kadar (SG, ketebalan)
    "abu": [(0.0, 40, 44, 52), (1.0, 235, 238, 242)],
    # merah-putih-biru: untuk nilai berpusat (mis. selisih)
    "selisih": [(0.0, 33, 85, 180), (0.5, 245, 245, 245), (1.0, 180, 40, 35)],
}

# palet kategori (domain, material): dibedakan rona, bukan hanya terang-gelap, supaya tetap
# terbaca bagi pemakai yang sulit membedakan merah-hijau
PALET_KATEGORI = [
    (31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189),
    (140, 86, 75), (227, 119, 194), (127, 127, 127), (188, 189, 34), (23, 190, 207),
]
WARNA_KOSONG = (120, 120, 120)


def tangga_warna(nama: str, n: int = 256) -> np.ndarray:
    """Tangga warna sebagai larik (n, 3) uint8."""
    simpul = TANGGA.get(nama) or TANGGA["kadar"]
    t = np.linspace(0.0, 1.0, n)
    pos = np.array([s[0] for s in simpul])
    out = np.zeros((n, 3), dtype=np.uint8)
    for k in range(3):
        nilai = np.array([s[k + 1] for s in simpul], dtype=np.float64)
        out[:, k] = np.clip(np.interp(t, pos, nilai), 0, 255).astype(np.uint8)
    return out


def warna_angka(nilai: np.ndarray, vmin: float, vmax: float, tangga: str = "kadar",
                alpha: int = 255) -> np.ndarray:
    """Warnai nilai angka -> (n, 4) uint8. Nilai tak sah / penanda <= -90 jadi abu-abu."""
    v = np.asarray(nilai, dtype=np.float64)
    sah = np.isfinite(v) & (v > -90)
    if vmax <= vmin:
        vmax = vmin + 1e-12
    t = np.clip((v - vmin) / (vmax - vmin), 0.0, 1.0)
    T = tangga_warna(tangga)
    idx = (np.nan_to_num(t, nan=0.0) * (T.shape[0] - 1)).astype(np.int64)
    idx = np.where(sah, idx, 0)
    out = np.empty((v.size, 4), dtype=np.uint8)
    out[:, :3] = T[idx]
    out[~sah, 0] = WARNA_KOSONG[0]
    out[~sah, 1] = WARNA_KOSONG[1]
    out[~sah, 2] = WARNA_KOSONG[2]
    out[:, 3] = alpha
    return out


def warna_kategori(kode: np.ndarray, alpha: int = 255) -> np.ndarray:
    """Warnai atribut kategori -> (n, 4) uint8. Kode 65535 (kosong) jadi abu-abu."""
    k = np.asarray(kode)
    out = np.empty((k.size, 4), dtype=np.uint8)
    P = np.array(PALET_KATEGORI + [WARNA_KOSONG], dtype=np.uint8)
    pilih = np.where(k == 65535, len(PALET_KATEGORI), k % len(PALET_KATEGORI))
    out[:, :3] = P[pilih]
    out[:, 3] = alpha
    return out


# ---------------------------------------------------------------------------
@dataclass
class Saringan:
    """Batas yang menentukan blok mana yang digambar. Semuanya opsional."""

    rl: Optional[Tuple[float, float]] = None           # rentang RL (z)
    atribut: Optional[str] = None                      # nama atribut angka yang dibatasi
    rentang: Optional[Tuple[float, float]] = None      # rentang nilainya
    kategori: Optional[Tuple[str, Sequence[str]]] = None   # (nama atribut, nilai yang ditampilkan)
    sayatan: Optional[Tuple[float, float, float, float]] = None  # (x, y, azimut derajat, tebal)

    def terapkan(self, bm: BlockModel) -> np.ndarray:
        """Hasil: larik bool sepanjang jumlah blok."""
        pakai = np.ones(bm.n, dtype=bool)
        if self.rl:
            pakai &= (bm.z >= self.rl[0]) & (bm.z <= self.rl[1])
        if self.atribut and self.rentang and self.atribut in bm.angka:
            v = bm.angka[self.atribut]
            pakai &= np.isfinite(v) & (v >= self.rentang[0]) & (v <= self.rentang[1])
        if self.kategori:
            nama, nilai = self.kategori
            if nama in bm.kategori:
                kode, daftar = bm.kategori[nama]
                ikut = np.array([s in set(nilai) for s in daftar] + [False], dtype=bool)
                pakai &= ikut[np.where(kode == 65535, len(daftar), np.minimum(kode, len(daftar) - 1))]
        if self.sayatan:
            # slab tegak: jarak tegak lurus titik pusat blok ke bidang sayatan <= tebal/2.
            # azimut 0 = utara, diukur searah jarum jam, sama dengan sayatan di aplikasi.
            x0, y0, az, tebal = self.sayatan
            a = np.radians(az)
            # normal bidang (mendatar, tegak lurus arah sayatan)
            nx, ny = np.cos(a), -np.sin(a)
            d = (bm.x - x0) * nx + (bm.y - y0) * ny
            pakai &= np.abs(d) <= max(1e-9, tebal / 2.0)
        return pakai


@dataclass
class Adegan:
    """Larik siap-GPU. Semua koordinat SUDAH digeser ke `asal` dan bertipe float32."""

    asal: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    pusat: np.ndarray = field(default_factory=lambda: np.zeros((0, 3), np.float32))
    ukuran: np.ndarray = field(default_factory=lambda: np.zeros((0, 3), np.float32))
    warna: np.ndarray = field(default_factory=lambda: np.zeros((0, 4), np.uint8))
    garis: np.ndarray = field(default_factory=lambda: np.zeros((0, 3), np.float32))
    garis_awal: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int32))
    garis_cacah: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int32))
    topo_simpul: np.ndarray = field(default_factory=lambda: np.zeros((0, 3), np.float32))
    topo_indeks: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint32))
    kotak: Tuple[float, float, float, float, float, float] = (0, 0, 0, 0, 0, 0)

    @property
    def n_blok(self) -> int:
        return int(self.pusat.shape[0])

    def dunia(self, p: Sequence[float]) -> Tuple[float, float, float]:
        """Ubah titik adegan kembali ke koordinat dunia (untuk ditampilkan ke pemakai)."""
        return (float(p[0]) + self.asal[0], float(p[1]) + self.asal[1], float(p[2]) + self.asal[2])


def titik_asal(bm: Optional[BlockModel] = None, titik: Optional[np.ndarray] = None
               ) -> Tuple[float, float, float]:
    """Titik asal lokal: tengah kotak pembatas, DIBULATKAN ke meter supaya stabil antar muat.

    Dibulatkan agar penggeseran tidak berubah-ubah sedikit setiap kali adegan disusun ulang --
    kamera dan posisi tersimpan tetap cocok.
    """
    if bm is not None and bm.n:
        k = bm.kotak()
        return (round((k[0] + k[1]) / 2), round((k[2] + k[3]) / 2), round((k[4] + k[5]) / 2))
    if titik is not None and titik.size:
        return (round(float(titik[:, 0].mean())), round(float(titik[:, 1].mean())),
                round(float(titik[:, 2].mean())))
    return (0.0, 0.0, 0.0)


def _f32(a: np.ndarray, geser: float) -> np.ndarray:
    """Geser dalam float64 LALU ubah ke float32 -- urutan ini yang menjaga ketelitian."""
    return (np.asarray(a, dtype=np.float64) - geser).astype(np.float32)


def blok(bm: BlockModel, warna: np.ndarray, pakai: Optional[np.ndarray] = None,
         asal: Optional[Tuple[float, float, float]] = None) -> Adegan:
    """Susun instans blok. `warna` sepanjang jumlah blok (sebelum disaring)."""
    A = Adegan(asal=asal or titik_asal(bm))
    k = np.flatnonzero(pakai) if pakai is not None else np.arange(bm.n)
    A.pusat = np.stack([_f32(bm.x[k], A.asal[0]), _f32(bm.y[k], A.asal[1]),
                        _f32(bm.z[k], A.asal[2])], axis=1)
    A.ukuran = np.stack([bm.sx[k].astype(np.float32), bm.sy[k].astype(np.float32),
                         bm.sz[k].astype(np.float32)], axis=1)
    A.warna = np.asarray(warna)[k].astype(np.uint8)
    if k.size:
        h = A.ukuran / 2.0
        lo = (A.pusat - h).min(axis=0)
        hi = (A.pusat + h).max(axis=0)
        A.kotak = (float(lo[0]), float(hi[0]), float(lo[1]), float(hi[1]), float(lo[2]), float(hi[2]))
    return A


def garis_bor(A: Adegan, bor: Bor) -> Adegan:
    """Tambahkan jalur bor sebagai rangkaian garis. Tiap lubang satu rentang gambar."""
    if not bor.n:
        return A
    titik = []
    awal, cacah = [], []
    n = 0
    for P in bor.titik:
        if P.shape[0] < 2:
            continue
        titik.append(np.stack([_f32(P[:, 0], A.asal[0]), _f32(P[:, 1], A.asal[1]),
                               _f32(P[:, 2], A.asal[2])], axis=1))
        awal.append(n)
        cacah.append(P.shape[0])
        n += P.shape[0]
    if titik:
        A.garis = np.concatenate(titik).astype(np.float32)
        A.garis_awal = np.asarray(awal, dtype=np.int32)
        A.garis_cacah = np.asarray(cacah, dtype=np.int32)
    return A


def permukaan_grid(A: Adegan, titik: np.ndarray, toleransi: float = 1e-6) -> Adegan:
    """Jadikan titik topografi jaring segitiga, bila titiknya tersusun di kisi teratur.

    Topografi GC-Ex biasanya hasil pengambilan kisi (data latihan: kisi 5 m), jadi jaringnya bisa
    disusun langsung tanpa triangulasi Delaunay -- lebih cepat, hasilnya pasti, dan tidak menambah
    ketergantungan pustaka. Bila titiknya TIDAK berpola kisi, fungsi ini tidak memaksakan apa pun:
    jaringnya dibiarkan kosong dan pemanggil bisa memilih cara lain.
    """
    if titik is None or titik.shape[0] < 4:
        return A
    xs = np.unique(titik[:, 0])
    ys = np.unique(titik[:, 1])
    if xs.size < 2 or ys.size < 2 or xs.size * ys.size > 4_000_000:
        return A
    # kisi teratur? jarak antar nilai unik harus seragam
    for u in (xs, ys):
        d = np.diff(u)
        if d.size and (d.max() - d.min()) > max(toleransi, 1e-3 * d.mean()):
            return A
    if titik.shape[0] < xs.size * ys.size * 0.5:
        return A                                    # terlalu banyak lubang: bukan kisi penuh
    ix = np.searchsorted(xs, titik[:, 0])
    iy = np.searchsorted(ys, titik[:, 1])
    Z = np.full((xs.size, ys.size), np.nan)
    Z[ix, iy] = titik[:, 2]
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    simpul = np.stack([_f32(X.ravel(), A.asal[0]), _f32(Y.ravel(), A.asal[1]),
                       _f32(np.nan_to_num(Z, nan=np.nanmin(Z)).ravel(), A.asal[2])], axis=1)
    # dua segitiga per sel, hanya bila keempat sudutnya ada datanya
    i0 = np.arange(xs.size - 1)[:, None] * ys.size + np.arange(ys.size - 1)[None, :]
    a = i0.ravel()
    b = a + ys.size
    c = b + 1
    d = a + 1
    ada = (np.isfinite(Z.ravel()[a]) & np.isfinite(Z.ravel()[b])
           & np.isfinite(Z.ravel()[c]) & np.isfinite(Z.ravel()[d]))
    a, b, c, d = a[ada], b[ada], c[ada], d[ada]
    A.topo_simpul = simpul.astype(np.float32)
    A.topo_indeks = np.concatenate([np.stack([a, b, c], 1), np.stack([a, c, d], 1)]).ravel().astype(np.uint32)
    return A


def susun(bm: Optional[BlockModel], bor: Optional[Bor] = None,
          topo: Optional[np.ndarray] = None, atribut: Optional[str] = None,
          saringan: Optional[Saringan] = None, tangga: str = "kadar",
          vmin: Optional[float] = None, vmax: Optional[float] = None,
          alpha: int = 255) -> Adegan:
    """Susun seluruh adegan dari satu proyek. Atribut boleh atribut angka atau kategori.

    Batas warna (vmin, vmax) dihitung dari persentil 2 dan 98 bila tidak diberikan, supaya satu
    blok pencilan tidak memucatkan seluruh model.
    """
    if bm is None or bm.n == 0:
        A = Adegan(asal=titik_asal(titik=topo))
    else:
        pakai = saringan.terapkan(bm) if saringan else None
        if atribut and atribut in bm.kategori:
            W = warna_kategori(bm.kategori[atribut][0], alpha)
        elif atribut and atribut in bm.angka:
            v = bm.angka[atribut]
            sah = np.isfinite(v) & (v > -90)
            lo = float(np.percentile(v[sah], 2)) if sah.any() and vmin is None else (vmin or 0.0)
            hi = float(np.percentile(v[sah], 98)) if sah.any() and vmax is None else (vmax or 1.0)
            W = warna_angka(v, lo, hi, tangga, alpha)
        else:
            W = np.tile(np.array([[160, 170, 185, alpha]], dtype=np.uint8), (bm.n, 1))
        A = blok(bm, W, pakai)
    if bor is not None:
        garis_bor(A, bor)
    if topo is not None and topo.size:
        permukaan_grid(A, topo)
    return A
