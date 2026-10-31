"""Data simulasi tutorial GC-Ex Drill Hole Ultimate & Block Model — SEPENUHNYA SINTETIS.

TIDAK memuat nama perusahaan, Hole ID, koordinat, atau angka proyek nyata. Semua dihitung dari model
matematika di bawah ini, jadi jawaban "yang benar" selalu diketahui dan bisa dipakai memeriksa hasil
pemodelan, estimasi, geostatistik dan reporting di GC-Ex.

MODEL GEOLOGI (endapan emas epitermal low-sulphidation, terkontrol sesar geser)
------------------------------------------------------------------------------
1. Zona geser utama: strike 045 deg, dip 70 deg ke tenggara (azimuth dip 135).
2. Vein ARRAY EN-ECHELON: 4 lensa kuarsa sigmoidal yang saling bertumpang (right-stepping, khas
   pergerakan geser dekstral). Tiap lensa meruncing (taper) di keempat ujungnya, tidak terputus tegak.
3. DILATANT JOG: tebal vein membesar di tempat bidang vein melengkung ke arah yang membuka
   (tebal dihitung dari kelengkungan permukaan tengah vein) — inilah tempat breksi & kadar tinggi.
4. ORE SHOOT ber-PITCH KONSISTEN 55 deg diukur dari garis strike di dalam bidang vein, sama untuk
   semua lensa (satu kontrol struktur). Ini angka yang seharusnya ditemukan kembali oleh menu
   Ore Geometry / analisis pitch.
5. ZONASI VERTIKAL epitermal terhadap paleo-muka air tanah (boiling zone):
     - di zona didih (+-25 m): tekstur colloform-crustiform banded, kadar Au tertinggi (bonanza)
     - di atasnya: Ag/Au tinggi, kuarsa vuggy, lempung (argilik)
     - di bawahnya: Au & Ag menurun, Pb-Zn naik (base-metal zone)
6. PROFIL PELAPUKAN: tudung tercuci (leached cap) di 15 m teratas, selimut pengayaan supergen
   (supergene enrichment blanket) tepat di atas muka air tanah, lalu zona transisi dan batuan segar.
7. HALO ALTERASI menjauh dari vein: silisifikasi -> ilit/argilik -> propilitik, dengan kadar dinding
   yang menurun eksponensial (halo geokimia).
8. SESAR PASCA-MINERALISASI: strike 110 deg, dip 65 deg ke baratdaya, offset dip-slip 12 m, memotong
   lensa ke-2 dan ke-3. Dipakai untuk melatih Sesar 3D (pemulihan sebelum pemodelan).
9. EFEK NUGGET: Au lognormal dengan lonjakan emas kasar (5% sampel) -> variogram Au bernugget tinggi,
   Ag jauh lebih jinak. Ini membuat latihan top-cut & variografi masuk akal.

KELUARAN (folder data/)
  SIM_collar.csv SIM_survey.csv SIM_assay.csv SIM_geologi.csv   ~1.800 bor, ~230.000 baris assay
  SIM_kecil_*.csv                                               subset 120 bor untuk latihan cepat
  SIM_upsert_*.csv                                              bor baru (latihan upsert / estimasi ulang)
  SIM_qaqc.csv                                                  CRM / duplikat / blank (latihan QAQC)
  SIM_struktur.csv SIM_pickup_survey.csv                        pengukuran struktur & pick-up permukaan
  SIM_sesar.csv                                                 bidang sesar pasca-mineralisasi
  SIM_topo_xyz.csv                                              topografi titik XYZ
  SIM_BM_GC.csv                                                 block model kosong (untuk estimasi)
  QV_Lensa2_Leapfrog.obj                                        wireframe vein (uji import solid)
  JAWABAN_MODEL.txt                                             parameter sebenarnya (kunci jawaban)

Pemakaian: python make_sim_data.py [folder_output] [--kecil | --besar]
  (tanpa opsi) : ~1.070 bor, ~98.000 baris assay — ukuran bawaan data latihan
  --kecil      : ~160 bor (cepat, untuk mencoba alur sebelum memakai data penuh)
  --besar      : kerapatan dua kali, ~300.000 baris assay (untuk uji beban seperti produksi)
"""
import csv
import math
import os
import sys

import numpy as np

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
KECIL = '--kecil' in sys.argv
BESAR = '--besar' in sys.argv      # kerapatan dua kali (~300.000 baris assay, untuk uji beban)
OUTD = ARGS[0] if ARGS else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(OUTD, exist_ok=True)
rng = np.random.default_rng(20260401)

# ---------------------------------------------------------------- kerangka struktur
E0, N0 = 505000.0, 9012000.0          # titik acuan fiktif (UTM generik)
STRIKE, DIPAZ, DIP = 45.0, 135.0, 70.0
PITCH = 55.0                           # pitch ore shoot di dalam bidang vein, dari garis strike
WT_RL = 250.0                          # paleo-muka air tanah (boiling zone)
r = math.radians
s_vec = np.array([math.sin(r(STRIKE)), math.cos(r(STRIKE)), 0.0])
dh = np.array([math.sin(r(DIPAZ)), math.cos(r(DIPAZ)), 0.0])
dd = math.cos(r(DIP)) * dh + np.array([0, 0, -math.sin(r(DIP))])      # menurun searah dip, di bidang vein
nrm = np.cross(s_vec, dd)
nrm = nrm if nrm[2] > 0 else -nrm                                     # normal ke sisi hangingwall


def topo(x, y):
    """Permukaan: lereng landai + punggungan halus (bukan bidang datar, supaya kontur ada isinya)."""
    return (330 + 0.030 * (x - E0) - 0.018 * (y - N0)
            + 6.0 * np.sin((x - E0) / 160.0) * np.cos((y - N0) / 190.0)
            + 1.8 * np.sin((x - E0) / 41.0))


