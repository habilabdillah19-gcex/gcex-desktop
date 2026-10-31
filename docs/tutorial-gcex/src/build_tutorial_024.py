# -*- coding: utf-8 -*-
"""Menyusun 'Tutorial Tambahan GC-Ex 0.24' (HTML -> PDF A4).

BEDANYA dengan build_tutorial.py / build_tutorial_bm.py: tutorial ini TIDAK memakai tangkapan layar
aplikasi, jadi bisa dibangun di mesin mana pun (termasuk CI Linux) tanpa menjalankan GC-Ex.
Semua gambarnya dihitung langsung dari model data simulasi (make_sim_data.py) dan dari berkas CSV
yang dihasilkannya, sehingga angka di gambar selalu cocok dengan data latihan yang dikirim.

Jalankan:  python docs/tutorial-gcex/src/build_tutorial_024.py
Hasil:     docs/tutorial-gcex/GCEx_Tutorial_0.24_Tambahan.pdf
"""
import csv
import datetime
import html
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
TUT = os.path.abspath(os.path.join(HERE, '..'))
DATA = os.path.join(TUT, 'data')
FIGD = os.path.join(HERE, 'fig_024')
PDF = os.path.join(TUT, 'GCEx_Tutorial_0.24_Tambahan.pdf')
os.makedirs(FIGD, exist_ok=True)

INK, ACC, ACC2, MUT = '#1b2a3a', '#1f4e8c', '#c98a16', '#6b7682'
plt.rcParams.update({'font.size': 8, 'axes.edgecolor': INK, 'axes.labelcolor': INK,
                     'xtick.color': INK, 'ytick.color': INK, 'axes.titlesize': 9,
                     'figure.facecolor': 'white', 'axes.grid': True, 'grid.color': '#e3e8ee',
                     'grid.linewidth': 0.6, 'axes.axisbelow': True})

# ------------------------------------------------------------------ muat model & data
GEN = os.path.join(TUT, 'make_sim_data.py')
src = open(GEN, encoding='utf-8').read()
g = {'__name__': 'model', '__file__': GEN}
CUT = src.index('lubang bor', src.index('def unfault'))      # berhenti sebelum bagian pembuatan bor
exec(compile(src[:src.rindex('# ---', 0, CUT)], 'model', 'exec'), g)
LENSA, thick, shoot, shoot_uv = g['LENSA'], g['thick'], g['shoot'], g['shoot_uv']
topo, vpt, C, s_vec, dd, nrm = g['topo'], g['vpt'], g['C'], g['s_vec'], g['dd'], g['nrm']
PITCH, WT_RL, DIP, DIPAZ, STRIKE = g['PITCH'], g['WT_RL'], g['DIP'], g['DIPAZ'], g['STRIKE']
FA_P, fa_s, FA_OFF = g['FA_P'], g['fa_s'], g['FA_OFF']

rd = lambda fn: list(csv.DictReader(open(os.path.join(DATA, fn), encoding='utf-8')))
COL = {r['Hole_ID']: np.array([float(r['Easting']), float(r['Northing']), float(r['RL'])]) for r in rd('SIM_collar.csv')}
SVY = {}
for r in rd('SIM_survey.csv'):
    SVY.setdefault(r['Hole_ID'], []).append((float(r['Depth']), float(r['Dip']), float(r['Azimuth'])))
ASY, GEO = rd('SIM_assay.csv'), rd('SIM_geologi.csv')


def xyz(hid, d):
    S = sorted(SVY[hid]); dip, az = S[0][1], S[0][2]
    for dd0, dp, a in S:
        if dd0 <= d:
            dip, az = dp, a
    v = np.array([math.sin(math.radians(az)) * math.cos(math.radians(dip)),
                  math.cos(math.radians(az)) * math.cos(math.radians(dip)), math.sin(math.radians(dip))])
    return COL[hid] + v * d


VEIN = {'QV', 'QVB', 'BX'}
P = np.array([xyz(a['Hole_ID'], (float(a['From']) + float(a['To'])) / 2) for a in ASY])
AU = np.array([float(a['Au']) for a in ASY]); AG = np.array([float(a['Ag']) for a in ASY])
PB = np.array([float(a['Pb']) for a in ASY]); ZN = np.array([float(a['Zn']) for a in ASY])
LIT = np.array([x['Lith'] for x in GEO]); TEX = np.array([x['Texture'] for x in GEO])
INV = np.isin(LIT, list(VEIN))

# GT per bor (seperti menu Ore Geometry)
HH = {}
for a, gg in zip(ASY, GEO):
    if gg['Lith'] not in VEIN:
        continue
    h = a['Hole_ID']; L = float(a['To']) - float(a['From'])
    q = HH.setdefault(h, {'gt': 0.0, 'L': 0.0, 's': np.zeros(3), 'w': 0.0})
    q['gt'] += float(a['Au']) * L; q['L'] += L
    q['s'] += xyz(h, (float(a['From']) + float(a['To'])) / 2) * L; q['w'] += L
HK = list(HH)
HP = np.array([HH[k]['s'] / HH[k]['w'] for k in HK])
HGT = np.array([HH[k]['gt'] for k in HK]); HTB = np.array([HH[k]['L'] for k in HK])
HLN = np.array([k.split('-')[2] if len(k.split('-')) > 2 else '?' for k in HK])

NOTE = {}


def save(fig, name):
    p = os.path.join(FIGD, name + '.png')
    fig.savefig(p, dpi=190, bbox_inches='tight', pad_inches=0.08)
    plt.close(fig)
    return name + '.png'


