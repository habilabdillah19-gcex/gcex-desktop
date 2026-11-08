# -*- coding: utf-8 -*-
"""Drill Hole 0.24.42: jeda 3D, urutan Project Tree, menu kembar & ekspor ganda.

A/B: build lama (git, bawaan HEAD:app-dh/index.html) vs build baru (app-dh/index.html), data latihan sama.

Yang diukur:
  1. Jeda: sesudah Ore Geometry pernah dibuka, gambar ulang 3D (updatePlot) dan 3x klik Maju sayatan
     beruntun -- waktu JavaScript (sinkron) build baru harus jauh lebih kecil (< 40 % build lama).
  2. Lapisan yang memang berubah tetap di-update: ganti opasitas block model -> update GL berjalan
     (GLSKIP.run bertambah) dan opasitas di adegan sama dengan nilai baru.
  3. Membuka Ore Geometry tidak lagi menghitung intercept otomatis (build lama menghitung).
  4. Membuka ulang Geostatistik tanpa perubahan tidak menghitung ulang (GS.R objek yang sama).
  5. Urutan node atas: ... Struktur, Ore Geometry, Geomodeller, ..., Geostatistik, Block Model, Model
     Estimation, Validasi, Reporting, Layout. Langkah: og 5b, gs 7, bm 8, me 9, val 10, rep 11.
  6. Menu Database Bor tanpa kembaran kampanye / merge; Layout & Ekspor tanpa export database / .mdl
     (keduanya tetap ada di Database Bor / Block Model).
  7. Node versi block model: tab Topografi / Pit / Ortho Data Spasial tersembunyi; node Topografi: tampil.
  8. Tonase Reporting (batas pit fase 2) identik di kedua build.

Pemakaian: python tools/uji/uji_lag_tree_dh.py [--dasar=<ref git>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")

TUNGGU = "function(ms){return new Promise(function(r){setTimeout(r,ms);});}"

JS_JEDA = r"""
(async function () {
  var W = %s, o = {};
  PT.select('og'); await W(4000); o.ogR = !!OG.R;
  if (!OG.R) { try { ogRunIc(); } catch (e) {} await W(500); }   /* samakan keadaan: lapisan OG ada di kedua build */
  PT.select('db'); await W(800); updatePlot(); await W(3500);
  var t = performance.now(); updatePlot(); o.up = Math.round(performance.now() - t); await W(3500);
  t = performance.now(); stepPos(1); stepPos(1); stepPos(1); o.step3 = Math.round(performance.now() - t); await W(4500);
  o.skip = window.GLSKIP ? GLSKIP.skip : null;
  return o;
})()
""" % TUNGGU

JS_BENAR = r"""
(async function () {
  var W = %s, gd = document.getElementById('plotDiv');
  if (!window.GLSKIP) return {ada: false};
  var r0 = GLSKIP.run; BX.ui.op = 0.42; updatePlot(); await W(3000);
  var sc = gd._fullLayout.scene._scene, op = [];
  Object.keys(sc.traces).forEach(function (u) { var d = sc.traces[u].data; if (d && d.type === 'mesh3d' && /AU_GC/.test(d.name || '')) op.push(d.opacity); });
  BX.ui.op = 0.85; updatePlot(); await W(2500);
  return {ada: true, runNaik: GLSKIP.run - r0, opasitas: op};
})()
""" % TUNGGU

JS_GS = r"""
(async function () {
  var W = %s; PT.select('gs'); await W(2500); var R1 = GS.R;
  if (GS.open) gsToggle(); await W(600);
  var t = performance.now(); gsToggle(); await W(2500);
  return {sama: !!R1 && GS.R === R1, ms: Math.round(performance.now() - t)};
})()
""" % TUNGGU

JS_TREE = r"""
(async function () {
  var W = %s; PT.render(true);
  var top = PT.nodes.map(function (n) { return n.id + (n.step ? '[' + n.step + ']' : ''); });
  var L = PT.flatAll(PT.nodes), by = function (id) { return L.filter(function (n) { return n.id === id; })[0]; };
  var menu = function (id) { var n = by(id); try { return (n.menu() || []).filter(function (x) { return x.t; }).map(function (x) { return x.t; }); } catch (e) { return []; } };
  var out = (by('out') || {kids: []}).kids.map(function (k) { return k.id; });
  var bv = L.filter(function (n) { return /^bm\.v\./.test(n.id); })[0], tabsV = null, tabsT = null;
  var vis = function () { var u = document.querySelector('#pSP .uitabs'); return !!(u && u.offsetHeight > 0); };
  if (bv) { PT.select(bv.id); await W(700); tabsV = vis(); }
  PT.select('sp.topo'); await W(700); tabsT = vis();
  return {top: top, db: menu('db'), bm: menu('bm'), out: out, tabsVersiBM: tabsV, tabsTopografi: tabsT};
})()
""" % TUNGGU

JS_LAPOR = r"""
(function () {
  if (!(window.BX && BX.m) || typeof rpRun !== 'function') return {err: 'tidak ada BM / reporting'};
  var C = [];
  try { spL('pit').forEach(function (v) { if (v.tin) C.push({n: v.name, k: 'sp:pit:' + v.id}); }); } catch (e) {}
  (MD.models || []).forEach(function (m, i) { C.push({n: m.name, k: 'wf:' + i}); });
  var f2 = C.filter(function (c) { return /pit_fase2/.test(c.n); })[0]; if (!f2) return {err: 'pit fase 2 tidak ada'};
  var o = rpO(); o.dom = 'all'; o.cat = {}; o.surf = 'none'; o.poly = ''; o.z0 = ''; o.z1 = ''; o.cuts = '0'; o.grp = 'none'; o.show = false;
  RP.ovr = null; o.sx = [{k: f2.k, side: 'above'}]; rpRun();
  var R = RP.res, t = 0; Object.keys(R.rows[0].G).forEach(function (k) { t += R.rows[0].G[k].t; });
  o.sx = []; rpRun(); var R2 = RP.res, t2 = 0; Object.keys(R2.rows[0].G).forEach(function (k) { t2 += R2.rows[0].G[k].t; });
  return {diatasPit2: +t.toFixed(3), total: +t2.toFixed(3)};
})()
"""


def layani(html_bytes, nama):
    port = str(random.randint(9100, 9899))
    d = Path(tempfile.mkdtemp(prefix="gcex_lag_" + nama + "_"))
    (d / "index.html").write_bytes(html_bytes)
    os.symlink(DATA, d / "data-latihan")
    subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            urllib.request.urlopen("http://localhost:%s/index.html" % port, timeout=1); return port
        except Exception:
            time.sleep(0.4)
    raise SystemExit("peladen %s mati" % nama)


def boot(pg, port):
    pg.goto("http://localhost:%s/index.html" % port); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length>0", timeout=900000)
    pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(5000)
    return pg.evaluate("({hole: collars.length, blok: BX.m ? BX.m.n : 0})")


def main():
    from playwright.sync_api import sync_playwright
    lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=str(ROOT), capture_output=True).stdout
    baru = (ROOT / "app-dh" / "index.html").read_bytes()
    H, galat = {}, []
    with sync_playwright() as pw:
        for v, html in (("lama", lama), ("baru", baru)):
            port = layani(html, v)
            ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(),
                  args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
            ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
            pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
            pg.on("pageerror", lambda e, v=v: galat.append(v + ": " + str(e)[:200]))
            h = H[v] = {}
            h["boot"] = boot(pg, port); h["lapor"] = pg.evaluate(JS_LAPOR)
            h["jeda"] = pg.evaluate(JS_JEDA); h["benar"] = pg.evaluate(JS_BENAR)
            h["gs"] = pg.evaluate(JS_GS); h["tree"] = pg.evaluate(JS_TREE)
            ctx.close()
    for v in ("lama", "baru"):
        print("== %s" % v)
        for k in ("boot", "lapor", "jeda", "benar", "gs"): print("  %-6s %s" % (k, H[v][k]))
        T = H[v]["tree"]; print("  top    %s" % T["top"]); print("  db     %s" % T["db"]); print("  out    %s" % T["out"])
        print("  tab SP: versi BM %s | topografi %s" % (T["tabsVersiBM"], T["tabsTopografi"]))
    A, B, salah = H["lama"], H["baru"], []
    if B["boot"]["hole"] <= 0 or B["boot"]["blok"] <= 0: salah.append("boot baru gagal")
    if A["lapor"] != B["lapor"] or B["lapor"].get("err"): salah.append("tonase Reporting berubah")
    if not A["jeda"]["ogR"]: salah.append("build lama tidak menghitung OG otomatis -> uji 3 tidak membuktikan")
    if B["jeda"]["ogR"]: salah.append("build baru masih menghitung intercept otomatis saat OG dibuka")
    if not (B["jeda"]["up"] < 0.4 * A["jeda"]["up"]): salah.append("gambar ulang 3D tidak cukup cepat: %s vs %s ms" % (B["jeda"]["up"], A["jeda"]["up"]))
    if not (B["jeda"]["step3"] < 0.4 * A["jeda"]["step3"]): salah.append("3x Maju sayatan tidak cukup cepat: %s vs %s ms" % (B["jeda"]["step3"], A["jeda"]["step3"]))
    if not B["jeda"]["skip"]: salah.append("GLSKIP tidak pernah melewati update")
    Bn = B["benar"]
    if not Bn.get("ada") or Bn["runNaik"] <= 0 or not Bn["opasitas"] or any(abs(x - 0.42) > 1e-9 for x in Bn["opasitas"]):
        salah.append("lapisan yang berubah tidak ter-update dengan benar: %s" % Bn)
    if not B["gs"]["sama"]: salah.append("Geostatistik dihitung ulang padahal tidak ada perubahan")
    T = B["tree"]; ids = [x.split("[")[0] for x in T["top"]]
    want = ["proj", "sp", "wf", "db", "mp", "st", "og", "gm", "sl", "gs", "bm", "me", "val", "rep", "out", "set"]
    if [i for i in ids if i in want] != want: salah.append("urutan node atas salah: %s" % ids)
    for nid, st in (("og", "5b"), ("gs", "7"), ("bm", "8"), ("me", "9"), ("val", "10"), ("rep", "11")):
        if "%s[%s]" % (nid, st) not in T["top"]: salah.append("langkah %s bukan %s" % (nid, st))
    if any(x in T["db"] for x in ("Kampanye baru…", "Gabungkan kampanye… (merge)")): salah.append("menu kembar kampanye masih ada")
    if not any(x.startswith("Buat set merge") for x in T["db"]): salah.append("menu kampanye yang dipertahankan hilang")
    if "Export database (CSV)" not in T["db"]: salah.append("export database hilang dari Database Bor")
    if not any("Export block model GC (.mdl)" in x for x in T["bm"]): salah.append("export .mdl hilang dari Block Model")
    if "out.db" in T["out"] or "out.mdl" in T["out"]: salah.append("ekspor ganda masih di Layout & Ekspor: %s" % T["out"])
    if "out.db" not in A["tree"]["out"]: salah.append("build lama tidak punya ekspor ganda -> uji 6 tidak membuktikan")
    if T["tabsVersiBM"] is not False or T["tabsTopografi"] is not True: salah.append("tab Data Spasial untuk versi BM salah: %s / %s" % (T["tabsVersiBM"], T["tabsTopografi"]))
    if galat: print("galat halaman:", galat[:4])
    print("\n" + ("LULUS" if not salah else "GAGAL:\n  " + "\n  ".join(salah)))
    return 0 if not salah else 1


if __name__ == "__main__":
    raise SystemExit(main())