C = np.array([E0, N0, 0.0])
C[2] = topo(E0, N0) - 5.0

# 4 lensa en-echelon: a = jarak sepanjang strike, b = jarak menurun dip (dari C)
LENSA = []
for i, (a0, step) in enumerate([(-360, 0.0), (-120, 16.0), (120, 32.0), (360, 48.0)]):
    LENSA.append(dict(
        nama='QV_Lensa%d' % (i + 1),
        off=step,                                  # pergeseran ke sisi HW (right-stepping array)
        a=(a0 - 150, a0 + 150),                    # panjang sepanjang strike ~300 m
        b=(5, 215),                                # tinggi menurun dip ~210 m
        t0=0.55, t1=1.9,                           # tebal dasar & tambahan di zona dilatan
        ac=a0, bc=85,
        sa=130, sb=95,
        g=2.4 + 0.35 * (i % 2),                    # kadar dasar lensa
    ))
# splay hangingwall di lensa tengah
LENSA.append(dict(nama='QV_Splay_HW', off=26.0, a=(-90, 70), b=(20, 120), t0=0.30, t1=0.75,
                  ac=-10, bc=70, sa=60, sb=45, g=1.5))


def wmid(a, b, V):
    """Posisi permukaan tengah vein pada arah normal: sigmoidal + lengkungan (sumber dilatant jog)."""
    return (V['off'] + 7.0 * np.tanh((b - 105) / 45.0)
            + 3.2 * np.sin(2 * np.pi * a / 210.0)
            + 1.6 * np.sin(2 * np.pi * b / 95.0))


def taper(a, b, V):
    a0, a1 = V['a']; b0, b1 = V['b']
    return np.minimum.reduce([np.clip((a - a0) / 45, 0, 1), np.clip((a1 - a) / 45, 0, 1),
                              np.clip((b - b0) / 40, 0, 1), np.clip((b1 - b) / 40, 0, 1)])


def shoot_uv(a, b, V):
    """Koordinat di dalam bidang vein, diputar ke sumbu ore shoot: u searah pitch, v melintangnya."""
    p = r(PITCH)
    u = (a - V['ac']) * math.cos(p) + (b - V['bc']) * math.sin(p)
    v = -(a - V['ac']) * math.sin(p) + (b - V['bc']) * math.cos(p)
    return u, v


def jog(a, b, V):
    """DILATANT JOG = zona bukaan, dan di vein geser zona inilah ore shoot-nya.

    Jadi tebal maksimum dan kadar maksimum DIKONTROL SATU STRUKTUR YANG SAMA: keduanya memanjang
    searah pitch %g deg. Itulah sebabnya GT (kadar x tebal) punya satu arah kemenerusan terbaik yang
    seharusnya bisa ditemukan kembali dengan kipas variogram / menu Ore Geometry.
    Dua pembengkakan (swell) berjarak di sepanjang sumbu shoot, meniru rangkaian jog di satu zona.""" % PITCH
    u, v = shoot_uv(a, b, V)
    swell = 0.75 + 0.25 * np.sin(2 * np.pi * u / 130.0)     # pembengkakan berjarak, tapi zona tetap MENERUS
    return 1.0 + 2.5 * swell * np.exp(-(v / 34.0) ** 2) * np.exp(-(u / 160.0) ** 2)


def thick(a, b, V):
    """Tebal vein = tebal dasar + bukaan zona dilatan, lalu meruncing di tepi lensa.

    Hanya SATU kontrol arah (zona dilatan ber-pitch), supaya arah kemenerusan tebal, kadar dan GT
    sama dan dapat ditemukan kembali dengan kipas variogram."""
    return (V['t0'] + V['t1'] * (jog(a, b, V) - 1.0)) * taper(a, b, V)


def shoot(a, b, V):
    """Kadar ore shoot: punggungan di bidang vein, sumbu sama dengan zona dilatan (pitch PITCH).
    Lebar melintang ~64 m, yaitu lebih lebar dari spasi sayatan bor (25 m) sehingga dapat terdeteksi."""
    u, v = shoot_uv(a, b, V)
    return 0.22 + 2.60 * np.exp(-(u / 120.0) ** 2 - (v / 40.0) ** 2)


def frame(p):
    q = p - C
    return q @ s_vec, q @ dd, q @ nrm


def vpt(a, b, V, side=0.0):
    return C + a * s_vec + b * dd + (wmid(a, b, V) + side * thick(a, b, V) / 2) * nrm


# ---------------------------------------------------------------- sesar pasca-mineralisasi
FA_STRIKE, FA_DIP, FA_OFF = 110.0, 65.0, 12.0
fa_s = np.array([math.sin(r(FA_STRIKE)), math.cos(r(FA_STRIKE)), 0.0])
fa_dh = np.array([math.sin(r(FA_STRIKE + 90)), math.cos(r(FA_STRIKE + 90)), 0.0])
fa_dd = math.cos(r(FA_DIP)) * fa_dh + np.array([0, 0, -math.sin(r(FA_DIP))])
fa_n = np.cross(fa_s, fa_dd); fa_n = fa_n if fa_n[2] > 0 else -fa_n
FA_P = C + 60.0 * s_vec + 90.0 * dd                 # bidang sesar lewat sini


FA_HALF = 150.0      # setengah panjang sesar sepanjang strike-nya (sesar nyata tidak tak-berhingga)


def fault_side(p):
    """Besar perpindahan per titik: 1 = penuh di blok atas (turun), 0 = tidak terpengaruh.

    Sesar dibatasi panjangnya: hanya +-FA_HALF m dari pusatnya sepanjang strike sesar, dan
    perpindahannya meruncing (taper) ke kedua ujung seperti sesar sebenarnya. Dengan begitu sesar
    hanya memotong bagian tengah array vein (lensa 2 & 3); lensa 1 & 4 tetap utuh."""
    q = p - FA_P
    atas = (q @ fa_n > 0).astype(float)
    t = np.abs(q @ fa_s)
    ramp = np.clip((FA_HALF - t) / 45.0, 0.0, 1.0)      # 1 di tengah, 0 di luar ujung sesar
    return atas * ramp