# ------------------------------------------------------------------ F1 peta array lensa
def f_peta():
    fig, ax = plt.subplots(figsize=(6.3, 4.4))
    for i, V in enumerate(LENSA):
        aa = np.linspace(V['a'][0], V['a'][1], 160); bb = np.linspace(V['b'][0], V['b'][1], 60)
        AAg, BBg = np.meshgrid(aa, bb, indexing='ij')
        T = thick(AAg, BBg, V)
        pts = np.array([vpt(float(x), float(y), V) for x, y in zip(AAg[T > 0.35][::40], BBg[T > 0.35][::40])])
        if len(pts):
            ax.scatter(pts[:, 0], pts[:, 1], s=2, color=ACC if i < 4 else ACC2, alpha=0.5,
                       label=('lensa vein' if i == 0 else ('splay hangingwall' if i == 4 else None)))
    cs = np.array(list(COL.values()))
    ax.scatter(cs[:, 0], cs[:, 1], s=5, marker='+', color=MUT, label='collar bor (%d)' % len(COL))
    fl = np.array([FA_P + t * fa_s for t in np.linspace(-150, 150, 40)])
    ax.plot(fl[:, 0], fl[:, 1], color='#c0392b', lw=1.8, label='sesar pasca-min. (offset %.0f m)' % FA_OFF)
    ax.set_xlabel('Easting (m)'); ax.set_ylabel('Northing (m)'); ax.set_aspect('equal')
    ax.ticklabel_format(style='plain', useOffset=False)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(6))
    ax.tick_params(axis='x', labelrotation=0, labelsize=7); ax.tick_params(axis='y', labelsize=7)
    ax.set_title('Array 4 lensa vein en-echelon (right-stepping), strike %.0f°' % STRIKE)
    ax.legend(fontsize=6.5, loc='upper left', framealpha=0.9)
    return save(fig, 'f1_peta')


# ------------------------------------------------------------------ F2 bidang vein: tebal + sumbu pitch
def f_bidang():
    V = LENSA[1]
    aa = np.linspace(V['a'][0], V['a'][1], 260); bb = np.linspace(V['b'][0], V['b'][1], 200)
    AAg, BBg = np.meshgrid(aa, bb, indexing='ij')
    T = thick(AAg, BBg, V); S = shoot(AAg, BBg, V)
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.1))
    for ax, Z, ttl, cm in ((axs[0], T, 'Tebal vein (m)', 'YlOrBr'), (axs[1], T * S, 'GT model = tebal × kadar relatif', 'YlGnBu')):
        im = ax.pcolormesh(AAg, BBg, np.where(T > 0.3, Z, np.nan), cmap=cm, shading='auto')
        p = math.radians(PITCH)
        t = np.linspace(-170, 170, 2)
        ax.plot(V['ac'] + t * math.cos(p), V['bc'] + t * math.sin(p), '--', color='#c0392b', lw=1.4)
        ax.set_xlim(V['a'][0], V['a'][1]); ax.set_ylim(V['b'][1], V['b'][0])
        ax.set_xlabel('sepanjang strike (m)'); ax.set_title(ttl)
        fig.colorbar(im, ax=ax, pad=0.02, fraction=0.045)
    axs[0].set_ylabel('menurun dip (m)')
    axs[1].text(0.03, 0.06, 'garis putus = sumbu ore shoot, pitch %.0f°' % PITCH, transform=axs[1].transAxes,
                fontsize=6.5, color='#c0392b')
    fig.suptitle('Bidang vein lensa 2: tebal dan GT dikontrol SATU struktur (zona dilatan ber-pitch)', fontsize=8.5)
    return save(fig, 'f2_bidang')


# ------------------------------------------------------------------ F3 GT per bor di bidang vein
def f_gt():
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0))
    for ax, sel, ttl in ((axs[0], np.isin(HLN, ['L1', 'L4']), 'Lensa utuh (L1 + L4)'),
                         (axs[1], np.isin(HLN, ['L2', 'L3']), 'Lensa terpotong sesar (L2 + L3)')):
        for L in sorted(set(HLN[sel])):
            m = (HLN == L) & sel
            R = HP[m] - HP[m].mean(0)
            aa = R @ s_vec; bb = R @ dd
            sz = 4 + 46 * (HGT[m] / max(HGT.max(), 1e-9)) ** 0.45
            ax.scatter(aa, bb, s=sz, c=HGT[m], cmap='YlGnBu', norm=matplotlib.colors.LogNorm(vmin=0.3, vmax=max(HGT.max(), 1)),
                       edgecolor=INK, linewidth=0.2)
        p = math.radians(PITCH); t = np.linspace(-120, 120, 2)
        ax.plot(t * math.cos(p), t * math.sin(p), '--', color='#c0392b', lw=1.3)
        ax.invert_yaxis(); ax.set_xlabel('sepanjang strike (m)'); ax.set_title(ttl, fontsize=8.5)
    axs[0].set_ylabel('menurun dip (m)')
    fig.suptitle('GT (kadar × tebal) per bor, diproyeksikan ke bidang vein — besar & warna = GT', fontsize=8.5)
    return save(fig, 'f3_gt')


