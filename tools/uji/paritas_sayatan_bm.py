# -*- coding: utf-8 -*-
"""Uji paritas: sayatan (slicing) penampil Qt vs `secGeom` / `secK` / `bxSlabHit` aplikasi HTML.

Yang dibandingkan bukan parameter bidangnya, melainkan **blok mana yang terpilih** -- itulah yang
dilihat pemakai, dan itu kebal terhadap perbedaan cara menuliskan pusat bidang. (Aplikasi HTML
memakai ruang koordinat internal dengan pusat `c = [-offX, 0, 0]` pada mode X; penampil Qt memakai
koordinat penuh dengan pusat nol. Hasilnya harus sama, representasinya berbeda -- membandingkan
`c` secara langsung hanya akan menghasilkan beda yang tidak berarti apa-apa.)

Lima mode diuji (H, X, Y, A, P), masing-masing dengan beberapa ketebalan termasuk slab yang lebih
TIPIS daripada satu blok -- di situlah perbedaan uji kotak vs uji titik tengah paling tajam.

Pemakaian:
    python tools/uji/paritas_sayatan_bm.py [port] [--fixture]
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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from qtbm import sayatan as SY                                       # noqa: E402
from qtbm.proyek import BlockModel                                   # noqa: E402

ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--")]
FIXTURE = "--fixture" in sys.argv
PORT = ARG[0] if ARG else "8785"
SRV = ROOT / "tools" / "uji" / "_srv_bm"
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
BEKU = ROOT / "qtbm" / "tests" / "data" / "sayatan_bm_js.json"

KECIL = 2500

JS = r"""
(function (kecil) {
  var m0 = window.BX && BX.m;
  if (!m0) return {err: 'belum ada block model aktif'};
  if (typeof bxSlabHit !== 'function' || typeof secK !== 'function')
    return {err: 'bxSlabHit / secK tidak tersedia'};

  /* model dicuplik berjarak lalu dipasang sebagai BX.m: yang diuji pemilihan slab, bukan
     kerapatan model, jadi cuplikan berjarak cukup dan jauh lebih ringan dikirim balik */
  var step = Math.max(1, Math.floor(m0.n / kecil)), pick = [];
  for (var i = 0; i < m0.n; i += step) pick.push(i);
  var amb = function (A) { var o = new Float64Array(pick.length);
    for (var t = 0; t < pick.length; t++) o[t] = A[pick[t]]; return o; };
  var m = {name: m0.name, n: pick.length, sizes: m0.sizes, ext: m0.ext, s0: m0.s0,
           x: amb(m0.x), y: amb(m0.y), z: amb(m0.z),
           sx: amb(m0.sx), sy: amb(m0.sy), sz: amb(m0.sz), num: {}, cat: {}};
  Object.keys(m0.num).forEach(function (a) { m.num[a] = amb(m0.num[a]); });
  BX.m = m; BX.ver = (BX.ver || 0) + 1; BX.sc = {};

  var lap = function (A) { return Array.prototype.slice.call(A).map(function (v) { return +v; }); };
  /* Kotak DATA aplikasi: `secGeom` memakai (G.z0+G.z1)/2 sebagai RL pusat bidang mode A / P,
     bukan tengah block model. Tanpa angka ini, paritas dip != 90 tidak mungkin tepat. */
  var out = {kecil: kecil, n: m.n, nama: m.name, offX: offX, offY: offY,
             G: (window.G ? {x0: G.x0, x1: G.x1, y0: G.y0, y1: G.y1, z0: G.z0, z1: G.z1} : null),
             x: lap(m.x), y: lap(m.y), z: lap(m.z),
             sx: lap(m.sx), sy: lap(m.sy), sz: lap(m.sz), kasus: []};

  var E = function (id) { return document.getElementById(id); };
  /* `pos` adalah input RANGE: nilainya DIJEPIT ke min/max, sehingga menyetelnya begitu saja
     memberi angka lain tanpa ada tanda apa pun. Batasnya dilebarkan dulu, lalu dipulihkan. */
  var set = function (id, v) {
    var e = E(id);
    if (!e) return;
    if (e.type === 'checkbox') { e.checked = v; return; }
    if (e.type === 'range') { e.min = -1e9; e.max = 1e9; e.step = 'any'; }
    e.value = v;
  };

  function jalan(nama, p) {
    var simpan = {}, batas = {};
    ['sMode', 'pos', 'thick', 'az', 'dipS', 'p1e', 'p1n', 'p2e', 'p2n', 'ext', 'limSeg', 'hC']
      .forEach(function (id) {
        var e = E(id);
        if (!e) return;
        simpan[id] = (e.type === 'checkbox') ? e.checked : e.value;
        if (e.type === 'range') batas[id] = [e.min, e.max, e.step];
      });
    try {
      Object.keys(p).forEach(function (id) { set(id, p[id]); });
      var S = secK();
      var hit = [];
      for (var i = 0; i < m.n; i++) if (bxSlabHit(i, S.K)) hit.push(i);
      /* juga uji titik tengah (inK) supaya kedua jalur bisa dibandingkan terpisah */
      var hitT = [];
      for (var j = 0; j < m.n; j++) {
        var c = {x: m.x[j] - offX, y: m.y[j] - offY, z: m.z[j]};
        if (inK(S.K, c)) hitT.push(j);
      }
      out.kasus.push({nama: nama, set: p, kotak: hit, titik: hitT,
                      pos: S.pos, thick: S.thick,
                      g: {m: S.g.m, az: S.g.az, dip: S.g.dip, seg: S.g.seg},
                      nBatas: S.K.length});
    } catch (e) {
      out.kasus.push({nama: nama, set: p, err: String(e && e.message || e)});
    } finally {
      Object.keys(simpan).forEach(function (id) { set(id, simpan[id]); });
      Object.keys(batas).forEach(function (id) {
        var e = E(id);
        if (e) { e.min = batas[id][0]; e.max = batas[id][1]; e.step = batas[id][2]; }
      });
    }
  }

  /* titik acuan di dalam model, supaya slab benar-benar kena blok */
  var xm = (m0.ext ? 0 : 0);
  var xs = [], ys = [], zs = [];
  for (var q = 0; q < m.n; q++) { xs.push(m.x[q]); ys.push(m.y[q]); zs.push(m.z[q]); }
  xs.sort(function (a, b) { return a - b; });
  ys.sort(function (a, b) { return a - b; });
  zs.sort(function (a, b) { return a - b; });
  var cx = xs[xs.length >> 1], cy = ys[ys.length >> 1], cz = zs[zs.length >> 1];
  var sz = m.sz[0] || 2.5;
  out.acuan = {cx: cx, cy: cy, cz: cz, sz: sz};

  /* HANYA mode yang benar-benar bisa dicapai dari antarmuka aplikasi Block Model: H dan P.
     `secGeom` juga memuat mode X, Y dan A, tetapi pilihan `sMode` aplikasi ini hanya menawarkan
     'H' (Horizontal) dan 'P' (Garis manual). Menyetel 'X' ke pilihan itu DITOLAK peramban dan
     `secGeom` jatuh ke cabang miring dengan azimut 0 -- jadi menguji mode itu berarti menguji
     dugaan sendiri, bukan perilaku aplikasi. Karena itu panel Qt pun hanya menawarkan H dan P. */
  var opsiMode = Array.prototype.map.call(E('sMode').options, function (o) { return o.value; });
  out.modeTersedia = opsiMode;

  jalan('H tebal 10', {sMode: 'H', pos: cz, thick: 10});
  jalan('H tebal sama dengan satu blok', {sMode: 'H', pos: cz, thick: sz});
  jalan('H tebal 0,2 (lebih tipis dari satu blok)', {sMode: 'H', pos: cz, thick: 0.2});
  jalan('H tepat di batas blok', {sMode: 'H', pos: cz + sz / 2, thick: sz});
  jalan('H di luar model', {sMode: 'H', pos: cz + 100000, thick: 10});
  jalan('P dip 90', {sMode: 'P', pos: 0, thick: 20, dipS: 90, limSeg: false,
                     p1e: cx - 100, p1n: cy - 50, p2e: cx + 120, p2n: cy + 80});
  jalan('P dip 70', {sMode: 'P', pos: 0, thick: 25, dipS: 70, limSeg: false,
                     p1e: cx - 100, p1n: cy - 50, p2e: cx + 120, p2n: cy + 80});
  jalan('P dip 45 tebal tipis 1', {sMode: 'P', pos: 0, thick: 1, dipS: 45, limSeg: false,
                                   p1e: cx - 100, p1n: cy - 50, p2e: cx + 120, p2n: cy + 80});
  jalan('P offset 30', {sMode: 'P', pos: 30, thick: 15, dipS: 90, limSeg: false,
                        p1e: cx - 100, p1n: cy - 50, p2e: cx + 120, p2n: cy + 80});
  jalan('P dibatasi ruas', {sMode: 'P', pos: 0, thick: 25, dipS: 90, limSeg: true, ext: 0,
                            p1e: cx - 100, p1n: cy - 50, p2e: cx + 120, p2n: cy + 80});
  jalan('P dibatasi ruas + perpanjangan 40', {sMode: 'P', pos: 0, thick: 25, dipS: 90,
                                              limSeg: true, ext: 40,
                                              p1e: cx - 100, p1n: cy - 50,
                                              p2e: cx + 120, p2n: cy + 80});
  jalan('P ruas pendek', {sMode: 'P', pos: 0, thick: 20, dipS: 90, limSeg: true, ext: 0,
                          p1e: cx - 20, p1n: cy, p2e: cx + 20, p2n: cy});
  return out;
})
"""


def siapkan() -> None:
    SRV.mkdir(parents=True, exist_ok=True)
    (SRV / "index.html").write_bytes((ROOT / "app" / "index.html").read_bytes())
    t = SRV / "data-latihan"
    if t.is_symlink():
        t.unlink()
    if not t.exists():
        os.symlink(DATA, t)


def ambil() -> dict:
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
            tempfile.mkdtemp(prefix="gcex_sy_"),
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
            viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page()
        galat: list = []
        pg.on("pageerror", lambda e: galat.append(str(e)[:200]))
        pg.on("dialog", lambda d: d.accept())
        pg.goto(url)
        pg.wait_for_timeout(1500)
        pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
        print("  memuat data latihan...", flush=True)
        pg.evaluate("document.getElementById('dlatBtn').click()")
        pg.wait_for_function("window.BX && BX.m && BX.m.n > 0", timeout=600000)
        pg.wait_for_function("!DLAT.busy", timeout=600000)
        pg.wait_for_timeout(2000)
        print("  menjalankan secK() + bxSlabHit() asli...", flush=True)
        d = pg.evaluate("(%s)(%d)" % (JS, KECIL))
        if d is None or d.get("err"):
            raise SystemExit("gagal: %s" % (d or {}).get("err", "tidak ada hasil"))
        d["galatHalaman"] = galat
        ctx.close()
    return d


def model_dari(d: dict) -> BlockModel:
    return BlockModel(
        x=np.array(d["x"], float), y=np.array(d["y"], float), z=np.array(d["z"], float),
        sx=np.array(d["sx"], float), sy=np.array(d["sy"], float), sz=np.array(d["sz"], float),
        nama=d.get("nama", ""))


def opsi_dari(s: dict, G=None) -> SY.Opsi:
    """Pengaturan kotak isian aplikasi -> `sayatan.Opsi`."""
    f = lambda k, d=0.0: float(s[k]) if k in s and s[k] not in ("", None) else d   # noqa: E731
    O = SY.Opsi(mode=str(s.get("sMode") or "H"), pos=f("pos"), tebal=f("thick", 5.0),
                azimut=f("az"), dip=f("dipS", 90.0),
                batasi_ruas=bool(s.get("limSeg")), perpanjang=f("ext"))
    if G:
        # RL pusat bidang diambil dari kotak DATA aplikasi, sama dengan `zc` di `secGeom`
        O.pusat_z = (float(G["z0"]) + float(G["z1"])) / 2.0
    if O.mode == "P" and all(k in s for k in ("p1e", "p1n", "p2e", "p2n")):
        O.titik1 = (f("p1e"), f("p1n"))
        O.titik2 = (f("p2e"), f("p2n"))
    return O


def bandingkan(d: dict) -> list:
    salah = []
    bm = model_dari(d)
    for ks in d["kasus"]:
        nm = ks["nama"]
        if ks.get("err"):
            salah.append("%s: %s" % (nm, ks["err"]))
            continue
        O = opsi_dari(ks["set"], d.get("G"))
        # mode A bawaan aplikasi berpusat di tengah kotak data (CX/CY, zc); Opsi tanpa `pusat`
        # memakai tengah kotak model -- pada cuplikan ini keduanya sama, dan kalau tidak, uji
        # inilah yang akan menyatakannya alih-alih mendiamkannya.
        try:
            kotak = np.flatnonzero(SY.dalam_slab(bm, O)).tolist()
            titik = np.flatnonzero(SY.dalam_slab_titik(bm, O)).tolist()
        except Exception as e:                      # noqa: BLE001
            salah.append("%s: Python melempar %s: %s" % (nm, type(e).__name__, e))
            continue
        if kotak != ks["kotak"]:
            a, b = set(kotak), set(ks["kotak"])
            salah.append("%s: blok terpilih (uji kotak) beda -- Python %d, JS %d, "
                         "hanya di Python %d, hanya di JS %d"
                         % (nm, len(kotak), len(ks["kotak"]), len(a - b), len(b - a)))
        if titik != ks["titik"]:
            salah.append("%s: blok terpilih (uji titik tengah) beda -- Python %d, JS %d"
                         % (nm, len(titik), len(ks["titik"])))
        S = SY.slab(bm, O)
        if len(S.batas) != ks["nBatas"]:
            salah.append("%s: jumlah batas slab Python %d vs JS %d"
                         % (nm, len(S.batas), ks["nBatas"]))
        gj = ks["g"]
        if abs(S.g.az - float(gj["az"])) > 1e-9 or abs(S.g.dip - float(gj["dip"])) > 1e-9:
            salah.append("%s: azimut/dip bidang Python (%r, %r) vs JS (%r, %r)"
                         % (nm, S.g.az, S.g.dip, gj["az"], gj["dip"]))
        if gj.get("seg") is not None and S.g.seg is not None:
            if abs(S.g.seg - float(gj["seg"])) > 1e-6:
                salah.append("%s: panjang ruas Python %r vs JS %r" % (nm, S.g.seg, gj["seg"]))
    return salah


def main() -> int:
    if FIXTURE and BEKU.exists():
        print("memakai hasil JS yang dibekukan: %s" % BEKU.relative_to(ROOT))
        d = json.loads(BEKU.read_text(encoding="utf-8"))
    else:
        d = ambil()
        BEKU.parent.mkdir(parents=True, exist_ok=True)
        BEKU.write_text(json.dumps(d), encoding="utf-8")
        print("hasil JS dibekukan ke %s (%.0f KB)"
              % (BEKU.relative_to(ROOT), BEKU.stat().st_size / 1024))
    if d.get("galatHalaman"):
        print("galat halaman: %s" % d["galatHalaman"][:3])
    print("model cuplikan: %d blok (offX %r, offY %r)" % (d["n"], d["offX"], d["offY"]))
    salah = bandingkan(d)
    print("kasus: %d" % len(d["kasus"]))
    for ks in d["kasus"]:
        print("  - %-42s kotak %5d blok, titik tengah %5d blok"
              % (ks["nama"], len(ks.get("kotak") or []), len(ks.get("titik") or [])))
    if salah:
        print("\nTIDAK SAMA (%d):" % len(salah))
        for s in salah:
            print("  ! %s" % s)
        return 1
    print("\nSEMUA SAMA PERSIS: sayatan Qt = sayatan aplikasi HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
