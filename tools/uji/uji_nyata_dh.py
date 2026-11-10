# -*- coding: utf-8 -*-
"""DH 0.24.65: perbaikan dari uji data nyata Zona 3 (pemilik, 11-11-2026). Data latihan vein bercabang (SIM_split_*), fiktif.
Diperiksa:
  #11/#12 validasi impor menyebut Hole ID per butir; geologi Windows-1252 (karakter ±) terbaca benar + peringatan
  #13 import flag CSV menawarkan hapus flag lama domain yang sama di lubang yang tidak ada di file
  #2/#9 statistik solid: nab (flag di atas topografi) & far15/far30 (ekstrapolasi) ada
  #3 titik sambung cabang dibatasi <= max(3, kontak cabang); tebal dibatasi 1,5 x tebal kontak terbesar
  #4 selubung: statistik & validasi solid tidak lagi 0
  #6/#7 fitting otomatis mayor >= semi-mayor; minor per struktur (mD) dipakai bila diubah
  #16 sayatan di bidang domain mengumpulkan komposit domain
  #8 kerangka AOI snap ke origin grid
  #10 ID² pembanding (au_id2) + radius pencarian / jarak pengaruh maks (semua lubang) mengurangi blok terestimasi
  #1 export .mdl dari kerangka AOI terbaca kembali (jumlah blok & nilai sama)
  #18 jendela Status alur pemodelan berisi 10 langkah"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
TMP = Path(tempfile.mkdtemp())
# geologi Windows-1252 dengan karakter ± (seperti file Excel Indonesia)
g = (DATA / "SIM_split_geologi.csv").read_text(encoding="utf-8").splitlines()
g = [g[0]] + [l.replace(",PRO,", ",PRO±ARG,", 1) if i % 7 == 0 else l for i, l in enumerate(g[1:])]
(TMP / "geo1252.csv").write_bytes(("\r\n".join(g) + "\r\n").encode("cp1252"))

def serve(app):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / app).read_bytes())
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    return srv, P

H = {}; salah = []; DLG = []
with sync_playwright() as pw:
    srv, P = serve("app-dh/index.html")
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900}, accept_downloads=True)
    ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
    pg = ctx.new_page(); ERR = []
    pg.on("pageerror", lambda e: ERR.append(str(e)[:300]))
    pg.on("dialog", lambda x: (DLG.append(x.message[:200]), x.accept(x.default_value) if x.type == "prompt" else x.accept()))
    pg.goto(P); pg.wait_for_timeout(1500)
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(400)
    inp = lambda k: pg.locator('input[onchange*="%s"]' % k).first
    for role, f in [("collar", DATA / "SIM_split_collar.csv"), ("survey", DATA / "SIM_split_survey.csv"), ("assay", DATA / "SIM_split_assay.csv"), ("geo", TMP / "geo1252.csv")]:
        inp("slotFile('%s'" % role).set_input_files(str(f)); pg.wait_for_timeout(1200)
    inp("addSp('topo'").set_input_files(str(DATA / "SIM_topo_xyz.csv")); pg.wait_for_timeout(1500)
    pg.evaluate("SA.preview()"); pg.wait_for_timeout(800)
    H["val"] = pg.evaluate("(function(){document.querySelectorAll('#imp details').forEach(function(d){d.open=true;});return {enc:SA.encNote||'',txt:(document.getElementById('dbSum')||{}).textContent||''};})()")
    pg.evaluate("document.getElementById('dsName').value='Uji_nyata';try{SA.preview()}catch(e){};SA.go()")
    pg.wait_for_function("document.getElementById('imp').classList.contains('off') && window.collars && collars.length>0", timeout=300000); pg.wait_for_timeout(4000)
    H["geo"] = pg.evaluate("(function(){var s=JSON.stringify(geoCat);return {pm:s.indexOf('PRO±ARG')>=0,bad:s.indexOf('�')>=0};})()")
    # ---- domain induk + cabang (run terdalam di lubang bertembusan dua = cabang)
    H["gm"] = pg.evaluate("""(function(){uiTab('GM');var u=gmAddDom('QVS_Utama');Object.assign(GM.opt,{el:'Au',cut:0.5,dil:1,minL:1,scope:'all',keep:true});gmAuto();var c=gmAddDom('QVS_Cabang');
      Object.keys(GM.flags).forEach(function(h){var L=GM.flags[h].filter(function(f){return f[2]===u.id;});if(L.length>=2){var f=L[L.length-1];gmSetRange(h,f[0],f[1],c.id);}});gmSetPar(c.id,u.id);gmDirty(true);
      var S=arStrike(u),sp=20,azL=(S.az+90)%180,r=azL*Math.PI/180,ux=Math.sin(r),uy=Math.cos(r),L2=S.panjang/2;$('sMode').value='P';$('p1e').value=(S.c[0]-ux*L2+offX).toFixed(2);$('p1n').value=(S.c[1]-uy*L2+offY).toFixed(2);$('p2e').value=(S.c[0]+ux*L2+offX).toFixed(2);$('p2n').value=(S.c[1]+uy*L2+offY).toFixed(2);$('dipS').value=90;$('thick').value=sp;modeChanged();
      GM.act=u.id;gmDraft(true);GM.act=c.id;gmDraft(true);imAll(true);var o={};GM.doms.forEach(function(d){var R=IM.R[d.id];o[d.name]=R.err?{err:R.err}:{vol:R.st.vol,nin:R.st.nin,nfl:R.st.nfl,nab:R.st.nab,far15:R.st.far15,nj:R.st.nj,njAll:R.st.njAll,nc:R.st.nc,tCap:R.st.tCap,tmax:R.st.tmax};});
      var ba=document.querySelector('[data-k="all"]');if(ba)ba.click();o.panel=(document.getElementById('gmBody')||{}).textContent||'';return o;})()""")
    # ---- import flag CSV: lubang di luar file ber-flag lama -> ditawari hapus
    rows = pg.evaluate("(function(){var r=['HoleID,From,To,Domain'],u=GM.doms[0],n=0;Object.keys(GM.flags).sort().forEach(function(h){GM.flags[h].forEach(function(f){if(f[2]===u.id&&n<5){r.push([h,f[0],f[1],'QVS_Utama'].join(','));n++;}});});return r.join('\\n');})()")
    (TMP / "flag.csv").write_text(rows + "\n", encoding="utf-8")
    pg.evaluate("GM._snap=JSON.stringify(GM.flags)")
    DLG.clear(); pg.locator('input[onchange*="gmFlagImport"]').first.set_input_files(str(TMP / "flag.csv")); pg.wait_for_timeout(1200)
    H["flag"] = {"dlg": list(DLG), "msg": pg.evaluate("GM.lastAuto"), "nU": pg.evaluate("(function(){var u=GM.doms[0].id,n=0;Object.keys(GM.flags).forEach(function(h){GM.flags[h].forEach(function(f){if(f[2]===u)n++;});});return n;})()")}
    pg.evaluate("GM.flags=JSON.parse(GM._snap);gmDirty(true);imSync(true)")
    # ---- selubung
    H["env"] = pg.evaluate("""(function(){var u=GM.doms[0];envNew(u.id);var e=envOf(u.id);e.envO=Object.assign(envO(e),{cut:0.2});envAuto(e.id,true);GM.act=e.id;gmDraft(true);e.im=Object.assign(imPar(e),{on:true});imSync(true);gmDirty(true);
      var S=gmStats()[e.id],R=IM.R[e.id];return {h:Object.keys(S.h).length,l:S.l,nfl:R&&R.st?R.st.nfl:-1,nin:R&&R.st?R.st.nin:-1,softD:envO(e).softD};})()""")
    # ---- geostatistik: sayatan bidang domain + fitting
    pg.evaluate("GM.act=GM.doms[0].id;GS.domOnly=true;NY.planeSec()"); pg.wait_for_timeout(3000)
    pg.evaluate("$('gComp').value=1;$('gAuto').checked=true;gsRun()"); pg.wait_for_timeout(2500)
    pg.evaluate("gsgAll()"); pg.wait_for_function("!(window.GSG&&GSG.busy)&&!(window.GSR&&GSR.busy)", timeout=600000); pg.wait_for_timeout(1500)
    H["gs"] = pg.evaluate("""(function(){var R=GS.R,M=R.M;var o={n:R.st.n,plane:NY.lastPlane,a:M.a,b:M.b,bar:($('gsDomBar')||{}).innerText||''};
      var s=function(i,v){$(i).value=v;$(i).dispatchEvent(new Event('change'));};s('mMin','');var b1=M.b[0];s('mD1',Math.max(0.5,b1/3));o.Cn=okModel().Cn;o.d1=+$('mD1').value;o.ok=meFromGs(GM.doms[0].id);
      GM.act=envOf(GM.doms[0].id).id;o.okHalo=meFromGs(GM.act);return o;})()""")
    # ---- kerangka AOI: snap ke origin grid sembarang
    H["aoi"] = pg.evaluate("""(function(){uiTab('BM');var x=collars.map(function(c){return c[1];}),y=collars.map(function(c){return c[2];}),z=collars.map(function(c){return c[3];});
      var mn=function(a){return Math.min.apply(null,a);},mx=function(a){return Math.max.apply(null,a);};AOI.dlg();
      Object.assign(AOI.cfg,{x0:mn(x)-40,x1:mx(x)+40,y0:mn(y)-40,y1:mx(y)+40,zb:mn(z)-120,zt:mx(z)+5,bx:4,by:4,bz:2,snap:true,ox:7,oy:3,oz:1,topo:0,pit:0,poly:'',mode:'penuh',name:'AOI_uji'});AOI.body();AOI.go();return 1;})()""")
    pg.wait_for_function("window.BX&&BX.m&&BX.m.aoi&&!AOI.busy", timeout=300000); pg.wait_for_timeout(800)
    H["aoi"] = pg.evaluate("(function(){var c=BX.m.aoi.cfg;return {n:BX.m.n,x0:c.x0,y0:c.y0,zb:c.zb,rx:((c.x0-7)/4)%1,ry:((c.y0-3)/4)%1,rz:((c.zb-1)/2)%1};})()")
    # ---- Model Estimation: ID², lalu radius & jarak pengaruh maks (semua lubang)
    def run():
        pg.evaluate("uiTab('ME');meRun()"); pg.wait_for_function("!ME.job", timeout=900000, polling=500); pg.wait_for_timeout(800)
        return pg.evaluate("""(function(){var u=GM.doms[0],r=ME.store.runs.filter(function(q){return q.domId===u.id;}).pop(),m=BX.m,E=m.num.au_est,I=m.num.au_id2,n=0,sx=0,sy=0,sxx=0,syy=0,sxy=0;
          if(I)for(var i=0;i<m.n;i++){if(E[i]>-90&&I[i]>-90){n++;sx+=E[i];sy+=I[i];sxx+=E[i]*E[i];syy+=I[i]*I[i];sxy+=E[i]*I[i];}}var cor=n>2?(n*sxy-sx*sy)/Math.sqrt((n*sxx-sx*sx)*(n*syy-sy*sy)):null;
          return {nEst:r.nEst,nFail:r.nFail,id2:!!I,nPair:n,cor:cor,panel:document.body.textContent.indexOf('Area pengaruh')>=0};})()""")
    H["me1"] = run()
    pg.evaluate("(function(){var u=GM.doms[0];meLimPar(u.id,'sr0',12);meLimPar(u.id,'sr1',12);meLimPar(u.id,'sr2',6);meLimPar(u.id,'d',8);})()")
    H["me2"] = run()
    H["lim"] = pg.evaluate("(function(){var P=GM.doms[0].est;return {sr:P.sr,lim:P.lim,of:meLimOf(P)};})()")
    # ---- export .mdl kerangka AOI -> dibaca ulang
    H["mdl"] = pg.evaluate("""(async function(){var m=BX.m,S=NY.mdlSynth(m);if(S.err)return {err:S.err};var R=bxMdlBytes(S.mm,'uji.mdl'),f=new File(R.parts,'uji.mdl');var M=await SA.readMDL(f,function(){});
      var k=function(x,y,z){return Math.round(x*2)+'|'+Math.round(y*2)+'|'+Math.round(z*2);},mp={};for(var i=0;i<m.n;i++)mp[k(m.x[i],m.y[i],m.z[i])]=i;var hit=0,eq=0,A=m.num.au_est,B=M.num.au_est,j;
      for(j=0;j<M.n;j++){var i2=mp[k(M.x[j],M.y[j],M.z[j])];if(i2===undefined)continue;hit++;var a=A[i2],b=B?B[j]:NaN;if((!isFinite(a)&&b===-99)||Math.abs(a-b)<1e-6)eq++;}
      return {n:m.n,nR:M.n,hit:hit,eq:eq,attrs:Object.keys(M.num).length,bad:R.bad,origin:S.origin,L:S.L};})()""")
    # ---- status alur
    pg.evaluate("NY.status()"); pg.wait_for_timeout(600)
    H["st"] = pg.evaluate("(function(){var w=document.getElementById('nyStatusWin');return {n:w?w.querySelectorAll('.nyr').length:0,txt:w?w.innerText.slice(0,400):''};})()")
    H["err"] = ERR
    ctx.close(); srv.terminate()

for k, v in H.items(): print(k, json.dumps(v, ensure_ascii=False)[:600])
v = H["val"]
if "bukan UTF-8" not in v["enc"] or "Windows-1252" not in v["txt"]:
    print("VAL-TXT", v["txt"][-700:])
    salah.append("#12 peringatan encoding tidak muncul")
if not (H["geo"]["pm"] and not H["geo"]["bad"]): salah.append("#12 karakter ± tidak terbaca benar: %s" % H["geo"])
gm = H["gm"]; c = gm.get("QVS_Cabang", {}); u = gm.get("QVS_Utama", {})
if "err" in c or "err" in u: salah.append("solid gagal: %s" % gm)
else:
    if c.get("nj", 0) > max(3, c.get("nc", 0)): salah.append("#3 titik sambung tidak dibatasi: %s" % c)
    if not (c.get("tCap", 0) > 0 and c["tmax"] <= c["tCap"] + 1e-6): salah.append("#3 batas tebal tidak bekerja: %s" % c)
    for d in (u, c):
        if d.get("nab") is None or d.get("far15") is None: salah.append("#2/#9 statistik solid baru tidak ada: %s" % d)
    if "Volume jauh dari kontak bor" not in gm["panel"]: salah.append("#9 baris ekstrapolasi tidak tampil di panel")
f = H["flag"]
if not any("TIDAK tercantum di file" in x for x in f["dlg"]) or f["nU"] != 5: salah.append("#13 import flag: %s" % f)
e = H["env"]
if not (e["h"] > 0 and e["l"] > 0 and e["nfl"] > 0): salah.append("#4 statistik / validasi selubung masih 0: %s" % e)
s = H["gs"]
if not (s["n"] > 20 and s["ok"] and s["okHalo"]): salah.append("#16 sayatan bidang domain / simpan parameter: %s" % s)
if any(a + 1e-9 < b for a, b in zip(s["a"], s["b"])): salah.append("#6 mayor < semi-mayor: %s" % s)
if abs(s["Cn"][0] - min(s["d1"], s["b"][0])) > 1e-6: salah.append("#7 minor per struktur tidak dipakai: %s" % s)
if "Sayatan di bidang domain" not in s["bar"]: salah.append("#16 tombol tidak ada di bilah domain")
a = H["aoi"]
if max(abs(a["rx"]), abs(a["ry"]), abs(a["rz"])) > 1e-6: salah.append("#8 AOI tidak sejajar origin grid: %s" % a)
m1, m2 = H["me1"], H["me2"]
if not (m1["id2"] and m1["nPair"] > 50 and m1["cor"] > 0.8 and m1["panel"]): salah.append("#10 ID² / panel: %s" % m1)
if not (m2["nEst"] < m1["nEst"]): salah.append("#10 radius / jarak pengaruh tidak mengurangi blok: %s %s" % (m1, m2))
md = H["mdl"]
if "err" in md or md["nR"] != md["n"] or md["eq"] != md["hit"] or md["hit"] != md["n"]: salah.append("#1 export .mdl AOI: %s" % md)
if H["st"]["n"] != 10: salah.append("#18 status alur: %s" % H["st"])
if H["err"]: salah.append("pageerror: %s" % H["err"][:3])
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
sys.exit(1 if salah else 0)
