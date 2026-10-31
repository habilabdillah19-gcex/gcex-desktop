"""Tangkapan layar tutorial GC-Ex Block Model 0.20.1 (aplikasi app/ di repo) dengan data latihan SIM_BM_GC.csv.
Hasil: img_bm/*.png + img_bm/notes.json (angka untuk keterangan). Lalu: python build_tutorial_bm.py"""
from playwright.sync_api import sync_playwright
import os, sys, json, time, subprocess, urllib.request, csv, io
T = os.path.dirname(os.path.abspath(__file__)) + '/'; R = os.path.abspath(T + '../../../') + '/'; DATA = T + '../data/'; IMG = T + 'img_bm/'
os.makedirs(IMG, exist_ok=True)
for f in os.listdir(IMG):
    if f.endswith('.png'): os.remove(IMG + f)
PORT = 8778; P = 'http://localhost:%d/index.html' % PORT
MOCK = "window.showDirectoryPicker=async function(){var r=await navigator.storage.getDirectory();return r.getDirectoryHandle('Proyek_Tutorial_BM',{create:true});};"
NOTES = {}; SEQ = [0]
def note(k, v):
    """Pencetakan angka hasil tidak boleh menggagalkan pembuatan tutorial: konsol Windows
    bawaannya cp1252, sedangkan teks panel GC-Ex memuat karakter di luar cp1252."""
    NOTES[k] = v
    try:
        print('  ', k, '=', str(v)[:160], flush=True)
    except Exception as _e:
        try: print('  ', k, '= <tidak dapat dicetak di konsol ini:', type(_e).__name__ + '>', flush=True)
        except Exception: pass
