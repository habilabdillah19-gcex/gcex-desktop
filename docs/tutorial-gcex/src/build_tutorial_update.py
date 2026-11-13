# -*- coding: utf-8 -*-
"""Menyusun 'Tutorial Update GC-Ex' (HTML -> PDF A4) untuk GC-Ex Drill Hole Ultimate & Block Model.

BEDANYA dengan build_tutorial.py / build_tutorial_bm.py: tutorial ini TIDAK memakai tangkapan layar
aplikasi, jadi bisa dibangun di mesin mana pun (termasuk CI Linux) tanpa menjalankan GC-Ex.
Semua gambarnya dihitung langsung dari model data simulasi (make_sim_data.py) dan dari berkas CSV
yang dihasilkannya, sehingga angka di gambar selalu cocok dengan data latihan yang dikirim.

Pendamping 'Petunjuk Teknis GC-Ex' (build_petunjuk_teknis.py): kalau petunjuk teknis menjawab
*bagaimana cara kerjanya*, dokumen ini menjawab *apa yang baru dan bagaimana memakainya*.

Jalankan:  python docs/tutorial-gcex/src/build_tutorial_update.py
Hasil:     docs/GCEx_Tutorial_Update.pdf
"""
import csv
import datetime
import html
import math
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import doc_gcex as D

HERE = os.path.dirname(os.path.abspath(__file__))
TUT = os.path.abspath(os.path.join(HERE, '..'))
DATA = os.path.join(TUT, 'data')
FIGD = os.path.join(HERE, 'fig_update')
PDF = os.path.join(os.path.abspath(os.path.join(TUT, '..')), 'GCEx_Tutorial_Update.pdf')
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



# ------------------------------------------------------------------ F8 kerangka AOI pada sayatan
def f_aoi():
    """Sayatan E-RL: topografi, lensa vein, dan kerangka blok AOI yang dipotong topografi."""
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    yN = float(np.median([c[1] for c in COL.values()]))
    xs = np.linspace(C[0] - 120, C[0] + 120, 240)
    zt = topo(xs, np.full_like(xs, yN))
    ax.plot(xs, zt, color=INK, lw=1.4, zorder=6, label='topografi')
    # kerangka blok 10 x 5 m di bawah topografi
    bx, bz = 10.0, 5.0
    x0 = np.floor((C[0] - 120) / bx) * bx
    zb = float(np.floor((np.min(zt) - 110) / bz) * bz)
    nx = int((240) // bx)
    nz = int((np.max(zt) - zb) // bz) + 1
    pit = lambda x: np.maximum(np.min(zt) - 55, topo(x, yN) - 85 + 0.55 * np.abs(x - C[0]))
    nIn = nPit = 0
    for i in range(nx):
        xc = x0 + (i + 0.5) * bx
        tzv = float(topo(np.array([xc]), np.array([yN]))[0])
        pzv = float(pit(np.array([xc]))[0])
        for k in range(nz):
            zc = zb + (k + 0.5) * bz
            if zc > tzv:
                continue
            inpit = zc >= pzv
            ax.add_patch(plt.Rectangle((xc - bx / 2, zc - bz / 2), bx, bz, fill=True,
                                       facecolor=('#dde7f3' if inpit else '#f1f3f6'),
                                       edgecolor='#c3ccd8', lw=0.3, zorder=1))
            nIn += 1
            nPit += 1 if inpit else 0
    ax.plot(xs, pit(xs), color=ACC2, lw=1.6, ls='--', zorder=6, label='desain pit')
    # jejak lensa pada sayatan ini
    AAg, BBg = np.meshgrid(np.linspace(-170, 170, 300), np.linspace(-120, 120, 180))
    first = True
    for V in LENSA:
        T = thick(AAg.ravel(), BBg.ravel(), V)
        q1 = vpt(AAg.ravel()[:, None], BBg.ravel()[:, None], V, 0.0)
        m = (T > 0.3) & (np.abs(q1[:, 1] - yN) < 2.0)
        if m.any():
            ax.scatter(q1[m, 0], q1[m, 2], s=1.0, color=ACC, alpha=0.75, zorder=5,
                       label=('solid domain (vein)' if first else None))
            first = False
    ax.set_xlabel('Easting (m)'); ax.set_ylabel('RL (m)')
    ax.set_title('Kerangka blok AOI pada sayatan: biru = di dalam desain pit, kelabu = di bawah topografi di luar pit')
    ax.legend(loc='lower left', fontsize=7, framealpha=0.9)
    NOTE['aoi_blok'] = nIn; NOTE['aoi_pit'] = nPit
    return save(fig, 'aoi')


# ------------------------------------------------------------------ F9 kadar waste vs jarak ke vein
def f_waste():
    """Dari data latihan: kadar Au sampel DI LUAR vein terhadap jaraknya ke vein terdekat."""
    ins, dist, _, _, _ = g['inside_all'](P)
    out = (~INV) & (dist > 0) & (dist < 40) & np.isfinite(AU)
    d, a = dist[out], AU[out]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.7))
    ax.scatter(d, a, s=2.4, color=MUT, alpha=0.30, lw=0)
    bins = np.array([0, 1.5, 3, 5, 8, 12, 18, 25, 40.0])
    md, q9, xc = [], [], []
    for i in range(len(bins) - 1):
        m = (d >= bins[i]) & (d < bins[i + 1])
        if m.sum() >= 8:
            md.append(float(np.median(a[m]))); q9.append(float(np.percentile(a[m], 90)))
            xc.append(float((bins[i] + bins[i + 1]) / 2))
    ax.plot(xc, md, '-o', color=ACC, lw=1.8, ms=3.5, label='median')
    ax.plot(xc, q9, '--', color=ACC2, lw=1.3, label='persentil 90')
    ax.set_yscale('log'); ax.set_xlabel('jarak ke vein terdekat (m)'); ax.set_ylabel('Au (g/t)')
    ax.set_title('Kadar sampel di luar solid'); ax.legend(fontsize=7)
    # berapa logam yang ada di luar solid
    LEN = np.array([float(x['To']) - float(x['From']) for x in ASY])
    inM = float(np.sum(AU[INV] * LEN[INV])); outM = float(np.sum(AU[~INV] * LEN[~INV]))
    bands, vals = [], []
    for i in range(len(bins) - 1):
        m = (~INV) & (dist >= bins[i]) & (dist < bins[i + 1])
        if m.sum():
            bands.append('%g-%g' % (bins[i], bins[i + 1])); vals.append(float(np.sum(AU[m] * LEN[m])))
    ax2.bar(bands, vals, color=ACC, alpha=0.85)
    ax2.set_xlabel('pita jarak ke vein (m)'); ax2.set_ylabel('Au x panjang (g/t.m)')
    ax2.set_title('Logam dalam sampel di luar solid')
    ax2.tick_params(axis='x', labelrotation=35, labelsize=6.5)
    NOTE['w_med15'] = round(float(np.median(a[d < 1.5])), 3) if (d < 1.5).sum() else None
    NOTE['w_med5'] = round(float(np.median(a[(d >= 1.5) & (d < 5)])), 3) if ((d >= 1.5) & (d < 5)).sum() else None
    NOTE['w_med12'] = round(float(np.median(a[(d >= 5) & (d < 12)])), 3) if ((d >= 5) & (d < 12)).sum() else None
    NOTE['w_share'] = round(100 * outM / max(1e-9, inM + outM), 1)
    NOTE['w_n'] = int(out.sum())
    return save(fig, 'waste')


# ------------------------------------------------------------------ F10 proporsi volume blok di batas solid
def f_frac():
    """Sayatan E-RL: grid blok 5 m di atas jejak solid, tiap sel diberi proporsi volumenya di dalam solid."""
    yN = float(np.median([c[1] for c in COL.values()]))
    # medan 'di dalam solid' pada bidang sayatan y = yN, dihitung dari model
    def ins_grid(xs, zs):
        GX, GZ = np.meshgrid(xs, zs)
        pts = np.column_stack([GX.ravel(), np.full(GX.size, yN), GZ.ravel()])
        ins, _, _, _, _ = g['inside_all'](pts)
        return ins.reshape(GZ.shape)
    # cari jendela: di mana solid memotong sayatan ini
    xs0 = np.linspace(C[0] - 160, C[0] + 160, 200)
    zs0 = np.linspace(C[2] - 90, C[2] + 70, 140)
    M0 = ins_grid(xs0, zs0)
    if not M0.any():
        yN = float(C[1]); M0 = ins_grid(xs0, zs0)
    XX, ZZ = np.meshgrid(xs0, zs0)
    xc0, zc0 = float(np.median(XX[M0])), float(np.median(ZZ[M0]))
    bs, nx, nz = 5.0, 14, 11
    x0 = np.floor((xc0 - nx * bs / 2) / bs) * bs
    z0 = np.floor((zc0 - nz * bs / 2) / bs) * bs
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    nPart = nFull = 0
    for i in range(nx):
        for k in range(nz):
            xc = x0 + (i + 0.5) * bs
            zc = z0 + (k + 0.5) * bs
            gx = xc - bs / 2 + (np.arange(8) + 0.5) * bs / 8
            gz = zc - bs / 2 + (np.arange(8) + 0.5) * bs / 8
            fr = float(ins_grid(gx, gz).mean())
            if fr <= 0:
                col = '#f6f8fa'
            elif fr >= 0.999:
                col = '#1f4e8c'; nFull += 1
            else:
                col = '#aac4e4'; nPart += 1
            ax.add_patch(plt.Rectangle((xc - bs / 2, zc - bs / 2), bs, bs, facecolor=col,
                                       edgecolor='#c3ccd8', lw=0.4, zorder=1))
            if 0 < fr < 0.999:
                ax.text(xc, zc, ('%.2f' % fr).lstrip('0'), ha='center', va='center',
                        fontsize=5.6, color=INK, zorder=4)
    # batas solid sebagai garis kontur, bukan sebaran titik
    xf = np.linspace(x0, x0 + nx * bs, 320)
    zf = np.linspace(z0, z0 + nz * bs, 260)
    ax.contour(xf, zf, ins_grid(xf, zf).astype(float), levels=[0.5],
               colors=[ACC2], linewidths=1.7, zorder=5)
    ax.set_xlim(x0, x0 + nx * bs); ax.set_ylim(z0, z0 + nz * bs)
    ax.set_xlabel('Easting (m)'); ax.set_ylabel('RL (m)'); ax.set_aspect('equal')
    ax.set_title('Proporsi volume di dalam solid per blok 5 m\n(garis oranye = batas solid, angka = sb_frac)')
    ax.grid(False)
    NOTE['fr_part'] = nPart; NOTE['fr_full'] = nFull
    return save(fig, 'frac')



def adp_nodes(a0, a1, D, h0, K):
    """Sama dengan imAdpNodes (GC-Ex Drill Hole 0.24.71): simpul rapat (= h0) di dekat data, menjarang sampai K x h0."""
    D = np.sort(np.asarray(D)); o = [a0]; x = a0
    while x < a1 - 1e-9:
        near = float(np.min(np.abs(D - x))) if len(D) else 1e9
        h = h0 * min(K, 1 + near / (3 * h0)); x = x + h
        if x > a1 - 0.3 * h: x = a1
        o.append(x)
    return np.array(o)


