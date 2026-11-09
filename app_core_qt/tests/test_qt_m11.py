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
    qtbot.waitUntil(lambda: said or (tr.pv is not None and tr.grid.rowCount() == 3), timeout=8000)
    assert not said, said
    assert tr.txt.toPlainText().startswith("Tanggal: 05-11-26") and "Here is" not in tr.txt.toPlainText()
    assert tr.hdr.rowCount() == 2 and tr.hdr.cellWidget(0, 2).currentData() == "tanggal" and tr.hdr.cellWidget(1, 2).currentData() == "shift"
    assert 0 in tr.skip  # baris judul kolom dilewati
    assert tr.maprow.cellWidget(0, 0).currentData() == "no" and tr.maprow.cellWidget(0, 3).currentData() == "kelas"
    assert tr.maprow.cellWidget(0, 4).currentData() == "ton" and tr.maprow.cellWidget(0, 5).currentData() == "tujuan"
    # 'Jam' -> start (dipilih pengguna), 'Truck' -> unit
    cb = tr.maprow.cellWidget(0, 1)
    cb.setCurrentIndex(cb.findData("start"))
    cb = tr.maprow.cellWidget(0, 2)
    cb.setCurrentIndex(cb.findData("unit"))
    assert "6/6 kolom" in tr.info.text() and tr.bApply2.isEnabled()
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
    qtbot.waitUntil(lambda: tr.pv is not None and tr.grid.rowCount() == 1, timeout=8000)
    assert tr.maprow.cellWidget(0, 1).currentData() == "start" and tr.maprow.cellWidget(0, 2).currentData() == "unit"


