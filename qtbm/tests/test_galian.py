# -*- coding: utf-8 -*-
"""Uji dig block (qtbm/galian.py).

Dua lapis:
  1. geometri dengan jawaban yang bisa dihitung tangan (luas, potong, di dalam / di tepi, flitch);
  2. paritas terhadap hasil `lyTon()` / `lyTonS()` ASLI aplikasi HTML yang dibekukan di
     `data/galian_bm_js.json` -- jadi CI memeriksanya tanpa peramban.

Lapis kedua yang menentukan. Lapis pertama hanya menjaga agar salah ketik tertangkap dengan pesan
yang jelas, bukan sebagai selisih tonase yang membingungkan.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from qtbm import galian as GA
from qtbm.proyek import BlockModel
from qtbm.tampil_bm import Tampilan

BEKU = Path(__file__).parent / "data" / "galian_bm_js.json"


# ---------------------------------------------------------------- geometri

def test_luas_persegi():
    assert GA.luas([(0, 0), (10, 0), (10, 5), (0, 5)]) == pytest.approx(50.0)


def test_luas_tidak_peduli_arah():
    P = [(0, 0), (10, 0), (10, 5), (0, 5)]
    assert GA.luas(P) == pytest.approx(GA.luas(list(reversed(P))))


def test_luas_segitiga():
    assert GA.luas([(0, 0), (4, 0), (0, 3)]) == pytest.approx(6.0)


def test_di_dalam():
    P = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert GA.di_dalam(P, 5, 5)
    assert not GA.di_dalam(P, 15, 5)
    assert not GA.di_dalam(P, 5, -1)


def test_di_tepi():
    P = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert GA.di_tepi(P, 5, 0)
    assert GA.di_tepi(P, 10, 4)
    assert not GA.di_tepi(P, 5, 5)


def test_di_dalam_atau_tepi_menangkap_titik_di_garis():
    """Blok yang titik tengahnya tepat di garis poligon HARUS ikut (metode Surpac)."""
    P = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert GA.di_dalam_atau_tepi(P, 0, 5)
    assert GA.di_dalam_atau_tepi(P, 10, 5)


def test_luas_terpotong_persegi_penuh():
    P = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert GA.luas_terpotong(P, (2, 4, 2, 4)) == pytest.approx(4.0)


def test_luas_terpotong_separuh():
    P = [(0, 0), (10, 0), (10, 10), (0, 10)]
    # persegi uji setengah di luar poligon
    assert GA.luas_terpotong(P, (-1, 1, 0, 10)) == pytest.approx(10.0)


def test_luas_terpotong_di_luar_nol():
    P = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert GA.luas_terpotong(P, (20, 22, 0, 2)) == 0.0


def test_luas_terpotong_segitiga():
    P = [(0, 0), (10, 0), (0, 10)]
    # persegi 0..2 x 0..2 seluruhnya di dalam segitiga (garis miring x+y=10)
    assert GA.luas_terpotong(P, (0, 2, 0, 2)) == pytest.approx(4.0)


def test_kotak_pembatas():
    assert GA.kotak([(1, 2), (5, 0), (3, 9)]) == (1, 5, 0, 9)


# ---------------------------------------------------------------- flitch

def _bm_satu_blok(z=100.0, sz=10.0):
    return BlockModel(x=np.array([0.0]), y=np.array([0.0]), z=np.array([z]),
                      sx=np.array([5.0]), sy=np.array([5.0]), sz=np.array([sz]))


def test_flitch_comp_sebagian():
    bm = _bm_satu_blok(z=100.0, sz=10.0)          # blok 95..105
    ov = GA.tebal_dalam_flitch(bm, (102.0, 98.0), "comp")
    assert float(ov[0]) == pytest.approx(4.0)     # 98..102


def test_flitch_comp_di_luar_nol():
    bm = _bm_satu_blok(z=100.0, sz=10.0)
    ov = GA.tebal_dalam_flitch(bm, (200.0, 190.0), "comp")
    assert float(ov[0]) == 0.0


def test_flitch_mid_memakai_tebal_flitch_penuh():
    """Mode 'mid' membengkakkan blok tipis jadi setebal flitch -- perilaku yang ditiru, bukan galat."""
    bm = _bm_satu_blok(z=100.0, sz=2.0)           # blok hanya 2 m tebal
    ov = GA.tebal_dalam_flitch(bm, (105.0, 95.0), "mid")   # flitch 10 m, tengahnya 100
    assert float(ov[0]) == pytest.approx(10.0)


def test_flitch_mid_tidak_kena_bidang_tengah():
    bm = _bm_satu_blok(z=90.0, sz=2.0)
    ov = GA.tebal_dalam_flitch(bm, (105.0, 95.0), "mid")
    assert float(ov[0]) == 0.0


def test_zs_flitch():
    assert GA.zs_flitch((105.0, 95.0)) == pytest.approx(100.0)


def test_bench_menukar_bila_terbalik():
    assert GA.bench(90.0, 110.0) == (110.0, 90.0)


# ---------------------------------------------------------------- tonase dasar

def test_tonase_satu_blok_penuh_presisi():
    bm = _bm_satu_blok(z=100.0, sz=10.0)
    T = Tampilan(sg=2.5)
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="clip", waste_on=False)
    P = [(-2.5, -2.5), (2.5, -2.5), (2.5, 2.5), (-2.5, 2.5)]
    H = GA.tonase(bm, P, T, O)
    assert H.n == 1
    assert H.v == pytest.approx(250.0)            # 5 x 5 x 10
    assert H.t == pytest.approx(625.0)            # x 2,5


def test_tonase_setengah_blok_presisi():
    """Poligon memotong blok tepat separuh -> volume separuh. Inilah inti metode presisi."""
    bm = _bm_satu_blok(z=100.0, sz=10.0)
    T = Tampilan(sg=2.0)
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="clip", waste_on=False)
    P = [(-2.5, -2.5), (0.0, -2.5), (0.0, 2.5), (-2.5, 2.5)]
    H = GA.tonase(bm, P, T, O)
    assert H.v == pytest.approx(125.0)
    assert H.t == pytest.approx(250.0)


def test_tonase_setengah_blok_surpac_ikut_utuh():
    """Metode Surpac: titik tengah blok (0,0) ada di TEPI poligon -> blok ikut UTUH."""
    bm = _bm_satu_blok(z=100.0, sz=10.0)
    T = Tampilan(sg=2.0)
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="surpac")
    P = [(-2.5, -2.5), (0.0, -2.5), (0.0, 2.5), (-2.5, 2.5)]
    H = GA.tonase(bm, P, T, O)
    assert H.n == 1
    assert H.v == pytest.approx(250.0)            # utuh, bukan separuh


def test_tonase_surpac_titik_tengah_di_luar_tidak_ikut():
    bm = _bm_satu_blok(z=100.0, sz=10.0)
    T = Tampilan(sg=2.0)
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="surpac")
    P = [(-2.5, -2.5), (-1.0, -2.5), (-1.0, 2.5), (-2.5, 2.5)]
    H = GA.tonase(bm, P, T, O)
    assert H.n == 0
    assert H.t == 0.0


def test_tonase_kadar_berbobot_tonase():
    bm = BlockModel(x=np.array([0.0, 10.0]), y=np.array([0.0, 0.0]),
                    z=np.array([100.0, 100.0]), sx=np.array([5.0, 5.0]),
                    sy=np.array([5.0, 5.0]), sz=np.array([10.0, 10.0]))
    bm.angka["AU"] = np.array([1.0, 3.0])
    T = Tampilan(sg=2.0)
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, kadar="AU", metode="surpac")
    P = [(-5.0, -5.0), (15.0, -5.0), (15.0, 5.0), (-5.0, 5.0)]
    H = GA.tonase(bm, P, T, O)
    assert H.n == 2
    assert H.kadar == pytest.approx(2.0)          # bobot tonase sama -> rata-rata biasa


def test_tonase_kadar_nan_tidak_ikut_rata_rata_tapi_tonase_tetap():
    bm = BlockModel(x=np.array([0.0, 10.0]), y=np.array([0.0, 0.0]),
                    z=np.array([100.0, 100.0]), sx=np.array([5.0, 5.0]),
                    sy=np.array([5.0, 5.0]), sz=np.array([10.0, 10.0]))
    bm.angka["AU"] = np.array([2.0, float("nan")])
    T = Tampilan(sg=2.0)
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, kadar="AU", metode="surpac")
    P = [(-5.0, -5.0), (15.0, -5.0), (15.0, 5.0), (-5.0, 5.0)]
    H = GA.tonase(bm, P, T, O)
    assert H.kadar == pytest.approx(2.0)
    assert H.t == pytest.approx(2 * 250.0 * 2.0)  # kedua blok tetap dilaporkan


def test_tonase_lubang_mengurangi():
    bm = _bm_satu_blok(z=100.0, sz=10.0)
    T = Tampilan(sg=2.0)
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="clip", waste_on=False)
    P = [(-2.5, -2.5), (2.5, -2.5), (2.5, 2.5), (-2.5, 2.5)]
    lubang = [[(-2.5, -2.5), (0.0, -2.5), (0.0, 2.5), (-2.5, 2.5)]]
    H = GA.tonase(bm, P, T, O, lubang)
    assert H.v == pytest.approx(125.0)


def test_waste_pengisi_hanya_presisi():
    """Asimetri yang ditiru dari aplikasi HTML: Surpac tidak pernah menambah waste pengisi."""
    bm = _bm_satu_blok(z=100.0, sz=10.0)
    T = Tampilan(sg=2.0)
    P = [(-10.0, -10.0), (10.0, -10.0), (10.0, 10.0), (-10.0, 10.0)]   # jauh lebih luas dari blok
    Oc = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="clip", waste_on=True, waste_sg=1.5)
    Os = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="surpac", waste_on=True, waste_sg=1.5)
    Hc = GA.tonase(bm, P, T, Oc)
    Hs = GA.tonase(bm, P, T, Os)
    assert Hc.waste_t > 0
    assert Hs.waste_t == 0.0
    assert Hs.waste_didukung is False


def test_waste_pengisi_bawaan_menyala():
    """Bawaan harus MENYALA, sama dengan `dbU()` di aplikasi HTML (U.wOn = true)."""
    assert GA.Opsi().waste_on is True


def test_coverage_memberi_tahu_luas_tak_tertutup():
    bm = _bm_satu_blok(z=100.0, sz=10.0)          # blok 25 m2
    T = Tampilan(sg=2.0)
    P = [(-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0)]   # 100 m2
    O = GA.Opsi(rl_atas=105.0, rl_bawah=95.0, metode="clip", waste_on=False)
    H = GA.tonase(bm, P, T, O)
    assert H.cov == pytest.approx(0.25)


def test_poligon_kurang_titik_ditolak():
    bm = _bm_satu_blok()
    with pytest.raises(ValueError):
        GA.tonase(bm, [(0, 0), (1, 1)], Tampilan(), GA.Opsi(rl_atas=105, rl_bawah=95))


def test_flitch_nol_ditolak():
    bm = _bm_satu_blok()
    P = [(-2.5, -2.5), (2.5, -2.5), (2.5, 2.5), (-2.5, 2.5)]
    with pytest.raises(ValueError):
        GA.tonase(bm, P, Tampilan(), GA.Opsi(rl_atas=100.0, rl_bawah=100.0))


# ---------------------------------------------------------------- SG per blok

def test_sg_tanpa_kolom():
    assert Tampilan(sg=2.7).sg_blok(float("nan")) == pytest.approx(2.7)


def test_sg_kolom_nilai_sah_dipakai():
    T = Tampilan(sg=2.6, sg_kolom="SG")
    assert T.sg_blok(3.1) == pytest.approx(3.1)


def test_sg_kolom_tidak_sah_jatuh_ke_sg_tunggal():
    """Cara GC-Ex ('rep') tanpa SG pengganti -> SG tunggal."""
    T = Tampilan(sg=2.6, sg_kolom="SG", sg_nol="rep")
    assert T.sg_blok(0.0) == pytest.approx(2.6)
    assert T.sg_blok(float("nan")) == pytest.approx(2.6)


def test_sg_kolom_bawaan_seperti_surpac():
    """0.24.70: bawaan = nilai bawaan atribut .mdl (blok yang tidak pernah diisi menyimpan nilai itu); tanpa .mdl = 0."""
    T = Tampilan(sg=2.6, sg_kolom="SG")
    assert T.sg_blok(0.0) == 0.0
    bm = BlockModel(x=np.zeros(2), y=np.zeros(2), z=np.zeros(2), sx=np.ones(2), sy=np.ones(2), sz=np.ones(2))
    bm.angka["SG"] = np.array([0.0, 3.0])
    bm.bawaan["SG"] = 2.5
    assert list(T.sg_larik(bm)) == pytest.approx([2.5, 3.0])


def test_sg_kolom_mode_zero():
    T = Tampilan(sg=2.6, sg_kolom="SG", sg_nol="zero")
    assert T.sg_blok(0.0) == 0.0


def test_sg_kolom_pengganti():
    T = Tampilan(sg=2.6, sg_kolom="SG", sg_nol="rep", sg_ganti="1.8")
    assert T.sg_blok(0.0) == pytest.approx(1.8)


def test_sg_larik_sama_dengan_per_blok():
    bm = BlockModel(x=np.zeros(4), y=np.zeros(4), z=np.zeros(4),
                    sx=np.ones(4), sy=np.ones(4), sz=np.ones(4))
    bm.angka["SG"] = np.array([2.0, 0.0, float("nan"), 3.0])
    T = Tampilan(sg=2.6, sg_kolom="SG", sg_ganti="1.8")
    L = T.sg_larik(bm)
    for i in range(4):
        assert L[i] == pytest.approx(T.sg_blok(bm.angka["SG"][i]))


# ---------------------------------------------------------------- paritas JS

def _muat():
    if not BEKU.exists():
        pytest.skip("hasil JS belum dibekukan; jalankan tools/uji/paritas_galian_bm.py")
    return json.loads(BEKU.read_text(encoding="utf-8"))


def test_fixture_ada_dan_tidak_kosong():
    d = _muat()
    assert d["n"] > 100
    assert len(d["kasus"]) >= 15


def test_fixture_benar_benar_menguji_cabang_sg():
    """Penjaga: bila ketiga kasus kolom SG memberi tonase sama, cabangnya tidak teruji."""
    d = _muat()
    t = {k["nama"]: k["hasil"]["t"] for k in d["kasus"] if k["nama"].startswith("kolom SG")}
    nilai = sorted(set(round(v, 6) for v in t.values()))
    assert len(nilai) >= 3, "kasus kolom SG memberi angka identik: cabang SG tidak teruji (%r)" % t


def test_fixture_kedua_metode_benar_benar_berbeda():
    """Penjaga: kalau presisi == surpac di semua kasus, ujinya tidak membedakan apa-apa."""
    d = _muat()
    H = {k["nama"]: k["hasil"]["t"] for k in d["kasus"]}
    beda = [a for a in H if " presisi" in a and a.replace(" presisi", " surpac") in H
            and abs(H[a] - H[a.replace(" presisi", " surpac")]) > 1e-6]
    assert beda, "tidak ada satu pun kasus di mana kedua metode berbeda"


def test_paritas_dengan_lyton_aplikasi_html():
    """Inti: angka dig block Qt harus sama persis dengan `lyTon()` / `lyTonS()` aplikasi HTML."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "uji"))
    import paritas_galian_bm as PG

    d = _muat()
    salah = PG.bandingkan(d)
    assert not salah, "dig block Qt berbeda dari aplikasi HTML:\n" + "\n".join(salah)


def test_paritas_ekspor_dengan_aplikasi_html():
    """Isi berkas .str dan .dxf harus sama baris per baris dengan `dgExport()` aplikasi HTML."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "uji"))
    import paritas_galian_bm as PG

    d = _muat()
    if not d.get("ekspor"):
        pytest.skip("fixture belum memuat keluaran dgExport; bekukan ulang")
    salah = PG.bandingkan_ekspor(d)
    assert not salah, "ekspor string Qt berbeda dari aplikasi HTML:\n" + "\n".join(salah)
