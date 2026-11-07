# -*- coding: utf-8 -*-
"""CSV pick-up tanpa baris judul berbentuk ID,X,Y,Z,Kode harus terbaca sebagai koordinat
yang benar -- bukan tergeser satu kolom. Bentuk berkasnya meniru berkas pemilik."""
import os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path("/home/claude/gcex-desktop"); PORT=str(random.randint(9100,9899))
SRC=sys.argv[1] if len(sys.argv)>1 else str(ROOT/"app"/"index.html")
d=Path(tempfile.mkdtemp()); shutil.copyfile(SRC,d/"index.html")
os.symlink(ROOT/"docs"/"tutorial-gcex"/"data",d/"data-latihan")
# berkas tiruan: ID, Easting, Northing, RL, kode -- tanpa baris judul (seperti Gambar 2 & 3)
atap=[]; lantai=[]
for i in range(1,61):
    atap.append("%d,%0.0f,%0.0f,%0.3f,204"%(i,558990+i%12,9010220+i%15,271.6+(i%7)*0.12))
    lantai.append("%d,%0.0f,%0.0f,%0.3f,204"%(i,558990+i%12,9010220+i%15,270.6+(i%7)*0.10))
(d/"roof.csv").write_text("\n".join(atap),encoding="utf-8")
(d/"floor.csv").write_text("\n".join(lantai),encoding="utf-8")
subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen("http://localhost:%s/index.html"%PORT,timeout=1); break
    except Exception: time.sleep(0.4)
print("sumber:",SRC)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(),args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(2500)
    for slot,nama in (("pts","floor.csv"),("ptsR","roof.csv")):
        pg.evaluate("""async function(a){var t=await (await fetch(a.n)).text();
          var f=new File([t],a.n,{type:'text/csv'});amPtsFile([f],a.s);}""",{"n":nama,"s":slot})
    pg.wait_for_timeout(4000)
    r=pg.evaluate("""(function(){var D=amD(),o={};['pts','ptsR'].forEach(function(k){
      var P=D[k]||[],rng=function(f){var v=P.map(f).filter(isFinite);return v.length?[Math.min.apply(0,v),Math.max.apply(0,v)]:null;};
      o[k]={n:P.length,x:rng(function(q){return q.x;}),y:rng(function(q){return q.y;}),z:rng(function(q){return q.z;})};});return o;})()""")
    for k in ("pts","ptsR"):
        v=r[k]; print("  %-5s n=%d x=%s y=%s z=%s"%(k,v["n"],v["x"],v["y"],v["z"]))
    def wajar(v):
        return (v["n"]>0 and v["x"] and v["y"] and v["z"]
                and 558000<=v["x"][0]<=560000 and 9009000<=v["y"][0]<=9011000
                and 200<=v["z"][0]<=400)
    ok = wajar(r["pts"]) and wajar(r["ptsR"])
    print("\n%s"%("BENAR: X, Y dan Z terbaca dari kolom yang benar."
        if ok else "GAGAL: kolom tergeser -- X/Y/Z tidak masuk akal."))
    ctx.close(); raise SystemExit(0 if ok else 1)