try: urllib.request.urlopen(P, timeout=2)
except Exception: subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=R + 'app/', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as pw:
    br = pw.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    ctx = br.new_context(viewport={'width': 1600, 'height': 940}, device_scale_factor=1.25, accept_downloads=True)
    ctx.add_init_script(MOCK); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('dialog', lambda d: (d.accept('Habil') if d.type == 'prompt' else d.accept()))
    def ev(js): return pg.evaluate(js)
    def shot(name, clip=None):
        SEQ[0] += 1; fn = '%02d_%s.png' % (SEQ[0], name); pg.wait_for_timeout(600)
        pg.screenshot(path=IMG + fn, clip=clip) if clip else pg.screenshot(path=IMG + fn); print('shot', fn, flush=True)
    SIDE = {'x': 0, 'y': 0, 'width': 316, 'height': 940}
    def tree(sel, opens=()):
        ev("(function(){%sPT.render(true);PT.select(%r);})()" % (''.join("PT.open[%r]=1;" % o for o in opens), sel)); pg.wait_for_timeout(900)
    pg.goto(P); pg.wait_for_timeout(1200); ev("localStorage.clear();localStorage.setItem('gcex_user','Habil')"); pg.reload(); pg.wait_for_timeout(1500)
    # 1. halaman muka & import
    ev("var i=document.getElementById('gxSite');if(i){i.value='Site Latihan · Pit Simulasi';i.dispatchEvent(new Event('input'));}")
    shot('halaman_muka')
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(500)
    pg.set_input_files("input[onchange*='SA.bmPick']", DATA + 'SIM_BM_GC.csv'); pg.wait_for_timeout(800)
    ev("var e=document.getElementById('dsName');if(e)e.value='Latihan_BM'")
    shot('import')
    pg.click('#btnGo'); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(3000)
    note('nBlok', ev('BX.m.n')); note('atribut', ev('Object.keys(BX.m.num).join(", ")'))
    # 2. tampilan awal
    ev("BX.ui.fAttr='AU';BX.ui.fOp='ge';BX.ui.fVal='0.19';BX.sc={};BX.mc=null;updatePlot();setCam(1.3,-1.5,0.8)"); pg.wait_for_timeout(2500); shot('bm_3d')
    shot('header', {'x': 0, 'y': 0, 'width': 1600, 'height': 40})
    tree('bm.cls', ['bm']); shot('warna_kelas')
    # 3. flitch aktif
    ev("lySet('fh',2.5);lyU().bot='';lySet('top',292.5);lyApply()"); pg.wait_for_timeout(2500)
    tree('fl', ['fl']); shot('flitch')
    note('flitch1', ev('lyBench()'))
    # 4. dig block otomatis
    tree('dig.auto', ['dig']); ev("dbAuto()"); pg.wait_for_timeout(2500); shot('digblock_auto')
    note('db1', ev("lyItems(true).length"))
    # 5. additional flagging
    ev("""(function(){var R=afRules();R.length=0;R.push({n:'Ore Sulfide',k:'num',a:'S_PCT',op:'>',c:0.8,on:true});R.push({n:'Zn tinggi',k:'num',a:'ZN_PPM',op:'>',c:500,on:true});
          dbSet('sfOn',true);afDirty2();dbInner(true);dbPanel();var d=[...document.querySelectorAll('#dbBody details.mini')].find(x=>/Additional/i.test(x.textContent));if(d){d.open=true;d.scrollIntoView({block:'start'});}updatePlot();})()""")
    pg.wait_for_timeout(2000); shot('flagging_aturan', SIDE); shot('flagging_2d')
    it = ev("lyItems(true).map(o=>[o.name,o.s.d,o.dest,Math.round(o.ton.t),+(o.ton.grade||0).toFixed(2),(o.ton.af||[]).join(', ')])")
    note('db1_items', it); note('db1_flag', sum(1 for o in it if o[5]))
    # 6. rekap & edit string
    tree('dig.str', ['dig']); shot('rekap_string', SIDE)
    # 7. laporan grade x tonase (flitch aktif)
    tree('rep.run', ['rep']); shot('laporan_flitch')
    # 8. flitch kedua
    ev("lySet('top',295);lyApply()"); pg.wait_for_timeout(2500); ev("dbAuto();dbInner(true)"); pg.wait_for_timeout(2000)
    note('db2', ev("lyItems(true).length"))
    # 9. review per flitch di Project Tree
    ev("PT.open['dig']=1;PT.open['dig.fl']=1;PT.open['rep']=1;PT.open['rep.fl']=1;PT.render(true)")
    tree('dig.fl', ['dig', 'dig.fl']); ev("var s=document.querySelector('#ptree');if(s){var n=[...s.querySelectorAll('*')].find(e=>e.children.length===0&&/^Per flitch/.test(e.textContent));if(n)n.scrollIntoView({block:'start'});}"); shot('pertree_digblock', SIDE)
    G = ev("flGroups().map(g=>[g.k,g.top,g.bot])"); note('flitches', G)
    k1 = [g for g in G if abs(g[1] - 292.5) < 1e-6][0][0]
    ev("PT.open['dig.fl.%s']=1;PT.render(true)" % k1); tree('dig.fl.%s' % k1); ev("var s=document.querySelector('#ptree');var n=[...s.querySelectorAll('*')].find(e=>e.children.length===0&&/^RL 292.5/.test(e.textContent));if(n)n.scrollIntoView({block:'start'})")
    shot('pertree_digblock_flitch', SIDE); shot('pertree_digblock_2d')
    tree('rep.fl', ['rep', 'rep.fl']); ev("var s=document.querySelector('#ptree');var n=[...s.querySelectorAll('*')].find(e=>e.children.length===0&&/^Per flitch/.test(e.textContent)&&e.closest('[data-id]')&&/rep/.test(e.closest('[data-id]').dataset.id||''));if(n)n.scrollIntoView({block:'start'})")
    shot('pertree_laporan', SIDE)
    note('rekap', ev("flGroups().map(g=>{var c=flCalc(g);return c?[g.top,g.bot,c.it.length,Math.round(c.t),+(c.m/c.t).toFixed(2),c.it.filter(o=>o.af.length).length]:null})"))
    with pg.expect_download() as d: ev("flCsvAll()")
    note('csv_baris', len(open(d.value.path(), encoding='utf-8-sig').read().strip().splitlines()) - 1)
    # 10. layout & plot
    tree('out.ly', ['out']); shot('layout', SIDE)
    # 11. as-mined: poligon aktual = dig block ore yang tergeser 1,5 m (simulasi penggalian) di flitch 280
    ev("lySet('top',292.5);lyApply()"); pg.wait_for_timeout(2500)
    nam = ev("""(function(){var n=0;lyItems(true).forEach(function(o){if(!/HG|LG/i.test(o.s.d||''))return;var p=o.r.map(function(q){return[q[0]+0.6,q[1]-0.4];});if(amBndAdd(p,'AM_'+o.s.d+'_'+(++n)))0;});try{AM.show=true;amRun(true);}catch(e){}return n;})()""")
    note('am_n', nam); pg.wait_for_timeout(2000)
    tree('am.3', ['am']); shot('asmined_poligon')
    ev("PT.open['am']=1;PT.open['am.fl']=1;PT.render(true)"); tree('am.fl', ['am', 'am.fl']); k0 = [g for g in G if abs(g[1] - 292.5) < 1e-6][0][0]; ev("PT.open['am.fl.%s']=1;PT.render(true)" % k0); tree('am.fl.%s' % k0); ev("var s=document.querySelector('#ptree');var n=[...s.querySelectorAll('*')].find(e=>e.children.length===0&&e.textContent==='Rencana (dig block)');if(n)n.scrollIntoView({block:'center'})")
    shot('pertree_asmined', SIDE)
    note('am_vs', ev("""flGroups().map(g=>{var c=flCalc(g),at=0,am=0,nc=0;g.am.forEach(function(x){var I=amInfoById(x.id);if(I&&I.calc&&x.on!==false){nc++;at+=I.ton;if(isFinite(I.gA))am+=I.gA*I.ton;}});return[g.top,g.bot,c?Math.round(c.t):0,c&&c.t?+(c.m/c.t).toFixed(2):0,nc,Math.round(at),at?+(am/at).toFixed(2):0];})"""))
    k = [g for g in G if abs(g[1] - 292.5) < 1e-6][0][0]
    tree('am.fl.%s' % k); pg.wait_for_timeout(1500); shot('asmined_review_2d')
    # 12. register & 3D hasil kerja
    tree('reg.1', ['reg']); shot('register', SIDE)
    ev("if(window.am3Toggle)am3Toggle(true)"); pg.wait_for_timeout(2500); ev("if(VIEW2D)toggle2D();setCam(1.2,-1.4,0.9)"); pg.wait_for_timeout(2500); shot('hasil_kerja_3d')
    note('errs', errs)
    json.dump(NOTES, open(IMG + 'notes.json', 'w'), ensure_ascii=False, indent=1)
    br.close()
print('selesai', SEQ[0], 'gambar')
