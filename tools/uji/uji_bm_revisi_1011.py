# -*- coding: utf-8 -*-
"""GC-Ex Block Model 0.24.56 — revisi pemilik 10-11-2026 (data latihan + pick-up SINTETIS bertata letak berkas pemilik):
  A. titik ATAP tampil di plan as-mined & jadi sasaran snap saat mendigit (dulu hanya titik lantai)
  B. klik As-Mined > Per flitch > RL ... tidak lagi kembali ke panel 'Buat Flitch Aktif'
  C. node baru 'Register untuk database' (bagian tersendiri; tidak lagi di dalam Layout)
  D. popup Slicer: 'Sayatan Garis Bebas', 'Tampilan 2D / 3D', tanpa 'Pengaturan lanjutan'; node 'Sayatan' di Pengaturan tampilan hilang
  E. laporan kinerja tidak menghitung waktu kotak dialog
Pemakaian: python tools/uji/uji_bm_revisi_1011.py"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
gagal = []
def cek(ok, pesan):
    print(("  ok   " if ok else "  GAGAL ") + pesan)
    if not ok: gagal.append(pesan)
TUNDA = {"s": 0}
def dlg(x):
    if TUNDA["s"]: time.sleep(TUNDA["s"])
    x.accept(x.default_value) if x.type == "prompt" else x.accept()
SEL = "(function(){var v=[].slice.call(document.querySelectorAll('section[id^=p]')).filter(function(s){return !s.hidden&&s.offsetParent;});return {sel:PT.sel,sec:v.map(function(s){return s.id;}).join(','),on:v.map(function(s){return (s.querySelector('.uitabs button.on')||{}).textContent||'';}).join(',')};})()"
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", dlg); err = []; pg.on("pageerror", lambda e: err.append(str(e)))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    # A: OB CSV (atap) + lantai di flitch 238,75-236,25
    a = pg.evaluate("""(async function(){var m=BX.m,cx=0,cy=0,n=Math.min(m.n,5000);for(var i=0;i<n;i++){cx+=m.x[i];cy+=m.y[i];}cx/=n;cy/=n;
      var R=[[0,0],[12,1],[13,9],[6,14],[-1,8]],s='',f='';R.forEach(function(q,i){s+=(i+1)+','+(cx+q[0]).toFixed(3)+','+(cy+q[1]).toFixed(3)+','+(237.9+0.6*(i%3)).toFixed(3)+',204\\n';});
      for(var k=0;k<20;k++)f+=(k+1)+','+(cx+Math.random()*12).toFixed(3)+','+(cy+Math.random()*12).toFixed(3)+',236.3,204\\n';
      lySet('fh',2.5);lyU().bot='';lySet('top',238.75);lyApply();await new Promise(function(r){setTimeout(r,1500);});
      amBndFile([new File([s],'ACT_SO261106OB_238-75_236-25_ZX.csv')]);amPtsFile([new File([f],'PROG261107ORE_ZX.csv')],'pts');await new Promise(function(r){setTimeout(r,1500);});
      if(!VIEW2D)toggle2D();updatePlot();await new Promise(function(r){setTimeout(r,2000);});window._c=[cx,cy];
      var T=document.getElementById('plotDiv').data||[],at=T.filter(function(t){return /^Pick-up ATAP/.test(t.name||'');}),lt=T.filter(function(t){return /^Pick-up (di|sekitar)/.test(t.name||'');});
      return {atap:at.length?at[0].x.length:0,lantai:lt.reduce(function(a,t){return a+t.x.length;},0),roofN:AMN.roofNear().length};})()"""); print("A", a)
    cek(a["atap"] == 5 and a["lantai"] >= 20, "A plan as-mined: 5 titik ATAP tampil bersama titik lantai (atap %s, lantai %s)" % (a["atap"], a["lantai"]))
    sn = pg.evaluate("""(function(){AM.digOn=true;var A=dgAx(),q=AMN.roofNear()[1],p=dgPx(A,q.x,q.y),r=dgSnapHook(A,p[0]+4,p[1]-3);AM.digOn=false;return {r:r,q:[q.x,q.y]};})()"""); print("snap", sn)
    cek(sn["r"] and abs(sn["r"][0] - sn["q"][0]) < 1e-6 and abs(sn["r"][1] - sn["q"][1]) < 1e-6, "A saat mendigit, kursor dekat titik atap menempel ke titik atap")
    # A2: tombol tampil/sembunyikan lapisan titik (pemilik 10-11-2026)
    v = pg.evaluate("""(async function(){uiTab('AM');amPanel();await new Promise(function(r){setTimeout(r,300);});
      var bs=[].slice.call(document.querySelectorAll('#amBody .amvis button')),n=function(re){return (document.getElementById('plotDiv').data||[]).filter(function(t){return re.test(t.name||'');}).length;};
      var o={tombol:bs.length};bs[0].click();await new Promise(function(r){setTimeout(r,1500);});o.lantaiMati=n(/^Pick-up (di|sekitar)/);o.atapTetap=n(/^Pick-up ATAP/);
      AM.digOn=true;var A=dgAx(),f=amPtsNear()[0],p=dgPx(A,f.x,f.y),r=dgSnapHook(A,p[0]+1,p[1]+1);o.snapLantai=!!(r&&Math.abs(r[0]-f.x)<1e-6&&Math.abs(r[1]-f.y)<1e-6);
      var q=AMN.roofNear()[1],pq=dgPx(A,q.x,q.y),rq=dgSnapHook(A,pq[0]+4,pq[1]-3);o.snapAtap=!!(rq&&Math.abs(rq[0]-q.x)<1e-6);AM.digOn=false;
      document.querySelectorAll('#amBody .amvis button')[1].click();await new Promise(function(r){setTimeout(r,1500);});o.atapMati=n(/^Pick-up ATAP/);
      document.querySelectorAll('#amBody .amvis button')[0].click();document.querySelectorAll('#amBody .amvis button')[1].click();await new Promise(function(r){setTimeout(r,1500);});o.kembali=n(/^Pick-up ATAP/)+n(/^Pick-up (di|sekitar)/);return o;})()"""); print("A2", v)
    cek(v["tombol"] == 2 and v["lantaiMati"] == 0 and v["atapTetap"] == 1 and not v["snapLantai"] and v["snapAtap"] and v["atapMati"] == 0 and v["kembali"] >= 2,
        "A2 tombol Titik lantai / Titik atap menyembunyikan lapisannya di jendela & titik tersembunyi tidak ditempeli snap")
    # B: Per flitch
    pg.evaluate("amRun(true)"); pg.wait_for_timeout(2500); pg.evaluate("PT.render(true)"); pg.wait_for_timeout(500)
    kid = pg.evaluate("(function(){var r=[].slice.call(document.querySelectorAll('#ptree .ptr')).map(function(e){return e.dataset.id;});return r.filter(function(i){return /^am\\.fl\\./.test(i);});})()")
    if not kid:
        pg.evaluate("PT.open['am']=1;PT.open['am.fl']=1;PT.render(true)"); pg.wait_for_timeout(500)
        kid = pg.evaluate("[].slice.call(document.querySelectorAll('#ptree .ptr')).map(function(e){return e.dataset.id;}).filter(function(i){return /^am\\.fl\\./.test(i);})")
    print("node am.fl:", kid[:6])
    pg.evaluate("lyFlOff()"); pg.wait_for_timeout(1500)
    fl = kid[0] if kid else ''
    tgt = [fl, fl + '.a'] if fl else []
    for t in tgt:
        pg.evaluate("PT.open['am']=1;PT.open['am.fl']=1;PT.open[%s]=1;PT.render(true)" % json.dumps(fl)); pg.wait_for_timeout(400)
        pg.click('#ptree .ptr[data-id=%s] .ptl' % json.dumps(t)); pg.wait_for_timeout(1500)
        r = pg.evaluate(SEL); print("klik", t, r)
        cek(r["sel"] == t and "pAM" in r["sec"] and "pBM" not in r["sec"], "B klik %s: node tetap terpilih & panel As-Mined (bukan Buat Flitch)" % t)
    cek(len(tgt) == 2, "B node Per flitch ditemukan (%s)" % tgt)
    # C: Register untuk database
    pg.evaluate("PT.open['reg']=1;PT.render(true)"); pg.wait_for_timeout(300)
    has = pg.evaluate("!!document.querySelector('#ptree .ptr[data-id=\"reg.db\"]')")
    pg.click('#ptree .ptr[data-id="reg.db"] .ptl') if has else None; pg.wait_for_timeout(1200)
    c = pg.evaluate("(function(){var p=document.getElementById('pAM'),sec=[].slice.call(p.querySelectorAll('.uisec')).filter(function(s){return s.offsetParent;});var t=sec.map(function(s){return s.innerText;}).join('\\n');return {tab:(p.querySelector('.uitabs button.on')||{}).textContent,salin:/Salin ke Excel/.test(t),layout:/Layout PDF/.test(t),xl:/workbook/i.test(t)};})()"); print("C", has, c)
    cek(has and c["salin"] and c["xl"] and not c["layout"], "C node 'Register untuk database' membuka bagian tersendiri (Salin ke Excel + workbook, tanpa Layout PDF)")
    pg.click('#ptree .ptr[data-id="reg.2"] .ptl'); pg.wait_for_timeout(1000)
    c2 = pg.evaluate("(function(){var p=document.getElementById('pAM');var t=[].slice.call(p.querySelectorAll('.uisec')).filter(function(s){return s.offsetParent;}).map(function(s){return s.innerText;}).join('\\n');return {salin:/Salin ke Excel/.test(t),layout:/Layout PDF/.test(t)};})()")
    cek(c2["layout"] and not c2["salin"], "C Layout as-mined tidak lagi memuat menu register")
    # D: Slicer
    pg.click('#btnSecM'); pg.wait_for_timeout(500)
    t = pg.evaluate("(function(){var m=document.getElementById('secMenu');return {txt:m.innerText,b2:document.getElementById('btn2d').innerText.trim(),b3:(document.getElementById('btnSec3')||{innerText:''}).innerText.trim()};})()")
    cek("Sayatan Garis Bebas" in t["txt"] and "Garis di peta" not in t["txt"] and "Pengaturan lanjutan" not in t["txt"] and t["b2"] == "Tampilan 2D" and t["b3"] == "Tampilan 3D", "D popup Slicer: Sayatan Garis Bebas, Tampilan 2D / 3D, tanpa Pengaturan lanjutan (%s | %s)" % (t["b2"], t["b3"]))
    pg.click("#secMenu button[data-pre=line]"); pg.wait_for_timeout(700)
    s3 = pg.evaluate("({mode:S3.mode,box:!!document.getElementById('s3Box')&&getComputedStyle(document.getElementById('s3Box')).display!=='none'})"); pg.evaluate("s3Off()")
    cek(s3["mode"] == "free" and s3["box"], "D 'Sayatan Garis Bebas' membuka kotak Sayatan garis bebas")
    def klik(sel):
        pg.click('#btnSecM'); pg.wait_for_timeout(400); pg.click(sel); pg.wait_for_timeout(2000); return pg.evaluate("({v:!!VIEW2D,s3:S3.mode||''})")
    k1 = klik('#btn2d'); k2 = klik('#btn2d'); k3 = klik('#btnSec3'); k4 = klik('#btnSec3'); print(k1, k2, k3, k4)
    cek(k1["v"] and k2["v"] and not k3["v"] and not k4["v"] and not (k3["s3"] or k4["s3"]), "D Tampilan 2D / 3D hanya berpindah tampilan (tidak bolak-balik, tidak membuka garis bebas)")
    pg.evaluate("PT.open['set']=1;PT.render(true)"); pg.wait_for_timeout(300)
    cek(not pg.evaluate("!!document.querySelector('#ptree .ptr[data-id=\"set.s\"]')"), "D node 'Sayatan' di Pengaturan tampilan dihapus")
    # E: kinerja
    pg.evaluate("(function(){var b=document.createElement('button');b.id='ujiDlg';b.textContent='UjiDialog';b.onclick=function(){prompt('uji','1');};document.getElementById('side').appendChild(b);})()")
    TUNDA["s"] = 1.5; pg.click('#ujiDlg'); TUNDA["s"] = 0; pg.wait_for_timeout(2500)
    e = pg.evaluate("(function(){var o=KIN.log.filter(function(x){return /UjiDialog/.test(x.aksi);})[0];return o?{sync:o.sync,lt:Math.round(o.lt),aksi:o.aksi}:null;})()"); print("E", e)
    cek(e and e["sync"] < 400 and e["lt"] < 400 and "dialog" in e["aksi"], "E laporan kinerja: dialog 1,5 dtk tidak dihitung (sinkron %s ms, long task %s ms)" % (e and e["sync"], e and e["lt"]))
    cek(not err, "tanpa galat halaman: %s" % err[:3])
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
