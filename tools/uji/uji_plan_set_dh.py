# -*- coding: utf-8 -*-
"""Drill Hole 0.24.44: set plan bor -- tiap "Plan baru" menjadi sub-node berurutan di Project Tree.

A/B: build lama (git, bawaan HEAD:app-dh/index.html) vs build baru, data latihan sama.

Skenario (meniru kerja harian):
  hari 1  : 5 titik sepanjang garis (plan pertama)
  hari 2  : Plan baru -> 3 titik di tempat lain
  hari 1  : extend: aktifkan lagi plan hari 1 -> 2 titik tambahan
Yang diukur:
  1. Node "Plan bor (rencana)" punya 2 sub-node berurutan (1. ..., 2. ...) dengan 7 dan 3 titik; plan
     aktif bertanda. Build lama: tanpa sub-node (bukti uji membedakan).
  2. 3D: dua lapisan garis plan (satu per plan); mematikan centang plan 2 menghilangkannya.
  3. Export plan 1 = 7 baris, export semua = 10 baris (lewat gxSimpan, isi CSV dibaca).
  4. Simpan proyek -> kosongkan -> buka lagi: 2 plan dengan 7 / 3 titik dan plan aktif yang sama.
  5. Proyek lama (plan tanpa set): 4 titik masuk ke satu plan "Plan lama", tidak ada yang hilang.
  6. "Hapus semua titik di plan aktif" hanya mengosongkan plan aktif.

Pemakaian: python tools/uji/uji_plan_set_dh.py [--dasar=<ref git>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")

JS_KIDS = r"""
(function () {
  PT.render && PT.render(true);
  var n = PT.flatAll(PT.nodes || []).filter(function (x) { return x.id === 'db.plan'; })[0];
  if (!n) return {ada: false};
  return {ada: true, b: n.b, kids: (n.kids || []).map(function (k) { return {t: k.t, b: k.b, mark: k.mark || '', chk: k.chk}; })};
})()
"""

JS_SKENARIO = r"""
(async function () {
  var W = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  if (!window.PLS) return {err: 'PLS tidak ada'};
  var c = collars[0], x0 = c[1] - offX + 40, y0 = c[2] - offY + 40;
  plLine({x: x0, y: y0}, {x: x0 + 40, y: y0});                         /* hari 1: 5 titik (spasi 10 m) */
  var s1 = PL.act;
  PLS.baru(); await W(200);                                            /* hari 2 */
  var s2 = PL.act;
  for (var i = 0; i < 3; i++) plNew(x0 + i * 10, y0 + 80); plRefresh(true);
  PLS.aktif(s1); await W(100);                                         /* extend hari 1 */
  plNew(x0 + 50, y0); plNew(x0 + 60, y0); plRefresh(true);
  var T = []; planTraces(T, {clip: false});
  var garis = T.filter(function (t) { return t.mode === 'lines'; }).map(function (t) { return t.name; });
  PLS.tampil(s2, false); var T2 = []; planTraces(T2, {clip: false});
  var garis2 = T2.filter(function (t) { return t.mode === 'lines'; }).length; PLS.tampil(s2, true);
  /* export: tangkap isi berkas */
  var cap = []; var g0 = window.gxSimpan; window.gxSimpan = function (b, fn) { return b.text().then(function (t) { cap.push({fn: fn, n: t.trim().split(/\r?\n/).length - 1}); }); };
  PLS.export(s1); PLS.exportSemua(); await W(300); window.gxSimpan = g0;
  /* simpan -> kosongkan -> buka */
  var w = JSON.parse(JSON.stringify(SA.collectWork()));
  PL.sets = null; PL.h = []; PL.act = null; PL._hDari = null;
  SA.applyWork({plan: w.plan}); await W(200);
  var buka = PL.sets.map(function (s) { return s.name + ':' + s.h.length; }), aktifSama = PL.act === s1;
  /* proyek lama tanpa set */
  var lama = {plan: {h: w.plan.sets[0].h.slice(0, 4), b: w.plan.b, s: w.plan.s}};
  SA.applyWork(lama); await W(200);
  var migrasi = PL.sets.map(function (s) { return s.name + ':' + s.h.length; });
  /* hapus titik plan aktif saja */
  SA.applyWork({plan: w.plan}); await W(200);
  plClear(); await W(100);
  var sesudahHapus = PL.sets.map(function (s) { return s.h.length; });
  return {s1: s1, s2: s2, garis: garis, garisTanpaPlan2: garis2, export: cap, buka: buka, aktifSama: aktifSama, migrasi: migrasi, sesudahHapus: sesudahHapus};
})()
"""


def layani(html_bytes, nama):
    port = str(random.randint(9100, 9899))
    d = Path(tempfile.mkdtemp(prefix="gcex_pls_" + nama + "_"))
    (d / "index.html").write_bytes(html_bytes)
    os.symlink(DATA, d / "data-latihan")
    subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    pg.evaluate("try{localStorage.removeItem(plKey()+'_sets');}catch(e){}")
    return pg.evaluate("({hole: collars.length})")


def main():
    from playwright.sync_api import sync_playwright
    lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=str(ROOT), capture_output=True).stdout
    baru = (ROOT / "app-dh" / "index.html").read_bytes()
    H, galat = {}, []
    with sync_playwright() as pw:
        for v, html in (("lama", lama), ("baru", baru)):
            port = layani(html, v)
            ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900})
            ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
            pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept(d.default_value) if d.type == "prompt" else d.accept())
            pg.on("pageerror", lambda e, v=v: galat.append(v + ": " + str(e)[:200]))
            h = H[v] = {"boot": boot(pg, port)}
            if v == "lama":
                pg.evaluate("plLine({x:collars[0][1]-offX+40,y:collars[0][2]-offY+40},{x:collars[0][1]-offX+80,y:collars[0][2]-offY+40})")
                h["kids"] = pg.evaluate(JS_KIDS)
            else:
                h["sk"] = pg.evaluate(JS_SKENARIO)
                pg.evaluate("SA.applyWork({plan:(function(){var w=SA.collectWork();return w.plan;})()})")
                h["kids"] = pg.evaluate("""(async function(){var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});};
                  /* susun ulang keadaan akhir untuk dibaca tree: 2 plan, plan 1 aktif */
                  PL.sets=null;PL.h=[];PL.act=null;PL._hDari=null;plRefresh(true);var s1=PL.act;var c=collars[0],x0=c[1]-offX+40,y0=c[2]-offY+40;
                  plLine({x:x0,y:y0},{x:x0+40,y:y0});PLS.baru();await W(150);for(var i=0;i<3;i++)plNew(x0+i*10,y0+80);plRefresh(true);PLS.aktif(s1);plNew(x0+50,y0);plNew(x0+60,y0);plRefresh(true);await W(200);
                  return (%s);})()""" % JS_KIDS.strip())
            ctx.close()
    print("lama:", H["lama"]["kids"]); print("baru:", H["baru"]["kids"]); print("skenario:", json.dumps(H["baru"]["sk"], ensure_ascii=False))
    salah = []
    K, S = H["baru"]["kids"], H["baru"]["sk"]
    if H["lama"]["kids"].get("kids"): salah.append("build lama sudah punya sub-node plan -> uji tidak membuktikan")
    ks = K.get("kids") or []
    if len(ks) != 2 or not ks[0]["t"].startswith("1. ") or not ks[1]["t"].startswith("2. "): salah.append("sub-node plan tidak 2 / tidak berurutan: %s" % ks)
    elif ks[0]["b"] != "7 titik" or ks[1]["b"] != "3 titik" or ks[0]["mark"] != "aktif" or ks[1]["mark"]: salah.append("jumlah titik / tanda aktif salah: %s" % ks)
    if S.get("err"): salah.append(S["err"])
    else:
        if len(S["garis"]) != 2 or S["garisTanpaPlan2"] != 1: salah.append("lapisan 3D per plan salah: %s / %s" % (S["garis"], S["garisTanpaPlan2"]))
        if [e["n"] for e in S["export"]] != [7, 10]: salah.append("isi export salah: %s" % S["export"])
        if [b.split(":")[-1] for b in S["buka"]] != ["7", "3"] or not S["aktifSama"]: salah.append("simpan / buka proyek salah: %s" % S["buka"])
        if S["migrasi"] != ["Plan lama:4"]: salah.append("migrasi proyek lama salah: %s" % S["migrasi"])
        if S["sesudahHapus"] != [0, 3]: salah.append("hapus titik plan aktif ikut menghapus plan lain: %s" % S["sesudahHapus"])
    if galat: print("galat halaman:", galat[:4])
    print("\n" + ("LULUS" if not salah else "GAGAL:\n  " + "\n  ".join(salah)))
    return 0 if not salah else 1


if __name__ == "__main__":
    raise SystemExit(main())
