# -*- coding: utf-8 -*-
"""GLSKIP (lewati update() lapisan 3D yang tidak berubah) tidak boleh mengubah GAMBAR. Untuk tiap aplikasi: data latihan,
lalu serangkaian aksi (ganti atribut warna, centang overlay, klik node flitch / sayatan, ganti atribut lagi). Sesudah tiap
aksi: PNG adegan 3D dengan GLSKIP aktif vs PNG sesudah GLSKIP dimatikan + Plotly.react penuh. Keduanya harus identik
(hash sama). Juga melaporkan jumlah lapisan yang dilewati vs di-update.
Pemakaian: python tools/uji/uji_glskip_gambar.py app/index.html | app-dh/index.html"""
import hashlib, json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"; APP = sys.argv[1]
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / APP).read_bytes()); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
AKSI_BM = [("tree", "bm.a.CU_PPM"), ("cb", "ovTopoS"), ("tree", "fl"), ("tree", "bm.a.AU_GC"), ("cb", "ovPit"), ("tree", "dig.auto")]
AKSI_DH = [("tree", "db.el.Ag"), ("cb", "ovTopoS"), ("tree", "db.geo.0"), ("tree", "sp.topo"), ("tree", "db.el.Au"), ("cb", "showCollar")]
AKSI = AKSI_DH if "dh" in APP else AKSI_BM
IMG = r"""(async function(){var gd=document.getElementById('plotDiv');var u=await Plotly.toImage(gd,{format:'png',width:900,height:600});return u;})()"""
hasil = []
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    assert pg.evaluate("!!window.GLSKIP"), "GLSKIP tidak terpasang"
    pg.evaluate("for(var k=0;k<3;k++){PT.render(true);PT.flatAll(PT.nodes).forEach(function(n){if(n.kids&&n.kids.length)PT.open[n.id]=1;});}PT.render(true)")
    for jenis, target in AKSI:
        pg.evaluate("GLSKIP.on=true;GLSKIP.skip=0;GLSKIP.run=0")
        if jenis == "tree": pg.evaluate("document.querySelector('#ptree .ptr[data-id=\"%s\"] .ptl').click()" % target)
        else: pg.evaluate("(function(id){var c=document.getElementById(id);c.checked=!c.checked;c.dispatchEvent(new Event('change',{bubbles:true}));})('%s')" % target)
        pg.wait_for_timeout(2500)
        sk = pg.evaluate("[GLSKIP.skip,GLSKIP.run]")
        a = hashlib.md5(pg.evaluate(IMG).encode()).hexdigest()
        pg.evaluate("GLSKIP.on=false"); pg.evaluate("(function(){var gd=document.getElementById('plotDiv');return Plotly.react(gd,gd.data,gd.layout);})()"); pg.wait_for_timeout(1500)
        b = hashlib.md5(pg.evaluate(IMG).encode()).hexdigest()
        hasil.append({"aksi": jenis + ":" + target, "skip": sk[0], "run": sk[1], "sama": a == b})
        pg.evaluate("GLSKIP.on=true")
    ctx.close()
srv.terminate()
for h in hasil: print(h)
beda = [h["aksi"] for h in hasil if not h["sama"]]
if beda: print("\nGAGAL: gambar berbeda sesudah", beda)
elif not any(h["skip"] for h in hasil): print("\nGAGAL: GLSKIP tidak pernah melewati lapisan (tidak berguna / tidak aktif)")
else: print("\nLULUS")
