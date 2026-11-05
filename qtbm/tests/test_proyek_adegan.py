# -*- coding: utf-8 -*-
"""Uji pembaca proyek & penyusun adegan penampil Qt.

Tidak memakai Qt maupun OpenGL, jadi bisa dijalankan tanpa layar. Yang diuji hal-hal yang bisa
dihitung dengan tangan: panjang jalur bor harus sama dengan kedalaman collar, ukuran blok yang
ditaksir, pembongkaran larik bersandi base64, penyaringan sayatan, dan -- yang paling mudah
terlewat -- ketelitian koordinat float32 di northing 9 juta.
"""
from __future__ import annotations

import base64
import json
import math
from pathlib import Path

import numpy as np
import pytest

from qtbm import adegan, proyek

LATIHAN = Path(__file__).resolve().parents[2] / "docs" / "tutorial-gcex" / "data" / "SIM_BM_GC_kadar.csv"


# ---------------------------------------------------------------------------
# pembaca proyek
# ---------------------------------------------------------------------------
def test_bongkar_larik_bersandi():
    """Larik angka di JSON aplikasi bersandi {"__ta": tipe, "b": base64}."""
    asli = np.array([1.5, -2.25, 1e6], dtype=np.float32)
    sandi = {"__ta": "Float32Array", "b": base64.b64encode(asli.tobytes()).decode()}
    hasil = proyek._bongkar({"nilai": sandi})["nilai"]
    assert isinstance(hasil, np.ndarray) and hasil.dtype == np.float32
    assert np.array_equal(hasil, asli)


def test_jalur_bor_sepanjang_kedalaman():
    """Lubang tegak 50 m: jalurnya harus 50 m dan ujungnya 50 m di bawah collar."""
    collars = [["H1", 1000.0, 2000.0, 300.0, 50.0]]
    surveys = [["H1", 0.0, -90.0, 0.0], ["H1", 50.0, -90.0, 0.0]]
    B = proyek.jalur_bor(collars, surveys)
    assert B.n == 1
    P = B.titik[0]
    panjang = float(np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1)))
    assert panjang == pytest.approx(50.0, abs=1e-9)
    assert P[-1][2] == pytest.approx(250.0, abs=1e-9)
    assert P[-1][0] == pytest.approx(1000.0, abs=1e-9)


def test_jalur_bor_miring_arah_benar():
    """Dip -45 azimut 90 (timur): ujungnya harus bergeser ke timur dan turun sama banyak."""
    L = 100.0
    B = proyek.jalur_bor([["H", 0.0, 0.0, 0.0, L]], [["H", 0.0, -45.0, 90.0], ["H", L, -45.0, 90.0]])
    P = B.titik[0][-1]
    assert P[0] == pytest.approx(L * math.cos(math.radians(45)), rel=1e-9)   # easting
    assert P[1] == pytest.approx(0.0, abs=1e-6)                              # northing
    assert P[2] == pytest.approx(-L * math.sin(math.radians(45)), rel=1e-9)  # turun


def test_jalur_bor_tanpa_survey_dianggap_tegak():
    B = proyek.jalur_bor([["H", 0.0, 0.0, 100.0, 20.0]], [])
    assert B.titik[0][-1][2] == pytest.approx(80.0, abs=1e-9)


def tulis_csv(p: Path, judul: str, baris: list) -> Path:
    p.write_text(judul + "\n" + "\n".join(baris) + "\n", encoding="utf-8")
    return p


def test_baca_csv_dengan_ukuran_blok(tmp_path):
    p = tulis_csv(tmp_path / "bm.csv", "X,Y,Z,XINC,YINC,ZINC,AU,DOMAIN",
                  ["100,200,50,5,5,2.5,1.25,ORE", "105,200,50,5,5,2.5,-99,WASTE"])
    bm = proyek.baca_bm(p)
    assert bm.n == 2
    assert bm.sx.tolist() == [5.0, 5.0] and bm.sz.tolist() == [2.5, 2.5]
    assert bm.volume() == pytest.approx(2 * 5 * 5 * 2.5)
    assert "AU" in bm.angka and "DOMAIN" in bm.kategori
    kode, daftar = bm.kategori["DOMAIN"]
    assert daftar == ["ORE", "WASTE"] and kode.tolist() == [0, 1]


