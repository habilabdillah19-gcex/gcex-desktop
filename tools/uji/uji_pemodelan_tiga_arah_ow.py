# -*- coding: utf-8 -*-
"""Uji pemodelan eksplisit Ore Works pada data Vein Tiga Arah (pemilik 19 Nov 2026: "Laksanakan").

"Geologis simulasi" memodelkan tiap lengan (VA, VB, VC) di Studio Pemodelan dengan penampang tegak lurus jurus
lengan itu (penampang = garis bor, spasi 20 m, plus penampang pertemuan s = 3 m):
  - string per penampang: kontak sisi atap dari atas ke bawah lalu kontak sisi alas dari bawah ke atas (dipisah per
    sisi jejak vein, bukan per From/To lubang);
  - diteruskan ke atas searah jejak sampai topografi − 2 m, ke bawah sampai intercept terdalam penampang itu &
    tetangganya + ½ spasi (10 m);
  - ujung solid "titik" ½ spasi melewati penampang terakhir (ke ujung lengan & melewati pertemuan → saling menumpang);
  - VB & VC = Cabang dari VA → boolean union jadi satu tubuh.
Hasil dibandingkan dengan wireframe AKTUAL (VT_aktual_vein.obj): volume, tumpang tindih (recall / presisi) per lengan,
per zona jarak dari pertemuan, per kedalaman; satu tubuh tertutup; intercept di dalam; sampel non-vein di luar.
Pakai: python tools/uji/uji_pemodelan_tiga_arah_ow.py [folder data] (bawaan docs/tutorial-ow/data/Vein_Tiga_Arah)
Perlu: playwright + chromium, numpy, trimesh, rtree, manifold3d.
"""
import asyncio, json, math, sys, pathlib, runpy, tempfile, os
import numpy as np, trimesh, manifold3d as mf
from playwright.async_api import async_playwright

REPO = pathlib.Path(__file__).resolve().parents[2]
APP = (REPO / 'app-ow' / 'index.html').as_uri()
B = (sys.argv[1] if len(sys.argv) > 1 else str(REPO / 'docs/tutorial-ow/data/Vein_Tiga_Arah')).rstrip('/') + '/'
OUT = str(pathlib.Path.cwd()) + '/'
# geometri sebenarnya: jalankan pembuat data ke folder sementara (deterministik) untuk mendapat fungsi kebenarannya
_tmp = tempfile.mkdtemp()
_argv = sys.argv
sys.argv = ['x', _tmp]
with open(os.devnull, 'w') as _dn:
    _so = sys.stdout; sys.stdout = _dn
    try:
        GEN = runpy.run_path(str(REPO / 'tools/uji/buat_data_vein_tiga_arah_ow.py'), run_name='gen')
    finally:
        sys.stdout = _so
sys.argv = _argv
ARMS, kode_di, topo, ztop, tinggi = GEN['ARMS'], GEN['kode_di'], GEN['topo'], GEN['ztop'], GEN['tinggi']
E0, N0 = GEN['E0'], GEN['N0']
# pilihan interpretasi (lihat catatan temuan): hanya lubang di penampang lengan itu; ujung titik ½ spasi (10 m) di kedua ujung
HANYA_LUBANG_PENAMPANG = os.environ.get('VT_SEMUA_LUBANG') != '1'
CAPD = float(os.environ.get('VT_CAPD', '10'))
MODE = os.environ.get('VT_MODE', 'bor')          # 'bor' = interpretasi dari intercept; 'ideal' = string dari penampang sebenarnya
SPASI = float(os.environ.get('VT_SPASI', '0'))
SAMBUNG = os.environ.get('VT_SAMBUNG') == '1'   # salin string pertemuan ke s = −8 m     # mode ideal: 0 = posisi penampang bor; >0 = spasi lain

