# -*- coding: utf-8 -*-
"""Drill Hole: menu "Pindahkan ke Data Spasial" untuk proyek lama yang menyimpan pit / topo di daftar wireframe.

Proyek lama ditiru di build baru: berkas pit / topo latihan diimport lagi ke daftar wireframe (MD.models),
ditambah satu wireframe sesudahnya, lalu Reporting diberi batas DTM yang merujuk 'wf:<indeks>'.

Yang diukur:
  1. Sesudah "Pindahkan permukaan pit / topo ke Data Spasial": tak ada berkas SIM_pit / SIM_topo di daftar
     wireframe / node wf; masing-masing muncul sebagai versi pit / topografi dengan TIN.
  2. Topografi & pit AKTIF tidak berubah (versi baru non-aktif).
  3. Rujukan Reporting dialihkan: batas ke topo Juli -> 'sp:topo:<id>', batas ke wireframe sesudahnya
     bergeser satu indeks tetapi tetap menunjuk berkas yang sama (namanya dicek).
  4. Tonase Reporting dengan batas itu IDENTIK sebelum dan sesudah pindah.
  5. Pindah satu berkas lewat menu per-berkas (peran pit) juga jalan.
  6. Build lama tidak punya menu ini (A/B: kalau ada, uji tidak membuktikan apa pun).

Pemakaian: python tools/uji/uji_pindah_spasial.py [--dasar=<ref git>]
"""
import os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")

JS_ADA_MENU = r"""
(function () {
  PT.render && PT.render(true);
  var w = PT.flatAll(PT.nodes || []).filter(function (n) { return n.id === 'wf'; })[0];
  if (!w) return {wf: false, menu: false};
  return {wf: true, menu: (w.menu() || []).some(function (x) { return x.t && /Pindahkan permukaan pit/.test(x.t); }), fungsi: typeof window.wfxKeSpasialSemua === 'function'};
})()
"""

JS_LAMA = r"""
(async function () {
  var F = [];
  for (var n of ['SIM_pit_fase1.dxf', 'SIM_pit_fase2.dxf', 'SIM_topo_akhir_juni.dxf', 'SIM_topo_akhir_juli.dxf']) {
    var t = await (await fetch('data-latihan/' + n)).text(); F.push(new File([t], n));
  }
  await mdImport({files: F, value: ''});
  var q = await (await fetch('data-latihan/QV_Lensa2_Leapfrog.obj')).text();
  await mdImport({files: [new File([q], 'UJI_SESUDAH.obj')], value: ''});
  /* proyek lama tidak punya jenis */
  MD.models.forEach(function (m) { delete m.jenis; });
  var idx = function (re) { var r = -1; MD.models.forEach(function (m, i) { if (re.test(m.name)) r = i; }); return r; };
  var iJuli = idx(/topo_akhir_juli/), iSes = idx(/UJI_SESUDAH/);
  var o = rpO(); o.dom = 'all'; o.cat = {}; o.surf = 'none'; o.poly = ''; o.z0 = ''; o.z1 = ''; o.cuts = '0'; o.grp = 'none'; o.show = false;
  RP.ovr = null; o.sx = [{k: 'wf:' + iJuli, side: 'below'}, {k: 'wf:' + iSes, side: 'above'}];
  rpRun();
  var ton = function () { var R = RP.res, t = 0; Object.keys(R.rows[0].G).forEach(function (k) { t += R.rows[0].G[k].t; }); return +t.toFixed(3); };
  return {models: MD.models.map(function (m) { return m.name; }), sx: o.sx.map(function (q) { return q.k; }), ton: ton(),
          topoAktif: spAct('topo') ? spAct('topo').id : null, pitAktif: spAct('pit') ? spAct('pit').id : null,
          nTopo: spL('topo').length, nPit: spL('pit').length};
})()
"""

JS_PINDAH = r"""
(function () {
  wfxKeSpasialSemua();
  var o = rpO(); rpRun();
  var ton = function () { var R = RP.res, t = 0; Object.keys(R.rows[0].G).forEach(function (k) { t += R.rows[0].G[k].t; }); return +t.toFixed(3); };
  PT.render && PT.render(true);
  var w = PT.flatAll(PT.nodes || []).filter(function (n) { return n.id === 'wf'; })[0];
  var nama = function (k) { if (/^wf:/.test(k)) { var m = MD.models[+k.slice(3)]; return m ? m.name : null; }
    var a = k.split(':'); var v = spL(a[1]).filter(function (x) { return x.id === a[2]; })[0]; return v ? a[1] + '/' + v.name + (v.tin ? '[tin]' : '') : null; };
  return {models: MD.models.map(function (m) { return m.name; }), wf: w.kids.map(function (k) { return k.t; }),
          sx: o.sx.map(function (q) { return q.k; }), sxNama: o.sx.map(function (q) { return nama(q.k); }), ton: ton(),
          topo: spL('topo').map(function (v) { return v.name + (v.tin ? '[tin]' : ''); }), pit: spL('pit').map(function (v) { return v.name + (v.tin ? '[tin]' : ''); }),
          topoAktif: spAct('topo') ? spAct('topo').id : null, pitAktif: spAct('pit') ? spAct('pit').id : null};
})()
"""

