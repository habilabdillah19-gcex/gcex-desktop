# -*- coding: utf-8 -*-
"""Uji metode tonase: Audit CSV dig block & tab "Metode tonase" di Reporting BM.

Dipakai karena inilah angka yang pernah diperdebatkan antara hitungan Surpac dan hitungan GC-Ex.
Yang diuji bukan "tombolnya ada", melainkan bahwa angkanya saling konsisten:

  1. Audit CSV dig block: kolom "Ton presisi + waste" HARUS sama dengan tonase yang ditampilkan
     panel Dig block. Sebelum kolom waste pengisi ditambahkan, keduanya tidak pernah cocok --
     panel memuat waste pengisi (area poligon tanpa blok BM), ekspornya tidak -- dan selisih itu
     tidak bisa dijelaskan oleh siapa pun yang memegang ekspornya.
  2. Tab "Metode tonase" di Reporting BM: baris "Seperti Surpac" harus sama persis dengan laporan
     biasa tanpa pembobotan, dan baris "Presisi GC-Ex" sama persis dengan laporan biasa dengan
     pembobotan proporsi. Tab itu memang menjalankan rpRun() yang sama, jadi kalau sampai berbeda
     berarti ada yang salah dalam cara ia menyetel pilihannya.
  3. Kedua aplikasi (Block Model & Drill Hole) diuji, karena sakelar pembobotannya BERBEDA
     bentuknya: Block Model memakai boolean, Drill Hole memakai nama atribut. Pernah salah tebak,
     akibatnya tonase "presisi" keluar sama dengan "Surpac" tanpa tanda apa pun bahwa ada yang
     salah -- justru kesalahan yang paling berbahaya.

Pemakaian:
    python tools/uji/uji_metode_tonase.py [--port 8785]
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
PORT = "8785"
for i, a in enumerate(sys.argv):
    if a == "--port" and i + 1 < len(sys.argv):
        PORT = sys.argv[i + 1]


def siapkan(app: str) -> Path:
    srv = ROOT / "tools" / "uji" / ("_srv_bm" if app == "bm" else "_srv_dh")
    srv.mkdir(parents=True, exist_ok=True)
    (srv / "index.html").write_bytes((ROOT / ("app" if app == "bm" else "app-dh") / "index.html").read_bytes())
    t = srv / "data-latihan"
    if t.is_symlink():
        t.unlink()
    if not t.exists():
        os.symlink(DATA, t)
    return srv


def layani(srv: Path, port: str) -> str:
    url = "http://localhost:%s/index.html" % port
    try:
        urllib.request.urlopen(url, timeout=2)
    except Exception:
        subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(srv),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    return url


# ---------------------------------------------------------------------------
# 1. Audit CSV dig block (hanya ada di GC-Ex Block Model)
# ---------------------------------------------------------------------------
SIAP_DIG = r"""(function(){
  var m=BX.m, L=lyU(), ox=window.offX||0, oy=window.offY||0;
  var X=[].slice.call(m.x), Y=[].slice.call(m.y), Z=[].slice.call(m.z);
  var cx=(Math.min.apply(null,X)+Math.max.apply(null,X))/2, cy=(Math.min.apply(null,Y)+Math.max.apply(null,Y))/2;
  var zs=Z.slice().sort(function(a,b){return a-b;}), zmid=zs[Math.floor(zs.length/2)], sz=m.sz[0];
  L.fh=sz; L.top=zmid+sz/2;
  /* poligon sengaja berukuran 31,7 m (BUKAN kelipatan ukuran blok 5 m) supaya tepinya memotong
     blok -- di situlah kedua metode berbeda */
  var r=31.7, pts=[[cx-ox-r,cy-oy-r,zmid],[cx-ox+r,cy-oy-r,zmid],[cx-ox+r,cy-oy+r,zmid],[cx-ox-r,cy-oy+r,zmid]];
  DG.S.push({closed:true,inner:false,vis:true,no:1,d:'ORE',pts:pts});
  L.calcM='clip';
  var it=lyItems();
  if(!it.length) return {err:'dig block tidak terbentuk'};
  return {ton_panel: it[0].ton.t, waste_ton: it[0].ton.wT||0, blok_ton: it[0].ton.t-(it[0].ton.wT||0),
          wOn: !!dbU().wOn, luas: it[0].area};
})()"""


def uji_audit(pg, galat: list) -> None:
    d = pg.evaluate(SIAP_DIG)
    if d.get("err"):
        galat.append("dig block: %s" % d["err"])
        return
    print("  panel Dig block: %.2f t (blok %.2f t + waste pengisi %.2f t, pilihan waste %s)"
          % (d["ton_panel"], d["blok_ton"], d["waste_ton"], "menyala" if d["wOn"] else "mati"), flush=True)
    with pg.expect_download(timeout=300000) as dl:
        pg.evaluate("lyAuditCsv()")
    f = Path(tempfile.mkdtemp()) / "audit.csv"
    dl.value.save_as(str(f))
    baris = [b for b in f.read_text(encoding="utf-8-sig").splitlines() if b.strip()]
    hdr = next((b for b in baris if b.startswith("RINGKASAN")), None)
    if not hdr:
        galat.append("Audit CSV tidak memuat baris RINGKASAN")
        return
    kol = hdr.split(";")
    isi = baris[baris.index(hdr) + 1].split(";")
    peta = dict(zip(kol, isi))
    for k in ("Ton presisi", "Waste pengisi m2", "Ton waste pengisi", "Ton presisi + waste", "Ton Surpac"):
        if k not in peta:
            galat.append("Audit CSV tidak punya kolom '%s'" % k)
    if galat:
        return
    ang = lambda s: float(str(s).replace(".", "").replace(",", "."))
    total = ang(peta["Ton presisi + waste"])
    print("  Audit CSV     : presisi %.2f t + waste %.2f t = %.2f t | Surpac %.2f t"
          % (ang(peta["Ton presisi"]), ang(peta["Ton waste pengisi"]), total, ang(peta["Ton Surpac"])), flush=True)
    if abs(total - d["ton_panel"]) > 0.05:
        galat.append("total Audit CSV (%.2f t) tidak sama dengan tonase panel (%.2f t)"
                     % (total, d["ton_panel"]))
    if abs(ang(peta["Ton waste pengisi"]) - d["waste_ton"]) > 0.05:
        galat.append("waste pengisi di Audit CSV (%.2f t) tidak sama dengan di panel (%.2f t)"
                     % (ang(peta["Ton waste pengisi"]), d["waste_ton"]))
    if d["wOn"] and not (ang(peta["Ton waste pengisi"]) > 0):
        galat.append("pilihan waste pengisi menyala tetapi kolomnya nol")


# ---------------------------------------------------------------------------
# 2. Tab "Metode tonase" di Reporting BM (kedua aplikasi)
# ---------------------------------------------------------------------------
SIAP_REP = r"""(function(){
  var m=BX.m, o=rpO();
  var nums=Object.keys(m.num).filter(function(a){return a!=='sb_frac';});
  o.gr = m.num['AU_GC']?'AU_GC':nums[0];
  o.atts=[o.gr]; o.unit=o.unit||{}; o.unit[o.gr]='g/t';
  o.cuts='0'; o.grp='none'; o.dom='all'; o.surf='none'; o.sx=[]; o.poly='';
  o.fA=''; o.show=false; o.z0=''; o.z1='';
  /* sb_frac buatan 0,4 di separuh blok: cukup untuk membuat kedua metode berbeda, tanpa perlu
     membangun solid (itu diuji terpisah di paritas_subblok.py) */
  var F=new Float32Array(m.n); for(var i=0;i<m.n;i++) F[i]=(i%2===0)?0.4:1;
  m.num['sb_frac']=F; BX.ver=(BX.ver||0)+1; BX.sc={};
  /* rpDef() global hanya ada di Drill Hole; di Block Model ia lokal di dalam IIFE-nya. Jadi
     bentuk sakelar ditentukan dengan cara yang sama seperti modulnya sendiri. */
  var nama = (typeof rpDef==='function') ? (typeof rpDef().frac==='string') : ((window.GCEX_APP||'')==='dh');
  return {gr:o.gr, bentuk_frac: nama?'nama atribut':'boolean'};
})()"""

BANDING = r"""(function(){
  var o=rpO();
  var nama = (typeof rpDef==='function') ? (typeof rpDef().frac==='string') : ((window.GCEX_APP||'')==='dh');
  /* fungsi penjumlah Reporting tidak global di Block Model: jumlahkan sendiri, rumus sama */
  var jum=function(G){var r={n:0,v:0,t:0};Object.keys(G).forEach(function(k){r.n+=G[k].n;r.v+=G[k].v;r.t+=G[k].t;});return r;};
  var hasil={};
  [['tanpa', nama?'':false], ['dengan', nama?'sb_frac':true]].forEach(function(q){
    o.frac=q[1]; rpRun();
    var T=jum(RP.res.rows[0].G);
    hasil[q[0]]={ton:T.t, vol:T.v, n:T.n};
  });
  var X=RPM.res;
  return {laporan:hasil,
          tab:{surpac:{ton:X.surpac.rows[0].t, vol:X.surpac.rows[0].v, n:X.surpac.rows[0].n},
               presisi:X.presisi?{ton:X.presisi.rows[0].t, vol:X.presisi.rows[0].v, n:X.presisi.rows[0].n}:null},
          rinci:X.rinci, attr:X.attr};
})()"""


def uji_reporting(pg, galat: list, app: str) -> None:
    d = pg.evaluate(SIAP_REP)
    print("  atribut kadar %s | bentuk sakelar proporsi: %s" % (d["gr"], d["bentuk_frac"]), flush=True)
    pg.evaluate("RP.sec='2';rpPanel();")
    pg.wait_for_timeout(600)                      # pengamat DOM bekerja asinkron
    if not pg.evaluate("!!document.querySelector('#rpBody .rpmtab')"):
        galat.append("%s: tab 'Metode tonase' tidak tersisip di bilah tab Reporting" % app)
    pg.evaluate("RPM.run()")
    pg.wait_for_function("window.RPM && !RPM.busy && (RPM.res || RPM.msg)", timeout=600000)
    if not pg.evaluate("!!RPM.res"):
        galat.append("%s: tab Metode tonase gagal: %s" % (app, pg.evaluate("RPM.msg")))
        return
    r = pg.evaluate(BANDING)
    L, T = r["laporan"], r["tab"]
    if T["presisi"] is None:
        galat.append("%s: baris presisi tidak dihitung padahal sb_frac ada" % app)
        return
    print("  Seperti Surpac: %.2f t (laporan biasa %.2f t) | Presisi GC-Ex: %.2f t (laporan biasa %.2f t)"
          % (T["surpac"]["ton"], L["tanpa"]["ton"], T["presisi"]["ton"], L["dengan"]["ton"]), flush=True)
    print("  rincian proporsi: %s" % (r["rinci"],), flush=True)
    for nama, a, b in (("Seperti Surpac", T["surpac"]["ton"], L["tanpa"]["ton"]),
                       ("Presisi GC-Ex", T["presisi"]["ton"], L["dengan"]["ton"])):
        if abs(a - b) > 1e-6 * max(1.0, abs(b)):
            galat.append("%s: baris '%s' (%.4f t) tidak sama dengan laporan biasa (%.4f t)"
                         % (app, nama, a, b))
    if not (T["presisi"]["ton"] < T["surpac"]["ton"]):
        galat.append("%s: pembobotan proporsi tidak mengurangi tonase -- sakelarnya tidak kena"
                     % app)


# ---------------------------------------------------------------------------
def jalankan(app: str, galat: list) -> None:
    from playwright.sync_api import sync_playwright

    srv = siapkan(app)
    url = layani(srv, PORT if app == "bm" else str(int(PORT) + 1))
    print("== %s ==" % ("GC-Ex Block Model" if app == "bm" else "GC-Ex Drill Hole"), flush=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            tempfile.mkdtemp(prefix="mtd_"),
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
            viewport={"width": 1500, "height": 900}, accept_downloads=True)
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};window.showSaveFilePicker=undefined;")  # gxSimpan (DB-Ex 0.44.1) memakai pemilih berkas; headless menggantung
        pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.on("pageerror", lambda e: galat.append("%s: galat halaman: %s" % (app, str(e)[:160])))
        pg.goto(url)
        pg.wait_for_timeout(1500)
        pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
        print("  memuat data latihan...", flush=True)
        pg.evaluate("document.getElementById('dlatBtn').click()")
        pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000)
        pg.wait_for_function("!DLAT.busy", timeout=600000)
        pg.wait_for_timeout(2500)
        if app == "bm":
            uji_audit(pg, galat)
        uji_reporting(pg, galat, app)
        ctx.close()


def main() -> int:
    galat: list = []
    for app in ("bm", "dh"):
        try:
            jalankan(app, galat)
        except Exception as e:
            galat.append("%s: %s" % (app, e))
    print()
    if galat:
        print("TIDAK LULUS (%d temuan):" % len(galat))
        for g in galat:
            print("  -", g)
        return 1
    print("LULUS: total Audit CSV cocok dengan panel Dig block, dan kedua baris di tab "
          "Metode tonase cocok dengan laporan biasa di kedua aplikasi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