# ------------------------------------------------------------------ F4 kipas variogram GT
def f_kipas():
    aa = np.zeros(len(HK)); bb = np.zeros(len(HK))
    for L in set(HLN):
        m = HLN == L; R = HP[m] - HP[m].mean(0); aa[m] = R @ s_vec; bb[m] = R @ dd

    def fan(val, mask):
        v = np.log(np.maximum(val[mask], 1e-3)); x = aa[mask]; y = bb[mask]; lb = HLN[mask]
        I, J = np.triu_indices(len(v), 1)
        same = lb[I] == lb[J]
        dx = x[J] - x[I]; dy = y[J] - y[I]; hh = np.hypot(dx, dy); dv = (v[J] - v[I]) ** 2 / 2
        ang = np.degrees(np.arctan2(dy, dx)) % 180
        th = np.arange(0, 180, 5.0); out = np.full(len(th), np.nan)
        for i, t in enumerate(th):
            da = np.abs((ang - t + 90) % 180 - 90)
            k = same & (da <= 22.5) & (hh > 25) & (hh < 90)
            if k.sum() >= 40:
                out[i] = dv[k].mean()
        return th, out

    fig, ax = plt.subplots(figsize=(6.3, 2.9))
    allm = np.ones(len(HK), bool)
    for lab, val, c in (('GT (kadar × tebal)', HGT, ACC), ('tebal intersep', HTB, ACC2)):
        th, gm = fan(val, allm)
        ax.plot(th, gm / np.nanmean(gm), 'o-', ms=3, lw=1.3, color=c, label=lab)
        NOTE['fan_' + ('gt' if val is HGT else 'tb')] = int(th[np.nanargmin(gm)])
    ax.axvline(PITCH, color='#c0392b', ls='--', lw=1.4)
    ax.text(PITCH + 2, ax.get_ylim()[1] * 0.95, 'pitch model %.0f°' % PITCH, color='#c0392b', fontsize=7, va='top')
    ax.set_xlabel('arah di dalam bidang vein (° dari garis strike)')
    ax.set_ylabel('γ ternormalisasi\n(kecil = lebih menerus)')
    ax.set_xticks(range(0, 181, 15)); ax.legend(fontsize=7)
    ax.set_title('Kipas variogram: arah kemenerusan terbaik = sumbu ore shoot', fontsize=9)
    return save(fig, 'f4_kipas')


# ------------------------------------------------------------------ F5 zonasi vertikal
def f_zonasi():
    zs = np.arange(150, 320, 10.0); A1 = []; R1 = []; B1 = []; T1 = []
    for z in zs:
        m = INV & (P[:, 2] >= z) & (P[:, 2] < z + 10)
        if m.sum() < 15:
            A1.append(np.nan); R1.append(np.nan); B1.append(np.nan); T1.append(np.nan); continue
        A1.append(AU[m].mean()); R1.append(AG[m].sum() / max(AU[m].sum(), 1e-9))
        B1.append((PB[m] + ZN[m]).mean() * 100); T1.append(100 * (TEX[m] == 'COLL').mean())
    fig, axs = plt.subplots(1, 4, figsize=(6.6, 3.2), sharey=True)
    for ax, v, lab, c in ((axs[0], A1, 'Au (g/t)', ACC), (axs[1], R1, 'Ag/Au', ACC2),
                          (axs[2], B1, 'Pb+Zn (%)', '#2e7d32'), (axs[3], T1, 'tekstur\ncolloform (%)', '#7b1fa2')):
        ax.plot(v, zs + 5, 'o-', ms=2.6, lw=1.2, color=c)
        ax.axhline(WT_RL, color='#c0392b', ls='--', lw=1.1)
        ax.set_xlabel(lab, fontsize=7.5)
    axs[0].set_ylabel('RL (m)')
    axs[0].text(0.5, WT_RL + 4, 'paleo-muka air tanah', fontsize=6.3, color='#c0392b')
    fig.suptitle('Zonasi vertikal epitermal terhadap paleo-muka air tanah RL %.0f m' % WT_RL, fontsize=8.5)
    NOTE['zon_puncak'] = int(zs[int(np.nanargmax(A1))])
    NOTE['zon_agau_bawah'] = round(float(np.nanmin(R1)), 1)
    NOTE['zon_agau_atas'] = round(float(np.nanmax(R1)), 1)
    return save(fig, 'f5_zonasi')


# ------------------------------------------------------------------ F6 sebaran Au & top-cut
def f_topcut():
    x = AU[INV]; x = x[x > 0]
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.7))
    axs[0].hist(np.log10(x), bins=46, color=ACC, alpha=0.85, edgecolor='white', linewidth=0.3)
    axs[0].set_xlabel('log10 Au (g/t)'); axs[0].set_ylabel('jumlah sampel')
    axs[0].set_title('Sebaran Au di dalam vein (n=%d)' % len(x), fontsize=8.5)
    xs = np.sort(x)[::-1]
    cum = np.cumsum(xs) / xs.sum() * 100
    axs[1].plot(np.arange(1, len(xs) + 1) / len(xs) * 100, cum, color=ACC2, lw=1.5)
    for q in (1, 5, 10):
        i = max(1, int(len(xs) * q / 100)) - 1
        axs[1].plot([q], [cum[i]], 'o', ms=4, color=INK)
        axs[1].annotate('%d%% sampel teratas = %.0f%% logam' % (q, cum[i]), (q, cum[i]),
                        textcoords='offset points', xytext=(8, -2), fontsize=6.5)
        NOTE['tc_%d' % q] = round(float(cum[i]), 1)
    axs[1].set_xlabel('% sampel teratas'); axs[1].set_ylabel('% logam Au terkumpul')
    axs[1].set_xlim(0, 30); axs[1].set_title('Pemusatan logam → perlunya top-cut', fontsize=8.5)
    NOTE['au_cv'] = round(float(x.std() / x.mean()), 2)
    NOTE['au_mean'] = round(float(x.mean()), 2); NOTE['au_med'] = round(float(np.median(x)), 2)
    NOTE['au_max'] = round(float(x.max()), 1)
    return save(fig, 'f6_topcut')


