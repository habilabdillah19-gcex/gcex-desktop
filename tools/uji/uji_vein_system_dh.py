# -*- coding: utf-8 -*-
"""Vein System (Drill Hole 0.24.71): flag dari kolom kode, opsi semua vein + prioritas, volume & ekspor gabungan,
solid usang, resolusi adaptif. Data latihan simulasi (kolom geologi "Vein" dari tambah_kode_vein.py).

A. A/B (build lama vs baru): solid QV_Lensa2 dari wireframe Leapfrog (Serap) dengan parameter BAWAAN harus identik
   -- volume, jumlah verteks/segitiga, checksum koordinat, interval flag di dalam solid. (Resolusi adaptif bawaan mati.)
B. Build baru saja:
   1. Flag dari kolom "Vein": domain QV_Lensa1..4 + QV_Splay_HW dibuat, jumlah run per domain = hitungan Python dari CSV.
   2. Solid domain baru terbangun tanpa galat.
   3. Volume gabungan <= jumlah volume, tumpang tindih >= 0.
   4. Ekspor gabungan OBJ: satu berkas, jumlah verteks = jumlah verteks semua solid.
   5. Prioritas: domain ke-2 dinaikkan -> jadi urutan pertama gmTops().
   6. Resolusi adaptif: verteks berkurang, volume bergeser <= 5 %.
   7. Usang: Jalankan ulang otomatis mati -> flag diubah (sebab data) lalu parameter diubah (sebab + parameter),
      tampil di Project Tree; "Bangun ulang yang usang" mengosongkan daftar.
Pemakaian: python tools/uji/uji_vein_system_dh.py [--dasar=<ref git>]
"""
import csv, json, os, random, subprocess, sys, tempfile, time, urllib.request
from collections import defaultdict
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "3e9af7c")

AB = r"""(async function(){var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});};
  var mi=MD.models.findIndex(function(m){return /QV_Lensa2/.test(m.name);});WFX.o={mi:mi,sp:0,nama:'QV_Lensa2'};
  var r0=wfSerap();if(r0&&r0.then)await r0;for(var k=0;k<60&&!(GM.doms.length&&IM.R[GM.doms[0].id]);k++)await W(500);
  var d=GM.doms.find(function(x){return x.name==='QV_Lensa2';})||GM.doms[0];d.im=Object.assign(imPar(d),{on:true});imSync(true);await W(300);
  var R=IM.R[d.id],m=R.mesh,cs=0;for(var i=0;i<m.nv;i++)cs+=m._x[i]*1.3+m._y[i]*0.7+m._z[i]*1.1;
  return{vol:Math.round(R.st.vol*1000)/1000,nv:m.nv,nt:m.nt,cs:Math.round(cs*100)/100,nin:R.st.nin,nfl:R.st.nfl,area:Math.round(R.st.area)};})()"""

BARU = r"""(async function(){var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});},o={};
  var col=VS.kolom().filter(function(c){return c.n==='Vein'&&c.src==='g';})[0];o.kolom=col&&col.key;gmOpt('vsCol',col.key);gmOpt('vsGap',0);
  o.scan=VS.scan(col.key).map(function(s){return[s.kode,s.n,VS.itemKode(col.key,s).on];});
  o.ter=VS.terapkan(true);await W(500);imSync(true);await W(300);
  o.doms=GM.doms.map(function(d){var n=0;Object.keys(GM.flags).forEach(function(h){GM.flags[h].forEach(function(f){if(f[2]===d.id)n++;});});var R=IM.R[d.id];
    return{n:d.name,runs:n,on:imPar(d).on,err:R&&R.err||null,vol:R&&R.st?Math.round(R.st.vol):null,nv:R&&R.mesh?R.mesh.nv:0};});
  /* panel: bagian Flag punya tabel kode, bagian Solid punya tabel opsi + kotak gabungan */
  gmPanel();o.ui={flag:!!document.querySelector('#vsFlag #vsTab'),opsi:!!document.querySelector('#vsOpsiTab'),gab:!!document.querySelector('#vsGab')};
  /* jendela lebar: isi ikut diperbarui saat panel digambar ulang, tutup = berhenti diperbarui */
  var w=VS.pop('opsi');var n0=w.querySelectorAll('tr').length;o.ui.pop=n0===GM.doms.length+1&&w.style.display!=='none';var dd=GM.doms[0];VS.set(dd.id,'minT',imPar(dd).minT);
  o.ui.popSegar=w.querySelectorAll('tr').length===n0;w.querySelector('[data-x]').click();o.ui.popTutup=w.style.display==='none'&&!VS.popOn.opsi;
  var M=VS.hitung();o.gab={n:M.n,sum:Math.round(M.sum),ov:Math.round(M.ov),vol:Math.round(M.vol),pairs:M.pairs.length};
  var dl=[],sv=window.gxDl;window.gxDl=function(b,fn){dl.push(fn);};var X=VS.ekspor('obj');window.gxDl=sv;
  var txt=X.files[0].data,nvo=(txt.match(/\nv /g)||[]).length,sumNv=0;VS.solidL().forEach(function(d){sumNv+=IM.R[d.id].mesh.nv;});o.eks={files:X.files.length,nama:dl,nvObj:nvo,nvSum:sumNv};
  var T0=gmTops().map(function(d){return d.name;});VS.pindah(gmTops()[1].id,-1);o.prio={awal:T0,akhir:gmTops().map(function(d){return d.name;})};
  var d=GM.doms.find(function(x){return x.name==='QV_Lensa2';});var R0=IM.R[d.id].st;VS.set(d.id,'adp',true);imSync(true);await W(300);var R1=IM.R[d.id].st;
  o.adp={nv0:IM.R[d.id]&&R0.nnode,v0:Math.round(R0.vol),nv1:R1.nnode,v1:Math.round(R1.vol),adp:R1.adp};
  VS.set(d.id,'adp',false);imSync(true);await W(200);
  gmOpt('imAuto',false);var h=Object.keys(GM.flags).find(function(h){return GM.flags[h].some(function(f){return f[2]===d.id;});});var f=GM.flags[h].find(function(f){return f[2]===d.id;});
  gmPush();gmSetRange(h,f[0],f[1],null);gmDirty();imSync();await W(200);
  o.us1=VS.usang().map(function(x){return[x.d.name,x.sebab];});
  var P=imPar(d);d.im=Object.assign(P,{minT:P.minT+0.5});gmDirty();imSync();await W(200);o.us2=VS.usang().map(function(x){return[x.d.name,x.sebab];});
  PT.render(true);await W(300);o.tree=Array.prototype.slice.call(document.querySelectorAll('*')).some(function(e){return e.children.length===0&&/usang/.test(e.textContent||'')&&e.closest&&e.closest('#ptree,.ptree,[id*=tree]');});
  o.panelUsang=!!document.querySelector('#vsUsang');
  o.bangun=VS.bangunUsang();await W(300);o.us3=VS.usang().length;gmOpt('imAuto',true);
  return o;})()"""


