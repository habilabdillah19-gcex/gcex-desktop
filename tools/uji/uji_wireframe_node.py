# -*- coding: utf-8 -*-
"""Drill Hole: wireframe geologi hanya diimport & dilihat di SATU node, "Import Wireframe Geologi".

A/B: build lama (git, bawaan HEAD:app-dh/index.html) vs build baru (app-dh/index.html).

Yang diukur:
  1. Jalan masuk import wireframe (tombol file yang memanggil mdImport / rpImpWf di panel mana pun,
     dan menu Project Tree yang memanggil mdImport). Build baru: tepat SATU panel (pWf) dan SATU node
     (wf). Build lama harus lebih dari satu -- kalau tidak, uji ini tidak membuktikan apa pun.
  2. Anak node wf = MD.models dengan urutan yang sama; berkas yang baru diimport muncul PALING BAWAH.
  3. Fungsi domain tetap jalan dari menu anak node: "Kunci domain ... ke wireframe ini" benar-benar
     mengisi d.wfx, dan badge node menyebut domain eksaknya.
  4. Memilih node wf menampilkan panel pWf (terlihat, ber-ukuran) beserta tombol import-nya.
  5. Node "Wireframe luar" tidak lagi ada di bawah Geomodeller Vein.

Pemakaian: python tools/uji/uji_wireframe_node.py [--dasar=<ref git>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")

JS_PINTU = r"""
(async function () {
  try { uiTab('Rep'); if (window.rpPanel) rpPanel(); } catch (e) {}
  await new Promise(function (r) { setTimeout(r, 400); });
  var panel = [];
  [].forEach.call(document.querySelectorAll('input[type=file]'), function (i) {
    var o = i.getAttribute('onchange') || '';
    if (/mdImport|rpImpWf/.test(o)) { var s = i.closest('section'); panel.push(s ? s.id : '(luar section)'); }
  });
  var L = PT.flatAll(PT.nodes || []), node = [];
  L.forEach(function (n) {
    if (!n.menu) return; var M = []; try { M = n.menu() || []; } catch (e) {}
    M.forEach(function (it) { if (it && it.fn && (/mdImport/.test(String(it.fn)) || /Import (wireframe|model vein)/i.test(it.t || ''))) node.push(n.id); });
  });
  if (window.rpPanel && /rpImpWf\(this\)/.test(String(rpPanel))) panel.push('pRep (Reporting BM)');
  var wfx = L.filter(function (n) { return n.id === 'wfx'; }).length;
  return {panel: panel, node: node, wfxDiGM: wfx};
})()
"""

JS_URUT = r"""
(async function () {
  var t = await (await fetch('data-latihan/QV_Lensa2_Leapfrog.obj')).text();
  var f = new File([t], 'UJI_URUTAN_TERAKHIR.obj', {type: 'text/plain'});
  await mdImport({files: [f], value: ''});
  PT.render && PT.render(true);
  await new Promise(function (r) { setTimeout(r, 300); });
  var w = PT.flatAll(PT.nodes || []).filter(function (n) { return n.id === 'wf'; })[0];
  return {ada: !!w, kids: w ? w.kids.filter(function (k) { return /^wf\.\d/.test(k.id); }).map(function (k) { return k.t; }) : [],
          models: MD.models.map(function (m) { return m.name; })};
})()
"""

JS_DOMAIN = r"""
(async function () {
  if (!window.gmAddDom) return {err: 'gmAddDom tidak ada'};
  gmAddDom('UJI_DOM');
  var d = GM.doms.filter(function (x) { return x.name === 'UJI_DOM'; })[0];
  PT.render && PT.render(true);
  var w = PT.flatAll(PT.nodes || []).filter(function (n) { return n.id === 'wf'; })[0];
  var k = w.kids[w.kids.length - 1], M = k.menu(), it = M.filter(function (x) { return x.t && x.t.indexOf('Kunci domain UJI_DOM') === 0; })[0];
  var serap = M.some(function (x) { return x.t && /Serap/.test(x.t); });
  if (!it) return {err: 'menu kunci tidak ada', menu: M.map(function (x) { return x.t || x.h; })};
  it.fn();
  PT.render && PT.render(true);
  var w2 = PT.flatAll(PT.nodes || []).filter(function (n) { return n.id === 'wf'; })[0], k2 = w2.kids[w2.kids.length - 1];
  return {wfx: d.wfx || null, badge: k2.b, serap: serap};
})()
"""

JS_PILIH = r"""
(async function () {
  PT.select('wf');
  await new Promise(function (r) { setTimeout(r, 400); });
  var p = document.getElementById('pWf'), r = p ? p.getBoundingClientRect() : null;
  var inp = p ? p.querySelector('input[type=file]') : null, lab = inp ? inp.closest('label') : null, rl = lab ? lab.getBoundingClientRect() : null;
  return {sel: PT.sel, tampil: !!(p && !p.hidden && r.height > 20), tombol: !!(rl && rl.height > 5 && rl.width > 5),
          judul: p ? (p.querySelector('h3') || {}).textContent : null};
})()
"""


def layani(html_bytes, nama):
    port = str(random.randint(9100, 9899))
    d = Path(tempfile.mkdtemp(prefix="gcex_wf_" + nama + "_"))
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
    return pg.evaluate("({hole: collars.length, model: MD.models.length})")


def main():
    from playwright.sync_api import sync_playwright
    lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=str(ROOT), capture_output=True).stdout
    baru = (ROOT / "app-dh" / "index.html").read_bytes()
    pl, pb = layani(lama, "lama"), layani(baru, "baru")
    H, galat = {"lama": {}, "baru": {}}, []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(),
              args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.on("pageerror", lambda e: galat.append(str(e)[:200]))
        H["lama"]["boot"] = boot(pg, pl); H["lama"]["pintu"] = pg.evaluate(JS_PINTU)
        H["baru"]["boot"] = boot(pg, pb); H["baru"]["pintu"] = pg.evaluate(JS_PINTU)
        H["baru"]["urut"] = pg.evaluate(JS_URUT)
        H["baru"]["dom"] = pg.evaluate(JS_DOMAIN)
        H["baru"]["pilih"] = pg.evaluate(JS_PILIH)
        ctx.close()
    for v in ("lama", "baru"):
        print("%s: boot %s | pintu import panel %s | menu node %s | node wfx di GM %s"
              % (v, H[v]["boot"], H[v]["pintu"]["panel"], H[v]["pintu"]["node"], H[v]["pintu"]["wfxDiGM"]))
    U, D, P = H["baru"]["urut"], H["baru"]["dom"], H["baru"]["pilih"]
    print("anak node wf:", U["kids"]); print("MD.models   :", U["models"])
    print("kunci domain:", D); print("pilih node  :", P)
    salah = []
    if H["baru"]["boot"]["hole"] <= 0: salah.append("boot baru gagal (0 hole)")
    pb_, nb_ = H["baru"]["pintu"]["panel"], H["baru"]["pintu"]["node"]
    if pb_ != ["pWf"]: salah.append("pintu import panel baru bukan tepat [pWf]: %s" % pb_)
    if nb_ != ["wf"]: salah.append("menu import node baru bukan tepat [wf]: %s" % nb_)
    if len(H["lama"]["pintu"]["panel"]) + len(H["lama"]["pintu"]["node"]) <= 2: salah.append("build lama tidak punya pintu ganda -> uji tidak membuktikan")
    if H["baru"]["pintu"]["wfxDiGM"]: salah.append("node wfx masih ada di Geomodeller")
    if not U["ada"] or U["kids"] != U["models"]: salah.append("urutan anak node wf != urutan MD.models")
    if not U["kids"] or U["kids"][-1] != "UJI_URUTAN_TERAKHIR": salah.append("berkas yang baru diimport tidak berada paling bawah")
    if D.get("err") or D.get("wfx") != "UJI_URUTAN_TERAKHIR" or "UJI_DOM" not in (D.get("badge") or "") or not D.get("serap"):
        salah.append("fungsi domain dari menu node gagal: %s" % D)
    if P["sel"] != "wf" or not P["tampil"] or not P["tombol"]: salah.append("panel pWf tidak tampil saat node wf dipilih: %s" % P)
    if galat: print("galat halaman:", galat[:3])
    print("\n" + ("LULUS" if not salah else "GAGAL:\n  " + "\n  ".join(salah)))
    return 0 if not salah else 1


if __name__ == "__main__":
    raise SystemExit(main())
