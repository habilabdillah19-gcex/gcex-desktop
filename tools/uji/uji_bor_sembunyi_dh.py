# -*- coding: utf-8 -*-
"""DH 0.24.101: bor di 3D ikut centang dataset / kampanye di Project Tree (dulu tetap digambar walau semua tidak dicentang).
Pemakaian: python tools/uji/uji_bor_sembunyi_dh.py"""
import random, subprocess, sys, tempfile, time, json
gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];d=Path(tempfile.mkdtemp());(d/'index.html').write_bytes((ROOT/'app-dh/index.html').read_bytes());(d/'data-latihan').symlink_to(ROOT/'docs/tutorial-gcex/data')
P=random.randint(9300,9399);srv=subprocess.Popen([sys.executable,'-m','http.server',str(P)],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
TR="""()=>{var g=document.getElementById('gd')||document.querySelector('.js-plotly-plot');var o={};(g&&g.data||[]).forEach(function(t){if(t.visible===false)return;var n=(t.name||t.type)+'|'+t.type;var c=(t.x||[]).filter(function(v){return v!==null;}).length;o[n]=(o[n]||0)+c;});return o;}"""
with sync_playwright() as pw:
    b=pw.chromium.launch(args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"]);pg=b.new_page(viewport={'width':1600,'height':950});pg.on('dialog',lambda x:x.accept())
    pg.goto('http://127.0.0.1:%d/index.html'%P);pg.wait_for_function("window.DLAT && DLAT.siap",timeout=60000);pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length > 0",timeout=600000);pg.wait_for_function("!DLAT.busy",timeout=600000);pg.wait_for_timeout(5000)
    a0=pg.evaluate(TR)
    pg.evaluate("""()=>{['showCollar','showTraj','showLabel','plShow'].forEach(function(k){var e=document.getElementById(k);if(e&&e.checked){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}});if(window.KP)KP.L.forEach(function(k){kpVis(k.id,false);});}""")
    pg.wait_for_timeout(5000)
    a1=pg.evaluate(TR); nv=pg.evaluate('visHoles().length')
    pg.evaluate("if(window.KP)KP.L.forEach(function(k){kpVis(k.id,true);})"); pg.wait_for_timeout(5000); a2=pg.evaluate(TR)
    iv=lambda a: sum(v for k,v in a.items() if '|scatter3d' in k and k.split('|')[0].endswith(')') and k[0] in '<>0123456789')
    cek(iv(a0) > 0, "B1 awal: interval assay tampil (%d titik)" % iv(a0))
    cek(nv == 0 and iv(a1) == 0, "B2 dataset tidak dicentang: visHoles %d, interval assay di 3D %d" % (nv, iv(a1)))
    cek(iv(a2) == iv(a0), "B3 dicentang lagi: interval assay kembali (%d)" % iv(a2))
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
