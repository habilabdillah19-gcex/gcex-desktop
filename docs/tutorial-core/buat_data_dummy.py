"""Buat paket data dummy tutorial DB-Ex.

Pemakaian: python docs/tutorial-core/buat_data_dummy.py <folder_keluaran>

SEMUA ISI FIKTIF (perusahaan, lubang bor, koordinat, tanggal, kadar, foto), aman dibagikan ke pihak luar.
Tidak ada foto atau data proyek nyata di dalam paket.

Isi:
  Foto_Core/LTH-101/   11 foto core box sintetis (box 1-10, 12), nama file berpola Hole_Box_From-To
  Foto_Core/LTH-102/   12 foto core box sintetis
  Foto_Core/IMG_0001.jpg  foto core box sintetis bergaya foto HP (LTH-101 box 11, 36.30-40.10 m) dengan nama file
                          tanpa info, untuk latihan AI membaca papan label
  Data_Lab/Collar_Latihan.csv              titik koma, koma desimal, header BHID / Easting / Northing / RL / EOH
  Data_Lab/Survey_Latihan.csv              header Hole_ID / Depth / Inclination / Bearing
  Data_Lab/Assay_Latihan.xlsx              2 baris judul laporan di atas header, Au (ppm) dengan nilai <0.01, kolom Lab_Stat
  Data_Lab/Geologi_Latihan.txt             tab, hanya LTH-101 (LTH-102 belum dilogging): Lith, Alt_Int, Ox, Mineralogy, Vein_Type
  Data_Lab/Assay_Latihan_LTH-102_ulang.csv  hasil assay ulang LTH-102 (latihan tambah / perbarui per hole)
  Dashboard_lama/Geotech_Dashboard_LTH-102.json  file proyek dashboard lama (Gemini), latihan Impor JSON
  Foto_Singkapan/  foto dinding trench sintetis + tabel sampel channel (tutorial bab 12, DB-Ex versi Qt)
  QAQC/            workbook QAQC fiktif (Master_CRM, Assay_Import, CRM_Data, Blank_Data, Duplicate_Data) (bab 17-18)
  Borang/          scan borang fiktif Ore Spotter loading pit, ROM / crusher, Daily Drilling Report (+ PDF 3 halaman) (bab 13-16)
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(sys.argv[1]) if __name__ == "__main__" else None
rnd = random.Random(20261028)
COMPANY = "PT. CONTOH TAMBANG (FIKTIF)"
H1, H2 = "LTH-101", "LTH-102"
START, DATE1, DATE2 = "05-03-25", "12-03-25", "20-03-25"


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
    d.text((W // 2, 56), COMPANY, fill=(25, 25, 25), font=FB, anchor="mm")
    for (x, y, t) in [(56, 128, f"HOLE ID:{hole}"), (840, 128, "START DRILL:" + START), (56, 200, f"BOX    :{bx}"),
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


def phone_photo(path, hole, bx, a, b):
    """Foto core box sintetis bergaya foto HP: papan label tulisan spidol agak miring, core basah abu gelap,
    baki logam, papan catur skala; resolusi kecil & sedikit buram. Memakai Random sendiri supaya urutan acak
    data lain (kadar, foto lain) tidak berubah."""
    from PIL import ImageFilter
    r = random.Random(11)
    W, H = 1280, 960
    im = Image.new("RGB", (W, H), (118, 110, 98))
    d = ImageDraw.Draw(im)
    # papan label putih kusam
    d.rectangle([20, 10, W - 20, 330], fill=(226, 226, 220), outline=(60, 60, 60), width=6)
    for _ in range(260):  # noda / bekas hapus spidol
        x, y = r.randint(30, W - 30), r.randint(20, 320)
        g = r.randint(195, 225)
        d.ellipse([x, y, x + r.randint(4, 30), y + r.randint(2, 10)], fill=(g, g, g - 4))
    FH = font(46, True)
    board = [((W // 2, 52), COMPANY, "mm"), ((40, 125), "HOLE ID:" + hole, "lm"), ((640, 125), "START DRILL:" + START, "lm"),
             ((40, 200), "BOX  :" + str(bx), "lm"), ((640, 200), "DATE POTO:" + DATE1, "lm"),
             ((40, 280), "DEPTH:%.2f" % a, "lm"), ((440, 280), "M:TO:%.2f" % b, "lm"), ((830, 280), "M:CONDT:", "lm")]
    for (xy, t, anc) in board:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(xy, t, fill=(30, 30, 34, 235), font=FH, anchor=anc)
        layer = layer.rotate(r.uniform(-1.2, 1.2), center=xy)
        im.paste(layer, (0, 0), layer)
    d.rectangle([1090, 245, 1240, 318], outline=(30, 30, 34), width=5)
    d.text((1165, 282), "WET", fill=(30, 30, 34), font=FH, anchor="mm")
    # baki logam & 4 baris core basah
    d.rectangle([24, 345, W - 24, 860], fill=(176, 178, 180), outline=(120, 120, 120), width=4)
    for row in range(4):
        y = 360 + row * 125
        d.rectangle([36, y, W - 36, y + 112], fill=(28, 30, 31))
        x = 40
        while x < W - 46:
            L = int(r.uniform(40, 260))
            g = r.randint(48, 66)
            d.rounded_rectangle([x, y + 10, min(W - 40, x + L), y + 102], 40, fill=(g, g + 2, g + 3))
            d.line([x + 8, y + 26, min(W - 48, x + L - 8), y + 26], fill=(118, 122, 126), width=4)  # kilap basah
            if r.random() < .35:
                q = x + r.randint(5, max(6, L - 5))
                d.line([q, y + 10, q + r.randint(-20, 20), y + 102], fill=(150, 150, 146), width=3)
            x += L + r.randint(2, 10)
        if row in (1, 3):
            d.rectangle([620, y + 22, 650, y + 90], fill=(236, 236, 230))
    for i in range(0, W, 80):
        for j, yy in enumerate([872, 916]):
            d.rectangle([i, yy, i + 80, yy + 44], fill=(22, 22, 22) if (i // 80 + j) % 2 else (230, 230, 225))
    im = im.rotate(1.3, resample=Image.BICUBIC, fillcolor=(90, 86, 80))
    im = im.filter(ImageFilter.GaussianBlur(1.1)).resize((640, 480), Image.LANCZOS)
    px = im.load()
    for _ in range(9000):  # derau sensor HP
        x, y = r.randrange(640), r.randrange(480)
        c = px[x, y]
        n = r.randint(-14, 14)
        px[x, y] = tuple(max(0, min(255, v + n)) for v in c)
    im.save(path, quality=72)


# ================================================================ data latihan DB-Ex versi Qt (Singkapan & Borang, bab 12-16)
rq = random.Random(20261101)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_I = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(path, size):
    for p in (path, path.replace("/usr/share/fonts/truetype/dejavu/", "C:/Windows/Fonts/").replace("DejaVuSans-Oblique", "ariali")
              .replace("DejaVuSans-Bold", "arialbd").replace("DejaVuSans", "arial")):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def hand(dr, xy, text, size=26, color=(25, 40, 140)):
    """Tulisan 'tangan': miring biru, posisi tiap huruf sedikit bergoyang."""
    x, y = xy
    fo = f(FONT_I, size)
    for ch in str(text):
        dr.text((x + rq.uniform(-1, 1), y + rq.uniform(-1.5, 1.5)), ch, fill=color, font=fo)
        x += dr.textlength(ch, font=fo) * rq.uniform(0.96, 1.08)


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


def wall_photo(p: Path) -> None:
    """Dinding pit sintetis untuk analisis foto: andesit propilitik, zona oksida (limonit), vein kuarsa miring dan dua set
    kekar (curam ke kanan ~65°, landai ~160°) dengan spasi teratur — kunci jawaban tutorial bab Analisis foto."""
    W, H = 1800, 1200
    yy, xx = np.mgrid[0:H, 0:W]
    rng = np.random.default_rng(11)
    noise = rng.normal(0, 1, (H // 5, W // 5))
    noise = np.array(Image.fromarray(((noise - noise.min()) / np.ptp(noise) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)) / 255
    img = np.zeros((H, W, 3), np.float32)
    img[:] = (104, 116, 98)                                   # andesit propilitik hijau keabuan
    oks = (xx < 640 + 0.35 * (yy - 600) + 60 * np.sin(yy / 140.0))
    img[oks] = (150, 96, 52)                                  # zona oksida limonit di kiri
    vein = np.abs(yy - (300 + 0.42 * xx)) < 11
    img[vein] = (236, 234, 226)                               # vein kuarsa
    img *= (0.80 + 0.36 * noise[..., None])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    dr = ImageDraw.Draw(im)
    for c in range(-6, 14):                                   # set 1: curam (~65° dari mendatar), spasi ~150 px
        x0 = 120 + c * 150
        dr.line([(x0, H), (x0 + H / math.tan(math.radians(65)), 0)], fill=(38, 40, 36), width=3)
    for c in range(0, 9):                                     # set 2: landai (~20° turun ke kanan), spasi ~170 px
        y0 = 80 + c * 170
        dr.line([(0, y0), (W, y0 + W * math.tan(math.radians(20)))], fill=(44, 46, 40), width=2)
    for i in range(5):                                        # pita ukur georef di dinding
        dr.rectangle([200 + i * 340, 1150, 260 + i * 340, 1170], fill=(230, 60, 160))
    im.save(p, quality=90)


def with_gps(src: Path, dst: Path, lat: float, lon: float, alt: float, heading: float, hacc: float, taken: str,
             camera: str = "iPhone 17 Pro") -> None:
    """Salin foto dengan metadata GPS gaya iPhone (lintang / bujur / ketinggian / arah hadap / ketelitian / waktu).
    Dipakai untuk data latihan Lokasi foto (koordinat FIKTIF) dan uji otomatis."""
    from PIL.TiffImagePlugin import IFDRational

    def dms(v):
        v = abs(v)
        d = int(v)
        m = int((v - d) * 60)
        sec = (v - d - m / 60) * 3600
        return (IFDRational(d, 1), IFDRational(m, 1), IFDRational(round(sec * 10000), 10000))
    with Image.open(src) as im:
        im = im.convert("RGB")
        ex = Image.Exif()
        ex[271], ex[272] = "Apple", camera
        ex[306] = taken.replace("-", ":")
        sub = ex.get_ifd(0x8769)
        sub[36867] = taken.replace("-", ":")
        sub[36881] = "+08:00"
        sub[0xA405] = 24
        sub[0xA434] = f"{camera} back triple camera 6.86mm f/1.78"
        g = ex.get_ifd(0x8825)
        g[1], g[2] = ("S" if lat < 0 else "N"), dms(lat)
        g[3], g[4] = ("W" if lon < 0 else "E"), dms(lon)
        g[5], g[6] = b"\x00", IFDRational(round(alt * 100), 100)
        g[16], g[17] = "T", IFDRational(round(heading * 100), 100)
        g[31] = IFDRational(round(hacc * 100), 100)
        im.save(dst, quality=90, exif=ex)


# ================================================================ data latihan Model 3D (fotogrametri, bab 21)
# Dinding pit FIKTIF berbentuk zig-zag (empat bidang tegak) dengan tekstur foto dinding pit generik, satu vein
# kuarsa (bidang) dan satu set kekar (bidang sejajar), lima titik cat RTK. Difoto dari 10 posisi sambil berjalan sejajar
# dinding (kamera virtual 24 mm). Koordinat lokal digeser ke UTM 50S fiktif (laut).
M3D_ORIGIN = (533500.0, 9391900.0, 300.0)        # E, N, RL titik (0, 0, 0) model
M3D_PLAN = [(0.0, 0.0), (8.0, 0.0), (14.0, 3.5), (21.0, -1.0), (30.0, 0.0)]   # jejak kaki dinding (x timur, y utara)
M3D_H, M3D_LEAN = 10.0, 90.0                      # tinggi dinding (m), kemiringan muka dinding (tegak: sudut zig-zag rapat)
M3D_VEIN = {"dip": 62.0, "ddir": 120.0, "p": (15.0, 1.0, 5.0), "w": 0.22}      # kunci jawaban vein
M3D_JOINT = {"dip": 78.0, "ddir": 255.0, "p": (3.0, 0.0, 2.0), "w": 0.035, "spacing": 3.2}
M3D_GCP = [("RTK01", 2.0, 1.5), ("RTK02", 9.0, 7.5), ("RTK03", 14.5, 2.0), ("RTK04", 21.0, 8.0), ("RTK05", 28.0, 2.5)]  # (nama, jarak sepanjang dinding, tinggi)


def _m3d_facets():
    """Bidang dinding: titik bawah A, B (kaki dinding) dan vektor ke atas (condong ke belakang / menjauhi kamera)."""
    out, s0 = [], 0.0
    t = 1 / math.tan(math.radians(M3D_LEAN))
    for (x0, y0), (x1, y1) in zip(M3D_PLAN, M3D_PLAN[1:]):
        A, B = np.array([x0, y0, 0.0]), np.array([x1, y1, 0.0])
        d = B - A
        L = float(np.linalg.norm(d))
        nrm = np.array([-d[1], d[0], 0.0]) / L       # normal mendatar menghadap utara (menjauhi kamera di selatan)
        up = np.array([0, 0, 1.0]) + nrm * t
        out.append({"A": A, "B": B, "L": L, "up": up, "s0": s0})
        s0 += L
    return out


def _plane(dip: float, ddir: float, p) -> tuple:
    """Normal satuan bidang geologi (mengarah ke atas) dari dip / arah dip, dan titik di bidang."""
    d, a = math.radians(dip), math.radians(ddir)
    n = np.array([math.sin(d) * math.sin(a), math.sin(d) * math.cos(a), math.cos(d)])
    return n, np.array(p, float)


def m3d_point(s: float, z: float) -> np.ndarray:
    """Titik di permukaan dinding dari jarak sepanjang kaki dinding s dan tinggi z."""
    for f in _m3d_facets():
        if s <= f["s0"] + f["L"] or f is _m3d_facets()[-1]:
            u = (s - f["s0"]) / f["L"]
            return f["A"] + u * (f["B"] - f["A"]) + f["up"] * z
    raise ValueError


def _m3d_texture(tex: np.ndarray, S: np.ndarray, Z: np.ndarray, P: np.ndarray) -> np.ndarray:
    """Warna permukaan di titik dunia P (… x 3) dengan koordinat dinding (S, Z): tekstur + vein + kekar + titik cat."""
    th, tw = tex.shape[:2]
    total = sum(f["L"] for f in _m3d_facets())
    u = np.clip(S / total * (tw - 1), 0, tw - 1)
    v = np.clip((1 - Z / M3D_H) * (th - 1), 0, th - 1)
    col = tex[v.astype(int), u.astype(int)].astype(np.float32)
    nv, pv = _plane(M3D_VEIN["dip"], M3D_VEIN["ddir"], M3D_VEIN["p"])
    dv = np.abs((P - pv) @ nv)
    vein = dv < M3D_VEIN["w"] / 2
    col[vein] = col[vein] * 0.15 + np.array([236, 232, 220], np.float32) * 0.85
    halo = (dv >= M3D_VEIN["w"] / 2) & (dv < M3D_VEIN["w"] * 1.6)
    col[halo] = col[halo] * 0.55 + np.array([170, 105, 50], np.float32) * 0.45        # selubung oksida
    nj, pj = _plane(M3D_JOINT["dip"], M3D_JOINT["ddir"], M3D_JOINT["p"])
    dj = ((P - pj) @ nj) % M3D_JOINT["spacing"]
    joint = np.minimum(dj, M3D_JOINT["spacing"] - dj) < M3D_JOINT["w"] / 2
    col[joint] = col[joint] * 0.35
    for _n, gs, gz in M3D_GCP:
        g = m3d_point(gs, gz)
        dd = np.linalg.norm(P - g, axis=-1)
        col[dd < 0.16] = (235, 40, 170)
        col[(dd >= 0.16) & (dd < 0.20)] = (250, 250, 250)
    return col


def m3d_cameras(n: int = 10) -> list[dict]:
    """10 posisi kamera berjalan sejajar dinding (±10 m di selatan dinding), tinggi mata 1,6 m, menghadap utara ± sedikit."""
    cams = []
    for i in range(n):
        x = 1.5 + i * 27.0 / (n - 1)
        y = -10.5 + 0.8 * math.sin(i * 1.3)
        yaw = math.radians(-10 + 20 * (x - 1.5) / 27)        # sedikit menoleh ke tengah dinding
        pitch = math.radians(20.0)
        C = np.array([x, y, 1.6])
        fwd = np.array([math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
        right = np.cross(fwd, [0, 0, 1.0])
        right /= np.linalg.norm(right)
        down = np.cross(fwd, right)
        R = np.vstack([right, down, fwd])                   # baris = sumbu kamera (x kanan, y bawah, z depan) di dunia
        cams.append({"C": C, "R": R, "heading": (math.degrees(math.atan2(fwd[0], fwd[1])) + 360) % 360})
    return cams


def m3d_render(tex: np.ndarray, cam: dict, W: int = 1600, H: int = 1200, f35: float = 24.0) -> np.ndarray:
    """Render satu foto: sinar per piksel -> perpotongan terdekat dengan bidang dinding -> warna tekstur (+ langit / lantai)."""
    f = f35 / 36.0 * W
    jj, ii = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    dirs_c = np.stack([(jj - W / 2) / f, (ii - H / 2) / f, np.ones_like(jj)], -1)
    D = dirs_c @ cam["R"]                                  # ke dunia
    C = cam["C"]
    best = np.full((H, W), np.inf, np.float32)
    S = np.zeros((H, W), np.float32)
    Z = np.zeros((H, W), np.float32)
    for fc in _m3d_facets():
        e1 = (fc["B"] - fc["A"]) / fc["L"]
        n = np.cross(e1, fc["up"])
        n /= np.linalg.norm(n)
        den = D @ n
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((fc["A"] - C) @ n) / den
        P = C + D * t[..., None]
        rel = P - fc["A"]
        z = rel[..., 2] / fc["up"][2]
        u = (rel - z[..., None] * fc["up"]) @ e1
        ok = (t > 0) & (u >= -1e-3) & (u <= fc["L"] + 1e-3) & (z >= 0) & (z <= M3D_H) & (t < best)
        best[ok] = t[ok]
        S[ok] = fc["s0"] + u[ok]
        Z[ok] = z[ok]
    hit = np.isfinite(best)
    img = np.zeros((H, W, 3), np.float32)
    P = C + D * np.where(hit, best, 0)[..., None]
    img[hit] = _m3d_texture(tex, S[hit], Z[hit], P[hit])
    sky = (~hit) & (D[..., 2] > 0)
    img[sky] = np.array([150, 185, 225], np.float32) * (0.85 + 0.15 * (ii[sky] / H))[:, None]
    gnd = (~hit) & (D[..., 2] <= 0)
    tg = -C[2] / np.minimum(D[gnd][:, 2], -1e-6)
    G = C + D[gnd] * tg[:, None]
    rng = np.random.default_rng(3)
    gn = rng.normal(0, 1, (64, 64)).astype(np.float32)
    gidx = ((G[:, 0] * 6).astype(int) % 64, (G[:, 1] * 6).astype(int) % 64)
    img[gnd] = (np.array([128, 122, 112], np.float32) * (0.85 + 0.08 * gn[gidx][:, None]))
    yy = (ii - H / 2) / H
    xx = (jj - W / 2) / W
    img *= (1 - 0.18 * (xx ** 2 + yy ** 2))[..., None]        # vinyet lensa
    img += rng.normal(0, 2.0, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def utm_to_ll(E: float, N: float, zone: int = 50, south: bool = True) -> tuple[float, float]:
    """UTM -> lintang / bujur (iterasi Newton memakai fungsi maju core_oclokasi; cukup untuk metadata latihan)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
    from gcex_backend.core_oclokasi import to_utm
    lat, lon = (N - (10000000 if south else 0)) / 110574.0, zone * 6 - 183 + (E - 500000) / 111320.0
    for _ in range(8):
        e, n, _z, _s = to_utm(lat, lon, zone, south)
        lat += (N - n) / 110574.0
        lon += (E - e) / (111320.0 * math.cos(math.radians(lat)))
    return lat, lon


