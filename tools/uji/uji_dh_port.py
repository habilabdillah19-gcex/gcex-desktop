"""Uji Drillhole 0.24.98 — fitur Block Model yang dipindahkan ke Drillhole (data latihan DH + .mdl sintetis).
  P1 tampilan ala Ore Works: bilah alat (#bmTb, Semua data, Latar 3D), status bar E/N/RL & VE, cari Project Tree,
     panel Properti tempel kiri / kanan / lepas, kompas 3D (cpDraw).
  P2 import .mdl dengan "Hanya di dalam desain pit" + "Hanya di bawah topografi asbuilt": hasil = aturan Block Model yang
     diterapkan pada seluruh blok (permukaan dari SA.surfGrid, titik tengah blok).
  P3 blok yang lolos filter > batas memori -> bagian teratas yang muat dimuat + pesan rentang berikutnya.
  P4 Ringkasan seluruh model per RL: node Project Tree; dengan batas pit / topografi dihitung sambil membaca SELURUH file
     = hitungan langsung dari semua blok; tanpa batas = hitungan dari blok yang dimuat.
  P5 tampilan 3D 17,5 juta blok: LOD jadi (dulu "Map maximum size exceeded" -> kosong).
  P6 dialog Block model besar: pilihan desain pit / topografi + kotak folder cache.
  P7 Topo × Pit (gabungan) di Drillhole: node Data Spasial, permukaan gabungan dibuat & tampil, kartu legenda.
  P8 kamera 3D digerakkan 4x tanpa orthofoto: tidak ada gambar ulang penuh (DH 0.24.97: 4x -> jeda pada model besar).
Pemakaian: python tools/uji/uji_dh_port.py [app-dh/index.html]   (build DH 0.24.97 harus GAGAL)
"""
from __future__ import annotations
import json, random, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app-dh" / "index.html"
PORT = random.randint(8900, 8990)
sys.path.insert(0, str(ROOT / "backend" / "tests"))