def unfault(p):
    """Pulihkan offset: blok yang turun diangkat kembali sebelum dibandingkan ke model vein."""
    return p + np.outer(fault_side(p), fa_dd) * (-FA_OFF)


def inside_all(p):
    """Untuk tiap titik: (fraksi di dalam vein per lensa, jarak terdekat ke vein terdekat, lensa dominan)."""
    q = unfault(p)
    a, b, w = frame(q)
    best_d = np.full(len(p), 99.0)
    inside = np.zeros(len(p), dtype=bool)
    which = np.full(len(p), -1)
    for k, V in enumerate(LENSA):
        T = thick(a, b, V)
        d = np.abs(w - wmid(a, b, V)) - T / 2
        d = np.where(T > 0.25, d, 99.0)
        ins = d <= 0
        which = np.where(ins & ~inside, k, which)
        inside |= ins
        best_d = np.minimum(best_d, d)
    return inside, best_d, which, a, b


# ---------------------------------------------------------------- lubang bor
holes = []


def mk_hole(hid, a, b, dipd, az=315.0, extra=8.0, lens=0):
    """Bor dari sisi hangingwall menembus lensa pada (a,b)."""
    v = np.array([math.sin(r(az)) * math.cos(r(dipd)), math.cos(r(az)) * math.cos(r(dipd)), -math.sin(r(dipd))])
    tgt = vpt(a, b, LENSA[lens])
    t = 20.0
    for _ in range(60):
        c = tgt - t * v
        t += (topo(c[0], c[1]) - c[2]) / max(-v[2], 0.3) * 0.7
    c = tgt - t * v
    c[2] = float(topo(c[0], c[1]))
    depth = float(math.ceil(t + extra))
    if depth < 25 or depth > 320 or not np.isfinite(depth):
        return
    holes.append(dict(id=hid, c=c, v=v, dip=-dipd, az=az, depth=depth))


# pola grade control: sayatan tiap 25 m sepanjang strike, kipas 5-7 bor menurun dip per sayatan
A_STEP = (7 if BESAR else 13) if not KECIL else 100
for si, a_sec in enumerate(range(-480, 481, A_STEP)):
    for li, V in enumerate(LENSA[:4]):
        if not (V['a'][0] - 20 <= a_sec <= V['a'][1] + 20):
            continue
        deep = (si % 3 == 0)          # tiap sayatan ke-3 ditambah bor dalam (resource definition)
        geser = 12 if (si % 2) else 0  # pola ZIGZAG: sayatan ganjil digeser setengah langkah
        for j, b_t in enumerate(range(20 + geser, 201 if deep else 141, 24)):
            a = a_sec + float(rng.uniform(-2.0, 2.0))
            b = b_t + float(rng.uniform(-6.0, 6.0))
            dipd = 50 + 0.055 * b_t + float(rng.uniform(-2.5, 2.5))
            mk_hole('SIM-%02d-L%d-%02d' % (si + 1, li + 1, j + 1), a, b, dipd, lens=li)

# bor baru untuk latihan upsert / estimasi ulang (tidak ikut tabel utama)
upsert = []
for i in range(14):
    a = float(rng.uniform(-300, 300)); b = float(rng.uniform(40, 130))
    mk_hole('SIM-INF-%02d' % (i + 1), a, b, 58 + float(rng.uniform(-3, 3)), lens=1 if a < 0 else 2)
    if holes:
        upsert.append(holes.pop())

# ---------------------------------------------------------------- kampanye GRADE CONTROL
# Bor tegak (RC) per bench 5 m di bagian atas endapan, pola 7 x 7 m: inilah basis data grade control
# sebenarnya — banyak bor pendek, sampel 1 m. Disimpan terpisah (SIM_gc_*) supaya bisa dipakai untuk
# latihan dua kampanye / upsert, atau digabung dengan data resource.
gc_holes = []
if not KECIL:
    for a_s in np.arange(-470, 471, 4.0 if BESAR else 7.0):
        for V in LENSA[:4]:
            if not (V['a'][0] + 10 <= a_s <= V['a'][1] - 10):
                continue
            for off in (-7.0, 0.0, 7.0):                    # 3 baris melintang jejak vein
                b_top = 18.0
                p0 = vpt(float(a_s), b_top, V) + off * nrm
                zt = float(topo(p0[0], p0[1]))
                if p0[2] < zt - 70 or p0[2] > zt + 5:
                    continue
                c = np.array([p0[0], p0[1], zt])
                v = np.array([0.0, 0.0, -1.0])              # tegak
                gc_holes.append(dict(id='GC-%05d' % (len(gc_holes) + 1), c=c, v=v, dip=-90.0, az=0.0,
                                     depth=float(np.ceil(min(60.0, zt - (p0[2] - 25.0))))))
print('lubang bor: %d resource + %d grade control + %d upsert' % (len(holes), len(gc_holes), len(upsert)))

# ---------------------------------------------------------------- sampel / assay
SUB = 6          # sub-titik per sampel untuk fraksi vein
LEN_IN, LEN_OUT = 0.5, 1.0


