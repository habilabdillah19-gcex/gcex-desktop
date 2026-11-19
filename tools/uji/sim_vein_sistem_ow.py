# -*- coding: utf-8 -*-
"""Simulasi sistem vein epitermal (data fiktif) + uji pemodelan eksplisit Studio Ore Works.

Pemilik 19 Nov 2026: "Sebelum mengerjakan usulan, buat 3 simulasi vein system dulu agar dapat mereview lebih komprehensif".

Tiga sistem (melengkapi Vein_Cabang = bercabang ke bawah dan Vein_Tiga_Arah = tiga arah jurus menyatu di tengah):
  sigmoid   Vein_Sigmoid_EkorKuda  vein utama berjurus melengkung 340°→020° (240 m), ujung utara pecah jadi 3 cabang ekor kuda
  echelon   Vein_EnEchelon         4 segmen en echelon jurus 045° bertangga kanan 14 m, tumpang 25 m, satu vein penghubung (jog)
  silang    Vein_Silang            vein curam (jurus 090°, dip 80°) disilang vein landai (jurus 000°, dip 32°), keduanya menerus

Model geometri umum tiap "tubuh" vein: jejak permukaan melengkung C(s) (s = jarak sepanjang jurus), disapu ke bawah searah
VEKTOR DIP tetap d dengan sudut dip; tinggi lensa (menipis ke ujung), liuk sepanjang jurus, pinch & swell, menebal di titik
tertentu, menipis ke dasar. Tebal = lebar horizontal tegak lurus jurus setempat.

Pakai:
  python tools/uji/sim_vein_sistem_ow.py buat <sigmoid|echelon|silang> <folder>
  python tools/uji/sim_vein_sistem_ow.py uji  <sigmoid|echelon|silang> <folder data> [bor|ideal|ideal10|ideal5|segmen]
Perlu: numpy, trimesh, rtree, manifold3d; uji: playwright + chromium.
"""
import math, csv, json, os, sys, asyncio, pathlib
import numpy as np
import trimesh, manifold3d as mf

REPO = pathlib.Path(__file__).resolve().parents[2]
sm = lambda x: (lambda c: c * c * (3 - 2 * c))(np.clip(x, 0, 1))


class Sistem:
    def __init__(self, nama, E0, N0, topo, deskripsi):
        self.nama, self.E0, self.N0, self.topo, self.desk, self.B = nama, E0, N0, topo, deskripsi, []


