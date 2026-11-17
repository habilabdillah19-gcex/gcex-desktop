# -*- coding: utf-8 -*-
"""BM 0.24.103 / DH 0.24.106: kotak melayang bisa ditutup, teks penjelas diringkas (tutup.js).
  K1 bilah Sayatan muncul saat potong slab, punya tombol x; ditutup -> hilang; tombol Slicer dibuka -> muncul lagi.
  K2 Ringkasan ditutup -> hilang, tombol "Panel tersembunyi (1)" muncul; tetap tertutup sesudah muat ulang; tombol itu -> tampil lagi.
  K3 teks penjelas statis (.hint tanpa id) tersembunyi secara bawaan; tombol (i) menampilkannya; pesan status ber-id tetap tampil.
  K4 BM: tombol (i) & x pada Ringkasan ada, tanpa galat.
Pemakaian: python tools/uji/uji_kerapian.py"""
import random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
def server(app):
    d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / app / "index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
    P = random.randint(9400, 9799); s = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); return s, P
VIS = "(s)=>{var e=document.querySelector(s);return !!(e&&e.offsetWidth&&getComputedStyle(e).display!=='none');}"
HINTS = "(function(){var n=0,a=0;document.querySelectorAll('.hint').forEach(function(e){if(!e.id&&e.offsetWidth)n++;if(e.id&&e.offsetWidth)a++;});return [n,a];})()"
def muat(pg, P, tunggu):
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function(tunggu, timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(4000)
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1600, "height": 950})
    srv, P = server("app-dh"); pg = ctx.new_page(); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    muat(pg, P, "window.collars && collars.length > 0")
    pg.evaluate("$('sliceClip').checked=true;$('sliceClip').dispatchEvent(new Event('change',{bubbles:true}));updatePlot()"); pg.wait_for_timeout(1500)
    k1a = pg.evaluate(VIS, "#slabBar") and pg.evaluate("!!document.querySelector('#slabBar > .gxX')")
    pg.click("#slabBar > .gxX"); pg.wait_for_timeout(400); k1b = pg.evaluate(VIS, "#slabBar")
    pg.click("#btnSecM"); pg.wait_for_timeout(600); k1c = pg.evaluate(VIS, "#slabBar"); pg.keyboard.press("Escape"); pg.mouse.click(900, 500); pg.wait_for_timeout(300)
    cek(k1a and not k1b and k1c, "K1 bilah Sayatan: tampil+x %s, ditutup %s, Slicer dibuka -> tampil %s" % (k1a, not k1b, k1c))
    pg.click("#statsCard > .gxX"); pg.wait_for_timeout(400)
    k2a = not pg.evaluate(VIS, "#statsCard"); t = pg.evaluate("(function(){var b=document.getElementById('tutupBtn');return b&&b.offsetWidth?b.textContent:null;})()")
    muat(pg, P, "window.collars && collars.length > 0"); k2b = not pg.evaluate(VIS, "#statsCard")
    pg.click("#tutupBtn"); pg.wait_for_timeout(400); k2c = pg.evaluate(VIS, "#statsCard") and not pg.evaluate(VIS, "#tutupBtn")
    cek(k2a and t == "Panel tersembunyi (1)" and k2b and k2c, "K2 Ringkasan: ditutup %s, tombol %r, tetap tertutup sesudah muat ulang %s, dibuka lagi %s" % (k2a, t, k2b, k2c))
    pg.evaluate("(function(){var el=document.querySelector('#ptree .ptr[data-id=\"ov\"] .ptl')||document.querySelector('#ptree .ptr[data-id=\"set\"] .ptl');if(el)el.click();})()"); pg.wait_for_timeout(800)
    h0 = pg.evaluate(HINTS); pg.click("#hintBtn"); pg.wait_for_timeout(400); h1 = pg.evaluate(HINTS); pg.click("#hintBtn"); pg.wait_for_timeout(300)
    cek(h0[0] == 0 and h1[0] > 0 and h0[1] == h1[1] and h0[1] >= 1, "K3 penjelas: bawaan %d tampil, tombol (i) -> %d; pesan status ber-id tetap %d" % (h0[0], h1[0], h0[1]))
    cek(not E, "DH tanpa galat halaman %s" % E[:2]); srv.terminate()
    srv, P = server("app"); pg = ctx.new_page(); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    muat(pg, P, "window.BX && BX.m")
    k4 = pg.evaluate("[!!document.getElementById('hintBtn'),!!document.querySelector('#statsCard > .gxX')]")
    cek(all(k4), "K4 BM: tombol (i) %s, x Ringkasan %s" % tuple(k4))
    cek(not E, "BM tanpa galat halaman %s" % E[:2]); srv.terminate(); ctx.close()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
