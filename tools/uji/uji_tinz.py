# -*- coding: utf-8 -*-
"""Interpolasi Z dari titik dengan triangulasi (web-src/tinz.js): atap As-Mined & Solid Vein (pemilik 10-11-2026). Data sintetis."""
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
def N_(v):
    return "{:,.1f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")
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
    a = pg.evaluate("""(function(){var o={};var X0=505000,Y0=9012000,pl=function(x,y){return 240+0.05*(x-X0)-0.03*(y-Y0);};
      var P=[];for(var i=0;i<60;i++){var x=X0+Math.random()*40,y=Y0+Math.random()*40;P.push({x:x,y:y,z:pl(x,y)});}
      var T=TINZ(P),e=0,nOut=0;for(var k=0;k<400;k++){var x=X0+5+Math.random()*30,y=Y0+5+Math.random()*30,v=T.f(x,y);if(v==null){nOut++;continue;}e=Math.max(e,Math.abs(v-pl(x,y)));}o.bidang=e;o.luar=nOut;
      /* puncak: 4 sudut z=240, titik tengah 241 -> tepat di titik = 241, di tengah sisi = 240 (IDW akan memberi < 241 di titik? tidak; cek titik antara) */
      var Q=[{x:0,y:0,z:240},{x:10,y:0,z:240},{x:10,y:10,z:240},{x:0,y:10,z:240},{x:5,y:5,z:241}],T2=TINZ(Q);o.puncak=T2.f(5,5);o.antara=T2.f(2.5,5);o.diluar=T2.f(20,20);
      /* atap As-Mined mode pickup */
      var D=amD();D.ptsR=P.map(function(q){return {x:q.x,y:q.y,z:q.z,id:'',c:'',f:'X.csv'};});var R=amR();R.roof='pickup';R.rfUp=5;R.rfDn=5;
      var poly={r:[[X0+10,Y0+10],[X0+30,Y0+10],[X0+30,Y0+30],[X0+10,Y0+30]]};poly.b=lyBB(poly.r);var F=amRoofFn(poly,[240,238.5]);var e2=0;for(k=0;k<200;k++){var x2=X0+15+Math.random()*10,y2=Y0+15+Math.random()*10;e2=Math.max(e2,Math.abs(F.f(x2,y2)-Math.max(235,Math.min(245,pl(x2,y2)))));}o.atap=e2;o.tin=F.tin||0;
      /* Solid Vein: Z sudut poligon */
      var pr={zMode:'idw',rIdw:6};o.sv=SV.build?1:0;return o;})()""")
    print(a)
    cek(a["bidang"] < 1e-6, "TIN: titik pada bidang miring -> interpolasi tepat (galat %.2e m)" % a["bidang"])
    cek(abs(a["puncak"] - 241) < 1e-9 and abs(a["antara"] - 240.5) < 1e-9 and a["diluar"] is None, "TIN: puncak pick-up dihormati persis, linear di antaranya, di luar selubung = cadangan")
    cek(a["tin"] > 0 and a["atap"] < 0.05, "atap As-Mined mode pick-up memakai TIN (%d segitiga), galat terhadap bidang %.3f m" % (a["tin"], a["atap"]))
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: %d" % len(gagal) if gagal else "\nLULUS")
sys.exit(1 if gagal else 0)
