# -*- coding: utf-8 -*-
"""Uji paritas: penyimpanan string dig block penampil Qt vs berkas proyek aplikasi HTML.

Tiga hal diuji, dan ketiganya bisa salah TANPA memunculkan galat apa pun:

1. `FP.hash` -- hash isi berkas proyek. Kalau salinan Python-nya berbeda, berkas yang ditulis Qt
   dianggap rusak oleh pihak mana pun yang memeriksanya, dan sebaliknya.
2. `offX` / `offY` -- titik hasil digitasi aplikasi HTML tersimpan RELATIF terhadap offset ini,
   sementara block model memakai koordinat penuh. Salah hitung satu kali saja memindahkan
   poligon ratusan kilometer: berkasnya tetap sah, gambarnya saja kosong.
3. Membaca `body.work.dg` dari berkas `gcex_project.json` sungguhan yang dibuat `FP.pack` +
   `SA.collectWork` di aplikasi -- bukan dari berkas tiruan yang saya buat sendiri, sebab berkas
   tiruan hanya membuktikan Python cocok dengan dugaan Python.

Pemakaian:
    python tools/uji/paritas_simpan_galian.py [port] [--fixture]
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from qtbm import simpan_galian as SG                                 # noqa: E402
from qtbm.proyek import Proyek                                       # noqa: E402

ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--")]
FIXTURE = "--fixture" in sys.argv
PORT = ARG[0] if ARG else "8783"
SRV = ROOT / "tools" / "uji" / "_srv_bm"
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
BEKU = ROOT / "qtbm" / "tests" / "data" / "simpan_galian_js.json"

TEKS_HASH = ["", "a", "halo dunia", '{"dg":[]}', "ORE kanan · 5,5 m²",
             "emoji \U0001f600 di keterangan", "garis\nbaru\tdan \"kutip\"",
             "angka 1234567890 " * 7]

JS = r"""
(function (teks) {
  if (typeof FP === 'undefined' || typeof FP.hash !== 'function') return {err: 'FP.hash tidak ada'};
  if (typeof offX !== 'number') return {err: 'offX belum ada (data belum dimuat?)'};
  var out = {hash: {}, offX: offX, offY: offY,
             nCollar: (window.collars || []).length,
             anch: window.ANCH || null, zone: String(window.ZONE || '')};
  teks.forEach(function (t) { out.hash[t] = FP.hash(t); });

  /* minX/minY mentah, supaya rumus pembulatan ke ribuan ikut teruji dan bukan hanya hasilnya */
  var mnx = Infinity, mny = Infinity;
  (window.collars || []).forEach(function (c) {
    if (c[1] < mnx) mnx = c[1];
    if (c[2] < mny) mny = c[2];
  });
  out.minX = isFinite(mnx) ? mnx : null;
  out.minY = isFinite(mny) ? mny : null;

  /* string dig block buatan: dipasang ke DG.S lalu berkas proyek SUNGGUHAN dibuat dengan
     FP.pack + SA.collectWork, sehingga yang dibaca Python adalah berkas asli aplikasi. */
  var simpan = DG.S;
  DG.S = [
    {no: 3, d: 'ORE', closed: true, vis: true, col: '#2f9e44',
     pts: [[120.5, 240.25, 237.5], [160.5, 240.25, 237.5], [160.5, 280.75, 237.5]]},
    {no: 4, d: 'WASTE kanan', closed: false, vis: false, col: '#c2255c',
     pts: [[10.125, 20.5, 240], [30.25, 40.75, 240]]}
  ];
  out.dg = JSON.parse(JSON.stringify(DG.S));
  try {
    /* `encTA` (penyandi larik bertipe) tidak terjangkau dari luar lingkupnya, jadi dipakai bila
       ada dan dilewati bila tidak. Itu sah untuk uji ini: bagian `dg` yang dibaca Qt berisi
       angka biasa, tidak ada larik bertipe di dalamnya. Yang penting hash dihitung oleh
       FP.pack ASLI atas body yang sama persis dengan yang dibaca Python. */
    var rep = (typeof encTA === 'function') ? encTA : (window.encTA || undefined);
    out.pakaiEncTA = !!rep;
    var W = SA.collectWork();
    /* bagian berat & bergantung larik bertipe dibuang: yang diuji penyimpanan STRING */
    delete W.bx; delete W.bxui; delete W.bm; delete W.md; delete W.gs; delete W.ui;
    var body = JSON.stringify({work: W, dataHash: 'x', dataFile: FP.DATAF}, rep);
    var P = FP.pack({format: 'gcex-project', version: 2, app: 'GC-Ex Block Model',
                     name: String(SA.pname || 'uji'), rev: 7,
                     savedAt: new Date().toISOString(), savedBy: 'uji', session: 's',
                     why: 'uji paritas'}, body);
    out.proyek = P.text;
    out.bodyHash = P.hash;
  } catch (e) {
    out.err2 = String(e && e.message || e);
  }
  DG.S = simpan;
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
            tempfile.mkdtemp(prefix="gcex_sg_"),
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
            viewport={"width": 1400, "height": 900})
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
        d = pg.evaluate("(%s)(%s)" % (JS, json.dumps(TEKS_HASH)))
        if d is None or d.get("err"):
            raise SystemExit("gagal: %s" % (d or {}).get("err", "tidak ada hasil"))
        d["galatHalaman"] = galat
        ctx.close()
    return d


# ---------------------------------------------------------------- perbandingan

def bandingkan_hash(d: dict) -> list:
    salah = []
    for t, h in (d.get("hash") or {}).items():
        p = SG.hash_fp(t)
        if p != h:
            salah.append("FP.hash(%r): JS %s vs Python %s" % (t[:40], h, p))
    return salah


def bandingkan_offset(d: dict) -> list:
    """Rumus offX/offY Qt harus memberi angka yang sama dengan aplikasi."""
    P = Proyek()
    P.data = {"collars": [["h", d["minX"], d["minY"], 0, 0]] if d.get("minX") is not None else [],
              "anch": d.get("anch")}
    ox, oy = P.offset()
    salah = []
    if ox != d["offX"] or oy != d["offY"]:
        salah.append("offset: JS (%r, %r) vs Python (%r, %r)" % (d["offX"], d["offY"], ox, oy))
    # tanpa collar dan tanpa anch harus nol, seperti `if(!isFinite(minX)){minX=0;minY=0;}`
    K = Proyek()
    K.data = {}
    if K.offset() != (0.0, 0.0):
        salah.append("tanpa collar & tanpa anch seharusnya (0, 0), dapat %r" % (K.offset(),))
    return salah


def bandingkan_proyek(d: dict) -> list:
    """Baca berkas gcex_project.json SUNGGUHAN buatan aplikasi, lalu cocokkan stringnya."""
    teks = d.get("proyek")
    if not teks:
        return ["berkas proyek tidak terekam: %s" % d.get("err2", "tidak diketahui")]
    salah = []
    try:
        meta, body = SG.unpack(teks)
    except Exception as e:                          # noqa: BLE001
        return ["unpack gagal pada berkas asli aplikasi: %s: %s" % (type(e).__name__, e)]
    if meta.get("hash") != d.get("bodyHash"):
        salah.append("hash body: JS %r vs yang terbaca %r" % (d.get("bodyHash"), meta.get("hash")))
    dg = ((body.get("work") or {}).get("dg")) or []
    if len(dg) != len(d["dg"]):
        salah.append("jumlah string: JS %d vs terbaca %d" % (len(d["dg"]), len(dg)))
        return salah

    import tempfile as _tf
    ox, oy = float(d["offX"]), float(d["offY"])
    with _tf.TemporaryDirectory() as td:
        (Path(td) / SG.BERKAS_PROYEK).write_text(teks, encoding="utf-8")
        S = SG.baca_string_html(td, ox, oy)
        if len(S) != len(d["dg"]):
            salah.append("baca_string_html memberi %d string, seharusnya %d"
                         % (len(S), len(d["dg"])))
            return salah
        for a, s in zip(d["dg"], S):
            if int(a["no"]) != s.no or str(a["d"]) != s.ket or bool(a["closed"]) != s.tertutup:
                salah.append("string #%s: no/ket/tertutup tidak cocok" % a["no"])
            if bool(a["vis"]) != s.tampil:
                salah.append("string #%s: penanda tampil tidak cocok" % a["no"])
            for q, p in zip(a["pts"], s.pts):
                # Qt memakai koordinat PENUH: titik HTML + offset
                for k, (jv, pv) in enumerate(zip((q[0] + ox, q[1] + oy, q[2]), p)):
                    if abs(jv - pv) > 1e-9:
                        salah.append("string #%s titik sumbu %d: %r vs %r" % (a["no"], k, jv, pv))

        # bolak-balik: tulis dengan Qt, baca lagi, harus kembali ke angka yang sama
        SG.tulis(td, S, ox, oy, nama_proyek="uji")
        S2, m2 = SG.baca(td)
        if len(S2) != len(S):
            salah.append("tulis lalu baca memberi %d string, seharusnya %d" % (len(S2), len(S)))
        else:
            for a, b in zip(S, S2):
                if a.no != b.no or a.ket != b.ket or a.tertutup != b.tertutup:
                    salah.append("bolak-balik string #%s: keterangan berubah" % a.no)
                for pa, pb in zip(a.pts, b.pts):
                    for k in range(3):
                        if abs(pa[k] - pb[k]) > 1e-9:
                            salah.append("bolak-balik string #%s sumbu %d: %r vs %r"
                                         % (a.no, k, pa[k], pb[k]))
        if m2.get("format") != SG.FORMAT_QT:
            salah.append("meta berkas Qt tidak berformat %s" % SG.FORMAT_QT)
        # berkas proyek aplikasi TIDAK BOLEH tersentuh
        if (Path(td) / SG.BERKAS_PROYEK).read_text(encoding="utf-8") != teks:
            salah.append("gcex_project.json BERUBAH: penampil Qt tidak boleh menulis ke situ")
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
    print("offX/offY aplikasi: %r / %r (dari %d collar)"
          % (d["offX"], d["offY"], d.get("nCollar", 0)))
    salah = bandingkan_hash(d) + bandingkan_offset(d) + bandingkan_proyek(d)
    print("yang diuji: FP.hash (%d teks), offX/offY, baca gcex_project.json asli, bolak-balik "
          "berkas Qt" % len(d.get("hash") or {}))
    if salah:
        print("\nTIDAK SAMA (%d):" % len(salah))
        for s in salah:
            print("  ! %s" % s)
        return 1
    print("\nSEMUA SAMA PERSIS: penyimpanan string Qt sejalan dengan berkas proyek aplikasi HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
