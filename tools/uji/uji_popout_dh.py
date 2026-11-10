# -*- coding: utf-8 -*-
"""Pop-up Drillhole: Data per lubang, hasil Reporting, Geostatistik dilepas (pemilik 10-11-2026). Data latihan."""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes()); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
gagal = []
def N_(v):
    return "{:,.1f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")
def cek(ok, pesan):
    print(("  ok   " if ok else "  GAGAL ") + pesan)
    if not ok: gagal.append(pesan)
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    a = pg.evaluate("""(async function(){var w=function(t){return new Promise(function(r){setTimeout(r,t);});};var o={};
      o.pop=!!window.POP;o.btn=!!document.getElementById('hdBtn');o.node=PT.flatAll(PT.nodes).some(function(n){return n.id==='db.hole';});
      var id=collars[5][0];HD.buka(id);await w(400);var W=document.getElementById('hdPop');
      var nA=assays.filter(function(r){return r[0]===id;}).length,nG=geoRows.filter(function(r){return r[0]===id;}).length;
      var tb=W?W.querySelectorAll('table.gxtb'):[];o.win=!!(W&&W.style.display!=='none');o.tabel=tb.length;
      var at=[].filter.call(tb,function(t){return /Sample/.test(t.rows[0].textContent);})[0];o.nA=nA;o.rowsA=at?at.rows.length-2:-1;o.nG=nG;
      /* ikut filter Hole ID */
      var id2=collars[9][0],hf=document.getElementById('holeFilter');document.getElementById('benchFilter').value='ALL';benchChanged();hf.value=id2;hf.dispatchEvent(new Event('change',{bubbles:true}));await w(400);o.ikut=HD.id===id2&&/Data per lubang — /.test(W.textContent)&&W.textContent.indexOf(id2)>=0;
      /* hasil Reporting DH */
      if(window.BX&&BX.m&&window.rpRun){uiTab('Rep');rpPanel();await w(300);rpRun();await w(2500);POP.set('rp.res',true);await w(800);var W2=document.getElementById('gxpo_rp_res');o.rp=!!(W2&&W2.style.display!=='none'&&W2.querySelector('.rptb'));}else o.rp='tanpa BM';
      /* panel Geostatistik dilepas */
      var g=document.getElementById('gsPanel');if(g){if(window.gsToggle&&!GS.open)gsToggle();await w(500);var b=g.querySelector('.gh .gxpob');o.gsBtn=!!b;if(b){b.click();await w(400);o.gsFloat=g.classList.contains('gxfloat')&&getComputedStyle(g).position==='fixed';b.click();await w(300);o.gsBack=!g.classList.contains('gxfloat');}}
      o.kin=!!window.KIN;return o;})()""")
    print(a)
    cek(a["pop"] and a["btn"] and a["node"], "DH: modul pop-up, tombol 'Data per lubang' di Data & Filter dan node Database Bor ada")
    cek(a["win"] and a["tabel"] >= 2 and a["rowsA"] == a["nA"], "jendela Data per lubang: collar + assay (%d interval sama dengan database)" % a["nA"])
    cek(a["ikut"], "jendela mengikuti filter Hole ID")
    cek(a["rp"] is True or a["rp"] == "tanpa BM", "hasil Reporting DH di pop-up (%s)" % a["rp"])
    cek(a.get("gsBtn") and a.get("gsFloat") and a.get("gsBack"), "panel Geostatistik bisa dilepas jadi jendela dan dikembalikan")
    cek(a["kin"], "modul Kinerja tetap terpasang")
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: %d" % len(gagal) if gagal else "\nLULUS")
sys.exit(1 if gagal else 0)
