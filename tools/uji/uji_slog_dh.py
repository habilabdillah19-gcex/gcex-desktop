"""Parameter estimasi dari log Surpac (Drill Hole 0.24.79, web-src-dh/slog_dh.js).

Data latihan (fiktif) + log Surpac SINTETIS (tiga run BM FILL OK dengan parameter berbeda, satu run IDW).
1. Pembaca log: jumlah run, run kriging, unsur dari nama komposit, parameter tiap run, constraint, soft/hard.
2. Orientasi ZXY LRL: sumbu saling tegak lurus & satuan; bearing 90 / plunge 0 / dip 0 -> mayor ke timur.
3. Salin ke domain: variogram, elipsoid pencarian (mayor / faktor), min-maks sampel, sumber tercatat di jejak jalur.
4. Uji kecocokan: kolom acuan "auok" dibuat dari estimasi GC-Ex dengan parameter run B -> uji harus memilih run B
   (korelasi ~1), parameter domain dikembalikan, riwayat Model Estimation tidak bertambah.
5. Jalur Mulai dari nol: tombol tidak tampil di panel parameter & menu node Model Estimation.
"""
import json, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "tutorial-gcex" / "data"

def run(b, c0, c1, a1, az, pl, dp, sr, mr, maj, sf, mf, mn, mx, att="auok", comp="compositeau.str", con="QV_A", tag="Y"):
    return f"""§ 2026-01-0{b} 10:00:00
§ Surpac 6.6.2 (x64)
§ BM FILL OK
§ {{
frm20030={{
{{
attname="{att}"
}}
}}
frm20040={{
{{
datasrc="STRING FILE"
location="model/composite/{comp}"
range="1"
constrain="{'N' if tag == 'Y' else 'Y'}"
}}
}}
frm20080={{
{{
search="ELLIPSOID"
minsamples="{mn}"
maxsamples="{mx}"
majordist="{maj}"
max_samp_per_id="{mx}"
axis_1="{az}"
axis_2="{pl}"
axis_3="{dp}"
semimajfact="{sf}"
minorfact="{mf}"
rotationTypes="Surpac ZXY LRL"
}}
}}
frm20101={{
{{
model="SPHERICAL"
numstruct="1"
co="{c0}"
c1="{c1}"
a1="{a1}"
azimuth1="{az}"
plunge1="{pl}"
dip1="{dp}"
semi_ratio1="{sr}"
minor_ratio1="{mr}"
c2="0"
a2="0"
}}
}}
frm20111={{
{{
constraints=table {{ not op contype location id rnga rngb lbound ubound ext }} {{
{{ "" "INSIDE" "CONSTRAINT" "{con}" "" "" "" "" "" "" }}
}}
}}
}}
"""

LOG = (run(1, 0.10, 0.90, 60, 20, 0, 0, 1.5, 3.0, 40, 1.5, 3.0, 2, 20) +
       run(2, 0.05, 0.95, 30, 150, 60, 70, 1.3, 2.7, 20, 1.3, 2.7, 3, 12) +
       run(3, 0.30, 0.70, 15, 60, 10, 30, 2.0, 4.0, 10, 2.0, 4.0, 4, 8, tag="N") +
       "§ 2026-01-04 10:00:00\n§ BM FILL INVERSE DISTANCE\n§ {\nfrm20080={\n{\nmajordist=\"20\"\n}\n}\n}\n" +
       run(5, 0.05, 0.95, 30, 150, 60, 70, 1.3, 2.7, 20, 1.3, 2.7, 3, 12, att="ag", comp="compositeag.str"))

port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
(d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes()); (d / "data-latihan").symlink_to(DATA)
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)

