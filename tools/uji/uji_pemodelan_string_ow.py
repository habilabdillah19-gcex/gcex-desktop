# -*- coding: utf-8 -*-
"""Simulasi pemodelan string Ore Works (gaya Micromine) pada data latihan LTH (vein V2001).
Geologis-simulasi: tiap penampang tegak lurus jurus vein, string = kontak HW (atas) intercept QV kiri->kanan lalu
kontak FW kembali kanan->kiri (titik = posisi kontak interval di lubang, persis yang dihasilkan snap). Lalu solid dibangun
dan diuji: tertutup, tanpa swa-potong, tanpa puntiran, volume vs metode luas-ujung, kecocokan dengan wireframe acuan
LTH_V2001.obj, intercept QV di dalam solid, sampel non-QV di luar solid."""
import asyncio, json, sys, math
import numpy as np
from playwright.async_api import async_playwright
import pathlib
REPO = pathlib.Path(__file__).resolve().parents[2]
APP = (REPO / 'app-ow' / 'index.html').as_uri()
D = str(REPO / 'docs' / 'tutorial-ow' / 'data') + '/'
OUT = str(pathlib.Path.cwd()) + '/'

JS_SETUP = r"""()=>{
 const ref=WI.find(w=>/V2001/i.test(w.nm));const V=ref.v;let c=[0,0,0];const n=V.length/3;for(let i=0;i<n;i++){c[0]+=V[i*3];c[1]+=V[i*3+1];c[2]+=V[i*3+2];}c=c.map(x=>x/n);
 // jurus dari sisi atas acuan (titik RL tertinggi)
 const P=[];for(let i=0;i<n;i++)P.push([V[i*3],V[i*3+1],V[i*3+2]]);P.sort((a,b)=>b[2]-a[2]);const t=P.slice(0,4);let best=[0,1],bd=0;for(const a of t)for(const b of t){const d=Math.hypot(a[0]-b[0],a[1]-b[1]);if(d>bd){bd=d;best=[a,b];}}
 const sx=best[1][0]-best[0][0],sy=best[1][1]-best[0][1],strike=((Math.atan2(sx,sy)*180/Math.PI)+360)%180;
 return {c,strike,len:bd};}"""