def f_vsys():
    """Vein system: satu kolom kode -> satu domain per kode (kiri); resolusi adaptif sepanjang strike (kanan)."""
    VC = np.array([x.get('Vein', '-') for x in GEO]); m = VC != '-'
    cod = sorted(set(VC[m])); col = ['#1f4e8c', '#c98a16', '#2f9e44', '#c2255c', '#7048e8']
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.2), gridspec_kw={'width_ratios': [1.25, 1]})
    a = ax[0]
    for k, c in zip(cod, col):
        q = P[m & (VC == k)]; a.scatter(q[:, 0] - g['E0'], q[:, 1] - g['N0'], s=3, c=c, label='%s (%d)' % (k, int((VC == k).sum())))
    a.set_aspect('equal'); a.set_xlabel('Easting relatif (m)'); a.set_ylabel('Northing relatif (m)')
    a.set_title('Kolom geologi "Vein" \u2192 %d domain' % len(cod)); a.legend(fontsize=6, markerscale=3, loc='best')
    sv = np.array([math.sin(math.radians(STRIKE)), math.cos(math.radians(STRIKE)), 0.0])
    q = P[m & (VC == 'QV_Lensa2')]; s = (q - q.mean(0)) @ sv; s0, s1 = s.min() - 15, s.max() + 15
    nU = np.linspace(s0, s1, int(math.ceil((s1 - s0) / 2)) + 1); nA = adp_nodes(s0, s1, s, 2.0, 4.0)
    b = ax[1]; b.plot(s, np.full(len(s), 2.0), '|', color=INK, ms=8, label='kontak bor')
    b.plot(nU, np.full(len(nU), 1.0), '|', color=MUT, ms=8, label='seragam 2 m: %d simpul' % len(nU))
    b.plot(nA, np.zeros(len(nA)), '|', color=ACC2, ms=8, label='adaptif \u00d74: %d simpul' % len(nA))
    b.set_ylim(-0.8, 3.2); b.set_yticks([]); b.set_xlabel('jarak searah strike QV_Lensa2 (m)')
    b.set_title('Simpul mesh searah strike'); b.legend(fontsize=6, loc='upper center', ncol=1)
    NOTE['vs_kode'] = {k: int((VC == k).sum()) for k in cod}; NOTE['vs_simpul'] = [len(nU), len(nA)]
    fig.tight_layout(); return save(fig, 'vsys')


def f_jalur():
    """Jalur proyek (DH 0.24.73): tiap tahap punya pintu "Buat di GC-Ex" dan, di jalur Lanjutan, "Pakai acuan"."""
    from matplotlib.patches import FancyBboxPatch
    tahap = [('Domain & solid', 'Geomodeller Vein / Autorun Wireframe', 'wireframe Leapfrog / Surpac\n(Serap atau Eksak)'),
             ('Block model', 'Buat kerangka blok (AOI)', 'block model .mdl / CSV\n(versi acuan)'),
             ('Parameter estimasi', 'Geostatistik, auto-fit, KNA,\nAutorun Estimasi dari Nol', 'parameter dari log Surpac\n(konfirmasi bila ditimpa)'),
             ('Estimasi & laporan', 'Model Estimation, Autorun Estimation', 'sama: memakai domain,\nblok & parameter di atas')]
    fig, ax = plt.subplots(figsize=(7.4, 3.6)); ax.set_xlim(0, 10); ax.set_ylim(0, len(tahap) + 1.1); ax.axis('off')
    ax.text(2.05, len(tahap) + 0.6, 'Tahap', ha='center', fontsize=8.5, weight='bold', color=INK)
    ax.text(5.0, len(tahap) + 0.6, 'Mulai dari nol', ha='center', fontsize=8.5, weight='bold', color='#2f9e44')
    ax.text(8.05, len(tahap) + 0.6, 'Lanjutkan dari Surpac / Leapfrog', ha='center', fontsize=8.5, weight='bold', color=ACC2)
    for i, (t, nol, acu) in enumerate(tahap):
        y = len(tahap) - i - 0.1
        ax.add_patch(FancyBboxPatch((0.6, y - 0.36), 2.9, 0.72, boxstyle='round,pad=0.02', fc='#eef2f7', ec=MUT, lw=0.6))
        ax.text(2.05, y, t, ha='center', va='center', fontsize=8, color=INK, weight='bold')
        ax.add_patch(FancyBboxPatch((3.7, y - 0.36), 2.6, 0.72, boxstyle='round,pad=0.02', fc='#e8f5ec', ec='#2f9e44', lw=0.8))
        ax.text(5.0, y, 'Buat di GC-Ex:\n' + nol, ha='center', va='center', fontsize=6.3, color=INK)
        last = i == len(tahap) - 1
        ax.add_patch(FancyBboxPatch((6.5, y - 0.36), 1.45, 0.72, boxstyle='round,pad=0.02', fc='#e8f5ec', ec='#2f9e44', lw=0.8))
        ax.text(7.22, y, 'Buat baru\n(alat yang sama)', ha='center', va='center', fontsize=6.0, color=INK)
        ax.add_patch(FancyBboxPatch((8.05, y - 0.36), 1.85, 0.72, boxstyle='round,pad=0.02', fc='#fdf3e1' if not last else '#f4f4f4', ec=ACC2 if not last else MUT, lw=0.8))
        ax.text(8.97, y, ('Pakai acuan:\n' if not last else '') + acu, ha='center', va='center', fontsize=5.9, color=INK)
    ax.text(5.0, 0.15, 'fitur adaptasi tidak tampil', ha='center', fontsize=6.5, color=MUT, style='italic')
    ax.text(8.05, 0.15, 'pintu acuan terbuka hanya bila acuannya dicentang', ha='center', fontsize=6.5, color=MUT, style='italic')
    fig.tight_layout(); return save(fig, 'jalur')


F = {k: f() for k, f in (('peta', f_peta), ('bidang', f_bidang), ('gt', f_gt), ('kipas', f_kipas),
                         ('zonasi', f_zonasi), ('topcut', f_topcut), ('klas', f_klas),
                         ('aoi', f_aoi), ('waste', f_waste), ('frac', f_frac), ('vsys', f_vsys), ('jalur', f_jalur))}
F['vunion'] = 'vunion.png'   # tangkapan layar aplikasi (data latihan fiktif), bukan matplotlib
F['svrek'] = 'svrek.png'     # tangkapan layar uji uji_solid_vein_union.py (data sintetis)
F['skin_bm'] = 'skin_bm.png' # data latihan: Project Tree & Properti tema baru (0.24.74)
F['topopit'] = 'topopit.png' # data latihan: topografi Data Spasial x SIM_pit_fase1, AU_GC >= 0,34 di antara topo & pit

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
    return ('<figure><img src="fig_update/%s"><figcaption><b>Gambar %d.</b> %s</figcaption></figure>'
            % (F[key], fign[0], cap))


VBM, VDH = D.versi()


B = []
# sampul disisipkan di akhir: daftar isinya dihitung dari judul <h2> yang ada

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
B.append(D.tabel(['Kelas', 'Syarat bawaan (semuanya dapat diubah di panel)'], [
    ['<b>Measured</b>', 'pass &le; 1, komposit &ge; 12, SoR &ge; 0,75, lubang bor berbeda &ge; 3, spasi bor &le; 25 m'],
    ['<b>Indicated</b>', 'pass &le; 2, komposit &ge; 7, SoR &ge; 0,45, lubang bor berbeda &ge; 2, spasi bor &le; 50 m'],
    ['<b>Inferred</b>', 'blok terestimasi lainnya'],
    ['Belum terklasifikasi', 'blok tanpa estimasi']]))
B.append('<p>Dua syarat terakhir dijelaskan di bab 4.</p>')
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
B.append('<div class="page"></div><h2>4. Kerapatan bor per blok</h2>')
B.append('<p class="lead">Jumlah komposit saja bukan ukuran kerapatan bor. Dua puluh komposit dari '
         '<b>satu</b> lubang bor tidak sama artinya dengan dua puluh komposit dari enam lubang &mdash; '
         'padahal justru kerapatan bor itulah yang dipakai Competent Person untuk menetapkan kelas.</p>')
B.append('<p>Karena itu <b>Model Estimation</b> kini merekam tiga atribut baru per blok, dihitung dari '
         'komposit yang benar-benar dipakai kriging:</p>')
B.append(D.tabel(['Atribut', 'Arti'], [
    ['<code>est_nhole</code>', 'jumlah <b>lubang bor berbeda</b> yang komposit-nya dipakai blok itu'],
    ['<code>est_dmin</code>', 'jarak (m) dari pusat blok ke komposit terdekat yang dipakai'],
    ['<code>est_spasi</code>', 'perkiraan <b>spasi bor setempat</b> (m): tiap lubang diwakili komposit '
     'terdekatnya ke blok, lalu dirata-ratakan jarak mendatar tiap lubang ke lubang terdekat lainnya. '
     'Bernilai &minus;99 bila lubang yang dipakai kurang dari dua']]))
B.append('<p>Ketiganya ikut ke block model, tampilan 3D, reporting dan export <code>.mdl</code> seperti '
         'atribut estimasi lainnya &mdash; jadi dapat juga Anda pakai sebagai filter atau pewarnaan sendiri, '
         'bukan hanya untuk klasifikasi.</p>')
B.append('<p>Contoh perbedaannya pada uji dengan kisi bor teratur:</p>')
B.append(D.tabel(['Keadaan blok', 'Kelas menurut aturan lama', 'Kelas sekarang'], [
    ['4 bor, spasi 20 m, 16 komposit', 'Measured', 'Measured'],
    ['<b>1 bor</b>, 20 komposit', 'Measured', '<b>Inferred</b>'],
    ['3 bor, <b>spasi 80 m</b>, 16 komposit', 'Measured', '<b>Inferred</b>'],
    ['2 bor, spasi 40 m, 10 komposit', 'Indicated', 'Indicated']]))
B.append('<div class=warn>&#9888; Block model yang diestimasi dengan versi sebelum 0.24.4 belum punya '
         '<code>est_nhole</code> / <code>est_spasi</code>. Panel memberi tahu hal ini, kedua syarat itu '
         'diabaikan, dan hasilnya sama seperti sebelumnya. Jalankan ulang <b>Model Estimation</b> agar '
         'kerapatan bor ikut terekam.</div>')
B.append('<p><b>Latihan.</b> Pada data simulasi, bagian dalam endapan (lebih dari &plusmn;140 m menurun dip) '
         'hanya terbor di tiap sayatan ke-3. Jalankan klasifikasi lalu warnai block model dengan '
         '<code>est_spasi</code>: bagian itu akan terlihat jelas renggang, dan wajar jatuh ke Inferred.</p>')

B.append('<div class="page"></div><h2>5. Topografi &amp; orthofoto resolusi sangat tinggi</h2>')
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
B.append('<div class="page"></div><h2>6. GC-Ex Block Model: yang baru</h2>')
B.append('<p class="lead">Perbaikan di GC-Ex Block Model berpusat pada satu keluhan: digitasi manual dulu '
         'terasa seperti warga kelas dua dibanding dig block otomatis. Sekarang keduanya setara.</p>')
