# -*- coding: utf-8 -*-
"""Tangkapan layar tutorial "Membangun vein bercabang tiga" (Ore Works, pemodelan string gaya Micromine).
Data fiktif: docs/tutorial-ow/data/Vein_Cabang (tools/uji/buat_data_vein_cabang_ow.py).
Hasil: /home/claude/tut/shots/vc*.png + /home/claude/tut/sim/vc_hasil.json"""
import asyncio, json, math, sys, numpy as np
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).parent))
from lib import APP, shot, menu, sub
B = str(Path(__file__).resolve().parents[1] / 'data' / 'Vein_Cabang') + '/'
G = json.load(open(B + 'geom.json')); E0, N0 = G['E0'], G['N0']
CODES = ['V1', 'V1A', 'V1B', 'V1C']; COLS = {'V1': '#d81b60', 'V1A': '#1e88e5', 'V1B': '#43a047', 'V1C': '#fb8c00'}
CAM = """([E,N,Z,az,el,d])=>{const t=new THREE.Vector3(E-O[0],(Z-O[2])*W.scale.y,-(N-O[1]));const a=az*Math.PI/180,e=el*Math.PI/180;
 C.position.set(t.x+Math.sin(a)*Math.cos(e)*d,t.y+Math.sin(e)*d,t.z-Math.cos(a)*Math.cos(e)*d);CT.target.copy(t);C.far=Math.max(C.far,d*20);C.updateProjectionMatrix();CT.update();}"""
# intercept per kode vein di tiap penampang E-W (az 90): kontak HW / FW dalam koordinat penampang [jarak, RL]
JS_ICS = r"""(a)=>{const {offs,t}=a,GA=geoActive(),M=activeHoles(),out=[];const az=90,r=az*Math.PI/180,u=[Math.sin(r),Math.cos(r)],nr=[Math.cos(r),-Math.sin(r)];
 const posAt=(p,cum,d)=>{for(let i=0;i+1<cum.length;i++)if(d<=cum[i+1]||i+2===cum.length){const f=cum[i+1]>cum[i]?Math.min(1,Math.max(0,(d-cum[i])/(cum[i+1]-cum[i]))):0;return [(p[i*3]+(p[i*3+3]-p[i*3])*f)/10+O[0],(p[i*3+1]+(p[i*3+4]-p[i*3+1])*f)/10+O[1],(p[i*3+2]+(p[i*3+5]-p[i*3+2])*f)/10+O[2]];}};
 for(const off of offs){const q={m:'v',E:a.E,N:a.N,az:r,azd:az,off,len:0,t,u,nr},ics=[];
  for(const [id,{h}] of M){const iv=GA.get(id);if(!iv)continue;const cum=cumP(h.p);let cur=null;const sg=[];
   for(const x of iv.slice().sort((p,q)=>p.f-q.f)){const v=String(x.v.Vein_Type||'').trim();if(v&&v!=='-'){if(cur&&cur.c===v&&Math.abs(cur.t-x.f)<1e-6)cur.t=x.t;else{cur={c:v,f:x.f,t:x.t};sg.push(cur);}}else cur=null;}
   for(const s of sg){const A=posAt(h.p,cum,s.f),Bp=posAt(h.p,cum,s.t),mid=posAt(h.p,cum,(s.f+s.t)/2);if(Math.abs(scDist(q,...mid))>t)continue;ics.push({c:s.c,id,hw:scProj(q,...A),fw:scProj(q,...Bp),mid,cz:h.p[2]/10+O[2]});}}
  out.push({off,ics});}return out;}"""
PIX = """(p)=>{const cv=document.getElementById('scc'),R=cv.getBoundingClientRect(),V=SC.v,ve=SC.ve||1;return [R.left+R.width/2+20+(p[0]-V.cx)*V.s,R.top+R.height/2-12-(p[1]-V.cy)*V.s*ve];}"""