# ------------------------------------------------------------------ F7 skema klasifikasi
def f_klas():
    fig, ax = plt.subplots(figsize=(6.3, 2.5)); ax.axis('off'); ax.grid(False)
    kot = [('Blok hasil\nModel Estimation', 0.02, '#eef2f7', INK),
           ('pass ≤ 1\nkomposit ≥ 12\nSoR ≥ 0,75', 0.27, '#d9ecdf', '#1b7f4b'),
           ('pass ≤ 2\nkomposit ≥ 7\nSoR ≥ 0,45', 0.52, '#dde7f3', ACC),
           ('sisanya\n(terestimasi)', 0.77, '#f6ebd3', ACC2)]
    for t, x, bg, fg in kot:
        ax.add_patch(plt.Rectangle((x, 0.45), 0.19, 0.42, facecolor=bg, edgecolor=fg, linewidth=1.2))
        ax.text(x + 0.095, 0.66, t, ha='center', va='center', fontsize=7, color=fg)
    for t, x, fg in (('Measured', 0.27, '#1b7f4b'), ('Indicated', 0.52, ACC), ('Inferred', 0.77, ACC2)):
        ax.text(x + 0.095, 0.3, t, ha='center', fontsize=9, color=fg, fontweight='bold')
        ax.annotate('', (x + 0.095, 0.4), (x + 0.095, 0.44), arrowprops=dict(arrowstyle='-|>', color=fg, lw=1.1))
    for x in (0.21, 0.46, 0.71):
        ax.annotate('', (x + 0.06, 0.66), (x, 0.66), arrowprops=dict(arrowstyle='-|>', color=MUT, lw=1))
    ax.text(0.5, 0.12, 'Blok tanpa estimasi → "Belum terklasifikasi". Semua ambang dapat diubah di panel.',
            ha='center', fontsize=7, color=MUT)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return save(fig, 'f7_klas')


F = {k: f() for k, f in (('peta', f_peta), ('bidang', f_bidang), ('gt', f_gt), ('kipas', f_kipas),
                         ('zonasi', f_zonasi), ('topcut', f_topcut), ('klas', f_klas))}

# angka ringkas untuk narasi
Q = HP[np.ones(len(HK), bool)]
QQ = P[INV] - P[INV].mean(0)
_, _, vt = np.linalg.svd(QQ, full_matrices=False); nn = vt[2]; nn = nn if nn[2] > 0 else -nn
NOTE['dip_ukur'] = round(math.degrees(math.acos(abs(nn[2]))), 1)
NOTE['daz_ukur'] = round(math.degrees(math.atan2(nn[0], nn[1])) % 360, 1)
NOTE['n_bor'] = len(COL); NOTE['n_assay'] = len(ASY)
NOTE['n_gc'] = len(rd('SIM_gc_collar.csv')); NOTE['n_gc_assay'] = len(rd('SIM_gc_assay.csv'))
tb = HTB
NOTE['tb_med'] = round(float(np.median(tb)), 1); NOTE['tb_p90'] = round(float(np.quantile(tb, 0.9)), 1)

# ------------------------------------------------------------------ HTML
e = lambda s: html.escape(str(s))
num = lambda v: format(int(v), ',d').replace(',', '.')   # pemisah ribuan gaya Indonesia
TGL = datetime.datetime.now().strftime('%d %B %Y')
fign = [0]


def fig_html(key, cap):
    fign[0] += 1
    return ('<figure><img src="fig_024/%s"><figcaption><b>Gambar %d.</b> %s</figcaption></figure>'
            % (F[key], fign[0], cap))


CSS = """
@page { size: A4; margin: 18mm 16mm 16mm 16mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #1b2a3a; font-size: 10pt; line-height: 1.5; }
h1 { font-size: 20pt; color: #1f4e8c; margin: 0 0 2mm; }
h2 { font-size: 13pt; color: #1f4e8c; border-bottom: 1.5pt solid #1f4e8c; padding-bottom: 1mm;
     margin: 9mm 0 3mm; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 1.5mm; page-break-after: avoid; }
p { margin: 0 0 2.5mm; text-align: justify; }
figure { margin: 4mm 0; page-break-inside: avoid; }
figure img { width: 100%; border: 0.5pt solid #d6dde6; }
figcaption { font-size: 8pt; color: #6b7682; margin-top: 1.2mm; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin: 3mm 0; page-break-inside: avoid; }
th, td { border: 0.5pt solid #d6dde6; padding: 1.4mm 2mm; text-align: left; vertical-align: top; }
th { background: #eef2f7; color: #1f4e8c; }
code { background: #f3f6f9; padding: 0 1mm; font-size: 9pt; }
.lead { font-size: 10.5pt; color: #42526b; }
.box { border-left: 3pt solid #1f4e8c; background: #f7f9fb; padding: 2.5mm 3mm; margin: 3mm 0; }
.warn { border-left: 3pt solid #c98a16; background: #fdf8ee; padding: 2.5mm 3mm; margin: 3mm 0; }
.cover { text-align: center; padding-top: 55mm; }
.cover .sub { color: #6b7682; font-size: 11pt; margin-top: 3mm; }
.toc { font-size: 9.5pt; } .toc li { margin: 1mm 0; }
ol.steps > li { margin: 0 0 2mm; }
.page { page-break-after: always; }
small { color: #6b7682; }
"""

B = []
B.append('<div class="cover page"><h1>Tutorial Tambahan GC-Ex 0.24</h1>'
         '<div class="sub">Klasifikasi keyakinan sumber daya &middot; Topografi &amp; orthofoto resolusi tinggi'
         '<br>Data latihan simulasi baru: array vein en-echelon ber-<i>ore shoot</i></div>'
         '<p style="margin-top:22mm"><small>Pelengkap <i>Tutorial Modelling &amp; Estimasi</i> dan '
         '<i>Tutorial Block Model</i>. Semua gambar di dokumen ini dihitung langsung dari model dan berkas '
         'data latihan, bukan tangkapan layar, sehingga angkanya selalu cocok dengan data yang Anda terima.'
         f'<br>Disusun otomatis {e(TGL)}.</small></p></div>')

B.append('<h2>Isi</h2><ol class="toc">'
         '<li>Data latihan simulasi baru &mdash; model geologi &amp; daftar berkas</li>'
         '<li>Latihan terpandu: menemukan kembali geometri endapan</li>'
         '<li>Klasifikasi keyakinan sumber daya di Reporting BM</li>'
         '<li>Topografi &amp; orthofoto resolusi sangat tinggi</li>'
         '<li>Bagian tutorial lama yang perlu disesuaikan</li></ol>')

