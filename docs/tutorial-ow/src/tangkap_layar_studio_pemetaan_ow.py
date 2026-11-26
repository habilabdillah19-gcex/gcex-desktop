# -*- coding: utf-8 -*-
"""Tangkapan layar tutorial "Studio Pemetaan" (Ore Works 0.34+, digitasi pemetaan di plan 2D).
Data fiktif latihan: docs/tutorial-ow/data (LTH_*). Ortofoto latihan dibuat dari bayangan topografi (fiktif).
Hasil: /home/claude/tut/shots/sp*.png"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).parent))
from lib import APP, shot
D = str(Path(__file__).resolve().parents[1] / 'data') + '/'
Path('/home/claude/tut/shots').mkdir(parents=True, exist_ok=True)

ORTO = """async()=>{const s=SF.find(x=>x.kind==='topo'),G=sfGrid(s),W=360,H=360,E0=10000,N1=20200,px=200/W;const cv=document.createElement('canvas');cv.width=W;cv.height=H;const cx=cv.getContext('2d'),im=cx.createImageData(W,H),z=(E,N)=>gridZ(G,E,N);
 for(let j=0;j<H;j++)for(let i=0;i<W;i++){const E=E0+(i+.5)*px,N=N1-(j+.5)*px,a=z(E-px,N),b=z(E+px,N),c=z(E,N-px),d=z(E,N+px);let v=200;if(isFinite(a)&&isFinite(b)&&isFinite(c)&&isFinite(d)){const dx=(b-a)/(2*px),dy=(d-c)/(2*px),sh=(-dx*.6+dy*.6+1)/Math.sqrt(dx*dx+dy*dy+1);v=Math.max(60,Math.min(250,120+110*sh));}
  const q=(j*W+i)*4,t=((i*7+j*13)%17)/17*10;im.data[q]=v*.86+t;im.data[q+1]=v*.8+t;im.data[q+2]=v*.62+t;im.data[q+3]=255;}
 cx.putImageData(im,0,0);const bl=await new Promise(r=>cv.toBlob(r,'image/png'));const dt=new DataTransfer();dt.items.add(new File([bl],'LTH_ortofoto.png',{type:'image/png'}));dt.items.add(new File([[px,0,0,-px,E0+px/2,N1-px/2].join('\\n')],'LTH_ortofoto.pgw'));
 const inp=document.getElementById('orf');inp.files=dt.files;inp.dispatchEvent(new Event('change',{bubbles:true}));}"""
W2S = "([E,N,Z])=>SPM.api.w2s(E,N,Z)"

async def klik_peta(pg, p, o=None):
    x, y = await pg.evaluate(W2S, p); await pg.mouse.move(x, y); await pg.mouse.click(x, y, **(o or {})); await pg.wait_for_timeout(350)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1440, 'height': 860}, device_scale_factor=1.5); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto(APP); await pg.wait_for_timeout(5000)
        await pg.evaluate("()=>{try{localStorage.removeItem('ow.spm');}catch(e){}}")
        await pg.goto(APP); await pg.wait_for_timeout(5000)
        for k, f in [('collar', 'LTH_collar.csv'), ('survey', 'LTH_survey.csv'), ('assay', 'LTH_assay.csv'), ('geo', 'LTH_geologi.csv')]:
            await pg.set_input_files('#dsf-' + k, D + f); await pg.wait_for_timeout(300)
        await pg.evaluate("()=>document.getElementById('dsgo').click()"); await pg.wait_for_timeout(3000)
        await pg.set_input_files('#sff', D + 'LTH_topografi.str'); await pg.wait_for_timeout(2500)
        await pg.set_input_files('#fmpf', D + 'LTH_pickup.csv'); await pg.wait_for_timeout(1200)
        await pg.evaluate(ORTO); await pg.wait_for_timeout(2500)
        # pintu masuk: menu Pemetaan
        await pg.locator('#mbar >> text=/^Pemetaan/').first.click(); await pg.wait_for_timeout(600)
        await shot(pg, 'sp01_menu', ['.spmi', '#otbsp'], clip=(0, 0, 1440, 380))
        await pg.locator('.spmi').click(); await pg.wait_for_timeout(1500)
        await pg.evaluate("()=>SPM.api.fitTo(FM.pf[0].P.map(r=>[+r[1],+r[2],+r[3]]),1.9)"); await pg.wait_for_timeout(600)
        await shot(pg, 'sp02_layar', ['#sptl', '#spc', '.rp', '#spw .tb', '#sppk', '#spw .sb'])
        await shot(pg, 'sp03_bilah', ['#splyr', '#spkat', '#spvp', '[data-z=topo]', '#sprl', '#spsnap', '#splb', '#spud'], clip=(0, 0, 1440, 110))
        await pg.evaluate("()=>{document.getElementById('splb').click()}"); await pg.wait_for_timeout(500)
        await shot(pg, 'sp04_latar', ['#splay'])
        await pg.evaluate("()=>{document.getElementById('splx').click()}")
        # digit vein mengikuti pick-up P001..P0xx (snap)
        await pg.fill('#splyr', 'VN_Latihan'); await pg.keyboard.press('Enter')
        K = lambda code: pg.evaluate("(c)=>FM.pf[0].P.filter(r=>String(r[4]).trim()===c).map(r=>[+r[1],+r[2],+r[3]])", code)
        P = (await K('VN'))[::2]
        await pg.keyboard.press('1'); await pg.wait_for_timeout(200)
        for q in P[:-1]: await klik_peta(pg, q)
        x, y = await pg.evaluate(W2S, P[-1]); await pg.mouse.move(x, y); await pg.wait_for_timeout(400)
        await shot(pg, 'sp05_digit_vein', ['#sptl .tl[data-t=vein]', '#sptip'])
        await pg.mouse.click(x, y); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(600)
        await shot(pg, 'sp06_atribut', ['#sptree .tr.sel', '#spat'])
        # channel, kontak, struktur, poligon, grab
        c = await pg.evaluate("()=>{const v=SPM.api.view();return [v.cx,v.cy]}")
        Z = lambda e, n: [c[0] + e, c[1] + n, 0]
        CH, KT, SL, GB = await K('CH'), await K('KT'), await K('SL'), await K('GB')
        await pg.keyboard.press('2'); await klik_peta(pg, CH[0]); await klik_peta(pg, CH[-1]); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(300)
        await pg.keyboard.press('3')
        for q in KT: await klik_peta(pg, q)
        await pg.keyboard.press('Enter')
        await pg.keyboard.press('4'); await klik_peta(pg, SL[0]); await klik_peta(pg, SL[-1]); await pg.keyboard.press('Enter')
        v0 = (await K('VN'))
        await pg.keyboard.press('5')
        for q in [[v0[0][0]-9, v0[0][1]+4, 0], [v0[0][0]+9, v0[0][1]+7, 0], [v0[-1][0]+10, v0[-1][1]-3, 0], [v0[-1][0]-8, v0[-1][1]-6, 0]]: await klik_peta(pg, q)
        await klik_peta(pg, [v0[0][0]-9, v0[0][1]+4, 0])
        await pg.keyboard.press('6')
        for q in GB: await klik_peta(pg, q)
        await pg.keyboard.press('8'); await klik_peta(pg, Z(-35, 30))
        # strike / dip: seret
        await pg.keyboard.press('7'); await pg.fill('#spdip', '65'); await pg.keyboard.press('Enter')
        x, y = await pg.evaluate(W2S, Z(-45, -5)); await pg.mouse.move(x, y); await pg.mouse.down(); await pg.mouse.move(x + 40, y - 10, steps=6)
        await shot(pg, 'sp07_strike_dip', ['#sptl .tl[data-t=sd]', '#spsdj', '#spdip', '#spstk'])
        await pg.mouse.up(); await pg.wait_for_timeout(400)
        await pg.keyboard.press('v'); await pg.mouse.move(10, 10); await pg.wait_for_timeout(300)
        await shot(pg, 'sp08_hasil_plan', ['#sptree'])
        # edit: pilih vein, seret titik
        await pg.evaluate("()=>{const i=FM.F.findIndex(f=>f.k==='vein'&&f.a.grup==='VN_Latihan');document.querySelector('#sptree [data-f=\"'+i+'\"]').click();}"); await pg.wait_for_timeout(400)
        q = await pg.evaluate("()=>SPM.sel.f.pts[3]")
        x, y = await pg.evaluate(W2S, q); await pg.mouse.move(x, y); await pg.mouse.down(); await pg.mouse.move(x + 30, y + 18, steps=6)
        await shot(pg, 'sp09_edit', ['#sptl .tl[data-t=sel]', '#spud'])
        await pg.mouse.up(); await pg.keyboard.press('Control+z'); await pg.wait_for_timeout(300)
        # filter RL
        await pg.check('#sprl'); await pg.wait_for_timeout(500)
        await shot(pg, 'sp10_filter_rl', ['#sprl', '#sprlv', '#sprlt'], clip=(0, 0, 1440, 560))
        await pg.uncheck('#sprl')
        # muka dinding
        await pg.keyboard.press('w'); await klik_peta(pg, Z(-50, 10)); await klik_peta(pg, Z(50, -10)); await pg.wait_for_timeout(800)
        await pg.fill('#spwt', '15'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(300)
        await pg.evaluate("()=>{const w=SPM.wall,P=[];for(let u=0;u<=w.len;u+=w.len/10){const E=w.a[0]+u*w.ux,N=w.a[1]+u*w.uy;P.push([E,N,topoZ(E,N)],[E,N,topoZ(E,N)-25]);}SPM.api.fitTo(P,1.2);}"); await pg.wait_for_timeout(400)
        await pg.keyboard.press('3')
        W = await pg.evaluate("()=>{const w=SPM.wall,o=[];for(const k of [.2,.4,.6,.8]){const u=w.len*k,E=w.a[0]+u*w.ux,N=w.a[1]+u*w.uy;o.push([E,N,topoZ(E,N)-6-k*8]);}return o}")
        for q in W: await klik_peta(pg, q)
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
        await shot(pg, 'sp11_dinding', ['#spvw', '#spwt', '#sptl .tl[data-t=wl]'])
        await pg.click('#spvp'); await pg.wait_for_timeout(400)
        await pg.evaluate("()=>{document.getElementById('sptema').click()}"); await pg.wait_for_timeout(500)
        await shot(pg, 'sp12_gelap', ['#sptema'])
        await pg.evaluate("()=>{document.getElementById('sptema').click()}")
        # hasil di 3D
        await pg.keyboard.press('F8'); await pg.wait_for_timeout(800)
        await pg.evaluate("()=>{const P=[];FM.F.forEach(f=>f.pts.forEach(p=>P.push(p)));fmZoom(P);}"); await pg.wait_for_timeout(1500)
        await shot(pg, 'sp13_hasil_3d', [])
        print('galat', errs[:5])
        await b.close()
asyncio.run(main())
