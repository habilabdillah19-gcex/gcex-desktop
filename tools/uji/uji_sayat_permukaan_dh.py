# -*- coding: utf-8 -*-
"""DH 0.24.102 / BM 0.24.99: sayatan 3D ikut memotong topografi & desain pit; Topo × Pit tanpa jaring rusuk segitiga.
  S1 Potong data (slab) aktif: segitiga permukaan topografi / pit di 3D tinggal yang titik beratnya di dalam slab.
  S2 garis potong permukaan dengan bidang tengah sayatan tergambar (Z dekat elevasi sayatan untuk slab horizontal).
  S3 slab dimatikan: permukaan utuh lagi.
  S4 Topo × Pit: desain pit berupa SEGITIGA (potongan 3 titik) -> tidak ada 'Garis jenjang pit' (rusuk segitiga);
     desain pit berupa STRING jenjang -> garis jenjang tetap ada.
Pemakaian: python tools/uji/uji_sayat_permukaan_dh.py"""
import random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9400, 9799); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
INFO = """()=>{var gd=$('plotDiv'),o={};gd.data.forEach(function(t){if(t.uid==='ovTopoS'||t.uid==='ovPitS'){var z0=1e9,z1=-1e9;for(var f=0;f<t.i.length;f++){var z=(t.z[t.i[f]]+t.z[t.j[f]]+t.z[t.k[f]])/3;if(z<z0)z0=z;if(z>z1)z1=z;}o[t.uid]={n:t.i.length,z0:z0,z1:z1};}
  if(t._slabSurf){var zs=t.z.filter(function(v){return v!==null;});o[t.name]={n:zs.length,z0:Math.min.apply(null,zs),z1:Math.max.apply(null,zs)};}});return o;}"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1600, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length > 0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(4000)
    pg.evaluate("$('ovTopoS').checked=true;if($('ovPit')&&!$('ovPit').disabled)$('ovPit').checked=true;$('sliceClip').checked=false;$('sMode').value='H';modeChanged();updatePlot()"); pg.wait_for_timeout(4000)
    a0 = pg.evaluate(INFO)
    zt = a0.get("ovTopoS"); zmid = round((zt["z0"] + zt["z1"]) / 2) if zt else 0
    pg.evaluate("(z)=>{$('pos').value=z;$('thick').value=20;$('sliceClip').checked=true;updatePlot();}", zmid); pg.wait_for_timeout(4000)
    a1 = pg.evaluate(INFO)
    t1 = a1.get("ovTopoS")
    cek(zt and t1 and 0 < t1["n"] < zt["n"] and t1["z0"] >= zmid - 10 - 1e-6 and t1["z1"] <= zmid + 10 + 1e-6, "S1 topo di slab Z %s±10: %s dari %s segitiga, titik berat %s" % (zmid, t1 and t1["n"], zt and zt["n"], t1 and (round(t1["z0"], 1), round(t1["z1"], 1))))
    gl = [v for k, v in a1.items() if k.startswith("Sayatan")]
    cek(gl and all(abs(v["z0"] - zmid) < 1 and abs(v["z1"] - zmid) < 1 for v in gl), "S2 garis potong permukaan: %s" % {k: v for k, v in a1.items() if k.startswith("Sayatan")})
    pg.evaluate("$('sliceClip').checked=false;updatePlot()"); pg.wait_for_timeout(3000); a3 = pg.evaluate(INFO)
    cek(a3.get("ovTopoS", {}).get("n") == zt["n"] and not [k for k in a3 if k.startswith("Sayatan")], "S3 slab mati: topo utuh %s segitiga" % a3.get("ovTopoS", {}).get("n"))
    s4 = pg.evaluate("""()=>{if(!window.TP||!TP.garis)return null;var tri={x:[],y:[],z:[]},str={x:[],y:[],z:[]};
      for(var i=0;i<200;i++){var x=(i%20)*10,y=Math.floor(i/20)*10;[[x,y],[x+10,y],[x,y+10]].forEach(function(p){tri.x.push(p[0]);tri.y.push(p[1]);tri.z.push(50);});tri.x.push(null);tri.y.push(null);tri.z.push(null);}
      [20,40,60].forEach(function(d){[[100-d,100-d],[100+d,100-d],[100+d,100+d],[100-d,100+d],[100-d,100-d]].forEach(function(p){str.x.push(p[0]);str.y.push(p[1]);str.z.push(40+d);});str.x.push(null);str.y.push(null);str.z.push(null);});
      var sv=OV.pitF,st=OV.topoF,r={};var m={gab:{src:{t:'',p:'ov:pit'},at:Math.random()}};
      OV.pitF=tri;r.tri=(TP.garis(m)||[]).map(function(g){return g.nm+':'+g.x.filter(function(v){return v!==null;}).length;});
      m.gab.at=Math.random();OV.pitF=str;r.str=(TP.garis(m)||[]).map(function(g){return g.nm+':'+g.x.filter(function(v){return v!==null;}).length;});
      OV.pitF=sv;OV.topoF=st;return r;}""")
    cek(s4 and not any(x.startswith("Garis jenjang") for x in s4["tri"]) and any(x.startswith("Garis jenjang") for x in s4["str"]), "S4 Topo × Pit: pit segitiga -> %s; pit string -> %s" % (s4 and s4["tri"], s4 and s4["str"]))
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
