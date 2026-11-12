# -*- coding: utf-8 -*-
"""Reporting BM: batas permukaan seperti Surpac (bawaan) + proporsi volume terhadap permukaan (cara GC-Ex).

Permintaan pemilik 12 Nov 2026: "reporting block model hanya yang berada di bawah topografi saja seperti pada Surpac"
dan "Seluruh opsi yang memuat cara surpac harus menjadi default, tapi tetap berikan opsi cara GCEx".

Model SINTETIS (tanpa data nyata): blok 10 x 10 x 10 m, X 0-200, Y 0-100, Z 0-100. Topografi = bidang miring
z = 50 + 0,2 x dari grid titik 5 m yang HANYA menutup X 0-120 (block model lebih luas dari pick-up topografi).
  A. Cara Surpac (bawaan): blok dihitung utuh bila titik pusatnya di bawah topografi DAN berada di dalam jangkauan
     topografi. Blok X > 120 tidak boleh terlapor (dulu IDW mengisi 30 m di luar selubung dan blok yang lebih jauh
     lagi lolos tanpa diuji).
  B. Cara GC-Ex: volume = integral bidang di atas Z 0 pada X 0-120 = 100 x (50 x 120 + 0,1 x 120^2) = 744.000 m3,
     tepat (bidang linear, interpolasi TIN linear, rata-rata kolom titik tengah eksak untuk bidang).
  C. Tab "Metode tonase": baris Cara Surpac = A, baris Cara GC-Ex = B.
  D. Bawaan: sfrac mati (kedua aplikasi), sb_frac mati (Block Model).
Kedua aplikasi (Block Model & Drill Hole).

Pemakaian:  python tools/uji/uji_rp_permukaan.py [--bm app/index.html] [--dh app-dh/index.html]
            (A/B: arahkan --bm / --dh ke build lama; uji harus GAGAL di A dan B)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARG = dict(zip(sys.argv[1::2], sys.argv[2::2]))
HTML = {"bm": Path(ARG.get("--bm", ROOT / "app" / "index.html")), "dh": Path(ARG.get("--dh", ROOT / "app-dh" / "index.html"))}
PORT = {"bm": 8791, "dh": 8792}

# harapan analitis
CX = [5 + 10 * i for i in range(20)]
CZ = [5 + 10 * i for i in range(10)]
N_SURPAC = sum(10 for cx in CX if cx <= 115 for cz in CZ if cz <= 50 + 0.2 * cx)
V_SURPAC = N_SURPAC * 1000.0
V_GCEX = 100.0 * (50 * 120 + 0.1 * 120 ** 2)

JS = r"""async function(){
  var ox=(typeof offX!=='undefined'?offX:0)||0, oy=(typeof offY!=='undefined'?offY:0)||0;
  var X=[],Y=[],Z=[];for(var a=0;a<20;a++)for(var b=0;b<10;b++)for(var c=0;c<10;c++){X.push(5+10*a+ox);Y.push(5+10*b+oy);Z.push(5+10*c);}
  var n=X.length,F=function(v){var r=new Float32Array(n);r.fill(v);return r;};
  var m={name:'uji_permukaan',n:n,x:new Float64Array(X),y:new Float64Array(Y),z:new Float64Array(Z),sx:F(10),sy:F(10),sz:F(10),
    num:{au:F(1)},cat:{},sizes:'10',ext:[0,200,0,100,0,100],s0:10};
  BX.m=m;BX.ver=(BX.ver||0)+1;
  var tx=[],ty=[],tz=[];for(var x=0;x<=120;x+=5)for(var y=0;y<=100;y+=5){tx.push(x);ty.push(y);tz.push(50+0.2*x);}
  OV.topoF={x:tx,y:ty,z:tz};
  if(typeof spAct==='function'){window.spAct=function(){return null;};}
  RP.o=null;var o=rpO(),out={def:{sfrac:o.sfrac,frac:o.frac}};
  o.surf='topo';o.cuts='0';o.gr='au';o.atts=['au'];o.grp='none';o.sx=[];o.show=false;
  if(o.sgMode!==undefined){o.sgMode='c';o.sg=1;} else {BX.ui=BX.ui||{};BX.ui.sg=1;BX.ui.sgCol='';}
  var tot=function(){var G=RP.res.rows[0].G,r={n:0,v:0,t:0};Object.keys(G).forEach(function(k){r.n+=G[k].n;r.v+=G[k].v;r.t+=G[k].t;});r.nOut=RP.res.nOut;return r;};
  rpRun();out.A=tot();
  o.sfrac=true;o.sfN=4;rpRun();out.B=tot();o.sfrac=false;
  if(window.RPM){RPM.res=null;RPM.run();for(var k=0;k<200&&(RPM.busy||!RPM.res);k++)await new Promise(function(r){setTimeout(r,50);});
    var X2=RPM.res;out.C={s:X2&&X2.surpac.rows[0].v,g:X2&&X2.presisi?X2.presisi.rows[0].v:null};}
  return out;}"""


def jalankan(app: str, galat: list) -> None:
    from playwright.sync_api import sync_playwright
    d = Path(tempfile.mkdtemp(prefix="rpperm_"))
    shutil.copy(HTML[app], d / "index.html")
    (d / "data-latihan").symlink_to(ROOT / "docs" / "tutorial-gcex" / "data")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT[app])], cwd=str(d),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 1500, "height": 900})
            pg.on("dialog", lambda x: x.accept())
            pg.on("pageerror", lambda e: galat.append("%s: galat halaman: %s" % (app, str(e)[:160])))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT[app])
            pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
            pg.evaluate("document.getElementById('dlatBtn').click()")      # data latihan fiktif hanya untuk membuka viewer
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0 && typeof rpRun==='function'", timeout=600000)
            pg.wait_for_function("!DLAT.busy", timeout=600000)
            pg.wait_for_timeout(2000)
            r = pg.evaluate(JS)
            b.close()
    finally:
        srv.terminate()
        shutil.rmtree(d, ignore_errors=True)
    A, B, C = r["A"], r["B"], r.get("C") or {}
    print("== %s ==" % app)
    print("  bawaan        sfrac=%s frac=%r" % (r["def"]["sfrac"], r["def"]["frac"]))
    print("  A Surpac      %6d blok  %12.1f m3  (harapan %d blok, %.1f m3)  dikeluarkan %s" % (A["n"], A["v"], N_SURPAC, V_SURPAC, A["nOut"]))
    print("  B GC-Ex       %6d blok  %12.1f m3  (harapan %.1f m3)" % (B["n"], B["v"], V_GCEX))
    print("  C tab metode  Surpac %s | GC-Ex %s" % (C.get("s"), C.get("g")))
    cek = lambda ok, pesan: ok or galat.append("%s: %s" % (app, pesan))
    cek(r["def"]["sfrac"] is False, "bawaan sfrac bukan False (cara Surpac harus bawaan)")
    if app == "bm":
        cek(r["def"]["frac"] is False, "bawaan sb_frac Block Model bukan False (cara Surpac harus bawaan)")
    cek(A["n"] == N_SURPAC and abs(A["v"] - V_SURPAC) < 1e-6, "A: cara Surpac tidak sama dengan titik pusat di dalam jangkauan topografi")
    cek(abs(B["v"] - V_GCEX) < 1e-3 * V_GCEX, "B: proporsi volume terhadap permukaan tidak sama dengan volume analitis")
    cek(C.get("s") is not None and abs(C["s"] - A["v"]) < 1e-6, "C: baris Cara Surpac di tab Metode tonase != A")
    cek(C.get("g") is not None and abs(C["g"] - B["v"]) < 1e-6, "C: baris Cara GC-Ex di tab Metode tonase != B")


def main() -> int:
    galat: list = []
    for app in ("bm", "dh"):
        try:
            jalankan(app, galat)
        except Exception as e:
            galat.append("%s: %s" % (app, e))
    print()
    if galat:
        print("GAGAL (%d):" % len(galat))
        for g in galat:
            print("  -", g)
        return 1
    print("LULUS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