def strings(secs):
    """Interpretasi geologis yang sama dengan simulasi: arah jejak per kode (PCA), V1 dari permukaan sampai RL percabangan -4 m,
    cabang mulai RL percabangan +4 m (tumpang tindih -> union mulus) sampai intercept terdalam penampang itu & tetangganya -10 m."""
    tr = {}
    for c in CODES:
        P = np.array([(np.array(i['hw']) + np.array(i['fw'])) / 2 for s in secs for i in s['ics'] if i['c'] == c]); cm = P.mean(0)
        d = np.linalg.svd(P - cm)[2][0]; tr[c] = d if d[1] < 0 else -d
    zt = min(i['mid'][2] for s in secs for i in s['ics'] if i['c'] == 'V1'); zb = max(i['mid'][2] for s in secs for i in s['ics'] if i['c'] != 'V1'); zsp = (zt + zb) / 2
    to_z = lambda p, z, d: p + d * ((z - p[1]) / d[1]); S = {c: [] for c in CODES}; EXT = {c: [] for c in CODES}
    for c in CODES:
        L2 = [(s['off'], sorted([i for i in s['ics'] if i['c'] == c], key=lambda i: -(i['hw'][1] + i['fw'][1]))) for s in secs]; L2 = [x for x in L2 if x[1]]
        for k, (o, ics) in enumerate(L2):
            d = tr[c]; nrm = np.array([-d[1], d[0]])  # kontak dipisah per sisi (barat / timur jejak vein), bukan per From/To lubang
            side = lambda i: (np.array(i['hw']), np.array(i['fw'])) if np.dot(np.array(i['hw']) - np.array(i['fw']), nrm) > 0 else (np.array(i['fw']), np.array(i['hw']))
            HW = [side(i)[0] for i in ics]; FW = [side(i)[1] for i in ics]
            if c == 'V1': ztop = max(i['cz'] for i in ics); zbot = zsp - 4
            else:
                ztop = zsp + 4
                zbot = min(min(i['hw'][1], i['fw'][1]) for j in range(max(0, k - 1), min(len(L2), k + 2)) for i in L2[j][1]) - 10 * (-d[1])
            th, tf = to_z(HW[0], ztop, -d), to_z(FW[0], ztop, -d)
            bh = to_z(HW[-1], zbot, d) if HW[-1][1] > zbot else HW[-1] + d * 2; bf = to_z(FW[-1], zbot, d) if FW[-1][1] > zbot else FW[-1] + d * 2
            pts = [th] + HW + [bh, bf] + FW[::-1] + [tf]
            ext = [True] + [False] * len(HW) + [True, True] + [False] * len(FW) + [True]   # titik hasil perpanjangan (bukan kontak bor)
            S[c].append({'o': o, 'pts': [[round(float(q[0]), 3), round(float(q[1]), 3)] for q in pts]}); EXT[c].append(ext)
    return S, EXT, zsp

async def cm(pg, top, item):
    await pg.click(f'#mbar .mbb:has-text("{top}")'); await pg.wait_for_timeout(350)
    await pg.evaluate("(t)=>{const e=[...document.querySelectorAll('.cmi')].find(x=>x.offsetParent&&x.textContent.trim().startsWith(t));e&&e.click();}", item); await pg.wait_for_timeout(500)
async def slicing(pg):
    v = await pg.evaluate("()=>{const e=document.getElementById('sca');return !!(e&&e.offsetParent)}")
    if not v: await pg.click('#mbar .mbb:has-text("Slicing")'); await pg.wait_for_timeout(500)
async def tutup_lain(pg, kecuali=('scw',)):
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(150)
    await pg.evaluate('''(kc)=>{document.querySelectorAll('.flw').forEach(w=>{if(kc.includes(w.id)||!w.offsetParent)return;const b=w.querySelector('button[title="Tutup"]');if(b)b.click();else w.style.display='none';});
      document.querySelectorAll('#mbar .mbb.on').forEach(b=>{if(b.dataset.n&&!b.dataset.cm)b.click();});}''', list(kecuali)); await pg.wait_for_timeout(300)
