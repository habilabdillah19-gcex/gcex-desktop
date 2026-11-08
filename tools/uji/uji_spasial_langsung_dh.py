# -*- coding: utf-8 -*-
"""Drillhole 0.24.51: menu ⋯ Data Spasial / Topografi / Desain pit / Orthofoto membuka jendela pilih file dan menambah
VERSI baru di tempat (spAdd), tidak kembali ke layar Mulai. Data latihan -> ⋯ Data Spasial > "Tambah versi topografi dari file…"
(SIM_topo_akhir_juli.dxf) -> ⋯ Desain pit > "Tambah versi desain pit dari file…" (SIM_pit_fase2.dxf).
Diukur: layar Mulai tetap tertutup, jumlah versi topo & pit +1, sub-node versi baru muncul di Project Tree, jumlah hole tetap."""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes()); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
ST = r"""(function(){PT.render(true);var L=PT.flatAll(PT.nodes);return {mulaiTutup:document.getElementById('imp').classList.contains('off'),
  topoV:L.filter(function(n){return /^sp\.topo\./.test(n.id)&&!n.addRow;}).length,pitV:L.filter(function(n){return /^sp\.pit\./.test(n.id)&&!n.addRow;}).length,
  nTopo:(spL?spL('topo'):[]).length,nPit:(spL?spL('pit'):[]).length,hole:collars.length};})()"""
H = {}; salah = []
def menu_klik(pg, node, teks, berkas):
    pg.evaluate("PT.open['sp']=1;PT.render(true)"); pg.locator("#ptree .ptr[data-id='%s'] .ptx" % node).click(); pg.wait_for_timeout(300)
    with pg.expect_file_chooser() as fc: pg.locator("#ptMenu button", has_text=teks).first.click()
    fc.value.set_files(str(DATA / berkas)); pg.wait_for_function("!(window.SPV&&SPV.busy)", timeout=120000); pg.wait_for_timeout(2500)
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
    H["awal"] = pg.evaluate(ST)
    menu_klik(pg, "sp", "Tambah versi topografi", "SIM_topo_akhir_juli.dxf"); H["topo"] = pg.evaluate(ST)
    menu_klik(pg, "sp.pit", "Tambah versi desain pit", "SIM_pit_fase2.dxf"); H["pit"] = pg.evaluate(ST)
    ctx.close()
srv.terminate()
for k, v in H.items(): print(k, json.dumps(v))
a, t, p = H["awal"], H["topo"], H["pit"]
for k in ("topo", "pit"):
    if not H[k]["mulaiTutup"]: salah.append(k + ": layar Mulai terbuka lagi")
    if H[k]["hole"] != a["hole"]: salah.append(k + ": jumlah hole berubah")
if not (t["nTopo"] == a["nTopo"] + 1 and t["topoV"] == a["topoV"] + 1): salah.append("versi topografi tidak bertambah satu: %s -> %s" % (a, t))
if not (p["nPit"] == a["nPit"] + 1 and p["pitV"] == a["pitV"] + 1 and p["nTopo"] == t["nTopo"]): salah.append("versi desain pit tidak bertambah satu: %s -> %s" % (t, p))
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
