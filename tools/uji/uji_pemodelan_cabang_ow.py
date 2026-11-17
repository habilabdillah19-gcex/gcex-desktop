# -*- coding: utf-8 -*-
"""Simulasi: vein V1 bercabang tiga ke bawah (V1A barat-landai, V1B tengah-tegak, V1C timur-berlawanan).
Data fiktif /tmp/br (gen.py). Geologis-simulasi mendigit string per kode vein di tiap penampang E-W (spasi 10 m),
lalu cabang dijadikan 'Cabang dari' V1 -> boolean union. Diuji: satu tubuh tertutup, intercept di dalam, non-vein di luar,
kecocokan penampang dengan geometri sebenarnya (presisi / recall), tanpa puntiran per cabang."""
import asyncio, json, math, numpy as np
from playwright.async_api import async_playwright
import pathlib
REPO = pathlib.Path(__file__).resolve().parents[2]
APP = (REPO / 'app-ow' / 'index.html').as_uri()
import sys
B = (sys.argv[1] if len(sys.argv) > 1 else '/tmp/br').rstrip('/') + '/'; OUT = str(pathlib.Path.cwd()) + '/'
G = json.load(open(B + 'geom.json'))
def xc(code, z):
    ZT, ZS = G['ZT'], G['ZS']
    if code == 'V1': return -(ZT - z) / math.tan(math.radians(75))
    x0 = -(ZT - ZS) / math.tan(math.radians(75)); dz = ZS - z
    return {'V1A': x0 - dz / math.tan(math.radians(60)), 'V1B': x0 - dz / math.tan(math.radians(80)), 'V1C': x0 + dz / math.tan(math.radians(65))}[code]
def true_code(x, z, n):
    w = 1 + 0.15 * math.sin(n / 25.0)
    if G['ZS'] <= z <= G['ZT'] and abs(x - xc('V1', z)) <= G['TH']['V1'] * w / 2: return True
    if G['ZB'] <= z < G['ZS']:
        return any(abs(x - xc(c, z)) <= G['TH'][c] * w / 2 for c in ('V1A', 'V1B', 'V1C'))
    return False

