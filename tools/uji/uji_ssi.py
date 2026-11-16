# -*- coding: utf-8 -*-
"""BM 0.24.96: gaya Surpac (.ssi) — baca gaya string & skema warna rentang, tulis .ssi di samping .str.
Contoh .ssi di bawah dibuat sendiri mengikuti format Surpac (bukan berkas situs).
  S1 parse gaya string: nomor tunggal, rentang "awal, akhir, langkah", default.
  S2 (bila ada) semua .ssi di /mnt/user-data/uploads terbaca (lokal saja, tidak di-commit).
  S3 Import .ssi situs: warna kelas dig block, material, As-Mined & string ikut warna nomornya.
  S4 Ekspor string STR -> berkas .ssi bernama sama; warna tiap nomor = warna GC-Ex; baris gaya situs lain tetap.
  S5 skema rentang (0;0.4;1;3;999~range) -> kelas warna block model.
  S6 sakelar ekspor .ssi mati -> hanya .str.
  S7 UI: kotak Warna Surpac di Dig Block › Otomatis & tombol impor di Warna & kelas kadar.
Pemakaian: python tools/uji/uji_ssi.py"""
import glob, json, random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
T = "HGS_line_pattern=|--->,HGS_line_weight=1"
SITUS = "\r\n".join(["STRINGS:", "default=ssi_label=yellow line,HGS_color=lines=text=edges=markers=yellow," + T,
    "1=ssi_label=,HGS_color=lines=text=edges=markers=white," + T, "4=ssi_label=,HGS_color=lines=text=edges=markers=r=0.478 g=0.819 b=0.478," + T,
    "7=ssi_label=,HGS_color=lines=text=edges=markers=r=1.0 g=0.6 b=0.2," + T,
    "14, 99, 10=ssi_label=,HGS_color=lines=text=edges=markers=r=0.349 g=1.0 b=0.349," + T, "17, 99, 10=ssi_label=,HGS_color=lines=text=edges=markers=red," + T,
    "30000=ssi_label=thick grey arrow line,HGS_color=lines=text=edges=markers=light grey," + T, "TRIOBJECTS:", "default=ssi_label=,HGS_color=lines=text=edges=markers=blue," + T, ""])
