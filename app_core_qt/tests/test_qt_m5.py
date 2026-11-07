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

ORE_AI = {"header": {"tanggal": "30-10-2026", "shift": "I", "crew": "Spotter A", "lokasi": "Pit X", "excavator": "EX-901", "ragu": ["crew"]},
          "rows": [{"no": "1", "start": "06.30", "finish": "", "pit": "Pit X", "elevasi": "120", "kelas": "OX-LG", "unit": "7101",
                    "ton": "30", "tujuan": "ROM A1"},
                   {"no": "2", "start": "46", "finish": "", "pit": "", "elevasi": "", "kelas": "OX-LG", "unit": "02", "ton": "30",
                    "tujuan": "〃", "ragu": ["unit"]},
                   {"no": "3", "start": "07.05", "finish": "", "pit": "", "elevasi": "", "kelas": "OX-HG", "unit": "7103", "ton": "3O",
                    "tujuan": "Crusher", "ragu": ["ton"]}]}


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
    assert pg.cbNew.count() == 8 and pg.cbNew.itemData(0) == "auto" and pg.lst.count() == 0
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
    assert pg.hdrEd["lokasi"].text() == "Pit X" and pg.hdrEd["crew"].styleSheet()  # header ragu disorot
    cols = [k for k, _l in pg.cols(pg.types["ore"])]
    ton, truk = 1 + cols.index("ton"), 1 + cols.index("unit")
    assert pg.t.item(1, truk).text() == "7102" and pg.t.item(1, truk).background().color() == QColor("#fff3bf")  # singkat -> lengkap, ragu
    assert pg.t.item(1, 1 + cols.index("start")).text() == "06:46"
    assert pg.t.item(2, ton).background().color() == QColor("#ffe3e3") and "angka" in pg.t.item(2, ton).toolTip()  # galat
    assert pg.t.item(0, pg.t.columnCount() - 1).text() == "2026-10-30"  # tanggal muat turunan
    # perbaiki sel -> tersimpan, sorotan hilang
    pg.t.item(2, ton).setText("30")
    qtbot.waitUntil(lambda: pg.cur["valid"]["n"] == 0, timeout=4000)
    assert pg.cur["rows"][2]["data"]["ton"] == "30" and "ton" not in pg.cur["rows"][2]["unc"]
    # pivot per shift
    assert pg.pv[0].rowCount() == 1 and pg.pv[0].item(0, 3).text() == "3" and "shift" in pg.pvLab[0].text()
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
        assert cn.execute("select count(*) from ORE_LOADING_PIT").fetchone()[0] == 3
    import openpyxl
    wb = openpyxl.load_workbook(xl)
    assert "Data_Loading_Pit" in wb.sheetnames and wb["Data_Loading_Pit"].max_row == 4
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
    assert pg.lst.count() == 2 and not pg.tabs.isTabEnabled(2) and "RC Drill" in pg.lst.item(1).text()
    pg._save_rows([{"id": None, "data": {"sample_id": "DX 100007 ZA", "from_m": "6", "to_m": "7"}, "verified": False}])
    pg.add_row(None)
    d = pg.cur["rows"][1]["data"]
    assert (d["sample_id"], d["from_m"], d["to_m"]) == ("DX 100008 ZA", "7", "8")


DDR_AI = {"header": {"tanggal": "31-10-26", "shift": "I", "rig": "RIG-X1", "driller": "Driller A", "wh": "5", "dl": "1"},
          "rows": [{"mulai": "0700", "selesai": "0710", "aktivitas": "P2H", "kategori": ""},
                   {"mulai": "0710", "selesai": "1200", "aktivitas": "Start drilling", "kategori": ""},
                   {"mulai": "1200", "selesai": "1300", "aktivitas": "Istirahat", "kategori": ""}],
          "lubang": [{"from_m": "0", "to_m": "30", "hole_id": "XX-1", "az": "60", "dip": "60"},
                     {"from_m": "0", "to_m": "24", "hole_id": "XX-2", "az": "60", "dip": "60"}]}


