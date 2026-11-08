"""Borang 0.44 (Qt): navigasi Borang | Riwayat | Template | Pengaturan | Bantuan, Auto Detect, jenis baru (Geological Mapping,
Channel Sampling, Drill Progress Report), template kustom, ubah jenis. Semua data fiktif."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image  # noqa: E402

from test_qt_m1 import _win, prj  # noqa: E402,F401


def _img(tmp, name):
    f = tmp / "lapangan" / name
    f.parent.mkdir(exist_ok=True)
    Image.new("RGB", (800, 1000), "white").save(f)
    return f


def test_nav_auto_detect_template_riwayat(qtbot, prj, tmp_path, monkeypatch):
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    assert not w.forms.nav.isVisible()
    w.set_mode("form")
    pg = w.forms
    assert pg.nav.isVisible() and [b.text().split()[-1] for b in pg.navBtns] == ["Borang", "Riwayat", "Template", "Pengaturan", "Bantuan"]
    keys = [pg.typeList.item(i).data(0x0100) for i in range(pg.typeList.count())]
    assert keys == ["auto", "ore", "rom", "ddr", "rc", "map", "chn", "dpr"]
    # Auto Detect: jenis dari nama file
    pg.typeList.setCurrentRow(0)
    assert pg.cbNew.currentData() == "auto"
    src = _img(tmp_path, "Channel_Sampling_fiktif.jpg")
    monkeypatch.setattr("corex.forms.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_files()
    qtbot.waitUntil(lambda: pg.cur is not None, timeout=8000)
    assert pg.cur["doc"]["type"] == "chn" and "dari nama file" in pg.lst.item(0).data(0x0101)["type"]
    assert pg.tblFold.text().startswith("Data Tabel") and pg.t.columnCount() == 1 + 10
    # ubah jenis (belum ada baris)
    pg.change_type("dpr")
    assert pg.cur["doc"]["type"] == "dpr" and "Drill Progress" in pg.lst.item(0).data(0x0101)["type"]
    pg.add_row(None)
    assert len(pg.cur["rows"]) == 1
    # jenis salah setelah dibaca: ganti jenis -> baris dibuang + baca ulang AI
    ran = []
    monkeypatch.setattr("corex.forms.ask", lambda *a, **k: True)
    monkeypatch.setattr(pg, "run_ai", lambda: ran.append(1))
    pg.change_type("ddr")
    assert pg.cur["doc"]["type"] == "ddr" and pg.cur["rows"] == [] and ran == [1]
    pg.change_type("dpr")
    assert ran == [1]  # tanpa baris: tidak perlu baca ulang
    # Template kustom
    pg.show_page(2)
    assert pg.pages.currentWidget() is pg.pgTpl and pg.navBtns[2].isChecked()
    tp = pg.pgTpl
    names = [tp.lst.item(i).text() for i in range(tp.lst.count())]
    assert any(n.startswith("Channel Sampling") and "bawaan" in n for n in names) and not tp.bSave.isEnabled()
    tp.new()
    tp.eName.setText("Trench Log Fiktif")
    tp.col.load([["trench_id", "Trench ID", "text"], ["from_m", "From", "num"], ["to_m", "To", "num"], ["litologi", "Litologi", "text"]])
    tp.eCarry.setText("trench_id")
    tp.save()
    assert tp.key == "x_trench_log_fiktif" and "x_trench_log_fiktif" in pg.types
    assert pg.typeList.count() == 9 and pg.cbNew.findData("x_trench_log_fiktif") > 0
    # Riwayat
    pg.show_page(1)
    h = pg.pgHist
    assert h.t.rowCount() >= 4 and h.t.item(0, 4).text() == "template"
    whats = {h.t.item(i, 4).text() for i in range(h.t.rowCount())}
    assert {"tambah", "jenis", "template"} <= whats
    h.q.setText("Channel_Sampling")
    h.refresh()
    assert h.t.rowCount() >= 2 and all("Channel_Sampling" in h.t.item(i, 2).text() for i in range(h.t.rowCount()))
    pg.show_page(0)
    h._open_doc(0, 0)
    assert pg.pages.currentIndex() == 0 and pg.cur["doc"]["name"].startswith("Channel_Sampling")
    # Pengaturan & Bantuan
    pg.show_page(3)
    assert "Data borang" in pg.pgSet.path.text() and pg.pgSet.cbType.count() == pg.cbNew.count()
    pg.pgSet.cbType.setCurrentIndex(pg.pgSet.cbType.findData("map"))
    assert pg.cbNew.currentData() == "map" and pg.typeList.currentItem().data(0x0100) == "map"
    pg.show_page(4)
    assert pg.pages.currentWidget() is pg.pgHelp
    w.set_mode("core")
    assert not pg.nav.isVisible()
