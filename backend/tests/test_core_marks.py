"""Uji tanda interval DB-Ex: half core (wajib nomor sampel), core loss -> recovery otomatis, riwayat, AI, Excel, CSV, cari."""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import core_io  # noqa: E402
from gcex_backend.server import app  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def folder(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "foto"
    (d / "LTH-101").mkdir(parents=True)
    for n, (a, b) in enumerate([(0, 3.6), (3.6, 7.2)], 1):
        Image.new("RGB", (400, 300), (90, 80, 70)).save(d / "LTH-101" / f"LTH-101_Box{n}_{a:.2f}-{b:.2f}.jpg")
    core_io._PROJECTS.clear()
    assert c.post("/core/open", json={"folder": str(d)}).json()["scan"]["total"] == 2
    return str(d)


def _rows(folder):
    return {r["name"]: r for r in c.post("/core/rows", json={"folder": folder}).json()["rows"]}


def test_halfcore_requires_sample_and_coreloss_sets_recovery(folder):
    r1 = _rows(folder)["LTH-101_Box1_0.00-3.60.jpg"]
    bad = c.post("/core/marks/save", json={"folder": folder, "by": "Rina", "photo_id": r1["id"], "mark": {"kind": "halfcore", "from_m": 1, "to_m": 2}})
    assert bad.status_code >= 400 and "sampel" in bad.text
    j = c.post("/core/marks/save", json={"folder": folder, "by": "Rina", "photo_id": r1["id"],
                                         "mark": {"kind": "halfcore", "from_m": 1.0, "to_m": 2.0, "sample_no": "LT-0102", "row0": 1, "x0": 0.1, "row1": 1, "x1": 0.4}}).json()
    assert j["ok"] and j["row"]["half_m"] == 1.0 and j["row"]["half_samples"] == "LT-0102"
    assert j["row"]["rec_src"] == "tanda" and j["row"]["recovery_pct"] == 100.0  # ada tanda, belum ada loss
    j = c.post("/core/marks/save", json={"folder": folder, "by": "Rina", "photo_id": r1["id"],
                                         "mark": {"kind": "coreloss", "from_m": 2.5, "to_m": 2.86, "note": "zona hancur"}}).json()
    assert j["row"]["loss_m"] == 0.36 and j["row"]["recovery_pct"] == 90.0  # (3.6-0.36)/3.6
    # tanda keluar dari rentang foto hanya dihitung bagian yang di dalam foto
    lid = j["id"]
    j = c.post("/core/marks/save", json={"folder": folder, "by": "Rina", "photo_id": r1["id"], "mark_id": lid,
                                         "mark": {"kind": "coreloss", "from_m": 3.24, "to_m": 4.0}}).json()
    assert j["row"]["recovery_pct"] == 90.0
    h = c.post("/core/history", json={"folder": folder, "id": r1["id"], "values": {}}).json()["history"]
    assert any(x["field"] == "tanda" and x["src"] == "tanda" for x in h) and any(x["field"] == "recovery_pct" and x["src"] == "tanda" for x in h)


def test_manual_recovery_wins_until_marks_change_and_ai_does_not_overwrite(folder):
    r1 = _rows(folder)["LTH-101_Box1_0.00-3.60.jpg"]
    j = c.post("/core/marks/save", json={"folder": folder, "by": "A", "photo_id": r1["id"], "mark": {"kind": "coreloss", "from_m": 0, "to_m": 0.72}}).json()
    assert j["row"]["recovery_pct"] == 80.0
    p = core_io.get_project(folder)
    core_io.apply_ai(p, r1["id"], {"recovery_pct": 55, "rqd_pct": 40}, "qwen3-vl:8b", 1.0)
    row = _rows(folder)["LTH-101_Box1_0.00-3.60.jpg"]
    assert row["recovery_pct"] == 80.0 and row["rqd_pct"] == 40.0
    row = c.post("/core/update", json={"folder": folder, "by": "A", "id": r1["id"], "values": {"recovery_pct": 85}}).json()["row"]
    assert row["recovery_pct"] == 85.0 and row["rec_src"] is None
    # ubah To foto: tanda dihitung ulang
    c.post("/core/marks/save", json={"folder": folder, "by": "A", "photo_id": r1["id"], "mark": {"kind": "coreloss", "from_m": 1, "to_m": 1.36}})
    row = c.post("/core/update", json={"folder": folder, "by": "A", "id": r1["id"], "values": {"to_m": 4.0}}).json()["row"]
    assert row["recovery_pct"] == round((4.0 - 1.08) / 4.0 * 100, 1) and row["rec_src"] == "tanda"
    # hapus semua tanda: nilai tetap, sumber dilepas
    for m in c.post("/core/marks/list", json={"folder": folder, "id": r1["id"]}).json()["marks"]:
        c.post("/core/marks/delete", json={"folder": folder, "by": "A", "mark_id": m["id"]})
    row = _rows(folder)["LTH-101_Box1_0.00-3.60.jpg"]
    assert row["n_marks"] == 0 and row["rec_src"] is None and row["recovery_pct"] == 91.0


def test_validation_search_csv_and_excel(folder):
    r2 = _rows(folder)["LTH-101_Box2_3.60-7.20.jpg"]
    assert c.post("/core/marks/save", json={"folder": folder, "photo_id": r2["id"], "mark": {"kind": "coreloss", "from_m": 5, "to_m": 4}}).status_code >= 400
    c.post("/core/marks/save", json={"folder": folder, "by": "B", "photo_id": r2["id"], "mark": {"kind": "halfcore", "from_m": 4, "to_m": 5.1, "sample_no": "LT-0207", "note": "untuk duplikat"}})
    c.post("/core/marks/save", json={"folder": folder, "by": "B", "photo_id": r2["id"], "mark": {"kind": "Rusak pengangkutan", "from_m": 6, "to_m": 6.2}})
    s = c.post("/core/dh/search", json={"folder": folder, "q": "LT-0207"}).json()
    assert s["results"][0]["type"] == "tanda" and s["results"][0]["photo_id"] == r2["id"]
    assert any(x["type"] == "tanda" for x in c.post("/core/dh/search", json={"folder": folder, "q": "half core"}).json()["results"])
    csv = c.post("/core/marks/csv", json={"folder": folder}).content.decode("utf-8-sig").splitlines()
    assert csv[0].startswith("Hole ID,From (m),To (m)") and len(csv) == 3 and "LT-0207" in csv[1]
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(c.post("/core/export/xlsx", json={"folder": folder}).content))
    assert wb["Interval"].max_row == 3 and wb["Interval"]["F2"].value == "LT-0207"
    head = [x.value for x in wb["Core Log"][1]]
    i = head.index("Half core (m)")
    vals = [r[i].value for r in wb["Core Log"].iter_rows(min_row=2)]
    assert 1.1 in vals
