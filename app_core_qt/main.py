"""DB-Ex (Qt for Python). Pemakaian: python main.py [--folder D:\\Foto_Core] [--version 1.0.0]"""
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
    ap.add_argument("--selftest", nargs=2, metavar=("FOLDER", "OUT_JSON"), help="uji tanpa jendela (CI): buka folder, baris, thumbnail, Excel")
    a, _ = ap.parse_known_args(argv)
    from corex.util import SET, log, user_dir
    os.environ.setdefault("GCEX_CACHE", str(user_dir() / "cache"))
    os.environ.setdefault("GCEX_LOG_DIR", str(user_dir() / "logs"))
    if a.selftest:
        return selftest(*a.selftest)
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox
    from corex import shell
    if QApplication.instance() is None:
        shell.apply_zoom_env()  # Tampilan > Ukuran tampilan (berlaku sejak DB-Ex dibuka)
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    # satu jendela DB-Ex saja: bila sudah terbuka, jendela itu yang tampil (folder diteruskan), proses ini selesai
    folder = str(Path(a.folder).resolve()) if a.folder else ""
    inst = shell.SingleInstance()
    if os.environ.get("COREX_MULTI") != "1":
        if shell.SingleInstance.send(inst.name, {"cmd": "show", "folder": folder}):
            log("[satu jendela] DB-Ex sudah terbuka; folder diteruskan:", folder or "-")
            return 0
        inst.listen()
    app.setApplicationName("DB-Ex")
    app.setOrganizationName("GC-Ex")
    for ic in (Path(getattr(sys, "_MEIPASS", "")) / "icon-core.ico", HERE.parent / "build" / "icon-core.ico"):
        if ic.exists():
            app.setWindowIcon(QIcon(str(ic)))
            break
    from corex import dialogs, lic, theme
    theme.load_fonts()
    theme.apply(app, bool(SET.get("dark", False)))
    ver = app_version()
    log("[mulai] DB-Ex Qt", ver)
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
    w.showMaximized()  # sama dengan versi Electron: jendela dibuka penuh
    inst.message.connect(w.from_instance)
    inst.ready()
    if folder:
        QTimer.singleShot(100, lambda: w.open_folder(folder))
    rc = app.exec()
    inst.close()
    if getattr(w, "restart_after", False):
        shell.restart(w.folder)
    return rc


def selftest(folder: str, out: str) -> int:
    res: dict = {"version": app_version()}
    try:
        from corex import api, lic, theme  # noqa: F401
        from PySide6.QtGui import QGuiApplication, QImage
        app = QGuiApplication.instance() or QGuiApplication(["DB-Ex"])  # noqa: F841
        theme.load_fonts()
        res["fonts"] = [theme.SANS, theme.MONO]
        j = api.call("/core/open", {"folder": folder, "by": "CI"})
        rows = api.call("/core/rows", {"folder": folder})["rows"]
        res["photos"] = j["scan"]["total"]
        res["hole"] = rows[0]["hole_id"] if rows else None
        im = QImage(str(api.image_file(folder, rows[0]["id"], 160)))
        res["thumb"] = [im.width(), im.height()]
        res["xlsx"] = len(api.call("/core/export/xlsx", {"folder": folder}))
        res["machine_id"] = lic.machine_id()
        # visi Singkapan: OpenCV, Shapely, ONNX Runtime + model SAM & Depth Anything harus ikut terbundel dan jalan
        from gcex_backend import core_vision
        vs = core_vision.status()
        res["vision"] = vs
        ph = api.image_file(folder, rows[0]["id"], 0)
        e = core_vision.sam_embed(Path(ph), "selftest")
        m, sc, _a = core_vision.sam_mask(e, [[0.5, 0.5, 1]], 1)
        res["sam"] = [round(float(m.mean()), 3), round(sc, 3), len(core_vision.mask_polygon(m))]
        res["depth"] = list(core_vision.depth_map(Path(ph)).shape)
        import shapely  # noqa: F401  (ikut terbundel)
        # Borang: PDF scan -> halaman gambar (pypdfium2 ikut terbundel), rute /core/forms terdaftar
        import tempfile
        import pypdfium2 as pdfium
        from PIL import Image
        tp = Path(tempfile.mkdtemp()) / "borang_uji.pdf"
        Image.new("RGB", (400, 560), "white").save(tp, "PDF")
        pg = pdfium.PdfDocument(str(tp))[0].render(scale=2).to_pil()
        res["pdf"] = list(pg.size)
        res["forms"] = len(api.call("/core/forms/open", {"folder": folder})["types"])
        res["ok"] = (bool(rows) and not im.isNull() and res["xlsx"] > 1000 and theme.SANS.lower().startswith("inter")
                     and vs["sam"] and vs["depth"] and bool(vs["libs"].get("shapely")) and res["depth"][0] > 0
                     and res["pdf"][0] > 0 and res["forms"] == 2)
    except Exception as e:  # noqa: BLE001
        import traceback
        res["ok"], res["error"] = False, traceback.format_exc()
    Path(out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
