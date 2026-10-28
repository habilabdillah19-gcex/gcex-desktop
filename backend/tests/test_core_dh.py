"""Uji integrasi data bor GC-Ex Core Interpretation: header dinamis, import Collar/Survey/Assay/Geologi,
kadar per foto, detail foto (overlay), area core box, cari cepat."""
import base64
import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import core_dh, core_io  # noqa: E402
from gcex_backend.server import app  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def prj(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "foto"
    (d / "LTH-101").mkdir(parents=True)
    for bx, a, b in [(10, 32.4, 36.3), (11, 36.3, 40.1)]:
        Image.new("RGB", (400, 300)).save(d / "LTH-101" / f"LTH-101_Box{bx}_{a}-{b}.jpg")
    Image.new("RGB", (400, 300)).save(d / "IMG_0001.jpg")
    core_io._PROJECTS.clear()
    c.post("/core/open", json={"folder": str(d)})
    return d, tmp_path


def _csv(tmp, name, text):
    f = tmp / name
    f.write_text(text, encoding="utf-8")
    return str(f)


ASSAY = """Laporan Lab PT X;;;;;;
BHID;Depth_From (m);TO;Sample No;Au_ppm;Ag ppm;Cu_pct
LTH 101;35,0;36,5;S001;0,25;3;0.01
LTH 101;36,5;38,0;S002;<0.01;1;0.02
LTH 101;38,0;39,0;S003;4.80;25;0.15
LTH 101;39,0;41,0;S004;1.2;-;0.05
LTH-999;0;1;S005;9;9;9
;1;2;S006;1;1;1
LTH 101;5;4;S007;1;1;1
"""


def test_preview_guesses_dynamic_headers(prj):
    d, tmp = prj
    f = _csv(tmp, "assay.csv", ASSAY)
    j = c.post("/core/dh/preview", json={"folder": str(d), "kind": "assay", "path": f}).json()
    assert j["ok"] and j["header_row"] == 1 and j["nrows"] == 7
    h = j["headers"]
    r = j["guess"]["roles"]
    assert (h[r["hole"]], h[r["from"]], h[r["to"]]) == ("BHID", "Depth_From (m)", "TO")
    cols = {x["src"]: x for x in j["guess"]["cols"]}
    assert cols["Au_ppm"]["type"] == "n" and cols["Ag ppm"]["type"] == "n" and cols["Sample No"]["type"] == "s"


def test_import_assay_geology_collar_survey_and_photo_detail(prj):
    d, tmp = prj
    f = _csv(tmp, "assay.csv", ASSAY)
    pv = c.post("/core/dh/preview", json={"folder": str(d), "kind": "assay", "path": f}).json()
    cols = pv["guess"]["cols"]
    for x in cols:  # pengguna memberi nama tampilan sendiri
        x["name"] = {"Au_ppm": "Au", "Ag ppm": "Ag", "Cu_pct": "Cu", "Sample No": "Sample"}[x["src"]]
    j = c.post("/core/dh/import", json={"folder": str(d), "kind": "assay", "path": f, "header_row": pv["header_row"],
                                         "roles": pv["guess"]["roles"], "cols": cols, "mode": "replace"}).json()
    rep = j["report"]
    assert j["ok"] and rep["rows"] == 5 and rep["skipped"] == 2 and rep["bdl"] == 1
    assert rep["reasons"] == {"Hole ID kosong": 1, "From ≥ To": 1} and rep["matched_photo_holes"] == 1
    assert [x["name"] for x in j["summary"]["columns"]["assay"]] == ["Sample", "Au", "Ag", "Cu"]

    # geologi dari Excel dengan header lain
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "Log"
    ws.append(["HoleID", "From", "To", "Lith", "Alteration", "Mineralogy"])
    ws.append(["LTH-101", 30, 37.5, "AND", "Argilik", "pyrite 2%"])
    ws.append(["LTH-101", 37.5, 41, "QV", "Silisifikasi kuat", "pyrite, chalcopyrite"])
    gx = tmp / "geo.xlsx"; wb.save(gx)
    pv = c.post("/core/dh/preview", json={"folder": str(d), "kind": "geology", "path": str(gx)}).json()
    assert pv["sheets"] == ["Log"] and [c_["type"] for c_ in pv["guess"]["cols"]] == ["s", "s", "s"]
    j = c.post("/core/dh/import", json={"folder": str(d), "kind": "geology", "b64": base64.b64encode(gx.read_bytes()).decode(), "name": "geo.xlsx",
                                         "roles": pv["guess"]["roles"], "cols": pv["guess"]["cols"]}).json()
    assert j["report"]["rows"] == 2

    # collar X-Y-Z & survey (dip negatif = ke bawah)
    fc = _csv(tmp, "collar.csv", "Hole,X,Y,Z,EOH\nLTH-101,1000,2000,300,80\n")
    pv = c.post("/core/dh/preview", json={"folder": str(d), "kind": "collar", "path": fc}).json()
    assert {k: pv["headers"][v] for k, v in pv["guess"]["roles"].items() if v is not None} == {"hole": "Hole", "x": "X", "y": "Y", "z": "Z", "depth": "EOH"}
    c.post("/core/dh/import", json={"folder": str(d), "kind": "collar", "path": fc, "roles": pv["guess"]["roles"], "cols": pv["guess"]["cols"]})
    fs = _csv(tmp, "survey.csv", "Hole\tDepth\tDip\tAzimuth\nLTH-101\t0\t-90\t0\nLTH-101\t100\t-90\t0\n")
    pv = c.post("/core/dh/preview", json={"folder": str(d), "kind": "survey", "path": fs}).json()
    j = c.post("/core/dh/import", json={"folder": str(d), "kind": "survey", "path": fs, "roles": pv["guess"]["roles"], "cols": []}).json()
    assert j["report"]["rows"] == 2 and j["summary"]["survey"] == 2

    rows = {r["name"]: r for r in c.post("/core/rows", json={"folder": str(d)}).json()["rows"]}
    box11 = rows["LTH-101_Box11_36.3-40.1.jpg"]
    # Au tertimbang di 36.3-40.1: (0.2*0.25 + 1.5*0.005 + 1*4.8 + 1.1*1.2) / 3.8
    assert box11["g"]["Au"] == pytest.approx((0.2 * 0.25 + 1.5 * 0.005 + 4.8 + 1.1 * 1.2) / 3.8, abs=1e-3)
    assert box11["gmax"]["Au"] == 4.8 and "g" not in rows["IMG_0001.jpg"]

    det = c.post("/core/dh/photo", json={"folder": str(d), "id": box11["id"]}).json()
    assert [x["Sample"] for x in det["assay"]] == ["S001", "S002", "S003", "S004"]
    assert [x["Lith"] for x in det["geology"]] == ["AND", "QV"]
    assert det["collar"]["x"] == 1000 and det["xyz_from"] == {"x": 1000.0, "y": 2000.0, "z": 263.7}
    assert det["tray"]["rows"] == 4 and det["tray_own"] is False

    # Excel memuat kolom rata-rata kadar
    from openpyxl import load_workbook
    x = c.post("/core/export/xlsx", json={"folder": str(d)})
    head = [h.value for h in load_workbook(BytesIO(x.content))["Core Log"][1]]
    assert "Au rata-rata" in head and "Cu maks" in head

    # cari cepat: teks (geologi) dan angka (assay)
    s = c.post("/core/dh/search", json={"folder": str(d), "q": "chalcopyrite"}).json()
    assert s["results"][0]["type"] == "geologi" and s["results"][0]["photo"] == "LTH-101_Box11_36.3-40.1.jpg"
    s = c.post("/core/dh/search", json={"folder": str(d), "q": "au>=1"}).json()
    assert [r["v"] for r in s["results"]] == [9, 4.8, 1.2] and s["results"][0]["photo_id"] is None
    s = c.post("/core/dh/search", json={"folder": str(d), "q": "LTH542"}).json()
    assert any(r["type"] == "foto" for r in s["results"])
    bad = c.post("/core/dh/search", json={"folder": str(d), "q": "Zn>1"})
    assert bad.status_code == 500 and "Zn" in bad.json()["error"]

    # area core box: per foto & bawaan proyek
    c.post("/core/dh/tray", json={"folder": str(d), "scope": "default", "tray": {"x0": 0.05, "y0": 0.4, "x1": 0.95, "y1": 0.9, "rows": 5}})
    assert c.post("/core/dh/photo", json={"folder": str(d), "id": box11["id"]}).json()["tray"]["rows"] == 5
    c.post("/core/dh/tray", json={"folder": str(d), "id": box11["id"], "scope": "photo", "tray": {"x0": 0.1, "y0": 0.3, "x1": 0.9, "y1": 0.95, "rows": 4}})
    t = c.post("/core/dh/photo", json={"folder": str(d), "id": box11["id"]}).json()
    assert t["tray"]["x0"] == 0.1 and t["tray_own"]
    r = c.post("/core/dh/tray", json={"folder": str(d), "id": box11["id"], "tray": {"x0": 0.9, "y0": 0, "x1": 0.1, "y1": 1}})
    assert r.status_code == 500


def test_upsert_replaces_only_holes_in_file_and_reuses_mapping(prj):
    d, tmp = prj
    f = _csv(tmp, "a1.csv", "Hole,From,To,Au\nA-1,0,1,1\nA-1,1,2,2\nB-2,0,1,3\n")
    pv = c.post("/core/dh/preview", json={"folder": str(d), "kind": "assay", "path": f}).json()
    c.post("/core/dh/import", json={"folder": str(d), "kind": "assay", "path": f, "roles": pv["guess"]["roles"], "cols": pv["guess"]["cols"]})
    f2 = _csv(tmp, "a2.csv", "Hole,From,To,Au\nA-1,0,2,5\n")
    pv2 = c.post("/core/dh/preview", json={"folder": str(d), "kind": "assay", "path": f2}).json()
    assert pv2["reused"] is True
    j = c.post("/core/dh/import", json={"folder": str(d), "kind": "assay", "path": f2, "roles": pv2["guess"]["roles"], "cols": pv2["guess"]["cols"], "mode": "upsert"}).json()
    assert j["summary"]["assay"] == 2  # A-1 diganti (1 baris) + B-2 tetap
    j = c.post("/core/dh/clear", json={"folder": str(d), "kind": "assay"}).json()
    assert j["summary"]["assay"] == 0 and j["summary"]["columns"]["assay"] == []


def test_import_requires_roles_and_xls_message(prj):
    d, tmp = prj
    f = _csv(tmp, "x.csv", "A,B\n1,2\n")
    r = c.post("/core/dh/import", json={"folder": str(d), "kind": "assay", "path": f, "roles": {"hole": 0, "from": None, "to": 1}, "cols": []})
    assert r.status_code == 500 and "From" in r.json()["error"]
    (tmp / "old.xls").write_bytes(b"\xd0\xcf")
    r = c.post("/core/dh/preview", json={"folder": str(d), "kind": "assay", "path": str(tmp / "old.xls")})
    assert ".xls" in r.json()["error"]


def test_num_parsing():
    assert core_dh._num("<0.01") == (0.005, True)
    assert core_dh._num(">10") == (10.0, True)
    assert core_dh._num("0,25") == (0.25, True)
    assert core_dh._num("1.234,5") == (1234.5, True)
    assert core_dh._num("-") == (None, False)
    assert core_dh.hole_key("LTH 101") == core_dh.hole_key("lth-101") == "lth101"


def test_geologist_logging_has_priority_over_ai(prj, monkeypatch):
    """AI visual untuk geoteknik; litologi / alterasi dari logging geologist diutamakan dan tidak ditimpa AI."""
    d, tmp = prj
    f = _csv(tmp, "geo.csv", "Hole,From,To,Lithology,Alt_Int,Mineralogy\nLTH-101,36.3,38.5,QV,Silisifikasi kuat,pyrite\nLTH-101,38.5,40.1,DAC,Argilik,-\n")
    pv = c.post("/core/dh/preview", json={"folder": str(d), "kind": "geology", "path": f}).json()
    j = c.post("/core/dh/import", json={"folder": str(d), "kind": "geology", "path": f, "roles": pv["guess"]["roles"], "cols": pv["guess"]["cols"]}).json()
    assert j["summary"]["geo_link"]["lithology"] == "Lithology" and j["summary"]["geo_link"]["alteration"] == "Alt_Int"
    rows = {r["name"]: r for r in c.post("/core/rows", json={"folder": str(d)}).json()["rows"]}
    r11 = rows["LTH-101_Box11_36.3-40.1.jpg"]
    assert r11["log"]["lithology"] == "QV (58%) / DAC (42%)" and "log" not in rows["IMG_0001.jpg"]

    # AI dijalankan: prompt memuat logging, isian logging dilindungi, geoteknik terisi
    sent = {}

    def fake(host, model, img, extra="", timeout=900, logged=None):
        sent["logged"] = logged
        sent["prompt"] = core_io.ai_prompt(extra, logged)
        return {"lithology": "Andesit", "alteration": "Propilitik", "rqd_pct": 75, "gsi": "55-65", "confidence": "sedang"}
    monkeypatch.setattr(core_io, "ollama_analyze", fake)
    core_io.ai_start(core_io.get_project(str(d)), [r11["id"]], "h", "m", "", 800)
    core_io.JOB.thread.join(5)
    assert sent["logged"] == {"lithology": "QV (58%) / DAC (42%)", "alteration": "Silisifikasi kuat (58%) / Argilik (42%)"}
    assert "SUDAH DILOGGING GEOLOGIST" in sent["prompt"] and "GEOTEKNIK" in sent["prompt"]
    r = {x["name"]: x for x in c.post("/core/rows", json={"folder": str(d)}).json()["rows"]}["LTH-101_Box11_36.3-40.1.jpg"]
    assert r["lithology"] is None and r["alteration"] is None and r["rqd_pct"] == 75 and r["log"]["lithology"].startswith("QV")

    # Excel memakai logging + kolom sumber
    from openpyxl import load_workbook
    ws = load_workbook(BytesIO(c.post("/core/export/xlsx", json={"folder": str(d)}).content))["Core Log"]
    head = [h.value for h in ws[1]]
    line = next([x.value for x in row] for row in ws.iter_rows(min_row=2) if row[1].value == "LTH-101_Box11_36.3-40.1.jpg")
    assert line[head.index("Litologi")] == "QV (58%) / DAC (42%)" and "Litologi: logging" in line[head.index("Sumber isian geologi")]

    # pengguna memilih kolom logging sendiri / mematikan
    j = c.post("/core/dh/geolink", json={"folder": str(d), "link": {"lithology": "Lithology", "alteration": None}}).json()
    assert j["summary"]["geo_link"] == {"lithology": "Lithology", "alteration": None} and not j["summary"]["geo_link_auto"]
    j = c.post("/core/dh/geolink", json={"folder": str(d), "link": None}).json()
    assert j["summary"]["geo_link_auto"] and j["summary"]["geo_link"]["alteration"] == "Alt_Int"
