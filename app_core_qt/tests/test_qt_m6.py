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


def test_qaqc_manual_edit_paste(qtbot, prj, tmp_path, monkeypatch):
    """Tab Data: CRM_Data / Blank_Data / Duplicate_Data bisa diedit, ditambah, dihapus dan ditempel dari Excel; ID ganda ditandai."""
    w, pg, said = _open(qtbot, prj, tmp_path, monkeypatch)
    monkeypatch.setattr("corex.qaqc.ask", lambda *a, **k: False)
    pg.tabs.setCurrentIndex(6)
    pg.cbTbl.setCurrentIndex(pg.cbTbl.findData("CRM_Data"))
    qtbot.waitUntil(lambda: pg._tblShown == "CRM_Data" and pg.tT.rowCount() == 48, timeout=8000)
    assert not pg.tDirty and not pg.bSaveM.isEnabled() and pg._nbad == 0
    first = pg.tT.item(0, 0).text()
    # tempel dari Excel dengan baris judul (urutan kolom berbeda): satu baris baru + satu ID ganda
    pg.tT.setCurrentCell(-1, -1)
    n = pg.paste_rows(f"Lab_Grade\tSample_ID\tStandard_Name\n0,512\tZ7_MAN_001\tCRM-A\n0.5\t{first}\tCRM-A\n")
    assert n == 2 and pg.tT.rowCount() == 50 and pg.tDirty and pg.bSaveM.isEnabled()
    assert pg.tT.item(48, 0).text() == "Z7_MAN_001" and pg.tT.item(48, 2).text() == "0,512"
    assert "ganda" in pg.tT.item(49, 0).toolTip() and "ganda" in pg.tT.item(0, 0).toolTip()
    said.clear()
    assert pg.save_table() is False and "belum disimpan" in said[-1]
    assert pg.res["counts"]["crm_data"] == 48
    # hapus baris ganda, ketik angka tidak valid lalu perbaiki
    pg.tT.setCurrentCell(49, 0)
    pg.tT.clearSelection()
    pg.del_rows()
    assert pg.tT.rowCount() == 49 and not pg.tT.item(0, 0).toolTip()
    pg.tT.item(48, 2).setText("abc")
    assert "bukan angka" in pg.tT.item(48, 2).toolTip() and pg._nbad == 1
    pg.tT.item(48, 2).setText("0,515")
    assert pg._nbad == 0
    # + Baris di tengah, lalu tempel posisi (tanpa judul) mulai sel terpilih
    pg.tT.setCurrentCell(48, 0)
    pg.add_row()
    assert pg.tT.rowCount() == 50 and pg.tT.currentRow() == 49
    pg.paste_rows("Z8_MAN_002\tCRM-B\t1.47\tZ8\r\n")
    assert pg.tT.item(49, 3).text() == "Z8" and pg._nbad == 0
    assert pg.save_table() is True
    qtbot.waitUntil(lambda: pg.res and pg.res["counts"]["crm_data"] == 50 and not pg.tDirty, timeout=8000)
    # pindah tabel dengan perubahan belum disimpan -> ask (dijawab: buang)
    qtbot.waitUntil(lambda: pg.tT.rowCount() == 50, timeout=8000)
    pg.tT.item(0, 2).setText("9")
    assert pg.tDirty
    pg.cbTbl.setCurrentIndex(pg.cbTbl.findData("Duplicate_Data"))
    qtbot.waitUntil(lambda: pg._tblShown == "Duplicate_Data" and not pg.tDirty, timeout=8000)
    assert pg.res["counts"]["crm_data"] == 50


def test_qaqc_filter_batch_sample(qtbot, prj, tmp_path, monkeypatch):
    """Panel kontrol: filter Batch_ID (rentang, pilih dari daftar) dan Sample_ID (daftar tempel Excel); Hapus filter."""
    w, pg, said = _open(qtbot, prj, tmp_path, monkeypatch)
    pg.tabs.setCurrentIndex(8)
    assert pg.ed["batch_from"].count() == 25 and pg.ed["batch_from"].itemText(1) == "LAB26000"
    pg.ed["batch_from"].setCurrentText("LAB26000")
    pg.ed["batch_to"].setCurrentText("LAB26002")
    pg.save_settings()
    qtbot.waitUntil(lambda: pg.res and pg.res["filter_text"].startswith("Batch LAB26000 s.d. LAB26002"), timeout=8000)
    assert pg.bT.rowCount() == 3 and "Filter:" in pg.sum.text() and "Filter aktif" in pg.dWarn.text()
    # pilih batch dari daftar (dialog dijawab otomatis)
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QDialog

    def answer():
        dlg = pg._pickDlg
        lw = dlg.findChild(QListWidget)
        lw.item(lw.count() - 1).setCheckState(Qt.Checked)
        dlg.accept()
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QListWidget
    QTimer.singleShot(300, answer)
    pg.pick_batches()
    assert pg.ed["batch_list"].toPlainText() == "LAB26111"
    assert isinstance(pg._pickDlg, QDialog)
    pg.save_settings()
    qtbot.waitUntil(lambda: pg.res and len(pg.res["batches"]) == 4, timeout=8000)
    # daftar Sample_ID ditempel dari Excel (dengan judul kolom)
    pg.clear_filter()
    qtbot.waitUntil(lambda: pg.res and not pg.res["filter_text"], timeout=8000)
    assert pg.ed["batch_from"].currentText() == "" and pg.bT.rowCount() == 24
    pg.ed["sid_list"].setPlainText("Sample_ID\nZZ_TIDAK_ADA\n")
    pg.save_settings()
    qtbot.waitUntil(lambda: pg.res and pg.res["filter_text"].startswith("Sample_ID 1 ID daftar"), timeout=8000)
    assert "Tidak ada sampel QAQC dalam filter" in pg.dHead.text() and pg.ed["sid_list"].toPlainText() == "ZZ_TIDAK_ADA"
