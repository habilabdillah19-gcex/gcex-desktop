# -*- coding: utf-8 -*-
"""Uji paritas: laporan Block Model di penampil Qt harus SAMA dengan laporan aplikasi HTML.

Bedanya dengan `paritas_laporan.py`: yang itu menguji MESIN hitungnya
(`gcex_backend.laporan.run()`) terhadap `rpRun()` di aplikasi Drill Hole. Yang ini menguji
LAPISAN QT-nya (`qtbm/laporan_bm.py`) terhadap `rpRun()` di aplikasi **Block Model** -- sebab
mesin yang benar masih bisa dipanggil dengan pilihan yang salah: SG tetap vs kolom SG, daftar
cut-off, atribut yang dilaporkan, pengelompokan per RL, dan sakelar proporsi `sb_frac` (yang di
Block Model bertipe BOOLEAN, bukan nama atribut).

Caranya: aplikasi Block Model sungguhan dibuka dengan data latihan, `rpRun()` ASLI dijalankan di
dalam halaman untuk beberapa susunan pilihan, lalu blok + pilihan + hasilnya diambil. Pilihan yang
sama dijalankan lewat `qtbm/laporan_bm.jalankan()`, dan tonase, volume, jumlah blok serta kadar
rata-rata berbobot dibandingkan -- total maupun per grup.

Pemakaian:
    python tools/uji/paritas_laporan_bm.py [port] [--fixture]
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
from qtbm import laporan_bm as LB                                    # noqa: E402
from qtbm.proyek import BlockModel                                   # noqa: E402

ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--")]
FIXTURE = "--fixture" in sys.argv
PORT = ARG[0] if ARG else "8773"
SRV = ROOT / "tools" / "uji" / "_srv_bm"
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
BEKU = ROOT / "qtbm" / "tests" / "data" / "laporan_bm_js.json"

KECIL = 3000
TOL = 1e-6          # toleransi relatif; keduanya float64 jadi seharusnya nyaris nol

JS = r"""
(function(kecil){
  var m0 = window.BX && BX.m;
  if (!m0) return {err: 'belum ada block model aktif'};
  if (typeof rpRun !== 'function' || typeof rpO !== 'function')
    return {err: 'Reporting BM tidak tersedia di halaman ini'};
  var nums = Object.keys(m0.num), cats = Object.keys(m0.cat);

  /* model dicuplik, lalu dipasang sebagai BX.m -- rpRun() menghitung atas model cuplikan ini */
  var step = Math.max(1, Math.floor(m0.n / kecil)), pick = [];
  for (var i = 0; i < m0.n; i += step) pick.push(i);
  var amb = function(A){ var o = new Float64Array(pick.length);
    for (var t = 0; t < pick.length; t++) o[t] = A[pick[t]]; return o; };
  var m = {name: m0.name, n: pick.length, sizes: m0.sizes, ext: m0.ext, s0: m0.s0,
           x: amb(m0.x), y: amb(m0.y), z: amb(m0.z),
           sx: amb(m0.sx), sy: amb(m0.sy), sz: amb(m0.sz), num: {}, cat: {}};
  nums.forEach(function(a){ m.num[a] = amb(m0.num[a]); });
  cats.forEach(function(a){
    var C = m0.cat[a], kode = new Uint16Array(pick.length);
    for (var t = 0; t < pick.length; t++) kode[t] = C.codes[pick[t]];
    m.cat[a] = {codes: kode, dict: C.dict.slice(), cnt: C.cnt};
  });
  /* sb_frac buatan supaya metode tonase benar-benar berbeda: sebagian blok di perbatasan,
     sebagian berproporsi nol. Dibuat dari indeks (bukan acak) agar Python bisa menirunya persis. */
  var fr = new Float64Array(m.n);
  for (var q = 0; q < m.n; q++) fr[q] = (q % 10 === 0) ? 0 : ((q % 4 === 0) ? 0.25 : 1);
  m.num.sb_frac = fr;
  BX.m = m; BX.ver = (BX.ver || 0) + 1; BX.sc = {};

  var lap = function(A){ return Array.prototype.slice.call(A).map(function(v){ return +v; }); };
  var out = {kecil: kecil, n: m.n, nama: m.name,
             x: lap(m.x), y: lap(m.y), z: lap(m.z),
             sx: lap(m.sx), sy: lap(m.sy), sz: lap(m.sz), num: {}, cat: {}, kasus: []};
  Object.keys(m.num).forEach(function(a){ out.num[a] = lap(m.num[a]); });
  cats.forEach(function(a){ out.cat[a] = {kode: lap(m.cat[a].codes), dict: m.cat[a].dict}; });

  var A0 = nums.filter(function(n){ return /^AU/i.test(n); })[0] || nums[0];
  var sgCol = nums.filter(function(n){ return /^(sg|dens|density|bd)$/i.test(n); })[0] || '';

  /* PENTING: SG yang dipakai Reporting BM diambil dari PANEL TAMPILAN (BX.ui.sg / BX.ui.sgCol),
     bukan dari RP.o. Jadi kasus "SG kolom" harus menyetel BX.ui, bukan opsi laporan. */
  var jalan = function(nama, set){
    var o = rpO();
    var simpan = {}, simpanUi = {};
    ['sg', 'sgCol'].forEach(function(k){
      if (set.hasOwnProperty(k)) { simpanUi[k] = BX.ui[k]; BX.ui[k] = set[k]; }
    });
    Object.keys(set).forEach(function(k){ simpan[k] = o[k]; o[k] = set[k]; });
    var show0 = o.show; o.show = false;
    var res = null, err = null;
    try { rpRun(); res = RP.res; } catch (e) { err = String(e && e.message || e); }
    /* Pilihan dicatat SEKARANG, selagi o masih memegang nilai yang diuji. Kalau dicatat setelah
       dikembalikan di bawah, yang terbawa adalah pilihan BAWAAN -- dan Python akan dibandingkan
       dengan susunan yang sama sekali lain. */
    var opsi = {cuts: String(o.cuts), gr: res ? res.gr : o.gr, atts: res ? res.atts : o.atts,
                grp: res ? res.grp : o.grp, bh: res ? res.bh : o.bh, br: res ? res.br : o.bref,
                sg: BX.ui.sg, sgCol: BX.ui.sgCol, catAttr: o.catAttr, frac: o.frac};
    o.show = show0;
    Object.keys(simpan).forEach(function(k){ o[k] = simpan[k]; });
    Object.keys(simpanUi).forEach(function(k){ BX.ui[k] = simpanUi[k]; });
    if (err || !res) { out.kasus.push({nama: nama, err: err || 'rpRun tidak memberi hasil'}); return; }
    out.kasus.push({nama: nama, set: set, opsi: opsi,
      rows: res.rows.map(function(r){
        var G = {};
        Object.keys(r.G).forEach(function(k){
          var a = r.G[k], s = {};
          Object.keys(a.s).forEach(function(at){ s[at] = {tw: a.s[at].tw, w: a.s[at].w}; });
          G[k] = {n: a.n, v: a.v, t: a.t, s: s};
        });
        return {c: r.c, G: G};
      }),
      nb: res.nb, nOut: res.nOut, nPart: res.nPart});
  };

  jalan('total, SG tetap', {cuts: '0,0.3,0.5', gr: A0, atts: [A0], grp: 'none',
                            sg: 2.6, sgCol: '', frac: true});
  jalan('total, SG kolom', {cuts: '0,0.3', gr: A0, atts: [A0], grp: 'none',
                            sg: 2.6, sgCol: sgCol, frac: true});
  jalan('beberapa atribut', {cuts: '0.3', gr: A0, atts: nums.filter(function(n){
                              return n !== 'sb_frac'; }).slice(0, 3),
                             grp: 'none', sg: 2.6, sgCol: '', frac: true});
  jalan('per RL 5 m', {cuts: '0.3', gr: A0, atts: [A0], grp: 'bench', bh: 5, bref: 0,
                       sg: 2.6, sgCol: '', frac: true});
  jalan('per RL 10 m, acuan 300', {cuts: '0.3', gr: A0, atts: [A0], grp: 'bench', bh: 10,
                                   bref: 300, sg: 2.6, sgCol: '', frac: true});
  jalan('seperti Surpac (frac mati)', {cuts: '0,0.3', gr: A0, atts: [A0], grp: 'none',
                                       sg: 2.6, sgCol: '', frac: false});
  if (cats.length) {
    jalan('per kategori', {cuts: '0.3', gr: A0, atts: [A0], grp: 'cat', catAttr: cats[0],
                           sg: 2.6, sgCol: '', frac: true});
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
            tempfile.mkdtemp(prefix="gcex_lbm_"),
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
        print("  menjalankan rpRun() asli di aplikasi Block Model...", flush=True)
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


def pilihan_dari(o: dict) -> LB.Pilihan:
    P = LB.Pilihan()
    P.kadar = o["gr"]
    P.cuts = sorted(float(c) for c in str(o["cuts"]).replace(";", ",").split(",") if c.strip())
    P.atribut = list(o["atts"])
    P.grup = o.get("grp") or "none"
    P.grup_atribut = o.get("catAttr") or ""
    P.tinggi_bench = float(o.get("bh") or 5)
    P.rl_acuan = float(o.get("br") or 0)
    P.sg = float(o.get("sg") or 2.6)
    P.sg_kolom = o.get("sgCol") or ""
    P.metode = "presisi" if o.get("frac") is not False else "surpac"
    return P


def _dekat(a: float, b: float) -> bool:
    a, b = float(a), float(b)
    if not np.isfinite(a) or not np.isfinite(b):
        return (not np.isfinite(a)) and (not np.isfinite(b))
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def bandingkan(d: dict) -> list:
    salah = []
    bm = model_dari(d)
    for ks in d["kasus"]:
        nm = ks["nama"]
        if ks.get("err"):
            salah.append("%s: %s" % (nm, ks["err"]))
            continue
        P = pilihan_dari(ks["opsi"])
        h = LB.jalankan(bm, P)
        R = h["metode"][h["urut"][0]]
        js_rows, py_rows = ks["rows"], R["rows"]
        if len(js_rows) != len(py_rows):
            salah.append("%s: jumlah baris cut-off Python %d vs JS %d"
                         % (nm, len(py_rows), len(js_rows)))
            continue
        for i, (jr, pr) in enumerate(zip(js_rows, py_rows)):
            if not _dekat(jr["c"], pr["c"]):
                salah.append("%s: cut-off baris %d Python %s vs JS %s" % (nm, i, pr["c"], jr["c"]))
            jg, pg = jr["G"], pr["G"]
            if set(jg) != set(pg):
                salah.append("%s cut-off %s: grup Python %s vs JS %s"
                             % (nm, jr["c"], sorted(pg), sorted(jg)))
                continue
            for g in jg:
                for kunci in ("n", "v", "t"):
                    if not _dekat(pg[g][kunci], jg[g][kunci]):
                        salah.append("%s cut-off %s grup %s: %s Python %.6f vs JS %.6f"
                                     % (nm, jr["c"], g, kunci, pg[g][kunci], jg[g][kunci]))
                for a in jg[g]["s"]:
                    jq, pq = jg[g]["s"][a], (pg[g]["s"] or {}).get(a)
                    if pq is None:
                        salah.append("%s cut-off %s grup %s: atribut %s tidak ada di Python"
                                     % (nm, jr["c"], g, a))
                        continue
                    for kunci in ("tw", "w"):
                        if not _dekat(pq[kunci], jq[kunci]):
                            salah.append("%s cut-off %s grup %s atribut %s: %s Python %.6f vs "
                                         "JS %.6f" % (nm, jr["c"], g, a, kunci, pq[kunci],
                                                      jq[kunci]))
        # total seluruh grup juga harus sama (ini yang dilihat pemakai di tabel utama)
        jt = {"n": 0, "v": 0.0, "t": 0.0}
        for g in js_rows[0]["G"].values():
            for kunci in jt:
                jt[kunci] += g[kunci]
        pt = LB._total(py_rows[0]["G"])
        for kunci in jt:
            if not _dekat(pt[kunci], jt[kunci]):
                salah.append("%s: total %s Python %.6f vs JS %.6f" % (nm, kunci, pt[kunci],
                                                                      jt[kunci]))
        if int(R.get("nPart") or 0) != int(ks.get("nPart") or 0):
            salah.append("%s: nPart Python %s vs JS %s" % (nm, R.get("nPart"), ks.get("nPart")))
        print("  %-30s %8s blok, %14s t  %s"
              % (nm, f"{pt['n']:,}".replace(",", "."), ("%.2f" % pt["t"]),
                 "ok" if not salah else ""), flush=True)
    return salah


def main() -> int:
    d = ambil()
    if d.get("galatHalaman"):
        print("galat halaman:", d["galatHalaman"][:3])
    print("model cuplikan: %d blok" % d["n"])
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
    print("\nLULUS: tonase, volume, jumlah blok dan kadar berbobot sama persis dengan "
          "laporan aplikasi HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
