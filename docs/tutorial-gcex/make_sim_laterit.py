"""Data simulasi LATERIT NIKEL untuk tutorial Geomodeller Stratified-Laterite & Sesar 3D (SINTETIS, bukan data perusahaan).
Profil: TS (tanah penutup) -> LIM (limonit) -> SAP (saprolit) -> BRK (bedrock). Bor vertikal grid 25 m, sampel 1 m.
Sesar F1 (post-laterit): jejak N010E lewat E 412140, dip 65 ke 100 (timur), normal, net slip 12 m (HW timur turun).
python make_sim_laterit.py [folder_output]   (default: ./data)"""
import numpy as np, os, sys, csv, math
OUTD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(OUTD, exist_ok=True); rng = np.random.default_rng(7)
E0, N0 = 412000.0, 9620000.0
# ---------- sesar F1 ----------
F_E, F_az, F_dip, F_dd, F_off = E0 + 140.0, 10.0, 65.0, 100.0, 12.0
st = np.array([math.sin(math.radians(F_az)), math.cos(math.radians(F_az))])
dvh = np.array([math.sin(math.radians(F_dd)), math.cos(math.radians(F_dd))])
dv = np.array([dvh[0] * math.cos(math.radians(F_dip)), dvh[1] * math.cos(math.radians(F_dip)), -math.sin(math.radians(F_dip))])
SLIP = dv * F_off                                      # gerak hanging wall (turun searah dip)
TR = [(F_E - 220 * st[0], N0 - 220 * st[1]), (F_E + 520 * st[0], N0 + 520 * st[1])]   # jejak di permukaan (dunia)
def s0_rest(x, y):  # atap limonit sebelum sesar
    return 182 + 7 * np.sin((x - E0) / 85.0) * np.cos((y - N0) / 110.0) + 0.015 * (x - E0) - 0.01 * (y - N0)
def t_lim(x, y): return np.clip(5.5 + 3.5 * np.sin((x - E0) / 60.0 + 1) * np.cos((y - N0) / 75.0) + 1.5 * np.cos((x + y - E0 - N0) / 40.0), 0, None)
def t_sap(x, y): return np.clip(9 + 4 * np.cos((x - E0) / 70.0) * np.sin((y - N0) / 90.0 + 0.5), 2.5, None)
ZF = 190.0   # jejak sesar diambil pada elevasi tetap 190 (menu Sesar 3D: Elevasi jejak = Tetap, Z 190)
NUP = np.array([dvh[0] * math.sin(math.radians(F_dip)), dvh[1] * math.sin(math.radians(F_dip)), math.cos(math.radians(F_dip))])
def zfault(x, y):  # elevasi bidang sesar di kolom (x, y)
    return ZF - ((x - F_E) * NUP[0] + (y - N0) * NUP[1]) / NUP[2]
def surf(x, y):
    a = s0_rest(x, y); b = a - t_lim(x, y); c = b - t_sap(x, y); return a, b, c
def column(x, y):
    """kolom present: (fungsi kode(z) & rel(z), topo). Di atas bidang sesar = HW (profil tergeser), di bawah = FW."""
    zf = zfault(x, y); fw = surf(x, y); h = [v + SLIP[2] for v in surf(x - SLIP[0], y - SLIP[1])]
    top = h[0] if h[0] > zf else fw[0]
    def prof(z):
        P = h if z > zf else fw
        if z > P[0]: return 'TS', 0.5, P
        if z > P[1]: return ('LIM' if P[0] - P[1] >= 0.5 else 'SAP'), (P[0] - z) / max(0.1, P[0] - P[1]), P
        if z > P[2]: return 'SAP', (P[1] - z) / max(0.1, P[1] - P[2]), P
        return 'BRK', 0.5, P
    bot = (h if h[2] > zf else fw)[2]; bot = min(bot, fw[2])
    return prof, top + 1.0, bot