def test_forms_daily_drilling_report(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    pg.cbNew.setCurrentIndex(pg.cbNew.findData("ddr"))
    src = tmp_path / "lapangan" / "DDR_fiktif.png"
    Image.new("RGB", (900, 1300), "white").save(src)
    monkeypatch.setattr("corex.forms.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_files()
    qtbot.waitUntil(lambda: bool(pg.cur) and pg.cur["doc"]["type"] == "ddr", timeout=8000)
    _fake_ai(w, monkeypatch, DDR_AI)
    pg.run_ai()
    qtbot.waitUntil(lambda: not pg.ai_busy and pg.t.rowCount() == 3, timeout=8000)
    assert not pg.tblRow.isHidden() and pg.cbTbl.count() == 2 and "Aktivitas (3)" in pg.cbTbl.itemText(0)
    cols = [k for k, _l in pg.cols(pg.types["ddr"])]
    kc = 1 + cols.index("kategori")
    assert [pg.t.item(i, kc).text() for i in range(3)] == ["P2H", "DRILLING", "ISTIRAHAT"]
    assert isinstance(pg.t.itemDelegateForColumn(kc), type(pg._katDel))
    assert pg.t.item(1, len(cols) + 1).text() == "4.83"  # durasi turunan (jam)
    assert not pg.sumInfo.isHidden() and "54 m" in pg.sumInfo.text() and "2</b> lubang" in pg.sumInfo.text()
    # tabel meterage: edit tidak menyentuh aktivitas
    pg.cbTbl.setCurrentIndex(1)
    assert pg.tbl == "hole" and pg.t.rowCount() == 2 and pg.t.horizontalHeaderItem(3).text() == "Hole ID"
    hc = 1 + [k for k, _l in pg.cols(pg.types["ddr"])].index("to_m")
    pg.t.item(1, hc).setText("30")
    qtbot.waitUntil(lambda: "60 m" in pg.sumInfo.text(), timeout=4000)
    assert sum(1 for r in pg.cur["rows"] if not r["tbl"]) == 3 and pg.tbl == "hole"
    # kegiatan baru mulai saat kegiatan terakhir selesai
    pg.cbTbl.setCurrentIndex(0)
    pg.add_row(None)
    assert pg.t.rowCount() == 4 and pg.t.item(3, 1 + cols.index("mulai")).text() == "13:00"
    assert not pg.pv[3].isHidden() and "lubang" in pg.pvLab[3].text().lower()
    monkeypatch.setattr("corex.forms.ask", lambda *a, **k: True)
    pg.verify_all(True)
    z = tmp_path / "keluar" / "ddr.zip"
    z.parent.mkdir(exist_ok=True)
    monkeypatch.setattr("corex.forms.QFileDialog.getSaveFileName", lambda *a, **k: (str(tmp_path / "keluar" / "ddr"), ""))
    monkeypatch.setattr("corex.forms.show_in_folder", lambda p: None)
    monkeypatch.setattr("corex.forms.ask", lambda *a, **k: True)
    pg.export("csv")
    qtbot.waitUntil(lambda: z.exists(), timeout=6000)
    import zipfile
    assert "DDR_METERAGE.csv" in zipfile.ZipFile(z).namelist()


def test_forms_antrean_ai_cepat_tanpa_think(qtbot, prj, tmp_path, monkeypatch):
    """Baca semua yang belum: borang diantrekan & dibaca satu per satu; model 'berpikir' dikirim think=false;
    ukuran gambar mengikuti pilihan Cepat / Seimbang / Teliti; Ollama lama yang menolak think diulang tanpa itu."""
    import base64
    import io
    import urllib.error
    from corex.api import core_io
    from corex import api as capi
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    src2 = _scan(tmp_path).with_name("Borang_Spotter_fiktif_2.jpg")
    Image.new("RGB", (1000, 1300), "white").save(src2)
    monkeypatch.setattr("corex.forms.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src2)], ""))
    pg.add_files()
    qtbot.waitUntil(lambda: pg.lst.count() == 2, timeout=8000)
    sent = []
    old_ollama = {"on": True}

    def fake(url, body=None, timeout=5.0):
        if url.endswith("/api/show"):
            return {"capabilities": ["completion", "vision", "thinking"]}
        if old_ollama["on"] and "think" in body:
            old_ollama["on"] = False
            raise urllib.error.HTTPError(url, 400, "think not supported", {}, None)
        im = Image.open(io.BytesIO(base64.b64decode(body["messages"][0]["images"][0])))
        sent.append(("think" in body, body.get("think"), max(im.size)))
        return {"message": {"content": json.dumps(ORE_AI)}}
    monkeypatch.setattr(core_io, "_http", fake)
    from gcex_backend import core_forms
    core_forms._THINK.clear()
    w.ai.info = {"running": True}
    monkeypatch.setattr(w.ai, "model", lambda: "qwen3-vl:4b")
    pg.cbSpeed.setCurrentIndex(pg.cbSpeed.findData(1280))  # Cepat
    pg.run_ai_all()
    assert "Antrean AI: 2" in pg.bAIAll.text()
    qtbot.waitUntil(lambda: pg.ai_did is None and not pg.ai_q and all(d["status"] == "done" for d in pg.docs), timeout=15000)
    assert [x[0] for x in sent] == [False, False]  # Ollama lama menolak think: diulang tanpa itu, borang berikutnya tidak dicoba lagi
    assert all(px <= 1280 for *_a, px in sent)
    assert pg.bAIAll.text() == "Baca Semua dengan AI"
    assert "AI ·" in pg.lst.item(0).text() or " · AI" in pg.lst.item(0).text()
    # think=false dikirim bila Ollama menerimanya
    sent.clear()
    core_forms._THINK.clear()
    pg.lst.setCurrentRow(0)
    monkeypatch.setattr("corex.forms.ask", lambda *a, **k: True)
    pg.run_ai()
    qtbot.waitUntil(lambda: pg.ai_did is None and bool(sent), timeout=15000)
    assert sent[-1][:2] == (True, False)


