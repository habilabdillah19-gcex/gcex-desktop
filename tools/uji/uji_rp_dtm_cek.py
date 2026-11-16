# -*- coding: utf-8 -*-
"""BM 0.24.95: Reporting memperingatkan bila topografi / desain pit berasal dari string / titik (bukan segitiga DTM Surpac).
  D1 data latihan (topo & pit dari .str) + permukaan "Di dalam desain pit": peringatan di panel constraint & di hasil.
  D2 topografi & pit diganti segitiga DTM (string segitiga tertutup, seperti .dtm / DXF 3DFACE): tanda centang, tanpa peringatan.
  D3 "Tanpa batas permukaan": tidak ada peringatan.
Pemakaian: python tools/uji/uji_rp_dtm_cek.py"""
import random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9900, 9999); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1500, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m", timeout=600000); pg.wait_for_timeout(5000)
    r1 = pg.evaluate("""()=>{rpO();RP.o.surf='topo';RP.sec='c';rpPanel();var c=(document.body.textContent.indexOf('Perhatian rekonsiliasi')>=0);rpRun();var res=!!(RP.res&&RP.res.dtmW);return [rpDtmJenis(OV.topoF),rpDtmJenis(OV.pitF),c,res];}""")
    cek(r1[0] == "str" and r1[2] and r1[3], "D1 topografi dari string (%s/%s): peringatan di constraint & hasil" % (r1[0], r1[1]))
    r2 = pg.evaluate("""()=>{var tri=function(src){var x=[],y=[],z=[];var X=src.x,Y=src.y,Z=src.z,P=[];for(var i=0;i<X.length;i++)if(X[i]!=null)P.push([X[i],Y[i],Z[i]]);
        var D=new Delaunator(P.map(function(p){return[p[0],p[1]];}).flat());for(var t=0;t<D.triangles.length;t+=3){[0,1,2,0].forEach(function(k){var p=P[D.triangles[t+k]];x.push(p[0]);y.push(p[1]);z.push(p[2]);});x.push(null);y.push(null);z.push(null);}return{x:x,y:y,z:z};};
        var t0=OV.topoF;OV.topoF=tri(t0);var w=rpDtmCek({surf:'topo'});var j=[rpDtmJenis(OV.topoF)];OV.topoF=t0;return [j,/Perhatian/.test(w),/segitiga DTM/.test(w)];}""")
    cek(r2[0] == ["dtm"] and not r2[1] and r2[2], "D2 permukaan segitiga DTM: %s, tanpa peringatan" % r2[0])
    cek(pg.evaluate("rpDtmCek({surf:'none'})") == "", "D3 tanpa batas permukaan: tidak ada peringatan")
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