B.append(D.tabel(['Yang berubah', 'Keterangan'], [
    ['<b>Digitasi manual setara otomatis</b>', 'menekan <b>Enter</b> menutup string secara otomatis, lalu '
     'poligonnya mendapat menu yang sama dengan hasil otomatis: edit bentuk, ubah warna, dan hitungan '
     'grade &times; tonase'],
    ['<b>Poligon as-mined dapat diedit</b>', 'bentuk maupun warnanya, tidak lagi hanya dapat dilihat'],
    ['<b>Register poligon</b>', 'warna dapat diubah, tidak lagi hanya String ID'],
    ['<b>Subnode per flitch di Project Tree</b>', 'audit atau review dapat langsung memilih flitch yang '
     'dimaksud, tanpa menelusuri dari awal'],
    ['<b>Tampilan 3D dig block &rarr; as-mined</b>', 'satu menu untuk melihat hasil pekerjaan dari pembuatan '
     'dig block sampai model as-mined'],
    ['<b>Rekap as-mined satu berkas</b>', 'hasil running as-mined murni dapat digabung menjadi satu '
     '<code>.mdl</code>'],
    ['<b>Penampang Sayatan seragam</b>', 'UI/UX Penampang 2D dan Sayatan 3D freehand dibuat sama dengan '
     'GC-Ex Drill Hole Ultimate'],
    ['<b>Tanpa jeda saat zoom</b>', 'segmen garis yang bersambung digabung dan kotak blok 2D dirapatkan, '
     'sehingga window zoom tidak lagi tersendat'],
    ['<b>Topografi &amp; orthofoto resolusi tinggi</b>', 'sama dengan Drill Hole Ultimate (bab 5)']]))
B.append('<div class=box>Garis putus-putus merah yang dulu tidak bisa dihapus pada dig block berasal dari '
         'pemutus segmen yang ditulis di setiap ruas poligon. Segmen yang bersambung kini disatukan, jadi '
         'garis itu tidak muncul lagi dan gambarnya jauh lebih ringan.</div>')

# ---- 7  kerangka blok AOI
B.append('<div class="page"></div><h2>7. Block model dari nol: kerangka AOI</h2>')
B.append('<p class="lead">Sampai versi lalu, GC-Ex Drill Hole <b>selalu memerlukan block model dari luar</b>. '
         'Estimasi hanya mengoreksi blok yang pusatnya di dalam solid domain, dan hanya bisa menambah blok pada '
         'bagian solid yang belum punya blok. Akibatnya pemodelan selalu dituntun model lama, dan material '
         '<b>waste</b> di sekitar wireframe ore hanya ada bila model impornya memang memuatnya.</p>')
B.append('<p>Menu <b>Block Model</b> sekarang punya tombol <b>&#8862; Buat kerangka blok (AOI)</b>: grid persegi '
         'seluruh <i>area of interest</i> &mdash; ore <b>dan</b> waste &mdash; dari extent, ukuran blok dan RL yang '
         'Anda tentukan. Berlaku untuk semua tipe deposit, karena kerangkanya murni geometri dan tidak mengenal '
         'tipe endapan.</p>')
B.append(D.tabel(['Batas', 'Perilaku'], [
    ['Potong topografi aktif', 'hanya blok yang pusatnya <b>di bawah</b> permukaan (sisa / in-situ)'],
    ['Di dalam desain pit', 'blok dipertahankan hanya <b>antara dasar pit dan topografi</b>'],
    ['Rentang RL', 'batas atas / bawah manual'],
    ['Poligon area', 'fitur tertutup menu <b>Map</b> atau string Surpac &mdash; sama dengan poligon di Reporting BM']]))
B.append(fig_html('aoi', 'Kerangka blok AOI pada satu sayatan data latihan: %d blok terbentuk di bawah topografi, '
                  '%d di antaranya di dalam desain pit. Permukaan yang dipakai sama dengan Reporting BM, jadi volume '
                  'yang dilaporkan konsisten dengan kerangka yang dibangun.' % (NOTE['aoi_blok'], NOTE['aoi_pit'])))
B.append('<h3>Tiga keadaan, tiga mode</h3>')
B.append(D.tabel(['Keadaan Anda', 'Mode'], [
    ['Belum ada block model sama sekali', '<b>Ganti / penuh</b> &mdash; seluruh AOI dibuat dari nol, tanpa acuan apa pun'],
    ['Sudah ada <code>.mdl</code>, cakupannya lebih sempit dari AOI',
     '<b>Pertahankan &amp; isi kekosongan</b> &mdash; <code>.mdl</code> dipertahankan <b>utuh</b> beserta seluruh atributnya '
     '(termasuk kadar waste), blok baru hanya di sel yang <b>belum tercakup</b>'],
    ['Sudah ada <code>.mdl</code>, ingin mulai dari nol', '<b>Ganti</b>']]))
B.append('<div class=box>Cakupan diuji <b>per sel</b>: setiap blok impor menandai semua sel AOI yang ditimpa '
         'kotaknya. Jadi sub-blok Surpac yang lebih kecil maupun blok induk yang lebih besar sama-sama terbaca '
         'benar. Atribut kategori <code>AOI_ASAL</code> membedakan <b>impor</b> dan <b>kerangka</b>.</div>')
B.append('<div class=warn>Blok kerangka <b>belum punya kadar</b>: atribut numerik model lama diisi NaN, atribut '
         'kategori dibiarkan kosong. Pengisian kadarnya pekerjaan Model Estimation &mdash; bab berikutnya.</div>')
B.append('<p>Tombol <b>Hitung jumlah blok</b> menampilkan ukuran grid, jumlah blok baru, jumlah blok impor yang '
         'dipertahankan, perincian yang dibuang per sebab, dan perkiraan volume &mdash; sebelum apa pun dibangun. '
         'Versi block model berjenis <code>aoi</code> menyimpan <b>parameter saja, bukan bloknya</b>, jadi file '
         'proyek tetap ringan dan kerangka dibangun ulang saat versi itu diaktifkan.</p>')

# ---- 8  estimasi waste
B.append('<div class="page"></div><h2>8. Estimasi waste: kadar di luar wireframe ore</h2>')
B.append('<p class="lead">Model Estimation adalah <i>hard boundary</i> per domain: hanya blok yang pusatnya di '
         'dalam solid vein yang diestimasi. Blok di luarnya tidak disentuh, sehingga kadar waste di sekitar '
         'wireframe tidak pernah ada &mdash; padahal justru itu yang menentukan <b>dilusi</b>, <b>ore loss</b>, dan '
         'tonase total material di bawah topografi / di dalam desain pit.</p>')
B.append('<h3>Mengapa waste bukan kadar nol</h3>')
B.append(fig_html('waste', 'Dari %s sampel data latihan yang berada <b>di luar</b> solid vein: kadar Au terhadap '
                  'jarak ke vein terdekat (kiri) dan logam yang dikandungnya per pita jarak (kanan).'
                  % ('{:,}'.format(NOTE['w_n']).replace(',', '.'))))
B.append('<p>Angka dari data latihan itu sendiri:</p>')
B.append(D.tabel(['Jarak ke vein', 'Median Au sampel di luar solid'], [
    ['&lt; 1,5 m', '<b>%s g/t</b>' % str(NOTE['w_med15']).replace('.', ',')],
    ['1,5 &ndash; 5 m', '%s g/t' % str(NOTE['w_med5']).replace('.', ',')],
    ['5 &ndash; 12 m', '%s g/t' % str(NOTE['w_med12']).replace('.', ',')]]))
B.append('<div class=box>Dari seluruh logam Au yang terkandung dalam sampel (kadar &times; panjang), '
         '<b>%s%%</b> berada pada interval <b>di luar</b> solid vein. Halo di sekitar vein epitermal '
         'bukan kadar nol &mdash; justru halo 0,1&ndash;0,3 g/t itulah yang menentukan apakah dilusi masih '
         'ekonomis.</div>' % str(NOTE['w_share']).replace('.', ','))
B.append('<h3>Cara memakainya &mdash; jalur vein</h3>')
B.append(D.steps(
    'Pastikan blok waste <b>sudah ada</b> di block model. Bila cakupannya belum penuh, buat / lengkapi dulu dengan '
    '<b>kerangka blok AOI</b> (bab 7). Modul ini tidak membuat blok baru.',
    'Menu <b>Model Estimation</b> &rarr; bagian <b>&#9317; Estimasi waste</b>.',
    '<b>Variogram yang dipakai</b>: biarkan <b>Otomatis</b>. Bila Anda sudah memfit variogram waste sendiri '
    '(lihat di bawah), variogram itu dipakai untuk seluruh blok waste; kalau belum, dipakai variogram '
    '<b>domain terdekat</b> dan blok yang jauh dari semua domain diisi <b>IDW</b>.',
    'Atur <b>panjang komposit</b> dan <b>top-cut</b> waste. Top-cut tersendiri mencegah satu assay tinggi di luar '
    'solid menarik kadar seluruh halo.',
    'Pilih batas: hanya blok <b>di bawah topografi</b> dan/atau <b>di dalam desain pit</b>.',
    'Klik <b>Periksa dulu</b> &rarr; jumlah blok waste, jumlah komposit waste, perkiraan pembagian kriging vs IDW. '
    'Lalu <b>Jalankan estimasi waste</b>.'))
B.append(D.tabel(['Unsur', 'Aturan'], [
    ['Sampel', 'komposit dari interval bor yang <b>tidak di-flag domain apa pun</b> &mdash; <i>hard boundary waste</i>, '
     'sehingga kadar halo tidak tertarik naik oleh kadar vein'],
    ['Variogram', 'waste sendiri bila ada; kalau tidak, variogram <b>domain terdekat</b> (dicari dari komposit '
     'ber-flag tiap domain), dan <b>IDW</b> bila jaraknya melebihi ambang'],
    ['Penanda hasil', '<code>domain_est = WASTE</code>, <code>est_type = 3</code>; blok IDW <code>est_pass = 9</code> '
     'dengan <code>est_sor</code> / <code>est_ke</code> / <code>est_kv</code> = &minus;99']]))
B.append('<div class=box><b>Mengapa IDW untuk blok yang jauh.</b> Variogram sebuah domain hanya berlaku di sekitar '
         'domain itu. Memakainya pada blok yang jauh berarti mengaku tahu kontinuitas di tempat yang tidak punya '
         'data domain &mdash; kriging akan tetap menghasilkan angka, lengkap dengan <i>slope of regression</i> dan '
         '<i>kriging efficiency</i> yang <b>menyesatkan</b>. IDW tidak berpura-pura: ia hanya pembobotan jarak, '
         'dan karena itu ketiga ukuran keyakinannya diisi &minus;99.</div>')
B.append('<h3>Memfit variogram waste sendiri</h3>')
B.append('<p>Memakai salinan variogram domain tetap sebuah pinjaman: kontinuitas halo tidak harus sama dengan '
         'kontinuitas bijih &mdash; biasanya <b>nugget lebih besar</b>, <b>sill lebih kecil</b>, dan <b>range lebih '
         'panjang</b>. Seluruh mesin Geostatistik kini terbuka untuk populasi waste:</p>')
B.append(D.steps(
    'Menu <b>Geostatistik</b>, bilah <b>Domain</b> &rarr; pilih <b>WASTE (di luar semua domain)</b>. Komposit yang '
    'dipakai hanya interval yang tidak di-flag domain apa pun &mdash; populasi yang <b>sama</b> dengan sampel '
    'estimasi waste.',
    'Kerjakan seperti biasa: statistik, histogram, variogram arah &amp; <b>fan</b>, fitting model, <b>KNA</b>.',
    'Tab <b>Uji estimasi</b> &rarr; <b>&#8681; Simpan ke WASTE</b>.',
    'Kembali ke <b>Model Estimation</b>: mode <b>Otomatis</b> kini memakai variogram itu untuk <b>seluruh</b> blok '
    'waste tanpa uji jarak, dan IDW hanya dipakai bila sampel di sekitar blok tidak cukup.'))
B.append('<h3>Jalur laterit</h3>')
B.append('<p>Pada endapan berlapis, kadar berubah mengikuti <b>kelengkungan permukaan lapisan</b>, bukan jarak '
         'lurus 3D: dua titik berjarak sama bisa sangat berbeda bila satu sejajar permukaan dan satu memotongnya. '
         'Karena itu menu <b>Stratified-Laterite</b> punya bagian <b>&#9316;b Estimasi waste</b> sendiri, dengan '
         'pencarian sampel di <b>ruang unfold</b>:</p>')
