# -*- coding: utf-8 -*-
"""BM 0.24.99 / DH 0.24.102: alat Ukur jarak (ukur.js) di 3D dan penampang / peta 2D.
  U1 tombol Ukur ada di plot 3D DH (samping kotak skala).
  U2 3D: klik mouse di layar pada dua collar -> titik menempel ke data; jarak miring = jarak 3D kedua titik.
  U3 klik di area kosong 3D -> tidak menambah titik, ada pesan.
  U4 klik kanan menghapus titik terakhir; Esc selesai.
  U5 2D (Penampang): dua klik -> jarak = jarak koordinat sumbu (p2l), juga dengan VE.
  U6 BM: tombol Ukur ada di peta 2D & 3D.
Pemakaian: python tools/uji/uji_ukur.py"""
import math, random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
def server(app):
    d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / app / "index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
    P = random.randint(9400, 9799); s = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); return s, P
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    # ---------------- DH ----------------
    srv, P = server("app-dh"); pg = b.new_page(viewport={"width": 1600, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length > 0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(5000)
    cek(pg.evaluate("(function(){var b=document.querySelector('#plotDiv > .gxUkurB');return !!b&&b.style.display!=='none';})()"), "U1 tombol Ukur di 3D DH")
    # dua collar yang tampak di layar, berjauhan
    T = pg.evaluate("""()=>{var gd=$('plotDiv'),pr=SKL.proj3d(gd),r=gd.getBoundingClientRect(),c=[];
      gd.data.forEach(function(t){if(t.type!=='scatter3d'||t.visible===false||!t.x)return;for(var i=0;i<t.x.length;i+=1){if(t.x[i]==null)continue;var s=pr(+t.x[i],+t.y[i],+t.z[i]);if(s[0]>60&&s[0]<r.width-60&&s[1]>60&&s[1]<r.height-120)c.push([+t.x[i],+t.y[i],+t.z[i],s[0],s[1]]);}});
      c.sort(function(a,b){return a[3]-b[3];});return {a:c[Math.floor(c.length*0.1)],b:c[Math.floor(c.length*0.9)],L:r.left,T:r.top};}""")
    pg.evaluate("UKUR.mulai('plotDiv')")
    for q in (T["a"], T["b"]): pg.mouse.click(T["L"] + q[3], T["T"] + q[4]); pg.wait_for_timeout(300)
    R = pg.evaluate("UKUR.hasil()")
    ok2 = R and len(R["P"]) == 2
    if ok2:
        sp = pg.evaluate("(P)=>{var pr=SKL.proj3d($('plotDiv'));return P.map(function(p){return pr(p[0],p[1],p[2]);});}", R["P"])
        near = all(math.hypot(sp[i][0] - q[3], sp[i][1] - q[4]) <= 14.01 for i, q in enumerate((T["a"], T["b"])))
        d = math.dist(R["P"][0], R["P"][1])
    cek(ok2 and near and abs(R["ruas"][0]["d"] - d) < 1e-6 and abs(R["ruas"][0]["h"] - math.hypot(R["P"][1][0] - R["P"][0][0], R["P"][1][1] - R["P"][0][1])) < 1e-6,
        "U2 3D dua klik menempel ke data: %s m (horizontal %s, ΔZ %s)" % (R and R["ruas"] and round(R["ruas"][0]["d"], 2), R and R["ruas"] and round(R["ruas"][0]["h"], 2), R and R["ruas"] and round(R["ruas"][0]["dz"], 2)))
    pg.mouse.click(T["L"] + 8, T["T"] + 300); pg.wait_for_timeout(300)
    n3 = pg.evaluate("UKUR.hasil().P.length"); m3 = pg.evaluate("document.querySelector('.gxUkurP').textContent")
    cek(n3 == 2 and "menempel" in m3, "U3 klik area kosong 3D: titik tetap %d, ada pesan" % n3)
    pg.mouse.click(T["L"] + T["b"][3], T["T"] + T["b"][4], button="right"); pg.wait_for_timeout(200); n4 = pg.evaluate("UKUR.hasil().P.length")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200); n4b = pg.evaluate("UKUR.aktif===null&&!document.querySelector('.gxUkurC')")
    cek(n4 == 1 and n4b, "U4 klik kanan -> %d titik; Esc selesai: %s" % (n4, n4b))
    # 2D penampang
    pg.evaluate("if(!VIEW2D)toggle2D()"); pg.wait_for_timeout(5000)
    I = pg.evaluate("(function(){var gd=$('plotDiv'),fl=gd._fullLayout,xa=fl.xaxis,ya=fl.yaxis,r=gd.getBoundingClientRect();return {is2d:!fl.scene||!fl.scene._scene,L:r.left,T:r.top,x0:xa._offset,y0:ya._offset,w:xa._length,h:ya._length,ve:+(gd.layout.yaxis.scaleratio||1),btn:!!gd.querySelector(':scope > .gxUkurB')};})()")
    pg.evaluate("UKUR.mulai('plotDiv')")
    p1 = (I["x0"] + I["w"] * 0.25, I["y0"] + I["h"] * 0.3); p2 = (I["x0"] + I["w"] * 0.7, I["y0"] + I["h"] * 0.75)
    for q in (p1, p2): pg.mouse.click(I["L"] + q[0], I["T"] + q[1]); pg.wait_for_timeout(300)
    R5 = pg.evaluate("UKUR.hasil()")
    ex = pg.evaluate("(Q)=>{var fl=$('plotDiv')._fullLayout,xa=fl.xaxis,ya=fl.yaxis;return Q.map(function(q){return [xa.p2l(q[0]-xa._offset),ya.p2l(q[1]-ya._offset)];});}", [p1, p2])
    d5 = math.dist(ex[0], ex[1])
    cek(I["is2d"] and I["btn"] and R5 and not R5["d3"] and len(R5["P"]) == 2 and abs(R5["ruas"][0]["d"] - d5) < 2 * pg.evaluate("SKL.info('plotDiv').mpp"), "U5 2D: %s m = jarak koordinat sumbu %s m (VE %s)" % (R5 and R5["ruas"] and round(R5["ruas"][0]["d"], 2), round(d5, 2), I["ve"]))
    pg.screenshot(path=str(Path(tempfile.gettempdir()) / "uji_ukur_2d.png"))
    pg.evaluate("UKUR.selesai()")
    cek(not E, "DH tanpa galat halaman %s" % E[:2])
    srv.terminate()
    # ---------------- BM ----------------
    srv, P = server("app"); pg = b.new_page(viewport={"width": 1600, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m", timeout=600000); pg.wait_for_timeout(6000)
    u6 = pg.evaluate("[].slice.call(document.querySelectorAll('.js-plotly-plot')).filter(function(g){var b=g.querySelector(':scope > .gxUkurB');return b&&b.style.display!=='none'&&g.offsetParent;}).map(function(g){return g.id+(g._fullLayout.scene&&g._fullLayout.scene._scene?':3d':':2d');})")
    cek(len(u6) >= 1, "U6 BM: tombol Ukur di plot %s" % u6)
    cek(not E, "BM tanpa galat halaman %s" % E[:2])
    srv.terminate(); b.close()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
