# -*- coding: utf-8 -*-
"""Integrasi data struktur -> model vein (solid RBF) tidak berubah oleh perubahan UI 8 Nov 2026
(⋯ / + Tambah / satu pintu import / panel dipisah). A/B: build sebelum perubahan UI (bawaan 4ad4a36) vs build baru.
Data latihan simulasi + SIM_struktur.csv, domain QV_Lensa2. Yang diukur per build:
  v0  volume solid tanpa struktur file           | v1, nst  sesudah SIM_struktur.csv diimport (dipakai RBF)
  v2  sumber SIM_struktur.csv DIMATIKAN (izin geolog per sumber)  -> harus = v0, nst 0
  v3  sumber hidup lagi, tapi domain "Pakai struktur" dimatikan     -> harus = v0, nst 0
  Build baru harus memberi angka identik dengan build lama.
Pemakaian: python tools/uji/uji_struktur_rbf.py [--dasar=<ref git>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "4ad4a36")
JS = r"""(async function(){var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});};
  /* data latihan belum punya domain: buat domain QV_Lensa2 dari wireframe Leapfrog (Serap, Mode B) -> string + solid RBF */
  var mi=MD.models.findIndex(function(m){return /QV_Lensa2/.test(m.name);});WFX.o={mi:mi,sp:0,nama:'QV_Lensa2'};
  var r0=wfSerap();if(r0&&r0.then)await r0;for(var k=0;k<60&&!(GM.doms.length&&IM.R[GM.doms[0].id]);k++)await W(500);
  var d=GM.doms.find(function(x){return x.name==='QV_Lensa2';})||GM.doms[0];
  var ukur=async function(){imSync(true);await W(400);var S=IM.R[d.id]&&IM.R[d.id].st;return S?[Math.round(S.vol),S.nst,S.nstx]:null;};
  d.im=Object.assign(imPar(d),{on:true,str:true});var r={dom:d.name,v0:await ukur()};
  var t=await (await fetch('data-latihan/SIM_struktur.csv')).text();stImport({files:[new File([t],'SIM_struktur.csv')],value:''});await W(1200);
  r.nP=STR.P.length;r.v1=await ukur();
  var f=STR.F.filter(function(x){return x.kind==='csv';})[0];f.on=false;stDirty();r.v2=await ukur();
  f.on=true;stDirty();d.im.str=false;r.v3=await ukur();d.im.str=true;r.v4=await ukur();return r;})()"""

def jalan(html):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
    (d / "index.html").write_bytes(html); os.symlink(DATA, d / "data-latihan")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
        pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
        pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
        r = pg.evaluate(JS); ctx.close()
    srv.terminate(); return r

lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=ROOT, capture_output=True).stdout
A = jalan(lama); B = jalan((ROOT / "app-dh/index.html").read_bytes())
print("lama (%s):" % DASAR, json.dumps(A)); print("baru        :", json.dumps(B))
salah = []
for nm, R in (("lama", A), ("baru", B)):
    if not R.get("v0") or not R.get("v1"): salah.append(nm + ": solid tidak terbangun %s" % R); continue
    if R["v1"][1] <= 0 or R["v1"][0] == R["v0"][0]: salah.append(nm + ": struktur tidak dipakai RBF %s" % R)
    if R["v2"][1] != 0 or R["v2"][0] != R["v0"][0]: salah.append(nm + ": sumber dimatikan tapi struktur masih dipakai %s" % R)
    if R["v3"][1] != 0 or R["v3"][0] != R["v0"][0]: salah.append(nm + ": 'Pakai struktur' domain dimatikan tapi masih dipakai %s" % R)
    if R["v4"] != R["v1"]: salah.append(nm + ": dihidupkan lagi tidak kembali ke hasil semula %s" % R)
if {k: A.get(k) for k in ("v0", "v1", "v2", "v3", "v4", "nP")} != {k: B.get(k) for k in ("v0", "v1", "v2", "v3", "v4", "nP")}: salah.append("angka build baru berbeda dari build lama")
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
