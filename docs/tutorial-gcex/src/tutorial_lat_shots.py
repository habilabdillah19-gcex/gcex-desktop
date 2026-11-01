"""Tangkapan layar tutorial bab Sesar 3D & Geomodeller Stratified-Laterite (GC-Ex Drill Hole Ultimate 0.21)
dengan data simulasi laterit nikel (docs/tutorial-gcex/data/SIM_LAT_*). Hasil: img_lat/*.png + img_lat/notes.json."""
from playwright.sync_api import sync_playwright
import os, sys, json, time, subprocess, urllib.request
T = os.path.dirname(os.path.abspath(__file__)) + '/'; R = os.path.abspath(T + '../../../') + '/'; DATA = T + '../data/'; IMG = T + 'img_lat/'; os.makedirs(IMG, exist_ok=True)
PORT = 8779; P = 'http://localhost:%d/index.html' % PORT
MOCK = """window.showDirectoryPicker=async function(){var r=await navigator.storage.getDirectory();return r.getDirectoryHandle('Proyek_Tutorial_Laterit',{create:true});};"""
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

for _f in os.listdir(IMG):
    if _f.endswith('.png'): os.remove(IMG + _f)
def note(k, v):
    """Pencetakan angka hasil tidak boleh menggagalkan pembuatan tutorial: konsol Windows
    bawaannya cp1252, sedangkan teks panel GC-Ex memuat karakter di luar cp1252."""
    NOTES[k] = v
    JEJAK['catatan'] = '%s = %s' % (k, str(v)[:90])
    try:
        print('  ', k, '=', str(v)[:200], flush=True)
    except Exception as _e:
        try: print('  ', k, '= <tidak dapat dicetak di konsol ini:', type(_e).__name__ + '>', flush=True)
        except Exception: pass
try: urllib.request.urlopen(P, timeout=2)
except Exception: subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=R + 'app-dh', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
C = (412150.0, 9620150.0)
SEC = """(()=>{var cx=%f,cy=%f,az=100*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-75*Math.sin(az)).toFixed(1);$('p1n').value=(cy-75*Math.cos(az)).toFixed(1);$('p2e').value=(cx+75*Math.sin(az)).toFixed(1);$('p2n').value=(cy+75*Math.cos(az)).toFixed(1);
  $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=14;$('sliceClip').checked=true;if(!VIEW2D)toggle2D();updatePlot();})()""" % C