# ---- 1
B.append('<h2>1. Data latihan simulasi baru</h2>')
B.append('<p class="lead">Data latihan GC-Ex diganti dengan endapan yang jauh lebih besar dan jauh lebih '
         'taat kaidah geologi. Tujuannya satu: setiap latihan punya <b>jawaban yang diketahui</b>, sehingga '
         'Anda bisa menilai apakah hasil pemodelan Anda sendiri sudah masuk akal.</p>')
B.append('<p>Endapannya emas <b>epitermal <i>low-sulphidation</i></b> yang dikontrol zona geser. Semuanya '
         'fiktif &mdash; dihitung dari rumus di <code>make_sim_data.py</code>, tanpa nama perusahaan, Hole ID, '
         'koordinat, atau hasil lab proyek nyata.</p>')
B.append('<table><tr><th>Unsur model</th><th>Isi</th></tr>'
         f'<tr><td>Zona geser</td><td>strike {STRIKE:.0f}°, dip {DIP:.0f}° ke azimuth {DIPAZ:.0f}° (bidang acuan)</td></tr>'
         '<tr><td>Array vein</td><td>4 lensa sigmoidal <b>en-echelon</b> <i>right-stepping</i> + 1 splay hangingwall</td></tr>'
         f'<tr><td>Ore shoot</td><td><b>pitch {PITCH:.0f}°</b> dari garis strike, di dalam bidang vein, sama untuk semua lensa</td></tr>'
         '<tr><td>Zona dilatan</td><td>tebal <b>dan</b> kadar maksimum dikontrol satu struktur yang sama '
         '(<i>jog</i> dilatan = ore shoot) &mdash; inilah sebabnya GT punya satu arah kemenerusan terbaik</td></tr>'
         f'<tr><td>Zonasi vertikal</td><td>paleo-muka air tanah RL {WT_RL:.0f} m: zona didih bertekstur '
         '<i>colloform</i> (bonanza), Ag/Au naik ke atas, Pb&ndash;Zn naik ke bawah, As penanda vein</td></tr>'
         '<tr><td>Pelapukan</td><td>tudung tercuci 15 m teratas, selimut pengayaan supergen tepat di atas muka '
         'air tanah, zona transisi, batuan segar</td></tr>'
         f'<tr><td>Sesar</td><td>pasca-mineralisasi, strike 110°, dip 65°, offset dip-slip {FA_OFF:.0f} m, panjang '
         '&plusmn;150 m &mdash; hanya memotong lensa 2 &amp; 3, lensa 1 &amp; 4 tetap utuh</td></tr>'
         '<tr><td>Efek nugget</td><td>5% sampel Au dilonjakkan (emas kasar) &rarr; variogram Au bernugget tinggi, '
         'Ag jauh lebih jinak</td></tr></table>')
B.append(fig_html('peta', 'Jejak permukaan keempat lensa vein, collar bor, dan sesar pasca-mineralisasi. '
                          'Perhatikan pola <i>en-echelon</i>: tiap lensa berpindah ke sisi hangingwall, '
                          'bukan satu vein menerus.'))
B.append('<h3>Ukuran dan berkas</h3>')
B.append('<table><tr><th>Berkas</th><th>Isi</th></tr>'
         f'<tr><td><code>SIM_collar/survey/assay/geologi.csv</code></td><td>kampanye resource: '
         f'<b>{NOTE["n_bor"]} bor</b>, <b>{num(NOTE["n_assay"])} baris assay</b> dengan Au, Ag, Cu, Pb, Zn, S, As, SG; '
         'logging Lith, Alt, Ox, Texture, RQD, Recovery</td></tr>'
         f'<tr><td><code>SIM_gc_*.csv</code></td><td>kampanye <b>grade control</b>: {NOTE["n_gc"]} bor tegak per '
         f'bench pola 7 m, {num(NOTE["n_gc_assay"])} baris assay</td></tr>'
         '<tr><td><code>SIM_kecil_*.csv</code></td><td>subset untuk latihan cepat sebelum memakai data penuh</td></tr>'
         '<tr><td><code>SIM_upsert_*.csv</code>, <code>SIM_upsert2_*.csv</code></td><td>bor baru tahap 1 &amp; 2 '
         '&rarr; latihan estimasi ulang sebagian</td></tr>'
         '<tr><td><code>SIM_split_*.csv</code> + <code>SIM_split_BM_GC.csv</code></td><td>vein bercabang '
         '(lensa 2 + splay) dengan block model 2,5 m</td></tr>'
         '<tr><td><code>SIM_rusak_*.csv</code></td><td>database dengan 9 kesalahan sengaja &rarr; latihan '
         'menu Validasi data bor</td></tr>'
         '<tr><td><code>SIM_qaqc.csv</code></td><td>CRM 3 standar, duplikat, blank</td></tr>'
         '<tr><td><code>SIM_struktur.csv</code>, <code>SIM_pickup_survey.csv</code>, <code>SIM_sesar.csv</code></td>'
         '<td>pengukuran struktur (Dip, Dip_Azimuth, Plunge, Trend), pick-up permukaan, bidang sesar</td></tr>'
         '<tr><td><code>SIM_topo_xyz.csv</code>, <code>SIM_topo_xyz_nov.csv</code></td><td>topografi dua versi '
         '(survei berikutnya area tambang turun s/d 7 m) &rarr; latihan versi topografi &amp; volume sisa</td></tr>'
         '<tr><td><code>SIM_BM_GC.csv</code></td><td>block model kosong 10 &times; 10 &times; 5 m di sekitar array vein</td></tr>'
         '<tr><td><code>SIM_LAT_*.csv</code></td><td>endapan laterit berlapis untuk Geomodeller Stratified-Laterite</td></tr>'
         '<tr><td><code>QV_Lensa2_Leapfrog.obj</code></td><td>wireframe contoh untuk uji import solid</td></tr>'
         '<tr><td><code>JAWABAN_MODEL.txt</code></td><td><b>kunci jawaban</b>: parameter model + angka hasil ukur</td></tr>'
         '</table>')