def jalan(html, js):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
    (d / "index.html").write_bytes(html); os.symlink(DATA, d / "data-latihan")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    err = []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
        pg.on("pageerror", lambda e: err.append(str(e)[:300]))
        pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
        pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
        r = pg.evaluate(js); ctx.close()
    srv.terminate(); r = r if isinstance(r, dict) else {"r": r}; r["pageerror"] = err; return r


def harap():
    """run per kode dari CSV: interval berurutan sekode di lubang yang sama digabung (sela 0)."""
    H = defaultdict(list)
    for x in csv.DictReader(open(DATA / "SIM_geologi.csv")):
        if x["Vein"] != "-": H[(x["Hole_ID"], x["Vein"])].append((float(x["From"]), float(x["To"])))
    n = defaultdict(int)
    for (h, k), L in H.items():
        L.sort(); e = None
        for f, t in L:
            if e is None or f - e > 1e-6: n[k] += 1
            e = t if e is None else max(e, t)
    return dict(n)


salah = []
lama = subprocess.run(["git", "show", "%s:app-dh/index.html" % DASAR], cwd=ROOT, capture_output=True).stdout
baru = (ROOT / "app-dh/index.html").read_bytes()
A = jalan(lama, AB); B = jalan(baru, AB)
print("A/B lama (%s):" % DASAR, json.dumps(A)); print("A/B baru        :", json.dumps(B))
for k in ("vol", "nv", "nt", "cs", "nin", "nfl", "area"):
    if A.get(k) != B.get(k): salah.append("A/B solid bawaan berbeda: %s %s vs %s" % (k, A.get(k), B.get(k)))
if B["pageerror"]: salah.append("galat halaman (A/B baru): %s" % B["pageerror"][:3])

C = jalan(baru, BARU); print("\nfitur baru:", json.dumps(C, ensure_ascii=False, indent=1))
E = harap(); print("harapan run per kode:", E)
got = {d["n"]: d for d in C["doms"]}
for k, n in E.items():
    if k not in got: salah.append("domain %s tidak dibuat" % k); continue
    if got[k]["runs"] != n: salah.append("run %s: %s, harap %s" % (k, got[k]["runs"], n))
    if not got[k]["on"] or got[k]["err"] or not got[k]["vol"]: salah.append("solid %s tidak terbangun: %s" % (k, got[k]))
if any(s[0] == "-" and s[2] for s in C["scan"]): salah.append("kode '-' ikut tercentang")
if not all(C["ui"].values()): salah.append("bagian UI hilang: %s" % C["ui"])
g = C["gab"]
if not (g["n"] >= len(E) and g["vol"] <= g["sum"] and g["ov"] >= 0 and g["vol"] > 0): salah.append("gabungan tidak masuk akal: %s" % g)
if C["eks"]["files"] != 1 or C["eks"]["nvObj"] != C["eks"]["nvSum"] or not C["eks"]["nama"]: salah.append("ekspor gabungan: %s" % C["eks"])
if C["prio"]["akhir"][0] != C["prio"]["awal"][1]: salah.append("prioritas tidak berpindah: %s" % C["prio"])
a = C["adp"]
if not a["adp"] or not (a["nv1"] < a["nv0"]) or abs(a["v1"] - a["v0"]) > 0.05 * a["v0"]: salah.append("resolusi adaptif: %s" % a)
if not C["us1"] or "data" not in C["us1"][0][1]: salah.append("usang karena flag tidak terdeteksi: %s" % C["us1"])
if not C["us2"] or "parameter" not in C["us2"][0][1]: salah.append("usang karena parameter tidak terdeteksi: %s" % C["us2"])
if not C["tree"]: salah.append("tanda usang tidak tampil di Project Tree")
if not C["panelUsang"]: salah.append("kotak usang tidak tampil di panel Solid")
if C["bangun"] < 1 or C["us3"] != 0: salah.append("bangun ulang usang gagal: %s / sisa %s" % (C["bangun"], C["us3"]))
if C["pageerror"]: salah.append("galat halaman: %s" % C["pageerror"][:3])
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
sys.exit(1 if salah else 0)
