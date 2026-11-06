# -*- coding: utf-8 -*-
"""Paritas 'Ringkasan seluruh model per RL': jalur LOKAL (JS, di aplikasi) vs jalur BACKEND (Python).

Fitur ini punya dua pelaksana untuk pekerjaan yang sama: `bsLocal` di web-src/mdlsum.js untuk model
yang sudah dimuat penuh, dan `bench_summary` di backend/gcex_backend/mdl_io.py untuk .mdl besar yang
hanya dimuat sepotong. Dua pelaksana untuk satu angka produksi adalah cara paling sunyi untuk
menghasilkan dua jawaban berbeda: yang satu diperbaiki, yang lain tidak, dan tidak ada yang tahu
sampai rekonsiliasi.

Jadi di sini keduanya dijalankan atas blok yang SAMA PERSIS dan dibandingkan baris per baris:
.mdl sintetis dibaca backend, dan blok yang sama ditulis sebagai CSV lalu dimuat ke aplikasi
sungguhan di peramban. Yang diperiksa: jumlah baris bench, RL atas / bawah, jumlah blok, volume,
ton, dan kadar tiap atribut -- termasuk saat ada cut-off dan saat SG diambil dari kolom.
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
PORT = sys.argv[1] if len(sys.argv) > 1 else "8811"
# Toleransi relatif 1e-6, bukan nol. Sebabnya BUKAN rumus: sisi backend membaca nilai AU sebagai
# double penuh dari .mdl, sedangkan sisi aplikasi membacanya dari CSV yang ditulis 6 desimal. Selisih
# yang tersisa berada di kisaran 1e-9 relatif (mis. 143.691.923,6067 vs ...,8321 pada total 1,4e8).
# Kalau rumusnya yang berbeda, selisihnya akan jauh melampaui ini, bukan di digit ke-10.
TOL = 1e-6

sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))


def buat_mdl(tmp: Path):
    """.mdl sintetis + CSV berisi blok yang sama persis, dibaca langsung dari cache backend."""
    from test_mdl_io import make_mdl          # noqa: E402
    from gcex_backend import mdl_io           # noqa: E402
    os.environ["GCEX_CACHE"] = str(tmp / "cache")
    f = tmp / "uji_rl.mdl"
    make_mdl(f, n=4000, seed=7)
    for _ in range(200):
        st = mdl_io.open_model(str(f))
        if st.get("state") != "building":
            break
        time.sleep(0.3)
    c, m = mdl_io.open_cache(str(f))
    import numpy as np
    lv = np.asarray(c.col("lv", "u1")[:], dtype=np.int64)
    fct = np.power(2.0, -lv.astype(np.float64))
    RT = m["root"]
    x = np.asarray(c.col("x", "<f8")[:]); y = np.asarray(c.col("y", "<f8")[:]); z = np.asarray(c.col("z", "<f8")[:])
    names = [a["name"] for a in c.ST]
    au = np.asarray(c.col("f%d" % names.index("au"), "<f8")[:], dtype=np.float64)
    # Kolom SG diisi nilai AU: .mdl sintetis hanya punya satu atribut angka (`au`), jadi supaya kedua
    # sisi memakai ANGKA YANG SAMA sebagai kolom SG, kolomnya memang nilai AU. Kolom SG0 (sebagian
    # <= 0) tidak ada di .mdl dan hanya dipakai untuk menguji aturan SG di sisi lokal, terhadap
    # hitungan langsung dari CSV yang sama.
    hdr = ["X", "Y", "Z", "DX", "DY", "DZ", "AU", "SG", "SG0"]
    sg0 = np.where((np.arange(len(z)) % 7) == 0, 0.0, 2.2 + (np.arange(len(z)) % 5) * 0.15)
    rows = [",".join(hdr)]
    vol = []
    for i in range(len(z)):
        dx, dy, dz = RT[0] * fct[i], RT[1] * fct[i], RT[2] * fct[i]
        vol.append(dx * dy * dz)
        rows.append("%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.4f" % (
            x[i], y[i], z[i], dx, dy, dz, au[i], au[i], sg0[i]))
    csv = tmp / "uji_rl.csv"
    csv.write_text("\n".join(rows), encoding="utf-8")
    return f, csv, {"z": z, "vol": np.asarray(vol), "au": au, "sg0": sg0}


def backend(path: Path, bench, ref, attrs, sg_col, cut_attr=None, cut=None, sg=2.6, sg_zero="rep", sg_rep=None):
    from gcex_backend import mdl_io           # noqa: E402
    return mdl_io.bench_summary(str(path), bench, ref, attrs, sg_col, sg, sg_zero, sg_rep, cut_attr, cut)


JS = r"""
(function (par) {
  var U = BX.ui;
  U.sg = par.sg; U.sgCol = par.sgCol || ''; U.sgZero = par.sgZero || 'rep'; U.sgRep = par.sgRep || '';
  var S = {bench: par.bench, ref: par.ref, cut: par.cut == null ? '' : String(par.cut), cutA: par.cutA || ''};
  if (typeof bsLocal !== 'function') return {err: 'bsLocal tidak ada'};
  try {
    var R = bsLocal(S, par.attrs);
    return {rows: R.rows.map(function (r) {
      return {top: r.top, bot: r.bot, n: r.n, vol: r.vol, ton: r.ton,
              grade: par.attrs.map(function (a) { return r.grade[a]; })};
    }), total: {n: R.total.n, vol: R.total.vol, ton: R.total.ton,
                grade: par.attrs.map(function (a) { return R.total.grade[a]; })}};
  } catch (e) { return {err: String(e && e.message || e)}; }
})
"""


def dekat(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def main() -> int:
    from playwright.sync_api import sync_playwright
    tmp = Path(tempfile.mkdtemp(prefix="gcex_rl_"))
    mdl, csv, BLK = buat_mdl(tmp)
    print("blok uji: %s" % csv.name)

    srv = Path(tempfile.mkdtemp(prefix="gcex_rlsrv_"))
    shutil.copyfile(ROOT / "app" / "index.html", srv / "index.html")
    shutil.copyfile(csv, srv / "uji_rl.csv")
    # Sumber viewer baru di-eval setelah proyek dibuka (SA.boot -> evalJs #vsrc), jadi fungsi seperti
    # bxDlg belum ada sebelum itu. Data latihan dipakai hanya untuk membuka proyek; block model-nya
    # langsung diganti dengan CSV uji di bawah.
    os.symlink(ROOT / "docs" / "tutorial-gcex" / "data", srv / "data-latihan")
    subprocess.Popen([sys.executable, "-m", "http.server", PORT], cwd=str(srv),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            urllib.request.urlopen("http://localhost:%s/index.html" % PORT, timeout=1); break
        except Exception:
            time.sleep(0.4)

    KASUS = [
        ("SG tetap, tanpa cut-off", dict(bench=10, ref=0, attrs=["AU"], sgCol="", sg=2.6)),
        ("SG dari kolom", dict(bench=10, ref=0, attrs=["AU"], sgCol="SG", sg=2.6)),
        ("cut-off AU >= 1,5", dict(bench=10, ref=0, attrs=["AU"], sgCol="SG", sg=2.6, cut=1.5, cutA="AU")),
        ("bench 7,5 m, acuan RL 2,5", dict(bench=7.5, ref=2.5, attrs=["AU"], sgCol="", sg=2.6)),
        ("bench 25 m, acuan RL -12,5", dict(bench=25, ref=-12.5, attrs=["AU"], sgCol="SG", sg=2.6)),
    ]
    salah = []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(prefix="gcex_rlctx_"),
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
            viewport={"width": 1400, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        galat = []; pg.on("pageerror", lambda e: galat.append(str(e)[:160]))
        pg.goto("http://localhost:%s/index.html" % PORT); pg.wait_for_timeout(1200)
        pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
        pg.evaluate("document.getElementById('dlatBtn').click()")
        pg.wait_for_function("typeof window.bxDlg==='function'", timeout=600000)
        pg.wait_for_function("!DLAT.busy", timeout=600000)
        pg.wait_for_timeout(1500)
        # jalur import yang sama dengan yang dipakai pengguna: dialog Import block model
        # bxDlg() tidak terjangkau dari page.evaluate (lingkup modul), jadi tombolnya yang diklik
        pg.evaluate("document.querySelector('button[onclick*=bxDlg]').click()")
        pg.wait_for_selector("#bxDlg input[type=file]", state="attached", timeout=30000)
        pg.set_input_files("#bxDlg input[type=file]", str(srv / "uji_rl.csv"))
        pg.wait_for_function("document.getElementById('bxGo') && !document.getElementById('bxGo').disabled",
                             timeout=180000)
        pg.evaluate("document.getElementById('bxGo').click()")
        pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=180000)
        pg.wait_for_timeout(1200)
        n = pg.evaluate("BX.m.n")
        print("block model dimuat di aplikasi: %d blok" % n)

        for nama, par in KASUS:
            # backend memakai nama atribut huruf kecil seperti di .mdl
            batt = [a.lower() for a in par["attrs"]]
            # Kolom "SG" di CSV berisi nilai AU (lihat buat_mdl), jadi padanannya di .mdl adalah `au`.
            B = backend(mdl, par["bench"], par["ref"], batt,
                        "au" if par.get("sgCol") else None,
                        cut_attr=par.get("cutA", "").lower() or None, cut=par.get("cut"),
                        sg=par.get("sg", 2.6), sg_zero=par.get("sgZero", "rep"),
                        sg_rep=float(par["sgRep"]) if par.get("sgRep") else None)
            L = pg.evaluate("(%s)(%s)" % (JS, json.dumps(par)))
            if L.get("err"):
                salah.append("%s: jalur lokal gagal: %s" % (nama, L["err"])); continue
            br, lr = B["rows"], L["rows"]
            print("\n%s" % nama)
            print("   bench: backend %d baris, lokal %d baris" % (len(br), len(lr)))
            if len(br) != len(lr):
                salah.append("%s: jumlah bench beda (%d vs %d)" % (nama, len(br), len(lr))); continue
            beda = 0
            for i, (b, l) in enumerate(zip(br, lr)):
                for k in ("top", "bot", "vol", "ton"):
                    if not dekat(b[k], l[k]):
                        salah.append("%s: bench %d %s beda: backend %r vs lokal %r" % (nama, i, k, b[k], l[k])); beda += 1
                if b["n"] != l["n"]:
                    salah.append("%s: bench %d jumlah blok beda: %r vs %r" % (nama, i, b["n"], l["n"])); beda += 1
                for j, a in enumerate(batt):
                    if not dekat(b["grade"][a], l["grade"][j]):
                        salah.append("%s: bench %d kadar %s beda: %r vs %r" % (nama, i, a, b["grade"][a], l["grade"][j])); beda += 1
            T, LT = B["total"], L["total"]
            print("   total: %d blok, %.4f m3, %.4f t (backend) | %d blok, %.4f m3, %.4f t (lokal)"
                  % (T["n"], T["vol"], T["ton"], LT["n"], LT["vol"], LT["ton"]))
            for k in ("vol", "ton"):
                if not dekat(T[k], LT[k]):
                    salah.append("%s: TOTAL %s beda: %r vs %r" % (nama, k, T[k], LT[k]))
            if T["n"] != LT["n"]:
                salah.append("%s: TOTAL jumlah blok beda: %r vs %r" % (nama, T["n"], LT["n"]))
            for j, a in enumerate(batt):
                if not dekat(T["grade"][a], LT["grade"][j]):
                    salah.append("%s: TOTAL kadar %s beda: %r vs %r" % (nama, a, T["grade"][a], LT["grade"][j]))
            print("   %s" % ("SAMA PERSIS" if not beda else "%d beda" % beda))
        # ---- aturan SG <= 0 (kolom SG0): dibanding hitungan langsung dari CSV yang sama ----
        import numpy as np
        for nama, zero, rep in (("SG<=0 diganti 2,8", "rep", 2.8), ("SG<=0 dianggap 0 (Surpac)", "zero", None)):
            par = dict(bench=10, ref=0, attrs=["AU"], sgCol="SG0", sg=2.6, sgZero=zero,
                       sgRep=("2.8" if rep else ""))
            L = pg.evaluate("(%s)(%s)" % (JS, json.dumps(par)))
            if L.get("err"):
                salah.append("%s: jalur lokal gagal: %s" % (nama, L["err"])); continue
            s0 = BLK["sg0"]
            sg = np.where(s0 > 0, s0, (0.0 if zero == "zero" else rep))
            ton = float((BLK["vol"] * sg).sum())
            vol = float(BLK["vol"].sum())
            g = float((BLK["au"] * BLK["vol"] * sg).sum() / ton) if ton else None
            print("\n%s" % nama)
            print("   total ton: hitungan langsung %.4f | aplikasi %.4f" % (ton, L["total"]["ton"]))
            if not dekat(ton, L["total"]["ton"]):
                salah.append("%s: TOTAL ton beda: %r vs %r" % (nama, ton, L["total"]["ton"]))
            if not dekat(vol, L["total"]["vol"]):
                salah.append("%s: TOTAL volume beda: %r vs %r" % (nama, vol, L["total"]["vol"]))
            if not dekat(g, L["total"]["grade"][0]):
                salah.append("%s: TOTAL kadar AU beda: %r vs %r" % (nama, g, L["total"]["grade"][0]))
        if galat:
            print("\ngalat halaman: %s" % galat[:3])
        ctx.close()

    print()
    if salah:
        print("GAGAL (%d):" % len(salah))
        for x in salah[:25]:
            print("  - %s" % x)
        return 1
    print("SEMUA BENAR: jalur lokal (JS) dan jalur backend (Python) memberi angka yang sama\n"
          "(dalam 1e-6 relatif; sisanya pembulatan 6 desimal di CSV, bukan perbedaan rumus).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