async def tampil3d(pg):
    await pg.evaluate("()=>{const k=document.getElementById('owSkala');if(k)k.style.visibility='';}")
async def besar2d(pg, v):
    await tutup_lain(pg)
    await pg.evaluate('''(v)=>{const w=document.getElementById('scw');Object.assign(w.style,{left:'6px',top:'6px',width:'1426px',height:'752px',right:'auto',bottom:'auto'});
      const k=document.getElementById('owSkala');if(k)k.style.visibility='hidden';SC.v=v;scDraw();}''', v); await pg.wait_for_timeout(700)
    print('  scw', await pg.evaluate("()=>{const r=document.getElementById('scw').getBoundingClientRect();return [r.left,r.top,r.width,r.height].map(Math.round)}"))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1440, 'height': 860}, device_scale_factor=1.5, accept_downloads=True); E = pg.evaluate; errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300])); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept('V1') if d.type == 'prompt' else d.accept()))
        await pg.goto(APP); await pg.wait_for_timeout(3000)
        await E("()=>{const e=document.getElementById('pjn');if(e){e.textContent='Latihan Vein Bercabang';e.dispatchEvent(new Event('blur'));}}")
        # 1. impor
        await cm(pg, 'Data bor', 'Impor tabel')
        for k, f in [('collar', 'BR_collar.csv'), ('survey', 'BR_survey.csv'), ('assay', 'BR_assay.csv'), ('geo', 'BR_geologi.csv')]:
            await pg.set_input_files('#dsf-' + k, B + f); await pg.wait_for_timeout(300)
        await pg.wait_for_timeout(800)
        await shot(pg, 'vc01_impor', ['#dss-collar', '#dss-survey', '#dss-assay', '#dss-geo', '#dsgo'])
        await pg.click('#dsgo'); await pg.wait_for_timeout(3500)
        await cm(pg, 'Data bor', 'Warna lubang')
        await E("()=>{const s=document.getElementById('hcm');const o=[...s.options].find(o=>/Vein_Type/.test(o.textContent));if(o){s.value=o.value;s.dispatchEvent(new Event('change',{bubbles:true}));}}"); await pg.wait_for_timeout(600)
        await shot(pg, 'vc02_warna', ['#hcm'])
        await tutup_lain(pg, ()); await tampil3d(pg)
        await E(CAM, [E0 - 40, N0 + 60, 120, 200, 18, 420]); await pg.wait_for_timeout(800)
        await shot(pg, 'vc03_3d_bor')
        # 2. slicing
        await tutup_lain(pg, ()); await slicing(pg)
        await E(f"()=>{{const g=id=>document.getElementById(id);g('scm').value='v';g('scm').dispatchEvent(new Event('change'));g('sca').value=90;g('sce').value={E0};g('scn').value={N0};g('sco').value=0;g('sct').value=5;g('scs').value=10;scUpd();}}"); await pg.wait_for_timeout(600)
        await shot(pg, 'vc04_slicing', ['#sca', '#sce', '#sct', '#scs', '#sc2d'])
        await E("()=>document.getElementById('sc2d').click()"); await pg.wait_for_timeout(1200)
        await E("()=>{const set=(id,v)=>{const s=document.getElementById(id);const o=[...s.options].find(o=>o.value===v||o.textContent.trim()===v);if(o){s.value=o.value;s.dispatchEvent(new Event('change'));}};set('lgl','Vein_Type');set('lgr','Alt');}")
        V0 = {'m': 'v', 'cx': -50, 'cy': 132, 's': 3.15}
        await besar2d(pg, V0)
        await shot(pg, 'vc05_pen2d', ['#msbar', '#lgl', '#lgr'])
        # strings interpretasi
        offs = [float(-n) for n in range(0, 121, 10)]
        secs = await E(JS_ICS, {'offs': offs, 't': 5, 'E': E0, 'N': N0})
        S, EXT, zsp = strings(secs); print('RL percabangan taksiran %.1f' % zsp, {c: len(S[c]) for c in CODES})
        # 3. solid V1: + Solid (prompt dijawab 'V1'), digit penampang pertama dengan klik mouse sungguhan
        await besar2d(pg, {'m': 'v', 'cx': -22, 'cy': 172, 's': 7.5})
        await pg.click('#msbnew'); await pg.wait_for_timeout(400)
        await E("()=>{const M=__ms.mCur();if(M){M.nm='V1';M.col='#d81b60';M.capd=0;}__ms.panel();}")
        print('digit aktif', await E("()=>MS.dig"))
        s0 = S['V1'][0]; ex0 = EXT['V1'][0]; assert s0['o'] == 0.0
        n = len(s0['pts']); half = n // 2
        for j, pt in enumerate(s0['pts'][:half]):
            x, y = await E(PIX, pt)
            if ex0[j]: await pg.keyboard.down('Alt')
            await pg.mouse.click(x, y); await pg.wait_for_timeout(80)
            if ex0[j]: await pg.keyboard.up('Alt')
        await pg.mouse.move(x + 25, y + 6); await pg.wait_for_timeout(300)
        await shot(pg, 'vc06_digit_hw', ['#msdig', '#mssnap'])
        for j, pt in enumerate(s0['pts'][half:], start=half):
            x, y = await E(PIX, pt)
            if ex0[j]: await pg.keyboard.down('Alt')
            await pg.mouse.click(x, y); await pg.wait_for_timeout(80)
            if ex0[j]: await pg.keyboard.up('Alt')
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
        got = await E("()=>{const M=__ms.mCur();return M&&M.S.map(s=>[s.o,s.pts])}")
        dev = max(math.dist(a, c) for a, c in zip(got[0][1], s0['pts'])) if got and len(got[0][1]) == n else None
        print('string penampang 1 (klik):', got and len(got[0][1]), 'titik; selisih maks thd interpretasi', dev)
        await shot(pg, 'vc07_string1', ['#msbinf'])
        # PageDown -> penampang berikut, string sebelumnya tampil sebagai bayangan
        await pg.keyboard.press('PageDown'); await pg.wait_for_timeout(700)
        print('off sesudah PageDown', await E("()=>SC.q&&SC.q.off"))
        await shot(pg, 'vc08_bayangan', ['#msbinf'])
        # sisa string V1 + cabang dimasukkan seperti hasil digit
        await E("""(a)=>{const M=__ms.mCur();M.S=a.S.V1.map(s=>({o:s.o,pts:s.pts}));M.E=a.E;M.N=a.N;M.m='v';M.az=90;let id=M.id+1;
          for(const c of ['V1A','V1B','V1C'])MS.L.push({id:id++,nm:c,col:a.cols[c],cap:'titik',capd:0,den:2.6,on:true,m:'v',az:90,E:a.E,N:a.N,S:a.S[c]});
          for(const m of MS.L)__ms.build(m,true);__ms.panel();}""", {'S': S, 'cols': COLS, 'E': E0, 'N': N0}); await pg.wait_for_timeout(1200)
        indiv = await E("()=>MS.L.map(m=>[m.nm,m.S.length,m.res&&Math.round(m.res.vol),m.res&&m.res.open])"); print('solid:', indiv)
        # penampang di sekitar percabangan (N+60), semua string
        await E("()=>{document.getElementById('sco').value=-60;SC.v=null;scUpd();}"); await pg.wait_for_timeout(500)
        await besar2d(pg, V0)
        await shot(pg, 'vc09_cabang_pen', ['#msbsel'])
        await E("()=>document.getElementById('scx').click()"); await pg.wait_for_timeout(400); await tutup_lain(pg, ()); await tampil3d(pg)
        await E("()=>{for(const k of ['pdh','gc'])if(L[k])L[k].visible=false;}")
        await E(CAM, [E0 - 50, N0 + 60, 120, 205, 12, 360]); await pg.wait_for_timeout(900)
        await shot(pg, 'vc10_sendiri_3d')
        # 4. Cabang dari V1 lewat panel Wireframe
        await tutup_lain(pg, ()); await menu(pg, 'Wireframe geologi'); await sub(pg, 'Pemodelan string')
        id0 = await E("()=>MS.L[0].id")
        for c in ['V1A', 'V1B', 'V1C']:
            await E("(nm)=>{const s=document.getElementById('mssel');s.value=String(MS.L.find(m=>m.nm===nm).id);s.dispatchEvent(new Event('change'));}", c); await pg.wait_for_timeout(300)
            await E("(v)=>{const s=document.getElementById('mspar');s.value=String(v);s.dispatchEvent(new Event('change'));}", id0)
            for k in range(80):
                await pg.wait_for_timeout(250); st = await E("()=>MS.L[0].bst||''")
                if st and 'menghitung' not in st: break
            if c == 'V1A': await E("()=>document.getElementById('mspnl').scrollIntoView()"); await shot(pg, 'vc11_cabang_dari', ['#mssel', '#mspar', '#msinfo'])
        await E("()=>{const s=document.getElementById('mssel');s.value=String(MS.L[0].id);s.dispatchEvent(new Event('change'));}"); await pg.wait_for_timeout(500)
        res = await E("()=>{const M=MS.L[0];return [M.bst,M.res,WI.filter(w=>w.ms).map(w=>w.nm)]}"); print('union:', res)
        mesh = await E("()=>{const w=WI.find(w=>w.ms===MS.L[0].id);return {v:Array.from(w.v),t:Array.from(w.t)}}")
        Vv = np.array(mesh['v']).reshape(-1, 3); Tt = np.array(mesh['t']).reshape(-1, 3); par = list(range(len(Vv)))
        def fd(a):
            while par[a] != a: par[a] = par[par[a]]; a = par[a]
            return a
        for t in Tt: par[fd(t[1])] = fd(t[0]); par[fd(t[2])] = fd(t[0])
        from collections import defaultdict
        comp = defaultdict(list); [comp[fd(i)].append(i) for i in range(len(Vv))]
        print('bagian:', [(len(c), Vv[c].min(0).round(1).tolist(), Vv[c].max(0).round(1).tolist()) for c in comp.values()])
        await E("()=>document.getElementById('mspnl').scrollIntoView()")
        await shot(pg, 'vc12_union_info', ['#msinfo', '#msctp', '#mscpl'])
        await shot(pg, 'vc15_ekspor', ['#msxobj', '#msxdxf', '#msxstr', '#msxs'])
        await tutup_lain(pg, ()); await tampil3d(pg)
        await E(CAM, [E0 - 50, N0 + 60, 115, 200, 10, 380]); await pg.wait_for_timeout(900)
        await shot(pg, 'vc13_union_3d')
        await E(CAM, [E0 - 50, N0 + 60, 115, 235, 32, 420]); await pg.wait_for_timeout(900)
        await shot(pg, 'vc13b_union_oblik')
        await slicing(pg); await E("()=>document.getElementById('sc2d').click()"); await pg.wait_for_timeout(900)
        await E("()=>{for(const k of ['pdh','gc'])if(L[k])L[k].visible=true;const s=document.getElementById('msbsel');s.value=String(MS.L[0].id);s.dispatchEvent(new Event('change'));}")
        await besar2d(pg, V0)
        await shot(pg, 'vc14_union_pen')
        json.dump({'zsp': zsp, 'indiv': indiv, 'union': res, 'dev_klik': dev}, open('/home/claude/tut/sim/vc_hasil.json', 'w'), ensure_ascii=False, default=str)
        print('errs', errs); await b.close()
asyncio.run(main())
