# -*- coding: utf-8 -*-
"""DH 0.24.66 / 0.24.69 (web-src-dh/sumber_dh.js): sumber sampel estimasi & domain wireframe eksak. Data latihan fiktif.
Diperiksa:
  1. wireframe QV_Lensa2_Leapfrog.obj dikunci ke domain baru -> interval bor di dalamnya di-flag otomatis, domain siap estimasi
  2. bawaan soft boundary = semua sampel database seperti Surpac: komposit saat run = seluruh database; hard boundary
     = komposit domain; di luar run (validasi) tetap komposit domain; blok tetap hanya di dalam wireframe
  3. panel parameter punya pilihan Soft / Hard boundary; mengubahnya mengubah hash parameter (domain diestimasi ulang)
Pemakaian: python tools/uji/uji_sumber_dh.py"""
import os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes())
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
gagal = []
def cek(ok, pesan):
    print(("  ok   " if ok else "  GAGAL ") + pesan)
    if not ok: gagal.append(pesan)
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
    pg = ctx.new_page(); ERR = []; pg.on("pageerror", lambda e: ERR.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto(P); pg.wait_for_timeout(1500)
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(400)
    inp = lambda k: pg.locator('input[onchange*="%s"]' % k).first
    for role, f in [("collar", "SIM_collar.csv"), ("survey", "SIM_survey.csv"), ("assay", "SIM_assay.csv")]:
        inp("slotFile('%s'" % role).set_input_files(str(DATA / f)); pg.wait_for_timeout(1200)
    pg.evaluate("document.getElementById('dsName').value='Uji_sumber';try{SA.preview()}catch(e){};SA.go()")
    pg.wait_for_function("document.getElementById('imp').classList.contains('off') && window.collars && collars.length>0", timeout=300000); pg.wait_for_timeout(3000)
    pg.evaluate("(function(){var i=document.createElement('input');i.type='file';i.id='wfIn';i.style.display='none';i.onchange=function(){mdImport(i,'geo');};document.body.appendChild(i);})()")
    pg.set_input_files('#wfIn', str(DATA / "QV_Lensa2_Leapfrog.obj")); pg.wait_for_timeout(3000)
    a = pg.evaluate("""(function(){var m=MD.models[0];if(!m)return {err:'tanpa wireframe'};var d=gmAddDom('WF_Lensa');wfxPakai(d.id,m.name);var R=meRuns(d.id),n=0;Object.keys(R).forEach(function(h){n+=R[h].length;});
      var r=Math.PI/180,vM=[1,0,0],vS=[0,0,-1],vN=[0,1,0];d.est={el:'Au',L:1,tc:0,nd:[1,1,1],m:{vM:vM,vS:vS,vN:vN,c0:0.1,cs:[0.9],A:[40],B:[30],Cn:[10]},P:[{mult:1,min:2,max:12,mph:0}],tr:'',src:'uji',n:0};gmDirty(true);
      return {wfx:d.wfx,on:imPar(d).on,holes:Object.keys(R).length,runs:n,ready:meDomsReady().map(function(x){return x.name;}),id:d.id,m:m.name};})()""")
    print("1", a)
    cek(a.get("wfx") and a["on"] and a["holes"] > 0 and "WF_Lensa" in a["ready"], "1 wireframe dikunci -> %d lubang di-flag otomatis, domain siap estimasi" % a.get("holes", 0))
    b = pg.evaluate("""(function(){var d=gmDom('%s'),P0=meParOf(d),c0=meComps(d,P0);SUMBER.on=true;var c1,c2,h1=imHash(JSON.stringify(meParOf(d)));try{c1=meComps(d,meParOf(d));SUMBER.set(d.id,'hard');c2=meComps(d,meParOf(d));}finally{SUMBER.on=false;}
      var h2=imHash(JSON.stringify(meParOf(d))),html=meParHtml(d.id);SUMBER.set(d.id,'soft');var html2=meParHtml(d.id);
      var mean=function(C){var s=0;C.forEach(function(c){s+=c.v;});return s/C.length;};
      return {n0:c0.length,n1:c1.length,n2:c2.length,m0:mean(c0),m1:mean(c1),hchg:h1!==h2,ui:html.indexOf('value="hard" selected')>=0&&html2.indexOf('value="soft" selected')>=0,all:assays.length};})()""" % a["id"])
    print("2", b)
    cek(b["n1"] > 3 * b["n0"] and b["n0"] >= 3 and b["n2"] == b["n0"], "2 soft (bawaan): komposit = semua sampel (%d); hard = komposit domain (%d); di luar run = komposit domain (%d)" % (b["n1"], b["n2"], b["n0"]))
    cek(b["m1"] < b["m0"], "2 kadar rata-rata komposit turun saat sampel waste ikut (%.3f -> %.3f)" % (b["m0"], b["m1"]))
    cek(b["ui"] and b["hchg"], "3 pilihan Soft / Hard boundary tampil & mengubah hash parameter")
    pg.evaluate("uiTab('BM');AOI.dlg();(function(){var m=MD.models[0];mdLocal(m);var x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,z0=1e18,z1=-1e18;for(var i=0;i<m.nv;i++){var x=m.v[i*3],y=m.v[i*3+1],z=m.v[i*3+2];x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);z0=Math.min(z0,z);z1=Math.max(z1,z);}Object.assign(AOI.cfg,{x0:x0-2,x1:x1+2,y0:y0-2,y1:y1+2,zb:z0-2,zt:z1+2,bx:2,by:2,bz:2,snap:false,topo:0,pit:0,poly:'',mode:'penuh',name:'uji'});AOI.body();AOI.go();})()")
    pg.wait_for_function("!AOI.busy && window.BX && BX.m", timeout=600000); pg.wait_for_timeout(800)
    pg.evaluate("uiTab('ME');meRun()"); pg.wait_for_function("ME.store && ME.store.runs.length>0 && !ME.job", timeout=600000); pg.wait_for_timeout(800)
    c = pg.evaluate("""(function(){var B=ME.store.B,d=GM.doms[0],R=meGrpR(d),n=0,luar=0;for(var i=0;i<B.x.length;i++){if(B.est[i]<=-90)continue;n++;if(!R.W.f(B.x[i]-offX,B.y[i]-offY,B.z[i]))luar++;}return {n:n,luar:luar,msg:ME.msg.replace(/<[^>]+>/g,' ')};})()""")
    print("4", c)
    cek(c["n"] > 0 and c["luar"] == 0, "2 blok terestimasi %d, semuanya di dalam wireframe (di luar: %d)" % (c["n"], c["luar"]))
    cek(not ERR, "tanpa galat halaman: %s" % ERR[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
