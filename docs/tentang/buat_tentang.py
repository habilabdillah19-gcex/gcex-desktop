# -*- coding: utf-8 -*-
"""Bangun docs/Tentang_GCEx.pdf — "Tentang GC-Ex": panduan menjawab pertanyaan Ahli IT / Programmer dan Investor
teknologi tentang GC-Ex Drillhole & Block Model for Desktop (pemilik, 23 Nov 2026).

Isi diambil dari repo (versi, jumlah uji, catatan perubahan) supaya angka selalu sesuai saat dibangun ulang.
Diagram = SVG tulisan tangan; grafik = matplotlib (SVG); PDF dicetak Chromium (Playwright).
Pakai: python docs/tentang/buat_tentang.py
"""
import io, json, os, re, subprocess, collections, datetime, glob, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = ROOT / 'docs' / 'Tentang_GCEx.pdf'

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

def g_cakupan():
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
    ax.set_xlim(0, len(app)); ax.set_ylim(len(tahap), 0)
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
    return s + '</svg>'

def d_alur():
    W, H = 660, 250
    s = '<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">%s' % (W, H, DEFS)
    s += '<rect x="4" y="8" width="652" height="98" rx="10" fill="#F3EDE4"/><text x="16" y="26" font-size="10.5" font-weight="600" fill="%s">GC-Ex DRILLHOLE — dari data bor ke block model</text>' % COPPER
    a = [('Data bor', 'collar·survey·assay'), ('Validasi', 'upsert·kampanye'), ('Pemodelan', 'domain·vein RBF'), ('Geostatistik', 'variogram·KNA'), ('Estimasi', 'OK·ID²·sub-blok'), ('Reporting', 'pit·topo·M/I/I')]
    for i, (t, u) in enumerate(a):
        x = 14 + i * 107; s += kotak(x, 36, 95, 58, t, u, fill='white', stroke=COPPER, fs=10.5)
        if i: s += panah(x - 12, 65, x - 2, 65)
    s += '<rect x="4" y="142" width="652" height="102" rx="10" fill="#E6EAF0"/><text x="16" y="236" font-size="10.5" font-weight="600" fill="%s">GC-Ex BLOCK MODEL — dari block model ke tambang harian</text>' % NAVY
    b = [('Import BM', '.mdl / CSV'), ('Flitch aktif', 'sayatan 2D'), ('Dig block', 'otomatis·manual'), ('Dig plan', 'PDF·STR·DXF'), ('As-mined', 'pick-up survei'), ('Rekonsiliasi', 'register Excel·Access')]
    for i, (t, u) in enumerate(b):
        x = 14 + i * 107; s += kotak(x, 152, 95, 58, t, u, fill='white', stroke=NAVY, fs=10.5)
        if i: s += panah(x - 12, 181, x - 2, 181)
    s += '<polyline points="596,96 596,122 61,122 61,149" fill="none" stroke="%s" stroke-width="1.6" marker-end="url(#ah)"/>' % GOLD
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

B = []
B.append('''<div class="sampul"><div><div class="logo">GC-Ex<small>GRADE CONTROL EXCELLENCE</small></div></div>
<div><h1>Tentang GC-Ex</h1><div class="garis"></div>
<div class="sub">GC-Ex Drillhole &amp; GC-Ex Block Model for Desktop — apa itu, bagaimana bekerja, apa yang ditawarkan,
kelebihan, status legal, dan cara menjawab pertanyaan dari <b>ahli IT / programmer</b> maupun <b>investor teknologi</b>.</div></div>
<div class="meta">Versi dokumen: %s · GC-Ex Block Model %s · GC-Ex Drillhole %s<br>Copyright © Habil Abdillah 2026 · Dokumen internal pemilik, bukan nasihat hukum atau investasi.</div></div>''' % (TGL, V['bm'], V['dh']))

