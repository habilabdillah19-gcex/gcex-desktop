"""Diagram & grafik untuk PDF 'Tentang Pit Studio for Desktop' (matplotlib, tanpa internet).
Pemakaian: python gambar.py <folder web-src-ps> <folder keluaran gambar>"""
import sys, os, glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NV, GD, AC, PN, LN, MU = "#1C2733", "#B5893E", "#2B5F9E", "#F7F5F0", "#D3CDC1", "#6b7280"
GR, KU, MR = "#2f9e44", "#e8a33d", "#c92a2a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": LN, "axes.labelcolor": NV,
                     "xtick.color": NV, "ytick.color": NV, "axes.spines.top": False, "axes.spines.right": False})
SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, t, fc="white", ec=NV, tc=NV, fs=8.6, bold=False, r=0.012, lw=1.1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.35)


def arr(ax, a, b, c=NV, st="-|>", lw=1.2, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=st, mutation_scale=11, color=c, lw=lw, linestyle=ls, shrinkA=0, shrinkB=0))


def canvas(w, h):
    f = plt.figure(figsize=(w, h), dpi=200)
    ax = f.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return f, ax


def save(f, n):
    f.savefig(os.path.join(OUT, n), dpi=200, facecolor="white"); plt.close(f)


# 1. Keluarga GC-Ex
f, ax = canvas(7.2, 3.0)
box(ax, 0.02, 0.80, 0.96, 0.15, "Keluarga GC-Ex — 5 aplikasi desktop Windows 64-bit, dipasang terpisah, satu pemilik hak cipta", fc=NV, ec=NV, tc="white", bold=True, fs=9)
apps = [("GC-Ex\nBlock Model", "estimasi\nblock model"), ("GC-Ex\nDrillhole", "data bor, AOI"), ("DB-Ex", "basis data geologi"),
        ("Ore Works", "pemetaan & model\nbijih 3D"), ("Pit Studio", "desain pit, jalan,\njadwal, G × T")]
for i, (a, d) in enumerate(apps):
    x = 0.02 + i * 0.196
    hl = a == "Pit Studio"
    box(ax, x, 0.40, 0.18, 0.32, a + "\n\n" + d, fc=GD if hl else "white", ec=GD if hl else NV, tc="white" if hl else NV, bold=False, fs=8.2, lw=1.8 if hl else 1.1)
box(ax, 0.02, 0.06, 0.465, 0.24, "Bersama: backend lokal Python (FastAPI / Uvicorn)\npembaca block model Surpac .mdl, cache", fc=PN, ec=LN, fs=8.2)
box(ax, 0.515, 0.06, 0.465, 0.24, "Bersama: satu file lisensi per komputer\n(tanda tangan Ed25519, %APPDATA%\\GC-Ex Lisensi)", fc=PN, ec=LN, fs=8.2)
for i in range(5):
    x = 0.02 + i * 0.196 + 0.09
    arr(ax, (x, 0.40), (x, 0.31), c=LN, st="-")
save(f, "d1_keluarga.png")

# 2. Arsitektur
f, ax = canvas(7.2, 4.3)
ax.add_patch(FancyBboxPatch((0.02, 0.03), 0.96, 0.94, boxstyle="round,pad=0,rounding_size=0.015", fc="#fbfaf7", ec=LN, lw=1, ls="--"))
ax.text(0.04, 0.935, "Komputer pengguna (Windows 64-bit) — tidak ada lalu lintas ke internet", color=MU, fontsize=8.2, style="italic")
ax.add_patch(FancyBboxPatch((0.04, 0.33), 0.60, 0.57, boxstyle="round,pad=0,rounding_size=0.012", fc="white", ec=AC, lw=1.4))
ax.text(0.06, 0.865, "Pit Studio.exe  (Electron · Chromium)", color=AC, fontsize=9, fontweight="bold")
box(ax, 0.06, 0.56, 0.56, 0.27, "Renderer — satu halaman app-ps/index.html (±2,9 MB)\n89 modul JavaScript · three.js (3D) · Clipper (poligon)\nDelaunator + TIN GC-Ex (permukaan presisi) · 4 bahasa", fc=PN, ec=LN, fs=8.1)
box(ax, 0.06, 0.36, 0.27, 0.15, "preload (contextIsolation,\nsandbox, tanpa Node)", fc="white", ec=LN, fs=7.8)
box(ax, 0.35, 0.36, 0.27, 0.15, "proses utama: menu, dialog,\nlisensi Ed25519, file lokal", fc="white", ec=LN, fs=7.8)
arr(ax, (0.195, 0.56), (0.195, 0.51), st="<|-|>"); arr(ax, (0.33, 0.435), (0.35, 0.435), st="<|-|>")
box(ax, 0.68, 0.62, 0.28, 0.28, "Backend lokal (Python)\nFastAPI / Uvicorn\n127.0.0.1 · port acak\n/mdl/open · /mdl/subset …", fc=PN, ec=GD, fs=8.1, lw=1.5)
arr(ax, (0.62, 0.47), (0.74, 0.62), c=GD, st="<|-|>")
ax.text(0.655, 0.555, "HTTP lokal", color=GD, fontsize=7.4)
box(ax, 0.68, 0.33, 0.15, 0.17, "File\nlisensi", fc="white", ec=LN, fs=7.8)
arr(ax, (0.62, 0.40), (0.68, 0.40), st="<|-|>")
fx = [("Topografi / string\n.str · .dxf", 0.04), ("Keluaran\n.str · .dxf · .csv · .png", 0.28), ("Proyek\n.json", 0.52), ("Block model\nSurpac .mdl", 0.76)]
for t, x in fx:
    box(ax, x, 0.07, 0.20, 0.16, t, fc="white", ec=NV, fs=7.9)
