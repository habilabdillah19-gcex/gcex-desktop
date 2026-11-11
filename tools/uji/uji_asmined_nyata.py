# -*- coding: utf-8 -*-
"""As-Mined sesudah review data nyata (web-src/amnyata.js, BM 0.24.54). Data SINTETIS dengan tata letak berkas pemilik
(CSV tanpa judul ID,X,Y,Z,kode; nama ACT_SO<yymmdd>OB_<atas>_<bawah>_<pit>.csv) -- berkas nyata tidak masuk repo.
  A. nama file -> RL flitch, tanggal, pit (termasuk salah ketik 7 angka)
  B. import boundary dari CSV OB: 1 poligon di flitch NAMA FILE (bukan flitch aktif), tanggal & pit ikut, titiknya jadi titik atap
  C. kelas kadar dari aturan IIF block model; kolom SG dipilih otomatis
  D. 3D hasil kerja: BLOCK MODEL di dalam solid as-mined tampil (BM 0.24.65; volume blok yang digambar = volume hitungan),
     solid as-mined jadi pilihan selubung, kubus sub-blok penuh tidak bawaan; zoom mengubah kamera / rentang plan
Pemakaian: python tools/uji/uji_asmined_nyata.py"""
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
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept()); err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    a = pg.evaluate("[AMN.nama('ACT_SO261106OB_272-5_271_Z3.csv'),AMN.nama('ACT_SO2611109OB_248-5_246_Z4.csv'),AMN.nama('PROG261107ORE_Z3.csv'),AMN.nama('boundary.csv')]"); print("A", a)
    cek(a[0] == {"top": 272.5, "bot": 271, "date": "2026-11-06", "pit": "Z3"}, "A nama file -> RL 272,5-271, 2026-11-06, pit Z3")
    cek(a[1]["top"] == 248.5 and a[1]["bot"] == 246 and a[1]["date"] == "2026-11-10" and a[1]["pit"] == "Z4", "A nama salah ketik (7 angka) tetap terbaca: %s" % a[1])
    cek(a[2]["date"] == "2026-11-07" and a[2]["pit"] == "Z3" and a[2]["top"] != a[2]["top"] and a[3]["date"] == "" and a[3]["pit"] == "", "A PROG: tanggal & pit, tanpa RL; nama tanpa pola -> kosong")
    # B: poligon sintetis di tengah model, flitch 238,75-236,25 (BUKAN flitch aktif)
    b = pg.evaluate("""(async function(){var m=BX.m,cx=0,cy=0,n=0,i;for(i=0;i<m.n;i++)if(m.z[i]>236.25&&m.z[i]<238.75){cx+=m.x[i];cy+=m.y[i];n++;}cx/=n;cy/=n;var bd=1e18,bi=-1;for(i=0;i<m.n;i++)if(m.z[i]>236.25&&m.z[i]<238.75){var d=Math.hypot(m.x[i]-cx,m.y[i]-cy);if(d<bd){bd=d;bi=i;}}cx=m.x[bi]-6;cy=m.y[bi]-7;lySet('fh',2.5);lyU().bot='';lySet('top',241.25);
      var P=[[0,0],[12,1],[13,9],[6,14],[-1,8]],s='';P.forEach(function(q,i){s+=(i+1)+','+(cx+q[0]).toFixed(3)+','+(cy+q[1]).toFixed(3)+','+(238.2+0.1*i).toFixed(3)+',204\\n';});s+='5,'+(cx-1).toFixed(3)+','+(cy+8).toFixed(3)+',238.600,204\\n';
      var n0=amBndAll().length,r0=(amD().ptsR||[]).length;amBndFile([new File([s],'ACT_SO261106OB_238-75_236-25_ZX.csv')]);await new Promise(function(r){setTimeout(r,1500);});var x=amBndAll()[amBndAll().length-1];window._x=x;
      return {n:amBndAll().length-n0,top:x.top,bot:x.bot,date:x.date,pit:x.pit,np:x.pts.length,roof:(amD().ptsR||[]).length-r0,msg:(AM.bmsg||'').replace(/<[^>]+>/g,' '),aktif:lyBench()};})()"""); print("B", b)
    cek(b["n"] == 1 and b["top"] == 238.75 and b["bot"] == 236.25 and b["aktif"][0] == 241.25, "B CSV OB -> 1 poligon di flitch nama file (238,75-236,25), flitch aktif tetap 241,25")
    cek(b["date"] == "2026-11-06" and b["pit"] == "ZX" and b["np"] == 5 and b["roof"] == 6, "B tanggal & pit dari nama file; titik ganda dibuang (5 sudut); 6 titik jadi titik atap")
    # C
    c = pg.evaluate("""(function(){var m=BX.m,sv=m.mdl;m.mdl={expr:{material_type:'IIF(au_gc<0.3,"WASTE", IIF(au_gc>=0.3 AND au_gc<0.40,"MO", IIF(au_gc>=0.40 AND au_gc<1,"LG",IIF(au_gc>=1 AND au_gc<3,"HG",IIF(au_gc>=3,"SG","material_type")))))'}};
      var ga=amU().attr;m.mdl.expr.material_type=m.mdl.expr.material_type.replace(/au_gc/g,ga);var ok=AMN.pakaiKelas(true),R=amR(),cls=R.cls.map(function(q){return [q.m,q.lo,q.hi];}),sgd=R.dst.some(function(d){return d.o==='SG*';});m.mdl=sv;
      var au=m.num[ga],mk=function(o,csv){return {n:m.n,num:Object.assign({AU:au},o),cat:{},mdl:csv?undefined:{}};},arr=function(v){return Float32Array.from({length:m.n},function(){return v;});};return {ok:ok,cls:cls,src:R.clsSrc,sg:bxDefUI(mk({sg3:arr(2.43)})).sgCol,sg0:bxDefUI(mk({})).sgCol,sgx:bxDefUI(mk({sg:arr(99)})).sgCol,lat:bxDefUI(m).sgCol,csv:bxDefUI(mk({sg3:arr(2.43)},1)).sgCol};})()"""); print("C", c)
    cek(c["ok"] and c["cls"] == [["MO", 0.3, 0.4], ["LG", 0.4, 1], ["HG", 1, 3], ["SG", 3, ""]] and "material_type" in c["src"], "C kelas dari aturan IIF block model: MO 0,3-0,4 / LG 0,4-1 / HG 1-3 / SG >=3")
    cek(c["sg"] == "sg3" and c["sg0"] == "" and c["sgx"] == "" and c["csv"] == "" and c["lat"] == "", "C kolom SG .mdl dipilih otomatis bila ada & masuk akal (sg3); tanpa kolom / nilai tak masuk akal / model CSV (data latihan) -> SG tetap")
    # D
    pg.evaluate("lySet('fh',2.5);lyU().bot='';lySet('top',238.75);lyApply()"); pg.wait_for_timeout(3000); pg.evaluate("amR().roof='pickup';amRun(true)"); pg.wait_for_timeout(3500)
    pg.evaluate("lyFlOff();if(VIEW2D)toggle2D();"); pg.wait_for_timeout(1500); pg.evaluate("PT.select('reg.3d');am3Toggle(true)"); pg.wait_for_timeout(6000)
    bm = pg.evaluate("""(function(){var gd=document.getElementById('plotDiv'),T=gd.data||[],B=T.filter(function(t){return t.type==='mesh3d'&&/^Block model as-mined/.test(t.name||'');}),S=T.filter(function(t){return /^Solid as-mined/.test(t.name||'');}),
      C=AMN.bmCells(),v=0,ar=function(Q){var a=0;for(var i=0;i<Q.length;i++){var p=Q[i],q=Q[(i+1)%Q.length];a+=p[0]*q[1]-q[0]*p[1];}return Math.abs(a)/2;};C.forEach(function(c){v+=ar(c.Q)*(c.zt-c.zb);});
      var vr=0;Object.keys(AM.res).forEach(function(k){vr+=AM.res[k].sum.vol;});var zt=Math.max.apply(null,C.map(function(c){return c.zt;}));return {nb:B.length,ns:S.length,blok:C.length,v:v,vr:vr,zt:zt,nm:B.map(function(t){return t.name;})};})()"""); print("BM", bm)
    cek(bm["nb"] >= 1 and bm["ns"] == 0 and bm["blok"] > 0, "D bawaan: block model di dalam solid as-mined tampil (%d kelas, %d blok), solid tidak" % (bm["nb"], bm["blok"]))
    cek(abs(bm["v"] - bm["vr"]) <= 1e-3 * max(1, bm["vr"]), "D volume blok yang digambar = volume hitungan as-mined (%.2f vs %.2f m3)" % (bm["v"], bm["vr"]))
    cek(bm["zt"] < 238.75 - 0.05, "D blok dipotong atap pick-up (puncak %.2f < 238,75)" % bm["zt"])
    pg.evaluate("AM3.sol=true;updatePlot()"); pg.wait_for_timeout(3000)
    dd = pg.evaluate("""(function(){var gd=document.getElementById('plotDiv'),T=gd.data||[],S=T.filter(function(t){return t.type==='mesh3d'&&/^Solid as-mined/.test(t.name||'');}),K=T.filter(function(t){return /sub-blok\\)/.test(t.name||'');}),c=gd._fullLayout.scene.camera,I=amInfoById(_x.id),z=S[0]?Array.from(S[0].z):[];
      return {solid:S.length,kubus:K.length,zmax:z.length?Math.max.apply(null,z):null,zmin:z.length?Math.min.apply(null,z):null,ton:I&&I.ton,de:Math.hypot(c.eye.x-c.center.x,c.eye.y-c.center.y,c.eye.z-c.center.z),code:I&&I.code};})()"""); print("D", dd)
    cek(dd["solid"] == 1 and dd["kubus"] == 0 and dd["ton"] > 0, "D solid as-mined (selubung, dicentang): 1 solid; kubus sub-blok penuh tidak digambar")
    cek(dd["zmax"] is not None and dd["zmax"] <= 238.75 + 1e-6 and dd["zmax"] < 238.75 - 0.05 and abs(dd["zmin"] - 236.25) < 1e-6, "D solid mengikuti atap pick-up (%.2f < RL atas 238,75) sampai lantai %.2f" % (dd["zmax"] or 0, dd["zmin"] or 0))
    cek(dd["de"] < 0.6, "D kamera otomatis mendekat ke poligon as-mined (jarak mata %.3f)" % dd["de"])
    pg.evaluate("lyApply()"); pg.wait_for_timeout(3000); pg.evaluate("AMN.zoom(false)"); pg.wait_for_timeout(2500)
    z2 = pg.evaluate("(function(){var L=document.getElementById('plotDiv')._fullLayout;return {v2d:VIEW2D,w:L.xaxis?L.xaxis.range[1]-L.xaxis.range[0]:null};})()"); print("Z", z2)
    cek(z2["v2d"] and z2["w"] is not None and z2["w"] < 120, "D zoom di plan 2D: lebar tampilan %.0f m (poligon 14 m)" % (z2["w"] or 0))
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
