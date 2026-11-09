# -*- coding: utf-8 -*-
"""STR biner Surpac dengan DESKRIPSI TEKS berpanjang bebas (tata letak berkas pit nyata, 9 Nov 2026):
   header 2 baris teks, 4 byte awalan nol, rekaman [0x00][int32 nomor string][Y][X][Z] + teks ",2" / ",Lensa A" / kosong,
   rekaman 29 byte nol = pemisah string, bantalan nol + "END".
   Pembaca lama menganggap deskripsi = 8 byte biner per kolom (rekaman tetap) -> koordinat bergeser / liar.
   Uji: berkas biner sintetis (koordinat fiktif) dibaca GCBL.readLinesS di kedua aplikasi dan harus menghasilkan titik yang
   IDENTIK dengan berkas STR teks berisi titik yang sama; juga varian lama (deskripsi biner tetap) harus tetap terbaca.
   Pemakaian: python tools/uji/uji_str_desc_teks.py"""
import base64, json, os, random, struct, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
random.seed(7)
PTS = []  # (sn, x, y, z, desc)
for j in range(12):
    sn = 1 + (j % 4)
    for i in range(25 + (j % 3)):
        x = 504800 + i * 7.5 + j * 1.3; y = 9011700 + j * 11.0 + (i % 4) * 0.25; z = 300 - j * 2.5
        desc = ["", ",2", ",9", ",Lensa A", ",2,abc def"][(i + j) % 5]
        PTS.append((sn, x, y, z, desc))
    PTS.append((0, 0, 0, 0, ""))

def biner_teks(path):
    b = b"pit_uji,09-Nov-26,,SSI_STYLES:styles.ssi\r\n0,           0.000,           0.000,           0.000,           0.000,           0.000,           0.000\r\n"
    b += b"\x00\x00\x00\x00"
    for sn, x, y, z, desc in PTS:
        b += b"\x00" + struct.pack(">I", sn) + struct.pack(">ddd", y, x, z) + desc.encode("ascii")
    path.write_bytes(b + b"\x00" * 57 + b"END\x00")

def biner_lama(path):  # deskripsi 1 kolom biner tetap (format yang dipakai uji_koordinat_rusak)
    b = b"pit_uji,09-Nov-26,,\n0,0.000,0.000,0.000,0.000,0.000,0.000\n"
    for sn, x, y, z, desc in PTS:
        b += bytes([1]) + struct.pack(">I", sn) + struct.pack(">ddd", y, x, z) + struct.pack(">d", 7.0)
    path.write_bytes(b + b"END")

def teks(path):
    L = ["pit_uji,09-Nov-26,,", "0,0.000,0.000,0.000,0.000,0.000,0.000"]
    for sn, x, y, z, desc in PTS: L.append("%d,%.3f,%.3f,%.3f%s" % (sn, y, x, z, desc))
    path.write_text("\n".join(L) + "\nEND\n", encoding="latin1")

TMP = Path(tempfile.mkdtemp()); biner_teks(TMP / "b_teks.str"); biner_lama(TMP / "b_lama.str"); teks(TMP / "t.str")
JS = """async function(a){var bin=atob(a[0]),u=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);var f=new File([u],a[1]);
  var S=[];await GCBL.readLinesS({k:'str',f:f},function(P){S.push(P);});
  return JSON.stringify(S.map(function(P){return [P.sn].concat(P.map(function(p){return p.map(function(v){return Math.round(v*1000)/1000;});}));}));}"""
gagal = []
for APP in ["app/index.html", "app-dh/index.html"]:
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / APP).read_bytes())
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1200, "height": 800})
        pg = ctx.new_page(); pg.goto(P); pg.wait_for_timeout(2500)
        out = {}
        for nm in ["t.str", "b_teks.str", "b_lama.str"]:
            out[nm] = pg.evaluate(JS, [base64.b64encode((TMP / nm).read_bytes()).decode(), nm])
        ctx.close()
    srv.terminate()
    n = len(json.loads(out["t.str"])); npts = sum(len(s) - 1 for s in json.loads(out["t.str"]))
    print(APP, "segmen", n, "titik", npts, "| biner-teks sama:", out["b_teks.str"] == out["t.str"], "| biner-lama sama:", out["b_lama.str"] == out["t.str"])
    if out["b_teks.str"] != out["t.str"]: gagal.append(APP + " biner deskripsi teks")
    if out["b_lama.str"] != out["t.str"]: gagal.append(APP + " biner deskripsi tetap (lama)")
    if npts != sum(1 for p in PTS if p[0]): gagal.append(APP + " jumlah titik teks %d" % npts)
print("\nGAGAL: " + ", ".join(gagal) if gagal else "\nLULUS")
