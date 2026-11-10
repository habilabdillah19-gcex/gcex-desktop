# -*- coding: utf-8 -*-
"""GC-Ex Drill Hole 0.24.60 — popup Slicer (permintaan pemilik 10-11-2026):
  - 'Sayatan Garis Bebas' (dulu 'Garis di peta…') membuka popup Sayatan garis bebas (S3)
  - 'Tampilan 2D' / 'Tampilan 3D' hanya berpindah cara melihat; tidak membuka alat lain, tidak bolak-balik
  - tidak ada 'Pengaturan lanjutan (panel Sayatan)'; panel Properti tidak berpindah ke Sayatan
  - centang Label hole / Collar / Trajectory / No-data tidak lagi tampil di panel Tampilan & performa (tetap berfungsi dari Layer)
Pemakaian: python tools/uji/uji_slicer_tombol_dh.py"""
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
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept()); err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    pg.evaluate("PT.select('db')"); pg.wait_for_timeout(500)
    tab0 = pg.evaluate("(document.querySelector('section[id^=p]:not([hidden])')||{}).id")
    pg.click('#btnSecM'); pg.wait_for_timeout(500)
    t = pg.evaluate("(function(){var m=document.getElementById('secMenu');return {txt:m.innerText,b2:document.getElementById('btn2d').innerText.trim(),b3:document.getElementById('btnSec3').innerText.trim(),v:VIEW2D};})()"); print(t["b2"], "|", t["b3"])
    cek("Sayatan Garis Bebas" in t["txt"] and "Garis di peta" not in t["txt"], "tombol bernama 'Sayatan Garis Bebas'")
    cek(t["b2"] == "Tampilan 2D" and t["b3"] == "Tampilan 3D" and "Sayatan 2D" not in t["txt"] and "Sayatan 3D" not in t["txt"], "tombol 'Tampilan 2D' dan 'Tampilan 3D'")
    cek("Pengaturan lanjutan" not in t["txt"], "tidak ada 'Pengaturan lanjutan (panel Sayatan)'")
    pg.click("#secMenu button[data-pre=line]"); pg.wait_for_timeout(700)
    s = pg.evaluate("(function(){var b=document.getElementById('s3Box');return {mode:S3.mode,box:!!b&&getComputedStyle(b).display!=='none',txt:b?b.innerText.slice(0,40):'',menu:getComputedStyle(document.getElementById('secMenu')).display};})()"); print(s)
    cek(s["mode"] == "free" and s["box"] and "Sayatan garis bebas" in s["txt"] and s["menu"] == "none", "'Sayatan Garis Bebas' membuka popup Sayatan garis bebas dan menutup popup Slicer")
    pg.evaluate("s3Off()"); pg.wait_for_timeout(300)
    def klik(sel):
        pg.click('#btnSecM'); pg.wait_for_timeout(400); pg.click(sel); pg.wait_for_timeout(2500)
        return pg.evaluate("({v:!!VIEW2D,s3:S3.mode||''})")
    a = klik('#btn2d'); b = klik('#btn2d'); c = klik('#btnSec3'); e = klik('#btnSec3'); print(a, b, c, e)
    cek(a == {"v": True, "s3": ""} and b == {"v": True, "s3": ""}, "'Tampilan 2D' masuk 2D; diklik lagi tetap 2D (tidak bolak-balik)")
    cek(c == {"v": False, "s3": ""} and e == {"v": False, "s3": ""}, "'Tampilan 3D' kembali ke 3D tanpa membuka alat garis bebas")
    # memakai kendali Slicer (preset, dip, posisi, maju) dari node lain tidak boleh memindahkan panel Properti ke Sayatan
    pg.evaluate("PT.select('sp.pit')"); pg.wait_for_timeout(500); pg.click('#btnSecM'); pg.wait_for_timeout(400)
    pg.click("#secMenu button[data-pre=ew]"); pg.wait_for_timeout(1200); pg.click("#secMenu button[data-d='1']"); pg.wait_for_timeout(1200); pg.click("#secMenu button[data-pre=plan]"); pg.wait_for_timeout(1200)
    pg.evaluate("SLICER.set(60,45)"); pg.wait_for_timeout(1200); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    tabS = pg.evaluate("[].slice.call(document.querySelectorAll('#side section')).filter(function(s){return !s.hidden&&s.offsetParent;}).map(function(s){return s.id;}).join(',')"); print("panel sesudah Slicer:", tabS)
    cek("pSlice" not in tabS and "pSP" in tabS, "memakai Slicer dari node Desain pit: Properti tetap Data Spasial, bukan Sayatan (%s)" % tabS)
    pg.evaluate("PT.select('db')"); pg.wait_for_timeout(500)
    tab1 = pg.evaluate("(document.querySelector('section[id^=p]:not([hidden])')||{}).id")
    cek(tab0 == tab1 and tab1 != "pSlice", "panel Properti tidak berpindah ke Sayatan (%s)" % tab1)
    h = pg.evaluate("(function(){var e=document.getElementById('showLabel'),vis=function(x){return !!(x&&x.offsetParent);};uiTab('Set');var a=vis(e);e.checked=false;updatePlot();return {tampil:a,ada:!!e};})()")
    cek(h["ada"] and not h["tampil"], "centang Label hole / Collar / Trajectory / No-data tidak tampil di panel Tampilan & performa (tetap ada untuk Layer)")
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
