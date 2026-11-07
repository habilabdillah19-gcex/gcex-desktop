# -*- coding: utf-8 -*-
"""Uji laporan titik LANTAI as-mined + menu "Buka daftar poligon as-mined flitch ini".

A/B: build lama (git, bawaan HEAD) vs build baru (app/index.html), data latihan & susunan sama.

Yang diukur (akibat, bukan keberadaan):
  1. Tonase as-mined IDENTIK di kedua build untuk setiap skenario (patch hanya menambah laporan).
  2. Panel Lantai build baru MENAMPILKAN peringatan yang terlihat (tidak di dalam <details> tertutup,
     kotaknya ber-ukuran) pada tiga kasus yang dulu diam:
       a. semua titik lantai di luar pita  -> "Tidak satu pun titik lantai"
       c. titik di pita tetapi jauh dari poligon -> "poligon punya < 3 titik"
       b. atap di bawah lantai (jepit)     -> "atapnya berada di bawah"
     dan TIDAK menampilkan peringatan apa pun pada kasus d (titik benar).
  3. Menu flitch -> node terpilih = reg.1 (pemilik panel Register), bukan tetap di node flitch.

Pemakaian: python tools/uji/uji_lantai_laporan.py [--dasar=<ref git>]
"""
import json, os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")

JS_SIAPKAN = r"""
(function () {
  var m = BX.m, zc = {}, i;
  for (i = 0; i < m.n; i++) { var k = Math.round(m.z[i] * 100); zc[k] = (zc[k] || 0) + 1; }
  var zb = null, nb = -1;
  Object.keys(zc).forEach(function (k) { if (zc[k] > nb) { nb = zc[k]; zb = +k / 100; } });
  var xs = [], ys = [];
  for (i = 0; i < m.n; i++) if (Math.abs(m.z[i] - zb) < 1e-6) { xs.push(m.x[i]); ys.push(m.y[i]); }
  xs.sort(function (a, b) { return a - b; }); ys.sort(function (a, b) { return a - b; });
  var cx = xs[xs.length >> 1], cy = ys[ys.length >> 1], sz = m.sz[0] || 2.5;
  var L = lyU(); L.top = zb + sz / 2; L.bot = zb - sz / 2; L.flMode = 'comp'; L.onlyPass = false; L.calcM = 'clip';
  var U = BX.ui; U.sg = 2.6; U.sgCol = ''; U.sgZero = ''; U.sgRep = ''; U.wOn = false;
  if (window.LY) LY.ix = null;
  var pts = [[cx - 40, cy - 30], [cx + 35, cy - 35], [cx + 40, cy + 30], [cx - 35, cy + 35]];
  amD().bnd = [{id: 'ujifl', name: 'UJI_FLOOR', pts: pts, top: L.top, bot: L.bot, on: true,
                d: 'ORE', no: 1, print: true}];
  return {cx: cx, cy: cy, top: L.top, bot: L.bot};
})
"""

# skenario: dz lantai relatif RL bawah, geser XY lantai (m), atap (null = nominal) relatif RL bawah
JS_SKENARIO = r"""
(function (S, sk) {
  var D = amD(), R = amR();
  D.pts = []; D.ptsR = [];
  for (var a = -40; a <= 40; a += 5) for (var b = -35; b <= 35; b += 5) {
    D.pts.push({x: S.cx + a + sk.geser, y: S.cy + b, z: S.bot + sk.fl, id: '', c: 'FLOOR'});
    if (sk.rf !== null) D.ptsR.push({x: S.cx + a, y: S.cy + b, z: S.bot + sk.rf, id: '', c: 'ROOF'});
  }
  R.floor = 'pickup';
  if (typeof amRoofMode === 'function') R.roof = sk.rf === null ? 'flitch' : 'flat';
  BX.sc = {}; AM.res = {}; AM.msg = ''; AM.jepit = null;
  amRun(true);
  var B = lyBench(), E = AM.res[lyFmt(B[0]) + '_' + lyFmt(B[1])];
  try { uiTab('AM'); PT.goSub('AM', 'Poligon'); } catch (e) {}
  amPanel();
  var box = document.getElementById('amFloorBox'), warn = [];
  if (box) [].forEach.call(box.querySelectorAll('.warn'), function (w) {
    var d = w.closest('details'); if (d && !d.open) return;
    var r = w.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return;
    warn.push(w.textContent.replace(/\s+/g, ' ').trim());
  });
  return {t: E && E.sum ? E.sum.t : null, vol: E && E.sum ? E.sum.vol : null,
          jepit: AM.jepit ? AM.jepit.a : 0, warn: warn, adaBox: !!box};
})
"""