JS = r"""async function(){var R={},w=function(t){return new Promise(function(r){setTimeout(r,t);});},$=function(i){return document.getElementById(i);};
  if(!window.SHELL||typeof cpDraw!=='function'||!SA.surfGrid||!window.bsStream)return {lama:1};
  /* P1 */
  var tb=$('bmTb'),ph=$('ptPH');R.p1={tb:!!tb,all:!!$('tbAll'),bg:!!$('tbBg'),xy:!!$('sbXY'),ve:!!$('sbVE'),cari:!!$('ptCari'),pdk:ph?ph.querySelectorAll('.pdk button[data-p]').length:0,ell:!!$('cpEll')};
  SHELL.dock('kanan');await w(300);R.p1.kanan=!!($('propR')&&$('propR').contains($('side')));SHELL.dock('lepas');await w(300);R.p1.lepas=!!($('propF')&&$('propF').contains($('side')));SHELL.dock('kiri');await w(300);R.p1.kiri=$('ptCol').contains($('side'));
  /* data uji: .mdl sintetis di koordinat proyek DH */
  var f=document.getElementById('__f').files[0],H=await SA.mdlHead(f),O=H.O,ox=offX,oy=offY,cx0=O[0]+40,cy0=O[1]+40;
  var pF0=OV.pitF,tF0=OV.topoF,ring=function(r,z){var X=[],Y=[],Z=[];for(var a=0;a<=48;a++){X.push(cx0+r*Math.cos(a/48*6.2832)-ox);Y.push(cy0+r*Math.sin(a/48*6.2832)-oy);Z.push(z);}return [X,Y,Z];};
  var pit={x:[],y:[],z:[]};[[30,O[2]+45],[15,O[2]+15]].forEach(function(q){var r=ring(q[0],q[1]);pit.x=pit.x.concat(r[0],[null]);pit.y=pit.y.concat(r[1],[null]);pit.z=pit.z.concat(r[2],[null]);});
  var tp={x:[],y:[],z:[]};for(var gx=-1;gx<=1;gx++){for(var gy=-1;gy<=1;gy++){tp.x.push(cx0+gx*60-ox);tp.y.push(cy0+gy*60-oy);tp.z.push(O[2]+62+gx*8);}tp.x.push(null);tp.y.push(null);tp.z.push(null);}
  OV.pitF=pit;OV.topoF=tp;
  /* P2 */
  var A=await SA.readMDL(f,null,{f32:false}),B=await SA.readMDL(f,null,{f32:false,pit:true,topo:true});
  var Lp=SA.mdlLines(null,'pit'),Lt=SA.mdlLines(null,'topo'),PG=SA.surfGrid(Lp,'crest'),TG=SA.surfGrid(Lt,'hull'),eN=0,nOut=0;
  for(var i=0;i<A.n;i++){var hz=A.sz[i]/2,zp=SA.surfAt(PG,A.x[i],A.y[i]);if(!(zp<A.z[i]+hz))continue;var zt=SA.surfAt(TG,A.x[i],A.y[i]);if(zt===zt&&!(A.z[i]-hz<zt))continue;eN++;}
  R.p2={all:A.n,n:B.n,exp:eN,note:(B.mdl.notes||[]).join(' ').slice(0,160),flt:!!(B.mdl.filt&&B.mdl.filt.st.pit&&B.mdl.filt.st.topo)};
  /* P3 */
  var M0=SA.mdlMaxMem;SA.mdlMaxMem=function(){return Math.max(1,Math.floor(B.n/3));};var C=await SA.readMDL(f,null,{f32:false,pit:true,topo:true});SA.mdlMaxMem=M0;
  var m3=/RL ([0-9.\-]+) /.exec(C.warn||''),cut=m3?+m3[1]:NaN,nB=0;for(i=0;i<B.n;i++)if(B.z[i]+B.sz[i]/2>cut)nB++;
  R.p3={n:C.n,cap:Math.floor(B.n/3),cut:cut,exp:nB,warn:(C.warn||'').slice(0,200)};
  /* P4 */
  var tree=[].some.call(document.querySelectorAll('#ptree .ptr'),function(r){return r.getAttribute('data-id')==='bm.rl';});
  var m0=BX.m,u0=BX.ui,TP0=window.TP,fl0=SA.mdlFileLast;BX.m=A;BX.ui=bxDefUI(A);BX.ui.sgCol='';BX.ui.sg=2.6;BX.ver++;SA.mdlFileLast=f;
  var zP=function(x,y){return x+offX>O[0]+70?null:O[2]+20+0.2*(y+offY-O[1]);},zT=function(x,y){return O[2]+70+0.1*(x+offX-O[0]);};window.TP={zf:function(k){return k==='ov:pit'?zP:zT;}};
  var S={bench:10,ref:O[2],cut:'',cutA:'au'};
  try{var L0=bsLocal(S,['au']),S0=await bsStream(S,['au'],{pit:false,topo:false}),S1=await bsStream(S,['au'],{pit:true,topo:true});
    var eT=0,eG=0,eW=0,eK=0;for(i=0;i<A.n;i++){var x=A.x[i]-offX,y=A.y[i]-offY,z=A.z[i],zp2=zP(x,y);if(zp2==null||!(z>=zp2)||!(z<=zT(x,y)))continue;var t=A.sx[i]*A.sy[i]*A.sz[i]*2.6,au=A.num.au[i];eK++;eT+=t;if(isFinite(au)&&au>-1e20){eG+=au*t;eW+=t;}}
    R.p4={tree:tree,same0:L0.total.n===S0.total.n&&Math.abs(L0.total.ton-S0.total.ton)<1e-6,n:[S1.total.n,eK],ton:[S1.total.ton,eT],au:[S1.total.grade.au,eW?eG/eW:null],con:S1.con};}
  catch(e){R.p4={err:String(e&&e.stack||e).slice(0,400),tree:tree};}
  window.TP=TP0;SA.mdlFileLast=fl0;
  /* P5 */
  try{var e=A.ext,s=0.5,nx=260,ny=260,nz=259,n=nx*ny*nz,X=new Float64Array(n),Y=new Float64Array(n),Z=new Float64Array(n),SX=new Float32Array(n).fill(s),AU=new Float32Array(n),q=0;
    for(var k=0;k<nz;k++)for(var j=0;j<ny;j++)for(i=0;i<nx;i++){X[q]=e[0]+(i+0.5)*s;Y[q]=e[2]+(j+0.5)*s;Z[q]=e[4]+(k+0.5)*s;AU[q]=k/nz*4;q++;}
    BX.m={name:'besar',n:n,x:X,y:Y,z:Z,sx:SX,sy:SX,sz:SX,num:{au:AU},cat:{},s0:s,ext:[e[0],e[0]+nx*s,e[2],e[2]+ny*s,e[4],e[4]+nz*s],sizes:'0.5',mdl:null};
    BX.ui=bxDefUI(BX.m);BX.ver++;BX.sc={};if($('bxShow'))$('bxShow').checked=true;var T=[],t7=performance.now();bxTraces(T,{clip:false});
    R.p5={n:n,nT:T.length,shown:BX.lim3d&&BX.lim3d.shown,lim:BX.lim3d&&BX.lim3d.lim,tot:BX.lim3d&&BX.lim3d.tot,ms:Math.round(performance.now()-t7)};X=Y=Z=SX=AU=null;}catch(e7){R.p5={err:String(e7)};}
  BX.m=m0;BX.ui=u0;BX.ver++;BX.sc={};BX.lim3d=null;
  /* P6 */
  var D0=window.gcexDesktop;window.gcexDesktop={api:async function(u){if(u==='/mdl/cache')return {root:'D:/GC-Ex_cache_mdl',used:0,free:5e11,items:[],custom:true};throw new Error('stub');}};
  var pr=SA.mdlAsk(f,H);await w(400);var d=$('mdlDlg');R.p6={pit:!!$('mdPit')&&!$('mdPit').disabled,topo:!!$('mdTopo')&&!$('mdTopo').disabled,cache:!!(d&&d.querySelector('#mdlCache')),cacheTxt:(d&&d.querySelector('#mdlCache')||{}).textContent||''};
  $('mdPit').checked=true;$('mdPit').dispatchEvent(new Event('change'));R.p6.mem=$('mdMem').textContent.slice(0,90);$('mdNo').click();await pr;window.gcexDesktop=D0;
  OV.pitF=pF0;OV.topoF=tF0;
  /* P7: Topo × Pit di Drillhole (data latihan: topografi & desain pit Data Spasial) */
  try{var r7=TP.gabung();if(r7&&r7.then)await r7;await w(2500);var tm=TP.model();updatePlot();await w(1500);var gd=$('plotDiv');
    R.p7={node:!!document.querySelector('#ptree [data-id="sp.tp"]'),nt:tm&&tm.nt,tr:/Topografi\s*\(gabungan\)/.test((document.querySelector('#tpLeg,.tplg')||document.body).textContent),leg:!!document.querySelector('.tplg-h'),bor:[].some.call(document.querySelectorAll('.tplg-h'),function(h){return /^Data bor/.test(h.textContent);}),
};}
  catch(e){R.p7={err:String(e&&e.stack||e).slice(0,400)};}
  /* P8: kamera digerakkan -> tanpa gambar ulang penuh bila orthofoto tidak tampil (hires.js + HR_perlu) */
  try{await new Promise(function(r){setTimeout(r,4000);});var gd8=document.getElementById('plotDiv'),n8=0,u8=window.updatePlot;window.updatePlot=function(){n8++;return u8.apply(this,arguments);};
    for(var k8=1;k8<=4;k8++){await Plotly.relayout(gd8,{'scene.camera':{eye:{x:0.3*k8,y:-0.35*k8,z:0.25*k8},center:{x:0.05,y:0,z:0},up:{x:0,y:0,z:1}}});await new Promise(function(r){setTimeout(r,800);});}
    window.updatePlot=u8;R.p8={n:n8,hp:typeof window.HR_perlu==='function'};}
  catch(e){R.p8={err:String(e&&e.stack||e).slice(0,400)};}
  return R;}"""