# 1. ringkasan
B.append('''<div class="bab"><h2>1. Jawaban singkat (30 detik)</h2>
<p class="lead"><b>GC-Ex</b> (Grade Control Excellence) adalah perangkat lunak desktop Windows untuk <b>grade control tambang</b>:
mengolah data bor menjadi model geologi dan block model (<b>GC-Ex Drillhole</b>), lalu memakai block model itu untuk pekerjaan
tambang harian — dig block, dig plan, as-mined, rekonsiliasi (<b>GC-Ex Block Model</b>). Seluruhnya berjalan <b>offline di
laptop pengguna</b>, membaca &amp; menulis format Surpac, dan hasil hitungnya diaudit terhadap Surpac.</p>
<div class="kartu">
<div class="k"><b>2 aplikasi inti</b><span>Drillhole (pemodelan &amp; estimasi) + Block Model (operasi harian)</span></div>
<div class="k"><b>100%% offline</b><span>tanpa cloud, tanpa telemetri, tanpa auto-update</span></div>
<div class="k"><b>%d skrip uji</b><span>uji otomatis tampilan &amp; backend di repo</span></div>
<div class="k"><b>%d catatan rilis</b><span>riwayat perubahan terdokumentasi di README</span></div></div>
<h3>Versi 2 menit — tiga kalimat yang perlu diingat</h3>
<ul><li><b>Masalah:</b> pekerjaan grade control harian (membuat dig block, menghitung tonase &amp; kadar yang akan digali, mencatat yang benar-benar tergali)
banyak dikerjakan manual atau dengan perangkat lunak tambang umum yang mahal, berat, dan tidak mengikuti alur kerja harian tim GC.</li>
<li><b>Solusi:</b> GC-Ex mengikuti alur kerja itu langkah demi langkah, dari data bor sampai rekonsiliasi, di satu laptop, dengan angka yang bisa dicocokkan ke Surpac.</li>
<li><b>Bukti:</b> dipakai dan diuji pada data tambang emas vein sungguhan oleh pengembangnya (geologist GC), dengan block model .mdl lebih dari 6 GB di laptop RAM 8 GB.</li></ul>
<div class="fig">%s</div><div class="cap">Gambar 1 — Alur kerja yang dicakup GC-Ex. Drillhole menghasilkan block model; Block Model memakainya untuk tambang harian; bor infill memperbarui model.</div>
<div class="catat"><b>Cara memakai dokumen ini.</b> Bab 2–6 menjelaskan produk; Bab 7 adalah daftar pertanyaan yang biasa diajukan beserta usulan jawaban,
ditandai <span class="tag it">IT</span> atau <span class="tag inv">Investor</span>. Jawab sesuai fakta; bagian yang belum ada (harga, pelanggan, pencatatan HKI) jawab jujur sebagai "belum" atau "sedang disiapkan".</div></div>''' % (N_UJI, N_LOG, d_alur()))

# 2. apa itu
B.append('''<div class="bab"><h2>2. Apa itu GC-Ex Drillhole dan GC-Ex Block Model</h2>
<p>GC-Ex adalah keluarga aplikasi buatan Habil Abdillah, geologist grade control. Dokumen ini membahas dua aplikasi intinya.
Aplikasi keluarga lainnya (DB-Ex, Ore Works, Pit Studio) disebut sebagai konteks.</p>
%s
<h3>Untuk siapa</h3>
<ul><li><b>GC-Ex Drillhole:</b> geologist pemodelan / resource geologist di tambang — membangun domain vein, estimasi block model, laporan sumber daya.</li>
<li><b>GC-Ex Block Model:</b> junior grade control dan short-term / junior mine planner — pekerjaan harian per flitch: dig block, dig plan, as-mined, laporan produksi.</li></ul>
<h3>Posisi terhadap perangkat lunak tambang umum</h3>
<p>Surpac, Leapfrog, Micromine dan sejenisnya adalah perangkat lunak <b>serba guna</b> untuk seluruh siklus tambang. GC-Ex <b>bukan pengganti penuh</b>
perangkat lunak itu; GC-Ex fokus pada alur kerja <b>grade control harian</b> dan dibuat agar <b>berdampingan</b> dengan Surpac: membaca &amp; menulis format Surpac
(<code>.mdl</code>, <code>.str</code>, <code>.ssi</code>, DXF), dan setiap hitungan yang punya cara Surpac memakai cara Surpac sebagai bawaan supaya hasil bisa direkonsiliasi.</p>
<div class="fig">%s</div><div class="cap">Gambar 2 — Cakupan tahap kerja per aplikasi keluarga GC-Ex (penilaian pengembang). "Inti" = fitur utama; "sebagian" = tersedia sebagai pendukung.</div></div>''' % (
    tabel(['', 'GC-Ex Drillhole', 'GC-Ex Block Model'], [
        ['Peran', 'Dari data bor ke block model', 'Dari block model ke tambang harian'],
        ['Versi saat ini', V['dh'], V['bm']],
        ['Masukan utama', 'Collar, survey, assay, geologi (CSV / Excel); wireframe; topografi &amp; pit (.str / .dxf)', 'Block model (.mdl Surpac / CSV); topografi, pit, pick-up survei; orthofoto'],
        ['Keluaran utama', 'Domain / solid vein, variogram, block model GC (.mdl), laporan grade × tonase + klasifikasi', 'Dig block &amp; dig plan (PDF / STR / DXF), model as-mined, register poligon Excel / Access, laporan harian–bulanan'],
        ['Installer', 'GC-Ex-Drillhole-Setup-&lt;versi&gt;.exe', 'GC-Ex-Setup-&lt;versi&gt;.exe']], w=['18%', '41%', '41%']), g_cakupan()))

