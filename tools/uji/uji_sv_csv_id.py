"""Uji BM 0.24.88 — pembaca CSV titik atap Solid Vein (SV.bacaCsv), CSV tanpa judul `ID,X,Y,Z,kode` (data sintetis).
  C1 nomor titik >= 1000 (penomoran survey berjalan): X / Y / Z tetap dari kolom 2 / 3 / 4 (dulu X = nomor titik).
  C2 nomor titik kecil, C3 tanpa kolom nomor (X,Y,Z), C4 berjudul, C5 Easting bulat tanpa nomor titik: tidak berubah.
Pemakaian: python tools/uji/uji_sv_csv_id.py [app/index.html]   (build 0.24.87 harus GAGAL)"""
from __future__ import annotations
import json, random, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app" / "index.html"
PORT = random.randint(8900, 8990)
JS = r"""function(){var mk=function(id0,dec,kol){var s='';for(var i=0;i<60;i++){var x=(505000+i*1.5).toFixed(dec),y=(9012000+i*2.25).toFixed(dec),z=(250+i*0.01).toFixed(2);s+=(kol==='xyz'?'':(id0+i)+',')+x+','+y+','+z+(kol==='xyz'?'':',204')+'\n';}return s;};
  var t=function(txt){var Q=SV.bacaCsv(txt),a=Q[0],b=Q[Q.length-1];return {n:Q.length,x:[a.x,b.x],y:[a.y,b.y],z:[a.z,b.z],id:a.id,c:a.c};};
  return {c1:t(mk(1500,3)),c1b:t(mk(250000,3)),c2:t(mk(1,3)),c3:t(mk(0,3,'xyz')),c4:t('ID,X,Y,Z,KODE\n'+mk(1500,3)),c5:t(mk(0,0,'xyz'))};}"""
def main() -> int:
    from playwright.sync_api import sync_playwright
    d = Path(tempfile.mkdtemp()); shutil.copy(HTML, d / "index.html"); (d / "data-latihan").symlink_to(ROOT / "docs" / "tutorial-gcex" / "data")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2); gagal = []
    def cek(ok, msg):
        print(("  ok   " if ok else "  GAGAL ") + msg)
        if not ok: gagal.append(msg)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page()
            pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_function("window.SV && SV.bacaCsv", timeout=60000)
            r = pg.evaluate("(%s)()" % JS); b.close()
    finally:
        srv.terminate()
    print(json.dumps(r)[:700])
    benar = lambda v: v["n"] == 60 and v["x"] == [505000, 505088.5] and v["y"] == [9012000, 9012132.75] and abs(v["z"][0] - 250) < 1e-9
    cek(benar(r["c1"]) and r["c1"]["id"] == "1500" and r["c1"]["c"] == "204", "C1 nomor titik 1500+: X/Y/Z dari kolom yang benar, ID & kode terbaca")
    cek(benar(r["c1b"]), "C1 nomor titik 250000+ (lebih besar dari Easting)")
    cek(benar(r["c2"]) and r["c2"]["id"] == "1", "C2 nomor titik kecil: tidak berubah")
    cek(benar(r["c3"]), "C3 tanpa kolom nomor (X,Y,Z)")
    cek(benar(r["c4"]) and r["c4"]["id"] == "1500", "C4 berjudul ID,X,Y,Z,KODE")
    cek(r["c5"]["n"] == 60 and r["c5"]["x"][0] == 505000 and r["c5"]["y"][0] == 9012000, "C5 X,Y,Z dengan Easting bulat: tidak dianggap nomor titik")
    print("GAGAL (%d)" % len(gagal) if gagal else "LULUS"); return 1 if gagal else 0
if __name__ == "__main__":
    sys.exit(main())