def sample_hole(h):
    """Satu bor -> (baris assay, baris geologi). Panjang sampel 0,5 m di/di dekat vein, 1,0 m di luar."""
    # 1) tentukan batas sampel: scan 1 m dulu untuk tahu di mana vein berada
    d = np.arange(0.0, h['depth'], 1.0)
    mid = h['c'] + np.outer(d + 0.5, h['v'])
    ins, dist, _, _, _ = inside_all(mid)
    dekat = (dist < 2.5) | ins
    bats = [0.0]
    for i, dd0 in enumerate(d):
        step = LEN_IN if dekat[i] else LEN_OUT
        x = bats[-1]
        while x < min(dd0 + 1.0, h['depth']) - 1e-9:
            x = min(x + step, h['depth'])
            bats.append(x)
    bats = np.array(sorted(set(np.round(bats, 2))))
    f, t = bats[:-1], bats[1:]
    nS = len(f)
    if nS == 0:
        return [], []
    # 2) fraksi vein per sampel dari SUB sub-titik
    frac = np.zeros(nS); dmin = np.full(nS, 99.0); lens = np.full(nS, -1); aa = np.zeros(nS); bb = np.zeros(nS)
    for q in range(SUB):
        dq = f + (t - f) * (q + 0.5) / SUB
        p = h['c'] + np.outer(dq, h['v'])
        i2, d2, w2, a2, b2 = inside_all(p)
        frac += i2.astype(float) / SUB
        dmin = np.minimum(dmin, d2)
        lens = np.where((w2 >= 0) & (lens < 0), w2, lens)
        if q == SUB // 2:
            aa, bb = a2, b2
    pm = h['c'] + np.outer((f + t) / 2, h['v'])
    z = pm[:, 2]
    zt = topo(pm[:, 0], pm[:, 1])
    # 3) zonasi vertikal epitermal
    dwt = z - WT_RL                                  # >0 di atas muka air tanah
    boil = np.exp(-(dwt / 25.0) ** 2)                # zona didih (bonanza)
    gbase = np.array([LENSA[max(k, 0)]['g'] for k in lens])
    gsh = np.zeros(nS)
    for k in range(len(LENSA)):
        m = lens == k
        if m.any():
            gsh[m] = shoot(aa[m], bb[m], LENSA[k])
    # 4) profil pelapukan
    depth_bs = zt - z                                 # kedalaman di bawah permukaan
    leach = np.clip(1 - depth_bs / 15.0, 0, 1)        # tudung tercuci
    enrich = np.exp(-((dwt - 6.0) / 7.0) ** 2) * (depth_bs > 12)   # selimut supergen
    ox = np.where(dwt > 4, 'OX', np.where(dwt > -8, 'TR', 'FR'))
    # 5) kadar
    nug = np.where(rng.random(nS) < 0.05, np.exp(rng.uniform(1.0, 2.2, nS)), 1.0)   # emas kasar
    au_v = gbase * gsh * (0.55 + 1.35 * boil) * (1 + 0.8 * enrich) * (1 - 0.35 * leach)
    au_v = au_v * np.exp(rng.normal(-0.36, 0.82, nS)) * nug
    halo = np.where(dmin < 1.5, 0.30, np.where(dmin < 5, 0.10, np.where(dmin < 12, 0.03, 0.008)))
    au_w = halo * np.exp(rng.normal(0, 0.65, nS))
    au = frac * au_v + (1 - frac) * au_w
    agau = 9.0 * np.exp(0.75 * np.clip(dwt, -60, 60) / 60.0) * (1 - 0.40 * leach)    # Ag/Au naik ke atas
    ag = np.maximum(0.1, au * agau * np.exp(rng.normal(0, 0.20, nS)))
    bm = np.clip(-dwt / 90.0, 0, 1.3)                                               # base metal makin ke bawah
    pb = np.maximum(0.001, (0.03 + 0.55 * bm) * frac * np.exp(rng.normal(0, 0.55, nS)) + 0.004)
    zn = np.maximum(0.001, (0.05 + 0.85 * bm) * frac * np.exp(rng.normal(0, 0.55, nS)) + 0.006)
    cu = np.maximum(0.0005, (0.01 + 0.09 * bm) * frac * np.exp(rng.normal(0, 0.6, nS)) + 0.002)
    sS = np.maximum(0.02, (0.4 + 2.2 * frac + 1.1 * bm) * np.exp(rng.normal(0, 0.3, nS)))
    ars = np.maximum(2.0, (25 + 420 * frac) * np.exp(rng.normal(0, 0.5, nS)))        # As ppm, penanda epitermal
    sg = 2.62 + 0.09 * frac + 0.012 * (sS / 2.0) - 0.05 * leach + rng.normal(0, 0.015, nS)
    # 6) logging geologi
    lith = np.where(frac >= 0.6, np.where(boil > 0.55, 'QVB', np.where(jogmask(aa, bb, lens), 'BX', 'QV')),
                    np.where(frac >= 0.15, 'QV_AND', np.where(depth_bs < 18, 'TUF', 'AND')))
    alt = np.where(dmin < 2, np.where(dwt > 25, 'VSIL', 'SIL'),
                   np.where(dmin < 6, 'ILL', np.where(dmin < 14, 'ARG', 'PRO')))
    tex = np.where(frac < 0.15, '-', np.where(boil > 0.55, 'COLL', np.where(dwt > 25, 'VUG',
                   np.where(bm > 0.5, 'MASS', 'CRUST'))))
    rqd = np.clip(np.where(frac > 0.3, 55, 82) - 25 * leach + rng.normal(0, 7, nS), 5, 100)
    rec = np.clip(np.where(frac > 0.3, 93, 97) - 18 * leach + rng.normal(0, 3, nS), 40, 100)
    A, G = [], []
    for i in range(nS):
        A.append([h['id'], round(float(f[i]), 2), round(float(t[i]), 2), '%s_%04d' % (h['id'], i + 1),
                  round(float(au[i]), 3), round(float(ag[i]), 2), round(float(cu[i]), 4),
                  round(float(pb[i]), 4), round(float(zn[i]), 4), round(float(sS[i]), 3),
                  int(ars[i]), round(float(sg[i]), 3)])
        G.append([h['id'], round(float(f[i]), 2), round(float(t[i]), 2), str(lith[i]), str(alt[i]),
                  str(ox[i]), str(tex[i]), int(rqd[i]), int(rec[i])])
    return A, G


