"""Uji tab Analisis di ruang kerja Singkapan (Qt): peta warna oksida (overlay & % per zona), deteksi jejak kekar -> set,
rose diagram, scanline, Jv / RQD / GSI dengan garis skala, segmentasi SAM otomatis, terima / buang usulan. Foto dinding fiktif."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))

import pytest  # noqa: E402

from test_qt_m1 import _win, prj  # noqa: E402,F401

pytest.importorskip("cv2")


def _open(qtbot, prj, tmp_path, monkeypatch):
    from buat_data_dummy import wall_photo
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    w.set_mode("oc")
    pg = w.outcrop
    src = tmp_path / "lapangan" / "Dinding_Latihan_W01.jpg"
    src.parent.mkdir()
    wall_photo(src)
    monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_photo()
    qtbot.waitUntil(lambda: pg.cur is not None and pg.view.w > 0, timeout=8000)
    pg.tabs.setCurrentIndex(4)
    said = []
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: said.append(a[1]))
    pg._said = said
    return w, pg


def test_analisis_color_traces_structure(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open(qtbot, prj, tmp_path, monkeypatch)
    assert pg.tabs.tabText(4) == "Analisis" and pg.anScan.count() == 1
    # peta warna oksida
    pg.anIdx.setCurrentIndex(0)
    pg.an_index(False)
    qtbot.waitUntil(lambda: pg._said or (pg.ovl is not None and "luas foto" in pg.anIdxInfo.text()), timeout=20000)
    assert not pg._said
    assert "m² perlu georef" in pg.anIdxInfo.text() and not pg.anIdxT.isVisible()
    pg.canvas.update()
    pg.an_index(True)
    qtbot.waitUntil(lambda: any(f["attrs"].get("_draft") == "indeks:oks" for f in pg.feats) and not pg.an_busy, timeout=20000)
    # jejak kekar -> struktur otomatis
    pg.an_traces()
    qtbot.waitUntil(lambda: pg.scan_res is not None and pg.anSetT.rowCount() == 2 and not pg.an_busy, timeout=30000)
    assert "Foto belum berskala" in pg.anStInfo.text() and sum(1 for f in pg.feats if f["attrs"].get("_draft") == "struktur") >= 15
    angles = sorted(int(pg.anSetT.item(i, 1).text().rstrip("°")) for i in range(2))
    assert abs(angles[0] - 65) <= 4 and abs(angles[1] - 160) <= 4
    pytest.importorskip("matplotlib")
    assert pg.anRose.pixmap() is not None and not pg.anRose.pixmap().isNull()
    # garis skala 18 m (dari pita ukur) + pelapukan W2 -> Jv, RQD, GSI; scanline pilihan
    from gcex_backend import core_outcrop as O
    s = O.store(pg.folder)
    O.save_feature(s, pg.cur["id"], None, {"kind": "skala", "pts": [[0, 0.99], [1, 0.99]], "attrs": {"length_m": 18}}, "uji")
    O.update_photo(s, pg.cur["id"], {"desc:weathering": "W2"}, "uji")
    pg._pick(0)
    pg.tabs.setCurrentIndex(4)
    assert pg.anScan.count() == 2
    pg.an_struct()
    qtbot.waitUntil(lambda: "GSI ≈ 75–85" in pg.anStInfo.text() and not pg.an_busy, timeout=20000)
    assert "Jv ≈" in pg.anStInfo.text() and "RQD ≈ <b>100</b>" in pg.anStInfo.text() and " m" in pg.anSetT.item(0, 3).text()
    pg.anScan.setCurrentIndex(1)
    pg.an_struct()
    qtbot.waitUntil(lambda: pg.scan_res and not pg.scan_res["auto"] and not pg.an_busy, timeout=20000)
    # terima semua usulan lalu hitung tanpa draf: jejak tetap ada (sudah diterima)
    pg.auto_accept(None)
    assert not any(f["attrs"].get("_draft") for f in pg.feats) and not pg.bAnAcc.isEnabled()
    pg.anDraft.setChecked(False)
    pg.an_struct()
    qtbot.waitUntil(lambda: pg.anSetT.rowCount() == 2 and "yang sudah diterima" in pg.anStInfo.text() and not pg.an_busy, timeout=20000)


def test_analisis_sam(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open(qtbot, prj, tmp_path, monkeypatch)
    if not pg.vision().get("sam"):
        pytest.skip("model SAM tidak tersedia")
    pg.anGrid.setCurrentIndex(pg.anGrid.findData("kasar"))
    pg.an_sam()
    qtbot.waitUntil(lambda: "zona usulan dari" in pg.anSamInfo.text(), timeout=180000)
    kinds = {f["kind"] for f in pg.feats if f["attrs"].get("_draft") == "sam"}
    assert {"zona_oks", "zona_lito"} <= kinds and pg.bAnRej.isEnabled()
    monkeypatch.setattr("corex.outcrop.ask", lambda *a, **k: True)
    pg.auto_reject(None)
    assert not pg.feats
