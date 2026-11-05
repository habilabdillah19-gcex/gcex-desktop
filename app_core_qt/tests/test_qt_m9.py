"""Uji jendela Model 3D (Qt): model baru dari 10 foto dinding sintetis, bangun, tempel koordinat titik cat RTK, klik titik
cat di foto (menempel ke usulan deteksi), ukur bidang vein dengan klik di sepanjang jejak, tampilan & ekspor CSV."""
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PySide6.QtCore import QPointF  # noqa: E402

from test_qt_m1 import _win, prj  # noqa: E402,F401

pytest.importorskip("cv2")


def _uv(B, i, X, W=1600, H=1200):
    cam = B.m3d_cameras(10)[i]
    f = 24 / 36 * W
    xc = cam["R"] @ (np.array(X) - cam["C"])
    return (f * xc[0] / xc[2] + W / 2) / W, (f * xc[1] / xc[2] + H / 2) / H, xc[2]


def test_model3d_dialog(qtbot, prj, tmp_path, monkeypatch):
    import buat_data_dummy as B
    from corex.oc3d import Model3DDialog
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    w.set_mode("oc")
    pg = w.outcrop
    assert pg.bM3d.isEnabled()
    src = B.model3d_data(tmp_path / "data")
    monkeypatch.setattr("corex.oc3d.say", lambda *a, **k: pytest.fail(str(a[1:])))
    d = Model3DDialog(pg)
    qtbot.addWidget(d)
    assert d.m is None and not d.bBuild.isEnabled()
    monkeypatch.setattr("corex.oc3d.QFileDialog.getOpenFileNames", lambda *a, **k: (sorted(str(p) for p in src.glob("IMG_*.jpg")), ""))
    d.new_model()
    assert d.m["name"] == "Dinding_M01" and d.lst.count() == 10 and "Belum dibangun" in d.st.text()
    d.build()
    qtbot.waitUntil(lambda: not d.busy and bool(d.m.get("recon")), timeout=300000)
    assert "georef GPS kamera" in d.st.text() and d.m["recon"]["n_cams"] == 10
    # koordinat RTK ditempel dari CSV
    assert d.paste_gcps((src / "Titik_RTK_Dinding_M01.csv").read_text(encoding="utf-8")) == 5
    assert d.gT.rowCount() == 5 and d.gT.item(0, 4).text() == "0"
    # klik titik cat di foto: usulan deteksi + klik dekat (menempel)
    for i in range(10):
        d.lst.setCurrentRow(i)
        qtbot.waitUntil(lambda: d.view.w > 0 and d.img == i, timeout=8000)
        d.detect()
        for k, (nm, gs, gz) in enumerate(B.M3D_GCP):
            u, v, z = _uv(B, i, B.m3d_point(gs, gz))
            if z > 0 and 0.02 < u < 0.98 and 0.02 < v < 0.98:
                d.gT.selectRow(k)
                d.tool.press(QPointF((u + 0.0015) * d.view.w, v * d.view.h), None)
    assert d.m["georef"]["method"] == "rtk" and d.m["georef"]["rms"] < 0.12 and "georef RTK" in d.st.text()
    assert all(int(d.gT.item(k, 4).text()) >= 2 for k in range(5)) and d.gT.item(0, 5).text()
    t = d.m["gcps"][0]["obs"]
    tg = d.targets  # foto terakhir
    assert t and tg
    # ukur bidang vein di foto 5 (indeks 4)
    nv, pv = B._plane(B.M3D_VEIN["dip"], B.M3D_VEIN["ddir"], B.M3D_VEIN["p"])
    tr = []
    for ss in np.linspace(0.1, 29.9, 200):
        P = np.array([B.m3d_point(ss, zz) for zz in np.linspace(0.2, 9.8, 200)])
        dd = (P - pv) @ nv
        tr += [P[k] for k in np.where(np.diff(np.sign(dd)) != 0)[0]]
    d.lst.setCurrentRow(4)
    qtbot.waitUntil(lambda: d.view.w > 0 and d.img == 4, timeout=8000)
    d.cbKind.setCurrentIndex(0)
    d.eName.setText("Vein utama")
    d.start_measure()
    for X in tr[::4]:
        u, v, z = _uv(B, 4, X)
        if z > 0 and 0.02 < u < 0.98 and 0.02 < v < 0.98:
            d.tool.press(QPointF(u * d.view.w, v * d.view.h), None)
    assert "Ukur bidang" in d.info.text() and len(d.draft) >= 6
    d.finish_measure()
    assert d.mT.rowCount() == 1 and d.tool.mode == "gcp"
    dip = int(d.mT.item(0, 2).text().rstrip("°"))
    ddir = int(d.mT.item(0, 3).text().rstrip("°"))
    assert abs(dip - 62) <= 4 and abs(ddir - 120) <= 12 and "dip" in d.mInfo.text()
    # tampilan & ekspor
    pytest.importorskip("matplotlib")
    d.tabs.setCurrentIndex(2)
    qtbot.waitUntil(lambda: d.vImg.pixmap() is not None and not d.vImg.pixmap().isNull(), timeout=30000)
    monkeypatch.setattr("corex.oc3d.show_in_folder", lambda p: None)
    out = tmp_path / "bidang.csv"
    monkeypatch.setattr("corex.oc3d.QFileDialog.getSaveFileName", lambda *a, **k: (str(out), ""))
    d.export("csv")
    assert "Vein utama" in out.read_text(encoding="utf-8-sig")