B.append(D.tabel(['Zona', 'Blok', 'Koordinat <i>unfold</i> sumbu ketiga'], [
    ['bawah', 'di bawah permukaan terbawah model (mis. bedrock)', 'kedalaman di bawah permukaan itu'],
    ['atas', 'di atas kontak teratas, <b>masih di bawah topografi aktif</b>', 'tinggi di atas kontak teratas'],
    ['(luar)', 'di luar cakupan grid permukaan', 'tanpa kerangka unfold &rarr; 3D biasa (opsional, bawaan mati)']]))
B.append('<p>Sampelnya komposit dari interval yang <b>kodenya tidak dipetakan ke lapisan mana pun</b>, dan setiap '
         'komposit ditempatkan ke zona sesuai posisinya sendiri. Metodenya IDW anisotropis, bukan kriging: variogram '
         'sebuah lapisan berlaku <i>di dalam</i> lapisan itu, dan di luar seluruh lapisan tidak ada domain yang '
         'variogramnya pantas diwarisi. Hasil: <code>sl_pass = 9</code> dan kategori '
         '<code>sl_lapisan = WASTE (di luar lapisan)</code>.</p>')
B.append('<div class=warn>Blok di atas topografi adalah <b>udara, bukan waste</b>, jadi tidak pernah ikut. Dan '
         'setiap kali estimasi lapisan dijalankan ulang, estimasi waste laterit ikut terhapus &mdash; jalankan ulang '
         'sesudahnya.</div>')
B.append('<div class=box>Blok waste <b>tidak diberi kelas keyakinan</b>. Pada atribut <code>klasifikasi</code> ada '
         'kelas tersendiri <i>Waste (di luar solid)</i>, dan blok ini dikeluarkan dari kurva grade-tonase per kelas, '
         'karena waste bukan sumber daya. Tetapi volume &amp; tonasenya tetap dapat dilaporkan bersama ore di '
         'Reporting BM &mdash; itulah gunanya.</div>')

# ---- 9  sub-blocking & proporsi volume
B.append('<div class="page"></div><h2>9. Sub-blocking di batas solid &amp; proporsi volume</h2>')
B.append('<p class="lead">Blok dihitung utuh berdasarkan <b>titik pusatnya</b>: blok yang separuh di dalam vein dan '
         'separuh di luar tetap dihitung 100% ore atau 100% waste. Pada vein tipis, kesalahan batas itu sendiri '
         'sebesar dilusi yang mau diukur.</p>')
B.append(fig_html('frac', 'Jejak satu lensa pada sayatan dengan grid blok 5 m di atasnya. Dari %d sel yang '
                  'bersinggungan dengan solid, <b>%d hanya sebagian</b> di dalamnya dan <b>%d</b> seluruhnya &mdash; '
                  'angka pada tiap sel adalah <code>sb_frac</code>, proporsi volumenya yang di dalam solid.'
                  % (NOTE['fr_part'] + NOTE['fr_full'], NOTE['fr_part'], NOTE['fr_full'])))
B.append('<div class=box>Perhatikan: <b>tidak satu pun</b> blok 5 m yang seluruhnya di dalam vein. Dengan vein '
         'setipis ini, perhitungan berbasis titik pusat tidak punya peluang untuk benar &mdash; bukan kurang teliti, '
         'tetapi salah secara sistematis.</div>')
B.append('<h3>Dua tombol di menu Block Model</h3>')
B.append(D.tabel(['Tombol', 'Yang dilakukan'], [
    ['<b>&#9707; Pecah blok di batas solid</b>',
     'blok yang <b>menyeberangi</b> batas solid dipecah <b>2 &times; 2 &times; 2</b>, berulang 1&ndash;3 tingkat. '
     'Uji menyeberang memakai 27 titik (kisi 3 &times; 3 &times; 3), supaya vein tipis yang melintas tengah blok '
     'tanpa menyentuh sudut tetap terdeteksi.'],
    ['<b>&#9634; Hitung proporsi volume ore per blok</b>',
     'tanpa memecah blok: proporsi volume tiap blok yang di dalam solid, disimpan sebagai atribut '
     '<code>sb_frac</code> (0&ndash;1), dicuplik 10&sup3; = 1.000 titik per blok perbatasan.']]))
B.append('<p>Pemecahan 2 &times; 2 &times; 2 (bukan 2 &times; 2 &times; 1) disengaja: block model Surpac '
         '<code>.mdl</code> adalah <b>octree</b> yang membelah ketiga sumbu bersamaan, sehingga blok anak tetap jatuh '
         'tepat di kisi octree dan modelnya masih bisa ditulis balik ke <code>.mdl</code>. '
         '<b>Sub-blok yang sudah ada dihormati</b>: batas ukuran minimum dihitung dari ukuran blok <b>dominan</b> '
         'dibagi 2<sup>tingkat</sup> per sumbu, dan blok yang sudah lebih halus dibiarkan utuh &mdash; model Surpac '
         'yang memang sudah ber-sub-blok di sekitar wireframe tidak dipecah ulang.</p>')
B.append('<h3>Mana yang sebenarnya menyelesaikan masalah volume</h3>')
B.append('<p>Diukur pada vein mendatar tebal 4 m dengan blok 5 &times; 5 &times; 5 m, yang bench-nya berpusat '
         'tepat di luar vein sehingga <b>tidak satu pun titik pusat blok jatuh di dalam vein</b> '
         '(volume sebenarnya 400 m&sup3;):</p>')
B.append(D.tabel(['Tingkat pecah', 'Blok', 'Dihitung titik pusat', 'Ditimbang <code>sb_frac</code>'], [
    ['utuh', '80', '<b>0 m&sup3; (&minus;100%)</b>', '400,0 m&sup3; (0,00%)'],
    ['1', '136', '500 m&sup3; (+25%)', '400,0 m&sup3; (0,00%)'],
    ['2', '360', '500 m&sup3; (+25%)', '400,0 m&sup3; (0,00%)'],
    ['3', '1.256', '375 m&sup3; (&minus;6,3%)', '400,0 m&sup3; (0,00%)']]))
B.append('<p>Dan pada batas melengkung (bola radius 30 m, volume analitik 113.097 m&sup3;):</p>')
B.append(D.tabel(['Tingkat', 'Blok', 'Titik pusat', 'Ditimbang <code>sb_frac</code>', 'Waktu'], [
    ['utuh', '4.096', '114.000 m&sup3; (+0,80%)', '<b>113.120 m&sup3; (+0,02%)</b>', '77 ms'],
    ['1', '8.520', '112.625 m&sup3; (&minus;0,42%)', '113.103 m&sup3; (+0,01%)', '0,5 s'],
    ['2', '26.720', '113.000 m&sup3; (&minus;0,09%)', '113.096 m&sup3; (&minus;0,00%)', '2,7 s']]))
B.append('<div class=box>Kolom "titik pusat" membaik tetapi <b>berayun</b>: &minus;100% &rarr; +25% &rarr; &minus;6%. '
         'Pembulatan titik pusat tidak hilang hanya dengan memperkecil blok. Untuk <b>volume</b>, '
         '<code>sb_frac</code>-lah yang menyelesaikan masalah &mdash; bahkan <b>tanpa</b> memecah blok, galatnya '
         'sudah +0,02%.</div>')
B.append('<p>Jadi urutan kerjanya: kalau yang Anda perlukan hanya <b>volume &amp; tonase</b> yang benar, cukup '
         'jalankan tombol kedua, lalu pilih <code>sb_frac</code> pada <b>Timbang volume &amp; tonase dengan '
         'proporsi</b> di Reporting BM &mdash; lebih cepat dan tidak melipatgandakan jumlah blok. Sub-blocking tetap '
         'berguna untuk hal lain: resolusi <b>kadar</b> di dekat kontak (blok lebih kecil diestimasi dari komposit '
         'yang lebih relevan) dan geometri <b>dig block</b> yang mengikuti batas ore lebih rapat.</p>')
B.append('<div class=warn>Sub-blocking mengubah posisi blok, sehingga hasil estimasi lama tidak lagi cocok. '
         'Jalankan <b>sebelum</b> estimasi &mdash; panelnya memperingatkan bila sudah ada hasil. Urutan yang '
         'disarankan: impor / kerangka AOI &rarr; sub-blocking (bila perlu) &rarr; <code>sb_frac</code> &rarr; '
         'estimasi domain vein &rarr; estimasi waste.</div>')
B.append('<div class=box>Kadar <b>tidak</b> dikalikan proporsi: kadarnya memang kadar bagian yang di dalam solid, '
         'dan kadar rata-rata di laporan ditimbang tonase yang sudah berproporsi.</div>')

B.append('<div class="page"></div><h2>10. Database per kampanye, filter data bor &amp; export terfilter</h2>')
B.append('<p>Tiga tambahan di <b>GC-Ex Drill Hole Ultimate</b> yang semuanya dijalankan dari <b>Project Tree</b>, '
         'bukan dari panel &mdash; supaya panel kerja tidak perlu digulung naik-turun.</p>')
B.append('<h3>10.1 Database bor per kampanye</h3>')
B.append('<p>Node <b>Database Bor</b> dipecah per <b>kampanye pemboran</b> (eksplorasi, infill, grade control per '
         'periode). Baris <b>+ Tambah kampanye&hellip;</b> (paling bawah di node Database Bor); kampanye tujuan juga bisa dipilih di '
         'dialog import / upsert.</p>')
B.append(D.tabel(['Keadaan node', 'Peran', 'Akibat'], [
    ['<b>AKTIF</b>', 'set kerja', 'satu-satunya sumber pemodelan, estimasi, Geostatistik dan statistik'],
    ['dicentang, tidak aktif', 'referensi', 'tampil di 3D / Sayatan sebagai pembanding, tidak ikut analisis'],
    ['tidak dicentang', 'sembunyi', 'tidak tampil dan tidak ikut analisis']]))
B.append('<p>Bila data GC sudah dinilai bagus, <b>Buat set merge&hellip;</b> menggabungkan beberapa kampanye '
         'menjadi <b>database baru</b> (Collar / Survey / Assay / Geologi <b>Merge</b>) yang bisa dijadikan '
         'dataset aktif, dan diekspor ke <b>.xlsx 4 sheet</b> untuk pihak luar. Set merge bersifat hidup: '
         'hole baru di kampanye sumbernya otomatis ikut. Bentrok HoleID saat upsert diputuskan oleh '
         '<b>urutan prioritas</b> kampanye &mdash; data yang kalah ditolak dan dilaporkan.</p>')
B.append('<h3>10.2 Filter data bor (AND / OR)</h3>')
B.append('<p>Node <b>Filter data bor</b> menyaring data yang dipakai seluruh aplikasi, dinilai <b>per interval</b>. '
         'Atributnya dinamis mengikuti kolom yang ada: kadar unsur (termasuk operator <b>antara</b> untuk rentang), '
         'kategori assay, atribut geologi, kampanye, data collar, From / To / panjang, HoleID, dan <b>posisi</b> '
         'terhadap topografi, DTM, solid domain, wireframe atau poligon. Centang node = hidup/mati tanpa '
         'menghapus aturan; tiap aturan muncul sebagai anak node.</p>')
