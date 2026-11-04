"""Uji Model 3D (fotogrametri) Singkapan: 10 foto dinding zig-zag sintetis (buat_data_dummy.model3d_data) -> rekonstruksi,
georef GPS HP (kasar) lalu titik RTK (teliti), deteksi titik cat, ukur bidang vein -> dip / arah dip sebenarnya mendekati kunci
jawaban, ekspor CSV / STR / PLY. Semua data fiktif."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "backend"))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))
from gcex_backend import core_io, core_outcrop as O  # noqa: E402

pytest.importorskip("cv2")


def _truth_uv(B, i, X, W=1600, H=1200):
    cam = B.m3d_cameras(10)[i]
    f = 24 / 36 * W
    xc = cam["R"] @ (np.array(X) - cam["C"])
    return (f * xc[0] / xc[2] + W / 2) / W, (f * xc[1] / xc[2] + H / 2) / H, xc[2]


def test_model3d_end_to_end(tmp_path, monkeypatch):
    import buat_data_dummy as B
    from gcex_backend import core_oc3d as M
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "proyek"
    d.mkdir()
    core_io._PROJECTS.clear()
    O._STORES.clear()
    s = O.store(str(d))
    src = B.model3d_data(tmp_path / "data")
    fs = sorted(str(p) for p in src.glob("IMG_*.jpg"))
    with pytest.raises(ValueError, match="minimal 3"):
        M.create(s, "x", fs[:2], "uji")
    with pytest.raises(ValueError, match="Maksimal 10"):
        M.create(s, "x", fs + fs[:1], "uji")
    m = M.create(s, "Dinding M01", fs, "uji")
    assert m["id"] == 1 and len(m["photos"]) == 10 and m["photos"][0]["exif"]["f35"] == 24 and M.models(s)[0]["status"] == "baru"
    m = M.build(s, 1)
    rec = m["recon"]
    assert rec["n_cams"] == 10 and rec["n_points"] > 3000 and rec["reproj_px"] < 1.0
    # tanpa RTK: georef kasar dari GPS HP
    assert m["georef"]["method"] == "gps" and "KASAR" in m["georef"]["msg"]
    # deteksi titik cat di foto 4 cocok dengan proyeksi sebenarnya
    tg = M.detect_targets(M.photo_path(s, 1, 3))
    true3 = [u for nm, gs, gz in B.M3D_GCP for u in [_truth_uv(B, 3, B.m3d_point(gs, gz))] if u[2] > 0 and 0 < u[0] < 1 and 0 < u[1] < 1]
    assert all(min(math.hypot(t["u"] - a, t["v"] - b) for t in tg) < 0.004 for a, b, _z in true3)
    # titik RTK (posisi sebenarnya diklik di semua foto yang melihatnya)
    E0, N0, RL0 = B.M3D_ORIGIN
    gcps = []
    for nm, gs, gz in B.M3D_GCP:
        X = B.m3d_point(gs, gz)
        obs = {str(i): [u, v] for i in range(10) for u, v, z in [_truth_uv(B, i, X)] if z > 0 and 0.01 < u < 0.99 and 0.01 < v < 0.99}
        gcps.append({"name": nm, "e": E0 + X[0], "n": N0 + X[1], "rl": RL0 + X[2], "obs": obs})
    gcps.append({"name": "RTK99", "e": "", "n": "", "rl": "", "obs": {}})
    m = M.save_gcps(s, 1, gcps)
    g = m["georef"]
    assert g["method"] == "rtk" and g["n"] == 5 and g["rms"] < 0.12  # 0,1 cm (OpenCV 5) s.d. ~6 cm (OpenCV 4.10 di CI)
    # vein: titik di sepanjang jejak yang melintasi sudut dinding -> dip / arah dip sebenarnya
    nv, pv = B._plane(B.M3D_VEIN["dip"], B.M3D_VEIN["ddir"], B.M3D_VEIN["p"])
    tr = []
    for ss in np.linspace(0.1, 29.9, 300):
        P = np.array([B.m3d_point(ss, z) for z in np.linspace(0.2, 9.8, 300)])
        dd = (P - pv) @ nv
        tr += [P[k] for k in np.where(np.diff(np.sign(dd)) != 0)[0]]
    uv = [[u, v] for X in tr[::5] for u, v, z in [_truth_uv(B, 4, X)] if z > 0 and 0.02 < u < 0.98 and 0.02 < v < 0.98]
    me = M.add_measure(s, 1, "Vein utama", "vein", 4, uv, "uji")
    r = me["result"]
    assert abs(r["dip"] - B.M3D_VEIN["dip"]) < 4 and min(abs(r["ddir"] - B.M3D_VEIN["ddir"]), 360 - abs(r["ddir"] - B.M3D_VEIN["ddir"])) < 12
    assert r["quality"] in ("baik", "sedang") and r["georef"] == "rtk" and r["strike"] == pytest.approx((r["ddir"] - 90) % 360)
    # jejak lurus di satu bidang dinding datar -> mutu tidak pasti
    flat = [[0.30 + 0.02 * k, 0.55] for k in range(6)]
    me2 = M.add_measure(s, 1, "Lurus", "kekar", 1, flat, "uji")
    assert me2["result"]["quality"] in ("tidak pasti", "lemah")
    with pytest.raises(ValueError, match="minimal 3"):
        M.add_measure(s, 1, "x", "vein", 4, uv[:2], "uji")
    csv = M.export(s, 1, "csv").decode("utf-8-sig")
    assert "Vein utama,vein" in csv and csv.count("\n") == 3
    st = M.export(s, 1, "str").decode()
    assert "vein, Vein utama" in st and st.strip().endswith("END")
    ply = M.export(s, 1, "ply").decode()
    assert f"element vertex {rec['n_points']}" in ply
    M.del_measure(s, 1, me2["id"])
    assert len(M.load(s, 1)["measures"]) == 1
    pytest.importorskip("matplotlib")
    assert M.views_png(s, 1)
