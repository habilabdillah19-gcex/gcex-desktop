# -*- coding: utf-8 -*-
"""Aturan tampilan block model: kelas diskrit, cut-off, dan warna -- SALINAN PERSIS aturan HTML.

Modul ini menirukan `bxCls`, `bxClassOf`, `bxPass`, `bxLab`, `bxDefUI` dan `bxSel` di aplikasi
GC-Ex Block Model (HTML). Tujuannya satu: blok yang tampil, kelasnya, dan warnanya di penampil Qt
harus SAMA ANGKANYA dengan yang di aplikasi HTML -- bukan sekadar mirip. Karena kedua aplikasi akan
dipakai berdampingan, perbedaan sekecil apa pun antara keduanya adalah cacat, bukan selera.

Yang DISENGAJA ditiru apa adanya, meski kelihatan aneh:

1. Batas kelas otomatis diambil dari KUANTIL atas data yang DICUPLIK, bukan seluruh blok:
   langkah cuplikan = max(1, floor(n/20000)). Jadi model besar memakai paling banyak ~20.000 nilai.
   Kuantilnya pun bukan interpolasi: v[floor(p*(len-1))], lalu dibulatkan ke 2 angka berarti.
2. Batas yang sama setelah pembulatan DIBUANG (dedupe), jadi jumlah kelas bisa kurang dari 5.
3. Blok yang nilainya tidak sah (NaN / tak hingga) TIDAK digambar sama sekali -- kelasnya -1,
   dan `pilih()` membuangnya. Ini juga berarti blok itu tidak ikut hitungan apa pun di panel.
4. Kelas memakai batas bawah TERTUTUP dan batas atas TERBUKA: lo <= v < hi. Nilai yang tepat sama
   dengan batas masuk ke kelas DI ATASNYA.
5. Kategori: kode 65535 berarti kosong -- tidak digambar, dan tidak bisa dicentang.

Penanda data kosong -90 yang dipakai `adegan.warna_angka` TIDAK berlaku di sini, sebab aplikasi
HTML pun tidak memperlakukan -90 secara khusus pada kelas block model; nilai -90 akan masuk kelas
terbawah di kedua aplikasi. Perbedaan itu nyata dan disengaja agar Qt tidak "memperbaiki" angka
yang di HTML dihitung lain.
"""
from __future__ import annotations

import decimal
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .proyek import BlockModel

# Palet kelas angka dan kategori -- urutan harus sama dengan BXPAL / BXCAT di aplikasi HTML.
PALET = ["#2166ac", "#4daf4a", "#ffd92f", "#fc8d59", "#d7301f",
         "#7a0177", "#1b1b1b", "#35978f", "#bf812d", "#8073ac"]
PALET_KAT = ["#e8590c", "#2f9e44", "#1971c2", "#c2255c", "#f08c00", "#7048e8",
             "#0c8599", "#5c940d", "#862e9c", "#495057", "#d6336c", "#364fc7"]

KODE_KOSONG = 65535
CUPLIK_MAKS = 20000          # jumlah nilai maksimum yang dipakai menghitung kuantil
KUANTIL = (0.5, 0.75, 0.9, 0.97)


def rgb(warna: str) -> Tuple[int, int, int]:
    """'#rrggbb' -> (r, g, b). Warna tak terbaca jadi abu-abu, tidak melempar galat."""
    t = str(warna or "").strip().lstrip("#")
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    try:
        n = int(t[:6], 16)
    except ValueError:
        return (128, 128, 128)
    return ((n >> 16) & 255, (n >> 8) & 255, n & 255)