RENTANG = "pink~default face colour\nblue~default edge colour\n0;0.4;1;3;999~range\ngrey~0.00 -> 0.40\ngreen~0.40 -> 1.00\nred~1.00 -> 3.00\nmagenta~3.00 -> 999.00\n"
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9100, 9199); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1500, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && window.SWN && SWN.ssi", timeout=600000); pg.wait_for_timeout(4000)
    s1 = pg.evaluate("(t)=>{var S=SWN.ssi.parse(t);return [1,4,7,14,24,94,17,27,99,30000].map(function(n){return SWN.ssi.colorOf(S,n);});}", SITUS)
    cek(s1 == ["#ffffff", "#7ad17a", "#ff9933", "#59ff59", "#59ff59", "#59ff59", "#ff0000", "#ff0000", "#ffff00", "#d3d3d3"], "S1 gaya string terbaca: %s" % s1)
    up = sorted(glob.glob("/mnt/user-data/uploads/*.ssi"))
    if up:
        r2 = [pg.evaluate("(t)=>{var S=SWN.ssi.parse(t);return S?S.kind+':'+(S.kind==='styles'?SWN.ssi.colorOf(S,14)+'/'+SWN.ssi.colorOf(S,17):S.cuts.join(';')):null;}", Path(f).read_text(errors="replace")) for f in up]
        cek(all(r2), "S2 %d berkas .ssi lokal terbaca: %s" % (len(up), sorted(set(r2))))
    pg.evaluate("""()=>{var u=dbU();u.rules=[{lo:0.4,hi:1,n:14,c:'#7ee04a',m:'LG'},{lo:1,hi:'',n:17,c:'#ff1a1a',m:'HG'}];u.sn={WS:{n:1,c:'#9aa3ad'}};u.snc={};var R=amR();R.cls=[{m:'LG',lo:0.5,hi:1,n:14,c:'#4caf50'},{m:'HG',lo:1,hi:'',n:17,c:'#d62728'}];
      window.__f=[];window.dgDl=function(t,f){__f.push([f,t]);};DG.S.forEach(function(s){s.vis=false;});var p=function(d){return [[d,0,0],[d+10,0,0],[d+10,10,0],[d,10,0]];};
      DG.S.push({id:'s1',pts:p(0),closed:true,vis:true,no:14,col:'#7ee04a',d:'LG'});DG.S.push({id:'s2',pts:p(20),closed:true,vis:true,no:17,col:'#ff1a1a',d:'HG'});window.__i=DG.S.length-2;}""")
    n3 = pg.evaluate("(t)=>SWN.imporSitus(t,'uji_situs.ssi')", SITUS)
    s3 = pg.evaluate("[dbU().rules[0].c,dbU().rules[1].c,dbU().sn.WS.c,amR().cls[0].c,amR().cls[1].c,DG.S[__i].col,DG.S[__i+1].col]")
    cek(s3 == ["#59ff59", "#ff0000", "#ffffff", "#59ff59", "#ff0000", "#59ff59", "#ff0000"], "S3 impor gaya situs (%s perubahan): %s" % (n3, s3))
    pg.evaluate("dbStrSet(__i+1,'col','#cc00cc');__f=[];dgExport('str')"); pg.wait_for_timeout(1500)
    f4 = pg.evaluate("__f.map(function(x){return [x[0],x[1]];})")
    names = [x[0] for x in f4]; ssi = [x[1] for x in f4 if x[0].endswith(".ssi")]
    ok4 = len(names) == 2 and names[0].endswith(".str") and names[1] == names[0][:-4] + ".ssi"
    if ok4:
        back = pg.evaluate("(t)=>{var S=SWN.ssi.parse(t);return [SWN.ssi.colorOf(S,14),SWN.ssi.colorOf(S,17),SWN.ssi.colorOf(S,30000),SWN.ssi.colorOf(S,7)];}", ssi[0])
        L = ssi[0].split("\r\n"); i14 = [k for k, l in enumerate(L) if l.startswith("14=")]; idf = [k for k, l in enumerate(L) if l.startswith("default=")]
    cek(ok4 and back == ["#59ff59", "#cc00cc", "#d3d3d3", "#ff9933"] and i14 and i14[0] == idf[0] + 1, "S4 ekspor %s; warna di .ssi %s" % (names, back if ok4 else None))
    n5 = pg.evaluate("(t)=>SWN.imporRentang(t)", RENTANG); s5 = pg.evaluate("BX.ui.cls[BX.ui.attr].map(function(c){return [c.lo,c.hi,c.col];})")
    cek(n5 == 4 and s5 == [[None, 0.4, "#808080"], [0.4, 1, "#00ff00"], [1, 3, "#ff0000"], [3, None, "#ff00ff"]], "S5 skema rentang -> kelas %s" % s5)
    pg.evaluate("dbU().ssiOut=false;__f=[];dgExport('str')"); pg.wait_for_timeout(600)
    cek(pg.evaluate("__f.length") == 1, "S6 sakelar mati -> %s berkas" % pg.evaluate("__f.length"))
    # S8 (17 Nov 2026): tanpa .ssi situs -> gaya bawaan Surpac (legend pemilik); header STR menunjuk .ssi pasangannya
    pg.evaluate("SWN.lupaSitus();dbU().ssiOut=true;__f=[];dgExport('str')"); pg.wait_for_timeout(1500)
    f8 = pg.evaluate("__f.map(function(x){return [x[0],x[1]];})")
    h8 = f8[0][1].split("\r\n")[0] if f8 else ""
    b8 = pg.evaluate("(t)=>{var S=SWN.ssi.parse(t);return [16,24,18,7,1,19].map(function(n){return SWN.ssi.colorOf(S,n);});}", f8[1][1]) if len(f8) == 2 else None
    cek(len(f8) == 2 and h8.endswith("SSI_STYLES:" + f8[1][0]) and b8 == ["#ff9933", "#59ff59", "#ff66ff", "#ff9933", "#ffffff", "#ffff00"] and "TRIOBJECTS:" in f8[1][1], "S8 header %r; warna bawaan 16/24/18/7/1/19 %s" % (h8[-40:], b8))
    d8 = pg.evaluate("[SWN.dekat('#e2b922',17,{}),SWN.dekat('#ff8c00',19,{16:1}),SWN.dekat('#ff1a1a',14,{8:1})]")
    cek(d8 == [16, 26, 17], "S9 nomor baru ikut warna Surpac terdekat (kuning-oranye->16, oranye bila 16 terpakai->26, merah->17): %s" % d8)
    pg.evaluate("dbU().ssiOut=true;PT&&PT.select&&PT.select('dig.auto')"); pg.wait_for_timeout(800); u1 = pg.evaluate("!!document.getElementById('swSsi')")
    if len(sys.argv) > 1:
        pg.evaluate("document.getElementById('swSsi').scrollIntoView({block:'center'})"); pg.wait_for_timeout(400); bb = pg.evaluate("(function(){var r=document.getElementById('swSsi').getBoundingClientRect();return [r.x,r.y,r.width,r.height];})()")
        pg.screenshot(path=sys.argv[1], clip={"x": max(0, bb[0] - 10), "y": max(0, bb[1] - 160), "width": bb[2] + 20, "height": bb[3] + 200})
    pg.evaluate("bxPanel()"); pg.wait_for_timeout(300)
    cek(u1 and pg.evaluate("!!document.querySelector('.swRg')"), "S7 kotak Warna Surpac & tombol skema kadar ada")
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