def dalam_v(A, s, z, q):
    """Versi tervektor fungsi kebenaran pembuat data: titik (s sepanjang jurus, z, q sepanjang normal) di dalam lengan A?"""
    sp = np.maximum(s, 0.0); p = A['u'][None, :] * sp[:, None]
    zt = 214.0 + 0.025 * p[:, 0] - 0.015 * p[:, 1] + 5.0 * np.exp(-(p[:, 0] ** 2 + p[:, 1] ** 2) / (2 * 110.0 ** 2)) - 2.0
    r = np.minimum(sp / A['L'], 0.999); h = 100.0 * (1 - r * r) ** 0.6
    ok = (s >= -12) & (s <= A['L'] * 0.985) & (z <= zt) & (z >= zt - h)
    v = np.clip((zt - z) / h, 0, 1)
    sm = lambda x: (lambda c: c * c * (3 - 2 * c))(np.clip(x, 0, 1))
    off = (zt - z) / math.tan(math.radians(A['dip'])) * sm((s - 8.0) / 52.0) + 1.2 * np.sin(2 * math.pi * s / 55.0 + A['ph']) * sm(s / 10.0)
    ps = 1 + 0.35 * np.sin(2 * math.pi * s / 40.0 + A['ph']) * np.cos(1.5 * math.pi * v + A['ph'] * 0.5)
    tb = np.maximum(0.15, A['t0'] * ps * (1 + 0.8 * np.exp(-sp / 18.0)) * np.sqrt(1 - np.minimum(sp / A['L'], 1) ** 2) * np.sqrt(1 - v ** 3))
    return ok & (np.abs(q - off) <= tb / 2)


JS_ICS = r"""(a)=>{const {offs,t,az}=a,GA=geoActive(),M=activeHoles(),out=[];const r=az*Math.PI/180,u=[Math.sin(r),Math.cos(r)],nr=[Math.cos(r),-Math.sin(r)];
 const posAt=(p,cum,d)=>{for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]||i+2===cum.length){const f=cum[i+1]>cum[i]?Math.min(1,Math.max(0,(d-cum[i])/(cum[i+1]-cum[i]))):0;return [(p[i*3]+(p[i*3+3]-p[i*3])*f)/10+O[0],(p[i*3+1]+(p[i*3+4]-p[i*3+1])*f)/10+O[1],(p[i*3+2]+(p[i*3+5]-p[i*3+2])*f)/10+O[2]];}};
 for(const off of offs){const q={m:'v',E:a.E,N:a.N,az:r,azd:az,off,len:0,t,u,nr},ics=[];
  for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;if(a.awal&&!a.awal.some(p=>String(id).startsWith(p)))continue;const cum=cumP(h.p);let cur=null;const sg=[];
   for(const x of iv.slice().sort((p,q)=>p.f-q.f)){const v=String(x.v.Vein_Type||'').trim();if(v===a.kode){if(cur&&Math.abs(cur.t-x.f)<1e-6)cur.t=x.t;else{cur={f:x.f,t:x.t};sg.push(cur);}}else cur=null;}
   for(const s of sg){const A=posAt(h.p,cum,s.f),Bp=posAt(h.p,cum,s.t),mid=posAt(h.p,cum,(s.f+s.t)/2);if(Math.abs(scDist(q,...mid))>t)continue;ics.push({id,hw:scProj(q,...A),fw:scProj(q,...Bp),mid});}}
  out.push({off,ics});}return out;}"""


def trend(P):
    P = np.asarray(P, float)
    if len(P) < 2:
        return None
    _, _, vt = np.linalg.svd(P - P.mean(0))
    d = vt[0]
    return d if d[1] < 0 else -d


