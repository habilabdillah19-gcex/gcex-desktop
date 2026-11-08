# -*- coding: utf-8 -*-
"""Block Model: wireframe geologi hanya di node "Import Wireframe Geologi"; permukaan pit / topo (DTM)
tetap di Data Referensi untuk Reporting > Pit & progres.

A/B: build lama (git, bawaan HEAD:app/index.html) vs build baru (app/index.html), data latihan sama.

Yang diukur:
  1. Pintu import wireframe geologi (tombol file / menu Project Tree yang memanggil mdImport TANPA jenis
     'surf'): build baru tepat panel pWf + node wf. Build lama: pintunya di Data Referensi.
  2. Permukaan latihan (pit fase 1/2, topo Juni/Juli) di build baru berjenis 'surf', tampil di
     Data Referensi, TIDAK di node wireframe.
  3. Wireframe yang diimport ke node wf muncul paling bawah di node wf dan di daftar panel pWf, tidak di
     Data Referensi; "Pindahkan ke Data Referensi" benar-benar memindahkannya.
  4. Jenis ikut tersimpan di berkas proyek (SA.collectWork).
  5. Tonase Reporting dengan batas DTM / progres topo IDENTIK di kedua build.

Pemakaian: python tools/uji/uji_wireframe_bm.py [--dasar=<ref git>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")

JS_PINTU = r"""
(function () {
  var geo = [], surf = [];
  [].forEach.call(document.querySelectorAll('input[type=file]'), function (i) {
    var o = i.getAttribute('onchange') || '', s = i.closest('section'), id = s ? s.id : '(luar)';
    if (/mdImport\(this,'surf'\)/.test(o)) surf.push(id); else if (/mdImport\(this/.test(o)) geo.push(id);
  });
  PT.render && PT.render(true);
  var ng = [], ns = [];
  PT.flatAll(PT.nodes || []).forEach(function (n) {
    var M = []; if (n.menu) { try { M = n.menu() || []; } catch (e) {} } if (n.add) M = M.concat(n.add.items || [n.add]); /* 0.24.45: perintah tambah = baris + Tambah */
    M.forEach(function (it) { var f = it && it.fn ? String(it.fn) : ''; if (/mdImport\(i,'surf'\)/.test(f)) ns.push(n.id); else if (/mdImport\(i/.test(f)) ng.push(n.id); });
  });
  return {panelGeo: geo, panelSurf: surf, nodeGeo: ng, nodeSurf: ns};
})()
"""

JS_DAFTAR = r"""
(function () {
  PT.render && PT.render(true);
  var L = PT.flatAll(PT.nodes || []), kidsOf = function (id, re) { var n = L.filter(function (x) { return x.id === id; })[0]; return n ? (n.kids || []).filter(function (k) { return re.test(k.id) && !k.addRow; }).map(function (k) { return k.t; }) : null; };
  return {models: MD.models.map(function (m) { return m.name + ':' + (m.jenis || '-'); }),
          wf: kidsOf('wf', /^wf\./), ref: kidsOf('ref', /^ref\.models\./),
          wfList: ((document.getElementById('wfList') || {}).textContent || ''),
          mdList: ((document.getElementById('mdList') || {}).textContent || '')};
})()
"""

JS_IMPORT = r"""
(async function () {
  var t = await (await fetch('data-latihan/QV_Lensa2_Leapfrog.obj')).text();
  await mdImport({files: [new File([t], 'UJI_WF_BM.obj')], value: ''}, 'geo');
  await new Promise(function (r) { setTimeout(r, 200); });
  var P = SA.mdPack ? SA.mdPack() : null; if (P && P.then) P = await P; var w = (P && P.models) || [];
  return {simpan: w.map(function (m) { return m.name + ':' + (m.jenis || '-'); })};
})()
"""

JS_PINDAH = r"""
(function () {
  PT.render && PT.render(true);
  var n = PT.flatAll(PT.nodes || []).filter(function (x) { return x.id === 'wf'; })[0], k = n.kids.filter(function (q) { return !q.addRow; }).slice(-1)[0];
  var it = k.menu().filter(function (x) { return x.t && /Pindahkan ke Data Referensi/.test(x.t); })[0];
  if (!it) return {err: 'menu pindah tidak ada'};
  it.fn(); return {ok: 1};
})()
"""

JS_LAPOR = r"""
(function () {
  if (!(window.BX && BX.m) || typeof rpRun !== 'function') return {err: 'block model / reporting tidak ada'};
  var C = (MD.models || []).map(function (m, i) { return {n: m.name, k: 'wf:' + i, tin: m}; });
  var cari = function (re) { return C.filter(function (c) { return re.test(c.n); })[0]; };
  var juni = cari(/topo_akhir_juni/), juli = cari(/topo_akhir_juli/), f2 = cari(/pit_fase2/);
  if (!juni || !juli || !f2) return {err: 'permukaan latihan tidak ditemukan'};
  var o = rpO(), ton = function () { var R = RP.res, t = 0; if (!R || !R.rows || !R.rows.length) return null; Object.keys(R.rows[0].G).forEach(function (k) { t += R.rows[0].G[k].t; }); return +t.toFixed(3); };
  var zf = function (tin, j) { var tf = RP.api.tin(tin), ox = window.offX || 0, oy = window.offY || 0; return function (x, y) { var r = tf(x + ox, y + oy); return r ? r[j] : null; }; };
  o.dom = 'all'; o.cat = {}; o.surf = 'none'; o.poly = ''; o.z0 = ''; o.z1 = ''; o.cuts = '0'; o.grp = 'none'; o.show = false;
  var out = {};
  RP.ovr = null; o.sx = [{k: juli.k, side: 'below'}]; rpRun(); out.dibawahJuli = ton();
  o.sx = [{k: f2.k, side: 'above'}]; rpRun(); out.diatasPitFase2 = ton();
  o.sx = []; RP.ovr = {tz: zf(juni.tin, 1), pz: zf(juli.tin, 0), tzT: true, pzT: true, lab: 'uji'}; rpRun(); out.progresJuniJuli = ton();
  RP.ovr = null; o.sx = []; rpRun(); out.tanpaBatas = ton();
  return out;
})()
"""


def layani(html_bytes, nama):
    port = str(random.randint(9100, 9899))
    d = Path(tempfile.mkdtemp(prefix="gcex_wfbm_" + nama + "_"))
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
    pg.wait_for_function("window.BX && BX.m && BX.m.n > 0", timeout=600000)
    pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(2500)
    return pg.evaluate("({blok: BX.m.n, model: MD.models.length})")


def main():
    from playwright.sync_api import sync_playwright
    lama = subprocess.run(["git", "show", "%s:app/index.html" % DASAR], cwd=str(ROOT), capture_output=True).stdout
    baru = (ROOT / "app" / "index.html").read_bytes()
    pl, pb = layani(lama, "lama"), layani(baru, "baru")
    H, galat = {"lama": {}, "baru": {}}, []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(),
              args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.on("pageerror", lambda e: galat.append(str(e)[:200]))
        for v, port in (("lama", pl), ("baru", pb)):
            H[v]["boot"] = boot(pg, port); H[v]["lapor"] = pg.evaluate(JS_LAPOR); H[v]["pintu"] = pg.evaluate(JS_PINTU)
        H["baru"]["d0"] = pg.evaluate(JS_DAFTAR)
        H["baru"]["imp"] = pg.evaluate(JS_IMPORT); H["baru"]["d1"] = pg.evaluate(JS_DAFTAR)
        H["baru"]["pindah"] = pg.evaluate(JS_PINDAH); pg.wait_for_timeout(300); H["baru"]["d2"] = pg.evaluate(JS_DAFTAR)
        ctx.close()
    for v in ("lama", "baru"):
        print("%s: boot %s | pintu %s" % (v, H[v]["boot"], H[v]["pintu"]))
        print("   laporan %s" % H[v]["lapor"])
    B = H["baru"]
    for k in ("d0", "d1", "d2"): print(k, {x: B[k][x] for x in ("models", "wf", "ref")})
    print("simpan:", B["imp"]["simpan"])
    salah = []
    P = B["pintu"]
    if P["panelGeo"] != ["pWf"] or P["nodeGeo"] != ["wf"]: salah.append("pintu import wireframe build baru bukan tepat pWf + wf: %s" % P)
    if P["panelSurf"] != ["pModel"] or P["nodeSurf"] != ["ref"]: salah.append("pintu import permukaan DTM bukan tepat pModel + ref: %s" % P)
    if "pModel" not in H["lama"]["pintu"]["panelGeo"]: salah.append("build lama tidak mengimpor wireframe di Data Referensi -> uji tidak membuktikan")
    d0, d1, d2 = B["d0"], B["d1"], B["d2"]
    if d0["wf"] != ["QV_Lensa2_Leapfrog"] or len(d0["ref"] or []) != 4 or not all(m.endswith(":surf") for m in d0["models"] if "SIM_" in m):
        salah.append("permukaan latihan tidak berada di Data Referensi sebagai 'surf': %s" % d0)
    if (d1["wf"] or [None])[-1] != "UJI_WF_BM" or "UJI_WF_BM" in (d1["ref"] or []) or "UJI_WF_BM" not in d1["wfList"] or "UJI_WF_BM" in d1["mdList"]:
        salah.append("wireframe baru tidak berada (hanya) di node / panel wireframe: %s" % d1)
    if "UJI_WF_BM:geo" not in B["imp"]["simpan"] or "SIM_pit_fase1:surf" not in B["imp"]["simpan"]: salah.append("jenis tidak ikut tersimpan di proyek")
    if B["pindah"].get("err") or "UJI_WF_BM" in (d2["wf"] or []) or "UJI_WF_BM" not in (d2["ref"] or []): salah.append("menu pindah ke Data Referensi gagal: %s" % d2)
    LA, LB = H["lama"]["lapor"], H["baru"]["lapor"]
    if LA.get("err") or LA != LB: salah.append("tonase Reporting berubah: %s vs %s" % (LA, LB))
    if LA.get("dibawahJuli") == LA.get("tanpaBatas"): salah.append("batas DTM tidak memotong apa pun -> uji tonase tidak membuktikan")
    if galat: print("galat halaman:", galat[:3])
    print("\n" + ("LULUS" if not salah else "GAGAL:\n  " + "\n  ".join(salah)))
    return 0 if not salah else 1


if __name__ == "__main__":
    raise SystemExit(main())
