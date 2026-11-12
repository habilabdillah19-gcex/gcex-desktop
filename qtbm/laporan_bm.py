# -*- coding: utf-8 -*-
"""Laporan Block Model untuk penampil Qt: menjembatani BlockModel ke mesin hitung Python.

Mesin hitungnya BUKAN ditulis di sini. Yang dipakai adalah `gcex_backend.laporan.run()` -- modul
yang sudah dibuktikan menghasilkan angka yang sama dengan `rpRun()` di aplikasi HTML (lihat
backend/tests/test_laporan.py dan tools/uji/paritas_laporan.py). Modul ini hanya:

  1. menyusun payload dari BlockModel + pilihan panel,
  2. menjalankan mesin itu dua kali bila metode tonase dibandingkan,
  3. merapikan hasilnya jadi tabel dan CSV.

Alasan pembagian ini sama dengan di tampil_bm.py: kalau rumusnya ikut ditulis di sini, uji paritas
tidak lagi menjamin angka yang dilihat pemakai. Satu laporan = satu sumber angka.

TENTANG METODE TONASE. Dua baris yang dibandingkan panel ini sama dengan tab "⑤ Metode tonase" di
aplikasi HTML:

  * Presisi GC-Ex  -- blok perbatasan ditimbang proporsi volumenya (`sb_frac`).
  * Seperti Surpac -- blok dihitung UTUH; `sb_frac` diabaikan (Surpac *Keep partial = False*).

Yang WAJIB diingat saat membaca selisihnya: pada metode presisi, blok yang proporsinya NOL tidak
dilaporkan sama sekali (terbuang di tahap `frac`), sedangkan metode Surpac melaporkan semua blok
yang lolos constraint -- termasuk yang sepenuhnya di luar solid. Karena itu selisih bisa tampak
sangat besar dan itu WAJAR, bukan tanda salah hitung. Perbandingan yang berarti baru muncul setelah
constraint domainnya disamakan.

CATATAN tentang waste pengisi: laporan Block Model tidak memuatnya. Waste pengisi (area poligon
tanpa blok BM) hanya ada di perhitungan dig block per poligon, bukan di laporan ini -- lihat
PANDUAN_INSTALL bagian 88.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .proyek import BlockModel

NAMA_METODE = {"presisi": "Presisi GC-Ex", "surpac": "Seperti Surpac"}


def _mesin():
    """Ambil `gcex_backend.laporan`; None bila backend tidak terjangkau."""
    try:
        from gcex_backend import laporan           # type: ignore
        return laporan
    except ImportError:
        pass
    jalur = Path(__file__).resolve().parents[1] / "backend"
    if jalur.is_dir() and str(jalur) not in sys.path:
        sys.path.insert(0, str(jalur))
    try:
        from gcex_backend import laporan           # type: ignore
        return laporan
    except ImportError:
        return None


@dataclass
class Pilihan:
    """Pilihan panel laporan. Namanya mengikuti panel, isinya diterjemahkan ke opsi mesin."""

    kadar: str = ""                                  # atribut kadar untuk cut-off
    cuts: List[float] = field(default_factory=lambda: [0.0])
    atribut: List[str] = field(default_factory=list)  # atribut lain yang dilaporkan kadarnya
    grup: str = "none"                               # 'none' | 'bench' | 'cat'
    grup_atribut: str = ""                           # dipakai bila grup == 'cat'
    tinggi_bench: float = 5.0
    rl_acuan: float = 0.0
    rl: Optional[Tuple[float, float]] = None
    sg: float = 2.6
    sg_kolom: str = ""
    sg_nol: str = ""                                 # 'zero' = blok tanpa SG sah bertonase 0
    sg_ganti: str = ""                               # SG pengganti bila kolom SG kosong/nol
    metode: str = "presisi"                          # 'presisi' | 'surpac'
    bandingkan: bool = False                         # True = hitung kedua metode

    def opsi(self) -> Dict[str, Any]:
        o: Dict[str, Any] = {
            "cuts": list(self.cuts) or [0.0],
            "gr": self.kadar,
            "atts": list(self.atribut),
            "grp": self.grup,
            "catAttr": self.grup_atribut,
            "bh": float(self.tinggi_bench),
            "bref": float(self.rl_acuan),
            "sg": float(self.sg),
            "sgCol": self.sg_kolom,
            # Perlakuan blok yang kolom SG-nya kosong / nol. Mesin laporan sudah mendukungnya;
            # kalau tidak diteruskan dari panel, tonase model yang kolom SG-nya berlubang akan
            # berbeda dari aplikasi HTML tanpa ada yang merasa mengubah apa-apa.
            "sgZero": self.sg_nol,
            "sgRep": self.sg_ganti,
            # Proporsi sub-blok dipakai HANYA pada metode presisi. Di Block Model sakelar ini
            # bertipe BOOLEAN (di Drill Hole ia nama atribut) -- beda konvensi yang sudah pernah
            # membuat angka "presisi" diam-diam sama dengan angka Surpac.
            "frac": self.metode != "surpac",
        }
        if self.rl:
            o["z0"], o["z1"] = float(self.rl[0]), float(self.rl[1])
        return o


def payload(bm: BlockModel, P: Pilihan, pakai: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """Susun payload mesin laporan dari block model (opsional: hanya blok terpilih)."""
    k = np.flatnonzero(pakai) if pakai is not None else np.arange(bm.n)
    ambil = lambda a: np.asarray(a, dtype=np.float64)[k].tolist()           # noqa: E731
    num = {nama: ambil(v) for nama, v in bm.angka.items()}
    cat = {nama: {"codes": np.asarray(kode, dtype=np.int64)[k].tolist(), "dict": list(daftar)}
           for nama, (kode, daftar) in bm.kategori.items()}
    return {
        "blocks": {"x": ambil(bm.x), "y": ambil(bm.y), "z": ambil(bm.z),
                   "sx": ambil(bm.sx), "sy": ambil(bm.sy), "sz": ambil(bm.sz)},
        "off": [0.0, 0.0],
        "num": num,
        "cat": cat,
        "opsi": dict(P.opsi(), sgBawaan=float((getattr(bm, "bawaan", None) or {}).get(P.sg_kolom, 0.0) or 0.0)),
    }


def jalankan(bm: BlockModel, P: Pilihan, pakai: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """Jalankan laporan untuk satu metode (atau kedua metode bila `P.bandingkan`).

    Hasil: {'metode': {nama: hasil_mesin}, 'urut': [...], 'atts': [...], 'cuts': [...]}
    """
    mesin = _mesin()
    if mesin is None:
        raise RuntimeError(
            "mesin laporan ada di backend GC-Ex (gcex_backend.laporan) tetapi tidak terjangkau "
            "dari penampil ini. Jalankan dari folder repo.")
    if bm is None or not bm.n:
        raise ValueError("belum ada block model")
    if not P.kadar or P.kadar not in bm.angka:
        raise ValueError("atribut kadar untuk cut-off belum dipilih")

    urut = ["presisi", "surpac"] if P.bandingkan else [P.metode]
    keluar: Dict[str, Any] = {}
    for m in urut:
        Pm = Pilihan(**{**P.__dict__, "metode": m, "bandingkan": False})
        keluar[m] = mesin.run(payload(bm, Pm, pakai))
    satu = keluar[urut[0]]
    return {"metode": keluar, "urut": urut, "atts": satu.get("atts") or [],
            "cuts": satu.get("cuts") or []}


# ---------------------------------------------------------------------------
# Satuan, label dan kolom logam: SAMA dengan rpUnitDef / rpBenchLab / rpMetal di web-src/rpbm.js.
# Ditiru, bukan dikarang, karena laporan dari kedua aplikasi akan diletakkan bersebelahan.
import re as _re


def satuan(a: str) -> str:
    """Satuan bawaan atribut -- padanan `rpUnitDef()`, TERMASUK `elUnit()` yang dipanggilnya.

    URUTANNYA PENTING DAN BUKAN SELERA. `rpUnitDef` memanggil `elUnit(a)` lebih dulu dan hanya
    jatuh ke regex cadangannya bila `elUnit` mengembalikan string kosong. Dan `elUnit` memeriksa
    `ppm` / `ppb` SEBELUM aturan awalan unsur -- itulah sebabnya `CU_PPM` menjadi `'ppm'`, bukan
    `'%'` dari awalan `cu`.

    Versi modul ini pernah menyalin regex cadangannya saja, tanpa `elUnit`. Akibatnya `CU_PPM`
    dan `ZN_PPM` dihitung sebagai persen: untuk 1.000 t @ 50 ppm, aplikasi HTML memberi 50.000
    gram sedangkan Qt memberi 500 "t logam" -- salah 10.000 kali DAN salah satuan. Docstring
    lama di sini bahkan menyatakan aplikasi HTML yang keliru dan Qt sengaja menirunya; itu tidak
    benar, aplikasi HTML benar sejak awal.

    Catatan: `elUnit` juga menghormati penimpaan manual `BX.ui.rptU[a]`. Itu tidak ditiru di sini
    karena panel Qt belum punya kendalinya; bila nanti ada, ia harus diperiksa lebih dulu.
    """
    s = str(a).lower()
    # --- urutan elUnit(), persis ---
    if _re.search(r"(pct|perc|%|_p$|pc$)", s):
        return "%"
    if _re.search(r"ppm", s):
        return "ppm"
    if _re.search(r"ppb", s):
        return "ppb"
    if _re.search(r"(gpt|g_?t$|gt$)", s):
        return "g/t"
    if _re.match(r"^(au|ag|pt|pd)", s):
        return "g/t"
    if _re.match(r"^(cu|pb|zn|fe|mn|ni|s|sxs|scis|stot|c|al|si|mg|ca)", s):
        return "%"
    # --- elUnit mengembalikan '': barulah regex cadangan rpUnitDef ---
    if _re.match(r"^(cu|zn|pb|fe|s|stot|scis|c|mn)(_|pct|$)", a, _re.I) or \
            _re.search(r"pct$", a, _re.I):
        return "%"
    return "g/t"


def logam(ton: float, kadar: float, unit: str) -> float:
    """Logam terkandung -- padanan `rpMetal()`.

    '%'   -> ton logam (t x kadar / 100)
    'ppb' -> gram      (t x kadar / 1000; ppb x t = mg, jadi dibagi 1000 menjadi gram)
    lain  -> gram      (g/t dan ppm sama-sama gram per ton, jadi t x kadar langsung gram)
    """
    if unit == "%":
        return ton * kadar / 100.0
    if unit == "ppb":
        return ton * kadar / 1000.0
    return ton * kadar


def satuan_logam(unit: str) -> str:
    return "t logam" if unit == "%" else "gram"


def _nilai(G: Dict[str, Any], grup: str) -> Dict[str, Any]:
    return G.get(grup) or {"n": 0, "v": 0.0, "t": 0.0, "s": {}}


def _total(G: Dict[str, Any]) -> Dict[str, Any]:
    """Jumlah seluruh grup -- padanan rpTot(). Kadar dijumlahkan sebagai (tw, w), bukan dirata-rata
    dua kali: merata-ratakan rata-rata per grup akan memberi angka yang salah."""
    r: Dict[str, Any] = {"n": 0, "v": 0.0, "t": 0.0, "s": {}}
    for a in (G or {}).values():
        r["n"] += int(a.get("n") or 0)
        r["v"] += float(a.get("v") or 0.0)
        r["t"] += float(a.get("t") or 0.0)
        for at, q in (a.get("s") or {}).items():
            d = r["s"].setdefault(at, {"tw": 0.0, "w": 0.0})
            d["tw"] += float(q.get("tw") or 0.0)
            d["w"] += float(q.get("w") or 0.0)
    return r


def label_grup(hasil: Dict[str, Any], kunci: str, P: Optional[Pilihan] = None) -> str:
    """Label grup seperti di aplikasi: bench jadi 'RL <atas> – <bawah>', kategori apa adanya."""
    m = hasil["urut"][0]
    R = hasil["metode"][m]
    if (R.get("grp") or (P.grup if P else "none")) != "bench":
        return str(kunci)
    bh = float(R.get("bh") or (P.tinggi_bench if P else 5.0))
    br = float(R.get("br") or (P.rl_acuan if P else 0.0))     # mesin memakai nama 'br'
    try:
        k = int(kunci)
    except (TypeError, ValueError):
        return str(kunci)
    lo = br + k * bh
    return "RL %s – %s" % (_ribu(lo + bh, 1), _ribu(lo, 1))


def daftar_grup(hasil: Dict[str, Any]) -> List[str]:
    """Kunci grup yang muncul di hasil, URUTANNYA sama dengan aplikasi: bench dari RL tertinggi
    ke terendah (menurun), kategori menurut abjad."""
    nama: List[str] = []
    for m in hasil["urut"]:
        for baris in hasil["metode"][m].get("rows") or []:
            for g in (baris.get("G") or {}):
                if g not in nama:
                    nama.append(g)
    angka = all(_bisa_angka(g) for g in nama) and bool(nama)
    if angka:
        nama.sort(key=lambda s: -float(s))
    else:
        nama.sort(key=str)
    return nama


def _bisa_angka(s: Any) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def tabel(hasil: Dict[str, Any], grup: Optional[str] = None,
          P: Optional[Pilihan] = None) -> Tuple[List[str], List[List[str]]]:
    """Tabel siap tampil: satu baris per cut-off (per metode bila dibandingkan).

    `grup=None` berarti TOTAL seluruh grup (seperti tabel utama di aplikasi); `grup` yang diisi
    menampilkan satu grup saja (seperti tabel per RL / per kategori).

    Kolom: cut-off, [metode], blok, volume m3, tonase, lalu kadar rata-rata DAN logam terkandung
    tiap atribut. Bila kedua metode dihitung, ditambah baris 'Selisih' dalam ton dan persen.
    """
    banyak = len(hasil["urut"]) > 1
    judul = ["Cut-off"] + (["Metode"] if banyak else []) + ["Blok", "Volume m³", "Tonase t"]
    for a in hasil["atts"]:
        u = satuan(a)
        judul += ["%s (%s)" % (a, u), "Logam (%s)" % satuan_logam(u)]

    baris: List[List[str]] = []
    for i, c in enumerate(hasil["cuts"]):
        ton: Dict[str, float] = {}
        for m in hasil["urut"]:
            rows = hasil["metode"][m].get("rows") or []
            if i >= len(rows):
                continue
            G = rows[i].get("G") or {}
            v = _total(G) if grup is None else _nilai(G, grup)
            ton[m] = float(v.get("t") or 0.0)
            isi = ["≥ %g" % c] + ([NAMA_METODE.get(m, m)] if banyak else [])
            isi += [_ribu(v.get("n") or 0), _ribu(v.get("v") or 0.0, 1), _ribu(v.get("t") or 0.0, 1)]
            for a in hasil["atts"]:
                s = (v.get("s") or {}).get(a) or {}
                w = float(s.get("w") or 0.0)
                if w > 0:
                    g = float(s.get("tw") or 0.0) / w
                    u = satuan(a)
                    isi += ["%.3f" % g, _ribu(logam(float(v.get("t") or 0.0), g, u),
                                              1 if u == "%" else 0)]
                else:
                    isi += ["-", "-"]
            baris.append(isi)
        if banyak and len(ton) == 2:
            d = ton["presisi"] - ton["surpac"]
            persen = (100.0 * d / ton["surpac"]) if ton["surpac"] else float("nan")
            baris.append(["≥ %g" % c, "Selisih", "", "",
                          "%s t (%s)" % (_ribu(d, 1),
                                         "-" if persen != persen else "%+.1f%%" % persen)]
                         + [""] * (2 * len(hasil["atts"])))
    return judul, baris


def _ribu(v: float, desimal: int = 0) -> str:
    """Angka dengan pemisah ribuan titik dan desimal koma, seperti di aplikasi."""
    s = f"{float(v):,.{desimal}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def alasan_terbuang(hasil: Dict[str, Any], metode: Optional[str] = None) -> List[Tuple[str, int]]:
    """Jumlah blok yang terbuang per tahap penyaringan -- alasan 'kenapa tonasenya sekian'."""
    m = metode or hasil["urut"][0]
    nama = {"z": "di luar rentang RL", "poly": "di luar poligon", "flt": "tersaring filter atribut",
            "surf": "di luar permukaan atas/bawah", "sx": "di luar DTM tambahan",
            "dom": "di luar domain", "nan": "kadar tidak sah", "sg": "SG tidak sah",
            "frac": "proporsi volume nol"}
    out = hasil["metode"][m].get("nOut") or {}
    return [(nama.get(k, k), int(v)) for k, v in out.items() if int(v) > 0]


def catatan(bm: BlockModel, hasil: Dict[str, Any]) -> List[str]:
    """Peringatan yang harus dibaca BERSAMA angkanya, bukan sebagai hiasan.

    Yang paling penting: bila block model tidak punya atribut `sb_frac`, metode presisi tidak punya
    apa pun untuk ditimbang, sehingga kedua metode menghasilkan angka yang SAMA. Tanpa peringatan
    ini, selisih 0,0% mudah dibaca sebagai "sudah dibuktikan cocok", padahal yang terjadi adalah
    perbandingannya tidak berlaku -- model itu belum pernah di-sub-blocking.
    """
    pesan: List[str] = []
    if bm is not None and "sb_frac" not in bm.angka:
        pesan.append("Block model ini tidak punya atribut sb_frac, jadi tidak ada blok perbatasan "
                     "untuk ditimbang: kedua metode tonase menghasilkan angka yang sama. "
                     "Selisih 0% di sini BUKAN bukti kedua cara cocok — jalankan "
                     "sub-blocking dulu di aplikasi bila ingin membandingkannya.")
    if len(hasil.get("urut") or []) > 1:
        np_ = int((hasil["metode"].get("presisi") or {}).get("nPart") or 0)
        if np_:
            pesan.append("%s blok berada di perbatasan (proporsi < 1); itulah satu-satunya blok "
                         "yang dihitung berbeda oleh kedua metode." % _ribu(np_))
        buang = dict(alasan_terbuang(hasil, "presisi"))
        nol = buang.get("proporsi volume nol", 0)
        if nol:
            pesan.append("%s blok berproporsi NOL tidak dilaporkan sama sekali oleh metode presisi, "
                         "sedangkan metode Surpac tetap melaporkannya. Itu penyebab utama selisih "
                         "yang tampak besar." % _ribu(nol))
    if bm is not None and "sb_frac" in bm.angka and not (hasil.get("urut") or []):
        pesan.append("Metode tonase belum dibandingkan.")
    return pesan


def csv(hasil: Dict[str, Any], grup: Optional[str] = None) -> str:
    """Ekspor CSV. Angka ditulis dengan titik desimal supaya mudah dibaca ulang perangkat lain."""
    g = grup or (daftar_grup(hasil) or ["TOTAL"])[0]
    banyak = len(hasil["urut"]) > 1
    kol = ["cutoff"] + (["metode"] if banyak else []) + ["grup", "blok", "volume_m3", "tonase_t"]
    kol += ["%s_rata2" % a for a in hasil["atts"]]
    garis = [",".join(kol)]
    for i, c in enumerate(hasil["cuts"]):
        for m in hasil["urut"]:
            rows = hasil["metode"][m].get("rows") or []
            if i >= len(rows):
                continue
            v = _nilai(rows[i].get("G") or {}, g)
            isi = ["%g" % c] + ([m] if banyak else []) + [g, str(int(v.get("n") or 0)),
                                                          "%.4f" % float(v.get("v") or 0.0),
                                                          "%.4f" % float(v.get("t") or 0.0)]
            for a in hasil["atts"]:
                s = (v.get("s") or {}).get(a) or {}
                w = float(s.get("w") or 0.0)
                isi.append("%.6f" % (float(s.get("tw") or 0.0) / w) if w > 0 else "")
            garis.append(",".join(isi))
    garis.append("")
    garis.append("# Metode presisi GC-Ex menimbang blok perbatasan menurut proporsi volumenya")
    garis.append("# (sb_frac); blok berproporsi NOL tidak dilaporkan sama sekali.")
    garis.append("# Metode Seperti Surpac menghitung blok UTUH (Keep partial = False) dan")
    garis.append("# melaporkan semua blok yang lolos constraint, termasuk yang di luar solid.")
    garis.append("# Karena itu selisih yang besar bisa wajar; samakan dulu constraint domainnya.")
    garis.append("# Waste pengisi (area poligon tanpa blok BM) TIDAK termasuk di laporan ini --")
    garis.append("# itu hanya ada di perhitungan dig block per poligon.")
    return "\n".join(garis) + "\n"
