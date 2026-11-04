"""Uji lokasi kamera (GPS HP) di ruang kerja Singkapan (Qt): info posisi di tab Deskripsi, kompas infografis otomatis
dari arah hadap, sistem koordinat proyek, peta foto & tabel lokasi. Koordinat FIKTIF."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))

from PIL import Image  # noqa: E402

from test_qt_m1 import _win, prj  # noqa: E402,F401


def test_lokasi_kamera_gps(qtbot, prj, tmp_path, monkeypatch):
    from buat_data_dummy import with_gps
    from corex.dialogs import Dlg
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    w.set_mode("oc")
    pg = w.outcrop
    src = tmp_path / "lapangan"
    src.mkdir()
    Image.new("RGB", (1200, 800), (120, 110, 100)).save(src / "polos.jpg")
    with_gps(src / "polos.jpg", src / "IMG_0101.jpg", -5.5012, 117.3021, 312.4, 285.0, 6.5, "2026-10-30 09:15:00")
    with_gps(src / "polos.jpg", src / "IMG_0102.jpg", -5.5020, 117.3030, 305.0, 40.0, 4.0, "2026-10-30 09:40:00")
    monkeypatch.setattr("corex.outcrop.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src / "IMG_0101.jpg"), str(src / "IMG_0102.jpg"),
                                                                                         str(src / "polos.jpg")], ""))
    pg.add_photo()
    qtbot.waitUntil(lambda: len(pg.photos) == 3 and pg.cur is not None, timeout=8000)
    pg.lst.setCurrentRow(0)
    qtbot.waitUntil(lambda: pg.cam is not None, timeout=5000)
    t = pg.locInfo.text()
    assert "Kamera (GPS HP)" in t and "50S" in t and "±6.5 m" in t and "285°" in t and pg.eTaken.text() == "2026-10-30 09:15"
    # kompas infografis otomatis dari arah hadap (tanpa georef)
    assert pg.info()["_compass"] == {"mode": "view", "az": 285.0}
    pg.lst.setCurrentRow(2)
    qtbot.waitUntil(lambda: "tanpa data GPS" in pg.locInfo.text(), timeout=5000)
    assert pg.cam is None and "_compass" not in pg.info()
    # sistem koordinat: pilih UTM 51S
    def crs_exec(self):
        pg._crsCb.setCurrentIndex(pg._crsCb.findText("UTM 51S (WGS84)"))
        return Dlg.Accepted
    monkeypatch.setattr(Dlg, "exec", crs_exec)
    pg.lst.setCurrentRow(1)
    qtbot.waitUntil(lambda: pg.cam is not None and pg.cam["heading"] == 40.0, timeout=5000)
    pg.loc_crs()
    assert pg.cam["zone"] == "51S" and "zona UTM 50" in pg.locInfo.text()
    # peta foto: gambar + tabel 3 foto (satu tanpa GPS)
    monkeypatch.setattr(Dlg, "exec", lambda self: Dlg.Accepted)
    pg.loc_map()
    tw = pg._locTw
    assert tw.rowCount() == 3 and tw.item(2, 8).text() == "tanpa GPS" and tw.item(0, 6).text() == "285°"
    import pytest
    pytest.importorskip("matplotlib")
    assert pg._locImg.pixmap() is not None and not pg._locImg.pixmap().isNull()
