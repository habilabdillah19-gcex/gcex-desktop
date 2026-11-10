"""Tangkapan layar tutorial GC-Ex Block Model 0.20.1 (aplikasi app/ di repo) dengan data latihan SIM_BM_GC_kadar.csv (block model GC berisi kadar).
Hasil: img_bm/*.png + img_bm/notes.json (angka untuk keterangan). Lalu: python build_tutorial_bm.py"""
from playwright.sync_api import sync_playwright
import os, sys, json, time, subprocess, urllib.request, csv, io
T = os.path.dirname(os.path.abspath(__file__)) + '/'; R = os.path.abspath(T + '../../../') + '/'; DATA = T + '../data/'; IMG = T + 'img_bm/'
os.makedirs(IMG, exist_ok=True)
for f in os.listdir(IMG):
    if f.endswith('.png'): os.remove(IMG + f)
PORT = 8778; P = 'http://localhost:%d/index.html' % PORT
MOCK = "try{delete window.showSaveFilePicker;window.showSaveFilePicker=undefined;}catch(e){}window.showDirectoryPicker=async function(){var r=await navigator.storage.getDirectory();return r.getDirectoryHandle('Proyek_Tutorial_BM',{create:true});};"
NOTES = {}; SEQ = [0]
# Penanda jejak: bila tahap ini gagal, cetak di LANGKAH MANA berhentinya. Tanpa ini log CI
# hanya memperlihatkan pengecualian Playwright tanpa konteks.
JEJAK = {"gambar": "(belum ada)", "catatan": "(belum ada)"}
def _jejak_hook(t, v, tb):
    import sys as _s, traceback as _tb
    print("", flush=True)
    print("GAGAL setelah gambar: %s" % JEJAK["gambar"], flush=True)
    print("catatan terakhir     : %s" % JEJAK["catatan"], flush=True)
    _tb.print_exception(t, v, tb)
    _s.__excepthook__ if False else None
import sys as _sys_jejak
_sys_jejak.excepthook = _jejak_hook

def note(k, v):
    """Pencetakan angka hasil tidak boleh menggagalkan pembuatan tutorial: konsol Windows
    bawaannya cp1252, sedangkan teks panel GC-Ex memuat karakter di luar cp1252."""
    NOTES[k] = v
    JEJAK['catatan'] = '%s = %s' % (k, str(v)[:90])
    try:
        print('  ', k, '=', str(v)[:160], flush=True)
    except Exception as _e:
        try: print('  ', k, '= <tidak dapat dicetak di konsol ini:', type(_e).__name__ + '>', flush=True)
        except Exception: pass