# 3. cara kerja
B.append('''<div class="bab"><h2>3. Bagaimana GC-Ex bekerja</h2>
<p>GC-Ex adalah aplikasi <b>desktop hibrida</b>: tampilannya dibangun dengan teknologi web (HTML/JavaScript) dan dijalankan oleh <b>Electron</b>
(Chromium + Node.js) sebagai aplikasi Windows biasa. Pekerjaan berat yang tidak cocok di browser — membaca block model .mdl berukuran gigabyte,
menulis ke workbook Excel yang sudah ada, membaca database MS Access — dikerjakan oleh <b>backend Python (FastAPI)</b> yang dijalankan aplikasi
di komputer itu sendiri, hanya di alamat <code>127.0.0.1</code> dengan port acak, dan dimatikan saat aplikasi ditutup.</p>
<div class="fig">%s</div><div class="cap">Gambar 3 — Arsitektur. Semua komponen berjalan di laptop pengguna; tidak ada server luar.</div>
%s
<h3>Mesin hitung</h3>
<p>Perhitungan geologi dikerjakan di kode GC-Ex sendiri (bukan pustaka hitung pihak ketiga): interpolasi permukaan vein dengan RBF, variogram dan
Kriging Neighbourhood Analysis, estimasi Ordinary Kriging / ID² dengan sub-blok di batas solid, triangulasi (TIN) untuk permukaan, dan laporan
grade × tonase dengan constraint topografi / pit / domain. Prinsip yang dipegang: <b>angka laporan harus sama dengan Surpac</b>; tampilan boleh berbeda.</p></div>''' % (d_arsitektur(), tabel(['Lapisan', 'Teknologi', 'Catatan'], [
    ['Shell aplikasi', 'Electron %s' % ELECTRON.lstrip('^~'), 'contextIsolation aktif, nodeIntegration mati, sandbox aktif'],
    ['Tampilan &amp; visual', 'HTML / JavaScript satu file, Plotly.js (WebGL)', '3D, sayatan 2D, grafik; tanpa CDN — semua aset dibundel'],
    ['Backend', 'Python, FastAPI, Uvicorn, NumPy, openpyxl, pyodbc', 'dibekukan dengan PyInstaller menjadi gcex-backend.exe'],
    ['Penyimpanan', 'IndexedDB (proyek), SQLite (gcex_proyek.db), file kerja', 'proyek bisa dipindah ke laptop lain untuk dilanjutkan'],
    ['Installer', 'electron-builder + NSIS, per pengguna', 'tanpa hak administrator, tanpa internet saat pasang'],
    ['Lisensi', 'Ed25519 (kriptografi kunci publik)', 'kunci terikat ID komputer, satu file lisensi untuk semua aplikasi']], w=['18%', '40%', '42%'])))

