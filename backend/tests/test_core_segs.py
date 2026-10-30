"""Uji segmen per baris core: AI -> segmen, edit manual (atribut, batas, belah, gabung, tambah, hapus) tidak ditimpa AI."""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import core_io, core_segs  # noqa: E402
from gcex_backend.server import app  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)
AI = [{"row": 1, "start": 0, "end": 0.6, "lithology": "AND", "weathering": "W2 (Slightly Weathered)", "rqd_pct": 80, "recovery_pct": 98},
      {"row": 1, "start": 0.6, "end": 1, "lithology": "QV", "weathering": "W1 (Fresh)", "rqd_pct": 92, "recovery_pct": 100},
      {"row": 2, "start": 0, "end": 1, "lithology": "QV", "weathering": "W1 (Fresh)", "rqd_pct": 35, "ff_per_m": 14, "recovery_pct": 90},
      {"row": 3, "start": 0, "end": 1.2, "lithology": "DAC", "weathering": None, "rqd_pct": 60, "recovery_pct": 95},
      {"row": 4, "start": 0.5, "end": 0.2, "lithology": "DAC", "rqd_pct": "70%", "recovery_pct": 96}]


@pytest.fixture()
def prj(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "foto"
    d.mkdir()
    Image.new("RGB", (400, 300), (90, 80, 70)).save(d / "LTH-101_Box1_0.00-4.00.jpg")
    core_io._PROJECTS.clear()
    c.post("/core/open", json={"folder": str(d)})
    r = c.post("/core/rows", json={"folder": str(d)}).json()["rows"][0]
    return str(d), r["id"]


def _segs(folder, pid):
    return c.post("/core/segs/list", json={"folder": folder, "id": pid}).json()["segs"]


def test_ai_segments_to_depth(prj):
    folder, pid = prj
    p = core_io.get_project(folder)
    assert core_segs.apply_ai_segments(p, pid, AI, 4, "qwen3-vl:8b") == 5
    s = _segs(folder, pid)
    assert [(x["from_m"], x["to_m"]) for x in s] == [(0.0, 0.6), (0.6, 1.0), (1.0, 2.0), (2.0, 3.0), (3.2, 3.5)]
    assert s[2]["ff_per_m"] == 14 and s[4]["rqd_pct"] == 70 and s[0]["src"] == "ai" and s[0]["edited"] == []
    assert c.post("/core/rows", json={"folder": folder}).json()["rows"][0]["n_segs"] == 5


def test_manual_edits_survive_ai_rerun(prj):
    folder, pid = prj
    p = core_io.get_project(folder)
    core_segs.apply_ai_segments(p, pid, AI, 4, "m")
    s = _segs(folder, pid)
    # edit atribut segmen 2 (QV 0.6-1.0)
    j = c.post("/core/segs/save", json={"folder": folder, "by": "Rina", "photo_id": pid, "seg_id": s[1]["id"], "seg": {"attrs": {"rqd_pct": 88, "weathering": "W2 (Slightly Weathered)"}}}).json()
    assert j["ok"] and {"rqd_pct", "weathering"} <= set(next(x for x in j["segs"] if x["id"] == s[1]["id"])["edited"])
    # geser batas AND|QV dari 0.6 m ke 0.7 m: tetangga ikut
    j = c.post("/core/segs/bound", json={"folder": folder, "by": "Rina", "seg_id": s[1]["id"], "side": "start", "f": 0.7 / 4}).json()
    t = {x["id"]: x for x in j["segs"]}
    assert t[s[0]["id"]]["to_m"] == 0.7 and t[s[1]["id"]]["from_m"] == 0.7
    # belah segmen row 2 di 1.5 m, gabung kembali
    j = c.post("/core/segs/split", json={"folder": folder, "by": "Rina", "seg_id": s[2]["id"], "f": 1.5 / 4}).json()
    assert len(j["segs"]) == 6
    j = c.post("/core/segs/merge", json={"folder": folder, "by": "Rina", "seg_id": s[2]["id"]}).json()
    assert len(j["segs"]) == 5 and next(x for x in j["segs"] if x["id"] == s[2]["id"])["to_m"] == 2.0
    # segmen manual baru 3.0-3.2 (celah AI) memotong yang tumpang tindih
    j = c.post("/core/segs/save", json={"folder": folder, "by": "Rina", "photo_id": pid, "seg": {"from_m": 2.8, "to_m": 3.2, "attrs": {"lithology": "BX", "rqd_pct": 10}}}).json()
    ss = j["segs"]
    assert any(x["lithology"] == "BX" and x["src"] == "manual" for x in ss)
    assert next(x for x in ss if x["lithology"] == "DAC" and x["from_m"] == 2.0)["to_m"] == 2.8
    # AI dijalankan ulang: segmen yang diedit / manual tetap, AI mengisi sisanya tanpa tumpang tindih
    core_segs.apply_ai_segments(p, pid, AI, 4, "m2")
    ss = _segs(folder, pid)
    kept = next(x for x in ss if x["id"] == s[1]["id"])
    assert kept["rqd_pct"] == 88 and kept["from_m"] == 0.7
    assert any(x["lithology"] == "BX" for x in ss)
    for a, b in zip(ss, ss[1:]):
        assert a["to_m"] <= b["from_m"] + 1e-6
    h = c.post("/core/history", json={"folder": folder, "id": pid, "values": {}}).json()["history"]
    assert any(x["field"] == "segmen" and x["src"] == "manual" for x in h)


def test_verified_photo_untouched_and_excel_search(prj):
    folder, pid = prj
    p = core_io.get_project(folder)
    core_segs.apply_ai_segments(p, pid, AI, 4, "m")
    c.post("/core/verify", json={"folder": folder, "ids": [pid], "value": True, "by": "x"})
    assert core_segs.apply_ai_segments(p, pid, AI[:1], 4, "m") == 0 and len(_segs(folder, pid)) == 5
    assert c.post("/core/segs/save", json={"folder": folder, "photo_id": pid, "seg": {"from_m": 3, "to_m": 2}}).status_code >= 400
    s = c.post("/core/dh/search", json={"folder": folder, "q": "QV"}).json()["results"]
    assert any(x["type"] == "segmen" for x in s)
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(c.post("/core/export/xlsx", json={"folder": folder}).content))
    ws = wb["Segmen"]
    assert ws.max_row == 6 and ws["E2"].value == "AND" and ws["B4"].value == 1.0
