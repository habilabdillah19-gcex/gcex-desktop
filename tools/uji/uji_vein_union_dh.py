# -*- coding: utf-8 -*-
"""DH 0.24.84: induk + cabang vein MENYATU (boolean union, web-src-dh/vunion_dh.js; pustaka web-src/manifold.js + web-src/mfbool.js sejak DH 0.24.85).

Pemilik 12 Nov 2026: "Bisakah GCex menyambungkan cabang dengan induk sehingga benar-benar menyatu?" -> Pilihan 1.
Data latihan vein bercabang SIM_split_* (fiktif), domain QVS_Utama + QVS_Cabang (cabang = run terdalam di lubang
bertembusan dua), seperti tutorial bab "Vein bercabang: domain induk".
Diperiksa:
  A. pustaka boolean termuat (WASM tertanam, tanpa jaringan) dan grup induk tergabung jadi SATU bagian
  B. mesh gabungan tertutup: setiap sisi dipakai tepat dua segitiga, orientasi konsisten (volume bertanda > 0)
  C. volume union = volume gabungan sampling grid lama (+-3 %), <= jumlah, >= solid terbesar
  D. tampilan 3D & sayatan 2D: satu trace solid untuk grup (dulu dua); dimatikan -> dua lagi
  E. ekspor STR+DTM per domain (cabang ikut induk, bawaan nyala): satu berkas solid induk, tanpa berkas cabang,
     DTM closed=yes, jumlah segitiga = mesh union
  F. estimasi tidak berubah: ME._grp (induk + cabang) tetap dari solid anggota
Pemakaian: python tools/uji/uji_vein_union_dh.py [--html app-dh/index.html]
A/B: build lama (tanpa VU) -> GAGAL di A."""
import json, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
ARG = dict(zip(sys.argv[1::2], sys.argv[2::2])); HTML = Path(ARG.get("--html", ROOT / "app-dh" / "index.html"))
salah = []
def cek(ok, m):
    print(("  ok    " if ok else "  GAGAL ") + m)
    if not ok: salah.append(m)