# 4. yang ditawarkan
B.append('''<div class="bab"><h2>4. Apa saja yang ditawarkan</h2>
<h3>GC-Ex Drillhole — pemodelan &amp; estimasi</h3>
%s
<h3>GC-Ex Block Model — operasi tambang harian</h3>
%s
<h3>Format data</h3>
%s
<p>Kedua aplikasi juga punya: Project Tree mengikuti urutan alur kerja, mode demo terpandu, 10 palet warna, 5 bahasa antarmuka
(Indonesia, English UK / US, Español, Basa Sunda — tahap 1), alat ukur jarak 3D / 2D, dan tutorial PDF bergambar dengan data latihan fiktif.</p></div>''' % (
    tabel(['Kelompok', 'Fitur'], [
        ['Database bor', 'Import collar / survey / assay / geologi dengan header dinamis; validasi; database per kampanye; upsert bor infill; filter AND / OR; export terfilter'],
        ['Pemodelan geologi', 'Geomodeller Vein (domain vein, flag otomatis dari kadar, koreksi interaktif, string HW/FW, solid RBF), vein bercabang, struktur dip / dip azimuth, sesar 3D dengan offset &amp; urutan umur; menyerap wireframe Leapfrog menjadi domain yang bisa diedit'],
        ['Geostatistik', 'Statistik per domain, komposit, top-cut, variogram &amp; anisotropi, KNA, estimasi per lapisan (unfold)'],
        ['Estimasi', 'Block model dari nol (kerangka AOI) atau melanjutkan model lama; Ordinary Kriging / ID²; sub-blok &amp; proporsi volume; estimasi waste; radius pencarian &amp; area pengaruh'],
        ['Reporting', 'Grade × tonase dengan constraint topografi / pit / domain / RL; beberapa desain pit; progres topo-ke-topo; klasifikasi Measured / Indicated / Inferred'],
        ['Pendukung', 'Plan bor, Ore Geometry Studio (long section, ore shoot), orthofoto di-drape ke topografi, export .mdl / .str / DXF']], w=['18%', '82%']),
    tabel(['Kelompok', 'Fitur'], [
        ['Block model', 'Import .mdl Surpac (termasuk &gt; 6 GB di RAM 8 GB) atau CSV; block model terotasi (bearing); filter &amp; SG; kelas kadar &amp; warna .ssi Surpac'],
        ['Flitch &amp; dig block', 'Flitch aktif, sayatan 2D, orthofoto resolusi tinggi; dig block otomatis &amp; manual; additional flagging (garis ganda); pemeriksaan sebelum dig plan terbit; preset kelas kadar &amp; tujuan material'],
        ['Dig plan', 'Layout &amp; plot PDF dengan kop, legenda, skala; export STR / DXF dengan string number sesuai warna'],
        ['As-mined', 'Atap dari pick-up survei, lantai dari DTM, kunci per tanggal-shift; Solid Vein Aktual; model as-mined (.mdl)'],
        ['Laporan', 'Grade × tonase dalam constraint, ringkasan harian, rekap per flitch, laporan mingguan / bulanan, laporan per desain pit, rekonsiliasi'],
        ['Integrasi', 'Register poligon langsung ke workbook Excel yang sudah ada (rumus &amp; makro tetap utuh) dan ke MS Access']], w=['18%', '82%']),
    tabel(['Arah', 'Format'], [
        ['Baca', 'Surpac .mdl, .str, .ssi; DXF; CSV / Excel; GeoTIFF / JPG + world file; wireframe; MS Access .accdb / .mdb'],
        ['Tulis', 'Surpac .mdl, .str (+ .ssi); DXF; CSV; Excel .xlsx; PDF; PNG; MS Access']], w=['18%', '82%'])))

# 5. kelebihan
B.append('''<div class="bab"><h2>5. Kelebihan</h2>
%s
<h3>Ukuran dan aktivitas pengembangan</h3>
<div class="fig">%s</div><div class="cap">Gambar 4 — Ukuran kode sumber per komponen (dihitung dari repo saat dokumen dibangun). Pustaka pihak ketiga (Plotly, Electron, Python) tidak dihitung.</div>
<div class="fig">%s</div><div class="cap">Gambar 5 — Commit per hari pada riwayat yang tersedia di repo (%s hari terakhir). Setiap commit yang mengubah installer menaikkan versi dan menerbitkan GitHub Release.</div></div>''' % (
    tabel(['Kelebihan', 'Artinya bagi pengguna', 'Bukti / cara mengecek'], [
        ['Offline penuh', 'Aman dipakai di site tanpa sinyal; data tambang tidak keluar dari laptop', 'Tidak ada pemanggilan jaringan; backend hanya 127.0.0.1; publish: null (tanpa auto-update)'],
        ['Selaras dengan Surpac', 'Angka bisa direkonsiliasi dengan perangkat lunak yang diakui di tambang', 'Cara Surpac jadi bawaan untuk dig block, as-mined dan reporting; uji paritas di repo'],
        ['Mengikuti alur kerja GC', 'Langkah di aplikasi = langkah kerja harian tim; cepat dipelajari junior', 'Project Tree berurutan; tutorial per langkah; mode demo'],
        ['Data besar di laptop biasa', 'Tidak perlu workstation', 'Block model .mdl &gt; 6 GB di RAM 8 GB; topo / pit .str 500–700 MB; assay 200.000 baris; orthofoto 1 GB'],
        ['Terintegrasi dengan Excel &amp; Access', 'Register tetap di file kantor yang sudah ada', 'Penulisan sel input saja, rumus / makro / grafik tetap, cadangan otomatis'],
        ['Iterasi cepat', 'Permintaan lapangan bisa masuk rilis berikutnya dalam hitungan hari', 'Rilis otomatis via GitHub Actions; %d catatan perubahan' % N_LOG],
        ['Teruji otomatis', 'Perubahan tidak diam-diam merusak fitur lama', '%d skrip uji (Playwright untuk tampilan, pytest untuk backend)' % N_UJI],
        ['Lisensi aman', 'Pemakaian terkendali per komputer', 'Tanda tangan Ed25519; kunci privat tidak pernah ada di repo / Release']], w=['20%', '38%', '42%']),
    g_ukuran(), g_aktivitas(), len(HARI)))

