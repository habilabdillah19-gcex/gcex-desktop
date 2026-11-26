# -*- coding: utf-8 -*-
"""Bangun docs/Tentang_GCEx_BlockModel.pdf dan docs/Tentang_GCEx_Drillhole.pdf (dipisah per aplikasi, pemilik 26 Nov 2026) — panduan menjawab pertanyaan Ahli IT / Programmer dan Investor
teknologi tentang GC-Ex Drillhole & Block Model for Desktop (pemilik, 23 Nov 2026).

Isi diambil dari repo (versi, jumlah uji, catatan perubahan) supaya angka selalu sesuai saat dibangun ulang.
Diagram = SVG tulisan tangan; grafik = matplotlib (SVG); PDF dicetak Chromium (Playwright).
Pakai: python docs/tentang/buat_tentang.py
"""
import io, json, os, re, subprocess, collections, datetime, glob, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

NAVY, NAVY2, COPPER, GOLD, CREAM, LINE, MUTED, INK = '#1C2733', '#2C3B57', '#B8692E', '#B5893E', '#F7F5F0', '#D3CDC1', '#5C6672', '#1F2430'
GREEN, AMBER, GREY = '#3E7C59', '#C9A227', '#C9CED6'

# ---------------------------------------------------------------- fakta dari repo
def ver(f, key=None):
    d = json.load(open(ROOT / f, encoding='utf-8'))
    return (d.get('extraMetadata') or {}).get('version') or d.get('version')
V = {'bm': ver('package.json'), 'dh': ver('builder-dh.json'), 'db': ver('builder-core.json'), 'ow': ver('builder-ow.json'), 'ps': ver('builder-ps.json')}
ELECTRON = json.load(open(ROOT / 'package.json'))['devDependencies'].get('electron', '?') if 'devDependencies' in json.load(open(ROOT / 'package.json')) else '?'
N_UJI = len(glob.glob(str(ROOT / 'tools' / 'uji' / '*.py'))) + len(glob.glob(str(ROOT / 'backend' / 'tests' / '*.py')))
N_LOG = len(re.findall(r'^\| [0-9][a-z]* \|', open(ROOT / 'README.md', encoding='utf-8').read(), re.M))
def kb(*dirs):
    s = 0
    for d in dirs:
        for p in (ROOT / d).rglob('*'):
            if p.is_file() and p.suffix in ('.js', '.py', '.html', '.css') and '__pycache__' not in p.parts and p.name != 'bahasa_kamus.js':
                s += p.stat().st_size
    return s / 1024
UKURAN = [('Tampilan Block Model\n(web-src)', kb('web-src')), ('Tampilan Drillhole\n(web-src-dh)', kb('web-src-dh')),
          ('Backend Python\n(FastAPI)', kb('backend/gcex_backend')), ('Shell Electron\n(lisensi, jendela)', kb('electron'))]
try:
    log = subprocess.run(['git', 'log', '--format=%ad', '--date=short'], cwd=ROOT, capture_output=True, text=True).stdout.split()
except Exception:
    log = []
HARI = sorted(collections.Counter(log).items())[-21:]
TGL = datetime.date.today().strftime('%d %b %Y')

# ---------------------------------------------------------------- grafik
for f in ['/usr/share/fonts/opentype/inter/Inter-Regular.otf', '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf']:
    if os.path.exists(f): fm.fontManager.addfont(f)
plt.rcParams.update({'font.family': ['Inter', 'DejaVu Sans'], 'font.size': 9, 'axes.edgecolor': LINE, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False, 'svg.fonttype': 'none'})

def svg(fig):
    b = io.StringIO(); fig.savefig(b, format='svg', bbox_inches='tight', transparent=True); plt.close(fig)
    s = b.getvalue(); return s[s.index('<svg'):]

def g_ukuran():
    fig, ax = plt.subplots(figsize=(6.4, 1.9))
    lab = [u[0] for u in UKURAN][::-1]; val = [u[1] / 1024 for u in UKURAN][::-1]
    bars = ax.barh(lab, val, color=[GREY, NAVY2, GOLD, COPPER][::-1][::-1], height=0.6)
    for bb, v in zip(bars, val): ax.text(v + max(val) * 0.01, bb.get_y() + bb.get_height() / 2, ('%.1f MB' % v) if v >= 1 else ('%.0f KB' % (v * 1024)), va='center', fontsize=8.5, color=INK)
    ax.set_xlabel('Ukuran kode sumber (MB, tanpa pustaka pihak ketiga yang dibundel terpisah)'); ax.set_xlim(0, max(val) * 1.18)
    ax.tick_params(axis='y', length=0); return svg(fig)

def g_aktivitas():
    if not HARI: return ''
    fig, ax = plt.subplots(figsize=(6.4, 1.45))
    d = [h[0][5:].replace('-', '/') for h in HARI]; n = [h[1] for h in HARI]
    ax.bar(d, n, color=COPPER, width=0.65)
    for i, v in enumerate(n): ax.text(i, v + 0.6, str(v), ha='center', fontsize=7.5, color=MUTED)
    ax.set_ylabel('commit / hari'); ax.tick_params(axis='x', labelsize=7.5, rotation=0); ax.set_ylim(0, max(n) * 1.2)
    return svg(fig)

def g_cakupan(sorot=None):
    tahap = ['Database bor & validasi', 'Pemodelan geologi (domain / vein)', 'Geostatistik & estimasi BM', 'Reporting grade × tonase',
             'Klasifikasi sumber daya (M/I/I)', 'Desain pit & jadwal', 'Dig block harian & dig plan', 'As-mined & rekonsiliasi', 'Foto core / borang / QAQC', 'Pemetaan lapangan (struktur)']
    app = ['GC-Ex\nDrillhole', 'GC-Ex\nBlock Model', 'DB-Ex', 'Ore Works', 'Pit Studio']
    # 2 = inti, 1 = sebagian / pendukung, 0 = tidak
    M = [[2, 0, 2, 0, 0], [2, 0, 0, 1, 0], [2, 1, 0, 0, 0], [2, 2, 0, 0, 1], [2, 0, 0, 0, 0],
         [0, 1, 0, 0, 2], [0, 2, 0, 0, 0], [0, 2, 0, 0, 0], [0, 0, 2, 0, 0], [1, 0, 1, 2, 0]]
    col = {0: '#EEF0F3', 1: '#E8CDB0', 2: COPPER}
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for r, row in enumerate(M):
        for c, v in enumerate(row):
            ax.add_patch(plt.Rectangle((c, r), 0.94, 0.86, color=col[v]))
            ax.text(c + 0.47, r + 0.43, {0: '', 1: 'sebagian', 2: 'inti'}[v], ha='center', va='center', fontsize=7.5, color='white' if v == 2 else INK)
    if sorot is not None:
        ax.add_patch(plt.Rectangle((sorot - 0.04, -0.06), 1.02, len(tahap) + 0.02, fill=False, ec=NAVY, lw=2.2, clip_on=False))
    ax.set_xlim(-0.06, len(app)); ax.set_ylim(len(tahap) + 0.04, -0.1)
    ax.set_xticks([i + 0.47 for i in range(len(app))]); ax.set_xticklabels(app, fontsize=8)
    ax.set_yticks([i + 0.43 for i in range(len(tahap))]); ax.set_yticklabels(tahap, fontsize=8)
    ax.xaxis.tick_top(); ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    return svg(fig)