async def main():
    rep = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'], **({'executable_path': '/usr/bin/google-chrome'} if os.path.exists('/usr/bin/google-chrome') else {}))
        pg = await b.new_page(viewport={'width': 1536, 'height': 864}); E = pg.evaluate; errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300])); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto(APP); await pg.wait_for_timeout(2500)
        for k, f in [('collar', 'VT_collar.csv'), ('survey', 'VT_survey.csv'), ('assay', 'VT_assay.csv'), ('geo', 'VT_geologi.csv')]:
            await pg.set_input_files('#dsf-' + k, B + f)
        await pg.wait_for_timeout(1500); await E("()=>document.getElementById('dsgo').click()"); await pg.wait_for_timeout(3500)
        await pg.set_input_files('#sff', B + 'VT_topografi.str'); await pg.wait_for_timeout(2500)
        STR, META, MIDS = {}, {}, {}
        for kode, A in ARMS.items():
            azs = A['dipdir']                                 # garis penampang tegak lurus jurus
            r = math.radians(azs); usec = np.array([math.sin(r), math.cos(r)]); nr = np.array([math.cos(r), -math.sin(r)])
            ss = [3.0] + list(np.arange(10.0, A['L'] - 12.0, 20.0))
            offs = [float(np.dot(A['u'] * s, nr)) for s in ss]   # geser = proyeksi ke normal penampang
            secs = await E(JS_ICS, {'offs': offs, 't': 3.4, 'az': azs, 'E': E0, 'N': N0, 'kode': kode, 'awal': ['VT' + kode[1], 'VTJ_' + kode[1]] if HANYA_LUBANG_PENAMPANG else None})
            secs = [s for s in secs if s['ics']]
            if MODE == 'ideal':                                  # string dari penampang SEBENARNYA (uji mesin loft/union saja)
                sk = ss if SPASI <= 0 else [3.0] + list(np.arange(SPASI, A['L'] - 12.0, SPASI))
                S = []
                for s in sk:
                    sp = max(s, 0.0); zt = ztop(A, sp); h = tinggi(A, sp); vs = np.linspace(0, 1, 21)
                    zz = zt - vs * h; off = [GEN['offset'](A, s, z) for z in zz]; tb = [GEN['tebal'](A, s, v) for v in vs]
                    HWp = [[o + w / 2, z] for o, w, z in zip(off, tb, zz)]; FWp = [[o - w / 2, z] for o, w, z in zip(off, tb, zz)]
                    S.append({'o': float(np.dot(A['u'] * s, nr)), 'pts': [[round(x, 3), round(z, 3)] for x, z in HWp + FWp[::-1]]})
                STR[kode] = S; MIDS[kode] = [i['mid'] for s2 in secs for i in s2['ics']]
                META[kode] = {'az': azs, 'penampang': len(S), 'intercept': len(MIDS[kode]), 'mode': 'ideal'}
                continue
            MIDS[kode] = [i['mid'] for s in secs for i in s['ics']]
            allc = [((np.array(i['hw']) + np.array(i['fw'])) / 2) for s in secs for i in s['ics']]
            dg = trend(allc)
            S = []
            for k, s in enumerate(secs):
                ics = sorted(s['ics'], key=lambda i: -((np.array(i['hw']) + np.array(i['fw'])) / 2)[1])
                # jejak lokal: intercept penampang ini + tetangganya (jejak global salah di pertemuan yang tegak & di ujung lengan)
                loc = [(np.array(i['hw']) + np.array(i['fw'])) / 2 for j in range(max(0, k - 1), min(len(secs), k + 2)) for i in secs[j]['ics']]
                d = trend([(np.array(i['hw']) + np.array(i['fw'])) / 2 for i in ics]) if len(ics) >= 3 else (trend(loc) if len(loc) >= 2 else dg)
                if d is None or abs(d[1]) < 0.5:
                    d = dg
                nrm = np.array([-d[1], d[0]])
                side = lambda i: (np.array(i['hw']), np.array(i['fw'])) if np.dot(np.array(i['hw']) - np.array(i['fw']), nrm) > 0 else (np.array(i['fw']), np.array(i['hw']))
                HW = [side(i)[0] for i in ics]; FW = [side(i)[1] for i in ics]
                # puncak: topografi − 2 m di atas intercept teratas (lokasi dunia dari titik tengahnya)
                m0 = ics[0]['mid']; zt = topo(m0[0] - E0, m0[1] - N0) - 2.0
                nb = [secs[j]['ics'] for j in range(max(0, k - 1), min(len(secs), k + 2))]
                zb = min(min(i['hw'][1], i['fw'][1]) for L in nb for i in L) - 10 * (-d[1])
                to_z = lambda q, z, dd: q + dd * ((z - q[1]) / dd[1])
                th, tf = to_z(HW[0], zt, -d), to_z(FW[0], zt, -d)
                bh = to_z(HW[-1], zb, d) if HW[-1][1] > zb else HW[-1] + d * 2
                bf = to_z(FW[-1], zb, d) if FW[-1][1] > zb else FW[-1] + d * 2
                pts = [th] + HW + [bh, bf] + FW[::-1] + [tf]
                S.append({'o': s['off'], 'pts': [[round(float(q[0]), 3), round(float(q[1]), 3)] for q in pts]})
            STR[kode] = S
            META[kode] = {'az': azs, 'penampang': len(S), 'intercept': len(MIDS[kode])}
        if SAMBUNG:                                              # string pertemuan disalin 11 m ke belakang (s = −8 m): lengan masuk penuh ke tubuh pertemuan
            for kode, A in ARMS.items():
                r = math.radians(A['dipdir']); nr = np.array([math.cos(r), -math.sin(r)]); S0s = sorted(STR[kode], key=lambda s: -s['o'] if np.dot(A['u'], nr) < 0 else s['o'])
                f = S0s[0]; STR[kode] = [{'o': float(np.dot(A['u'] * -8.0, nr)), 'pts': f['pts']}] + S0s
        rep['penampang_per_lengan'] = META
        json.dump(STR, open(OUT + 'string_%s.json' % MODE, 'w'))
        cols = {'VA': '#d81b60', 'VB': '#1e88e5', 'VC': '#43a047'}
        await E("""(a)=>{let id=700;for(const c of ['VA','VB','VC']){const M={id:id++,nm:c,col:a.cols[c],cap:'titik',capd:a.capd,den:2.6,on:true,m:'v',az:a.az[c],E:a.E,N:a.N,S:a.S[c]};MS.L.push(M);}
          for(const M of MS.L)__ms.build(M,true);}""", {'cols': cols, 'E': E0, 'N': N0, 'S': STR, 'capd': CAPD, 'az': {k: ARMS[k]['dipdir'] for k in ARMS}})
        await pg.wait_for_timeout(1000)
        indiv = await E("()=>MS.L.filter(m=>m.id>=700).map(m=>[m.nm,m.res&&Math.round(m.res.vol),m.res&&m.res.open,m.res&&m.res.nt])")
        rep['solid_sendiri'] = {x[0]: {'vol_m3': x[1], 'sisi_terbuka': x[2], 'segitiga': x[3]} for x in indiv}
        pre = await E("()=>MS.L.filter(m=>m.id>=700).map(m=>{const R=__ms.solid(m);return {nm:m.nm,v:Array.from(R.v),t:Array.from(R.t)}})")
        await E("()=>{for(const m of MS.L)if(m.id>700)m.par=700;__ms.build(MS.L.find(m=>m.id===700),true);}")
        for _ in range(120):
            await pg.wait_for_timeout(250); st = await E("()=>MS.L.find(m=>m.id===700).bst||''")
            if st and 'menghitung' not in st:
                break
        res = await E("()=>{const M=MS.L.find(m=>m.id===700);return [M.bst,M.res]}")
        mesh = await E("()=>{const w=WI.find(w=>w.ms===700);return {v:Array.from(w.v),t:Array.from(w.t)}}")
        rep['union_status'] = res[0]; print('tahap: union', res[0], flush=True)
        V = np.array(mesh['v'], float).reshape(-1, 3); T = np.array(mesh['t'], int).reshape(-1, 3)
        model = trimesh.Trimesh(V, T, process=True)
        from collections import Counter
        ec = Counter(); [ec.update([tuple(sorted((t[e], t[(e + 1) % 3]))) for e in range(3)]) for t in model.faces]
        rep['union'] = {'vol_m3': round(float(model.volume), 1), 'segitiga': int(len(model.faces)), 'tertutup': bool(model.is_watertight),
                        'sisi_bukan_2_segitiga': sum(1 for v in ec.values() if v != 2), 'tubuh': len(model.split(only_watertight=False)),
                        'jumlah_vol_sendiri_m3': sum(x[1] or 0 for x in indiv)}
        aktual = trimesh.load(B + 'VT_aktual_vein.obj', process=True)
        rep['aktual_vol_m3'] = round(float(aktual.volume), 1)
        # tumpang tindih tepat (boolean manifold)
        try:
            ka = mf.Manifold(mf.Mesh(vert_properties=np.asarray(aktual.vertices, np.float32), tri_verts=np.asarray(aktual.faces, np.uint32)))
            km = mf.Manifold(mf.Mesh(vert_properties=np.asarray(model.vertices, np.float32), tri_verts=np.asarray(model.faces, np.uint32)))
            vi = (ka ^ km).volume()
            rep['tumpang_tindih'] = {'irisan_m3': round(vi, 1), 'recall_%': round(100 * vi / aktual.volume, 1), 'presisi_%': round(100 * vi / model.volume, 1),
                                     'status_manifold_model': str(km.status())}
        except Exception as ex:
            rep['tumpang_tindih'] = {'galat': str(ex)[:200]}
        # rincian per lengan / zona: titik acak seragam DI DALAM vein aktual (fungsi kebenaran tervektor) → % yang
        # tertangkap model; bagian model di luar aktual dipecah per komponen (boolean manifold)
        print('tahap: zona', flush=True)
        rng = np.random.default_rng(3); zona = {}; cont = lambda M, Q: np.concatenate([M.contains(Q[i:i + 500]) for i in range(0, len(Q), 500)])
        for kode, A in ARMS.items():
            n0 = 0; PP = []
            while n0 < 6000:
                s = rng.uniform(-12, A['L'], 200000); z = rng.uniform(100, 225, 200000); q = rng.uniform(-45, 45, 200000)
                ok = dalam_v(A, s, z, q); n0 += ok.sum(); PP.append(np.stack([s[ok], z[ok], q[ok]], 1))
            PP = np.concatenate(PP)[:6000]; s, z, q = PP.T
            XY = np.array([E0, N0]) + np.outer(s, A['u']) + np.outer(q, A['n']); W = np.column_stack([XY, z])
            inm = cont(model, W)
            zona['%s_semua' % kode] = round(100 * inm.mean(), 1)
            for nm, s0, s1 in (('pertemuan_s<15m', -99, 15), ('tengah', 15, A['L'] * 0.6), ('ujung', A['L'] * 0.6, 999)):
                k2 = (s >= s0) & (s < s1)
                if k2.sum(): zona['%s_%s' % (kode, nm)] = round(100 * inm[k2].mean(), 1)
            sp = np.maximum(s, 0); zt = np.array([ztop(A, x) for x in sp]); hh = np.array([tinggi(A, x) for x in sp]); v = (zt - z) / hh
            for nm, v0, v1 in (('atas_0-30%', 0, .3), ('tengah_30-70%', .3, .7), ('bawah_70-100%', .7, 1.01)):
                k3 = (v >= v0) & (v < v1)
                if k3.sum(): zona['%s_%s' % (kode, nm)] = round(100 * inm[k3].mean(), 1)
        rep['recall_per_zona_%'] = zona
        try:
            lebih = km - ka; kurang = ka - km
            rep['model_di_luar_aktual_m3'] = round(lebih.volume(), 0); rep['aktual_tak_tertangkap_m3'] = round(kurang.volume(), 0)
            rep['komponen_lebih_terbesar'] = [[round(c.volume()), [round(float(x)) for x in np.asarray(c.to_mesh().vert_properties)[:, :3].min(0)], [round(float(x)) for x in np.asarray(c.to_mesh().vert_properties)[:, :3].max(0)]] for c in sorted(lebih.decompose(), key=lambda c: -c.volume())[:4]]
        except Exception as ex:
            rep['selisih_galat'] = str(ex)[:200]
        # pasangan solid sendiri: saling menumpang?
        PM = {m['nm']: mf.Manifold(mf.Mesh(vert_properties=np.array(m['v'], np.float32).reshape(-1, 3), tri_verts=np.array(m['t'], np.uint32).reshape(-1, 3))) for m in pre}
        rep['tumpang_antar_solid_m3'] = {a2 + '∩' + b2: round((PM[a2] ^ PM[b2]).volume(), 1) for a2, b2 in (('VA', 'VB'), ('VA', 'VC'), ('VB', 'VC'))}
        rep['status_solid_sendiri'] = {k: str(v.status()) for k, v in PM.items()}
        # intercept & non-vein
        allm = np.array([q for v in MIDS.values() for q in v])
        rep['intercept_dalam_solid'] = '%d/%d' % (model.contains(allm).sum(), len(allm))
        nonv = await E("""()=>{const GA=geoActive(),M=activeHoles(),out=[];for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);for(const x of iv){const v=String(x.v.Vein_Type||'').trim();if(v&&v!=='-')continue;const d=(x.f+x.t)/2;for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]){const f=(d-cum[i])/(cum[i+1]-cum[i]);out.push([(h.p[i*3]+(h.p[i*3+3]-h.p[i*3])*f)/10+O[0],(h.p[i*3+1]+(h.p[i*3+4]-h.p[i*3+1])*f)/10+O[1],(h.p[i*3+2]+(h.p[i*3+5]-h.p[i*3+2])*f)/10+O[2]]);break;}}}return out;}""")
        nonv = np.array(nonv)
        rep['sampel_nonvein_dalam_solid'] = '%d/%d' % (model.contains(nonv).sum(), len(nonv))
        # puntiran per lengan (sisi segitiga antar-penampang yang menghubungkan kontak atap ke alas di tengah string)
        tw = {}
        for m in pre:
            Vm = np.array(m['v']).reshape(-1, 3); Tm = np.array(m['t']).reshape(-1, 3); A = ARMS[m['nm']]
            r = math.radians(A['dipdir']); usec = np.array([math.sin(r), math.cos(r)]); nr = np.array([math.cos(r), -math.sin(r)]); role = {}
            for st in STR[m['nm']]:
                k2 = len(st['pts']) // 2
                for j, (a2, z2) in enumerate(st['pts']):
                    w = np.array([E0, N0]) + usec * a2 + nr * st['o']
                    role[tuple(np.round([w[0], w[1], z2], 1))] = ('HW' if j < k2 else 'FW', j in (0, k2 - 1, k2, len(st['pts']) - 1))
            rv = [role.get(tuple(np.round(v, 1)), (None, True)) for v in Vm]; cr = 0
            for t in Tm:
                for e in range(3):
                    i0, i1 = t[e], t[(e + 1) % 3]
                    if i0 < i1 and rv[i0][0] and rv[i1][0] and rv[i0][0] != rv[i1][0] and not (rv[i0][1] or rv[i1][1]) and abs(np.dot(Vm[i1][:2] - Vm[i0][:2], A['u'])) > 5:
                        cr += 1
            tw[m['nm']] = cr
        rep['puntiran_atap_ke_alas'] = tw
        print(json.dumps(rep, indent=1, ensure_ascii=False))
        rep['pilihan'] = {'sambung_pertemuan': SAMBUNG, 'mode': MODE, 'spasi_ideal': SPASI, 'hanya_lubang_penampang': HANYA_LUBANG_PENAMPANG, 'capd_m': CAPD}
        json.dump(rep, open(OUT + 'sim_tiga_arah%s%s.json' % ('' if MODE == 'bor' else '_ideal%d' % SPASI, '_sambung' if SAMBUNG else ''), 'w'), ensure_ascii=False, indent=1)
        # gambar: model (warna) + aktual (bayangan), plan & oblik; penampang VA s=50
        await pg.set_input_files('#wif', B + 'VT_aktual_vein.obj'); await pg.wait_for_timeout(2500)
        await E("""()=>{const w=WI.find(w=>!w.ms);if(w){const r=[...document.querySelectorAll('#wil .dsr')][WI.indexOf(w)];const c=r&&r.querySelector('.w-c'),o=r&&r.querySelector('.w-op');if(c){c.value='#9aa3ad';c.dispatchEvent(new Event('input',{bubbles:true}));c.dispatchEvent(new Event('change',{bubbles:true}));}if(o){o.value=0.25;o.dispatchEvent(new Event('input',{bubbles:true}));}}
          if(window.__pr)__pr.show(false);if(window.__pt)__pt.show(false);const s=document.querySelector('#sfl .s-on');if(s&&s.checked)s.click();for(const k of ['pdh','gc'])if(L[k])L[k].visible=false;}""")
        await pg.wait_for_timeout(800)
        await E("()=>view('plan')"); await pg.wait_for_timeout(1200); await pg.screenshot(path=OUT + 'tiga_arah_plan.png')
        await E("()=>view('sse')"); await pg.wait_for_timeout(1200); await pg.screenshot(path=OUT + 'tiga_arah_3d.png')
        await E("()=>{for(const k of ['pdh','gc'])if(L[k])L[k].visible=true;view('wsw')}"); await pg.wait_for_timeout(1200); await pg.screenshot(path=OUT + 'tiga_arah_3d_bor.png')
        print('errs', errs); await b.close()


asyncio.run(main())
