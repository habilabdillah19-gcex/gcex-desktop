# -*- coding: utf-8 -*-
"""Data fiktif Ore Works: vein epitermal "aktual" bercabang TIGA ARAH (jurus berbeda) yang menyatu di tengah.

Permintaan pemilik (19 Nov 2026): "simulasi wireframe Vein model dengan bentuk seideal mungkin dengan Aktual Epithermal
Vein yang memiliki percabangan 3 arah trend mineralisasi dengan tinggi vein terbentuk adalah 100 meter. Buat percabangan
3 arah dimana penyatuan vein ada di bagian tengah."

Geometri (semua koordinat lokal fiktif, E0/N0 di bawah):
- Titik pertemuan (junction) di tengah sistem (E0, N0). Tiga lengan memancar dengan jurus berbeda:
    VA  jurus 018° (ke NNE)  panjang 170 m, dip 72° ke 108° (ESE), tebal dasar 2,8 m  — lengan utama
    VB  jurus 138° (ke SE)   panjang 130 m, dip 68° ke 228° (SW),  tebal dasar 2,2 m
    VC  jurus 262° (ke W)    panjang 110 m, dip 78° ke 352° (N),   tebal dasar 1,6 m
- Tinggi vein 100 m di pertemuan: puncak = topografi − 2 m (tererosi / tertutup tanah), dasar 100 m di bawahnya.
  Ke arah ujung lengan dasar naik (bentuk lensa: tinggi = 100·(1−(s/L)²)^0,6) → lengan menipis & berakhir di ujung.
- Di dekat pertemuan (s < 8 m) ketiga lengan tegak dan menyatu pada satu sumbu vertikal; menjauh dari pertemuan
  (8–60 m) kemiringan berangsur ke dip masing-masing (lengan sedikit "terpuntir" seperti pada percabangan nyata).
- Bentuk epitermal: liuk sepanjang jurus (±1,2 m, gelombang 55 m), pinch & swell (±35 %), menebal di pertemuan
  (zona dilatasi, ×1,8), menipis ke ujung & ke dasar (akar vein), kadar puncak di "zona didih" ±30 % dari puncak.
- Tebal = lebar HORIZONTAL tegak lurus jurus.

Keluaran (folder argumen 1, bawaan /tmp/vt):
  VT_collar.csv, VT_survey.csv, VT_assay.csv, VT_geologi.csv  — bor (Vein_Type VA / VB / VC, logging 1 m)
  VT_topografi.str                                             — topografi grid 5 m (Surpac string)
  VT_aktual_vein.obj                                           — wireframe AKTUAL gabungan (union, tertutup, 1 tubuh)
  VT_aktual_VA.obj / _VB.obj / _VC.obj                         — tiap lengan (tertutup, saling menumpang di pertemuan)
  geom.json                                                    — parameter + ringkasan uji
Perlu: numpy, trimesh, manifold3d (pip).
"""
import math, csv, json, os, sys
import numpy as np
import trimesh, manifold3d as mf

OUT = (sys.argv[1] if len(sys.argv) > 1 else '/tmp/vt').rstrip('/') + '/'
os.makedirs(OUT, exist_ok=True)
E0, N0 = 60000.0, 90000.0
H = 100.0                       # tinggi vein di pertemuan
S0 = -12.0                      # lengan diteruskan 12 m melewati pertemuan agar saling menumpang (union)
ARMS = {  # kode: jurus (arah lengan menjauh), panjang, dip, tebal dasar, fase
    'VA': dict(az=18.0, L=170.0, dip=72.0, t0=2.8, ph=0.0),
    'VB': dict(az=138.0, L=130.0, dip=68.0, t0=2.2, ph=1.7),
    'VC': dict(az=262.0, L=110.0, dip=78.0, t0=1.6, ph=3.1),
}


def topo(e, n):
    """Topografi lokal (e, n relatif E0/N0): bukit landai di atas pertemuan + kemiringan regional."""
    return 214.0 + 0.025 * e - 0.015 * n + 5.0 * math.exp(-(e * e + n * n) / (2 * 110.0 ** 2))


