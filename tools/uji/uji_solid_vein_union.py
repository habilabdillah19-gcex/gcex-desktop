# -*- coding: utf-8 -*-
"""Solid Vein Aktual: satukan pulau (boolean union) + rekonsiliasi dengan wireframe model -- GC-Ex Block Model 0.24.71
(web-src/svbool_bm.js, web-src/svrek_bm.js, pustaka web-src/mfbool.js + manifold.js). Data SINTETIS.
Pemilik 12 Nov 2026: "Nomor 2" (union + rekonsiliasi).
  U1 dua poligon 20 x 10 bergeser 10 m di dua flitch, penggabungan 2D dimatikan -> dua pulau saling menembus;
     union = 1 tubuh, volume 30 x 10 x 2 flitch (dulu 40 x 10 x 2, ganda); pilihan dimatikan = dua pulau
  U2 pulau yang tidak bertampalan tidak diubah
  U4 (0.24.72) dua pick-up satu flitch digabung, titik potong segaris: solid tetap tertutup
  U3 Bangun solid menyimpan hasil tersatukan; ekspor DTM satu TRISOLATION
  K  model = kotak X 120-140 (aktual X 100-130), dua flitch: tergali 10x10x2fh, dilusi 20x10x2fh;
     ore loss lebar zona 3 m = (133-130) x 10 x 2fh, lebar 0 = 0; tampil di panel & 3D
Pemakaian: python tools/uji/uji_solid_vein_union.py   (A/B: build lama tanpa SVB/SVK -> GAGAL)"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app/index.html").read_bytes()); os.symlink(DATA, d / "data-latihan")
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
    ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://localhost") or r.request.url.startswith("data:") or r.request.url.startswith("blob:") else r.abort())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    ada = pg.evaluate("!!(window.SVB && window.SVK && window.MFB)")
    cek(ada, "modul union & rekonsiliasi Solid Vein terpasang")
    if ada:
        fh = pg.evaluate(JS_SIAP); print("tinggi flitch:", fh)
        pg.evaluate("MFB.load()"); pg.wait_for_function("MFB.ok() || MFB.err", timeout=60000)
        cek(pg.evaluate("MFB.ok()"), "pustaka boolean termuat tanpa jaringan (%s)" % pg.evaluate("MFB.err"))
        # U1: dua poligon bertampalan di dua flitch, penggabungan 2D dimatikan -> dua pulau saling menembus
        u = pg.evaluate("mk('U1',[[0,rect(100,100,20,10)],[0,rect(110,100,20,10)],[1,rect(100,100,20,10)],[1,rect(110,100,20,10)]],{gab:false})"); print("U1", u)
        v = [s["vol"] for s in u["isl"]]
        cek(u["n"] == 1 and u["isl"][0]["closed"] and abs(v[0] - 600 * fh) < 1e-4, "U1 dua pulau bertampalan disatukan: 1 tubuh tertutup, volume %.4f = %.4f (dulu %.4f)" % (v[0] if v else -1, 600 * fh, 800 * fh))
        r0 = pg.evaluate("(function(){var p=SV.D().per[SV.D().per.length-1];p.par.uni=false;var R=SV.build(p);p.par.uni=true;return R.IS.map(function(s){return s.vol;});})()")
        cek(abs(sum(r0) - 800 * fh) < 1e-4, "U1 pilihan dimatikan: kembali seperti dulu, %d pulau berisi dua cangkang saling menembus, volume %.4f (ganda)" % (len(r0), sum(r0)))
        # U2: pulau terpisah tidak disentuh
        b = pg.evaluate("mk('U2',[[0,rect(100,100,20,10)],[1,rect(100,100,20,10)],[1,rect(170,100,10,10)]])"); print("U2", b)
        vols = sorted(round(s["vol"], 6) for s in b["isl"])
        cek(b["n"] == 2 and abs(vols[0] - 100 * fh) < 1e-6 and abs(vols[1] - 400 * fh) < 1e-6, "U2 pulau yang tidak bertampalan tidak diubah (volume tepat sama)")
        # U4 (0.24.72): dua pick-up satu flitch yang digabung, titik potongnya jatuh TEPAT di sisi poligon pertama (segaris
        # dengan sudutnya) -> segitiga lantai berluas nol. Dulu dibuang -> solid berlubang (3 sisi terbuka) -> rekonsiliasi
        # menolak "bukan mesh tertutup". Bentuk kasus lapangan, diputar 180 derajat & diskala 2x (eksak dalam floating point,
        # jadi pembulatan yang memicu kasus ini tetap sama; geser biasa menghilangkannya). Koordinat fiktif.
        g = pg.evaluate("mk('U4',[[0,[[-1999.8919999999925, -2439.822000000626], [-1999.7600000000093, -2451.807999998331], [-1992.9220000000205, -2465.8859999999404], [-1988.6620000000112, -2469.9340000003576], [-1979.1340000000782, -2470.140000000596], [-1985.3540000000503, -2455.210000000894], [-1993.8240000000224, -2444.5159999988973], [-1996.8940000000875, -2441.302000001073]]],[0,[[-1999.591999999946, -2439.7459999993443], [-1999.6059999999125, -2451.7439999990165], [-1993.4760000000242, -2464.6140000000596], [-1991.1599999999162, -2469.177999999374], [-1979.2399999999907, -2469.4640000015497], [-1985.8359999998938, -2454.629999998957]]]])"); print("U4", g)
        cek(g["n"] == 1 and g["isl"][0]["closed"] and g["isl"][0]["open"] == 0, "U4 gabungan dua pick-up dengan titik potong segaris: solid tertutup (sisi terbuka %s)" % (g["isl"][0]["open"] if g["isl"] else "-"))
        # U3 + K: periode nyata (Bangun solid), model kotak, rekonsiliasi
        pg.evaluate("""(function(){var d=SV.D(),p={id:'rek1',name:'REK',from:'',to:'',polys:[],par:{dmax:10,zMode:'flat',rIdw:6,zTol:FH/2,capPts:false,method:'min',sg:2.5,reg:false,gab:false},res:null};d.per.push(p);d.cur=p.id;
          [[0,rect(100,100,20,10)],[0,rect(110,100,20,10)],[1,rect(100,100,20,10)],[1,rect(110,100,20,10)]].forEach(function(q,i){p.polys.push({id:'r'+i,top:T0-q[0]*FH,bot:T0-(q[0]+1)*FH,pts:q[1],key:'q'+i,src:'digit',name:'R'+i,on:true});});
          var x0=120+offX,x1=140+offX,y0=100+offY,y1=110+offY,z0=T0-2*FH,z1=T0,P=[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],F=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]];
          var v=[];P.forEach(function(q){v.push(q[0],q[1],q[2]);});var t=[];F.forEach(function(f){t.push(f[0],f[1],f[2]);});
          MD.models.push({name:'Model_uji',v:new Float64Array(v),t:new Uint32Array(t),nv:8,nt:12,jenis:'geo',col:'#888',op:0.5,vis:true});SV.run();})()""")
        pg.wait_for_function("(function(){var p=SV.D().per.filter(function(q){return q.id==='rek1';})[0];return p&&p.res&&!SV.busy;})()", timeout=120000)
        U3 = pg.evaluate("(function(){var p=SV.per();return {n:p.res.IS.length,vol:p.res.IS[0].vol,uni:p.res.uni};})()"); print("U3", U3)
        cek(U3["n"] == 1 and abs(U3["vol"] - 600 * fh) < 1e-4 and U3["uni"] and U3["uni"]["nGab"] == 2, "U3 Bangun solid menyimpan hasil tersatukan (1 tubuh, ringkasan union tersimpan)")
        X = pg.evaluate("(function(){var a=null;window.gxSimpan=function(t,n){a=a||[];a.push([n,t]);return Promise.resolve(true);};SV.expDtm();return new Promise(function(ok){setTimeout(function(){ok(a);},300);});})()")
        dtm = [t for n, t in (X or []) if n.endswith(".dtm")]
        cek(bool(dtm) and dtm[0].count("TRISOLATION") == 1, "U3 ekspor DTM: satu TRISOLATION (satu solid)")
        for buf, harap_loss in ((3, 60 * fh), (0, 0.0)):
            pg.evaluate("(function(){var p=SV.per();SVK.set('buf',%s);p.rek.mods=['Model_uji'];SVK.hitung();})()" % buf)
            pg.wait_for_function("!SVK.busy && SVK.R['rek1'] && (SVK.R['rek1'].part || SVK.R['rek1'].err)", timeout=120000); pg.wait_for_timeout(300)
            K = pg.evaluate("(function(){var r=SVK.R['rek1'];if(r.err)return {err:r.err};return {tg:r.part.tg.vol,dil:r.part.dil.vol,loss:r.part.loss.vol,mz:r.volMZ,buf:r.buf,html:(document.getElementById('svBody')||{}).innerText||''};})()"); print("K", buf, {k: K[k] for k in K if k != "html"})
            cek(not K.get("err") and abs(K["tg"] - 200 * fh) < 1e-3 and abs(K["dil"] - 400 * fh) < 1e-3, "K lebar %s m: ore tergali %.3f = %.3f, dilusi %.3f = %.3f" % (buf, K.get("tg", -1), 200 * fh, K.get("dil", -1), 400 * fh))
            cek(not K.get("err") and abs(K["loss"] - harap_loss) < 1e-3, "K lebar %s m: ore loss %.3f = %.3f (model di luar zona = belum ditambang)" % (buf, K.get("loss", -1), harap_loss))
        cek("Ore loss" in K.get("html", "") and "Dilusi" in K.get("html", ""), "K tabel rekonsiliasi tampil di panel")
        T = pg.evaluate("(function(){SV.show=true;var T=[];dgTraces(T,{clip:false,K:null});return T.filter(function(t){return /^(Ore tergali|Dilusi|Ore loss)/.test(t.name||'');}).map(function(t){return t.name;});})()")
        cek(len(T) >= 2, "K bagian rekonsiliasi tampil di 3D: %s" % T)
        if ada and os.environ.get("SHOT"):
            pg.evaluate("SVK.set('buf',3);SVK.hitung()"); pg.wait_for_function("!SVK.busy", timeout=60000)
            pg.evaluate("(function(){try{PT.select('sv')}catch(e){};SV.show=true;SV.foc='rek';SV.panel();SV.lihat();})()"); pg.wait_for_timeout(3500)
            pg.screenshot(path=os.environ["SHOT"])
    cek(not err, "tanpa galat halaman: %s" % err[:2])
    ctx.close()
srv.terminate()
print("\nGAGAL (%d)" % len(gagal) if gagal else "\nLULUS")
sys.exit(1 if gagal else 0)
