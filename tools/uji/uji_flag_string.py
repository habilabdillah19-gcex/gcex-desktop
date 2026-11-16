# -*- coding: utf-8 -*-
"""BM 0.24.93: aturan flag (Additional flagging) boleh punya string number sendiri untuk garis ganda.
  F1 kolom String di tabel aturan flag.
  F2 sn = 19 -> garis ganda ber-flag memakai string 19 (BM 0.24.98: warna flag ikut warna 19 di legend Surpac = kuning), garis asli tetap 14.
  F3 ganti nomor / tombol kelas garis asli (17) -> garis ganda tetap 19.
  F4 kosongkan sn -> garis ganda kembali ikut nomor garis asli (cara lama).
  F5 ekspor STR teks: baris garis ganda memakai string 19.
Pemakaian: python tools/uji/uji_flag_string.py"""
import random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
P = random.randint(9700, 9799); srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1500, "height": 950}); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:300])); pg.on("dialog", lambda x: x.accept())
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && window.afRules", timeout=600000); pg.wait_for_timeout(4000)
    pg.evaluate("""()=>{var R=afRules();if(!R.length)afAdd();R[0].n='Ore Sulfide';R[0].col='#ff8c00';
      var p=[[0,0,0],[20,0,0],[20,20,0],[0,20,0]],q=[[1,1,0],[19,1,0],[19,19,0],[1,19,0]];DG.S.push({id:'fP',pts:p,closed:true,vis:true,no:14,col:'#7ee04a',d:'LG'});
      DG.S.push({id:'fI',pts:q,closed:true,vis:true,no:14,col:'#ff8c00',fcol:'#ff8c00',fl:'Ore Sulfide',inner:true,parent:'fP'});window.__pi=DG.S.length-2;
      PT&&PT.select&&PT.select('dig.auto');}""")
    pg.wait_for_timeout(1200)
    cek(pg.evaluate("!!document.querySelector('input.afsn')"), "F1 kolom String di tabel aturan flag")
    pg.evaluate("afSet(0,'sn',19)"); pg.wait_for_timeout(500)
    f2 = pg.evaluate("[DG.S[__pi].no, DG.S[__pi+1].no, DG.S[__pi+1].col]")
    cek(f2 == [14, 19, "#ffff00"], "F2 sn 19: garis asli %s, garis ganda %s warna %s" % tuple(f2))
    pg.evaluate("dbStrSet(__pi,'no',17);dbStrKelas(__pi,dbKelas().map(function(q){return q.n;}).indexOf(17))"); pg.wait_for_timeout(500)
    f3 = pg.evaluate("[DG.S[__pi].no, DG.S[__pi+1].no]")
    cek(f3 == [17, 19], "F3 garis asli diganti -> %s, garis ganda tetap %s" % tuple(f3))
    pg.evaluate("window.__txt=null;window.dgDl=function(t,f){window.__txt=t;};var o=dbStrings;dbStrings=function(){return DG.S.filter(function(s){return s.id==='fP'||s.id==='fI';});};dbExport('strt');dbStrings=o;")
    t5 = pg.evaluate("window.__txt||''")
    cek(any(l.startswith("19,") for l in t5.split("\r\n")) and any(l.startswith("17,") for l in t5.split("\r\n")), "F5 ekspor STR: string 17 (asli) dan 19 (garis ganda)")
    pg.evaluate("afSet(0,'sn','')"); pg.wait_for_timeout(500)
    f4 = pg.evaluate("[DG.S[__pi].no, DG.S[__pi+1].no, !!DG.S[__pi+1].fsn]")
    cek(f4 == [17, 17, False], "F4 sn dikosongkan -> garis ganda ikut garis asli %s" % f4)
    if len(sys.argv) > 1:
        pg.evaluate("afSet(0,'sn',19);var d=document.querySelector('input.afsn').closest('details');if(d)d.open=true;document.querySelector('input.afsn').scrollIntoView({block:'center'})"); pg.wait_for_timeout(600)
        bb = pg.evaluate("(function(){var r=document.querySelector('table.aftb').getBoundingClientRect();return [r.x,r.y,r.width,r.height];})()")
        pg.screenshot(path=sys.argv[1], clip={"x": max(0, bb[0] - 10), "y": max(0, bb[1] - 90), "width": bb[2] + 20, "height": bb[3] + 140})
    cek(not E, "tanpa galat halaman %s" % E[:2])
    b.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
