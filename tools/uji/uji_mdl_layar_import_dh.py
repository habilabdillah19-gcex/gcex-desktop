# -*- coding: utf-8 -*-
"""DH 0.24.70: Import Block Model .mdl di LAYAR IMPORT (sebelum "Mulai") gagal sejak 0.24.61 dengan
"mdlAttrs is not defined": pembaca .mdl di layar Import memakai mdlAttrs (web-src/mdlattr.js) yang hanya ikut di dalam
skrip viewer (vsrc). Ditemukan saat menjalankan data nyata Zona 2 (11-11-2026).
Uji (data latihan fiktif):
  1. halaman A: kerangka AOI kecil dari data latihan -> .mdl (NY.mdlSynth + bxMdlBytes) disimpan ke berkas sementara
  2. halaman B baru: mdlAttrs sudah ada di layar Import; collar + Import Block Model (.mdl) -> Mulai -> BX.m terbaca,
     jumlah blok sama, tanpa dialog "gagal dibaca"
Pemakaian: python tools/uji/uji_mdl_layar_import_dh.py"""
import base64, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"; TMP = Path(tempfile.mkdtemp())
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes())
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
gagal = []
def cek(ok, pesan):
    print(("  ok   " if ok else "  GAGAL ") + pesan)
    if not ok: gagal.append(pesan)
def halaman(pw):
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1400, "height": 850})
    ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
    pg = ctx.new_page(); DLG = []; ERR = []
    pg.on("dialog", lambda x: (DLG.append(x.message[:200]), x.accept())); pg.on("pageerror", lambda e: ERR.append(str(e)[:200]))
    pg.goto(P); pg.wait_for_timeout(1500)
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(400)
    return ctx, pg, DLG, ERR
inp = lambda pg, k: pg.locator('input[onchange*="%s"]' % k).first
with sync_playwright() as pw:
    ctx, pg, DLG, ERR = halaman(pw)
    inp(pg, "slotFile('collar'").set_input_files(str(DATA / "SIM_collar.csv")); pg.wait_for_timeout(1200)
    pg.evaluate("document.getElementById('dsName').value='A';try{SA.preview()}catch(e){};SA.go()")
    pg.wait_for_function("document.getElementById('imp').classList.contains('off') && window.collars && collars.length>0", timeout=300000); pg.wait_for_timeout(2500)
    pg.evaluate("(function(){var x=0,y=0;collars.forEach(function(c){x+=c[1];y+=c[2];});x/=collars.length;y/=collars.length;uiTab('BM');AOI.dlg();Object.assign(AOI.cfg,{x0:x-15,x1:x+15,y0:y-15,y1:y+15,zb:200,zt:230,bx:3,by:3,bz:1.5,snap:false,topo:0,pit:0,poly:'',mode:'penuh',name:'uji'});AOI.body();AOI.go();})()")
    pg.wait_for_function("!AOI.busy && window.BX && BX.m", timeout=300000); pg.wait_for_timeout(800)
    a = pg.evaluate("""(async function(){var m=BX.m,S=NY.mdlSynth(m);if(S.err)return {err:S.err};var R=bxMdlBytes(S.mm,'uji.mdl'),b=await new Blob(R.parts).arrayBuffer(),u=new Uint8Array(b),s='';for(var i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return {n:m.n,b64:btoa(s)};})()""")
    ctx.close()
    cek("err" not in a and a["n"] > 0, "1 kerangka AOI %s blok diekspor ke .mdl" % a.get("n"))
    (TMP / "uji_layar.mdl").write_bytes(base64.b64decode(a["b64"]))
    ctx, pg, DLG, ERR = halaman(pw)
    t = pg.evaluate("typeof mdlAttrs")
    cek(t == "function", "2 mdlAttrs tersedia di layar Import (%s)" % t)
    inp(pg, "slotFile('collar'").set_input_files(str(DATA / "SIM_collar.csv")); pg.wait_for_timeout(1200)
    inp(pg, "SA.bmPick").set_input_files(str(TMP / "uji_layar.mdl")); pg.wait_for_timeout(1500)
    pg.evaluate("document.getElementById('dsName').value='B';try{SA.preview()}catch(e){};SA.go()")
    pg.wait_for_function("document.getElementById('imp').classList.contains('off') && window.collars && collars.length>0", timeout=300000); pg.wait_for_timeout(3000)
    b = pg.evaluate("({n:window.BX&&BX.m?BX.m.n:0})")
    cek(b["n"] == a["n"] and not any("gagal dibaca" in x for x in DLG), "2 .mdl dari layar Import terbaca: %d blok (diharapkan %d); dialog: %s" % (b["n"], a["n"], DLG[:2]))
    cek(not ERR, "tanpa galat halaman: %s" % ERR[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
