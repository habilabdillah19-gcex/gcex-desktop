# -*- coding: utf-8 -*-
"""Uji paritas: variogram & fitting versi Python (NumPy) harus SAMA dengan versi JavaScript.

Jalannya: aplikasi GC-Ex Drill Hole yang sungguhan dibuka di browser dengan data latihan
simulasi, panel Geostatistik dijalankan seperti biasa (gsRun), lalu DUA hal diambil dari
halaman itu:
  1. masukan apa adanya -- komposit yang dipakai, nilai yang sudah ditransformasi, parameter
     lag/toleransi, sumbu bidang sayatan, dan sill;
  2. keluaran JS -- variogram eksperimental 36 arah + omni + downhole, beserta model hasil
     auto-fit (pitch, nugget, sill tiap struktur, range mayor/semi/downhole).
Masukan yang sama lalu dihitung oleh backend Python, dan hasilnya dibandingkan lag per lag.

Dipakai karena pemindahan perhitungan ke Python tidak boleh mengubah angka: angka variogram
data latihan sudah tercetak di buku tutorial (nugget 0,648, range mayor 108,5 m, dst.).

Pemakaian:
    python tools/uji/paritas_geostat.py [port]
Butuh: playwright + chromium, folder data latihan di sebelah index.html (lihat --siapkan).
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
from gcex_backend import geostat  # noqa: E402

ARG = [a for a in sys.argv[1:] if not a.startswith("--")]
FIXTURE = "--fixture" in sys.argv
PORT = ARG[0] if ARG else "8766"
SRV = ROOT / "tools" / "uji" / "_srv_dh"
DATA = ROOT / "docs" / "tutorial-gcex" / "data"


def siapkan() -> None:
    """Folder penyajian: index.html hasil build + data-latihan (agar jalur 'web' modul dipakai)."""
    SRV.mkdir(parents=True, exist_ok=True)
    (SRV / "index.html").write_bytes((ROOT / "app-dh" / "index.html").read_bytes())
    tautan = SRV / "data-latihan"
    if tautan.is_symlink() or tautan.exists():
        if tautan.is_symlink():
            tautan.unlink()
    if not tautan.exists():
        os.symlink(DATA, tautan)


AMBIL = r"""
(function(){
  var R = GS.R; if(!R || !R.E || !R.M) return null;
  var P = R.P, zv = gsTrans(R.vc, P.tr), Cv = R.C;
  var mx = Math.max(50, parseInt(document.getElementById('gMax').value) || 5000);
  if (R.C.length > mx) {                      /* sama dengan gsRun: subsample berjarak tetap */
    var st = R.C.length / mx, Cs = [], zs = [];
    for (var q = 0; q < mx; q++) { var ix = Math.floor(q * st); Cs.push(R.C[ix]); zs.push(zv[ix]); }
    Cv = Cs; zv = zs;
  }
  var ringkas = function (A) { return A.map(function (e) { return [e.h, e.g, e.n]; }); };
  return {
    C: Cv.map(function (c) { return { x: c.x, y: c.y, z: c.z, id: c.id, d: c.d }; }),
    z: zv, P: { lag: P.lag, nl: P.nl, lt: P.lt, at: P.at, bw: P.bw, dlag: P.dlag, dnl: P.dnl,
                minP: P.minP, ns: P.ns, B: P.B, BD: P.BD },
    u: R.S.g.u, w: R.S.g.w, sill: R.sill, ms: R.ms, label: R.label, el: R.el, nComp: R.C.length,
    E: { D: R.E.D.map(ringkas), O: ringkas(R.E.O), DH: ringkas(R.E.DH) },
    M: { pitch: R.M.pitch, c0: R.M.c0, c: R.M.c, a: R.M.a, b: R.M.b, d: R.M.d, fan: R.M.fan || R.fan }
  };
})()
"""


def ambil_dari_aplikasi() -> dict:
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
            tempfile.mkdtemp(prefix="gcex_paritas_"),
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
        print("  data: %s lubang, %s assay" % (pg.evaluate("collars.length"), pg.evaluate("assays.length")), flush=True)

        # sayatan sejajar bidang vein + domain vein, seperti bab "Filter domain & statistik"
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
        data = pg.evaluate(AMBIL)
        if data is None:
            raise SystemExit("gsRun tidak menghasilkan variogram (komposit terlalu sedikit?)")
        data["galatHalaman"] = galat
        ctx.close()
    return data


def banding(nama: str, js, py, rtol=1e-9, atol=1e-9) -> list:
    """Bandingkan daftar [h, g, n] JS dengan daftar {h,g,n} Python."""
    salah = []
    if len(js) != len(py):
        return ["%s: jumlah lag beda (JS %d, Python %d)" % (nama, len(js), len(py))]
    for i, (a, b) in enumerate(zip(js, py)):
        if int(a[2]) != int(b["n"]):
            salah.append("%s lag %d: jumlah pasangan beda (JS %d, Python %d)" % (nama, i + 1, a[2], b["n"]))
        for k, v in (("h", a[0]), ("g", a[1])):
            p = b[k]
            if abs(v - p) > atol + rtol * max(abs(v), abs(p)):
                salah.append("%s lag %d: %s beda (JS %.12g, Python %.12g)" % (nama, i + 1, k, v, p))
    return salah


def main() -> int:
    print("Mengambil masukan & hasil JS dari aplikasi sungguhan...", flush=True)
    d = ambil_dari_aplikasi()
    print("  %s | unsur %s | %d komposit (dipakai %d)" % (d["label"], d["el"], d["nComp"], len(d["C"])), flush=True)
    print("  JS: %d ms" % d["ms"], flush=True)

    t0 = time.perf_counter()
    out = geostat.run({"C": d["C"], "z": d["z"], "P": d["P"], "u": d["u"], "w": d["w"],
                       "sill": d["sill"], "fit": True})
    ms = int((time.perf_counter() - t0) * 1000)
    print("  Python: %d ms variogram + %d ms fitting (%s pasangan)"
          % (out["ms"], out.get("msFit", 0), format(out["npair"], ",d").replace(",", ".")), flush=True)

    salah = []
    salah += banding("omni", d["E"]["O"], out["E"]["O"])
    salah += banding("downhole", d["E"]["DH"], out["E"]["DH"])
    for j in range(36):
        salah += banding("arah %d deg" % (j * 5), d["E"]["D"][j], out["E"]["D"][j])

    M, Mp = d["M"], out.get("M") or {}
    def cek(nama, a, b, tol=1e-6):
        if a is None or b is None:
            salah.append("model %s: salah satu kosong (JS %r, Python %r)" % (nama, a, b))
        elif abs(float(a) - float(b)) > tol + 1e-9 * max(abs(float(a)), abs(float(b))):
            salah.append("model %s beda (JS %.10g, Python %.10g)" % (nama, a, b))
    cek("pitch", M["pitch"], Mp.get("pitch"), 0)
    cek("nugget c0", M["c0"], Mp.get("c0"))
    for i in (0, 1):
        cek("sill struktur %d" % (i + 1), M["c"][i], (Mp.get("c") or [None, None])[i])
        cek("range mayor %d" % (i + 1), M["a"][i], (Mp.get("a") or [None, None])[i])
        cek("range semi %d" % (i + 1), M["b"][i], (Mp.get("b") or [None, None])[i])
        cek("range downhole %d" % (i + 1), M["d"][i], (Mp.get("d") or [None, None])[i])

    print()
    print("Model JS     : pitch %s, nugget %.4f, C %s, a %s, b %s, d %s"
          % (M["pitch"], M["c0"], [round(x, 4) for x in M["c"]], [round(x, 2) for x in M["a"]],
             [round(x, 2) for x in M["b"]], [round(x, 2) for x in M["d"]]))
    print("Model Python : pitch %s, nugget %.4f, C %s, a %s, b %s, d %s"
          % (Mp.get("pitch"), Mp.get("c0", float("nan")), [round(x, 4) for x in Mp.get("c", [])],
             [round(x, 2) for x in Mp.get("a", [])], [round(x, 2) for x in Mp.get("b", [])],
             [round(x, 2) for x in Mp.get("d", [])]))
    if FIXTURE and not salah:
        fx = ROOT / "backend" / "tests" / "data" / "geostat_js.json"
        fx.parent.mkdir(parents=True, exist_ok=True)
        beku = {k: d[k] for k in ("C", "z", "P", "u", "w", "sill", "E", "M", "label", "el", "nComp")}
        beku["catatan"] = ("Masukan & keluaran JS asli dari aplikasi GC-Ex Drill Hole pada data latihan "
                           "simulasi; dipakai backend/tests/test_geostat.py agar hasil Python tidak pernah "
                           "bergeser dari angka JS. Dibuat oleh tools/uji/paritas_geostat.py --fixture.")
        fx.write_text(json.dumps(beku, separators=(",", ":")), encoding="utf-8")
        print("Berkas paritas ditulis: %s (%.0f KB)" % (fx.relative_to(ROOT), fx.stat().st_size / 1024))

    print()
    if d["galatHalaman"]:
        print("Galat halaman:", d["galatHalaman"][:3])
    if salah:
        print("TIDAK SAMA (%d temuan, 20 pertama):" % len(salah))
        for s in salah[:20]:
            print("  -", s)
        return 1
    print("SAMA: 36 arah + omni + downhole + seluruh parameter model cocok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
