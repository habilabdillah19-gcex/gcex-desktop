"""Uji DB-Ex Qt: perilaku jendela yang dulu diurus Electron (satu jendela, ukuran tampilan, layar penuh, buka ulang),
pintasan tanpa bentrok, daftar pilihan di sel tabel."""
import os
import sys
import uuid
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_qt_m1 import _win, prj  # noqa: E402,F401  (fixture proyek & jendela uji)


def _send_bg(name: str, payload: dict, timeout_ms: int = 3000) -> list:
    """Kirim dari PROSES lain, persis seperti DB-Ex kedua (thread lain dalam satu proses tidak andal untuk named
    pipe Windows). Hasil: [] selama proses berjalan, lalu [True] / [False]."""
    import json
    import subprocess
    code = ("import sys, json; sys.path.insert(0, sys.argv[1]);"
            "from PySide6.QtCore import QCoreApplication; app = QCoreApplication([]);"
            "from corex.shell import SingleInstance;"
            "sys.exit(0 if SingleInstance.send(sys.argv[2], json.loads(sys.argv[3]), int(sys.argv[4])) else 3)")
    p = subprocess.Popen([sys.executable, "-c", code, str(Path(__file__).resolve().parents[1]), name, json.dumps(payload), str(timeout_ms)],
                         env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))

    class Res(list):
        def __eq__(self, other):  # noqa: D105
            rc = p.poll()
            self[:] = [] if rc is None else [rc == 0]
            return list.__eq__(self, other)

        __hash__ = None

    return Res()


def test_single_instance_forwards_folder(qtbot):
    from corex.shell import SingleInstance
    a = SingleInstance("CoreEx-uji-" + uuid.uuid4().hex[:8])
    assert a.listen()
    got = []
    a.message.connect(got.append)
    # pesan yang datang sebelum jendela utama siap (mis. dialog lisensi masih terbuka) disimpan dulu
    r1 = _send_bg(a.name, {"cmd": "show", "folder": "D:/Foto/LTH-1"})
    qtbot.waitUntil(lambda: bool(a.queue) and r1 == [True], timeout=8000)
    assert not got
    a.ready()
    assert got == [{"cmd": "show", "folder": "D:/Foto/LTH-1"}]
    r2 = _send_bg(a.name, {"cmd": "show", "folder": ""})
    qtbot.waitUntil(lambda: len(got) == 2 and r2 == [True], timeout=8000)
    a.close()
    r3 = _send_bg(a.name, {"cmd": "show"}, 300)  # tidak ada DB-Ex lain -> jalan sebagai jendela pertama
    qtbot.waitUntil(lambda: r3 == [False], timeout=5000)
    b = SingleInstance(a.name)
    assert b.listen()  # nama bisa dipakai lagi setelah dilepas
    b.close()


def test_from_instance_opens_folder(qtbot, prj):
    w = _win(qtbot)
    w.showMinimized()
    w.from_instance({"cmd": "show", "folder": prj})
    qtbot.waitUntil(lambda: len(w.view) == 3, timeout=25000)
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
    # buka ulang: jendela ditutup, DB-Ex baru dijalankan dengan folder yang sama
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


def test_closed_window_pending_callbacks(qtbot, prj):
    """Tata letak panel / cek Ollama yang tertunda tidak boleh menyentuh jendela yang sudah ditutup (penyebab galat CI Windows)."""
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    from corex.mainwin import MainWindow
    w = MainWindow("uji")  # tidak didaftarkan ke qtbot: jendela ini sengaja dihapus di tengah uji
    w.show()
    w.open_folder(prj)
    qtbot.waitUntil(lambda: w.cur_id is not None, timeout=8000)
    w.interp.update()  # menjadwalkan relayout
    w.ai.check(True)  # hasil datang belakangan
    w.close()
    w.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    for _ in range(30):
        QApplication.processEvents()
        qtbot.wait(20)


def test_user_dir_migrates_from_core_ex(tmp_path, monkeypatch):
    """0.31.0: Core-Ex berganti nama menjadi DB-Ex; folder data lama (%APPDATA%\\Core-Ex) dipindah sekali, isinya utuh."""
    from corex import util
    monkeypatch.delenv("COREX_USERDATA", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    old = tmp_path / "Core-Ex"
    old.mkdir()
    (old / "settings.json").write_text('{"user": "Rina"}')
    d = util.user_dir()
    assert d == tmp_path / "DB-Ex" and (d / "settings.json").read_text() == '{"user": "Rina"}' and not old.exists()
    old.mkdir()  # folder baru sudah ada: folder lama tidak menimpa
    assert util.user_dir() == d and old.exists()
