# -*- coding: utf-8 -*-
"""Uji atap (roof) as-mined: bawaan HARUS identik dengan rumus lama, dan mode atap harus bekerja.

Dua hal diuji, dan yang pertama lebih penting daripada yang kedua:

1. **TIDAK ADA ANGKA LAMA YANG BERUBAH.** Dengan `roof = 'flitch'` (bawaan), hasil as-mined
   aplikasi SETELAH perubahan harus sama persis dengan hasil aplikasi SEBELUM perubahan. Kedua
   versi dijalankan berdampingan di dua peladen, dengan boundary dan pengaturan yang sama, lalu
   volume / tonase / jumlah sub-blok dibandingkan. Perubahan yang menggeser angka produksi tanpa
   ada yang meminta adalah kerusakan, bukan peningkatan.

2. Mode atap benar-benar mengubah angkanya ke arah yang benar: atap pick-up di BAWAH RL nominal
   harus memberi volume LEBIH KECIL, dan besar selisihnya harus sesuai dengan selisih elevasinya.

Pemakaian:
    python tools/uji/uji_atap_asmined.py [port_lama] [port_baru] [--dasar=<ref git>]

Versi pembanding diambil dari git (`--dasar`, bawaan HEAD), jadi ujinya bisa diulang siapa pun.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
# Versi pembanding diambil dari GIT, bukan dari salinan di folder sementara: supaya ujinya bisa
# diulang siapa pun, kapan pun, dan bukan hanya di mesin yang kebetulan menyimpan salinannya.
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")

ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--")]
PORT_LAMA = ARG[0] if ARG else "8791"
PORT_BARU = ARG[1] if len(ARG) > 1 else "8792"

# Satu susunan boundary + pengaturan, dipakai SAMA di kedua versi. Poligon dibuat dari koordinat
# median model supaya benar-benar memotong blok.
JS_SIAPKAN = r"""
(function (rfTurun) {
  var m = BX.m;
  if (!m) return {err: 'belum ada block model'};
  if (typeof amRun !== 'function') return {err: 'amRun tidak tersedia'};

  /* flitch terpadat */
  var zc = {}, i;
  for (i = 0; i < m.n; i++) { var k = Math.round(m.z[i] * 100); zc[k] = (zc[k] || 0) + 1; }
  var zb = null, nb = -1;
  Object.keys(zc).forEach(function (k) { if (zc[k] > nb) { nb = zc[k]; zb = +k / 100; } });
  var xs = [], ys = [];
  for (i = 0; i < m.n; i++) if (Math.abs(m.z[i] - zb) < 1e-6) { xs.push(m.x[i]); ys.push(m.y[i]); }
  xs.sort(function (a, b) { return a - b; });
  ys.sort(function (a, b) { return a - b; });
  var cx = xs[xs.length >> 1], cy = ys[ys.length >> 1], sz = m.sz[0] || 2.5;

  /* flitch aktif: RL atas = zb + sz/2 */
  var L = lyU();
  L.top = zb + sz / 2; L.bot = zb - sz / 2; L.flMode = 'comp'; L.onlyPass = false;
  var U = BX.ui;
  U.sg = 2.6; U.sgCol = ''; U.sgZero = ''; U.sgRep = ''; U.wOn = false;
  L.calcM = 'clip';
  if (window.LY) LY.ix = null;

  /* Boundary as-mined diambil dari amD().bnd (bukan DG.S), disaring per flitch oleh amBndCur().
     Titiknya 2D: lyBB / lyArea memakai [0] dan [1]. */
  var pts = [[cx - 40, cy - 30], [cx + 35, cy - 35], [cx + 40, cy + 30], [cx - 35, cy + 35]];
  var D0 = amD();
  D0.bnd = [{id: 'ujiroof', name: 'UJI_ROOF', pts: pts, top: L.top, bot: L.bot, on: true,
             d: 'ORE', no: 1}];

  /* titik pick-up ATAP: rata, pada RL atas - rfTurun. Grid teratur supaya Python bisa menirunya. */
  var D = D0;
  D.ptsR = [];
  if (rfTurun !== null) {
    for (var a = -40; a <= 40; a += 5) for (var b = -35; b <= 35; b += 5) {
      D.ptsR.push({x: cx + a, y: cy + b, z: L.top - rfTurun, id: '', c: 'ROOF'});
    }
  }
  D.pts = D.pts || [];                 /* lantai dibiarkan kosong: yang diuji atapnya */
  var R = amR();
  R.floor = 'full';                    /* lantai memakai rumus lama, supaya hanya atap yang berubah */
  return {ok: true, zb: zb, sz: sz, cx: cx, cy: cy, top: L.top, bot: L.bot,
          nRoof: D.ptsR.length, luas: lyArea(pts)};
})
"""

JS_HITUNG = r"""
(function (mode) {
  var R = amR();
  if (mode !== null) {
    if (typeof amRoofMode !== 'function') return {err: 'amroof.js tidak terpasang di versi ini'};
    R.roof = mode;
  } else if (R.roof !== undefined) {
    R.roof = 'flitch';
  }
  BX.sc = {};
  /* AM.res diisi amRun per flitch; normalnya dibuat saat tab as-mined dibuka. Di sini dibuat
     sendiri, dan DIKOSONGKAN tiap kali supaya hasil mode sebelumnya tidak terbaca ulang. */
  if (window.AM) { AM.res = {}; AM.msg = ''; }
  try { amRun(true); } catch (e) { return {err: String(e && e.message || e)}; }
  /* AM.res berindeks per flitch: AM.res["<RL atas>_<RL bawah>"] = {top,bot,cells,sum,...} */
  var B = lyBench(), kk = lyFmt(B[0]) + '_' + lyFmt(B[1]);
  var E = (window.AM && AM.res) ? AM.res[kk] : null;
  if (!E || !E.sum) return {err: 'amRun tidak memberi hasil untuk flitch ' + kk +
                                 ' (AM.msg: ' + String((window.AM && AM.msg) || '').slice(0, 160) + ')'};
  var S = E.sum;
  var out = {vol: S.vol, t: S.t, ns: S.ns, ne: S.ne, nf: S.nf, mode: S.mode,
             gA: S.gA, gO: S.gO, nCell: E.cells.length, area: E.area, volP: E.volP,
             roof: (R.roof === undefined ? '(tidak ada)' : R.roof)};
  if (window.AM && AM.jepit) out.jepit = AM.jepit.a;
  return out;
})
"""


def ambil_dasar() -> Path:
    """Tulis app/index.html versi `DASAR` (ref git) ke berkas sementara."""
    r = subprocess.run(["git", "show", "%s:app/index.html" % DASAR], cwd=str(ROOT),
                       capture_output=True)
    if r.returncode != 0 or not r.stdout:
        raise SystemExit("tidak bisa mengambil app/index.html dari %r: %s"
                         % (DASAR, (r.stderr or b"").decode("utf-8", "replace")[:200]))
    d = Path(tempfile.mkdtemp(prefix="gcex_dasar_"))
    f = d / "index.html"
    f.write_bytes(r.stdout)
    return f


def layani(port: str, html: Path, nama: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="gcex_roof_" + nama + "_"))
    shutil.copyfile(html, d / "index.html")
    os.symlink(DATA, d / "data-latihan")
    subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            urllib.request.urlopen("http://localhost:%s/index.html" % port, timeout=1)
            return d
        except Exception:
            time.sleep(0.4)
    raise SystemExit("peladen %s tidak mau hidup" % nama)


def jalankan(pg, url: str, mode_list, rf_turun):
    pg.goto(url)
    pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n > 0", timeout=600000)
    pg.wait_for_function("!DLAT.busy", timeout=600000)
    pg.wait_for_timeout(2000)
    S = pg.evaluate("(%s)(%s)" % (JS_SIAPKAN, json.dumps(rf_turun)))
    if not S or S.get("err"):
        raise SystemExit("siapkan gagal: %s" % (S or {}).get("err"))
    out = {"siap": S, "hasil": {}}
    for mode in mode_list:
        out["hasil"][str(mode)] = pg.evaluate("(%s)(%s)" % (JS_HITUNG, json.dumps(mode)))
    return out


def main() -> int:
    from playwright.sync_api import sync_playwright

    dasar = ambil_dasar()
    print("versi pembanding: app/index.html pada %r" % DASAR)
    layani(PORT_LAMA, dasar, "lama")
    layani(PORT_BARU, ROOT / "app" / "index.html", "baru")
    hasil = {}
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            tempfile.mkdtemp(prefix="gcex_roofctx_"),
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
            viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        galat = []
        pg.on("pageerror", lambda e: galat.append(str(e)[:200]))
        print("  versi LAMA (sebelum perubahan)...", flush=True)
        hasil["lama"] = jalankan(pg, "http://localhost:%s/index.html" % PORT_LAMA, [None], 0.22)
        print("  versi BARU...", flush=True)
        hasil["baru"] = jalankan(pg, "http://localhost:%s/index.html" % PORT_BARU,
                                 [None, "flitch", "flat", "pickup"], 0.22)
        hasil["galat"] = galat
        ctx.close()

    if hasil["galat"]:
        print("galat halaman: %s" % hasil["galat"][:3])
    S = hasil["baru"]["siap"]
    print("flitch RL %.2f-%.2f, luas poligon %.1f m2, %d titik atap pada RL atas - 0,22 m"
          % (S["top"], S["bot"], S["luas"], S["nRoof"]))

    salah = []
    A = hasil["lama"]["hasil"]["None"]
    B = hasil["baru"]["hasil"]["None"]
    for nm, r in (("lama", A), ("baru", B)):
        if r.get("err"):
            salah.append("versi %s gagal menghitung: %s" % (nm, r["err"]))
    if not salah:
        print("\n1. BAWAAN TIDAK MENGUBAH ANGKA LAMA")
        for k in ("vol", "t", "ns", "ne", "nf", "nCell", "area", "volP"):
            a, b = A.get(k), B.get(k)
            sama = (a == b) or (isinstance(a, (int, float)) and isinstance(b, (int, float))
                                and abs(a - b) <= 1e-9 * max(1.0, abs(a)))
            print("   %-5s lama %r vs baru %r  %s" % (k, a, b, "OK" if sama else "BEDA"))
            if not sama:
                salah.append("bawaan mengubah %s: lama %r vs baru %r" % (k, a, b))

        print("\n2. MODE ATAP MENGUBAH ANGKA KE ARAH YANG BENAR")
        F = hasil["baru"]["hasil"]["flitch"]
        FL = hasil["baru"]["hasil"]["flat"]
        PK = hasil["baru"]["hasil"]["pickup"]
        for nm, r in (("flitch", F), ("flat", FL), ("pickup", PK)):
            if r.get("err"):
                salah.append("mode %s gagal: %s" % (nm, r["err"]))
        if not any(r.get("err") for r in (F, FL, PK)):
            print("   flitch  volume %.2f m3" % F["vol"])
            print("   flat    volume %.2f m3  (selisih %+.2f = %+.2f%%)"
                  % (FL["vol"], FL["vol"] - F["vol"],
                     (FL["vol"] - F["vol"]) / F["vol"] * 100 if F["vol"] else 0))
            print("   pickup  volume %.2f m3  (selisih %+.2f = %+.2f%%)"
                  % (PK["vol"], PK["vol"] - F["vol"],
                     (PK["vol"] - F["vol"]) / F["vol"] * 100 if F["vol"] else 0))
            if not (FL["vol"] < F["vol"] - 1e-6):
                salah.append("atap rata 0,22 m di bawah RL nominal TIDAK memberi volume lebih "
                             "kecil (%r vs %r)" % (FL["vol"], F["vol"]))
            if not (PK["vol"] < F["vol"] - 1e-6):
                salah.append("atap permukaan TIDAK memberi volume lebih kecil (%r vs %r)"
                             % (PK["vol"], F["vol"]))
            # titik atap rata & teratur: mode rata dan mode permukaan harus nyaris sama
            if F["vol"] and abs(FL["vol"] - PK["vol"]) > 1e-6 * max(1.0, FL["vol"]):
                salah.append("atap rata dan atap permukaan berbeda pada titik yang SEMUANYA rata: "
                             "%r vs %r" % (FL["vol"], PK["vol"]))
            # besar selisihnya harus masuk akal: 0,22 m dari tebal flitch
            fh = S["top"] - S["bot"]
            harap = 0.22 / fh
            nyata = (F["vol"] - FL["vol"]) / F["vol"] if F["vol"] else 0
            print("   selisih relatif %.4f, diperkirakan %.4f (0,22 m dari tebal flitch %.2f m)"
                  % (nyata, harap, fh))
            if abs(nyata - harap) > 0.02:
                salah.append("besar selisih tidak masuk akal: %.4f vs perkiraan %.4f"
                             % (nyata, harap))

    if salah:
        print("\nADA YANG SALAH (%d):" % len(salah))
        for x in salah:
            print("  ! %s" % x)
        return 1
    print("\nSEMUA BENAR: bawaan tidak mengubah angka lama, dan mode atap bekerja seperti "
          "yang diharapkan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
