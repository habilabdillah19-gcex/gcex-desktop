# -*- coding: utf-8 -*-
"""Block Model 0.24.73: permukaan gabungan Topo × Pit, Batas permukaan blok, Buka atap, legenda (web-src/topopit_bm.js).

Permintaan pemilik 13 Nov 2026. Data SINTETIS (tanpa data nyata), koordinat lokal:
  topografi = bidang datar z = 100 (grid 5 m, X/Y 0-200);
  desain pit = pit bujur sangkar berpusat (100,100): dasar z = 61 (|dx|,|dy| <= 20), dinding 1:1 sampai z = 141 di tepi grid
  -> garis potong (daylight) di jarak Chebyshev 59 m (z = 100), di antara titik grid.
  block model = kubus 10 m, X/Y 0-200, Z 0-150, au = 1.
  T1 permukaan gabungan: Z mesh = min(topo, pit) dari TIN yang sama (selisih maks kecil), ada titik garis potong, dua nada
     (segitiga topo & segitiga pit), tercatat sebagai permukaan DTM (jenis surf) & muncul di daftar permukaan Reporting.
  T2 batas permukaan: 'pit' = jumlah blok Reporting "di dalam desain pit & di bawah topografi" (cara Surpac, titik pusat);
     'bawah' & 'pit' tidak bertumpang; contoh titik.
  T3 buka atap: segitiga permukaan gabungan DI ATAS blok tampil ('di bawah topo x pit') disembunyikan (tidak ada titik berat
     segitiga tersisa di atas atap blok); untuk blok 'di antara topo & pit' lantai pit di bawahnya TIDAK dibuka.
  T4 legenda: kartu #tpLeg berisi Block model / Permukaan (topografi & desain pit gabungan); legenda Plotly mati;
     tutup -> tombol "Legenda"; buka lagi.
  T5 ekspor DTM + STR: jumlah titik & segitiga sama dengan model.
  T6 tanpa pit: tombol gabung memberi pesan, tidak membuat model.
  T7 desain pit = permukaan DTM data latihan (Data Referensi): segitiga DTM dipakai apa adanya, Z = min(topo, DTM) tepat,
     tampilan DTM sumber dimatikan.
  T9 tampilan: titik string pit dirapatkan 2 m, garis jenjang pit tergambar & di legenda, awan titik topo tanpa garis,
     segitiga panjang di DALAM topografi tidak dibuang (tanpa lubang).
  T11 (BM 0.24.76) Reporting & Batas permukaan memakai pit string yang dirapatkan (= Topo x Pit, cocok DTM Surpac).
  T10 (0.24.75) node Data Spasial: Topo x Pit sesudah Desain pit + '+ Import topografi/desain pit'; panel properti #pTP;
     gabungan tidak lagi di Data Referensi; survei dari Reporting menjadi node Data Referensi bertanda survei, angka progres
     topo-ke-topo SAMA dengan cara lama (titik sementara), dan bisa dipilih sebagai sumber Topo x Pit.
  T8 langkah Demo 'Topografi terpotong desain pit' ada, menampilkan blok di dalam pit, lalu mengembalikan pilihan.
Pemakaian: python tools/uji/uji_topopit.py [app/index.html]   (build lama harus GAGAL)
"""
from __future__ import annotations
import random, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app" / "index.html"
PORT = random.randint(8800, 8899)

