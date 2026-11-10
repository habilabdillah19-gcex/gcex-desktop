# -*- coding: utf-8 -*-
"""Judul Properti harus selalu menunjuk panel yang BENAR-BENAR tampil.

Kasusnya: pengguna memilih node 'Sayatan', lalu menjalankan sesuatu yang memindahkan tab sendiri
(lyApply pindah ke tab Block Model). Panelnya berganti jadi Dig block, tetapi judulnya tertinggal
di 'Sayatan' -- terbaca sebagai panel milik judul yang keliru."""
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
JS=r"""(function(){var ph=document.getElementById('ptPH');
  var seg={},bd=document.getElementById('dbBody');
  if(bd)[].forEach.call(bd.querySelectorAll('[data-seg]'),function(c){
    var vis=!!c.offsetParent&&getComputedStyle(c).display!=='none'&&c.offsetHeight>8;
    var k=c.getAttribute('data-seg'); if(vis)seg[k]=1;});
  return{judul:ph?ph.textContent.replace('Properti','').trim().slice(0,30):null,
         sel:PT.sel,foc:(window.FOC||''),seg:Object.keys(seg).sort()};})"""
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(),args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(3000)
    pg.evaluate("PT.select('set.o')"); pg.wait_for_timeout(1200)
    a=pg.evaluate(JS); print("  pilih node Overlay      ->",a)
    # jalankan sesuatu yang memindahkan tab sendiri
    pg.evaluate("""(function(){var m=BX.m,zc={},i;for(i=0;i<m.n;i++){var k=Math.round(m.z[i]*100);zc[k]=(zc[k]||0)+1;}
      var zb=null,nb=-1;Object.keys(zc).forEach(function(k){if(zc[k]>nb){nb=zc[k];zb=+k/100;}});
      lySet('fh',1.5);lySet('top',+(zb+0.75).toFixed(3));lyApply();})()""")
    pg.wait_for_timeout(4000)
    b=pg.evaluate(JS); print("  sesudah lyApply         ->",b)
    bad=[x for x in ("auto","man") if x in b["seg"]]
    ok = not (len(bad)>1 or (b["judul"] and "ayatan" in b["judul"] and b["seg"]))
    print("\n%s"%("BENAR: judul cocok dengan isi panel, satu fungsi saja." if ok else
          "GAGAL: judul '%s' tetapi segmen tampak %s"%(b["judul"],b["seg"])))
    ctx.close()
    raise SystemExit(0 if ok else 1)