# ---------------------------------------------------------------- diagram (SVG)
def kotak(x, y, w, h, t, sub='', fill='white', stroke=LINE, tc=INK, fs=11, bold=True, r=8):
    s = '<rect x="%g" y="%g" width="%g" height="%g" rx="%d" fill="%s" stroke="%s" stroke-width="1.4"/>' % (x, y, w, h, r, fill, stroke)
    ty = y + h / 2 + (-5 if sub else 4)
    s += '<text x="%g" y="%g" text-anchor="middle" font-size="%d" font-weight="%d" fill="%s">%s</text>' % (x + w / 2, ty, fs, 600 if bold else 400, tc, html.escape(t))
    if sub: s += '<text x="%g" y="%g" text-anchor="middle" font-size="9" fill="%s">%s</text>' % (x + w / 2, ty + 14, tc if fill not in ('white', CREAM) else MUTED, html.escape(sub))
    return s
def panah(x1, y1, x2, y2, c=MUTED, dash=False, label=''):
    s = '<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="1.6" marker-end="url(#ah)"%s/>' % (x1, y1, x2, y2, c, ' stroke-dasharray="4 3"' if dash else '')
    if label: s += '<text x="%g" y="%g" text-anchor="middle" font-size="8.5" fill="%s">%s</text>' % ((x1 + x2) / 2, (y1 + y2) / 2 - 4, MUTED, html.escape(label))
    return s
DEFS = '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker></defs>' % MUTED

def d_arsitektur():
    W, H = 660, 380
    s = '<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">%s' % (W, H, DEFS)
    s += '<rect x="6" y="6" width="%d" height="%d" rx="12" fill="%s" stroke="%s" stroke-dasharray="6 4"/>' % (W - 150, H - 12, CREAM, LINE)
    s += '<text x="20" y="28" font-size="11" font-weight="600" fill="%s">Satu komputer Windows 64-bit (laptop pengguna) — semua proses lokal</text>' % NAVY
    s += kotak(24, 44, 470, 112, '', fill='white')
    s += '<text x="36" y="64" font-size="11" font-weight="600" fill="%s">Electron (Chromium + Node.js)</text>' % NAVY
    s += kotak(36, 74, 140, 70, 'Proses utama', 'jendela · menu · log', fill=NAVY, stroke=NAVY, tc='white')
    s += kotak(186, 74, 120, 70, 'Lisensi', 'Ed25519 · ID komputer', fill=NAVY2, stroke=NAVY2, tc='white')
    s += kotak(316, 74, 166, 70, 'Jembatan preload', 'contextIsolation · sandbox', fill='white')
    s += kotak(24, 170, 300, 110, '', fill='white')
    s += '<text x="36" y="190" font-size="11" font-weight="600" fill="%s">Tampilan (HTML / JavaScript, satu file)</text>' % NAVY
    s += kotak(36, 200, 132, 68, 'Plotly.js (WebGL)', '3D · sayatan 2D · grafik', fill=COPPER, stroke=COPPER, tc='white')
    s += kotak(178, 200, 134, 68, 'Mesin hitung JS', 'RBF · kriging · laporan', fill=COPPER, stroke=COPPER, tc='white')
    s += kotak(340, 170, 154, 110, 'Backend Python', 'FastAPI · Uvicorn', fill=GOLD, stroke=GOLD, tc='white')
    s += '<text x="417" y="250" text-anchor="middle" font-size="9" fill="white">127.0.0.1 · port acak</text><text x="417" y="263" text-anchor="middle" font-size="9" fill="white">.mdl besar · Excel · Access</text>'
    s += panah(324, 225, 338, 225); s += panah(417, 156, 417, 168); s += panah(175, 156, 175, 168)
    s += kotak(24, 300, 150, 62, 'Proyek (IndexedDB)', 'sesi kerja · versi', fill='white')
    s += kotak(184, 300, 150, 62, 'SQLite proyek', 'gcex_proyek.db · riwayat', fill='white')
    s += kotak(344, 300, 150, 62, 'File kerja', '.mdl .str .dxf .csv .xlsx .accdb', fill='white')
    s += panah(110, 282, 100, 298); s += panah(400, 282, 400, 298); s += panah(260, 282, 260, 298)
    # internet dicoret
    s += kotak(530, 140, 120, 60, 'Internet', 'tidak dipakai', fill='white', stroke='#C0392B', tc='#C0392B')
    s += '<line x1="498" y1="170" x2="526" y2="170" stroke="#C0392B" stroke-width="2"/><line x1="505" y1="160" x2="519" y2="180" stroke="#C0392B" stroke-width="2.4"/><line x1="519" y1="160" x2="505" y2="180" stroke="#C0392B" stroke-width="2.4"/>'
    s += '<text x="590" y="222" text-anchor="middle" font-size="8.5" fill="%s">tanpa telemetri,</text><text x="590" y="234" text-anchor="middle" font-size="8.5" fill="%s">tanpa auto-update,</text><text x="590" y="246" text-anchor="middle" font-size="8.5" fill="%s">tanpa akun cloud</text>' % (MUTED, MUTED, MUTED)
    s += kotak(516, 272, 138, 86, 'Versi .html portabel', 'tanpa instal · Edge/Chrome', fill=CREAM, stroke=GOLD, fs=10)
    s += '<text x="585" y="340" text-anchor="middle" font-size="8.5" fill="%s">tanpa backend Python</text>' % MUTED
    return s + '</svg>'

def d_alur(sorot=None):
    W, H = 660, 250
    s = '<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">%s' % (W, H, DEFS)
    redup = {'dh': '<g opacity=".42">', 'bm': '<g>'} if sorot == 'bm' else ({'dh': '<g>', 'bm': '<g opacity=".42">'} if sorot == 'dh' else {'dh': '<g>', 'bm': '<g>'})
    s += redup['dh']
    s += '<rect x="4" y="8" width="652" height="98" rx="10" fill="#F3EDE4"/><text x="16" y="26" font-size="10.5" font-weight="600" fill="%s">GC-Ex DRILLHOLE — dari data bor ke block model</text>' % COPPER
    a = [('Data bor', 'collar·survey·assay'), ('Validasi', 'upsert·kampanye'), ('Pemodelan', 'domain·vein RBF'), ('Geostatistik', 'variogram·KNA'), ('Estimasi', 'OK·ID²·sub-blok'), ('Reporting', 'pit·topo·M/I/I')]
    for i, (t, u) in enumerate(a):
        x = 14 + i * 107; s += kotak(x, 36, 95, 58, t, u, fill='white', stroke=COPPER, fs=10.5)
        if i: s += panah(x - 12, 65, x - 2, 65)
    s += '</g>' + redup['bm'] + '<rect x="4" y="142" width="652" height="102" rx="10" fill="#E6EAF0"/><text x="16" y="236" font-size="10.5" font-weight="600" fill="%s">GC-Ex BLOCK MODEL — dari block model ke tambang harian</text>' % NAVY
    b = [('Import BM', '.mdl / CSV'), ('Flitch aktif', 'sayatan 2D'), ('Dig block', 'otomatis·manual'), ('Dig plan', 'PDF·STR·DXF'), ('As-mined', 'pick-up survei'), ('Rekonsiliasi', 'register Excel·Access')]
    for i, (t, u) in enumerate(b):
        x = 14 + i * 107; s += kotak(x, 152, 95, 58, t, u, fill='white', stroke=NAVY, fs=10.5)
        if i: s += panah(x - 12, 181, x - 2, 181)
    s += '</g><polyline points="596,96 596,122 61,122 61,149" fill="none" stroke="%s" stroke-width="1.6" marker-end="url(#ah)"/>' % GOLD
    s += '<text x="330" y="117" text-anchor="middle" font-size="8.5" fill="%s">block model GC (.mdl, format Surpac)</text>' % MUTED
    s += '<path d="M 645 181 C 662 181, 662 66, 647 66" fill="none" stroke="%s" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#ah)"/>' % MUTED
    s += '<text x="640" y="136" text-anchor="end" font-size="8.5" fill="%s">bor infill → update model</text>' % MUTED
    return s + '</svg>'

