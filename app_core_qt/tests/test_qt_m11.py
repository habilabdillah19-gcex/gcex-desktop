"""Uji tab Transkrip (0.45): AI menyalin teks (Ollama tiruan), pratinjau kisi + usulan pemetaan, ubah tujuan kolom, Terapkan -> tabel Data.
Data fiktif."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_qt_m1 import _win, prj  # noqa: E402,F401
from test_qt_m5 import _open_forms  # noqa: E402

TEKS = ("Here is the text:\nTanggal: 05-11-26\nShift: I\n"
        "No | Jam | Truck | Kelas | Ton | Tujuan\n1 | 0905 | T01 | OX-LG | 30 | ROM 1\n2 | 0916 | T02 | SF-LG? | 31 | ROM 1\n")


def test_transkrip_salin_petakan_terapkan(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    from corex.api import core_io

    def fake(url, body=None, timeout=5.0):
        assert "format" not in body and "SALIN" in body["messages"][0]["content"]
        return {"message": {"content": TEKS}, "eval_count": 40}
    monkeypatch.setattr(core_io, "_http", fake)
    w.ai.info = {"running": True}
    monkeypatch.setattr(w.ai, "model", lambda: "qwen3-vl:2b-instruct")
    said = []
    monkeypatch.setattr("corex.forms_transkrip.say", lambda *a, **k: said.append(a[1]))
    tr = pg.tr
    assert pg.tabs.tabText(4).endswith("Transkrip") and tr.did == pg.cur["doc"]["id"]
    tr.run_ai()
    qtbot.waitUntil(lambda: said or (tr.pv is not None and tr.grid.rowCount() == 4), timeout=8000)
    assert not said, said
    assert tr.txt.toPlainText().startswith("Tanggal: 05-11-26") and "Here is" not in tr.txt.toPlainText()
    assert tr.hdr.rowCount() == 2 and tr.hdr.cellWidget(0, 2).currentData() == "tanggal" and tr.hdr.cellWidget(1, 2).currentData() == "shift"
    assert 0 in tr.skip  # baris judul kolom dilewati
    assert tr.grid.cellWidget(0, 0).currentData() == "no" and tr.grid.cellWidget(0, 3).currentData() == "kelas"
    assert tr.grid.cellWidget(0, 4).currentData() == "ton" and tr.grid.cellWidget(0, 5).currentData() == "tujuan"
    # 'Jam' -> start (dipilih pengguna), 'Truck' -> unit
    cb = tr.grid.cellWidget(0, 1)
    cb.setCurrentIndex(cb.findData("start"))
    cb = tr.grid.cellWidget(0, 2)
    cb.setCurrentIndex(cb.findData("unit"))
    assert "6/6 kolom" in tr.info.text()
    assert pg.cur["rows"] == []  # menyalin belum mengubah tabel Data
    tr.apply()
    qtbot.waitUntil(lambda: pg.t.rowCount() == 2, timeout=8000)
    assert pg.tabs.currentIndex() == 0 and pg.hdrEd["tanggal"].text()
    cols = [k for k, _l in pg.cols(pg.types["ore"])]
    assert pg.t.item(0, 1 + cols.index("unit")).text() == "T01" and pg.t.item(1, 1 + cols.index("kelas")).text() == "SF-LG"
    assert "kelas" in pg.cur["rows"][1]["unc"] and pg.cur["doc"]["teks"].startswith("Tanggal")
    # buka ulang borang: teks tersimpan ikut tampil; pemetaan tersimpan dipakai untuk teks tanpa baris judul
    tr.set_doc(None)
    tr.set_doc(pg.cur["doc"])
    assert tr.txt.toPlainText().startswith("Tanggal: 05-11-26")
    tr.txt.setPlainText("3 | 1002 | T03 | OX-HG | 29 | ROM 2")
    qtbot.waitUntil(lambda: tr.pv is not None and tr.grid.rowCount() == 2, timeout=8000)
    assert tr.grid.cellWidget(0, 1).currentData() == "start" and tr.grid.cellWidget(0, 2).currentData() == "unit"