def model3d_data(out: Path, n: int = 10, W: int = 1600, H: int = 1200) -> Path:
    """Folder Model_3D/Dinding_M01: 10 foto (metadata GPS fiktif ±3–6 m) + Titik_RTK_Dinding_M01.csv (koordinat titik cat)."""
    d = out / "Model_3D" / "Dinding_M01"
    d.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve().parent / "aset" / "Dinding_Pit_C.jpg"
    tex = np.asarray(Image.open(src).convert("RGB"))
    tex = tex[int(tex.shape[0] * 0.25):int(tex.shape[0] * 0.75)]          # pita tengah foto: batuan bertekstur
    tex = np.asarray(Image.fromarray(tex).resize((3000, 1000)))
    E0, N0, RL0 = M3D_ORIGIN
    rng = np.random.default_rng(21)
    for i, cam in enumerate(m3d_cameras(n), 1):
        im = Image.fromarray(m3d_render(tex, cam, W, H))
        tmp = d / f"_tmp_{i}.jpg"
        im.save(tmp, quality=92)
        e = E0 + cam["C"][0] + rng.normal(0, 3)
        nn = N0 + cam["C"][1] + rng.normal(0, 3)
        lat, lon = utm_to_ll(e, nn)
        with_gps(tmp, d / f"IMG_{7100 + i:04d}.jpg", lat, lon, RL0 + cam["C"][2] + rng.normal(0, 4), cam["heading"],
                 round(float(rng.uniform(3, 6)), 1), f"2026-11-02 09:{10 + i:02d}:00")
        tmp.unlink()
    rows = ["Nama,E,N,RL"]
    for nm, gs, gz in M3D_GCP:
        g = m3d_point(gs, gz)
        rows.append(f"{nm},{E0 + g[0]:.3f},{N0 + g[1]:.3f},{RL0 + g[2]:.3f}")
    (d / "Titik_RTK_Dinding_M01.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (d / "KUNCI_JAWABAN.txt").write_text(
        "Model 3D latihan (FIKTIF)\n"
        f"Vein kuarsa : dip {M3D_VEIN['dip']:.0f}° ke arah {M3D_VEIN['ddir']:.0f}° (strike {(M3D_VEIN['ddir'] - 90) % 360:.0f}°, aturan tangan kanan)\n"
        f"Set kekar   : dip {M3D_JOINT['dip']:.0f}° ke arah {M3D_JOINT['ddir']:.0f}°, spasi {M3D_JOINT['spacing']:.1f} m\n"
        "Muka dinding: tegak, zig-zag empat bidang\n", encoding="utf-8")
    return d


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