for A in ARMS.values():
    a = math.radians(A['az'])
    A['u'] = np.array([math.sin(a), math.cos(a)])            # arah jurus (menjauh dari pertemuan)
    A['n'] = np.array([math.cos(a), -math.sin(a)])           # normal horizontal = arah dip (jurus + 90°)
    A['dipdir'] = (A['az'] + 90.0) % 360.0


def ztop(A, s):
    p = A['u'] * max(s, 0.0)
    return topo(p[0], p[1]) - 2.0


def tinggi(A, s):
    r = min(max(s, 0.0) / A['L'], 0.999)
    return H * (1 - r * r) ** 0.6


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def offset(A, s, z):
    """Posisi bidang tengah vein, diukur sepanjang normal horizontal (m)."""
    w = smooth((s - 8.0) / 52.0)
    dip = (ztop(A, s) - z) / math.tan(math.radians(A['dip'])) * w
    liuk = 1.2 * math.sin(2 * math.pi * s / 55.0 + A['ph']) * smooth(s / 10.0)
    return dip + liuk


def tebal(A, s, v):
    """Tebal horizontal (m) pada jarak jurus s dan fraksi kedalaman v (0 = puncak, 1 = dasar)."""
    ps = 1 + 0.35 * math.sin(2 * math.pi * s / 40.0 + A['ph']) * math.cos(1.5 * math.pi * v + A['ph'] * 0.5)
    jn = 1 + 0.8 * math.exp(-max(s, 0.0) / 18.0)
    uj = (1 - min(max(s, 0.0) / A['L'], 1.0) ** 2) ** 0.5
    ak = (1 - v ** 3) ** 0.5
    return max(0.15, A['t0'] * ps * jn * uj * ak)


def titik(A, s, v, sisi):
    zt = ztop(A, s)
    z = zt - v * tinggi(A, s)
    m = offset(A, s, z) + sisi * tebal(A, s, v) / 2.0
    p = A['u'] * s + A['n'] * m
    return [p[0], p[1], z]


def mesh_lengan(A):
    ss = np.concatenate([np.arange(S0, 0, 3.0), np.arange(0, A['L'] * 0.985, 2.5), [A['L'] * 0.985]])
    vv = np.linspace(0, 1, 41)
    ns, nv = len(ss), len(vv)
    V = []
    for sisi in (+1, -1):
        for s in ss:
            for v in vv:
                V.append(titik(A, s, v, sisi))
    V = np.array(V)
    idx = lambda k, i, j: k * ns * nv + i * nv + j
    F = []
    for i in range(ns - 1):
        for j in range(nv - 1):
            a, b, c, d = idx(0, i, j), idx(0, i + 1, j), idx(0, i + 1, j + 1), idx(0, i, j + 1)
            F += [[a, b, c], [a, c, d]]
            a, b, c, d = idx(1, i, j), idx(1, i + 1, j), idx(1, i + 1, j + 1), idx(1, i, j + 1)
            F += [[a, c, b], [a, d, c]]
    for i in range(ns - 1):                     # puncak (j=0) & dasar (j=nv-1)
        for j in (0, nv - 1):
            a, b, c, d = idx(0, i, j), idx(0, i + 1, j), idx(1, i + 1, j), idx(1, i, j)
            F += [[a, c, b], [a, d, c]] if j == 0 else [[a, b, c], [a, c, d]]
    for i in (0, ns - 1):                       # ujung pertemuan (i=0) & ujung lengan
        for j in range(nv - 1):
            a, b, c, d = idx(0, i, j), idx(0, i, j + 1), idx(1, i, j + 1), idx(1, i, j)
            F += [[a, b, c], [a, c, d]] if i == 0 else [[a, c, b], [a, d, c]]
    m = trimesh.Trimesh(V, np.array(F), process=True)
    trimesh.repair.fix_normals(m)
    assert m.is_watertight, 'lengan tidak tertutup'
    if m.volume < 0:
        m.invert()
    return m


def ke_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32), tri_verts=np.asarray(m.faces, dtype=np.uint32)))


