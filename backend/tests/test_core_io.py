"""Uji GC-Ex Core Interpretation: proyek foto, nama file, thumbnail, AI lokal (Ollama tiruan), Excel, impor JSON lama."""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import core_io  # noqa: E402
from gcex_backend.server import app  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)


# ---------- Ollama tiruan ----------
class FakeOllama(BaseHTTPRequestHandler):
    calls: list = []

    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/api/version":
            return self._send({"version": "0.12.9"})
        if self.path == "/api/tags":
            return self._send({"models": [{"name": "qwen3-vl:8b", "size": 6100000000, "details": {"parameter_size": "8.8B"}},
                                          {"name": "llama3.2:3b", "size": 2000000000, "details": {}}]})
        self._send({"error": "not found"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/show":
            return self._send({"capabilities": ["completion", "vision"] if "vl" in body["model"] else ["completion"]})
        if self.path == "/api/chat":
            FakeOllama.calls.append(body)
            assert body["messages"][0]["images"], "gambar tidak dikirim"
            assert body["format"]["type"] == "object"
            assert "M:TO" in body["messages"][0]["content"] and "drill_start" in body["format"]["required"]
            ans = {"hole_id": "LTH-101", "box_no": "11", "from_m": 36.3, "to_m": 40.1, "drill_start": "05-03-25", "photo_date": "12-03-25", "lithology": "Andesit",
                   "color": "Abu-abu gelap (Dark Grey)", "weathering": "W2 (Slightly Weathered)", "oxidation": "Slightly Oxidized",
                   "alteration": "Silisifikasi lemah", "condition": "WET", "recovery_pct": 98, "rqd_pct": 120, "gsi": "60-70",
                   "rmr": 68, "notes": "Rekahan jarang, vein kuarsa tipis.", "confidence": "sedang"}
            return self._send({"message": {"role": "assistant", "content": "```json\n" + json.dumps(ans) + "\n```"}, "done": True})
        self._send({"error": "not found"}, 404)


@pytest.fixture(scope="module")
def ollama():
    srv = HTTPServer(("127.0.0.1", 0), FakeOllama)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture()
def folder(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "Foto Core"
    (d / "LTH-101").mkdir(parents=True)
    for i, n in enumerate(["LTH-101_Box11_36.30-40.10.jpg", "LTH-101_Box2_3.5-7.2.JPG", "LTH-101_Box10_32.4-36.3.png"]):
        Image.new("RGB", (3000, 1200), (90 + i * 30, 90, 80)).save(d / "LTH-101" / n)
    Image.new("RGB", (800, 600), (200, 180, 160)).save(d / "IMG_0001.jpg")
    (d / "catatan.txt").write_text("bukan foto")
    core_io._PROJECTS.clear()
    return d


def test_parse_filename():
    assert core_io.parse_filename("LTH-101_Box11_36.30-40.10.jpg") == {"box_no": "11", "from_m": 36.3, "to_m": 40.1, "hole_id": "LTH-101"}
    assert core_io.parse_filename("GCD0123 B05 12,5-15,0m.jpg") == {"box_no": "5", "from_m": 12.5, "to_m": 15.0, "hole_id": "GCD0123"}
    assert core_io.parse_filename("IMG_0001.jpg") == {}
    assert core_io.parse_filename("DSC00012.JPG") == {}
    assert core_io.parse_filename("DDH-07-15 BX4 10.2m-14.0m.jpg") == {"box_no": "4", "from_m": 10.2, "to_m": 14.0, "hole_id": "DDH-07-15"}
    assert core_io.parse_filename("DDH_08_22_box3_4.5-9.0.jpg")["hole_id"] == "DDH_08_22"


def test_open_scan_order_and_filename_guess(folder):
    j = c.post("/core/open", json={"folder": str(folder), "by": "Uji"}).json()
    assert j["ok"] and j["scan"]["added"] == 4 and j["summary"]["total"] == 4 and not j["db_local"]
    assert (folder / "_GCEx_Core" / "gcex_core.db").exists()
    rows = c.post("/core/rows", json={"folder": str(folder)}).json()["rows"]
    names = [r["name"] for r in rows]
    assert names == ["IMG_0001.jpg", "LTH-101_Box2_3.5-7.2.JPG", "LTH-101_Box10_32.4-36.3.png", "LTH-101_Box11_36.30-40.10.jpg"]
    r = rows[1]
    assert (r["hole_id"], r["box_no"], r["from_m"], r["to_m"]) == ("LTH-101", "2", 3.5, 7.2)
    assert r["from_name"] == ["box_no", "from_m", "hole_id", "to_m"]
    # buka ulang: tidak ada duplikat; foto baru & foto hilang terdeteksi
    Image.new("RGB", (100, 100)).save(folder / "LTH-101" / "LTH-101_Box12_40.1-44.0.jpg")
    (folder / "IMG_0001.jpg").unlink()
    core_io._PROJECTS.clear()
    j = c.post("/core/open", json={"folder": str(folder)}).json()
    assert j["scan"] == {"added": 1, "missing": 1, "total": 4}


def test_thumbnail_and_original(folder):
    c.post("/core/open", json={"folder": str(folder)})
    pid = c.post("/core/rows", json={"folder": str(folder)}).json()["rows"][1]["id"]
    r = c.get("/core/img", params={"folder": str(folder), "id": pid, "w": 320})
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    from io import BytesIO
    assert max(Image.open(BytesIO(r.content)).size) == 320
    r0 = c.get("/core/img", params={"folder": str(folder), "id": pid, "w": 0})
    assert r0.status_code == 200 and len(r0.content) > 0
    bad = c.get("/core/img", params={"folder": str(folder), "id": 9999})
    assert bad.status_code == 500 and bad.json()["ok"] is False


def test_ollama_status(ollama):
    j = c.post("/core/ollama", json={"host": ollama}).json()
    assert j["running"] and j["version"] == "0.12.9"
    vis = {m["name"]: m["vision"] for m in j["models"]}
    assert vis == {"qwen3-vl:8b": True, "llama3.2:3b": False}
    off = c.post("/core/ollama", json={"host": "http://127.0.0.1:9"}).json()
    assert off["ok"] and off["running"] is False and "tidak berjalan" in off["error"]


def _wait_job():
    for _ in range(100):
        s = c.get("/core/ai/status").json()["job"]
        if not s.get("running"):
            return s
        time.sleep(0.05)
    raise AssertionError("AI tidak selesai")


def test_ai_respects_manual_edits_and_verification(folder, ollama):
    c.post("/core/open", json={"folder": str(folder)})
    rows = c.post("/core/rows", json={"folder": str(folder)}).json()["rows"]
    a, b, v = rows[0]["id"], rows[1]["id"], rows[2]["id"]
    # geologist mengedit warna di foto a dan memverifikasi foto v sebelum AI dijalankan
    j = c.post("/core/update", json={"folder": str(folder), "id": a, "values": {"color": "Merah kecoklatan"}, "by": "Habil"}).json()
    assert j["row"]["color"] == "Merah kecoklatan" and j["row"]["edited"] == ["color"]
    c.post("/core/verify", json={"folder": str(folder), "ids": [v], "by": "Habil"})
    FakeOllama.calls.clear()
    j = c.post("/core/ai/start", json={"folder": str(folder), "model": "qwen3-vl:8b", "host": ollama, "scope": "pending", "max_px": 800}).json()
    assert j["ok"] and j["job"]["total"] == 3  # yang sudah diverifikasi tidak ikut
    s = _wait_job()
    assert s["done"] == 3 and s["failed"] == 0 and s["message"] == "Selesai"
    # gambar diperkecil sebelum dikirim
    import base64
    from io import BytesIO
    im = Image.open(BytesIO(base64.b64decode(FakeOllama.calls[0]["messages"][0]["images"][0])))
    assert max(im.size) == 800
    rows = {r["id"]: r for r in c.post("/core/rows", json={"folder": str(folder)}).json()["rows"]}
    assert rows[a]["color"] == "Merah kecoklatan"            # editan manual dipertahankan
    assert rows[a]["lithology"] == "Andesit" and rows[a]["status"] == "done" and rows[a]["ai_conf"] == "sedang"
    assert (rows[a]["drill_start"], rows[a]["photo_date"]) == ("05-03-25", "12-03-25")
    assert rows[a]["rqd_pct"] == 100                           # dibatasi 0-100
    assert rows[v]["status"] == "pending" and rows[v]["lithology"] is None  # terverifikasi: tidak disentuh
    # Hole/Box/kedalaman dari nama file b (3.5-7.2) tidak ditimpa bacaan AI (36.3-40.1); bacaan AI tetap tersimpan
    assert (rows[b]["from_m"], rows[b]["to_m"], rows[b]["box_no"]) == (3.5, 7.2, "2")
    assert rows[a]["hole_id"] == "LTH-101"  # IMG_0001 tanpa info di nama file: diisi AI
    h = c.post("/core/history", json={"folder": str(folder), "id": a, "values": {}}).json()
    assert h["ai"]["lithology"] == "Andesit" and any(x["src"] == "manual" and x["field"] == "color" for x in h["history"])
    # jalankan lagi 'pending': tidak ada yang tersisa
    r = c.post("/core/ai/start", json={"folder": str(folder), "model": "qwen3-vl:8b", "host": ollama})
    assert r.status_code == 500 and "Tidak ada foto" in r.json()["error"]


def test_ai_null_does_not_erase_filename_values(folder):
    c.post("/core/open", json={"folder": str(folder)})
    p = core_io.get_project(str(folder))
    row = [r for r in core_io.rows(p) if r["name"].startswith("LTH-101_Box2")][0]
    core_io.apply_ai(p, row["id"], {"hole_id": None, "from_m": None, "lithology": "Diorit", "confidence": "rendah"}, "m", 1.0)
    r = [x for x in core_io.rows(p) if x["id"] == row["id"]][0]
    assert r["hole_id"] == "LTH-101" and r["from_m"] == 3.5 and r["lithology"] == "Diorit"


def test_ollama_down_marks_error(folder):
    c.post("/core/open", json={"folder": str(folder)})
    j = c.post("/core/ai/start", json={"folder": str(folder), "model": "qwen3-vl:8b", "host": "http://127.0.0.1:9"}).json()
    s = _wait_job()
    assert s["failed"] >= 1 and s["done"] == 0
    assert "Ollama" in s["message"]
    rows = c.post("/core/rows", json={"folder": str(folder)}).json()["rows"]
    assert any(r["status"] == "error" and r["error"] for r in rows)


def test_export_xlsx_and_import_old_json(folder):
    c.post("/core/open", json={"folder": str(folder)})
    old = {"projectName": "Geotech_Dashboard_LTH-101", "data": [
        {"fileName": "LTH-101_Box11_36.30-40.10.jpg", "status": "done", "holeId": "LTH-101", "boxNo": "11", "fromM": 36.3, "toM": 40.1,
         "color": "Abu-abu", "weathering": "W1 (Fresh)", "rqdPct": 92, "gsi": "70-80", "rmr": 76, "notes": "-"},
        {"fileName": "tidak_ada.jpg", "status": "done"}]}
    j = c.post("/core/import/json", json={"folder": str(folder), "payload": old, "by": "Habil"}).json()
    assert j["matched"] == 1 and j["unmatched"] == 1
    r = c.post("/core/export/xlsx", json={"folder": str(folder)})
    assert r.status_code == 200 and r.content[:2] == b"PK"
    from io import BytesIO
    from openpyxl import load_workbook
    ws = load_workbook(BytesIO(r.content))["Core Log"]
    head = [x.value for x in ws[1]]
    assert head[:5] == ["No", "File Foto", "Subfolder", "Hole ID", "Box No"]
    vals = {ws.cell(row=i, column=2).value: [x.value for x in ws[i]] for i in range(2, ws.max_row + 1)}
    line = vals["LTH-101_Box11_36.30-40.10.jpg"]
    assert line[2] == "LTH-101" and line[head.index("RQD (%)")] == 92 and line[head.index("Interval (m)")] == 3.8
    assert ws.cell(row=2, column=2).hyperlink is not None


def test_readonly_folder_uses_local_db(folder, monkeypatch):
    monkeypatch.setattr(core_io, "_writable", lambda d: False)
    j = c.post("/core/open", json={"folder": str(folder)}).json()
    assert j["db_local"] is True and "core_projects" in j["db"]


def test_missing_folder_is_readable_error():
    r = c.post("/core/open", json={"folder": "C:/tidak/ada/folder"})
    assert r.status_code == 500 and "tidak ditemukan" in r.json()["error"]


def test_project_folder_deleted_while_open_is_recreated(folder):
    import shutil
    c.post("/core/open", json={"folder": str(folder)})
    shutil.rmtree(folder / "_GCEx_Core")
    j = c.post("/core/open", json={"folder": str(folder)}).json()
    assert j["ok"] and j["scan"]["total"] == 4 and (folder / "_GCEx_Core" / "gcex_core.db").exists()
