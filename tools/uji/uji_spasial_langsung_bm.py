# -*- coding: utf-8 -*-
"""Block Model 0.24.44: Data Spasial diimport langsung dari menu ⋯ Project Tree (tanpa kembali ke layar Mulai).
Alur sungguhan: layar Mulai hanya SIM_BM_GC_kadar.csv -> klik ⋯ Data Spasial -> "Topografi…" -> jendela pilih file
(SIM_topo_akhir_juni.dxf) -> ⋯ Desain pit -> "Import desain pit…" (SIM_pit_fase1.dxf) -> ⋯ Topografi -> "Ganti topografi…"
(SIM_topo_akhir_juli.dxf). Diukur: layar Mulai tetap tertutup, overlay topo/pit terisi & tercentang, titik di area BM,
blok tidak berubah, data tersimpan di proyek (IndexedDB) dan muncul lagi setelah halaman dimuat ulang + proyek dibuka.
Pemakaian: python tools/uji/uji_spasial_langsung_bm.py"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes())
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
ST = r"""(function(){var inA=function(p){return p&&p[0]>504500&&p[0]<505600&&p[1]>9011500&&p[1]<9012500;};var t=(window.topoData||[]).filter(Boolean),q=(window.pitData||[]).filter(Boolean);
 return {mulaiTutup:document.getElementById('imp').classList.contains('off'),topo:t.length,topoArea:t.filter(inA).length,pit:q.length,ovTopo:OV.topoF.x.filter(function(v){return v!==null;}).length,
  ovPit:OV.pitF.x.filter(function(v){return v!==null;}).length,zSum:+t.reduce(function(a,p){return a+p[2];},0).toFixed(1),cTopo:document.getElementById('ovTopoS').checked,cPit:document.getElementById('ovPit').checked,blok:BX.m?BX.m.n:0,proj:SA.pname};})()"""
H = {}; salah = []; alerts = []
def menu_klik(pg, node, teks, berkas):
    pg.evaluate("PT.open['sp']=1;PT.render(true)"); pg.locator("#ptree .ptr[data-id='%s'] .ptx" % node).click(); pg.wait_for_timeout(300)
    with pg.expect_file_chooser() as fc: pg.locator("#ptMenu button", has_text=teks).first.click()
    fc.value.set_files(str(DATA / berkas))
    n0 = len(alerts); t0 = time.time()
    while len(alerts) <= n0 and time.time() - t0 < 120: pg.wait_for_timeout(300)   # alert hasil import (ditangani di handler dialog)
    if len(alerts) <= n0: raise RuntimeError("tidak ada alert hasil import untuk %s" % berkas)
    pg.wait_for_timeout(1200)
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;window._alertN=0;")
    pg = ctx.new_page()
    def dlg(x):
        if x.type == "alert": alerts.append(x.message)
        x.accept(x.default_value) if x.type == "prompt" else x.accept()
    pg.on("dialog", dlg)
    pg.goto(P); pg.wait_for_timeout(1500)
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(500)
    pg.set_input_files("input[onchange*='SA.bmPick']", str(DATA / "SIM_BM_GC_kadar.csv")); pg.evaluate("document.getElementById('dsName').value='Uji_spasial'")
    pg.click('#btnGo'); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(2500)
    H["awal"] = pg.evaluate(ST)
    menu_klik(pg, "sp", "Topografi (STR", "SIM_topo_akhir_juni.dxf"); H["topo"] = pg.evaluate(ST)
    menu_klik(pg, "sp.pit", "Import desain pit", "SIM_pit_fase1.dxf"); H["pit"] = pg.evaluate(ST)
    menu_klik(pg, "sp.topo", "Ganti topografi", "SIM_topo_akhir_juli.dxf"); H["ganti"] = pg.evaluate(ST)
    pg.evaluate("SA.saveWork()"); pg.wait_for_timeout(1500)
    H["idb"] = pg.evaluate("""(async function(){var r=await window._fpH.idbGet('proj:'+SA.pname);return r?{topo:(r.data.topoData||[]).filter(Boolean).length,pit:(r.data.pitData||[]).filter(Boolean).length}:null;})()""")
    ctx.close()
srv.terminate()
for k, v in H.items(): print(k, json.dumps(v))
print("alert:", json.dumps(alerts, ensure_ascii=False))
a, t, p, g = H["awal"], H["topo"], H["pit"], H["ganti"]
if a["topo"] or a["pit"]: salah.append("awal mestinya tanpa topo/pit")
for k in ("topo", "pit", "ganti"):
    if not H[k]["mulaiTutup"]: salah.append(k + ": layar Mulai terbuka lagi")
    if H[k]["blok"] != a["blok"]: salah.append(k + ": jumlah blok berubah")
if not (t["topo"] > 100 and t["topoArea"] == t["topo"] and t["ovTopo"] > 100 and t["cTopo"]): salah.append("topografi tidak masuk / tidak tampil: %s" % t)
if not (p["pit"] > 10 and p["ovPit"] > 10 and p["cPit"] and p["topo"] == t["topo"]): salah.append("desain pit tidak masuk / topografi ikut berubah: %s" % p)
# kedua file topo sama-sama 28.000 titik -> bedakan lewat jumlah elevasi; "ganti" tidak boleh menggandakan jumlah titik
if not (g["topo"] == t["topo"] and g["zSum"] != t["zSum"] and g["pit"] == p["pit"]): salah.append("ganti topografi tidak mengganti (atau menggandakan / pit ikut berubah): %s vs %s" % (g, t))
if not H["idb"] or H["idb"]["topo"] != g["topo"] or H["idb"]["pit"] != g["pit"]: salah.append("proyek tersimpan tidak memuat data baru: %s" % H["idb"])
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