def dua_angka_berarti(v: float) -> float:
    """Padanan `+x.toPrecision(2)` di JavaScript.

    Ditulis sendiri, bukan memakai round() maupun '%.1e', karena keduanya salah di sini:
    round() membulatkan ke jumlah DESIMAL sedangkan toPrecision ke jumlah ANGKA BERARTI
    (0,0123 -> 0,012 dan 1234 -> 1200); dan '%.1e' milik Python membulatkan nilai TEPAT SETENGAH
    ke angka genap, sedangkan JavaScript membulatkannya ke ATAS. Bedanya nyata pada kadar yang
    sering muncul: 1,25 jadi 1,3 di JavaScript tetapi 1,2 dengan '%.1e'. Karena batas kelas di
    kedua aplikasi harus sama persis, pembulatannya dikerjakan dengan Decimal, setengah ke atas,
    atas nilai biner yang sesungguhnya.
    """
    if not math.isfinite(v) or v == 0.0:
        return 0.0 if v == 0.0 else float(v)
    d = decimal.Decimal(v)                     # nilai biner apa adanya, bukan teksnya
    tanda = -1 if d < 0 else 1
    d = abs(d)
    pangkat = d.adjusted()                     # 10^pangkat <= d < 10^(pangkat+1)
    kuantum = decimal.Decimal(1).scaleb(pangkat - 1)
    bulat = d.quantize(kuantum, rounding=decimal.ROUND_HALF_UP)
    return float(tanda * bulat)


@dataclass
class Kelas:
    """Satu kelas diskrit. `lo=None` berarti terbuka ke bawah, `hi=None` terbuka ke atas."""

    lo: Optional[float]
    hi: Optional[float]
    col: str

    def label(self) -> str:
        if self.lo is None:
            return "< %s" % _angka(self.hi)
        if self.hi is None:
            return "≥ %s" % _angka(self.lo)
        return "%s – %s" % (_angka(self.lo), _angka(self.hi))


def _angka(v: Optional[float]) -> str:
    """Tulis angka seperti JavaScript: tanpa nol ekor dan tanpa '.0'."""
    if v is None:
        return ""
    if float(v).is_integer():
        return str(int(v))
    return repr(float(v)).rstrip("0").rstrip(".")


