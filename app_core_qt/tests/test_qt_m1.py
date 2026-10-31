"""Uji DB-Ex Qt (offscreen): lisensi (Ed25519 & ID komputer sama dengan license.js), jembatan API, jendela utama
(buka folder, edit sel, verifikasi, filter, cari, export, AI dengan Ollama palsu)."""
import base64
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corex import lic  # noqa: E402


# ---------------------------------------------------------------- lisensi
def _keypair():
    crypto = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.ed25519")
    from cryptography.hazmat.primitives import serialization as S
    k = crypto.Ed25519PrivateKey.generate()
    return k, k.public_key().public_bytes(S.Encoding.Raw, S.PublicFormat.Raw)


def _key(k, data: dict) -> str:
    p = base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    s = base64.urlsafe_b64encode(k.sign(("GCEX1." + p).encode())).rstrip(b"=").decode()
    return f"GCEX1.{p}.{s}"


def test_ed25519_and_machine_id(monkeypatch):
    k, pub = _keypair()
    assert lic.ed25519_verify(pub, b"abc", k.sign(b"abc"))
    assert not lic.ed25519_verify(pub, b"abd", k.sign(b"abc"))
    monkeypatch.setattr(lic, "_raw_machine", lambda: "guid:1234abcd-0000-1111-2222-333344445555")
    monkeypatch.setattr(lic, "_MID", None)
    assert lic.machine_id() == "Y6QY-8EN6-K3YF-W9CP"  # nilai dari electron/license.js untuk GUID yang sama


def test_license_store(tmp_path, monkeypatch):
    k, pub = _keypair()
    monkeypatch.setattr(lic, "_pub_raw", lambda: pub)
    monkeypatch.setattr(lic, "_MID", "AAAA-BBBB-CCCC-DDDD")
    st = lic.Store(str(tmp_path))
    assert st.check("core")["none"]
    bad = _key(k, {"id": "L1", "n": "Uji", "m": "ZZZZ-BBBB-CCCC-DDDD", "a": ["core"]})
    assert "komputer lain" in st.activate(bad)["reason"]
    dh_only = _key(k, {"id": "L2", "n": "Uji", "m": "AAAA-BBBB-CCCC-DDDD", "a": ["dh"]})
    assert "tidak berlaku untuk DB-Ex" in st.activate(dh_only)["reason"]
    old = _key(k, {"id": "L3", "n": "Uji", "m": "AAAA-BBBB-CCCC-DDDD", "a": ["*"], "e": "2020-01-01"})
    assert st.activate(old).get("expired")
    good = _key(k, {"id": "L4", "n": "Uji", "o": "PT Fiktif", "m": "AAAA-BBBB-CCCC-DDDD", "a": ["core", "dh"], "e": "2099-12-31"})
    r = st.activate(good)
    assert r["ok"] and r["days_left"] > 1000
    assert st.check("core")["ok"] and json.loads((tmp_path / "GC-Ex Lisensi" / "lisensi.json").read_text())["key"] == good
    assert not lic.parse_key(good[:-3] + "AAA")["ok"]  # tanda tangan rusak
    st.remove()
    assert st.check("core").get("none")


# ---------------------------------------------------------------- Ollama palsu
class _Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, o):
        b = json.dumps(o).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/version":
            return self._send({"version": "0.12.9"})
        return self._send({"models": [{"name": "qwen3-vl:8b", "size": 6100000000, "details": {"parameter_size": "8.8B"}}]})

    def do_POST(self):  # noqa: N802
        self.rfile.read(int(self.headers["Content-Length"]))
        if self.path == "/api/show":
            return self._send({"capabilities": ["completion", "vision"]})
        ans = {"lithology": "Andesit", "weathering": "W2 (Slightly Weathered)", "recovery_pct": 96, "rqd_pct": 70, "gsi": "55-65", "rmr": 60,
               "notes": "uji", "confidence": "sedang", "segments": [{"row": 1, "start": 0, "end": 1, "lithology": "AND", "rqd_pct": 70}]}
        return self._send({"message": {"content": json.dumps(ans)}, "done": True})


@pytest.fixture()
def fake_ollama():
    s = ThreadingHTTPServer(("127.0.0.1", 0), _Fake)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()


@pytest.fixture()
def prj(tmp_path, monkeypatch):
    monkeypatch.setenv("COREX_USERDATA", str(tmp_path / "ud"))
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "Foto" / "LTH-101"
    d.mkdir(parents=True)
    for i, (a, b) in enumerate(((0, 3.5), (3.5, 7.0), (7.0, 10.5)), 1):
        Image.new("RGB", (600, 400), (90 + i * 20, 80, 70)).save(d / f"LTH-101_Box{i}_{a:.2f}-{b:.2f}.jpg")
    from corex import util
    util.SET.__init__()
    util.SET.set("user", "Rina")
    util.SET.set("autoOllama", False)
    from corex.api import core_io
    core_io._PROJECTS.clear()
    return str(tmp_path / "Foto")


