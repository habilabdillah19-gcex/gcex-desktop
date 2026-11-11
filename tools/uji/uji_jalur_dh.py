# -*- coding: utf-8 -*-
"""Jalur proyek (Drill Hole 0.24.73): Mulai dari nol vs Lanjutkan dari Surpac / Leapfrog.

1. Halaman pembuka: kartu jalur ada; slot Block model tersembunyi sampai jalur Lanjutan + acuan block model dicentang;
   tombol Tampilkan viewer menolak proyek baru tanpa pilihan jalur.
2. Jalur Mulai dari nol: node Import Wireframe Geologi & ribbon Wireframe tidak ada, menu Block Model tanpa Import,
   bxDlg / mdImport(geo) / uiTab('Wf') ditolak (data tidak masuk), tombol kerangka AOI tetap ada, jalur tersimpan
   di pekerjaan proyek; "Jadikan jalur Lanjutan" membuka pintu wireframe dan tercatat di jejak.
3. Jalur Lanjutan (wireframe + block model): BM CSV masuk dari halaman pembuka & ditandai "acuan"; wireframe masuk;
   serap -> domain "diserap"; kunci eksak -> "acuan eksak" dan domain eksak tidak ikut Autorun Wireframe;
   acuan yang objeknya ada tidak bisa dimatikan; Kembali ke nol ditolak.
4. Proyek lama tanpa jalur: ditebak dari isinya (lanjut bila ada wireframe / BM acuan), tanda perlu konfirmasi.
5. Demo data latihan: jalur Lanjutan (wireframe + block model) tanpa memblokir alur Demo.
Pemakaian: python tools/uji/uji_jalur_dh.py
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
html = (ROOT / "app-dh/index.html").read_bytes()
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
(d / "index.html").write_bytes(html); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
salah = []; hasil = {}

TREE = r"""(function(){PT.render(true);var ids=[];(function w(L){(L||[]).forEach(function(n){ids.push(n.id);w(n.kids);});})(PT.nodes);
  var f=function(id){var r=null;(function w(L){(L||[]).forEach(function(n){if(n.id===id)r=n;w(n.kids);});})(PT.nodes);return r;};
  var bm=f('bm'),mn=bm&&bm.menu?bm.menu().map(function(x){return x&&x.t;}):[];
  var vis=function(id){var e=document.getElementById(id);return !!(e&&e.offsetParent!==null&&getComputedStyle(e).display!=='none');};
  return{wf:ids.indexOf('wf')>=0,jalur:ids.indexOf('proj.jalur')>=0,jalurT:(f('proj.jalur')||{}).t,bmImport:mn.some(function(t){return /^Import block model/.test(t||'');}),
    rbWf:vis('rbWf'),aoi:!!document.getElementById('aoiBtn'),pita:(document.getElementById('jlrPita')||{}).textContent||'',mode:JLR.mode,acuan:JLR.acuan,tebak:JLR.tebak,log:(JLR.log||[]).length,
    badges:(function(){var o={};(function w(L){(L||[]).forEach(function(n){if(/^(gm\.|bm\.v\.)/.test(n.id))o[n.t]=n.b||'';w(n.kids);});})(PT.nodes);return o;})()};})()"""
FILE = r"""async function(nm){var r=await fetch('data-latihan/'+nm);var b=await r.blob();return new File([b],nm);}"""


def buka(ctx):
    pg = ctx.new_page(); err = []
    pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.on("pageerror", lambda e: err.append(str(e)[:300]))
    pg.goto(P); pg.wait_for_timeout(1500); return pg, err


def slot(pg, role, nm):
    pg.set_input_files('#imp .slot[data-role="%s"] input[type=file]' % role, str(DATA / nm)); pg.wait_for_timeout(700)


def masuk(pg):
    pg.click('#btnGo'); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(4000)


with sync_playwright() as pw:
    def ctxBaru():
        c = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1500, "height": 900})
        c.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};"); return c

    # ---------- 1 + 2: halaman pembuka & jalur Mulai dari nol ----------
    ctx = ctxBaru(); pg, err = buka(ctx)
    bmSlot = "(function(){var i=document.querySelector('#imp input[onchange*=\"SA.bmPick\"]');var s=i&&i.closest('.slot');return !!(s&&s.offsetParent!==null);})()"
    a = {"kartu": pg.evaluate("!!document.getElementById('jlrCard')"), "bmAwal": pg.evaluate(bmSlot)}
    for r, f in (("collar", "SIM_kecil_collar.csv"), ("survey", "SIM_kecil_survey.csv"), ("assay", "SIM_kecil_assay.csv"), ("geo", "SIM_kecil_geologi.csv")): slot(pg, r, f)
    pg.click('#btnGo'); pg.wait_for_timeout(1500)
    a["tolakTanpaPilih"] = pg.evaluate("!document.getElementById('imp').classList.contains('off')&&/Pilih jalur/.test(document.getElementById('jlrMsg').textContent)")
    pg.click('#jlrCard [data-jlr="lanjut"]'); pg.wait_for_timeout(300)
    pg.click('#btnGo'); pg.wait_for_timeout(800)
    a["tolakTanpaAcuan"] = pg.evaluate("/minimal satu acuan/.test(document.getElementById('jlrMsg').textContent)")
    pg.evaluate("JLR.acuanPend('bm',true)"); a["bmLanjut"] = pg.evaluate(bmSlot)
    pg.click('#jlrCard [data-jlr="nol"]'); pg.wait_for_timeout(300); a["bmNol"] = pg.evaluate(bmSlot)
    masuk(pg)
    a["nol"] = pg.evaluate(TREE)
    tolak = pg.evaluate("""(async function(){var F=%s;var o={};var n0=MD.models.length;
      bxDlg();await new Promise(function(r){setTimeout(r,300);});var d=document.getElementById('bxDlg');o.bxDlg=!!(d&&d.style.display==='flex');var a=document.getElementById('aoiDlg');o.aoiAlih=!!(a&&a.style.display==='flex');if(window.AOI)AOI.close();
      await mdImport({files:[await F('QV_Lensa2_Leapfrog.obj')],value:''},'geo');o.wfMasuk=MD.models.length-n0;
      uiTab('Wf');var p=document.getElementById('pWf');o.pWf=!!(p&&p.offsetParent!==null);
      o.simpan=(SA.collectWork().jalur||{}).mode;return o;})()""" % FILE)
    a["tolak"] = tolak
    pg.evaluate("JLR.dlg();JLR.keLanjut();document.getElementById('jlrK_wf').checked=true;JLR.keLanjutGo()"); pg.wait_for_timeout(1500)
    a["keLanjut"] = pg.evaluate(TREE); a["err"] = err; ctx.close(); hasil["nol"] = a
    if not (a["kartu"] and not a["bmAwal"] and a["tolakTanpaPilih"] and a["tolakTanpaAcuan"] and a["bmLanjut"] and not a["bmNol"]): salah.append("halaman pembuka: %s" % {k: a[k] for k in ("kartu", "bmAwal", "tolakTanpaPilih", "tolakTanpaAcuan", "bmLanjut", "bmNol")})
    n = a["nol"]
    if n["mode"] != "nol" or n["wf"] or n["rbWf"] or n["bmImport"] or not n["aoi"] or not n["jalur"] or "Mulai dari nol" not in n["pita"] or n["tebak"]: salah.append("jalur nol: %s" % n)
    if tolak["bxDlg"] or not tolak.get("aoiAlih") or tolak["wfMasuk"] or tolak["pWf"] or tolak["simpan"] != "nol": salah.append("pintu nol tidak tertutup: %s" % tolak)
    k = a["keLanjut"]
    if k["mode"] != "lanjut" or not k["wf"] or not k["acuan"]["wf"] or k["bmImport"] or k["log"] < 2 or "Lanjutan" not in k["pita"]: salah.append("jadikan lanjutan: %s" % k)
    if err: salah.append("galat halaman (nol): %s" % err[:3])

    # ---------- 3: jalur Lanjutan wireframe + block model ----------
    ctx = ctxBaru(); pg, err = buka(ctx)
    for r, f in (("collar", "SIM_kecil_collar.csv"), ("survey", "SIM_kecil_survey.csv"), ("assay", "SIM_kecil_assay.csv"), ("geo", "SIM_kecil_geologi.csv")): slot(pg, r, f)
    pg.click('#jlrCard [data-jlr="lanjut"]'); pg.wait_for_timeout(300); pg.evaluate("JLR.acuanPend('wf',true);JLR.acuanPend('bm',true)")
    pg.set_input_files('#imp input[onchange*="SA.bmPick"]', str(DATA / "SIM_BM_GC.csv")); pg.wait_for_timeout(1500)
    masuk(pg)
    b = {"awal": pg.evaluate(TREE)}
    b["aksi"] = pg.evaluate("""(async function(){var F=%s,W=function(ms){return new Promise(function(r){setTimeout(r,ms);});},o={};
      await mdImport({files:[await F('QV_Lensa2_Leapfrog.obj')],value:''},'geo');o.wf=MD.models.length;
      WFX.o={mi:0,sp:0,nama:'QV_Lensa2'};var r0=wfSerap();if(r0&&r0.then)await r0;for(var k=0;k<60&&!GM.doms.length;k++)await W(500);await W(1500);
      var d0=GM.doms[0];gmAddDom('QV_Eksak');var d1=GM.doms[GM.doms.length-1];wfxPakai(d1.id,MD.models[0].name);await W(500);
      o.arWf=arWfDoms().map(function(d){return d.name;});o.doms=GM.doms.map(function(d){return d.name+(d.wfx?'*':'');});
      JLR.setAcuan('wf',false);o.wfTetap=JLR.acuan.wf;JLR.keNol();o.nolDitolak=JLR.mode==='lanjut';JLR.dlgTutup();
      o.meFromGs=!!(window.meFromGs&&meFromGs._jlr);o.bmV=BXV.length;return o;})()""" % FILE)
    b["akhir"] = pg.evaluate(TREE); b["err"] = err; ctx.close(); hasil["lanjut"] = b
    w = b["awal"]
    if w["mode"] != "lanjut" or not (w["acuan"]["wf"] and w["acuan"]["bm"]) or not w["wf"] or not w["bmImport"] or w["tebak"]: salah.append("jalur lanjutan awal: %s" % w)
    if not any("acuan" == v.split(" · ")[-1] for v in w["badges"].values()): salah.append("versi block model acuan tidak ditandai: %s" % w["badges"])
    x = b["aksi"]; bd = b["akhir"]["badges"]
    if x["wf"] != 1 or "QV_Eksak" in x["arWf"] or not x["wfTetap"] or not x["nolDitolak"] or not x["meFromGs"]: salah.append("aksi lanjutan: %s" % x)
    if "acuan eksak" not in bd.get("QV_Eksak", "") or "diserap" not in bd.get("QV_Lensa2", ""): salah.append("tanda domain: %s" % bd)
    if err: salah.append("galat halaman (lanjut): %s" % err[:3])

    # ---------- 4: proyek lama tanpa jalur (SA.go tanpa pilihan, lalu applyWork tanpa w.jalur) ----------
    ctx = ctxBaru(); pg, err = buka(ctx)
    for r, f in (("collar", "SIM_kecil_collar.csv"), ("survey", "SIM_kecil_survey.csv"), ("assay", "SIM_kecil_assay.csv"), ("geo", "SIM_kecil_geologi.csv")): slot(pg, r, f)
    pg.evaluate("SA.go()"); pg.wait_for_function("document.getElementById('imp').classList.contains('off')", timeout=180000); pg.wait_for_timeout(4000)
    c = {"tebak0": pg.evaluate("[JLR.mode,JLR.tebak]")}
    c["impor"] = pg.evaluate("""(async function(){var F=%s;await mdImport({files:[await F('QV_Lensa2_Leapfrog.obj')],value:''},'geo');JLR.sinkron();return [MD.models.length,JLR.mode,JLR.acuan.wf,JLR.tebak];})()""" % FILE)
    c["lama"] = pg.evaluate("""(async function(){SA.applyWork({date:'x'});await new Promise(function(r){setTimeout(r,2200);});return [JLR.mode,JLR.acuan.wf,JLR.tebak];})()""")
    c["konfirmasi"] = pg.evaluate("JLR.konfirmasi();JLR.dlgTutup();[JLR.tebak,(JLR.log||[]).slice(-1)[0].ket]")
    c["pulih"] = pg.evaluate("SA.applyWork({jalur:{mode:'nol',acuan:{},log:[{t:'x',ket:'uji'}],tebak:false}});[JLR.mode,JLR.log.length]")
    c["err"] = err; ctx.close(); hasil["lama"] = c
    if c["tebak0"] != ["nol", True] or c["impor"] != [1, "lanjut", True, True] or c["lama"] != ["lanjut", True, True] or c["konfirmasi"][0] is not False or c["pulih"][0] != "nol":
        salah.append("proyek lama / tebakan: %s" % c)
    if err: salah.append("galat halaman (lama): %s" % err[:3])

    # ---------- 5: Demo data latihan ----------
    ctx = ctxBaru(); pg, err = buka(ctx)
    pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000); pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
    pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
    e = pg.evaluate(TREE); e["models"] = pg.evaluate("MD.models.length"); e["bx"] = pg.evaluate("!!(BX&&BX.m)"); e["err"] = err; ctx.close(); hasil["demo"] = e
    if e["mode"] != "lanjut" or not (e["acuan"]["wf"] and e["acuan"]["bm"]) or not e["wf"] or e["models"] < 1 or not e["bx"] or e["tebak"]: salah.append("demo: %s" % e)
    if err: salah.append("galat halaman (demo): %s" % err[:3])

srv.terminate()
print(json.dumps(hasil, ensure_ascii=False, indent=1))
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
sys.exit(1 if salah else 0)