JS = r"""async function(){
  var R={};var ox=offX||0,oy=offY||0;
  var X=[],Y=[],Z=[];for(var a=0;a<20;a++)for(var b=0;b<20;b++)for(var c=0;c<15;c++){X.push(5+10*a+ox);Y.push(5+10*b+oy);Z.push(5+10*c);}
  var n=X.length,F=function(v){var r=new Float32Array(n);r.fill(v);return r;};
  BX.m={name:'uji_topopit',n:n,x:new Float64Array(X),y:new Float64Array(Y),z:new Float64Array(Z),sx:F(10),sy:F(10),sz:F(10),num:{au:F(1)},cat:{},sizes:'10',ext:[0,200,0,200,0,150],s0:10};
  BX.ver=(BX.ver||0)+1;BX.ui=bxDefUI(BX.m);BX.ui.fAttr='';BX.sc={};BX.scL=[];BX.mc=null;BX.mcL=[];
  var tx=[],ty=[],tz=[],px=[],py=[],pz=[];for(var x=0;x<=200;x+=5)for(var y=0;y<=200;y+=5){tx.push(x);ty.push(y);tz.push(100);var d=Math.max(Math.abs(x-100),Math.abs(y-100));px.push(x);py.push(y);pz.push(61+Math.max(0,d-20));}
  // T7 (sesudah T1..T5) memakai permukaan DTM data latihan sebagai pit; simpan dulu
  var MD0=MD.models.slice();
  // T6 dulu: tanpa pit (permukaan DTM disingkirkan sementara)
  MD.models=MD.models.filter(function(w){return w.jenis!=='surf';});OV.topoF={x:tx,y:ty,z:tz};OV.pitF={x:[],y:[],z:[]};TP.cfg={t:'',p:''};mdList();var m0=TP.gabung();R.t6={model:!!m0,msg:(document.getElementById('tpMsg')||{}).textContent||''};
  OV.pitF={x:px,y:py,z:pz};TP.cfg={t:'ov:topo',p:'ov:pit'};mdList();
  var m=TP.gabung();R.t1={ada:!!m,nv:m.nv,nt:m.nt,nC:m.gab.nC,jenis:m.jenis,nTopo:0,nPit:0};
  for(var q=0;q<m.nt;q++){if(m.fsrc[q])R.t1.nPit++;else R.t1.nTopo++;}
  var fT={f:TP.zf('ov:topo')},fP={f:TP.zf('ov:pit')},mx=0,cnt=0;
  // z mesh gabungan pada titik berat setiap segitiga vs min(topo,pit) TIN
  for(q=0;q<m.nt;q+=3){var A=m.t[3*q],B=m.t[3*q+1],C2=m.t[3*q+2],cx=(m.v[3*A]+m.v[3*B]+m.v[3*C2])/3-ox,cy=(m.v[3*A+1]+m.v[3*B+1]+m.v[3*C2+1])/3-oy,cz=(m.v[3*A+2]+m.v[3*B+2]+m.v[3*C2+2])/3;
    var t=fT.f(cx,cy),p=fP.f(cx,cy);if(t==null||p==null)continue;var e=Math.abs(cz-Math.min(t,p));if(e>mx)mx=e;cnt++;}
  R.t1.maxErr=mx;R.t1.nCek=cnt;
  R.t1.rp=MD.models.filter(function(w){return w.jenis==='surf';}).map(function(w){return w.name;});
  // T2
  bxSet('tpB','pit',true);var S1=bxSel({clip:false,K:[]}).idx.slice();bxSet('tpB','bawah',true);var S2=bxSel({clip:false,K:[]}).idx.slice();bxSet('tpB','',true);var S0=bxSel({clip:false,K:[]}).idx.length;
  var set1=new Set(S1),ov=S2.filter(function(i){return set1.has(i);}).length;
  var ix=function(x,y,z){return (Math.floor(x/10)*20+Math.floor(y/10))*15+Math.floor(z/10);};
  R.t2={pit:S1.length,bawah:S2.length,semua:S0,tumpang:ov,c1:set1.has(ix(105,105,95)),c2:new Set(S2).has(ix(105,105,55)),c3:new Set(S2).has(ix(5,5,95)),c4:set1.has(ix(5,5,95))};
  RP.o=null;var o=rpO();o.surf='pit';o.cuts='0';o.gr='au';o.atts=['au'];o.grp='none';o.sx=[];o.show=false;if(o.sgMode!==undefined){o.sgMode='c';o.sg=1;}else{BX.ui.sg=1;BX.ui.sgCol='';}
  rpRun();var G=RP.res.rows[0].G,nr=0;Object.keys(G).forEach(function(k){nr+=G[k].n;});R.t2.rpPit=nr;
  // T3 buka atap: blok 'bawah' (di bawah permukaan) -> atap dibuka; blok 'pit' (di atas lantai pit) -> lantai tidak dibuka
  bxSet('tpB','bawah',true);document.getElementById('bxShow').checked=true;document.getElementById('ovBuka').checked=true;document.getElementById('ovBukaM').value='0';
  updatePlot();await new Promise(function(r){setTimeout(r,1500);});
  var gd=document.getElementById('plotDiv'),tr=gd.data.filter(function(t){return t.name===TP.NAMA&&t.type==='mesh3d';})[0];
  R.t3={nt:m.nt,tampil:tr?tr.i.length:-1,diJejak:0};
  if(tr){var J=TP.jejak();for(q=0;q<tr.i.length;q++){var a1=tr.i[q],b1=tr.j[q],c1=tr.k[q],u=Math.floor(((tr.x[a1]+tr.x[b1]+tr.x[c1])/3-J.x0)/J.cs),w=Math.floor(((tr.y[a1]+tr.y[b1]+tr.y[c1])/3-J.y0)/J.cs);if(u>=0&&w>=0&&u<J.gx&&w<J.gy&&(tr.z[a1]+tr.z[b1]+tr.z[c1])/3>J.G[w*J.gx+u]-0.01)R.t3.diJejak++;}}
  bxSet('tpB','pit',true);updatePlot();await new Promise(function(r){setTimeout(r,1200);});var tr3=gd.data.filter(function(t){return t.name===TP.NAMA&&t.type==='mesh3d';})[0];R.t3.pitBuka=tr3?tr3.i.length:-1;
  // T3c: hanya blok kolom X<50 yang tampil (cut-off pada atribut uji) -> permukaan di X>=60 tidak boleh terbuka
  var au=BX.m.num.au;for(var i2=0;i2<BX.m.n;i2++)au[i2]=(BX.m.x[i2]-ox)<50?1:0;BX.ui.fAttr='au';BX.ui.fOp='ge';BX.ui.fVal='0.5';bxSet('tpB','bawah',true);updatePlot();await new Promise(function(r){setTimeout(r,1200);});
  var tr4=gd.data.filter(function(t){return t.name===TP.NAMA&&t.type==='mesh3d';})[0],hilangJauh=0,ada=new Set();if(tr4)for(q=0;q<tr4.i.length;q++)ada.add(tr4.i[q]+'_'+tr4.j[q]+'_'+tr4.k[q]);
  for(q=0;q<m.nt;q++){var A3=m.t[3*q],B3=m.t[3*q+1],C3=m.t[3*q+2],cx3=(m.v[3*A3]+m.v[3*B3]+m.v[3*C3])/3-ox;if(cx3>=60&&!ada.has(A3+'_'+B3+'_'+C3))hilangJauh++;}
  R.t3.hilangJauh=hilangJauh;R.t3.sebagian=tr4?tr4.i.length:-1;BX.ui.fAttr='';for(i2=0;i2<BX.m.n;i2++)au[i2]=1;bxSet('tpB','pit',true);
  // T4 legenda
  var L=document.getElementById('tpLeg');R.t4={ada:!!L,teks:L?L.innerText:'',plotlyLeg:gd.layout.showlegend};
  TP.legSet('on',false);await new Promise(function(r){setTimeout(r,800);});R.t4.tutup=document.getElementById('tpLeg').innerText;TP.legSet('on',true);await new Promise(function(r){setTimeout(r,800);});R.t4.buka=document.getElementById('tpLeg').innerText.indexOf('Permukaan')>=0;
  document.getElementById('ovBuka').checked=false;updatePlot();await new Promise(function(r){setTimeout(r,1000);});
  var tr2=gd.data.filter(function(t){return t.name===TP.NAMA&&t.type==='mesh3d';})[0];R.t3.tanpaBuka=tr2?tr2.i.length:-1;R.t3.duaNada=!!(tr2&&tr2.facecolor&&new Set(tr2.facecolor).size>2);
  // T5 ekspor
  var F2=[];window.gxSimpan=function(t,nm){F2.push([nm,t]);return Promise.resolve(true);};await TP.ekspor();
  R.t5=F2.map(function(f){var L2=f[1].split(/\r?\n/);return [f[0],L2.filter(function(l){return /^1, /.test(l);}).length,L2.filter(function(l){return /^[1-9]\d*, \d+, \d+, \d+, 0, 0, 0,/.test(l);}).length];});
  // T7: desain pit dari permukaan DTM (segitiga DTM dipakai apa adanya) + topografi data latihan asli
  var gm=TP.model();MD.models=MD0.filter(function(w){return !w.gab;});MD.models.push(gm);MD.models.forEach(function(w){if(w.jenis==='surf'&&!w.gab)w.vis=true;});
  var pk=TP.daftar().map(function(x){return x[0];}).filter(function(k){return /^md:.*pit/i.test(k);})[0];R.t7={pk:pk};
  if(pk){var tz2=[],tx2=[],ty2=[];var sp=MD0.filter(function(w){return 'md:'+w.name===pk;})[0];mdLocal(sp);var bx=[1e18,-1e18,1e18,-1e18];for(q=0;q<sp.nv;q++){bx[0]=Math.min(bx[0],sp._x[q]);bx[1]=Math.max(bx[1],sp._x[q]);bx[2]=Math.min(bx[2],sp._y[q]);bx[3]=Math.max(bx[3],sp._y[q]);}
    var zmax=-1e9;for(q=0;q<sp.nv;q++)zmax=Math.max(zmax,sp._z[q]);
    for(var xx=bx[0]-50;xx<=bx[1]+50;xx+=10)for(var yy=bx[2]-50;yy<=bx[3]+50;yy+=10){tx2.push(xx);ty2.push(yy);tz2.push(zmax-5);}
    OV.topoF={x:tx2,y:ty2,z:tz2};TP.cfg={t:'ov:topo',p:pk};var m7=TP.gabung();var f1=TP.zf('ov:topo'),f2=TP.zf(pk),e7=0,n7=0,ns=[0,0];
    for(q=0;q<m7.nt;q++){ns[m7.fsrc[q]]++;if(q%5)continue;var A7=m7.t[3*q],B7=m7.t[3*q+1],C7=m7.t[3*q+2],x7=(m7.v[3*A7]+m7.v[3*B7]+m7.v[3*C7])/3-ox,y7=(m7.v[3*A7+1]+m7.v[3*B7+1]+m7.v[3*C7+1])/3-oy,z7=(m7.v[3*A7+2]+m7.v[3*B7+2]+m7.v[3*C7+2])/3,a7=f1(x7,y7),b7=f2(x7,y7);if(a7==null||b7==null)continue;n7++;e7=Math.max(e7,Math.abs(z7-Math.min(a7,b7)));}
    R.t7.nt=m7.nt;R.t7.src=m7.gab.src;R.t7.ns=ns;R.t7.err=e7;R.t7.n=n7;R.t7.pitVis=sp.vis;}
  // T8 langkah Demo (BX uji sintetis berada di luar pit latihan -> jumlah blok boleh 0; yang diuji alur & pemulihan)
  bxSet('tpB','',true);  var DS=(typeof dmSteps==='function'?dmSteps():[]),st=DS.filter(function(x){return x.t==='Topografi terpotong desain pit';})[0];R.t8={ada:!!st,n:-1,urut:DS.map(function(x){return x.s;}).slice(-3)};
  if(st){var Q=[];st.run(function(t,fn){Q.push([t,fn]);});Q.sort(function(a,b){return a[0]-b[0];});for(var z8=0;z8<Q.length-1;z8++)Q[z8][1]();R.t8.n=bxSel({clip:false,K:[]}).idx.length;R.t8.tpB=BX.ui.tpB;Q[Q.length-1][1]();R.t8.balik=BX.ui.tpB;}
  // T9 tampilan (13 Nov, revisi bentuk): pit berupa STRING (cincin jenjang, dipisah null) -> titik dirapatkan 2 m, garis jenjang
  // tergambar; topografi awan titik berlubang di tengah -> segitiga dalam tidak dibuang (tanpa lubang), tanpa garis kontur.
  var gx=[],gy=[],gz=[];for(var x9=0;x9<=200;x9+=5)for(var y9=0;y9<=200;y9+=5){if(x9>85&&x9<115&&y9>85&&y9<115)continue;gx.push(x9);gy.push(y9);gz.push(100);}
  var sx=[],sy=[],sz=[];[20,30,40,50,60].forEach(function(dd){var zz=61+Math.max(0,dd-20);[[100-dd,100-dd],[100+dd,100-dd],[100+dd,100+dd],[100-dd,100+dd],[100-dd,100-dd]].forEach(function(p){sx.push(p[0]);sy.push(p[1]);sz.push(zz);});sx.push(null);sy.push(null);sz.push(null);});
  OV.topoF={x:gx,y:gy,z:gz};OV.pitF={x:sx,y:sy,z:sz};TP.cfg={t:'ov:topo',p:'ov:pit'};MD.models=MD.models.filter(function(w){return !w.gab;});
  var tt9=TIN.build(OV.topoF),lubang=true;for(q=0;q<tt9.i.length;q++){var a9=tt9.i[q],b9=tt9.j[q],c9=tt9.k[q],xa=tt9.x[a9],ya=tt9.y[a9],xb=tt9.x[b9],yb=tt9.y[b9],xc=tt9.x[c9],yc=tt9.y[c9],pxx=100,pyy=100;
    var d1=(pxx-xb)*(ya-yb)-(xa-xb)*(pyy-yb),d2=(pxx-xc)*(yb-yc)-(xb-xc)*(pyy-yc),d3=(pxx-xa)*(yc-ya)-(xc-xa)*(pyy-ya);if(!((d1<0||d2<0||d3<0)&&(d1>0||d2>0||d3>0))){lubang=false;break;}}
  var rp=TIN.rapat(OV.pitF,2),nr=rp.x.filter(function(v){return v!==null;}).length;
  var m9=TP.gabung();document.getElementById('ovBuka').checked=false;updatePlot();await new Promise(function(r){setTimeout(r,1200);});
  var gl=gd.data.filter(function(t){return /Garis jenjang pit|Kontur topografi/.test(t.name);}).map(function(t){return [t.name,t.x.filter(function(v){return v!==null;}).length];});
  R.t9={lubang:lubang,titikPit:sx.filter(function(v){return v!==null;}).length,titikRapat:nr,garis:gl,leg:(document.getElementById('tpLeg')||{}).innerText||''};
  // T11 (13 Nov, audit DTM Surpac pit_z3south_r4): Reporting (rpSurf) & Batas permukaan (TP.zf) memakai pit string yang
  // DIRAPATKAN 2 m, sama dengan Topo x Pit; triangulasi titik string asli menyeberangi jenjang (beda > 0,5 m).
  var fR=RP.api.surf(OV.pitF),zR=TINZ.of(TIN.rapat(OV.pitF,2),true),zA=TINZ.of(OV.pitF),tb=TP.zf('ov:pit'),s11=0,b11=0,n11=0;
  for(var x11=41;x11<=159;x11+=1.7)for(var y11=41;y11<=159;y11+=1.3){var v1=fR(x11,y11),v2=zR.f(x11,y11),v3=zA.f(x11,y11),v4=tb?tb(x11,y11):null;if(v1==null||v2==null)continue;n11++;
    if(Math.abs(v1-v2)<1e-9&&v4!=null&&Math.abs(v4-v2)<1e-9)s11++;if(v3!=null&&Math.abs(v3-v2)>0.5)b11++;}
  R.t11={n:n11,sama:s11,bedaAsli:b11,tengah:fR(100,100)};
  // T10 (0.24.75) node Data Spasial + import Reporting -> Data Referensi
  try{PT.render(true);}catch(e){}await new Promise(function(r){setTimeout(r,600);});
  var ids=[].map.call(document.querySelectorAll('#ptree .ptr'),function(r){return r.dataset.id;});
  try{PT.select('sp');}catch(e){}try{PT.render(true);}catch(e){}await new Promise(function(r){setTimeout(r,400);});
  ids=[].map.call(document.querySelectorAll('#ptree .ptr'),function(r){return r.dataset.id;});
  try{PT.select('sp.tp');}catch(e){}await new Promise(function(r){setTimeout(r,500);});
  R.t10={ids:ids.filter(function(i){return /^sp\./.test(i);}),refGab:ids.some(function(i){return /^ref\.models\..*gabungan/.test(i);}),pTP:!document.getElementById('pTP').hidden,pOv:document.getElementById('pOverlay').hidden,box:(document.getElementById('tpBox')||{}).innerText||''};
  var qx=[],qy=[],qz=[];for(var xa2=0;xa2<=200;xa2+=5)for(var ya2=0;ya2<=200;ya2+=5){qx.push(xa2);qy.push(ya2);qz.push(xa2<100?80:100);}
  var q1={x:qx.slice(),y:qy.slice(),z:qz.slice()};RPX.mode='tt';RPX.ta='ov:topo';RPX.surf.push(q1);RPX.tb='pt:'+(RPX.surf.length-1);RPX.run();
  var tot=function(){var G=RPX.res.rows[0].res.rows[0].G,n=0,t=0;Object.keys(G).forEach(function(k){n+=G[k].n;t+=G[k].t;});return [n,Math.round(t)];};var lama=RPX.res?tot():null;
  var kid=RPX.keRef('survei_juni.str',{x:qx.slice(),y:qy.slice(),z:qz.slice()});RPX.tb=kid;RPX.run();var baru=RPX.res?tot():null;
  try{PT.render(true);}catch(e){}var mw=MD.models[+kid.slice(3)];
  R.t10.prog={lama:lama,baru:baru,kid:kid,survei:!!(mw&&mw.survei),nt:mw?mw.nt:0,diTopoPit:TP.daftar().some(function(x){return x[0]==='md:survei_juni.str';}),msg:RPX.msg};
  return R;}"""