# 6. legal
B.append('''<div class="bab"><h2>6. Status legal</h2>
<div class="catat">Bagian ini merangkum dokumen di folder <code>legal/</code> repo dan ketentuan UU Hak Cipta. <b>Ini bukan nasihat hukum</b>; untuk
kesepakatan dengan investor atau perusahaan, mintalah pendapat konsultan kekayaan intelektual.</div>
<h3>Yang sudah ada</h3>
%s
<h3>Lisensi kepada pengguna</h3>
<div class="fig">%s</div><div class="cap">Gambar 6 — Alur kunci lisensi. Aplikasi hanya memegang kunci publik, jadi kunci tidak bisa dipalsukan tanpa kunci privat pemilik.</div>
%s
<h3>Yang perlu diperkuat sebelum bicara investasi</h3>
%s
<div class="fig">%s</div><div class="cap">Gambar 7 — Jalur rilis: dari commit sampai laptop pengguna.</div></div>''' % (
    tabel(['Aspek', 'Status'], [
        ['Hak cipta', 'GC-Ex dinyatakan ciptaan Habil Abdillah, dilindungi sebagai Program Komputer menurut UU No. 28 Tahun 2014. Hak cipta timbul otomatis (prinsip deklaratif); pencatatan bukan syarat untuk mendapatkan hak cipta (Pasal 64 ayat 2). Masa perlindungan program komputer: 50 tahun sejak pertama kali diumumkan (Pasal 59).'],
        ['Syarat penggunaan', '<code>legal/SYARAT_PENGGUNAAN.txt</code> (versi 2026-10-29): perangkat lunak dilisensikan, bukan dijual; lisensi non-eksklusif, tidak dapat dialihkan, dapat dicabut; larangan menjual, menyewakan, membongkar (reverse engineering) dan menghapus tanda hak cipta.'],
        ['Komponen open source', 'Electron, Chromium, Node.js, Python, FastAPI, Uvicorn, NumPy, Plotly.js, font OFL, dll. Lisensi masing-masing (MIT, BSD, Apache-2.0, PSF, OFL, dll.) dibundel di folder legal dan menu Bantuan.'],
        ['Merek pihak lain', '<code>legal/PENAFIAN_MEREK.txt</code>: Surpac, Leapfrog, Micromine, Microsoft, dll. disebut hanya untuk menjelaskan kecocokan format; GC-Ex tidak berafiliasi dengan pemilik merek tersebut.'],
        ['Tanda hak cipta', '"Copyright © Habil Abdillah 2026" tampil di setiap aplikasi; watermark cadangan muncul bila tulisan itu dihapus.'],
        ['Data contoh', 'Data latihan di repo dan Release fiktif (tanpa nama perusahaan, Hole ID atau koordinat proyek nyata).']], w=['20%', '80%']),
    d_lisensi(),
    '<p>Kode sumber disimpan di GitHub dalam repositori <b>publik</b> (agar build otomatis tidak memakan kuota). <b>Publik tidak sama dengan open source</b>: '
    'repo tidak memakai lisensi open source, jadi semua hak tetap pada pemilik dan syarat penggunaan tetap berlaku. Bagi investor, hal ini perlu disampaikan '
    'terbuka karena siapa pun dapat membaca kodenya; nilai produk terletak pada pengetahuan domain, kecepatan pengembangan, dan kepercayaan pengguna, bukan '
    'pada kerahasiaan kode. Pertimbangkan menjadikan repo privat kembali sebelum pembicaraan investasi.</p>',
    tabel(['Hal', 'Mengapa penting', 'Langkah'], [
        ['Pencatatan ciptaan di DJKI', 'Bukan syarat hak cipta, tetapi menjadi bukti awal kepemilikan yang kuat di hadapan investor atau pengadilan', 'Ajukan pencatatan program komputer GC-Ex (dan DB-Ex, Ore Works, Pit Studio) secara daring di DJKI'],
        ['Hubungan kerja dengan perusahaan', 'Pasal 36 UU Hak Cipta: kecuali diperjanjikan lain, pencipta dan pemegang hak cipta atas ciptaan dalam hubungan kerja adalah pihak yang membuat ciptaan. Perjanjian kerja bisa mengatur lain', 'Periksa perjanjian kerja / kebijakan HKI perusahaan; bila perlu buat surat pernyataan atau perjanjian tertulis tentang kepemilikan GC-Ex'],
        ['Pemakaian data perusahaan', 'Investor akan bertanya apakah produk dibangun dari data milik perusahaan', 'Tegaskan data contoh fiktif; data nyata tidak pernah masuk repo / Release'],
        ['Merek "GC-Ex" / "Grade Control Excellence"', 'Nama produk adalah aset; belum ada pendaftaran merek', 'Cek ketersediaan dan daftarkan merek di DJKI pada kelas perangkat lunak'],
        ['Badan usaha &amp; kontrak lisensi', 'Investor berinvestasi ke badan usaha, bukan ke perorangan; pelanggan perusahaan butuh kontrak (EULA, SLA)', 'Siapkan badan usaha (mis. PT perorangan / PT), EULA komersial, kebijakan dukungan'],
        ['Kode yang ditulis dengan bantuan AI', 'Sebagian besar kode disusun dengan bantuan asisten AI di bawah arahan, pengujian dan keputusan pemilik', 'Siapkan penjelasan proses pengembangan; minta konsultan menilai implikasinya terhadap klaim hak cipta']], w=['22%', '40%', '38%']),
    d_rilis()))