JS_ICS = r"""(a)=>{const {offs,t}=a,GA=geoActive(),M=activeHoles(),out=[];const az=90,r=az*Math.PI/180,u=[Math.sin(r),Math.cos(r)],nr=[Math.cos(r),-Math.sin(r)];
 const posAt=(p,cum,d)=>{for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]||i+2===cum.length){const f=cum[i+1]>cum[i]?Math.min(1,Math.max(0,(d-cum[i])/(cum[i+1]-cum[i]))):0;return [(p[i*3]+(p[i*3+3]-p[i*3])*f)/10+O[0],(p[i*3+1]+(p[i*3+4]-p[i*3+1])*f)/10+O[1],(p[i*3+2]+(p[i*3+5]-p[i*3+2])*f)/10+O[2]];}};
 for(const off of offs){const q={m:'v',E:a.E,N:a.N,az:r,azd:az,off,len:0,t,u,nr},ics=[];
  for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);let cur=null;const sg=[];
   for(const x of iv.slice().sort((p,q)=>p.f-q.f)){const v=String(x.v.Vein_Type||'').trim();if(v&&v!=='-'){if(cur&&cur.c===v&&Math.abs(cur.t-x.f)<1e-6)cur.t=x.t;else{cur={c:v,f:x.f,t:x.t};sg.push(cur);}}else cur=null;}
   for(const s of sg){const A=posAt(h.p,cum,s.f),Bp=posAt(h.p,cum,s.t),mid=posAt(h.p,cum,(s.f+s.t)/2);if(Math.abs(scDist(q,...mid))>t)continue;ics.push({c:s.c,id,hw:scProj(q,...A),fw:scProj(q,...Bp),mid,cz:h.p[2]/10+O[2]});}}
  out.push({off,ics});}return out;}"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1536, 'height': 864}); E = pg.evaluate; errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300])); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto(APP); await pg.wait_for_timeout(2500)
        for k, f in [('collar', 'BR_collar.csv'), ('survey', 'BR_survey.csv'), ('assay', 'BR_assay.csv'), ('geo', 'BR_geologi.csv')]:
            await pg.set_input_files('#dsf-' + k, B + f)
        await pg.wait_for_timeout(1500); await E("()=>document.getElementById('dsgo').click()"); await pg.wait_for_timeout(3500)
        E0, N0 = G['E0'], G['N0']; offs = [float(-n) for n in range(0, 121, 10)]  # az 90: normal = (0,-1) -> geser = -(N-N0)
        secs = await E(JS_ICS, {'offs': offs, 't': 5, 'E': E0, 'N': N0})
        codes = ['V1', 'V1A', 'V1B', 'V1C']
        allm = {c: np.array([i['mid'] for s in secs for i in s['ics'] if i['c'] == c]) for c in codes}
        print('intercept per kode:', {c: len(allm[c]) for c in codes})
        # arah jejak tiap kode di penampang (x = jarak sepanjang garis E, z = RL)
        tr = {}
        for c in codes:
            P = np.array([((np.array(i['hw']) + np.array(i['fw'])) / 2) for s in secs for i in s['ics'] if i['c'] == c]); cm = P.mean(0)
            _, _, vt = np.linalg.svd(P - cm); d = vt[0]; d = d if d[1] < 0 else -d; tr[c] = d
        zt_min = min(i['mid'][2] for s in secs for i in s['ics'] if i['c'] == 'V1'); zb_max = max(i['mid'][2] for s in secs for i in s['ics'] if i['c'] != 'V1')
        zsp = (zt_min + zb_max) / 2; print('RL percabangan (taksiran dari data): %.1f (sebenarnya %.1f)' % (zsp, G['ZS']))
        to_z = lambda p, z, d: p + d * ((z - p[1]) / d[1])
        S = {c: [] for c in codes}
        for c in codes:
            L2 = [(s['off'], sorted([i for i in s['ics'] if i['c'] == c], key=lambda i: -((np.array(i['hw']) + np.array(i['fw'])) / 2)[1])) for s in secs]
            L2 = [(o, ic) for o, ic in L2 if ic]
            for k, (o, ics) in enumerate(L2):
                d = tr[c]; HW = [np.array(i['hw']) for i in ics]; FW = [np.array(i['fw']) for i in ics]
                if c == 'V1': ztop = max(i['cz'] for i in ics); zbot = zsp - 4
                else:
                    ztop = zsp + 4
                    zbot = min(min(i['hw'][1], i['fw'][1]) for j in range(max(0, k - 1), min(len(L2), k + 2)) for i in L2[j][1]) - 10 * (-d[1])
                th, tf = to_z(HW[0], ztop, -d), to_z(FW[0], ztop, -d)
                bh = to_z(HW[-1], zbot, d) if HW[-1][1] > zbot else HW[-1] + d * 2; bf = to_z(FW[-1], zbot, d) if FW[-1][1] > zbot else FW[-1] + d * 2
                pts = [th] + HW + [bh, bf] + FW[::-1] + [tf]
                S[c].append({'o': o, 'pts': [[round(float(q[0]), 3), round(float(q[1]), 3)] for q in pts]})
        print('string per kode:', {c: len(S[c]) for c in codes})
        cols = {'V1': '#d81b60', 'V1A': '#1e88e5', 'V1B': '#43a047', 'V1C': '#fb8c00'}
        await E("""(a)=>{let id=600;for(const c of a.codes){const M={id:id++,nm:c,col:a.cols[c],cap:'titik',capd:0,den:2.6,on:true,m:'v',az:90,E:a.E,N:a.N,S:a.S[c]};MS.L.push(M);}
          for(const M of MS.L)__ms.build(M,true);}""", {'codes': codes, 'cols': cols, 'E': E0, 'N': N0, 'S': S})
        await pg.wait_for_timeout(800)
        indiv = await E("()=>MS.L.filter(m=>m.id>=600).map(m=>[m.nm,m.res&&Math.round(m.res.vol),m.res&&m.res.open,m.res&&m.res.nm])"); print('solid sendiri-sendiri:', indiv)
        # mesh tiap solid sebelum union (untuk uji puntiran per cabang)
        pre = await E("()=>MS.L.filter(m=>m.id>=600).map(m=>{const R=__ms.solid(m);return {nm:m.nm,v:Array.from(R.v),t:Array.from(R.t)}})")
        await E("()=>{for(const m of MS.L)if(m.id>600)m.par=600;__ms.build(MS.L.find(m=>m.id===600),true);}")
        for k in range(80):
            await pg.wait_for_timeout(250); st = await E("()=>MS.L.find(m=>m.id===600).bst||''")
            if st and 'menghitung' not in st: break
        res = await E("()=>{const M=MS.L.find(m=>m.id===600);return [M.bst,M.res,WI.filter(w=>w.ms).map(w=>w.nm)]}"); print('union:', res)
        mesh = await E("()=>{const w=WI.find(w=>w.ms===600);return {v:Array.from(w.v),t:Array.from(w.t)}}")
        V = np.array(mesh['v']).reshape(-1, 3); T = np.array(mesh['t']).reshape(-1, 3)
        # tertutup / manifold sisi
        from collections import Counter
        ec = Counter(); [ec.update([tuple(sorted((t[e], t[(e + 1) % 3]))) for e in range(3)]) for t in T]
        rep = {'segitiga_union': len(T), 'sisi_bukan_2_segitiga': sum(1 for v in ec.values() if v != 2), 'tubuh': res[1].get('nb'), 'vol_union_m3': round(res[1]['vol'], 1),
               'jumlah_vol_sendiri_m3': sum(x[1] for x in indiv)}
        # point-in-mesh vektor
        def inside_many(P):
            P = np.asarray(P, float); a = V[T[:, 0]]; e1 = V[T[:, 1]] - a; e2 = V[T[:, 2]] - a; votes = np.zeros(len(P), int)
            for dv in (np.array([0.31, 0.52, 0.79]), np.array([-0.6, 0.2, 0.77]), np.array([0.1, -0.9, 0.42])):
                h = np.cross(dv, e2); det = (e1 * h).sum(1); ok = np.abs(det) > 1e-12; f = np.where(ok, 1 / np.where(ok, det, 1), 0); cnt = np.zeros(len(P), int)
                for i0 in range(0, len(P), 2000):
                    Pp = P[i0:i0 + 2000]; s = Pp[:, None, :] - a[None]; u = f * (s * h[None]).sum(2); q = np.cross(s, e1[None]); v = f * (q * dv).sum(2); tt = f * (q * e2[None]).sum(2)
                    hit = ok & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (tt > 1e-9); cnt[i0:i0 + 2000] = hit.sum(1)
                votes += cnt % 2
            return votes >= 2
        mids = {c: [i['mid'] for s in secs for i in s['ics'] if i['c'] == c] for c in codes}
        rep['intercept_dalam_solid'] = {c: '%d/%d' % (inside_many(mids[c]).sum(), len(mids[c])) for c in codes}
        # recall / presisi pada dua bidang: tepat di penampang (N+60) dan di tengah antar-penampang (N+55)
        for nn in (60.0, 55.0):
            xs = np.arange(-160, 90, 0.5); zs = np.arange(40, 206, 0.5); X, Z = np.meshgrid(xs, zs)
            P = np.stack([E0 + X.ravel(), np.full(X.size, N0 + nn), Z.ravel()], 1)
            zl = V[:, 2].min()
            tru = np.array([true_code(x, z, nn) for x, z in zip(X.ravel(), Z.ravel())])
            sel = (P[:, 2] >= zl)  # hanya rentang RL yang dimodelkan
            ins = inside_many(P[sel | tru])
            tsel = tru[sel | tru]; zz = P[sel | tru][:, 2]; inr = zz >= zl
            tp = (ins & tsel & inr).sum(); rec = tp / max(1, (tsel & inr).sum()); prec = tp / max(1, ins.sum())
            band = {}
            for nmb, z0, z1 in (('atas_cabang', G['ZS'], 206), ('cabang_RL100-150', 100, G['ZS']), ('cabang_bawah_RL100', zl, 100)):
                m_ = tsel & inr & (zz >= z0) & (zz < z1); band[nmb] = round(100 * (ins & m_).sum() / max(1, m_.sum()), 1)
            rep['penampang_N+%d' % nn] = {'recall_vein_%': round(100 * rec, 1), 'presisi_%': round(100 * prec, 1), 'recall_per_RL_%': band, 'RL_terdalam_solid': round(float(zl), 1)}
        # puntiran per cabang (sebelum union): sisi antar-penampang menghubungkan kontak HW ke FW di tengah string
        tw = {}
        for m in pre:
            Vm = np.array(m['v']).reshape(-1, 3); Tm = np.array(m['t']).reshape(-1, 3); role = {}
            for st in S[m['nm']]:
                k2 = len(st['pts']) // 2
                for j, (a2, z2) in enumerate(st['pts']):
                    w = np.array([E0 + a2, N0 - st['o'], z2]); role[tuple(np.round(w, 2))] = ('HW' if j < k2 else 'FW', j in (0, k2 - 1, k2, len(st['pts']) - 1))
            rv = [role.get(tuple(np.round(v, 2)), (None, True)) for v in Vm]; cr = 0
            for t in Tm:
                for e in range(3):
                    i0, i1 = t[e], t[(e + 1) % 3]
                    if i0 < i1 and abs(Vm[i1][1] - Vm[i0][1]) > 5 and rv[i0][0] and rv[i1][0] and rv[i0][0] != rv[i1][0] and not (rv[i0][1] or rv[i1][1]): cr += 1
            tw[m['nm']] = cr
        rep['puntiran_HW_ke_FW_per_solid'] = tw
        # sampel non-vein di dalam solid
        nonv = await E("""()=>{const GA=geoActive(),M=activeHoles(),out=[];for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);for(const x of iv){const v=String(x.v.Vein_Type||'').trim();if(v&&v!=='-')continue;const d=(x.f+x.t)/2;for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]){const f=(d-cum[i])/(cum[i+1]-cum[i]);out.push([(h.p[i*3]+(h.p[i*3+3]-h.p[i*3])*f)/10+O[0],(h.p[i*3+1]+(h.p[i*3+4]-h.p[i*3+1])*f)/10+O[1],(h.p[i*3+2]+(h.p[i*3+5]-h.p[i*3+2])*f)/10+O[2]]);break;}}}return out;}""")
        lo, hi = V.min(0) - 2, V.max(0) + 2; near = [q for q in nonv if all(lo[k] <= q[k] <= hi[k] for k in range(3))]
        rep['sampel_nonvein_dalam_solid'] = '%d/%d' % (inside_many(near).sum(), len(near))
        print(json.dumps(rep, indent=1, ensure_ascii=False)); json.dump(rep, open(OUT + 'sim_cabang.json', 'w'), ensure_ascii=False)
        # gambar: penampang tengah + 3D
        await E("""()=>{const g=id=>document.getElementById(id);g('scm').value='v';g('sca').value=90;g('sce').value=50000;g('scn').value=80000;g('sco').value=-60;g('sct').value=5;g('scs').value=10;SC.v=null;scUpd();g('sc2d').click();}""")
        await pg.wait_for_timeout(1500); await E("()=>{const s=document.getElementById('msbsel');s.value='600';s.dispatchEvent(new Event('change'));const c=document.getElementById('lgk');c.checked=false;c.dispatchEvent(new Event('change'));SC.v={m:'v',cx:-35,cy:125,s:3.4};scDraw();}"); await pg.wait_for_timeout(700)
        await pg.screenshot(path=OUT + 'cabang_pen.png')
        await E("()=>document.getElementById('scx').click()")
        await E("()=>{for(const k of ['pdh','gc'])if(L[k])L[k].visible=false;const b=[...document.querySelectorAll('button')].find(b=>b.title==='Zoom ke semua data');b&&b.click();const c=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='NNW');c&&c.click()}"); await pg.wait_for_timeout(1200)
        await E("()=>{document.getElementById('wie').checked=true;document.getElementById('wie').dispatchEvent(new Event('change'));}"); await pg.wait_for_timeout(800)
        await pg.screenshot(path=OUT + 'cabang_3d.png')
        await E("()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Oblik');b&&b.click()}"); await pg.wait_for_timeout(800)
        await pg.screenshot(path=OUT + 'cabang_3d_oblik.png')
        print('errs', errs); await b.close()
asyncio.run(main())
