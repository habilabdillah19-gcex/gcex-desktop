# -*- coding: utf-8 -*-
"""Ore Works 0.26.0: sisipkan / perbarui paket Demo Studio ke app-ow/index.html (<script type="text/plain" id="ow-demo">).

Pemilik 19 Nov 2026: "di platform Studio ada satu tombol demo yang melakukan simulasi ril (dengan data simulasi terinstal
seperti di GC-Ex) yang outputnya bisa dipilih berdasarkan jenis Vein (3 vein hasil simulasi)".

Isi paket per sistem vein (data fiktif di docs/tutorial-ow/data/<Vein_*>): tabel bor (collar/survey/assay/geologi CSV apa
adanya), topografi STR dijarangkan ke grid 10 m, string interpretasi penampang (<awalan>_string_interpretasi.json) dan
vein aktual kasar (permukaan parametrik dari tools/uji/sim_vein_sistem_ow.py, grid 5 m) untuk perbandingan di akhir demo.
JSON → gzip → base64 (dibuka di aplikasi dengan DecompressionStream, tanpa internet).

  python web-src-ow/sisip_demo_ow.py
"""
import base64, gzip, json, math, pathlib, sys
import numpy as np

R = pathlib.Path(__file__).resolve().parents[1]
H = R / 'app-ow' / 'index.html'
DATA = R / 'docs' / 'tutorial-ow' / 'data'
sys.path.insert(0, str(R / 'tools' / 'uji'))
import sim_vein_sistem_ow as sim  # noqa: E402

SISTEM = [
    ('sigmoid', 'Vein_Sigmoid_EkorKuda', 'Sigmoid + ekor kuda',
     'Vein utama melengkung 240 m; ujung utaranya pecah menjadi 3 cabang (ekor kuda).', {'VS2': 'VS1', 'VS3': 'VS1', 'VS4': 'VS1'}),
    ('echelon', 'Vein_EnEchelon', 'En echelon + penghubung',
     '4 segmen sejajar bertangga; satu vein penghubung pendek dan miring (jog).', {'VE5_RL': 'VE2'}),
    ('silang', 'Vein_Silang', 'Silang landai–curam',
     'Vein curam timur–barat disilang vein landai utara–selatan; keduanya menerus.', {'VX2': 'VX1'}),
    ('splay', 'Vein_Splay_Vertikal', 'Bercabang vertikal (Y)',
     'Vein curam pecah ke atas menjadi dua lengan; penampangnya berbentuk huruf Y.', {'VY2': 'VY1', 'VY3': 'VY1'}),
]


def rdp(P, tol):
    if len(P) < 4: return P
    a, b = np.array(P[0]), np.array(P[-1]); ab = b - a; L = np.hypot(*ab) or 1.0
    d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / L for p in P[1:-1]]
    i = int(np.argmax(d)) + 1
    if d[i - 1] <= tol: return [P[0], P[-1]]
    return rdp(P[:i + 1], tol)[:-1] + rdp(P[i:], tol)


def jarang(pts, nmax=14):
    """poligon tertutup → ≤ nmax titik (RDP pada dua belahan)."""
    if len(pts) <= nmax: return pts
    tol = 0.2
    while True:
        h = len(pts) // 2; Q = rdp(pts[:h + 1], tol)[:-1] + rdp(pts[h:] + [pts[0]], tol)[:-1]
        if len(Q) <= nmax or tol > 20: return Q
        tol *= 1.4


def mesh_kasar(T, ds=5.0, nv=12):
    a0 = -T.ext0 if T.ext0 > 0 else (T.L * 0.015 if (T.r0 and T.r1) else 0.0)
    ss = np.concatenate([np.arange(a0, T.L * 0.985, ds), [T.L * 0.985]]); vv = np.linspace(0, 1, nv); ns = len(ss)
    Sg, Vg = np.meshgrid(ss, vv, indexing='ij')
    V = np.concatenate([T.titik(Sg, Vg, +1).reshape(-1, 3), T.titik(Sg, Vg, -1).reshape(-1, 3)])
    idx = lambda k, i, j: k * ns * nv + i * nv + j; F = []
    for i in range(ns - 1):
        for j in range(nv - 1):
            F += [[idx(0, i, j), idx(0, i + 1, j), idx(0, i + 1, j + 1)], [idx(0, i, j), idx(0, i + 1, j + 1), idx(0, i, j + 1)]]
            F += [[idx(1, i, j), idx(1, i + 1, j + 1), idx(1, i + 1, j)], [idx(1, i, j), idx(1, i, j + 1), idx(1, i + 1, j + 1)]]
        for j in (0, nv - 1):
            a, b, c, d = idx(0, i, j), idx(0, i + 1, j), idx(1, i + 1, j), idx(1, i, j)
            F += [[a, c, b], [a, d, c]] if j == 0 else [[a, b, c], [a, c, d]]
    for i in (0, ns - 1):
        for j in range(nv - 1):
            a, b, c, d = idx(0, i, j), idx(0, i, j + 1), idx(1, i, j + 1), idx(1, i, j)
            F += [[a, b, c], [a, c, d]] if i == 0 else [[a, c, b], [a, d, c]]
    return V, np.array(F)