B.append(D.tabel(['Jalur', 'Cara interval dinilai'], [
    ['Statistik, komposit, Geostatistik, <b>estimasi</b>',
     '<b>utuh atau gugur</b> dari <b>titik tengah</b> interval &mdash; tidak dipotong. Interval yang tidak lolos '
     'tidak dipakai sebagai data masukan, jadi filter memang mempengaruhi hasil estimasi'],
    ['<b>Export</b> terfilter (.xlsx 4 sheet / CSV 4 berkas)',
     'interval yang memotong permukaan <b>dipotong tepat di permukaannya</b>: 10&ndash;20 m dengan permukaan di '
     '15 m keluar sebagai 15&ndash;20. Tanpa ini &ldquo;hanya di bawah topografi&rdquo; melebihkan panjang bor '
     'sebesar separuh interval di batasnya']]))
B.append('<div class=box>Bila hasil estimasi terasa kurang data, periksa dulu node <b>Filter data bor</b>: '
         'filter yang tertinggal menyala adalah penyebab yang paling sering terlewat. Aturan dan status '
         'hidup-matinya ikut tersimpan di berkas proyek.</div>')

B.append('<div class="page"></div><h2>11. Laporan beberapa desain pit &amp; progres topo-ke-topo</h2>')
B.append('<p>Reporting BM memakai topografi dan desain pit yang <b>sedang aktif</b> &mdash; satu-satu. '
         'Membandingkan fase pit berarti mengganti versi aktif lalu menghitung lagi, dan angkanya tidak pernah '
         'berdampingan. Tab baru <b>&#9315; Pit &amp; progres</b> di Reporting (ada di Drill Hole maupun Block '
         'Model, juga sebagai node Project Tree di bawah Reporting / Laporan) mengerjakan dua hal:</p>')
B.append(D.tabel(['Mode', 'Untuk apa'], [
    ['Per desain pit', 'centang beberapa desain pit sekaligus; semuanya dihitung dengan <b>topografi yang '
     'sama</b>. Satu baris per pit, plus baris <b>tambahan</b>: berapa tonase &amp; logam yang bertambah bila '
     'pit diperdalam ke fase berikutnya (untuk pit bersarang)'],
    ['Progres topo-ke-topo', 'untuk <b>ore reconcile</b>: material tergali antara dua survei = blok di bawah '
     'topografi lama dan di atas topografi baru, mis. akhir Juni &rarr; akhir Juli. Seluruh atribut kadar '
     'block model dapat dilaporkan sekaligus, dengan rincian per RL dan export CSV']]))
B.append('<p>Atribut, cut-off, pengelompokan, domain, poligon, SG dan <code>sb_frac</code> tetap diambil dari '
         'tab &#9312; dan &#9313;; yang diganti hanya permukaan atas &amp; bawah, sehingga angkanya sebanding '
         'dengan laporan biasa. Permukaan berasal dari versi topografi / desain pit di <b>Data Spasial</b> (Drill '
         'Hole) atau permukaan DTM di <b>Data Referensi (DTM, titik, string)</b> (Block Model); DTM segitiga dan DXF '
         '3DFACE dipakai persis seperti Surpac.</p>')
B.append('<p><b>Data latihannya baru:</b> <code>SIM_pit_fase1.dxf</code> dan <code>SIM_pit_fase2.dxf</code> '
         '(dua tahap desain pit, bersarang) serta <code>SIM_topo_akhir_juni.dxf</code> dan '
         '<code>SIM_topo_akhir_juli.dxf</code> (dua survei bulanan pit yang sama). Pada data itu: fase 1 '
         '3.384 blok / 549.900 t, fase 2 16.103 blok / 2.616.738 t, dan progres sebulan 2.439 blok / '
         '396.338 t.</p>')
B.append('<div class=warn>&#9888; Hasil progres adalah <b>block model di antara dua permukaan</b>, bukan '
         'timbangan. Rekonsiliasi tetap membandingkannya dengan tonase ROM / pabrik.</div>')
B.append('<h3>Tombol Demo disusun ulang</h3>')
B.append('<p><b>Demo sekarang bisa memuat data latihannya sendiri.</b> Berkas simulasi yang dipakai buku '
         'tutorial dititipkan di dalam installer, jadi ada dua tombol: <b>&#8681; Muat data latihan '
         'simulasi</b> di halaman import, dan <b>&#8681; Muat data latihan &amp; jalankan Demo</b> di menu '
         'Demo. Karena datanya sama dengan data tutorial, angka yang muncul di bilah bawah demo bisa '
         'dicocokkan langsung dengan PDF ini &mdash; mis. 524 interval hasil usulan flag, 98 string kontrol, '
         '657 komposit domain QV_Lensa2, dan 3.384 / 16.103 / 2.439 blok pada laporan per pit &amp; progres. '
         'Angka itu dibaca dari hasil perhitungan saat demo berjalan, bukan ditulis tangan di dalam '
         'program.</p>')
B.append('<p>Tur otomatis di bilah atas kini mengikuti urutan <b>buku tutorial</b>, bukan urutan menu: '
         'Drill Hole berjalan dari data &amp; filter &rarr; sayatan &rarr; Geomodeller Vein &rarr; '
         'Geostatistik &rarr; kerangka AOI (Block Model) &rarr; Model Estimation &amp; waste &rarr; autorun &rarr; laporan; '
         'Block Model dari block model &rarr; flitch &rarr; dig block &rarr; pemeriksaan &rarr; laporan &rarr; '
         'layout &rarr; as-mined &rarr; laporan periode. Keterangan tiap langkah dipendekkan menjadi satu '
         'kalimat, tempo bawaan dipercepat (0,55&times;, 20 fps) dengan pilihan Pelan / Sedang / Cepat / Kilat, '
         'dan langkah pertamanya menyebutkan <b>data yang sedang terbuka</b> &mdash; demo dimaksudkan '
         'dijalankan di atas data latihan simulasi <code>SIM_*</code>.</p>')

B.append('<div class="page"></div><h2>12. Wireframe terpusat, Project Tree sesuai alur kerja &amp; 3D lebih ringan</h2>')
B.append('<p><b>Satu node untuk wireframe geologi.</b> Wireframe / solid geologi (Leapfrog .msh / .obj, Surpac '
         '.dtm + .str, DXF) kini diimport dan dilihat hanya di node <b>Import Wireframe Geologi</b> (Drill Hole '
         'langkah 2b, Block Model langkah 4b). Setiap berkas menjadi anak node sesuai urutan import. Di Drill Hole, '
         'tombol &#8943; berkasnya untuk menjadikannya domain:</p>')
B.append(D.tabel(['Menu &#8943; berkas', 'Hasil'], [
    ['Serap jadi domain yang bisa diedit (Mode B)&hellip;', 'string HW/FW + solid RBF, ikut diperbarui saat ada bor baru'],
    ['Iris jadi string / flag interval bor (manual)&hellip;', 'membuka bagian iris &amp; flag di panel yang sama, langkah demi langkah per section'],
    ['Kunci domain &hellip; ke wireframe ini (Mode A)', 'batas EKSAK untuk audit; <i>Lepaskan</i> mengembalikan ke solid RBF'],
    ['Pindahkan ke Data Spasial sebagai versi topografi / desain pit&hellip;', 'untuk proyek lama yang menyimpan pit / topo di daftar wireframe; versi non-aktif, rujukan Reporting ikut dialihkan']]))
B.append('<p>Desain pit dan survei topografi bukan wireframe: di Drill Hole masuk <b>Data Spasial</b> sebagai versi '
         '(DXF 3DFACE disimpan sebagai DTM segitiga), di Block Model masuk <b>Data Referensi (DTM, titik, string)</b>. '
         'Tombol <i>Import DTM</i> di Reporting &rsaquo; Batas DTM dihapus; memilih DTM yang sudah diimport tetap bisa.</p>')
B.append('<p><b>Urutan Project Tree Drill Hole</b> kini mengikuti alur kerja nyata: 1 Proyek &middot; 2 Data Spasial '
         '&middot; 2b Import Wireframe Geologi &middot; 3 Database Bor &middot; 4 Peta &middot; 5 Struktur Geologi &middot; '
         '<b>5b Ore Geometry</b> &middot; 6 Geomodeller &middot; <b>7 Geostatistik</b> &middot; 8 Block Model &middot; 9 Model '
         'Estimation &middot; 10 Validasi BM &middot; 11 Reporting BM &middot; 12 Layout &amp; Ekspor. Export database hanya di '
         'menu Database Bor dan export .mdl hanya di menu Block Model; menu kembar kampanye / merge dihapus.</p>')
B.append('<p><b>3D lebih ringan.</b> Lapisan 3D yang tidak berubah (mis. block model) tidak lagi dikirim ulang ke kartu '
         'grafis setiap kali sayatan digeser atau centang diganti. Pada data latihan: gambar ulang 1.290 &rarr; 158 ms, '
         '3&times; klik Maju sayatan 3.690 &rarr; 494 ms. <b>Ore Geometry</b> tidak lagi menghitung otomatis saat dibuka '
         '&mdash; tekan <b>Hitung intercept &amp; GT</b>.</p>')
B.append('<p><b>Drillhole 0.24.65 (uji data nyata).</b> Model Estimation: bagian <b>Area pengaruh &amp; radius pencarian</b> per domain (elipsoid pass 1 dalam meter, <b>jarak pengaruh maks sampel</b> untuk semua lubang atau awalan Hole ID) untuk menyamakan tonase &amp; kadar dengan BMGC lama; atribut pembanding <b>au_id2</b> (ID&sup2;); export <b>.mdl Surpac</b> juga untuk Kerangka AOI. Geomodeller Vein: flag di atas topografi dicatat <i>sudah tertambang</i>, peringatan volume ekstrapolasi, tebal solid dibatasi 1,5 &times; tebal kontak terbesar, titik sambung cabang dibatasi, statistik selubung terisi, soft boundary zona transisi 2 m, tombol <b>Status alur pemodelan</b>. Geostatistik: tombol <b>Sayatan di bidang domain</b>; fitting memakai nugget downhole dan mayor &ge; semi-mayor. Impor: CSV bukan UTF-8 dibaca benar, validasi menyebut Hole ID; AOI punya <i>Origin grid</i>.</p>')
B.append('<p><b>Block Model 0.24.64 / Drillhole 0.24.63.</b> Pop-up juga untuk daftar dig block, hasil Reporting dan poligon per flitch Solid Vein; panel Geostatistik bisa dilepas. Solid Vein punya <b>Report block model dalam solid</b> (grade &times; tonase BM resmi per cut-off, pulau, flitch). Drillhole: jendela <b>Data per lubang</b> (collar, survey, assay, geologi) yang mengikuti Hole ID dan klik di 3D.</p>')
B.append('<p><b>Block Model 0.24.63.</b> Report As-Mined bisa <b>harian, mingguan, bulanan</b> atau <b>rentang tanggal</b> (diikat tanggal &amp; shift poligon, semua flitch); kunci otomatis hanya pada report harian. Register untuk database tampil sebagai jendela pop-up.</p>')
B.append('<p><b>Block Model 0.24.61.</b> Report As-Mined harian &amp; kunci tanggal-shift kini di panel <b>Register untuk database</b>: pilih tanggal &amp; shift, lalu salin / simpan CSV / kirim ke workbook &mdash; poligonnya <b>terkunci otomatis</b> begitu laporan itu keluar. Daftar poligon per flitch tampil sebagai jendela pop-up.</p>')
B.append('<p><b>Block Model 0.24.60 / Drillhole 0.24.62.</b> Topografi, desain pit dan lantai As-Mined kini dihitung dengan <b>triangulasi (TIN)</b> yang sama dengan tampilan 3D (estimasi, Reporting, potong saat import, kedalaman dari topografi). Tombol <b>&#10697; Pop-up</b> memindah <i>Register poligon</i>, <i>Layout &amp; export</i> As-Mined dan <i>Titik atap</i> Solid Vein ke jendela yang bisa digeser, diperkecil dan ditutup.</p>')
B.append('<p><b>Block Model 0.24.59.</b> Atap As-Mined dari pick-up dan Z atap poligon Solid Vein kini dihitung dengan <b>triangulasi (TIN)</b> seperti DTM Surpac: elevasi titik pick-up dipakai persis, linear di antaranya.</p>')
B.append('<p><b>Block Model 0.24.58.</b> As-Mined: <b>Report As-Mined per tanggal</b> (pilih tanggal &amp; shift; tonase &amp; kadar per poligon, subtotal shift, Salin ke Excel / CSV) dan <b>kunci tanggal-shift</b>: poligon hari yang sudah dilaporkan tidak dihitung ulang ketika flitch yang sama digali lagi. Poligon baru yang bertampalan dengan poligon terkunci diberi peringatan dan bisa dikurangi otomatis.</p>')
B.append('<p><b>Block Model 0.24.57.</b> Solid Vein Aktual punya <b>flitch kerja sendiri</b>: selesai import titik atap, plan flitch file itu langsung terbuka dan titiknya siap didigit; mencentang file / <b>Buka</b> / isian RL memindah flitch kerja tanpa mengubah flitch Dig Block / As-Mined.</p>')
B.append('<p><b>Block Model 0.24.56 / Drillhole 0.24.61.</b> Block model .mdl yang gagal dibuka dengan pesan <i>Tipe atribut "" belum didukung</i> kini terbaca. As-Mined: titik <b>atap</b> tampil di plan (&times; ungu) dan bisa di-snap, dan tombol <b>Titik lantai / Titik atap</b> mematikan salah satu lapisan saat mendigit; <b>Per flitch</b> membuka panel As-Mined flitch itu; <b>Register untuk database</b> menjadi node sendiri. '
         'Slicer Block Model disamakan dengan Drillhole (<b>Sayatan Garis Bebas</b>, <b>Tampilan 2D / 3D</b>, tanpa Pengaturan lanjutan). Laporan kinerja tidak lagi menghitung waktu kotak dialog.</p>')