def main() -> int:
    from playwright.sync_api import sync_playwright
    d = Path(tempfile.mkdtemp(prefix="topopit_")); shutil.copy(HTML, d / "index.html")
    (d / "data-latihan").symlink_to(ROOT / "docs" / "tutorial-gcex" / "data")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2); galat = []
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 1500, "height": 900}); pg.on("dialog", lambda x: x.accept())
            pg.on("pageerror", lambda e: galat.append("galat halaman: %s" % str(e)[:200]))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT)
            pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
            pg.evaluate("document.getElementById('dlatBtn').click()")
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0 && typeof rpRun==='function'", timeout=600000)
            pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(1500)
            if not pg.evaluate("!!window.TP"):
                print("GAGAL: modul TP (topopit_bm.js) tidak ada"); return 1
            r = pg.evaluate(JS)
            if len(sys.argv) > 2: pg.screenshot(path=sys.argv[2])
            b.close()
    finally:
        srv.terminate(); shutil.rmtree(d, ignore_errors=True)
    t1, t2, t3, t4 = r["t1"], r["t2"], r["t3"], r["t4"]
    print("T1", t1); print("T2", t2); print("T3", t3); print("T4", {k: (v[:160] if isinstance(v, str) else v) for k, v in t4.items()}); print("T5", r["t5"]); print("T6", r["t6"]); print("T7", r["t7"]); print("T8", r["t8"]); print("T9", r["t9"]); print("T10", r["t10"])
    cek = lambda ok, p: ok or galat.append(p)
    cek(r["t6"]["model"] is False and "desain pit" in r["t6"]["msg"], "T6 tanpa pit seharusnya menolak dengan pesan")
    cek(t1["ada"] and t1["jenis"] == "surf" and t1["nC"] > 20 and t1["nTopo"] > 0 and t1["nPit"] > 0, "T1 permukaan gabungan / garis potong / dua sumber")
    cek(t1["nCek"] > 100 and t1["maxErr"] < 0.6, "T1 Z permukaan gabungan menyimpang dari min(topo, pit): %.3f m" % t1["maxErr"])
    cek(any("Topo" in x and "Pit" in x for x in t1["rp"]), "T1 permukaan gabungan tidak ada di daftar permukaan Reporting")
    cek(t2["pit"] > 0 and t2["pit"] == t2["rpPit"], "T2 'di antara topo & pit' (%d) != Reporting di dalam pit (%d)" % (t2["pit"], t2["rpPit"]))
    cek(t2["tumpang"] == 0 and t2["bawah"] > 0 and t2["semua"] == 6000, "T2 bawah/pit bertumpang atau jumlah salah")
    cek(t2["c1"] and t2["c2"] and t2["c3"] and not t2["c4"], "T2 contoh titik salah")
    cek(0 < t3["tampil"] < t3["nt"] and t3["diJejak"] == 0 and t3["tanpaBuka"] == t3["nt"], "T3 buka atap")
    cek(t3["hilangJauh"] == 0 and 0 < t3["sebagian"] < t3["nt"], "T3 buka atap membuka permukaan jauh dari blok tampil (%s segitiga)" % t3["hilangJauh"])
    cek(t3["pitBuka"] == t3["nt"], "T3 lantai pit di bawah blok 'di antara topo & pit' ikut dibuka (%s dari %s)" % (t3["pitBuka"], t3["nt"]))
    cek(t3["duaNada"], "T3 permukaan gabungan tidak berwarna dua nada")
    cek(t4["ada"] and "Block model" in t4["teks"] and "Permukaan" in t4["teks"] and "gabungan" in t4["teks"] and t4["plotlyLeg"] is False, "T4 legenda")
    cek("Legenda" in t4["tutup"] and t4["buka"], "T4 tutup / buka legenda")
    cek(len(r["t5"]) == 2 and r["t5"][0][1] == t1["nv"] and r["t5"][1][2] == t1["nt"], "T5 ekspor DTM + STR")
    t7 = r["t7"]
    cek(t7.get("pk") and t7["ns"][0] > 0 and t7["ns"][1] > 0 and t7["n"] > 50 and t7["err"] < 0.01 and t7["pitVis"] is False, "T7 pit dari permukaan DTM")
    cek(r["t8"]["ada"] and r["t8"]["n"] >= 0 and r["t8"]["tpB"] == "pit" and r["t8"]["balik"] == "", "T8 langkah Demo")
    t9 = r["t9"]
    cek(not t9["lubang"] and t9["titikRapat"] > 5 * t9["titikPit"] and len(t9["garis"]) == 1 and t9["garis"][0][0] == "Garis jenjang pit" and t9["garis"][0][1] > 100 and "Garis jenjang pit" in t9["leg"], "T9 tampilan: lubang topo / perapatan pit / garis jenjang")
    t10 = r["t10"]; ids = t10["ids"]
    cek("sp.tp" in ids and "sp.+topo" in ids and "sp.+pit" in ids and ids.index("sp.tp") == ids.index("sp.pit") + 1 and not t10["refGab"], "T10 node Data Spasial (Topo x Pit sesudah Desain pit, baris import) / gabungan keluar dari Data Referensi")
    cek(t10["pTP"] and t10["pOv"] and "topografi" in t10["box"].lower(), "T10 panel properti node Topo x Pit")
    pg_ = t10["prog"]
    cek(pg_["lama"] and pg_["lama"][0] > 0 and pg_["lama"] == pg_["baru"] and pg_["survei"] and pg_["nt"] > 0 and pg_["diTopoPit"], "T10 import survei Reporting -> Data Referensi: angka progres sama, tersimpan sebagai node survei, bisa dipilih Topo x Pit")
    t11 = r["t11"]; print("T11", t11)
    cek(t11["n"] > 1000 and t11["sama"] == t11["n"] and t11["bedaAsli"] > 0 and t11["tengah"] is not None and abs(t11["tengah"] - 61) < 1e-6, "T11 Reporting & Batas permukaan = pit dirapatkan (titik asli berbeda > 0,5 m di %s titik); dasar pit lebar tetap ada (hanya tepi luar dikupas)" % t11["bedaAsli"])
    print()
    if galat:
        print("GAGAL (%d):" % len(galat)); [print("  -", g) for g in galat]; return 1
    print("LULUS"); return 0


if __name__ == "__main__":
    sys.exit(main())