B.append('<div class="box"><b>Membuat ulang datanya.</b> <code>python make_sim_data.py [folder]</code> '
         '(hasil selalu sama karena benihnya tetap). Tambahkan <code>--kecil</code> untuk latihan cepat, atau '
         '<code>--besar</code> untuk uji beban &plusmn;300.000 baris assay seperti skala produksi.</div>')

# ---- 2
B.append('<div class="page"></div><h2>2. Latihan terpandu: menemukan kembali geometri endapan</h2>')
B.append('<p class="lead">Inti latihan ini: data bor dibuat dari geometri yang sudah ditentukan, jadi '
         'Anda bisa memeriksa apakah cara kerja Anda benar-benar mengembalikan geometri itu.</p>')
B.append(fig_html('bidang', 'Bidang vein lensa 2 dibentangkan. Kiri: tebal vein. Kanan: GT model '
                            '(tebal × kadar relatif). Keduanya memanjang searah garis putus-putus, yaitu sumbu '
                            f'ore shoot ber-pitch {PITCH:.0f}°. Satu struktur mengontrol keduanya.'))
B.append('<h3>Latihan 2a &mdash; orientasi bidang vein</h3>')
B.append(f'<p>Setelah <i>flagging</i> domain, pasang bidang terbaik pada seluruh intersep vein. Hasil yang '
         f'seharusnya Anda dapat: <b>dip &asymp; {NOTE["dip_ukur"]:.0f}°, dip-azimuth &asymp; {NOTE["daz_ukur"]:.0f}°</b>.</p>')
B.append(f'<div class="warn"><b>Jangan bingung bila bukan {DIP:.0f}°.</b> Bidang acuan model memang '
         f'{DIP:.0f}°/{DIPAZ:.0f}°, tetapi permukaan vein <b>sigmoidal</b> (melengkung). Bidang rata-rata dari '
         f'bagian yang terbor memang lebih landai, yaitu sekitar {NOTE["dip_ukur"]:.0f}°. Inilah perbedaan antara '
         'bidang acuan struktur dan bidang terbaik data &mdash; dua hal yang berbeda, dan keduanya benar.</div>')
B.append('<h3>Latihan 2b &mdash; pitch ore shoot</h3>')
B.append('<ol class="steps">'
         '<li>Hitung <b>GT = kadar &times; tebal</b>, <b>dijumlah per bor</b> (bukan per sampel). Menu '
         '<b>Ore Geometry</b> melakukan ini sendiri.</li>'
         '<li>Proyeksikan GT tiap bor ke bidang vein, lalu cari arah kemenerusan terbaiknya (kipas variogram).</li>'
         '<li><b>Gabungkan keempat lensa</b> &mdash; kontrol strukturnya satu. Satu lensa saja datanya terlalu '
         'sedikit untuk menembus efek nugget Au.</li></ol>')
B.append(fig_html('gt', 'GT per bor di bidang vein. Kiri (lensa utuh): pemusatan GT jelas memanjang searah '
                        'sumbu ore shoot. Kanan (lensa yang dipotong sesar): polanya pecah, karena blok yang '
                        f'turun menggeser bagian vein sejauh {FA_OFF:.0f} m.'))
B.append(fig_html('kipas', f'Kipas variogram. Lembah terdalam = arah paling menerus. GT jatuh di '
                           f'{NOTE.get("fan_gt", "-")}° dan tebal intersep di {NOTE.get("fan_tb", "-")}°, '
                           f'berbanding pitch model {PITCH:.0f}°.'))
B.append(f'<p>Pakai hasil itu untuk <b>orientasi elipsoid pencarian</b> saat estimasi: sumbu <i>major</i> '
         f'searah pitch &asymp; {PITCH:.0f}° di dalam bidang vein, <i>semi</i> searah strike, <i>minor</i> tegak '
         'lurus bidang vein; nisbah kira-kira 3 : 2 : 1.</p>')
B.append('<h3>Latihan 2c &mdash; pemulihan sesar lebih dulu</h3>')
B.append(f'<p>Di <b>Sesar 3D</b>, masukkan bidang dari <code>SIM_sesar.csv</code> (strike 110°, dip 65°, offset '
         f'{FA_OFF:.0f} m, <i>post</i>-mineralisasi) dan jalankan pemulihan sebelum pemodelan. Bandingkan domain '
         'lensa 2 &amp; 3 sebelum dan sesudah: tanpa pemulihan, domainnya pecah dan arah ore shoot-nya kacau '
         '(Gambar 3 kanan). Lensa 1 &amp; 4 tidak terpengaruh karena sesarnya terbatas &plusmn;150 m.</p>')
B.append('<h3>Latihan 2d &mdash; zonasi vertikal</h3>')
B.append(fig_html('zonasi', f'Zonasi vertikal terhadap paleo-muka air tanah RL {WT_RL:.0f} m. Kadar Au memuncak '
                            f'di sekitar RL {NOTE["zon_puncak"]} m bersamaan dengan tekstur <i>colloform</i>; '
                            f'Ag/Au naik dari &asymp;{NOTE["zon_agau_bawah"]} di bawah menjadi '
                            f'&asymp;{NOTE["zon_agau_atas"]} di atas; Pb+Zn naik ke bawah.'))
B.append('<p>Pelajaran praktisnya: <b>jangan menginterpolasi menembus batas zona</b>. Zona didih, zona '
         'base-metal, dan tudung tercuci adalah populasi kadar yang berbeda. Kalau dicampur dalam satu domain '
         'estimasi, variogramnya menjadi campuran dan hasil estimasi di kedua zona ikut salah.</p>')