# 7. tanya jawab
qa_it = [
    ('Dibangun dengan teknologi apa?', 'Electron (Chromium + Node.js) untuk aplikasi desktop, tampilan HTML / JavaScript dengan Plotly.js untuk 3D, dan backend Python (FastAPI, Uvicorn, NumPy) yang dibekukan dengan PyInstaller. Installer dibuat electron-builder + NSIS.'),
    ('Kenapa Electron, bukan aplikasi native?', 'GC-Ex awalnya aplikasi HTML offline; Electron memungkinkan kode yang sama menjadi aplikasi Windows tanpa menulis ulang, dengan akses file dan proses lokal. Penampil Qt (PySide6) untuk Block Model sedang diuji berdampingan sebagai jalur native.'),
    ('Apakah butuh internet atau server?', 'Tidak. Semua proses di laptop. Backend Python hanya mendengar di 127.0.0.1 dengan port acak dan mati bersama aplikasi. Tidak ada telemetri, akun cloud, atau pemeriksaan pembaruan online.'),
    ('Bagaimana keamanan aplikasinya?', 'Jendela Electron memakai contextIsolation, sandbox, dan nodeIntegration dimatikan; halaman hanya bicara ke sistem lewat jembatan preload yang terbatas. Lisensi diverifikasi dengan tanda tangan Ed25519; kunci privat tidak pernah ada di repo atau installer.'),
    ('Data disimpan di mana? Bisa dipindah?', 'Proyek disimpan lokal (IndexedDB dan SQLite <code>gcex_proyek.db</code> di folder proyek, dengan tabel riwayat perubahan). Proyek bisa disalin ke laptop lain untuk dilanjutkan rekan.'),
    ('Seberapa besar data yang sanggup diolah?', 'Diuji: block model .mdl lebih dari 6 GB di RAM 8 GB / VRAM 4 GB (indeks RL di luar RAM), topografi / pit .str 500–700 MB dibaca per potongan, assay 200.000 baris, orthofoto 1 GB.'),
    ('Bagaimana memastikan hitungannya benar?', 'Setiap hitungan yang punya cara Surpac memakai cara Surpac sebagai bawaan, dan hasil diaudit terhadap laporan Surpac pada data nyata. %d skrip uji otomatis dijalankan; uji tampilan memakai Playwright, backend memakai pytest.' % N_UJI),
    ('Bagaimana proses rilis dan versi?', 'Setiap push ke cabang utama menjalankan GitHub Actions: uji, build backend, cek backend menyala, build installer, lalu terbit di GitHub Release lengkap dengan dokumen, data latihan, lisensi, catatan rilis dan SHA-256. Versi tiap aplikasi naik hanya bila isi installernya berubah.'),
    ('Bisa diintegrasikan dengan sistem lain?', 'Lewat format file standar tambang (Surpac .mdl / .str, DXF, CSV, Excel) dan langsung ke workbook Excel / database MS Access. API backend lokal ada, tetapi saat ini hanya untuk aplikasi itu sendiri.'),
    ('Apa keterbatasan teknisnya?', 'Hanya Windows 64-bit; satu pengguna per proyek (belum kolaborasi bersamaan); grafis 3D bergantung GPU (sudah diuji di Intel Iris Xe); block model terotasi baru lewat CSV; pengembang inti satu orang.'),
    ('Kodenya open source?', 'Tidak. Repo GitHub saat ini publik agar build gratis, tetapi tanpa lisensi open source; semua hak tetap pada pemilik. Komponen pihak ketiga tetap di bawah lisensinya masing-masing.')]