def test_ukuran_blok_ditaksir_bila_tidak_ada_kolomnya():
    """Tanpa kolom XINC/YINC/ZINC, ukuran ditaksir dari jarak terkecil antar pusat blok."""
    import tempfile
    d = Path(tempfile.mkdtemp())
    p = tulis_csv(d / "bm.csv", "X,Y,Z,AU",
                  ["100,200,50,1", "110,200,50,2", "120,200,52,3", "100,210,50,4"])
    bm = proyek.baca_bm(p)
    assert bm.sx[0] == pytest.approx(10.0)
    assert bm.sy[0] == pytest.approx(10.0)
    assert bm.sz[0] == pytest.approx(2.0)
    assert "ditaksir" in bm.asal


def test_csv_tanpa_kolom_wajib_ditolak(tmp_path):
    p = tulis_csv(tmp_path / "bm.csv", "A,B,C", ["1,2,3"])
    with pytest.raises(ValueError):
        proyek.baca_bm(p)


def test_folder_bukan_proyek_ditolak(tmp_path):
    with pytest.raises(FileNotFoundError):
        proyek.buka_folder(tmp_path)


def test_folder_proyek_minimal(tmp_path):
    (tmp_path / proyek.BERKAS_DATA).write_text(json.dumps(
        {"name": "Uji", "collars": [["H", 0, 0, 100, 10]],
         "surveys": [["H", 0, -90, 0], ["H", 10, -90, 0]],
         "topoData": [[0, 0, 100.0], None, [5, 0, 100.5]]}), encoding="utf-8")
    (tmp_path / proyek.BERKAS_KERJA).write_text(json.dumps(
        {"meta": {"app": "dh", "name": "Uji"}, "body": {"work": {"src": {"name": "bm.csv"}}}}),
        encoding="utf-8")
    P = proyek.buka_folder(tmp_path)
    assert P.nama == "Uji" and P.aplikasi == "dh"
    assert P.bor.n == 1
    assert P.topo().shape == (2, 3)          # pemisah None dilewati
    assert P.asal_bm() == "bm.csv"


@pytest.mark.skipif(not LATIHAN.exists(), reason="data latihan tidak ada")
def test_baca_block_model_data_latihan():
    """Block model data latihan: 66.147 blok, volume 4.134.188 m3 (dihitung dari berkasnya)."""
    bm = proyek.baca_bm(LATIHAN)
    assert bm.n == 66147
    assert set(["AU_GC", "SG", "S_PCT", "ZN_PPM", "CU_PPM"]) <= set(bm.angka)
    assert "DOMAIN" in bm.kategori
    assert bm.volume() == pytest.approx(66147 * 5 * 5 * 2.5, rel=1e-9)


# ---------------------------------------------------------------------------
# penyusun adegan
# ---------------------------------------------------------------------------
def bm_uji(n=4, y0=9011697.5):
    """Block model kecil dengan northing ~9 juta BERKOMA -- keadaan yang menjebak float32."""
    x = np.array([505000.0 + 2.5 * i for i in range(n)])
    y = np.full(n, y0)
    z = np.array([240.0 + i for i in range(n)])
    s = np.full(n, 2.5)
    return proyek.BlockModel(x=x, y=y, z=z, sx=s, sy=s, sz=s,
                             angka={"AU": np.linspace(0.1, 2.0, n)}, nama="uji")


def test_koordinat_digeser_dulu_sebelum_float32():
    """Inti rancangan: digeser dalam float64 lalu float32 harus JAUH lebih teliti daripada
    langsung float32, pada koordinat tambang yang sebenarnya."""
    bm = bm_uji()
    A = adegan.susun(bm, atribut="AU")
    balik = A.pusat.astype(np.float64) + np.array(A.asal)
    asli = np.stack([bm.x, bm.y, bm.z], axis=1)
    kesalahan_digeser = float(np.abs(asli - balik).max())
    langsung = np.stack([bm.x.astype(np.float32), bm.y.astype(np.float32),
                         bm.z.astype(np.float32)], axis=1).astype(np.float64)
    kesalahan_langsung = float(np.abs(asli - langsung).max())
    assert kesalahan_digeser < 1e-3                      # di bawah milimeter
    assert kesalahan_langsung >= 0.4                      # dibulatkan ~setengah meter
    assert float(np.spacing(np.float32(9011700))) == 1.0  # dasar kejadiannya


