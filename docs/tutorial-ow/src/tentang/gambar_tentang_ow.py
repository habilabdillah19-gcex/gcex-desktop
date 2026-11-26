import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "DejaVu Sans"
import os, tempfile
OUT = os.path.join(tempfile.gettempdir(), "tentang_ow"); os.makedirs(OUT, exist_ok=True)

def box(ax, x, y, w, h, txt, fc="#E6F1FB", ec="#185FA5", fs=8.5, ls="-", bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.2, linestyle=ls))
    ax.text(x + w/2, y + h/2, txt, ha="center", va="center", fontsize=fs,
            weight="bold" if bold else "normal")

def arr(ax, x1, y1, x2, y2, txt=None, col="#444", ls="-", dx=0, dy=0.12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
                                 color=col, lw=1.1, linestyle=ls))
    if txt:
        ax.text((x1+x2)/2 + dx, (y1+y2)/2 + dy, txt, ha="center", fontsize=7, color=col)

def new(w, h, xl, yl):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.axis("off")
    return fig, ax

# Gambar 1 - arsitektur
fig, ax = new(8, 5.2, (0, 10), (0, 6.4))
box(ax, 0.2, 5.2, 2.6, 0.9, "Pengguna\nWindows 64-bit, offline", fc="#F1EFE8", ec="#5F5E5A")
box(ax, 3.7, 5.2, 2.8, 0.9, "Shell Electron\nelectron/main.js: menu, jendela,\ngerbang lisensi", fc="#EEEDFE", ec="#534AB7")
box(ax, 7.2, 5.2, 2.6, 0.9, "Installer NSIS x64\nOre-Works-Setup-versi.exe", fc="#F1EFE8", ec="#5F5E5A")
box(ax, 3.5, 2.7, 3.2, 1.5, "app-ow/index.html\nSatu berkas HTML: pemetaan, pemodelan,\nanalisis, peta 2D, 3D\nthree.js r128 · geotiff.js · sql.js",
    fc="#E1F5EE", ec="#0F6E56", fs=8, bold=False)
