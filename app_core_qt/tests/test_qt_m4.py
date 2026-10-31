"""Uji ruang kerja Singkapan (Qt): pindah mode, tambah foto, gambar garis / poligon / label dengan snap, atribut kadar,
belah, garis skala, deskripsi AI (Ollama palsu), infografis & ekspor PNG / PDF."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image  # noqa: E402
from PySide6.QtCore import QPointF  # noqa: E402

from test_qt_m1 import _win, fake_ollama, prj  # noqa: E402,F401


def _open_oc(qtbot, prj, tmp_path, monkeypatch):
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    w.set_mode("oc")
    pg = w.outcrop
    assert w.stack.currentWidget() is pg and not w.fbar.isVisible()
    src = tmp_path / "lapangan" / "Sebunga_RL256.jpg"
    src.parent.mkdir()
    Image.new("RGB", (1200, 800), (110, 140, 130)).save(src)
    monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_photo()
    qtbot.waitUntil(lambda: pg.cur is not None and pg.view.w > 0, timeout=8000)
    return w, pg


def _pt(pg, u, v):
    return QPointF(u * pg.view.w, v * pg.view.h)


def _draw(pg, kind, pts, name=""):
    pg.cbKind.setCurrentIndex(pg.cbKind.findData(kind))
    pg.bDraw.click()
    for u, v in pts:
        pg.tool.press(_pt(pg, u, v), None)
    if pg.kmap[kind]["shape"] != "point":
        pg.tool.finish()


def test_draw_snap_edit_and_export(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    assert pg.cur["w"] == 1200 and "Sebunga" in pg.lst.item(0).text()
    # poligon zona alterasi lalu garis vein yang ujungnya di-snap ke sudut poligon
    _draw(pg, "zona_alt", [(0.1, 0.2), (0.45, 0.2), (0.45, 0.8), (0.1, 0.8)])
    poly = pg.feats[-1]
    assert poly["shape"] == "poly" and len(poly["pts"]) == 4 and pg.tool.sel == poly["id"]
    _draw(pg, "vein", [(0.452, 0.203), (0.6, 0.5), (0.7, 0.9)])
    vein = pg.feats[-1]
    assert vein["pts"][0] == poly["pts"][1]  # snap ke titik poligon
    # atribut kadar lewat form
    pg.tool.select(vein["id"])
    pg.fName.setText("Qz-Cly-Oxide Vein")
    pg.fAu.setText("0,42")
    pg.fAg.setText("7")
    pg.fSxs.setText("1.88")
    pg.save_form()
    vein = pg.feat(vein["id"])
    assert vein["attrs"] == {"au_ppm": 0.42, "ag_ppm": 7.0, "sxs_pct": 1.88} and vein["name"] == "Qz-Cly-Oxide Vein"
    pg.fAu.setText("tinggi")
    pg.save_form()
    assert "angka" in pg.fErr.text()
    # geser titik dengan alat pilih (tarik kotak putih)
    pg.tool.select(vein["id"])
    assert pg.tool.press(_pt(pg, 0.6, 0.5), None)
    pg.tool.move(_pt(pg, 0.62, 0.55))
    pg.tool.release(_pt(pg, 0.62, 0.55))
    assert abs(pg.feat(vein["id"])["pts"][1][0] - 0.62) < 1e-3
    # belah di titik tengah
    pg.tool.select(vein["id"])
    pg.tool.vsel = 1
    pg.split_sel()
    assert len([f for f in pg.feats if f["kind"] == "vein"]) == 2
    # gabung lagi
    pg.tool.select(next(f["id"] for f in pg.feats if f["kind"] == "vein"))
    pg.join_sel()
    assert len([f for f in pg.feats if f["kind"] == "vein"]) == 1
    # sisipkan titik dengan klik ganda di garis
    v = next(f for f in pg.feats if f["kind"] == "vein")
    pg.tool.select(v["id"])
    n0 = len(v["pts"])
    pg.tool.dbl(_pt(pg, (v["pts"][0][0] + v["pts"][1][0]) / 2, (v["pts"][0][1] + v["pts"][1][1]) / 2))
    assert len(pg.feat(v["id"])["pts"]) == n0 + 1
    # label & garis skala 2 m
    monkeypatch.setattr(pg, "ask_text", lambda *a: "PROPYLITIC (CHL-SME) PYRITIC TUFF")
    _draw(pg, "label", [(0.25, 0.5)])
    assert pg.feats[-1]["name"].startswith("PROPYLITIC")
    _draw(pg, "skala", [(0.7, 0.95), (0.9, 0.95)])
    pg.fLen.setText("2")
    pg.save_form()
    assert pg.scale and abs(pg.scale["m_per_px"] - 2 / 240) < 1e-9 and pg.m_per_unit()
    # infografis: judul & komposit, template
    pg.iTitle.setText("TRENCHING SAMPLING SEBUNGA PIT RL256 BLOCK 11")
    pg.iTitle.editingFinished.emit()
    pg.save_info({"composite": "Composite Sample Block Digging @0.29 ppm Au"})
    assert pg.info()["title"].startswith("TRENCHING") and pg.cur["info"]["composite"].endswith("Au")
    pg.canvas.update()
    qtbot.wait(50)
    from PySide6.QtGui import QImage, QPainter
    img = QImage(400, 300, QImage.Format_RGB32)
    p = QPainter(img)
    pg.canvas.paint(p, None)
    p.end()
    assert any(k == "box" for _f, _r, k in pg.boxes) and any(k == "comp" for _f, _r, k in pg.boxes)
    # tarik kotak kadar
    fid, r, _k = next(b for b in pg.boxes if b[2] == "box")
    pg.tool.press(r.center(), None)
    pg.tool.move(QPointF(r.center().x() + 20, r.center().y() - 30))
    pg.tool.release(QPointF(r.center().x() + 20, r.center().y() - 30))
    assert "box_u" in pg.feat(fid)["attrs"]
    # ekspor PNG & PDF
    for fmt in ("png", "pdf"):
        out = tmp_path / f"info.{fmt}"
        monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, out=out, **k: (str(out), ""))
        monkeypatch.setattr("corex.outcrop.show_in_folder", lambda p: None)
        pg.export(fmt)
        qtbot.waitUntil(lambda out=out: out.exists() and out.stat().st_size > 2000, timeout=15000)
    from PySide6.QtGui import QImage as QI
    im = QI(str(tmp_path / "info.png"))
    assert im.width() == 1200 and im.pixelColor(600, 10).name() == "#f2c230"  # pita judul kuning template trenching
    pg.save_info({"template": "wall"})
    wall = tmp_path / "dinding"
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(wall), ""))
    pg.export("png")
    qtbot.waitUntil(lambda: (tmp_path / "dinding.png").exists(), timeout=15000)
    assert QI(str(tmp_path / "dinding.png")).pixelColor(600, 10).name() == "#232f45"  # pita navy template dinding
    # hapus fitur
    pg.tool.select(next(f["id"] for f in pg.feats if f["kind"] == "label"))
    monkeypatch.setattr("corex.outcrop.ask", lambda *a: True)
    pg.tool.vsel = None
    pg.delete_selected()
    assert not any(f["kind"] == "label" for f in pg.feats)
    # Esc membatalkan gambar; kembali ke Core box
    pg.bDraw.click()
    assert pg.escape() and pg.tool.mode == "select"
    w.set_mode("core")
    assert w.stack.currentIndex() == 1 and w.fbar.isVisibleTo(w)


def test_ai_description_and_edit_protected(qtbot, prj, tmp_path, monkeypatch, fake_ollama):
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    pg.dw["lithology"].setText("Tuf piritik")
    pg.dw["lithology"].editingFinished.emit()
    assert pg.cur["desc"]["lithology"] == "Tuf piritik" and pg.dTag["lithology"].text() == "diedit"
    w.ai.host.setText(fake_ollama)
    w.ai.check(True)
    qtbot.waitUntil(lambda: bool(w.ai.model()), timeout=5000)
    pg.run_ai()
    qtbot.waitUntil(lambda: not pg.ai_busy and pg.cur.get("status") == "done", timeout=20000)
    assert pg.cur["desc"]["lithology"] == "Tuf piritik"  # editan tidak ditimpa
    assert pg.cur["desc"]["weathering"].startswith("W2") and pg.dTag["weathering"].text() == "AI"
    assert "sedang" in pg.aiInfo.text()
    pg.histBtn.setChecked(True)
    assert "Jawaban asli AI" in pg.histTxt.text()


def test_kinds_dialog_string_numbers(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    from corex.outcrop import KindsDlg
    d = KindsDlg(pg, pg.kinds)
    qtbot.addWidget(d)
    d._add()
    r = d.t.rowCount() - 1
    d.t.item(r, 0).setText("Dike andesit")
    d.t.cellWidget(r, 1).setCurrentIndex(1)
    ks = d.result_kinds()
    assert ks[-1]["key"] == "dike_andesit" and ks[-1]["shape"] == "poly"
    monkeypatch.setattr("corex.outcrop.KindsDlg.exec", lambda self: KindsDlg.Accepted)
    monkeypatch.setattr("corex.outcrop.KindsDlg.result_kinds", lambda self: ks)
    pg.edit_kinds()
    assert "dike_andesit" in pg.kmap and pg.cbKind.findData("dike_andesit") >= 0


def test_georef_tab_measure_and_export(qtbot, prj, tmp_path, monkeypatch):
    """Titik Pylox di foto + E,N,RL (tabel / tempel Excel) -> bidang dinding, galat, ukuran 3D, ekspor STR / DXF."""
    import math
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[1])))
    monkeypatch.setattr("corex.outcrop.ask", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[1])))
    pg.tabs.setCurrentIndex(3)
    assert pg.geo_visible() and "Belum ada titik" in pg.gRes.text() and not pg.gStr.isEnabled()
    # dinding fiktif berarah 060°, 24 m x 16 m dalam foto 1200 x 800
    az = math.radians(60)

    def enr(u, v):
        s_, t = u * 24, (1 - v) * 16
        return 5000 + s_ * math.sin(az), 2000 + s_ * math.cos(az), 250 + t
    pg.gAdd.click()
    assert pg.tool.mode == "geo"
    uv = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9), (0.5, 0.45)]
    for u, v in uv[:4]:
        pg.tool.press(_pt(pg, u, v), None)
        pg.tool.release(_pt(pg, u, v))
    assert [q["name"] for q in pg.geo["points"]] == ["G1", "G2", "G3", "G4"] and pg.gT.rowCount() == 4
    assert "klik di foto" not in pg.gT.item(0, 4).text()
    # isi koordinat dengan menempel dari Excel (tab, desimal koma, ada judul kolom); G5 belum diklik
    rows = ["Nama\tE\tN\tRL"] + [f"G{i + 1}\t" + "\t".join(f"{x:.3f}".replace(".", ",") for x in enr(*uv[i])) for i in range(5)]
    from PySide6.QtGui import QGuiApplication
    QGuiApplication.clipboard().setText("\n".join(rows))
    pg.geo_paste()
    assert len(pg.geo["points"]) == 5 and pg.gT.item(4, 4).text() == "klik di foto"
    sol = pg.geo_res["solution"]
    assert sol["ok"] and "homografi" in sol["method"] and sol["rms"] < 0.01 and abs(sol["dip"] - 90) < 0.1
    # klik berikutnya menempatkan G5 (baris tanpa posisi), bukan titik baru
    pg.tool.press(_pt(pg, *uv[4]), None)
    pg.tool.release(_pt(pg, *uv[4]))
    assert len(pg.geo["points"]) == 5 and pg.geo_res["solution"]["n"] == 5 and pg.geo_err()
    # tarik penanda G5 jauh -> galat naik; kembalikan
    pg.tool.press(_pt(pg, *uv[4]), None)
    pg.tool.move(_pt(pg, 0.6, 0.45))
    pg.tool.release(_pt(pg, 0.6, 0.45))
    assert pg.geo_res["solution"]["rms"] > 0.3 and "galat terbesar" in pg.gRes.text()
    pg.tool.press(_pt(pg, 0.6, 0.45), None)
    pg.tool.move(_pt(pg, *uv[4]))
    pg.tool.release(_pt(pg, *uv[4]))
    assert pg.geo_res["solution"]["rms"] < 0.01
    # ubah RL lewat tabel
    said = []
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: said.append(a[1]))
    pg.gT.item(0, 3).setText("abc")
    assert said and "angka" in said[0]
    assert pg.geo["points"][0]["rl"] is not None
    pg.escape()
    assert pg.tool.mode == "select" and not pg.gAdd.isChecked()
    # penanda tergambar di kanvas
    from PySide6.QtGui import QImage, QPainter
    img = QImage(300, 200, QImage.Format_RGB32)
    p = QPainter(img)
    pg.canvas.paint(p, None)
    p.end()
    # vein lurus: panjang & apparent dip di form Fitur; bar skala dari georef (tanpa garis skala)
    _draw(pg, "vein", [(0.1, 0.9), (0.6, 0.4)])
    pg.tool.select(pg.feats[-1]["id"])
    head = pg.fHead.text()
    assert "panjang 3D" in head and "apparent dip" in head and pg.scale is None and pg.m_per_unit()
    m = pg.geo_res["measure"][pg.feats[-1]["id"]]
    assert abs(m["length_m"] - math.hypot(12, 8)) < 0.05 and abs(m["apparent_dip"] - math.degrees(math.atan2(8, 12))) < 0.2
    _draw(pg, "zona_lito", [(0.1, 0.1), (0.35, 0.1), (0.35, 0.6), (0.1, 0.6)])
    assert "luas" in pg.fHead.text()
    # ekspor STR & DXF
    monkeypatch.setattr("corex.outcrop.show_in_folder", lambda p: None)
    for fmt in ("str", "dxf"):
        out = tmp_path / f"digit.{fmt}"
        monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, out=out, **k: (str(out)[:-4], ""))
        assert pg.gStr.isEnabled()
        pg.export_geo(fmt, False)
        assert out.exists()
    t = (tmp_path / "digit.str").read_text()
    assert t.rstrip().endswith("END") and "Vein" in t
    first = next(x for x in t.splitlines() if x.startswith(str(pg.kmap["vein"]["string"]) + ","))
    sn, y, x, z = (float(a) for a in first.split(",")[:4])
    e0, n0, rl0 = enr(0.1, 0.9)
    assert abs(x - e0) < 0.05 and abs(y - n0) < 0.05 and abs(z - rl0) < 0.05
    assert "AC1009" in (tmp_path / "digit.dxf").read_text()
    # semua foto: foto kedua tanpa georef dilewati dengan konfirmasi
    src2 = tmp_path / "lapangan" / "lain.jpg"
    Image.new("RGB", (600, 400), (90, 90, 90)).save(src2)
    monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src2)], ""))
    pg.add_photo()
    qtbot.waitUntil(lambda: pg.cur and pg.cur["name"] == "lain.jpg", timeout=5000)
    assert not pg.geo["points"] and not pg.gStr.isEnabled()
    asked = []
    monkeypatch.setattr("corex.outcrop.ask", lambda _p, m: asked.append(m) or True)
    out = tmp_path / "semua.dxf"
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(out), ""))
    pg.export_geo("dxf", True)
    assert out.exists() and asked and "lain" in asked[0]
