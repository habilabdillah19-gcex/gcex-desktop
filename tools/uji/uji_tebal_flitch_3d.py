# -*- coding: utf-8 -*-
"""Tebal block model yang digambar di 3D HARUS sama dengan tebal flitch aktif.

Tinggi flitch sengaja dibuat 1,5 m, LEBIH KECIL dari tinggi blok data latihan (2,5 m). Itu bukan
kebetulan: dengan flitch yang sama besar dengan tinggi blok, "blok dipilih lalu digambar utuh" dan
"blok dipotong di RL flitch" memberi angka yang IDENTIK -- dan uji seperti itu lolos sambil
membiarkan cacatnya hidup. Persis itu yang terjadi: perbaikan 0.24.31 diuji dengan flitch 2,5 m,
lolos, lalu pemilik melaporkan 3D-nya masih berbentuk pagar tegak.

Diuji pada dua mode komposit ('comp' dan 'mid'), sebab keduanya menempuh cabang berbeda di bxSel().
"""
import os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path("/home/claude/gcex-desktop"); PORT=str(random.randint(9100,9899))
OUT=Path("/tmp/claude-0/-home-claude/d60768e3-df84-535c-a4b8-ec5d39e6bda3/scratchpad")
d=Path(tempfile.mkdtemp(prefix="gcex_cmp_")); shutil.copyfile(ROOT/"app"/"index.html",d/"index.html")
os.symlink(ROOT/"docs"/"tutorial-gcex"/"data",d/"data-latihan")
subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen("http://localhost:%s/index.html"%PORT,timeout=1); break
    except Exception: time.sleep(0.4)

JS_SET=r"""(function(mode){var m=BX.m;
  var zc={},i;for(i=0;i<m.n;i++){var k=Math.round(m.z[i]*100);zc[k]=(zc[k]||0)+1;}
  var zb=null,nb=-1;Object.keys(zc).forEach(function(k){if(zc[k]>nb){nb=zc[k];zb=+k/100;}});
  var L=lyU();
  try{lySet('flMode',mode);}catch(e){L.flMode=mode;}
  L.fh=1.5; L.top=zb+0.75; L.bot='';
  lySet('fh',1.5); lySet('top',+(zb+0.75).toFixed(3));
  lyApply();
  return{top:lyBench()[0],bot:lyBench()[1],flMode:(window.lyFlMode?lyFlMode():'?')};})"""
JS_LAPIS=r"""(function(){var g=document.getElementById('plotDiv'),dd=(g&&g.data)||[],F=function(v){return isFinite(v)?+(+v).toFixed(2):null;};
  var bm=[];dd.forEach(function(t){var n=(t.z&&t.z.length)||0;if(!n||t.type!=='mesh3d')return;
    var nm=String(t.name||'');if(!/auok|AU|<|>|≥/i.test(nm))return;
    var z0=1e9,z1=-1e9;for(var i=0;i<n;i++){var v=t.z[i];if(isFinite(v)){if(v<z0)z0=v;if(v>z1)z1=v;}}
    bm.push({nama:nm.slice(0,28),zmin:F(z0),zmax:F(z1)});});
  return{fl:!!(window.BX&&BX.ui&&BX.ui.fl),secMode:(window.secGeom?secGeom().m:'?'),
         bench:(window.lyBench?lyBench():null),view2d:!!window.VIEW2D,blok:bm};})"""
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(prefix="gcex_cmpc_"),
        args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    er=[]; pg.on("pageerror",lambda e:er.append(str(e)[:140]))
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(3000)
    salah=[]
    for mode in ("comp","mid"):
        print("\n######## flMode = %s ########"%mode)
        print("  terapkan:",pg.evaluate(JS_SET,mode)); pg.wait_for_timeout(3500)
        pg.evaluate("(function(){if(window.VIEW2D)document.getElementById('btn2d').click();})()")
        pg.wait_for_timeout(4000)
        R=pg.evaluate(JS_LAPIS)
        print("  fl=%s  mode sayatan=%s  flitch=%s  2D=%s"%(R["fl"],R["secMode"],R["bench"],R["view2d"]))
        lo,hi = min(R["bench"]), max(R["bench"])
        for b in R["blok"]:
            print("    %-30s z %-8s .. %s"%(b["nama"],b["zmin"],b["zmax"]))
            if abs(b["zmin"]-lo) > 1e-6 or abs(b["zmax"]-hi) > 1e-6:
                salah.append("flMode %s, lapisan %s: digambar %s..%s, seharusnya %s..%s"
                             % (mode, b["nama"], b["zmin"], b["zmax"], lo, hi))
        if not R["blok"]: salah.append("flMode %s: tidak ada lapisan block model yang tergambar"%mode)
        pg.screenshot(path=str(OUT/("comp_%s.png"%mode)))
    if er: print("galat:",er[:3])
    ctx.close()

if salah:
    print("\nGAGAL (%d):"%len(salah))
    for x in salah: print("  - %s"%x)
    raise SystemExit(1)
print("\nBENAR: tebal block model yang digambar sama persis dengan tebal flitch aktif.")