class Tubuh:
    def __init__(self, S, kode, mulai, arah, L, daz, dip, H, t0, ph=0.0, cover=2.0, ext0=0.0, runcing0=True, runcing1=True,
                 benjol=(), liuk=1.2, lam_liuk=55.0, ps=0.35, lam_ps=40.0, sambung=False, Hfn=None):
        """arah: fungsi s(array) -> heading jurus (derajat). daz: azimut vektor dip. ext0: diteruskan lurus ke belakang (m)."""
        self.S, self.kode, self.L, self.dip, self.H, self.t0, self.ph, self.cover = S, kode, L, dip, H, t0, ph, cover
        self.ext0, self.r0, self.r1, self.benjol, self.liuk, self.lam_liuk, self.ps, self.lam_ps = ext0, runcing0, runcing1, benjol, liuk, lam_liuk, ps, lam_ps
        self.sambung, self.Hfn = sambung, Hfn
        a = math.radians(daz); self.d = np.array([math.sin(a), math.cos(a)])
        # jejak: integrasi heading (langkah 0,5 m)
        ss = np.arange(0, L + 0.5, 0.5); hd = np.radians(arah(ss)); C = np.zeros((len(ss), 2)); C[0] = mulai
        for i in range(1, len(ss)):
            hm = (hd[i] + hd[i - 1]) / 2; C[i] = C[i - 1] + 0.5 * np.array([math.sin(hm), math.cos(hm)])
        if ext0 > 0:
            sb = np.arange(-ext0, 0, 0.5); h0 = hd[0]; Cb = np.array(mulai)[None] + sb[:, None] * np.array([math.sin(h0), math.cos(h0)])[None]
            ss = np.concatenate([sb, ss]); C = np.concatenate([Cb, C]); hd = np.concatenate([np.full(len(sb), h0), hd])
        self.ss, self.C, self.hd = ss, C, hd
        self.U = np.stack([np.sin(hd), np.cos(hd)], 1); self.N = np.stack([np.cos(hd), -np.sin(hd)], 1)
        S.B.append(self)

    # ---- fungsi bentuk (tervektor terhadap s) ----
    def _i(self, s):
        return np.clip(np.round((np.asarray(s, float) + self.ext0) / 0.5).astype(int), 0, len(self.ss) - 1)

    def Cs(self, s): return self.C[self._i(s)]
    def Us(self, s): return self.U[self._i(s)]
    def Ns(self, s): return self.N[self._i(s)]

    def ztop(self, s):
        c = self.Cs(s); return self.S.topo(c[..., 0], c[..., 1]) - self.cover

    def tinggi(self, s):
        s = np.asarray(s, float); r = np.clip(s / self.L, 0, 0.999)
        if self.r0 and self.r1:
            rr = np.clip(np.abs(2 * s / self.L - 1), 0, 0.999); f = (1 - rr ** 2) ** 0.6
        elif self.r1:
            f = (1 - r ** 2) ** 0.6
        else:
            f = np.ones_like(s)
        base = self.Hfn(s) if self.Hfn else self.H
        return np.maximum(5.0, base * f)

    def ujung_tebal(self, s):
        s = np.asarray(s, float)
        if self.r0 and self.r1:
            rr = np.clip(np.abs(2 * s / self.L - 1), 0, 1); return np.sqrt(1 - rr ** 2)
        if self.r1:
            return np.sqrt(1 - np.clip(s / self.L, 0, 1) ** 2)
        return np.ones_like(s)

    def liuk_off(self, s):
        s = np.asarray(s, float); return self.liuk * np.sin(2 * math.pi * s / self.lam_liuk + self.ph) * (sm(s / 10.0) if self.sambung else 1.0)

    def tebal(self, s, v):
        s = np.asarray(s, float); v = np.asarray(v, float)
        p = 1 + self.ps * np.sin(2 * math.pi * s / self.lam_ps + self.ph) * np.cos(1.5 * math.pi * v + self.ph * 0.5)
        b = 1.0
        for sc, amp, w in self.benjol:
            b = b + amp * np.exp(-((s - sc) / w) ** 2)
        return np.maximum(0.15, self.t0 * p * b * self.ujung_tebal(s) * np.sqrt(np.clip(1 - v ** 3, 0, 1)))

    def titik(self, s, v, sisi):
        s = np.asarray(s, float); v = np.asarray(v, float); zt = self.ztop(s); z = zt - v * self.tinggi(s)
        geser = (zt - z) / math.tan(math.radians(self.dip))
        P = self.Cs(s) + self.d * geser[..., None] + self.Ns(s) * (self.liuk_off(s) + sisi * self.tebal(s, v) / 2)[..., None]
        return np.concatenate([P, z[..., None]], -1)

    # ---- titik → apakah di dalam (fungsi kebenaran) ----
    def dalam(self, P):
        """P (n,3) koordinat lokal → (bool dalam, rasio |m|/(t/2), s, v)."""
        P = np.asarray(P, float); n = len(P); ok = np.zeros(n, bool); rr = np.full(n, 9e9); so = np.zeros(n); vo = np.zeros(n)
        tn = math.tan(math.radians(self.dip)); K = self.C[::2]; Ks = self.ss[::2]
        for i0 in range(0, n, 4000):
            Q = P[i0:i0 + 4000]; zt = self.S.topo(Q[:, 0], Q[:, 1]) - self.cover
            for _ in range(2):
                q0 = Q[:, :2] - self.d[None] * ((zt - Q[:, 2]) / tn)[:, None]
                d2 = ((q0[:, None, :] - K[None]) ** 2).sum(2); s = Ks[d2.argmin(1)]
                zt = self.ztop(s)
            q0 = Q[:, :2] - self.d[None] * ((zt - Q[:, 2]) / tn)[:, None]
            m = ((q0 - self.Cs(s)) * self.Ns(s)).sum(1) - self.liuk_off(s); h = self.tinggi(s); v = (zt - Q[:, 2]) / h
            along = ((q0 - self.Cs(s)) * self.Us(s)).sum(1)
            inr = (s > -self.ext0 + 0.6 + 0 * along) & (s < self.L * 0.985) & (np.abs(along) < 1.0) & (v >= 0) & (v <= 1)
            r = np.abs(m) / (self.tebal(s, np.clip(v, 0, 1)) / 2)
            ok[i0:i0 + 4000] = inr & (r <= 1); rr[i0:i0 + 4000] = np.where(inr, r, 9e9); so[i0:i0 + 4000] = s; vo[i0:i0 + 4000] = v
        return ok, rr, so, vo

    def mesh(self):
        ss = np.concatenate([np.arange(-self.ext0, 0, 2.0), np.arange(0, self.L * 0.985, 2.0), [self.L * 0.985]]) if self.ext0 > 0 else np.concatenate([np.arange(0, self.L * 0.985, 2.0), [self.L * 0.985]])
        if self.r0 and self.r1:
            ss = ss[ss >= self.L * 0.015]; ss = np.concatenate([[self.L * 0.015], ss])
        vv = np.linspace(0, 1, 41); ns, nv = len(ss), len(vv)
        Sg, Vg = np.meshgrid(ss, vv, indexing='ij')
        V = np.concatenate([self.titik(Sg, Vg, +1).reshape(-1, 3), self.titik(Sg, Vg, -1).reshape(-1, 3)])
        idx = lambda k, i, j: k * ns * nv + i * nv + j; F = []
        for i in range(ns - 1):
            for j in range(nv - 1):
                a, b, c, d = idx(0, i, j), idx(0, i + 1, j), idx(0, i + 1, j + 1), idx(0, i, j + 1); F += [[a, b, c], [a, c, d]]
                a, b, c, d = idx(1, i, j), idx(1, i + 1, j), idx(1, i + 1, j + 1), idx(1, i, j + 1); F += [[a, c, b], [a, d, c]]
            for j in (0, nv - 1):
                a, b, c, d = idx(0, i, j), idx(0, i + 1, j), idx(1, i + 1, j), idx(1, i, j); F += [[a, c, b], [a, d, c]] if j == 0 else [[a, b, c], [a, c, d]]
        for i in (0, ns - 1):
            for j in range(nv - 1):
                a, b, c, d = idx(0, i, j), idx(0, i, j + 1), idx(1, i, j + 1), idx(1, i, j); F += [[a, b, c], [a, c, d]] if i == 0 else [[a, c, b], [a, d, c]]
        m = trimesh.Trimesh(V, np.array(F), process=True); trimesh.repair.fix_normals(m)
        assert m.is_watertight, self.kode + ' tidak tertutup'
        if m.volume < 0: m.invert()
        return m