def d_rilis():
    W, H = 660, 150
    s = '<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">%s' % (W, H, DEFS)
    st = [('Kode di GitHub', 'setiap commit', 'white', INK), ('GitHub Actions', 'uji · build exe · cek versi', NAVY, 'white'), ('GitHub Release', 'installer · dokumen · SHA-256', NAVY2, 'white'),
          ('Admin', 'unduh · bagikan', 'white', INK), ('Laptop pengguna', 'pasang · aktivasi · offline', COPPER, 'white')]
    for i, (t, u, f, tc) in enumerate(st):
        x = 6 + i * 131; s += kotak(x, 20, 118, 62, t, u, fill=f, stroke=f if f != 'white' else LINE, tc=tc, fs=10.5)
        if i: s += panah(x - 12, 51, x - 2, 51)
    s += kotak(400, 100, 254, 42, 'Pemilik: kunci lisensi (kunci privat offline)', '', fill=CREAM, stroke=GOLD, fs=9.5, bold=False)
    s += panah(560, 100, 590, 84, c=GOLD)
    return s + '</svg>'

def d_lisensi():
    W, H = 660, 120
    s = '<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">%s' % (W, H, DEFS)
    st = [('1. ID Komputer', 'hash ID Windows', 'white', INK), ('2. Pemilik menandatangani', 'Ed25519 · kunci privat offline', GOLD, 'white'),
          ('3. Kunci GCEX1.…', 'pemegang · aplikasi · kedaluwarsa', NAVY2, 'white'), ('4. Aplikasi memverifikasi', 'hanya memegang kunci publik', NAVY, 'white')]
    for i, (t, u, f, tc) in enumerate(st):
        x = 6 + i * 164; s += kotak(x, 24, 150, 70, t, u, fill=f, stroke=f if f != 'white' else LINE, tc=tc, fs=10.5)
        if i: s += panah(x - 12, 59, x - 2, 59)
    return s + '</svg>'

# ---------------------------------------------------------------- isi
def tabel(head, rows, w=None, cls=''):
    h = '<table class="%s"><thead><tr>%s</tr></thead><tbody>' % (cls, ''.join('<th%s>%s</th>' % ((' style="width:%s"' % w[i]) if w else '', c) for i, c in enumerate(head)))
    for r in rows: h += '<tr>' + ''.join('<td>%s</td>' % c for c in r) + '</tr>'
    return h + '</tbody></table>'
def qa(q, a, who=''):
    tag = {'it': '<span class="tag it">IT</span>', 'inv': '<span class="tag inv">Investor</span>', 'dua': '<span class="tag it">IT</span><span class="tag inv">Investor</span>'}.get(who, '')
    return '<div class="qa"><div class="q">%s%s</div><div class="a">%s</div></div>' % (tag, q, a)

CSS = """
@font-face{font-family:'Playfair Display';src:url('file://%s') format('truetype');font-weight:400 900}
@page{size:A4;margin:16mm 15mm 16mm 15mm}
*{box-sizing:border-box}
body{font-family:Inter,'DejaVu Sans',sans-serif;color:%s;font-size:9.6pt;line-height:1.5;margin:0}
h1,h2{font-family:'Playfair Display',serif;color:%s;font-weight:700;letter-spacing:-.01em}
h1{font-size:30pt;margin:0 0 6px;line-height:1.1}
h2{font-size:17pt;margin:0 0 8px;padding-bottom:5px;border-bottom:2px solid %s;break-after:avoid}
h3{font-size:11pt;color:%s;margin:14px 0 5px;break-after:avoid}
p{margin:0 0 7px}
.bab{break-before:page}
.lead{font-size:10.5pt;color:%s}
.kartu{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0}
.k{background:%s;border:1px solid %s;border-radius:8px;padding:8px 10px}
.k b{display:block;font-size:15pt;color:%s;font-family:'Playfair Display',serif}
.k span{font-size:8pt;color:%s}
table{width:100%%;border-collapse:collapse;margin:6px 0 10px;font-size:8.8pt;break-inside:auto}
th{background:%s;color:white;text-align:left;padding:5px 7px;font-weight:600}
td{padding:5px 7px;border-bottom:1px solid %s;vertical-align:top}
tr:nth-child(even) td{background:#FAF8F4}
.fig{margin:8px 0 4px;break-inside:avoid}
.fig svg{width:100%%;height:auto}
.cap{font-size:8pt;color:%s;margin:2px 0 10px}
.qa{break-inside:avoid;border-left:3px solid %s;padding:5px 0 5px 10px;margin:0 0 8px;background:#FBFAF7}
.q{font-weight:600;color:%s;margin-bottom:2px}
.a{color:%s}
.tag{display:inline-block;font-size:7pt;font-weight:600;padding:1px 5px;border-radius:3px;margin-right:5px;vertical-align:1px}
.tag.it{background:%s;color:white}.tag.inv{background:%s;color:white}
.catat{background:#FFF6E5;border:1px solid #E7C98C;border-radius:8px;padding:8px 11px;margin:8px 0;font-size:9pt;break-inside:avoid}
.ok{background:#EEF5F0;border:1px solid #B7D3C1;border-radius:8px;padding:8px 11px;margin:8px 0;font-size:9pt;break-inside:avoid}
.dua{display:grid;grid-template-columns:1fr 1fr;gap:12px}
ul{margin:2px 0 8px 16px;padding:0}li{margin:0 0 3px}
.sampul{height:255mm;display:flex;flex-direction:column;justify-content:space-between;background:%s;color:white;margin:-16mm -15mm 0;padding:28mm 20mm 18mm}
.sampul h1{color:white;font-size:40pt}
.sampul .sub{font-size:13pt;color:#E8ECF2;max-width:150mm}
.sampul .garis{height:4px;width:70mm;background:%s;margin:14px 0}
.sampul .meta{font-size:9pt;color:#B9C3D0}
.logo{font-family:'Playfair Display',serif;font-size:16pt;letter-spacing:.02em}
.logo small{display:block;font-family:Inter;font-size:8pt;letter-spacing:.18em;color:%s}
code{font-family:'DejaVu Sans Mono',monospace;font-size:8.3pt;background:#F1EEE8;padding:0 3px;border-radius:3px}
""" % (ROOT / 'docs' / 'fonts' / 'PlayfairDisplay-wght.ttf', INK, NAVY, COPPER, NAVY2, MUTED, CREAM, LINE, COPPER, MUTED, NAVY, LINE, MUTED, COPPER, NAVY, INK, NAVY2, COPPER, NAVY, COPPER, GOLD)


