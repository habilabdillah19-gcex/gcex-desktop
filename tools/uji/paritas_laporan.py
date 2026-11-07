# -*- coding: utf-8 -*-
"""Uji paritas: agregasi laporan block model versi Python harus SAMA dengan JS.

Caranya sama dengan paritas_geostat.py / paritas_krige.py / paritas_subblok.py: aplikasi GC-Ex
Drill Hole sungguhan dibuka dengan data latihan simulasi, lalu DI DALAM halaman itu rpRun()
dijalankan -- fungsi yang dipakai produksi, bukan salinan -- pada beberapa susunan constraint.
Masukan (blok, atribut, opsi, permukaan) dan hasilnya (RP.res) diambil, lalu masukan yang sama
dihitung backend Python dan dibandingkan: tonase, volume, jumlah blok, kadar rata-rata berbobot
per cut-off dan per grup, serta jumlah blok yang terbuang di tiap tahap (nOut).

Dipakai karena angka inilah yang dilaporkan ke manajemen tambang. Pemindahan ke Python tidak
boleh menggeser satu ton pun.

Pemakaian:
    python tools/uji/paritas_laporan.py [port] [--fixture]
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
from gcex_backend import laporan  # noqa: E402

KECIL = 0          # >0 = block model dicuplik jadi sekitar N blok (agar berkas paritas kecil)
for i, a in enumerate(sys.argv):
    if a == "--kecil" and i + 1 < len(sys.argv):
        KECIL = int(sys.argv[i + 1])
_pakai: set = {i + 1 for i, a in enumerate(sys.argv) if a == "--kecil"}
ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--") and i not in _pakai]
FIXTURE = "--fixture" in sys.argv
PORT = ARG[0] if ARG else "8765"
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


# Beberapa susunan constraint dijalankan lewat rpRun() asli; masukan & hasil dikembalikan.
JS = r"""
(function(kecil){
  var m = window.BX && BX.m;
  if (!m) return {err: 'belum ada block model aktif'};
  /* mode kecil: block model dicuplik supaya berkas paritas yang dibekukan untuk pytest tetap
     kecil. rpRun() tetap dijalankan atas model cuplikan ini, jadi angkanya tetap angka JS. */
  if (kecil > 0 && m.n > kecil) {
    var st = Math.ceil(m.n / kecil), pilih = [];
    for (var q = 0; q < m.n; q += st) pilih.push(q);
    var amb = function (A) { return pilih.map(function (i) { return A[i]; }); };
    var m2 = {n: pilih.length, name: m.name, num: {}, cat: {}, mdl: m.mdl, src: m.src};
    ['x', 'y', 'z', 'sx', 'sy', 'sz'].forEach(function (k) { m2[k] = amb(m[k]); });
    Object.keys(m.num).forEach(function (a) { m2.num[a] = amb(m.num[a]); });
    Object.keys(m.cat || {}).forEach(function (a) {
      m2.cat[a] = {dict: m.cat[a].dict, codes: amb(m.cat[a].codes)};
    });
    BX.m = m = m2; BX.ver++; BX.sc = {};
  }
  if (typeof rpRun !== 'function' || typeof rpO !== 'function') return {err: 'modul Reporting tidak ada'};
  var nums = Object.keys(m.num).filter(function (a) { return a !== 'sb_frac'; });
  var gr = null, urut = ['au', 'Au', 'AU', 'au_gpt', 'kadar'];
  for (var u = 0; u < urut.length && !gr; u++) if (m.num[urut[u]]) gr = urut[u];
  if (!gr) gr = nums[0];
  if (!gr) return {err: 'block model tidak punya atribut angka'};
  var atts = nums.slice(0, 4);
  if (atts.indexOf(gr) < 0) atts.unshift(gr);

  var o = rpO();
  var U = BX.ui || {};
  /* DTM dari data latihan untuk kasus progres topo-ke-topo & batas DTM tambahan */
  /* sejak Drillhole 0.24.40 survei topografi latihan adalah VERSI topografi di Data Spasial (v.tin),
     bukan lagi wireframe di MD.models; keduanya dicari supaya uji ini jalan di build lama & baru */
  var MM = [], KEY = [], iJuni = -1, iJuli = -1;
  ((window.MD && MD.models) || []).forEach(function (m, i) { MM.push(m); KEY.push('wf:' + i); });
  try { spL('topo').forEach(function (v) { if (v.tin) { MM.push({name: v.name, v: v.tin.v, t: v.tin.t, tin0: v.tin}); KEY.push('sp:topo:' + v.id); } }); } catch (e) {}
  for (var w = 0; w < MM.length; w++) {
    if (/topo_akhir_juni/i.test(MM[w].name)) iJuni = w;
    if (/topo_akhir_juli/i.test(MM[w].name)) iJuli = w;
  }
  var tinOf = function (i) {
    var T = MM[i];
    return {v: Array.prototype.slice.call(T.v), t: Array.prototype.slice.call(T.t), nama: T.name};
  };
  var zfTin = function (i, which) {
    var ox = window.offX || 0, oy = window.offY || 0, j = which === 'lo' ? 0 : 1;
    var tf = RP.api.tin(MM[i].tin0 || MM[i]);
    return function (x, y) { var r = tf(x + ox, y + oy); return r ? r[j] : null; };
  };

  var hasil = [], kasus = [
    {nama: 'total, tiga cut-off', set: {cuts: '0, 0.3, 0.8', grp: 'none'}},
    {nama: 'per bench RL 5 m',    set: {cuts: '0, 0.5', grp: 'bench', bh: 5, bref: 0}},
    {nama: 'rentang RL dibatasi', set: {cuts: '0', grp: 'none', z0: '180', z1: '260'}}
  ];
  if (iJuni >= 0 && iJuli >= 0) {
    kasus.push({nama: 'progres topo juni-juli', set: {cuts: '0, 0.5', grp: 'none'},
                ovr: {atas: iJuni, bawah: iJuli}});
    kasus.push({nama: 'batas DTM tambahan',     set: {cuts: '0', grp: 'none'},
                sx: [{i: iJuli, side: 'below'}]});
  }
  if (window.SB && m.num['sb_frac']) {
    kasus.push({nama: 'bobot sb_frac mati', set: {cuts: '0, 0.5', grp: 'none', frac: false}});
  }
  kasus.forEach(function (ks) {
    o.gr = gr; o.atts = atts.slice(); o.unit = o.unit || {};
    atts.forEach(function (a) { if (!o.unit[a]) o.unit[a] = 'g/t'; });
    o.dom = 'all'; o.cat = {}; o.surf = 'none'; o.sx = []; o.poly = ''; o.polyOut = false;
    o.fA = ''; o.fV = ''; o.show = false; o.z0 = ''; o.z1 = ''; o.frac = true;
    Object.keys(ks.set).forEach(function (k) { o[k] = ks.set[k]; });
    RP.ovr = null;
    if (ks.ovr) {
      /* sama seperti yang dilakukan rppit.js: permukaan atas / bawah diisi dari luar */
      RP.ovr = {tz: zfTin(ks.ovr.atas, 'hi'), pz: zfTin(ks.ovr.bawah, 'lo'),
                tzT: true, pzT: true, lab: 'uji paritas'};
    }
    if (ks.sx) o.sx = ks.sx.map(function (q) { return {k: KEY[q.i], side: q.side}; });
    rpRun();
    var R = RP.res;
    if (!R) { hasil.push({nama: ks.nama, err: 'rpRun tidak menghasilkan apa pun'}); return; }
    hasil.push({
      nama: ks.nama, opsi: JSON.parse(JSON.stringify(ks.set)),
      ovr: ks.ovr ? {atas: tinOf(ks.ovr.atas), bawah: tinOf(ks.ovr.bawah)} : null,
      sxT: ks.sx ? ks.sx.map(function (q) { return {tin: tinOf(q.i), side: q.side}; }) : null,
      nb: R.nb, nOut: R.nOut, nPart: R.nPart, atts: R.atts, cuts: R.cuts, grp: R.grp,
      bh: R.bh, br: R.br, ms: R.ms,
      rows: R.rows.map(function (r) {
        var G = {};
        Object.keys(r.G).forEach(function (k) {
          var a = r.G[k], s = {};
          Object.keys(a.s).forEach(function (at) { s[at] = {tw: a.s[at].tw, w: a.s[at].w}; });
          G[k] = {n: a.n, v: a.v, t: a.t, s: s};
        });
        return {c: r.c, G: G};
      })
    });
  });

  return {
    gr: gr, atts: atts, nTot: m.n, nama: m.name,
    off: [window.offX || 0, window.offY || 0],
    sg: +U.sg || 2.6, sgCol: U.sgCol || '', sgZero: U.sgZero || '', sgRep: U.sgRep || '',
    blocks: {x: Array.prototype.slice.call(m.x), y: Array.prototype.slice.call(m.y),
             z: Array.prototype.slice.call(m.z), sx: Array.prototype.slice.call(m.sx),
             sy: Array.prototype.slice.call(m.sy), sz: Array.prototype.slice.call(m.sz)},
    num: (function () { var N = {}; atts.forEach(function (a) { N[a] = Array.prototype.slice.call(m.num[a]); });
      if (m.num['sb_frac']) N['sb_frac'] = Array.prototype.slice.call(m.num['sb_frac']);
      if (U.sgCol && m.num[U.sgCol]) N[U.sgCol] = Array.prototype.slice.call(m.num[U.sgCol]);
      return N; })(),
    kasus: hasil
  };
})
"""


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
            tempfile.mkdtemp(prefix="gcex_lap_"),
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
        print("  menjalankan rpRun() asli untuk beberapa constraint...", flush=True)
        d = pg.evaluate("(%s)(%d)" % (JS, KECIL))
        if d is None or d.get("err"):
            raise SystemExit("gagal: %s" % (d or {}).get("err", "tidak ada hasil"))
        d["galatHalaman"] = galat
        ctx.close()
    return d


def bandingkan(d: dict) -> list:
    salah = []
    for ks in d["kasus"]:
        if ks.get("err"):
            salah.append("%s: %s" % (ks["nama"], ks["err"]))
            continue
        se = ks["opsi"]
        o = {"cuts": [float(c) for c in str(se.get("cuts", "0")).replace(";", ",").split(",")
                      if c.strip()],
             "gr": d["gr"], "atts": d["atts"], "grp": se.get("grp") or "none",
             "bh": se.get("bh") or 5, "bref": se.get("bref") or 0,
             "z0": se.get("z0", ""), "z1": se.get("z1", ""), "frac": True,
             "sg": d["sg"], "sgCol": d["sgCol"], "sgZero": d["sgZero"], "sgRep": d["sgRep"]}
        if se.get("frac") is False:
            o["frac"] = False
        if ks.get("ovr"):
            # DTM: permukaan atas memakai z maksimum, bawah memakai z minimum, dan di luar
            # jangkauan DTM blok dibuang (tegas) -- sama dengan tzT / pzT di JS
            o["surf"] = {"atas": {"tin": ks["ovr"]["atas"], "tegas": True},
                         "bawah": {"tin": ks["ovr"]["bawah"], "tegas": True}}
        if ks.get("sxT"):
            o["sx"] = [{"tin": q["tin"], "side": q["side"]} for q in ks["sxT"]]
        t0 = time.perf_counter()
        r = laporan.run({"blocks": d["blocks"], "off": d["off"], "num": d["num"], "opsi": o})
        ms = int((time.perf_counter() - t0) * 1000)
        print("    %-24s JS %4d ms | Python %4d ms | blok JS %d / Python %d"
              % (ks["nama"], ks["ms"], ms, ks["nb"], r["nb"]), flush=True)
        if ks["nb"] != r["nb"]:
            salah.append("%s: jumlah blok terhitung beda (JS %d, Python %d)"
                         % (ks["nama"], ks["nb"], r["nb"]))
        for kunci, v in ks["nOut"].items():
            if int(v) != int(r["nOut"].get(kunci, 0)):
                salah.append("%s: nOut.%s beda (JS %d, Python %d)"
                             % (ks["nama"], kunci, v, r["nOut"].get(kunci, 0)))
        # nPart hanya ada bila block model punya atribut sb_frac
        jp = int(ks.get("nPart") or 0)
        if jp != int(r["nPart"] or 0):
            salah.append("%s: jumlah blok sebagian (sb_frac) beda (JS %d, Python %d)"
                         % (ks["nama"], jp, int(r["nPart"] or 0)))
        if len(ks["rows"]) != len(r["rows"]):
            salah.append("%s: jumlah baris cut-off beda" % ks["nama"])
            continue
        for rj, rp in zip(ks["rows"], r["rows"]):
            if abs(float(rj["c"]) - float(rp["c"])) > 1e-12:
                salah.append("%s: nilai cut-off beda (%s vs %s)" % (ks["nama"], rj["c"], rp["c"]))
            kj, kp = set(rj["G"]), set(rp["G"])
            if kj != kp:
                salah.append("%s cut-off %s: grup beda (hanya JS %s, hanya Python %s)"
                             % (ks["nama"], rj["c"], sorted(kj - kp)[:4], sorted(kp - kj)[:4]))
                continue
            for g in sorted(kj):
                aj, ap = rj["G"][g], rp["G"][g]
                if aj["n"] != ap["n"]:
                    salah.append("%s cut-off %s grup %s: jumlah blok beda (%d vs %d)"
                                 % (ks["nama"], rj["c"], g, aj["n"], ap["n"]))
                for nama, kunci in (("volume", "v"), ("tonase", "t")):
                    a, b = float(aj[kunci]), float(ap[kunci])
                    if abs(a - b) > 1e-6 + 1e-9 * max(abs(a), abs(b)):
                        salah.append("%s cut-off %s grup %s: %s beda (%.6f vs %.6f)"
                                     % (ks["nama"], rj["c"], g, nama, a, b))
                for at in d["atts"]:
                    qj, qp = aj["s"].get(at), ap["s"].get(at)
                    gj = (qj["tw"] / qj["w"]) if qj and qj["w"] else None
                    gp = (qp["tw"] / qp["w"]) if qp and qp["w"] else None
                    if (gj is None) != (gp is None):
                        salah.append("%s cut-off %s grup %s: kadar %s ada/tidak beda"
                                     % (ks["nama"], rj["c"], g, at))
                    elif gj is not None and abs(gj - gp) > 1e-9 + 1e-9 * max(abs(gj), abs(gp)):
                        salah.append("%s cut-off %s grup %s: kadar %s beda (%.9g vs %.9g)"
                                     % (ks["nama"], rj["c"], g, at, gj, gp))
    return salah


def main() -> int:
    print("Mengambil masukan & hasil laporan JS dari aplikasi sungguhan...", flush=True)
    d = ambil()
    print("  block model %s | %d blok | kadar cut-off '%s' | atribut %s"
          % (d["nama"], d["nTot"], d["gr"], ", ".join(d["atts"])), flush=True)
    salah = bandingkan(d)
    if d["galatHalaman"]:
        print("Galat halaman:", d["galatHalaman"][:3])

    if FIXTURE and not salah:
        fx = ROOT / "backend" / "tests" / "data" / "laporan_js.json"
        fx.parent.mkdir(parents=True, exist_ok=True)
        beku = {k: d[k] for k in ("gr", "atts", "off", "sg", "sgCol", "sgZero", "sgRep",
                                  "blocks", "num", "kasus", "nTot", "nama")}
        beku["catatan"] = ("Masukan & keluaran rpRun() asli dari aplikasi GC-Ex pada data latihan; "
                           "dipakai backend/tests/test_laporan.py agar angka Python tidak bergeser.")
        fx.write_text(json.dumps(beku, separators=(",", ":")), encoding="utf-8")
        print("Berkas paritas ditulis: %s (%.0f KB)" % (fx.relative_to(ROOT), fx.stat().st_size / 1024))

    print()
    if salah:
        print("TIDAK SAMA (%d temuan, 20 pertama):" % len(salah))
        for s in salah[:20]:
            print("  -", s)
        return 1
    print("SAMA: jumlah blok, volume, tonase, kadar rata-rata berbobot, dan alasan blok terbuang "
          "cocok di semua constraint yang diuji.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
