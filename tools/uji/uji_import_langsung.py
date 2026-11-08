# -*- coding: utf-8 -*-
"""BM 0.24.45 / DH 0.24.52: ⋯ Block Model -> "Import block model dari file…" membuka jendela pilih file dulu, lalu dialog
pemetaan terisi file itu; ⋯ Database Bor / Collar / … (DH) -> "Import <tabel> dari file…" membuka jendela pilih file lalu
jendela upsert dengan file terpasang, dan Gabungkan benar-benar menambah data.
Diukur (data latihan DH; BM: SIM_BM_GC_kadar.csv): layar Mulai tidak terbuka (BM) / jendela upsert yang terbuka dengan
slot collar terisi (DH); nama file terpasang; sesudah Gabungkan jumlah collar bertambah 32 (SIM_split_collar.csv)."""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
def serve(app):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / app).read_bytes()); os.symlink(DATA, d / "data-latihan")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    return srv, P
def ctx_new(pw):
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;"); return ctx
def menu_file(pg, node, teks, berkas):
    pg.evaluate("PT.render(true)"); pg.locator("#ptree .ptr[data-id='%s'] .ptx" % node).click(); pg.wait_for_timeout(300)
    with pg.expect_file_chooser() as fc: pg.locator("#ptMenu button", has_text=teks).first.click()
    fc.value.set_files(str(DATA / berkas)); pg.wait_for_timeout(2500)
H = {}; salah = []
with sync_playwright() as pw:
    # ---- Block Model
    srv, P = serve("app/index.html"); ctx = ctx_new(pw); pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept())
    pg.goto(P); pg.wait_for_timeout(1500)
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(500)
    pg.set_input_files("input[onchange*='SA.bmPick']", str(DATA / "SIM_BM_GC_kadar.csv")); pg.evaluate("document.getElementById('dsName').value='Uji_bm'")
    pg.click('#btnGo'); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(2500)
    menu_file(pg, "bm", "Import block model dari file", "SIM_BM_GC_estimasi.csv")
    H["bm"] = pg.evaluate("""(function(){var d=document.getElementById('bxDlg');return {mulaiTutup:document.getElementById('imp').classList.contains('off'),dlg:!!d&&d.style.display==='flex',
      map:(document.getElementById('bxMap')||{}).innerText||'',go:!(document.getElementById('bxGo')||{}).disabled};})()""")
    ctx.close(); srv.terminate()
    # ---- Drill Hole
    srv, P = serve("app-dh/index.html"); ctx = ctx_new(pw); pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
    n0 = pg.evaluate("collars.length")
    menu_file(pg, "bm", "Import block model dari file", "SIM_BM_GC_estimasi.csv")
    H["dhbm"] = pg.evaluate("(function(){var d=document.getElementById('bxDlg');return {dlg:!!d&&d.style.display==='flex',go:!(document.getElementById('bxGo')||{}).disabled};})()")
    pg.evaluate("bxDlgClose()"); pg.evaluate("PT.open['db']=1;PT.render(true)")
    menu_file(pg, "db.collar", "Import collar dari file", "SIM_split_collar.csv")
    H["dh"] = pg.evaluate("""(function(){var imp=document.getElementById('imp');return {ups:imp.classList.contains('ups')&&!imp.classList.contains('off'),
      slot:(document.getElementById('sfcollar')||{}).innerText||'',lain:['survey','assay','geo'].map(function(r){return (document.getElementById('sf'+r)||{}).innerText||'';}),n0:collars.length,tombol:!!document.getElementById('btnUps')};})()""")
    pg.click("#btnUps"); pg.wait_for_timeout(6000); pg.wait_for_function("window.collars && collars.length>0 && !document.getElementById('imp').classList.contains('ups')", timeout=120000); pg.wait_for_timeout(2000)
    H["dh2"] = {"n": pg.evaluate("collars.length"), "n0": n0, "ada": pg.evaluate("collars.some(function(c){return c[0]==='SPL-01-1';})")}
    ctx.close(); srv.terminate()
for k, v in H.items(): print(k, json.dumps(v, ensure_ascii=False)[:400])
b = H["bm"]
if not (b["mulaiTutup"] and b["dlg"] and "AU_GC" in b["map"] and b["go"]): salah.append("BM: dialog block model tidak terbuka dengan file terisi: %s" % b)
if not (H["dhbm"]["dlg"] and H["dhbm"]["go"]): salah.append("DH: dialog block model tidak terbuka dengan file terisi")
d = H["dh"]
if not (d["ups"] and "SIM_split_collar.csv" in d["slot"] and all("belum ada file" in x for x in d["lain"]) and d["tombol"]): salah.append("DH: jendela upsert tidak terbuka dengan collar terpasang: %s" % d)
if not (H["dh2"]["n"] == n0 + 32 and H["dh2"]["ada"]): salah.append("DH: Gabungkan tidak menambah 32 collar: %s" % H["dh2"])
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