arr(ax, (0.14, 0.23), (0.14, 0.33), st="<|-|>"); arr(ax, (0.895, 0.23), (0.895, 0.62), c=GD, st="-|>", ls="--")
arr(ax, (0.38, 0.23), (0.45, 0.33), st="<|-"); arr(ax, (0.62, 0.23), (0.58, 0.33), st="<|-|>")
save(f, "d2_arsitektur.png")

# 3. Alur kerja
f, ax = canvas(7.2, 2.6)
st = [("1", "Data", "topografi\n.str / .dxf\nblock model .mdl"), ("2", "Pit final", "otomatis,\nterpandu, manual\n+ geoteknik"),
      ("3", "Jalan", "spiral,\nswitchback,\njalan luar"), ("4", "Staging &\nEdit", "fase bulanan,\nPlay-Doh, trim,\nperdalam"),
      ("5", "Grade ×\nTonnage", "otomatis tiap\ndesain berubah\n+ notifikasi"), ("6", "Pit\nSchedule", "bench × strip\n× blok, fleet,\nperiode, SR"),
      ("7", "Keluaran", "sayatan,\nlayout peta,\nstr/dxf/csv/png")]
w = 0.128
for i, (n, a, d) in enumerate(st):
    x = 0.012 + i * 0.141
    hl = n in ("5", "6")
    box(ax, x, 0.50, w, 0.34, a, fc=GD if hl else NV, ec=GD if hl else NV, tc="white", bold=True, fs=8.4)
    ax.text(x + 0.012, 0.79, n, color="white", fontsize=7, alpha=.8)
    ax.text(x + w / 2, 0.42, d, ha="center", va="top", fontsize=6.9, color=NV, linespacing=1.3)
    if i < 6:
        arr(ax, (x + w + 0.002, 0.67), (x + 0.141 - 0.002, 0.67), c=MU)
ax.text(0.5, 0.06, "Semua langkah berjalan offline; data contoh di installer bersifat fiktif.", ha="center", color=MU, fontsize=7.8, style="italic")
save(f, "d3_alur.png")

# 4. Komposisi kode sumber
G = {"Mesin desain pit & jalan": "a1 a3 a4 a5 a8 a9 a11 a13 a15 a16 a17 a18 a19 a21 a22 a23 a26 a51 a57 a62 a85 a88",
     "Edit, front bulanan & tolok ukur": "a6 a12 a14 a20 a27 a52 a54 a55 a56 a58 a65 a66 a86",
     "Pit Schedule & blok tambang": "a31 a39 a40 a41 a67 a68 a70 a78",
     "Block model, G × T & presisi": "a36 a38 a43 a46 a53 a60 a84 a87",
     "Sayatan, ukur & keluaran": "a7 a30 a48 a49 a59 a81",
     "Antarmuka & kerangka": "a2 a10 a34 a37 a44 a45 a61 a64 a69 a71 a72 a73 a75 a76 a77 a79 a80 a83 a90 a91",
     "Terjemahan (4 bahasa)": "a29 a33 a50 a74",
     "Demo otomatis (kode)": "a24_demo a28 a32 a47 a63 a82 a89"}
sz = {}
for p in glob.glob(os.path.join(SRC, "a*.js")):
    sz[os.path.basename(p)[:-3]] = os.path.getsize(p)