# sampel channel latihan di foto dinding pit B (kadar fiktif): oksida, andesit segar, vein hematit, dinding kanan
SAMPEL_PIT_B = [("CH-B-01", 0, 4, "0,21", 3), ("CH-B-02", 4, 8.4, "0,48", 5), ("CH-B-03", 8.4, 9.6, "6,4", 21), ("CH-B-04", 9.6, 12, "1,85", 9)]


def qt_data(out: Path) -> None:
    """Foto dinding pit generik (aset/) + tabel sampel channel fiktif, dan scan borang fiktif (JPG + satu PDF tiga halaman)."""
    sk = out / "Foto_Singkapan"
    sk.mkdir(parents=True, exist_ok=True)
    # foto dinding pit generik (metadata asli dibuang); diberi metadata GPS gaya iPhone dengan koordinat FIKTIF (laut, UTM 50S)
    # untuk latihan Lokasi kamera (bab 20)
    for n, lat, lon, alt, hd, acc, t in (("Dinding_Pit_A.jpg", -5.50120, 117.30210, 312.4, 285.0, 6.5, "2026-10-30 09:15:00"),
                                         ("Dinding_Pit_B.jpg", -5.50245, 117.30330, 298.7, 12.0, 4.8, "2026-10-30 10:02:00"),
                                         ("Dinding_Pit_C.jpg", -5.50060, 117.30455, 305.2, 205.0, 9.1, "2026-10-31 08:41:00")):
        with_gps(Path(__file__).resolve().parent / "aset" / n, sk / n, lat, lon, alt, hd, acc, t)
    model3d_data(out)
    (sk / "Sampel_Channel_Pit_B.txt").write_text("Sample ID\tDari\tKe\tAu (ppm)\tAg_ppm\n" + "".join(
        f"{a}\t{str(b).replace('.', ',')}\t{str(c).replace('.', ',')}\t{au}\t{ag}\n" for a, b, c, au, ag in SAMPEL_PIT_B), encoding="utf-8")
    bo = out / "Borang"
    bo.mkdir(exist_ok=True)
    form_pit(bo / "Borang_Loading_Pit_30Okt.jpg")
    form_rom(bo / "Borang_ROM_31Okt.jpg")
    form_ddr(bo / "DDR_31Okt.jpg")
    pages = [Image.open(bo / n).convert("RGB") for n in ("Borang_Loading_Pit_30Okt.jpg", "Borang_ROM_31Okt.jpg", "DDR_31Okt.jpg")]
    pages[0].save(bo / "Borang_Latihan_3_halaman.pdf", "PDF", resolution=200, save_all=True, append_images=pages[1:])