qa_inv = [
    ('Masalah apa yang diselesaikan dan seberapa penting?', 'Selisih antara rencana dan realisasi tambang (dilusi, ore loss, salah tujuan material) langsung menjadi kerugian. GC-Ex mempercepat dan merapikan keputusan harian grade control serta pencatatannya, dengan angka yang bisa direkonsiliasi ke Surpac.'),
    ('Siapa penggunanya dan siapa pembelinya?', 'Pengguna: geologist grade control, junior GC, short-term mine planner. Pembeli yang mungkin: perusahaan tambang (departemen geologi / mine planning) dan kontraktor tambang. <i>Saat ini dipakai internal oleh pengembang; belum ada pelanggan berbayar.</i>'),
    ('Apa bedanya dengan Surpac / Leapfrog?', 'GC-Ex tidak berusaha menggantikan perangkat lunak serba guna itu. GC-Ex fokus pada alur kerja GC harian, berjalan offline di laptop biasa, berbahasa Indonesia, dan tetap kompatibel dengan format Surpac sehingga bisa dipakai berdampingan.'),
    ('Seberapa matang produknya?', 'Versi masih 0.x: Block Model %s, Drillhole %s. Fitur inti lengkap dan diuji pada data nyata satu tambang emas vein; validasi di tambang lain dan pengguna di luar pengembang belum ada.' % (V['bm'], V['dh'])),
    ('Siapa timnya?', 'Pengembang tunggal: Habil Abdillah, geologist grade control yang memakai sendiri alat ini. Kekuatan: pemahaman domain langsung dan iterasi cepat. Risiko: ketergantungan pada satu orang — bagian dari rencana penggunaan dana.'),
    ('Bagaimana model bisnisnya?', 'Mekanisme lisensi per komputer sudah ada (kunci bertanda tangan, bisa diberi tanggal kedaluwarsa), sehingga model langganan tahunan atau lisensi per kursi bisa langsung dijalankan. <i>Harga belum ditetapkan</i> — siapkan angka sebelum pertemuan.'),
    ('Apa yang melindungi dari peniru?', 'Hak cipta atas kode, pengetahuan domain grade control yang tertanam di alur kerja, kepercayaan karena angka cocok dengan Surpac, dan kecepatan iterasi. Kode yang terlihat publik melemahkan kerahasiaan — pertimbangkan repo privat dan pencatatan HKI.'),
    ('Bagaimana status kepemilikannya?', 'Hak cipta dinyatakan atas nama Habil Abdillah. Sebelum investasi, pastikan tidak ada klaim perusahaan tempat bekerja (Pasal 36 UU Hak Cipta dan perjanjian kerja) dan lakukan pencatatan ciptaan di DJKI. Lihat Bab 6.'),
    ('Untuk apa dana investasi?', 'Usulan: (1) tim kecil (programmer kedua, QA) untuk mengurangi risiko satu orang; (2) validasi di beberapa tambang; (3) legal &amp; HKI; (4) dukungan pelanggan dan pelatihan; (5) versi native Qt dan kolaborasi multi-pengguna.'),
    ('Apakah bisa dipakai di luar Indonesia / komoditas lain?', 'Antarmuka sudah 5 bahasa (tahap 1). Data latihan mencakup vein emas, laterit nikel, bauksit dan stratiform; alur kerja grade control berlaku umum untuk tambang terbuka.')]
