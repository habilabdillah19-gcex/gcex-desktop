"""Tangkapan layar tutorial DB-Ex versi Qt (bab Singkapan, Borang ore spotter, Daily Drilling Report): docs/tutorial-core/gambar/q*.png.

Semua isi FIKTIF: foto singkapan sintetis, scan borang digambar ulang (tulisan miring biru meniru tulisan tangan), nama spotter /
driller / rig / lubang contoh. Jawaban AI diambil dari jawaban tiruan (tanpa Ollama), sama seperti uji otomatis.

Pemakaian:  QT_QPA_PLATFORM=offscreen python docs/tutorial-core/tutorial_shots_qt.py
            (butuh PySide6, fastapi, pillow, openpyxl, numpy; lalu cetak PDF: python docs/tutorial-core/buat_pdf.py)
"""
import json
import os
import random
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

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402

rnd = random.Random(20261101)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_I = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def hand(dr, xy, text, size=26, color=(25, 40, 140)):
    """Tulisan 'tangan': miring biru, posisi tiap huruf sedikit bergoyang."""
    x, y = xy
    fo = f(FONT_I, size)
    for ch in str(text):
        dr.text((x + rnd.uniform(-1, 1), y + rnd.uniform(-1.5, 1.5)), ch, fill=color, font=fo)
        x += dr.textlength(ch, font=fo) * rnd.uniform(0.96, 1.08)