def test_warna_angka_dan_penanda_tidak_ada_data():
    v = np.array([0.0, 0.5, 1.0, -99.0, np.nan])
    W = adegan.warna_angka(v, 0.0, 1.0)
    assert W.shape == (5, 4)
    assert tuple(W[3][:3]) == adegan.WARNA_KOSONG      # -99 = tidak ada data
    assert tuple(W[4][:3]) == adegan.WARNA_KOSONG      # NaN
    assert not np.array_equal(W[0][:3], W[2][:3])      # ujung tangga berbeda


def test_warna_kategori_kosong_abu():
    W = adegan.warna_kategori(np.array([0, 1, 65535], dtype=np.uint16))
    assert tuple(W[2][:3]) == adegan.WARNA_KOSONG
    assert not np.array_equal(W[0][:3], W[1][:3])


def test_saringan_rl_dan_atribut():
    bm = bm_uji(n=5)
    pakai = adegan.Saringan(rl=(241.0, 243.0)).terapkan(bm)
    assert pakai.tolist() == [False, True, True, True, False]
    pakai2 = adegan.Saringan(atribut="AU", rentang=(0.0, 1.0)).terapkan(bm)
    assert pakai2.sum() == int(np.count_nonzero(bm.angka["AU"] <= 1.0))


def test_saringan_sayatan_memilih_slab_tegak():
    """Sayatan berarah utara-selatan (azimut 0) tebal 6 m: hanya blok dalam 3 m dari bidang."""
    bm = bm_uji(n=5)              # x berjarak 2,5 m
    pakai = adegan.Saringan(sayatan=(bm.x[0], bm.y[0], 0.0, 6.0)).terapkan(bm)
    jarak = np.abs(bm.x - bm.x[0])
    assert pakai.tolist() == (jarak <= 3.0).tolist()


def test_adegan_blok_terpakai_saja():
    bm = bm_uji(n=5)
    A = adegan.susun(bm, atribut="AU", saringan=adegan.Saringan(rl=(241.0, 242.0)))
    assert A.n_blok == 2
    assert A.warna.shape == (2, 4)
    assert A.ukuran.shape == (2, 3)


def test_garis_bor_satu_rentang_per_lubang():
    B = proyek.jalur_bor([["A", 0, 0, 100, 10], ["B", 50, 0, 100, 10]],
                         [["A", 0, -90, 0], ["A", 10, -90, 0], ["B", 0, -90, 0], ["B", 10, -90, 0]])
    A = adegan.Adegan()
    adegan.garis_bor(A, B)
    assert A.garis_awal.size == 2
    assert int(A.garis_cacah.sum()) == A.garis.shape[0]
    assert A.garis_awal[1] == A.garis_cacah[0]


def test_permukaan_grid_dari_kisi_teratur():
    """Kisi 3 x 3 -> 4 sel -> 8 segitiga."""
    g = np.array([0.0, 5.0, 10.0])
    X, Y = np.meshgrid(g, g, indexing="ij")
    titik = np.stack([X.ravel(), Y.ravel(), np.full(9, 100.0)], axis=1)
    A = adegan.Adegan()
    adegan.permukaan_grid(A, titik)
    assert A.topo_simpul.shape == (9, 3)
    assert A.topo_indeks.size // 3 == 8


def test_permukaan_tidak_dipaksakan_bila_bukan_kisi():
    """Titik sebaran acak: jaring dibiarkan kosong, bukan dipaksa jadi segitiga yang salah."""
    rng = np.random.default_rng(3)
    titik = np.column_stack([rng.uniform(0, 100, 40), rng.uniform(0, 100, 40),
                             rng.uniform(90, 110, 40)])
    A = adegan.Adegan()
    adegan.permukaan_grid(A, titik)
    assert A.topo_indeks.size == 0


def test_adegan_kosong_tidak_melempar():
    A = adegan.susun(None)
    assert A.n_blok == 0 and A.garis.shape[0] == 0