# ================================================================ isi per aplikasi
APP = {
    'bm': dict(nama='GC-Ex Block Model', file='Tentang_GCEx_BlockModel.pdf', ver=V['bm'], kol=1, src='web-src', exe='GC-Ex-Setup', html='GCEx_BlockModel.html',
               peran='dari block model ke tambang harian',
               untuk='junior grade control dan short-term / junior mine planner — pekerjaan harian per flitch: dig block, dig plan, as-mined, laporan produksi',
               masuk='Block model (.mdl Surpac / CSV, termasuk model terotasi lewat CSV); topografi, desain pit, pick-up survei (.str / .dxf / CSV); orthofoto (GeoTIFF / JPG + world file)',
               keluar='Dig block &amp; dig plan (PDF / STR / DXF dengan string number sesuai warna), model as-mined (.mdl), register poligon Excel / Access, laporan grade × tonase harian–bulanan'),
    'dh': dict(nama='GC-Ex Drillhole', file='Tentang_GCEx_Drillhole.pdf', ver=V['dh'], kol=0, src='web-src-dh', exe='GC-Ex-Drillhole-Setup', html='GCEx_DrillHole.html',
               peran='dari data bor ke block model',
               untuk='geologist pemodelan / resource geologist di tambang — membangun domain vein, estimasi block model, laporan sumber daya',
               masuk='Collar, survey, assay, geologi (CSV / Excel, header dinamis); wireframe (Surpac / Leapfrog); topografi &amp; desain pit (.str / .dxf); orthofoto',
               keluar='Domain / solid vein, variogram, block model GC (.mdl Surpac), laporan grade × tonase dengan klasifikasi Measured / Indicated / Inferred, string &amp; DXF'),
}
FITUR = {
    'bm': [['Block model', 'Import .mdl Surpac (termasuk &gt; 6 GB di RAM 8 GB) atau CSV; <b>block model terotasi</b> (bearing, konvensi Surpac) lewat import CSV; filter &amp; SG; kelas kadar &amp; warna .ssi Surpac'],
           ['Flitch &amp; dig block', 'Flitch aktif, sayatan 2D, orthofoto resolusi tinggi; dig block otomatis &amp; manual; additional flagging (garis ganda); pemeriksaan sebelum dig plan terbit; preset kelas kadar &amp; tujuan material'],
           ['Dig plan', 'Layout &amp; plot PDF dengan kop, legenda, skala; export STR / DXF dengan string number sesuai warna'],
           ['As-mined', 'Atap dari pick-up survei, lantai dari DTM, kunci per tanggal-shift; Solid Vein Aktual; model as-mined (.mdl)'],
           ['Laporan', 'Grade × tonase dalam constraint topografi / pit / RL (cara Surpac), ringkasan harian, rekap per flitch, laporan mingguan / bulanan, per desain pit, rekonsiliasi'],
           ['Integrasi', 'Register poligon langsung ke workbook Excel yang sudah ada (rumus &amp; makro tetap utuh) dan ke MS Access'],
           ['Kenyamanan', 'Project Tree mengikuti urutan kerja, mode Demo terpandu, 10 palet warna (kontras teks dijaga), 5 bahasa antarmuka, alat ukur jarak 3D / 2D, panel bisa ditutup']],
    'dh': [['Database bor', 'Import collar / survey / assay / geologi dengan header dinamis; validasi; database per kampanye; upsert bor infill; filter AND / OR; export terfilter'],
           ['Pemodelan geologi', 'Geomodeller Vein (domain vein, flag otomatis dari kadar &amp; dari kolom kode, koreksi interaktif, string HW/FW, solid RBF), vein bercabang, struktur dip / dip azimuth, sesar 3D dengan offset &amp; urutan umur; menyerap wireframe Leapfrog menjadi domain yang bisa diedit'],
           ['Geostatistik', 'Statistik per domain, komposit, top-cut, variogram &amp; anisotropi, KNA, estimasi per lapisan (unfold)'],
           ['Estimasi', 'Block model dari nol (kerangka AOI) atau melanjutkan model lama; Ordinary Kriging / ID²; sub-blok &amp; proporsi volume; estimasi waste; radius pencarian &amp; area pengaruh'],
           ['Reporting', 'Grade × tonase dengan constraint topografi / pit / domain / RL; beberapa desain pit; progres topo-ke-topo; klasifikasi Measured / Indicated / Inferred'],
           ['Pendukung', 'Plan bor, Ore Geometry Studio (long section, ore shoot), orthofoto di-drape ke topografi, sayatan memotong topografi &amp; pit, export .mdl / .str / DXF'],
           ['Kenyamanan', 'Project Tree mengikuti urutan kerja, mode Demo terpandu, 10 palet warna (kontras teks dijaga), 5 bahasa antarmuka, alat ukur jarak 3D / 2D, panel bisa ditutup']],
}
FORMAT = {'bm': [['Baca', 'Surpac .mdl, .str, .ssi; DXF; CSV / Excel; GeoTIFF / JPG + world file; MS Access .accdb / .mdb'],
                 ['Tulis', 'Surpac .mdl, .str (+ .ssi); DXF; CSV; Excel .xlsx; PDF; PNG; MS Access']],
          'dh': [['Baca', 'CSV / Excel (collar, survey, assay, geologi); Surpac .str, .mdl, wireframe; DXF; GeoTIFF / JPG + world file'],
                 ['Tulis', 'Surpac .mdl, .str (+ .ssi); DXF; CSV; Excel .xlsx; PNG']]}
BATAS = {'bm': [['Block model terotasi dari .mdl belum dibaca langsung (lewat CSV sudah bisa)', 'Butuh contoh .mdl terotasi dari Surpac untuk dicocokkan'],
                ['Dig block otomatis, snap sudut blok, komposit flitch &amp; as-mined belum mendukung model terotasi (dihentikan dengan pesan)', 'Kerjakan di kerangka lokal model'],
                ['Tanpa klasifikasi sumber daya (sengaja: fokus operasi harian)', 'Klasifikasi ada di GC-Ex Drillhole'],
                ['Penampil Qt (native) masih percobaan', 'Versi HTML/Electron tetap utama'],
                ['Pengembang tunggal; baru divalidasi pada data satu tambang emas vein', 'Programmer kedua; uji coba di tambang lain'],
                ['Hanya Windows; satu pengguna per proyek (ada kunci pemakai)', 'Kolaborasi lewat folder proyek bersama']],
         'dh': [['Pemodelan vein memakai RBF GC-Ex sendiri, tidak meniru Leapfrog (keputusan pemilik)', 'Hanya fitur Leapfrog yang layak yang diadopsi'],
                ['Grafis 3D bergantung GPU (sudah diuji di Intel Iris Xe)', 'Mode ringan &amp; LOD sudah ada'],
                ['Pengembang tunggal; baru divalidasi pada data satu tambang emas vein', 'Programmer kedua; uji coba di tambang / komoditas lain'],
                ['Hanya Windows; satu pengguna per proyek (ada kunci pemakai)', 'Kolaborasi lewat folder proyek bersama'],
                ['Belum ada audit independen oleh competent person', 'Siapkan studi pembanding vs Surpac untuk ditinjau pihak ketiga']]}