port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes(HTML.read_bytes())
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
try:
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1500, "height": 900}, accept_downloads=True)
        ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
        pg = ctx.new_page(); ERR = []
        pg.on("pageerror", lambda e: ERR.append(str(e)[:300]))
        pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
        # blokir jaringan luar: pustaka harus tertanam
        pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://localhost") or r.request.url.startswith("data:") or r.request.url.startswith("blob:") else r.abort())
        pg.goto(P); pg.wait_for_timeout(1500)
        if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(400)
        inp = lambda k: pg.locator('input[onchange*="%s"]' % k).first
        for role, f in [("collar", "SIM_split_collar.csv"), ("survey", "SIM_split_survey.csv"), ("assay", "SIM_split_assay.csv"), ("geo", "SIM_split_geologi.csv")]:
            inp("slotFile('%s'" % role).set_input_files(str(DATA / f)); pg.wait_for_timeout(1000)
        inp("addSp('topo'").set_input_files(str(DATA / "SIM_topo_xyz.csv")); pg.wait_for_timeout(1500)
        pg.evaluate("document.getElementById('dsName').value='Uji_union';try{SA.preview()}catch(e){};SA.go()")
        pg.wait_for_function("document.getElementById('imp').classList.contains('off') && window.collars && collars.length>0", timeout=300000); pg.wait_for_timeout(3000)
        pg.evaluate("""(function(){uiTab('GM');var u=gmAddDom('QVS_Utama');Object.assign(GM.opt,{el:'Au',cut:0.5,dil:1,minL:1,scope:'all',keep:true});gmAuto();var c=gmAddDom('QVS_Cabang');
          Object.keys(GM.flags).forEach(function(h){var L=GM.flags[h].filter(function(f){return f[2]===u.id;});if(L.length>=2&&L[L.length-1][0]-L[L.length-2][1]>=4){var f=L[L.length-1];gmSetRange(h,f[0],f[1],c.id);}});
          gmSetPar(c.id,u.id);GM.act=u.id;gmDraft(true);GM.act=c.id;gmDraft(true);GM.act=u.id;imAll(true);gmDirty(true);})()""")
        pg.wait_for_timeout(1500)
        ada = pg.evaluate("!!window.VU")
        cek(ada, "A modul penyatuan (VU) ada di build")
        if ada:
            pg.evaluate("VU.load()")
            pg.wait_for_function("window.VU && (VU.mod || VU.err)", timeout=60000)
            H = pg.evaluate("""(function(){var u=GM.doms[0],c=GM.doms[1],g=VU.grup(u.id),m=g&&g.mesh,o={err:VU.err,ok:!!g,
                vU:IM.R[u.id].st.vol,vC:IM.R[c.id].st.vol};if(!g)return Object.assign(o,{gerr:(VU.C[u.id]||{}).err});
              o.vol=g.vol;o.nKomp=g.nKomp;o.nv=m.nv;o.nt=m.nt;
              var E={},bad=0,sv=0;for(var t=0;t<m.nt;t++){var a=[m._i[t],m._j[t],m._k[t]];for(var q=0;q<3;q++){var x=a[q],y=a[(q+1)%3],k=x<y?x+'_'+y:y+'_'+x;E[k]=(E[k]||0)+1;}
                var A=a[0],B=a[1],C=a[2];sv+=m._x[A]*(m._y[B]*m._z[C]-m._z[B]*m._y[C])-m._y[A]*(m._x[B]*m._z[C]-m._z[B]*m._x[C])+m._z[A]*(m._x[B]*m._y[C]-m._y[B]*m._x[C]);}
              Object.keys(E).forEach(function(k){if(E[k]!==2)bad++;});o.edgeBad=bad;o.edges=Object.keys(E).length;o.sv=sv/6;
              GM.opt.imUni=false;var s0=imGrpStat(u.id);o.volGrid=s0.vol;o.sum=s0.sum;GM.opt.imUni=true;var s1=imGrpStat(u.id);o.stUni=s1.uni;o.stVol=s1.vol;
              var cnt=function(){var T=[];imTraces(T,{clip:false,K:null});return T.filter(function(t){return t.type==='mesh3d';}).length;};
              o.tr1=cnt();GM.opt.imUni=false;o.tr0=cnt();GM.opt.imUni=true;
              var K=[{n:[0,1,0],c:[0,0,0],lo:-1,hi:1}];try{var cx=(m._x[0]),cy=0;var Fr=IM.R[u.id].fr;K=[{n:[Fr.u[0],Fr.u[1],Fr.u[2]],c:Fr.c,lo:-1.25,hi:1.25}];}catch(e){}
              var F=function(x,y,z){return [x,z];};o.s2=imTraces2D({K:K},F).length;GM.opt.imUni=false;o.s2off=imTraces2D({K:K},F).length;GM.opt.imUni=true;
              var X=imFiles('str',false);o.files=X?X.files.map(function(f){return f.name;}):[];var dtm=X?X.files.filter(function(f){return /\\.dtm$/.test(f.name);}):[];
              o.dtmClosed=dtm.length?/closed=yes/.test(dtm[0].data):false;o.dtmTri=dtm.length?dtm[0].data.split('\\n').filter(function(l){return /^[1-9]\\d*, /.test(l);}).length:0;
              try{var G=ME._grp&&ME._grp[u.id];o.meGrp=G?G.mesh.parts:null;}catch(e){}
              o.kompU=VU.union([IM.R[u.id].mesh],'u').nKomp;o.kompC=VU.union([IM.R[c.id].mesh],'c').nKomp;o.ngrU=IM.R[u.id].st.ngr;o.ngrC=IM.R[c.id].st.ngr;
              o.vKomp=VU.union([IM.R[u.id].mesh,IM.R[c.id].mesh],'x').vKomp;
              return o;})()""")
            print(json.dumps(H, indent=1))
            cek(not H.get("err") and H["ok"], "A pustaka boolean termuat tanpa jaringan dan grup tergabung (%s)" % (H.get("err") or H.get("gerr") or "ok"))
            if H["ok"]:
                cek(H["nKomp"] < H["kompU"] + H["kompC"], "A cabang menyatu dengan induk: union %d bagian, induk sendiri %d, cabang sendiri %d" % (H["nKomp"], H["kompU"], H["kompC"]))
                cek(H["edgeBad"] == 0, "B mesh tertutup: %d dari %d sisi tidak dipakai tepat dua segitiga" % (H["edgeBad"], H["edges"]))
                cek(H["sv"] > 0 and abs(H["sv"] - H["vol"]) < 1e-3 * H["vol"] + 1, "B orientasi hadap luar (volume bertanda %.1f = %.1f)" % (H["sv"], H["vol"]))
                cek(abs(H["vol"] - H["volGrid"]) <= 0.03 * H["volGrid"], "C volume union %.0f = sampling grid %.0f (+-3 %%)" % (H["vol"], H["volGrid"]))
                cek(max(H["vU"], H["vC"]) - 1 <= H["vol"] <= H["sum"] + 1, "C max anggota %.0f <= union %.0f <= jumlah %.0f" % (max(H["vU"], H["vC"]), H["vol"], H["sum"]))
                cek(H["stUni"] and abs(H["stVol"] - H["vol"]) < 1, "C panel volume gabungan memakai hasil union")
                cek(H["tr1"] == 1 and H["tr0"] == 2, "D 3D: satu solid gabungan (%d), dimatikan dua (%d)" % (H["tr1"], H["tr0"]))
                cek(H["s2"] <= 1 and H["s2off"] >= H["s2"], "D sayatan 2D: %d trace (dimatikan %d)" % (H["s2"], H["s2off"]))
                cek(len([f for f in H["files"] if f.endswith(".str")]) == 1 and not any("cabang" in f.lower() for f in H["files"]), "E ekspor: satu solid induk, tanpa berkas cabang: %s" % H["files"])
                cek(H["dtmClosed"] and H["dtmTri"] == H["nt"], "E DTM closed=yes, %d segitiga = mesh union %d" % (H["dtmTri"], H["nt"]))
                cek(H.get("meGrp") in (None, 2), "F estimasi tetap dari solid anggota (ME._grp parts = %s)" % H.get("meGrp"))
        if ada and ARG.get("--shot"):
            # gambar sayatan untuk dokumentasi: sayatan tegak memotong strike di tengah grup, union nyala vs mati
            pg.evaluate("""(()=>{var cx=505000,cy=9012000,az=135*Math.PI/180;$('sMode').value='P';$('p1e').value=(cx-90*Math.sin(az)).toFixed(1);$('p1n').value=(cy-90*Math.cos(az)).toFixed(1);$('p2e').value=(cx+90*Math.sin(az)).toFixed(1);$('p2n').value=(cy+90*Math.cos(az)).toFixed(1);
              $('dipS').value=90;$('dipN').value=90;modeChanged();$('pos').value=0;$('thick').value=20;GM.doms[1].col='#1971c2';if(!VIEW2D)toggle2D();(LYR.items=lyrDef()).forEach(function(it){if(it.k==='bx'||it.k==='bm')it.c.set(false);});$('sliceClip').checked=true;updatePlot();})()""")
            for nm, on in (("union", "true"), ("dua_kulit", "false")):
                pg.evaluate("GM.opt.imUni=%s;updatePlot()" % on); pg.wait_for_timeout(2500); pg.screenshot(path=str(Path(ARG["--shot"]) / ("sayatan_%s.png" % nm)))
            pg.evaluate("GM.opt.imUni=true")
        cek(not ERR, "tanpa galat halaman: %s" % ERR[:2])
        ctx.close()
finally:
    srv.terminate()
print("\nGAGAL (%d)" % len(salah) if salah else "\nLULUS")
sys.exit(1 if salah else 0)
