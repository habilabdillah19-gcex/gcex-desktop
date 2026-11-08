# -*- coding: utf-8 -*-
"""Drill Hole 0.24.49: kolom No tabel titik struktur. A/B: build lama (git <dasar>) vs baru.
Kasus: SIM_struktur.csv (tanpa kolom ID; ada Northing) -> No harus 1, 2, 3 …; berkas ber-kolom No / ID / Point / Kode
harus tetap memakai nilai kolom itu; dip, dip azimuth, X, Y tidak berubah.
Pemakaian: python tools/uji/uji_struktur_no.py [--dasar=<ref git>]"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")
KASUS = {"sim": (DATA / "SIM_struktur.csv").read_text(encoding="utf-8"),
         "no": "No,Easting,Northing,RL,Dip,Dip_Azimuth\nS-01,504670.69,9011678.77,324.77,75.2,133.6\nS-02,504685.62,9011692.13,324.62,68.2,132.1\n",
         "id": "ID;X;Y;Z;Dip;DipDir\nA7;504670.69;9011678.77;324.77;75.2;133.6\n",
         "point": "Point,East,North,Elevasi,Dip,Azimuth\nP1,504670.69,9011678.77,324.77,75.2,133.6\n",
         "kode": "Kode,X,Y,Z,Dip,Dip_Azimuth,Keterangan\nK-9,504670.69,9011678.77,324.77,75.2,133.6,Sesar\n"}
JS = r"""(function(K){var out={};Object.keys(K).forEach(function(k){var a=STR.P.length;stParse(K[k],k+'.csv');out[k]=STR.P.slice(a).slice(0,3).map(function(p){return [p.no,+p.x.toFixed(2),+p.y.toFixed(2),p.dip,p.az];});});return out;})"""

def jalan(html):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes(html); os.symlink(DATA, d / "data-latihan")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1400, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept()); pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(1500)
        r = pg.evaluate(JS + "(%s)" % json.dumps(KASUS)); ctx.close()
    srv.terminate(); return r

lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=ROOT, capture_output=True).stdout
A = jalan(lama); B = jalan((ROOT / "app-dh/index.html").read_bytes())
for k in KASUS: print(k, "\n  lama:", A[k], "\n  baru:", B[k])
salah = []
if not str(A["sim"][0][0]).startswith("9011"): salah.append("build lama tidak menunjukkan No = Northing -> uji tidak membuktikan")
if [r[0] for r in B["sim"]] != ["1", "2", "3"]: salah.append("SIM_struktur.csv: No bukan 1, 2, 3: %s" % B["sim"])
harap = {"no": ["S-01", "S-02"], "id": ["A7"], "point": ["P1"], "kode": ["K-9"]}
for k, v in harap.items():
    if [r[0] for r in B[k]] != v: salah.append("%s: No mestinya %s, dapat %s" % (k, v, B[k]))
for k in KASUS:
    if [r[1:] for r in A[k]] != [r[1:] for r in B[k]]: salah.append("%s: koordinat / dip / azimuth berubah" % k)
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