FAQ_KHUSUS = {
    'bm': [('Seberapa besar block model yang sanggup diolah?', 'Diuji: .mdl lebih dari 6 GB di laptop RAM 8 GB (di aplikasi terpasang, backend membuat cache kolom di disk); topografi / pit .str 500–700 MB dibaca per potongan; orthofoto 1 GB.', 'it'),
           ('Bisa membaca block model terotasi?', 'Ya, untuk rotasi bearing (konvensi Surpac, 90 = tidak diputar) lewat import CSV: pusat blok, sayatan, 3D dan laporan memperhitungkan rotasi. Pembacaan rotasi langsung dari file .mdl menyusul setelah ada contoh dari Surpac.', 'it'),
           ('Bagaimana angka tonase / kadar dicocokkan dengan Surpac?', 'Dig block, as-mined dan reporting memakai cara Surpac sebagai bawaan (cara GC-Ex tetap tersedia sebagai pilihan); hasilnya diaudit terhadap laporan Surpac pada data nyata.', 'dua')],
    'dh': [('Algoritma estimasi apa yang dipakai?', 'Ordinary Kriging dan ID² dengan sub-blok di batas solid, didahului variogram dan Kriging Neighbourhood Analysis. Aturan sampel (radius, jumlah sampel, boundary) mengikuti Surpac; hard / soft boundary tetap bisa dipilih.', 'it'),
           ('Bagaimana domain vein dibuat?', 'Interval bor ditandai (flag) dari kadar atau kolom kode, dikoreksi interaktif, lalu permukaan HW / FW diinterpolasi dengan RBF menjadi solid tertutup; wireframe dari Leapfrog / Surpac bisa diserap menjadi domain yang tetap bisa diperbarui saat ada bor baru.', 'it'),
           ('Apakah laporannya layak untuk pelaporan sumber daya?', 'GC-Ex menghitung grade × tonase dan klasifikasi M/I/I, tetapi pelaporan publik (JORC / KCMI) tetap tanggung jawab competent person; GC-Ex adalah alat, bukan pengganti tinjauan itu.', 'inv')]}

