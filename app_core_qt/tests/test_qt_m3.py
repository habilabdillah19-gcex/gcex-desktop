"""Uji Core-Ex Qt: perilaku jendela yang dulu diurus Electron (satu jendela, ukuran tampilan, layar penuh, buka ulang),
pintasan tanpa bentrok, daftar pilihan di sel tabel."""
import os
import sys
import uuid
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_qt_m1 import _win, prj  # noqa: E402,F401  (fixture proyek & jendela uji)


def test_single_instance_forwards_folder(qtbot):
    from corex.shell import SingleInstance
    a = SingleInstance("CoreEx-uji-" + uuid.uuid4().hex[:8])
    assert a.listen()
    got = []
    a.message.connect(got.append)
    # pesan yang datang sebelum jendela utama siap (mis. dialog lisensi masih terbuka) disimpan dulu
    assert SingleInstance.send(a.name, {"cmd": "show", "folder": "D:/Foto/LTH-1"})
    qtbot.waitUntil(lambda: bool(a.queue), timeout=3000)
    assert not got
    a.ready()
    assert got == [{"cmd": "show", "folder": "D:/Foto/LTH-1"}]
    assert SingleInstance.send(a.name, {"cmd": "show", "folder": ""})
    qtbot.waitUntil(lambda: len(got) == 2, timeout=3000)
    a.close()
    assert not SingleInstance.send(a.name, {"cmd": "show"}, 300)  # tidak ada Core-Ex lain -> jalan sebagai jendela pertama
    b = SingleInstance(a.name)
    assert b.listen()  # nama bisa dipakai lagi setelah dilepas
    b.close()


def test_from_instance_opens_folder(qtbot, prj):
    w = _win(qtbot)
    w.showMinimized()
    w.from_instance({"cmd": "show", "folder": prj})
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    assert not w.isMinimized() and Path(w.folder) == Path(prj).resolve()
    w.from_instance({"cmd": "show", "folder": str(Path(prj) / "tidak-ada")})  # folder tidak ada -> diabaikan
    assert Path(w.folder) == Path(prj).resolve()


def test_zoom_setting_and_restart(qtbot, prj, monkeypatch):
    from corex import shell, util
    w = _win(qtbot)
    asked = []
    monkeypatch.setattr("corex.mainwin.ask", lambda p, t, *a: asked.append(t) or False)
    w.set_zoom(1.25)
    assert util.SET.get("qt_zoom") == 1.25 and "125%" in asked[0] and not w.restart_after
    assert [a.text() for a in w.zoomGrp.actions() if a.isChecked()] == ["125%"]
    assert shell.zoom_step(+1) == 1.5 and shell.zoom_step(-1) == 1.1 and shell.zoom_now() == 1.25
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    shell.apply_zoom_env()
    assert os.environ.pop("QT_SCALE_FACTOR") == "1.25"
    util.SET.set("qt_zoom", "rusak")
    assert shell.zoom_now() == shell.ZOOM_DEF
    # buka ulang: jendela ditutup, Core-Ex baru dijalankan dengan folder yang sama
    started = []
    monkeypatch.setattr("corex.shell.QProcess.startDetached", lambda prog, args: started.append((prog, args)) or True)
    monkeypatch.setattr("corex.mainwin.ask", lambda *a: True)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: bool(w.folder), timeout=8000)
    w.set_zoom(0.9)
    assert w.restart_after and not w.isVisible()
    assert shell.restart(w.folder)
    assert started and started[0][1][-2:] == ["--folder", w.folder] and started[0][1][0].endswith("main.py")


def test_fullscreen_toggle(qtbot):
    w = _win(qtbot)
    w.showMaximized()
    w.toggle_full()
    qtbot.waitUntil(lambda: w.isFullScreen(), timeout=3000)
    assert w.aFull.isChecked()
    w.toggle_full()
    qtbot.waitUntil(lambda: not w.isFullScreen(), timeout=3000)
    assert not w.aFull.isChecked()


def test_shortcuts_not_ambiguous(qtbot):
    """Dua pintasan dengan tombol sama di jendela yang sama membuat Qt tidak menjalankan keduanya."""
    from PySide6.QtGui import QAction, QShortcut
    w = _win(qtbot)
    seen: dict[str, str] = {}
    for a in w.findChildren(QAction):
        for k in a.shortcuts():
            s = k.toString()
            assert s not in seen, f"pintasan {s} dipakai dua kali: {seen[s]} & {a.text()}"
            seen[s] = a.text()
    for sc in w.findChildren(QShortcut):
        s = sc.key().toString()
        assert s not in seen, f"pintasan {s} dipakai dua kali: {seen[s]} & QShortcut"
        seen[s] = "QShortcut"
    for k in ("Ctrl+O", "F5", "Ctrl+S", "F11", "Ctrl+=", "Ctrl+-", "Ctrl+0", "Ctrl+K"):
        assert k in seen, k


def test_table_cell_completer(qtbot, prj):
    from PySide6.QtWidgets import QLineEdit, QStyleOptionViewItem
    w = _win(qtbot)
    w.open_folder(prj)
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=8000)
    cols = [c[0] for c in w.model.cols()]
    dg = w.table.itemDelegate()
    for k, first in (("weathering", "W1 (Fresh)"), ("oxidation", "Unoxidized")):
        ed = dg.createEditor(w.table.viewport(), QStyleOptionViewItem(), w.model.index(0, cols.index(k)))
        assert isinstance(ed, QLineEdit) and ed.completer() is not None
        assert ed.completer().model().index(0, 0).data() == first
    ed = dg.createEditor(w.table.viewport(), QStyleOptionViewItem(), w.model.index(0, cols.index("lithology")))
    assert ed.completer() is None
