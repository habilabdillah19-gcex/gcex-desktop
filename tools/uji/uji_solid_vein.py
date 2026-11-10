# -*- coding: utf-8 -*-
"""Solid Vein Aktual (trial) — GC-Ex Block Model (web-src/svein_bm.js).
Yang dibuktikan (data sintetis, bukan data proyek):
  A. prisma: persegi 20x10 di dua flitch berurutan, Z datar -> 1 pulau TERTUTUP, volume = luas x 2 tinggi flitch (galat < 1e-6)
  B. pulau: poligon lain 50 m jauhnya, jarak sambung 10 m -> pulau terpisah, masing-masing tertutup; jarak sambung 100 m -> tersambung
  C. putus: flitch di antaranya kosong -> solid TIDAK disambung melewati flitch kosong
  D. cabang: 1 induk -> 2 anak -> 1 pulau tertutup (induk dibelah garis bagi), volume di antara batas masuk akal
  E. poligon cekung & jumlah titik berbeda, tiga metode Surpac (min / equi / prop): semuanya tertutup, luas min <= lainnya
  F. Z atap IDW + atap ikut titik pick-up di dalam poligon: tetap tertutup
  G. tampil di 3D: garis poligon & mesh solid ada di jendela; terdaftar di Wireframe geologi (dipakai Reporting)
  H. ekspor DTM + STR Surpac: jumlah segitiga & TRISOLATION cocok, indeks titik valid, dibaca ulang SA.readMeshes -> volume sama
  I. digit: poligon hasil digit masuk ke periode (bukan ke daftar string / dig block); tersimpan di proyek (BX.ui.sv)
Pemakaian: python tools/uji/uji_solid_vein.py"""
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
JS_SIAP = """(function(){var B=lyBench(),fh=B[0]-B[1];window.T0=B[0];window.FH=fh;
  window.rect=function(x,y,w,h){return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]];};
  window.mk=function(nm,L,par){var d=SV.D(),p={id:'t'+Math.random().toString(36).slice(2,7),name:nm,from:'',to:'',polys:[],par:{},res:null};d.per.push(p);d.cur=p.id;
    L.forEach(function(q,i){p.polys.push({id:'v'+i,top:T0-q[0]*FH,bot:T0-(q[0]+1)*FH,pts:q[1],key:'k'+i,src:'digit',name:'V'+i,on:true});});
    var pr={dmax:10,zMode:'flat',rIdw:6,zTol:FH/2,capPts:false,method:'min',sg:2.5,reg:false};for(var k in (par||{}))pr[k]=par[k];p.par=pr;
    var R=SV.build(p);return {n:R.IS.length,isl:R.IS.map(function(s){return {vol:s.vol,closed:s.closed,open:s.open,dup:s.dup,nLv:s.nLv,nPoly:s.nPoly,area:s.area,nt:s.tri.length};}),warn:R.warn};};
  return fh;})()"""
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    cek(pg.evaluate("!!window.SV && !!document.getElementById('pSV') && typeof svTree==='function'"), "modul, panel & node Solid Vein terpasang")
    cek(pg.evaluate("PT.flatAll(PT.nodes).some(function(n){return n.id==='sv';})"), "node 'Solid Vein Aktual (trial)' ada di Project Tree")
    fh = pg.evaluate(JS_SIAP); print("tinggi flitch:", fh)
    # A
    a = pg.evaluate("mk('A',[[0,rect(100,100,20,10)],[1,rect(100,100,20,10)]])"); print("A", a)
    cek(a["n"] == 1 and a["isl"][0]["closed"] and abs(a["isl"][0]["vol"] - 200 * 2 * fh) < 1e-6, "A prisma: 1 pulau tertutup, volume %.4f = %.4f" % (a["isl"][0]["vol"], 400 * fh))
    # B
    b = pg.evaluate("mk('B',[[0,rect(100,100,20,10)],[1,rect(100,100,20,10)],[1,rect(170,100,10,10)]])"); print("B", b)
    vols = sorted(round(s["vol"], 6) for s in b["isl"])
    cek(b["n"] == 2 and all(s["closed"] for s in b["isl"]) and abs(vols[0] - 100 * fh) < 1e-6 and abs(vols[1] - 400 * fh) < 1e-6, "B dua pulau terpisah (50 m > 10 m), keduanya tertutup")
    b2 = pg.evaluate("mk('B2',[[0,rect(100,100,20,10)],[1,rect(100,100,20,10)],[1,rect(170,100,10,10)]],{dmax:100})"); print("B2", b2)
    cek(b2["n"] == 1 and b2["isl"][0]["closed"], "B jarak sambung 100 m: tersambung jadi 1 pulau tertutup (bercabang)")
    # C
    c = pg.evaluate("mk('C',[[0,rect(100,100,20,10)],[2,rect(100,100,20,10)]])"); print("C", c)
    cek(c["n"] == 2 and all(s["closed"] and abs(s["vol"] - 200 * fh) < 1e-6 for s in c["isl"]), "C flitch kosong di tengah: solid putus (2 pulau, tidak menembus flitch kosong)")
    # D
    dd = pg.evaluate("mk('D',[[0,rect(100,100,40,10)],[1,rect(100,100,14,10)],[1,rect(126,100,14,10)]])"); print("D", dd)
    v = dd["isl"][0]["vol"] if dd["n"] else 0
    cek(dd["n"] == 1 and dd["isl"][0]["closed"] and 280 * fh + 280 * fh - 1e-6 <= v <= 400 * fh + 280 * fh + 1e-6, "D cabang 1->2: 1 pulau tertutup, volume %.2f dalam batas [%.2f, %.2f]" % (v, 560 * fh, 680 * fh))
    # E
    Lc = "[[0,[[0,0],[30,0],[30,8],[12,8],[12,20],[0,20]]],[1,[[2,2],[10,1],[20,2],[28,3],[27,7],[11,7],[10,18],[6,19],[2,17],[1,9]]]]"
    luas = {}
    for mt in ("min", "equi", "prop"):
        e = pg.evaluate("mk('E%s',%s,{method:'%s'})" % (mt, Lc, mt)); luas[mt] = e["isl"][0]["area"]
        cek(e["n"] == 1 and e["isl"][0]["closed"] and e["isl"][0]["vol"] > 0 and not e["warn"], "E cekung, metode %s: tertutup, vol %.2f, luas %.2f" % (mt, e["isl"][0]["vol"], e["isl"][0]["area"]))
    cek(luas["min"] <= luas["equi"] + 1e-6 and luas["min"] <= luas["prop"] + 1e-6, "E luas permukaan metode minimum <= dua metode lain")
    # F
    pg.evaluate("""(function(){var D=amD();D.ptsR=[];for(var i=0;i<=10;i++)for(var j=0;j<=6;j++){D.ptsR.push({x:offX+98+i*2.4,y:offY+98+j*2.4,z:T0+0.3*Math.sin(i*0.7)*Math.cos(j*0.9),id:'R'+i+'_'+j,c:'atap_sintetis'});}})()""")
    f = pg.evaluate("mk('F',[[0,rect(100,100,20,10)],[1,rect(101,101,18,8)]],{zMode:'idw',capPts:true})"); print("F", f)
    f0 = pg.evaluate("mk('F0',[[0,rect(100,100,20,10)],[1,rect(101,101,18,8)]],{zMode:'idw',capPts:false})")
    cek(f["n"] == 1 and f["isl"][0]["closed"] and f["isl"][0]["nt"] > f0["isl"][0]["nt"] and f0["isl"][0]["closed"], "F Z atap IDW + titik pick-up di atap: tertutup (%d segitiga vs %d tanpa titik dalam)" % (f["isl"][0]["nt"], f0["isl"][0]["nt"]))
    # G: lewat UI (SV.run) -> 3D
    pg.evaluate("(function(){var d=SV.D();d.per=d.per.filter(function(p){return p.name==='B';});d.cur=d.per[0].id;d.per[0].par.reg=true;if(VIEW2D)toggle2D();PT.select('sv');SV.run();})()")
    pg.wait_for_function("!SV.busy && SV.per().res", timeout=60000); pg.wait_for_timeout(2500)
    g = pg.evaluate("""(function(){var gd=document.getElementById('plotDiv'),T=gd.data||[];return {mesh:T.filter(function(t){return t.type==='mesh3d'&&/^Vein aktual/.test(t.name||'');}).length,
      garis:T.filter(function(t){return t.type==='scatter3d'&&/^Vein /.test(t.name||'');}).length,titik:T.filter(function(t){return /^Titik atap/.test(t.name||'');}).length,
      md:MD.models.filter(function(m){return m.sv&&m.jenis==='geo';}).length,dom:(typeof rpDomList==='function'?rpDomList().filter(function(q){return /Vein aktual/.test(q[1]);}).length:-1),
      panel:document.getElementById('svBody').textContent.indexOf('Hasil: solid per pulau')>=0&&!document.getElementById('pSV').hidden,v2d:VIEW2D};})()"""); print("G", g)
    cek(g["mesh"] == 2 and g["garis"] == 3 and not g["v2d"], "G 3D: 2 mesh solid + 3 garis poligon tampil di jendela")
    cek(g["titik"] == 1, "G titik atap tampil saat node Solid Vein dibuka")
    cek(g["md"] == 2 and g["dom"] in (2, -1), "G solid terdaftar di Wireframe geologi (domain Reporting: %s)" % g["dom"])
    cek(g["panel"], "G panel Solid Vein tampil dengan tabel hasil")
    pg.evaluate("SV.lihat()"); pg.wait_for_timeout(2500)
    lk = pg.evaluate("""(function(){var gd=document.getElementById('plotDiv'),sc=gd._fullLayout.scene,c=sc.camera,ar=sc.aspectratio,p=SV.per().polys[0],q=p.pts[0],f=function(ax,v,a){var r=ax.range;return((v-(r[0]+r[1])/2)/(r[1]-r[0]))*a;};
      var t=[f(sc.xaxis,q[0],ar.x),f(sc.yaxis,q[1],ar.y),f(sc.zaxis,p.top,ar.z)];return {dc:Math.hypot(t[0]-c.center.x,t[1]-c.center.y,t[2]-c.center.z),de:Math.hypot(c.eye.x-c.center.x,c.eye.y-c.center.y,c.eye.z-c.center.z)};})()"""); print("G lihat", lk)
    cek(lk["dc"] < lk["de"] and lk["de"] < 0.6, "G 'Lihat di 3D': kamera berpusat di vein dan didekatkan (jarak mata %.3f)" % lk["de"])
    pg.evaluate("PT.select('bm')"); pg.wait_for_timeout(2500)
    g2 = pg.evaluate("(function(){var T=document.getElementById('plotDiv').data||[];return {mesh:T.filter(function(t){return t.type==='mesh3d'&&/^Vein aktual/.test(t.name||'');}).length,garis:T.filter(function(t){return t.type==='scatter3d'&&/^Vein /.test(t.name||'');}).length,titik:T.filter(function(t){return /^Titik atap/.test(t.name||'');}).length};})()"); print("G2", g2)
    cek(g2["mesh"] == 2 and g2["garis"] == 3 and g2["titik"] == 0, "G di node lain: poligon & solid TETAP tampil 3D, titik atap disembunyikan")
    pg.evaluate("(function(){SV.setPar('reg',false);})()"); pg.wait_for_timeout(1500)
    g3 = pg.evaluate("(function(){var T=document.getElementById('plotDiv').data||[];return {mesh:T.filter(function(t){return t.type==='mesh3d'&&/^Vein aktual/.test(t.name||'');}).length,md:MD.models.filter(function(m){return m.sv;}).length};})()"); print("G3", g3)
    cek(g3["mesh"] == 2 and g3["md"] == 0, "G tanpa didaftarkan ke Wireframe: solid tetap tampil di 3D")
    pg.evaluate("SV.setPar('reg',true)"); pg.wait_for_timeout(800)
    # slab menyala di 3D: garis poligon semua flitch tetap ada; 'Lihat di 3D' mematikan slab sehingga solid tidak samar
    pg.evaluate("(function(){document.getElementById('sliceClip').checked=true;updatePlot();})()"); pg.wait_for_timeout(2000)
    g4 = pg.evaluate("(function(){var T=document.getElementById('plotDiv').data||[];return T.filter(function(t){return t.type==='scatter3d'&&/^Vein /.test(t.name||'')&&!/sayatan/.test(t.name);}).length;})()")
    pg.evaluate("SV.lihat()"); pg.wait_for_timeout(2500)
    g5 = pg.evaluate("(function(){var T=document.getElementById('plotDiv').data||[],M=T.filter(function(t){return t.type==='mesh3d'&&/^Vein aktual/.test(t.name||'');});return {clip:document.getElementById('sliceClip').checked,n:M.length,op:M.map(function(t){return t.opacity;})};})()"); print("G4", g4, g5)
    cek(g4 == 3, "G slab menyala: 3 garis poligon (semua flitch) tetap tampil di 3D")
    cek(not g5["clip"] and g5["n"] == 2 and min(g5["op"]) >= 0.5, "G 'Lihat di 3D' mematikan slab: solid tampil penuh (opasitas %s)" % g5["op"])
    # H
    pg.evaluate("window.OUTF={};window._gx=gxSimpan;gxSimpan=function(d,fn){OUTF[fn.split('.').pop()]=String(d);return Promise.resolve(fn);};SV.expDtm();SV.expDxf();SV.expCsv();"); pg.wait_for_timeout(800)
    h = pg.evaluate("""(async function(){var d=OUTF.dtm.split(/\\r?\\n/),s=OUTF.str.split(/\\r?\\n/),nt=d.filter(function(l){return /^\\d+, \\d+, \\d+, \\d+, \\d+, \\d+, \\d+,$/.test(l);}).length,np=s.filter(function(l){return /^1, /.test(l);}).length,mx=0,nb0=0;
      d.forEach(function(l){var a=l.split(',');if(/^\\d+$/.test(a[0])&&+a[0]>0&&a.length>=7){mx=Math.max(mx,+a[1],+a[2],+a[3]);if(+a[4]===0||+a[5]===0||+a[6]===0)nb0++;}});
      var L=await SA.readMeshes([new File([OUTF.dtm],'VeinAktual_B.dtm'),new File([OUTF.str],'VeinAktual_B.str')]),m=L[0],V={x:[],y:[],z:[]},T=[];for(var i=0;i<m.nv;i++){V.x.push(m.v[i*3]-offX);V.y.push(m.v[i*3+1]-offY);V.z.push(m.v[i*3+2]);}for(i=0;i<m.nt;i++)T.push([m.t[i*3],m.t[i*3+1],m.t[i*3+2]]);
      return {nt:nt,np:np,mx:mx,nb0:nb0,tris:d.filter(function(l){return /^TRISOLATION/.test(l);}).length,vol:SV.volume(V,T),vol0:SV.per().res.IS.reduce(function(a,s){return a+s.vol;},0),ntRes:SV.per().res.IS.reduce(function(a,s){return a+s.nt;},0),dxf:(OUTF.dxf.match(/3DFACE/g)||[]).length,csv:OUTF.csv.split(/\\r?\\n/).length};})()"""); print("H", h)
    cek(h["nt"] == h["ntRes"] and h["tris"] == 2 and h["mx"] == h["np"] and h["nb0"] == 0, "H DTM: %d segitiga, 2 TRISOLATION, indeks titik s.d. %d, semua segitiga punya 3 tetangga" % (h["nt"], h["np"]))
    cek(abs(h["vol"] - h["vol0"]) < 1e-3 and h["dxf"] == h["nt"] and h["csv"] >= 3, "H DTM+STR dibaca ulang: volume %.3f = %.3f; DXF %d 3DFACE" % (h["vol"], h["vol0"], h["dxf"]))
    pg.evaluate("gxSimpan=window._gx")
    # I
    n0 = pg.evaluate("[DG.S.length, SV.per().polys.length]")
    pg.evaluate("SV.dig()"); pg.wait_for_timeout(2500)
    st = pg.evaluate("({on:DG.on,svm:!!DG.svm,v2d:VIEW2D,fl:dbFlOn()})"); print("I", st)
    cek(st["on"] and st["svm"] and st["v2d"], "I Digit poligon: plan 2D flitch aktif terbuka & mode digit vein menyala")
    snap = pg.evaluate("(function(){var A=dgAx(),q=SV.ptsOn()[0];if(!A||!q)return null;var p=dgPx(A,q.x,q.y),r=dgSnap2(A,p[0],p[1]);return r?[r[0]-q.x,r[1]-q.y]:null;})()"); print("  snap:", snap)
    cek(snap is not None and abs(snap[0]) < 1e-6 and abs(snap[1]) < 1e-6, "I snap ke titik atap tepat di koordinat titik")
    pg.evaluate("(function(){[[60,60],[70,60],[70,68],[60,68]].forEach(function(q){DG.c2.push([q[0]+offX,q[1]+offY]);DG.cur.push(dg3(DG.pl,q[0]+offX,q[1]+offY));});dgFinish(true);})()"); pg.wait_for_timeout(1500)
    n1 = pg.evaluate("[DG.S.length, SV.per().polys.length, DG.on, !!DG.svm]"); print("  sesudah:", n0, "->", n1)
    cek(n1[0] == n0[0] and n1[1] == n0[1] + 1 and not n1[2] and not n1[3], "I poligon digit masuk ke periode, daftar string / dig block tidak berubah")
    w = pg.evaluate("(function(){var w=SA.collectWork();return !!(w.bxui&&w.bxui.sv&&w.bxui.sv.per.length===1&&w.bxui.sv.per[0].polys.length===%d);})()" % n1[1])
    cek(w, "I data Solid Vein ikut tersimpan di proyek (BX.ui.sv)")
    # J (0.24.52): pick-up nyata = CSV tanpa judul "ID,X,Y,Z,kode", beberapa file, RL flitch di NAMA FILE (data sintetis, tata letak sama)
    j = pg.evaluate("""(async function(){var mkf=function(nm,x0,y0,top,pts){var s='';pts.forEach(function(q,i){s+=(i+1)+','+(offX+x0+q[0]).toFixed(3)+','+(offY+y0+q[1]).toFixed(3)+','+(top+q[2]).toFixed(3)+',204\\n';});return new File([s],nm);};
      var L=[[0,0],[20,0],[20,6],[8,6],[8,18],[0,18],[4,3],[14,3],[4,12],[10,0],[0,9],[20,3],[8,12],[4,18],[14,6]].map(function(q,i){return [q[0],q[1],(i%3-1)*0.8];});   /* bentuk L, Z naik-turun +-0,8 m */
      amD().ptsR=[];amPtsFile([mkf('ACT_SO261108OB_235-5_234_ZX.csv',300,300,235.5,L),mkf('ACT_SO261109OB_234_232-5_ZX.csv',302,301,234,L.slice(0,9)),mkf('titik_tanpa_rl.csv',500,500,240,L.slice(0,5))],'ptsR');
      await new Promise(function(r){setTimeout(r,1500);});var F=SV.files(),d=SV.D();d.per=[];d.filt={};SV.addPer();var p=SV.per();p.par.aEdge=13;p.par.dmax=3;p.par.capPts=true;p.par.zMode='idw';SV.auto();
      var R=SV.build(p);return {F:F.map(function(f){return [f.c,f.n,f.top,f.bot];}),lv:[SV.ptsLv(235.5).length,SV.ptsLv(234).length],pol:p.polys.map(function(v){return [v.top,v.bot,v.pts.length,v.src];}),
        isl:R.IS.map(function(s){return [s.closed,s.nLv,+s.vol.toFixed(2)];}),par:[SV.flParse('ACT_SO2611109OB_248-5_246_Z4.csv'),SV.flParse('pickup_roof.csv'),SV.flParse('A_251-5_250_Z4.str')]};})()"""); print("J", j)
    cek(len(j["F"]) == 3 and j["F"][0][1:] == [15, 235.5, 234] and j["F"][1][1:] == [9, 234, 232.5] and j["F"][2][2] != j["F"][2][2], "J file dipisah menurut NAMA FILE (bukan kolom kode) dan RL flitch dibaca dari namanya")
    cek(j["par"][0] == {"top": 248.5, "bot": 246} and j["par"][1] is None and j["par"][2] == {"top": 251.5, "bot": 250}, "J pola nama file: 248-5_246 -> 248,5-246; tanpa pola -> kosong")
    cek(j["lv"] == [15, 9], "J titik dipilah ke flitch menurut file walau Z-nya +-0,8 m dari RL atas (%s)" % j["lv"])
    cek(len(j["pol"]) == 2 and j["pol"][0][:2] == [235.5, 234] and j["pol"][0][3] == "auto" and j["pol"][0][2] >= 6, "J garis luar otomatis: 1 poligon per file ber-flitch, file tanpa RL dilewati (%s)" % j["pol"])
    cek(len(j["isl"]) == 1 and j["isl"][0][0] and j["isl"][0][1] == 2 and j["isl"][0][2] > 0, "J dua flitch bertumpuk -> 1 pulau tertutup 2 flitch, vol %s" % (j["isl"][0][2] if j["isl"] else None))
    pg.evaluate("(function(){amD().ptsR=[];var d=SV.D();d.per=d.per.slice(0,0);})()")
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
