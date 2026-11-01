"""Uji ruang kerja Borang (Qt): mode Borang, tambah scan, AI (Ollama tiruan), sel ragu / galat, edit, verifikasi,
pivot, ekspor Excel & SQLite, AI gagal = tabel tidak diisi. Semua data fiktif."""
import json
import os
import sqlite3
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QColor  # noqa: E402

from test_qt_m1 import _win, prj  # noqa: E402,F401

ORE_AI = {"header": {"tanggal": "30-Oct-26", "shift": "Siang", "spotter": "Spotter A", "pit": "PIT-X", "block": "24", "elevasi": "250",
                     "jenis_ore": "OX-LG", "tujuan": "ROM 418", "ragu": ["spotter"]},
          "rows": [{"jam": "06:30", "id_truk": "DT4035", "jenis_ore": "", "tujuan": "", "ton": "30", "ragu": []},
                   {"jam": "06:46", "id_truk": "DT4046", "jenis_ore": "OX-LG", "tujuan": "ROM 418", "ton": "30", "ragu": ["id_truk"]},
                   {"jam": "07:05", "id_truk": "DT4051", "jenis_ore": "OX-MO", "tujuan": "Crusher", "ton": "3O", "ragu": ["ton"]}]}


def _scan(tmp):
    f = tmp / "lapangan" / "Borang_Spotter_fiktif.jpg"
    f.parent.mkdir(exist_ok=True)
    im = Image.new("RGB", (1000, 1300), "white")
    dr = ImageDraw.Draw(im)
    for y in range(120, 1300, 50):
        dr.line([(40, y), (960, y)], fill="black", width=2)
    im.save(f)
    return f