def ke_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def dari_mf(M):
    g = M.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


# ======================== definisi tiga sistem ========================
def sistem(nama):
    if nama == 'sigmoid':
        topo = lambda e, n: 205.0 + 0.02 * e + 0.01 * n + 6.0 * np.exp(-((e - 10) ** 2 + (n - 20) ** 2) / (2 * 130.0 ** 2))
        S = Sistem('Vein_Sigmoid_EkorKuda', 70000.0, 30000.0, topo, 'vein utama jurus melengkung 340°→020° (240 m, dip 70° ke E), ujung utara pecah 3 cabang ekor kuda')
        Tubuh(S, 'VS1', (-10.0, -120.0), lambda s: 340.0 + 40.0 * sm(s / 240.0), 240.0, 90.0, 70.0, 100.0, 2.6, ph=0.3, benjol=[(150, 0.5, 30)])
        Tm = S.B[0]; i0 = Tm._i(195.0); P0 = tuple(Tm.C[i0]); Hm = float(Tm.tinggi(195.0))
        for k, (hd, L, t0, ph) in enumerate([(355.0, 55.0, 1.2, 1.1), (22.0, 70.0, 1.5, 2.0), (48.0, 50.0, 1.0, 2.9)]):
            Tubuh(S, 'VS%d' % (k + 2), P0, (lambda h: (lambda s: np.full(np.shape(s), h)))(hd), L, 90.0, 70.0, Hm, t0, ph=ph, ext0=10.0, runcing0=False,
                  sambung=True, liuk=0.6, benjol=[(0, 0.6, 8)])
        return S
    if nama == 'echelon':
        topo = lambda e, n: 190.0 - 0.015 * e + 0.02 * n + 4.0 * np.exp(-(e ** 2 + n ** 2) / (2 * 150.0 ** 2))
        S = Sistem('Vein_EnEchelon', 40000.0, 50000.0, topo, '4 segmen en echelon jurus 045° bertangga kanan 14 m, tumpang 25 m (dip 75° ke SE), satu vein penghubung')
        u = np.array([math.sin(math.radians(45)), math.cos(math.radians(45))]); n = np.array([math.cos(math.radians(45)), -math.sin(math.radians(45))])
        base = np.array([-140.0, -140.0])
        for k in range(4):
            st = base + u * (65.0 * k) + n * (14.0 * k)
            Tubuh(S, 'VE%d' % (k + 1), tuple(st), lambda s: np.full(np.shape(s), 45.0), 90.0, 135.0, 75.0, [95.0, 100.0, 90.0, 85.0][k], [2.0, 2.4, 2.2, 1.8][k], ph=0.7 * k)
        # penghubung (jog) dari segmen 2 (s=72) ke segmen 3 (s=18)
        A = S.B[1].Cs(72.0); Bp = S.B[2].Cs(18.0); dv = Bp - A; hd = math.degrees(math.atan2(dv[0], dv[1])) % 360; L = float(np.hypot(*dv))
        Tubuh(S, 'VE5', tuple(A), lambda s: np.full(np.shape(s), hd), L + 6.0, 135.0, 75.0, 72.0, 1.4, ph=1.3, ext0=6.0, runcing0=False, runcing1=False, sambung=True, liuk=0.3)
        return S
    if nama == 'silang':
        topo = lambda e, n: 230.0 + 0.01 * e - 0.02 * n + 5.0 * np.exp(-((e + 20) ** 2 + n ** 2) / (2 * 140.0 ** 2))
        S = Sistem('Vein_Silang', 20000.0, 70000.0, topo, 'vein curam jurus 090° dip 80° ke S disilang vein landai jurus 000° dip 32° ke W, keduanya menerus')
        Tubuh(S, 'VX1', (-150.0, 0.0), lambda s: np.full(np.shape(s), 90.0), 260.0, 180.0, 80.0, 100.0, 2.4, ph=0.4)
        Tubuh(S, 'VX2', (70.0, -110.0), lambda s: np.full(np.shape(s), 0.0), 220.0, 270.0, 32.0, 100.0, 4.5, ph=1.9, liuk=0.8)
        return S
    raise SystemExit('sistem tidak dikenal: ' + nama)


