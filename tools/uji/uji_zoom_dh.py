# -*- coding: utf-8 -*-
"""BM 0.24.103 / DH 0.24.106: zoom 3D tidak membangun ulang adegan bila tidak ada lapisan yang resolusinya ikut zoom.
  Z1 tanpa ortho: zoom kamera -> 0 kali updatePlot (dulu 1 kali per zoom: topo TIN + hillshade + semua lapisan dikirim ulang).
  Z2 ortho kecil (muat anggaran pada resolusi piksel asli): zoom -> 0 kali updatePlot, mesh ortho tetap utuh.
  Z3 ortho besar (lebih dari anggaran): zoom -> 1 kali updatePlot (LOD ortho tetap bekerja).
  Z4 segitiga topografi yang tertutup ortho drape (opasitas penuh) tidak digambar; ortho tembus pandang -> topo utuh.
Pemakaian: python tools/uji/uji_zoom_dh.py"""
import random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9400, 9799); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ORT = """(dx)=>{var b=OV.topoF.b,w=Math.floor((b.x1-b.x0)/dx),h=Math.floor((b.y1-b.y0)/dx),px=new Uint8Array(w*h*3).fill(120);
  window.orthoImg={src:'uji.tif',w:w,h:h,dx:dx,dy:dx,e0:b.x0+offX+dx/2,n0:b.y1+offY-dx/2,px:px};orthoInit();var c=$('ovOrtho');c.disabled=false;c.checked=true;$('orRes').value='0';ORT.cache={};updatePlot();return w*h;}"""
def zoom(pg, f):
    pg.evaluate("window.__up=0;HR.ext=null;HR.ver++;")
    pg.wait_for_timeout(500); pg.evaluate("window.__up=0")
    pg.evaluate("(f)=>{Plotly.relayout('plotDiv',{'scene.camera':{eye:{x:1.25*f,y:1.25*f,z:1.25*f},center:{x:0.05,y:0,z:0}}});}", f)
    pg.wait_for_timeout(1500); return pg.evaluate("window.__up")
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1600, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length > 0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(3000)
    pg.evaluate("$('ovTopoS').checked=true;updatePlot();var _u=updatePlot;window.updatePlot=updatePlot=function(){window.__up++;return _u.apply(this,arguments);};")
    pg.wait_for_timeout(2000)
    cek(zoom(pg, 0.4) == 0, "Z1 tanpa ortho: zoom tidak menggambar ulang adegan")
    n = pg.evaluate(ORT, 3); pg.wait_for_timeout(4000)
    n0 = pg.evaluate("$('plotDiv').data.filter(function(t){return t.name==='Orthofoto';})[0].x.length")
    u2 = zoom(pg, 0.3); n2 = pg.evaluate("$('plotDiv').data.filter(function(t){return t.name==='Orthofoto';})[0].x.length")
    cek(u2 == 0 and n2 == n0, "Z2 ortho %s piksel (muat anggaran): zoom -> %s gambar ulang, mesh %s = %s titik" % (n, u2, n2, n0))
    pg.evaluate("$('perfPreset').value='eco'"); n = pg.evaluate(ORT, 0.5); pg.wait_for_timeout(5000)
    u3 = zoom(pg, 0.3)
    cek(u3 == 1, "Z3 ortho %s piksel > anggaran Hemat: zoom -> %s gambar ulang (LOD)" % (n, u3))
    TT = "(function(){var t=$('plotDiv').data.filter(function(t){return t.uid==='ovTopoS';})[0];return t?t.i.length:-1;})()"
    pg.evaluate("$('perfPreset').value='bal';$('ovOrtho').checked=false;updatePlot()"); pg.wait_for_timeout(3000); t0 = pg.evaluate(TT)
    pg.evaluate("HR.ext=null;HR.ver++;$('ovOrtho').checked=true;$('orOp').value=1;ORT.cache={};updatePlot()"); pg.wait_for_timeout(5000); t1 = pg.evaluate(TT)
    pg.evaluate("$('orOp').value=0.6;updatePlot()"); pg.wait_for_timeout(4000); t2 = pg.evaluate(TT)
    cek(t0 > 1000 and 0 <= t1 < t0 * 0.2 and t2 == t0, "Z4 segitiga topo: tanpa ortho %s, tertutup ortho drape %s, ortho tembus 0,6 -> %s" % (t0, t1, t2))
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
