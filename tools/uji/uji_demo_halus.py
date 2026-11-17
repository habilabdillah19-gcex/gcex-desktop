# -*- coding: utf-8 -*-
"""BM 0.24.104 / DH 0.24.107: demo sehalus video (demohalus.js).
  H1 dmSet pada isian angka: kursor meluncur (posisi antara teramati), lalu angka diketik huruf demi huruf, baru onchange.
  H2 dmClick: aksi baru dijalankan sesudah kursor tiba (tidak seketika).
  H3 setCam saat demo: mata kamera berpindah bertahap (posisi antara dikirim ke Plotly), berakhir di target.
     (render GPU tidak ikut diuji: Plotly.relayout & requestAnimationFrame diganti perekam supaya tidak bergantung GPU kontainer)
  H4 digitasi saat demo: titik baru didahului garis yang memanjang (DG.hov bergerak), semua titik akhirnya masuk.
  H5 bilah keterangan: bab, judul, satu kalimat.
  H6 demo jalan beberapa langkah tanpa galat, Stop mengembalikan tampilan; BM juga tanpa galat.
Pemakaian: python tools/uji/uji_demo_halus.py"""
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
SAMPLE = """(a)=>new Promise(function(res){var out=[],t0=performance.now();(function f(){out.push(eval(a.expr));if(performance.now()-t0<a.ms)requestAnimationFrame(f);else res(out);})();})"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server("app-dh"); pg = b.new_page(viewport={"width": 1600, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept()); pg.on("console", lambda m: print(m.text[:600]) if "ERRCAM" in m.text else None)
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length > 0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(3000)
    pg.evaluate("dmStart();DM.pause=true;"); pg.wait_for_timeout(1500)
    pg.evaluate("window.__inp=document.createElement('input');__inp.type='number';__inp.step='any';__inp.id='__ujiNum';__inp.style.cssText='position:fixed;left:1000px;top:420px;width:80px;z-index:5';__inp.onchange=function(){};document.body.appendChild(__inp);var c=$('dmCur');c.style.left='200px';c.style.top='200px';c.style.opacity=1;")
    pg.wait_for_timeout(700)
    print("  (isian uji: %s)" % pg.evaluate("__inp&&__inp.id")); pg.evaluate("window.__fired=0;var _o=__inp.onchange;__inp.onchange=function(){__fired++;return _o.apply(this,arguments);};dmSet(__inp.id,12.5)")
    S = pg.evaluate(SAMPLE, {"expr": "[Math.round(parseFloat(getComputedStyle($('dmCur')).left)),__inp.value,window.__fired]", "ms": 1600})
    xs = sorted(set(s[0] for s in S)); vals = [s[1] for s in S]; ket = []
    for v in vals:
        if not ket or ket[-1] != v: ket.append(v)
    fired_at = next((k for k, s in enumerate(S) if s[2]), None); full_at = next((k for k, s in enumerate(S) if s[1] == "12.5"), None)
    cek(len(xs) >= 4 and "1" in ket and "12" in ket and "12." in ket and ket[-1] == "12.5" and fired_at is not None and full_at is not None and fired_at >= full_at,
        "H1 kursor %d posisi antara; ketik %s; onchange sesudah lengkap" % (len(xs), ket[-6:]))
    pg.evaluate("window.__klik=0;var bt=document.createElement('button');bt.id='__ujiBtn';bt.textContent='uji';bt.style.cssText='position:fixed;left:900px;top:300px;z-index:5';bt.onclick=function(){__klik=performance.now();};document.body.appendChild(bt);window.__t0=performance.now();dmClick('__ujiBtn');")
    pg.wait_for_timeout(1300); dk = pg.evaluate("__klik?__klik-__t0:-1")
    cek(dk >= 400, "H2 klik dijalankan %d ms sesudah kursor berangkat (menunggu kursor tiba)" % dk)
    pg.evaluate("window.__raf=window.requestAnimationFrame;window.requestAnimationFrame=function(cb){return setTimeout(function(){cb(performance.now());},16);};window.__eyes=[];window.__rl=Plotly.relayout;Plotly.relayout=function(g,u){if(u&&u['scene.camera']){var e=u['scene.camera'].eye;__eyes.push([+e.x.toFixed(3),+e.y.toFixed(3),+e.z.toFixed(3)]);return Promise.resolve();}return __rl.apply(this,arguments);};try{setCam(-1.6,1.2,0.8);}catch(er){console.log('ERRCAM '+er.stack);}")
    pg.wait_for_timeout(4000); C = pg.evaluate("__eyes"); pg.evaluate("Plotly.relayout=__rl;window.requestAnimationFrame=__raf;0")
    uniq = []
    for c in C:
        if not uniq or uniq[-1] != c: uniq.append(c)
    cek(len(uniq) >= 5 and abs(uniq[-1][0] + 1.6) < 0.02 and abs(uniq[-1][1] - 1.2) < 0.02, "H3 kamera %d posisi antara, akhir %s" % (len(uniq), uniq[-1]))
    pg.evaluate("uiTab('Dig');if(!VIEW2D)toggle2D();"); pg.wait_for_timeout(3000)
    pg.evaluate("dgStart&&dgStart();var g=secGeom(),s0=(g.seg||60)/2,z0=(g.z0!=null?g.z0:0);window.__Q=[[s0-15,z0+6],[s0,z0+12],[s0+15,z0+4]];")
    pg.evaluate("""()=>{var A=dgAx(),x=A.x.range||A.x._rl,y=A.y._rl||A.y.range;var cx=(x[0]+x[1])/2,cy=(y[0]+y[1])/2,w=(x[1]-x[0])/8,h=(y[1]-y[0])/8;window.__Q=[[cx-w,cy],[cx,cy+h],[cx+w,cy-h]];
      __Q.forEach(function(q,k){setTimeout(function(){if(!DG.on)return;DG.c2.push(q);DG.cur.push(dg3(DG.pl,q[0],q[1]));dgDraw();dgState();},k*900);});}""")
    D = pg.evaluate(SAMPLE, {"expr": "[DG.hov?Math.round(DG.hov[0]):null,DG.c2.length]", "ms": 3200})
    hov = sorted(set(d[0] for d in D if d[0] is not None))
    cek(len(hov) >= 6 and D[-1][1] == 3, "H4 digitasi: garis memanjang (%d posisi ujung), titik akhir %d" % (len(hov), D[-1][1]))
    pg.evaluate("if(DG.on)dgCancel();if(VIEW2D)toggle2D();")
    pg.evaluate("dmGo(3)"); pg.wait_for_timeout(500)
    cap = pg.evaluate("[$('dmSec').textContent,$('dmT').textContent,$('dmD').textContent]")
    cek(all(cap) and cap[2].count(". ") == 0, "H5 bilah keterangan: %s" % cap)
    pg.evaluate("$('plotDiv').style.width='420px';dmPos();"); w7 = pg.evaluate("$('dmBar').getBoundingClientRect().width"); pg.evaluate("$('plotDiv').style.width='';dmPos();")
    cek(w7 >= 600, "H7 bilah keterangan tetap lebar %d px saat area 3D sempit (420 px)" % w7)
    pg.evaluate("DM.pause=false;DM.spd=0.25;"); pg.wait_for_timeout(20000)
    i = pg.evaluate("DM.i"); pg.evaluate("dmStop()"); pg.wait_for_timeout(2000)
    cek(i >= 5 and not E and not pg.evaluate("DM.on"), "H6 DH demo jalan sampai langkah %d tanpa galat %s; Stop" % (i, E[:2]))
    srv.terminate()
    srv, P = server("app"); pg = b.new_page(viewport={"width": 1600, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(4000)
    pg.evaluate("dmStart();DM.spd=0.25;"); pg.wait_for_timeout(25000); i = pg.evaluate("DM.i"); pg.evaluate("dmStop()"); pg.wait_for_timeout(1500)
    cek(i >= 5 and not E and bool(pg.evaluate("!!window.DMH")), "H6 BM demo jalan sampai langkah %d tanpa galat %s" % (i, E[:2]))
    srv.terminate(); b.close()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
