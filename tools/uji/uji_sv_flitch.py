# -*- coding: utf-8 -*-
"""Solid Vein Aktual: flitch kerja milik menu sendiri, tidak terikat flitch aktif Dig Block / As-Mined (pemilik 10-11-2026).
Data sintetis. Pemakaian: python tools/uji/uji_sv_flitch.py"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); os.symlink(DATA, d / "data-latihan")
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
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    a = pg.evaluate("""(async function(){var w=function(t){return new Promise(function(r){setTimeout(r,t);});};
      lySet('fh',2.5);lyU().bot='';lySet('top',238.75);lyApply();await w(1500);var g0=lyBench();
      var m=BX.m,cx=0,cy=0,nn=Math.min(m.n,5000);for(var i=0;i<nn;i++){cx+=m.x[i];cy+=m.y[i];}cx=cx/nn+offX;cy=cy/nn+offY;var mk=function(z,n){var s='';for(var i=0;i<n;i++)s+=(i+1)+','+(cx+Math.cos(i)*8).toFixed(3)+','+(cy+Math.sin(i)*8).toFixed(3)+','+(z+0.3*(i%3)).toFixed(3)+',OB\\n';return s;};
      var d=SV.D();d.per.push({id:'pz',name:'Uji',from:'',to:'',polys:[],par:{},res:null});d.cur='pz';d.lv=null;
      await SV.importFiles([new File([mk(272.6,10)],'ACT_SO261106OB_272-5_271_ZX.csv'),new File([mk(274.4,12)],'ACT_SO261104OB_275-5_274_ZX.csv')]);
      var imp={lv:SV.lvB(),on:SV.lvOn(),n:SV.ptsOn().length};      SV.fileOn('ACT_SO261106OB_272-5_271_ZX.csv',false);SV.fileOn('ACT_SO261104OB_275-5_274_ZX.csv',false);await w(500);
      SV.fileOn('ACT_SO261104OB_275-5_274_ZX.csv',true);await w(2500);
      var T=document.getElementById('plotDiv').data||[],tt=T.filter(function(t){return /^Titik atap/.test(t.name||'');});
      var o={imp:imp,np:SV.D().pts.length,files:SV.files().map(function(f){return [f.c,f.n,f.top,f.bot];}),off:SV.D().filt.off,on:SV.ptsOn().length,show:SV.show,names:T.map(function(t){return t.name;}).slice(0,30),tampil:tt.length?tt[0].x.length:0,lv:SV.lvB(),lvOn:SV.lvOn(),v2d:!!VIEW2D,flGlobal:!!BX.ui.fl,globBench:lyBench(),g0:g0,pos:+document.getElementById('pos').value};
      SV.dig();await w(800);o.dig=!!DG.svm;o.dgOn=DG.on;DG.cur=[[cx-5,cy-5],[cx+5,cy-5],[cx+5,cy+5],[cx-5,cy+5]];o.cur=DG.cur.length;dgFinish(true);await w(800);o.svmAfter=DG.svm;
      var p=SV.per();o.poly=p.polys.map(function(v){return [v.top,v.bot];});o.msg=SV.msg;o.sel=PT.sel;
      SV.flSet('top',277);await w(300);o.lv2=SV.lvB();o.glob2=lyBench();return o;})()"""); print(a)
    cek(a["imp"]["lv"] == [275.5, 274] and a["imp"]["on"] and a["imp"]["n"] == 12, "selesai import: flitch kerja = flitch file terakhir, plan dibuka, 12 titik siap didigit")
    cek(a["tampil"] == 12 and a["np"] == 22, "mencentang file RL 275,5-274 langsung menampilkan 12 titiknya (CSV tanpa judul, kolom kode teks: baris pertama tidak hilang) di plan (flitch global 238,75 tetap)")
    cek(a["lv"] == [275.5, 274] and a["lvOn"] and a["v2d"] and abs(a["pos"] - 274.75) < 1e-6, "flitch kerja Solid Vein = RL 275,5-274 dan plan 2D dibuka di RL itu")
    cek(a["globBench"] == a["g0"] and not a["flGlobal"], "flitch Dig Block / As-Mined (lyBench) tidak diubah; tampilan flitch global dimatikan")
    cek(a["dig"] and a["poly"] == [[275.5, 274]], "poligon hasil digit tercatat di flitch kerja RL 275,5-274")
    cek(a["lv2"] == [277, 275.5] and a["glob2"] == a["g0"], "isian RL atas di panel Solid Vein hanya mengubah flitch kerja menu ini")
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: %d" % len(gagal) if gagal else "\nLULUS")
sys.exit(1 if gagal else 0)
