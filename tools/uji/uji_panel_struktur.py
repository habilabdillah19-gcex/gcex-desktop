# -*- coding: utf-8 -*-
"""Drill Hole 0.24.48: panel #pModel dipisah menurut node (keputusan pemilik 8 Nov 2026).
A/B (build lama git <dasar> vs baru), data latihan simulasi + SIM_struktur.csv. Yang diukur (yang TERLIHAT di layar):
  1. Node Struktur Geologi: judul h3 Data referensi, tab, bagian titik survey / string TIDAK terlihat; bagian struktur
     (#stBody, tabel SIM_struktur.csv) terlihat. Build lama: judul Data referensi + tab Titik survey/String terlihat.
  2. Node Data referensi: tab "Struktur" tidak terlihat, #stBody tidak terlihat, bagian titik survey terlihat
     (juga bila sebelumnya tab Struktur yang terakhir dibuka). Build lama: tab Struktur terlihat.
  3. Pindah bolak-balik tetap benar; isi STR.P tidak berubah.
Pemakaian: python tools/uji/uji_panel_struktur.py [--dasar=<ref git>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")
JS_LIHAT = r"""(function(){var p=document.getElementById('pModel');var vis=function(e){if(!e)return false;var r=e.getBoundingClientRect();return r.width>2&&r.height>2&&getComputedStyle(e).visibility!=='hidden';};
  var tabs=[].slice.call(p.querySelectorAll('.uitabs button')).filter(vis).map(function(b){return b.textContent.trim();});
  return {sel:PT.sel,h3:vis(p.querySelector('h3')),tabs:tabs,stBody:vis(document.getElementById('stBody')),ptList:vis(document.getElementById('ptList')),
    stTabel:((document.getElementById('stBody')||{}).innerText||'').indexOf('SIM_struktur.csv')>=0&&vis(document.getElementById('stBody')),nP:STR.P.length};})()"""

def jalan(html):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
    (d / "index.html").write_bytes(html); os.symlink(DATA, d / "data-latihan")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    H = {}
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
        pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
        pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2000)
        pg.evaluate("""(async function(){var t=await (await fetch('data-latihan/SIM_struktur.csv')).text();stImport({files:[new File([t],'SIM_struktur.csv')],value:''});})()"""); pg.wait_for_timeout(1500)
        klik = lambda i: (pg.evaluate("PT.open['sp']=1;PT.open['st']=1;PT.render(true)"), pg.locator("#ptree .ptr[data-id='%s'] .ptl" % i).click(), pg.wait_for_timeout(700))
        klik("st"); H["st1"] = pg.evaluate(JS_LIHAT)
        klik("sp.ref"); H["ref1"] = pg.evaluate(JS_LIHAT)
        klik("st"); H["st2"] = pg.evaluate(JS_LIHAT)
        klik("sp.ref"); H["ref2"] = pg.evaluate(JS_LIHAT)
        ctx.close()
    srv.terminate(); return H

lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=ROOT, capture_output=True).stdout
A = jalan(lama); B = jalan((ROOT / "app-dh/index.html").read_bytes())
for k in A: print(k, "\n  lama:", A[k], "\n  baru:", B[k])
salah = []
if not (A["st1"]["h3"] and A["st1"]["ptList"] is not None and "Struktur" in A["ref1"]["tabs"]): salah.append("build lama tidak menampilkan campuran -> uji tidak membuktikan")
for k in ("st1", "st2"):
    x = B[k]
    if x["h3"] or x["tabs"] or x["ptList"]: salah.append("%s: node Struktur masih menampilkan judul / tab / titik survey %s" % (k, x))
    if not x["stTabel"]: salah.append("%s: bagian struktur (tabel SIM_struktur.csv) tidak terlihat %s" % (k, x))
for k in ("ref1", "ref2"):
    x = B[k]
    if "Struktur" in x["tabs"] or x["stBody"]: salah.append("%s: node Data referensi masih menampilkan struktur %s" % (k, x))
    if not x["ptList"] or not x["h3"]: salah.append("%s: bagian titik survey tidak terlihat %s" % (k, x))
if len({B[k]["nP"] for k in B}) != 1 or B["st1"]["nP"] != A["st1"]["nP"]: salah.append("jumlah titik struktur berubah")
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
