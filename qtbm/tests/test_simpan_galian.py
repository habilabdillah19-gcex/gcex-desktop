# -*- coding: utf-8 -*-
"""Uji penyimpanan string dig block ke folder proyek.

Yang dijaga di sini adalah hal-hal yang kalau salah **tidak memunculkan galat apa pun**:
offset koordinat (poligon pindah ratusan kilometer, berkasnya tetap sah), hash isi berkas
(berkas dianggap rusak oleh pihak lain), dan janji bahwa `gcex_project.json` milik aplikasi HTML
**tidak pernah ditulis** oleh penampil Qt.

Paritas terhadap `FP.hash` dan `offX`/`offY` aplikasi sungguhan dijalankan ulang dari hasil JS
yang dibekukan di `data/simpan_galian_js.json`, jadi CI memeriksanya tanpa peramban.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qtbm import simpan_galian as SG
from qtbm.proyek import Proyek
from qtbm.string_io import String

BEKU = Path(__file__).parent / "data" / "simpan_galian_js.json"


def _s(no=1, ket="ORE", tertutup=True, z=240.0):
    return String(no=no, ket=ket, tertutup=tertutup,
                  pts=[(504120.5, 9011240.25, z), (504160.5, 9011240.25, z),
                       (504160.5, 9011280.75, z)])


# ---------------------------------------------------------------- hash & pack

def test_hash_kosong():
    assert SG.hash_fp("") == "811c9dc5-1000193-0"


def test_hash_peka_isi():
    assert SG.hash_fp("a") != SG.hash_fp("b")


def test_hash_memakai_satuan_kode_utf16():
    """JavaScript menghitung emoji sebagai DUA satuan kode; Python harus sama."""
    h = SG.hash_fp("\U0001f600")
    assert h.rsplit("-", 1)[1] == "2", "panjang harus 2 satuan kode, bukan 1 titik kode"


def test_pack_unpack_bolak_balik():
    body = '{"dg":[],"offX":0,"offY":0}'
    teks, h = SG.pack({"format": "uji", "version": 1}, body)
    meta, obj = SG.unpack(teks)
    assert meta["hash"] == h
    assert obj == {"dg": [], "offX": 0, "offY": 0}


def test_unpack_menolak_hash_salah():
    body = '{"dg":[]}'
    teks, _h = SG.pack({"format": "uji"}, body)
    rusak = teks.replace('"dg":[]', '"dg":[1]')
    with pytest.raises(ValueError, match="hash"):
        SG.unpack(rusak)


def test_unpack_menolak_format_asing():
    with pytest.raises(ValueError, match="format"):
        SG.unpack('{"tidak ada body":1}')


# ---------------------------------------------------------------- offset

def test_offset_dari_collar():
    P = Proyek()
    P.data = {"collars": [["h1", 504123.4, 9011987.6, 0, 0], ["h2", 504999.0, 9011001.0, 0, 0]]}
    assert P.offset() == (504000.0, 9011000.0)


def test_offset_dari_anch_bila_tanpa_collar():
    P = Proyek()
    P.data = {"collars": [], "anch": [612345.0, 613000.0, 9122222.0, 9123000.0, 0, 100]}
    assert P.offset() == (612000.0, 9122000.0)


def test_offset_nol_bila_tidak_ada_apa_apa():
    P = Proyek()
    P.data = {}
    assert P.offset() == (0.0, 0.0)


def test_offset_collar_mengalahkan_anch():
    """Aplikasi HTML memakai ANCH HANYA bila tidak ada collar."""
    P = Proyek()
    P.data = {"collars": [["h", 504500.0, 9011500.0, 0, 0]],
              "anch": [1000.0, 2000.0, 3000.0, 4000.0]}
    assert P.offset() == (504000.0, 9011000.0)


def test_offset_koordinat_negatif_dibulatkan_ke_bawah():
    """floor, bukan pemotongan: -1234 harus jadi -2000, bukan -1000."""
    P = Proyek()
    P.data = {"collars": [["h", -1234.0, -5678.0, 0, 0]]}
    assert P.offset() == (-2000.0, -6000.0)


# ---------------------------------------------------------------- konversi offset

def test_konversi_bolak_balik_mempertahankan_koordinat():
    s = _s()
    d = SG.ke_html(s, 504000.0, 9011000.0)
    kembali = SG.dari_html(d, 504000.0, 9011000.0)
    for a, b in zip(s.pts, kembali.pts):
        assert a == pytest.approx(b)


def test_ke_html_mengurangi_offset():
    d = SG.ke_html(_s(), 504000.0, 9011000.0)
    assert d["pts"][0][0] == pytest.approx(120.5)
    assert d["pts"][0][1] == pytest.approx(240.25)
    assert d["pts"][0][2] == pytest.approx(240.0)      # RL tidak digeser


def test_dari_html_menambah_offset():
    s = SG.dari_html({"no": 2, "d": "X", "closed": True,
                      "pts": [[1.0, 2.0, 3.0], [4.0, 5.0, 3.0], [4.0, 9.0, 3.0]]},
                     504000.0, 9011000.0)
    assert s.pts[0] == (504001.0, 9011002.0, 3.0)


def test_dari_html_vis_tidak_ada_dianggap_tampil():
    s = SG.dari_html({"no": 1, "pts": [[0, 0, 0], [1, 0, 0], [1, 1, 0]]}, 0, 0)
    assert s.tampil is True


def test_dari_html_vis_false_disembunyikan():
    s = SG.dari_html({"no": 1, "vis": False, "pts": [[0, 0, 0], [1, 0, 0], [1, 1, 0]]}, 0, 0)
    assert s.tampil is False


# ---------------------------------------------------------------- berkas Qt

def test_tulis_lalu_baca(tmp_path):
    S = [_s(no=1), _s(no=2, ket="WASTE", tertutup=False)]
    SG.tulis(tmp_path, S, 504000.0, 9011000.0, nama_proyek="uji")
    S2, meta = SG.baca(tmp_path)
    assert meta["format"] == SG.FORMAT_QT
    assert meta["n"] == 2
    assert [x.no for x in S2] == [1, 2]
    assert S2[1].tertutup is False
    for a, b in zip(S[0].pts, S2[0].pts):
        assert a == pytest.approx(b)


def test_baca_folder_kosong_tidak_melempar(tmp_path):
    S, meta = SG.baca(tmp_path)
    assert S == [] and meta == {}


def test_tulis_memakai_berkas_sementara(tmp_path):
    """Tidak boleh ada .tmp tertinggal: itu tanda penulisan dua tahap tidak tuntas."""
    SG.tulis(tmp_path, [_s()], 0.0, 0.0)
    assert not list(tmp_path.glob("*.tmp"))
    assert (tmp_path / SG.BERKAS_QT).is_file()


def test_offset_tersimpan_di_berkas_dipakai_saat_membaca(tmp_path):
    """Kalau offset proyek berubah, string lama harus tetap kembali ke tempat yang benar."""
    S = [_s()]
    SG.tulis(tmp_path, S, 504000.0, 9011000.0)
    S2, _m = SG.baca(tmp_path)      # baca TIDAK diberi offset; ia memakai yang tersimpan
    for a, b in zip(S[0].pts, S2[0].pts):
        assert a == pytest.approx(b)


def test_berkas_rusak_dilaporkan_bukan_didiamkan(tmp_path):
    (tmp_path / SG.BERKAS_QT).write_text('{"format":"x","hash":"salah","body":{"dg":[]}}',
                                         encoding="utf-8")
    with pytest.raises(ValueError):
        SG.baca(tmp_path)


# ---------------------------------------------------------------- aplikasi HTML

def _proyek_palsu(tmp_path, dg):
    body = json.dumps({"work": {"dg": dg}, "dataHash": "x", "dataFile": "gcex_data.json"},
                      ensure_ascii=False, separators=(",", ":"))
    teks, _h = SG.pack({"format": "gcex-project", "version": 2, "rev": 3}, body)
    (tmp_path / SG.BERKAS_PROYEK).write_text(teks, encoding="utf-8")
    return teks


def test_baca_string_html(tmp_path):
    _proyek_palsu(tmp_path, [{"no": 5, "d": "ORE", "closed": True, "vis": True,
                              "pts": [[1, 2, 3], [4, 2, 3], [4, 6, 3]]}])
    S = SG.baca_string_html(tmp_path, 504000.0, 9011000.0)
    assert len(S) == 1 and S[0].no == 5
    assert S[0].pts[0] == (504001.0, 9011002.0, 3.0)


def test_baca_string_html_tanpa_berkas(tmp_path):
    assert SG.baca_string_html(tmp_path, 0, 0) == []


def test_baca_string_html_berkas_rusak_tidak_melempar(tmp_path):
    """Gagal membaca pekerjaan orang lain tidak boleh menghalangi pemakai memakai penampilnya."""
    (tmp_path / SG.BERKAS_PROYEK).write_text("bukan json sama sekali", encoding="utf-8")
    assert SG.baca_string_html(tmp_path, 0, 0) == []


def test_baca_string_html_melewati_string_terlalu_pendek(tmp_path):
    _proyek_palsu(tmp_path, [{"no": 1, "pts": [[0, 0, 0]]},
                             {"no": 2, "pts": [[0, 0, 0], [1, 1, 0]]}])
    S = SG.baca_string_html(tmp_path, 0, 0)
    assert [x.no for x in S] == [2]


def test_menulis_tidak_menyentuh_berkas_proyek(tmp_path):
    """Janji inti modul ini: gcex_project.json milik aplikasi HTML tidak pernah ditulis."""
    asli = _proyek_palsu(tmp_path, [{"no": 1, "pts": [[0, 0, 0], [1, 0, 0], [1, 1, 0]]}])
    SG.tulis(tmp_path, [_s(), _s(no=9)], 0.0, 0.0)
    assert (tmp_path / SG.BERKAS_PROYEK).read_text(encoding="utf-8") == asli


# ---------------------------------------------------------------- paritas JS

def _muat():
    if not BEKU.exists():
        pytest.skip("hasil JS belum dibekukan; jalankan tools/uji/paritas_simpan_galian.py")
    return json.loads(BEKU.read_text(encoding="utf-8"))


def test_paritas_hash_dengan_aplikasi_html():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "uji"))
    import paritas_simpan_galian as PS

    d = _muat()
    salah = PS.bandingkan_hash(d)
    assert not salah, "FP.hash Python berbeda dari aplikasi HTML:\n" + "\n".join(salah)


def test_paritas_offset_dengan_aplikasi_html():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "uji"))
    import paritas_simpan_galian as PS

    d = _muat()
    salah = PS.bandingkan_offset(d)
    assert not salah, "offX/offY Python berbeda dari aplikasi HTML:\n" + "\n".join(salah)


def test_paritas_baca_berkas_proyek_asli():
    """Berkas gcex_project.json yang dibaca di sini dibuat `FP.pack` + `SA.collectWork` ASLI."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "uji"))
    import paritas_simpan_galian as PS

    d = _muat()
    if not d.get("proyek"):
        pytest.skip("fixture belum memuat berkas proyek; bekukan ulang")
    salah = PS.bandingkan_proyek(d)
    assert not salah, "pembacaan berkas proyek berbeda:\n" + "\n".join(salah)


def test_fixture_offset_tidak_nol():
    """Penjaga: offset nol akan membuat uji paritas lulus tanpa menguji pergeseran apa pun."""
    d = _muat()
    assert d["offX"] and d["offY"], "offset fixture nol: uji pergeseran koordinat jadi hampa"