JS_STRINGS = r"""(a)=>{const {az,E,N,offs,t}=a;const GA=geoActive(),M=activeHoles(),out=[];
 const posAt=(p,cum,d)=>{for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]||i+2===cum.length){const f=cum[i+1]>cum[i]?Math.min(1,Math.max(0,(d-cum[i])/(cum[i+1]-cum[i]))):0;return [(p[i*3]+(p[i*3+3]-p[i*3])*f)/10+O[0],(p[i*3+1]+(p[i*3+4]-p[i*3+1])*f)/10+O[1],(p[i*3+2]+(p[i*3+5]-p[i*3+2])*f)/10+O[2]];}};
 const r=az*Math.PI/180,u=[Math.sin(r),Math.cos(r)],nr=[Math.cos(r),-Math.sin(r)];
 for(const off of offs){const q={m:'v',E,N,az:r,azd:az,off,len:0,t,u,nr};const ics=[];
  for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);
   // gabung interval QV berurutan
   let cur=null;const segs=[];for(const x of iv.slice().sort((p,q)=>p.f-q.f)){const v=String(x.v.Vein_Type||'').trim();const isV=v&&v!=='-';if(isV){if(cur&&Math.abs(cur.t-x.f)<1e-6)cur.t=x.t;else{cur={f:x.f,t:x.t};segs.push(cur);}}else cur=null;}
   for(const s of segs){const A=posAt(h.p,cum,s.f),B=posAt(h.p,cum,s.t),mid=posAt(h.p,cum,(s.f+s.t)/2);if(Math.abs(scDist(q,...mid))>t)continue;
    ics.push({id,hw:scProj(q,...A),fw:scProj(q,...B),f:s.f,t:s.t,mid,cz:h.p[2]/10+O[2]});}}
  out.push({off,ics});}
 return out;}"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1536, 'height': 864}); E = pg.evaluate; errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300])); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto(APP); await pg.wait_for_timeout(2500)
        for k, f in [('collar', 'LTH_collar.csv'), ('survey', 'LTH_survey.csv'), ('assay', 'LTH_assay.csv'), ('geo', 'LTH_geologi.csv')]:
            await pg.set_input_files('#dsf-' + k, D + f)
        await pg.wait_for_timeout(1200); await E("()=>document.getElementById('dsgo').click()"); await pg.wait_for_timeout(3000)
        await pg.set_input_files('#wif', D + 'LTH_V2001.obj'); await pg.wait_for_timeout(1000)
        S = await E(JS_SETUP); print('acuan: pusat', [round(x, 1) for x in S['c']], 'jurus %.1f°' % S['strike'], 'panjang %.0f m' % S['len'])
        az = (S['strike'] + 90) % 360  # garis sayatan = arah kemiringan (tegak lurus jurus)
        E0, N0 = S['c'][0], S['c'][1]
        spacing = 10.0; half = S['len'] / 2 + 25
        offs = [round(k * spacing, 3) for k in range(-int(half // spacing), int(half // spacing) + 1)]
        secs = await E(JS_STRINGS, {'az': az, 'E': E0, 'N': N0, 'offs': offs, 't': spacing / 2})
        # bidang vein dari semua intercept QV (PCA) -> arah jejak vein di penampang (kemiringan semu = sebenarnya, penampang tegak lurus jurus)
        mids = np.array([i['mid'] for s in secs for i in s['ics']]); cm = mids.mean(0); _, _, vt = np.linalg.svd(mids - cm); nv = vt[2]
        if nv[2] < 0: nv = -nv
        r_ = math.radians(az); u3 = np.array([math.sin(r_), math.cos(r_), 0.0]); ns = np.array([math.cos(r_), -math.sin(r_), 0.0])
        dr = np.cross(ns, nv); tr = np.array([dr @ u3, dr[2]]); tr /= np.linalg.norm(tr)
        if tr[1] > 0: tr = -tr  # ke bawah
        dipv = math.degrees(math.atan2(-tr[1], abs(tr[0])))
        print('bidang vein (PCA intercept): kemiringan semu di penampang %.1f°' % dipv)
        # interpretasi geologis yang konsisten antar-penampang (seperti geologis di Micromine):
        #  - ke atas: string diteruskan searah kemiringan sampai permukaan (RL collar lubang di penampang itu);
        #  - ke bawah: semua penampang ditutup pada batas bawah yang sama dengan tetangganya = intercept terdalam di
        #    penampang itu dan kedua tetangganya, lalu diteruskan ½ spasi bor searah kemiringan (10 m).
        S2 = []
        for s in secs:
            if not s['ics']: continue
            ics = sorted(s['ics'], key=lambda i: ((np.array(i['hw']) + np.array(i['fw'])) / 2) @ tr)
            S2.append({'o': s['off'], 'ics': ics, 'ztop': max(i['cz'] for i in ics), 'zdeep': min(min(i['hw'][1], i['fw'][1]) for i in ics)})
        strings = []
        for k, s in enumerate(S2):
            zb = min(S2[j]['zdeep'] for j in range(max(0, k - 1), min(len(S2), k + 2))) - 10.0 * (-tr[1])
            ics = s['ics']; HW = [np.array(i['hw']) for i in ics]; FW = [np.array(i['fw']) for i in ics]
            to_z = lambda p, z, d: p + d * ((z - p[1]) / d[1]) if abs(d[1]) > 1e-6 else p
            up = -tr
            top_h = to_z(HW[0], s['ztop'], up); top_f = to_z(FW[0], s['ztop'], up)
            bot_h = to_z(HW[-1], zb, tr) if HW[-1][1] > zb else HW[-1] + tr * 2; bot_f = to_z(FW[-1], zb, tr) if FW[-1][1] > zb else FW[-1] + tr * 2
            pts = [top_h] + HW + [bot_h, bot_f] + FW[::-1] + [top_f]
            strings.append({'o': s['o'], 'pts': [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in pts], 'n': len(ics), 'ids': [i['id'] for i in ics]})
        print('penampang dengan intercept QV:', len(strings), '·', [(s['o'], s['n']) for s in strings])
        await E("""(a)=>{const M={id:500,nm:'V2001_string',col:'#d81b60',cap:'titik',capd:0,den:2.6,on:true,m:'v',az:a.az,E:a.E,N:a.N,S:a.S.map(s=>({o:s.o,pts:s.pts}))};MS.L.push(M);MS.cur=500;__ms.build(M,true);}""",
                {'az': az, 'E': E0, 'N': N0, 'S': strings})
        await pg.wait_for_timeout(500)
        res = await E("()=>MS.L.find(m=>m.id===500).res"); print('solid:', res)
        mesh = await E("()=>{const w=WI.find(w=>w.ms===500);return {v:Array.from(w.v),t:Array.from(w.t)}}")
        V = np.array(mesh['v']).reshape(-1, 3); T = np.array(mesh['t']).reshape(-1, 3)
        rep = {'n_string': len(strings), 'spasi': spacing, 'nv': len(V), 'nt': len(T), 'tertutup': res['open'] == 0 and res['nm'] == 0}
        # --- swa-potong (segitiga tak bersebelahan) ---
        def tri_seg(p0, p1, a, b, c):
            e1, e2 = b - a, c - a; d = p1 - p0; h = np.cross(d, e2); det = e1 @ h
            if abs(det) < 1e-12: return False
            f = 1 / det; s = p0 - a; u = f * (s @ h)
            if u < 1e-9 or u > 1 - 1e-9: return False
            qv = np.cross(s, e1); v = f * (d @ qv)
            if v < 1e-9 or u + v > 1 - 1e-9: return False
            tt = f * (e2 @ qv); return 1e-9 < tt < 1 - 1e-9
        nx = 0
        for i in range(len(T)):
            for j in range(len(T)):
                if i == j or set(T[i]) & set(T[j]): continue
                A = V[T[j]]
                for e in range(3):
                    if tri_seg(V[T[i][e]], V[T[i][(e + 1) % 3]], *A): nx += 1; break
        rep['swa_potong'] = nx
        # --- puntiran: sudut sisi penghubung terhadap normal penampang ---
        r = math.radians(az); nr = np.array([math.cos(r), -math.sin(r), 0.0]); ang = []; rat = []
        for t in T:
            for e in range(3):
                a, bb = V[t[e]], V[t[(e + 1) % 3]]; d = bb - a; dn = abs(d @ nr)
                if dn > spacing * 0.5:  # sisi antar-penampang
                    lat = np.linalg.norm(d - (d @ nr) * nr); ang.append(math.degrees(math.atan2(lat, dn))); rat.append(np.linalg.norm(d) / dn)
        ang = np.array(ang); rep['sudut_penghubung_p50'] = round(float(np.median(ang)), 1); rep['sudut_penghubung_p95'] = round(float(np.percentile(ang, 95)), 1); rep['sudut_penghubung_maks'] = round(float(ang.max()), 1)
        # --- puntiran: sisi penghubung (antar-penampang) yang menghubungkan titik kontak HW ke titik kontak FW ---
        role = {}
        for st in strings:
            k = len(st['pts']) // 2
            for j, (a2, z2) in enumerate(st['pts']):
                w = np.array([E0, N0, 0.0]) + nr * st['o'] + u3 * a2; w[2] = z2
                role[tuple(np.round(w, 2))] = ('HW' if j < k else 'FW', j in (0, k - 1, k, len(st['pts']) - 1))
        rv_ = [role.get(tuple(np.round(v, 2)), (None, True)) for v in V]
        cross_ = 0; cross_tip = 0; lat = 0
        for t in T:
            for e in range(3):
                i0, i1 = t[e], t[(e + 1) % 3]; d = V[i1] - V[i0]
                if abs(d @ nr) > spacing * 0.5 and i0 < i1:
                    lat += 1; r0, r1 = rv_[i0], rv_[i1]
                    if r0[0] and r1[0] and r0[0] != r1[0]:
                        if r0[1] or r1[1]: cross_tip += 1
                        else: cross_ += 1
        rep['sisi_penghubung'] = lat; rep['penghubung_HW_ke_FW_di_tengah (puntiran)'] = cross_; rep['penghubung_HW_ke_FW_di_ujung (wajar)'] = cross_tip
        # --- volume prismoidal (Simpson) dari potongan solid di tengah antar-penampang: harus sama dengan volume mesh ---
        def sec_area(o):
            # luas penampang solid pada bidang (p - P0)·nr = o, P0 = pusat model
            P0 = np.array([E0, N0, 0.0]); dist = (V - P0) @ nr - o; A2 = 0.0
            for t in T:
                dd = dist[t]
                if (dd > 0).all() or (dd < 0).all(): continue
                P = []
                for e in range(3):
                    a1, b1 = t[e], t[(e + 1) % 3]
                    if (dist[a1] > 0) != (dist[b1] > 0): f = dist[a1] / (dist[a1] - dist[b1]); P.append(V[a1] + (V[b1] - V[a1]) * f)
                if len(P) != 2: continue
                ntri = np.cross(V[t[1]] - V[t[0]], V[t[2]] - V[t[0]]); dvec = np.cross(ntri, nr); p0, p1 = (P[0], P[1]) if (P[1] - P[0]) @ dvec > 0 else (P[1], P[0])
                A2 += 0.5 * (np.cross(p0 - P0, p1 - P0) @ nr)
            return abs(A2)
        # --- volume metode luas-ujung (end-area) + piramida ujung ---
        def area(P):
            P = np.array(P); return 0.5 * abs(np.dot(P[:, 0], np.roll(P[:, 1], -1)) - np.dot(P[:, 1], np.roll(P[:, 0], -1)))
        Ss = sorted(strings, key=lambda s: s['o']); A_ = [area(s['pts']) for s in Ss]; ve = 0
        for k in range(len(Ss) - 1): ve += (A_[k] + A_[k + 1]) / 2 * (Ss[k + 1]['o'] - Ss[k]['o'])
        d0 = (Ss[1]['o'] - Ss[0]['o']) / 2 if len(Ss) > 1 else 5; d1 = (Ss[-1]['o'] - Ss[-2]['o']) / 2 if len(Ss) > 1 else 5
        ve += A_[0] * d0 / 3 + A_[-1] * d1 / 3
        vs = 0
        for k in range(len(Ss) - 1):
            o0, o1 = Ss[k]['o'], Ss[k + 1]['o']; vs += (o1 - o0) / 6 * (A_[k] + 4 * sec_area((o0 + o1) / 2) + A_[k + 1])
        vs += A_[0] * d0 / 3 + A_[-1] * d1 / 3; rep['vol_prismoidal_simpson'] = round(vs, 1)
        rep['vol_solid'] = round(res['vol'], 1); rep['vol_luas_ujung'] = round(ve, 1); rep['selisih_vs_luas_ujung_%'] = round((res['vol'] - ve) / ve * 100, 2); rep['selisih_vs_simpson_%'] = round((res['vol'] - vs) / vs * 100, 3)
        # --- kecocokan dengan acuan (boolean manifold) ---
        cmp = await E("""async()=>{await MFB.load();const W=MFB.mod,w=WI.find(w=>w.ms===500),r=WI.find(w=>/V2001/i.test(w.nm)),F=x=>({v:x.v,t:x.t,nv:x.v.length/3,nt:x.t.length/3});const A=F(w),B=F(r),c=MFB._pusat([A,B]);
          const a=MFB._keMf(W,A,c),b=MFB._keMf(W,B,c),i=a.intersect(b),u=a.add?null:null;const va=a.volume(),vb=b.volume(),vi=i.volume();[a,b,i].forEach(m=>m.delete());return {va,vb,vi};}""")
        rep['vol_acuan'] = round(cmp['vb'], 1); rep['irisan'] = round(cmp['vi'], 1)
        rep['solid_dalam_acuan_%'] = round(cmp['vi'] / cmp['va'] * 100, 1); rep['acuan_tertutup_%'] = round(cmp['vi'] / cmp['vb'] * 100, 1)
        rep['jaccard'] = round(cmp['vi'] / (cmp['va'] + cmp['vb'] - cmp['vi']), 3)
        # --- intercept QV di dalam solid; sampel non-QV di luar ---
        def inside(pt):
            o = np.array(pt, float); dirs = [np.array([0.31, 0.52, 0.79]), np.array([-0.6, 0.2, 0.77]), np.array([0.1, -0.9, 0.42])]; votes = 0
            for dv in dirs:
                cnt = 0
                for t in T:
                    a, bb, c = V[t]; e1, e2 = bb - a, c - a; h = np.cross(dv, e2); det = e1 @ h
                    if abs(det) < 1e-12: continue
                    f = 1 / det; s = o - a; u = f * (s @ h)
                    if u < 0 or u > 1: continue
                    q = np.cross(s, e1); v = f * (dv @ q)
                    if v < 0 or u + v > 1: continue
                    if f * (e2 @ q) > 1e-9: cnt += 1
                votes += cnt % 2
            return votes >= 2
        allics = [i for s in secs for i in s['ics']]
        rep['intercept_QV_dalam_solid'] = '%d / %d' % (sum(inside(i['mid']) for i in allics), len(allics))
        non = await E("""(a)=>{const GA=geoActive(),M=activeHoles(),out=[];for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);for(const x of iv){const v=String(x.v.Vein_Type||'').trim();if(v&&v!=='-')continue;const d=(x.f+x.t)/2;
          for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]){const f=(d-cum[i])/(cum[i+1]-cum[i]);out.push([(h.p[i*3]+(h.p[i*3+3]-h.p[i*3])*f)/10+O[0],(h.p[i*3+1]+(h.p[i*3+4]-h.p[i*3+1])*f)/10+O[1],(h.p[i*3+2]+(h.p[i*3+5]-h.p[i*3+2])*f)/10+O[2]]);break;}}}return out;}""")
        lo, hi = V.min(0) - 2, V.max(0) + 2
        near = [q for q in non if all(lo[k] <= q[k] <= hi[k] for k in range(3))]
        rep['sampel_nonQV_dalam_solid'] = '%d / %d (di kotak solid)' % (sum(inside(q) for q in near), len(near))
        # --- uji puntiran: titik awal string diputar ---
        tw = await E("""()=>{const M=MS.L.find(m=>m.id===500),S0=JSON.stringify(M.S);M.S.forEach((s,k)=>{const r=(k*3)%s.pts.length;s.pts=s.pts.slice(r).concat(s.pts.slice(0,r));});const R=__ms.solid(M);M.S=JSON.parse(S0);return {vol:R.vol,open:R.open,nm:R.nm};}""")
        rep['uji_titik_awal_diputar'] = {'vol': round(tw['vol'], 1), 'sama_%': round(tw['vol'] / res['vol'] * 100, 2), 'tertutup': tw['open'] == 0 and tw['nm'] == 0}
        rv = await E("""()=>{const M=MS.L.find(m=>m.id===500),S0=JSON.stringify(M.S);M.S.forEach((s,k)=>{if(k%2)s.pts=s.pts.slice().reverse();});const R=__ms.solid(M);M.S=JSON.parse(S0);return {vol:R.vol,open:R.open,nm:R.nm};}""")
        rep['uji_arah_string_dibalik'] = {'vol': round(rv['vol'], 1), 'sama_%': round(rv['vol'] / res['vol'] * 100, 2), 'tertutup': rv['open'] == 0 and rv['nm'] == 0}
        print(json.dumps(rep, indent=1, ensure_ascii=False))
        json.dump({'rep': rep, 'strings': strings, 'az': az}, open(OUT + 'sim_string.json', 'w'), ensure_ascii=False)
        # --- gambar ---
        mid = Ss[len(Ss) // 2]['o']
        await E("""(a)=>{const g=id=>document.getElementById(id);g('scm').value='v';g('sca').value=a.az;g('sce').value=a.E;g('scn').value=a.N;g('sco').value=a.o;g('sct').value=5;g('scs').value=10;SC.v=null;scUpd();g('sc2d').click();}""", {'az': round(az, 3), 'E': E0, 'N': N0, 'o': mid})
        await pg.wait_for_timeout(1200); await pg.screenshot(path=OUT + 'sim_pen.png')
        await E("()=>{document.getElementById('scx').click();}")
        await E("()=>{const r=WI.find(w=>/V2001/i.test(w.nm));r.op=0.25;r.mesh.material.opacity=.25;r.mesh.material.transparent=true;document.getElementById('wie').checked=true;document.getElementById('wie').dispatchEvent(new Event('change'));}")
        await pg.wait_for_timeout(800); await pg.screenshot(path=OUT + 'sim_3d.png')
        print('errs', errs); await b.close()

asyncio.run(main())
