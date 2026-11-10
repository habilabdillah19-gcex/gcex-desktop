# -*- coding: utf-8 -*-
"""As-Mined: kunci tanggal-shift, Report per tanggal, tampalan dengan poligon terkunci (pemilik 10-11-2026). Data sintetis.
Pemakaian: python tools/uji/uji_am_kunci.py"""
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
    pg = ctx.new_page(); dlg = []
    def _d(x):
        dlg.append(x.message[:90]); x.accept(x.default_value) if x.type == "prompt" else x.accept()
    pg.on("dialog", _d)
    err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    g = pg.evaluate("""(function(){var Q=[];var sh=function(P){var a=0;for(var i=0;i<P.length;i++){var q=P[i],r=P[(i+1)%P.length];a+=q[0]*r[1]-r[0]*q[1];}return a/2;};
      var t=function(A,B){var d=AMK.diff(A,B),ov=AMK.overlap(A,B);return {n:d?d.length:-1,luas:d?d.reduce(function(s,l){return s+sh(l);},0):null,harap:Math.abs(sh(A))-ov};};
      Q.push(t([[0,0],[10,0],[10,10],[0,10]],[[5,-2],[15,-2],[15,12],[5,12]]));   /* setengah */
      Q.push(t([[0,0],[10,0],[10,10],[0,10]],[[4,-2],[6,-2],[6,12],[4,12]]));     /* membelah dua */
      Q.push(t([[0,0],[10,0],[10,10],[0,10]],[[10,0],[20,0],[20,10],[10,10]]));   /* bersinggungan sisi */
      Q.push(t([[0,0],[10,0],[10,10],[0,10]],[[3,3],[6,3],[6,6],[3,6]]));         /* di dalam -> lubang */
      Q.push(t([[0,0],[10,0],[10,4],[4,4],[4,10],[0,10]],[[2,2],[12,2],[12,8],[2,8]])); /* L */
      return Q;})()""")
    print("diff", g)
    cek(g[0]["n"] == 1 and abs(g[0]["luas"] - 50) < 0.6, "selisih: setengah tertampal -> sisa 50 m2")
    cek(g[1]["n"] == 2 and abs(g[1]["luas"] - 80) < 0.6, "selisih: terbelah dua -> 2 potong, 80 m2")
    cek(g[2]["n"] == 1 and abs(g[2]["luas"] - 100) < 0.6, "selisih: hanya bersinggungan -> tetap 100 m2")
    cek(g[3]["n"] == -1, "selisih: poligon terkunci di dalam -> ditolak (akan berlubang)")
    cek(g[4]["n"] >= 1 and abs(g[4]["luas"] - g[4]["harap"]) < 1.5, "selisih: bentuk L")
    a = pg.evaluate("""(async function(){var w=function(t){return new Promise(function(r){setTimeout(r,t);});};
      lySet('fh',2.5);lyU().bot='';lySet('top',238.75);lyApply();await w(1500);uiTab('AM');
      var m=BX.m,cx=0,cy=0,nb=0;for(var i=0;i<m.n;i++){if(m.z[i]>236.3&&m.z[i]<238.7){cx+=m.x[i];cy+=m.y[i];nb++;}}cx/=nb;cy/=nb;
      var R=function(x,y,a,b){return [[x,y,238],[x+a,y,238],[x+a,y+b,238],[x,y+b,238]];},o={};
      amRSet('auto',false);amR().auto=false;
      amBndAdd(R(cx-20,cy-20,20,20),'A',{top:238.75,bot:236.25,date:'2026-11-01'});var A=amBndAll().filter(function(x){return x.name==='A';})[0];A.shift='DS';
      amRun(true);await w(500);o.a0=A.st&&A.st.t;o.msg=String(AM.msg).replace(/<[^>]+>/g,'').slice(0,300);o.z=[Math.min.apply(null,Array.from(m.z.slice(0,50000))),Math.max.apply(null,Array.from(m.z.slice(0,50000)))];o.c=[cx,cy,offX,offY];o.pa=A.pts.slice(0,2);o.aEl=A.st&&A.st.gA;
      o.kunci=AMK.lock('2026-11-01','DS');o.isLk=AMK.isLk(A);
      BX.ui.sg=(BX.ui.sg||2.6)*1.2;if(BX.ui.sgCol)BX.ui.sgCol='';
      amBndAdd(R(cx+30,cy+30,15,15),'B',{top:238.75,bot:236.25,date:'2026-11-15'});var Bp=amBndAll().filter(function(x){return x.name==='B';})[0];Bp.shift='NS';
      amRun(true);await w(500);o.a1=A.st.t;o.aNow=A._stNow&&A._stNow.t;o.b=Bp.st&&Bp.st.t;var r=AM.res[lyFmt(238.75)+'_'+lyFmt(236.25)];o.sum=r.sum.t;
      var n0=amBndAll().length;amBndAdd(R(cx-10,cy-30,20,20),'C',{top:238.75,bot:236.25,date:'2026-11-15'});var C=amBndAll().filter(function(x){return x.name==='C';})[0];
      var sh=function(P){var a=0;for(var i=0;i<P.length;i++){var q=P[i],r=P[(i+1)%P.length];a+=q[0]*r[1]-r[0]*q[1];}return Math.abs(a/2);};o.cLuas=C?sh(C.pts):-1;
      amBndDel(A.id);o.aMasih=!!amBndAll().filter(function(x){return x.id===A.id;})[0];amPSet(A.id,'ore','ZZ');o.aOre=A.ore||'';
      AMK.f={date:'2026-11-01',shift:''};AMK.open();await w(300);var tb=document.querySelector('#amkPop tr.tot');o.rep=tb?tb.textContent:'';o.repLk=!!document.querySelector('#amkPop .lk');
      AMK.unlock('2026-11-01','DS');o.lepas=!AMK.isLk(A);amRun(true);await w(500);o.a2=A.st.t;return o;})()""")
    print(a)
    cek(a["a0"] and a["kunci"] == 1 and a["isLk"], "Hitung poligon A (1 Nov DS) lalu kunci tanggal-shift itu")
    cek(abs(a["a1"] - a["a0"]) < 1e-9 and a["aNow"] and abs(a["aNow"] - a["a0"] * 1.2) < 1, "SG berubah + flitch sama digali lagi (B): A tetap %.1f t (bila dihitung ulang %.1f t)" % (a["a1"], a["aNow"] or 0))
    cek(a["b"] and abs(a["sum"] - (a["a0"] + a["b"])) < 1e-6, "rekap flitch = A beku + B baru")
    cek(abs(a["cLuas"] - 300) < 2, "poligon baru C (400 m2) bertampalan 100 m2 dengan A terkunci -> dikurangi jadi %.1f m2" % a["cLuas"])
    cek(a["aMasih"] and a["aOre"] != 'ZZ', "poligon terkunci tidak bisa dihapus / diubah atributnya")
    cek(a["repLk"] and N_(a["a0"]) in a["rep"], "Report As-Mined 1 Nov: total = angka beku A (%s)" % a["rep"][:80])
    cek(a["lepas"] and abs(a["a2"] - a["a0"] * 1.2) < 1, "buka kunci -> Hitung berikutnya menghitung ulang A")
    cek(any("bertampalan" in m for m in dlg), "peringatan tampalan muncul")
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: %d" % len(gagal) if gagal else "\nLULUS")
sys.exit(1 if gagal else 0)
