# -*- coding: utf-8 -*-
"""Uji paritas: sub-blocking & proporsi volume ore (sb_frac) versi Python harus SAMA dengan JS.

Caranya sama dengan paritas_geostat.py dan paritas_krige.py: aplikasi GC-Ex Drill Hole sungguhan
dibuka dengan data latihan simulasi, Demo dijalankan sampai langkah "Model vein HW / FW -> solid"
supaya solid domain benar-benar terbangun seperti yang dilakukan pemakai, lalu DI DALAM halaman itu
fungsi produksi SB.frac() dijalankan atas block model yang aktif. Mesh solid, daftar blok, dan
atribut sb_frac hasil JS diambil; masukan yang sama dihitung backend Python dan dibandingkan
BLOK PER BLOK.

Dipakai karena sb_frac menentukan tonase blok perbatasan -- angka dilusi dan ore loss. Pemindahan
ke Python tidak boleh menggeser satu pun proporsi.

Pemakaian:
    python tools/uji/paritas_subblok.py [port] [--fixture] [--blok N]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from gcex_backend import subblok  # noqa: E402

# nilai yang mengikuti --blok bukan nomor port
_pakai = {i + 1 for i, a in enumerate(sys.argv) if a in ("--blok", "--res")}
ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--") and i not in _pakai]
FIXTURE = "--fixture" in sys.argv
NBLOK = 0          # 0 = semua blok model
RES = 0            # >0 = resolusi mesh solid dikasarkan (dipakai agar berkas paritas kecil)
for i, a in enumerate(sys.argv):
    if a == "--blok" and i + 1 < len(sys.argv):
        NBLOK = int(sys.argv[i + 1])
    if a == "--res" and i + 1 < len(sys.argv):
        RES = float(sys.argv[i + 1])
PORT = ARG[0] if ARG else "8764"
SRV = ROOT / "tools" / "uji" / "_srv_dh"
DATA = ROOT / "docs" / "tutorial-gcex" / "data"


def siapkan() -> None:
    SRV.mkdir(parents=True, exist_ok=True)
    (SRV / "index.html").write_bytes((ROOT / "app-dh" / "index.html").read_bytes())
    t = SRV / "data-latihan"
    if t.is_symlink():
        t.unlink()
    if not t.exists():
        os.symlink(DATA, t)


# Mesh solid + blok + sb_frac diambil memakai fungsi produksi (bukan salinan).
JS = r"""
(function(nblok){
  if (typeof SB === 'undefined' || !SB.frac) return {err: 'modul sub-blocking tidak ada'};
  if (!window.BX || !BX.m) return {err: 'belum ada block model aktif'};
  /* solid domain: disusun sama seperti solids() di subblk_dh.js */
  var L = (window.gmTops ? gmTops() : (window.GM ? GM.doms : [])) || [], W = [];
  L.forEach(function (d) {
    var R = (typeof meGrpR === 'function') ? meGrpR(d) : null;
    if (!R || !R.mesh) return;
    mdLocal(R.mesh);
    var ms = R.mesh;
    W.push({name: d.name, bb: meBBox(ms),
            mesh: {x: Array.prototype.slice.call(ms._x), y: Array.prototype.slice.call(ms._y),
                   z: Array.prototype.slice.call(ms._z), i: Array.prototype.slice.call(ms._i),
                   j: Array.prototype.slice.call(ms._j), k: Array.prototype.slice.call(ms._k)}});
  });
  if (!W.length) return {err: 'belum ada solid domain terbangun'};

  var m = BX.m, n = m.n;
  var t0 = performance.now();
  var fr = SB.frac(10, true);                       /* <-- fungsi produksi */
  var ms = Math.round(performance.now() - t0);
  var F = m.num['sb_frac'];
  if (!F) return {err: 'sb_frac tidak terbentuk'};

  /* blok dikirim dalam koordinat LOKAL, sama dengan yang dipakai straddle() di JS */
  var pakai = [], step = (nblok && nblok < n) ? Math.ceil(n / nblok) : 1, i;
  for (i = 0; i < n; i += step) pakai.push(i);
  var B = {x: [], y: [], z: [], sx: [], sy: [], sz: []}, FJ = [];
  pakai.forEach(function (i) {
    B.x.push(m.x[i] - offX); B.y.push(m.y[i] - offY); B.z.push(m.z[i]);
    B.sx.push(m.sx[i]); B.sy.push(m.sy[i]); B.sz.push(m.sz[i]);
    FJ.push(F[i]);
  });
  var vol = 0;
  for (i = 0; i < n; i++) vol += m.sx[i] * m.sy[i] * m.sz[i] * F[i];
  return {solids: W, blocks: B, F: FJ, nPart: fr.nPart, nFull: fr.nFull, nNol: fr.nNol,
          N: fr.N, vol: vol, nAll: n, ms: ms, nDom: W.length};
})
"""


def ambil(nblok: int) -> dict:
    from playwright.sync_api import sync_playwright

    siapkan()
    url = "http://localhost:%s/index.html" % PORT
    try:
        urllib.request.urlopen(url, timeout=2)
    except Exception:
        subprocess.Popen([sys.executable, "-m", "http.server", PORT], cwd=str(SRV),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            tempfile.mkdtemp(prefix="gcex_sb_"),
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
            viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page()
        galat = []
        pg.on("pageerror", lambda e: galat.append(str(e)[:200]))
        pg.on("dialog", lambda d: d.accept())
        pg.goto(url)
        pg.wait_for_timeout(1500)
        pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
        print("  memuat data latihan...", flush=True)
        pg.evaluate("document.getElementById('dlatBtn').click()")
        pg.wait_for_function("window.collars && collars.length > 0", timeout=600000)
        pg.wait_for_function("!DLAT.busy", timeout=600000)
        pg.wait_for_timeout(3000)

        # Solid domain dibangun lewat fungsi produksi, urutan sama dengan bab tutorial:
        # wireframe vein di-flag ke domain -> model implisit (RBF) dinyalakan -> mesh dibangun.
        print("  flag wireframe vein & membangun solid (RBF)...", flush=True)
        r = pg.evaluate(r"""(function(res){
          try {
            var ada = -1;
            for (var i = 0; i < MD.models.length; i++) if (/QV_Lensa2/i.test(MD.models[i].name)) ada = i;
            if (ada < 0) return {err: 'wireframe vein QV_Lensa2 tidak ada di data latihan'};
            WF.mi = ada; gmWfFlag();
            var d = GM.doms[GM.doms.length - 1];
            if (!d) return {err: 'domain tidak terbentuk dari flag wireframe'};
            GM.act = d.id; imSet('on', true);
            if (res > 0) imSet('res', res);   /* mesh lebih kasar: berkas paritas jadi kecil */
            imSync(true);
            return {dom: d.name, wf: MD.models[ada].name, nt: MD.models[ada].nt};
          } catch (e) { return {err: String(e).slice(0, 200)}; }
        })(%g)""" % RES)
        if r.get("err"):
            raise SystemExit("gagal membangun solid: %s" % r["err"])
        print("    domain %s dari wireframe %s (%d segitiga)" % (r["dom"], r["wf"], r["nt"]), flush=True)
        pg.wait_for_function(
            "(function(){var L=(window.gmTops?gmTops():[]);return L.some(function(d){"
            "var R=(typeof meGrpR==='function')?meGrpR(d):null;return R&&R.mesh;});})()",
            timeout=900000)
        pg.wait_for_timeout(2000)

        print("  menghitung sb_frac dengan fungsi JS...", flush=True)
        d = pg.evaluate("(%s)(%d)" % (JS, nblok))
        if d is None or d.get("err"):
            raise SystemExit("gagal: %s" % (d or {}).get("err", "tidak ada hasil"))
        d["galatHalaman"] = galat
        ctx.close()
    return d


def bandingkan(d: dict) -> list:
    o = subblok.run({"solids": d["solids"], "blocks": d["blocks"], "mode": "frac",
                     "nF": d["N"], "workers": "auto"})
    salah = []
    FJ = np.asarray(d["F"], dtype=np.float64)
    FP = np.asarray(o["F"], dtype=np.float64)
    if FJ.size != FP.size:
        return ["jumlah blok beda: JS %d, Python %d" % (FJ.size, FP.size)]
    # sb_frac JS disimpan Float32Array, jadi pembandingnya setara presisi float32
    beda = np.abs(FJ - FP)
    tol = 1e-6 + 1e-6 * np.maximum(np.abs(FJ), np.abs(FP))
    buruk = np.flatnonzero(beda > tol)
    print("  Python: %d ms | blok dibandingkan %d | beda maksimum %.3g"
          % (o["ms"], FJ.size, float(beda.max()) if beda.size else 0.0), flush=True)
    if NBLOK == 0:
        print("  utuh JS %d / Python %d | perbatasan JS %d / Python %d | di luar JS %d / Python %d"
              % (d["nFull"], o["nFull"], d["nPart"], o["nPart"], d["nNol"], o["nNol"]), flush=True)
    else:
        print("  cuplikan %d blok dari %d: jumlah utuh / perbatasan / di luar hanya dibandingkan "
              "bila seluruh blok dipakai (--blok 0)" % (FJ.size, d["nAll"]), flush=True)
    for i in buruk[:20]:
        salah.append("blok %d: sb_frac beda (JS %.9g, Python %.9g)" % (i, FJ[i], FP[i]))
    if buruk.size > 20:
        salah.append("... dan %d blok lain" % (buruk.size - 20))
    if NBLOK == 0:
        for nama, a, b in (("blok utuh", d["nFull"], o["nFull"]),
                           ("blok perbatasan", d["nPart"], o["nPart"]),
                           ("blok di luar", d["nNol"], o["nNol"])):
            if a != b:
                salah.append("jumlah %s beda (JS %d, Python %d)" % (nama, a, b))
        if abs(d["vol"] - o["vol"]) > 1e-3 + 1e-9 * abs(d["vol"]):
            salah.append("volume ore berbobot beda (JS %.6f, Python %.6f)" % (d["vol"], o["vol"]))
    return salah


def main() -> int:
    print("Mengambil mesh solid, blok & sb_frac dari aplikasi sungguhan...", flush=True)
    d = ambil(NBLOK)
    nt = sum(len(s["mesh"]["i"]) for s in d["solids"])
    print("  %d solid domain | %d segitiga | %d blok model | cuplikan %d^3 titik"
          % (d["nDom"], nt, d["nAll"], d["N"]), flush=True)
    print("  JS: %d ms (%d utuh, %d perbatasan, %d di luar)"
          % (d["ms"], d["nFull"], d["nPart"], d["nNol"]), flush=True)

    salah = bandingkan(d)
    if d["galatHalaman"]:
        print("Galat halaman:", d["galatHalaman"][:3])

    if FIXTURE and not salah:
        fx = ROOT / "backend" / "tests" / "data" / "subblok_js.json"
        fx.parent.mkdir(parents=True, exist_ok=True)
        beku = {k: d[k] for k in ("solids", "blocks", "F", "N", "nAll")}
        # cacah di bawah ini milik SELURUH model (66 ribu blok), sedangkan "blocks"/"F" bisa
        # berupa cuplikan: disimpan terpisah supaya tidak tertukar saat diuji.
        beku["penuh"] = {"nPart": d["nPart"], "nFull": d["nFull"], "nNol": d["nNol"],
                         "vol": d["vol"], "cuplikan": FIXTURE and NBLOK != 0}
        beku["catatan"] = ("Mesh solid, blok, dan atribut sb_frac asli dari aplikasi GC-Ex Drill Hole "
                           "(SB.frac) pada data latihan; dipakai backend/tests/test_subblok.py agar "
                           "hasil Python tidak bergeser.")
        fx.write_text(json.dumps(beku, separators=(",", ":")), encoding="utf-8")
        print("Berkas paritas ditulis: %s (%.0f KB)" % (fx.relative_to(ROOT), fx.stat().st_size / 1024))

    print()
    if salah:
        print("TIDAK SAMA (%d temuan):" % len(salah))
        for s in salah[:20]:
            print("  -", s)
        return 1
    print("SAMA: proporsi sb_frac tiap blok, jumlah blok utuh / perbatasan / di luar, "
          "dan volume ore berbobot cocok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