def jogmask(a, b, lens):
    out = np.zeros(len(a), dtype=bool)
    for k in range(len(LENSA)):
        m = lens == k
        if m.any():
            out[m] = jog(a[m], b[m], LENSA[k]) > 3.0
    return out


def write(fn, head, rows):
    with open(os.path.join(OUTD, fn), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(head); w.writerows(rows)


H_AS = ['Hole_ID', 'From', 'To', 'Sample_ID', 'Au', 'Ag', 'Cu', 'Pb', 'Zn', 'S', 'As_ppm', 'SG']
H_GE = ['Hole_ID', 'From', 'To', 'Lith', 'Alt', 'Ox', 'Texture', 'RQD', 'Recovery']


def tables(H, pre):
    col = [[h['id'], round(float(h['c'][0]), 3), round(float(h['c'][1]), 3), round(float(h['c'][2]), 3),
            h['depth']] for h in H]
    sv = []
    for h in H:                      # survey: sedikit menyimpang (drift) supaya realistis
        for dpt in (0.0, h['depth'] / 2, h['depth']):
            sv.append([h['id'], round(dpt, 1), round(h['dip'] - 0.012 * dpt, 2), round(h['az'] + 0.02 * dpt, 2)])
    A, G = [], []
    for h in H:
        a, g = sample_hole(h); A += a; G += g
    write(pre + 'collar.csv', ['Hole_ID', 'Easting', 'Northing', 'RL', 'Total_depth'], col)
    write(pre + 'survey.csv', ['Hole_ID', 'Depth', 'Dip', 'Azimuth'], sv)
    write(pre + 'assay.csv', H_AS, A)
    write(pre + 'geologi.csv', H_GE, G)
    return A, G


A, G = tables(holes, 'SIM_')
print('assay: %d baris, geologi: %d baris' % (len(A), len(G)))
tables(upsert[:7], 'SIM_upsert_')
tables(upsert[7:], 'SIM_upsert2_')      # tahap 2: latihan koreksi Model Estimation sebagian
if gc_holes:
    Agc, Ggc = tables(gc_holes, 'SIM_gc_')
    print('grade control: %d baris assay' % len(Agc))
else:
    Agc = []
# subset kecil untuk latihan cepat (sayatan tiap 100 m)
kecil = [h for h in holes if int(h['id'].split('-')[1]) % 4 == 1]
tables(kecil, 'SIM_kecil_')
print('subset kecil: %d bor' % len(kecil))

# ---------------------------------------------------------------- QAQC
q = []
std = {'CRM-LOW': (0.52, 0.03), 'CRM-MED': (3.10, 0.12), 'CRM-HIGH': (12.40, 0.45)}
for i in range(0, len(A), 25):
    row = A[i]
    k = list(std)[(i // 25) % 3]
    tgt, sd = std[k]
    q.append([row[0], row[3], 'CRM', k, round(tgt, 3), round(float(rng.normal(tgt, sd)), 3)])
for i in range(0, len(A), 40):
    row = A[i]
    v = float(row[4])
    q.append([row[0], row[3], 'DUPLIKAT', '', v, round(max(0.001, v * float(np.exp(rng.normal(0, 0.115)))), 3)])
for i in range(0, len(A), 60):
    q.append([A[i][0], A[i][3], 'BLANK', '', 0.0, round(abs(float(rng.normal(0, 0.006))), 4)])
write('SIM_qaqc.csv', ['Hole_ID', 'Sample_ID', 'Jenis', 'Standar', 'Nilai_harap', 'Nilai_lab'], q)
print('QAQC: %d baris' % len(q))

# ---------------------------------------------------------------- struktur & pick-up permukaan
st = []
for a_s in np.arange(-460, 461, 20.0):
    for V in LENSA[:4]:
        if not (V['a'][0] <= a_s <= V['a'][1]):
            continue
        b_s = 8.0
        p = vpt(float(a_s), b_s, V)
        zt = float(topo(p[0], p[1]))
        if abs(p[2] - zt) > 25:
            continue
        st.append([round(float(p[0]), 2), round(float(p[1]), 2), round(zt, 2), 'Vein',
                   round(DIP + float(rng.normal(0, 3)), 1), round(DIPAZ + float(rng.normal(0, 5)), 1),
                   round(PITCH + float(rng.normal(0, 4)), 1), round(float(rng.normal(STRIKE + 180, 5)) % 360, 1),
                   V['nama']])
for i in range(40):                   # bidang sesar pasca-mineralisasi di permukaan
    p = FA_P + float(rng.uniform(-120, 120)) * fa_s
    zt = float(topo(p[0], p[1]))
    st.append([round(float(p[0]), 2), round(float(p[1]), 2), round(zt, 2), 'Sesar',
               round(FA_DIP + float(rng.normal(0, 4)), 1), round(FA_STRIKE + 90 + float(rng.normal(0, 6)), 1),
               '', '', 'Sesar_Pasca'])
write('SIM_struktur.csv', ['Easting', 'Northing', 'RL', 'Jenis', 'Dip', 'Dip_Azimuth', 'Plunge', 'Trend', 'Catatan'], st)

pu = []
for a_s in np.arange(-470, 471, 8.0):
    for V in LENSA[:4]:
        if not (V['a'][0] <= a_s <= V['a'][1]):
            continue
        p = vpt(float(a_s), 6.0, V)
        zt = float(topo(p[0], p[1]))
        if abs(p[2] - zt) > 20:
            continue
        pu.append([V['nama'], round(float(p[0]) + float(rng.normal(0, 0.4)), 2),
                   round(float(p[1]) + float(rng.normal(0, 0.4)), 2), round(zt, 2),
                   round(float(thick(float(a_s), 6.0, V)), 2), 'singkapan vein'])
write('SIM_pickup_survey.csv', ['Kode', 'Easting', 'Northing', 'RL', 'Tebal_m', 'Keterangan'], pu)

fp = FA_P
write('SIM_sesar.csv', ['Nama', 'Easting', 'Northing', 'RL', 'Strike', 'Dip', 'Offset_m', 'Waktu'],
      [['Sesar_Pasca', round(float(fp[0]), 2), round(float(fp[1]), 2), round(float(fp[2]), 2),
        FA_STRIKE, FA_DIP, FA_OFF, 'post']])

# ---------------------------------------------------------------- topografi
xs = np.arange(E0 - 620, E0 + 621, 5.0)
ys = np.arange(N0 - 420, N0 + 421, 5.0)
XX, YY = np.meshgrid(xs, ys, indexing='ij')
ZZ = topo(XX, YY)
write('SIM_topo_xyz.csv', ['X', 'Y', 'Z'],
      [[round(float(XX[i, j]), 2), round(float(YY[i, j]), 2), round(float(ZZ[i, j]), 2)]
       for i in range(XX.shape[0]) for j in range(XX.shape[1])])

# topografi survei berikutnya: area tambang turun s/d 7 m (latihan versi topografi & volume sisa)
def topo_nov(x, y):
    dx = (x - E0) / 150.0
    dy = (y - N0) / 110.0
    gali = 7.0 * np.exp(-(dx ** 2 + dy ** 2))
    return topo(x, y) - gali


write('SIM_topo_xyz_nov.csv', ['X', 'Y', 'Z'],
      [[round(float(XX[i, j]), 2), round(float(YY[i, j]), 2), round(float(topo_nov(XX[i, j], YY[i, j])), 2)]
       for i in range(XX.shape[0]) for j in range(XX.shape[1])])

# ---------------------------------------------------------------- vein bercabang (latihan split)
# Bor yang menembus lensa 2 DAN splay hangingwall-nya: latihan domain vein yang bercabang (split).
spl = []
for i, a_s in enumerate(np.arange(-80.0, 61.0, 20.0)):
    for j, b_t in enumerate((35.0, 60.0, 85.0, 110.0)):
        mk_hole('SPL-%02d-%d' % (i + 1, j + 1), float(a_s), float(b_t), 56 + 0.05 * b_t, lens=1)
        if holes:
            spl.append(holes.pop())
if spl:
    Asp, _ = tables(spl, 'SIM_split_')
    # block model kecil 2,5 m di sekitar lensa 2 + splay-nya (khusus latihan vein bercabang)
    cs = np.array([h['c'] for h in spl])
    gx2 = np.arange(cs[:, 0].min() - 30, cs[:, 0].max() + 31, 2.5)
    gy2 = np.arange(cs[:, 1].min() - 30, cs[:, 1].max() + 31, 2.5)
    gz2 = np.arange(210.0, 301.0, 2.5)
    bs2 = []
    for z in gz2:
        Pz = np.column_stack([np.repeat(gx2, len(gy2)), np.tile(gy2, len(gx2)), np.full(len(gx2) * len(gy2), z)])
        Pz = Pz[Pz[:, 2] < topo(Pz[:, 0], Pz[:, 1]) - 1.0]
        if not len(Pz):
            continue
        _, dz, _, _, _ = inside_all(Pz)
        for q2 in Pz[dz < 7.0]:
            bs2.append([round(float(q2[0]), 2), round(float(q2[1]), 2), round(float(q2[2]), 2),
                        2.5, 2.5, 2.5, -99, -99])
    write('SIM_split_BM_GC.csv', ['X', 'Y', 'Z', 'XINC', 'YINC', 'ZINC', 'AU_GC', 'DOMAIN'], bs2)
    print('vein bercabang (split): %d bor, %d baris assay, %d blok' % (len(spl), len(Asp), len(bs2)))

# ---------------------------------------------------------------- block model kosong
BS = (10.0, 10.0, 5.0)
gx = np.arange(E0 - 420, E0 + 421, BS[0])
gy = np.arange(N0 - 300, N0 + 301, BS[1])
gz = np.arange(120.0, 341.0, BS[2])
bm = []
for z in gz:
    P = np.column_stack([XXb := np.repeat(gx, len(gy)), np.tile(gy, len(gx)), np.full(len(gx) * len(gy), z)])
    zt = topo(P[:, 0], P[:, 1])
    keep = P[:, 2] < zt - 1.0                       # hanya blok di bawah topografi
    P = P[keep]
    if not len(P):
        continue
    _, dmin, _, _, _ = inside_all(P)
    near = dmin < 30.0                              # hanya di sekitar vein array (hemat ukuran)
    P = P[near]
    for p in P:
        bm.append([round(float(p[0]), 2), round(float(p[1]), 2), round(float(p[2]), 2),
                   BS[0], BS[1], BS[2], -99, -99])
write('SIM_BM_GC.csv', ['X', 'Y', 'Z', 'XINC', 'YINC', 'ZINC', 'AU_GC', 'DOMAIN'], bm)
print('block model: %d blok' % len(bm))

# ---------------------------------------------------------------- wireframe lensa 2 (OBJ)
V = LENSA[1]
na, nb = 90, 60
aa_ = np.linspace(V['a'][0] + 2, V['a'][1] - 2, na)
bb_ = np.linspace(V['b'][0] + 2, V['b'][1] - 2, nb)
verts = []; idx = {}


def vid(i, j, side):
    k = (i, j, side)
    if k not in idx:
        T_ = max(float(thick(aa_[i], bb_[j], V)), 0.2)
        p = C + aa_[i] * s_vec + bb_[j] * dd + (wmid(aa_[i], bb_[j], V) + (0.5 if side else -0.5) * T_) * nrm
        idx[k] = len(verts) + 1
        verts.append(p)
    return idx[k]


faces = []
for i in range(na - 1):
    for j in range(nb - 1):
        for side in (0, 1):
            A1, B1, C1, D1 = vid(i, j, side), vid(i + 1, j, side), vid(i + 1, j + 1, side), vid(i, j + 1, side)
            faces.append((A1, B1, C1) if side else (A1, C1, B1))
            faces.append((A1, C1, D1) if side else (A1, D1, C1))
for i in range(na - 1):               # tutup tepi
    for (j, sw) in ((0, 0), (nb - 1, 1)):
        A1, B1 = vid(i, j, 0), vid(i + 1, j, 0)
        C1, D1 = vid(i + 1, j, 1), vid(i, j, 1)
        faces.append((A1, B1, C1) if sw else (A1, C1, B1))
        faces.append((A1, C1, D1) if sw else (A1, D1, C1))
for j in range(nb - 1):
    for (i, sw) in ((0, 1), (na - 1, 0)):
        A1, B1 = vid(i, j, 0), vid(i, j + 1, 0)
        C1, D1 = vid(i, j + 1, 1), vid(i, j, 1)
        faces.append((A1, B1, C1) if sw else (A1, C1, B1))
        faces.append((A1, C1, D1) if sw else (A1, D1, C1))
with open(os.path.join(OUTD, 'QV_Lensa2_Leapfrog.obj'), 'w') as fh:
    fh.write('# GC-Ex data simulasi - wireframe sintetis %s (bukan data proyek nyata)\n' % V['nama'])
    for p in verts:
        fh.write('v %.3f %.3f %.3f\n' % (p[0], p[1], p[2]))
    for f3 in faces:
        fh.write('f %d %d %d\n' % f3)

# ---------------------------------------------------------------- kunci jawaban
with open(os.path.join(OUTD, 'JAWABAN_MODEL.txt'), 'w') as fh:
    fh.write("""KUNCI JAWABAN MODEL SIMULASI GC-Ex  (data sintetis, bukan proyek nyata)
======================================================================
Endapan emas epitermal low-sulphidation, terkontrol zona geser. Semua angka di bawah ini adalah
PARAMETER MODEL yang dipakai membuat datanya, plus ANGKA HASIL UKUR dari data yang jadi — supaya
Anda tahu sampai berapa dekat hasil pemodelan Anda masuk akal.

1. PARAMETER MODEL
------------------
Zona geser              : strike %.0f deg, dip %.0f deg ke azimuth %.0f  (bidang acuan datar)
Array vein              : 4 lensa sigmoidal EN-ECHELON right-stepping + 1 splay hangingwall
Pitch ore shoot         : %.0f deg dari garis strike, DI DALAM bidang vein, sama untuk semua lensa
Zona dilatan = ore shoot: tebal maksimum DAN kadar maksimum dikontrol satu struktur yang sama
Paleo-muka air tanah    : RL %.0f m; zona didih (bonanza, tekstur colloform) +-25 m
Sesar pasca-mineralisasi: strike %.0f deg, dip %.0f deg, offset dip-slip %.0f m, panjang +-%.0f m
                          (hanya memotong bagian tengah array = lensa 2 & 3; lensa 1 & 4 utuh)
Pelapukan               : tudung tercuci 15 m teratas, selimut supergen tepat di atas muka air tanah
Zonasi vertikal         : Ag/Au naik ke atas, Pb-Zn naik ke bawah, As penanda vein
Efek nugget Au          : 5%% sampel dilonjakkan (emas kasar)

2. ANGKA HASIL UKUR DARI DATA INI
---------------------------------
Bidang terbaik seluruh intersep : dip ~66 deg, dip-azimuth ~139 deg
  -> WAJAR kalau Anda mendapat dip ~64-66, BUKAN 70. Permukaan vein sigmoidal (melengkung), jadi
     bidang rata-rata bagian yang terbor memang lebih landai dari bidang acuan 70 deg.
Pitch dari kipas variogram GT   : 55 deg (gabungan 4 lensa; per lensa 50-65 deg)
  -> Ukur dengan GT (kadar x tebal) PER BOR, bukan per sampel, dan gabungkan keempat lensa:
     satu lensa saja terlalu sedikit datanya untuk menembus efek nugget Au.
  -> Pada lensa 2 & 3 arahnya kacau bila sesar BELUM dipulihkan. Itu latihan Sesar 3D.
Au di dalam vein                : mean ~4,8 g/t, median ~2,2 g/t, CV ~2,0, maks ~150 g/t
  -> CV 2 berarti top-cut memang perlu; coba 30-60 g/t dan lihat pengaruhnya ke estimasi.
Puncak kadar                    : RL 230-270 m (zona didih), Au rata-rata ~10 g/t
Ag/Au                           : ~4,4 di RL 150-170  ->  ~17 di RL 290-310
Pb, Zn                          : naik ke bawah (Zn ~0,06%% di atas  ->  ~0,93%% di bawah)
As                              : ~480 ppm di vein vs ~29 ppm di batuan dinding
Tebal intersep per bor          : median 1,0 m, p90 3,5 m, maks ~5,5 m (endapan vein sempit)
Tekstur colloform (COLL)        : hampir 100%% di RL 230-270, 0%% di luarnya
QAQC                            : CRM bias ~0%% (sd 3,7-5,6%%), duplikat HARD rata ~8%%, blank < 0,02 g/t

3. YANG SEHARUSNYA ANDA TEMUKAN KEMBALI
---------------------------------------
[ ] Domain vein: 4 lensa terpisah yang saling bertumpang sepanjang strike (JANGAN disatukan jadi
    satu vein menerus — itu akan melebarkan tonase dan menghaluskan kadar).
[ ] Orientasi elipsoid pencarian: major searah pitch 55 deg di dalam bidang vein, semi searah strike,
    minor tegak lurus bidang vein (rasio kira-kira 3 : 2 : 1).
[ ] Zona kadar tinggi memanjang searah pitch, memusat di sekitar RL 250 m.
[ ] Variogram Au bernugget tinggi; Ag lebih jinak. Top-cut Au diperlukan.
[ ] Tanpa pemulihan sesar, lensa 2 & 3 tampak bergeser %.0f m dan domainnya pecah.
[ ] Klasifikasi: bagian dalam (b > ~140 m menurun dip) hampir tidak terbor -> wajar jadi Inferred.
""" % (STRIKE, DIP, DIPAZ, PITCH, WT_RL, FA_STRIKE, FA_DIP, FA_OFF, FA_HALF, FA_OFF))

# ---------------------------------------------------------------- database dengan kesalahan sengaja
# Untuk latihan menu Validasi data bor: tiap kesalahan di bawah HARUS terdeteksi aplikasi.
rc = [list(x) for x in csv.reader(open(os.path.join(OUTD, 'SIM_kecil_collar.csv')))]
hd, bd = rc[0], rc[1:]
bd.append(list(bd[0]))                                   # (1) Hole_ID ganda
bd.append([bd[1][0] + '-DUP', bd[1][1], bd[1][2], bd[1][3], '0'])      # (2) kedalaman total 0
bd.append(['SIM-KOSONG', '', '', '310.5', '80'])                       # (3) koordinat kosong
bd.append(['SIM-JAUH', '999999.0', '1000.0', '310.5', '80'])           # (4) koordinat di luar area
with open(os.path.join(OUTD, 'SIM_rusak_collar.csv'), 'w', newline='') as fh:
    csv.writer(fh).writerows([hd] + bd)
ra = [list(x) for x in csv.reader(open(os.path.join(OUTD, 'SIM_kecil_assay.csv')))]
ha, ba = ra[0], ra[1:]
ba.append([ba[0][0], '5', '5', 'X-001', '0.10', '1.0', '0.01', '0.01', '0.01', '0.5', '20', '2.6'])     # (5) From = To
ba.append([ba[0][0], '2.0', '8.0', ba[3][3], '0.30', '1.0', '0.01', '0.01', '0.01', '0.5', '20', '2.6']) # (6) interval tumpang & Sample_ID ganda
ba.append(['SIM-X99', '0', '1', 'X-002', '0.2', '1', '0.01', '0.01', '0.01', '0.5', '20', '2.6'])        # (7) Hole_ID tak ada di collar
ba.append([ba[40][0], '40', '41', 'X-003', '-99', '1', '0.01', '0.01', '0.01', '0.5', '20', '2.6'])      # (8) nilai -99
ba.append([ba[50][0], '1000', '1001', 'X-004', '1.0', '1', '0.01', '0.01', '0.01', '0.5', '20', '2.6'])  # (9) melebihi kedalaman bor
with open(os.path.join(OUTD, 'SIM_rusak_assay.csv'), 'w', newline='') as fh:
    csv.writer(fh).writerows([ha] + ba)
print('database rusak: 4 kesalahan collar + 5 kesalahan assay (sengaja)')

# ---------------------------------------------------------------- BACA_SAYA
with open(os.path.join(OUTD, 'BACA_SAYA.txt'), 'w') as fh:
    fh.write("""DATA LATIHAN GC-Ex — SEPENUHNYA SINTETIS
========================================
Semua angka di folder ini dihitung dari model matematika (lihat make_sim_data.py).
TIDAK ada nama perusahaan, Hole ID, koordinat, atau hasil lab proyek nyata.

Mulai dari mana
---------------
1. Latihan cepat  : SIM_kecil_collar.csv / _survey / _assay / _geologi  (%d bor)
2. Data penuh     : SIM_collar.csv / _survey / _assay / _geologi        (%d bor, %d baris assay)
3. Topografi      : SIM_topo_xyz.csv        (Data Spasial -> topografi)
4. Block model    : SIM_BM_GC.csv           (Block Model -> import, lalu Model Estimation)
5. Struktur       : SIM_struktur.csv        (basis data struktur: Dip, Dip_Azimuth, Plunge, Trend)
   Pick-up permukaan: SIM_pickup_survey.csv (Peta / Mapping)
6. Sesar 3D       : SIM_sesar.csv           (post-mineralisasi, offset 12 m)
7. QAQC           : SIM_qaqc.csv            (CRM, duplikat, blank)
8. Wireframe      : QV_Lensa2_Leapfrog.obj  (uji import solid dari luar)
9. Upsert         : SIM_upsert_*.csv / SIM_upsert2_*.csv  (bor baru tahap 1 & 2, estimasi ulang sebagian)

Set latihan lain
----------------
SIM_gc_*.csv          kampanye GRADE CONTROL: bor tegak per bench, pola 7 m (%d bor, %d baris assay)
SIM_split_*.csv       vein BERCABANG (lensa 2 + splay hangingwall) + SIM_split_BM_GC.csv blok 2,5 m
SIM_rusak_*.csv       database dengan kesalahan SENGAJA (latihan menu Validasi data bor):
                      collar -> Hole_ID ganda, kedalaman 0, koordinat kosong, koordinat di luar area
                      assay  -> From=To, interval tumpang & Sample_ID ganda, Hole_ID tak ada di
                                collar, nilai -99, interval melebihi kedalaman bor
SIM_topo_xyz_nov.csv  topografi survei berikutnya (area tambang turun s/d 7 m) -> latihan versi
                      topografi di Data Spasial dan perhitungan volume sisa
SIM_LAT_*.csv         endapan LATERIT berlapis (dibuat make_sim_laterit.py) untuk menu
                      Geomodeller Stratified-Laterite Deposit

Catatan: wireframe contoh kini bernama QV_Lensa2_Leapfrog.obj (dulu QV_Utama_Leapfrog.obj),
karena model vein sekarang berupa array 4 lensa, bukan satu vein tunggal.

JAWABAN_MODEL.txt memuat parameter model sebenarnya DAN angka hasil ukur dari data ini —
buka setelah Anda mencoba sendiri.
""" % (len(kecil), len(holes), len(A), len(gc_holes), len(Agc)))

print('OK ->', OUTD)
