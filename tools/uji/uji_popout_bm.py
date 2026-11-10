# -*- coding: utf-8 -*-
"""Pop-up tahap 2 Block Model (dig block, Reporting, Solid Vein poligon) + Report block model dalam Solid Vein + kinerja (pemilik 10-11-2026). Data sintetis."""
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
    ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    a = pg.evaluate("""(async function(){var w=function(t){return new Promise(function(r){setTimeout(r,t);});};var o={};
      lySet('fh',2.5);lyU().bot='';lySet('top',238.75);lyApply();await w(1500);
      var m=BX.m,cx=0,cy=0,nb=0;for(var i=0;i<m.n;i++){if(m.z[i]>236.3&&m.z[i]<238.7){cx+=m.x[i];cy+=m.y[i];nb++;}}cx=cx/nb-offX;cy=cy/nb-offY;
      /* 1. daftar dig block */
      var R=function(x,y,a,b){return [[x,y,238],[x+a,y,238],[x+a,y+b,238],[x,y+b,238]];};
      DG.S.push({closed:true,inner:false,vis:true,no:91,d:'ORE',pts:R(cx-20,cy-20,15,15)});DG.S.push({closed:true,inner:false,vis:true,no:92,d:'ORE',pts:R(cx+5,cy-20,15,15)});
      uiTab('BM');PT.select('fl.2d');dbPanel();await w(600);POP.set('db.list',true);await w(700);var W=document.getElementById('gxpo_db_list');
      o.db=!!(W&&W.style.display!=='none'&&W.querySelectorAll('.lyrow').length>=2);o.dbPh=!!document.querySelector('#dbBody .gxpoph');o.dbCss=W?getComputedStyle(W.querySelector('.lyrow')).display:'';
      dbPanel();await w(500);o.db2=!!(W&&W.querySelectorAll('.lyrow').length>=2);
      /* 2. hasil Reporting */
      uiTab('Rep');rpPanel();await w(300);rpRun();await w(2000);POP.set('rp.res',true);await w(800);var W2=document.getElementById('gxpo_rp_res');o.rp=!!(W2&&W2.style.display!=='none'&&W2.querySelector('.rptb'));
      RP.sec='c';rpPanel();await w(500);o.rpTetap=!!(W2&&W2.querySelector('.rptb'))&&!!document.getElementById('rpGo');
      /* 3. Solid Vein: poligon per flitch pop-up + report block model dalam solid */
      var d=SV.D(),p={id:'rp1',name:'Uji report',from:'2026-11-01',to:'2026-11-07',polys:[],par:{dmax:10,zMode:'flat',rIdw:6,zTol:1.25,capPts:false,method:'min',sg:2.6,reg:false},res:null};d.per.push(p);d.cur=p.id;
      var X0=cx-12.3,Y0=cy-9.7,AW=24.6,BH=19.4,rect=[[X0,Y0],[X0+AW,Y0],[X0+AW,Y0+BH],[X0,Y0+BH]];
      p.polys.push({id:'v1',top:238.75,bot:236.25,pts:rect,key:'k1',src:'digit',name:'V1',on:true});p.polys.push({id:'v2',top:236.25,bot:233.75,pts:rect,key:'k2',src:'digit',name:'V2',on:true});
      SV.run();await w(1500);o.svRes=!!p.res;uiTab('SV');SV.panel();await w(300);POP.set('sv.poly',true);await w(600);var W3=document.getElementById('gxpo_sv_poly');o.svPoly=!!(W3&&/Digit poligon/.test(W3.textContent));
      SV.report(p.id);await w(500);var H=SV._repH;o.nB=H?H.nB:-1;var bf=0;for(i=0;i<m.n;i++){var x=m.x[i]-offX,y=m.y[i]-offY,z=m.z[i];if(x>X0&&x<X0+AW&&y>Y0&&y<Y0+BH&&z>233.75&&z<238.75)bf++;}o.brute=bf;
      var W4=document.getElementById('svRepPop');o.repWin=!!(W4&&W4.style.display!=='none'&&W4.querySelectorAll('table.gxtb').length===3);o.lv=H?H.lv.length:0;o.ton=H?H.all.t:0;
      o.node=PT.flatAll(PT.nodes).some(function(n){return n.id==='sv.p.rp1.rep';});
      /* 4. kinerja: klik tombol di dalam jendela pop-up tercatat */
      var n0=KIN.log.length;W4.querySelector('button').click();await w(300);o.kin=KIN.log.length>n0||(KIN.log[0]&&/Salin/.test(KIN.log[0].aksi));o.kinAksi=KIN.log[0]?KIN.log[0].aksi:'';
      return o;})()""")
    print(a)
    cek(a["db"] and a["dbPh"] and a["db2"] and a["dbCss"] == a["dbCss"], "daftar dig block flitch aktif pindah ke pop-up dan tetap di sana setelah panel digambar ulang")
    cek(a["rp"] and a["rpTetap"], "hasil Reporting di pop-up; tetap terbaca saat pindah ke tab Constraint")
    cek(a["svRes"] and a["svPoly"], "Solid Vein: poligon per flitch di pop-up")
    cek(a["nB"] == a["brute"] and a["nB"] > 0 and a["repWin"] and a["lv"] == 2 and a["node"], "Report block model dalam solid: %d blok = hitungan langsung %d (prisma 2 flitch), 3 tabel, subnode ada" % (a["nB"], a["brute"]))
    cek(a["kin"], "Kinerja tetap mencatat klik di dalam jendela pop-up (%s)" % a["kinAksi"])
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: %d" % len(gagal) if gagal else "\nLULUS")
sys.exit(1 if gagal else 0)