def _open_forms(qtbot, prj, tmp_path, monkeypatch):
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    w.set_mode("form")
    pg = w.forms
    assert w.stack.currentWidget() is pg and not w.fbar.isVisible() and w.bModeForm.isChecked()
    assert pg.cbNew.count() == 2 and pg.lst.count() == 0
    src = _scan(tmp_path)
    monkeypatch.setattr("corex.forms.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.cbNew.setCurrentIndex(pg.cbNew.findData("ore"))
    pg.add_files()
    qtbot.waitUntil(lambda: pg.cur is not None and pg.view.w > 0, timeout=8000)
    return w, pg


def _fake_ai(w, monkeypatch, res=None, fail=False):
    from corex.api import core_io

    def fake(url, body=None, timeout=5.0):
        if fail:
            raise RuntimeError("Ollama tidak menjawab")
        return {"message": {"content": json.dumps(res)}}
    monkeypatch.setattr(core_io, "_http", fake)
    w.ai.info = {"running": True}
    monkeypatch.setattr(w.ai, "model", lambda: "qwen2.5vl:7b")


def test_forms_ai_review_verify_export(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    assert pg.cur["doc"]["type"] == "ore" and pg.t.rowCount() == 0 and "Borang_Spotter_fiktif" in pg.lst.item(0).text()
    # putar scan -> tersimpan di borang
    pg.view.btn["rot"].click()
    assert pg.cur["doc"]["rot"] == 90
    _fake_ai(w, monkeypatch, ORE_AI)
    pg.run_ai()
    qtbot.waitUntil(lambda: not pg.ai_busy and pg.t.rowCount() == 3, timeout=8000)
    assert pg.hdrEd["pit"].text() == "PIT-X" and pg.hdrEd["spotter"].styleSheet()  # header ragu disorot
    cols = [k for k, _l in pg.cols(pg.types["ore"])]
    ton, truk = 1 + cols.index("ton"), 1 + cols.index("id_truk")
    assert pg.t.item(1, truk).background().color() == QColor("#fff3bf")  # AI ragu
    assert pg.t.item(2, ton).background().color() == QColor("#ffe3e3") and "angka" in pg.t.item(2, ton).toolTip()  # galat
    assert pg.t.item(0, pg.t.columnCount() - 1).text().startswith("PIT-X_250_24_")  # kunci poligon turunan
    # perbaiki sel -> tersimpan, sorotan hilang
    pg.t.item(2, ton).setText("30")
    qtbot.waitUntil(lambda: pg.cur["valid"]["n"] == 0, timeout=4000)
    assert pg.cur["rows"][2]["data"]["ton"] == "30" and not pg.cur["rows"][2]["unc"]
    # pivot per shift
    assert pg.pv["shift"].rowCount() == 1 and pg.pv["shift"].item(0, 3).text() == "3"
    # verifikasi baris 1 (Ctrl+Enter), lalu ekspor: hanya baris terverifikasi
    pg.t.setCurrentCell(0, 1)
    w.verify_current()
    qtbot.waitUntil(lambda: pg.cur["rows"][0]["verified"], timeout=4000)
    assert pg.t.currentRow() == 1 and pg.t.item(0, 0).checkState() == Qt.Checked
    db = tmp_path / "keluar" / "spotter.db"
    db.parent.mkdir()
    monkeypatch.setattr("corex.forms.QFileDialog.getSaveFileName", lambda *a, **k: (str(db), ""))
    pg.export("sqlite")
    qtbot.waitUntil(lambda: not pg.expInfo.isHidden(), timeout=6000)
    assert "1 baris baru" in pg.expInfo.text() and "2 baris belum diverifikasi" in pg.expInfo.text()
    pg.verify_all(True)
    assert all(r["verified"] for r in pg.cur["rows"]) and "3/3" in pg.lst.item(0).text()
    xl = tmp_path / "keluar" / "spotter.xlsx"
    monkeypatch.setattr("corex.forms.QFileDialog.getSaveFileName", lambda *a, **k: (str(xl), ""))
    monkeypatch.setattr("corex.forms.show_in_folder", lambda p: None)
    pg.export("xlsx")
    qtbot.waitUntil(lambda: xl.exists(), timeout=6000)
    monkeypatch.setattr("corex.forms.QFileDialog.getSaveFileName", lambda *a, **k: (str(db), ""))
    pg.export("sqlite")
    qtbot.waitUntil(lambda: "diperbarui" in pg.expInfo.text(), timeout=6000)
    with sqlite3.connect(db) as cn:
        assert cn.execute("select count(*) from ORE_SPOTTER").fetchone()[0] == 3
    import openpyxl
    wb = openpyxl.load_workbook(xl)
    assert "Import_Data_A_sampai_K" in wb.sheetnames and wb["Import_Data_A_sampai_K"].max_row == 4
    # baris baru & hapus baris
    pg.add_row(None)
    assert pg.t.rowCount() == 4
    pg.t.setCurrentCell(3, 1)
    pg.del_row()
    assert pg.t.rowCount() == 3


def test_forms_ai_failure_and_rc_row(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    said = []
    monkeypatch.setattr("corex.forms.say", lambda *a, **k: said.append(a[1]))
    _fake_ai(w, monkeypatch, fail=True)
    pg.run_ai()
    qtbot.waitUntil(lambda: not pg.ai_busy and bool(said), timeout=8000)
    assert pg.t.rowCount() == 0 and pg.cur["doc"]["status"] == "error" and "tidak diisi" in said[0]
    # borang RC: baris baru melanjutkan interval & nomor sampel
    pg.cbNew.setCurrentIndex(pg.cbNew.findData("rc"))
    src = tmp_path / "lapangan" / "Chiptray_fiktif.png"
    Image.new("RGB", (900, 1200), "white").save(src)
    monkeypatch.setattr("corex.forms.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_files()
    qtbot.waitUntil(lambda: pg.cur and pg.cur["doc"]["type"] == "rc", timeout=8000)
    assert pg.lst.count() == 2 and not pg.tabs.isTabEnabled(1)
    pg._save_rows([{"id": None, "data": {"sample_id": "DX 100007 ZA", "from_m": "6", "to_m": "7"}, "verified": False}])
    pg.add_row(None)
    d = pg.cur["rows"][1]["data"]
    assert (d["sample_id"], d["from_m"], d["to_m"]) == ("DX 100008 ZA", "7", "8")
