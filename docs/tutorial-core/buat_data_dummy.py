"""Buat paket data dummy tutorial GC-Ex Core Interpretation.

Pemakaian: python docs/tutorial-core/buat_data_dummy.py <folder_keluaran> [foto_asli.jpg]

Isi (semua angka fiktif, hanya untuk latihan):
  Foto_Core/LTH-101/   11 foto core box sintetis (box 1-10, 12), nama file berpola Hole_Box_From-To
  Foto_Core/LTH-102/   12 foto core box sintetis
  Foto_Core/IMG_0001.jpg  foto core box asli proyek (LTH-101 box 11, 36.30-40.10 m) dengan nama file tanpa info,
                          untuk latihan AI membaca papan label
  Data_Lab/Collar_Z3.csv              titik koma, koma desimal, header BHID / Easting / Northing / RL / EOH
  Data_Lab/Survey_Z3.csv              header Hole_ID / Depth / Inclination / Bearing
  Data_Lab/Assay_Z3.xlsx              2 baris judul laporan di atas header, Au (ppm) dengan nilai <0.01, kolom Lab_Stat
  Data_Lab/Geologi_Z3.txt             tab, hanya LTH-101 (LTH-102 belum dilogging): Lith, Alt_Int, Ox, Mineralogy, Vein_Type
  Data_Lab/Assay_LTH-102_ulang.csv  hasil assay ulang LTH-102 (latihan tambah / perbarui per hole)
  Dashboard_lama/Geotech_Dashboard_LTH-102.json  file proyek dashboard lama (Gemini), latihan Impor JSON
"""
import json
import random
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1])
REAL = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / "referensi" / "contoh_corebox_LTH-101_box11.jpg"
rnd = random.Random(20261028)


def font(sz, bold=False):
    for f in (["DejaVuSansMono-Bold.ttf", "consolab.ttf"] if bold else ["DejaVuSansMono.ttf", "consola.ttf"]):
        for d in ("/usr/share/fonts/truetype/dejavu/", "C:/Windows/Fonts/", ""):
            try:
                return ImageFont.truetype(d + f, sz)
            except OSError:
                continue
    return ImageFont.load_default()


F, FB = font(37), font(40, True)

# ------------------------------------------------------------------ geologi fiktif (dipakai foto, assay, logging)
GEO = [  # from, to, lith, alterasi, oksidasi, mineralogi, vein, warna core (RGB), rekahan (0-1)
    (0.0, 8.0, "AND", "Argilik", "OX", "limonit, goethit", "-", (150, 112, 82), 0.8),
    (8.0, 21.5, "AND", "Propilitik", "FR", "pyrite 1%, klorit", "-", (78, 92, 84), 0.35),
    (21.5, 30.5, "AND", "Propilitik", "FR", "pyrite 1%", "veinlet", (72, 86, 80), 0.3),
    (30.5, 36.8, "DAC", "Silisifikasi", "FR", "pyrite 2%", "stockwork", (96, 98, 100), 0.45),
    (36.8, 41.2, "QV", "Silisifikasi kuat", "FR", "pyrite, chalcopyrite, galena", "QV banded", (64, 66, 68), 0.25),
    (41.2, 50.0, "AND", "Propilitik", "FR", "pyrite 1%", "-", (80, 92, 86), 0.3),
]
GEO_543 = [(0, 6, (152, 116, 86), 0.85), (6, 19, (84, 96, 90), 0.35), (19, 23.5, (100, 102, 104), 0.5), (23.5, 50, (82, 94, 88), 0.3)]


def geo_at(d, table):
    for g in table:
        if g[0] <= d < g[1]:
            return g
    return table[-1]


