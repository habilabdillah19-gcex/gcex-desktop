# -*- coding: utf-8 -*-
"""Panel As-Mined harus menyebut dengan jelas MANA import lantai dan MANA import atap.
Diukur dari teks panel yang benar-benar tergambar, bukan dari kode sumber."""
import os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path("/home/claude/gcex-desktop"); PORT=str(random.randint(9100,9899))
SRC=sys.argv[1] if len(sys.argv)>1 else str(ROOT/"app"/"index.html")
d=Path(tempfile.mkdtemp()); shutil.copyfile(SRC,d/"index.html")
os.symlink(ROOT/"docs"/"tutorial-gcex"/"data",d/"data-latihan")
subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen("http://localhost:%s/index.html"%PORT,timeout=1); break
    except Exception: time.sleep(0.4)
print("sumber:",SRC)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(),args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(3000)
    pg.evaluate("(function(){try{rbAM&&rbAM();}catch(e){}try{amPanel();}catch(e){}})()")
    pg.wait_for_timeout(2500)
    t=pg.evaluate("""(function(){var e=document.getElementById('pAM')||document.querySelector('#side');
      return e?e.textContent.replace(/\\s+/g,' '):'';})()""")
    tombol=pg.evaluate("""(function(){var out=[];
      [].forEach.call(document.querySelectorAll('label.mdbtn, #amRoofBox label'),function(b){
        var s=(b.textContent||'').replace(/\\s+/g,' ').trim();if(s)out.push(s.slice(0,90));});return out;})()""")
    print("  label import:"); [print("    -",x) for x in tombol]
    adaLantai = "pick-up lantai" in t.lower() or "pick-up LANTAI" in t
    adaAtap   = "pick-up atap" in t.lower()
    print("\n  menyebut import LANTAI:",adaLantai,"| menyebut import ATAP:",adaAtap)
    ok = adaLantai and adaAtap
    print("%s"%("BENAR: kedua import dinamai jelas." if ok else
          "GAGAL: import lantai/atap tidak dinamai jelas di panel."))
    ctx.close(); raise SystemExit(0 if ok else 1)
