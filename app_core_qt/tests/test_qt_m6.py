"""Uji ruang kerja QAQC (Qt): mode QAQC, impor workbook QAQC fiktif, dashboard per zona, tab CRM / Blank / Duplikat / Batch /
Lampiran / Data, simpan Master_CRM, panel kontrol, QAQC data bor, ekspor Excel + PNG, laporan PDF. Semua data fiktif."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))

import pytest  # noqa: E402

from test_qt_m1 import _win, prj  # noqa: E402,F401


def _open(qtbot, prj, tmp_path, monkeypatch):
    from buat_data_dummy import qaqc_data
    from gcex_backend import core_qaqc
    core_qaqc._STORES.clear()
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    w.set_mode("qa")
    pg = w.qaqc
    assert w.stack.currentWidget() is pg and w.bModeQa.isChecked() and not w.fbar.isVisible()
    qtbot.waitUntil(lambda: pg.res is not None, timeout=8000)
    assert "Belum ada data QAQC" in pg.dHead.text() and not pg.bPdf.isEnabled()
    wbp = qaqc_data(tmp_path / "dummy")
    said = []
    monkeypatch.setattr("corex.qaqc.say", lambda *a, **k: said.append(a[1]))
    monkeypatch.setattr("corex.qaqc.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(wbp)], ""))
    pg.cbTarget.setCurrentIndex(0)
    pg.import_files()
    qtbot.waitUntil(lambda: bool(said) and pg.res and pg.res["counts"]["crm_data"] == 48, timeout=15000)
    return w, pg, said


def test_qaqc_import_dashboard_tabs_settings(qtbot, prj, tmp_path, monkeypatch):
    w, pg, said = _open(qtbot, prj, tmp_path, monkeypatch)
    assert "CRM_Data: 48 baru" in said[0] and "ID ganda" in said[0]
    assert pg.dT.rowCount() == 2 and pg.dT.item(0, 4).text() == "Perlu tindakan korektif" and pg.bPdf.isEnabled()
    assert pg.tCrm.rowCount() == 7 and "PASS" in pg.tCrm.item(6, 8).text()
    assert pg.tBlk.rowCount() == 2 and pg.tDup.rowCount() == 9 and "R² seluruh pasangan" in pg.nDup.text()
    assert pg.bT.rowCount() == 24
    # grafik dimuat saat tab dibuka
    pytest.importorskip("matplotlib")
    pg.tabs.setCurrentIndex(1)
    qtbot.waitUntil(lambda: len(pg.cCrm.labels) == 6 and all(lb.pixmap() and not lb.pixmap().isNull() for lb in pg.cCrm.labels), timeout=30000)
    # lampiran A
    pg.cbApp.setCurrentIndex(0)
    pg.show_app()
    qtbot.waitUntil(lambda: pg.aT.rowCount() == 6, timeout=5000)
    # Data: Master_CRM bisa diedit & disimpan
    pg.cbTbl.setCurrentIndex(0)
    qtbot.waitUntil(lambda: pg.tT.rowCount() == 3, timeout=5000)
    pg.tT.item(0, 2).setText("0.030")
    pg.save_master()
    # SD CRM-A lebih lebar: WARNING CRM-A hilang, CRM tertukar tetap FAIL
    qtbot.waitUntil(lambda: pg.res and pg.res["totals"]["crm"] == {"PASS": 44, "WARN": 1, "FAIL": 3}, timeout=8000)
    # panel kontrol: zona Z7
    pg.ed["zone"].setCurrentText("Z7")
    pg.save_settings()
    qtbot.waitUntil(lambda: pg.res and pg.res["zones"] == ["Z7"], timeout=8000)
    assert pg.dT.rowCount() == 1 and "Zona: Z7" in pg.sum.text()
    pg.reset_settings()
    qtbot.waitUntil(lambda: pg.res and pg.res["zones"] == ["Z7", "Z8"], timeout=8000)


def test_qaqc_exports_and_drillhole(qtbot, prj, tmp_path, monkeypatch):
    pytest.importorskip("matplotlib")
    w, pg, _said = _open(qtbot, prj, tmp_path, monkeypatch)
    monkeypatch.setattr("corex.qaqc.show_in_folder", lambda p: None)
    out = tmp_path / "keluar"
    out.mkdir()
    monkeypatch.setattr("corex.qaqc.QFileDialog.getSaveFileName", lambda *a, **k: (str(out / "QAQC_uji"), ""))
    pg.export_xlsx()
    qtbot.waitUntil(lambda: (out / "QAQC_uji.xlsx").exists() and len(list((out / "QAQC_uji_grafik").glob("*.png"))) > 5, timeout=60000)
    monkeypatch.setattr("corex.qaqc.QFileDialog.getSaveFileName", lambda *a, **k: (str(out / "Laporan"), ""))
    pg.export_pdf()
    qtbot.waitUntil(lambda: (out / "Laporan.pdf").exists() and (out / "Laporan.pdf").stat().st_size > 50000, timeout=60000)
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(out / "Laporan.pdf"))
    t = doc[0].get_textpage().get_text_range()
    assert len(doc) >= 4 and "Ringkasan Eksekutif" in t and "KESEHATAN DATA" in t and f"1 / {len(doc)}" in t
    # data bor kosong -> petunjuk
    pg.tabs.setCurrentIndex(7)
    pg.run_dh()
    qtbot.waitUntil(lambda: "Belum ada data bor" in pg.dhInfo.text(), timeout=5000)
