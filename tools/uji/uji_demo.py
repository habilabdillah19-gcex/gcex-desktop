# -*- coding: utf-8 -*-
"""Jalankan demo SUNGGUHAN (tidak di-pause) dan catat, per langkah, apakah elemen yang ditunjuk
pernah terlihat. Versi sebelumnya menjalankan demo dalam keadaan pause -- padahal yang membuka
panel adalah aksi terjadwal milik tiap langkah, yang hanya berjalan kalau demo benar-benar jalan."""
import os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path("/home/claude/gcex-desktop"); PORT = str(random.randint(9100, 9899))   # port acak: port tetap bisa tersangkut peladen lama
SRC=sys.argv[2] if len(sys.argv)>2 else str(ROOT/"app"/"index.html")
d=Path(tempfile.mkdtemp(prefix="gcex_dm2_")); shutil.copyfile(SRC,d/"index.html")
os.symlink(ROOT/"docs"/"tutorial-gcex"/"data",d/"data-latihan")
subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen("http://localhost:%s/index.html"%PORT,timeout=1); break
    except Exception: time.sleep(0.4)
print("sumber:",SRC)

JS_HOOK=r"""
(function(){
  window.__D={rec:{},n:0,sel:0};
  var vis=function(e){ if(!e) return false; var r=e.getBoundingClientRect(), c=getComputedStyle(e);
    return !!(e.offsetParent||e.tagName==='BODY') && c.display!=='none' && c.visibility!=='hidden' && r.width>0 && r.height>0; };
  setInterval(function(){
    if(!DM.on) return;
    var i=DM.i, st=DM.steps&&DM.steps[i]; if(!st) return;
    var o=__D.rec[i]||(__D.rec[i]={s:st.s,t:st.t,ada:!!st.el,tampak:false,ketemu:false,n:0});
    o.n++;
    if(st.el){ var e=null; try{e=dmEl(st.el);}catch(x){}
      if(e){o.ketemu=true; if(vis(e))o.tampak=true;} }
  },250);
  return true;})
"""
JS_DUMP=r"(function(){return{sel:Object.keys(__D.rec).length,rec:__D.rec,on:DM.on};})"
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(prefix="gcex_dm2c_"),
        args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1600,"height":1000})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    er=[]; pg.on("pageerror",lambda e:er.append(str(e)[:140]))
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1200)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=60000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(3000)
    pg.evaluate(JS_HOOK)
    pg.evaluate("dmStart()")
    # tunggu sampai demo selesai (DM.on jadi false) atau batas waktu
    for _ in range(600):
        if not pg.evaluate("!!DM.on"): break
        pg.wait_for_timeout(1000)
    R=pg.evaluate(JS_DUMP)
    rec=R["rec"]; bad=[]
    print("%d langkah terekam\n"%len(rec))
    for k in sorted(rec,key=lambda x:int(x)):
        o=rec[k]
        tag="-" if not o["ada"] else ("OK" if o["tampak"] else ("TIDAK TAMPAK" if o["ketemu"] else "TIDAK ADA"))
        if o["ada"] and not o["tampak"]: bad.append(o)
        print("%2s %-17s %-44s %s"%(k,o["s"][:17],o["t"][:44],tag))
    print("\n%d langkah menunjuk elemen yang tidak terlihat:"%len(bad))
    for o in bad: print("  - [%s] %s (ketemu=%s)"%(o["s"],o["t"],o["ketemu"]))
    if er: print("\ngalat:",er[:5])
    ctx.close()

raise SystemExit(1 if bad else 0)