B.append('<h3>Latihan 2e &mdash; top-cut</h3>')
B.append(fig_html('topcut', f'Sebaran Au di dalam vein: rata-rata {NOTE["au_mean"]} g/t, median '
                            f'{NOTE["au_med"]} g/t, CV {NOTE["au_cv"]}, maksimum {NOTE["au_max"]} g/t. '
                            f'1% sampel teratas sudah memuat {NOTE["tc_1"]}% logam &mdash; itulah alasan top-cut.'))
B.append('<p>Cobalah beberapa nilai top-cut dan lihat pengaruhnya pada rata-rata domain serta hasil estimasi. '
         'Catat juga: Ag <b>tidak</b> perlu top-cut seagresif Au, karena efek nuggetnya jauh lebih kecil &mdash; '
         'top-cut ditentukan per unsur, bukan satu angka untuk semua.</p>')

# ---- 3
B.append('<div class="page"></div><h2>3. Klasifikasi keyakinan sumber daya di Reporting BM</h2>')
B.append('<p class="lead">Baru di 0.24: <i>Reporting BM</i> dapat mengusulkan kelas Measured / Indicated / '
         'Inferred per blok, lalu melaporkan tonase dan kadar per kelas.</p>')
B.append('<p>Kelas dihitung dari atribut yang sudah dihasilkan <b>Model Estimation</b>:</p>')
B.append('<table><tr><th>Atribut</th><th>Arti</th></tr>'
         '<tr><td><code>est_pass</code></td><td>pass pencarian sampel: 1 = radius penuh (data rapat), '
         '2&ndash;3 = radius diperbesar</td></tr>'
         '<tr><td><code>est_nsamp</code></td><td>jumlah komposit yang dipakai blok itu</td></tr>'
         '<tr><td><code>est_sor</code> / <code>est_ke</code></td><td>slope of regression atau kriging '
         'efficiency (dapat dipilih)</td></tr></table>')
B.append(fig_html('klas', 'Alur penentuan kelas. Blok diuji berurutan dari syarat terketat; yang tidak '
                          'memenuhi turun ke kelas berikutnya.'))
B.append('<h3>Langkah</h3><ol class="steps">'
         '<li>Jalankan <b>Model Estimation</b> seperti biasa.</li>'
         '<li>Buka <b>Reporting BM</b> &rsaquo; bagian <b>&#9312; Atribut</b>. Di bawahnya ada kotak '
         '<b>Klasifikasi keyakinan</b>.</li>'
         '<li>Pilih ukuran keyakinan (SoR atau KE) dan sesuaikan ambangnya bila perlu.</li>'
         '<li>Klik <b>Hitung klasifikasi</b>. Hasilnya menjadi atribut kategori <code>klasifikasi</code>.</li>'
         '<li>Jalankan <b>Hitung reporting</b> dengan grup <b>Per atribut kategori &rarr; klasifikasi</b>.</li>'
         '<li>Di bagian <b>&#9314; Hasil</b> muncul tabel tonase &amp; kadar per kelas, ditambah '
         '<b>kurva grade &times; tonase bertumpuk per kelas</b>.</li></ol>')
B.append('<p>Atribut <code>klasifikasi</code> juga bisa diwarnai di tampilan 3D dan ikut ter-export ke CSV. '
         'Bila estimasi dijalankan ulang, klasifikasinya ikut dihitung ulang.</p>')
B.append('<div class="warn"><b>Ambang ini usulan geostatistik, bukan keputusan klasifikasi.</b> Penetapan '
         'Measured / Indicated / Inferred tetap wewenang <b>Competent Person</b> sesuai KCMI / JORC, yang juga '
         'menimbang spasi bor, kemenerusan geologi, kualitas QAQC dan kelayakan penambangan. Dua hal yang '
         '<b>belum</b> dipakai sebagai syarat otomatis: <b>spasi bor</b> dan <b>jumlah bor berbeda</b> per blok '
         '&mdash; keduanya belum direkam saat estimasi.</div>')
B.append('<p><b>Latihan.</b> Pada data simulasi, bagian dalam endapan (lebih dari ±140 m menurun dip) hampir '
         'tidak terbor &mdash; hanya tiap sayatan ke-3 yang punya bor dalam. Jalankan klasifikasi dan periksa: '
         'bagian itu seharusnya jatuh ke <b>Inferred</b>, dan bagian yang terbor rapat di dekat permukaan ke '
         '<b>Measured</b>. Kalau hasilnya tidak begitu, ambang Anda terlalu longgar.</p>')

# ---- 4
B.append('<div class="page"></div><h2>4. Topografi &amp; orthofoto resolusi sangat tinggi</h2>')
B.append('<p class="lead">Juga baru di 0.24, di <b>kedua</b> aplikasi: orthofoto dan topografi resolusi tinggi '
         'kini bisa ditampilkan tanpa membuat tampilan tersendat.</p>')
B.append('<p>Yang berubah di dalam: orthofoto disusun menjadi <b>piramida LOD</b> (tiap tingkat merata-ratakan '
         '2 &times; 2 piksel), lalu warna diambil dari tingkat yang sepadan dengan kerapatan tampilan. '
         'Resolusi <b>dan</b> luas mesh ortho sekarang mengikuti luas area yang sedang terlihat, jadi zoom masuk '
         'otomatis makin detail pada jumlah titik yang sama. Di menu <b>Peta (Mapping)</b>, orthofoto dipotong '
         'sesuai tampilan dan dikirim setajam layar &mdash; saat zoom dekat itu berarti resolusi aslinya. '
         'Topografi tidak lagi didesimasi sekali di awal, melainkan diambil satu titik per sel dari seluruh data '
         'di dalam tampilan.</p>')
