# -*- coding: utf-8 -*-
"""GC-Ex Drill Hole: sesudah 'Hapus seluruh database bor', topografi & desain pit harus TETAP tampil di 3D.
Sebelum 0.24.59 jangkar area jatuh ke (0,0) dan area kerja ke kotak 0-100 m, sehingga overlay yang dipotong ke
area kerja kosong (sumbu 'Easting (+0)'). Pemakaian: python tools/uji/uji_hapus_bor_overlay.py"""
import os, random, subprocess, sys, tempfile, time, urllib.request
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
def cek(ok, pesan):
    print(("  ok   " if ok else "  GAGAL ") + pesan)
    if not ok: gagal.append(pesan)
JS = "(function(){var T=document.getElementById('plotDiv').data||[],f=function(u){return T.filter(function(t){return t.uid===u&&t.x&&t.x.length>100;}).length;};return {topo:f('ovTopoS'),pit:f('ovPitS'),col:collars.length,off:[offX,offY],gx:[G.x0,G.x1],nt:(window.topoData||[]).length};})()"
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept()); err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    pg.evaluate("document.getElementById('ovTopoS').checked=true;document.getElementById('ovPit').checked=true;updatePlot()"); pg.wait_for_timeout(2500)
    a = pg.evaluate(JS); print("sebelum", a)
    cek(a["col"] > 0 and a["topo"] == 1 and a["pit"] == 1, "sebelum dihapus: bor ada, permukaan topo & pit tampil")
    pg.evaluate("PTD.drop('all')"); pg.wait_for_timeout(9000); pg.wait_for_function("window.SA && SA.D && document.getElementById('plotDiv') && document.getElementById('plotDiv').data", timeout=60000); pg.wait_for_timeout(4000)
    pg.evaluate("document.getElementById('ovTopoS').checked=true;document.getElementById('ovPit').checked=true;updatePlot()"); pg.wait_for_timeout(2500)
    b = pg.evaluate(JS); print("sesudah", b)
    cek(b["col"] == 0 and b["nt"] == a["nt"], "database bor kosong, data spasial utuh")
    cek(b["off"][0] > 1000 and b["gx"][1] - b["gx"][0] > 200, "jangkar & area kerja dihitung dari topografi + pit (offX %s, lebar %.0f m), bukan (0,0) / 100 m" % (b["off"][0], b["gx"][1] - b["gx"][0]))
    cek(b["topo"] == 1 and b["pit"] == 1, "sesudah dihapus: permukaan topografi & desain pit TETAP tampil di 3D")
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
