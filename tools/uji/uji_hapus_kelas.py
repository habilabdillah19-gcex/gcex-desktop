# -*- coding: utf-8 -*-
"""BM 0.24.92: hapus / tambah kelas warna saat flitch aktif di 2D tidak lagi memunculkan
'Galat JavaScript: Cannot read properties of undefined (reading lo)' (bxLab < bxClassInfo < elStTbl < bxStatsFc).
  H1 flitch aktif + 5 kelas -> hapus 2 kelas teratas: tanpa galat, ringkasan & legenda 3 kelas.
  H2 tambah kelas lagi -> 4 kelas, tanpa galat.
Pemakaian: python tools/uji/uji_hapus_kelas.py"""
import random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9600, 9699); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1500, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m", timeout=600000); pg.wait_for_timeout(4000)
    pg.evaluate("document.getElementById('sMode').value='H';modeChanged();if(!VIEW2D)toggle2D();lyApply()"); pg.wait_for_timeout(3000)
    pg.evaluate("var a=BX.ui.attr;BX.ui.cls[a]=[{lo:null,hi:0.3,col:'#1f77b4'},{lo:0.3,hi:0.5,col:'#2ca02c'},{lo:0.5,hi:1,col:'#ffd400'},{lo:1,hi:2,col:'#ff9966'},{lo:2,hi:null,col:'#d62728'}];BX.sc={};bxPanel();updatePlot();")
    pg.wait_for_timeout(3000)
    n0 = pg.evaluate("[lyFcOn(), (LY.fst?Object.keys(LY.fst).length:0)]")
    pg.evaluate("bxClsDel(4)"); pg.wait_for_timeout(300); pg.evaluate("bxClsDel(3)"); pg.wait_for_timeout(3000)
    r1 = pg.evaluate("[bxCls(BX.ui.attr).length, Math.max.apply(null,Object.keys(LY.fst||{}).map(Number).concat([-1])), (document.querySelector('#bxStat')||{}).innerText||'']")
    cek(n0[0] and not E and r1[0] == 3 and r1[1] <= 2 and "dihapus" not in r1[2], "H1 flitch aktif (%s kelas di statistik) -> hapus 2 kelas: %s kelas, indeks maks %s, galat %s" % (n0[1], r1[0], r1[1], E[:1]))
    pg.evaluate("bxClsAdd()"); pg.wait_for_timeout(2500)
    cek(not E and pg.evaluate("bxCls(BX.ui.attr).length") == 4, "H2 tambah kelas -> 4 kelas, tanpa galat %s" % E[:1])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
