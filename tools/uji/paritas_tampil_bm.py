# -*- coding: utf-8 -*-
"""Uji paritas: aturan tampilan block model versi Python harus SAMA dengan JS.

Caranya sama dengan paritas_laporan.py: aplikasi GC-Ex Block Model SUNGGUHAN dibuka dengan data
latihan simulasi, lalu di dalam halaman itu `bxCls()`, `bxClassOf()` dan `bxSel()` dijalankan --
fungsi yang dipakai produksi, bukan salinan. Untuk beberapa susunan panel (atribut berbeda,
cut-off berbeda, batas kelas manual, kategori dicentang-lepas) hasilnya diambil: batas kelas,
jumlah blok yang digambar, dan kelas tiap blok. Angka yang sama lalu dihitung `qtbm/tampil_bm.py`
dan dibandingkan satu-satu.

Kenapa seketat ini: aplikasi HTML dan penampil Qt akan dipakai BERDAMPINGAN oleh orang yang sama.
Kalau jumlah blok yang tampil atau warna kelasnya beda sedikit saja, yang terjadi bukan "selera
tampilan" melainkan dua jawaban berbeda untuk pertanyaan yang sama.

Pemakaian:
    python tools/uji/paritas_tampil_bm.py [port] [--fixture]
        --fixture   bekukan hasil JS ke qtbm/tests/data/tampil_bm_js.json supaya pytest di CI
                    bisa memeriksanya tanpa peramban
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
sys.path.insert(0, str(ROOT))
from qtbm import tampil_bm as TB                                     # noqa: E402
from qtbm.proyek import BlockModel                                   # noqa: E402

import numpy as np                                                   # noqa: E402

ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--")]
FIXTURE = "--fixture" in sys.argv
PORT = ARG[0] if ARG else "8771"
SRV = ROOT / "tools" / "uji" / "_srv_bm"
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
BEKU = ROOT / "qtbm" / "tests" / "data" / "tampil_bm_js.json"

# Model dicuplik supaya berkas beku tetap kecil. PENTING: pencuplikan dilakukan SEBELUM bxCls()
# dipanggil, jadi batas kelas JS pun dihitung atas model cuplikan -- Python menerima model yang
# sama, sehingga perbandingannya sah.
KECIL = 4000

JS = r"""
(function(kecil){
  var m0 = window.BX && BX.m;
  if (!m0) return {err: 'belum ada block model aktif di aplikasi'};
  var nums = Object.keys(m0.num), cats = Object.keys(m0.cat);
  if (!nums.length) return {err: 'block model tanpa atribut angka'};

  /* ---- cuplik model jadi <= kecil blok, lalu PASANG sebagai BX.m ---- */
  var step = Math.max(1, Math.floor(m0.n / kecil)), pick = [];
  for (var i = 0; i < m0.n; i += step) pick.push(i);
  var amb = function(A){ var o = new Float64Array(pick.length);
    for (var t = 0; t < pick.length; t++) o[t] = A[pick[t]]; return o; };
  var m = {name: m0.name, n: pick.length, sizes: m0.sizes, ext: m0.ext, s0: m0.s0,
           x: amb(m0.x), y: amb(m0.y), z: amb(m0.z),
           sx: amb(m0.sx), sy: amb(m0.sy), sz: amb(m0.sz), num: {}, cat: {}};
  nums.forEach(function(a){ m.num[a] = amb(m0.num[a]); });
  cats.forEach(function(a){
    var C = m0.cat[a], kode = new Uint16Array(pick.length), cnt = [];
    for (var t = 0; t < pick.length; t++) kode[t] = C.codes[pick[t]];
    for (var k = 0; k < C.dict.length; k++) cnt.push(0);
    for (var t2 = 0; t2 < kode.length; t2++) if (kode[t2] !== 65535) cnt[kode[t2]]++;
    m.cat[a] = {codes: kode, dict: C.dict.slice(), cnt: cnt};
  });
  BX.m = m; BX.ver = (BX.ver || 0) + 1; BX.sc = {};

  var lap = function(A){ return Array.prototype.slice.call(A).map(function(v){ return +v; }); };
  var out = {kecil: kecil, nama: m.name, n: m.n,
             x: lap(m.x), y: lap(m.y), z: lap(m.z),
             sx: lap(m.sx), sy: lap(m.sy), sz: lap(m.sz),
             num: {}, cat: {}, kasus: [], bawaan: null};
  nums.forEach(function(a){ out.num[a] = lap(m.num[a]); });
  cats.forEach(function(a){ out.cat[a] = {kode: lap(m.cat[a].codes), dict: m.cat[a].dict}; });

  /* keadaan panel bawaan dari bxDefUI -- supaya ui_awal() di Python bisa dibandingkan juga */
  var U0 = bxDefUI(m);
  out.bawaan = {attr: U0.attr, fAttr: U0.fAttr, fOp: U0.fOp, fVal: String(U0.fVal),
                op: U0.op, sg: U0.sg, sgCol: U0.sgCol};

  var jalan = function(nama, ui){
    BX.ui = bxDefUI(m);
    Object.keys(ui).forEach(function(k){ BX.ui[k] = ui[k]; });
    BX.sc = {};
    var k = {nama: nama, ui: {attr: BX.ui.attr, fAttr: BX.ui.fAttr, fOp: BX.ui.fOp,
                              fVal: String(BX.ui.fVal)}};
    if (BX.m.num[BX.ui.attr]) {
      k.kelas = bxCls(BX.ui.attr).map(function(c){
        return {lo: (c.lo === null ? null : c.lo), hi: (c.hi === null ? null : c.hi),
                col: c.col, lab: bxLab(c)};
      });
    } else {
      k.kelas = null;
      k.katOn = {}; k.katCol = {};
      BX.m.cat[BX.ui.attr].dict.forEach(function(d, idx){
        k.katOn[d] = bxCatOn(BX.ui.attr, d);
        k.katCol[d] = bxCatCol(BX.ui.attr, d, idx);
      });
    }
    var S = bxSel({clip: false, K: []});
    k.idx = S.idx.slice(); k.cl = S.cl.slice();
    /* kelas SELURUH blok (termasuk yang tidak digambar) -- memeriksa bxClassOf, bukan hanya bxSel */
    var semua = new Array(BX.m.n);
    for (var i2 = 0; i2 < BX.m.n; i2++) semua[i2] = bxClassOf(i2);
    k.kelas_semua = semua;
    out.kasus.push(k);
  };

  var A0 = nums.filter(function(n){ return /^AU/i.test(n); })[0] || nums[0];
  var A1 = nums.length > 1 ? nums[1] : A0;

  jalan('bawaan', {});
  jalan('atribut lain', {attr: A1});
  jalan('cutoff ge', {attr: A0, fAttr: A0, fOp: 'ge', fVal: '0.3'});
  jalan('cutoff lt', {attr: A0, fAttr: A0, fOp: 'lt', fVal: '0.3'});
  jalan('cutoff atribut lain', {attr: A0, fAttr: A1, fOp: 'ge', fVal: '1'});
  jalan('cutoff kosong', {attr: A0, fAttr: A0, fOp: 'ge', fVal: ''});

  /* batas kelas manual, termasuk batas yang sama dengan nilai blok (menguji lo <= v < hi) */
  BX.ui = bxDefUI(m); BX.ui.attr = A0; BX.sc = {};
  var L = [];
  [0.1, 0.3, 0.5, 1, 2].forEach(function(b, k){
    L.push({lo: k ? [0.1, 0.3, 0.5, 1, 2][k - 1] : null, hi: b, col: '#111111'});
  });
  L.push({lo: 2, hi: null, col: '#222222'});
  BX.ui.cls[A0] = L;
  (function(){
    var k = {nama: 'kelas manual', ui: {attr: A0, fAttr: '', fOp: 'ge', fVal: ''},
             kelas: L.map(function(c){ return {lo: c.lo, hi: c.hi, col: c.col, lab: bxLab(c)}; })};
    var S = bxSel({clip: false, K: []});
    k.idx = S.idx.slice(); k.cl = S.cl.slice();
    var semua = new Array(BX.m.n);
    for (var i3 = 0; i3 < BX.m.n; i3++) semua[i3] = bxClassOf(i3);
    k.kelas_semua = semua;
    out.kasus.push(k);
  })();

  if (cats.length) {
    var K0 = cats[0];
    jalan('kategori semua', {attr: K0});
    /* satu nilai kategori dilepas centangnya */
    BX.ui = bxDefUI(m); BX.ui.attr = K0; BX.sc = {};
    var d0 = m.cat[K0].dict[0];
    BX.ui.catOn[K0] = {}; BX.ui.catOn[K0][d0] = false;
    (function(){
      var k = {nama: 'kategori satu dilepas', ui: {attr: K0, fAttr: '', fOp: 'ge', fVal: ''},
               kelas: null, katOn: {}, katCol: {}, lepas: d0};
      m.cat[K0].dict.forEach(function(d, idx){
        k.katOn[d] = bxCatOn(K0, d); k.katCol[d] = bxCatCol(K0, d, idx);
      });
      var S = bxSel({clip: false, K: []});
      k.idx = S.idx.slice(); k.cl = S.cl.slice();
      var semua = new Array(BX.m.n);
      for (var i4 = 0; i4 < BX.m.n; i4++) semua[i4] = bxClassOf(i4);
      k.kelas_semua = semua;
      out.kasus.push(k);
    })();
  }
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
            tempfile.mkdtemp(prefix="gcex_tbm_"),
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                  "--ignore-gpu-blocklist"],
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
        print("  menjalankan bxCls/bxClassOf/bxSel asli...", flush=True)
        d = pg.evaluate("(%s)(%d)" % (JS, KECIL))
        if d is None or d.get("err"):
            raise SystemExit("gagal: %s" % (d or {}).get("err", "tidak ada hasil"))
        d["galatHalaman"] = galat
        ctx.close()
    return d


def model_dari(d: dict) -> BlockModel:
    bm = BlockModel(
        x=np.array(d["x"], float), y=np.array(d["y"], float), z=np.array(d["z"], float),
        sx=np.array(d["sx"], float), sy=np.array(d["sy"], float), sz=np.array(d["sz"], float),
        nama=d.get("nama", ""))
    for a, v in d["num"].items():
        bm.angka[a] = np.array(v, float)
    for a, c in d["cat"].items():
        bm.kategori[a] = (np.array(c["kode"], dtype=np.uint16), list(c["dict"]))
    return bm


def bandingkan(d: dict) -> list:
    salah = []
    bm = model_dari(d)

    # keadaan awal panel
    T0 = TB.ui_awal(bm)
    b = d.get("bawaan") or {}
    if b:
        if T0.atribut != b["attr"]:
            salah.append("atribut bawaan: Python %r vs JS %r" % (T0.atribut, b["attr"]))
        if T0.f_atribut != b["fAttr"]:
            salah.append("cut-off bawaan: Python %r vs JS %r" % (T0.f_atribut, b["fAttr"]))
        if str(T0.f_nilai) != str(b["fVal"]):
            salah.append("nilai cut-off bawaan: Python %r vs JS %r" % (T0.f_nilai, b["fVal"]))
        if abs(T0.opasitas - float(b["op"])) > 1e-12 or abs(T0.sg - float(b["sg"])) > 1e-12:
            salah.append("opasitas/SG bawaan beda")

    for ks in d["kasus"]:
        nm = ks["nama"]
        T = TB.ui_awal(bm)
        T.atribut = ks["ui"]["attr"]
        T.f_atribut = ks["ui"]["fAttr"]
        T.f_op = ks["ui"]["fOp"]
        T.f_nilai = ks["ui"]["fVal"]
        if ks.get("kelas"):
            # kelas manual dari JS dipasang apa adanya; kelas bawaan dibiarkan DIHITUNG Python
            if nm == "kelas manual":
                T.kelas[T.atribut] = [TB.Kelas(c["lo"], c["hi"], c["col"]) for c in ks["kelas"]]
            else:
                L = T.kelas_dari(bm, T.atribut)
                if len(L) != len(ks["kelas"]):
                    salah.append("%s: jumlah kelas Python %d vs JS %d"
                                 % (nm, len(L), len(ks["kelas"])))
                for i, (p, j) in enumerate(zip(L, ks["kelas"])):
                    for sisi, pv, jv in (("lo", p.lo, j["lo"]), ("hi", p.hi, j["hi"])):
                        if (pv is None) != (jv is None) or (
                                pv is not None and abs(float(pv) - float(jv)) > 1e-12):
                            salah.append("%s: kelas %d batas %s Python %r vs JS %r"
                                         % (nm, i, sisi, pv, jv))
                    if p.col != j["col"]:
                        salah.append("%s: kelas %d warna Python %s vs JS %s" % (nm, i, p.col, j["col"]))
                    if p.label() != j["lab"]:
                        salah.append("%s: kelas %d label Python %r vs JS %r"
                                     % (nm, i, p.label(), j["lab"]))
        if ks.get("katOn") is not None:
            lepas = ks.get("lepas")
            if lepas is not None:
                T.kat_on[T.atribut] = {lepas: False}
            for dd, warna in (ks.get("katCol") or {}).items():
                idx = bm.kategori[T.atribut][1].index(dd)
                if TB.Tampilan.warna_kategori(T, bm, T.atribut, idx) != warna:
                    salah.append("%s: warna kategori %r beda" % (nm, dd))

        kelas_semua = TB.kelas_blok(bm, T)
        js_semua = np.array(ks["kelas_semua"], dtype=np.int64)
        beda = int(np.count_nonzero(kelas_semua != js_semua))
        if beda:
            i0 = int(np.flatnonzero(kelas_semua != js_semua)[0])
            salah.append("%s: kelas per blok beda di %d blok (mis. blok %d: Python %d vs JS %d)"
                         % (nm, beda, i0, kelas_semua[i0], js_semua[i0]))

        idx, cl = TB.pilih(bm, T)
        ji = np.array(ks["idx"], dtype=np.int64)
        jc = np.array(ks["cl"], dtype=np.int64)
        if idx.size != ji.size:
            salah.append("%s: jumlah blok digambar Python %d vs JS %d" % (nm, idx.size, ji.size))
        elif not np.array_equal(idx, ji):
            salah.append("%s: indeks blok digambar tidak sama" % nm)
        elif not np.array_equal(cl, jc):
            salah.append("%s: kelas blok digambar tidak sama" % nm)
        print("  %-24s %6d blok digambar  %s" % (nm, idx.size, "ok" if not salah else ""),
              flush=True)
    return salah


def main() -> int:
    d = ambil()
    if d.get("galatHalaman"):
        print("galat halaman:", d["galatHalaman"][:3])
    print("model cuplikan: %d blok, atribut angka: %s" % (d["n"], ", ".join(d["num"])))
    salah = bandingkan(d)
    if FIXTURE:
        BEKU.parent.mkdir(parents=True, exist_ok=True)
        d.pop("galatHalaman", None)
        BEKU.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
        print("fixture ditulis: %s (%.0f KB)" % (BEKU, BEKU.stat().st_size / 1024))
    if salah:
        print("\nTIDAK LULUS:")
        for s in salah[:40]:
            print(" -", s)
        return 1
    print("\nLULUS: kelas, cut-off, warna dan daftar blok yang digambar sama persis dengan JS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