def kelas_otomatis(nilai: np.ndarray) -> List[Kelas]:
    """Batas kelas bawaan dari kuantil data tercuplik -- padanan `bxCls`."""
    A = np.asarray(nilai)
    langkah = max(1, A.size // CUPLIK_MAKS)
    v = A[::langkah]
    v = v[np.isfinite(v)]
    v = np.sort(v.astype(np.float64))

    def q(p: float) -> float:
        if v.size == 0:
            return 0.0
        return dua_angka_berarti(float(v[int(math.floor(p * (v.size - 1)))]))

    batas: List[float] = []
    for p in KUANTIL:
        b = q(p)
        if b not in batas:                 # dedupe menjaga urutan kemunculan, seperti indexOf
            batas.append(b)
    return kelas_dari_batas(batas)


def kelas_dari_batas(batas: Sequence[float]) -> List[Kelas]:
    """Ubah daftar batas menjadi kelas berurutan. n batas -> n+1 kelas."""
    b = list(batas)
    out: List[Kelas] = []
    for k in range(len(b) + 1):
        out.append(Kelas(lo=(b[k - 1] if k else None),
                         hi=(b[k] if k < len(b) else None),
                         col=PALET[k % len(PALET)]))
    return out


def batas_dari_teks(teks: str) -> List[float]:
    """Baca '0.3, 0.5, 1, 2' -> [0.3, 0.5, 1.0, 2.0]; nilai tak sah dibuang, lalu diurutkan."""
    out: List[float] = []
    for bagian in re.split(r"[;,\s]+", str(teks or "").strip()):
        if not bagian:
            continue
        try:
            v = float(bagian)
        except ValueError:
            continue
        if math.isfinite(v):
            out.append(v)
    return sorted(out)


@dataclass
class Tampilan:
    """Keadaan panel tampilan block model -- padanan `BX.ui` di aplikasi HTML."""

    atribut: Optional[str] = None
    kelas: Dict[str, List[Kelas]] = field(default_factory=dict)
    warna_kat: Dict[str, Dict[str, str]] = field(default_factory=dict)
    kat_on: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    f_atribut: str = ""                  # atribut cut-off tampilan
    f_op: str = "ge"                     # 'ge' (>=) atau 'lt' (<)
    f_nilai: str = ""                    # teks, kosong = tanpa cut-off
    opasitas: float = 0.85
    sg: float = 2.6
    sg_kolom: str = ""
    sg_nol: str = ""                     # '' / 'mdl' = nilai bawaan atribut .mdl (bawaan, seperti Surpac); 'zero' = 0; 'rep' = SG pengganti
    sg_bawaan: float = 0.0               # nilai bawaan atribut SG di header .mdl (diisi sg_larik dari BlockModel.bawaan)
    sg_ganti: str = ""                   # SG pengganti bila kolom SG kosong/nol; kosong = pakai `sg`

    # ---------- SG per blok ----------
    def sg_blok(self, v: float) -> float:
        """SG satu blok -- salinan `bxSGv` di aplikasi HTML.

        Urutannya penting dan bukan selera: tanpa kolom SG dipakai SG tunggal; dengan kolom SG,
        nilai yang sah (> 0) dipakai apa adanya; yang tidak sah jatuh ke 0 bila pemakai memilih
        'zero' (volume tetap terhitung, tonasenya nol -- cara Surpac), kalau tidak ke SG pengganti,
        kalau itu pun kosong ke SG tunggal. Mengubah urutan ini membuat tonase berbeda dari
        aplikasi HTML pada model yang kolom SG-nya berlubang -- selisih yang tidak akan dicari
        siapa pun karena tidak ada yang merasa mengubah apa-apa.
        """
        if not self.sg_kolom:
            return float(self.sg)
        try:
            fv = float(v)
        except (TypeError, ValueError):
            fv = float("nan")
        if math.isfinite(fv) and fv > 0:
            return fv
        if self.sg_nol == "zero":
            return 0.0
        if self.sg_nol != "rep":
            # 0.24.70: bawaan seperti Surpac -- blok yang tidak pernah diisi menyimpan nilai bawaan atribut
            d = float(self.sg_bawaan or 0.0)
            return d if (math.isfinite(d) and d > 0) else 0.0
        try:
            r = float(self.sg_ganti)
        except (TypeError, ValueError):
            r = 0.0
        return r if r > 0 else float(self.sg)

    def sg_larik(self, bm: BlockModel) -> np.ndarray:
        """SG untuk seluruh blok sekaligus (vektor, hasilnya sama dengan `sg_blok` per blok)."""
        n = bm.n
        if not self.sg_kolom or self.sg_kolom not in bm.angka:
            return np.full(n, float(self.sg), dtype=np.float64)
        v = np.asarray(bm.angka[self.sg_kolom], dtype=np.float64)
        try:
            self.sg_bawaan = float((getattr(bm, "bawaan", None) or {}).get(self.sg_kolom, 0.0))
        except (TypeError, ValueError):
            self.sg_bawaan = 0.0
        sah = np.isfinite(v) & (v > 0)
        ganti = self.sg_blok(float("nan"))     # satu jalur yang sama dengan versi per blok
        return np.where(sah, v, ganti)

    # ---------- kelas & warna ----------
    def kelas_dari(self, bm: BlockModel, atribut: str) -> List[Kelas]:
        """Kelas untuk satu atribut angka; dihitung sekali lalu disimpan, seperti `bxCls`."""
        if atribut not in self.kelas:
            self.kelas[atribut] = kelas_otomatis(bm.angka[atribut])
        return self.kelas[atribut]

    def warna_kategori(self, bm: BlockModel, atribut: str, k: int) -> str:
        daftar = bm.kategori[atribut][1]
        nilai = daftar[k] if 0 <= k < len(daftar) else ""
        peta = self.warna_kat.setdefault(atribut, {})
        if not peta.get(nilai):
            peta[nilai] = PALET_KAT[k % len(PALET_KAT)]
        return peta[nilai]

    def kategori_aktif(self, atribut: str, nilai: str) -> bool:
        """Belum pernah disentuh = tampil. Hanya False yang menyembunyikan, seperti `bxCatOn`."""
        peta = self.kat_on.get(atribut)
        return True if peta is None else peta.get(nilai, True) is not False

    # ---------- penyuntingan kelas ----------
    def set_batas(self, bm: BlockModel, atribut: str, k: int, sisi: str, nilai: float) -> None:
        """Ubah satu batas; batas kelas sebelah ikut berubah supaya tidak ada celah/tumpang."""
        L = self.kelas_dari(bm, atribut)
        v = float(nilai)
        if not math.isfinite(v):
            return
        if sisi == "lo":
            L[k].lo = v
            if k > 0:
                L[k - 1].hi = v
        else:
            L[k].hi = v
            if k < len(L) - 1:
                L[k + 1].lo = v

    def tambah_kelas(self, bm: BlockModel, atribut: str) -> None:
        L = self.kelas_dari(bm, atribut)
        akhir = L[-1]
        v = 1.0 if akhir.lo is None else dua_angka_berarti(akhir.lo * 2)
        akhir.hi = v
        L.append(Kelas(lo=v, hi=None, col=PALET[len(L) % len(PALET)]))

    def hapus_kelas(self, bm: BlockModel, atribut: str, k: int) -> None:
        L = self.kelas_dari(bm, atribut)
        if len(L) < 2:
            return
        if k == 0:
            L[1].lo = None
        elif k == len(L) - 1:
            L[k - 1].hi = None
        else:
            L[k - 1].hi = L[k + 1].lo
        L.pop(k)

    def kelas_kuantil_ulang(self, bm: BlockModel, atribut: str) -> None:
        self.kelas.pop(atribut, None)
        self.kelas_dari(bm, atribut)


def ui_awal(bm: BlockModel) -> Tampilan:
    """Keadaan awal panel -- padanan `bxDefUI`.

    Atribut bawaan: atribut angka pertama yang namanya mulai 'AU' (tanpa pandang huruf besar-kecil),
    kalau tidak ada yang angka pertama, kalau tidak ada lagi kategori pertama. Pada model besar
    (>300.000 blok) cut-off tampilan dinyalakan sendiri di 0,01 supaya tidak menggambar semuanya.
    """
    nums = list(bm.angka.keys())
    kats = list(bm.kategori.keys())
    pilih_au = [n for n in nums if re.match(r"^AU", n, re.I)]
    pref = pilih_au[0] if pilih_au else (nums[0] if nums else None)
    besar = bm.n > 300_000 and bool(pref)
    T = Tampilan()
    T.atribut = pref or (kats[0] if kats else None)
    if besar:
        T.f_atribut = pref or ""
        T.f_nilai = "0.01"
    return T


# ---------------------------------------------------------------------------
def kelas_blok(bm: BlockModel, T: Tampilan) -> np.ndarray:
    """Kelas tiap blok (-1 = tidak digambar) -- padanan `bxClassOf` untuk seluruh blok sekaligus."""
    a = T.atribut
    if not a:
        return np.full(bm.n, -1, dtype=np.int32)
    if a in bm.kategori:
        kode = np.asarray(bm.kategori[a][0])
        # kode bertipe uint16: dilebarkan dulu ke int32, baru kode kosong ditandai -1
        return np.where(kode == KODE_KOSONG, -1, kode.astype(np.int32)).astype(np.int32)
    if a not in bm.angka:
        return np.full(bm.n, -1, dtype=np.int32)
    v = np.asarray(bm.angka[a], dtype=np.float64)
    L = T.kelas_dari(bm, a)
    out = np.full(bm.n, -1, dtype=np.int32)
    sah = np.isfinite(v)
    for k in range(len(L) - 1, -1, -1):        # mundur: kelas pertama yang cocok harus menang
        c = L[k]
        m = sah.copy()
        if c.lo is not None:
            m &= v >= c.lo
        if c.hi is not None:
            m &= v < c.hi
        out[m] = k
    return out


def lolos(bm: BlockModel, T: Tampilan) -> np.ndarray:
    """Blok yang lolos cut-off tampilan dan centang kategori -- padanan `bxPass`."""
    ok = np.ones(bm.n, dtype=bool)
    if T.f_atribut and T.f_atribut in bm.angka and str(T.f_nilai) != "" and T.f_op != "none":
        try:
            t = float(T.f_nilai)
        except (TypeError, ValueError):
            t = float("nan")
        v = np.asarray(bm.angka[T.f_atribut], dtype=np.float64)
        sah = np.isfinite(v)
        if T.f_op == "ge":
            ok &= sah & (v >= t)
        elif T.f_op == "lt":
            ok &= sah & (v < t)
    a = T.atribut
    if a and a in bm.kategori:
        kode, daftar = bm.kategori[a]
        ikut = np.array([T.kategori_aktif(a, d) for d in daftar] + [False], dtype=bool)
        ok &= ikut[np.where(kode == KODE_KOSONG, len(daftar),
                            np.minimum(kode, max(0, len(daftar) - 1)))]
    return ok


def pilih(bm: BlockModel, T: Tampilan, pakai: Optional[np.ndarray] = None
          ) -> Tuple[np.ndarray, np.ndarray]:
    """Indeks blok yang digambar beserta kelasnya -- padanan `bxSel`.

    `pakai` adalah saringan tambahan dari luar (batas RL, sayatan). Urutannya tidak penting karena
    semuanya 'dan', tetapi hasilnya tetap urut indeks blok seperti di aplikasi HTML.
    """
    k = kelas_blok(bm, T)
    ok = lolos(bm, T) & (k >= 0)
    if pakai is not None:
        ok &= np.asarray(pakai, dtype=bool)
    idx = np.flatnonzero(ok)
    return idx, k[idx]


def warna_per_blok(bm: BlockModel, T: Tampilan, kelas: np.ndarray) -> np.ndarray:
    """Warna (n, 4) uint8 untuk blok terpilih, dari warna kelas / kategori + opasitas."""
    a = T.atribut or ""
    alpha = int(round(max(0.0, min(1.0, float(T.opasitas))) * 255))
    if a in bm.kategori:
        tabel = [rgb(T.warna_kategori(bm, a, i)) for i in range(len(bm.kategori[a][1]))]
    elif a in bm.angka:
        tabel = [rgb(c.col) for c in T.kelas_dari(bm, a)]
    else:
        tabel = [(160, 170, 185)]
    P = np.array(tabel + [(128, 128, 128)], dtype=np.uint8)
    kk = np.asarray(kelas, dtype=np.int64)
    kk = np.where((kk >= 0) & (kk < len(tabel)), kk, len(tabel))
    out = np.empty((kk.size, 4), dtype=np.uint8)
    out[:, :3] = P[kk]
    out[:, 3] = alpha
    return out


def legenda(bm: BlockModel, T: Tampilan, kelas: np.ndarray) -> List[Tuple[str, str, int]]:
    """Daftar (label, warna, jumlah blok tampil) untuk legenda panel."""
    a = T.atribut or ""
    if a in bm.kategori:
        daftar = bm.kategori[a][1]
        isi = [(daftar[i], T.warna_kategori(bm, a, i)) for i in range(len(daftar))]
    elif a in bm.angka:
        isi = [(c.label(), c.col) for c in T.kelas_dari(bm, a)]
    else:
        return []
    cacah = np.bincount(np.asarray(kelas, dtype=np.int64), minlength=len(isi)) if kelas.size \
        else np.zeros(len(isi), dtype=np.int64)
    return [(isi[i][0], isi[i][1], int(cacah[i])) for i in range(len(isi))]