B.append('<p><b>Slicer dirapikan (DH 0.24.60).</b> Di popup Slicer: <b>Sayatan Garis Bebas</b> (dulu <i>Garis di peta&hellip;</i>) membuka kotak sayatan garis bebas; <b>Tampilan 2D</b> / <b>Tampilan 3D</b> hanya mengganti cara melihat. '
         'Pengaturan sayatan terpusat di popup ini; panel Sayatan di Properti dan centang Label hole / Collar / Trajectory / No-data di Tampilan &amp; performa dibuang (pakai panel Layer). Galat <i>k.pick</i> saat kursor di atas model tidak muncul lagi.</p>')
B.append('<p><b>Topografi &amp; pit sesudah database bor dihapus (DH 0.24.59).</b> Menghapus seluruh database bor dulu membuat topografi dan desain pit tidak bisa ditampilkan; kini keduanya tetap tampil, dan proyek yang sudah terlanjur kosong pulih saat dibuka.</p>')
B.append('<p><b>Tombol Muat data latihan simulasi (BM 0.24.55 / DH 0.24.58).</b> Di aplikasi terpasang tombol ini gagal dengan pesan <i>HTTP 404</i>; sudah diperbaiki di kedua aplikasi.</p>')
B.append('<p><b>As-Mined sesudah diuji data nyata (BM 0.24.54).</b> <i>Import boundary</i> kini menerima <b>CSV pick-up OB</b>: RL flitch, tanggal dan pit dibaca dari nama file, dan titiknya langsung jadi titik atap. '
         '<b>Kelas kadar</b> As-Mined mengikuti aturan block model; <b>SG</b> memakai kolom SG model bila ada (tonase proyek baru bisa berubah karenanya). '
         '<b>3D hasil kerja</b> menampilkan solid as-mined di antara atap dan lantai pick-up, dengan <b>zoom ke poligon</b>. '
         'Di Solid Vein, poligon yang <b>bertampalan</b> di satu flitch digabung otomatis jadi satu tubuh (atap = permukaan tertinggi).</p>')
B.append('<p><b>Solid Vein Aktual berdiri sendiri (BM 0.24.53).</b> Menu ini tidak lagi mengambil data dari Dig Block maupun As-Mined: titik atap disimpan sendiri (import ulang titik atap yang dimasukkan di versi sebelumnya). '
         'Baru: <b>edit titik poligon</b> (tombol &#9998;), import ulang file bernama sama <b>mengganti</b> titiknya, tanda solid belum diperbarui, opsi <b>Kumulatif</b> lintas periode, dan peringatan <b>poligon bertampalan</b> di flitch yang sama beserta perkiraan volume gandanya.</p>')
B.append('<p><b>Solid Vein Aktual sesudah diuji pick-up nyata (BM 0.24.52).</b> Tabel titik atap kini per <b>file</b>, dengan <b>RL flitch dibaca dari nama file</b> '
         '(bisa dikoreksi) &mdash; titik tidak lagi dipilah dari elevasinya. Tombol baru <b>Garis luar otomatis</b> mengusulkan poligon dari gugus titik tiap file. Jarak sambung bawaan 3 m.</p>')
B.append('<p><b>Solid Vein Aktual &mdash; trial (BM 0.24.51).</b> Node baru paling bawah di Project Tree Block Model. Per <b>Periode</b>: import titik pick-up <b>atap</b> galian (saring RL), '
         'digit poligon tiap flitch (snap ke titik atap) atau ambil dari register as-mined / dig block, lalu <b>Bangun solid</b>. Poligon flitch berurutan disambung cara Surpac '
         '(semua titik dipakai; luas permukaan minimum / equi-angular / proporsional) bila jaraknya &le; <b>jarak sambung maks</b>; lebih jauh menjadi pulau tertutup sendiri, flitch kosong memutus solid, cabang dibelah otomatis. '
         'Tombol <b>Lihat di 3D (zoom ke vein)</b> mendekatkan kamera ke garis poligon dan tubuh solidnya. Hasil: volume &amp; tonase per pulau, tanda tertutup, ekspor DTM + STR Surpac / DXF / CSV; solid bisa dipakai sebagai batas domain Reporting.</p>')
B.append('<p><b>Permukaan &amp; ortho tajam, penyamaan kedua aplikasi (BM 0.24.50 / DH 0.24.57).</b> Permukaan topografi dan desain pit kini dibangun dari '
         '<b>seluruh titik survei</b> (bukan 15 ribu titik contoh), orthofoto digambar setajam anggaran profil Kinerja dan makin halus saat zoom masuk (Resolusi = Otomatis). '
         'Block Model mendapat tombol <b>Slicer</b> yang sama dengan Drill Hole; Drill Hole mendapat tampilan block model besar utuh (LOD) dan perbaikan acuan koordinat yang sama dengan Block Model.</p>')
B.append('<p><b>Slicer, panel Assay, permukaan topo / pit (DH 0.24.56 / BM 0.24.49).</b> Bilah atas Drill Hole kini punya satu tombol <b>Slicer</b>: '
         'dip, dip azimuth, lebar slab, langkah, pusat bidang (E, N, RL), Mundur / Maju, opsi slab, Sayatan 2D &mdash; memotong model dari arah mana saja tanpa menggambar garis. '
         'Node <b>Assay</b> membuka panel tampilan kadar (unsur, cutoff, deret warna diskrit / gradasi); sub-node unsur hanya daftar. '
         'Permukaan <b>topografi &amp; desain pit</b> akhirnya tampil di 3D Drill Hole (sebelumnya selalu dibuang oleh pengaman gambar) dengan warna seragam (bawaan) atau gradasi elevasi, di kedua aplikasi. '
         'Tombol bernomor lingkaran dihapus; garis plan bor utuh; STR biner Surpac berdeskripsi teks (berkas pit) kini terbaca benar.</p>')
B.append('<p><b>Jeda saat berganti panel / atribut (BM 0.24.47 / DH 0.24.54).</b> Berpindah panel sendiri murah; yang terasa adalah '
         'ganti atribut warna, centang overlay, dan ubah ukuran jendela. Kini: kembali ke atribut yang pernah tampil seketika (geometri / segmen '
         'disimpan untuk beberapa atribut terakhir), centang overlay tidak lagi mengunggah ulang semua lapisan 3D (rentang sumbu dibuat tetap selama '
         'filter hole / bench / sayatan sama &mdash; kotak 3D juga tidak melompat), ubah ukuran jendela digambar ulang sekali. Kotak baru '
         '<b>Kinerja &amp; grafis</b> di <b>Tampilan &amp; performa</b> memberi tahu apakah kartu grafis dipakai &mdash; bila tertulis <i>render '
         'perangkat lunak</i>, itulah penyebab lambatnya dan kotak memberi langkah di Windows &mdash; serta mencatat jeda 12 aksi terakhir; '
         '<b>Salin laporan kinerja</b> untuk dikirim saat melapor.</p>')
B.append('<p><b>As-Mined (Block Model).</b> Panel Lantai melaporkan titik lantai di pita elevasi dan yang tidak dipakai, '
         'menyebut poligon yang jatuh ke RL bawah nominal (&lt; 3 titik), dan memperingatkan luas yang atapnya menembus lantai. '
         'Tombol import titik atap kini sama dengan tombol titik lantai. Beberapa menu diganti namanya sesuai isinya, '
         'mis. <i>Buka daftar poligon as-mined flitch ini</i> (hanya membuka daftar; dig block tidak diubah menjadi as-mined).</p>')

B.append('<div class="page"></div><h2>13. Isi dokumen ini di tutorial bergambar</h2>')
B.append('<p>Semua bab di dokumen ini kini juga ada di dua tutorial bergambar, lengkap dengan <b>tangkapan layar '
         'aplikasi</b> dan angka dari satu kali jalannya latihan. Dokumen ini tetap diterbitkan sebagai ringkasan '
         '&ldquo;apa yang baru&rdquo;; untuk belajar langkah demi langkah, pakai tutorial bergambarnya.</p>')
