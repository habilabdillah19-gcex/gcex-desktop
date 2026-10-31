"""Core-Ex (Qt for Python). Pemakaian: python main.py [--folder D:\\Foto_Core] [--version 1.0.0]"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def app_version() -> str:
    for c in (Path(getattr(sys, "_MEIPASS", "")) / "version.txt", HERE / "version.txt"):
        if c.exists():
            return c.read_text(encoding="utf-8").strip()
    try:
        b = json.loads((HERE.parent / "builder-core.json").read_text(encoding="utf-8"))
        return b.get("extraMetadata", {}).get("version") or "dev"
    except Exception:  # noqa: BLE001
        return "dev"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder")
    a, _ = ap.parse_known_args(argv)
    from corex.util import SET, log, user_dir
    os.environ.setdefault("GCEX_CACHE", str(user_dir() / "cache"))
    os.environ.setdefault("GCEX_LOG_DIR", str(user_dir() / "logs"))
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox
    if QApplication.instance() is None:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Core-Ex")
    app.setOrganizationName("GC-Ex")
    for ic in (Path(getattr(sys, "_MEIPASS", "")) / "core.ico", HERE.parent / "build" / "core.ico"):
        if ic.exists():
            app.setWindowIcon(QIcon(str(ic)))
            break
    from corex import dialogs, lic, theme
    theme.load_fonts()
    theme.apply(app, bool(SET.get("dark", False)))
    ver = app_version()
    log("[mulai] Core-Ex Qt", ver)
    if not dialogs.ensure_terms():
        return 0
    lic_on = getattr(sys, "frozen", False) or os.environ.get("GCEX_LIC") == "1"
    store = lic.Store() if lic_on else None
    if store:
        c = store.check("core")
        if not c["ok"]:
            log("[lisensi] belum aktif:", c["reason"])
            if dialogs.LicenseDlg(None, store, "activate").exec() != dialogs.LicenseDlg.Accepted or not store.check("core")["ok"]:
                log("[lisensi] aplikasi ditutup tanpa lisensi")
                return 0
        elif c.get("days_left") is not None and c["days_left"] <= 14:
            QTimer.singleShot(4000, lambda: QMessageBox.warning(None, "Lisensi GC-Ex", f"Lisensi GC-Ex berakhir dalam {c['days_left']} hari ({c['info']['e']}).\n\n"
                                                                "Minta kunci perpanjangan ke penerbit GC-Ex, lalu masukkan lewat Bantuan > Lisensi GC-Ex."))
    from corex.mainwin import MainWindow
    w = MainWindow(ver, store)
    w.show()
    if a.folder:
        QTimer.singleShot(100, lambda: w.open_folder(a.folder))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