def _win(qtbot):
    from corex import theme
    from corex.mainwin import MainWindow
    from PySide6.QtWidgets import QApplication
    theme.load_fonts()
    theme.apply(QApplication.instance())
    w = MainWindow("uji")
    qtbot.addWidget(w)
    w.show()
    return w


def test_open_edit_verify_filter_export(qtbot, prj, tmp_path, monkeypatch):
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3 and w.cur_id is not None, timeout=8000)
    assert w.card.title.text().startswith("LTH-101_Box1") and w.card.f["hole_id"].tag.text() == "nama file"
    # edit dari tabel (kolom Litologi)
    col = next(i for i, c in enumerate(w.model.cols()) if c[0] == "lithology")
    assert w.model.setData(w.model.index(0, col), "Andesit")
    r = w.by_id[w.view[0]["id"]]
    assert r["lithology"] == "Andesit" and "lithology" in r["edited"]
    assert w.card.f["lithology"].ed.text() == "Andesit" and w.card.f["lithology"].tag.text() == "diedit"
    # edit dari kartu: angka tidak valid ditolak
    monkeypatch.setattr("corex.mainwin.say", lambda *a, **k: None)
    w.save_field(r["id"], "rqd_pct", "abc")
    assert r["rqd_pct"] is None
    w.card.f["rqd_pct"].ed.setText("75")
    w.card.f["rqd_pct"].ed.editingFinished.emit()
    assert r["rqd_pct"] == 75
    # verifikasi & lanjut
    w.verify_current()
    qtbot.waitUntil(lambda: w.by_id[r["id"]]["verified"] == 1 and w.cur_id == w.view[1]["id"], timeout=4000)
    assert "diverifikasi 1" in w.sSum.text()
    # filter status & kedalaman
    w.fStat.setCurrentIndex(w.fStat.findData("ver"))
    assert len(w.view) == 1
    w.reset_filter()
    w.fFrom.setText("8")
    qtbot.waitUntil(lambda: len(w.view) == 1, timeout=3000)
    w.reset_filter()
    # urut: klik header To dua kali -> menurun
    to = next(i for i, c in enumerate(w.model.cols()) if c[0] == "to_m")
    w.table._hdr(to)
    w.table._hdr(to)
    assert [x["to_m"] for x in w.view] == [10.5, 7.0, 3.5]
    # cari cepat
    got = []
    w.q.picked.connect(got.append)
    w.q.setText("Andesit")
    w.q.run(True)
    qtbot.waitUntil(lambda: bool(got), timeout=4000)
    w.goto_result(got[0])
    assert w.cur_id == r["id"]
    # export Excel
    out = tmp_path / "log.xlsx"
    monkeypatch.setattr("corex.mainwin.QFileDialog.getSaveFileName", lambda *a, **k: (str(out), ""))
    monkeypatch.setattr("corex.mainwin.show_in_folder", lambda p: None)
    w.export_xlsx()
    qtbot.waitUntil(lambda: out.exists() and out.stat().st_size > 1000, timeout=8000)


def test_ai_run_updates_card(qtbot, prj, fake_ollama, monkeypatch):
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: w.cur_id is not None, timeout=8000)
    w.ai.host.setText(fake_ollama)
    w.ai.check(True)
    qtbot.waitUntil(lambda: bool(w.ai.model()) and "qwen3-vl" in w.pill.text(), timeout=5000)
    w.run_ai("ids", [w.cur_id])
    qtbot.waitUntil(lambda: w.by_id[w.cur_id]["status"] == "done", timeout=20000)
    qtbot.waitUntil(lambda: w.card.f["rqd_pct"].ed.text() == "70", timeout=5000)
    assert w.card.f["rqd_pct"].tag.text() == "AI" and w.by_id[w.cur_id]["n_segs"] == 1
    # isian AI tidak ditimpa setelah diedit
    w.save_field(w.cur_id, "rqd_pct", "50")
    w.run_ai("ids", [w.cur_id])
    qtbot.waitUntil(lambda: not w.poll.isActive() and w.last_done == -1, timeout=20000)
    assert w.by_id[w.cur_id]["rqd_pct"] == 50


def test_license_dialog(qtbot, tmp_path, monkeypatch):
    k, pub = _keypair()
    monkeypatch.setattr(lic, "_pub_raw", lambda: pub)
    monkeypatch.setattr(lic, "_MID", "AAAA-BBBB-CCCC-DDDD")
    from corex.dialogs import LicenseDlg
    st = lic.Store(str(tmp_path))
    d = LicenseDlg(None, st)
    qtbot.addWidget(d)
    assert d.mid.text() == "AAAA-BBBB-CCCC-DDDD" and not d.stat.isVisible()
    d.key.setPlainText(_key(k, {"id": "L9", "n": "Rina", "m": "AAAA-BBBB-CCCC-DDDD", "a": ["core"]}))
    d.activate()
    assert st.check("core")["ok"] and "Lisensi aktif" in d.msg.text()
