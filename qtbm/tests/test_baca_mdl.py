# -*- coding: utf-8 -*-
"""Uji pembacaan block model Surpac .mdl oleh penampil Qt.

Berkas .mdl sintetis dibuat dengan PEMBUAT YANG SAMA yang dipakai uji backend
(`backend/tests/test_mdl_io.py`), bukan penulis format kedua yang ditulis khusus untuk uji ini --
kalau formatnya ditulis dua kali, salah satunya akan menyimpang tanpa ada yang tahu.

Yang diperiksa: jumlah blok, ukuran blok (dihitung dari kotak akar dibagi 2^level octree, karena
.mdl tidak menyimpan ukuran per blok), titik tengah blok, atribut angka, atribut kategori beserta
kamus nilainya, dan pembatasan rentang RL.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))

pytest.importorskip("gcex_backend.mdl_io")

from test_mdl_io import O, RT, make_mdl           # noqa: E402  (pembuat .mdl milik uji backend)

from qtbm import proyek as PR                    # noqa: E402
from qtbm import tampil_bm as TB                 # noqa: E402


@pytest.fixture
def mdl(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    p = tmp_path / "uji.mdl"
    blok = make_mdl(p, n=800, seed=3)
    return p, blok


def test_baca_mdl_jumlah_dan_atribut(mdl):
    p, blok = mdl
    bm = PR.baca_bm(p)
    assert bm.n == len(blok)
    assert "au" in bm.angka and "pass" in bm.angka
    assert "rock" in bm.kategori and "ox" in bm.kategori
    # atribut kalkulasi (IIF) TIDAK tersimpan di berkas, jadi tidak boleh muncul di sini
    assert "kelas" not in bm.angka and "kelas" not in bm.kategori


def test_ukuran_blok_dari_level_octree(mdl):
    p, blok = mdl
    bm = PR.baca_bm(p)
    # level 1..3 -> ukuran 40 / 20 / 10 m pada kotak akar 80 m
    assert set(np.unique(np.round(bm.sz, 6))) <= {40.0, 20.0, 10.0}
    # setengah tinggi tiap blok harus cocok dengan yang dihitung pembuat berkas
    hz_harap = sorted(round(b[1], 6) for b in blok)
    assert sorted(np.round(bm.sz / 2, 6)) == hz_harap


def test_titik_tengah_z_cocok(mdl):
    p, blok = mdl
    bm = PR.baca_bm(p)
    assert sorted(np.round(bm.z, 6)) == sorted(round(b[0], 6) for b in blok)


def test_kategori_kamus_dan_kode(mdl):
    p, blok = mdl
    bm = PR.baca_bm(p)
    kode, daftar = bm.kategori["rock"]
    assert set(daftar) <= {"BX", "AND", "QV", "DAC"}
    # tiap blok harus menunjuk nilai yang benar menurut pembuat berkas
    terbaca = sorted(daftar[k] for k in kode if k != PR.KODE_KOSONG_KAT)
    assert terbaca == sorted(b[2] for b in blok)


def test_batas_rl_mengurangi_blok(mdl):
    p, _ = mdl
    penuh = PR.baca_bm(p)
    z0, z1 = O[2] + RT[2] * 0.25, O[2] + RT[2] * 0.6
    sebagian = PR.baca_bm(p, rl=(z0, z1))
    assert 0 < sebagian.n < penuh.n
    # mdl_io memilih blok yang BERIRISAN rentang, jadi titik tengahnya boleh sedikit di luar;
    # yang tidak boleh adalah blok yang seluruh tubuhnya di luar rentang
    assert np.all(sebagian.z + sebagian.sz / 2 > z0 - 1e-6)
    assert np.all(sebagian.z - sebagian.sz / 2 < z1 + 1e-6)


def test_cuplikan_maks(mdl):
    p, blok = mdl
    bm = PR.baca_bm(p, maks=100)
    assert 0 < bm.n <= 100


def test_mdl_bisa_langsung_diwarnai_panel(mdl):
    """Model .mdl harus langsung bisa dipakai aturan tampilan, termasuk atribut kategorinya."""
    p, _ = mdl
    bm = PR.baca_bm(p)
    T = TB.ui_awal(bm)
    assert T.atribut in bm.angka                  # 'au' atau 'pass'
    idx, cl = TB.pilih(bm, T)
    assert idx.size == bm.n and cl.min() >= 0
    T.atribut = "rock"
    idx2, cl2 = TB.pilih(bm, T)
    assert idx2.size == bm.n
    lg = TB.legenda(bm, T, cl2)
    assert sum(l[2] for l in lg) == idx2.size