def dari_mf(M):
    g = M.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def tulis_obj(m, nm, judul):
    with open(OUT + nm, 'w') as f:
        f.write('# %s — data fiktif Ore Works (koordinat lokal fiktif)\n' % judul)
        f.write('o %s\n' % os.path.splitext(nm)[0])
        for x, y, z in m.vertices:
            f.write('v %.3f %.3f %.3f\n' % (x + E0, y + N0, z))
        for a, b, c in m.faces:
            f.write('f %d %d %d\n' % (a + 1, b + 1, c + 1))


# ---------------- wireframe aktual ----------------
lengan = {k: mesh_lengan(A) for k, A in ARMS.items()}
U = ke_mf(lengan['VA']) + ke_mf(lengan['VB']) + ke_mf(lengan['VC'])
uni = dari_mf(U)
assert uni.is_watertight and len(uni.split(only_watertight=False)) == 1, 'union bukan satu tubuh tertutup'
for k, m in lengan.items():
    tulis_obj(m, 'VT_aktual_%s.obj' % k, 'vein aktual lengan %s' % k)
tulis_obj(uni, 'VT_aktual_vein.obj', 'vein aktual gabungan VA+VB+VC (union)')


# ---------------- uji titik di dalam vein (kebenaran logging) ----------------
def kode_di(e, n, z):
    best, bv = '', 9e9
    for k, A in ARMS.items():
        p = np.array([e, n])
        s = float(p @ A['u'])
        if s < S0 or s > A['L'] * 0.985:
            continue
        zt = ztop(A, s)
        h = tinggi(A, s)
        if not (zt - h <= z <= zt):
            continue
        v = (zt - z) / h
        q = float(p @ A['n'])
        r = abs(q - offset(A, s, z)) / (tebal(A, s, v) / 2.0)
        if r <= 1 and r < bv:
            best, bv = k, r
    return best


# ---------------- pemboran ----------------
def arah(az, dip):
    a, d = math.radians(az), math.radians(dip)
    return np.array([math.sin(a) * math.cos(d), math.cos(a) * math.cos(d), math.sin(d)])


holes = []
for k, A in ARMS.items():
    az_bor = (A['dipdir'] + 180.0) % 360.0          # bor dari sisi atap (HW) memotong vein tegak lurus jurus
    for si, s in enumerate(np.arange(10.0, A['L'] - 12.0, 20.0)):
        h = tinggi(A, s)
        for hi, d in enumerate((20.0, 50.0, 80.0)):
            if d > h - 6:
                continue
            dip = -55.0 if d < 30 else (-62.0 if d < 60 else -68.0)
            D = arah(az_bor, dip)
            T = np.array(titik(A, s, d / h, 0))
            L = 10.0
            for _ in range(60):                       # mundur sepanjang lubang sampai keluar topografi
                C = T - D * L
                if C[2] >= topo(C[0], C[1]):
                    break
                L += 5.0
            for _ in range(30):
                C = T - D * L
                L += (topo(C[0], C[1]) - C[2]) / max(0.2, -D[2])
            C = T - D * L
            holes.append(('VT%s%02d_%d' % (k[1], si + 1, hi + 1), C[0], C[1], topo(C[0], C[1]), az_bor, dip, int(math.ceil(L + 25))))
# lubang pertemuan: tiap lengan satu lubang 3 m dari sumbu pertemuan (kedalaman 35 / 60 / 85 m), tegak lurus jurus
# lengannya — menembus zona tebal tempat ketiga lengan menyatu
for (k, A), d in zip(ARMS.items(), (35.0, 60.0, 85.0)):
    az_bor = (A['dipdir'] + 180.0) % 360.0
    dip = -60.0
    D = arah(az_bor, dip)
    T = np.array(titik(A, 3.0, d / tinggi(A, 3.0), 0))
    L = 10.0
    for _ in range(40):
        C = T - D * L
        L += (topo(C[0], C[1]) - C[2]) / max(0.2, -D[2])
    C = T - D * L
    holes.append(('VTJ_%s' % k[1], C[0], C[1], topo(C[0], C[1]), az_bor, dip, int(math.ceil(L + 30))))