ZOOM = "try{Plotly.relayout('plotDiv',{'xaxis.range':[-5,155],'yaxis.range':[150,200]});}catch(e){}"
with sync_playwright() as pw:
    br = pw.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    ctx = br.new_context(viewport={'width': 1600, 'height': 940}, device_scale_factor=1.25, accept_downloads=True)
    ctx.add_init_script(MOCK); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('dialog', lambda d: (d.accept('Habil') if d.type == 'prompt' else d.accept()))
    def shot(name, clip=None):
        SEQ[0] += 1; fn = '%02d_%s.png' % (SEQ[0], name); pg.wait_for_timeout(600)
        pg.screenshot(path=IMG + fn, clip=clip) if clip else pg.screenshot(path=IMG + fn); print('shot', fn, flush=True); return fn
    def ev(js): return pg.evaluate(js)
    PANEL = {'x': 0, 'y': 0, 'width': 480, 'height': 940}
    pg.goto(P); pg.wait_for_timeout(900); ev("localStorage.clear();localStorage.setItem('gcex_user','Habil')"); pg.reload(); pg.wait_for_timeout(900)
    pg.click("#fpCard button.sb"); pg.wait_for_timeout(500)
    for role, f in [('collar', 'SIM_LAT_collar.csv'), ('survey', 'SIM_LAT_survey.csv'), ('assay', 'SIM_LAT_assay.csv'), ('geo', 'SIM_LAT_geologi.csv')]:
        pg.set_input_files("input[onchange*=\"slotFile('%s'\"]" % role, DATA + f); pg.wait_for_timeout(600)
    ev("document.getElementById('dsName').value='Laterit_Simulasi';SA.preview&&SA.preview()")
    pg.set_input_files("input[onchange*=\"addSp('topo'\"]", DATA + 'SIM_LAT_topo_xyz.csv'); pg.wait_for_timeout(500)
    pg.set_input_files("input[onchange*='SA.bmPick']", DATA + 'SIM_LAT_BM_GC.csv'); pg.wait_for_timeout(500)
    pg.click('#btnGo'); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(2500)
    ev("var t=document.getElementById('fpToast');if(t)t.style.display='none'")
    note('nHole', ev('collars.length')); note('nAssay', ev('assays.length')); note('nBlok', ev('BX.m&&BX.m.n')); note('elements', ev('elements'))
    # 1. geologi Zona
    ev("$('bxShow').checked=false;uiTab('Geo');var ci=CAT.findIndex(c=>c.name==='Zona');$('geoAttr').value=ci;$('geoRib').checked=true;geoChanged();if(!$('statsCard').classList.contains('min'))uiStats();setCam(1.25,-1.55,0.75);updatePlot()"); pg.wait_for_timeout(900)
    shot('lat_geologi')
    # 2. preset laterit
    ev("['showLabel','showCollar'].forEach(k=>{var e=$(k);if(e)e.checked=false;});$('geoRib').checked=false;geoChanged();uiTab('SL');slPreset('lat');PT.open['sl']=1;PT.render(true);uiSecOpen('sl',1)"); pg.wait_for_timeout(1200)
    note('lapisan', ev("SL.L.map(l=>[l.name,l.codes.map(c=>slCodeName(SL.ci,c)).join(' '),l.dens,l.moist])"))
    shot('sl_lapisan', PANEL)
    ev("var d=document.querySelector('#slBody details');if(d)d.open=true"); pg.wait_for_timeout(300); shot('sl_kode', PANEL); ev("document.querySelectorAll('#slBody details').forEach(d=>d.open=false)")
    # 3. permukaan
    ev("uiSecOpen('sl',2)"); pg.wait_for_timeout(600)
    R0 = ev("(function(){var R=slEnsure();return {nh:R.nh,nx:R.nx,ny:R.ny,cell:R.cell,topo:R.topo,st:R.st.map(s=>[s.np,s.nc,+s.tav.toFixed(2),s.tmin,s.tmax]),vol:R.vol.map(v=>Math.round(v)),ms:Math.round(R.ms)};})()"); note('srf0', R0)
    shot('sl_permukaan', PANEL)
    ev("setCam(0.95,-1.2,0.6);updatePlot()"); pg.wait_for_timeout(1200); shot('sl_permukaan_3d')
    ev(SEC); pg.wait_for_timeout(1200); ev(ZOOM); pg.wait_for_timeout(700); shot('sl_sayatan_tanpa_sesar')
    # 4. sesar F1 dari koordinat
    tr = [r for r in __import__('csv').DictReader(open(DATA + 'SIM_LAT_sesar.csv', encoding='utf-8'))]
    TR = [[float(r['X']), float(r['Y'])] for r in tr]; note('jejakF1', TR)
    ev("if(VIEW2D)toggle2D();uiTab('FLT')"); pg.wait_for_timeout(500); shot('flt_kosong', PANEL)
    ev("fltNew({name:'F1',tr:%s,zm:'fix',z0:190,dip:65,dd:100,ty:'normal',off:12,tm:'post',up:20,dn:120});fltDirty();PT.open['st']=1;PT.open['st.flt']=1;PT.render(true)" % json.dumps(TR)); pg.wait_for_timeout(1500)
    shot('flt_atribut', PANEL)
    ev("document.getElementById('fltBody').lastElementChild.scrollIntoView({block:'end'})"); pg.wait_for_timeout(300); shot('flt_pengaruh', PANEL)
    note('fltPrep', ev("(function(){var P=fltPrep();return[P.rest.length,P.hb.length,P.syn.length,fltCheck()];})()"))
    ev("uiTab('SL');uiSecOpen('sl',2)"); pg.wait_for_timeout(800)
    R1 = ev("(function(){var R=slEnsure();return {nRest:R.nRest,st:R.st.map(s=>[s.np,s.nc,+s.tav.toFixed(2),s.tmin,s.tmax]),vol:R.vol.map(v=>Math.round(v)),ms:Math.round(R.ms)};})()"); note('srf1', R1)
    shot('sl_permukaan_sesar', PANEL)
    ev("if(VIEW2D)toggle2D();$('sliceClip').checked=false;setCam(0.95,-1.2,0.6);updatePlot()"); pg.wait_for_timeout(1500); shot('flt_3d')
    ev(SEC); pg.wait_for_timeout(1500); ev(ZOOM); pg.wait_for_timeout(700); shot('sl_sayatan_sesar')
    ev("if(VIEW2D)toggle2D();uiTab('Map');try{mapShow&&mapShow(true)}catch(e){}"); pg.wait_for_timeout(1500); shot('flt_map')
    # 5. estimasi
    ev("uiTab('SL');SL.o.el=['Ni','Co','Fe','MgO','SiO2'];SL.o.ra='SiO2';SL.o.rb='MgO';slDirty(true);uiSecOpen('sl',3)"); pg.wait_for_timeout(600)
    shot('sl_estimasi', PANEL)
    # 5b. geostatistik per lapisan (ruang unfold) -> simpan ke lapisan
    ev("$('elementFilter').value='Ni';gsToggle()"); pg.wait_for_timeout(1500)
    ev("slGsSet(1)"); pg.wait_for_timeout(2500)
    note('gsLap', ev("[GS.R.label,GS.R.C.length,+GS.R.st.mean.toFixed(3),+GS.R.st.cv.toFixed(2)]"))
    ev("gsTab('V')"); pg.wait_for_timeout(800); shot('gs_lapisan')
    ev("gsTab('M');gsFitAuto()"); pg.wait_for_timeout(1200); shot('gs_lapisan_model')
    ev("gsTab('K');knaRun()"); pg.wait_for_timeout(3500); note('knaLap', ev("$('knaMsg').innerText.split('Patokan')[0]"))
    ev("gsTab('E')"); pg.wait_for_timeout(600); ev("slFromGs()"); note('gsSimpan', ev("$('slGsMsg').innerText"))
    ev("var b=$('gsDomBox');if(b)b.scrollIntoView({block:'center'})"); pg.wait_for_timeout(400); shot('gs_simpan_lapisan')
    ev("slGsSet('');gsToggle();uiTab('SL');uiSecOpen('sl',3)"); pg.wait_for_timeout(800); shot('sl_estimasi_vario', PANEL)
    ev("slRun()"); pg.wait_for_function("!SL.job", timeout=180000); pg.wait_for_timeout(600)
    note('slMsg', ev("SL.msg.replace(/<[^>]+>/g,'')")); note('slSt', ev("SL.S.st"))
    shot('sl_estimasi_hasil', PANEL)
    ev("$('bxShow').checked=true;bxSet('attr','sl_ni');updatePlot()"); pg.wait_for_timeout(600)
    ev(SEC); pg.wait_for_timeout(1500); ev(ZOOM); pg.wait_for_timeout(700); shot('sl_bm_2d')
    ev("if(VIEW2D)toggle2D();$('sliceClip').checked=false;bxSet('attr','sl_lapisan');setCam(0.95,-1.2,0.6);updatePlot()"); pg.wait_for_timeout(1500); shot('sl_bm_lapisan_3d')
    # 6. laporan
    ev("$('bxShow').checked=false;updatePlot();uiTab('SL');SL.o.pel='Ni';SL.o.cut=0;slDirty(true);uiSecOpen('sl',4)"); pg.wait_for_timeout(600)
    note('lap0', ev("slReport().rows.map(r=>[r.name,r.n,Math.round(r.vol),Math.round(r.wmt),Math.round(r.dmt),r.avg.map(v=>isFinite(v)?+v.toFixed(3):null),isFinite(r.rat)?+r.rat.toFixed(2):null])"))
    shot('sl_laporan', PANEL)
    ev("SL.o.cut=1.5;slDirty(true);uiSecOpen('sl',4)"); pg.wait_for_timeout(500)
    note('lap15', ev("slReport().rows.map(r=>[r.name,r.n,Math.round(r.dmt),r.avg.map(v=>isFinite(v)?+v.toFixed(3):null)])"))
    shot('sl_laporan_cut', PANEL)
    ev("SL.o.cut=0;slDirty(true)")
    ev("SL.v.k=1;SL.v.el='Ni';SL.v.dir='z';SL.v.bw=1;slPanel();uiSecOpen('sl',5)"); pg.wait_for_timeout(600)
    note('valZ', ev("(function(){var Q=slVal();return{nC:Q.nC,cm:+Q.cm.toFixed(3),em:+Q.em.toFixed(3),sw:Q.sw.map(r=>[r[0],r[1]&&+r[1].toFixed(2),r[2]&&+r[2].toFixed(2)])};})()"))
    shot('sl_validasi', PANEL)
    ev("SL.v.dir='x';SL.v.bw=25;slPanel();uiSecOpen('sl',5)"); pg.wait_for_timeout(500); note('valX', ev("(function(){var Q=slVal();return Q.sw.map(r=>[r[0],r[1]&&+r[1].toFixed(2),r[2]&&+r[2].toFixed(2)]);})()"))
    shot('sl_validasi_e', PANEL)
    # 7. project tree
    ev("PT.open['st']=1;PT.open['st.flt']=1;PT.open['sl']=1;PT.render(true);PT.select('sl')"); pg.wait_for_timeout(600); shot('tree', {'x': 0, 'y': 40, 'width': 320, 'height': 520})
    note('errs', errs)
    json.dump(NOTES, open(IMG + 'notes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    br.close()
print('selesai', SEQ[0], 'gambar')