JS_SATU = r"""
(async function () {
  var t = await (await fetch('data-latihan/SIM_pit_fase1.dxf')).text();
  await mdImport({files: [new File([t], 'UJI_PIT_SATU.dxf')], value: ''});
  PT.render && PT.render(true);
  var w = PT.flatAll(PT.nodes || []).filter(function (n) { return n.id === 'wf'; })[0], k = w.kids.filter(function (x) { return x.t === 'UJI_PIT_SATU'; })[0];
  if (!k) return {err: 'berkas uji tidak ada di node wf'};
  var it = k.menu().filter(function (x) { return x.t && /sebagai versi desain pit/.test(x.t); })[0];
  if (!it) return {err: 'menu per-berkas tidak ada'};
  it.fn();
  return {diModels: MD.models.some(function (m) { return m.name === 'UJI_PIT_SATU'; }),
          diPit: spL('pit').some(function (v) { return v.name === 'UJI_PIT_SATU' && v.tin; })};
})()
"""


def layani(html_bytes, nama):
    port = str(random.randint(9100, 9899))
    d = Path(tempfile.mkdtemp(prefix="gcex_pindah_" + nama + "_"))
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


def boot(pg, port):
    pg.goto("http://localhost:%s/index.html" % port); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length>0", timeout=900000)
    pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(4000)
    return pg.evaluate("({hole: collars.length, blok: BX.m ? BX.m.n : 0})")


def main():
    from playwright.sync_api import sync_playwright
    lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=str(ROOT), capture_output=True).stdout
    baru = (ROOT / "app-dh" / "index.html").read_bytes()
    pl, pb = layani(lama, "lama"), layani(baru, "baru")
    H, galat = {}, []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(),
              args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.on("pageerror", lambda e: galat.append(str(e)[:200]))
        H["bootLama"] = boot(pg, pl); H["lamaMenu"] = pg.evaluate(JS_ADA_MENU)
        H["bootBaru"] = boot(pg, pb); H["baruMenu0"] = pg.evaluate(JS_ADA_MENU)
        H["sebelum"] = pg.evaluate(JS_LAMA); H["baruMenu1"] = pg.evaluate(JS_ADA_MENU)
        H["sesudah"] = pg.evaluate(JS_PINDAH)
        H["satu"] = pg.evaluate(JS_SATU)
        ctx.close()
    for k in ("bootLama", "lamaMenu", "bootBaru", "baruMenu0", "baruMenu1", "sebelum", "sesudah", "satu"):
        print("%-10s %s" % (k, H[k]))
    A, B, salah = H["sebelum"], H["sesudah"], []
    if H["bootBaru"]["hole"] <= 0 or H["bootBaru"]["blok"] <= 0: salah.append("boot baru gagal")
    if H["lamaMenu"].get("menu") or H["lamaMenu"].get("fungsi"): salah.append("build lama sudah punya menu -> uji tidak membuktikan")
    if not H["baruMenu1"]["menu"]: salah.append("menu node wf tidak muncul padahal ada berkas pit / topo")
    if not any("SIM_topo_akhir_juli" in m for m in A["models"]): salah.append("proyek lama tidak tertiru")
    if any("SIM_" in m for m in B["models"] + B["wf"]): salah.append("masih ada SIM_pit / SIM_topo di daftar wireframe")
    for nm, peran in (("SIM_pit_fase1", "pit"), ("SIM_pit_fase2", "pit"), ("SIM_topo_akhir_juni", "topo"), ("SIM_topo_akhir_juli", "topo")):
        if B[peran].count(nm + "[tin]") < 2:  # satu dari data latihan + satu hasil pindah
            salah.append("%s tidak masuk sebagai versi %s ber-TIN" % (nm, peran))
    if B["topo"][-2:] != ["SIM_topo_akhir_juni[tin]", "SIM_topo_akhir_juli[tin]"] or B["pit"][-2:] != ["SIM_pit_fase1[tin]", "SIM_pit_fase2[tin]"]:
        salah.append("urutan versi hasil pindah tidak mengikuti urutan import")
    if B["topoAktif"] != A["topoAktif"] or B["pitAktif"] != A["pitAktif"]: salah.append("versi aktif berubah")
    if not B["sx"][0].startswith("sp:topo:") or B["sxNama"][0] != "topo/SIM_topo_akhir_juli[tin]": salah.append("batas ke topo Juli tidak dialihkan: %s" % B["sxNama"])
    if B["sxNama"][1] != "UJI_SESUDAH" or B["sx"][1] == A["sx"][1]: salah.append("rujukan wireframe sesudahnya tidak bergeser dengan benar: %s -> %s" % (A["sx"], B["sx"]))
    if A["ton"] != B["ton"]: salah.append("tonase berubah: %s -> %s" % (A["ton"], B["ton"]))
    S = H["satu"]
    if S.get("err") or S.get("diModels") or not S.get("diPit"): salah.append("pindah satu berkas gagal: %s" % S)
    if galat: print("galat halaman:", galat[:3])
    print("\n" + ("LULUS" if not salah else "GAGAL:\n  " + "\n  ".join(salah)))
    return 0 if not salah else 1


if __name__ == "__main__":
    raise SystemExit(main())