B.append('<div class="bab"><h2>7. Pertanyaan yang sering diajukan &amp; usulan jawaban</h2><h3>Dari ahli IT / programmer</h3>' + ''.join(qa(q, a, 'it') for q, a in qa_it) +
         '<h3>Dari investor teknologi</h3>' + ''.join(qa(q, a, 'inv') for q, a in qa_inv) +
         '<div class="ok"><b>Tips menjawab.</b> Bedakan tegas "sudah ada", "sedang diuji", dan "rencana". Tunjukkan demo langsung (mode Demo di aplikasi) dan satu contoh rekonsiliasi angka GC-Ex vs Surpac. '
         'Jangan menyebut nama tambang, data, atau koordinat nyata tanpa izin perusahaan.</div></div>')

# 8. keterbatasan & peta jalan, istilah
B.append('''<div class="bab"><h2>8. Keterbatasan jujur &amp; langkah berikut</h2>
%s
<h2 style="margin-top:18px">9. Istilah untuk pendengar non-tambang</h2>
%s
<p class="cap" style="margin-top:14px">Dokumen ini dibangun otomatis dari repo GC-Ex (<code>docs/tentang/buat_tentang.py</code>); angka versi, jumlah uji dan grafik ikut terbarui setiap kali dibangun ulang.</p></div>''' % (
    tabel(['Keterbatasan saat ini', 'Langkah berikut'], [
        ['Pengembang tunggal', 'Tambah programmer kedua; dokumentasi teknis sudah tersedia (Petunjuk Teknis)'],
        ['Baru divalidasi pada data satu tambang (emas vein)', 'Uji coba di tambang lain / komoditas lain dengan data fiktif dan nyata'],
        ['Hanya Windows 64-bit, satu pengguna per proyek', 'Kolaborasi lewat file proyek; kolaborasi bersamaan dipertimbangkan kemudian'],
        ['Block model terotasi dari .mdl belum dibaca langsung', 'Butuh contoh .mdl terotasi dari Surpac untuk dicocokkan'],
        ['Belum ada pencatatan HKI, merek, badan usaha, dan harga', 'Lihat Bab 6; tetapkan harga dan model lisensi'],
        ['Repo publik', 'Kembalikan ke privat bila kerahasiaan kode menjadi pertimbangan investor']], w=['50%', '50%']),
    tabel(['Istilah', 'Arti singkat'], [
        ['Grade control (GC)', 'Pekerjaan memastikan batuan yang digali dikirim ke tujuan yang benar (bijih ke pabrik / stockpile, waste ke timbunan)'],
        ['Block model', 'Model 3D tubuh bijih yang dipotong menjadi kubus; setiap kubus punya kadar dan berat jenis'],
        ['Estimasi (Kriging / ID²)', 'Cara menghitung kadar tiap blok dari sampel bor di sekitarnya'],
        ['Flitch', 'Lapisan horizontal penggalian (mis. setebal 2,5 m)'],
        ['Dig block / dig plan', 'Poligon batas penggalian per jenis material di satu flitch, dan peta kerja yang dibagikan ke lapangan'],
        ['As-mined', 'Volume yang benar-benar tergali menurut pengukuran survei, untuk dibandingkan dengan rencana'],
        ['Rekonsiliasi', 'Membandingkan tonase dan kadar rencana, model, dan realisasi'],
        ['Surpac', 'Perangkat lunak tambang komersial yang menjadi acuan di banyak tambang']], w=['26%', '74%'])))

DOC = '<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><title>Tentang GC-Ex</title><style>%s</style></head><body>%s</body></html>' % (CSS, '\n'.join(B))

def cetak():
    from playwright.sync_api import sync_playwright
    tmp = HERE / '_tentang.html'; tmp.write_text(DOC, encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.goto(tmp.as_uri()); pg.wait_for_timeout(500)
        pg.pdf(path=str(OUT), format='A4', print_background=True, display_header_footer=True,
               header_template='<span></span>',
               footer_template='<div style="font-size:7pt;color:#5C6672;width:100%;padding:0 15mm;display:flex;justify-content:space-between;font-family:Inter,sans-serif"><span>Tentang GC-Ex · Copyright © Habil Abdillah 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
               margin={'top': '16mm', 'bottom': '16mm', 'left': '15mm', 'right': '15mm'})
        b.close()
    tmp.unlink()
    print('OK', OUT, OUT.stat().st_size, 'byte')

if __name__ == '__main__':
    cetak()
