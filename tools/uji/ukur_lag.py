# -*- coding: utf-8 -*-
"""Ukur yang benar-benar dirasakan pengguna: berapa lama layar MEMBEKU saat slider digeser.
Caranya memantau jeda antar-frame (requestAnimationFrame): frame normal ~16 ms; setiap jeda di atas
50 ms adalah waktu ketika aplikasi tidak menanggapi apa pun."""
import os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path("/home/claude/gcex-desktop"); PORT=sys.argv[1] if len(sys.argv)>1 else "8871"
MODE=sys.argv[2] if len(sys.argv)>2 else "auto"     # auto | paksa-mati
d=Path(tempfile.mkdtemp(prefix="gcex_bk_")); shutil.copyfile(ROOT/"app"/"index.html",d/"index.html")
os.symlink(ROOT/"docs"/"tutorial-gcex"/"data",d/"data-latihan")
rnd=random.Random(3); rows=["X,Y,Z,DX,DY,DZ,AUOK,SG,DOMAIN"]
for _ in range(586775):
    sz=rnd.choice([(6,6,3),(6,6,3),(3,3,3),(1.5,1.5,.75)])
    rows.append("%.3f,%.3f,%.3f,%g,%g,%g,%.4f,%.3f,%s"%(558900+rnd.random()*160,9010150+rnd.random()*160,
        200+rnd.random()*60,sz[0],sz[1],sz[2],rnd.random()*2.5,2.2+rnd.random()*.6,rnd.choice(["ORE","WASTE","OX"])))
(d/"besar.csv").write_text("\n".join(rows),encoding="utf-8")
subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen("http://localhost:%s/index.html"%PORT,timeout=1); break
    except Exception: time.sleep(0.4)

JS_MON=r"""
(function(){window.__F={gap:[],last:performance.now(),on:true};
  (function loop(){if(!__F.on)return;var t=performance.now();__F.gap.push(t-__F.last);__F.last=t;
    requestAnimationFrame(loop);})();return true;})
"""
JS_STOP=r"""
(function(){__F.on=false;var g=__F.gap.filter(function(x){return x>50;});
  var tot=g.reduce(function(a,b){return a+b;},0);
  return{frame:__F.gap.length,beku_n:g.length,beku_ms:+tot.toFixed(0),
         terlama:+Math.max.apply(null,__F.gap.concat([0])).toFixed(0)};})
"""
JS_GESER=r"""
(function(){var s=document.getElementById('pos');if(!s)return 'tak ada slider';
  for(var i=0;i<8;i++){s.value=+s.value+1;s.dispatchEvent(new Event('input',{bubbles:true}));}
  s.dispatchEvent(new Event('change',{bubbles:true}));return 'ok';})
"""
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(prefix="gcex_bkc_"),
        args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1200)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=60000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("typeof window.bxDlg==='function'",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelector('button[onclick*=bxDlg]').click()")
    pg.wait_for_selector("#bxDlg input[type=file]",state="attached",timeout=30000)
    pg.set_input_files("#bxDlg input[type=file]",str(d/"besar.csv"))
    pg.wait_for_function("document.getElementById('bxGo') && !document.getElementById('bxGo').disabled",timeout=300000)
    pg.evaluate("document.getElementById('bxGo').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>500000",timeout=600000)
    pg.wait_for_timeout(5000)
    # buka panel Sayatan dulu: slidernya ada di panel itu, dan selama panel lain yang tampil
    # slider #pos tidak terlihat sehingga tidak bisa diseret (ini yang bikin pengukuran sebelumnya gagal)
    pg.evaluate("PT.select('set.s')")
    pg.wait_for_timeout(1200)
    # nyalakan pemotongan slab supaya geseran slider benar-benar menggambar ulang block model
    pg.evaluate("(function(){var c=document.getElementById('sliceClip');if(c&&!c.checked){c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));}})()")
    pg.wait_for_timeout(4000)
    if MODE=="paksa-mati":
        pg.evaluate("(function(){var e=document.getElementById('perfRel');e.checked=false;})()")
    rel=pg.evaluate("document.getElementById('perfRel').checked")
    print("%s | Update saat slider dilepas: %s"%(MODE, "NYALA" if rel else "MATI"))
    # GESERAN SUNGGUHAN: tekan tombol mouse di gagang slider lalu seret, bukan event buatan.
    # Event buatan ternyata tidak memicu jalur gambar-ulang yang sama, jadi tidak menirukan lag.
    box = pg.locator("#pos").bounding_box()
    pg.evaluate("(%s)()"%JS_MON)
    pg.mouse.move(box["x"]+box["width"]*0.5, box["y"]+box["height"]/2)
    pg.mouse.down()
    for k in range(1, 25):
        pg.mouse.move(box["x"]+box["width"]*(0.5+0.016*k), box["y"]+box["height"]/2)
        pg.wait_for_timeout(60)
    pg.mouse.up()
    pg.wait_for_timeout(6000)
    r=pg.evaluate("(%s)()"%JS_STOP)
    print("   seret slider sayatan 24 langkah -> layar membeku %d x, total %d ms, jeda terlama %d ms"
          %(r["beku_n"],r["beku_ms"],r["terlama"]))
    ctx.close()
