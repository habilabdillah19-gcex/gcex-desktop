"""Uji API backend (dijalankan di GitHub Actions; butuh fastapi + httpx)."""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend.server import app  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)


def test_health():
    r = c.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_info_reports_access_driver_state():
    j = c.get("/info").json()
    assert "access" in j and "drivers" in j["access"]


def test_excel_register_returns_xlsx():
    r = c.post("/excel/register", json={"headers": ["A", "B"], "rows": [[1, 2]]})
    assert r.status_code == 200 and r.content[:2] == b"PK"


def test_error_is_readable_json():
    r = c.post("/excel/append", json={"path": "C:/tidak/ada.xlsx", "headers": ["A"], "rows": [[1]]})
    assert r.status_code == 500 and r.json()["ok"] is False and "tidak ditemukan" in r.json()["error"]


def test_register_write_dry_run_then_write(tmp_path):
    from openpyxl import Workbook
    f = tmp_path / "reg.xlsx"
    wb = Workbook(); ws = wb.active; ws.title = "GC_Polygon"
    ws["A4"], ws["B4"] = "Kode Poligon GC", "Volume As-mined (BCM)"
    ws["A5"], ws["B5"] = "P2_240_15_0101DS_LGSF_SPL", 383
    wb.save(f)
    body = {"path": str(f), "headers": ["Kode Poligon GC", "Volume As-mined (BCM)"],
            "rows": [["P1_274_05_0101DS_HGSF_ROM", 412.5], ["P2_240_15_0101DS_LGSF_SPL", 1]], "dry_run": True}
    j = c.post("/excel/register-write", json=body).json()
    assert j["ok"] and j["sheet"] == "GC_Polygon" and j["added"] == 1 and j["rows"][0]["row"] == 6
    body["dry_run"] = False
    j = c.post("/excel/register-write", json=body).json()
    assert j["ok"] and j["first_row"] == 6 and j["backup"]
    r = c.post("/excel/register-write", json={**body, "path": str(tmp_path / "tidak_ada.xlsx")})
    assert r.status_code == 500 and r.json()["ok"] is False


def test_mdl_open_subset_benches(tmp_path, monkeypatch):
    import time
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_mdl_io import make_mdl
    f = tmp_path / "uji.mdl"
    make_mdl(f, n=1500)
    for _ in range(100):
        j = c.post("/mdl/open", json={"path": str(f)}).json()
        if j["state"] != "building":
            break
        time.sleep(0.05)
    assert j["ok"] and j["state"] == "ready" and j["info"]["n"] == 1500
    r = c.post("/mdl/subset", json={"path": str(f), "z_min": 130, "z_max": 150})
    assert r.status_code == 200 and r.content.startswith(b"### Block Model ###") and int(r.headers["x-gcex-n"]) > 0
    rc = c.post("/mdl/subset", json={"path": str(f), "z_min": 130, "z_max": 150, "bbox": [None, None, None, None], "center": True})
    assert rc.status_code == 200 and 0 < int(rc.headers["x-gcex-n"]) <= int(r.headers["x-gcex-n"])
    rm = c.post("/mdl/subset", json={"path": str(f), "max_n": 400})
    assert rm.status_code == 200 and rm.headers["x-gcex-capped"] == "1" and 0 < int(rm.headers["x-gcex-n"]) <= 400
    assert int(rm.headers["x-gcex-nreq"]) == 1500 and float(rm.headers["x-gcex-zmin"]) > 0
    ru = c.post("/mdl/subset", json={"path": str(f), "max_n": 10 ** 6})
    assert ru.headers["x-gcex-capped"] == "0" and int(ru.headers["x-gcex-n"]) == 1500
    b = c.post("/mdl/benches", json={"path": str(f), "bench": 10, "ref": 100, "attrs": ["au"]}).json()
    assert b["ok"] and b["total"]["n"] == 1500 and abs(b["total"]["ton"] - sum(x["ton"] for x in b["rows"])) < 1e-6
    e = c.post("/mdl/benches", json={"path": str(f), "bench": 10, "ref": 100, "attrs": ["kelas"]}).json()
    assert e["ok"] is False and "kalkulasi" in e["error"]
