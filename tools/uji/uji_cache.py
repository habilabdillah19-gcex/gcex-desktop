# -*- coding: utf-8 -*-
"""Cache pemilihan blok (BX.scL), geometri kubus (BX.mcL) dan hasil buildDH (DHCL) TIDAK boleh mengubah hasil.
Urutan: atribut A -> B -> A (kembali ke A diambil dari cache), lalu centang overlay, filter kadar, dan A lagi.
Pada tiap langkah tanda tangan lapisan block model (nama, jumlah titik, jumlah segitiga, jumlah koordinat) + teks statistik
dibandingkan dengan hasil perhitungan ULANG tanpa cache (cache dikosongkan paksa, lalu updatePlot). Harus identik.
Juga mencetak waktu sinkron klik pertama vs klik dari cache.
Pemakaian: python tools/uji/uji_cache.py app/index.html | app-dh/index.html"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"; APP = sys.argv[1]; DH = "dh" in APP
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / APP).read_bytes()); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
SIG = r"""(function(){var gd=document.getElementById('plotDiv');var o=[];(gd.data||[]).forEach(function(t){if(t.type!=='mesh3d'&&t.type!=='scatter3d')return;if(t.name==='_rentang')return;/* titik batas rentang tetap: bukan data, boleh berbeda */
 var sx=0,sy=0,sz=0,nn=0;for(var q=0;q<t.x.length;q++){if(t.x[q]==null){nn++;continue;}sx+=t.x[q];sy+=t.y[q];sz+=t.z[q];}
 var zlo=1e18,zhi=-1e18;if(t.type==='mesh3d')for(var qz=0;qz<t.z.length;qz++){if(t.z[qz]<zlo)zlo=t.z[qz];if(t.z[qz]>zhi)zhi=t.z[qz];}
 o.push([t.type,t.name||'',t.x.length,nn,t.i?t.i.length:0,Math.round(sx),Math.round(sy),Math.round(sz),Math.round(zlo*10),Math.round(zhi*10),JSON.stringify(t.line&&t.line.color&&t.line.color.length>50?t.line.color.length:(t.line||t.color||0)),t.opacity]);});
 var st=document.getElementById('stats');return JSON.stringify([o,st?st.innerHTML:'',window.BX&&BX.ui?BX.ui.attr:'',document.getElementById('elementFilter').value,document.getElementById('ttl').textContent]);})()"""
KLIK = "document.querySelector('#ptree .ptr[data-id=\"%s\"] .ptl').click()"
LANGKAH_BM = [("tree", "bm.a.CU_PPM"), ("tree", "bm.a.AU_GC"), ("tree", "bm.a.CU_PPM"), ("cb", "ovTopoS"), ("tree", "bm.a.SG"), ("tree", "bm.a.AU_GC"), ("tree", "bm.a.CU_PPM"),
              # flitch aktif: geometri kubus dipotong di RL flitch (FLz) -> harus ikut kunci cache (laporan pemilik 9 Nov 2026: flitch lama tergambar)
              ("js", "lyApply();if(window.VIEW2D)document.getElementById('btn2d').click()"), ("js", "stepPos(1)"), ("js", "stepPos(-1)"), ("js", "stepPos(1)"), ("tree", "bm.a.AU_GC"), ("js", "stepPos(-1)")]
LANGKAH_DH = [("tree", "db.el.Ag"), ("tree", "db.el.Au"), ("tree", "db.el.Ag"), ("cb", "ovTopoS"), ("tree", "db.geo.0"), ("tree", "db.el.Au"), ("tree", "db.el.Ag")]
LANGKAH = LANGKAH_DH if DH else LANGKAH_BM
BERSIH = "DHCL=[];DHC=null;if(window.BX){BX.scL=[];BX.mcL=[];BX.mc=null;BX.sc={};}"
hasil = []
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    pg.evaluate("for(var k=0;k<3;k++){PT.render(true);PT.flatAll(PT.nodes).forEach(function(n){if(n.kids&&n.kids.length)PT.open[n.id]=1;});}PT.render(true)")
    pg.evaluate("window._LT=0;try{new PerformanceObserver(function(l){l.getEntries().forEach(function(e){window._LT+=e.duration;});}).observe({entryTypes:['longtask']});}catch(e){}")
    def jalan(cache):
        out = []
        # keadaan awal yang sama untuk kedua pass: flitch & slab mati, 3D (langkah flitch di akhir pass sebelumnya mengubahnya)
        pg.evaluate("if(window.lyFlOff)try{lyFlOff();}catch(e){}var c=document.getElementById('sliceClip');if(c&&c.checked){c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));}if(window.VIEW2D)document.getElementById('btn2d').click();"); pg.wait_for_timeout(2500)
        pg.evaluate(BERSIH)
        if not cache: pg.evaluate("window._uP=window._uP||updatePlot;updatePlot=function(){" + BERSIH + "return _uP.apply(this,arguments);}")
        else: pg.evaluate("if(window._uP)updatePlot=_uP;")
        pg.evaluate("(function(id){var c=document.getElementById(id);if(c.checked){c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));}})('ovTopoS')"); pg.wait_for_timeout(800)
        for jenis, target in LANGKAH:
            pg.evaluate("window._LT=0")
            if jenis == "tree": ms = pg.evaluate("(function(){var t=performance.now();%s;return performance.now()-t;})()" % (KLIK % target))
            elif jenis == "js": ms = pg.evaluate("(function(){var t=performance.now();%s;return performance.now()-t;})()" % target)
            else: ms = pg.evaluate("(function(id){var c=document.getElementById(id);var t=performance.now();c.checked=!c.checked;c.dispatchEvent(new Event('change',{bubbles:true}));return performance.now()-t;})('%s')" % target)
            pg.wait_for_timeout(2500)
            ms += pg.evaluate("(function(){var v=window._LT;window._LT=0;return v;})()")
            out.append({"aksi": jenis + ":" + target, "ms": round(ms), "sig": pg.evaluate(SIG)})
        return out
    A = jalan(True); B = jalan(False)
    if DH: pg.evaluate("if(window.trajModeDiam)trajModeDiam('grade')")
    for x, y in zip(A, B): hasil.append({"aksi": x["aksi"], "ms_cache": x["ms"], "ms_tanpa": y["ms"], "lapisan": len(json.loads(x["sig"])[0]), "sama": x["sig"] == y["sig"]})
    ctx.close()
srv.terminate()
for h in hasil: print(h)
for x, y in zip(A, B):
    if x["sig"] != y["sig"]:
        ja, jb = json.loads(x["sig"]), json.loads(y["sig"])
        print("BEDA", x["aksi"], "lapisan:", [p for p in ja[0] if p not in jb[0]], "vs", [p for p in jb[0] if p not in ja[0]], "| statistik sama:", ja[1] == jb[1], "| lain:", ja[2:], jb[2:])
beda = [h["aksi"] for h in hasil if not h["sama"]]
if beda: print("\nGAGAL: hasil dari cache berbeda dengan hitung ulang:", beda)
else: print("\nLULUS" + ("" if hasil[2]["ms_cache"] < hasil[2]["ms_tanpa"] * 0.7 else " (catatan: di lingkungan tanpa GPU waktu didominasi render SwiftShader, jadi selisih cache kecil: %d vs %d ms)" % (hasil[2]["ms_cache"], hasil[2]["ms_tanpa"])))
