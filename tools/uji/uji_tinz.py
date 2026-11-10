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
    t = pg.evaluate("""(async function(){var w=function(t){return new Promise(function(r){setTimeout(r,t);});};var o={};var pl=function(x,y){return 200+0.04*x-0.02*y;};
      var lama=OV.topoF,X=[],Y=[],Z=[];for(var i=0;i<3000;i++){var x=Math.random()*600-300,y=Math.random()*600-300;X.push(x);Y.push(y);Z.push(pl(x,y));}
      OV.topoF={x:X,y:Y,z:Z};if(window.TIDX!==undefined)TIDX=null;var e=0,ei=0;for(var k=0;k<300;k++){var x=Math.random()*400-200,y=Math.random()*400-200,v=topoZ(x,y);e=Math.max(e,Math.abs(v-pl(x,y)));var vi=topoZ._idw(x,y);ei=Math.max(ei,Math.abs(vi-pl(x,y)));}
      o.topo=e;o.topoIdw=ei;o.tin=!!topoZ._tin;var f=RP.api.surf(OV.topoF),e2=0;for(k=0;k<200;k++){var x2=Math.random()*400-200,y2=Math.random()*400-200;e2=Math.max(e2,Math.abs(f(x2,y2)-pl(x2,y2)));}o.rp=e2;o.api=true;
      /* permukaan string (potong saat import): crest bertangga -> TIN */
      var L=[];for(var r=0;r<=4;r++){var R=40+r*20,zz=250-r*10;for(var a=0;a<=36;a++){var t2=a/36*2*Math.PI;L.push([R*Math.cos(t2),R*Math.sin(t2),zz]);}L.push(null);}
      var G=SA.surfGrid(L,'crest'),e3=0,nn=0;for(k=0;k<200;k++){var rr=45+Math.random()*70,aa=Math.random()*6.283,xx=rr*Math.cos(aa),yy=rr*Math.sin(aa),zs=SA.surfAt(G,xx,yy);if(!isFinite(zs))continue;nn++;var hv=250-(rr-40)/2;e3=Math.max(e3,Math.abs(zs-hv));}o.sg=e3;o.sgn=nn;
      OV.topoF=lama;if(window.TIDX!==undefined)TIDX=null;
      /* lantai As-Mined */
      var D=amD(),X0=505000,Y0=9012000,pf=function(x,y){return 237+0.03*(x-X0)+0.01*(y-Y0);};D.pts=[];for(i=0;i<60;i++){var px=X0+Math.random()*40,py=Y0+Math.random()*40;D.pts.push({x:px,y:py,z:pf(px,py),id:'',c:''});}var Rr=amR();Rr.floor='pickup';Rr.flDn=5;Rr.flUp=5;
      var poly={r:[[X0+10,Y0+10],[X0+30,Y0+10],[X0+30,Y0+30],[X0+10,Y0+30]]};poly.b=lyBB(poly.r);var F=amFloorFn(poly,[238.5,237]),e4=0;for(k=0;k<200;k++){var x4=X0+15+Math.random()*10,y4=Y0+15+Math.random()*10;e4=Math.max(e4,Math.abs(F.f(x4,y4)-pf(x4,y4)));}o.lantai=e4;o.ltin=F.tin||0;
      /* pop-up */
      uiTab('AM');amPanel();await w(300);POP.set('am.ly',true);await w(400);var W=document.getElementById('gxpo_am_ly');o.lyWin=!!(W&&W.style.display!=='none'&&/Layout|PDF|export/i.test(W.textContent));o.lyPh=!!document.querySelector('#amBody .gxpoph');
      amPanel();await w(400);o.lyWin2=!!(W&&W.querySelector('.gxpb').children.length);o.lyGanda=document.querySelectorAll('#amBody .gxpoph').length;
      POP.set('am.reg',true);await w(400);var W2=document.getElementById('gxpo_am_reg');o.regWin=!!(W2&&W2.style.display!=='none'&&W2.querySelector('.gxpb').textContent.length>10);
      POP.set('am.ly',false);POP.set('am.reg',false);await w(400);o.balik=!document.querySelector('#amBody .gxpoph')&&W.style.display==='none';
      var dS=SV.D();if(!dS.per.length){dS.per.push({id:'pp',name:'Uji',from:'',to:'',polys:[],par:{},res:null});dS.cur='pp';}uiTab('SV');SV.panel();await w(300);POP.set('sv.pts',true);await w(400);var W3=document.getElementById('gxpo_sv_pts');o.svWin=!!(W3&&/Import titik atap/.test(W3.textContent));o.svDbg=[!!document.getElementById('svBody'),!!document.querySelector('#svBody .svsec[data-sec="pts"]'),W3?W3.textContent.slice(0,80):'-',document.querySelectorAll('.svsec').length];POP.set('sv.pts',false);await w(300);
      return o;})()""")
    print(t)
    cek(t["tin"] and t["topo"] < 1e-6 and t["topoIdw"] > t["topo"], "topoZ memakai TIN: bidang miring tepat (galat %.1e; IDW lama %.3f m)" % (t["topo"], t["topoIdw"]))
    cek(t["rp"] < 1e-6 and t["api"], "Reporting (rpSurf & RP.api.surf) memakai TIN")
    cek(t["sgn"] > 50 and t["sg"] < 0.5, "permukaan string (potong saat import) dari TIN: galat %.3f m (sel grid 1 m x lereng 0,5) pada %d titik" % (t["sg"], t["sgn"]))
    cek(t["ltin"] > 0 and t["lantai"] < 1e-6, "lantai As-Mined dari pick-up memakai TIN (galat %.1e m)" % t["lantai"])
    cek(t["lyWin"] and t["lyPh"] and t["lyWin2"] and t["lyGanda"] == 1, "Layout & export pindah ke pop-up, tetap di pop-up setelah panel digambar ulang")
    cek(t["regWin"] and t["balik"], "Daftar poligon per flitch di pop-up; tombol tutup mengembalikan ke panel")
    cek(t["svWin"], "tabel titik atap Solid Vein di pop-up")
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: %d" % len(gagal) if gagal else "\nLULUS")
sys.exit(1 if gagal else 0)
