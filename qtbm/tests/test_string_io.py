# -*- coding: utf-8 -*-
"""Uji ekspor string (.str Surpac dan .dxf).

Paritas baris-per-baris terhadap `dgExport()` aplikasi HTML ada di `test_galian.py`
(`test_paritas_ekspor_dengan_aplikasi_html`). Yang di sini menjaga hal-hal yang kalau salah tidak
memunculkan galat apa pun: urutan Y,X di .str, titik penutup poligon, dan CRLF.
"""
from __future__ import annotations

import datetime as dt

import pytest

from qtbm import string_io as SIO


def _s(**kw):
    d = dict(no=1, ket="ORE", tertutup=True,
             pts=[(100.0, 200.0, 50.0), (110.0, 200.0, 50.0), (110.0, 210.0, 50.0)])
    d.update(kw)
    return SIO.String(**d)


# ---------------------------------------------------------------- .str

def test_str_urutan_y_lalu_x():
    """Surpac membaca .str sebagai Y, X, Z. Tertukar = poligon tercermin, tanpa galat apa pun."""
    teks = SIO.teks_str([_s()], "ZONA", tanggal=dt.date(2026, 1, 2))
    baris = teks.splitlines()[2]
    bagian = [b.strip() for b in baris.split(",")]
    assert bagian[1] == "200.000"        # Y (northing) lebih dulu
    assert bagian[2] == "100.000"        # X (easting) kedua
    assert bagian[3] == "50.000"


def test_str_poligon_tertutup_mengulang_titik_pertama():
    teks = SIO.teks_str([_s(tertutup=True)], "ZONA", tanggal=dt.date(2026, 1, 2))
    titik = [b for b in teks.splitlines() if b.startswith("1,")]
    assert len(titik) == 4               # 3 titik + penutup
    assert titik[0] == titik[-1]


def test_str_polyline_terbuka_tidak_mengulang():
    teks = SIO.teks_str([_s(tertutup=False)], "ZONA", tanggal=dt.date(2026, 1, 2))
    titik = [b for b in teks.splitlines() if b.startswith("1,")]
    assert len(titik) == 3


def test_str_offset_dikembalikan():
    teks = SIO.teks_str([_s()], "ZONA", off_x=500000.0, off_y=9000000.0,
                        tanggal=dt.date(2026, 1, 2))
    baris = teks.splitlines()[2]
    assert "9000200.000" in baris
    assert "500100.000" in baris


def test_str_koma_di_keterangan_diganti_spasi():
    """Koma di keterangan akan memecah kolom .str; aplikasi HTML menggantinya dengan spasi."""
    teks = SIO.teks_str([_s(ket="ORE, kanan")], "ZONA", tanggal=dt.date(2026, 1, 2))
    baris = teks.splitlines()[2]
    assert baris.endswith("ORE  kanan")


def test_str_kepala_dan_penutup():
    teks = SIO.teks_str([_s()], "Vein A/1", tanggal=dt.date(2026, 3, 9))
    baris = teks.splitlines()
    assert baris[0] == "String_Vein_A_1,09-Mar-26,,SSI_STYLES:styles.ssi"
    assert baris[1] == "0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000"
    assert baris[-1] == "0, 0.000, 0.000, 0.000, END"


def test_str_crlf():
    teks = SIO.teks_str([_s()], "ZONA", tanggal=dt.date(2026, 1, 2))
    assert "\r\n" in teks
    assert teks.endswith("\r\n")


def test_str_beberapa_string_dipisah_baris_nol():
    teks = SIO.teks_str([_s(no=1), _s(no=2)], "ZONA", tanggal=dt.date(2026, 1, 2))
    assert teks.count("0, 0.000, 0.000, 0.000,\r\n") == 2


# ---------------------------------------------------------------- .dxf

def test_dxf_koordinat_x_lalu_y():
    teks = SIO.teks_dxf([_s()])
    b = teks.splitlines()
    i = b.index("VERTEX")
    assert b[i + 3] == "10" and b[i + 4] == "100.000"    # X
    assert b[i + 5] == "20" and b[i + 6] == "200.000"    # Y


def test_dxf_bendera_tertutup():
    """70 = 9 untuk poligon tertutup, 8 untuk polyline terbuka."""
    bt = SIO.teks_dxf([_s(tertutup=True)]).splitlines()
    bb = SIO.teks_dxf([_s(tertutup=False)]).splitlines()
    assert bt[bt.index("POLYLINE") + 6] == "9"
    assert bb[bb.index("POLYLINE") + 6] == "8"


def test_dxf_nama_layer_dibersihkan():
    teks = SIO.teks_dxf([_s(ket="ORE kanan/atas", no=7)])
    assert "ORE_kanan_atas_7" in teks


def test_dxf_layer_cadangan_bila_keterangan_kosong():
    assert "STRING_3" in SIO.teks_dxf([_s(ket="", no=3)])


def test_dxf_rangka_lengkap():
    teks = SIO.teks_dxf([_s()])
    assert teks.startswith("0\r\nSECTION\r\n2\r\nHEADER")
    assert teks.rstrip().endswith("EOF")


# ---------------------------------------------------------------- tulis berkas

def test_tulis_str(tmp_path):
    p = tmp_path / "uji.str"
    SIO.tulis(p, [_s()], "ZONA")
    isi = p.read_bytes()
    assert b"\r\n" in isi
    assert b"\r\r\n" not in isi          # CRLF tidak boleh jadi CRCRLF


def test_tulis_dxf(tmp_path):
    p = tmp_path / "uji.dxf"
    SIO.tulis(p, [_s()])
    # read_bytes, bukan read_text: pembacaan teks mengubah CRLF jadi LF dan ujinya jadi palsu
    assert p.read_bytes().startswith(b"0\r\nSECTION")


def test_tulis_format_tak_dikenal_ditolak(tmp_path):
    with pytest.raises(ValueError):
        SIO.tulis(tmp_path / "uji.txt", [_s()])


# ---------------------------------------------------------------- String

def test_panjang_string():
    s = _s(pts=[(0.0, 0.0, 0.0), (3.0, 4.0, 0.0), (3.0, 4.0, 12.0)])
    assert s.panjang() == pytest.approx(17.0)


def test_xy_membuang_z():
    assert _s().xy() == [(100.0, 200.0), (110.0, 200.0), (110.0, 210.0)]
