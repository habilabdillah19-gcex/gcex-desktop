# -*- coding: utf-8 -*-
"""BM 0.24.101 / DH 0.24.104: drape orthofoto seperti Ore Works.
  O1 drape di elevasi TIN asli bila grid tampilan (384 sel) lebih kasar dari resolusi mesh (HR.zFast(x,y,res) -> null).
  O2 titik ortho (resolusi 1 m) = topoZ TIN + 0,3 m.
  O3 bayangan matahari dipanggang: lampu Plotly mati (ambient 1); tanah datar = warna asli, lereng lebih terang / gelap.
  O4 Bayangan 'plotly' = warna asli + lampu lama.
Pemakaian: python tools/uji/uji_ortho_drape.py"""
import random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9400, 9799); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1600, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length > 0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(3000)
    # ortho fiktif abu-abu seragam (128) seluas topo, piksel 2 m
    pg.evaluate("""()=>{var b=OV.topoF.b,dx=2,w=Math.floor((b.x1-b.x0)/dx),h=Math.floor((b.y1-b.y0)/dx),px=new Uint8Array(w*h*3).fill(128);
      window.orthoImg={src:'uji_ortho.tif',w:w,h:h,dx:dx,dy:dx,e0:b.x0+offX+dx/2,n0:b.y1+offY-dx/2,px:px};orthoInit();var c=$('ovOrtho');c.disabled=false;c.checked=true;$('orRes').value='1';$('orMode').value='drape';ORT.cache={};updatePlot();}""")
    pg.wait_for_timeout(6000)
    R = pg.evaluate("""()=>{var g=HR.zGrid(),t=$('plotDiv').data.filter(function(t){return t.name==='Orthofoto';})[0];if(!t)return null;var n=t.x.length,mx=0,k=0;
      for(var s=0;s<n;s+=Math.max(1,Math.floor(n/2000))){var z=topoZ(t.x[s],t.y[s]);if(z==null)continue;mx=Math.max(mx,Math.abs(t.z[s]-0.3-z));k++;}
      var v=t.vertexcolor.map(function(c){return +c.slice(4).split(',')[0];}),lo=v.reduce(function(a,b){return a<b?a:b;},999),hi=v.reduce(function(a,b){return a>b?a:b;},-1);
      return {grid:g.dx,zf:HR.zFast(t.x[0],t.y[0],1),dz:mx,k:k,lit:t.lighting,lo:lo,hi:hi,n:n};}""")
    cek(R and R["zf"] is None and R["grid"] > 1, "O1 grid tampilan %s m > resolusi 1 m -> zFast null (pakai TIN)" % (R and round(R["grid"], 2)))
    cek(R and R["k"] > 100 and R["dz"] < 1e-6, "O2 titik ortho = topoZ TIN + 0,3 m (selisih maks %s, %s sampel)" % (R and R["dz"], R and R["k"]))
    cek(R and R["lit"]["ambient"] == 1 and R["lit"]["diffuse"] == 0 and R["lo"] <= 127 and R["hi"] >= 129, "O3 hillshade dipanggang: rentang kanal merah %s–%s dari abu 128" % (R and R["lo"], R and R["hi"]))
    pg.evaluate("$('ovShade').value='plotly';ORT.cache={};updatePlot()"); pg.wait_for_timeout(5000)
    R4 = pg.evaluate("(function(){var t=$('plotDiv').data.filter(function(t){return t.name==='Orthofoto';})[0];var u={};t.vertexcolor.forEach(function(c){u[c]=1;});return [Object.keys(u),t.lighting.ambient];})()")
    cek(R4[0] == ["rgb(128,128,128)"] and R4[1] == 0.85, "O4 Bayangan plotly: warna asli %s, ambient %s" % (R4[0][:3], R4[1]))
    pg.evaluate("$('ovShade').value='kuat';$('orRes').value='0';ORT.cache={};$('btnHome')&&0;updatePlot()"); pg.wait_for_timeout(5000)
    pg.screenshot(path=str(Path(tempfile.gettempdir()) / "uji_ortho_drape.png"))
    # O5 (BM 0.24.102 / DH 0.24.105): anggaran titik ortho Seimbang 1,5 jt -> ortho 1 m (±1 jt piksel) tampil di resolusi piksel asli
    pg.evaluate("""()=>{var b=OV.topoF.b,dx=1,w=Math.floor((b.x1-b.x0)/dx),h=Math.floor((b.y1-b.y0)/dx),px=new Uint8Array(w*h*3);for(var i=0;i<px.length;i++)px[i]=(i*7)%251;
      window.orthoImg={src:'uji_ortho_1m.tif',w:w,h:h,dx:dx,dy:dx,e0:b.x0+offX+dx/2,n0:b.y1+offY-dx/2,px:px};orthoInit();$('ovOrtho').checked=true;$('perfPreset').value='bal';$('orRes').value='0';ORT.cache={};}""")
    pg.evaluate("$('plotDiv').layout.scene.camera={eye:{x:0,y:0,z:1.6},up:{x:0,y:1,z:0}};HR.setExt&&HR.setExt(OV.topoF.b.x0,OV.topoF.b.x1,OV.topoF.b.y0,OV.topoF.b.y1);")
    t5 = pg.evaluate("(function(){var t=performance.now();var o=orthoTrace(true,false);return o?{ms:Math.round(performance.now()-t),n:o.n,res:o.res,px:ORT.m.w*ORT.m.h,bud:HR.anggaran()}:null;})()")
    cek(t5 and t5["bud"] == 1500000 and t5["res"] <= 1.3, "O5 Seimbang: anggaran %s, mesh %s m, %s titik dari %s piksel, %s ms" % (t5 and t5["bud"], t5 and round(t5["res"], 2), t5 and t5["n"], t5 and t5["px"], t5 and t5["ms"]))
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