def topo_jarang(path, step=10.0):
    out = []
    for ln in path.read_text(encoding='utf-8').splitlines():
        p = [x.strip() for x in ln.split(',')]
        if len(p) >= 4 and p[0] == '1':
            n, e = float(p[1]), float(p[2])
            if abs(n / step - round(n / step)) < 1e-6 and abs(e / step - round(e / step)) < 1e-6: out.append(ln)
        elif not out or p[0] != '1':
            out.append(ln)
    return '\n'.join(out) + '\n'


def paket():
    P = {'v': 1, 'sistem': []}
    for k, folder, nm, desk, par in SISTEM:
        D = DATA / folder; G = json.loads((D / 'geom.json').read_text(encoding='utf-8')); pre = G['awalan_berkas']
        S = sim.sistem(k)
        I = json.loads((D / ('%s_string_interpretasi.json' % pre)).read_text(encoding='utf-8'))
        sol = []
        for x in I['solid']:
            sol.append({'nm': x['nm'], 'm': x['m'], 'az': round(x['az'], 2), 'par': par.get(x['nm']),
                        'S': [{'o': round(t['o'], 2), 'pts': [[round(a, 2), round(b, 2)] for a, b in jarang([list(q) for q in t['pts']])]} for t in x['S']]})
        akt = []
        for T in S.B:
            V, F = mesh_kasar(T)
            akt.append({'k': T.kode, 'v': [int(round(c * 10)) for c in V.reshape(-1)], 't': F.reshape(-1).tolist()})
        csv = {t: (D / ('%s_%s.csv' % (pre, t))).read_text(encoding='utf-8') for t in ('collar', 'survey', 'assay', 'geologi')}
        if k == 'splay':                     # 0.32.0: poligon Y tertutup per penampang (irisan vein aktual) untuk demo Implisit
            import trimesh
            Ua = trimesh.load(D / 'aktual_vein.obj', process=True); Ua.apply_translation([-S.E0, -S.N0, 0]); az0 = sol[0]['az']; yp = []
            r = math.radians(az0); nr = np.array([math.cos(r), -math.sin(r)])
            for nl in range(-90, 91, 20):
                o = float(np.dot([0.0, float(nl)], nr)); pts = sim.irisan_ideal(Ua, S, az0, o)
                if pts: yp.append({'o': round(o, 2), 'pts': [[round(a, 2), round(b, 2)] for a, b in jarang([list(q) for q in pts], 26)]})
        else:
            yp = None
        P['sistem'].append({'k': k, 'nm': nm, 'desk': desk, 'pre': pre, 'E0': S.E0, 'N0': S.N0, 'E': I['E'], 'N': I['N'],
                            'nl': G['lubang'], 'vakt': G['vol_union_m3'], 'csv': csv, 'topo': topo_jarang(D / ('%s_topografi.str' % pre)),
                            'sol': sol, 'akt': akt, **({'yp': yp, 'az': sol[0]['az']} if yp else {})})
    return P


if __name__ == '__main__':
    js = json.dumps(paket(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    b64 = base64.b64encode(gzip.compress(js, 9, mtime=0)).decode('ascii')
    blok = '<script type="text/plain" id="ow-demo">' + b64 + '</script>\n'
    s = H.read_text(encoding='utf-8')
    if 'id="ow-demo">' in s:
        a = s.index('<script type="text/plain" id="ow-demo">'); b = s.index('</script>\n', a) + len('</script>\n'); s = s[:a] + blok + s[b:]
    else:
        k = s.index('<script type="text/plain" id="ore-main">'); s = s[:k] + blok + s[k:]
    H.write_text(s, encoding='utf-8')
    print('paket demo: %d KB JSON → %d KB base64' % (len(js) // 1024, len(b64) // 1024))