box(ax, 0.2, 2.7, 2.6, 1.5, "File proyek .owproj\nSQLite lokal\n(dibaca dan ditulis\npengguna)", fc="#FAEEDA", ec="#854F0B")
box(ax, 7.2, 2.7, 2.6, 1.5, "Berkas lisensi\n%APPDATA%\\GC-Ex Lisensi\\\nlisensi.json", fc="#FAEEDA", ec="#854F0B")
box(ax, 3.5, 0.3, 3.2, 1.0, "Data lokal pengguna (bor, kanal, DXF,\ntopografi, ortofoto, MapInfo / SHP)", fc="#F1EFE8", ec="#5F5E5A")
box(ax, 0.2, 0.3, 2.6, 1.0, "Server / cloud\nTIDAK digunakan", fc="white", ec="#A32D2D", ls="--")
arr(ax, 2.8, 5.65, 3.7, 5.65)
arr(ax, 7.2, 5.65, 6.5, 5.65, "pasang")
arr(ax, 5.1, 5.2, 5.1, 4.2, "memuat")
arr(ax, 3.5, 3.45, 2.8, 3.45, "baca / tulis")
arr(ax, 6.7, 3.45, 7.2, 3.45, "verifikasi", dy=0.14)
arr(ax, 5.1, 2.7, 5.1, 1.3, "proses lokal")
arr(ax, 3.6, 2.8, 2.8, 1.3, "tidak ada permintaan jaringan", col="#A32D2D", ls="--", dx=-0.4, dy=-0.25)
ax.set_title("Gambar 1. Arsitektur Ore Works for Desktop", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig1_arsitektur.png", dpi=200); plt.close(fig)

# Gambar 2 - alur kerja
steps = [("1. Impor", "Bor, kanal, DXF,\ntopografi, ortofoto,\nMapInfo / Shapefile"),
         ("2. Pemetaan", "Studio Pemetaan (F8):\ndigit di plan 2D /\nmuka dinding"),
         ("3. Pemodelan", "Eksplisit (string,\nStudio Pemodelan) &\nImplisit RBF per domain"),
         ("4. Analisis", "Geokimia, struktur\n(pergeseran batas,\nuji signifikansi)"),
         ("5. Visualisasi", "3D, penampang,\npeta level, Layout\npeta (PNG / PDF)"),
         ("6. Simpan", "Proyek .owproj\n(SQLite lokal)")]
fig, ax = new(9.6, 2.8, (0, 12.6), (0, 3.2))
for i, (t, d) in enumerate(steps):
    x = 0.1 + i * 2.1
    box(ax, x, 1.6, 1.8, 0.8, t, fc="#E6F1FB", ec="#185FA5", fs=8.5, bold=True)
    ax.text(x + 0.9, 1.4, d, ha="center", va="top", fontsize=7)
    if i < len(steps) - 1:
        arr(ax, x + 1.8, 2.0, x + 2.1, 2.0)
ax.set_title("Gambar 2. Alur kerja dari data sampai proyek tersimpan", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig2_alur.png", dpi=200); plt.close(fig)

# Gambar 3 - lisensi
fig, ax = new(9, 2.6, (0, 10.6), (0, 3.2))
ls_steps = [("Kunci lisensi", "format GCEX1.(data).\n(tanda tangan)"),
            ("Verifikasi tanda tangan", "Ed25519 dengan kunci publik\nyang tertanam di aplikasi"),
            ("Cocokkan ID mesin", "SHA-256 dari MachineGuid\nWindows"),
            ("Aplikasi terbuka", "lisensi.json disimpan di\n%APPDATA%")]
for i, (t, d) in enumerate(ls_steps):
    x = 0.1 + i * 2.6
    box(ax, x, 1.5, 2.2, 0.9, t, fc="#FAEEDA", ec="#854F0B", fs=8.5, bold=True)
    ax.text(x + 1.1, 1.1, d, ha="center", va="top", fontsize=7.3)
    if i < len(ls_steps) - 1:
        arr(ax, x + 2.2, 1.95, x + 2.6, 1.95)
ax.text(0.1, 0.05, "Kunci privat pembuat lisensi disimpan terpisah dan tidak pernah masuk repositori atau rilis.",
        fontsize=7, color="#5F5E5A")
ax.set_title("Gambar 3. Alur lisensi per mesin (berlaku pada build terpaket)", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig3_lisensi.png", dpi=200); plt.close(fig)

# Gambar 4 - matriks risiko (penilaian kualitatif)
items = [("Belum diuji pada data proyek penuh", 4, 4),
         ("Bergantung satu pengembang", 3, 5),
         ("Akurasi model bergantung kualitas data bor", 3, 4),
         ("Hanya Windows 64-bit", 5, 2),
         ("Performa 3D di GPU lemah", 3, 3),
         ("Lisensi komponen pihak ketiga (MIT)", 1, 2)]
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.set_xlim(0.5, 5.5); ax.set_ylim(0.5, 5.5)
import numpy as np
g = np.array([[(i*j) for i in range(1, 6)] for j in range(1, 6)])
ax.imshow(g, extent=(0.5, 5.5, 0.5, 5.5), origin="lower", cmap="Greys", alpha=0.10, aspect="auto")
for k, (lab, l, im) in enumerate(items):
    c = "#A32D2D" if l*im >= 15 else ("#BA7517" if l*im >= 8 else "#0F6E56")
    ax.scatter(l, im, s=140, color=c, zorder=3)
    off, ha = {1: ((-6, 9), "right"), 3: ((-8, -3), "right")}.get(k+1, ((8, -3), "left"))
    ax.annotate(f"{k+1}. {lab}", (l, im), xytext=off, textcoords="offset points", fontsize=7.8, ha=ha)
ax.set_xlabel("Kemungkinan (1 rendah - 5 tinggi)")
ax.set_ylabel("Dampak (1 rendah - 5 tinggi)")
ax.set_xticks(range(1, 6)); ax.set_yticks(range(1, 6))
ax.set_title("Gambar 4. Matriks risiko produk (penilaian kualitatif penyusun)", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig4_risiko.png", dpi=200); plt.close(fig)
print("ok")
