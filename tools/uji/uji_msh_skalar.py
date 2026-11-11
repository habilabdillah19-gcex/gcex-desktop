# -*- coding: utf-8 -*-
"""Mesh Leapfrog (.msh ARANZ) dengan kolom nilai per titik tanpa jumlah komponen ("Thickness_Value Double 8;")
dulu ditolak "indeks segitiga di luar jumlah titik" (DH 0.24.67 / BM 0.24.66 memperbaiki readMsh). Kubus sintetis 10 m.
Pemakaian: python tools/uji/uji_msh_skalar.py"""
import os, random, struct, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; T = Path(tempfile.mkdtemp())
V = [(x, y, z) for z in (0, 10) for y in (0, 10) for x in (0, 10)]; V = [(500000 + x, 9000000 + y, 100 + z) for x, y, z in V]
F = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4), (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
hd = b"%ARANZ-1.0\n\n[index]\nLocation Double 3 8;\nThickness_Value Double 8;\nTri Integer 3 12;\n\n[binary]"
body = struct.pack('<I', 0x00f00fff) + struct.pack('<d', 1.23456789) + b''.join(struct.pack('<3d', *v) for v in V) + struct.pack('<8d', *([1.5] * 8)) + b''.join(struct.pack('<3i', *f) for f in F)
(T / "kubus_skalar.msh").write_bytes(hd + body)
gagal = []
for app in ["app-dh/index.html", "app/index.html"]:
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / app).read_bytes())
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(); pg.goto(P); pg.wait_for_timeout(1500)
        pg.evaluate("(function(){var i=document.createElement('input');i.type='file';i.id='mIn';document.body.appendChild(i);})()")
        pg.set_input_files('#mIn', str(T / "kubus_skalar.msh"))
        r = pg.evaluate("(async function(){try{var f=document.getElementById('mIn').files[0];var L=await SA.readMeshes([f]);var m=L[0];var s=0;for(var t=0;t<m.nt;t++){var a=m.t[t*3],b=m.t[t*3+1],c=m.t[t*3+2],V=m.v;s+=(V[a*3]*(V[b*3+1]*V[c*3+2]-V[b*3+2]*V[c*3+1])-V[a*3+1]*(V[b*3]*V[c*3+2]-V[b*3+2]*V[c*3])+V[a*3+2]*(V[b*3]*V[c*3+1]-V[b*3+1]*V[c*3]))/6;}return {nv:m.nv,nt:m.nt,x0:m.v[0],vol:Math.abs(s)};}catch(e){return {err:String(e)};}})()")
        b.close()
    srv.terminate(); ok = r.get("nv") == 8 and r.get("nt") == 12 and abs(r.get("vol", 0) - 1000) < 1e-3
    print(("  ok   " if ok else "  GAGAL ") + app + " " + str(r))
    if not ok: gagal.append(app)
print("\nGAGAL: " + ", ".join(gagal) if gagal else "\nLULUS")