def test_transkrip_scan_kolom_ke_kanan(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    from corex.api import core_io
    outs = iter(["No | Jam\n1 | 0905\n2 | 0916", "Truck\nT01\nT02", "Kelas\nOX-LG\nSF-LG"])
    monkeypatch.setattr(core_io, "_http", lambda url, body=None, timeout=5.0: {"message": {"content": next(outs)}})
    w.ai.info = {"running": True}
    monkeypatch.setattr(w.ai, "model", lambda: "qwen3-vl:2b-instruct")
    monkeypatch.setattr("corex.forms_transkrip.ask", lambda *a, **k: (_ for _ in ()).throw(AssertionError("tidak boleh bertanya")))
    tr = pg.tr
    tr.cbMode.setCurrentIndex(tr.cbMode.findData("kanan"))
    for n in (2, 3, 4):
        tr.run_ai()
        qtbot.waitUntil(lambda: tr.pv is not None and tr.pv.get("ncol") == n and tr.bAI.isEnabled(), timeout=8000)
    assert tr.txt.toPlainText().split("\n") == ["No | Jam | Truck | Kelas", "1 | 0905 | T01 | OX-LG", "2 | 0916 | T02 | SF-LG"]
    assert tr.maprow.cellWidget(0, 3).currentData() == "kelas" and tr.bApply.isVisible() is not None


def test_baca_ai_cara_transkrip_keputusan_pengguna(qtbot, prj, tmp_path, monkeypatch):
    """0.46: ✦ Baca dengan AI = salin teks; tanpa pemetaan yakin -> 'Perlu pemetaan kolom' + tab Transkrip; pengguna menyunting kisi
    (geser sel, gabung baris, pecah kolom jam, kolom -> kop), Terapkan; borang berikutnya disusun otomatis dengan keputusan itu."""
    from corex.util import SET
    SET.set("fmCara", "transkrip")
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    from corex.api import core_io
    raw = ("0905 OX-LG | T01 | 30 | ROM 1 | 05-11-26\n"
           "0916 SF-LG | 31 | ROM 1 | 05-11-26\n"   # sel Truck terlewat -> perlu digeser
           "- | - | - | dekat ramp | -\n")            # lanjutan catatan / tujuan
    outs = iter([raw, "0930 OX-HG | T09 | 28 | ROM 2 | 06-11-26"])
    monkeypatch.setattr(core_io, "_http", lambda url, body=None, timeout=5.0: {"message": {"content": next(outs)}, "eval_count": 20})
    w.ai.info = {"running": True}
    monkeypatch.setattr(w.ai, "model", lambda: "qwen3-vl:2b-instruct")
    monkeypatch.setattr("corex.forms_transkrip.say", lambda *a, **k: None)
    pg.run_ai()
    qtbot.waitUntil(lambda: pg.ai_did is None and pg.tabs.currentWidget() is pg.tr and pg.tr.pv is not None, timeout=8000)
    tr = pg.tr
    d = next(x for x in pg.docs if x["id"] == pg.cur["doc"]["id"])
    assert pg._info(d)["st"] == "map" and pg.cur["rows"] == [] and "menunggu keputusan" in tr.info.text()
    assert tr.grid.rowCount() == 3 and tr.grid.columnCount() == 5
    # pecah kolom 1 "0905 OX-LG" -> jam | kelas  (lewat aksi kolom)
    hdr, rows = tr._model()
    ch = ["", "unit", "ton", "tujuan", "kop:tanggal"]
    from PySide6.QtWidgets import QMenu
    m = QMenu()
    tr._col_actions(m, 0, hdr, rows, ch)
    tr.choice = ch
    next(a for a in m.actions() if a.text().startswith("✂ Pecah kolom di spasi")).trigger()  # aksi menu kolom yang sebenarnya
    qtbot.waitUntil(lambda: tr.grid.columnCount() == 6, timeout=8000)
    cb = tr.maprow.cellWidget(0, 0)
    cb.setCurrentIndex(cb.findData("start"))
    cb = tr.maprow.cellWidget(0, 1)
    cb.setCurrentIndex(cb.findData("kelas"))
    qtbot.waitUntil(lambda: tr.grid.columnCount() == 6, timeout=8000)
    assert tr._cols() == ["start", "kelas", "unit", "ton", "tujuan", "kop:tanggal"]
    # baris 2: sisipkan sel kosong di kolom Truck (geser kanan)
    hdr, rows = tr._model()
    rows[1].insert(2, "")
    rows[1] = rows[1][:6]
    tr._commit(hdr, rows)
    qtbot.waitUntil(lambda: tr.grid.item(1, 3) is not None and tr.grid.item(1, 3).text() == "31", timeout=8000)
    # baris 3 = lanjutan tujuan baris 2 -> gabung ke atas
    hdr, rows = tr._model()
    for j, v in enumerate(rows[2]):
        if v.strip() and v != "-":
            rows[1][j] = (rows[1][j] + " " + v).strip()
    rows.pop(2)
    tr._commit(hdr, rows)
    qtbot.waitUntil(lambda: tr.grid.rowCount() == 2, timeout=8000)
    assert tr._cols()[5] == "kop:tanggal"  # pilihan pengguna bertahan selama teks disunting
    tr.apply()
    qtbot.waitUntil(lambda: len(pg.cur["rows"]) == 2, timeout=8000)
    rs = [r["data"] for r in pg.cur["rows"]]
    assert rs[1]["tujuan"] == "ROM 1 dekat ramp" and rs[1]["unit"] == "" and rs[0]["kelas"] == "OX-LG"
    assert pg.cur["doc"]["header"]["tanggal"]
    # borang kedua jenis sama: Baca dengan AI -> langsung tersusun dengan keputusan tadi? (teks tanpa judul, 5 kolom != 6) -> menunggu
    from test_qt_m5 import _scan
    import shutil
    src = tmp_path / "b_borang_kedua.jpg"
    shutil.copy(_scan(tmp_path), src)
    monkeypatch.setattr("corex.forms.QFileDialog.getOpenFileNames", lambda *a, **k: ([str(src)], ""))
    pg.add_files()
    qtbot.waitUntil(lambda: pg.cur is not None and pg.cur["doc"]["name"].startswith("b"), timeout=8000)
    pg.run_ai()
    qtbot.waitUntil(lambda: pg.ai_did is None and pg.tr.pv is not None and pg.tr.did == pg.cur["doc"]["id"], timeout=8000)
    assert pg.cur["rows"] == [] and pg.tabs.currentWidget() is pg.tr  # 5 kolom: belum pernah diputuskan -> tidak menebak


def test_gabung_baris_tanpa_jam(qtbot, prj, tmp_path, monkeypatch):
    w, pg = _open_forms(qtbot, prj, tmp_path, monkeypatch)
    tr = pg.tr
    tr.txt.setPlainText("0835-0900 | Start drilling + cleaning\n- | cyclone and splitter\n0900-0905 | Move")
    qtbot.waitUntil(lambda: tr.pv is not None and tr.grid.rowCount() == 3, timeout=8000)
    from PySide6.QtWidgets import QMenu
    hdr, rows = tr._model()
    m = QMenu()
    tr._col_actions(m, 0, hdr, rows, tr._cols())
    a = next(a for a in m.actions() if a.text().startswith("⤒ Gabungkan 1 baris"))
    a.trigger()
    qtbot.waitUntil(lambda: tr.grid.rowCount() == 2, timeout=8000)
    assert tr.grid.item(0, 1).text() == "Start drilling + cleaning cyclone and splitter"
