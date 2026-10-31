"""Ambil tangkapan layar tutorial GC-Ex Drill Hole Ultimate dari aplikasi app-dh (versi terpasang di repo) dengan data simulasi (docs/tutorial/data).
PLOTLY_JS=/path/plotly-2.27.0.min.js -> pakai Plotly asli; tanpa itu dipakai penampil pengganti (tests/stub2d.js + stub3d.js).
Hasil: docs/tutorial/img/*.png + docs/tutorial/img/notes.json (angka hasil untuk keterangan tutorial)."""
from playwright.sync_api import sync_playwright
import os,sys,json,time,subprocess,urllib.request
T=os.path.dirname(os.path.abspath(__file__))+'/';R=os.path.abspath(T+'../../../')+'/';DATA=T+'../data/';IMG=T+'img/';os.makedirs(IMG,exist_ok=True)
DIST=R+'app-dh/';PORT=8777;P='http://localhost:%d/index.html'%PORT
PL=None  # Plotly sudah tertanam di aplikasi
MOCK="""window.showDirectoryPicker=async function(){var r=await navigator.storage.getDirectory();return r.getDirectoryHandle('Proyek_Tutorial_VeinA',{create:true});};"""
NOTES={};SEQ=[0]
for _f in os.listdir(IMG):
    if _f.endswith('.png'):os.remove(IMG+_f)
def note(k,v):
    """Catat angka hasil. Pencetakannya TIDAK boleh menggagalkan pembuatan tutorial:
    konsol Windows bawaannya cp1252, sedangkan teks panel GC-Ex berisi karakter seperti
    '>=' tipografis dan titik tengah -> UnicodeEncodeError di print(), bukan di aplikasinya."""
    NOTES[k]=v
    try:
        print('  ',k,'=',v,flush=True)
    except Exception as _e:
        try:print('  ',k,'= <tidak dapat dicetak di konsol ini:',type(_e).__name__+'>',flush=True)
        except Exception:pass