def paper(w, h):
    a = np.full((h, w, 3), (246, 245, 238), np.uint8).astype(np.int16)
    a += np.random.default_rng(5).integers(-6, 6, (h, w, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ----------------------------------------------------------------------------------------------- gambar sintetis
def outcrop_photo(p: Path) -> None:
    """Dinding trench sintetis: tuff propilitik (hijau abu), zona argilik (pucat), pita gossan (coklat) & urat kuarsa."""
    W, H = 1800, 1100
    yy, xx = np.mgrid[0:H, 0:W]
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, (H // 6, W // 6))
    noise = np.array(Image.fromarray(((noise - noise.min()) / np.ptp(noise) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)) / 255
    img = np.zeros((H, W, 3), np.float32)
    img[:] = (118, 128, 108)
    arg = (xx > 520 + 0.25 * yy) & (xx < 1080 + 0.2 * yy)
    img[arg] = (196, 188, 168)
    gos = (abs(xx - (1180 + 0.18 * yy)) < 70)
    img[gos] = (142, 92, 54)
    vein = abs(xx - (860 - 0.45 * (yy - 550))) < 9
    img[vein] = (232, 230, 222)
    img *= (0.78 + 0.4 * noise[..., None])
    img[:140] = img[:140] * 0.55 + np.array((150, 170, 190)) * 0.45  # langit / latar atas
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    dr = ImageDraw.Draw(im)
    for i in range(6):  # pita ukur di lantai trench
        dr.rectangle([150 + i * 260, 1010, 150 + i * 260 + 130, 1030], fill=(220, 200, 40))
    im.save(p, quality=90)


KELAS = ["OX-LG", "SF-LG", "OX-HG", "SF-HG", "OX-SG", "SF-SG", "OX-MO", "SF-MO"]
KCOL = [(120, 200, 120), (120, 200, 120), (230, 110, 110), (230, 110, 110), (220, 120, 200), (220, 120, 200), (240, 220, 80), (240, 220, 80)]
PIT_ROWS = [("19.08", "Pit X", "268.5", "OX-LG", "7123", "37", "ROM A1"), ("13", "", "", "OX-LG", "32", "31", "〃"),
            ("30", "", "", "OX-LG", "7130", "35", "〃"), ("57", "", "", "OX-LG", "28", "35", "〃"), ("21.01", "", "", "OX-HG", "7123", "33", "ROM B2"),
            ("", "", "268.0", "", "", "", ""), ("23.35", "", "", "OX-LG", "7132", "30", "〃 A1"), ("46", "", "", "OX-LG", "29", "34", "〃"),
            ("55", "", "", "OX-LG", "23", "3l", "〃"), ("03.53", "", "", "OX-LG", "7132", "34", "〃"), ("56", "", "", "OX-LG", "29", "35", "〃")]


def form_pit(p: Path) -> None:
    W, H = 2000, 1300
    im = paper(W, H)
    dr = ImageDraw.Draw(im)
    dr.text((700, 40), "CONTOH TAMBANG (FIKTIF)", fill=(30, 30, 30), font=f(FONT_B, 30))
    dr.text((560, 85), "FORM LOADING ORE DARI PIT TO ROM / STOCKPILE", fill=(30, 30, 30), font=f(FONT_B, 28))
    for i, (lab, val) in enumerate((("NAMA CREW", "Spotter A"), ("LOKASI", "Pit X"))):
        dr.text((60, 150 + i * 40), lab, fill=(30, 30, 30), font=f(FONT_B, 22))
        hand(dr, (260, 145 + i * 40), ": " + val, 28)
    hand(dr, (620, 175), "EX-901", 32)
    for i, (lab, val) in enumerate((("TANGGAL", ": 30-10-2026"), ("SHIFT", ": II"))):
        dr.text((1250, 150 + i * 40), lab, fill=(30, 30, 30), font=f(FONT_B, 22))
        hand(dr, (1420, 145 + i * 40), val, 28)
    x0, y0, rh = 50, 250, 62
    cols = [70, 120, 120, 120, 120] + [95, 95] * 8 + [190]
    xs = [x0]
    for c in cols:
        xs.append(xs[-1] + c)
    heads = ["NO", "Start", "Finish", "PIT", "Elev."]
    for i, hd in enumerate(heads):
        dr.text((xs[i] + 8, y0 + 20), hd, fill=(30, 30, 30), font=f(FONT_B, 18))
    for k, (name, colr) in enumerate(zip(KELAS, KCOL)):
        a = xs[5 + 2 * k]
        dr.rectangle([a, y0, a + 190, y0 + 32], fill=colr)
        dr.text((a + 55, y0 + 4), name, fill=(20, 20, 20), font=f(FONT_B, 18))
        dr.text((a + 6, y0 + 38), "TRUCK", fill=(30, 30, 30), font=f(FONT, 14))
        dr.text((a + 100, y0 + 38), "Ton", fill=(30, 30, 30), font=f(FONT, 14))
    dr.rectangle([xs[-2], y0, xs[-1], y0 + 60], fill=(140, 200, 140))
    dr.text((xs[-2] + 10, y0 + 18), "Tujuan Dumping", fill=(20, 20, 20), font=f(FONT_B, 17))
    n = 15
    for r in range(n + 2):
        dr.line([(xs[0], y0 + 60 + r * rh - (60 if r == 0 else 0)), (xs[-1], y0 + 60 + r * rh - (60 if r == 0 else 0))], fill=(60, 60, 60), width=2)
    for x in xs:
        dr.line([(x, y0), (x, y0 + 60 + (n + 1) * rh)], fill=(60, 60, 60), width=2)
    for r in range(n + 1):
        dr.text((xs[0] + 20, y0 + 60 + r * rh + 18), str(r + 1), fill=(30, 30, 30), font=f(FONT, 18))
    for r, (jam, pit, el, kl, trk, ton, tj) in enumerate(PIT_ROWS):
        yy = y0 + 60 + r * rh + 12
        hand(dr, (xs[1] + 8, yy), jam)
        if pit:
            hand(dr, (xs[3] + 8, yy), pit, 24)
        if el:
            hand(dr, (xs[4] + 8, yy), el, 24)
        if kl:
            k = KELAS.index(kl)
            hand(dr, (xs[5 + 2 * k] + 6, yy), trk)
            hand(dr, (xs[6 + 2 * k] + 20, yy), ton)
        if tj:
            hand(dr, (xs[-2] + 12, yy), tj, 24)
    im.save(p, quality=90)


def form_rom(p: Path) -> None:
    W, H = 2000, 1100
    im = paper(W, H)
    dr = ImageDraw.Draw(im)
    dr.text((520, 50), "Form Ore to STOCKPILE / CRUSHER (Rehandling / Direct)  — FIKTIF", fill=(30, 30, 30), font=f(FONT_B, 28))
    for i, (lab, val) in enumerate((("CREW", ": Spotter B"), ("LOKASI", ": ROM A1"), ("TANGGAL", ": 31/10/2026"), ("SHIFT", ": I"))):
        dr.text((60 + (i // 2) * 900, 120 + (i % 2) * 40), lab, fill=(30, 30, 30), font=f(FONT_B, 22))
        hand(dr, (220 + (i // 2) * 900, 115 + (i % 2) * 40), val, 28)
    hd = ["NO", "Unit", "Finish", "Asal", "Tujuan", "SP-1", "SP-2", "SF-LG", "SCAT", "Baru", "Lama", "Keterangan"]
    ws = [70, 150, 130, 200, 200, 90, 90, 120, 120, 90, 90, 260]
    xs = [60]
    for w_ in ws:
        xs.append(xs[-1] + w_)
    y0, rh = 230, 62
    for i, h in enumerate(hd):
        fill = (120, 200, 120) if h == "SF-LG" else ((150, 210, 220) if h == "SCAT" else None)
        if fill:
            dr.rectangle([xs[i], y0, xs[i + 1], y0 + 50], fill=fill)
        dr.text((xs[i] + 8, y0 + 14), h, fill=(30, 30, 30), font=f(FONT_B, 18))
    rows = [("1", "DT 7101", "08.02", "Pit X", "Crusher", "✓", "", "39", "", "✓", "", "Direct"), ("2", "7102", "05", "〃", "〃", "✓", "", "37", "", "|", "", "Direct"),
            ("3", "7103", "11", "ROM A1", "=", "", "", "", "32", "", "✓", "Rehandling")]
    for r in range(11):
        dr.line([(xs[0], y0 + 50 + r * rh), (xs[-1], y0 + 50 + r * rh)], fill=(60, 60, 60), width=2)
    for x in xs:
        dr.line([(x, y0), (x, y0 + 50 + 10 * rh)], fill=(60, 60, 60), width=2)
    for r, row in enumerate(rows):
        for i, v in enumerate(row):
            if v:
                hand(dr, (xs[i] + 10, y0 + 60 + r * rh), v, 24)
    im.save(p, quality=90)


DDR_ACTS = [("0650", "0700", "Traveling to ROM A1"), ("0700", "0705", "P5M"), ("0705", "0710", "Traveling to pit"), ("0710", "0725", "P2H"),
            ("0725", "0750", "Start engine + cleaning siklon"), ("0750", "0830", "Traveling unit to titik bor"),
            ("0830", "0840", "Start engine + compressor"), ("0840", "1150", "Start drilling + cleaning siklon"),
            ("1150", "1200", "Traveling unit, jarak aman blasting"), ("1200", "1300", "Restaem"),
            ("1300", "1500", "Standby area titik bor longsor"), ("1500", "1800", "Standby tidak ada lokasi")]
DDR_HOLES = [("0", "30", "XX-100-S-05", "70", "60"), ("0", "30", "XX-100-S-01", "60", "60"), ("0", "30", "XX-100-S-02", "60", "60")]


def form_ddr(p: Path) -> None:
    W, H = 1500, 2100
    im = paper(W, H)
    dr = ImageDraw.Draw(im)
    dr.text((380, 60), "DAILY DRILLING REPORT (FIKTIF)", fill=(30, 30, 30), font=f(FONT_B, 40))
    for i, (lab, val) in enumerate((("Client", "Klien A"), ("DHP_ID", "KTR"), ("Driller", "Driller A"))):
        dr.text((560, 140 + i * 42), lab, fill=(30, 30, 30), font=f(FONT, 22))
        hand(dr, (700, 135 + i * 42), ": " + val, 28)
    for i, (lab, val) in enumerate((("Date", "31-10-26"), ("Drill Rig", "hansin - sdr - 101"), ("Shift", "I"))):
        dr.text((1000, 140 + i * 42), lab, fill=(30, 30, 30), font=f(FONT, 22))
        hand(dr, (1130, 135 + i * 42), ": " + val, 28)
    y0, rh = 290, 62
    xs = [60, 150, 240, 520, 600, 680, 1440]
    dr.rectangle([60, y0, 1440, y0 + 50], fill=(215, 225, 215))
    for x, t in zip(xs, ["From", "To", "Hole ID", "Az", "Dip", "DRILLING DETAILS and FORMATION DESCRIPTION"]):
        dr.text((x + 8, y0 + 14), t, fill=(30, 30, 30), font=f(FONT_B, 18))
    for r in range(25):
        dr.line([(60, y0 + 50 + r * rh), (1440, y0 + 50 + r * rh)], fill=(90, 90, 90), width=1)
    for x in xs:
        dr.line([(x, y0), (x, y0 + 50 + 24 * rh)], fill=(60, 60, 60), width=2)
    for r, h in enumerate(DDR_HOLES):
        for x, v in zip(xs, h):
            hand(dr, (x + 8, y0 + 60 + r * rh), v, 24)
    r = 0
    for a, b, t in DDR_ACTS:
        hand(dr, (690, y0 + 60 + r * rh), f"{a}-{b} {t.upper()}", 23)
        r += 2 if len(t) > 26 else 1
    yb = y0 + 50 + 24 * rh + 40
    dr.text((60, yb), "BITS / REAMER        HM ENGINE  Start: ", fill=(30, 30, 30), font=f(FONT_B, 20))
    hand(dr, (520, yb - 5), "1200.5     Finish: 1203.7", 26)
    hand(dr, (60, yb + 60), "WH: 4.75hr   DL: 3.5hrs   STD: 3hr", 30)
    hand(dr, (60, yb + 110), "area drillpad longsor, menunggu area baru", 28)
    im.save(p, quality=90)


# ----------------------------------------------------------------------------------------------- jawaban AI tiruan
AI_PIT = {"header": {"tanggal": "30-10-2026", "shift": "II", "crew": "Spotter A", "lokasi": "Pit X", "excavator": "EX-901", "ragu": []},
          "rows": [{"no": str(i + 1), "start": j, "finish": "", "pit": pt, "elevasi": el, "kelas": kl if trk else "", "unit": trk, "ton": tn,
                    "tujuan": tj, "ragu": (["ton"] if tn == "3l" else [])} for i, (j, pt, el, kl, trk, tn, tj) in enumerate(PIT_ROWS)]}
AI_ROM = {"header": {"tanggal": "31/10/2026", "shift": "I", "crew": "Spotter B", "lokasi": "ROM A1"},
          "rows": [{"no": "1", "unit": "DT 7101", "start": "", "finish": "08.02", "asal": "Pit X", "tujuan": "Crusher", "rehandling": "SP-1",
                    "kelas": "SF-LG", "ton": "39", "status": "Baru", "keterangan": "Direct"},
                   {"no": "2", "unit": "7102", "start": "", "finish": "05", "asal": "〃", "tujuan": "〃", "rehandling": "〃", "kelas": "SF-LG",
                    "ton": "37", "status": "", "keterangan": "Direct"},
                   {"no": "3", "unit": "7103", "start": "", "finish": "11", "asal": "ROM A1", "tujuan": "=", "rehandling": "", "kelas": "SCAT",
                    "ton": "32", "status": "Lama", "keterangan": "Rehandling"}]}
AI_DDR = {"header": {"tanggal": "31-10-26", "shift": "I", "rig": "hansin - sdr - 101", "driller": "Driller A", "client": "Klien A",
                     "dhp_id": "KTR", "wh": "4.75hr", "dl": "3.5hrs", "std": "3hr", "hm_start": "1200.5", "hm_finish": "1203.7",
                     "catatan": "area drillpad longsor, menunggu area baru", "ragu": ["dhp_id"]},
          "rows": [{"mulai": a, "selesai": b, "aktivitas": t, "kategori": ""} for a, b, t in DDR_ACTS],
          "lubang": [dict(zip(["from_m", "to_m", "hole_id", "az", "dip"], h)) for h in DDR_HOLES]}


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
    ph = src / "Trench_Latihan_TR01.jpg"
    outcrop_photo(ph)
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
    QGuiApplication.clipboard().setText("Sample ID\tDari\tKe\tAu (ppm)\tAg_ppm\n"
                                        "TR01-01\t0\t2\t0,21\t3\nTR01-02\t2\t3,5\t1,85\t9\nTR01-03\t3,5\t4,4\t6,4\t21\nTR01-04\t4,4\t6\t0,48\t5")
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
    p1 = src / "Borang_Loading_Pit_30Okt.jpg"
    form_pit(p1)
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
    p2 = src / "Borang_ROM_31Okt.jpg"
    form_rom(p2)
    add_form("rom", p2)
    fake_ai(AI_ROM)
    fp.tabs.setCurrentIndex(0)
    fp.run_ai()
    until(lambda: not fp.ai_busy and fp.t.rowCount() > 0)
    shot("q07_borang_rom")
    # --- Daily Drilling Report
    p3 = src / "DDR_31Okt.jpg"
    form_ddr(p3)
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
