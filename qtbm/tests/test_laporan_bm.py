# -*- coding: utf-8 -*-
"""Uji laporan Block Model di penampil Qt: jembatan ke mesin hitung, tabel, catatan, CSV, panel.

Mesin hitungnya (`gcex_backend.laporan`) sudah punya uji paritasnya sendiri terhadap `rpRun()` JS
di `backend/tests/test_laporan.py`. Yang diuji DI SINI adalah lapisan Qt-nya, dan terutama hal-hal
yang bisa membuat angka benar ditampilkan salah:

  * total seluruh grup harus sama dengan laporan tanpa grup (kalau tidak, satu dari keduanya salah);
  * kadar rata-rata harus dijumlahkan sebagai (tonase x kadar, tonase) lalu dibagi -- BUKAN
    merata-ratakan rata-rata per grup;
  * metode "seperti Surpac" harus benar-benar mengabaikan sb_frac, dan metode presisi harus
    benar-benar memakainya (sakelar `frac` di Block Model bertipe boolean, bukan nama atribut --
    kekeliruan ini pernah membuat angka presisi diam-diam sama dengan angka Surpac);
  * bila block model TIDAK punya sb_frac, panel harus mengatakan bahwa perbandingan tidak berlaku,
    bukan menampilkan selisih 0% seolah-olah kedua cara sudah terbukti cocok.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

pytest.importorskip("gcex_backend.laporan")

from qtbm import laporan_bm as LB            # noqa: E402
from qtbm.proyek import BlockModel           # noqa: E402


@pytest.fixture
def bm() -> BlockModel:
    """Model kecil 4 x 4 x 4 blok 5 m, kadar menaik, sebagian blok diberi proporsi sub-blok."""
    rng = np.random.default_rng(11)
    x, y, z = np.meshgrid(np.arange(4) * 5.0 + 502.5, np.arange(4) * 5.0 + 1002.5,
                          np.arange(4) * 5.0 + 102.5, indexing="ij")
    n = x.size
    b = BlockModel(x=x.ravel(), y=y.ravel(), z=z.ravel(),
                   sx=np.full(n, 5.0), sy=np.full(n, 5.0), sz=np.full(n, 5.0), nama="uji")
    b.angka["AU_GC"] = np.linspace(0.05, 3.0, n)
    b.angka["SG"] = np.full(n, 2.6)
    b.kategori["DOM"] = (rng.integers(0, 2, n).astype(np.uint16), ["ORE", "WASTE"])
    return b


def pilih(**kw) -> LB.Pilihan:
    dasar = dict(kadar="AU_GC", cuts=[0.0, 0.5], atribut=["AU_GC"], sg=2.6)
    dasar.update(kw)
    return LB.Pilihan(**dasar)


# --------------------------------------------------------------- dasar
def test_tonase_sesuai_volume_kali_sg(bm):
    h = LB.jalankan(bm, pilih(cuts=[0.0]))
    j, b = LB.tabel(h)
    v = h["metode"]["presisi"]["rows"][0]["G"]
    tot = LB._total(v)
    assert tot["n"] == bm.n
    assert tot["v"] == pytest.approx(bm.n * 125.0)
    assert tot["t"] == pytest.approx(bm.n * 125.0 * 2.6)


def test_cutoff_menyaring_blok(bm):
    h = LB.jalankan(bm, pilih(cuts=[0.0, 0.5, 2.0]))
    n = [LB._total(r["G"])["n"] for r in h["metode"]["presisi"]["rows"]]
    assert n[0] == bm.n > n[1] > n[2] > 0
    assert n[1] == int(np.count_nonzero(bm.angka["AU_GC"] >= 0.5))


def test_total_grup_sama_dengan_tanpa_grup(bm):
    """Kalau kedua angka ini beda, salah satu tabel menipu pembacanya."""
    a = LB.jalankan(bm, pilih(cuts=[0.5]))
    b = LB.jalankan(bm, pilih(cuts=[0.5], grup="bench", tinggi_bench=5.0))
    ta = LB._total(a["metode"]["presisi"]["rows"][0]["G"])
    tb = LB._total(b["metode"]["presisi"]["rows"][0]["G"])
    assert ta["n"] == tb["n"]
    assert ta["t"] == pytest.approx(tb["t"])
    assert (ta["s"]["AU_GC"]["tw"] / ta["s"]["AU_GC"]["w"]
            == pytest.approx(tb["s"]["AU_GC"]["tw"] / tb["s"]["AU_GC"]["w"]))


def test_kadar_berbobot_tonase_bukan_rata_rata_sederhana(bm):
    """Blok dengan tonase berbeda harus menimbang kadar berbeda."""
    bm.sz = np.where(bm.angka["AU_GC"] > 1.5, 20.0, 5.0)       # blok kadar tinggi 4x lebih berat
    h = LB.jalankan(bm, pilih(cuts=[0.0]))
    t = LB._total(h["metode"]["presisi"]["rows"][0]["G"])
    berbobot = t["s"]["AU_GC"]["tw"] / t["s"]["AU_GC"]["w"]
    sederhana = float(bm.angka["AU_GC"].mean())
    assert berbobot > sederhana + 1e-6


# --------------------------------------------------------------- metode tonase
def test_surpac_mengabaikan_sb_frac_presisi_memakainya(bm):
    bm.angka["sb_frac"] = np.full(bm.n, 0.5)
    h = LB.jalankan(bm, pilih(cuts=[0.0], bandingkan=True))
    tp = LB._total(h["metode"]["presisi"]["rows"][0]["G"])["t"]
    ts = LB._total(h["metode"]["surpac"]["rows"][0]["G"])["t"]
    assert tp == pytest.approx(ts * 0.5)


def test_blok_proporsi_nol_tidak_dilaporkan_presisi(bm):
    fr = np.ones(bm.n)
    fr[:10] = 0.0
    bm.angka["sb_frac"] = fr
    h = LB.jalankan(bm, pilih(cuts=[0.0], bandingkan=True))
    assert LB._total(h["metode"]["presisi"]["rows"][0]["G"])["n"] == bm.n - 10
    assert LB._total(h["metode"]["surpac"]["rows"][0]["G"])["n"] == bm.n
    alasan = dict(LB.alasan_terbuang(h, "presisi"))
    assert alasan["proporsi volume nol"] == 10


def test_catatan_memperingatkan_bila_sb_frac_tidak_ada(bm):
    h = LB.jalankan(bm, pilih(cuts=[0.0], bandingkan=True))
    tp = LB._total(h["metode"]["presisi"]["rows"][0]["G"])["t"]
    ts = LB._total(h["metode"]["surpac"]["rows"][0]["G"])["t"]
    assert tp == pytest.approx(ts)              # memang sama...
    pesan = " ".join(LB.catatan(bm, h))
    assert "sb_frac" in pesan and "BUKAN bukti" in pesan     # ...dan itu harus dikatakan


def test_catatan_menyebut_blok_perbatasan(bm):
    fr = np.ones(bm.n)
    fr[:5] = 0.4
    bm.angka["sb_frac"] = fr
    h = LB.jalankan(bm, pilih(cuts=[0.0], bandingkan=True))
    assert "perbatasan" in " ".join(LB.catatan(bm, h))


def test_baris_selisih_ada_saat_dibandingkan(bm):
    bm.angka["sb_frac"] = np.full(bm.n, 0.5)
    h = LB.jalankan(bm, pilih(cuts=[0.0], bandingkan=True))
    _j, b = LB.tabel(h)
    assert [r[1] for r in b] == ["Presisi GC-Ex", "Seperti Surpac", "Selisih"]
    assert "-50" in b[2][4]                     # presisi 50% lebih rendah


# --------------------------------------------------------------- label, satuan, logam
# Nilai yang diharapkan di bawah DIAMBIL dari `elUnit()` ASLI aplikasi HTML, bukan dari bacaan
# saya atas kodenya. Versi lama daftar ini menuliskan ("CU_PPM", "%") dan ("ZN_PPM", "%") --
# keliru, dan karena ujinya memuat keyakinan yang keliru itu, ia LULUS sambil melindungi bug di
# `laporan_bm.satuan()` yang menghitung logam ppm 10.000 kali terlalu besar. Jangan mengubah
# nilai di sini tanpa menjalankan paritas terhadap aplikasi sungguhan lebih dulu.
@pytest.mark.parametrize("nama,unit", [
    ("AU_GC", "g/t"), ("AU", "g/t"), ("AU_GPT", "g/t"), ("AG", "g/t"), ("PT", "g/t"),
    ("S_PCT", "%"), ("CU_PCT", "%"), ("FE", "%"), ("CU", "%"), ("STOT", "%"),
    ("CU_PPM", "ppm"), ("ZN_PPM", "ppm"), ("AG_PPM", "ppm"), ("PB_PPM", "ppm"),
    ("AS_PPB", "ppb"), ("HG_PPB", "ppb"),
    ("XYZ", "g/t"),
])
def test_satuan_sama_dengan_aplikasi(nama, unit):
    assert LB.satuan(nama) == unit


def test_satuan_ppm_tidak_dianggap_persen():
    """Penjaga tegas: awalan unsur TIDAK boleh mengalahkan akhiran ppm / ppb.

    `elUnit` memeriksa ppm/ppb SEBELUM awalan unsur. Kalau urutannya terbalik, `CU_PPM` jadi '%'
    dan kolom logamnya salah 10.000 kali sekaligus salah satuan -- tanpa galat apa pun.
    """
    for a in ("CU_PPM", "ZN_PPM", "PB_PPM", "FE_PPM", "MN_PPM"):
        assert LB.satuan(a) == "ppm", a
    for a in ("AS_PPB", "CU_PPB"):
        assert LB.satuan(a) == "ppb", a


def test_logam_ppm_dalam_gram_bukan_ton():
    """1.000 t @ 50 ppm = 50.000 gram (50 kg), bukan 500 ton."""
    assert LB.logam(1000.0, 50.0, "ppm") == pytest.approx(50000.0)
    assert LB.satuan_logam("ppm") == "gram"


def test_logam_mengikuti_satuan():
    assert LB.logam(1000.0, 2.0, "g/t") == pytest.approx(2000.0)
    assert LB.logam(1000.0, 2.0, "%") == pytest.approx(20.0)
    assert LB.logam(1000.0, 2.0, "ppb") == pytest.approx(2.0)


def test_label_bench_rl_atas_bawah(bm):
    P = pilih(cuts=[0.0], grup="bench", tinggi_bench=5.0, rl_acuan=0.0)
    h = LB.jalankan(bm, P)
    g = LB.daftar_grup(h)
    # urutan harus menurun (RL tertinggi lebih dulu), seperti di aplikasi
    assert [float(s) for s in g] == sorted((float(s) for s in g), reverse=True)
    lab = LB.label_grup(h, g[0], P)
    assert lab.startswith("RL ") and "–" in lab


def test_grup_kategori_memakai_nama_nilainya(bm):
    P = pilih(cuts=[0.0], grup="cat", grup_atribut="DOM")
    h = LB.jalankan(bm, P)
    assert set(LB.daftar_grup(h)) <= {"ORE", "WASTE", "(kosong)"}


# --------------------------------------------------------------- CSV
def test_csv_berisi_angka_dan_penjelasan(bm):
    bm.angka["sb_frac"] = np.full(bm.n, 0.5)
    h = LB.jalankan(bm, pilih(cuts=[0.0], bandingkan=True))
    t = LB.csv(h)
    garis = t.splitlines()
    assert garis[0].startswith("cutoff,metode,grup,blok,volume_m3,tonase_t")
    assert any(g.startswith("0,presisi") for g in garis)
    assert any(g.startswith("0,surpac") for g in garis)
    # penjelasan metode WAJIB ikut, supaya angkanya tidak dibaca tanpa konteks
    assert any("Keep partial = False" in g for g in garis)
    assert any("Waste pengisi" in g for g in garis)


def test_csv_memakai_titik_desimal(bm):
    h = LB.jalankan(bm, pilih(cuts=[0.0]))
    isi = LB.csv(h).splitlines()[1]
    assert "," in isi and isi.count(".") >= 1       # pemisah kolom koma, desimal titik


# --------------------------------------------------------------- panel Qt
@pytest.fixture(scope="module")
def app():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    yield QApplication.instance() or QApplication([])


def test_panel_menghitung_dan_mengisi_tabel(app, bm):
    from qtbm.panel_laporan import PanelLaporan

    p = PanelLaporan()
    p.pasang_model(bm)
    assert p.cmb_kadar.currentText() == "AU_GC"
    p.ed_cuts.setText("0, 0.5")
    p.hitung()
    assert p.hasil is not None
    assert p.tabel.rowCount() == 2
    assert p.b_csv.isEnabled()
    assert "blok dihitung" in p.pesan.text()


def test_panel_tidak_memilih_kolom_sg_otomatis(app, bm):
    """Bawaannya SG TETAP, sama dengan aplikasi HTML (bxDefUI menyetel sgCol kosong).

    Kalau panel memilih kolom SG sendiri, tonase bawaan kedua aplikasi akan berbeda untuk model
    yang sama -- selisih yang tidak akan dicari orang karena tidak ada yang mengubah apa pun.
    """
    from qtbm.panel_laporan import PanelLaporan

    p = PanelLaporan()
    p.pasang_model(bm)
    assert (p.cmb_sg.currentData() or "") == ""
    p.ed_cuts.setText("0")
    p.hitung()
    t = LB._total(p.hasil["metode"]["presisi"]["rows"][0]["G"])["t"]
    assert t == pytest.approx(bm.n * 125.0 * 2.6)


def test_sg_diambil_dari_panel_tampilan_bila_dipasang(app, bm):
    """SG punya satu sumber: panel Tampilan. Di aplikasi HTML pun laporan membaca BX.ui.sg."""
    from qtbm.panel_laporan import PanelLaporan

    p = PanelLaporan()
    p.sumber_sg = lambda: (3.1, "")
    p.pasang_model(bm)
    assert not p.spn_sg.isEnabled() and "panel Tampilan" in p.lbl_sg.text()
    p.ed_cuts.setText("0")
    p.hitung()
    t = LB._total(p.hasil["metode"]["presisi"]["rows"][0]["G"])["t"]
    assert t == pytest.approx(bm.n * 125.0 * 3.1)

    p.sumber_sg = lambda: (2.6, "SG")        # kolom SG dari panel Tampilan ikut dipakai
    p.hitung()
    t2 = LB._total(p.hasil["metode"]["presisi"]["rows"][0]["G"])["t"]
    assert t2 == pytest.approx(bm.n * 125.0 * 2.6)


def test_panel_tanpa_model_tidak_merusak(app):
    from qtbm.panel_laporan import PanelLaporan

    p = PanelLaporan()
    p.pasang_model(None)
    p.hitung()
    assert p.hasil is None


def test_panel_saringan_dipakai_bila_dicentang(app, bm):
    from qtbm.panel_laporan import PanelLaporan

    p = PanelLaporan()
    p.pasang_model(bm)
    p.ed_cuts.setText("0")
    p.hitung()
    penuh = LB._total(p.hasil["metode"]["presisi"]["rows"][0]["G"])["n"]
    separuh = np.zeros(bm.n, bool)
    separuh[: bm.n // 2] = True
    p.saringan_aktif = lambda: separuh
    p.cb_rl.setChecked(True)
    p.hitung()
    assert LB._total(p.hasil["metode"]["presisi"]["rows"][0]["G"])["n"] == bm.n // 2 < penuh


# --------------------------------------------------------------- paritas berkas beku
BEKU = Path(__file__).parent / "data" / "laporan_bm_js.json"


@pytest.mark.skipif(not BEKU.exists(), reason="berkas paritas laporan JS belum dibuat")
def test_paritas_laporan_dengan_js_beku():
    """Angka laporan Qt harus sama dengan `rpRun()` aplikasi Block Model sungguhan.

    Berkasnya dibuat `python tools/uji/paritas_laporan_bm.py --fixture`: aplikasi HTML dibuka
    dengan data latihan, rpRun() asli dijalankan untuk 7 susunan pilihan (SG tetap, kolom SG,
    beberapa atribut, per RL 5 m, per RL 10 m dengan RL acuan, metode seperti Surpac, per
    kategori), lalu hasilnya dibekukan. Di sini susunan yang sama dihitung lewat lapisan Qt dan
    dibandingkan: jumlah blok, volume, tonase, dan (tw, w) kadar tiap atribut per grup.
    """
    sys.path.insert(0, str(ROOT / "tools" / "uji"))
    import importlib

    PB = importlib.import_module("paritas_laporan_bm")
    d = json.loads(BEKU.read_text(encoding="utf-8"))
    bm = PB.model_dari(d)
    assert d["kasus"], "berkas paritas tidak memuat satu kasus pun"
    for ks in d["kasus"]:
        assert not ks.get("err"), "%s: %s" % (ks["nama"], ks.get("err"))
        P = PB.pilihan_dari(ks["opsi"])
        h = LB.jalankan(bm, P)
        py = h["metode"][h["urut"][0]]["rows"]
        assert len(py) == len(ks["rows"]), ks["nama"]
        for jr, pr in zip(ks["rows"], py):
            assert set(jr["G"]) == set(pr["G"]), "%s cut-off %s" % (ks["nama"], jr["c"])
            for g, jv in jr["G"].items():
                pv = pr["G"][g]
                assert pv["n"] == jv["n"], "%s / %s / blok" % (ks["nama"], g)
                assert pv["v"] == pytest.approx(jv["v"], rel=1e-9, abs=1e-6)
                assert pv["t"] == pytest.approx(jv["t"], rel=1e-9, abs=1e-6)
                for a, jq in jv["s"].items():
                    pq = pv["s"][a]
                    assert pq["tw"] == pytest.approx(jq["tw"], rel=1e-9, abs=1e-6)
                    assert pq["w"] == pytest.approx(jq["w"], rel=1e-9, abs=1e-6)


def test_paritas_satuan_dengan_aplikasi_html():
    """Satuan atribut Qt = `rpUnitDef` aplikasi (elUnit dulu, baru regex cadangan).

    Dijalankan ulang dari hasil `elUnit()` ASLI yang dibekukan, atas 43 nama atribut, supaya
    URUTAN aturannya ikut teruji -- bukan hanya satu-dua contoh. Uji lama di berkas ini pernah
    menuliskan nilai yang keliru dari bacaan kode, lalu lulus sambil melindungi bug.
    """
    import json as _json
    import sys
    from pathlib import Path as _P

    beku = _P(__file__).parent / "data" / "laporan_bm_js.json"
    if not beku.exists():
        pytest.skip("hasil JS belum dibekukan")
    d = _json.loads(beku.read_text(encoding="utf-8"))
    if not d.get("elUnit"):
        pytest.skip("fixture belum memuat elUnit; bekukan ulang")
    sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "tools" / "uji"))
    import paritas_laporan_bm as PL

    salah = PL.bandingkan_satuan(d)
    assert not salah, "satuan Qt berbeda dari aplikasi HTML:\n" + "\n".join(salah)
