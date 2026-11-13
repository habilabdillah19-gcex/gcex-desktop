# -*- coding: utf-8 -*-
"""Reporting Block Model > Pit & progres > Progres topo-ke-topo (Block Model): topografi atas / bawah bisa dipilih LANGSUNG DARI FILE
(laporan pemilik 9 Nov 2026: pilihan hanya "Topografi aktif" / "Desain pit aktif").
Uji: muat data latihan BM, buka panel, pilih file CSV topografi yang diturunkan 15 m (dibuat dari SIM_topo_xyz_nov.csv; puncak model latihan berada
>= 6,3 m di bawah topografi, sehingga topo nov asli memberi 0 blok) sebagai topografi BAWAH lewat jendela pilih file, topografi aktif
sebagai ATAS, hitung -> harus ada blok tergali (> 0) dan lebih kecil dari seluruh model; file yang sama untuk atas & bawah -> 0 blok.
0.24.75: file itu menjadi node Data Referensi bertanda survei (tersimpan di proyek) dan hitungan memakai titik aslinya. Pemakaian: python tools/uji/uji_rppit_file.py"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app/index.html").read_bytes()); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
TMP = Path(tempfile.mkdtemp()); L = (DATA / "SIM_topo_xyz_nov.csv").read_text(encoding="latin1").splitlines()
out = [L[0]]
for ln in L[1:]:
    a = ln.split(",")
    if len(a) >= 3:
        try: a[2] = "%.2f" % (float(a[2]) - 15.0)
        except ValueError: pass
    out.append(",".join(a))
(TMP / "topo_turun15.csv").write_text("\n".join(out) + "\n", encoding="latin1")
HASIL = "(function(){var X=RPX.res;if(!X)return null;var r=X.rows[0].res;return {atas:X.atas,bawah:X.bawah,n:r.nb,raw:JSON.stringify(r).slice(0,200)};})()"
gagal = []
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    pg.evaluate("RPX.open();RPX.set('mode','tt')"); pg.wait_for_timeout(800)
    opsi0 = pg.evaluate("Array.from(document.querySelectorAll('#rpBody select')).map(function(s){return Array.from(s.options).map(function(o){return o.textContent;});})")
    print("opsi awal:", opsi0[:2])
    ada_tombol = pg.evaluate("!!Array.from(document.querySelectorAll('#rpBody button')).filter(function(b){return /Pilih file topografi/.test(b.textContent);}).length")
    if not ada_tombol: gagal.append("tombol Pilih file topografi tidak ada")
    with pg.expect_file_chooser() as fc:
        pg.evaluate("RPX.pilihFile('tb')")
    fc.value.set_files(str(TMP / "topo_turun15.csv")); pg.wait_for_timeout(4000)
    st = pg.evaluate("JSON.stringify({ta:RPX.ta,tb:RPX.tb,surf:RPX.surf.map(function(q){return [q.name,q.x.length];}),msg:RPX.msg})")
    print("sesudah pilih file:", st)
    # 0.24.75: file topografi Reporting menjadi node Data Referensi (bertanda survei) -> sumber 'wf:<indeks>'
    tb = pg.evaluate("RPX.tb"); sv = pg.evaluate("(function(){var m=MD.models[+String(RPX.tb).slice(3)];return m?[m.name,!!m.survei,m.pts?m.pts.x.length:0]:null;})()")
    print("node survei:", sv)
    if not (str(tb).startswith("wf:") and sv and sv[1] and sv[2] > 0): gagal.append("tb tidak terpasang ke node survei Data Referensi")
    pg.evaluate("RPX.set('ta','ov:topo');RPX.run()"); pg.wait_for_function("!RPX.busy && RPX.res", timeout=300000); pg.wait_for_timeout(500)
    h1 = pg.evaluate(HASIL); print("hasil topo aktif -> file turun 15 m:", h1)
    ntot = pg.evaluate("BX.m.n")
    if not h1 or not (h1["n"] and 0 < h1["n"] < ntot): gagal.append("blok tergali tidak masuk akal: %s (total %s)" % (h1, ntot))
    if not h1 or "survei" not in str(h1.get("bawah")): gagal.append("sumber bawah bukan titik survei asli: %s" % (h1 and h1.get("bawah")))
    pg.evaluate("RPX.set('ta',RPX.tb);RPX.run()"); pg.wait_for_function("!RPX.busy", timeout=300000); pg.wait_for_timeout(500)
    h2 = pg.evaluate("RPX.msg"); print("file yang sama untuk atas & bawah ->", h2[:120])
    if "sama" not in h2: gagal.append("atas = bawah seharusnya ditolak dengan pesan: %s" % h2)
    ctx.close()
srv.terminate()
print("\nGAGAL: " + "; ".join(gagal) if gagal else "\nLULUS")