def bangun(k):
    A = APP[k]; lain = APP['dh' if k == 'bm' else 'bm']
    B = []
    B.append('''<div class="sampul"><div><div class="logo">GC-Ex<small>GRADE CONTROL EXCELLENCE</small></div></div>
<div><h1>Tentang %s</h1><div class="garis"></div>
<div class="sub">%s for Desktop — %s. Apa itu, bagaimana bekerja, apa yang ditawarkan, kelebihan, status legal, dan cara menjawab
pertanyaan dari <b>ahli IT / programmer</b> maupun <b>investor teknologi</b>.</div></div>
<div class="meta">Versi dokumen: %s · %s %s · aplikasi saudara: %s %s<br>Copyright © Habil Abdillah 2026 · Dokumen internal pemilik, bukan nasihat hukum atau investasi.</div></div>''' % (A['nama'], A['nama'], A['peran'], TGL, A['nama'], A['ver'], lain['nama'], lain['ver']))
    # 1 ringkasan
    pitch = {'bm': '<b>GC-Ex Block Model</b> adalah perangkat lunak desktop Windows untuk <b>pekerjaan grade control harian</b>: memuat block model, membuat dig block dan dig plan per flitch, mencatat yang benar-benar tergali (as-mined), dan merekonsiliasi tonase &amp; kadar. Berjalan <b>offline di laptop pengguna</b> — terpasang lewat installer, atau sebagai <b>file .html portabel tanpa instal</b> — membaca &amp; menulis format Surpac, dan hasil hitungnya diaudit terhadap Surpac.',
             'dh': '<b>GC-Ex Drillhole</b> adalah perangkat lunak desktop Windows untuk <b>mengolah data bor menjadi model geologi dan block model</b>: database bor, domain vein, geostatistik, estimasi, dan laporan grade × tonase dengan klasifikasi sumber daya. Berjalan <b>offline di laptop pengguna</b> — terpasang lewat installer, atau sebagai <b>file .html portabel tanpa instal</b> — membaca &amp; menulis format Surpac, dan hasil hitungnya diaudit terhadap Surpac.'}[k]
    masalah = {'bm': 'pekerjaan harian grade control (membuat dig block, menghitung tonase &amp; kadar yang akan digali, mencatat yang benar-benar tergali) banyak dikerjakan manual atau dengan perangkat lunak tambang umum yang mahal, berat, dan tidak mengikuti alur kerja harian tim GC.',
               'dh': 'memperbarui model geologi dan block model setiap ada bor infill lambat bila harus bolak-balik antar perangkat lunak serba guna yang mahal; tim GC butuh alat yang mengikuti alur kerja mereka dan tetap selaras dengan Surpac.'}[k]
    B.append('''<div class="bab"><h2>1. Jawaban singkat (30 detik)</h2><p class="lead">%s</p>
<div class="kartu"><div class="k"><b>v%s</b><span>versi saat dokumen dibuat</span></div>
<div class="k"><b>100%% offline</b><span>tanpa cloud, telemetri, atau auto-update</span></div>
<div class="k"><b>2 cara pakai</b><span>installer, atau .html portabel tanpa hak admin</span></div>
<div class="k"><b>%d skrip uji</b><span>uji otomatis keluarga GC-Ex di repo</span></div></div>
<h3>Versi 2 menit — tiga kalimat yang perlu diingat</h3>
<ul><li><b>Masalah:</b> %s</li>
<li><b>Solusi:</b> %s mengikuti alur kerja itu langkah demi langkah di satu laptop, dengan angka yang bisa dicocokkan ke Surpac.</li>
<li><b>Bukti:</b> dipakai dan diuji pada data tambang emas vein sungguhan oleh pengembangnya (geologist GC); %d catatan perubahan terdokumentasi.</li></ul>
<div class="fig">%s</div><div class="cap">Gambar 1 — Alur kerja keluarga GC-Ex. Bagian yang terang adalah wilayah %s; bagian redup dikerjakan %s.</div>
<div class="catat"><b>Cara memakai dokumen ini.</b> Bab 2–6 menjelaskan produk; Bab 7 berisi pertanyaan yang biasa diajukan beserta usulan jawaban (<span class="tag it">IT</span> / <span class="tag inv">Investor</span>).
Jawab sesuai fakta; yang belum ada (harga, pelanggan, pencatatan HKI) jawab jujur sebagai "belum" atau "sedang disiapkan".</div></div>''' % (
        pitch, A['ver'], N_UJI, masalah, A['nama'], N_LOG, d_alur(k), A['nama'], lain['nama']))
    # 2 apa itu
    B.append('''<div class="bab"><h2>2. Apa itu %s</h2>
<p>%s adalah salah satu dari lima aplikasi keluarga GC-Ex buatan Habil Abdillah, geologist grade control. Pasangannya, <b>%s</b>, %s.</p>
%s
<h3>Untuk siapa</h3><p>%s.</p>
<h3>Posisi terhadap perangkat lunak tambang umum</h3>
<p>Surpac, Leapfrog, Micromine dan sejenisnya adalah perangkat lunak <b>serba guna</b> untuk seluruh siklus tambang. %s <b>bukan pengganti penuh</b>
perangkat lunak itu; ia fokus pada alur kerja grade control dan dibuat <b>berdampingan</b> dengan Surpac: membaca &amp; menulis format Surpac
(<code>.mdl</code>, <code>.str</code>, <code>.ssi</code>, DXF), dan setiap hitungan yang punya cara Surpac memakai cara Surpac sebagai bawaan.</p>
<div class="fig">%s</div><div class="cap">Gambar 2 — Cakupan tahap kerja per aplikasi keluarga GC-Ex (penilaian pengembang); kolom bergaris tebal = %s.</div></div>''' % (
        A['nama'], A['nama'], lain['nama'], lain['peran'],
        tabel(['', A['nama']], [['Peran', A['peran'][0].upper() + A['peran'][1:]], ['Versi saat ini', A['ver']], ['Masukan utama', A['masuk']], ['Keluaran utama', A['keluar']],
                                ['Cara pakai', 'Installer <code>%s-&lt;versi&gt;.exe</code> (per pengguna, tanpa hak admin) <b>atau</b> file <code>%s</code> portabel di Edge / Chrome' % (A['exe'], A['html'])]], w=['22%', '78%']),
        A['untuk'][0].upper() + A['untuk'][1:], A['nama'], g_cakupan(A['kol']), A['nama']))
    # 3 cara kerja
    B.append('''<div class="bab"><h2>3. Bagaimana %s bekerja</h2>
<p>Aplikasi <b>desktop hibrida</b>: tampilan dibangun dengan teknologi web (HTML/JavaScript) dan dijalankan oleh <b>Electron</b> (Chromium + Node.js) sebagai aplikasi Windows biasa.
Pekerjaan berat — membaca block model .mdl berukuran gigabyte, menulis ke workbook Excel yang sudah ada, membaca MS Access — dikerjakan <b>backend Python (FastAPI)</b>
yang berjalan di komputer itu sendiri, hanya di <code>127.0.0.1</code> dengan port acak, dan mati bersama aplikasi.</p>
<div class="fig">%s</div><div class="cap">Gambar 3 — Arsitektur. Semua komponen berjalan di laptop pengguna; tidak ada server luar.</div>
%s</div>''' % (
        A['nama'], d_arsitektur(),
        tabel(['Lapisan', 'Teknologi', 'Catatan'], [
            ['Shell aplikasi', 'Electron %s' % ELECTRON.lstrip('^~'), 'contextIsolation aktif, nodeIntegration mati, sandbox aktif'],
            ['Tampilan &amp; visual', 'HTML / JavaScript satu file, Plotly.js (WebGL)', '3D, sayatan 2D, grafik; tanpa CDN — semua aset dibundel'],
            ['Backend', 'Python, FastAPI, Uvicorn, NumPy, openpyxl, pyodbc', 'dibekukan dengan PyInstaller menjadi gcex-backend.exe'],
            ['Penyimpanan', 'Folder proyek (JSON + salinan file sumber + backup berversi), IndexedDB, SQLite riwayat', 'proyek bisa dipindah ke laptop lain; kunci pemakai mencegah dua orang menyunting bersamaan'],
            ['Installer', 'electron-builder + NSIS, per pengguna', 'tanpa hak administrator, tanpa internet saat pasang'],
            ['Lisensi', 'Ed25519 (kriptografi kunci publik)', 'kunci terikat ID komputer (aplikasi terpasang)']], w=['18%', '40%', '42%'])))
    DUA = tabel(['', 'Aplikasi terpasang', 'File .html portabel'], [
            ['Cara pasang', 'Installer per pengguna (tanpa hak admin)', 'Ekstrak ZIP, buka file di Edge / Chrome — tidak ada yang diinstal'],
            ['Untuk', 'Laptop pribadi / laptop yang boleh memasang program', 'Laptop kantor yang tidak mengizinkan instalasi'],
            ['Folder proyek', 'Ya (mis. D:\\GC-Ex\\Proyek\\…)', 'Ya, format sama; izin folder diberikan lewat browser'],
            ['Backend Python', 'Ya: .mdl sangat besar lewat cache, tulis langsung ke Excel / Access', 'Tidak: .mdl dibaca langsung oleh browser; Excel / Access lewat export'],
            ['Lisensi per komputer', 'Ya', 'Tidak ada pemeriksaan lisensi (lihat Bab 6)']], w=['18%', '41%', '41%'])
    # 4 fitur
    B.append('''<div class="bab"><h2>4. Apa saja yang ditawarkan</h2>
<h3>Dua cara pakai: terpasang atau portabel</h3>%s
<p>Folder proyek berformat sama untuk kedua cara: proyek yang dibuat di aplikasi terpasang bisa dibuka dari file .html dan sebaliknya (diuji otomatis).
Bila file sumber proyek (mis. block model) dipindah, aplikasi mencarinya di subfolder proyek lalu memunculkan jendela <b>Sambungkan file</b> untuk menunjuk lokasi barunya.</p>
<h3>Fitur</h3>%s<h3>Format data</h3>%s
<p>Setiap fitur memiliki tutorial PDF bergambar dengan data latihan fiktif, dan mode Demo di dalam aplikasi memperagakan alur kerjanya langkah demi langkah.</p></div>''' % (
        DUA, tabel(['Kelompok', 'Fitur'], FITUR[k], w=['18%', '82%']), tabel(['Arah', 'Format'], FORMAT[k], w=['18%', '82%'])))
    # 5 kelebihan
    data_besar = 'Block model .mdl &gt; 6 GB di RAM 8 GB; topo / pit .str 500–700 MB; orthofoto 1 GB' if k == 'bm' else 'Assay 200.000 baris; topo / pit .str 500–700 MB; orthofoto 1 GB'
    B.append('''<div class="bab"><h2>5. Kelebihan</h2>%s
<h3>Ukuran dan aktivitas pengembangan</h3>
<div class="fig">%s</div><div class="cap">Gambar 4 — Ukuran kode sumber keluarga GC-Ex per komponen (dihitung dari repo saat dokumen dibangun; pustaka pihak ketiga tidak dihitung).</div>
<div class="fig">%s</div><div class="cap">Gambar 5 — Commit per hari pada riwayat yang tersedia di repo (%d hari terakhir). Setiap commit yang mengubah installer menaikkan versi dan menerbitkan GitHub Release.</div></div>''' % (
        tabel(['Kelebihan', 'Artinya bagi pengguna', 'Bukti / cara mengecek'], [
            ['Offline penuh', 'Aman dipakai di site tanpa sinyal; data tambang tidak keluar dari laptop', 'Tidak ada pemanggilan jaringan; backend hanya 127.0.0.1; tanpa auto-update'],
            ['Bisa tanpa instal', 'Tetap bisa dipakai di laptop kantor yang melarang instalasi program', 'File .html portabel; proyek desktop terbuka di .html dengan isi sama (uji otomatis)'],
            ['Selaras dengan Surpac', 'Angka bisa direkonsiliasi dengan perangkat lunak yang diakui di tambang', 'Cara Surpac jadi bawaan; uji paritas di repo'],
            ['Mengikuti alur kerja GC', 'Langkah di aplikasi = langkah kerja; cepat dipelajari', 'Project Tree berurutan; tutorial per langkah; mode Demo'],
            ['Data besar di laptop biasa', 'Tidak perlu workstation', data_besar],
            ['Proyek tahan pindah', 'Proyek tidak rusak bila file dipindah atau dibuka di laptop lain', 'Backup berversi, kunci pemakai, pencarian &amp; jendela Sambungkan file'],
            ['Iterasi cepat', 'Permintaan lapangan bisa masuk rilis berikutnya dalam hitungan hari', 'Rilis otomatis via GitHub Actions; %d catatan perubahan' % N_LOG],
            ['Teruji otomatis', 'Perubahan tidak diam-diam merusak fitur lama', '%d skrip uji (Playwright untuk tampilan, pytest untuk backend)' % N_UJI]], w=['20%', '38%', '42%']),
        g_ukuran(), g_aktivitas(), len(HARI)))
    # 6 legal
    B.append('''<div class="bab"><h2>6. Status legal</h2>
<div class="catat">Ringkasan dokumen di folder <code>legal/</code> repo dan ketentuan UU Hak Cipta. <b>Ini bukan nasihat hukum</b>; untuk kesepakatan dengan investor atau perusahaan, mintalah pendapat konsultan kekayaan intelektual.</div>
<h3>Yang sudah ada</h3>%s
<h3>Lisensi kepada pengguna</h3>
<div class="fig">%s</div><div class="cap">Gambar 6 — Alur kunci lisensi aplikasi terpasang. Aplikasi hanya memegang kunci publik, jadi kunci tidak bisa dipalsukan tanpa kunci privat pemilik.</div>
<p>Dua hal yang perlu disampaikan terbuka kepada investor: (1) <b>versi .html portabel tidak memeriksa lisensi</b> — kendali pemakaiannya bergantung pada distribusi file dan syarat penggunaan; (2) kode sumber
disimpan di repositori GitHub <b>publik</b>. Publik tidak sama dengan open source: repo tidak memakai lisensi open source, jadi semua hak tetap pada pemilik, tetapi siapa pun dapat membaca kodenya.
Pertimbangkan menjadikan repo privat dan menambahkan pemeriksaan lisensi ringan di versi .html sebelum pembicaraan investasi.</p>
<h3>Yang perlu diperkuat sebelum bicara investasi</h3>%s
<div class="fig">%s</div><div class="cap">Gambar 7 — Jalur rilis: dari commit sampai laptop pengguna.</div></div>''' % (
        tabel(['Aspek', 'Status'], [
            ['Hak cipta', '%s dinyatakan ciptaan Habil Abdillah, dilindungi sebagai Program Komputer menurut UU No. 28 Tahun 2014. Hak cipta timbul otomatis (prinsip deklaratif); pencatatan bukan syarat (Pasal 64 ayat 2). Masa perlindungan program komputer: 50 tahun sejak pertama kali diumumkan (Pasal 59).' % A['nama']],
            ['Syarat penggunaan', '<code>legal/SYARAT_PENGGUNAAN.txt</code>: dilisensikan, bukan dijual; non-eksklusif, tidak dapat dialihkan, dapat dicabut; dilarang menjual, menyewakan, membongkar, dan menghapus tanda hak cipta. Ikut dibundel di installer dan di paket .html portabel.'],
            ['Komponen open source', 'Electron, Chromium, Node.js, Python, FastAPI, Uvicorn, NumPy, Plotly.js, font OFL, dll.; lisensinya (MIT, BSD, Apache-2.0, PSF, OFL) dibundel.'],
            ['Merek pihak lain', '<code>legal/PENAFIAN_MEREK.txt</code>: Surpac, Leapfrog, Micromine, Microsoft dll. disebut hanya untuk kecocokan format; tidak berafiliasi.'],
            ['Tanda hak cipta', '"Copyright © Habil Abdillah 2026" tampil di aplikasi (juga di versi .html); watermark cadangan di aplikasi terpasang.'],
            ['Data contoh', 'Data latihan fiktif (tanpa nama perusahaan, Hole ID atau koordinat proyek nyata).']], w=['20%', '80%']),
        d_lisensi(),
        tabel(['Hal', 'Mengapa penting', 'Langkah'], [
            ['Pencatatan ciptaan di DJKI', 'Bukan syarat hak cipta, tetapi bukti awal kepemilikan yang kuat', 'Ajukan pencatatan program komputer secara daring di DJKI'],
            ['Hubungan kerja dengan perusahaan', 'Pasal 36 UU Hak Cipta: kecuali diperjanjikan lain, pemegang hak cipta atas ciptaan dalam hubungan kerja adalah pihak yang membuat ciptaan; perjanjian kerja bisa mengatur lain', 'Periksa perjanjian kerja / kebijakan HKI perusahaan; bila perlu buat perjanjian tertulis'],
            ['Pemakaian di laptop kantor', 'Versi .html dipakai karena kantor melarang instalasi; investor / perusahaan bisa bertanya soal kepatuhan kebijakan TI', 'Pastikan pemakaian sesuai kebijakan TI; bila perlu minta persetujuan tertulis'],
            ['Merek "GC-Ex"', 'Nama produk adalah aset; belum didaftarkan', 'Cek ketersediaan dan daftarkan merek di DJKI'],
            ['Badan usaha &amp; kontrak', 'Investor berinvestasi ke badan usaha; pelanggan butuh EULA / SLA', 'Siapkan badan usaha, EULA komersial, kebijakan dukungan'],
            ['Kode yang ditulis dengan bantuan AI', 'Sebagian besar kode disusun dengan bantuan asisten AI di bawah arahan, pengujian dan keputusan pemilik', 'Siapkan penjelasan proses; minta konsultan menilai implikasinya']], w=['22%', '40%', '38%']),
        d_rilis()))
    # 7 tanya jawab
    it = [('Dibangun dengan teknologi apa?', 'Electron untuk aplikasi desktop, tampilan HTML / JavaScript dengan Plotly.js untuk 3D, dan backend Python (FastAPI, Uvicorn, NumPy) yang dibekukan dengan PyInstaller. Installer dibuat electron-builder + NSIS.'),
          ('Butuh internet atau server?', 'Tidak. Semua proses di laptop; backend hanya di 127.0.0.1 dengan port acak. Tidak ada telemetri, akun cloud, atau pemeriksaan pembaruan online.'),
          ('Bisa dipakai tanpa instal?', 'Bisa. Aplikasinya satu file .html yang dibuka di Edge / Chrome; folder proyek disimpan di drive lokal (mis. D:) lewat pemilih folder browser. Tanpa backend: Excel / Access lewat export, .mdl dibaca langsung oleh browser.'),
          ('Bagaimana keamanan aplikasinya?', 'Jendela Electron memakai contextIsolation dan sandbox, nodeIntegration mati; halaman bicara ke sistem hanya lewat jembatan preload terbatas. Lisensi diverifikasi tanda tangan Ed25519; kunci privat tidak pernah di repo atau installer.'),
          ('Data disimpan di mana? Bisa dipindah?', 'Di folder proyek (JSON + salinan file sumber + backup berversi), dengan kunci pemakai agar tidak disunting dua orang bersamaan. Folder bisa disalin ke laptop lain; file sumber yang pindah bisa disambungkan ulang lewat jendela Sambungkan file.'),
          ('Bagaimana memastikan hitungannya benar?', 'Cara Surpac menjadi bawaan dan hasil diaudit terhadap Surpac pada data nyata; %d skrip uji otomatis (Playwright + pytest) dijalankan.' % N_UJI),
          ('Bagaimana proses rilis?', 'Setiap push menjalankan GitHub Actions: uji, build backend, build installer, terbit di GitHub Release lengkap dengan dokumen, data latihan, lisensi, catatan rilis dan SHA-256. Versi naik hanya bila isi installer berubah.'),
          ('Apa keterbatasan teknisnya?', 'Hanya Windows 64-bit; satu pengguna per proyek; grafis 3D bergantung GPU; pengembang inti satu orang. Lihat Bab 8.'),
          ('Kodenya open source?', 'Tidak. Repo GitHub saat ini publik agar build gratis, tetapi tanpa lisensi open source; semua hak tetap pada pemilik.')]
    inv = [('Masalah apa yang diselesaikan?', masalah[0].upper() + masalah[1:]),
           ('Siapa pengguna dan pembelinya?', 'Pengguna: %s. Pembeli yang mungkin: perusahaan tambang dan kontraktor tambang. <i>Saat ini dipakai internal oleh pengembang; belum ada pelanggan berbayar.</i>' % A['untuk'].split(' — ')[0]),
           ('Apa bedanya dengan Surpac / Leapfrog?', 'Tidak menggantikan perangkat lunak serba guna itu; fokus pada alur kerja grade control, offline di laptop biasa (bahkan tanpa instal), berbahasa Indonesia dan 4 bahasa lain, dan kompatibel dengan format Surpac.'),
           ('Seberapa matang produknya?', 'Versi masih 0.x (%s %s). Fitur inti lengkap dan diuji pada data nyata satu tambang emas vein; validasi di tambang lain belum ada.' % (A['nama'], A['ver'])),
           ('Siapa timnya?', 'Pengembang tunggal: Habil Abdillah, geologist grade control yang memakai sendiri alat ini. Kekuatan: pemahaman domain dan iterasi cepat. Risiko: ketergantungan pada satu orang.'),
           ('Bagaimana model bisnisnya?', 'Mekanisme lisensi per komputer sudah ada (bisa diberi kedaluwarsa), jadi langganan tahunan atau lisensi per kursi bisa langsung dijalankan untuk versi terpasang. <i>Harga belum ditetapkan</i>; versi .html portabel perlu kebijakan lisensi tersendiri.'),
           ('Apa yang melindungi dari peniru?', 'Hak cipta, pengetahuan domain di alur kerja, kepercayaan karena angka cocok dengan Surpac, dan kecepatan iterasi. Kode yang publik melemahkan kerahasiaan — pertimbangkan repo privat dan pencatatan HKI.'),
           ('Untuk apa dana investasi?', 'Usulan: tim kecil (programmer kedua, QA), validasi di beberapa tambang, legal &amp; HKI, dukungan pelanggan dan pelatihan, versi native Qt dan kolaborasi multi-pengguna.')]
    for q, a, w in FAQ_KHUSUS[k]:
        (it if w in ('it', 'dua') else inv).insert(3, (q, a))
    B.append('<div class="bab"><h2>7. Pertanyaan yang sering diajukan &amp; usulan jawaban</h2><h3>Dari ahli IT / programmer</h3>' + ''.join(qa(q, a, 'it') for q, a in it) +
             '<h3>Dari investor teknologi</h3>' + ''.join(qa(q, a, 'inv') for q, a in inv) +
             '<div class="ok"><b>Tips menjawab.</b> Bedakan tegas "sudah ada", "sedang diuji", dan "rencana". Tunjukkan demo langsung (mode Demo) dan satu contoh rekonsiliasi angka GC-Ex vs Surpac. '
             'Jangan menyebut nama tambang, data, atau koordinat nyata tanpa izin perusahaan.</div></div>')
    # 8-9
    istilah = [['Grade control (GC)', 'Memastikan batuan yang digali dikirim ke tujuan yang benar (bijih ke pabrik / stockpile, waste ke timbunan)'],
               ['Block model', 'Model 3D tubuh bijih yang dipotong menjadi kubus; tiap kubus punya kadar dan berat jenis']]
    istilah += ([['Flitch', 'Lapisan horizontal penggalian (mis. setebal 2,5 m)'], ['Dig block / dig plan', 'Poligon batas penggalian per jenis material di satu flitch, dan peta kerja untuk lapangan'],
                 ['As-mined', 'Volume yang benar-benar tergali menurut survei, dibandingkan dengan rencana'], ['Rekonsiliasi', 'Membandingkan tonase dan kadar rencana, model, dan realisasi'],
                 ['Rotasi block model', 'Model yang sumbunya diputar mengikuti arah urat; posisi blok harus diputar balik ke koordinat lapangan']] if k == 'bm' else
                [['Collar / survey / assay', 'Posisi mulut lubang bor, arah lubang, dan hasil analisis kadar per interval'], ['Domain / vein', 'Tubuh geologi (mis. urat kuarsa) yang diestimasi terpisah'],
                 ['Variogram', 'Ukuran seberapa jauh kadar masih saling berkaitan'], ['Estimasi (Kriging / ID²)', 'Cara menghitung kadar tiap blok dari sampel bor di sekitarnya'],
                 ['Klasifikasi M/I/I', 'Tingkat keyakinan sumber daya: Measured, Indicated, Inferred']])
    istilah.append(['Surpac', 'Perangkat lunak tambang komersial yang menjadi acuan di banyak tambang'])
    B.append('''<div class="bab"><h2>8. Keterbatasan jujur &amp; langkah berikut</h2>%s
<h2 style="margin-top:18px">9. Istilah untuk pendengar non-tambang</h2>%s
<p class="cap" style="margin-top:14px">Dokumen ini dibangun otomatis dari repo GC-Ex (<code>docs/tentang/buat_tentang.py</code>); versi, jumlah uji dan grafik ikut terbarui setiap kali dibangun ulang. Dokumen pasangan: Tentang %s.</p></div>''' % (
        tabel(['Keterbatasan saat ini', 'Langkah berikut'], BATAS[k] + [['Belum ada pencatatan HKI, merek, badan usaha, harga; versi .html tanpa pemeriksaan lisensi', 'Lihat Bab 6']], w=['55%', '45%']),
        tabel(['Istilah', 'Arti singkat'], istilah, w=['26%', '74%']), lain['nama']))
    return '<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><title>Tentang %s</title><style>%s</style></head><body>%s</body></html>' % (A['nama'], CSS, '\n'.join(B))

def cetak():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for k in ('bm', 'dh'):
            A = APP[k]; out = ROOT / 'docs' / A['file']
            tmp = HERE / ('_tentang_%s.html' % k); tmp.write_text(bangun(k), encoding='utf-8')
            pg = b.new_page(); pg.goto(tmp.as_uri()); pg.wait_for_timeout(500)
            pg.pdf(path=str(out), format='A4', print_background=True, display_header_footer=True, header_template='<span></span>',
                   footer_template='<div style="font-size:7pt;color:#5C6672;width:100%%;padding:0 15mm;display:flex;justify-content:space-between;font-family:Inter,sans-serif"><span>Tentang %s · Copyright © Habil Abdillah 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>' % A['nama'],
                   margin={'top': '16mm', 'bottom': '16mm', 'left': '15mm', 'right': '15mm'})
            pg.close(); tmp.unlink()
            print('OK', out, out.stat().st_size, 'byte')
        b.close()

if __name__ == '__main__':
    cetak()
