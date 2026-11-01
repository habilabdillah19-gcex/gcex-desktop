"""Uji ruang kerja Singkapan (Qt): pindah mode, tambah foto, gambar garis / poligon / label dengan snap, atribut kadar,
belah, garis skala, deskripsi AI (Ollama palsu), infografis & ekspor PNG / PDF."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image  # noqa: E402
from PySide6.QtCore import QPointF, Qt  # noqa: E402

from test_qt_m1 import _win, fake_ollama, prj  # noqa: E402,F401

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _coord_default(monkeypatch):
    """Dialog sumber koordinat ekspor: terima pilihan bawaan (georef) tanpa jendela modal."""
    from corex.dialogs import Dlg
    monkeypatch.setattr("corex.outcrop.CoordDlg.exec", lambda self: Dlg.Accepted)


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
    cols = [pg.sT.horizontalHeaderItem(c).text().split()[0] for c in range(pg.sT.columnCount())]
    assert pg.sT.isColumnHidden(1) is False and cols[3:6] == ["Au", "Ag", "Cu"]
    pg.sT.setRowCount(1)
    from PySide6.QtWidgets import QTableWidgetItem
    for c, v in ((0, "TC-01"), (cols.index("Au"), "0,42"), (cols.index("Ag"), "7"), (cols.index("SxS"), "1.88")):
        pg.sT.setItem(0, c, QTableWidgetItem(v))
    pg.save_form()
    vein = pg.feat(vein["id"])
    assert vein["attrs"]["samples"] == [{"id": "TC-01", "from": None, "to": None, "grades": {"Au": 0.42, "Ag": 7.0, "SxS": 1.88}}]
    assert vein["name"] == "Qz-Cly-Oxide Vein"
    pg.sT.setItem(0, cols.index("Au"), QTableWidgetItem("tinggi"))
    pg.save_form()
    assert "batas deteksi" in pg.fErr.text()
    pg.sT.setItem(0, cols.index("Au"), QTableWidgetItem("0,42"))
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
    # gaya bawaan editorial: gradasi gelap di bagian judul (foto uji berwarna hijau keabuan terang)
    assert im.width() == 1200 and im.pixelColor(600, 10).lightness() < 70
    pg.save_info({"style": "klasik"})
    klas = tmp_path / "klasik"
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(klas), ""))
    pg.export("png")
    qtbot.waitUntil(lambda: (tmp_path / "klasik.png").exists(), timeout=15000)
    assert QI(str(tmp_path / "klasik.png")).pixelColor(600, 10).name() == "#f2c230"  # pita judul kuning template trenching
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


def test_auto_proposals_color_and_ai(qtbot, prj, tmp_path, monkeypatch, fake_ollama):
    """Usulan zona warna & AI vision sebagai draf: tampil putus-putus, tidak ikut ekspor, bisa diterima / dibuang."""
    import json
    import numpy as np
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[1])))
    yy, xx = np.mgrid[0:400, 0:600]
    a = np.zeros((400, 600, 3)) + [128, 134, 126]
    a[(xx > 330) & (yy < 230)] = [168, 98, 52]
    src = tmp_path / "lapangan" / "zona.jpg"
    Image.fromarray(a.astype("uint8")).save(src)
    monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_photo()
    qtbot.waitUntil(lambda: pg.cur and pg.cur["name"] == "zona.jpg" and pg.view.w > 0, timeout=5000)
    pg.tabs.setCurrentIndex(1)
    assert "Belum ada usulan" in pg.auInfo.text() and not pg.bAcc.isEnabled()
    pg.auMeth.setCurrentIndex(0)
    pg.auK.setValue(2)
    pg.bAuto.click()
    qtbot.waitUntil(lambda: not pg.auto_busy, timeout=15000)
    drafts = [f for f in pg.feats if f["attrs"].get("_draft")]
    assert drafts and any(f["kind"] == "zona_oks" for f in drafts) and "usulan belum diterima" in pg.auInfo.text()
    assert pg.fList.item(0).text().startswith("◌ usulan")
    # pilih usulan: tombol Terima tampil; Simpan dengan jenis diganti = diterima
    ox = next(f for f in drafts if f["kind"] == "zona_oks")
    pg.tool.select(ox["id"])
    assert pg.bFAcc.isVisible()
    pg.fName.setText("Zona oksida / gossan")
    pg.save_form()
    f = pg.feat(ox["id"])
    assert not f["attrs"].get("_draft") and f["name"] == "Zona oksida / gossan" and not pg.bFAcc.isVisible()
    # kanvas menggambar draf tanpa galat; ekspor PNG hanya memuat fitur yang diterima
    from PySide6.QtGui import QImage, QPainter
    img = QImage(300, 200, QImage.Format_RGB32)
    p = QPainter(img)
    pg.canvas.paint(p, None)
    p.end()
    seen = {}
    monkeypatch.setattr("corex.outcrop.oc_paint.render", lambda src, feats, *a, **k: seen.setdefault("f", feats) and QImage(10, 10, QImage.Format_RGB32))
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(tmp_path / "x.png"), ""))
    monkeypatch.setattr("corex.outcrop.show_in_folder", lambda p: None)
    pg.export("png")
    qtbot.waitUntil(lambda: "f" in seen, timeout=5000)
    assert [x["id"] for x in seen["f"]] == [ox["id"]]
    # AI vision: jawaban model (format 0-1000) menjadi usulan; usulan warna tetap ada
    from corex.api import core_io
    orig = core_io._http
    ans = {"features": [{"kind": "vein", "name": "Vein kuarsa", "points": [[450, 0], [520, 1000]], "confidence": "sedang"},
                        {"kind": "sesar", "points": [[100, 200], [300, 900]]}], "notes": "uji"}

    def http(url, body=None, timeout=5.0):
        if isinstance(body, dict) and "features" in (body.get("format") or {}).get("properties", {}):
            return {"message": {"content": json.dumps(ans)}}
        return orig(url, body, timeout)
    monkeypatch.setattr(core_io, "_http", http)
    w.ai.host.setText(fake_ollama)
    w.ai.check(True)
    qtbot.waitUntil(lambda: bool(w.ai.model()), timeout=5000)
    n_color = sum(1 for f in pg.feats if f["attrs"].get("_draft") == "warna")
    pg.auMeth.setCurrentIndex(1)
    assert not pg.auK.isVisible()
    pg.bAuto.click()
    qtbot.waitUntil(lambda: not pg.auto_busy, timeout=15000)
    ai = [f for f in pg.feats if str(f["attrs"].get("_draft", "")).startswith("ai:")]
    assert {f["kind"] for f in ai} == {"vein", "sesar"} and sum(1 for f in pg.feats if f["attrs"].get("_draft") == "warna") == n_color
    # terima satu lewat tombol, buang sisanya
    v = next(f for f in ai if f["kind"] == "vein")
    pg.tool.select(v["id"])
    pg.bFAcc.click()
    assert not pg.feat(v["id"])["attrs"].get("_draft")
    monkeypatch.setattr("corex.outcrop.ask", lambda *a, **k: True)
    pg.bRej.click()
    assert not any(f["attrs"].get("_draft") for f in pg.feats) and {f["kind"] for f in pg.feats} == {"zona_oks", "vein"}
    assert "Belum ada usulan" in pg.auInfo.text()


def test_trench_intervals_multi_element(qtbot, prj, tmp_path, monkeypatch):
    """Garis trenching dibagi interval dari-ke: tabel sampel (tambah, tempel Excel), kotak per interval yang bisa ditarik,
    warna kelas Au + legenda, komposit otomatis, daftar unsur, ekspor CSV."""
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[1])))
    _draw(pg, "channel", [(0.05, 0.6), (0.5, 0.6), (0.95, 0.6)])
    ch = pg.feats[-1]
    pg.tool.select(ch["id"])
    assert pg.sBox.isVisible() and "dianggap sepanjang" in pg.sHead.text()
    # tempel dari Excel dengan judul kolom (urutan unsur berbeda, satuan di judul, desimal koma, <DL)
    QGuiApplication.clipboard().setText("Sample ID\tDari\tKe\tAg_ppm\tAu (ppm)\tSxS %\n"
                                        "TC261-01\t0\t1,5\t4\t1,03\t2,97\nTC261-02\t1,5\t2,4\t7\t11\t0,19\nTC261-03\t2,4\t4\t5\t<0.01\t1,05")
    pg.sample_paste()
    assert pg.sT.rowCount() == 3
    pg.save_form()
    sm = pg.feat(ch["id"])["attrs"]["samples"]
    assert [x["id"] for x in sm] == ["TC261-01", "TC261-02", "TC261-03"] and sm[1]["grades"] == {"Ag": 7.0, "Au": 11.0, "SxS": 0.19}
    assert sm[2]["grades"]["Au"] == "<0.01" and sm[2]["to"] == 4
    # + Interval melanjutkan 'ke' terakhir & menaikkan nomor sampel
    pg.tool.select(ch["id"])
    pg.sample_add()
    assert [pg.sT.item(3, c).text() for c in range(3)] == ["TC261-04", "4", "5.6"]
    pg.sample_del()
    assert pg.sT.rowCount() == 3
    # infografis: 3 kotak interval + komposit otomatis + kelas warna Au di legenda
    pg.save_info({"template": "trench", "grade_color": "Au"})
    assert pg.iColor.currentData() == "Au"
    img = QImage(600, 400, QImage.Format_RGB32)
    p = QPainter(img)
    pg.canvas.paint(p, None)
    p.end()
    sboxes = [b for b in pg.boxes if b[2].startswith("s")]
    assert len(sboxes) == 3 and any(b[2] == "comp" for b in pg.boxes)
    assert "3 sampel 4 m" in pg.fList.item(pg.feats.index(pg.feat(ch["id"]))).text()
    # tarik kotak interval ke-2: posisi tersimpan per sampel
    fid, r, k = sboxes[1]
    pg.tool.press(r.center(), None)
    pg.tool.move(QPointF(r.center().x() + 30, r.center().y() + 10))
    pg.tool.release(QPointF(r.center().x() + 30, r.center().y() + 10))
    sm = pg.feat(ch["id"])["attrs"]["samples"]
    assert "bu" in sm[int(k[1:])] and all("bu" not in x for i, x in enumerate(sm) if i != int(k[1:]))
    # Simpan form tidak menghapus posisi kotak
    pg.tool.select(ch["id"])
    pg.save_form()
    assert "bu" in pg.feat(ch["id"])["attrs"]["samples"][int(k[1:])]
    # komposit otomatis tertimbang panjang (Au <0.01 dihitung 0.005)
    from corex import oc_paint
    cp = oc_paint.composite(pg.feat(ch["id"])["attrs"]["samples"])
    assert abs(cp["grades"]["Au"] - (1.03 * 1.5 + 11 * 0.9 + 0.005 * 1.6) / 4) < 1e-9
    # daftar unsur: tampilkan Cu, batas kelas Ag
    from corex.outcrop import ElementsDlg
    d = ElementsDlg(pg, pg.elements)
    qtbot.addWidget(d)
    r_cu = next(i for i, e in enumerate(d.els) if e["key"] == "Cu")
    d.t.cellWidget(r_cu, 3).setChecked(True)
    d.t.item(1, 4).setText("5; 10")
    els = d.result_elements()
    monkeypatch.setattr("corex.outcrop.ElementsDlg.exec", lambda self: ElementsDlg.Accepted)
    monkeypatch.setattr("corex.outcrop.ElementsDlg.result_elements", lambda self: els)
    pg.edit_elements()
    assert next(e for e in pg.elements if e["key"] == "Cu")["show"] and pg.iColor.findData("Ag") >= 0
    # ekspor CSV & PNG (kotak interval ikut)
    monkeypatch.setattr("corex.outcrop.show_in_folder", lambda p: None)
    out = tmp_path / "sampel.csv"
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(out), ""))
    pg.export_samples()
    rows = out.read_text(encoding="utf-8-sig").splitlines()
    assert rows[1].split(",")[3] == "TC261-01" and rows[-1].split(",")[3] == "KOMPOSIT"
    png = tmp_path / "trench.png"
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(png), ""))
    pg.export("png")
    qtbot.waitUntil(lambda: png.exists(), timeout=15000)


def test_strike_dip_zone_label_compass(qtbot, prj, tmp_path, monkeypatch):
    """Simbol strike/dip (N100/80), label zona berkurung + kotak putih, label kotak, kompas arah pandang (manual & georef)."""
    from PySide6.QtGui import QImage, QPainter
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    said = []
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: said.append(a[1]))
    # strike / dip: format N100/80, 100 / 80 dan salah
    for txt, ok in (("N100/80", True), ("45 / 30", True), ("tegak", False)):
        monkeypatch.setattr(pg, "ask_text", lambda *a, t=txt: t)
        n0 = len(pg.feats)
        _draw(pg, "orientasi", [(0.5, 0.3)])
        assert (len(pg.feats) == n0 + 1) is ok
    o = [f for f in pg.feats if f["kind"] == "orientasi"]
    assert o[0]["attrs"] == {"strike": 100.0, "dip": 80.0} and o[1]["attrs"]["strike"] == 45 and said
    pg.tool.select(o[0]["id"])
    assert pg.sdW.isVisible() and not pg.sBox.isVisible() and pg.fStrike.text() == "100"
    pg.fDip.setText("75")
    pg.save_form()
    assert pg.feat(o[0]["id"])["attrs"]["dip"] == 75
    assert "N100/75" in pg.fList.item(pg.feats.index(pg.feat(o[0]["id"]))).text()
    # label zona (rentang) + kotak putih yang bisa ditarik
    monkeypatch.setattr(pg, "ask_text", lambda *a: "Intermediate Argillic Zone (Fine Grain Sulfide Rich)")
    _draw(pg, "label_zona", [(0.2, 0.7), (0.45, 0.7)])
    zl = pg.feats[-1]
    assert zl["name"].startswith("Intermediate") and not pg.sBox.isVisible()
    # label kotak (default dicentang)
    monkeypatch.setattr(pg, "ask_text", lambda *a: "PROPYLITIC (CHL-SME-PY) TUFF")
    pg.cbLabelBox.setChecked(True)
    _draw(pg, "label", [(0.85, 0.4)])
    lb = pg.feats[-1]
    assert lb["attrs"] == {"style": "box"}
    pg.tool.select(lb["id"])
    assert pg.fBoxStyle.isVisible() and pg.fBoxStyle.isChecked()
    # kompas manual
    pg.save_info({"compass": "W", "compass_pos": "tl"})
    assert pg.info()["_compass"] == {"mode": "view", "letter": "W"} and pg.iCompass.currentData() == "W"
    img = QImage(600, 400, QImage.Format_RGB32)
    p = QPainter(img)
    pg.canvas.paint(p, None)
    p.end()
    zb = next(b for b in pg.boxes if b[0] == zl["id"] and b[2] == "box")
    pg.tool.press(zb[1].center(), None)
    pg.tool.move(QPointF(zb[1].center().x() + 25, zb[1].center().y() + 15))
    pg.tool.release(QPointF(zb[1].center().x() + 25, zb[1].center().y() + 15))
    assert "box_u" in pg.feat(zl["id"])["attrs"]
    # menggeser simbol strike/dip memindahkan titiknya tanpa melompat
    ob = next(b for b in pg.boxes if b[0] == o[0]["id"])
    before = list(pg.feat(o[0]["id"])["pts"][0])
    q = QPointF(before[0] * pg.view.w, before[1] * pg.view.h + 2)
    pg.tool.press(q, None)
    hit = pg.tool.drag["fid"]  # dua simbol di titik yang sama: yang teratas terambil
    assert hit in (o[0]["id"], o[1]["id"])
    pg.tool.move(QPointF(q.x() + 12, q.y()))
    pg.tool.release(QPointF(q.x() + 12, q.y()))
    after = pg.feat(hit)["pts"][0]
    assert abs(after[0] - before[0] - 12 / pg.view.w) < 2e-3 and abs(after[1] - before[1]) < 2e-3 and ob
    # kompas otomatis dari georef (dinding berarah 090 -> kamera menghadap N)
    pg.save_info({"compass": "auto"})
    pts = [{"name": f"G{i}", "u": u, "v": v, "e": 100 + u * 30, "n": 500.0, "rl": 50 + (1 - v) * 20}
           for i, (u, v) in enumerate([(0.05, 0.05), (0.95, 0.05), (0.95, 0.95), (0.05, 0.95)])]
    from corex import api
    api.call("/core/outcrop/georef", {"folder": pg.folder, "id": pg.cur["id"], "points": pts, "kind": "wall", "by": "Rina"})
    pg.geo_refresh()
    cp = pg.info()["_compass"]
    assert cp["mode"] == "view" and min(abs(cp["az"]), abs(cp["az"] - 360)) < 0.5
    from corex import oc_paint
    assert oc_paint.az_letter(cp["az"]) == "N" and oc_paint.az_letter(268) == "W"
    # ekspor STR membawa N100/75; label zona tidak ikut
    monkeypatch.setattr("corex.outcrop.show_in_folder", lambda p: None)
    out = tmp_path / "s.str"
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(out), ""))
    monkeypatch.setattr("corex.outcrop.ask", lambda *a, **k: True)
    pg.export_geo("str", False)
    t = out.read_text()
    assert "N100/75" in t and "Intermediate" not in t


def test_export_drillhole_channel(qtbot, prj, tmp_path, monkeypatch):
    """Tombol database channel: 4 CSV (collar, survey, assay, geology), collar di ujung kiri walau digambar kanan->kiri."""
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[1])))
    _draw(pg, "channel", [(0.9, 0.5), (0.1, 0.5)])
    ch = pg.feats[-1]
    assert ch["pts"][0][0] < ch["pts"][-1][0]  # disimpan kiri -> kanan
    from PySide6.QtWidgets import QTableWidgetItem
    pg.tool.select(ch["id"])
    assert "ujung KIRI" in pg.sHead.text()
    pg.sT.setRowCount(1)
    for c, v in enumerate(("S-01", "0", "2,5")):
        pg.sT.setItem(0, c, QTableWidgetItem(v))
    pg.sT.setItem(0, 3, QTableWidgetItem("<0.01"))
    pg.save_form()
    from corex import api
    pts = [{"name": f"G{i}", "u": u, "v": v, "e": 100 + u * 24, "n": 500.0, "rl": 50 + (1 - v) * 16}
           for i, (u, v) in enumerate([(0.05, 0.05), (0.95, 0.05), (0.95, 0.95), (0.05, 0.95)])]
    api.call("/core/outcrop/georef", {"folder": pg.folder, "id": pg.cur["id"], "points": pts, "kind": "wall", "by": "Rina"})
    monkeypatch.setattr("PySide6.QtWidgets.QInputDialog.getItem", lambda *a, **k: (a[3][1], True))  # negatif DL
    monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, **k: (str(tmp_path / "db_collar.csv"), ""))
    monkeypatch.setattr("corex.outcrop.show_in_folder", lambda p: None)
    pg.export_drillhole()
    files = {k: (tmp_path / f"db_{k}.csv").read_text(encoding="utf-8-sig").splitlines() for k in ("collar", "survey", "assay", "geology")}
    c = files["collar"][1].split(",")
    assert c[1] == f"{100 + 0.1 * 24:.3f}" and c[5] == "90.0" and c[6] == "0"
    assert files["survey"][1].endswith(",0.00,90.0,0") and files["assay"][1].split(",")[1:5] == ["0.00", "2.50", "S-01", "-0.01"]
    assert files["geology"][0].startswith("HOLE_ID,FROM,TO,LITHOLOGY") and len(files["geology"]) == 2


def test_core_box_infographic_and_styles(qtbot, prj, tmp_path, monkeypatch):
    """Infografis foto core box (gaya editorial) lewat File > Ekspor infografis; Singkapan: gaya editorial & klasik."""
    from PySide6.QtGui import QImage, QPainter
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3 and w.cur_id is not None, timeout=8000)
    w.save_field(w.cur_id, "hole_id", "LTH-101")
    w.save_field(w.cur_id, "lithology", "Andesit porfiri")
    r = w.by_id[w.cur_id]
    w.interp.row_changed(r)
    info, leg = w.interp.infographic()
    assert info["title"].startswith("LTH-101") and "0.00 – 3.50 m" in info["title"] and "Andesit" in info["caption"]
    out = tmp_path / "core.png"
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", lambda *a, **k: (str(out), "PNG (*.png)"))
    monkeypatch.setattr("corex.layers.show_in_folder", lambda p: None)
    from PySide6.QtGui import QAction
    act = next(a for a in w.findChildren(QAction) if a.text().startswith("Ekspor infografis"))
    assert act.shortcut().toString() == "Ctrl+E"
    act.trigger()
    im = QImage(str(out))
    assert not im.isNull() and im.width() == 600
    # gradasi gelap di atas (judul) lebih gelap dari bagian tengah foto
    top, mid = QColor_l(im.pixel(300, 5)), QColor_l(im.pixel(300, 200))
    assert top < mid
    # Singkapan: kedua gaya tergambar tanpa galat
    w.set_mode("oc")
    pg = w.outcrop
    src = tmp_path / "lapangan" / "s.jpg"
    src.parent.mkdir()
    from PIL import Image
    Image.new("RGB", (800, 500), (150, 140, 120)).save(src)
    monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_photo()
    qtbot.waitUntil(lambda: pg.cur is not None and pg.view.w > 0, timeout=8000)
    assert pg.info()["style"] == "editorial" and pg.iStyle.currentData() == "editorial"
    for st in ("editorial", "klasik"):
        pg.save_info({"style": st, "title": "Trenching contoh", "caption": "Tuf terubah argilik.", "credit": "Foto: uji"})
        img = QImage(400, 250, QImage.Format_RGB32)
        p = QPainter(img)
        pg.canvas.paint(p, None)
        p.end()
    assert pg.iStyle.currentData() == "klasik"


def QColor_l(rgb: int) -> int:
    from PySide6.QtGui import QColor
    return QColor(rgb).lightness()


def test_sam_tool_topo_and_coord_dialog(qtbot, prj, tmp_path, monkeypatch):
    """SAM: klik di zona -> pratinjau -> Enter simpan poligon; topografi: impor, cek, ekspor bawaan georef vs tempel DTM."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))
    from test_core_outcrop import _wall_dtm
    from corex.outcrop import CoordDlg
    w, pg = _open_oc(qtbot, prj, tmp_path, monkeypatch)
    monkeypatch.setattr("corex.outcrop.say", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[1])))
    # ---- dialog koordinat: bawaan georef, tanpa DTM opsi tempel nonaktif
    d = CoordDlg(pg, "STR", [], None, False)
    qtbot.addWidget(d)
    assert d.rGeo.isChecked() and not d.rTopo.isEnabled() and d.result_opt() == {"coord": "georef"}
    d = CoordDlg(pg, "STR", [{"id": 7, "survey_date": "2026-10-13", "name": "T41"}], 7, True)
    qtbot.addWidget(d)
    assert d.result_opt() == {"coord": "georef"} and not d.cbT.isEnabled()
    d.rTopo.setChecked(True)
    assert d.cbT.isEnabled() and d.result_opt() == {"coord": "topo", "topo_id": 7, "depth": True}
    # ---- SAM (bila model tersedia)
    if pg.vision().get("sam"):
        import numpy as np
        from PIL import Image as Im
        a = np.zeros((400, 600, 3), np.uint8) + 120
        a[100:300, 250:450] = (200, 90, 40)
        src = tmp_path / "lapangan" / "kotak.png"
        Im.fromarray(a).save(src)
        monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
        pg.add_photo()
        qtbot.waitUntil(lambda: pg.cur and pg.cur["name"] == "kotak.png" and pg.view.w > 0, timeout=8000)
        pg.cbKind.setCurrentIndex(pg.cbKind.findData("vein"))  # garis -> SAM mengganti ke zona
        pg.bSam.click()
        assert pg.tool.mode == "sam" and pg.kmap[pg.cbKind.currentData()]["shape"] == "poly"
        pg.tool.press(_pt(pg, 0.58, 0.5), None)
        qtbot.waitUntil(lambda: bool(pg.sam_poly) and not pg.sam_busy, timeout=60000)
        us = [p[0] for p in pg.sam_poly]
        assert abs(min(us) - 0.417) < 0.04 and abs(max(us) - 0.75) < 0.04 and "SAM" in pg.hintL.text()
        n0 = len(pg.feats)
        pg.tool.key(Qt.Key_Return)
        assert len(pg.feats) == n0 + 1 and pg.feats[-1]["shape"] == "poly" and pg.tool.mode == "sam" and not pg.sam_poly
        from PySide6.QtGui import QImage, QPainter
        img = QImage(300, 200, QImage.Format_RGB32)
        p = QPainter(img)
        pg.canvas.paint(p, None)
        p.end()
        assert pg.escape() and pg.tool.mode == "select"
    # ---- topografi: impor DTM fiktif lewat dialog, cek, ekspor
    pts = [{"name": f"G{i}", "u": u, "v": v, "e": 1000 + u * 20, "n": 3000.0, "rl": 100 + (1 - v) * 16}
           for i, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
    from corex import api
    api.call("/core/outcrop/georef", {"folder": pg.folder, "id": pg.cur["id"], "points": pts, "kind": "wall", "by": "Rina"})
    _draw(pg, "kontak_lito", [(0.02, 0.5), (0.5, 0.5)])
    files = _wall_dtm(tmp_path)
    monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: (files, ""))
    from corex.dialogs import Dlg
    monkeypatch.setattr("corex.outcrop.TopoDlg.exec", lambda self: Dlg.Accepted)
    monkeypatch.setattr("corex.outcrop.TopoDlg.values", lambda self: ("Topo M41", "2026-10-13"))
    pg.topo_import()
    qtbot.waitUntil(lambda: pg.tList.count() == 1, timeout=15000)
    assert "Topo M41" in pg.tList.item(0).text() and pg.tChk.isEnabled()
    pg.tabs.setCurrentIndex(3)
    pg.topo_check()
    qtbot.waitUntil(lambda: "Cakupan DTM" in pg.tRes.text(), timeout=15000)
    assert "titik survey ke DTM" in pg.tRes.text()
    monkeypatch.setattr("corex.outcrop.show_in_folder", lambda p: None)
    for opt, name in (({"coord": "georef"}, "geo"), ({"coord": "topo", "topo_id": pg.topo_sel(), "depth": False}, "topo")):
        monkeypatch.setattr("corex.outcrop.CoordDlg.result_opt", lambda self, o=opt: o)
        out = tmp_path / f"k_{name}.str"
        monkeypatch.setattr("corex.outcrop.QFileDialog.getSaveFileName", lambda *a, out=out, **k: (str(out), ""))
        monkeypatch.setattr("corex.outcrop.ask", lambda *a, **k: True)
        pg.export_geo("str", False)
    geo = [ln for ln in (tmp_path / "k_geo.str").read_text().splitlines() if ln.startswith("1,")]
    topo = [ln for ln in (tmp_path / "k_topo.str").read_text().splitlines() if ln.startswith("1,")]
    assert len(geo) == 2 and len(topo) > 10 and all(abs(float(ln.split(",")[1]) - 3000) < 1e-6 for ln in geo)
    assert any(abs(float(ln.split(",")[1]) - 3000) > 0.05 for ln in topo)
