"""Uji lokasi kamera dari metadata foto HP (Fase 2a): baca EXIF GPS gaya iPhone, WGS84 -> UTM, sistem koordinat proyek,
tanggal foto otomatis, lubang terdekat, pemeriksaan terhadap georef, peta posisi foto. Koordinat FIKTIF."""
import sys
from pathlib import Path

import pytest
from PIL import Image

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "backend"))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))
from gcex_backend import core_dh, core_io, core_oclokasi as L, core_outcrop as O  # noqa: E402


def test_utm_reference_values():
    assert L.to_utm(0.0, 117.0, south=True)[:2] == pytest.approx((500000.0, 10000000.0), abs=1e-3)  # meridian tengah zona 50S
    e, n, z, south = L.to_utm(0.0, 120.0, zone=50, south=False)                      # 3° dari meridian tengah di ekuator
    assert e == pytest.approx(833978.556, abs=0.01) and n == pytest.approx(0.0, abs=1e-6) and z == 50 and not south
    assert L.utm_zone(117.3) == 50 and L.utm_zone(-0.1) == 30 and L.to_utm(-5.5, 117.3)[2:] == (50, True)


@pytest.fixture()
def prj(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "proyek"
    d.mkdir()
    core_io._PROJECTS.clear()
    O._STORES.clear()
    return d, tmp_path


def test_exif_camera_crs_nearest_and_map(prj):
    from buat_data_dummy import with_gps
    d, tmp = prj
    src = tmp / "lapangan"
    src.mkdir()
    Image.new("RGB", (800, 600), (120, 110, 100)).save(src / "plain.jpg")
    with_gps(src / "plain.jpg", src / "IMG_0001.jpg", -5.5012, 117.3021, 312.4, 285.0, 6.5, "2026-10-30 09:15:00")
    s = O.store(str(d))
    ex = L.read_exif(src / "IMG_0001.jpg")
    assert ex["lat"] == pytest.approx(-5.5012, abs=1e-6) and ex["lon"] == pytest.approx(117.3021, abs=1e-6)
    assert ex["alt"] == 312.4 and ex["hacc"] == 6.5 and ex["heading"] == 285.0 and ex["heading_ref"] == "sejati"
    assert ex["taken"] == "2026-10-30 09:15" and ex["tz"] == "+08:00" and ex["f35"] == 24 and "iPhone 17 Pro" in ex["camera"]
    p = O.add_photo(s, str(src / "IMG_0001.jpg"), "Rina")
    assert p["taken"] == "2026-10-30 09:15"  # tanggal foto terisi dari EXIF
    p0 = O.add_photo(s, str(src / "plain.jpg"), "Rina")
    assert L.camera(s, O.photo(s, p0["id"])) is None and L.read_exif(src / "plain.jpg") == {}
    cam = L.camera(s, O.photo(s, p["id"]))
    e, n = L.to_utm(-5.5012, 117.3021)[:2]
    assert cam["zone"] == "50S" and cam["e"] == pytest.approx(e, abs=0.01) and cam["n"] == pytest.approx(n, abs=0.01)
    assert cam["rl"] == 312.4 and cam["hacc"] == 6.5 and cam["heading"] == 285.0 and not cam["warn"] and "nearest" not in cam
    assert L.compass(cam, "wall") == {"mode": "view", "az": 285.0} and L.compass(cam, "floor") == {"mode": "north", "rot": -285.0}
    # collar bor UTM di dekat kamera -> lubang terdekat; collar grid lokal -> peringatan sistem koordinat
    pj = core_io.get_project(str(d))
    core_dh.do_import(pj, "collar", [["Hole", "E", "N", "RL", "EOH"], ["GC_001", e + 30, n + 40, 300, 50], ["GC_002", e + 300, n, 300, 50]],
                      0, {"hole": 0, "x": 1, "y": 2, "z": 3, "depth": 4}, [], "replace")
    cam = L.camera(s, O.photo(s, p["id"]))
    assert cam["nearest"] == {"hole": "GC_001", "dist": 50.0}
    core_dh.do_import(pj, "collar", [["Hole", "E", "N", "RL", "EOH"], ["LTH-101", 10250.5, 20410.2, 312, 80]],
                      0, {"hole": 0, "x": 1, "y": 2, "z": 3, "depth": 4}, [], "replace")
    assert any("grid lokal" in w for w in L.camera(s, O.photo(s, p["id"]))["warn"])
    # zona proyek dipaksa 51S: titik di zona 50 dihitung di zona 51 + peringatan
    L.save_crs(s, 51, True, "Rina")
    cam51 = L.camera(s, O.photo(s, p["id"]))
    assert cam51["zone"] == "51S" and cam51["e"] < 300000 and any("zona UTM 50" in w for w in cam51["warn"])
    L.save_crs(s, None, None, "Rina")
    assert L.crs(s) == {"zone": None, "south": None} and "otomatis" in L.crs_label(L.crs(s))
    # georef jauh dari kamera -> peringatan foto / titik tertukar
    O.update_photo(s, p["id"], {"desc:photo_type": "wall"}, "Rina")
    O.save_georef(s, p["id"], [{"name": f"G{i}", "u": u, "v": v, "e": e + 2000 + 10 * u, "n": n + 2000, "rl": 300 - 10 * v}
                               for i, (u, v) in enumerate(((0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)))], "wall", "Rina")
    cam = L.camera(s, O.photo(s, p["id"]))
    assert cam["georef_dist"] > 2000 and any("tertukar" in w for w in cam["warn"])
    loc = L.locations(s)
    assert loc["n_gps"] == 1 and len(loc["photos"]) == 2
    pytest.importorskip("matplotlib")
    assert L.map_png(s, p["id"])