JS_MENU = r"""
(function () {
  PT.render && PT.render();
  var L = PT.flatAll(PT.nodes || []), g = null;
  L.forEach(function (n) { if (!g && /^fl\./.test(n.id || '') && n.ic === 'flitch' && n.id !== 'fl.list' && n.menu) g = n; });
  if (!g) return {err: 'node flitch tidak ditemukan', ids: L.map(function (n) { return n.id; }).filter(function (i) { return /^fl/.test(i || ''); })};
  var M = g.menu(), it = M[1];
  try { uiTab('BM'); PT.select(g.id); } catch (e) {}
  var sebelum = PT.sel;
  window._selLog=[];var _s=PT.select;PT.select=function(id){window._selLog.push(id+'@'+(Date.now()%100000)+' '+String(new Error().stack).split('\n').slice(2,4).join(' | ').slice(0,160));return _s.apply(this,arguments);};
  it.fn();
  return {node: g.id, label: it.t, sebelum: sebelum};
})
"""

SK = {"a_luar_pita": {"fl": -5.0, "geser": 0, "rf": None},
      "c_jauh_poligon": {"fl": 0.3, "geser": 200, "rf": None},
      "b_atap_tembus": {"fl": 1.4, "geser": 0, "rf": 1.1},
      "d_benar": {"fl": 0.3, "geser": 0, "rf": None}}
HARAP = {"a_luar_pita": "Tidak satu pun titik lantai", "c_jauh_poligon": "poligon punya",
         "b_atap_tembus": "atapnya berada di bawah", "d_benar": None}


def layani(html_bytes, nama):
    port = str(random.randint(9100, 9899))
    d = Path(tempfile.mkdtemp(prefix="gcex_fl_" + nama + "_"))
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


def jalankan(pg, port):
    pg.goto("http://localhost:%s/index.html" % port); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n > 0", timeout=600000)
    pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(2000)
    S = pg.evaluate("(%s)()" % JS_SIAPKAN)
    out = {}
    for k, v in SK.items():
        out[k] = pg.evaluate("(%s)(%s,%s)" % (JS_SKENARIO, json.dumps(S), json.dumps(v)))
    out["menu"] = pg.evaluate("(%s)()" % JS_MENU)
    jejak = []
    for _ in range(12):
        pg.wait_for_timeout(150); jejak.append(pg.evaluate("PT.sel"))
    out["menu"]["jejak"] = jejak
    out["menu"]["adaReg1"] = pg.evaluate("!!PT.flatAll(PT.nodes||[]).filter(function(n){return n.id==='reg.1';}).length")
    out["menu"]["sesudah"] = jejak[-1]; out["menu"]["log"]=pg.evaluate("window._selLog")
    return out


def main():
    from playwright.sync_api import sync_playwright
    lama = subprocess.run(["git", "show", "%s:app/index.html" % DASAR], cwd=str(ROOT), capture_output=True).stdout
    baru = (ROOT / "app" / "index.html").read_bytes()
    pl, pb = layani(lama, "lama"), layani(baru, "baru")
    H, galat = {}, []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(),
              args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.on("pageerror", lambda e: galat.append(str(e)[:200]))
        H["lama"] = jalankan(pg, pl); H["baru"] = jalankan(pg, pb)
        ctx.close()
    salah = []
    for k in SK:
        A, B = H["lama"][k], H["baru"][k]
        print("%-15s ton lama %s | baru %s | jepit %.1f m2" % (k, A["t"], B["t"], B["jepit"]))
        print("   peringatan lama: %s" % (A["warn"] or "-"))
        print("   peringatan baru: %s" % (B["warn"] or "-"))
        if A["t"] is None or B["t"] is None or abs(A["t"] - B["t"]) > 1e-6:
            salah.append("%s: tonase berubah / kosong" % k)
        h = HARAP[k]
        if h is None:
            if B["warn"]: salah.append("%s: build baru memberi peringatan padahal datanya benar" % k)
        else:
            if not any(h in w for w in B["warn"]): salah.append("%s: build baru TIDAK menampilkan '%s'" % (k, h))
            if any(h in w for w in A["warn"]): salah.append("%s: build lama sudah menampilkannya -> uji tidak membuktikan" % k)
    if H["baru"]["b_atap_tembus"]["jepit"] <= 0: salah.append("b: kasus jepit tidak tereproduksi")
    for v in ("lama", "baru"):
        M = H[v]["menu"]; print("   jejak", H[v]["menu"].get("jejak"), "reg.1 ada:", H[v]["menu"].get("adaReg1")); [print("     ",x) for x in H[v]["menu"].get("log") or []]; print("menu %s: %s -> '%s', PT.sel %s -> %s" % (v, M.get("node"), M.get("label"), M.get("sebelum"), M.get("sesudah")))
    if H["baru"]["menu"].get("sesudah") != "reg.1": salah.append("menu baru: node terpilih bukan reg.1")
    if H["lama"]["menu"].get("sesudah") == "reg.1": salah.append("menu lama sudah memilih reg.1 -> uji tidak membuktikan")
    if galat: print("galat halaman:", galat[:3])
    print("\n" + ("LULUS" if not salah else "GAGAL:\n  " + "\n  ".join(salah)))
    return 0 if not salah else 1


if __name__ == "__main__":
    raise SystemExit(main())
