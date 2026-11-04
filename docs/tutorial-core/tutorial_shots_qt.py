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
from buat_data_dummy import AI_DDR, AI_PIT, AI_ROM, qaqc_data, qt_data  # noqa: E402  data latihan fiktif (sama dengan paket DB-Ex_Data_Dummy)


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
    ph = src / "Foto_Singkapan" / "Dinding_Pit_B.jpg"
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
    # foto dinding pit B: zona oksida hematit-limonit (kiri), andesit segar (tengah), vein / dike hematit tegak (kanan)
    draw("zona_oks", [(0.0, 0.21), (0.2, 0.19), (0.33, 0.21), (0.36, 0.45), (0.35, 0.62), (0.32, 0.82), (0.2, 0.86), (0.0, 0.86)])
    draw("vein", [(0.665, 0.21), (0.685, 0.45), (0.72, 0.58), (0.78, 0.82)])
    draw("kontak_lito", [(0.36, 0.33), (0.5, 0.3), (0.62, 0.48), (0.6, 0.62)])
    draw("label_zona", [(0.01, 0.25), (0.34, 0.25)], "Zona oksida hematit-limonit")
    pg.cbLabelBox.setChecked(True)
    draw("label", [(0.47, 0.62)], "ANDESIT SEGAR")
    draw("orientasi", [(0.69, 0.37)], "N350/80")
    draw("channel", [(0.04, 0.76), (0.5, 0.77), (0.95, 0.74)])
    ch = pg.feats[-1]
    pg.tool.select(ch["id"])
    QGuiApplication.clipboard().setText((src / "Foto_Singkapan" / "Sampel_Channel_Pit_B.txt").read_text(encoding="utf-8"))
    pg.sample_paste()
    pg.save_form()
    pg.save_info({"template": "trench", "grade_color": "Au", "compass": "W", "title": "Channel sampling dinding pit B (latihan)"})
    pg.tool.select(ch["id"])
    shot("q01_singkapan")
    png = WORK / "pit_b_infografis.png"
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
    # =============================================================== Singkapan: tab Analisis (Fase 1) — foto dinding pit A
    w.set_mode("oc")
    ph2 = src / "Foto_Singkapan" / "Dinding_Pit_A.jpg"
    O.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([str(ph2)], ""))
    pg.add_photo()
    until(lambda: pg.cur is not None and pg.cur["file"].startswith("Dinding_Pit_A") and pg.view.w > 0)
    pg.tabs.setCurrentIndex(4)
    pg.anIdx.setCurrentIndex(0)
    pg.an_index(False)
    until(lambda: pg.ovl is not None and not pg.an_busy, 30000)
    shot("q19_analisis_warna")
    pg.an_clear_index()
    # skala latihan (lebar dinding di kaki foto dianggap 20 m) + pelapukan zona segar
    from gcex_backend import core_outcrop as CO
    so = CO.store(pg.folder)
    pid = pg.cur["id"]
    CO.save_feature(so, pid, None, {"kind": "skala", "pts": [[0.05, 0.94], [0.95, 0.94]], "attrs": {"length_m": 20}}, "Rina W.")
    CO.update_photo(so, pid, {"desc:weathering": "W3 (Moderately Weathered) di zona batuan segar"}, "Rina W.")
    pg._pick(pg.lst.currentRow())
    pg.tabs.setCurrentIndex(4)
    pg.an_traces()
    until(lambda: pg.scan_res is not None and not pg.an_busy, 40000)
    wait(500)
    shot("q20_analisis_jejak_otomatis")
    # jejak kekar / vein / sesar digambar geologist mengikuti rekahan terisi oksida yang terlihat
    pg.auto_reject(None)
    for kind, pts in (("sesar", [(0.13, 0.42), (0.22, 0.70), (0.31, 0.97)]), ("kekar", [(0.36, 0.60), (0.44, 0.97)]),
                      ("vein", [(0.40, 0.45), (0.47, 0.66), (0.53, 0.86)]), ("kekar", [(0.48, 0.42), (0.60, 0.92)]),
                      ("kekar", [(0.56, 0.47), (0.63, 0.93)]), ("kekar", [(0.69, 0.42), (0.77, 0.97)]),
                      ("kekar", [(0.82, 0.42), (0.89, 0.97)]), ("kekar", [(0.88, 0.45), (0.97, 0.68)]),
                      ("kekar", [(0.31, 0.51), (0.47, 0.54)]), ("kekar", [(0.50, 0.66), (0.66, 0.70)]),
                      ("kekar", [(0.66, 0.56), (0.80, 0.59)])):
        CO.save_feature(so, pid, None, {"kind": kind, "pts": [list(q) for q in pts]}, "Rina W.")
    pg._pick(pg.lst.currentRow())
    pg.tabs.setCurrentIndex(4)
    pg.anDraft.setChecked(False)
    pg.an_struct()
    until(lambda: pg.scan_res is not None and pg.anSetT.rowCount() >= 1 and not pg.an_busy, 40000)
    wait(500)
    sa = pg.tabs.widget(4)
    sa.verticalScrollBar().setValue(sa.verticalScrollBar().maximum())
    shot("q21_analisis_struktur")
    sa.verticalScrollBar().setValue(0)
    pg.anDraft.setChecked(True)
    if pg.vision().get("sam"):
        pg.anGrid.setCurrentIndex(pg.anGrid.findData("sedang"))
        pg.an_sam()
        until(lambda: "zona usulan dari" in pg.anSamInfo.text(), 240000)
        shot("q22_analisis_sam")
    # =============================================================== Singkapan: lokasi kamera dari GPS HP (bab 20)
    ph4 = src / "Foto_Singkapan" / "Dinding_Pit_C.jpg"
    O.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([str(ph4)], ""))
    pg.add_photo()
    until(lambda: pg.cur is not None and pg.cur["file"].startswith("Dinding_Pit_C"))
    pg.lst.setCurrentRow(next(i for i, x in enumerate(pg.photos) if x["file"].startswith("Dinding_Pit_A")))
    until(lambda: pg.cur is not None and pg.cur["file"].startswith("Dinding_Pit_A"))
    pg.tabs.setCurrentIndex(0)
    until(lambda: pg.cam is not None)
    shot("q23_lokasi_kamera")
    from corex.dialogs import Dlg as _Dlg
    _old_exec = _Dlg.exec

    def _grab_exec(self):
        self.show()
        wait(800)
        self.grab().save(str(IMG / "q24_peta_foto.png"))
        print("OK q24_peta_foto")
        self.hide()
        return _Dlg.Accepted
    _Dlg.exec = _grab_exec
    pg.loc_map()
    _Dlg.exec = _old_exec
    # =============================================================== Singkapan: Model 3D (bab 21)
    import buat_data_dummy as B
    import numpy as np
    from corex.oc3d import Model3DDialog
    import corex.oc3d as M3
    M3.say = lambda *a, **k: print("SAY", a[1:2])
    m3src = src / "Model_3D" / "Dinding_M01"
    d3 = Model3DDialog(pg)
    d3.resize(1500, 900)
    d3.show()
    M3.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: (sorted(str(p) for p in m3src.glob("IMG_*.jpg")), ""))
    d3.new_model()
    d3.build()
    until(lambda: not d3.busy and bool(d3.m.get("recon")), 400000)
    d3.paste_gcps((m3src / "Titik_RTK_Dinding_M01.csv").read_text(encoding="utf-8"))

    def tuv(i, X, W=1600, H=1200):
        cam = B.m3d_cameras(10)[i]
        f = 24 / 36 * W
        xc = cam["R"] @ (np.array(X) - cam["C"])
        return (f * xc[0] / xc[2] + W / 2) / W, (f * xc[1] / xc[2] + H / 2) / H, xc[2]
    for i in range(10):
        d3.lst.setCurrentRow(i)
        until(lambda i=i: d3.view.w > 0 and d3.img == i)
        d3.detect()
        for k, (nm, gs, gz) in enumerate(B.M3D_GCP):
            u, v, z = tuv(i, B.m3d_point(gs, gz))
            if z > 0 and 0.02 < u < 0.98 and 0.02 < v < 0.98:
                d3.gT.selectRow(k)
                d3.tool.press(QPointF(u * d3.view.w, v * d3.view.h), None)
    d3.lst.setCurrentRow(3)
    until(lambda: d3.view.w > 0 and d3.img == 3)
    d3.detect()
    d3.gT.selectRow(2)
    wait(600)
    d3.grab().save(str(IMG / "q25_m3d_rtk.png"))
    print("OK q25_m3d_rtk")
    nv, pv = B._plane(B.M3D_VEIN["dip"], B.M3D_VEIN["ddir"], B.M3D_VEIN["p"])
    tr = []
    for ss in np.linspace(0.1, 29.9, 200):
        P = np.array([B.m3d_point(ss, zz) for zz in np.linspace(0.2, 9.8, 200)])
        dd = (P - pv) @ nv
        tr += [P[k] for k in np.where(np.diff(np.sign(dd)) != 0)[0]]
    d3.tabs.setCurrentIndex(1)
    d3.lst.setCurrentRow(4)
    until(lambda: d3.view.w > 0 and d3.img == 4)
    d3.targets = []
    d3.cbKind.setCurrentIndex(0)
    d3.eName.setText("Vein utama")
    d3.start_measure()
    for X in tr[::4]:
        u, v, z = tuv(4, X)
        if z > 0 and 0.02 < u < 0.98 and 0.02 < v < 0.98:
            d3.tool.press(QPointF(u * d3.view.w, v * d3.view.h), None)
    d3.finish_measure()
    wait(600)
    d3.grab().save(str(IMG / "q26_m3d_ukur.png"))
    print("OK q26_m3d_ukur")
    d3.tabs.setCurrentIndex(2)
    until(lambda: d3.vImg.pixmap() is not None and not d3.vImg.pixmap().isNull(), 30000)
    wait(600)
    d3.grab().save(str(IMG / "q27_m3d_tampilan.png"))
    print("OK q27_m3d_tampilan")
    d3.close()
    # =============================================================== QAQC
    import corex.qaqc as Q
    Q.show_in_folder = lambda p: None
    Q.say = lambda *a, **k: print("SAY", str(a[1])[:120])
    wbp = qaqc_data(src)
    w.set_mode("qa")
    qp = w.qaqc
    until(lambda: qp.res is not None)
    Q.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([str(wbp)], ""))
    qp.cbTarget.setCurrentIndex(0)
    qp.import_files()
    until(lambda: qp.res is not None and qp.res["counts"]["crm_data"] == 48)
    wait(2500)
    shot("q12_qaqc_dashboard")
    for i, name in ((1, "q13_qaqc_crm"), (3, "q14_qaqc_duplikat")):
        qp.tabs.setCurrentIndex(i)
        ch = qp.cCrm if i == 1 else qp.cDup
        until(lambda ch=ch: ch.labels and all(lb.pixmap() and not lb.pixmap().isNull() for lb in ch.labels), 40000)
        wait(300)
        shot(name)
    qp.tabs.setCurrentIndex(9 - 1)
    qp.ed["batch_from"].setCurrentText("LAB26000")
    qp.ed["batch_to"].setCurrentText("LAB26005")
    qp.save_settings()
    until(lambda: qp.res is not None and qp.res["filter_text"].startswith("Batch LAB26000"))
    wait(400)
    shot("q15_qaqc_panel")
    qp.clear_filter()
    until(lambda: qp.res is not None and not qp.res["filter_text"])
    # Data: input manual / tempel dari Excel (perubahan tidak disimpan -> Batal)
    qp.tabs.setCurrentIndex(6)
    qp.cbTbl.setCurrentIndex(qp.cbTbl.findData("CRM_Data"))
    until(lambda: qp._tblShown == "CRM_Data" and qp.tT.rowCount() == 48)
    qp.tT.setCurrentCell(-1, -1)
    dup = qp.tT.item(40, 0).text()
    qp.paste_rows(f"Sample_ID\tStandard_Name\tLab_Grade\tZona\nZ8_MAN_001\tCRM-B\t1,47\tZ8\n{dup}\tCRM-A\t0.51\tZ8\nZ8_MAN_003\tCRM-C\tabc\tZ8\n")
    qp.tT.scrollToBottom()
    qp.tT.setCurrentCell(48, 0)
    wait(400)
    shot("q18_qaqc_data_tempel")
    qp.bUndo.click()
    until(lambda: not qp.tDirty and qp.tT.rowCount() == 48)
    # data bor: impor Collar / Survey / Assay latihan lewat backend lalu periksa
    from gcex_backend import core_dh, core_io
    pj = core_io.get_project(str(prj))
    lab = src / "Data_Lab"
    if not lab.exists():
        from buat_data_dummy import main as _m  # noqa: F401
    qp.tabs.setCurrentIndex(7)
    rows = [["Hole", "E", "N", "RL", "EOH"], ["XX-1", 1000, 2000, 300, 30], ["XX-2", 1010, 2000, 300, None], ["XX-3", 1020, 2005, 300, 20]]
    core_dh.do_import(pj, "collar", rows, 0, {"hole": 0, "x": 1, "y": 2, "z": 3, "depth": 4}, [], "replace")
    core_dh.do_import(pj, "survey", [["Hole", "Depth", "Dip", "Azi"], ["XX-1", 0, -60, 90], ["XX-1", 15, -58, 92], ["XX-1", 30, 55, 95],
                                     ["XX-3", 0, -90, 0], ["XX-3", 24, -88, 10]], 0, {"hole": 0, "at": 1, "dip": 2, "azi": 3}, [], "replace")
    core_dh.do_import(pj, "assay", [["Hole", "From", "To", "Sample", "Au"], ["XX-1", 0, 2, "S1", 0.1], ["XX-1", 1.5, 3, "S2", 0.2],
                                    ["XX-1", 5, 6, "S3", 0.05], ["XX-1", 29, 31, "S1", 0.3], ["XX-3", 0, 1, "S9", 0.1]], 0,
                      {"hole": 0, "from": 1, "to": 2}, [{"i": 3, "src": "Sample", "name": "Sample", "type": "s", "use": True},
                                                        {"i": 4, "src": "Au", "name": "Au", "type": "n", "use": True}], "replace")
    qp.run_dh()
    until(lambda: "lubang" in qp.dhInfo.text())
    shot("q16_qaqc_databor")
    rep_dir = WORK / "keluar"
    rep_dir.mkdir(exist_ok=True)
    Q.QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (str(rep_dir / "Laporan_QAQC_Latihan"), ""))
    qp.export_pdf()
    until(lambda: (rep_dir / "Laporan_QAQC_Latihan.pdf").exists(), 60000)
    wait(500)
    import pypdfium2 as pdfium
    d = pdfium.PdfDocument(str(rep_dir / "Laporan_QAQC_Latihan.pdf"))
    for i in (0, 1):
        d[i].render(scale=1.0).to_pil().save(IMG / f"q17_qaqc_laporan_{i + 1}.png")
    print("OK q17 laporan", len(d), "halaman")
    w.close()


if __name__ == "__main__":
    main()
