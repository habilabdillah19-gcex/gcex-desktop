# -*- coding: utf-8 -*-
"""Ukur lamanya LAYAR MEMBEKU di GC-Ex Drill Hole, dengan cara yang sama seperti di Block Model:
jeda antar-frame > 50 ms selama gagang slider sayatan diseret dengan mouse sungguhan.
Dijalankan di atas data latihan SIM_* (yang memang dibundel ke installer)."""
import os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path("/home/claude/gcex-desktop"); PORT = str(random.randint(9100, 9899))   # port acak: port tetap bisa tersangkut peladen lama
MODE=sys.argv[2] if len(sys.argv)>2 else "apaadanya"     # apaadanya | rilis-slider
d=Path(tempfile.mkdtemp(prefix="gcex_dh_")); shutil.copyfile(ROOT/"app-dh"/"index.html",d/"index.html")
os.symlink(ROOT/"docs"/"tutorial-gcex"/"data",d/"data-latihan")
subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen("http://localhost:%s/index.html"%PORT,timeout=1); break
    except Exception: time.sleep(0.4)

JS_MON=r"""(function(){window.__F={gap:[],last:performance.now(),on:true};
  (function loop(){if(!__F.on)return;var t=performance.now();__F.gap.push(t-__F.last);__F.last=t;requestAnimationFrame(loop);})();return true;})"""
JS_STOP=r"""(function(){__F.on=false;var g=__F.gap.filter(function(x){return x>50;});
  return{beku_n:g.length,beku_ms:+g.reduce(function(a,b){return a+b;},0).toFixed(0),
         terlama:+Math.max.apply(null,__F.gap.concat([0])).toFixed(0)};})"""
JS_INFO=r"""(function(){var g=document.getElementById('plotDiv'),dd=(g&&g.data)||[],pts=0,m3=0;
  dd.forEach(function(t){pts+=(t.x&&t.x.length)||0;if(t.type==='mesh3d')m3++;});
  return{trace:dd.length,titik:pts,mesh3d:m3,
    lubang:(window.collars||[]).length,sampel:(window.assays||[]).length,
    bm:(window.BM&&BM.n)||0,perf:(document.getElementById('perfPreset')||{}).value,
    rel:!!(document.getElementById('perfRel')||{}).checked};})"""
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(prefix="gcex_dhc_"),
        args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    er=[]; pg.on("pageerror",lambda e:er.append(str(e)[:140]))
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length>0",timeout=900000)
    pg.wait_for_function("!DLAT.busy",timeout=900000); pg.wait_for_timeout(5000)
    print("data:",pg.evaluate(JS_INFO))
    # buka panel Sayatan supaya slider #pos terlihat, dan nyalakan pemotongan slab
    # buka panel Sayatan lewat tombolnya sendiri (#rbSlice); uiTab/PT.select tidak terjangkau
    # dari page.evaluate di aplikasi ini.
    pg.evaluate("document.getElementById('rbSlice').click()")
    pg.wait_for_timeout(1200)
    pg.evaluate("(function(){var c=document.getElementById('sliceClip');if(c&&!c.checked){c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));}})()")
    pg.wait_for_timeout(4000)
    if MODE=="rilis-slider":
        pg.evaluate("(function(){var e=document.getElementById('perfRel');if(e&&!e.checked){e.checked=true;}})()")
    print("sesudah siap:",pg.evaluate(JS_INFO))
    box=pg.locator("#pos").bounding_box()
    if not box: raise SystemExit("slider #pos tidak terlihat")
    pg.evaluate("(%s)()"%JS_MON)
    pg.mouse.move(box["x"]+box["width"]*0.5, box["y"]+box["height"]/2); pg.mouse.down()
    for k in range(1,25):
        pg.mouse.move(box["x"]+box["width"]*(0.5+0.016*k), box["y"]+box["height"]/2); pg.wait_for_timeout(60)
    pg.mouse.up(); pg.wait_for_timeout(6000)
    r=pg.evaluate(JS_STOP)
    print("%s -> seret slider 24 langkah: membeku %d x, total %d ms, terlama %d ms"
          %(MODE,r["beku_n"],r["beku_ms"],r["terlama"]))
    if er: print("galat:",er[:3])
    ctx.close()
