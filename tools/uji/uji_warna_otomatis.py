# -*- coding: utf-8 -*-
"""BM 0.24.98: pilih warna -> nomor string mengikuti (palet Surpac); ketik nomor -> warna mengikuti.
  A1 kelas dig block: oranye -> 16, warna dibulatkan ke oranye Surpac; ketik 17 -> merah Surpac.
  A2 flag garis ganda: oranye -> 16 (atau 26 bila 16 dipakai warna lain).
  A3 material & kelas As-Mined: biru -> 11, hijau -> 14; ws ketik 1 -> putih.
  A4 palet Surpac terpasang di pemilih warna (datalist).
  A5 dengan .ssi situs diimpor: nomor ikut gaya situs.
Pemakaian: python tools/uji/uji_warna_otomatis.py"""
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
    pg.evaluate("""()=>{var u=dbU();u.rules=[{lo:0.4,hi:1,n:14,c:'#7ee04a',m:'LG'},{lo:1,hi:'',n:17,c:'#ff1a1a',m:'HG'}];u.sn={};u.snc={};delete u.ssiTxt;u.sfCol='flag';
      var R=afRules();R.length=0;R.push({n:'Flag 1',k:'num',a:Object.keys(BX.m.num)[0],op:'>',c:1,col:'#000000',on:true});}""")
    pg.evaluate("dbRSet(0,'c','#ff8800')"); a1 = pg.evaluate("[dbU().rules[0].n,dbU().rules[0].c]")
    pg.evaluate("dbRSet(0,'n','17')"); a1b = pg.evaluate("[dbU().rules[0].n,dbU().rules[0].c]")
    cek(a1 == [16, "#ff9933"] and a1b == [17, "#ff0000"], "A1 kelas: oranye -> %s; ketik 17 -> %s" % (a1, a1b))
    pg.evaluate("dbRSet(0,'c','#59ff59')"); pg.evaluate("afSet(0,'col','#e2b922')"); a2 = pg.evaluate("[afRules()[0].sn,afRules()[0].col]")
    pg.evaluate("dbU().rules[0].n=16;dbU().rules[0].c='#59ff59';afSet(0,'col','#ff8c00')"); a2b = pg.evaluate("afRules()[0].sn")
    cek(a2 == [16, "#ff9933"] and a2b == 26, "A2 flag: kuning-oranye -> %s; 16 dipakai hijau -> %s" % (a2, a2b))
    pg.evaluate("dbU().rules[0].n=14;dbSNset('WS','c','#0000ff')"); a3 = pg.evaluate("[dbU().sn.WS.n,dbU().sn.WS.c]")
    pg.evaluate("""()=>{var R=amR();R.cls=[{m:'LG',lo:0.5,hi:1,n:1,c:'#000000'}];R.ws={m:'WS',n:5,c:'#000000'};amClsSet(0,'c','#00ff00');amClsSet('ws','n','1');}""")
    a3b = pg.evaluate("[amR().cls[0].n,amR().cls[0].c,amR().ws.n,amR().ws.c]")
    cek(a3 == [11, "#0000ff"] and a3b == [14, "#59ff59", 1, "#ffffff"], "A3 material biru -> %s; As-Mined hijau, ws 1 -> %s" % (a3, a3b))
    pg.evaluate("PT&&PT.select&&PT.select('dig.auto')"); pg.wait_for_timeout(800)
    a4 = pg.evaluate("""()=>{var i=[].slice.call(document.querySelectorAll('input[type=color]')).filter(function(x){return /dbRSet/.test(x.getAttribute('onchange')||'');})[0];if(!i)return null;
      i.dispatchEvent(new FocusEvent('focusin',{bubbles:true}));var d=document.getElementById('swPal');return [i.getAttribute('list'),d?d.options.length:0];}""")
    cek(a4 and a4[0] == "swPal" and a4[1] >= 8, "A4 palet Surpac di pemilih warna: %s" % a4)
    SITUS = "STRINGS:\r\ndefault=ssi_label=,HGS_color=lines=text=edges=markers=yellow\r\n3=ssi_label=,HGS_color=lines=text=edges=markers=r=1.0 g=0.6 b=0.2\r\n"
    pg.evaluate("(t)=>{dbU().ssiTxt=t;dbRSet(1,'c','#ff8800');}", SITUS); a5 = pg.evaluate("dbU().rules[1].n")
    cek(a5 == 3, "A5 gaya situs: oranye -> %s" % a5)
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
