# -*- coding: utf-8 -*-
"""Dialog yang dibuat modul harus benar-benar TERLIHAT di layar, bukan sekadar ada di DOM.
Diukur dari posisi kotaknya terhadap jendela: inilah yang luput pada pemeriksaan sebelumnya."""
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
VIS="""(function(id){var d=document.getElementById(id);if(!d)return 'tidak ada';
  var cs=getComputedStyle(d);if(cs.display==='none')return 'display:none';
  var r=d.getBoundingClientRect();
  if(r.width<50||r.height<50)return 'kotak kosong';
  if(r.bottom<=0||r.top>=innerHeight)return 'DI LUAR LAYAR (top='+Math.round(r.top)+')';
  return 'TERLIHAT';})"""
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(),args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(3000)
    bad=[]
    for nama,jalan,idd in [("Pemeriksaan dig block","GCO.qcRun(false)","qcDlg"),
                           ("Rekap harian","GCO.dayDlg&&GCO.dayDlg()","dayDlg"),
                           ("Periode","PRD.dlg()","prdDlg")]:
        try: pg.evaluate("(function(){try{%s}catch(e){}})()"%jalan)
        except Exception as e: print("  %-22s galat: %s"%(nama,e)); bad.append(nama); continue
        pg.wait_for_timeout(900)
        v=pg.evaluate(VIS,idd); print("  %-22s -> %s"%(nama,v))
        if v!="TERLIHAT": bad.append(nama)
        pg.evaluate("(function(){var d=document.getElementById('%s');if(d)d.style.display='none';})()"%idd)
    print("\n%s"%("BENAR: semua dialog muncul di layar." if not bad else "GAGAL: tidak terlihat -> "+", ".join(bad)))
    ctx.close(); raise SystemExit(0 if not bad else 1)