# ================================================================ data latihan QAQC (ruang kerja QAQC, bab 17-18)
def qaqc_data(out: Path) -> Path:
    """Workbook QAQC fiktif dengan sheet seperti workbook QAQC kantor: Master_CRM, Assay_Import, CRM_Data, Blank_Data, Duplicate_Data.
    Zona fiktif Z7 dan Z8, CRM fiktif CRM-A / CRM-B, batch LAB26xxx. Disisipkan sengaja: CRM WARNING / FAIL (termasuk satu CRM
    tertukar), blank terkontaminasi, duplikat lapangan yang lebih buruk daripada pulp, dan satu Sample_ID ganda."""
    from openpyxl import Workbook
    rg = np.random.default_rng(20261104)
    crm = {"CRM-A": (0.512, 0.015), "CRM-B": (1.48, 0.042), "CRM-C": (0.195, 0.009)}
    wb = Workbook()
    ws = wb.active
    ws.title = "Master_CRM"
    ws.append(["Standard_Name", "Certified_Mean", "Certified_SD", "Supplier", "Lot_Number"])
    for i, (k, (m, sd)) in enumerate(crm.items(), 1):
        ws.append([k, m, sd, "Pemasok Fiktif", i])
    assay, crm_rows, blank_rows, dup_rows = [], [], [], []
    n = 0
    for zi, zone in enumerate(("Z7", "Z8")):
        for b in range(12):
            batch = f"LAB26{zi}{b:02d}"
            hole = f"{zone}_210_{b + 1:02d}"
            for j in range(40):
                n += 1
                sid = f"LT_{n:05d}_{zone}"
                if j % 20 == 9:  # CRM
                    std = ("CRM-A", "CRM-B", "CRM-C")[(b + j // 20) % 3]
                    m, sd = crm[std]
                    v = m + rg.normal(0, sd * 0.9)
                    if zone == "Z8" and std == "CRM-A" and b in (3, 6) and j == 9:
                        v = crm["CRM-B"][0] + rg.normal(0, 0.02)  # CRM tertukar (tercatat CRM-A, nilai CRM-B)
                    if zone == "Z7" and b in (2, 7) and j == 29:
                        v = m + 2.4 * sd
                    if zone == "Z7" and b == 10 and j == 9:
                        v = m - 3.6 * sd
                    crm_rows.append([sid, std, round(v, 3)])
                    assay.append([batch, hole, sid, "Standard", round(v, 3)])
                elif j % 20 == 10:  # blank setelah CRM
                    v = 0.005 if rg.random() > 0.06 else round(float(rg.choice([0.02, 0.03, 0.05, 0.12])), 3)
                    blank_rows.append([sid, "Blank", v])
                    assay.append([batch, hole, sid, "Blank", v])
                elif j % 20 == 19:  # duplikat dari sampel sebelumnya
                    tipe = ("Lapangan", "Coarse", "Pulp")[(b + j // 20) % 3]
                    o = float(np.round(np.exp(rg.normal(-1.8, 1.1)), 3))
                    err = {"Lapangan": 0.42, "Coarse": 0.16, "Pulp": 0.05}[tipe]
                    d = max(0.005, round(o * float(np.exp(rg.normal(0, err))), 3))
                    oid = f"LT_{n - 1:05d}_{zone}"
                    dup_rows.append([oid, sid, max(0.005, round(o, 3)), d, zone, tipe])
                    assay.append([batch, hole, sid, "Duplicate", d])
    blank_rows.append(list(blank_rows[3]))  # Sample_ID ganda (latihan laporan impor)
    for title, heads, rows in (("Assay_Import", ["Batch_ID", "Hole_ID", "Sample_ID", "Sample_Type", "Lab_Au_ppm", "Zona"],
                                [r + [r[1][:2]] for r in assay]),
                               ("CRM_Data", ["Sample_ID", "Standard_Name", "Lab_Grade"], crm_rows),
                               ("Duplicate_Data", ["Original_ID", "Duplicate_ID", "Original", "Duplicate", "Zona", "Tipe"], dup_rows),
                               ("Blank_Data", ["Sample_ID", "Standard_Name", "Lab_Grade"], blank_rows)):
        w = wb.create_sheet(title)
        w.append(heads)
        for r in rows:
            w.append(r)
    d = out / "QAQC"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "QAQC_Latihan.xlsx"
    wb.save(p)
    return p


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    foto, lab, old = OUT / "Foto_Core", OUT / "Data_Lab", OUT / "Dashboard_lama"
    for p in (foto / H1, foto / H2, lab, old):
        p.mkdir(parents=True)
    t542 = [(g[0], g[1], g[7], g[8]) for g in GEO]
    # LTH-101: box 1-10 rata 3.63 m sampai 36.30; box 11 = foto bergaya HP (IMG_0001) 36.30-40.10; box 12 40.10-43.90
    for bx in range(1, 13):
        if bx == 11:
            continue
        a, b = ((bx - 1) * 3.63, bx * 3.63) if bx <= 10 else (40.10, 43.90)
        box_photo(foto / H1 / f"{H1}_Box{bx}_{a:.2f}-{b:.2f}.jpg", H1, bx, a, b, DATE1, t542)
    for bx in range(1, 13):
        a, b = (bx - 1) * 3.8, bx * 3.8
        box_photo(foto / H2 / f"{H2}_Box{bx}_{a:.2f}-{b:.2f}.jpg", H2, bx, a, b, DATE2, GEO_543)
    phone_photo(foto / "IMG_0001.jpg", H1, 11, 36.30, 40.10)

    # ---- collar & survey (format berbeda-beda, sengaja)
    # koordinat grid lokal fiktif (bukan UTM lokasi nyata)
    (lab / "Collar_Latihan.csv").write_text("BHID;Easting;Northing;RL;EOH;Dip;Azi\n"
                                            f"{H1};10250,5;20410,2;312,4;80;-60;135\n"
                                            f"{H2};10300,1;20380,7;305,9;80;-90;0\n", encoding="utf-8")
    (lab / "Survey_Latihan.csv").write_text(f"Hole_ID,Depth,Inclination,Bearing\n{H1},0,-60,135\n{H1},40,-58,137\n{H1},80,-55,140\n"
                                            f"{H2},0,-90,0\n{H2},80,-88,10\n", encoding="utf-8")

    # ---- assay
    def au(hole, f):
        if hole == H1:
            if 36.8 <= f < 41.2:
                return rnd.choice([1.2, 2.8, 3.6, 4.8, 7.5, 12.4])
            if 30.5 <= f < 36.8:
                return rnd.choice([0.15, 0.32, 0.6, 0.9])
        if hole == H2 and 19 <= f < 23.5:
            return rnd.choice([0.4, 0.7, 1.1, 1.6])
        return rnd.choice(["<0.01", 0.01, 0.02, 0.05, 0.08])

    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Assay Lab"
    ws.append(["LAPORAN HASIL ANALISA - LAB CONTOH (FIKTIF, UNTUK LATIHAN)"])
    ws["A1"].font = Font(bold=True)
    ws.append(["Metode: Fire Assay 30 g (Au), AAS (Ag, Cu)"])
    ws.append(["Hole ID", "Depth From", "Depth To", "Sample No", "Au (ppm)", "Ag (ppm)", "Cu (%)", "Lab_Stat"])
    n = 0
    a543 = []
    for hole, end in ((H1, 44.0), (H2, 45.6)):
        f = 0.0
        while f < end - 1e-6:
            t = round(min(end, f + rnd.choice([1.0, 1.0, 1.5, 0.8])), 2)
            n += 1
            row = [hole, round(f, 2), t, f"LT-{n:04d}", au(hole, f), round(rnd.uniform(0.5, 30), 1), round(rnd.uniform(0.004, 0.3), 3), "Final"]
            ws.append(row)
            if hole == H2:
                a543.append(row)
            f = t
    for col, w in zip("ABCDEFGH", (11, 11, 10, 11, 10, 10, 9, 9)):
        ws.column_dimensions[col].width = w
    wb.save(lab / "Assay_Latihan.xlsx")
    # assay ulang LTH-102: zona 19-23.5 m dianalisa ulang (lebih tinggi), format CSV titik koma + koma desimal
    lines = ["Hole ID;Depth From;Depth To;Sample No;Au (ppm);Ag (ppm);Cu (%);Lab_Stat"]
    for r in a543:
        v = r[4]
        if 19 <= r[1] < 23.5:
            v = round(float(v) * 1.8 + 0.3, 2)
        lines.append(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x) for x in [r[0], r[1], r[2], r[3] + "R", v, r[5], r[6], "Final-ulang"]))
    (lab / f"Assay_Latihan_{H2}_ulang.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- logging geologi: hanya LTH-101 (LTH-102 belum dilogging -> AI mengisi isian geologi)
    g = ["HoleID\tFrom\tTo\tLith\tAlt_Int\tOx\tMineralogy\tVein_Type\tLogged_By"]
    for fr, to, li, al, ox, mi, ve, _c, _r in GEO:
        if fr < 44:
            g.append(f"{H1}\t{fr}\t{min(to, 44.0)}\t{li}\t{al}\t{ox}\t{mi}\t{ve}\tGeologist-01")
    (lab / "Geologi_Latihan.txt").write_text("\n".join(g) + "\n", encoding="utf-8")

    # ---- proyek dashboard lama (Gemini)
    old_items = [{"id": 1, "status": "done", "fileName": f"{H2}_Box1_0.00-3.80.jpg", "holeId": H2, "boxNo": "1", "fromM": 0, "toM": 3.8,
                  "color": "Coklat kemerahan (Reddish Brown)", "weathering": "W3 (Moderately Weathered)", "oxidation": "Strongly Oxidized",
                  "condition": "WET", "recoveryPct": 82, "rqdPct": 35, "gsi": "35-45", "rmr": 41, "notes": "Zona oksidasi, core banyak pecah."},
                 {"id": 2, "status": "done", "fileName": f"{H2}_Box2_3.80-7.60.jpg", "holeId": H2, "boxNo": "2", "fromM": 3.8, "toM": 7.6,
                  "color": "Coklat (Brown)", "weathering": "W2 (Slightly Weathered)", "oxidation": "Moderately Oxidized",
                  "condition": "WET", "recoveryPct": 90, "rqdPct": 55, "gsi": "45-55", "rmr": 52, "notes": "Rekahan sedang."}]
    (old / f"Geotech_Dashboard_{H2}.json").write_text(json.dumps({"projectName": f"Geotech_Dashboard_{H2}", "savedAt": "2026-10-20T08:00:00Z",
                                                                    "data": old_items}, indent=2), encoding="utf-8")
    qt_data(OUT)
    qaqc_data(OUT)
    (OUT / "BACA_SAYA.txt").write_text(
        "DATA DUMMY TUTORIAL DB-Ex\n"
        "SEMUA ISI FIKTIF: nama perusahaan, lubang bor, koordinat (grid lokal), tanggal, kadar dan foto dibuat\n"
        "untuk latihan. Tidak ada foto atau data proyek nyata. Aman dibagikan.\n\n"
        "Foto_Core/        buka folder ini di DB-Ex (Buka folder). 24 foto sintetis; IMG_0001.jpg bergaya foto HP.\n"
        "Data_Lab/         import lewat tombol Data bor:\n"
        "   Collar_Latihan.csv             -> tab Collar   (pemisah titik koma, koma desimal)\n"
        "   Survey_Latihan.csv             -> tab Survey\n"
        "   Assay_Latihan.xlsx             -> tab Assay    (header di baris 3; Au (ppm) dll; ada nilai <0.01)\n"
        "   Geologi_Latihan.txt            -> tab Geologi  (hanya LTH-101; LTH-102 belum dilogging)\n"
        "   Assay_Latihan_LTH-102_ulang.csv -> tab Assay, cara 'Tambah / perbarui per hole' (latihan data baru)\n"
        "Dashboard_lama/   latihan tombol JSON (impor proyek dashboard lama)\n"
        "--- DB-Ex versi Qt (tutorial bab 12-19) ---\n"
        "Foto_Singkapan/   foto dinding pit sungguhan (generik; metadata GPS gaya iPhone dengan koordinat FIKTIF, bab 20):\n"
        "   Dinding_Pit_B.jpg + Sampel_Channel_Pit_B.txt -> bab 12 Singkapan (digitasi, channel sampling, infografis)\n"
        "   Dinding_Pit_A.jpg -> bab 19 Analisis foto (peta oksida, jejak kekar & scanline, zona SAM)\n"
        "   Dinding_Pit_C.jpg -> latihan tambahan (zona argilik pucat, sesar miring, zona oksida atas)\n"
        "Model_3D/Dinding_M01/  10 foto dinding pit sintetis (zig-zag) + Titik_RTK_Dinding_M01.csv + KUNCI_JAWABAN.txt\n"
        "                  (Singkapan -> Model 3D: bangun, titik cat RTK, ukur strike / dip vein; bab 21)\n"
        "Borang/           scan borang fiktif (Borang -> + Borang):\n"
        "   Borang_Loading_Pit_30Okt.jpg   -> jenis Ore Spotter: Loading Pit -> ROM / Stockpile (shift II, lewat tengah malam)\n"
        "   Borang_ROM_31Okt.jpg           -> jenis Ore ke Stockpile / Crusher (Rehandling / Direct)\n"
        "   DDR_31Okt.jpg                  -> jenis RC Drilling: Daily Drilling Report\n"
        "   Borang_Latihan_3_halaman.pdf   -> ketiganya dalam satu PDF (DB-Ex memecah per halaman; pilih jenis tiap borang)\n"
        "QAQC/             QAQC_Latihan.xlsx (QAQC -> Workbook QAQC -> Impor): Master_CRM, Assay_Import, CRM_Data, Blank_Data,\n"
        "                  Duplicate_Data; zona fiktif Z7 / Z8, CRM fiktif CRM-A / CRM-B / CRM-C\n\n"
        "Kunci: LTH-101 zona QV 36.8-41.2 m berkadar tinggi (Au s.d. 12.4 g/t); IMG_0001 = LTH-101 box 11 (36.30-40.10 m).\n"
        "Copyright (c) Habil Abdillah 2026 - data latihan DB-Ex.\n",
        encoding="utf-8")
    print("OK", OUT, sum(1 for _ in OUT.rglob("*.jpg")), "foto")


if __name__ == "__main__":
    main()