def tot(keys):
    s = 0
    for k in keys.split():
        m = [n for n in sz if n == k or n.startswith(k + "_")]
        s += sum(sz[n] for n in m)
    return s
rows = [(k, tot(v) / 1024) for k, v in G.items()]
extra = sz.get("a24_data", 0) / 1024
rows.sort(key=lambda r: r[1])
f = plt.figure(figsize=(7.2, 3.1), dpi=200); ax = f.add_axes([0.33, 0.2, 0.62, 0.76])
cols = [GD if "Schedule" in k or "G × T" in k else AC for k, _ in rows]
b = ax.barh([k for k, _ in rows], [v for _, v in rows], color=cols, height=.62)
for r, (k, v) in zip(b, rows):
    ax.text(v + 6, r.get_y() + r.get_height() / 2, f"{v:,.0f} kB".replace(",", "."), va="center", fontsize=8, color=NV)
ax.set_xlabel("ukuran kode sumber (kB)"); ax.set_xlim(0, max(v for _, v in rows) * 1.18)
ax.grid(axis="x", color="#eee"); ax.set_axisbelow(True)
f.text(0.02, 0.015, f"Tidak termasuk: data latihan fiktif terkompresi untuk demo ({extra:,.0f} kB), CSS & HTML (±74 kB), pustaka pihak ketiga.".replace(",", "."), fontsize=7, color=MU)
save(f, "c1_kode.png")
print("TOTAL kode (kB):", round(sum(v for _, v in rows)), "modul:", len(sz))

# 5. Verifikasi presisi
f = plt.figure(figsize=(7.2, 2.5), dpi=200); ax = f.add_axes([0.37, 0.2, 0.55, 0.7])
L = ["Cara lama: raster", "Pit Studio: TIN presisi GC-Ex", "Hitungan Python terpisah (acuan)"]
V = [70, 100.0, 100.0]
b = ax.barh(L, V, color=[MR, GD, NV], height=.55)
for r, v, t in zip(b, V, ["≈ 70 % (kurang ±30 %)", "6.548.307,0 t · 21.740 blok", "6.548.307,0 t · 21.740 blok"]):
    ax.text(v + 1, r.get_y() + r.get_height() / 2, t, va="center", fontsize=8, color=NV)
ax.set_xlim(0, 135); ax.set_xlabel("tonase bijih desain uji terhadap acuan (%)"); ax.invert_yaxis()
ax.axvline(100, color=MU, lw=.8, ls=":")
save(f, "c2_presisi.png")

# 6. Matriks status legal
items = [("Hak cipta program komputer", "Ada — otomatis (prinsip deklaratif)", GR),
         ("Lisensi open source pihak ketiga", "Permisif; teks lisensi ikut installer", GR),
         ("Kunci privat lisensi", "Tidak ada di repo / Release", GR),
         ("Data contoh di installer", "Fiktif", GR),
         ("Syarat penggunaan (EULA)", "Ada; daftar aplikasi belum menyebut Pit Studio", KU),
         ("Penafian merek pihak ketiga", "Ada; perlu ditambah Minex, Minescape, Whittle", KU),
         ("Pencatatan ciptaan di DJKI", "Belum (opsional, memperkuat bukti)", KU),
         ("Kepemilikan vs. pemberi kerja", "Perlu dicek terhadap kontrak kerja", KU),
         ("Merek \"Pit Studio\"", "Belum didaftarkan — hak merek lahir dari pendaftaran", MR),
         ("Kerahasiaan kode sumber", "Repositori GitHub saat ini PUBLIK", MR)]
f, ax = canvas(7.2, 3.6)
for i, (a, b2, c) in enumerate(items):
    y = 0.92 - i * 0.092
    ax.add_patch(FancyBboxPatch((0.01, y - 0.035), 0.98, 0.075, boxstyle="round,pad=0,rounding_size=0.008", fc="#fbfaf7" if i % 2 else "white", ec="#eeeae2", lw=.6))
    ax.add_patch(plt.Circle((0.035, y + 0.003), 0.013, color=c, transform=ax.transAxes))
    ax.text(0.06, y, a, va="center", fontsize=8.4, color=NV, fontweight="bold")
    ax.text(0.43, y, b2, va="center", fontsize=8.2, color=NV)
ax.text(0.01, 0.005, "●  hijau = beres   ●  kuning = perlu dilengkapi   ●  merah = perlu tindakan sebelum bicara dengan investor", fontsize=7.4, color=MU)
save(f, "d4_legal.png")
print("ok")