try:urllib.request.urlopen(P,timeout=2)
except Exception:subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=DIST,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
with sync_playwright() as pw:
    br=pw.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    ctx=br.new_context(viewport={'width':1600,'height':940},device_scale_factor=1.25,accept_downloads=True)
    ctx.add_init_script(MOCK);pg=ctx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
    pg.on('dialog',lambda d:(d.accept('Habil') if d.type=='prompt' else d.accept()))
    def shot(name,clip=None,full=False):
        SEQ[0]+=1;fn='%02d_%s.png'%(SEQ[0],name);pg.wait_for_timeout(500)
        if clip:pg.screenshot(path=IMG+fn,clip=clip)
        else:pg.screenshot(path=IMG+fn)
        print('shot',fn,flush=True);return fn
    def ev(js):return pg.evaluate(js)
    PANEL={'x':0,'y':0,'width':480,'height':940}
    pg.goto(P);pg.wait_for_timeout(900);ev("localStorage.clear();localStorage.setItem('gcex_user','Habil')");pg.reload();pg.wait_for_timeout(900)
    if PL:pg.set_input_files("input[onchange*='SA.addPlotly']",PL);pg.wait_for_function("!!window.Plotly",timeout=60000)
    # 1. jendela awal + folder proyek
    shot('jendela_awal',{'x':240,'y':0,'width':1120,'height':640})
    pg.click("#fpCard button.sb");pg.wait_for_timeout(500)
    # 2. import database + topo + BM GC
    for role,f in [('collar','SIM_collar.csv'),('survey','SIM_survey.csv'),('assay','SIM_assay.csv'),('geo','SIM_geologi.csv')]:
        pg.set_input_files("input[onchange*=\"slotFile('%s'\"]"%role,DATA+f);pg.wait_for_timeout(700)
    ev("document.getElementById('dsName').value='VeinA_Simulasi';SA.preview&&SA.preview()")
    pg.set_input_files("input[onchange*=\"addSp('topo'\"]",DATA+'SIM_topo_xyz.csv');pg.wait_for_timeout(500)
    pg.set_input_files("input[onchange*='SA.bmPick']",DATA+'SIM_BM_GC.csv');pg.wait_for_timeout(500)
    ev("document.getElementById('rCollar').scrollIntoView({block:'start'})");shot('import_database',{'x':240,'y':0,'width':1120,'height':940})
    ev("SA.preview();var d=document.querySelector('#dbSum details');if(d)d.open=true;document.getElementById('dbSum').scrollIntoView({block:'center'})");pg.wait_for_timeout(400)
    b=pg.locator('#dbSum').bounding_box();shot('validasi',{'x':max(0,b['x']-12),'y':max(0,b['y']-12),'width':min(1600-max(0,b['x']-12),b['width']+24),'height':min(940,b['height']+24)});note('valid',ev("(SA.VI||[]).map(r=>r[0]+'|'+r[1]).filter((v,i,a)=>a.indexOf(v)===i)"))
    note('dbSum',ev("document.getElementById('dbSum').innerText"))
    pg.click('#btnGo');pg.wait_for_function("document.getElementById('imp').classList.contains('off')",timeout=180000);pg.wait_for_timeout(2500)
    note('nHole',ev('collars.length'));note('nAssay',ev('assays.length'));note('bx',ev("BX.m&&BX.m.n"))
    # 3. tampilan 3D awal
    ev("$('thr').value='0.3,0.5,1,3';$('clsMode').checked=true;$('bxShow').checked=false;updatePlot();setCam(1.3,-1.5,0.8)");pg.wait_for_timeout(800)
    shot('viewer_3d')
    shot('header',{'x':0,'y':0,'width':1600,'height':62})
    # 4. Warna
    ev("uiTab('Warna')");shot('menu_warna')
    # 5. sayatan vertikal tegak lurus strike lewat tengah vein
    ev("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=12;$('sliceClip').checked=true;uiTab('Slice');updatePlot();})()""")
    pg.wait_for_timeout(500);shot('sayatan_3d')
    ev("if(!VIEW2D)toggle2D()");pg.wait_for_timeout(800);shot('penampang_2d')
    # 6. geologi
    ev("uiTab('Geo');var ci=CAT.findIndex(c=>c.name==='Lith');$('geoAttr').value=ci;$('geoRib').checked=true;geoChanged();updatePlot()");pg.wait_for_timeout(500);shot('geologi_lith')
    # 7. Geological Modelling: domain
    ev("uiTab('GM');$('geoRib').checked=false;if(!$('statsCard').classList.contains('min'))uiStats();updatePlot()")
    ev("gmAddDom('QV_Lensa2');gmAddDom('QV_Splay_HW');gmAct(GM.doms[0].id);PT.open['gm']=1;PT.render(true)")  # vein utama + splay hangingwall-nya  # 0.20: + Tambah domain di Project Tree
    ev("gmAct(GM.doms[0].id)");shot('gm_domain',PANEL)
    # 8. usulan otomatis
    ev("GM._openAuto=true;GM.opt.el='Au';GM.opt.cut=0.5;GM.opt.minL=1;GM.opt.dil=1;GM.opt.scope='all';GM.opt.keep=true;gmPanel()")
    shot('gm_usulan_param',PANEL)
    ev("gmAuto()");note('auto',ev("GM.lastAuto.replace(/<[^>]+>/g,'')"));pg.wait_for_timeout(500);shot('gm_usulan_hasil')
    E2=ev("""(()=>{var r=[];GM.flags&&Object.keys(GM.flags).forEach(id=>{GM.flags[id].forEach(f=>{r.push([id,f[0],f[1]]);});});return r.length;})()""");note('nRunAuto',E2)
    # 9. koreksi flag: hole yang menembus dua vein -> intercept dangkal = QV_HW1
    two=ev("""(()=>{var o=[];Object.keys(GM.flags).forEach(id=>{var L=GM.flags[id];if(L.length>=2&&L[L.length-1][0]-L[0][1]>8)o.push([id,L[0][0],L[0][1]]);});return o;})()""");note('holeDuaVein',len(two))
    hid=two[0][0];note('contohHole',hid)
    ev("""(()=>{var c=collars.find(c=>c[0]===%r),az=315*Math.PI/180;$('sMode').value='P';$('p1e').value=(c[1]-20*Math.sin(az)).toFixed(1);$('p1n').value=(c[2]-20*Math.cos(az)).toFixed(1);$('p2e').value=(c[1]+110*Math.sin(az)).toFixed(1);$('p2n').value=(c[2]+110*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=12;if(!VIEW2D)toggle2D();updatePlot();})()"""%hid)
    ev("gmAct(GM.doms[1].id);gmStart('flag')");pg.wait_for_timeout(500)
    H=ev("""(()=>{var A=dgAx(),H=gmHits(A),r=A.r;return H.filter(h=>h.id===%r).map(h=>({f:h.f,t:h.t,ax:h.A[0]+r.left,ay:h.A[1]+r.top,bx:h.B[0]+r.left,by:h.B[1]+r.top}));})()"""%hid)
    f0,t0=two[0][1],two[0][2];seg=[h for h in H if h['f']>=f0-1 and h['t']<=t0+1];seg.sort(key=lambda h:h['f'])
    a_,b_=seg[0],seg[-1];pg.mouse.move((a_['ax']+a_['bx'])/2,(a_['ay']+a_['by'])/2);pg.mouse.down();pg.mouse.move((b_['ax']+b_['bx'])/2,(b_['ay']+b_['by'])/2,steps=6)
    shot('flag_tarik_hw1');pg.mouse.up();pg.wait_for_timeout(300);note('flagHole',json.dumps(ev("GM.flags[%r]"%hid)))
    shot('flag_hasil_hw1');ev("gmStop()")
    # aturan yang sama untuk hole lain (di tutorial: ulangi per section)
    ev("""(()=>{var hw=GM.doms[1].id;Object.keys(GM.flags).forEach(id=>{var L=GM.flags[id];if(L.length>=2&&L[L.length-1][0]-L[0][1]>8)gmSetRange(id,L[0][0],L[0][1],hw);});gmDirty();})()""")
    note('stat',ev("JSON.stringify(Object.entries(gmStats()).map(([k,v])=>[gmDom(k).name,Object.keys(v.h).length,v.n,+v.l.toFixed(1),+(v.vl/v.lv).toFixed(2)]))"))
    # 10. string kontrol HW/FW: section bor tiap 20 m -> tebal slab 20
    ev("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=20;updatePlot();})()""")
    ev("gmAct(GM.doms[0].id);gmDraft(true)");note('strUtama',ev("GM.lastStr.replace(/<[^>]+>/g,'')"))
    ev("gmAct(GM.doms[1].id);gmDraft(true)");note('strHW1',ev("GM.lastStr.replace(/<[^>]+>/g,'')"));ev("gmAct(GM.doms[0].id)")
    ev("$('pos').value=-20;updatePlot()");pg.wait_for_timeout(500);shot('string_section');shot('string_panel',PANEL)
    i=ev("GM.str.findIndex(s=>s.dom===GM.doms[0].id&&s.role==='FW'&&Math.abs(s.pl.pos+20)<1e-3)");ev("if(!VIEW2D)toggle2D();updatePlot()");pg.wait_for_timeout(500)
    V=ev("""(()=>{var A=dgAx(),F=p2fn(secGeom()),s=GM.str[%d],r=A.r,k=Math.floor(s.pts.length/2),p=dgPx(A,...F(...s.pts[k]));return[p[0]+r.left,p[1]+r.top];})()"""%i)
    pg.mouse.move(V[0]+40,V[1]+40);pg.mouse.move(V[0],V[1],steps=4);pg.wait_for_timeout(250);shot('string_hover')
    pg.mouse.down();pg.mouse.move(V[0]+18,V[1]+10,steps=5);shot('string_edit');pg.mouse.up();pg.keyboard.press('Escape');pg.mouse.move(5,5)
    ev("if(VIEW2D)toggle2D();lyrPreset('gm');$('sliceClip').checked=false;updatePlot();setCam(1.2,-1.6,0.7)");pg.wait_for_timeout(600);shot('model_3d')
    # 10b. Tahap 2: solid vein HW/FW (RBF)
    SOL="JSON.stringify(GM.doms.filter(d=>IM.R[d.id]&&IM.R[d.id].st).map(d=>{var S=IM.R[d.id].st;return[d.name,Math.round(S.vol),+S.tav.toFixed(2),+S.tmax.toFixed(2),S.nH,S.nW,S.nc,S.nin,S.nfl,S.open,Math.round(S.dip),Math.round(S.ddir),Math.round(S.area),+(S.ms/1000).toFixed(2)];}))"
    ev("uiTab('GM');GM._openIm=true;imAll(true)");note('solid',ev(SOL));note('solidMsg',ev("IM.msg.replace(/<[^>]+>/g,'')"))
    ev("var h=[...document.querySelectorAll('#gmBody h4')].find(x=>/Model vein/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(300);shot('solid_panel',PANEL)
    ev("var d=[...document.querySelectorAll('#gmBody details.gmdet')].find(x=>/Parameter domain aktif/.test(x.textContent));if(d){d.open=true;d.scrollIntoView({block:'start'});}");pg.wait_for_timeout(300);shot('solid_param',PANEL)
    ev("uiSideW(560);var h=[...document.querySelectorAll('#gmBody h4')].find(x=>/Model vein/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(500);shot('panel_lebar');ev("uiSideW(292);localStorage.removeItem('gcex_sideW')")
    ev("$('sliceClip').checked=false;if(VIEW2D)toggle2D();updatePlot();setCam(1.2,-1.6,0.7)");pg.wait_for_timeout(700);shot('solid_3d')
    ev("gmAct(GM.doms[0].id);imSet('aS',100);imSet('aD',25);gmOpt('imEll',true);lyrPreset('gm');updatePlot()");pg.wait_for_timeout(700);shot('solid_ell')
    ev("gmOpt('imEll',false);imSet('aS',50);imSet('aD',50);updatePlot()")
    ev("$('pos').value=0;$('sliceClip').checked=true;if(!VIEW2D)toggle2D();updatePlot()");pg.wait_for_timeout(700);shot('solid_2d')
    ev("$('pos').value=-20;$('sliceClip').checked=false;if(VIEW2D)toggle2D();updatePlot()")
    # 11. wireframe dari Leapfrog
    ev("uiTab('Model')");pg.set_input_files("input[onchange='mdImport(this)']",DATA+'QV_Lensa2_Leapfrog.obj');pg.wait_for_function("MD.models.length>0",timeout=60000);pg.wait_for_timeout(800)
    shot('wireframe_import');note('wf',ev("MD.models.map(m=>m.name+' '+m.nv+' v '+m.nt+' f')[0]"))
    ev("uiTab('GM');GM._openWf=true;WF.dom='__new';gmPanel();$('pos').value=-20;if(!VIEW2D)toggle2D();updatePlot()");ev("gmWfStrings(false)");note('wfStr',ev("WF.msg.replace(/<[^>]+>/g,'')"))
    ev("GM.doms.find(d=>/Leapfrog/.test(d.name)).col='#0b7285';gmAct(GM.doms[0].id);WF.dom=GM.doms[0].id;gmDirty()");pg.wait_for_timeout(500);shot('wireframe_iris')
    ev("WF.keep=true;gmWfFlag()");note('wfFlag',ev("WF.msg.replace(/<[^>]+>/g,'')"));note('solidWf',ev("IM.msg.replace(/<[^>]+>/g,'')"));shot('wireframe_panel',PANEL)
    ev("var d=GM.doms.find(d=>/Leapfrog/.test(d.name));if(d){d.vis=false;gmDirty();}")
    ev("try{lyrSet('wf',false)}catch(e){MD.models.forEach(m=>m.vis=false);updatePlot()}")
    # 12. upsert bor infill
    ev("if(VIEW2D)toggle2D();uiTab('Data')");pg.click('#upsBox button.btn-pri');pg.wait_for_timeout(400)
    for role,f in [('collar','SIM_upsert_collar.csv'),('survey','SIM_upsert_survey.csv'),('assay','SIM_upsert_assay.csv'),('geo','SIM_upsert_geologi.csv')]:
        pg.set_input_files("input[onchange*=\"slotFile('%s'\"]"%role,DATA+f);pg.wait_for_timeout(600)
    ev("document.getElementById('upsBan').scrollIntoView({block:'start'})");shot('upsert_pratinjau',{'x':240,'y':0,'width':1120,'height':720})
    note('upsPrev',ev("document.getElementById('upsSum').innerText"))
    nBefore=ev('collars.length')          # jangan patok angka tetap: ukuran data latihan bisa berubah
    pg.click('#btnUps');pg.wait_for_timeout(2500)
    pg.wait_for_function("document.getElementById('imp').classList.contains('off')&&window.collars&&collars.length>%d"%nBefore,timeout=180000);pg.wait_for_timeout(3000)
    note('upsTambah',ev('collars.length')-nBefore)
    note('upsToast',ev("(document.getElementById('fpToast')||{}).innerText||''"));shot('upsert_hasil')
    note('bxAfterUps',ev("window.BX&&BX.m?BX.m.n:0"));ev("var t=document.getElementById('fpToast');if(t)t.style.display='none'")
    ev("uiTab('GM');GM.opt.scope='all';GM.opt.keep=true;gmAct(GM.doms[0].id);gmAuto()");note('autoInfill',ev("GM.lastAuto.replace(/<[^>]+>/g,'')"))
    ev("""(()=>{var hw=GM.doms[1].id;Object.keys(GM.flags).filter(id=>/INF/.test(id)).forEach(id=>{var L=GM.flags[id];if(L.length>=2&&L[L.length-1][0]-L[0][1]>8)gmSetRange(id,L[0][0],L[0][1],hw);});gmDirty();})()""")
    ev("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=20;$('sliceClip').checked=true;updatePlot();})()""")
    ev("gmAct(GM.doms[0].id);gmDraft(true)");note('strUpd',ev("GM.lastStr.replace(/<[^>]+>/g,'')"))
    ev("$('pos').value=0;if(!VIEW2D)toggle2D();updatePlot()");pg.wait_for_timeout(500);shot('upsert_string_baru')
    note('solidInfill',ev(SOL));note('solidInfillMsg',ev("IM.msg.replace(/<[^>]+>/g,'')"))
    # 13. geostatistik domain QV_Utama: sayatan sejajar bidang vein (strike 45, dip 70), slab tebal
    ev("""(()=>{var cx=505000,cy=9012000,az=45*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-130*Math.sin(az)).toFixed(1);$('p1n').value=(cy-130*Math.cos(az)).toFixed(1);$('p2e').value=(cx+130*Math.sin(az)).toFixed(1);$('p2n').value=(cy+130*Math.cos(az)).toFixed(1);
      $('dipS').value=70;$('dipN').value=70;modeChanged();$('pos').value=0;$('thick').value=40;$('sliceClip').checked=true;if(VIEW2D)toggle2D();updatePlot();
      uiTab('Geo');$('domAttr').value=GMCI;domAttrChanged();domAll(false);domSet(0,true);domChips();})()""")
    pg.wait_for_timeout(500);shot('domain_filter',PANEL)
    ev("if(!GS.open)gsToggle();gsRun()");pg.wait_for_timeout(1500);ev("gsTab('S')");pg.wait_for_timeout(600);shot('geostat_statistik')
    note('gsLabel',ev("GS.R&&GS.R.label"));note('gsN',ev("GS.R&&GS.R.C.length"));note('gsMean',ev("GS.R&&GS.R.st&&(+GS.R.st.wmean||+GS.R.st.mean).toFixed(3)"))
    ev("gsTab('V')");pg.wait_for_timeout(600);shot('geostat_variogram')
    ev("gsFitAuto()");pg.wait_for_timeout(800);ev("gsTab('F')");pg.wait_for_timeout(600);shot('geostat_anisotropi')
    ev("gsTab('M')");pg.wait_for_timeout(600);shot('geostat_model');note('model',ev("($('gsParam')||{}).textContent||''")[:900])
    ev("gsTab('K');$('bmBX').value=5;$('bmBY').value=5;$('bmBZ').value=2.5;knaRun()");pg.wait_for_timeout(1500);shot('geostat_kna');note('kna',ev("(document.getElementById('knaMsg')||{}).innerText||''")[:300])
    ev("knaApply()");note('knaPass1',ev("[$('okM1').value,$('okN1').value,$('okX1').value,$('okH1').value].join(',')"))
    ev("gsTab('E');$('bmDom').value='all';okRun()");pg.wait_for_timeout(500)
    pg.wait_for_function("!window.OKJ",timeout=600000);pg.wait_for_timeout(1200);shot('estimasi_ok_hasil')
    note('ok',ev("window.BM?BM.n:0"));note('okMsg',ev("(document.getElementById('okRes')||document.getElementById('okMsg')).innerText")[:600])
    ev("$('bmShow').checked=true;$('bmAttr').value='E';$('bxShow').checked=false;$('sliceClip').checked=false;$('showDH').checked=true;updatePlot();setCam(1.3,-1.5,0.8);var h=[...document.querySelectorAll('h5')].find(x=>/Tampilan block model/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(800);shot('estimasi_ok_3d')
    ev("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=5;$('sliceClip').checked=true;if(!VIEW2D)toggle2D();updatePlot();})()""");pg.wait_for_timeout(800);shot('estimasi_ok_2d')
    # 13b. simpan parameter ke domain (tab Uji estimasi)
    ev("gsTab('E');var b=document.getElementById('gsDomBox');if(b)b.scrollIntoView({block:'center'})");pg.wait_for_timeout(300)
    pg.click('#gsDomBox button');pg.wait_for_timeout(300);note('gsDomMsg',ev("$('gsDomMsg').innerText"));shot('simpan_ke_domain')
    ev("meFromGs(GM.doms[1].id)")
    # 13c. Model Estimation
    ev("if(GS.open)gsToggle();$('domAttr').value=-1;domAttrChanged();$('bmShow').checked=false;$('sliceClip').checked=false;if(VIEW2D)toggle2D();uiTab('ME');ME._openPar=true;mePanel()");pg.wait_for_timeout(400);shot('me_panel',PANEL)
    # 0.20: domain aktif dari node Geostatistik & Model Estimation di Project Tree
    ev("var d=GM.doms.find(x=>x.name==='QV_Utama');PT.open['gs']=1;PT.select('gs.d.'+d.id)");pg.wait_for_timeout(1800);shot('dom20_gs',{'x':1040,'y':0,'width':560,'height':560})
    ev("var d=GM.doms.find(x=>x.name==='QV_Utama');PT.open['me']=1;PT.select('me.d.'+d.id);if(GS.open)gsToggle()");pg.wait_for_timeout(800);shot('dom20_me',PANEL)
    ev("var d=GM.doms.find(x=>/Leapfrog/.test(x.name));if(d)ME.sel[d.id]=false;meRun()");pg.wait_for_function("!ME.job",timeout=900000);pg.wait_for_timeout(600)
    MER="JSON.stringify(ME.store.runs.filter(q=>q.id===Math.max.apply(null,ME.store.runs.map(r=>r.id))).map(q=>[q.dom,q.first,q.nHole,q.nIn,q.nAff,q.nEst,q.nAddC,q.nRev,q.nFail,q.cnt,q.v?+q.v.comp.toFixed(3):null,q.v?+q.v.mean.toFixed(3):null,q.v&&q.v.gc!=null?+q.v.gc.toFixed(3):null,q.v?Math.round(q.v.vol):0,q.v?Math.round(q.v.ton):0,q.v?Math.round(q.v.metal):0,q.v?Math.round(q.v.metalGc):0,q.ms,(q.holes||[]).join(' ')]))"
    note('me1',ev(MER));note('meBM',ev("[BX.m._meBase.n,BX.m.n,meGcAttr()]"))
    ev("var h=[...document.querySelectorAll('#meBody h4')].find(x=>/Validasi/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(300);shot('me_hasil',PANEL)
    ev("meShow();setCam(1.3,-1.5,0.8)");pg.wait_for_timeout(900);shot('me_bm3d')
    ev("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=2.5;$('sliceClip').checked=true;if(!VIEW2D)toggle2D();updatePlot();})()""");pg.wait_for_timeout(800);shot('me_bm2d')
    # 13d. infill tahap 2 -> koreksi hanya sekitar bor baru
    ev("if(VIEW2D)toggle2D();$('sliceClip').checked=false;uiTab('Data')");pg.click('#upsBox button.btn-pri');pg.wait_for_timeout(400)
    for role,f in [('collar','SIM_upsert2_collar.csv'),('survey','SIM_upsert2_survey.csv'),('assay','SIM_upsert2_assay.csv'),('geo','SIM_upsert2_geologi.csv')]:
        pg.set_input_files("input[onchange*=\"slotFile('%s'\"]"%role,DATA+f);pg.wait_for_timeout(600)
    nBefore2=ev('collars.length')
    pg.click('#btnUps');pg.wait_for_timeout(2500)
    pg.wait_for_function("document.getElementById('imp').classList.contains('off')&&window.collars&&collars.length>%d"%nBefore2,timeout=180000);pg.wait_for_timeout(3000)
    ev("var t=document.getElementById('fpToast');if(t)t.style.display='none'")
    ev("uiTab('GM');GM.opt.scope='all';GM.opt.keep=true;GM.opt.dil=2;gmAct(GM.doms[0].id);gmAuto();GM.opt.dil=1")
    note('autoInfill2',ev("GM.lastAuto.replace(/<[^>]+>/g,'')"))
    ev("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=20;$('sliceClip').checked=false;updatePlot();gmAct(GM.doms[0].id);gmDraft(true);})()""")
    note('solidInfill2',ev("IM.msg.replace(/<[^>]+>/g,'')"))
    ev("uiTab('ME');ME._openPar=false;var d=GM.doms.find(x=>/Leapfrog/.test(x.name));if(d)ME.sel[d.id]=false;mePanel()");pg.wait_for_timeout(300)
    note('mePending',ev("[...document.querySelectorAll('#meBody .gmstate')][1].innerText"))
    ev("var h=[...document.querySelectorAll('#meBody h4')].find(x=>/Jalankan/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(300);shot('me_tertunda',PANEL)
    ev("meRun()");pg.wait_for_function("!ME.job",timeout=900000);pg.wait_for_timeout(600);note('me2',ev(MER))
    ev("var h=[...document.querySelectorAll('#meBody h4')].find(x=>/Validasi/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(300);shot('me_koreksi',PANEL)
    ev("meShow();$('sliceClip').checked=false;if(VIEW2D)toggle2D();updatePlot();setCam(1.3,-1.5,0.8)");pg.wait_for_timeout(900)
    ev("meApply(true);BX.ui.attr='est_run';bxPanel();updatePlot()");pg.wait_for_timeout(800);shot('me_run')
    with pg.expect_download() as d:ev("uiTab('ME');meCsv()")
    d.value.save_as(IMG+'_me.csv');note('meCsv',ev("ME.msg.replace(/<[^>]+>/g,'')"));os.remove(IMG+'_me.csv')
    # 13e. Data Spasial: topografi versi baru
    ev("$('sliceClip').checked=false;if(VIEW2D)toggle2D();BX.ui.fAttr='';$('bxShow').checked=false;$('ovTopoL').checked=true;uiTab('SP')");pg.set_input_files("#spBody input[onchange^=\"spAdd('topo'\"]",DATA+'SIM_topo_xyz_nov.csv')
    pg.wait_for_function("spL('topo').length===2&&!SPV.busy",timeout=60000);ev("spSet('topo',spL('topo')[0].id,'show',true);setCam(1.3,-1.5,0.8)");pg.wait_for_timeout(900);shot('data_spasial')
    note('spMsg',ev("SPV.msg.replace(/<[^>]+>/g,'')"));ev("spSet('topo',spL('topo')[0].id,'show',false);$('ovTopoL').checked=false;updatePlot()")
    # 14. export
    ev("if(GS.open)gsToggle();if(VIEW2D)toggle2D();uiTab('Data')")
    with pg.expect_download() as d:ev("gxDbExport()")
    d.value.save_as(IMG+'_export_db.zip');note('exportDb',ev("document.getElementById('gxMsg').innerText"));shot('export_database',PANEL)
    import zipfile;note('zipIsi',zipfile.ZipFile(IMG+'_export_db.zip').namelist());os.remove(IMG+'_export_db.zip')
    # 15. layer
    ev("var t=document.getElementById('fpToast');if(t)t.style.display='none';$('sliceClip').checked=false;if(VIEW2D)toggle2D();lyrState('open');lyrPreset('dh');setCam(1.3,-1.5,0.8)");pg.wait_for_timeout(600);shot('layer_panel');ev("lyrState('mini')");pg.wait_for_timeout(600);shot('layer_strip');ev("lyrState('off')")
    # 16. folder proyek
    ev("SA.pjMenu()");pg.wait_for_timeout(500);shot('proyek_menu',{'x':0,'y':0,'width':1200,'height':720});ev("SA.pjMenu()")
    ev("FP.restoreUI()");pg.wait_for_timeout(800);shot('proyek_pulihkan');ev("document.getElementById('fpDlg').style.display='none'")
    note('rev',ev('FP.base'))
    # 16b. struktur geologi
    ev("uiTab('GM');gmAct(GM.doms[0].id);if(VIEW2D)toggle2D();updatePlot()");v0=ev("Math.round(IM.R[GM.doms[0].id].st.vol)")
    ev("uiTab('Model')");pg.set_input_files("#stBody input[type=file]",DATA+'SIM_struktur.csv');pg.wait_for_timeout(1200)
    note('strN',ev("STR.P.length"));note('strVol',[v0,ev("Math.round(IM.R[GM.doms[0].id].st.vol)"),ev("IM.R[GM.doms[0].id].st.nst"),ev("IM.R[GM.doms[0].id].st.nstx")])
    ev("STR.sel=STR.P[0].id;stPanel();document.getElementById('stBody').scrollIntoView({block:'start'})");pg.wait_for_timeout(400);shot('struktur_panel',PANEL)
    ev("lyrPreset('gm');STR.sz=7;updatePlot();setCam(1.15,-1.5,0.55)");pg.wait_for_timeout(1500);shot('struktur_3d')
    ev("uiTab('GM');$('pos').value=0;$('sliceClip').checked=true;if(!VIEW2D)toggle2D();updatePlot();STR.sd.dip=65;STR.sd.az=135;STR.sd.ket='kontak HW';stMode('gm2d')");pg.wait_for_timeout(1200)
    A=ev("(()=>{var A=dgAx(),r=A.r;return[r.left+A.x._offset+A.x._length*0.55,r.top+A.y._offset+A.y._length*0.35];})()")
    pg.mouse.click(A[0],A[1]);pg.wait_for_timeout(900);pg.mouse.click(A[0]+60,A[1]+90);pg.wait_for_timeout(900)
    note('strFlag',ev("STR.P.filter(p=>p.fid==='gm').map(p=>p.no+':'+p.dip+'/'+p.az)"))
    ev("var h=[...document.querySelectorAll('#gmBody h4')].find(x=>/Flag struktur/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(300);shot('struktur_flag')
    pg.keyboard.press('Escape');ev("stMode('x');STR.mode=null;if(VIEW2D)toggle2D();uiTab('Model');stAddCenter();stNudge('f');stNudge('u');var e=document.querySelector('#stBody .stnud');if(e)e.scrollIntoView({block:'center'})");pg.wait_for_timeout(600);shot('struktur_manual',PANEL)
    ev("stDel(STR.sel)")
    # 16c. Map
    ev("uiTab('Map')");pg.wait_for_timeout(3000);shot('map_layer')
    pg.set_input_files("#mapBody input[type=file][onchange^='mapPtImport']",DATA+'SIM_pickup_survey.csv');pg.wait_for_timeout(1500)
    ev("MAP.PF[0].lab='none';mapZoom(MAP.PF[0].id);mapPanel()");pg.wait_for_timeout(1500);note('pickN',ev("MAP.PF[0].P.length"));shot('map_pickup')
    ev("MAP.kind='str';MAP.type='Vein / urat';mapPanel();mapStart()");pg.wait_for_timeout(300)
    T=ev("(()=>{var A=mapAx(),P=MAP.PF[0].P.filter(p=>p[4]==='VEIN_HW');return P.slice(4,22).map(p=>{var q=mapPx(A,[p[1],p[2]]);return[q[0]+A.r.left+3,q[1]+A.r.top-2];});})()")
    for t in T:pg.mouse.move(t[0],t[1]);pg.wait_for_timeout(60);pg.mouse.click(t[0],t[1]);pg.wait_for_timeout(120)
    pg.keyboard.press('Enter');pg.wait_for_timeout(400)
    ev("MAP.kind='alt';MAP.name='SIL';MAP.col='#e8590c';mapPanel()")
    B=ev("(()=>{var A=mapAx(),P=MAP.PF[0].P.filter(p=>/VEIN/.test(p[4])),x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;P.slice(8,30).forEach(p=>{x0=Math.min(x0,p[1]);x1=Math.max(x1,p[1]);y0=Math.min(y0,p[2]);y1=Math.max(y1,p[2]);});return[[x0-8,y0-4],[x1+2,y0-10],[x1+8,y1+4],[x0-2,y1+10]].map(q=>{var p=mapPx(A,q);return[p[0]+A.r.left,p[1]+A.r.top];});})()")
    for t in B:pg.mouse.click(t[0],t[1]);pg.wait_for_timeout(150)
    pg.keyboard.press('Enter');pg.wait_for_timeout(400);ev("mapStart();MAP.mode=null;MAP.sel=null;mapPanel();mapDraw()");note('mapF',ev("MAP.F.map(f=>f.kind+':'+f.name+':'+f.pts.length)"))
    ev("var h=[...document.querySelectorAll('#mapBody h4')].find(x=>/Digitasi/.test(x.textContent));if(h)h.scrollIntoView({block:'start'})");pg.wait_for_timeout(300);shot('map_digit')
    ev("mapZoom();MAP.title='Peta Geologi Vein A (latihan)';MAP.sub='Data simulasi GC-Ex';MAP.auth='Habil';mapPanel()");pg.wait_for_timeout(1500)
    SEQ[0]+=1;fnl='%02d_map_layout.png'%SEQ[0]
    with pg.expect_download() as dl:ev("mapLayoutOut('png')")
    dl.value.save_as(IMG+fnl);print('shot',fnl)
    ev("uiTab('GM')");pg.wait_for_timeout(800)
    # 17. vein bercabang (proyek terpisah, data SIM_split_*)
    ctx2=br.new_context(viewport={'width':1600,'height':940},device_scale_factor=1.25,accept_downloads=True)

    ctx2.add_init_script(MOCK.replace('Proyek_Tutorial_VeinA','Proyek_Tutorial_Split'));pg=ctx2.new_page();pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('dialog',lambda d:(d.accept('Habil') if d.type=='prompt' else d.accept()))
    pg.goto(P);pg.wait_for_timeout(900)
    if PL:pg.set_input_files("input[onchange*='SA.addPlotly']",PL);pg.wait_for_function("!!window.Plotly",timeout=60000)
    pg.click("#fpCard button.sb");pg.wait_for_timeout(500)
    for role,f in [('collar','SIM_split_collar.csv'),('survey','SIM_split_survey.csv'),('assay','SIM_split_assay.csv'),('geo','SIM_split_geologi.csv')]:
        pg.set_input_files("input[onchange*=\"slotFile('%s'\"]"%role,DATA+f);pg.wait_for_timeout(600)
    ev("document.getElementById('dsName').value='VeinSplit_Simulasi';SA.preview&&SA.preview()")
    pg.set_input_files("input[onchange*=\"addSp('topo'\"]",DATA+'SIM_topo_xyz.csv');pg.wait_for_timeout(400)
    pg.set_input_files("input[onchange*='SA.bmPick']",DATA+'SIM_split_BM_GC.csv');pg.wait_for_timeout(500)
    pg.click('#btnGo');pg.wait_for_function("document.getElementById('imp').classList.contains('off')",timeout=120000);pg.wait_for_timeout(2500)
    ev("uiTab('GM');gmAddDom('QVS_Utama');gmAddDom('QVS_Cabang');GM.doms[1].col='#1971c2';gmAct(GM.doms[0].id);GM.opt.el='Au';GM.opt.cut=0.5;GM.opt.minL=1;GM.opt.dil=1;GM.opt.scope='all';GM.opt.keep=true;gmAuto()")
    ev("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
      $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=20;if(!VIEW2D)toggle2D();updatePlot();})()""")
    ev("(LYR.items=lyrDef()).forEach(function(it){if(it.k==='bx'||it.k==='bm')it.c.set(false);});updatePlot()");pg.wait_for_timeout(400)
    note('splitFlag',ev("""(()=>{var cb=GM.doms[1].id,n=0;Object.keys(GM.flags).forEach(id=>{var L=GM.flags[id];if(L.length>=2&&L[L.length-1][0]-L[L.length-2][1]>=4){var f=L[L.length-1];gmSetRange(id,f[0],f[1],cb);n++;}});gmDirty();return n;})()"""))
    shot('split_flag');ev("gmSetPar(GM.doms[1].id,GM.doms[0].id)");pg.wait_for_timeout(300);shot('split_domain',PANEL)
    ev("gmAct(GM.doms[0].id);gmDraft(true);gmAct(GM.doms[1].id);gmDraft(true);gmAct(GM.doms[0].id);imAll(true);$('sliceClip').checked=true;updatePlot()");pg.wait_for_timeout(700);shot('split_2d')
    note('split',ev("(()=>{var g=imGrpStat(GM.doms[0].id),R=GM.doms.map(d=>IM.R[d.id].st);return{vU:Math.round(R[0].vol),vC:Math.round(R[1].vol),vol:Math.round(g.vol),ov:Math.round(g.ov),nj:R[1].nj,inU:R[0].nin+'/'+R[0].nfl,inC:R[1].nin+'/'+R[1].nfl};})()"))
    ev("GM._openIm=true;gmPanel();var b=document.querySelector('#gmBody .grpbox');if(b)b.scrollIntoView({block:'center'})");pg.wait_for_timeout(300);shot('split_panel',PANEL)
    ev("$('sliceClip').checked=false;if(VIEW2D)toggle2D();lyrPreset('gm');(LYR.items=lyrDef()).forEach(function(it){if(it.k==='bx'||it.k==='bm')it.c.set(false);});updatePlot();setCam(1.6,0.9,0.5)");pg.wait_for_timeout(800);shot('split_3d')
    ev("""(()=>{var cx=505000,cy=9012000,az=45*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-130*Math.sin(az)).toFixed(1);$('p1n').value=(cy-130*Math.cos(az)).toFixed(1);$('p2e').value=(cx+130*Math.sin(az)).toFixed(1);$('p2n').value=(cy+130*Math.cos(az)).toFixed(1);
      $('dipS').value=70;$('dipN').value=70;modeChanged();$('pos').value=0;$('thick').value=60;$('sliceClip').checked=true;updatePlot();
      uiTab('Geo');$('domAttr').value=GMGI;domAttrChanged();domAll(false);domSet(0,true);domChips();})()""")
    ev("if(!GS.open)gsToggle();gsRun()");pg.wait_for_timeout(1500);ev("gsFitAuto()");pg.wait_for_timeout(800);ev("gsTab('E');$('bmBX').value=5;$('bmBY').value=5;$('bmBZ').value=2.5");pg.wait_for_timeout(300)
    note('splitGs',ev("GS.R&&GS.R.st?GS.R.st.n:0"));pg.click("#gsDomBox button");pg.wait_for_timeout(300);ev("if(GS.open)gsToggle()")
    ev("uiTab('ME');ME.opt.add=true;meRun()");pg.wait_for_function("!ME.job",timeout=600000);pg.wait_for_timeout(500)
    note('splitMe',ev("ME.store.runs.map(q=>({dom:q.dom,nIn:q.nIn,nEst:q.nEst,nAdd:q.nAddC,nComp:q.nComp}))"));shot('split_me',PANEL)
    print('ERR',errs);json.dump(NOTES,open(IMG+'notes.json','w'),indent=1,ensure_ascii=False)
    br.close()
