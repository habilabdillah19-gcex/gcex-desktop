# -*- coding: utf-8 -*-
"""BM 0.24.94: satu nomor string = satu warna di STR & DXF (dig block, string digitasi, As-Mined).
  W1 ekspor string: nomor 14 dipakai hijau & oranye -> OK = oranye diberi nomor baru; STR memuat 2 nomor; DXF layer = nomor, 62 = ACI.
  W2 popup: ganti warna string 14 -> semua string 14 & baris kelas 14 ikut.
  W3 popup: ganti nomor ke 17 -> warna ikut warna nomor 17 (kelas HG).
  W4 As-Mined: Warna poligon = warna String ID (ganti warna -> nomor itu; ganti String ID -> warnanya ikut).
  W5 As-Mined lama: warna manual beda dengan String ID-nya -> ekspor STR menawarkan nomor baru; DXF layer = String ID, 62 = ACI.
  W6 ACI: merah 1, kuning 2, hijau 3, oranye 30-ish, abu-abu.
Pemakaian: python tools/uji/uji_warna_nomor.py"""
import random, re, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9800, 9899); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
def dxf_layers(t):
    L = t.split("\r\n"); out = []
    for i in range(len(L) - 1):
        if L[i] == "POLYLINE":
            ly = L[i + 2]; c = L[i + 4] if L[i + 3] == "62" else None; out.append((ly, c))
    return out
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1500, "height": 950}); E = []; DLG = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: (DLG.append(x.message[:200]), x.accept()))
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && window.SWN", timeout=600000); pg.wait_for_timeout(4000)
    pg.evaluate("""()=>{window.__f=[];window.dgDl=function(t,f){__f.push([f,t]);};var u=dbU();u.rules=[{lo:0.4,hi:1,n:14,c:'#7ee04a',m:'LG'},{lo:1,hi:'',n:17,c:'#ff1a1a',m:'HG'}];u.sn={};u.snc={};
      DG.S.forEach(function(s){s.vis=false;});var p=function(d){return [[d,0,0],[d+10,0,0],[d+10,10,0],[d,10,0]];};
      DG.S.push({id:'w1',pts:p(0),closed:true,vis:true,no:14,col:'#7ee04a',d:'LG'});DG.S.push({id:'w2',pts:p(20),closed:true,vis:true,no:14,col:'#ff8c00',d:'LG'});DG.S.push({id:'w3',pts:p(40),closed:true,vis:true,no:14,col:'#7ee04a',d:'LG'});
      window.__i=DG.S.length-3;dgExport('str');dgExport('dxf');}""")
    f1 = pg.evaluate("__f"); st = f1[0][1]; nos = sorted(set(int(l.split(",")[0]) for l in st.split("\r\n")[2:] if re.match(r"^[1-9]\d*,", l)))
    lay = dxf_layers(f1[-1][1])
    cek(nos == [14, 16] and pg.evaluate("DG.S[__i+1].no") == 16 and pg.evaluate("SWN.dig()[16]") == "#ff8c00" and len(DLG) >= 1, "W1 STR nomor %s (oranye -> 16 = nomor oranye di gaya Surpac situs, terdaftar)" % nos)
    cek(set(lay) == {("14", str(pg.evaluate("SWN.aci('#7ee04a')"))), ("16", str(pg.evaluate("SWN.aci('#ff8c00')")))}, "W1 DXF layer & warna %s" % sorted(set(lay)))
    pg.evaluate("dbStrSet(__i,'col','#00aa55')")
    w2 = pg.evaluate("[DG.S[__i].col,DG.S[__i+2].col,dbU().rules[0].c,DG.S[__i+1].col]")
    cek(w2 == ["#00aa55", "#00aa55", "#00aa55", "#ff8c00"], "W2 warna string 14 -> semua string 14 + kelas LG ikut: %s" % w2)
    pg.evaluate("dbStrSet(__i+2,'no',17)"); w3 = pg.evaluate("[DG.S[__i+2].no,DG.S[__i+2].col]")
    cek(w3 == [17, "#ff1a1a"], "W3 ganti nomor -> warna nomor 17: %s" % w3)
    # ---------- As-Mined ----------
    ok = pg.evaluate("""()=>{var X=BX.m.x,Y=BX.m.y,i=0,x0=X[i],y0=Y[i];var a=amBndAdd([[x0,y0],[x0+10,y0],[x0+10,y0+10],[x0,y0+10]],'uji1'),b=amBndAdd([[x0+20,y0],[x0+30,y0],[x0+30,y0+10],[x0+20,y0+10]],'uji2');
      var L=amBndAll();window.__a=L[L.length-2];window.__b=L[L.length-1];__a.on=__b.on=true;__a.sid=14;__b.sid=14;var R=amR();R.cls=[{m:'LG',lo:0.5,hi:1,n:14,c:'#4caf50'},{m:'HG',lo:1,hi:'',n:17,c:'#ff1a1a'}];return !!(a&&b);}""")
    pg.evaluate("amPSet(__a.id,'col','#aa00aa')")
    w4 = pg.evaluate("[amInfo(__a).col,amInfo(__b).col,amR().cls[0].c,!!__a.col]")
    pg.evaluate("amPSet(__b.id,'sid','17')"); w4b = pg.evaluate("[amInfo(__b).sid,amInfo(__b).col]")
    cek(ok and w4 == ["#aa00aa", "#aa00aa", "#aa00aa", False] and w4b == [17, "#ff1a1a"], "W4 As-Mined warna -> nomor %s; ganti String ID -> %s" % (w4, w4b))
    DLG.clear(); pg.evaluate("__b.sid=14;__b.col='#0000ff';window.__f=[];amStr();amDxf();")
    f5 = pg.evaluate("__f"); ok5 = len(f5) == 2
    if ok5:
        n5 = sorted(set(int(l.split(",")[0]) for l in f5[0][1].split("\r\n")[2:] if re.match(r"^[1-9]\d*,", l))); l5 = sorted(set(dxf_layers(f5[1][1])))
    cek(ok5 and len(n5) == 2 and 14 in n5 and len(l5) == 2 and pg.evaluate("amInfo(__b).col") == "#0000ff" and f5[0][1].split("\r\n")[0].endswith(",SSI_STYLES:" + f5[0][0][:-4] + ".ssi"), "W5 As-Mined lama warna manual -> STR nomor %s, DXF %s, header %r" % (n5 if ok5 else None, l5 if ok5 else None, f5[0][1].split("\r\n")[0] if ok5 else None))
    w6 = pg.evaluate("[SWN.aci('#ff0000'),SWN.aci('#ffff00'),SWN.aci('#00ff00'),SWN.aci('#ff8c00'),SWN.aci('#808080')]")
    cek(w6[0] == 1 and w6[1] == 2 and w6[2] == 3 and 20 <= w6[3] <= 40 and w6[4] in (8, 252, 253), "W6 ACI %s" % w6)
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
