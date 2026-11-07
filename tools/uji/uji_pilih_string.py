# -*- coding: utf-8 -*-
"""Klik pada garis string milik elevasi LAIN tidak boleh terpilih.

Caranya: untuk tiap string yang BUKAN milik flitch aktif, hitung titik tepat di atas garisnya,
panggil dbPick() di titik itu, lalu periksa apakah yang terpilih masih string elevasi lain."""
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
JS=r"""(function(){
  var B=lyBench(),e=1e-6,A=dgAx();if(!A)return{err:'tidak ada sumbu 2D'};
  var pada=function(s){if(s.db)return Math.abs(s.db.top-B[0])<e&&Math.abs(s.db.bot-B[1])<e;
    if(s.pl&&s.pl.m&&s.pl.m!=='H')return false;
    var z=s.pts&&s.pts[0]&&s.pts[0][2];if(!isFinite(z))return true;
    return z>=B[1]-e&&z<=B[0]+e;};
  var luar=0,salah=0,contoh=[];
  DG.S.forEach(function(s,i){
    if(!s.vis||!s.closed||s.inner||pada(s))return;
    luar++;
    for(var k=0;k<s.pts.length;k++){
      var a=s.pts[k],b=s.pts[(k+1)%s.pts.length];
      var p=dgPx(A,(a[0]+b[0])/2+offX,(a[1]+b[1])/2+offY);
      var ev={clientX:A.r.left+p[0],clientY:A.r.top+p[1]};
      var j=dbPick(ev);
      if(j>=0&&!pada(DG.S[j])){salah++;if(contoh.length<3)contoh.push('String '+DG.S[j].no+' ('+(DG.S[j].d||'')+')');break;}
    }});
  return{flitch:[B[0],B[1]],stringLuarFlitch:luar,terpilihSalah:salah,contoh:contoh};})()"""
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(),args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(3000)
    # masuk mode flitch + Sayatan 2D, persis seperti di layar pemilik
    pg.evaluate("""(function(){var m=BX.m,zc={},i;for(i=0;i<m.n;i++){var k=Math.round(m.z[i]*100);zc[k]=(zc[k]||0)+1;}
      var zb=null,nb=-1;Object.keys(zc).forEach(function(k){if(zc[k]>nb){nb=zc[k];zb=+k/100;}});
      lySet('fh',1.5);lySet('top',+(zb+0.75).toFixed(3));lyApply();})()""")
    pg.wait_for_timeout(3000)
    if not pg.evaluate("!!window.VIEW2D"): pg.evaluate("toggle2D()")
    pg.wait_for_timeout(3000)
    print("  VIEW2D=%s mode=%s"%(pg.evaluate("!!window.VIEW2D"),pg.evaluate("secGeom().m")))
    # Data latihan tidak memuat string di elevasi lain, jadi keadaannya dibuat: dua ore line
    # yang bertumpang-tindih di bidang datar, satu pada flitch aktif dan satu 1,5 m di bawahnya --
    # persis yang terlihat pemilik (garis hijau aktif + garis coklat muda elevasi lain).
    pg.evaluate("""(function(){var B=lyBench(),m=BX.m,cx=0,cy=0,i,n=Math.min(m.n,4000);
      for(i=0;i<n;i++){cx+=m.x[i];cy+=m.y[i];}cx/=n;cy/=n;
      var buat=function(z,no,col,d,dx,dy){var P=[[cx-40+dx,cy-40+dy,z],[cx+40+dx,cy-40+dy,z],[cx+40+dx,cy+40+dy,z],[cx-40+dx,cy+40+dy,z]];
        DG.S.push({pts:P,closed:true,vis:true,no:no,col:col,d:d,pl:{m:'H'}});};
      /* dipisah jauh supaya tidak ada tepi yang berimpit: klik pada tepi yang satu tidak
         boleh kebetulan berjarak nol dari tepi yang lain. */
      buat((B[0]+B[1])/2,14,'#7ee04a','LG aktif',0,0);
      buat(B[1]-0.75,17,'#c8a165','LG elevasi lain',150,150);
      dgSave&&dgSave();updatePlot();})()""")
    pg.wait_for_timeout(2500)
    r=pg.evaluate(JS); print(" ",r)
    ok = isinstance(r,dict) and r.get("stringLuarFlitch",0)>0 and r.get("terpilihSalah",1)==0
    if r.get("stringLuarFlitch",0)==0: print("\nTIDAK TERUJI: tidak ada string di luar flitch aktif.")
    else: print("\n%s"%("BENAR: klik tidak pernah mendarat di string elevasi lain."
        if ok else "GAGAL: %d string elevasi lain ikut terpilih -> %s"%(r["terpilihSalah"],r["contoh"])))
    ctx.close(); raise SystemExit(0 if ok else 1)
