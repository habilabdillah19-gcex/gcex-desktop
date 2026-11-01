# -*- coding: utf-8 -*-
"""Menyusun Tutorial GC-Ex Block Model (gambar: tutorial_bm_shots.py -> img_bm; isi bab: bm_bab.py). Asal format: Tutorial GC-Ex Drillhole (HTML -> PDF A4) dari tangkapan layar docs/tutorial/img.
Jalankan: python docs/tutorial/tutorial_shots.py  (membuat img/*.png + notes.json)
          python docs/tutorial/build_tutorial.py  (membuat GCEx_Tutorial_Modelling_Estimasi.pdf)
"""
import os, json, re, html, datetime
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'img_bm')
OUT = os.path.join(HERE, 'build_bm')
os.makedirs(OUT, exist_ok=True)
if not os.path.isdir(IMG) or not os.path.exists(os.path.join(IMG, 'notes.json')):
    raise SystemExit(
        "Tangkapan layar belum ada di %s.\n"
        "Tutorial bergambar ini dibangun dari tangkapan layar aplikasi, jadi jalankan dulu:\n"
        "    python docs/tutorial-gcex/src/tutorial_bm_shots.py\n"
        "Langkah itu membuka GC-Ex di Chromium dan memerlukan browser yang dapat membuka folder\n"
        "proyek (File System Access API). Di lingkungan terbatas (mis. kontainer CI Linux) langkah\n"
        "ini dapat menghentikan renderer; pakai mesin Windows tempat GC-Ex biasa dipakai.\n"
        "Tutorial yang TIDAK memerlukan tangkapan layar: build_tutorial_update.py" % IMG)

N = json.load(open(os.path.join(IMG, 'notes.json'), encoding='utf-8'))
PDF = os.path.join(HERE, '..', 'GCEx_Tutorial_Block_Model.pdf')

def clean(s): return html.unescape(re.sub('<[^>]+>', '', str(s)))

# ---------- gambar: PNG -> JPEG ringan ----------
FIG = {}
for f in sorted(os.listdir(IMG)):
    if not f.endswith('.png'): continue
    im = Image.open(os.path.join(IMG, f)).convert('RGB')
    if im.width > 1700: im = im.resize((1700, round(im.height * 1700 / im.width)), Image.LANCZOS)
    j = f[:-4] + '.jpg'; im.save(os.path.join(OUT, j), quality=82, optimize=True)
    FIG[f[3:-4]] = (j, im.width / im.height)

fig_no = [0]; FNUM = {}
def fig(key, cap, w=None):
    j, ar = FIG[key]; fig_no[0] += 1; FNUM[key] = fig_no[0]
    narrow = ar < 0.8
    width = w or ('34%' if narrow else '100%')
    return ('<figure class="%s"><img src="%s" style="width:%s"><figcaption><b>Gambar %d.</b> %s</figcaption></figure>'
            % ('nar' if narrow else '', j, width, fig_no[0], cap))

def fig2(k1, c1, k2, c2):
    """dua gambar panel sempit berdampingan"""
    a = fig(k1, c1, '100%'); b = fig(k2, c2, '100%')
    return '<div class="duo"><div>%s</div><div>%s</div></div>' % (a, b)

def steps(*xs): return '<ol class="st">' + ''.join('<li>%s</li>' % x for x in xs) + '</ol>'
def tip(t, k='tip', h='Tips'): return '<div class="box %s"><b>%s</b> %s</div>' % (k, h, t)
def warn(t, h='Perhatian'): return tip(t, 'warn', h)
def why(t): return tip(t, 'why', 'Mengapa?')
def kv(rows): return '<table class="kv">' + ''.join('<tr><td>%s</td><td>%s</td></tr>' % r for r in rows) + '</table>'