def box_photo(path, hole, bx, a, b, date, table):
    W, H = 1600, 1200
    im = Image.new("RGB", (W, H), (70, 72, 74))
    d = ImageDraw.Draw(im)
    d.rectangle([24, 16, W - 24, 320], fill=(232, 233, 228), outline=(40, 40, 40), width=5)
    d.text((W // 2, 56), "PT. CONTOH TAMBANG", fill=(25, 25, 25), font=FB, anchor="mm")
    for (x, y, t) in [(56, 128, f"HOLE ID:{hole}"), (840, 128, "START DRILL:05-03-25"), (56, 200, f"BOX    :{bx}"),
                      (840, 200, f"DATE  POTO:{date}"), (56, 272, f"DEPTH:{a:.2f}"), (576, 272, f"M:TO:{b:.2f}"), (1000, 272, "M:CONDT:")]:
        d.text((x, y), t, fill=(20, 20, 20), font=F, anchor="lm")
    d.rectangle([1216, 244, 1360, 304], outline=(20, 20, 20), width=4)
    d.text((1288, 274), "WET", fill=(20, 20, 20), font=F, anchor="mm")
    d.rectangle([32, 336, W - 32, 1064], fill=(150, 150, 145))
    rows, rl = 4, (b - a) / 4
    for r in range(rows):
        y = 352 + r * 178
        d.rectangle([44, y, W - 44, y + 160], fill=(35, 37, 38))
        x = 48
        while x < W - 56:
            dep = a + rl * (r + (x - 48) / (W - 104))
            g = geo_at(dep, table)
            base, frac = g[-2], g[-1]
            L = int(rnd.uniform(30, 300) * (1.25 - frac))
            c = tuple(max(0, min(255, base[i] + rnd.randint(-10, 10))) for i in range(3))
            d.rounded_rectangle([x, y + 16, min(W - 48, x + L), y + 144], 48, fill=c)
            for _ in range(rnd.randint(0, 2)):
                q = x + rnd.randint(4, max(5, L - 4))
                d.line([q, y + 16, q + rnd.randint(-24, 24), y + 144], fill=(205, 205, 195), width=3)
            x += L + rnd.randint(3, 12)
        if r in (1, 3):
            d.rectangle([720, y + 32, 768, y + 128], fill=(240, 240, 235))
    for i in range(0, W, 96):
        for j, yy in enumerate([1076, 1136]):
            d.rectangle([i, yy, i + 96, yy + 60], fill=(20, 20, 20) if (i // 96 + j) % 2 else (235, 235, 230))
    im.save(path, quality=82)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    foto, lab, old = OUT / "Foto_Core", OUT / "Data_Lab", OUT / "Dashboard_lama"
    for p in (foto / "LTH-101", foto / "LTH-102", lab, old):
        p.mkdir(parents=True)
    t542 = [(g[0], g[1], g[7], g[8]) for g in GEO]
    # LTH-101: box 1-10 rata 3.63 m sampai 36.30; box 11 = foto asli 36.30-40.10; box 12 40.10-43.90
    for bx in range(1, 13):
        if bx == 11:
            continue
        a, b = ((bx - 1) * 3.63, bx * 3.63) if bx <= 10 else (40.10, 43.90)
        box_photo(foto / "LTH-101" / f"LTH-101_Box{bx}_{a:.2f}-{b:.2f}.jpg", "LTH-101", bx, a, b, "12-03-25", t542)
    for bx in range(1, 13):
        a, b = (bx - 1) * 3.8, bx * 3.8
        box_photo(foto / "LTH-102" / f"LTH-102_Box{bx}_{a:.2f}-{b:.2f}.jpg", "LTH-102", bx, a, b, "03-02-19", GEO_543)
    shutil.copy(REAL, foto / "IMG_0001.jpg")

    # ---- collar & survey (format berbeda-beda, sengaja)
    (lab / "Collar_Z3.csv").write_text("BHID;Easting;Northing;RL;EOH;Dip;Azi\n"
                                       "LTH-101;1050,0;2100,0;312,4;80;-60;135\n"
                                       "LTH-102;1100,0;2080,0;305,9;80;-90;0\n", encoding="utf-8")
    (lab / "Survey_Z3.csv").write_text("Hole_ID,Depth,Inclination,Bearing\nLTH-101,0,-60,135\nLTH-101,40,-58,137\nLTH-101,80,-55,140\n"
                                       "LTH-102,0,-90,0\nLTH-102,80,-88,10\n", encoding="utf-8")

    # ---- assay
    def au(hole, f):
        if hole == "LTH-101":
            if 36.8 <= f < 41.2:
                return rnd.choice([1.2, 2.8, 3.6, 4.8, 7.5, 12.4])
            if 30.5 <= f < 36.8:
                return rnd.choice([0.15, 0.32, 0.6, 0.9])
        if hole == "LTH-102" and 19 <= f < 23.5:
            return rnd.choice([0.4, 0.7, 1.1, 1.6])
        return rnd.choice(["<0.01", 0.01, 0.02, 0.05, 0.08])

    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Assay Lab"
    ws.append(["LAPORAN HASIL ANALISA - LAB SITE (FIKTIF, UNTUK LATIHAN)"])
    ws["A1"].font = Font(bold=True)
    ws.append(["Metode: Fire Assay 30 g (Au), AAS (Ag, Cu)"])
    ws.append(["Hole ID", "Depth From", "Depth To", "Sample No", "Au (ppm)", "Ag (ppm)", "Cu (%)", "Lab_Stat"])
    n = 0
    a543 = []
    for hole, end in (("LTH-101", 44.0), ("LTH-102", 45.6)):
        f = 0.0
        while f < end - 1e-6:
            t = round(min(end, f + rnd.choice([1.0, 1.0, 1.5, 0.8])), 2)
            n += 1
            row = [hole, round(f, 2), t, f"Z3-{n:04d}", au(hole, f), round(rnd.uniform(0.5, 30), 1), round(rnd.uniform(0.004, 0.3), 3), "Final"]
            ws.append(row)
            if hole == "LTH-102":
                a543.append(row)
            f = t
    for col, w in zip("ABCDEFGH", (11, 11, 10, 11, 10, 10, 9, 9)):
        ws.column_dimensions[col].width = w
    wb.save(lab / "Assay_Z3.xlsx")
    # assay ulang LTH-102: zona 19-23.5 m dianalisa ulang (lebih tinggi), format CSV titik koma + koma desimal
    lines = ["Hole ID;Depth From;Depth To;Sample No;Au (ppm);Ag (ppm);Cu (%);Lab_Stat"]
    for r in a543:
        v = r[4]
        if 19 <= r[1] < 23.5:
            v = round(float(v) * 1.8 + 0.3, 2)
        lines.append(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x) for x in [r[0], r[1], r[2], r[3] + "R", v, r[5], r[6], "Final-ulang"]))
    (lab / "Assay_LTH-102_ulang.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- logging geologi: hanya LTH-101 (LTH-102 belum dilogging -> AI mengisi isian geologi)
    g = ["HoleID\tFrom\tTo\tLith\tAlt_Int\tOx\tMineralogy\tVein_Type\tLogged_By"]
    for fr, to, li, al, ox, mi, ve, _c, _r in GEO:
        if fr < 44:
            g.append(f"LTH-101\t{fr}\t{min(to, 44.0)}\t{li}\t{al}\t{ox}\t{mi}\t{ve}\tHabil")
    (lab / "Geologi_Z3.txt").write_text("\n".join(g) + "\n", encoding="utf-8")

    # ---- proyek dashboard lama (Gemini)
    old_items = [{"id": 1, "status": "done", "fileName": "LTH-102_Box1_0.00-3.80.jpg", "holeId": "LTH-102", "boxNo": "1", "fromM": 0, "toM": 3.8,
                  "color": "Coklat kemerahan (Reddish Brown)", "weathering": "W3 (Moderately Weathered)", "oxidation": "Strongly Oxidized",
                  "condition": "WET", "recoveryPct": 82, "rqdPct": 35, "gsi": "35-45", "rmr": 41, "notes": "Zona oksidasi, core banyak pecah."},
                 {"id": 2, "status": "done", "fileName": "LTH-102_Box2_3.80-7.60.jpg", "holeId": "LTH-102", "boxNo": "2", "fromM": 3.8, "toM": 7.6,
                  "color": "Coklat (Brown)", "weathering": "W2 (Slightly Weathered)", "oxidation": "Moderately Oxidized",
                  "condition": "WET", "recoveryPct": 90, "rqdPct": 55, "gsi": "45-55", "rmr": 52, "notes": "Rekahan sedang."}]
    (old / "Geotech_Dashboard_LTH-102.json").write_text(json.dumps({"projectName": "Geotech_Dashboard_LTH-102", "savedAt": "2026-10-20T08:00:00Z",
                                                                    "data": old_items}, indent=2), encoding="utf-8")
    (OUT / "BACA_SAYA.txt").write_text(
        "DATA DUMMY TUTORIAL GC-Ex Core Interpretation (fiktif, hanya untuk latihan)\n\n"
        "Foto_Core/        buka folder ini di GC-Ex (Buka folder). 23 foto sintetis + 1 foto asli (IMG_0001.jpg).\n"
        "Data_Lab/         import lewat tombol Data bor:\n"
        "   Collar_Z3.csv             -> tab Collar   (pemisah titik koma, koma desimal)\n"
        "   Survey_Z3.csv             -> tab Survey\n"
        "   Assay_Z3.xlsx             -> tab Assay    (header di baris 3; Au (ppm) dll; ada nilai <0.01)\n"
        "   Geologi_Z3.txt            -> tab Geologi  (hanya LTH-101; LTH-102 belum dilogging)\n"
        "   Assay_LTH-102_ulang.csv -> tab Assay, cara 'Tambah / perbarui per hole' (latihan data baru)\n"
        "Dashboard_lama/   latihan tombol JSON (impor proyek dashboard lama)\n\n"
        "Kunci: LTH-101 zona QV 36.8-41.2 m berkadar tinggi (Au s.d. 12.4 g/t); IMG_0001 = LTH-101 box 11 (36.30-40.10 m).\n",
        encoding="utf-8")
    print("OK", OUT, sum(1 for _ in OUT.rglob("*.jpg")), "foto")


if __name__ == "__main__":
    main()
