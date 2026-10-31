"""Uji tahap 2: overlay berlapis, tanda interval (tarik di foto -> simpan -> recovery), editor segmen (baru, geser batas, belah,
gabung, hapus), kalibrasi area core, kotak Data lab."""
import os
import sys
from pathlib import Path

import pytest
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPointF  # noqa: E402


@pytest.fixture()
def win(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("COREX_USERDATA", str(tmp_path / "ud"))
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "Foto" / "LTH-101"
    d.mkdir(parents=True)
    Image.new("RGB", (800, 600), (120, 90, 70)).save(d / "LTH-101_Box1_0.00-4.00.jpg")
    Image.new("RGB", (800, 600), (100, 90, 70)).save(d / "LTH-101_Box2_4.00-8.00.jpg")
    (tmp_path / "assay.csv").write_text("Hole,From,To,Sample_No,Au\nLTH-101,0,1,S-001,0.2\nLTH-101,1,2.5,S-002,1.4\nLTH-101,2.5,4,S-003,4.1\n", encoding="utf-8")
    from corex import util
    util.SET.__init__()
    util.SET.set("user", "Rina")
    util.SET.set("autoOllama", False)
    from corex.api import core_io
    core_io._PROJECTS.clear()
    from corex import theme
    from corex.mainwin import MainWindow
    from PySide6.QtWidgets import QApplication
    theme.load_fonts()
    theme.apply(QApplication.instance())
    monkeypatch.setattr("corex.layers.ask", lambda *a, **k: True)
    w = MainWindow("uji")
    w.resize(1400, 900)
    qtbot.addWidget(w)
    w.show()
    folder = str(tmp_path / "Foto")
    from corex import api
    api.call("/core/open", {"folder": folder})
    pv = api.call("/core/dh/preview", {"folder": folder, "kind": "assay", "path": str(tmp_path / "assay.csv"), "name": "assay.csv"})
    api.call("/core/dh/import", {"folder": folder, "kind": "assay", "path": str(tmp_path / "assay.csv"), "name": "assay.csv",
                                 "header_row": pv["header_row"], "roles": pv["guess"]["roles"], "cols": pv["guess"]["cols"]})
    w.open_folder(folder)
    qtbot.waitUntil(lambda: w.cur_id is not None and w.interp.det is not None and w.viewer.w > 0, timeout=10000)
    return w


def pt(it, depth: float, yfrac: float = 0.5) -> QPointF:
    """Titik di foto (koordinat gambar) untuk kedalaman tertentu di box aktif."""
    g, r = it.geo(), it.r
    s = (depth - r["from_m"]) / (r["to_m"] - r["from_m"]) * g["rows"]
    row = min(g["rows"] - 1, int(s))
    if abs(s - g["rows"]) < 1e-9:
        row, s = g["rows"] - 1, float(g["rows"])
    return QPointF(g["X0"] + (s - row) * g["BW"], g["Y0"] + (row + yfrac) * g["RH"])


def test_overlay_and_lab_box(win, qtbot):
    it = win.interp
    assert [l["k"] for l in it.ov.layers][:1] == ["a:Au"]
    it.bOv.setChecked(True)
    m, items = it.ov.items(it.ov.layers[0], it.r, it.det, it.segs)
    assert len(items) == 3 and items[2]["v"] == 4.1
    assert it.ov.color("a:Au", m, 4.1) == "#141a26"  # kelas tertinggi Au >= 3
    assert "S-002" in it.boxLab.text() and "Assay" in it.boxLab.text()
    win.canvas_img = win.viewer.grab()  # menggambar tanpa galat
    # kelas kadar baru ikut ke tabel
    it._set_cls(it.ov.layers[0], "1, 2, 5")
    assert it.ov.grade_classes("Au") == [1.0, 2.0, 5.0] and win.model.grade_cls == [1.0, 2.0, 5.0]


def test_marks_drag_save_recovery(win, qtbot):
    it = win.interp
    it.bMk.setChecked(True)
    it.mark_mode(True)
    assert win.viewer.tool is it.mark_tool
    t = it.mark_tool
    assert t.press(pt(it, 1.0), None)
    t.move(pt(it, 1.5))
    t.release(pt(it, 1.5))
    assert it.mk_edit and it.mk_edit["from_m"] == 1.0 and it.mk_edit["to_m"] == 1.5
    assert it.mkS.text() == "S-002"  # nomor sampel dari assay yang tumpang tindih
    it.mark_save()
    assert len(it.marks) == 1 and it.marks[0]["sample_no"] == "S-002"
    # core loss 0.4 m -> recovery (4 - 0.4) / 4 = 90 %
    it.mk_kind = "coreloss"
    t.press(pt(it, 2.0), None)
    t.move(pt(it, 2.4))
    t.release(pt(it, 2.4))
    it.mark_save()
    r = win.by_id[win.cur_id]
    assert r["recovery_pct"] == 90.0 and r["rec_src"] == "tanda" and win.card.f["recovery_pct"].tag.text() == "tanda"
    # klik tanda yang ada -> form edit; hapus
    assert t.press(pt(it, 2.2, 0.5), None) and it.mk_edit["id"] == it.marks[1]["id"]
    it.mark_delete(it.mk_edit["id"])
    assert len(it.marks) == 1
    it.escape()
    assert not it.mk_mode and win.viewer.tool is None


def test_segment_editor(win, qtbot):
    it = win.interp
    it.seg_mode(True)
    assert it.sg_mode and win.viewer.tool is it.seg_tool
    st = it.seg_tool
    # segmen baru 0.5-1.5 m
    st.press(pt(it, 0.5), None)
    st.move(pt(it, 1.5))
    st.release(pt(it, 1.5))
    assert it.sg_cur and it.sg_cur["id"] is None
    it.sgEd["lithology"].setText("AND")
    it.sgEd["rqd_pct"].setText("80")
    it.seg_save()
    assert len(it.segs) == 1 and it.segs[0]["from_m"] == 0.5 and it.segs[0]["to_m"] == 1.5 and it.segs[0]["lithology"] == "AND"
    # segmen kedua 1.5-3.0 berbatasan
    it.seg_form_close()
    st.press(pt(it, 1.6), None)  # klik di dalam? 1.6 belum ada segmen -> tarik baru
    st.move(pt(it, 3.0))
    st.release(pt(it, 3.0))
    it.sgF.setValue(1.5)
    it.sgEd["lithology"].setText("QV")
    it.seg_save()
    assert [(s["from_m"], s["to_m"]) for s in it.segs] == [(0.5, 1.5), (1.5, 3.0)]
    it.seg_form_close()
    # geser batas bersama 1.5 -> 1.8 m: tetangga ikut
    assert st._bound_at(pt(it, 1.5))
    st.press(pt(it, 1.5), None)
    st.move(pt(it, 1.8))
    st.release(pt(it, 1.8))
    assert [(s["from_m"], s["to_m"]) for s in it.segs] == [(0.5, 1.8), (1.8, 3.0)]
    # klik segmen QV -> belah di titik klik, gabung, hapus
    st.press(pt(it, 2.4), None)
    assert it.sg_cur["lithology"] == "QV"
    it._seg_op("split", {"f": it.sg_click}, close=True)
    assert len(it.segs) == 3
    first_qv = next(s for s in it.segs if s["from_m"] == 1.8)
    it.seg_form(first_qv)
    it._seg_op("merge", {}, close=False)
    assert len(it.segs) == 2
    it.seg_form(it.segs[0])
    it._seg_op("delete", {}, close=True)
    assert len(it.segs) == 1 and win.by_id[win.cur_id]["n_segs"] == 1
    assert "PER BARIS" in it.boxSeg.text()


def test_calibration(win, qtbot):
    it = win.interp
    it.cal_start()
    assert it.cal_t and win.viewer.tool is it.cal_tool and it.pCal.isVisibleTo(win)
    c = it.cal_tool
    W, H = win.viewer.w, win.viewer.h
    t0 = dict(it.cal_t)
    assert c.press(QPointF(t0["x1"] * W, t0["y1"] * H), None)  # sudut kanan bawah
    c.move(QPointF(t0["x1"] * W - 40, t0["y1"] * H - 30))
    c.release(QPointF(0, 0))
    it.calRows.setValue(3)
    it.cal_save("hole")
    qtbot.waitUntil(lambda: it.det is not None and it.det["tray"]["rows"] == 3, timeout=5000)
    assert abs(it.det["tray"]["x1"] - (t0["x1"] - 40 / W)) < 1e-6 and it.cal_t is None
    win.table.go_row(1)
    qtbot.waitUntil(lambda: it.det is not None and it.r["id"] == win.cur_id, timeout=5000)
    assert it.det["tray"]["rows"] == 3  # berlaku untuk semua foto lubang ini