def grade(code, x, y, rel):
    n = rng.normal
    if code == 'TS': return dict(NI=0.6 + n(0, .08), CO=0.04 + n(0, .01), FE=35 + n(0, 3), MGO=1.2 + n(0, .3), SIO2=18 + n(0, 3))
    if code == 'LIM':
        g = 1.15 + 0.35 * math.sin((x - E0) / 55.0) + 0.25 * rel
        return dict(NI=g + n(0, .1), CO=0.11 + 0.04 * math.cos((y - N0) / 60.0) + n(0, .015), FE=46 - 8 * rel + n(0, 2.5), MGO=1.5 + 4 * rel + n(0, .6), SIO2=7 + 6 * rel + n(0, 1.5))
    if code == 'SAP':
        g = 1.7 + 0.6 * math.exp(-((rel - 0.3) / 0.35) ** 2) + 0.3 * math.cos((y - N0) / 65.0)
        return dict(NI=g + n(0, .15), CO=0.05 + n(0, .01), FE=17 - 6 * rel + n(0, 2), MGO=14 + 12 * rel + n(0, 2), SIO2=36 + 4 * rel + n(0, 2.5))
    return dict(NI=0.28 + n(0, .05), CO=0.012 + n(0, .003), FE=6.5 + n(0, .8), MGO=36 + n(0, 2), SIO2=40 + n(0, 1.5))
# ---------- bor ----------
col, sur, ass, geo = [], [], [], []
k = 0
for j in range(13):
    for i in range(13):
        x = E0 + i * 25 + rng.uniform(-2, 2); y = N0 + j * 25 + rng.uniform(-2, 2)
        prof, topo, zb = column(x, y)
        depth = int(math.ceil(topo - zb + 3 + rng.integers(0, 3)))
        k += 1; hid = 'LAT-%03d' % k
        col.append([hid, round(x, 3), round(y, 3), round(topo, 3), depth]); sur.append([hid, 0, -90, 0]); sur.append([hid, depth, -90, 0])
        for d in range(depth):
            z = topo - d - 0.5; code, rel, _ = prof(z)
            g = grade(code, x, y, min(1, max(0, rel)))
            ass.append([hid, d, d + 1, '%s_%03d' % (hid, d + 1)] + [round(max(0, g[e]), 3 if e in ('NI', 'CO') else 2) for e in ('NI', 'CO', 'FE', 'MGO', 'SIO2')])
            geo.append([hid, d, d + 1, code])
def W(name, head, rows):
    with open(os.path.join(OUTD, name), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(head); w.writerows(rows)
W('SIM_LAT_collar.csv', ['Hole_ID', 'Easting', 'Northing', 'RL', 'Total_depth'], col)
W('SIM_LAT_survey.csv', ['Hole_ID', 'Depth', 'Dip', 'Azimuth'], sur)
W('SIM_LAT_assay.csv', ['Hole_ID', 'From', 'To', 'Sample_ID', 'Ni', 'Co', 'Fe', 'MgO', 'SiO2'], ass)
W('SIM_LAT_geologi.csv', ['Hole_ID', 'From', 'To', 'Zona'], geo)
# ---------- topografi 10 m ----------
tp = []
for x in np.arange(E0 - 40, E0 + 341, 10.0):
    for y in np.arange(N0 - 40, N0 + 341, 10.0):
        tp.append([round(x, 1), round(y, 1), round(column(x, y)[1], 2)])
W('SIM_LAT_topo_xyz.csv', ['X', 'Y', 'Z'], tp)
# ---------- block model GC 12.5 x 12.5 x 1 m ----------
bm = []
for x in np.arange(E0 - 6.25 + 12.5, E0 + 300, 12.5):
    for y in np.arange(N0 - 6.25 + 12.5, N0 + 300, 12.5):
        prof, topo, zb = column(x, y)
        for z in np.arange(math.floor(zb - 4) + 0.5, topo, 1.0):
            bm.append([round(x, 2), round(y, 2), round(z, 2), 12.5, 12.5, 1, 1.6])
W('SIM_LAT_BM_GC.csv', ['X', 'Y', 'Z', 'XINC', 'YINC', 'ZINC', 'SG'], bm)
W('SIM_LAT_sesar.csv', ['Nama', 'X', 'Y', 'Dip', 'Dip_Direction', 'Jenis', 'Offset_m', 'Waktu'], [['F1', round(TR[0][0], 2), round(TR[0][1], 2), F_dip, F_dd, 'normal', F_off, 'post'], ['F1', round(TR[1][0], 2), round(TR[1][1], 2), F_dip, F_dd, 'normal', F_off, 'post']])
print(len(col), 'hole,', len(ass), 'sampel,', len(bm), 'blok; jejak F1', [(round(float(a), 2), round(float(b), 2)) for a, b in TR])