exec(open(os.path.join(HERE, 'bm_bab.py'), encoding='utf-8').read())
# ================= HTML =================
toc = ''.join('<li><span>%d. %s</span></li>' % (i, t) for i, (t, _) in enumerate(CH))
body = ''.join('<section class="ch"><h2><span>%d</span>%s</h2>%s</section>' % (i, t, b) for i, (t, b) in enumerate(CH))
today = datetime.date.today()
bulan = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'][today.month-1]
HTML = f'''<!doctype html><html lang="id"><head><meta charset="utf-8"><title>Tutorial GC-Ex: Pemodelan Vein & Estimasi Block Model</title>
<style>
@page{{size:A4;margin:16mm 15mm 16mm 15mm}}
:root{{--nv:#1f2d6b;--ac:#f2c200;--mu:#5b6478;--ln:#d9dde6}}
*{{box-sizing:border-box}}
body{{font-family:Inter,'DejaVu Sans',sans-serif;font-size:10pt;line-height:1.5;color:#1b2033;margin:0}}
code{{font-family:'DejaVu Sans Mono',monospace;font-size:8.6pt;background:#f1f3f8;padding:0 3px;border-radius:3px}}
.cover{{height:265mm;display:flex;flex-direction:column;justify-content:space-between;page-break-after:always}}
.cover .top{{background:var(--nv);color:#fff;padding:22mm 14mm 16mm;border-bottom:4mm solid var(--ac)}}
.cover .logo{{font-size:30pt;font-weight:800;color:var(--ac);letter-spacing:.5px}}
.cover h1{{font-size:24pt;line-height:1.2;margin:8mm 0 3mm;font-weight:700}}
.cover .sub{{font-size:12pt;opacity:.85}}
.cover .img{{padding:0 6mm}}.cover .img img{{width:100%;border:1px solid var(--ln);border-radius:4px}}
.cover .meta{{color:var(--mu);font-size:9.5pt;padding:0 6mm}}
.toc{{page-break-after:always}}.toc h2{{font-size:16pt;color:var(--nv);border-bottom:2px solid var(--ac);padding-bottom:2mm}}
.toc ol{{list-style:none;padding:0;columns:1}}.toc li{{padding:1.6mm 0;border-bottom:1px dotted var(--ln);font-size:10.5pt}}
.ch{{page-break-before:always}}
h2{{font-size:16pt;color:var(--nv);margin:0 0 4mm;display:flex;align-items:center;gap:3mm;border-bottom:2px solid var(--ac);padding-bottom:2mm}}
h2 span{{background:var(--nv);color:var(--ac);font-size:13pt;min-width:9mm;height:9mm;border-radius:2mm;display:inline-flex;align-items:center;justify-content:center}}
h3{{font-size:11.5pt;color:var(--nv);margin:5mm 0 2mm}}
p{{margin:0 0 2.5mm}}
ol.st{{counter-reset:s;list-style:none;padding:0;margin:2mm 0 3mm}}
ol.st li{{counter-increment:s;position:relative;padding:1.2mm 0 1.2mm 9mm;break-inside:avoid}}
ol.st li:before{{content:counter(s);position:absolute;left:0;top:1.2mm;width:6mm;height:6mm;border-radius:50%;background:var(--ac);color:var(--nv);font-weight:700;font-size:9pt;display:flex;align-items:center;justify-content:center}}
figure{{margin:3mm 0 4mm;break-inside:avoid;text-align:center}}
figure img{{border:1px solid var(--ln);border-radius:3px;display:block;margin:0 auto}}
figcaption{{font-size:8.8pt;color:var(--mu);margin-top:1.5mm;text-align:left}}
figure.nar figcaption{{max-width:52%;margin-left:auto;margin-right:auto}}
.duo{{display:flex;gap:6mm;break-inside:avoid}}.duo>div{{flex:1}}.duo figure.nar figcaption{{max-width:none}}
.box{{border-left:1.2mm solid;padding:2mm 3mm;margin:3mm 0;border-radius:0 2mm 2mm 0;break-inside:avoid;font-size:9.4pt}}
.box b:first-child{{display:block;font-size:8.6pt;text-transform:uppercase;letter-spacing:.4px}}
.tip{{border-color:#2f9e44;background:#ebfbee}}.tip b:first-child{{color:#2b8a3e}}
.why{{border-color:#1c7ed6;background:#e7f5ff}}.why b:first-child{{color:#1864ab}}
.warn{{border-color:#e8590c;background:#fff4e6}}.warn b:first-child{{color:#d9480f}}
.tag{{font-size:8pt;font-weight:700;padding:0 2mm;border-radius:1mm;border:0}}
table{{border-collapse:collapse;width:100%;margin:2mm 0 3mm;font-size:9pt;break-inside:avoid}}
table.t th{{background:var(--nv);color:#fff;text-align:left;padding:1.5mm 2mm}}table.t td{{border-bottom:1px solid var(--ln);padding:1.5mm 2mm;vertical-align:top}}
table.kv td{{border-bottom:1px solid var(--ln);padding:1.3mm 2mm;vertical-align:top}}table.kv td:first-child{{width:34%;font-weight:600;color:var(--nv)}}
.flow{{display:grid;grid-template-columns:repeat(5,1fr);gap:2.5mm;margin:2mm 0 4mm}}
.flow div{{background:#f1f3f8;border:1px solid var(--ln);border-radius:2mm;padding:2mm;text-align:center;font-size:8.8pt;line-height:1.3}}
.flow b{{display:block;color:var(--nv);font-size:12pt}}
ul{{margin:1mm 0 3mm;padding-left:5mm}}li{{margin:.6mm 0}}
</style></head><body>
<div class="cover"><div class="top"><div class="logo">GC-Ex</div><h1>Tutorial Grade Control<br>dengan Block Model</h1>
<div class="sub">GC-Ex Block Model 0.20 &middot; flitch, dig block, additional flagging, as-mined &amp; laporan</div></div>
<div class="img"><img src="{FIG['hasil_kerja_3d'][0]}"></div>
<div class="meta">Edisi {today.day} {bulan} {today.year} &middot; untuk pelatihan internal geologist grade control<br>
Data latihan sintetis &middot; semua gambar diambil dari satu kali jalannya latihan</div></div>
<div class="toc"><h2>Daftar isi</h2><ol>{toc}</ol></div>
{body}
</body></html>'''
def _bab(m):
    for i,(t,_) in enumerate(CH):
        if t.startswith(m.group(1)):return 'Bab %d'%i
    raise KeyError(m.group(1))
HTML = re.sub(r'\{\{B:([^}]+)\}\}', _bab, HTML)
HTML = re.sub(r'\[\[(\w+)\]\]', lambda m: 'Gambar %d' % FNUM[m.group(1)], HTML)
hp = os.path.join(OUT, 'tutorial.html'); open(hp, 'w', encoding='utf-8').write(HTML)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto('file://' + hp); pg.wait_for_timeout(800)
    pg.pdf(path=PDF, format='A4', print_background=True, display_header_footer=True,
           header_template='<div></div>',
           footer_template='<div style="font-size:7.5pt;color:#8a90a2;width:100%;padding:0 15mm;display:flex;justify-content:space-between;font-family:Inter,sans-serif"><span>GC-Ex &middot; Tutorial Block Model</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
           margin={'top': '14mm', 'bottom': '16mm', 'left': '15mm', 'right': '15mm'})
    b.close()
print('PDF', PDF, os.path.getsize(PDF) // 1024, 'KB', 'gambar', fig_no[0])
