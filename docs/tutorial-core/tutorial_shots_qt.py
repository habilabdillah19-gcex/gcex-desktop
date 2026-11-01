"""Tangkapan layar tutorial DB-Ex versi Qt (bab Singkapan, Borang ore spotter, Daily Drilling Report): docs/tutorial-core/gambar/q*.png.

Semua isi FIKTIF: foto singkapan sintetis, scan borang digambar ulang (tulisan miring biru meniru tulisan tangan), nama spotter /
driller / rig / lubang contoh. Jawaban AI diambil dari jawaban tiruan (tanpa Ollama), sama seperti uji otomatis.

Pemakaian:  QT_QPA_PLATFORM=offscreen python docs/tutorial-core/tutorial_shots_qt.py
            (butuh PySide6, fastapi, pillow, openpyxl, numpy; lalu cetak PDF: python docs/tutorial-core/buat_pdf.py)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
T = Path(__file__).resolve().parent
R = T.parents[1]
IMG = T / "gambar"
sys.path.insert(0, str(R / "app_core_qt"))
sys.path.insert(0, str(R / "backend"))
WORK = Path(tempfile.mkdtemp(prefix="dbex_tutqt_"))
os.environ["COREX_USERDATA"] = str(WORK / "ud")
os.environ["GCEX_CACHE"] = str(WORK / "cache")

from PIL import Image  # noqa: E402

sys.path.insert(0, str(T))
from buat_data_dummy import AI_DDR, AI_PIT, AI_ROM, qt_data  # noqa: E402  data latihan fiktif (sama dengan paket DB-Ex_Data_Dummy)


def main() -> None:
    from PySide6.QtCore import QEventLoop, QPointF, QTimer
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from corex import theme, util
    util.SET.__init__()
    util.SET.set("user", "Rina W.")
    util.SET.set("autoOllama", False)
    theme.load_fonts()
    theme.apply(app)
    import corex.forms as F
    import corex.outcrop as O
    from corex.api import core_io
    from corex.mainwin import MainWindow
    for m in (F, O):
        m.show_in_folder = lambda p: None
        m.ask = lambda *a, **k: True
        m.say = lambda *a, **k: print("SAY", a[1:2])

    def wait(ms=500):
        lp = QEventLoop()
        QTimer.singleShot(ms, lp.quit)
        lp.exec()

    def until(cond, ms=15000):
        t = 0
        while not cond() and t < ms:
            wait(100)
            t += 100

    prj = WORK / "Proyek_Latihan"
    (prj / "LTH-101").mkdir(parents=True)
    for i in range(1, 4):  # 3 foto core box kosong agar proyek bisa dibuka
        Image.new("RGB", (900, 600), (90 + i * 15, 80, 70)).save(prj / "LTH-101" / f"LTH-101_Box{i}_{(i - 1) * 3.5:.2f}-{i * 3.5:.2f}.jpg")
    src = WORK / "lapangan"
    src.mkdir()
    IMG.mkdir(exist_ok=True)
    w = MainWindow("uji")
    w.resize(1500, 900)
    w.show()
    w.open_folder(str(prj))
    until(lambda: len(w.view) == 3)

    def shot(name, wid=None):
        wait(400)
        w.toastL.hide()
        w.prj.setText("D:\\Latihan\\Proyek_Latihan")  # path gaya Windows seperti di tutorial
        (wid or w).grab().save(str(IMG / f"{name}.png"))
        print("OK", name)

    # =============================================================== Singkapan
    w.set_mode("oc")
    pg = w.outcrop
    qt_data(src)
    ph = src / "Foto_Singkapan" / "Trench_Latihan_TR01.jpg"
    O.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([str(ph)], ""))
    pg.add_photo()
    until(lambda: pg.cur is not None and pg.view.w > 0)

    def draw(kind, pts, name=None):
        if name is not None:
            pg.ask_text = lambda *a, n=name: n
        pg.cbKind.setCurrentIndex(pg.cbKind.findData(kind))
        pg.bDraw.click()
        for u, v in pts:
            pg.tool.press(QPointF(u * pg.view.w, v * pg.view.h), None)
        if pg.kmap[kind]["shape"] != "point":
            pg.tool.finish()
    draw("zona_alt", [(0.29, 0.13), (0.62, 0.13), (0.75, 0.93), (0.42, 0.93)])
    draw("vein", [(0.6, 0.14), (0.36, 0.92)])
    draw("label_zona", [(0.30, 0.2), (0.6, 0.2)], "Zona argilik (FIKTIF)")
    pg.cbLabelBox.setChecked(True)
    draw("label", [(0.12, 0.35)], "TUFF PROPILITIK")
    draw("orientasi", [(0.47, 0.55)], "N120/70")
    draw("channel", [(0.05, 0.78), (0.5, 0.8), (0.95, 0.77)])
    ch = pg.feats[-1]
    pg.tool.select(ch["id"])
    QGuiApplication.clipboard().setText((src / "Foto_Singkapan" / "Sampel_Trench_TR01.txt").read_text(encoding="utf-8"))
    pg.sample_paste()
    pg.save_form()
    pg.save_info({"template": "trench", "grade_color": "Au", "compass": "W"})
    pg.tool.select(ch["id"])
    shot("q01_singkapan")
    png = WORK / "trench_infografis.png"
    O.QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (str(png), ""))
    pg.export("png")
    until(lambda: png.exists())
    wait(800)
    im = Image.open(png)
    im.thumbnail((1500, 1500))
    im.save(IMG / "q02_infografis.png")
    print("OK q02_infografis")

    # =============================================================== Borang
    def fake_ai(res):
        core_io._http = lambda url, body=None, timeout=5.0: {"message": {"content": json.dumps(res)}}
        w.ai.info = {"running": True}
        w.ai.model = lambda: "qwen2.5vl:7b"
    w.set_mode("form")
    fp = w.forms

    def add_form(kind, path):
        fp.cbNew.setCurrentIndex(fp.cbNew.findData(kind))
        F.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([str(path)], ""))
        n = len(fp.docs)
        fp.add_files()
        until(lambda: len(fp.docs) == n + 1 and fp.cur and fp.cur["doc"]["type"] == kind and fp.view.w > 0)

    # --- Ore Spotter: Loading Pit
    p1 = src / "Borang" / "Borang_Loading_Pit_30Okt.jpg"
    add_form("ore", p1)
    shot("q03_borang_baru")
    fake_ai(AI_PIT)
    fp.run_ai()
    until(lambda: not fp.ai_busy and fp.t.rowCount() > 0)
    wait(600)
    fp.t.setCurrentCell(1, 1)
    fp.verify_next()
    wait(300)
    shot("q04_borang_ai")
    # perbaiki tonase '3l' -> 31 lalu verifikasi semua
    cols = [k for k, _l in fp.cols(fp.types["ore"])]
    bad = next(i for i in range(fp.t.rowCount()) if fp.t.item(i, 1 + cols.index("ton")).text() == "3l")
    fp.t.item(bad, 1 + cols.index("ton")).setText("31")
    wait(500)
    fp.verify_all(True)
    fp.tabs.setCurrentIndex(1)
    shot("q05_borang_pivot")
    fp.tabs.setCurrentIndex(2)
    db = WORK / "keluar" / "Borang_Latihan.db"
    db.parent.mkdir()
    F.QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (str(db), ""))
    fp.export("sqlite")
    until(lambda: not fp.expInfo.isHidden())
    shot("q06_borang_ekspor")
    # --- Ore ke ROM / crusher
    p2 = src / "Borang" / "Borang_ROM_31Okt.jpg"
    add_form("rom", p2)
    fake_ai(AI_ROM)
    fp.tabs.setCurrentIndex(0)
    fp.run_ai()
    until(lambda: not fp.ai_busy and fp.t.rowCount() > 0)
    shot("q07_borang_rom")
    # --- Daily Drilling Report
    p3 = src / "Borang" / "DDR_31Okt.jpg"
    add_form("ddr", p3)
    fake_ai(AI_DDR)
    fp.run_ai()
    until(lambda: not fp.ai_busy and fp.t.rowCount() > 0)
    fp.hdrEd["lokasi"].setText("Area Latihan")
    fp._hdr_save("lokasi")
    wait(400)
    shot("q08_ddr_aktivitas")
    fp.cbTbl.setCurrentIndex(1)
    shot("q09_ddr_meterage")
    fp.cbTbl.setCurrentIndex(0)
    fp.verify_all(True)
    fp.tabs.setCurrentIndex(1)
    shot("q10_ddr_pivot")
    xl = WORK / "keluar" / "DDR_Latihan.xlsx"
    F.QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (str(xl), ""))
    fp.tabs.setCurrentIndex(2)
    fp.rThis.setChecked(True)
    fp.export("xlsx")
    until(lambda: xl.exists())
    import openpyxl
    ws = openpyxl.load_workbook(xl)["Data_Dashboard"]
    rows = [[("" if c.value is None else (c.value.strftime("%d-%b-%Y") if hasattr(c.value, "strftime") else c.value)) for c in r][:16]
            for r in ws.iter_rows()]
    (WORK / "q11_data_dashboard.json").write_text(json.dumps(rows, ensure_ascii=False, default=str, indent=0), encoding="utf-8")
    print("OK q11_data_dashboard.json", len(rows) - 1, "baris")
    w.close()


if __name__ == "__main__":
    main()