# ======================== pembuat data ========================
def kode_di(S, P):
    """Kode vein di titik-titik P (lokal) — tubuh dengan rasio |m|/(t/2) terkecil."""
    best = np.array([''] * len(P), dtype=object); br = np.full(len(P), 9e9)
    for T in S.B:
        ok, r, _, _ = T.dalam(P); m = ok & (r < br); best[m] = T.kode; br[m] = r[m]
    return best


def buat(nama, OUT):
    S = sistem(nama); os.makedirs(OUT, exist_ok=True); OUT = OUT.rstrip('/') + '/'
    ms = {T.kode: T.mesh() for T in S.B}
    U = None
    for T in S.B:
        U = ke_mf(ms[T.kode]) if U is None else U + ke_mf(ms[T.kode])
    uni = dari_mf(U); bag = len(uni.split(only_watertight=False))
    def obj(m, nm, judul):
        with open(OUT + nm, 'w') as f:
            f.write('# %s — data fiktif Ore Works (koordinat lokal fiktif)\no %s\n' % (judul, nm[:-4]))
            for x, y, z in m.vertices: f.write('v %.4f %.4f %.4f\n' % (x + S.E0, y + S.N0, z))
            for a, b, c in m.faces: f.write('f %d %d %d\n' % (a + 1, b + 1, c + 1))
    pre = S.nama.split('_')[1][:2].upper()
    obj(uni, 'aktual_vein.obj', 'vein aktual %s (union)' % S.nama)
    for k, m in ms.items(): obj(m, 'aktual_%s.obj' % k, 'vein aktual %s' % k)
    # ---- bor per pagar (tegak lurus jurus setempat, dari sisi atap) ----
    holes = []
    for T in S.B:
        tn = math.tan(math.radians(T.dip)); s0 = 3.0 if T.sambung else 10.0
        for k, s in enumerate(np.arange(s0, T.L - 10.0, 20.0)):
            h = float(T.tinggi(s)); nrm = T.Ns(s); nrm = nrm if np.dot(nrm, T.d) > 0 else -nrm   # sisi atap = searah vektor dip
            az = (math.degrees(math.atan2(-nrm[0], -nrm[1]))) % 360
            for i, dd in enumerate((20.0, 50.0, 80.0)):
                if dd > h - 6: continue
                dip = (-55.0, -62.0, -68.0)[i] if T.dip >= 55 else -(90.0 - T.dip)
                a, dpr = math.radians(az), math.radians(dip); D = np.array([math.sin(a) * math.cos(dpr), math.cos(a) * math.cos(dpr), math.sin(dpr)])
                Tg = T.titik(np.array(s), np.array(dd / h), 0); L = 10.0
                for _ in range(60):
                    C = Tg - D * L; L += (float(S.topo(C[0], C[1])) - C[2]) / max(0.2, -D[2])
                C = Tg - D * L
                holes.append(('%s%02d_%d' % (T.kode, k + 1, i + 1), C, az, dip, int(math.ceil(L + 25))))
    rng = np.random.default_rng(23)
    col = [['Hole_ID', 'X', 'Y', 'Z', 'Max_Depth', 'Hole_Purpose']]; sv = [['Hole_ID', 'Depth', 'Dip', 'Azimuth']]
    asy = [['Hole_ID', 'From', 'To', 'Au_ppm', 'Ag_ppm']]; geo = [['Hole_ID', 'From', 'To', 'Lith', 'Alt', 'Vein_Type']]
    from collections import Counter
    icp = Counter(); tanpa = []
    for hid, C, az, dip, L in holes:
        col.append([hid, round(C[0] + S.E0, 2), round(C[1] + S.N0, 2), round(C[2], 2), L, 'Exploration']); sv.append([hid, 0, dip, round(az, 1)])
        a, dpr = math.radians(az), math.radians(dip); D = np.array([math.sin(a) * math.cos(dpr), math.cos(a) * math.cos(dpr), math.sin(dpr)])
        t = np.arange(0.05, L, 0.1); P = C[None] + t[:, None] * D[None]; kd = kode_di(S, P).reshape(L, 10)
        tm = C[None] + (np.arange(L) + 0.5)[:, None] * D[None]
        halo = np.zeros(L, bool)
        for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4)):
            halo |= kode_di(S, tm + np.array([dx, dy, 0])) != ''
        ada = False
        for f in range(L):
            vals = [x for x in kd[f]]; c = max(set(vals), key=vals.count)
            if c and vals.count(c) < 5: c = ''
            if not c:
                cs = [x for x in vals if x]
                c = max(set(cs), key=cs.count) if len(cs) >= 5 else ''
            if c:
                icp[c] += 1; ada = True; T = [x for x in S.B if x.kode == c][0]; _, _, s1, v1 = T.dalam(tm[f:f + 1])
                mu = 1.0 + 0.7 * math.exp(-((float(v1[0]) - 0.3) / 0.25) ** 2); au = float(rng.lognormal(mu, 0.55))
            elif halo[f]: au = float(rng.lognormal(-1.6, 0.6))
            else: au = float(rng.lognormal(-3.3, 0.7))
            asy.append([hid, f, f + 1, round(au, 3), round(au * float(rng.uniform(6, 15)), 2)])
            geo.append([hid, f, f + 1, 'QV' if c else 'AND', 'SIL' if c else ('ARG' if halo[f] else 'PRO'), c or '-'])
        if not ada: tanpa.append(hid)
    p = pre
    for nm, R in [('collar', col), ('survey', sv), ('assay', asy), ('geologi', geo)]:
        with open(OUT + '%s_%s.csv' % (p, nm), 'w', newline='') as f: csv.writer(f).writerows(R)
    with open(OUT + '%s_topografi.str' % p, 'w') as f:
        f.write('%s,19-Nov-26,,topografi fiktif\n0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000\n' % S.nama.upper())
        for nn in range(-220, 241, 5):
            for e in range(-240, 241, 5): f.write('1, %.3f, %.3f, %.3f, \n' % (nn + S.N0, e + S.E0, float(S.topo(e, nn))))
            f.write('0, 0.000, 0.000, 0.000,\n')
        f.write('0, 0.000, 0.000, 0.000, END\n')
    # cek kebenaran: titik tengah interval vein di dalam wireframe aktual
    ring = {'sistem': S.nama, 'deskripsi': S.desk, 'E0': S.E0, 'N0': S.N0, 'awalan_berkas': p,
            'tubuh': {T.kode: {'L': T.L, 'dip': T.dip, 'vektor_dip_az': round(math.degrees(math.atan2(*T.d)) % 360, 1), 't0': T.t0, 'H': T.H if not callable(T.H) else 'fungsi',
                               'vol_m3': round(float(ms[T.kode].volume), 1)} for T in S.B},
            'vol_union_m3': round(float(uni.volume), 1), 'bagian_union': bag, 'lubang': len(holes), 'meter_bor': int(sum(h[4] for h in holes)),
            'interval_vein_1m': dict(icp), 'lubang_tanpa_vein': tanpa}
    json.dump(ring, open(OUT + 'geom.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(ring, indent=1, ensure_ascii=False))
    return ring


# ======================== uji pemodelan di Studio ========================
JS_ICS = r"""(a)=>{const GA=geoActive(),M=activeHoles(),out=[];const r=a.az*Math.PI/180,u=[Math.sin(r),Math.cos(r)],nr=[Math.cos(r),-Math.sin(r)];
 const posAt=(p,cum,d)=>{for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]||i+2===cum.length){const f=cum[i+1]>cum[i]?Math.min(1,Math.max(0,(d-cum[i])/(cum[i+1]-cum[i]))):0;return [(p[i*3]+(p[i*3+3]-p[i*3])*f)/10+O[0],(p[i*3+1]+(p[i*3+4]-p[i*3+1])*f)/10+O[1],(p[i*3+2]+(p[i*3+5]-p[i*3+2])*f)/10+O[2]];}};
 for(const P of a.pagar){const q={m:'v',E:a.E,N:a.N,az:r,azd:a.az,off:P.off,len:0,t:P.t,u,nr},ics=[];
  for(const [id,{h}] of M){if(!String(id).startsWith(P.awal))continue;const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);let cur=null;const sg=[];
   for(const x of iv.slice().sort((p,q)=>p.f-q.f)){const v=String(x.v.Vein_Type||'').trim();if(v===a.kode){if(cur&&Math.abs(cur.t-x.f)<1e-6)cur.t=x.t;else{cur={f:x.f,t:x.t};sg.push(cur);}}else cur=null;}
   for(const s of sg){const A=posAt(h.p,cum,s.f),Bp=posAt(h.p,cum,s.t),mid=posAt(h.p,cum,(s.f+s.t)/2);ics.push({id,hw:scProj(q,...A),fw:scProj(q,...Bp),mid});}}
  out.push({off:P.off,ics});}return out;}"""


def trend(P):
    P = np.asarray(P, float)
    if len(P) < 2: return None
    _, _, vt = np.linalg.svd(P - P.mean(0)); d = vt[0]
    return d if d[1] < 0 else -d


def bidang(T, s_list):
    """Arah garis penampang Studio untuk sekelompok pagar: tegak lurus rata-rata jurus, menghadap sisi atap."""
    U = np.array([T.Us(s) for s in s_list]).mean(0); U /= np.linalg.norm(U); n = np.array([U[1], -U[0]])
    n = n if np.dot(n, T.d) > 0 else -n
    return math.degrees(math.atan2(n[0], n[1])) % 360


def irisan_ideal(mesh, S, az, off):
    """Penampang SEBENARNYA dari wireframe aktual pada bidang penampang Studio (string sebenarnya)."""
    r = math.radians(az); u = np.array([math.sin(r), math.cos(r), 0]); nr = np.array([math.cos(r), -math.sin(r), 0])
    sec = mesh.section(plane_origin=nr * off, plane_normal=nr)
    if sec is None: return None
    best = None
    for L in sec.discrete:
        if len(L) < 4: continue
        if best is None or len(L) > len(best): best = L
    if best is None: return None
    pts = [[float(np.dot(p, u)), float(p[2])] for p in best[:-1]]
    if len(pts) > 80: pts = pts[::int(math.ceil(len(pts) / 80))]
    return pts


async def uji(nama, B, mode='bor'):
    S = sistem(nama); B = B.rstrip('/') + '/'; G = json.load(open(B + 'geom.json')); p = G['awalan_berkas']; E0, N0 = S.E0, S.N0
    OUT = str(pathlib.Path.cwd()) + '/'; rep = {'sistem': S.nama, 'mode': mode}
    aktual = trimesh.load(B + 'aktual_vein.obj', process=True); aktual.apply_translation([-E0, -N0, 0])
    akt_b = {T.kode: (lambda m: (m.apply_translation([-E0, -N0, 0]), m)[1])(trimesh.load(B + 'aktual_%s.obj' % T.kode, process=True)) for T in S.B}
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        kw = {'executable_path': '/usr/bin/google-chrome'} if os.path.exists('/usr/bin/google-chrome') else {}
        b = await pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'], **kw)
        pg = await b.new_page(viewport={'width': 1536, 'height': 864}); E = pg.evaluate; errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300])); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto((REPO / 'app-ow' / 'index.html').as_uri()); await pg.wait_for_timeout(2500)
        for k in ('collar', 'survey', 'assay', 'geo'):
            await pg.set_input_files('#dsf-' + k, B + '%s_%s.csv' % (p, 'geologi' if k == 'geo' else k))
        await pg.wait_for_timeout(1500); await E("()=>document.getElementById('dsgo').click()"); await pg.wait_for_timeout(3500)
        await pg.set_input_files('#sff', B + '%s_topografi.str' % p); await pg.wait_for_timeout(2500)
        SOL = []; MIDS = []
        for T in S.B:
            s0 = 3.0 if T.sambung else 10.0; sk = list(np.arange(s0, T.L - 10.0, 20.0))
            kel = [list(range(len(sk)))]
            if os.environ.get('JOG_H') == '1' and T.sambung and len(sk) <= 1:
                # vein penghubung pendek: string HORIZONTAL (mode RL) dari irisan sebenarnya tiap 10 m — cara memodelkan
                # tubuh pendek/miring yang hanya terpotong satu penampang
                mb = akt_b[T.kode]; STR = []
                for z in np.arange(mb.bounds[0][2] + 2, mb.bounds[1][2] - 0.5, 10.0):
                    sec = mb.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
                    if sec is None: continue
                    Ls = [L for L in sec.discrete if len(L) >= 4]
                    if not Ls: continue
                    L = max(Ls, key=len)[:-1]; L = L[::int(math.ceil(len(L) / 60))] if len(L) > 60 else L
                    STR.append({'o': round(float(z), 2), 'pts': [[round(float(q[0] + E0), 3), round(float(q[1] + N0), 3)] for q in L]})
                SOL.append({'nm': T.kode + '_RL', 'az': 0.0, 'm': 'h', 'S': STR, 'sambung': True}); continue
            if mode == 'segmen' and len(sk) >= 6 and float(np.ptp(T.hd)) > math.radians(15):          # vein melengkung: dua solid dengan arah penampang sendiri, saling berbagi pagar tengah
                h = len(sk) // 2; kel = [list(range(0, h + 1)), list(range(h, len(sk)))]
            for gi, idx in enumerate(kel):
                az = bidang(T, [sk[i] for i in idx]); r = math.radians(az); nr = np.array([math.cos(r), -math.sin(r)])
                pag = [{'off': float(np.dot(T.Cs(sk[i]), nr)), 'awal': '%s%02d_' % (T.kode, i + 1), 't': 60.0} for i in idx]
                secs = await E(JS_ICS, {'pagar': pag, 'az': az, 'E': E0, 'N': N0, 'kode': T.kode})
                MIDS += [i['mid'] for s in secs for i in s['ics']]
                secs = [s for s in secs if s['ics']]
                if mode.startswith('ideal'):                 # ideal = irisan vein aktual di pagar bor; idealN = tiap N m
                    if mode != 'ideal':
                        ss = np.arange(sk[idx[0]], sk[idx[-1]] + 0.1, float(mode[5:]))
                    else:
                        ss = [sk[i] for i in idx]
                    STR = []
                    for s in ss:
                        o = float(np.dot(T.Cs(s), nr)); pts = irisan_ideal(akt_b[T.kode], S, az, o)
                        if pts: STR.append({'o': o, 'pts': [[round(x, 3), round(z, 3)] for x, z in pts]})
                else:
                    STR = []; dg = trend([(np.array(i['hw']) + np.array(i['fw'])) / 2 for s in secs for i in s['ics']])
                    for k, s in enumerate(secs):
                        ics = sorted(s['ics'], key=lambda i: -((np.array(i['hw']) + np.array(i['fw'])) / 2)[1])
                        loc = [(np.array(i['hw']) + np.array(i['fw'])) / 2 for j in range(max(0, k - 1), min(len(secs), k + 2)) for i in secs[j]['ics']]
                        d = trend([(np.array(i['hw']) + np.array(i['fw'])) / 2 for i in ics]) if len(ics) >= 3 else (trend(loc) if len(loc) >= 2 else dg)
                        if d is None or abs(d[1]) < 0.3: d = dg if dg is not None else np.array([0.0, -1.0])
                        nrm = np.array([-d[1], d[0]])
                        side = lambda i: (np.array(i['hw']), np.array(i['fw'])) if np.dot(np.array(i['hw']) - np.array(i['fw']), nrm) > 0 else (np.array(i['fw']), np.array(i['hw']))
                        HW = [side(i)[0] for i in ics]; FW = [side(i)[1] for i in ics]
                        m0 = ics[0]['mid']; zt = float(S.topo(m0[0] - E0, m0[1] - N0)) - T.cover
                        nb = [secs[j]['ics'] for j in range(max(0, k - 1), min(len(secs), k + 2))]
                        zb = min(min(i['hw'][1], i['fw'][1]) for L in nb for i in L) - 10 * (-d[1])
                        to_z = lambda q, z, dd: q + dd * ((z - q[1]) / dd[1])
                        th, tf = to_z(HW[0], zt, -d), to_z(FW[0], zt, -d)
                        bh = to_z(HW[-1], zb, d) if HW[-1][1] > zb else HW[-1] + d * 2
                        bf = to_z(FW[-1], zb, d) if FW[-1][1] > zb else FW[-1] + d * 2
                        STR.append({'o': s['off'], 'pts': [[round(float(q[0]), 3), round(float(q[1]), 3)] for q in [th] + HW + [bh, bf] + FW[::-1] + [tf]]})
                # 0.26.0: ujung cabang dekat induk otomatis 'diteruskan' oleh Studio; SAMBUNG_MANUAL=1 = cara lama (string pertemuan disalin masuk ke induk)
                if T.sambung and gi == 0 and STR and os.environ.get('SAMBUNG_MANUAL') == '1':
                    first = min(STR, key=lambda x: abs(x['o'] - float(np.dot(T.Cs(s0), nr))))
                    STR = [{'o': float(np.dot(T.Cs(-8.0), nr)), 'pts': first['pts']}] + STR
                SOL.append({'nm': T.kode + ('' if len(kel) == 1 else '_%d' % (gi + 1)), 'az': az, 'S': STR, 'sambung': bool(T.sambung)})
        rep['solid'] = {x['nm']: {'az_penampang': round(x['az'], 1), 'string': len(x['S'])} for x in SOL}
        if os.environ.get('SIMPAN_SOL'):          # string interpretasi untuk paket demo Studio (web-src-ow/buat_demo_ow.py)
            json.dump({'L': SOL, 'E': E0, 'N': N0}, open(OUT + 'sol_%s_%s.json' % (nama, mode), 'w'))
        await E("""(a)=>{let id=800;for(const x of a.L){MS.L.push({id:id++,nm:x.nm,col:'#d81b60',cap:x.m==='h'?'datar':'titik',capd:x.m==='h'?0:10,den:2.6,on:true,m:x.m||'v',az:x.az,E:a.E,N:a.N,S:x.S,capM:!x.sambung});}
          for(const M of MS.L)__ms.build(M,true);}""", {'L': SOL, 'E': E0, 'N': N0})
        await pg.wait_for_timeout(1000)
        indiv = await E("()=>MS.L.filter(m=>m.id>=800).map(m=>[m.nm,m.res&&Math.round(m.res.vol),m.res&&m.res.open])")
        rep['solid_sendiri'] = {x[0]: {'vol_m3': x[1], 'sisi_terbuka': x[2]} for x in indiv}
        await E("()=>{for(const m of MS.L)if(m.id>800)m.par=800;__ms.build(MS.L.find(m=>m.id===800),true);}")
        for _ in range(160):
            await pg.wait_for_timeout(250); st = await E("()=>MS.L.find(m=>m.id===800).bst||''")
            if st and 'menghitung' not in st: break
        rep['union_status'] = await E("()=>MS.L.find(m=>m.id===800).bst")
        mesh = await E("()=>{const w=WI.find(w=>w.ms===800);return {v:Array.from(w.v),t:Array.from(w.t)}}")
        V = np.array(mesh['v'], float).reshape(-1, 3) - [E0, N0, 0]; Tt = np.array(mesh['t'], int).reshape(-1, 3)
        model = trimesh.Trimesh(V, Tt, process=True)
        rep['union'] = {'vol_m3': round(float(model.volume), 1), 'tertutup': bool(model.is_watertight), 'bagian': len(model.split(only_watertight=False))}
        rep['aktual'] = {'vol_m3': round(float(aktual.volume), 1), 'bagian': G['bagian_union']}
        ka = ke_mf(aktual); km = ke_mf(model); vi = (ka ^ km).volume()
        rep['recall_%'] = round(100 * vi / aktual.volume, 1); rep['presisi_%'] = round(100 * vi / model.volume, 1)
        # rincian per tubuh & zona: titik acak seragam di dalam tiap tubuh (bentuk parametrik)
        rng = np.random.default_rng(5); zona = {}
        cont = lambda M, Q: np.concatenate([M.contains(Q[i:i + 500]) for i in range(0, len(Q), 500)])
        for T in S.B:
            n = 3000; s = rng.uniform(-T.ext0 if T.ext0 else 0, T.L * 0.985, n * 4); v = rng.uniform(0, 1, n * 4); w = rng.uniform(-0.5, 0.5, n * 4)
            wt = T.tebal(s, v) * T.tinggi(s); keep = rng.uniform(0, wt.max(), len(wt)) < wt
            s, v, w = s[keep][:n], v[keep][:n], w[keep][:n]
            zt = T.ztop(s); z = zt - v * T.tinggi(s); geser = (zt - z) / math.tan(math.radians(T.dip))
            XY = T.Cs(s) + T.d * geser[:, None] + T.Ns(s) * (T.liuk_off(s) + w * T.tebal(s, v))[:, None]
            inm = cont(model, np.column_stack([XY, z]))
            zona[T.kode] = round(100 * inm.mean(), 1)
            for nm2, a0, a1 in (('awal', -99, T.L / 3), ('tengah', T.L / 3, 2 * T.L / 3), ('akhir', 2 * T.L / 3, 999)):
                k2 = (s >= a0) & (s < a1)
                if k2.sum(): zona['%s_%s' % (T.kode, nm2)] = round(100 * inm[k2].mean(), 1)
            for nm2, v0, v1 in (('atas', 0, .3), ('tengah_v', .3, .7), ('bawah', .7, 1.01)):
                k3 = (v >= v0) & (v < v1)
                if k3.sum(): zona['%s_%s' % (T.kode, nm2)] = round(100 * inm[k3].mean(), 1)
        rep['recall_per_zona_%'] = zona
        mids = np.array(MIDS) - [E0, N0, 0]
        rep['intercept_dalam_solid'] = '%d/%d' % (cont(model, mids).sum(), len(mids)) if len(mids) else '0/0'
        nonv = await E("""()=>{const GA=geoActive(),M=activeHoles(),out=[];for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);for(const x of iv){const v=String(x.v.Vein_Type||'').trim();if(v&&v!=='-')continue;const d=(x.f+x.t)/2;for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]){const f=(d-cum[i])/(cum[i+1]-cum[i]);out.push([(h.p[i*3]+(h.p[i*3+3]-h.p[i*3])*f)/10+O[0],(h.p[i*3+1]+(h.p[i*3+4]-h.p[i*3+1])*f)/10+O[1],(h.p[i*3+2]+(h.p[i*3+5]-h.p[i*3+2])*f)/10+O[2]]);break;}}}return out;}""")
        nonv = np.array(nonv) - [E0, N0, 0]; lo, hi = model.bounds[0] - 2, model.bounds[1] + 2
        near = nonv[np.all((nonv >= lo) & (nonv <= hi), 1)]
        rep['sampel_nonvein_dalam_solid'] = '%d/%d' % (cont(model, near).sum() if len(near) else 0, len(nonv))
        rep['galat_js'] = errs
        tag = '%s_%s%s' % (nama, mode, '_jogh' if os.environ.get('JOG_H') == '1' else '')
        json.dump(rep, open(OUT + 'uji_%s.json' % tag, 'w'), ensure_ascii=False, indent=1)
        # gambar: model + aktual (bayangan)
        await pg.set_input_files('#wif', B + 'aktual_vein.obj'); await pg.wait_for_timeout(2500)
        await E("""()=>{const w=WI.find(w=>!w.ms);if(w){const r=[...document.querySelectorAll('#wil .dsr')][WI.indexOf(w)];const c=r&&r.querySelector('.w-c'),o=r&&r.querySelector('.w-op');if(c){c.value='#9aa3ad';c.dispatchEvent(new Event('input',{bubbles:true}));c.dispatchEvent(new Event('change',{bubbles:true}));}if(o){o.value=0.25;o.dispatchEvent(new Event('input',{bubbles:true}));}}
          if(window.__pr)__pr.show(false);if(window.__pt)__pt.show(false);const s=document.querySelector('#sfl .s-on');if(s&&s.checked)s.click();for(const k of ['pdh','gc'])if(L[k])L[k].visible=false;}""")
        await pg.wait_for_timeout(800)
        await E("()=>view('plan')"); await pg.wait_for_timeout(1200); await pg.screenshot(path=OUT + 'uji_%s_plan.png' % tag)
        await E("()=>view('sse')"); await pg.wait_for_timeout(1200); await pg.screenshot(path=OUT + 'uji_%s_3d.png' % tag)
        await b.close()
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep


if __name__ == '__main__':
    if len(sys.argv) < 4: raise SystemExit(__doc__)
    if sys.argv[1] == 'buat': buat(sys.argv[2], sys.argv[3])
    else: asyncio.run(uji(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'bor'))
