# -*- coding: utf-8 -*-
"""Ore Geometry Studio (Drill Hole 0.24.72): satu jendela pop-up berisi semua menu Ore Geometry.
Data latihan simulasi (Demo = jalur Lanjutkan: wireframe impor QV_Lensa*).

1. Panel samping hanya ringkasan + tombol pembuka (tidak ada lagi #ogBody di panel).
2. Flag otomatis dari wireframe: jumlah interval di dalam domain = hitungan wfInside langsung (titik tengah, prioritas urutan).
3. Intercept: tebal sebenarnya <= panjang, GT = kadar x tebal.
4. Semua halaman Studio tergambar tanpa galat; grafik Plotly ada di halaman bergrafik.
5. Envelope RBF: volume > 0 untuk domain utama; RBF dengan smoothing 0 melewati titik data (galat < 1e-6).
6. Penampang: sayatan usulan, Maju/Mundur menggeser posisi 2 x lebar jendela; Slicer 3D tidak berubah (berdiri sendiri).
7. Alat lama (Intercept / LS GT / Ore shoot / Grade shell) tergambar di dalam Studio dan tombol Hitung intercept jalan.
8. Jalur Mulai dari Nol: solid GC-Ex (IM.R) ikut menjadi sumber domain bila wireframe impor dimatikan.
9. Simpan / buka proyek: parameter Studio (sayatan, prioritas) kembali.
Pemakaian: python tools/uji/uji_ore_studio_dh.py [--gambar=<folder>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
GBR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--gambar=")), "")

JS = r"""(async function(){var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});},o={};
  uiTab('OG');await W(300);o.side={btn:!!document.querySelector('#ogsSide .btn-pri'),lama:!document.querySelector('#pOG #ogBody')};
  ogsOpen('data');await W(200);var F=ogsFlag();ogsRender();await W(600);
  /* hitungan langsung */
  var src=ogsSrc().filter(function(s){return OGS.p.mesh[s.k];}),Wf=src.map(function(s){return wfInside(s.m);}),cnt=src.map(function(){return 0;});
  (window.assays||[]).forEach(function(a){if(!(a[2]>a[1])||!holeData[a[0]])return;var p=getXYZ(a[0],(a[1]+a[2])/2);for(var q=0;q<Wf.length;q++)if(Wf[q].f(p.x,p.y,p.z)){cnt[q]++;break;}});
  o.flag={dom:F.dom.map(function(d){return d.nm;}),studio:F.dom.map(function(d,q){return ogsIn(F,q).length;}),langsung:cnt,nI:F.I.length};
  o.ic={Tlebih:F.I.filter(function(c){return c.T>c.L+1e-9;}).length,gtSalah:F.I.filter(function(c){return isFinite(c.gt)&&Math.abs(c.gt-c.g[ogsEi(ogsAu())]*c.T)>1e-9;}).length};
  /* RBF interpolasi tepat */
  var U=[0,10,25,40,7],Z=[0,5,-3,12,20],V=[1,3,2,5,4],f=ogsRbf(U,Z,V,0);o.rbf=Math.max.apply(null,U.map(function(u,i){return Math.abs(f(u,Z[i])-V[i]);}));
  o.hal={};var nav=['data','geo','kadar','ls','env','zon','prof','sec','lama','red','t2'];
  for(var i=0;i<nav.length;i++){ogsGo(nav[i]);await W(nav[i]==='env'?2500:900);var c=document.getElementById('ogsC');o.hal[nav[i]]={plot:c.querySelectorAll('.js-plotly-plot').length,galat:/Galat:/.test(c.textContent),tabel:c.querySelectorAll('table').length};}
  ogsGo('env');await W(2000);var q=+OGS.p.envDom,E=ogsEnv(q);o.env={dom:F.dom[q].nm,vol:Math.round(E.vol),ton:Math.round(E.ton),near:Math.round(E.near),cells:E.nCell};
  ogsGo('lama');await W(600);o.lama={body:!!document.querySelector('#ogsC #ogBody'),isi:(document.querySelector('#ogsC #ogBody')||{}).innerHTML.length||0};ogRunIc();await W(400);o.lama.R=!!OG.R;
  ogsGo('sec');await W(800);ogsSecUsul();await W(900);var s0=OGS.p.sec[OGS.p.secI],ls0=s0.ls,K0=JSON.stringify(window.SEC||window.secGeom&&secGeom()||null);ogsSecStep(1);await W(700);
  o.sec={n:OGS.p.sec.length,geser:OGS.p.sec[OGS.p.secI].ls-ls0,win:s0.win,slicerTetap:JSON.stringify(window.SEC||window.secGeom&&secGeom()||null)===K0,plot:!!document.querySelector('#ogsSP .main-svg')};
  /* Mulai dari Nol: solid GC-Ex (Vein System dari kolom "Vein") sebagai sumber, wireframe impor dimatikan */
  var col=VS.kolom().filter(function(c){return c.n==='Vein'&&c.src==='g';})[0];gmOpt('vsCol',col.key);gmOpt('vsGap',0);VS.terapkan(true);await W(500);imSync(true);await W(800);
  var S=ogsSrc();S.forEach(function(s){OGS.p.mesh[s.k]=s.k[0]==='i';});var F2=ogsFlag();
  o.nol={src:S.map(function(s){return [s.nm,s.j,!!OGS.p.mesh[s.k]];}),dom:F2?F2.dom.length:0,nI:F2?F2.I.length:0,isi:F2?F2.dom.map(function(d,q){return ogsIn(F2,q).length;}):[]};
  ogsGo('env');await W(2500);o.nol.env=!!document.querySelector('#ogsEnv .main-svg');ogsGo('sec');await W(1200);o.nol.sec=!!document.querySelector('#ogsSP .main-svg');
  /* simpan / buka */
  OGS.p.sec[0].nm='Uji';var w=SA.collectWork();OGS.p.sec=[];SA.applyWork(w);await W(300);o.simpan=OGS.p.sec.length&&OGS.p.sec[0].nm==='Uji';
  return o;})()"""

SHOT = r"""(async function(nav){var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});};if(!OGS.F)ogsFlag();ogsGo(nav);await W(nav==='env'?2500:1200);return 1;})"""


def jalan(html):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
    (d / "index.html").write_bytes(html); os.symlink(DATA, d / "data-latihan")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    err = []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1600, "height": 950})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
        pg.on("pageerror", lambda e: err.append(str(e)[:300]))
        pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
        pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
        r = pg.evaluate(JS)
        if GBR:
            os.makedirs(GBR, exist_ok=True)
            for nav in ['data', 'geo', 'kadar', 'ls', 'env', 'zon', 'prof', 'sec', 'lama']:
                pg.evaluate(SHOT + "('%s')" % nav); pg.screenshot(path=os.path.join(GBR, nav + '.png'))
        ctx.close()
    srv.terminate(); r["pageerror"] = err; return r


R = jalan((ROOT / "app-dh/index.html").read_bytes()); print(json.dumps(R, ensure_ascii=False, indent=1))
salah = []
if not (R["side"]["btn"] and R["side"]["lama"]): salah.append("panel samping: %s" % R["side"])
if R["flag"]["studio"] != R["flag"]["langsung"]: salah.append("flag Studio beda dengan hitungan langsung")
if not R["flag"]["nI"]: salah.append("tidak ada intercept")
if R["ic"]["Tlebih"] or R["ic"]["gtSalah"]: salah.append("intercept: %s" % R["ic"])
if R["rbf"] > 1e-6: salah.append("RBF tidak melewati titik data: %s" % R["rbf"])
for k, v in R["hal"].items():
    if v["galat"]: salah.append("halaman %s galat" % k)
    if k in ("data", "geo", "ls", "env", "zon", "prof", "sec") and not v["plot"]: salah.append("halaman %s tanpa grafik" % k)
if not (R["env"]["vol"] > 0 and R["env"]["cells"] > 0): salah.append("envelope kosong: %s" % R["env"])
if not (R["lama"]["body"] and R["lama"]["isi"] > 500 and R["lama"]["R"]): salah.append("alat lama: %s" % R["lama"])
s = R["sec"]
if s["n"] < 1 or abs(s["geser"] - 2 * s["win"]) > 1e-6 or not s["slicerTetap"] or not s["plot"]: salah.append("penampang: %s" % s)
n = R["nol"]
if n["dom"] < 2 or n["nI"] < 1 or min(n["isi"] or [0]) < 1 or not n["env"] or not n["sec"]: salah.append("jalur Mulai dari Nol (solid GC-Ex): %s" % n)
if not R["simpan"]: salah.append("parameter Studio tidak tersimpan")
if R["pageerror"]: salah.append("galat halaman: %s" % R["pageerror"][:3])
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
sys.exit(1 if salah else 0)