try: urllib.request.urlopen(P, timeout=2)
except Exception: subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=R + 'app/', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as pw:
    _args = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
    _o = dict(viewport={'width': 1600, 'height': 940}, device_scale_factor=1.25, accept_downloads=True)
    # GCEX_SHOTS_PERSISTENT=1: profil tetap, perlu di Linux karena folder proyek ditiru dengan OPFS
    # yang tidak tersedia di context sementara (lihat tutorial_shots.py).
    if os.environ.get('GCEX_SHOTS_PERSISTENT'):
        import tempfile, shutil, atexit
        _ud = tempfile.mkdtemp(prefix='gcex_bm_shots_')
        atexit.register(lambda: shutil.rmtree(_ud, ignore_errors=True))
        br = None
        ctx = pw.chromium.launch_persistent_context(_ud, args=_args, **_o)
    else:
        br = pw.chromium.launch(args=_args)
        ctx = br.new_context(**_o)
    ctx.add_init_script(MOCK); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('dialog', lambda d: (d.accept(d.default_value) if d.type == 'prompt' and 'nama berkas' in d.message else d.accept('Habil') if d.type == 'prompt' else d.accept()))  # ekspor lewat gxSimpan
    def ev(js): return pg.evaluate(js)
    def shot(name, clip=None):
        SEQ[0] += 1; fn = '%02d_%s.png' % (SEQ[0], name); pg.wait_for_timeout(600)
        pg.screenshot(path=IMG + fn, clip=clip) if clip else pg.screenshot(path=IMG + fn); print('shot', fn, flush=True)
    SIDE = {'x': 0, 'y': 0, 'width': 316, 'height': 940}
    def menu_shot(node, name, opens=()):
        # tombol ⋯ node -> menu terbuka -> potret kolom Project Tree + menu (BM 0.24.46 / DH 0.24.53: import langsung dari ⋯)
        ev("(function(){%sPT.render(true);})()" % ''.join("PT.open[%r]=1;" % o for o in opens)); pg.wait_for_timeout(400)
        pg.locator("#ptree .ptr[data-id='%s'] .ptx" % node).click(); pg.wait_for_timeout(500)
        r = pg.evaluate("(function(){var m=document.getElementById('ptMenu'),b=m?m.getBoundingClientRect():null;return b?[b.right,b.bottom]:[0,0];})()")
        shot(name, {'x': 0, 'y': 0, 'width': int(max(SIDE['width'], r[0] + 12)), 'height': int(min(940, max(560, r[1] + 12)))})
        ev("var m=document.getElementById('ptMenu');if(m)m.remove();")
    def tree(sel, opens=()):
        ev("(function(){%sPT.render(true);PT.select(%r);})()" % (''.join("PT.open[%r]=1;" % o for o in opens), sel)); pg.wait_for_timeout(900)
    pg.goto(P); pg.wait_for_timeout(1200); ev("localStorage.clear();localStorage.setItem('gcex_user','Habil')"); pg.reload(); pg.wait_for_timeout(1500)
    # 1. halaman muka & import
    ev("var i=document.getElementById('gxSite');if(i){i.value='Site Latihan · Pit Simulasi';i.dispatchEvent(new Event('input'));}")
    shot('halaman_muka')
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(500)
    pg.set_input_files("input[onchange*='SA.bmPick']", DATA + 'SIM_BM_GC_kadar.csv'); pg.wait_for_timeout(800)
    ev("var e=document.getElementById('dsName');if(e)e.value='Latihan_BM'")
    shot('import')
    pg.click('#btnGo'); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(3000)
    note('nBlok', ev('BX.m.n')); note('atribut', ev('Object.keys(BX.m.num).join(", ")'))
    # 2. tampilan awal
    ev("BX.ui.fAttr='AU';BX.ui.fOp='ge';BX.ui.fVal='0.19';BX.sc={};BX.mc=null;updatePlot();setCam(1.3,-1.5,0.8)"); pg.wait_for_timeout(2500); shot('bm_3d')
    shot('header', {'x': 0, 'y': 0, 'width': 1600, 'height': 40})
    menu_shot('bm', 'menu_bm', ['bm']); menu_shot('sp', 'menu_spasial', ['sp'])
    # Slicer (BM 0.24.50): popup dip 60 / az tegak lurus strike, potong data
    ev("$('sliceClip').checked=true;$('showPlane').checked=true;if(window.SLICER){SLICER.set(60,45);SLICER.open();}"); pg.wait_for_timeout(1500)
    rs = ev("(function(){var m=document.getElementById('secMenu'),b=m?m.getBoundingClientRect():null;return b?[b.left,b.top,b.width,b.height]:null;})()")
    if rs: shot('slicer_popup', {'x': max(0, int(rs[0] - 320)), 'y': max(0, int(rs[1] - 10)), 'width': int(rs[2] + 340), 'height': int(min(880, rs[3] + 20))})
    ev("if(window.SLICER){SLICER.close();SLICER.set(0,null);}$('sliceClip').checked=false;$('showPlane').checked=false;updatePlot()"); pg.wait_for_timeout(800)
    # kotak Kinerja & grafis di panel Tampilan & performa (BM 0.24.47 / DH 0.24.54)
    ev("PT.select('set.v');if(window.KIN&&KIN.gambar)KIN.gambar();var k=document.getElementById('kinBox');if(k)k.scrollIntoView({block:'center'})"); pg.wait_for_timeout(700)
    rk = ev("(function(){var k=document.getElementById('kinBox'),b=k?k.getBoundingClientRect():null;return b?[b.left,b.top,b.width,b.height]:null;})()")
    if rk: shot('kinerja_panel', {'x': max(0, int(rk[0] - 8)), 'y': max(0, int(rk[1] - 8)), 'width': int(rk[2] + 16), 'height': int(min(900, rk[3] + 16))})
    tree('bm.cls', ['bm']); shot('warna_kelas')
    # 3. flitch aktif
    # RL flitch diambil dari block model yang dimuat, bukan angka tetap: ukuran & posisi data
    # latihan boleh berubah tanpa merusak tutorial. Dipilih bench yang isinya paling banyak.
    RL_TOP = ev("(()=>{var m=BX.m,h={},bs=2.5;for(var i=0;i<m.n;i++){var k=Math.round(m.z[i]/bs)*bs;h[k]=(h[k]||0)+1;}"
                "var ks=Object.keys(h).map(Number).sort((a,b)=>h[b]-h[a]);return ks[0]+bs/2;})()")
    note('flitchTop', RL_TOP)
    ev("lySet('fh',2.5);lyU().bot='';lySet('top',%s);lyApply()" % RL_TOP); pg.wait_for_timeout(2500)
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
    if not G:
        raise SystemExit('flGroups() kosong: block model tidak menghasilkan flitch. Periksa SIM_BM_GC_kadar.csv.')
    k1 = min(G, key=lambda g: abs(g[1] - RL_TOP))[0]
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
    ev("lySet('top',%s);lyApply()" % RL_TOP); pg.wait_for_timeout(2500)
    nam = ev("""(function(){var n=0;lyItems(true).forEach(function(o){if(!/HG|LG/i.test(o.s.d||''))return;var p=o.r.map(function(q){return[q[0]+0.6,q[1]-0.4];});if(amBndAdd(p,'AM_'+o.s.d+'_'+(++n)))0;});try{AM.show=true;amRun(true);}catch(e){}return n;})()""")
    note('am_n', nam); pg.wait_for_timeout(2000)
    tree('am.3', ['am']); shot('asmined_poligon')
    ev("PT.open['am']=1;PT.open['am.fl']=1;PT.render(true)"); tree('am.fl', ['am', 'am.fl']); k0 = min(G, key=lambda g: abs(g[1] - RL_TOP))[0]; ev("PT.open['am.fl.%s']=1;PT.render(true)" % k0); tree('am.fl.%s' % k0); ev("var s=document.querySelector('#ptree');var n=[...s.querySelectorAll('*')].find(e=>e.children.length===0&&e.textContent==='Rencana (dig block)');if(n)n.scrollIntoView({block:'center'})")
    shot('pertree_asmined', SIDE)
    note('am_vs', ev("""flGroups().map(g=>{var c=flCalc(g),at=0,am=0,nc=0;g.am.forEach(function(x){var I=amInfoById(x.id);if(I&&I.calc&&x.on!==false){nc++;at+=I.ton;if(isFinite(I.gA))am+=I.gA*I.ton;}});return[g.top,g.bot,c?Math.round(c.t):0,c&&c.t?+(c.m/c.t).toFixed(2):0,nc,Math.round(at),at?+(am/at).toFixed(2):0];})"""))
    k = min(G, key=lambda g: abs(g[1] - RL_TOP))[0]
    tree('am.fl.%s' % k); pg.wait_for_timeout(1500); shot('asmined_review_2d')
    # 12. register & 3D hasil kerja
    tree('reg.1', ['reg']); shot('register', SIDE)
    ev("if(window.am3Toggle)am3Toggle(true)"); pg.wait_for_timeout(2500); ev("if(VIEW2D)toggle2D();setCam(1.2,-1.4,0.9)"); pg.wait_for_timeout(2500); shot('hasil_kerja_3d')
    # 13. Solid Vein Aktual (trial, BM 0.24.51): poligon sintetis 4 flitch (bercabang) + 1 pulau terpisah -> solid di 3D
    ev("if(window.am3Toggle)am3Toggle(false)")
    ev("""(function(){var m=BX.m,cx=0,cy=0,n=Math.min(m.n,5000);for(var i=0;i<n;i++){cx+=m.x[i];cy+=m.y[i];}cx=cx/n-offX;cy=cy/n-offY;var B=lyBench(),fh=B[0]-B[1],T0=B[0];
      var el=function(x,y,a,b,k,rot){var o=[];for(var i=0;i<k;i++){var t=i/k*6.2832,px=a*Math.cos(t)*(1+0.15*Math.sin(3*t)),py=b*Math.sin(t);o.push([x+px*Math.cos(rot)-py*Math.sin(rot),y+px*Math.sin(rot)+py*Math.cos(rot)]);}return o;};
      var d=SV.D(),p={id:'ptut',name:'Contoh W1',from:'',to:'',polys:[],par:{dmax:8,zMode:'flat',capPts:false,method:'min',sg:2.6,reg:true,rIdw:6,zTol:fh/2},res:null};window._svPer=d.per;window._svCur=d.cur;d.per=[p];d.cur=p.id;
      [[0,el(cx,cy,22,5,26,0.3)],[1,el(cx+1,cy+0.5,24,6,30,0.32)],[2,el(cx-9,cy-2,10,4.5,18,0.3)],[2,el(cx+16,cy+6,8,4,16,0.35)],[3,el(cx-10,cy-2.5,8,4,16,0.3)],[1,el(cx+60,cy+25,9,4,14,0.2)],[2,el(cx+61,cy+25,7,3.5,12,0.2)]].forEach(function(q,i){p.polys.push({id:'v'+i,top:T0-q[0]*fh,bot:T0-(q[0]+1)*fh,pts:q[1],key:'k'+i,src:'digit',name:'V'+(i+1),on:true});});
      window._svVis=MD.models.map(function(m){return m.vis;});MD.models.forEach(function(m){m.vis=false;});window._svBx=$('bxShow').checked;$('bxShow').checked=false;lyFlOff();if(VIEW2D)toggle2D();})()""")
    pg.wait_for_timeout(800); ev("PT.open['sv']=1;PT.select('sv');SV.run()"); pg.wait_for_function("!SV.busy && SV.per() && SV.per().res", timeout=60000); pg.wait_for_timeout(1500)
    ev("PT.open['sv.p.ptut']=1;PT.render(true);SV.focus('res');SV.lihat()"); pg.wait_for_timeout(3500); shot('solidvein_3d')
    note('solidvein', ev("SV.per().res.IS.map(function(s){return [s.n,s.closed,+s.vol.toFixed(1),s.nLv,s.nPoly];})"))
    ev("(function(){var d=SV.D(),p=SV.per();SV.setPar('reg',false);d.per=window._svPer||[];d.cur=window._svCur||'';MD.models.forEach(function(m,i){m.vis=window._svVis[i]!==false;});$('bxShow').checked=window._svBx;updatePlot();})()")
    note('errs', errs)
    json.dump(NOTES, open(IMG + 'notes.json', 'w'), ensure_ascii=False, indent=1)
    (br.close() if br else ctx.close())
print('selesai', SEQ[0], 'gambar')