salah, H, err = [], {}, []
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1600, "height": 950})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.on("pageerror", lambda e: err.append(str(e)[:300]))
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
    pg.wait_for_function("!DLAT.busy && window.SLOG", timeout=900000); pg.wait_for_timeout(2500)
    # domain dari kolom Vein + solid
    pg.evaluate("""(async function(){var col=VS.kolom().filter(function(c){return c.n==='Vein'&&c.src==='g';})[0];gmOpt('vsCol',col.key);gmOpt('vsGap',0);
      VS.terapkan(true);await new Promise(function(r){setTimeout(r,600);});imSync(true);await new Promise(function(r){setTimeout(r,600);});})()""")
    pg.wait_for_timeout(1500)
    # 1. pembaca
    H["baca"] = pg.evaluate("""(function(t){var n=SLOG.muat(t,'sintetis.log');var R=SLOG.runs;return {n:n,ok:R.filter(function(r){return r.ok;}).length,pil:SLOG.pil,
      un:R.map(function(r){return SLOG.unsur(r);}),r2:{c0:R[1].c0,S:R[1].S,cari:R[1].cari,con:R[1].con,hard:R[0].hard,hard3:R[2].hard}};})""", LOG)
    b = H["baca"]
    if b["n"] != 5 or b["ok"] != 4 or b["un"][:3] != ["Au", "Au", "Au"] or b["un"][4] != "Ag": salah.append("pembaca log: %s" % b)
    if abs(b["r2"]["c0"] - 0.05) > 1e-9 or b["r2"]["S"][0]["a"] != 30 or b["r2"]["S"][0]["p"] != 60 or b["r2"]["cari"]["maj"] != 20 or b["r2"]["cari"]["min"] != 3 or b["r2"]["con"] != ["INSIDE QV_A"]: salah.append("parameter run 2: %s" % b["r2"])
    if b["r2"]["hard"] or not b["r2"]["hard3"]: salah.append("soft/hard dari constrain data source: %s" % b["r2"])
    if b["pil"] != 2: salah.append("run bawaan bukan run Au terakhir (indeks 2): %s" % b["pil"])
    # 2. orientasi
    H["vek"] = pg.evaluate("""(function(){var o=[];[[90,0,0],[151,76,80],[20,-35,10]].forEach(function(a){var v=SLOG.vek(a[0],a[1],a[2]);var d=function(p,q){return p[0]*q[0]+p[1]*q[1]+p[2]*q[2];};
      o.push({v:v,orto:Math.max(Math.abs(d(v.vM,v.vS)),Math.abs(d(v.vM,v.vN)),Math.abs(d(v.vS,v.vN))),len:[d(v.vM,v.vM),d(v.vS,v.vS),d(v.vN,v.vN)],az:meAzPl(v.vM)});});return o;})()""")
    v0 = H["vek"][0]["v"]
    if abs(v0["vM"][0] - 1) > 1e-9 or abs(v0["vM"][2]) > 1e-9: salah.append("bearing 90 bukan ke timur: %s" % v0)
    for q in H["vek"]:
        if q["orto"] > 1e-9 or any(abs(x - 1) > 1e-9 for x in q["len"]): salah.append("sumbu tidak ortonormal: %s" % q)
    # 3. salin ke domain (run 2)
    H["salin"] = pg.evaluate("""(function(){SLOG.set('pil',1);SLOG.dom={};GM.doms.forEach(function(d){SLOG.dom[d.id]=true;});var n=SLOG.terapkan();var d=GM.doms[0],P=meParOf(d);
      return {n:n,nd:GM.doms.length,src:P.src,A:P.m.A,B:P.m.B,Cn:P.m.Cn,c0:P.m.c0,cs:P.m.cs,sr:P.sr,P:P.P,hard:!!P.hard,log:(JLR.log||[]).map(function(l){return l.ket;}).slice(-1)[0]||''};})()""")
    s = H["salin"]
    if s["n"] != s["nd"] or abs(s["A"][0] - 30) > 1e-9 or abs(s["B"][0] - 30 / 1.3) > 1e-3 or abs(s["Cn"][0] - 30 / 2.7) > 1e-3 or abs(s["sr"][0] - 20) > 1e-9 or abs(s["sr"][1] - 20 / 1.3) > 1e-2 or s["P"][0]["min"] != 3 or s["P"][0]["max"] != 12 or s["hard"]:
        salah.append("salin parameter: %s" % s)
    if "log Surpac" not in s["src"] or "log Surpac" not in s["log"]: salah.append("sumber / jejak tidak mencatat log Surpac: %s" % s)
    H["err_sebelum_uji"] = list(err)
    pg.evaluate("window.addEventListener('error',function(e){window._ES=(e.error&&e.error.stack)||e.message;});window.addEventListener('unhandledrejection',function(e){window._ES=(e.reason&&e.reason.stack)||String(e.reason);});")
    # 4. uji kecocokan: kolom acuan auok = estimasi GC-Ex dengan parameter run 2
    pg.evaluate("meRun()"); pg.wait_for_timeout(1500); pg.wait_for_function("!ME.job", timeout=900000); pg.wait_for_timeout(800)
    H["acuan"] = pg.evaluate("""(function(){var a=BX.m.num.au_est,n=0;BX.m.num.auok=Float32Array.from(a,function(v){return v>0?v:-99;});var B0=BX.m._meBase;if(B0&&B0.num)B0.num.auok=BX.m.num.auok.slice(0,B0.n);for(var i=0;i<BX.m.n;i++)if(a[i]>0)n++;
      GM.doms.forEach(function(d){d.est=null;});gmDirty(true);return {n:n,runs:ME.store.runs.length};})()""")
    if H["acuan"]["n"] < 100: salah.append("estimasi acuan terlalu sedikit blok: %s" % H["acuan"])
    pg.evaluate("SLOG.set('pil',2);SLOG.ujiJalan()"); pg.wait_for_timeout(2000)
    pg.wait_for_function("!SLOG.uji.jalan", timeout=1800000, polling=1000); pg.wait_for_timeout(800)
    H["uji"] = pg.evaluate("""(function(){var o={};Object.keys(SLOG.uji.hasil).forEach(function(i){var h=SLOG.uji.hasil[i];o[i]=h?[h.rS,h.r,h.n,h.cak]:null;});
      return {best:SLOG.uji.best,pil:SLOG.pil,h:o,par:GM.doms.map(function(d){return !!d.est;}),runs:ME.store.runs.length};})()""")
    u = H["uji"]
    if u["best"] != 1 or u["pil"] != 1: salah.append("uji kecocokan tidak memilih run 2 (indeks 1): %s" % u)
    if not u["h"].get("1") or (u["h"]["1"][0] or 0) < 0.999: salah.append("korelasi run 2 dengan acuan buatannya sendiri bukan ~1: %s" % u["h"])
    if any(u["par"]): salah.append("parameter domain tidak dikembalikan sesudah uji: %s" % u["par"])
    if u["runs"] != H["acuan"]["runs"]: salah.append("riwayat Model Estimation bertambah oleh uji: %s -> %s" % (H["acuan"]["runs"], u["runs"]))
    if "4" in u["h"]: salah.append("run Ag ikut diuji terhadap kolom auok")
    H["err_sesudah_uji"] = list(err); H["stack"] = pg.evaluate("window._ES||''")
    # 5. jalur nol: pintu tidak tampil
    H["nol"] = pg.evaluate("""(function(){JLR.mode='nol';JLR.tebak=false;JLR.acuan={wf:false,bm:false,par:false};PT.render(true);var d=GM.doms[0];
      var h=meParHtml(d);var me=PT.flatAll(PT.nodes).filter(function(n){return n.id==='me';})[0];var m=me&&me.menu?me.menu().map(function(x){return x.t;}):[];
      return {panel:/Isi dari log Surpac/.test(h),menu:m.some(function(t){return /log Surpac/.test(t);}),boleh:SLOG.boleh()};})()""")
    if H["nol"]["panel"] or H["nol"]["menu"] or H["nol"]["boleh"]: salah.append("jalur nol masih menampilkan pintu log Surpac: %s" % H["nol"])
    ctx.close()
srv.terminate()
if err: salah.append("galat halaman: %s" % err[:3])
print(json.dumps(H, ensure_ascii=False, indent=1)[:4000])
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
sys.exit(1 if salah else 0)