rng = np.random.default_rng(19)
col = [['Hole_ID', 'X', 'Y', 'Z', 'Max_Depth', 'Hole_Purpose']]
sv = [['Hole_ID', 'Depth', 'Dip', 'Azimuth']]
asy = [['Hole_ID', 'From', 'To', 'Au_ppm', 'Ag_ppm']]
geo = [['Hole_ID', 'From', 'To', 'Lith', 'Alt', 'Vein_Type']]
from collections import Counter
icp = Counter()
for hid, x, y, z, az, dip, L in holes:
    col.append([hid, round(x + E0, 2), round(y + N0, 2), round(z, 2), L, 'Exploration'])
    sv.append([hid, 0, dip, round(az, 1)])
    D = arah(az, dip)
    for f in range(0, L):
        cs = []
        dmin = 9e9
        for t in np.arange(f + 0.05, f + 1, 0.1):
            P = np.array([x, y, z]) + D * t
            c = kode_di(P[0], P[1], P[2])
            cs.append(c)
        c = max(set(cs), key=cs.count)
        if c and cs.count(c) < 5:
            c = ''
        P = np.array([x, y, z]) + D * (f + 0.5)
        # jarak ke vein terdekat (untuk halo alterasi & kadar)
        halo = any(kode_di(P[0] + dx, P[1] + dy, P[2]) for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4)))
        if c:
            icp[c] += 1
            A = ARMS[c]
            s = max(float(np.array([P[0], P[1]]) @ A['u']), 0.0)
            v = (ztop(A, s) - P[2]) / tinggi(A, s)
            mu = 1.0 + 0.7 * math.exp(-((v - 0.3) / 0.25) ** 2) + 0.4 * math.exp(-s / 25.0)
            au = float(rng.lognormal(mu, 0.55))
        elif halo:
            au = float(rng.lognormal(-1.6, 0.6))
        else:
            au = float(rng.lognormal(-3.3, 0.7))
        ag = au * float(rng.uniform(6, 15))
        asy.append([hid, f, f + 1, round(au, 3), round(ag, 2)])
        geo.append([hid, f, f + 1, 'QV' if c else 'AND', 'SIL' if c else ('ARG' if halo else 'PRO'), c or '-'])
for nm, R in [('VT_collar', col), ('VT_survey', sv), ('VT_assay', asy), ('VT_geologi', geo)]:
    with open(OUT + nm + '.csv', 'w', newline='') as f:
        csv.writer(f).writerows(R)

# ---------------- topografi (Surpac .str, grid 5 m, baris per N) ----------------
with open(OUT + 'VT_topografi.str', 'w') as f:
    f.write('VEIN_TIGA_ARAH,19-Nov-26,,topografi fiktif\n0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000\n')
    for n in range(-180, 221, 5):
        for e in range(-200, 201, 5):
            f.write('1, %.3f, %.3f, %.3f, \n' % (n + N0, e + E0, topo(e, n)))
        f.write('0, 0.000, 0.000, 0.000,\n')
    f.write('0, 0.000, 0.000, 0.000, END\n')

# ---------------- ringkasan ----------------
ring = {
    'E0': E0, 'N0': N0, 'tinggi_m': H, 'pertemuan_RL_puncak': round(topo(0, 0) - 2, 2),
    'lengan': {k: {kk: A[kk] for kk in ('az', 'L', 'dip', 't0', 'dipdir')} for k, A in ARMS.items()},
    'volume_m3': {k: round(m.volume, 1) for k, m in lengan.items()},
    'volume_union_m3': round(uni.volume, 1), 'tumpang_tindih_m3': round(sum(m.volume for m in lengan.values()) - uni.volume, 1),
    'segitiga_union': int(len(uni.faces)), 'rl_union': [round(float(uni.bounds[0][2]), 1), round(float(uni.bounds[1][2]), 1)],
    'lubang': len(holes), 'meter_bor': int(sum(h[6] for h in holes)), 'interval_vein_1m': dict(icp),
}
json.dump(ring, open(OUT + 'geom.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(ring, indent=1, ensure_ascii=False))
