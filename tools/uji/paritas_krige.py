# -*- coding: utf-8 -*-
"""Uji paritas: Ordinary Kriging versi Python (NumPy) harus SAMA dengan versi JavaScript.

Caranya sama dengan paritas_geostat.py: aplikasi GC-Ex Drill Hole sungguhan dibuka dengan data
latihan simulasi, variogram dijalankan & difit seperti biasa, lalu DI DALAM halaman itu sejumlah
blok uji diestimasi memakai fungsi JS yang dipakai produksi (okSearch + okKrige, pass demi pass
seperti okStep). Masukan dan hasilnya diambil, lalu masukan yang sama diestimasi oleh backend
Python dan dibandingkan BLOK PER BLOK: pass yang dipakai, jumlah sampel, kadar, kriging variance,
slope of regression, kriging efficiency, dan bobot negatif.

Dipakai karena angka inilah yang dipakai orang untuk menggali: pemindahan ke Python tidak boleh
menggeser satu pun dari angka itu.

Pemakaian:
    python tools/uji/paritas_krige.py [port] [--fixture] [--blok N] [--kecil RADIUS]
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from gcex_backend import krige  # noqa: E402

ARG = [a for a in sys.argv[1:] if not a.startswith("--")]
FIXTURE = "--fixture" in sys.argv
NBLOK = 300
KECIL = 0
for i, a in enumerate(sys.argv):
    if a == "--blok" and i + 1 < len(sys.argv):
        NBLOK = int(sys.argv[i + 1])
    if a == "--kecil" and i + 1 < len(sys.argv):
        KECIL = float(sys.argv[i + 1])
PORT = ARG[0] if ARG else "8763"
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


# Estimasi blok uji DI DALAM aplikasi, memakai fungsi produksi (bukan salinan).
JS = r"""
(function(nblok, kecil){
  var m = okModel(); if (!m) return {err: 'model variogram belum ada'};
  var bs = [5, 5, 2.5], nd = [3, 3, 2];
  var P = [{mult: 0.75, min: 4, max: 6, mph: 4},
           {mult: 1.5,  min: 4, max: 16, mph: 0},
           {mult: 2.5,  min: 2, max: 12, mph: 0}];
  var dd = okData(), C = dd.C, z = dd.z;
  if (C.length < 50) return {err: 'komposit terlalu sedikit: ' + C.length};
  /* mode kecil: komposit dibatasi satu kotak di tengah sebaran supaya berkas paritas yang
     dibekukan untuk pytest tetap kecil. Angkanya tetap angka JS asli atas masukan itu. */
  if (kecil) {
    var mx = 0, my = 0, mz = 0;
    C.forEach(function (c) { mx += c.x; my += c.y; mz += c.z; });
    mx /= C.length; my /= C.length; mz /= C.length;
    var r = kecil, C2 = [], z2 = [];
    for (var q = 0; q < C.length; q++) {
      if (Math.abs(C[q].x - mx) <= r && Math.abs(C[q].y - my) <= r && Math.abs(C[q].z - mz) <= r * 0.6) {
        C2.push(C[q]); z2.push(z[q]);
      }
    }
    if (C2.length < 200) return {err: 'kotak kecil hanya memuat ' + C2.length + ' komposit'};
    C = C2; z = z2;
  }
  var cell = Math.max(bs[0], bs[1], bs[2], m.R[0] * P[0].mult / 2);
  var I = okIndex(C, cell), D = okDisc(bs, nd), cbb = okCbb(m, D);
  var x0 = 1e18, x1 = -1e18, y0 = 1e18, y1 = -1e18, z0 = 1e18, z1 = -1e18;
  C.forEach(function (c) { x0 = Math.min(x0, c.x); x1 = Math.max(x1, c.x); y0 = Math.min(y0, c.y);
                           y1 = Math.max(y1, c.y); z0 = Math.min(z0, c.z); z1 = Math.max(z1, c.z); });
  /* blok uji: grid di tengah sebaran data supaya ada yang kena pass 1, 2, 3, dan ada yang gagal.
     Di mode kecil kotak komposit ikut mengecil, jadi grid dilebarkan 2,2x supaya blok di tepi
     tetap jatuh ke pass 2, pass 3, dan ada yang gagal -- ketiga jalur tetap teruji. */
  if (kecil) {
    var fx = (x1 - x0) * 0.6, fy = (y1 - y0) * 0.6, fz = (z1 - z0) * 0.6;
    x0 -= fx; x1 += fx; y0 -= fy; y1 += fy; z0 -= fz; z1 += fz;
  }
  var n1 = Math.ceil(Math.pow(nblok, 1 / 3)), list = [];
  for (var i = 0; i < n1; i++) for (var j = 0; j < n1; j++) for (var k = 0; k < n1; k++) {
    list.push([x0 + (x1 - x0) * (i + 0.5) / n1, y0 + (y1 - y0) * (j + 0.5) / n1, z0 + (z1 - z0) * (k + 0.5) / n1]);
  }
  var t0 = performance.now(), out = [];
  list.forEach(function (b, bi) {
    for (var p = 0; p < P.length; p++) {
      var sel = okSearch(m, I, C, b[0], b[1], b[2], P[p].mult, P[p].max, P[p].mph);
      if (sel.length < P[p].min) continue;
      var r = okKrige(m, C, z, sel, b[0], b[1], b[2], D, cbb);
      if (!r) continue;
      out.push({i: bi, est: r.est, kv: r.kv, sor: r.sor, ke: r.ke, ns: sel.length, ps: p + 1, neg: r.neg});
      return;
    }
  });
  return {
    m: {vM: m.vM, vS: m.vS, vN: m.vN, c0: m.c0, cs: m.cs, A: m.A, B: m.B, Cn: m.Cn, R: m.R},
    C: C.map(function (c) { return {x: c.x, y: c.y, z: c.z, id: c.id}; }), z: z,
    blocks: list, passes: P, bs: bs, nd: nd, cell: cell, cbb: cbb, out: out,
    ms: Math.round(performance.now() - t0), el: GS.R.el, label: GS.R.label
  };
})
"""


def ambil(nblok: int, kecil: float = 0.0) -> dict:
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
            tempfile.mkdtemp(prefix="gcex_krige_"),
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
        # sayatan sejajar bidang vein + variogram & fitting seperti bab tutorial
        pg.evaluate(r"""(function(){
          var cx = 505050, cy = 9012000, az = (135 - 90) * Math.PI / 180;
          $('sMode').value = 'P';
          $('p1e').value = (cx - 130 * Math.sin(az)).toFixed(1); $('p1n').value = (cy - 130 * Math.cos(az)).toFixed(1);
          $('p2e').value = (cx + 130 * Math.sin(az)).toFixed(1); $('p2n').value = (cy + 130 * Math.cos(az)).toFixed(1);
          $('dipS').value = 70; $('dipN').value = 70; modeChanged();
          $('pos').value = 0; $('thick').value = 40; $('sliceClip').checked = true; updatePlot();
        })()""")
        pg.wait_for_timeout(1200)
        pg.evaluate("if(!GS.open)gsToggle(); gsRun();")
        pg.wait_for_timeout(4000)
        print("  mengestimasi blok uji dengan fungsi JS...", flush=True)
        d = pg.evaluate("(%s)(%d,%g)" % (JS, nblok, kecil))
        if d is None or d.get("err"):
            raise SystemExit("gagal: %s" % (d or {}).get("err", "tidak ada hasil"))
        d["galatHalaman"] = galat
        ctx.close()
    return d


def main() -> int:
    print("Mengambil masukan & hasil JS dari aplikasi sungguhan...", flush=True)
    d = ambil(NBLOK, KECIL)
    print("  %s | unsur %s | %d komposit | %d blok uji" % (d["label"], d["el"], len(d["C"]), len(d["blocks"])), flush=True)
    print("  JS: %d ms untuk %d blok terestimasi (%.3f ms/blok)"
          % (d["ms"], len(d["out"]), d["ms"] / max(1, len(d["out"]))), flush=True)

    t0 = time.perf_counter()
    o = krige.run({"C": d["C"], "z": d["z"], "m": d["m"], "blocks": d["blocks"],
                   "passes": d["passes"], "bs": d["bs"], "nd": d["nd"], "cell": d["cell"]})
    ms = int((time.perf_counter() - t0) * 1000)
    print("  Python: %d ms untuk %d blok terestimasi (%.3f ms/blok; total panggilan %d ms)"
          % (o["ms"], o["n"], o["ms"] / max(1, o["n"]), ms), flush=True)
    print("  cbb JS %.12g | Python %.12g" % (d["cbb"], o["cbb"]), flush=True)

    salah = []
    py = {i: k for k, i in enumerate(o["i"])}
    js = {r["i"]: r for r in d["out"]}
    if set(py) != set(js):
        hanya_js = sorted(set(js) - set(py))[:5]
        hanya_py = sorted(set(py) - set(js))[:5]
        salah.append("blok yang berhasil beda: hanya JS %s, hanya Python %s" % (hanya_js, hanya_py))
    for i in sorted(set(py) & set(js)):
        k = py[i]
        r = js[i]
        if r["ps"] != o["ps"][k]:
            salah.append("blok %d: pass beda (JS %d, Python %d)" % (i, r["ps"], o["ps"][k]))
        if r["ns"] != o["ns"][k]:
            salah.append("blok %d: jumlah sampel beda (JS %d, Python %d)" % (i, r["ns"], o["ns"][k]))
        for nama, kunci in (("kadar", "est"), ("kriging variance", "kv"), ("SoR", "sor"),
                            ("KE", "ke"), ("bobot negatif", "neg")):
            a, b = float(r[kunci]), float(o[kunci][k])
            if abs(a - b) > 1e-9 + 1e-9 * max(abs(a), abs(b)):
                salah.append("blok %d: %s beda (JS %.12g, Python %.12g)" % (i, nama, a, b))

    print()
    print("Blok terestimasi: JS %d, Python %d dari %d kandidat" % (len(js), o["n"], len(d["blocks"])))
    print("Sebaran pass JS    :", [sum(1 for r in d["out"] if r["ps"] == p) for p in (1, 2, 3)])
    print("Sebaran pass Python:", o["cnt"])
    if d["galatHalaman"]:
        print("Galat halaman:", d["galatHalaman"][:3])

    if FIXTURE and not salah:
        fx = ROOT / "backend" / "tests" / "data" / "krige_js.json"
        fx.parent.mkdir(parents=True, exist_ok=True)
        beku = {k: d[k] for k in ("m", "C", "z", "blocks", "passes", "bs", "nd", "cell", "cbb", "out", "el", "label")}
        beku["catatan"] = ("Masukan & keluaran JS asli (okSearch + okKrige) dari aplikasi GC-Ex Drill Hole pada "
                           "data latihan; dipakai backend/tests/test_krige.py agar hasil Python tidak bergeser.")
        fx.write_text(json.dumps(beku, separators=(",", ":")), encoding="utf-8")
        print("Berkas paritas ditulis: %s (%.0f KB)" % (fx.relative_to(ROOT), fx.stat().st_size / 1024))

    print()
    if salah:
        print("TIDAK SAMA (%d temuan, 20 pertama):" % len(salah))
        for s in salah[:20]:
            print("  -", s)
        return 1
    print("SAMA: pass, jumlah sampel, kadar, KV, SoR, KE, dan bobot negatif cocok di seluruh blok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