# ---------------------------------------------------------------------------
# kamera & matriks (tidak butuh OpenGL)
# ---------------------------------------------------------------------------
def _proyeksi(mvp, titik):
    """Terapkan matriks ke satu titik; hasil koordinat layar -1..1."""
    v = np.array([titik[0], titik[1], titik[2], 1.0], dtype=np.float64)
    h = mvp.astype(np.float64) @ v
    return h[:3] / h[3]


def test_kubus_satuan_tertutup_36_simpul():
    from qtbm.render import kubus_satuan
    K = kubus_satuan()
    assert K.shape == (36, 6)
    assert np.abs(K[:, :3]).max() == pytest.approx(0.5)      # kubus satuan berpusat di nol
    # setiap sisi punya 6 simpul dengan normal sama
    normal = {tuple(r) for r in K[:, 3:]}
    assert len(normal) == 6


def test_kamera_sasaran_jatuh_di_tengah_layar():
    from qtbm.render import Kamera
    kam = Kamera()
    kam.pas_ke((-100, 100, -50, 50, 0, 20))
    p = _proyeksi(kam.mvp(800, 600), kam.sasaran)
    assert abs(p[0]) < 1e-6 and abs(p[1]) < 1e-6              # titik sasaran = tengah layar


def test_kamera_pas_ke_memasukkan_seluruh_kotak():
    from qtbm.render import Kamera
    kotak = (-250.0, 250.0, -150.0, 150.0, -40.0, 40.0)
    kam = Kamera()
    kam.pas_ke(kotak)
    mvp = kam.mvp(1000, 800)
    sudut = [(x, y, z) for x in kotak[0:2] for y in kotak[2:4] for z in kotak[4:6]]
    for s in sudut:
        p = _proyeksi(mvp, s)
        assert abs(p[0]) <= 1.0 and abs(p[1]) <= 1.0, "sudut %s keluar layar" % (s,)
        assert -1.0 <= p[2] <= 1.0, "sudut %s terpotong kedalaman" % (s,)


def test_kamera_putar_tidak_mengubah_jarak():
    from qtbm.render import Kamera
    kam = Kamera()
    kam.pas_ke((-10, 10, -10, 10, -10, 10))
    j0 = float(np.linalg.norm(kam.mata() - kam.sasaran))
    kam.azimut += 137.0
    kam.tunduk = -70.0
    j1 = float(np.linalg.norm(kam.mata() - kam.sasaran))
    assert j1 == pytest.approx(j0, rel=1e-12)


def test_kamera_tegak_lurus_tidak_pecah():
    """Melihat tepat dari atas: sumbu bantu harus diganti, bukan menghasilkan matriks NaN."""
    from qtbm.render import Kamera
    kam = Kamera()
    kam.pas_ke((-10, 10, -10, 10, -10, 10))
    kam.tunduk = 89.999
    mvp = kam.mvp(640, 480)
    assert np.isfinite(mvp).all()


def test_bm_contoh_uji_render_memakai_koordinat_tambang():
    """Block model buatan untuk uji render harus memakai northing 9 juta -- justru keadaan yang
    menjebak float32, supaya ujinya mewakili data sungguhan."""
    from qtbm.uji_render import bm_contoh
    b = bm_contoh(1000)
    assert b.n >= 900
    assert b.y.min() > 9_000_000
    A = adegan.susun(b, atribut="AU")
    assert np.abs(A.pusat).max() < 1000          # sudah digeser ke asal lokal


def test_kotak_proyeksi_memenuhi_layar():
    """Kotak yang sudah dipaskan kamera harus memenuhi sebagian besar layar dan berada di dalamnya.
    Ini dasar pemeriksaan letak di uji render CI, jadi diuji di sini juga."""
    from qtbm.render import Kamera
    from qtbm.uji_render import kotak_proyeksi
    kotak = (-300.0, 300.0, -200.0, 200.0, -50.0, 50.0)
    kam = Kamera()
    kam.pas_ke(kotak)
    kp = kotak_proyeksi(kotak, kam, 800, 600)
    assert kp is not None
    assert 0.0 <= kp[0] < kp[1] <= 1.0 and 0.0 <= kp[2] < kp[3] <= 1.0
    assert (kp[1] - kp[0]) > 0.3