def main() -> int:
    from playwright.sync_api import sync_playwright
    from test_mdl_io import make_mdl
    d = Path(tempfile.mkdtemp()); shutil.copy(HTML, d / "index.html"); (d / "data-latihan").symlink_to(ROOT / "docs" / "tutorial-gcex" / "data")
    make_mdl(d / "uji.mdl", n=3000)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2); gagal = []; err = []
    def cek(ok, msg):
        print(("  ok   " if ok else "  GAGAL ") + msg)
        if not ok: gagal.append(msg)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 1500, "height": 950}); pg.on("dialog", lambda x: x.accept()); pg.on("pageerror", lambda e: err.append(str(e)))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT)
            pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000); pg.wait_for_timeout(6000)
            pg.evaluate("var i=document.createElement('input');i.type='file';i.id='__f';document.body.appendChild(i)")
            pg.set_input_files("#__f", str(d / "uji.mdl"))
            r = pg.evaluate("(%s)()" % JS)
            if len(sys.argv) > 2: pg.screenshot(path=sys.argv[2])
            b.close()
    finally:
        srv.terminate()
    if r.get("lama"):
        print("GAGAL: build lama (shell / cpDraw / surfGrid / Ringkasan per RL tidak ada)"); return 1
    print(json.dumps(r, ensure_ascii=False)[:1600])
    p1 = r["p1"]
    cek(all(p1[k] for k in ("tb", "all", "bg", "xy", "ve", "cari", "ell", "kanan", "lepas", "kiri")) and p1["pdk"] >= 3, "P1 bilah alat, status bar, cari Project Tree, dock Properti, kompas 3D %s" % p1)
    p2 = r["p2"]
    cek(0 < p2["n"] < p2["all"] and p2["n"] == p2["exp"] and p2["flt"] and "desain pit" in p2["note"], "P2 filter pit + topografi sambil membaca: %s dari %s blok (harap %s)" % (p2["n"], p2["all"], p2["exp"]))
    p3 = r["p3"]
    cek(0 < p3["n"] == p3["exp"] and "Rentang berikutnya" in p3["warn"], "P3 lebih dari batas memori -> bagian teratas: %s blok, RL > %s; pesan: %s" % (p3["n"], p3["cut"], p3["warn"][:120]))
    p4 = r["p4"]
    cek("err" not in p4 and p4["tree"] and p4["same0"], "P4 node Ringkasan per RL ada; tanpa batas = blok dimuat %s" % p4.get("err", ""))
    cek("err" not in p4 and p4["n"][0] == p4["n"][1] and abs(p4["ton"][0] - p4["ton"][1]) < 1e-6 and (p4["au"][1] is None or abs(p4["au"][0] - p4["au"][1]) < 1e-9) and "cara Surpac" in p4["con"],
        "P4 dengan batas pit + topografi atas seluruh file: blok %s, ton %s, kadar %s" % (p4.get("n"), p4.get("ton"), p4.get("au")))
    p5 = r["p5"]
    cek("err" not in p5 and p5["nT"] >= 1 and 0 < p5["shown"] <= p5["lim"] and p5["tot"] > 16800000, "P5 %s blok terpilih -> LOD %s sel (batas %s), %s ms %s" % (p5.get("tot"), p5.get("shown"), p5.get("lim"), p5.get("ms"), p5.get("err", "")))
    p6 = r["p6"]
    cek(p6["pit"] and p6["topo"] and p6["cache"] and "D:/GC-Ex_cache_mdl" in p6["cacheTxt"] and "batas memori" in p6["mem"], "P6 dialog Block model besar: pilihan pit / topografi + folder cache %s" % p6)
    p8 = r["p8"]
    cek("err" not in p8 and p8["hp"] and p8["n"] == 0, "P8 kamera 3D digerakkan 4x tanpa orthofoto: gambar ulang penuh %s kali (harap 0) %s" % (p8.get("n"), p8.get("err", "")))
    p7 = r["p7"]
    cek("err" not in p7 and p7["node"] and p7["nt"] > 0 and p7["tr"] and p7["leg"] and p7["bor"], "P7 Topo × Pit: node, permukaan gabungan %s segitiga, tampil di 3D, kartu legenda (bagian Data bor) %s" % (p7.get("nt"), p7.get("err", "")))
    cek(not err, "tanpa error halaman %s" % err[:3])
    print("GAGAL (%d)" % len(gagal) if gagal else "LULUS")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