B.append('<table><tr><th></th><th>Sebelum</th><th>Sesudah</th></tr>'
         '<tr><td>Mesh ortho, tampilan 400 m</td><td>1 m/titik &middot; 160.000 titik &middot; 592 ms</td>'
         '<td>0,91 m/titik &middot; 193.000 titik &middot; 525 ms</td></tr>'
         '<tr><td>Mesh ortho, zoom 40 m</td><td>1 m/titik &middot; 160.000 titik &middot; 592 ms</td>'
         '<td><b>0,1 m/titik</b> &middot; 215.000 titik &middot; 136 ms</td></tr>'
         '<tr><td>Mesh ortho, zoom 10 m</td><td>1 m/titik &middot; 160.000 titik &middot; 592 ms</td>'
         '<td><b>0,1 m/titik</b> &middot; 13.700 titik &middot; <b>3 ms</b></td></tr>'
         '<tr><td>Gambar ortho Peta 2D, zoom 10 m</td><td>2.666 &times; 2.666 px @ 0,15 m &middot; 255 ms &middot; 3,1 MB</td>'
         '<td><b>220 &times; 220 px @ 0,05 m</b> &middot; 6 ms &middot; 9 KB</td></tr>'
         '<tr><td>Titik topografi di jendela 10 m (anggaran 15.000)</td><td>15</td><td><b>172</b></td></tr>'
         '<tr><td>200.000 pembacaan elevasi</td><td>512 ms</td><td><b>14 ms</b></td></tr>'
         '<tr><td>Warna ortho pada mesh kasar</td><td>titik tunggal (berkerlip)</td><td>rata-rata area (anti-alias)</td></tr>'
         '</table>')
B.append('<p>Yang perlu Anda ketahui saat memakainya: kotak <b>Resolusi (m)</b> di panel orthofoto sekarang '
         'berfungsi sebagai <b>batas paling halus</b>, bukan resolusi tetap. Tampilan disegarkan kira-kira 0,3 '
         'detik setelah gerakan zoom/geser berhenti (bukan tiap frame), dan mesh dibuat sedikit lebih luas dari '
         'layar supaya geseran kecil tidak menyisakan tepi kosong. Klik ganda / autoscale mengembalikan tampilan '
         'ke seluruh area.</p>')
B.append('<div class="box"><b>Hasil laporan tidak berubah.</b> Grid elevasi yang cepat itu dipakai '
         '<b>hanya untuk tampilan</b> (menempelkan warna ortho ke topografi). Semua perhitungan '
         '<i>Reporting BM</i>, estimasi dan validasi tetap memakai fungsi elevasi aslinya. Pada uji 300 titik '
         'acak, selisih kedua jalur itu rata-rata 4 mm dan paling besar 3,8 cm pada permukaan dengan relief 30 m.</div>')
B.append('<p><b>Latihan.</b> Import <code>SIM_topo_xyz.csv</code> sebagai topografi, lalu '
         '<code>SIM_topo_xyz_nov.csv</code> sebagai versi berikutnya. Di <b>Data Spasial</b> bergantilah antar '
         'versi, lalu hitung volume sisa di <i>Reporting BM</i> dengan batas <b>di bawah topografi aktif</b> '
         'untuk kedua versi &mdash; bedanya adalah material yang sudah tergali.</p>')

# ---- 5
B.append('<div class="page"></div><h2>5. Bagian tutorial lama yang perlu disesuaikan</h2>')
B.append('<p>Dua tutorial bergambar yang lama masih berlaku untuk alur kerjanya, tetapi beberapa nama dan '
         'angkanya mengikuti data simulasi versi sebelumnya:</p>')
B.append('<table><tr><th>Di tutorial lama</th><th>Sekarang</th></tr>'
         '<tr><td>Domain <code>QV_Utama</code> dan <code>QV_HW1</code> (2 vein)</td>'
         '<td><code>QV_Lensa1</code> &hellip; <code>QV_Lensa4</code> + <code>QV_Splay_HW</code> '
         '(array 4 lensa en-echelon)</td></tr>'
         '<tr><td><code>QV_Utama_Leapfrog.obj</code></td><td><code>QV_Lensa2_Leapfrog.obj</code></td></tr>'
         '<tr><td>Kolom assay: Au, Ag, SxS</td><td>Au, Ag, Cu, Pb, Zn, S, As_ppm, SG</td></tr>'
         '<tr><td>Kolom geologi: Lith, Alt, Ox</td><td>+ Texture, RQD, Recovery</td></tr>'
         f'<tr><td>&plusmn;33 bor, &plusmn;2.500 baris assay</td><td>{NOTE["n_bor"]} bor resource + '
         f'{NOTE["n_gc"]} bor grade control, &plusmn;{(NOTE["n_assay"]+NOTE["n_gc_assay"])//1000} ribu baris assay</td></tr>'
         f'<tr><td>Tebal vein 1&ndash;3,2 m</td><td>median {NOTE["tb_med"]} m, p90 {NOTE["tb_p90"]} m '
         '(endapan vein sempit, dengan pembengkakan di zona dilatan)</td></tr>'
         '</table>')
B.append('<p>Langkah-langkah menu, urutan kerja dan penjelasan konsep di kedua tutorial itu tidak berubah. '
         'Yang perlu Anda sesuaikan hanya nama domain yang diketik dan angka yang muncul di layar.</p>')

HTML = ('<html><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>'
        % (CSS, '\n'.join(B)))
tmp = os.path.join(HERE, '_tutorial_024.html')
open(tmp, 'w', encoding='utf-8').write(HTML)

with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--disable-dev-shm-usage'])
    pg = b.new_page()
    pg.goto('file://' + tmp)
    pg.wait_for_timeout(700)
    pg.pdf(path=PDF, format='A4', print_background=True,
           margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
           display_header_footer=True,
           header_template='<div></div>',
           footer_template='<div style="font-size:7pt;color:#6b7682;width:100%;text-align:center;'
                           'font-family:Arial">Tutorial Tambahan GC-Ex 0.24 &middot; halaman '
                           '<span class="pageNumber"></span> / <span class="totalPages"></span></div>')
    b.close()
os.remove(tmp)
print('OK', PDF, os.path.getsize(PDF), 'byte')
print('angka:', NOTE)