B.append(D.tabel(['Bab di dokumen ini', 'Di tutorial bergambar'], [
    ['1. Data latihan simulasi baru', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Data simulasi</b>'],
    ['2. Latihan terpandu', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Latihan terpandu</b>'],
    ['3&ndash;4. Klasifikasi keyakinan &amp; kerapatan bor', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Klasifikasi keyakinan &amp; kerapatan bor</b>'],
    ['5. Topografi &amp; orthofoto resolusi tinggi', 'kedua tutorial: bab <b>Topografi &amp; orthofoto resolusi tinggi</b>'],
    ['6. GC-Ex Block Model: yang baru', '<i>Tutorial Block Model</i>: bab <b>Yang baru di 0.24</b>'],
    ['7. Kerangka AOI', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Block model dari nol: kerangka AOI</b>'],
    ['8. Estimasi waste', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Estimasi waste</b> (jalur vein) dan bab <b>Geomodeller Stratified-Laterite</b> (jalur laterit)'],
    ['9. Sub-blocking &amp; proporsi volume', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Sub-blocking &amp; proporsi volume</b>'],
    ['10. Kampanye, filter &amp; export terfilter', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Database bor per kampanye</b> dan bab <b>Filter data bor</b> (Bagian I)'],
    ['11. Pit &amp; progres topo-ke-topo', 'kedua tutorial: bab <b>Laporan per desain pit &amp; progres topo-ke-topo</b>'],
    ['12. Wireframe terpusat &amp; Project Tree', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Memakai wireframe dari Leapfrog</b> dan <b>Wireframe Leapfrog menjadi domain</b>; <i>Tutorial Block Model</i>: bab <b>As-mined</b>'],
    ['14. Vein system', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Membangun solid vein (RBF)</b>, bagian <b>Vein system: banyak vein sekaligus</b>'],
    ['15. Jalur proyek', '<i>Tutorial Modelling &amp; Estimasi</i>: bab <b>Membuat folder proyek &amp; import data</b> dan bab <b>Jalur proyek: mulai dari nol atau lanjutkan</b>']]))
B.append('<p>Nama domain dan angka di kedua tutorial bergambar sudah mengikuti data latihan yang sekarang '
         '(<code>QV_Lensa2</code>, <code>QV_Splay_HW</code>, bor dan assay sesuai berkas yang Anda terima).</p>')

B.append('<div class="page"></div><h2>14. Vein system: banyak vein sekaligus, opsi per vein, solid usang, resolusi adaptif</h2>')
B.append('<p><b>Drill Hole 0.24.71.</b> Diadopsi dari review mesh <i>Vein System</i> Leapfrog Zona 2. Algoritma solid RBF tidak '
         'berubah: dengan pengaturan bawaan solid yang terbangun identik dengan versi sebelumnya. Yang baru ada di Geomodeller Vein:</p>')
B.append(D.tabel(['Di mana', 'Apa', 'Untuk apa'], [
    ['Tab <i>Flag</i> &rsaquo; <b>Flag dari kolom kode</b>', 'satu kolom kode interval (mis. <i>Orebody</i>, <i>Vein</i>) &rarr; satu domain per kode; beberapa kode boleh ke satu domain; kode kosong / &ldquo;-&rdquo; dilewati', 'interpretasi vein yang sudah ada di database langsung jadi domain, tanpa flag manual per section'],
    ['Tab <i>Solid</i> &rsaquo; <b>Opsi semua vein (tabel) &amp; prioritas</b>', 'snap / kehalusan, pinch-out bor kosong, pinch-out dip, tebal minimum, radius strike, ujung atas, resolusi, adaptif &mdash; semua domain sekaligus; &#9650;&#9660; prioritas', 'mengatur puluhan vein tanpa membuka satu per satu; prioritas menentukan domain pemilik blok bila solid bertumpang'],
    ['Tab <i>Solid</i> &rsaquo; kotak <b>Vein system</b>', 'volume gabungan (tumpang tindih dihitung sekali), ekspor semua solid dalam SATU berkas OBJ / DXF / STR+DTM', 'setara &ldquo;Merge Vein&rdquo; Leapfrog untuk pertukaran data'],
    ['Panel Solid &amp; Project Tree', '<b>solid usang</b> beserta sebabnya bila <i>Jalankan ulang otomatis</i> mati; <b>Bangun ulang solid usang</b>', 'tidak ada solid yang diam-diam tertinggal dari data bor baru'],
    ['Parameter domain &rsaquo; RBF &amp; mesh', '<b>Resolusi adaptif</b>: simpul rapat di dekat data, menjarang sampai <i>Jarang maks.</i> &times; resolusi', 'mesh lebih ringan untuk vein panjang dengan data jarang']]))
B.append(fig_html('vsys', 'Kiri: kolom geologi <b>Vein</b> data latihan &rarr; %d domain (jumlah interval dalam kurung). '
                  'Kanan: simpul mesh searah strike QV_Lensa2, seragam 2 m (%d simpul) vs adaptif &times;4 (%d simpul); '
                  'rapat di dekat kontak bor, jarang di ujung perpanjangan.' % (len(NOTE['vs_kode']), NOTE['vs_simpul'][0], NOTE['vs_simpul'][1])))
B.append('<p><b>Latihan.</b> Muat data latihan, buka Geomodeller Vein &rsaquo; tab <i>Flag</i> &rsaquo; <b>Flag dari kolom kode</b>, '
         'pilih kolom <b>Vein (geologi)</b>, lalu <b>Terapkan</b>: domain QV_Lensa1&ndash;4 dan QV_Splay_HW dibuat beserta solidnya. '
         'Di tab <i>Solid</i> tekan <b>Hitung volume gabungan</b>: lensa en-echelon yang saling tumpang menghasilkan volume gabungan '
         'sedikit lebih kecil daripada jumlah volumenya. Lubang L1 juga menembus Lensa2 (dan seterusnya), seperti vein array sungguhan.</p>')

B.append('<div class="page"></div><h2>15. Jalur proyek: mulai dari nol atau lanjutkan dari Surpac / Leapfrog</h2>')
B.append('<p><b>Drill Hole 0.24.73.</b> GC-Ex Drill Hole punya dua kelompok fitur yang tujuannya berlawanan. Yang satu <b>membuat</b> model '
         'dari data bor (domain, solid, kerangka blok, parameter). Yang lain <b>mempertahankan</b> model dari software lain supaya pembaruan '
         'di GC-Ex tidak mengubahnya (Serap / Eksak wireframe, versi block model acuan, parameter dari log). Sekarang keduanya dipisah dengan '
         '<b>jalur proyek</b> yang dipilih di halaman pembuka.</p>')
B.append(fig_html('jalur', 'Empat tahap pekerjaan dan pintunya di tiap jalur. Algoritmanya sama di kedua jalur; yang berbeda hanya '
                  'pintu yang terbuka.'))
B.append('<p><b>Aturan penentu.</b> Jalur ditentukan oleh ada-tidaknya <b>objek model dari software lain</b> yang dipakai: wireframe / domain, '
         'block model <code>.mdl</code> / CSV, atau parameter estimasi. Data mentah (collar, survey, assay, geologi, topografi) tidak dihitung. '
         'Contoh: Anda diberi wireframe domain Leapfrog lalu diminta mengestimasi block model dari awal &rarr; <b>Lanjutkan</b> dengan acuan '
         '<i>Wireframe</i> saja; kerangka blok dan parameter tetap dibuat baru di GC-Ex. Block model <code>.mdl</code> yang hanya dipakai sebagai '
         'pembanding juga termasuk Lanjutkan.</p>')
B.append(D.tabel(['Di mana', 'Mulai dari nol', 'Lanjutkan dari Surpac / Leapfrog'], [
    ['Halaman Import', 'slot <i>Block model</i> tidak tampil', 'slot <i>Block model</i> tampil bila acuan block model dicentang'],
    ['Project Tree', 'tanpa node <i>Import Wireframe Geologi</i>; menu &#8943; Block Model tanpa <i>Import block model dari file</i>', 'semua node; objek acuan bertanda <b>&middot; acuan</b>, domain dari wireframe <b>acuan eksak</b> / <b>diserap</b>'],
    ['Panel &amp; pintasan', '&ldquo;Import BM&hellip;&rdquo; (pesan panduan, skrip lama) membuka <b>Buat kerangka blok (AOI)</b>', 'tidak berubah'],
    ['Autorun Wireframe', 'membangun semua domain', 'domain <b>acuan eksak</b> dilewati (bentuknya milik wireframe asal)'],
    ['Simpan parameter ke domain', 'langsung', 'bila domain sudah berparameter dan acuan parameter dicentang: konfirmasi, lalu tercatat di jejak'],
    ['Autorun Estimasi dari Nol, auto-fit, KNA', 'sama', 'sama &mdash; hanya domain tanpa parameter yang diisi; tidak ada yang ditimpa']]))
B.append('<p><b>Pindah jalur.</b> Node <i>Proyek &rsaquo; Jalur</i> &rsaquo; <b>Jadikan jalur Lanjutan&hellip;</b>: satu arah (dari nol ke Lanjutan), '
         'proyek disimpan dulu ke folder, dan perpindahan tercatat di jejak (siapa, kapan). Kembali ke nol hanya mungkin selama belum ada objek acuan di proyek.</p>')
B.append('<p><b>Proyek lama.</b> Proyek dari versi sebelum 0.24.73 dibuka tanpa jalur. GC-Ex menebak dari isinya (wireframe / block model dari file '
         '&rarr; Lanjutkan, selain itu &rarr; Mulai dari nol) dan menandai node Jalur <b>perlu konfirmasi</b>. Sebelum dikonfirmasi tidak ada '
         'menu yang disembunyikan, sehingga proyek lama tetap bisa dikerjakan seperti biasa.</p>')
B.append('<p><b>Data latihan untuk kedua jalur (DH 0.24.76).</b> Halaman import punya dua tombol: <b>&#8681; Data latihan &mdash; Lanjutkan</b> '
         '(bor, topografi, block model GC dan wireframe Leapfrog &mdash; angka sama dengan buku tutorial) dan <b>&#8681; Data latihan &mdash; Mulai dari nol</b> '
         '(data simulasi yang sama tanpa block model GC dan wireframe Leapfrog). Jalur proyek mengikuti tombol yang ditekan, bukan kartu jalur, supaya isi '
         'dan jalur tidak bertentangan. Tombol Demo tetap memakai jalur Lanjutkan.</p>')

B.append('<h3>15a. Autorun Estimasi dari Nol: sayatan di bidang tiap domain (Drill Hole 0.24.75)</h3>')
B.append('<p>Variogram di Geostatistik dihitung dari komposit di dalam <b>sayatan aktif</b>. Autorun Estimasi dari Nol dulu memakai sayatan apa pun '
         'yang sedang terpasang. Pada simulasi jalur Mulai dari nol dengan data nyata, sayatan horizontal bawaan hanya memuat 13 dari 489 komposit '
         'sebuah vein, sehingga domain itu dilewati. Sekarang autorun memasang <b>sayatan di bidang domain</b> untuk tiap domain (sama dengan tombol '
         '<i>Sayatan di bidang domain</i> di Geostatistik): strike &amp; dip dari kontak bor, tebal = sebaran kontak, sehingga semua komposit domain ikut. '
         'Laporan autorun menyebut sayatan yang dipakai; sayatan Anda dikembalikan sesudah autorun selesai. Pilihan '
         '<b>Variogram dari sayatan di bidang tiap domain</b> (bawaan nyala) di dialog Autorun Estimasi dari Nol; dimatikan = perilaku lama. '
         'Kerangka AOI yang dibuat autorun juga tidak lagi memunculkan jendela &ldquo;langkah berikutnya&rdquo; di tengah proses.</p>')

B.append('<h3>15b. Parameter estimasi dari log Surpac (Drill Hole 0.24.79)</h3>')
B.append('<p>Di jalur Lanjutkan dengan acuan <i>Parameter estimasi</i>, Model Estimation &rsaquo; &#8943; &rsaquo; <b>Isi parameter dari log Surpac&hellip;</b> membaca log Surpac '
         'pendahulu: semua run <i>BM FILL</i> (variogram, orientasi ZXY LRL, elipsoid pencarian, sampel minimum&ndash;maksimum, komposit &rarr; unsur, constrain sumber sampel) '
         'dan menyalin run pilihan ke domain. Orientasi Surpac diterjemahkan ke sumbu GC-Ex; <code>constrain = N</code> = soft boundary.</p>')
B.append('<p><b>Memilih run.</b> Satu log berisi banyak run (percobaan, re-run sebagian area, unsur lain). Yang benar adalah run yang menghasilkan nilai di block model '
         'yang diserahkan. Tombol <b>Uji kecocokan dengan block model acuan</b> mengestimasi domain dengan tiap set parameter berbeda dan membandingkannya dengan kolom kadar '
         'block model Surpac aktif. Perbandingan dilakukan pada blok yang diisi semua kandidat, karena elipsoid kecil hanya mengisi blok dekat bor dan korelasinya tampak tinggi. '
         'Run paling cocok ditandai &#9733;. Run uji tidak masuk riwayat Model Estimation.</p>')
B.append('<p><b>Tanpa log.</b> Surpac tidak menyimpan parameter di .mdl. Buat parameter dari data bor dengan Autorun Estimasi dari Nol, lalu bandingkan dengan block model '
         'pendahulu pada blok yang sama. Tombol log Surpac tidak tampil di jalur Mulai dari nol.</p>')

B.append('<div class="page"></div><h2>16. Reporting BM: cara Surpac sebagai bawaan</h2>')
B.append('<p>Angka GC-Ex diaudit terhadap report Surpac, jadi setiap pilihan yang punya padanan Surpac memakai <b>cara Surpac sebagai bawaan</b>. Cara GC-Ex tetap ada sebagai pilihan.</p>')
B.append('<p><b>Hanya di bawah topografi.</b> Blok di luar jangkauan topografi, desain pit atau batas DTM <b>tidak dilaporkan</b> (seperti Surpac). Sebelum Block Model 0.24.68 / '
         'Drill Hole 0.24.81, block model yang lebih luas dari pick-up topografi ikut terlapor sebagai sisa di luar jangkauan itu.</p>')
B.append('<p><b>Blok di batas permukaan</b> (tab Constraint): <i>Cara Surpac &mdash; titik pusat blok</i> (bawaan) atau <i>Cara GC-Ex &mdash; proporsi volume blok</i>. Cara GC-Ex '
         'membagi telapak blok menjadi 4&times;4 kolom (bisa 2&ndash;8) dan menimbang tonase dengan bagian kolom yang di bawah topografi, di atas pit dan di sisi DTM yang dipilih. '
         'Tab <b>Metode tonase</b> menampilkan kedua cara berdampingan. Di Block Model, pembobotan <code>sb_frac</code> juga kini mati secara bawaan.</p>')

B.append('<h3>16a. Topografi &amp; desain pit ber-hillshade (Block Model 0.24.69 / Drill Hole 0.24.82)</h3>')
B.append('<p>Permukaan topografi, desain pit dan DTM Data Referensi digambar dengan <b>hillshade</b>: setiap segitiga digelapkan menurut arah cahaya matahari dari barat laut '
         '(azimut 315&deg;, elevasi 45&deg;). Lereng, jenjang pit dan punggungan terlihat jelas dari sudut kamera mana pun. Pilihan di panel <b>Overlay</b> &rsaquo; '
         '<b>Bayangan (shading) topo &amp; pit</b>: Hillshade jelas (bawaan), Hillshade lembut, atau Lampu 3D Plotly (cara lama). Hanya tampilan; tonase Reporting tidak berubah.</p>')

B.append('<h3>16b. Dig block, As-Mined dan SG kosong: cara Surpac sebagai bawaan (Block Model 0.24.70)</h3>')
B.append('<p><b>Metode tonase Dig block &amp; As-Mined</b> bawaannya kini <i>Seperti Surpac</i>: blok dihitung utuh bila titik tengahnya di dalam string / boundary '
         'dan RL flitch. <i>Presisi GC-Ex</i> (blok dipotong tepat di garis, ditimbang tebalnya di flitch) tetap bisa dipilih untuk dig plan.</p>')
B.append('<p><b>SG kosong.</b> Surpac mengalikan volume blok dengan nilai SG yang <i>tersimpan</i> di blok; blok yang tidak pernah diisi menyimpan <b>nilai bawaan atribut</b> '
         '(pada model GC lapangan, <code>sg3</code> berbawaan 0, jadi tonasenya 0 sementara volumenya tetap tercatat). Itulah bawaan GC-Ex sekarang. SG = 1 tidak dipakai: '
         'itu berat jenis air dan akan menurunkan tonase ±60% tanpa terlihat. Pilihan lain: <i>Anggap 0</i> dan <i>SG pengganti</i> (cara GC-Ex).</p>')

B.append('<h3>16c. Vein bercabang menyatu: boolean union induk + cabang (Drill Hole 0.24.84)</h3>')
B.append('<p>Solid domain induk dan semua cabangnya kini digabung dengan <b>boolean union</b> menjadi <b>satu solid tertutup</b>, seperti vein system Leapfrog atau <i>Solid &rsaquo; Boolean &rsaquo; Union</i> di Surpac. '
         'Garis luar induk dan cabang menyatu di titik percabangan (bentuk Y) di 3D dan sayatan; ekspor per domain dan ekspor Vein System berisi satu solid per induk; volume gabungan dihitung eksak dari solid hasil union. '
         'Pilihan <i>Satukan induk + cabang (boolean union)</i> ada di kotak <b>Solid gabungan per domain induk</b> (tab Solid), bawaan menyala. Pustaka boolean (manifold-3d) tertanam di aplikasi &mdash; tetap offline. Estimasi tidak berubah.</p>')
B.append(fig_html('vunion', 'Data latihan SIM_split, sayatan tegak: QVS_Utama + QVS_Cabang sesudah boolean union &mdash; satu solid bergaris luar Y (tangkapan layar uji <code>uji_vein_union_dh.py</code>).'))

B.append('<h3>16d. Solid Vein Aktual: satukan pulau &amp; rekonsiliasi dengan wireframe model (Block Model 0.24.71)</h3>')
B.append('<p>Potongan Solid Vein yang saling menembus kini disatukan dengan <b>boolean union</b> (pilihan <i>Satukan pulau yang bertampalan</i>, bawaan menyala) &mdash; volume ganda hilang, ekspor satu solid valid. '
         'Bagian baru <b>Rekonsiliasi dengan wireframe model</b> membandingkan solid aktual dengan wireframe model ore: <b>ore tergali</b> (aktual &cap; model), <b>dilusi</b> (aktual &minus; model) dan <b>ore loss</b> '
         '(model di zona penilaian &minus; aktual; zona = poligon aktual tiap flitch diperlebar, bawaan 3 m). Volume dari solid hasil boolean (eksak), tonase &times; SG Solid Vein dan tonase / kadar block model (blok utuh). '
         'Pustaka boolean yang sama dengan vein bercabang Drill Hole, kini dipakai bersama (<code>web-src/manifold.js</code> + <code>web-src/mfbool.js</code>).</p>')
B.append(fig_html('svrek', 'Data uji sintetis: Solid Vein aktual (dua poligon bertampalan, tersatukan) dibandingkan model kotak &mdash; hijau ore tergali, biru dilusi, merah ore loss (lebar zona 3 m), abu-abu model di luar zona.'))

B.append('<h3>16e. Topografi terpotong desain pit, batas permukaan blok, buka atap &amp; legenda (Block Model 0.24.73)</h3>')
B.append('<p><b>Topo &times; Pit (gabungan)</b> (Project Tree &rsaquo; Data Referensi &rsaquo; + Tambah &rsaquo; <i>Gabungkan topografi &times; desain pit</i>): satu permukaan yang di setiap titik memakai yang lebih rendah antara topografi dan desain pit. '
         'Segitiga kedua TIN ditumpang-susun dengan tepat (tanpa triangulasi ulang), sehingga jenjang pit dan lekuk topografi tidak terpotong; sumber bisa Data Spasial (bawaan, sama dengan Reporting) atau permukaan DTM Data Referensi. '
         'Diwarnai dua nada (hijau topo, biru pit) dengan hillshade, tersimpan di proyek, ada di daftar permukaan Reporting dan bisa diekspor DTM + STR. '
         'Menu Block Model mendapat satu pilihan <b>Batas permukaan</b> (<i>Di antara topo &amp; pit</i> / <i>Di bawah topo &times; pit</i>) yang bekerja bersama cut-off &amp; kelas yang sudah ada &mdash; tidak ada filter kadar baru. '
         'Panel Overlay: <b>Opasitas desain pit</b> sendiri dan <b>Buka atap</b> (permukaan di atas blok tampil disembunyikan, lantai pit tetap). Legenda berbentuk kartu di pojok kanan bawah grafik.</p>')
B.append(fig_html('topopit', 'Data latihan: topografi Data Spasial &times; SIM_pit_fase1 menjadi satu permukaan (hijau topo, biru pit); blok AU_GC &ge; 0,34 di antara topo &amp; pit tampil di dalam pit, legenda di pojok kanan bawah.'))

B.append('<h3>16f. Permukaan topo &amp; pit seperti Pit Studio, tampilan baru Project Tree &amp; Properti (Block Model 0.24.74, Drill Hole 0.24.86)</h3>')
B.append('<p>Mengacu Pit Studio: titik string desain pit <b>dirapatkan tiap 2 m</b> sebelum ditriangulasi sehingga bidang jenjang tidak diseberangi segitiga panjang; segitiga panjang hanya dikupas dari <b>tepi luar</b> TIN sehingga topografi tidak berlubang di bagian dalam; '
         'permukaan Topo &times; Pit mendapat <b>garis kontur topografi</b> dan <b>garis jenjang pit</b> yang dipotong di bagian tergali. Hanya tampilan &mdash; angka Reporting tetap. '
         'Block Model mendapat tema baru untuk <b>Project Tree</b> dan panel <b>Properti</b>: baris pohon bersudut dengan sorotan biru muda, setiap bagian panel menjadi kartu, tab bagian berupa segmented control, tombol dan isian 32 px; bar atas tetap navy.</p>')
B.append(fig_html('skin_bm', 'Data latihan: Project Tree dan panel Properti Block Model dengan tema baru (0.24.74).'))

import json as _json
_json.dump(dict({k: (v.item() if hasattr(v, 'item') else v) for k, v in NOTE.items()}, PITCH=float(PITCH), DIP=float(DIP), DIPAZ=float(DIPAZ),
               STRIKE=float(STRIKE), FA_OFF=float(FA_OFF), WT_RL=float(WT_RL), F=F),
           open(os.path.join(FIGD, 'notes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
_ISI = [re.sub('<[^>]+>', '', q) for x in B for q in re.findall(r'<h2>(.*?)</h2>', x)]
assert len(_ISI) >= 10, 'daftar isi kosong?'
B.insert(0, D.cover(
    'GRADE CONTROL EXCELLENCE · KELUARGA GC-EX',
    'Tutorial Update GC-', 'Ex',
    'Apa yang baru di GC-Ex Drill Hole Ultimate dan GC-Ex Block Model, dan bagaimana memakainya: '
    'data latihan simulasi baru, klasifikasi keyakinan sumber daya, kerapatan bor per blok, '
    'topografi &amp; orthofoto resolusi tinggi, block model dari nol (kerangka AOI), estimasi '
    '<b>waste</b> untuk jalur vein maupun laterit, serta sub-blocking dan proporsi volume di batas '
    'solid, vein system, dan <b>jalur proyek</b> (mulai dari nol / lanjutkan dari Surpac-Leapfrog). Pendamping <i>Petunjuk Teknis GC-Ex</i>.',
    _ISI,
    'GC-Ex Block Model %s &middot; GC-Ex Drill Hole Ultimate %s &middot; disusun otomatis %s.<br>'
    'Semua gambar di dokumen ini <b>dihitung langsung dari model dan berkas data latihan</b>, bukan '
    'tangkapan layar, sehingga angkanya selalu cocok dengan data yang Anda terima.<br>'
    'Copyright &copy; Habil Abdillah 2026. Seluruh hak dilindungi.' % (VBM, VDH, D.tanggal())))

sz = D.render(B, PDF, 'Tutorial Update GC-Ex %s / %s' % (VBM, VDH))
print('OK', PDF, sz, 'byte')
print('angka:', NOTE)
