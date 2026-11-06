# -*- coding: utf-8 -*-
"""Uji paritas: dig block di penampil Qt harus SAMA dengan dig block aplikasi HTML.

Yang diuji: `qtbm/galian.py` terhadap `lyTon()` (presisi) dan `lyTonS()` (seperti Surpac) ASLI di
aplikasi Block Model. Mesin ini tidak ada di `gcex_backend` -- ia ditulis ulang di Python -- jadi
seluruh perilakunya harus dibuktikan, bukan dipercaya: pemotongan blok di garis poligon
(Sutherland-Hodgman), tumpang tindih blok dengan flitch (mode composite & bidang tengah), poligon
lubang (exclusion), SG tetap vs kolom SG, cut-off tampilan `onlyPass`, dan waste pengisi.

Caranya: aplikasi Block Model dibuka dengan data latihan, modelnya dipotong ke satu jendela kecil
yang PADAT (bukan dicuplik berjarak -- poligon kecil harus kena blok), lalu `lyTon()` dijalankan
di dalam halaman untuk beberapa susunan poligon + pilihan. Model, poligon, pilihan dan hasilnya
diambil, dijalankan ulang lewat `qtbm/galian.tonase()`, dan n / volume / tonase / kadar / luas /
coverage / waste dibandingkan.

Pemakaian:
    python tools/uji/paritas_galian_bm.py [port] [--fixture]
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
from qtbm import galian as GA                                        # noqa: E402
from qtbm.proyek import BlockModel                                   # noqa: E402
from qtbm.tampil_bm import Tampilan                                  # noqa: E402

ARG = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith("--")]
FIXTURE = "--fixture" in sys.argv
PORT = ARG[0] if ARG else "8775"
SRV = ROOT / "tools" / "uji" / "_srv_bm"
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
BEKU = ROOT / "qtbm" / "tests" / "data" / "galian_bm_js.json"

LEBAR = 40.0        # setengah lebar jendela model yang dipakai (m)
TOL = 1e-6

JS = r"""
(function(lebar){
  var m0 = window.BX && BX.m;
  if (!m0) return {err: 'belum ada block model aktif'};
  if (typeof lyTon !== 'function') return {err: 'lyTon tidak tersedia'};
  var nums = Object.keys(m0.num), cats = Object.keys(m0.cat);

  /* ---- jendela PADAT di sekitar flitch dengan blok terbanyak ----
     Model dicuplik per-jendela, bukan berjarak: poligon galian berukuran puluhan meter harus
     benar-benar memotong blok, kalau tidak ujinya lulus dengan nol blok di kedua sisi. */
  var zc = {}, i;
  for (i = 0; i < m0.n; i++) { var zk = Math.round(m0.z[i] * 100); zc[zk] = (zc[zk] || 0) + 1; }
  var zb = null, nb = -1;
  Object.keys(zc).forEach(function(k){ if (zc[k] > nb) { nb = zc[k]; zb = +k / 100; } });
  var sx = [], sy = [];
  for (i = 0; i < m0.n; i++) if (Math.abs(m0.z[i] - zb) < 1e-6) { sx.push(m0.x[i]); sy.push(m0.y[i]); }
  sx.sort(function(a,b){return a-b;}); sy.sort(function(a,b){return a-b;});
  var cx = sx[sx.length >> 1], cy = sy[sy.length >> 1];
  var pick = [];
  for (i = 0; i < m0.n; i++)
    if (Math.abs(m0.x[i] - cx) <= lebar && Math.abs(m0.y[i] - cy) <= lebar) pick.push(i);
  if (!pick.length) return {err: 'jendela kosong'};

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
  /* ---- kolom SG BERLUBANG, dibuat dari indeks (bukan acak) supaya Python bisa menirunya persis.
     Tanpa ini, kolom SG data latihan tidak punya satu pun nilai tidak sah, sehingga cabang
     sgZero / sgRep di bxSGv TIDAK PERNAH dijalankan -- ujinya lulus tanpa menguji apa pun. */
  var sgu = new Float64Array(m.n);
  for (i = 0; i < m.n; i++)
    sgu[i] = (i % 7 === 0) ? 0 : ((i % 11 === 0) ? NaN : (2.2 + (i % 9) * 0.1));
  m.num.SG_UJI = sgu;

  BX.m = m; BX.ver = (BX.ver || 0) + 1; BX.sc = {}; if (window.LY) LY.ix = null;

  var lap = function(A){ return Array.prototype.slice.call(A).map(function(v){ return +v; }); };
  var out = {lebar: lebar, n: m.n, nama: m.name, zb: zb, cx: cx, cy: cy,
             x: lap(m.x), y: lap(m.y), z: lap(m.z),
             sx: lap(m.sx), sy: lap(m.sy), sz: lap(m.sz), num: {}, cat: {}, kasus: []};
  Object.keys(m.num).forEach(function(a){ out.num[a] = lap(m.num[a]); });
  cats.forEach(function(a){ out.cat[a] = {kode: lap(m.cat[a].codes), dict: m.cat[a].dict}; });

  var A0 = nums.filter(function(n){ return /^AU/i.test(n); })[0] || nums[0];
  /* kolom SG yang dipakai uji adalah SG_UJI yang berlubang (lihat atas), supaya cabang
     "SG tidak sah" benar-benar dijalankan. Kolom SG asli data latihan tidak punya lubang. */
  var sgCol = 'SG_UJI';
  var sz = m.sz[0] || 2.5;

  /* poligon uji, dalam koordinat internal (sama dengan m.x / m.y) */
  var kotak = function(w){ return [[cx-w,cy-w],[cx+w,cy-w],[cx+w,cy+w],[cx-w,cy+w]]; };
  /* digeser setengah blok supaya garis poligon JATUH DI TENGAH blok -- di situlah kedua metode
     berbeda paling tajam dan di situlah pemotongan benar-benar diuji */
  var geser = function(w,d){ return [[cx-w+d,cy-w+d],[cx+w+d,cy-w+d],[cx+w+d,cy+w+d],[cx-w+d,cy+w+d]]; };
  var segi = [[cx-26,cy-20],[cx+22,cy-30],[cx+32,cy+16],[cx-3,cy+35],[cx-30,cy+13]];

  var jalan = function(nama, P, set, excl){
    var L = lyU(), U = BX.ui;
    var sL = {}, sU = {};
    var DU = window.dbU ? dbU() : {};
    ['top','bot','fh','gAttr','calcM','flMode','onlyPass'].forEach(function(k){
      if (set.hasOwnProperty(k)) { sL[k] = L[k]; L[k] = set[k]; } });
    ['sg','sgCol','sgZero','sgRep','attr','fAttr','fOp','fVal','wOn','wSG','wG'].forEach(function(k){
      if (set.hasOwnProperty(k)) { sU[k] = U[k]; U[k] = set[k]; } });
    if (window.LY) LY.ix = null;
    BX.sc = {};
    var res = null, err = null;
    try { res = lyTon(P, undefined, excl || []); } catch (e) { err = String(e && e.message || e); }
    /* Pilihan dicatat SEKARANG, selagi L dan U masih memegang nilai yang diuji. */
    var opsi = {top: L.top, bot: L.bot, gAttr: lyGradeAttr(), calcM: lyCalcM(),
                flMode: (window.lyFlMode ? lyFlMode() : 'comp'), onlyPass: !!L.onlyPass,
                sg: U.sg, sgCol: U.sgCol || '', sgZero: U.sgZero || '', sgRep: U.sgRep || '',
                attr: U.attr, fAttr: U.fAttr || '', fOp: U.fOp || '', fVal: U.fVal === undefined ? '' : U.fVal,
                wOn: !!DU.wOn, wSG: DU.wSG === undefined ? '' : DU.wSG, wG: +DU.wG || 0,
                bench: lyBench()};
    Object.keys(sL).forEach(function(k){ L[k] = sL[k]; });
    Object.keys(sU).forEach(function(k){ U[k] = sU[k]; });
    if (window.LY) LY.ix = null;
    if (err || !res) { out.kasus.push({nama: nama, err: err || 'lyTon tidak memberi hasil'}); return; }
    out.kasus.push({nama: nama, P: P, excl: (excl || []).map(function(q){ return q.p; }), opsi: opsi,
      hasil: {n: res.n, v: res.v, t: res.t, a: res.a, grade: res.grade, cov: res.cov,
              wA: res.wA || 0, wT: res.wT || 0, fh: res.fh, zs: res.zs, attr: res.attr}});
  };

  var z1 = zb + sz / 2, z0 = zb - sz / 2;
  var dsr = {top: z1, bot: z0, gAttr: A0, flMode: 'comp', onlyPass: false,
             sg: 2.6, sgCol: '', sgZero: '', sgRep: '', wOn: false, wSG: '', wG: 0};
  var S = function(x){ var o = {}; Object.keys(dsr).forEach(function(k){ o[k] = dsr[k]; });
                       Object.keys(x || {}).forEach(function(k){ o[k] = x[k]; }); return o; };

  jalan('kotak presisi, garis di batas blok', kotak(30), S({calcM: 'clip'}));
  jalan('kotak surpac, garis di batas blok', kotak(30), S({calcM: 'surpac'}));
  jalan('kotak presisi, garis di tengah blok', geser(30, sz / 2), S({calcM: 'clip'}));
  jalan('kotak surpac, garis di tengah blok', geser(30, sz / 2), S({calcM: 'surpac'}));
  jalan('segi lima presisi', segi, S({calcM: 'clip'}));
  jalan('segi lima surpac', segi, S({calcM: 'surpac'}));
  jalan('flitch 3 blok (presisi)', kotak(30), S({calcM: 'clip', top: zb + sz * 1.5, bot: zb - sz * 1.5}));
  jalan('flitch 3 blok (surpac)', kotak(30), S({calcM: 'surpac', top: zb + sz * 1.5, bot: zb - sz * 1.5}));
  jalan('flitch setengah blok (presisi)', kotak(30), S({calcM: 'clip', top: zb + sz / 4, bot: zb - sz / 4}));
  jalan('mode bidang tengah', kotak(30), S({calcM: 'clip', flMode: 'mid',
                                            top: zb + sz * 2, bot: zb - sz * 2}));
  jalan('waste pengisi menyala', segi, S({calcM: 'clip', wOn: true, wSG: 2.0, wG: 0.05}));
  jalan('waste pengisi, Surpac (tidak ditambah)', segi, S({calcM: 'surpac', wOn: true, wSG: 2.0, wG: 0.05}));
  if (sgCol) {
    jalan('kolom SG (presisi)', kotak(30), S({calcM: 'clip', sgCol: sgCol}));
    jalan('kolom SG, tidak sah -> 0', kotak(30), S({calcM: 'clip', sgCol: sgCol, sgZero: 'zero'}));
    jalan('kolom SG, pengganti 1,8', kotak(30), S({calcM: 'clip', sgCol: sgCol, sgRep: 1.8}));
    jalan('kolom SG (surpac)', kotak(30), S({calcM: 'surpac', sgCol: sgCol}));
  }
  jalan('cut-off tampilan (onlyPass)', kotak(30),
        S({calcM: 'clip', onlyPass: true, attr: A0, fAttr: A0, fOp: 'ge', fVal: 0.3}));
  jalan('cut-off tampilan (onlyPass, surpac)', kotak(30),
        S({calcM: 'surpac', onlyPass: true, attr: A0, fAttr: A0, fOp: 'ge', fVal: 0.3}));
  /* lubang di tengah: poligon dalam yang dikeluarkan */
  var lub = {p: kotak(10), b: lyBB(kotak(10))};
  jalan('dengan lubang (presisi)', kotak(30), S({calcM: 'clip'}), [lub]);
  jalan('dengan lubang (surpac)', kotak(30), S({calcM: 'surpac'}), [lub]);
  jalan('atribut kadar tidak ada -> jatuh ke cadangan', kotak(30),
        S({calcM: 'clip', gAttr: '__tidak_ada__'}));

  /* ---- dbLain(): angka metode pembanding yang SELALU ditampilkan di panel dig block.
     Ia dihitung dengan membalik lyU().calcM sesaat lalu memanggil lyTon() yang sama. Kalau cache
     indeks flitch (LY.ix) tidak dibuang saat membalik, angkanya salah TANPA galat apa pun -- dan
     yang salah adalah justru angka pembanding yang dipakai untuk mempertanggungjawabkan tonase
     terhadap Surpac. Karena itu diperiksa di kedua arah, plus tidak meninggalkan jejak. */
  if (typeof dbLain === 'function') {
    var Lb = lyU(), Pb = segi, zsb;
    Lb.top = zb + sz / 2; Lb.bot = zb - sz / 2; Lb.flMode = 'comp'; Lb.onlyPass = false;
    var U0 = BX.ui; U0.sg = 2.6; U0.sgCol = ''; U0.sgZero = ''; U0.sgRep = ''; U0.wOn = false;
    zsb = lyZs();
    Lb.calcM = 'clip'; if (window.LY) LY.ix = null;
    var b_clip = lyTon(Pb, zsb, []).t, b_lain_clip = dbLain(Pb, zsb, []).t;
    Lb.calcM = 'surpac'; if (window.LY) LY.ix = null;
    var b_surpac = lyTon(Pb, zsb, []).t, b_lain_surpac = dbLain(Pb, zsb, []).t;
    var b_akhir = lyCalcM();
    Lb.calcM = 'clip'; if (window.LY) LY.ix = null;
    var b_clip2 = lyTon(Pb, zsb, []).t;
    out.pembanding = {clip: b_clip, surpac: b_surpac, lain_dari_clip: b_lain_clip,
                      lain_dari_surpac: b_lain_surpac, calcM_akhir: b_akhir, clip_ulang: b_clip2};
  }

  /* ---- ekspor string: tangkap keluaran dgExport() ASLI, bukan membaca kodenya ulang.
     Urutan Y,X di .str dan pengembalian offset adalah kesalahan yang tidak menimbulkan galat
     apa pun -- berkasnya tetap terbaca Surpac, poligonnya saja yang di tempat lain. Satu-satunya
     cara memastikannya adalah membandingkan isi berkas baris per baris. */
  var simpanS = DG.S, simpanDl = window.dgDl, tangkap = {};
  window.dgDl = function(txt, fn){ tangkap[fn.split('.').pop()] = txt; };
  DG.S = [
    {no: 7, d: 'ORE', closed: true, vis: true,
     pts: [[cx-20, cy-10, zb], [cx+15, cy-12, zb], [cx+10, cy+18, zb]]},
    {no: 8, d: 'WASTE, kanan', closed: false, vis: true,
     pts: [[cx-5, cy-5, zb+1.5], [cx+6, cy+7, zb+1.5]]},
    {no: 9, d: 'tersembunyi', closed: true, vis: false,
     pts: [[cx, cy, zb], [cx+1, cy, zb], [cx+1, cy+1, zb]]}
  ];
  try { dgExport('str'); dgExport('dxf'); } catch (e) { tangkap.err = String(e); }
  out.ekspor = {teks: tangkap, zona: String(ZONE), offX: window.offX || 0, offY: window.offY || 0,
                S: DG.S.map(function(s){ return {no: s.no, d: s.d, closed: s.closed,
                                                 vis: s.vis, pts: s.pts}; })};
  DG.S = simpanS; window.dgDl = simpanDl;
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
            tempfile.mkdtemp(prefix="gcex_gal_"),
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
        print("  menjalankan lyTon() asli di aplikasi Block Model...", flush=True)
        d = pg.evaluate("(%s)(%f)" % (JS, LEBAR))
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


def keadaan_dari(o: dict, bm: BlockModel):
    """Pilihan JS -> (Tampilan, Opsi) di Qt. Di sinilah salah-terjemah akan tertangkap."""
    T = Tampilan()
    T.atribut = o.get("attr") or None
    T.sg = float(o.get("sg") or 2.6)
    T.sg_kolom = o.get("sgCol") or ""
    T.sg_nol = o.get("sgZero") or ""
    T.sg_ganti = str(o.get("sgRep") or "")
    T.f_atribut = o.get("fAttr") or ""
    T.f_op = o.get("fOp") or "ge"
    T.f_nilai = "" if o.get("fVal") in (None, "") else str(o.get("fVal"))
    B = o.get("bench") or [0.0, 0.0]
    O = GA.Opsi(
        rl_atas=float(B[0]), rl_bawah=float(B[1]),
        kadar=(o.get("gAttr") or "") if (o.get("gAttr") or "") in bm.angka else "",
        metode="surpac" if o.get("calcM") == "surpac" else "clip",
        mode_flitch="mid" if o.get("flMode") == "mid" else "comp",
        hanya_lolos=bool(o.get("onlyPass")),
        waste_on=bool(o.get("wOn")),
        waste_sg=float(o.get("wSG") or 0) if str(o.get("wSG") or "").strip() else 0.0,
        waste_kadar=float(o.get("wG") or 0))
    return T, O


def _dekat(a, b) -> bool:
    a, b = float(a), float(b)
    if not np.isfinite(a) or not np.isfinite(b):
        return (not np.isfinite(a)) and (not np.isfinite(b))
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


RUAS = (("n", "n"), ("v", "v"), ("t", "t"), ("a", "a"), ("grade", "kadar"),
        ("cov", "cov"), ("wA", "waste_a"), ("wT", "waste_t"), ("fh", "fh"), ("zs", "zs"))


def bandingkan_pembanding(d: dict) -> list:
    """`dbLain()` harus memberi angka yang sama dengan memilih metode itu langsung, tanpa jejak."""
    P = d.get("pembanding")
    if not P:
        return ["dbLain tidak terekam: modul web-src/digband.js tidak terpasang di app/index.html"]
    salah = []
    if not _dekat(P["lain_dari_clip"], P["surpac"]):
        salah.append("dbLain dari mode presisi %r != Surpac langsung %r"
                     % (P["lain_dari_clip"], P["surpac"]))
    if not _dekat(P["lain_dari_surpac"], P["clip"]):
        salah.append("dbLain dari mode Surpac %r != presisi langsung %r"
                     % (P["lain_dari_surpac"], P["clip"]))
    if P["calcM_akhir"] != "surpac":
        salah.append("dbLain tidak mengembalikan calcM; jadi %r" % P["calcM_akhir"])
    if not _dekat(P["clip_ulang"], P["clip"]):
        salah.append("angka presisi berubah setelah dbLain dipanggil: %r -> %r"
                     % (P["clip"], P["clip_ulang"]))
    if _dekat(P["clip"], P["surpac"]):
        salah.append("kedua metode memberi angka sama pada poligon pembanding: ujinya tidak "
                     "membedakan apa-apa (%r)" % P["clip"])
    return salah


def bandingkan_ekspor(d: dict) -> list:
    """Isi berkas .str dan .dxf Qt harus sama baris per baris dengan `dgExport()` aplikasi HTML."""
    import datetime as _dt
    from qtbm import string_io as SIO

    E = d.get("ekspor")
    if not E:
        return ["ekspor tidak terekam di hasil JS"]
    if E["teks"].get("err"):
        return ["dgExport melempar galat: %s" % E["teks"]["err"]]
    salah = []
    # hanya string yang ditampilkan ikut diekspor -- sama dengan filter `s.vis` di dgExport
    daftar = [SIO.String(no=s["no"], ket=s["d"], tertutup=bool(s["closed"]),
                         pts=[(p[0], p[1], p[2]) for p in s["pts"]])
              for s in E["S"] if s["vis"]]
    hari_ini = _dt.date.today()
    py = {
        "str": SIO.teks_str(daftar, E["zona"], E["offX"], E["offY"], hari_ini),
        "dxf": SIO.teks_dxf(daftar, E["offX"], E["offY"]),
    }
    for fmt in ("str", "dxf"):
        js = E["teks"].get(fmt)
        if js is None:
            salah.append("ekspor %s: aplikasi HTML tidak menghasilkan apa-apa" % fmt)
            continue
        a, b = js.splitlines(), py[fmt].splitlines()
        if len(a) != len(b):
            salah.append("ekspor %s: %d baris JS vs %d baris Python" % (fmt, len(a), len(b)))
        for k, (ja, pa) in enumerate(zip(a, b)):
            if ja != pa:
                salah.append("ekspor %s baris %d: JS %r vs Python %r" % (fmt, k + 1, ja, pa))
                break
        if js != py[fmt]:
            if not any(("ekspor %s" % fmt) in s for s in salah):
                salah.append("ekspor %s: isi sama per baris tetapi akhiran baris berbeda" % fmt)
    return salah


def bandingkan(d: dict) -> list:
    salah = []
    bm = model_dari(d)
    for ks in d["kasus"]:
        nm = ks["nama"]
        if ks.get("err"):
            salah.append("%s: %s" % (nm, ks["err"]))
            continue
        T, O = keadaan_dari(ks["opsi"], bm)
        P = [(p[0], p[1]) for p in ks["P"]]
        excl = [[(q[0], q[1]) for q in Q] for Q in (ks.get("excl") or [])]
        try:
            H = GA.tonase(bm, P, T, O, excl)
        except Exception as e:                      # noqa: BLE001
            salah.append("%s: Python melempar %s: %s" % (nm, type(e).__name__, e))
            continue
        js = ks["hasil"]
        for kj, kp in RUAS:
            a, b = js.get(kj), getattr(H, kp)
            if not _dekat(a if a is not None else float("nan"), b):
                salah.append("%s: %s JS %r vs Python %r" % (nm, kj, a, b))
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
    print("model jendela: %d blok, flitch terpadat RL %.2f" % (d["n"], d["zb"]))
    salah = bandingkan(d) + bandingkan_ekspor(d) + bandingkan_pembanding(d)
    print("kasus: %d" % len(d["kasus"]))
    for ks in d["kasus"]:
        print("  - %s" % ks["nama"])
    if salah:
        print("\nTIDAK SAMA (%d):" % len(salah))
        for s in salah:
            print("  ! %s" % s)
        return 1
    print("  - ekspor .str dan .dxf (isi berkas dibandingkan baris per baris)")
    print("  - dbLain(): angka metode pembanding, diperiksa di kedua arah + tanpa jejak")
    print("\nSEMUA SAMA PERSIS: dig block & ekspor string Qt = aplikasi HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
