# -*- coding: utf-8 -*-
"""Block Model 0.24.43 / Drillhole 0.24.50: file spasial berkoordinat rusak tidak lagi membuat layar kosong.
Kasus (dibuat di folder sementara, koordinat fiktif di area SIM_BM_GC_kadar.csv):
  topo_d1.str  STR BINER Surpac dengan 1 kolom deskripsi (rekaman 37 byte). Pembaca lama (29 byte) membacanya bergeser
               -> koordinat ±1e+250…1e+307 -> offX/offY proyek ikut liar -> tampak kosong.
  pit_rusak.str STR teks berisi 2 titik liar (1e+307) di antara titik normal -> titik liar dibuang & dilaporkan.
A/B: build lama (git <dasar>) vs baru, import layar Mulai: SIM_BM_GC_kadar.csv + kedua file di atas.
Yang diukur: offX/offY (harus ±area 504000 / 9011000), jumlah titik topografi terbaca & di dalam area BM, info file.
Pemakaian: python tools/uji/uji_koordinat_rusak.py [--dasar=<ref git>] [--app=app/index.html]"""
import json, os, random, struct, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")
APP = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--app=")), "app/index.html")
TMP = Path(tempfile.mkdtemp())

def str_biner(path, n_desc):
    b = b"topo_latihan,08-Nov-26,,ssi_styles:styles.ssi\n0,0.000,0.000,0.000,0.000,0.000,0.000\n"
    k = 0
    for j in range(40):                                  # 40 garis kontur, 30 titik per garis
        for i in range(30):
            x = 504700 + i * 24.0; y = 9011720 + j * 14.0; z = 300 - j * 2.0 + (i % 5)
            b += bytes([1]) + struct.pack(">I", 1 + j) + struct.pack(">ddd", y, x, z) + struct.pack(">d", 7.0) * n_desc
            k += 1
        b += bytes([1]) + struct.pack(">I", 0) + struct.pack(">ddd", 0, 0, 0) + struct.pack(">d", 0) * n_desc
    path.write_bytes(b + b"END"); return k

def str_teks(path):
    L = ["pit_latihan,08-Nov-26,,", "0,0.000,0.000,0.000,0.000,0.000,0.000"]
    for j in range(10):
        for i in range(20):
            L.append("%d,%.3f,%.3f,%.3f" % (1, 9011750 + j * 50.0, 504750 + i * 30.0, 280 - j))
        if j == 4: L.append("1,1e+307,-2.5e+307,250.000"); L.append("1,-3.1e+307,1e+307,250.000")
        L.append("0,0.000,0.000,0.000")
    path.write_text("\n".join(L) + "\nEND\n", encoding="latin1")

NT = str_biner(TMP / "topo_d1.str", 1); str_teks(TMP / "pit_rusak.str")
JS = r"""(function(){var tp=(window.topoData||[]).filter(Boolean),pp=(window.pitData||[]).filter(Boolean),inA=function(p){return p[0]>504600&&p[0]<505500&&p[1]>9011600&&p[1]<9012400;};
  var info={};['topo','pit'].forEach(function(r){(SA.sp[r]||[]).forEach(function(s){info[s.f.name]=s.info||'';});});
  return {offX:offX,offY:offY,nTopo:tp.length,topoDiArea:tp.filter(inA).length,nPit:pp.length,pitLiar:pp.filter(function(p){return Math.abs(p[0])>1e8||Math.abs(p[1])>1e8;}).length,nBlok:(window.BX&&BX.m)?BX.m.n:0,info:info};})()"""

def jalan(html):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes(html)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=undefined;")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
        pg.goto(P); pg.wait_for_timeout(1500)
        if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(500)
        pg.evaluate("if(window.JLR&&JLR.pilih){JLR.pilih('lanjut');JLR.acuanPend('bm',true);}")  # DH: jalur proyek (0.24.73)
        if pg.query_selector("input[onchange*='SA.bmPick']"): pg.set_input_files("input[onchange*='SA.bmPick']", str(DATA / "SIM_BM_GC_kadar.csv"))
        pg.set_input_files("input[onchange*=\"SA.addSp('topo'\"]", str(TMP / "topo_d1.str"))
        pg.set_input_files("input[onchange*=\"SA.addSp('pit'\"]", str(TMP / "pit_rusak.str")); pg.wait_for_timeout(800)
        pg.evaluate("var e=document.getElementById('dsName');if(e)e.value='Uji_koordinat'")
        pg.click('#btnGo'); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(3000)
        r = pg.evaluate(JS); ctx.close()
    srv.terminate(); return r

lama = subprocess.run(["git", "show", "%s:%s" % (DASAR, APP)], cwd=ROOT, capture_output=True).stdout
A = jalan(lama); B = jalan((ROOT / APP).read_bytes())
print(APP, "topo titik dibuat:", NT); print("lama:", json.dumps(A, ensure_ascii=False)); print("baru:", json.dumps(B, ensure_ascii=False))
salah = []
if abs(A["offX"]) < 1e8: salah.append("build lama tidak tergeser -> uji tidak membuktikan")
if not (500000 <= B["offX"] <= 505000 and 9010000 <= B["offY"] <= 9012000): salah.append("offX/offY baru tidak di area data: %s %s" % (B["offX"], B["offY"]))
# jumlah TERBACA ada di info ("N titik → M"; M = sesudah penyederhanaan garis), semua titik tersimpan harus di area data
if ("%d titik" % NT) not in B["info"].get("topo_d1.str", "") or B["topoDiArea"] != B["nTopo"] or not B["nTopo"]:
    salah.append("titik topografi STR biner ber-deskripsi tidak terbaca benar: %s" % B)
if B["pitLiar"] or "200 titik" not in B["info"].get("pit_rusak.str", ""): salah.append("titik pit liar tidak dibuang / titik normal hilang: %s" % B)
if "rusak dibuang" not in B["info"].get("pit_rusak.str", ""): salah.append("info pit tidak melaporkan titik rusak: %s" % B["info"])
if "BlockModel" not in APP and "app-dh" not in APP and B["nBlok"] != A["nBlok"]: salah.append("jumlah blok berubah")
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
