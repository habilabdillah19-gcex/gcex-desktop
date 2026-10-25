# -*- coding: utf-8 -*-
"""GC-Ex Drillhole — Geological Modelling v2 (0.9.0):
  1. Orientasi bervariasi (structural trend): pitch elipsoid RBF di bidang vein diinterpolasi dari lineasi struktur
     (plunge / trend), bukan satu pitch global. Kernel TPS memakai rotasi rata-rata (sudut aksial) tiap pasangan titik.
  2. Pinch-out di bor tanpa vein: lubang yang menembus bidang tengah vein (di interval yang ter-log / ter-assay) tanpa
     interval domain -> ketebalan menipis ke nol di titik tembus (radius dibatasi agar tidak mengenai kontak bor terdekat).
  3. OK dengan orientasi elipsoid dinamis: sumbu variogram & pencarian diputar per blok mengikuti bidang lokal HW/FW
     (dan pitch lokal bila tren aktif) -> kriging mengikuti undulasi / perubahan strike-dip vein.
Dipanggil dari build_dh.py: s = gm2_patch.patch(s)."""


def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, 'gm2_patch: pola ditemukan %d kali (harus %d): %s' % (c, n, a[:90])
    return s.replace(a, b)


HELPERS = r"""
/* ================= GM v2: tren orientasi, pinch-out bor kosong (dipakai imBuild) ================= */
/* tren pitch dari lineasi struktur -> fungsi (s,d) -> [cos 2θ, sin 2θ] (sudut aksial, satuan rad di bidang vein) */
function imTrend(d,P,Fr,X){if(P.vo==='off'||!window.STR||!STR.P||!STR.P.length)return null;var aS=+P.aS||1,aD=+P.aD||1;if(Math.abs(aS-aD)<1e-9)return null;
  var SL=[];try{SL=stForDom(d,Object.assign({},P,{str:true}),X);}catch(e){return null;}var L=[],rad=Math.PI/180,dot=function(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];};
  SL.forEach(function(o){var p=stGet(o.id);if(!p||p.pl==null||p.tr==null||!isFinite(+p.pl)||!isFinite(+p.tr))return;var pl=(+p.pl)*rad,tr=(+p.tr)*rad,l=[Math.cos(pl)*Math.sin(tr),Math.cos(pl)*Math.cos(tr),-Math.sin(pl)],ls=dot(l,Fr.u),ld=dot(l,Fr.v);
    if(Math.hypot(ls,ld)<0.3)return;var th=Math.atan2(ld,ls),q=imLoc(Fr,o.c.concat([0]));L.push({s:q[0],d:q[1],c2:Math.cos(2*th),s2:Math.sin(2*th),th:th*180/Math.PI,id:p.no});});
  if(!L.length)return null;var th0=(+P.pitch||0)*rad,R=Math.max(1,+P.voR||40),w0=0.05,C0=Math.cos(2*th0),S0=Math.sin(2*th0);
  var fn=function(s,dd){var C=w0*C0,S=w0*S0;for(var i=0;i<L.length;i++){var q=L[i],e2=((s-q.s)*(s-q.s)+(dd-q.d)*(dd-q.d))/(R*R);if(e2<9){var w=Math.exp(-e2);C+=w*q.c2;S+=w*q.s2;}}var h=Math.hypot(C,S)||1;return[C/h,S/h];};
  fn.n=L.length;fn.L=L;fn.pitch=function(s,dd){var v=fn(s,dd);return Math.atan2(v[1],v[0])/2;};return fn;}
/* RBF thin-plate teregularisasi dengan anisotropi berorientasi lokal (rotasi rata-rata pasangan) */
function imTpsRV(T,lev,VT,aS,aD){var n=T.length;if(n<3)return null;var s0=1e18,s1=-1e18,d0=1e18,d1=-1e18;T.forEach(function(p){s0=Math.min(s0,p[0]);s1=Math.max(s1,p[0]);d0=Math.min(d0,p[1]);d1=Math.max(d1,p[1]);});
  var cx=(s0+s1)/2,cy=(d0+d1)/2,L=Math.max(1,s1-s0,d1-d0),lb=IMSMO[Math.max(0,Math.min(3,lev|0))],g=Math.sqrt(aS*aD),ka=g/aS,kb=g/aD;
  var X=new Float64Array(n),Y=new Float64Array(n),C2=new Float64Array(n),S2=new Float64Array(n),b0=[];for(var i=0;i<n;i++){X[i]=(T[i][0]-cx)/L;Y[i]=(T[i][1]-cy)/L;var v=VT(T[i][0],T[i][1]);C2[i]=v[0];S2[i]=v[1];b0.push(T[i][2]);}
  var ps=s1-s0>1e-6,pd=d1-d0>1e-6,np=1+(ps?1:0)+(pd?1:0),m=n+np,A=new Float64Array(m*m),b=new Float64Array(m);
  var r2f=function(dx,dy,C,S){var h=Math.hypot(C,S);if(h<1e-12){C=1;S=0;}else{C/=h;S/=h;}var c=Math.sqrt(Math.max(0,(1+C)/2)),sn=(S>=0?1:-1)*Math.sqrt(Math.max(0,(1-C)/2)),a=(c*dx+sn*dy)*ka,bb=(-sn*dx+c*dy)*kb;return a*a+bb*bb;};
  for(i=0;i<n;i++){b[i]=b0[i];var ri=i*m;for(var j=i+1;j<n;j++){var r2=r2f(X[i]-X[j],Y[i]-Y[j],C2[i]+C2[j],S2[i]+S2[j]),k=r2>0?0.5*r2*Math.log(r2):0;A[ri+j]=k;A[j*m+i]=k;}
    A[ri+i]=T[i][3]?lb*0.01:lb;var c=n;A[ri+c]=1;A[c*m+i]=1;c++;if(ps){A[ri+c]=X[i];A[c*m+i]=X[i];c++;}if(pd){A[ri+c]=Y[i];A[c*m+i]=Y[i];}}
  var w=imSolve(A,b,m);if(!w)return null;
  return function(s,dd){var x=(s-cx)/L,y=(dd-cy)/L,v=VT(s,dd),r=w[n],c=n+1;if(ps)r+=w[c++]*x;if(pd)r+=w[c]*y;for(var i=0;i<n;i++){var r2=r2f(x-X[i],y-Y[i],v[0]+C2[i],v[1]+S2[i]);if(r2>0)r+=w[i]*0.5*r2*Math.log(r2);}return r;};}
/* bor tanpa interval domain yang menembus bidang tengah vein -> faktor ketebalan g(s,d) (0 di titik tembus) */
function imEmpty(d,P,Fr,fH,fW,QH,QW){if(P.pinE===false||!window.holeData)return null;var G=new Set(window.gmGroup?gmGroup(d.id):[d.id]),hard=QH.concat(QW).filter(function(q){return q[3]===1;});if(!hard.length)return null;
  var s0=1e18,s1=-1e18,d0=1e18,d1=-1e18;QH.concat(QW).forEach(function(q){s0=Math.min(s0,q[0]);s1=Math.max(s1,q[0]);d0=Math.min(d0,q[1]);d1=Math.max(d1,q[1]);});var mg=Math.max(+P.aoi||15,+P.pinD||15)+5;s0-=mg;s1+=mg;d0-=mg;d1+=mg;
  /* radius otomatis: ½ median jarak kontak bor terdekat di bidang vein (5–30 m) */
  var Rp=+P.pinR||0;if(!(Rp>0)){var nn=[];hard.forEach(function(a,i){if(i%Math.max(1,Math.floor(hard.length/300)))return;var m2=1e18;hard.forEach(function(b){var e=(a[0]-b[0])*(a[0]-b[0])+(a[1]-b[1])*(a[1]-b[1]);if(e>0.25&&e<m2)m2=e;});if(m2<1e18)nn.push(Math.sqrt(m2));});nn.sort(function(a,b){return a-b;});Rp=Math.max(5,Math.min(30,nn.length?nn[Math.floor(nn.length/2)]*0.5:10));}
  var E=[],ids=[],mid=function(s,dd){return(fH(s,dd)+fW(s,dd))/2;};
  Object.keys(holeData).forEach(function(id){var h=holeData[id];if(!h||!(h.maxD>0))return;if((GM.flags[id]||[]).some(function(f){return G.has(f[2]);}))return;var iv=gmIv(id);if(!iv.length)return;
    var st=Math.max(0.5,Math.min(1,h.maxD/200)),pv=null;for(var m=0;m<=h.maxD+1e-9;m+=st){var p=getXYZ(id,Math.min(m,h.maxD)),q=imLoc(Fr,[p.x,p.y,p.z]);if(q[0]<s0||q[0]>s1||q[1]<d0||q[1]>d1){pv=null;continue;}
      var v=q[2]-mid(q[0],q[1]);if(pv&&(v===0||(v>0)!==(pv.v>0))){var t=pv.v/(pv.v-v),mm=pv.m+(Math.min(m,h.maxD)-pv.m)*t,sx=pv.q[0]+(q[0]-pv.q[0])*t,dx=pv.q[1]+(q[1]-pv.q[1])*t;
        if(iv.some(function(a){return a[0]-1e-6<=mm&&mm<=a[1]+1e-6;})){var dm=1e18;hard.forEach(function(b){var e=(sx-b[0])*(sx-b[0])+(dx-b[1])*(dx-b[1]);if(e<dm)dm=e;});var r=Math.min(Rp,0.8*Math.sqrt(dm));
          if(r>=1){var P3=getXYZ(id,mm);E.push({s:sx,d:dx,r:r,id:id,m:mm,x:P3.x,y:P3.y,z:P3.z});ids.push(id);}}break;}
      pv={v:v,m:Math.min(m,h.maxD),q:q};}});
  if(!E.length)return{n:0,ids:[],pts:[],Rp:Rp,g:function(){return 1;}};
  var gf=function(s,dd){var f=1;for(var i=0;i<E.length;i++){var e=E[i],x=Math.hypot(s-e.s,dd-e.d)/e.r;if(x<1){var sm=x*x*(3-2*x);if(sm<f)f=sm;}}return f;};
  return{n:E.length,ids:ids,pts:E,Rp:Rp,g:gf};}
/* ---------- OK: orientasi elipsoid dinamis mengikuti bidang HW / FW lokal ---------- */
function meVAprep(d){var ids=window.gmGroup?gmGroup(d.id):[d.id],L=ids.map(function(i){return IM.R[i];}).filter(function(R){return R&&R.fr&&R.fH&&R.fW;});return L.length?{R:L}:null;}
function meVArot(Q,a){return[Q[0][0]*a[0]+Q[0][1]*a[1]+Q[0][2]*a[2],Q[1][0]*a[0]+Q[1][1]*a[1]+Q[1][2]*a[2],Q[2][0]*a[0]+Q[2][1]*a[1]+Q[2][2]*a[2]];}
function meVA(X,x,y,z){var V=X.va;if(!V)return null;var best=null,bd=1e18;V.R.forEach(function(R){var q=imLoc(R.fr,[x,y,z]),md=(R.fH(q[0],q[1])+R.fW(q[0],q[1]))/2,e=Math.abs(q[2]-md);if(e<bd){bd=e;best={R:R,q:q};}});if(!best)return null;
  var R=best.R,F=R.fr,s=best.q[0],dd=best.q[1],h=Math.max(1,(R.st&&R.st.res)||2),mid=function(a,b){return(R.fH(a,b)+R.fW(a,b))/2;},ms=(mid(s+h,dd)-mid(s-h,dd))/(2*h),md2=(mid(s,dd+h)-mid(s,dd-h))/(2*h);
  if(!isFinite(ms)||!isFinite(md2))return null;var nrm=function(v){var l=Math.hypot(v[0],v[1],v[2])||1;return[v[0]/l,v[1]/l,v[2]/l];},cr=function(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];};
  var ts=nrm([F.u[0]+ms*F.n[0],F.u[1]+ms*F.n[1],F.u[2]+ms*F.n[2]]),td=[F.v[0]+md2*F.n[0],F.v[1]+md2*F.n[1],F.v[2]+md2*F.n[2]],nl=nrm(cr(ts,td));if(nl[0]*F.n[0]+nl[1]*F.n[1]+nl[2]*F.n[2]<0)nl=[-nl[0],-nl[1],-nl[2]];
  var ul=ts,vl=cr(nl,ul);if(R.vt&&R.vt.pitch){var dt=R.vt.pitch(s,dd)-(R.th0||0),c=Math.cos(dt),sn=Math.sin(dt),u2=[c*ul[0]+sn*vl[0],c*ul[1]+sn*vl[1],c*ul[2]+sn*vl[2]];vl=[-sn*ul[0]+c*vl[0],-sn*ul[1]+c*vl[1],-sn*ul[2]+c*vl[2]];ul=u2;}
  /* Q = [ul vl nl] · [u v n]^T  : memutar sumbu variogram dari kerangka vein global ke kerangka lokal */
  var Q=[[0,0,0],[0,0,0],[0,0,0]];for(var i=0;i<3;i++)for(var j=0;j<3;j++)Q[i][j]=ul[i]*F.u[j]+vl[i]*F.v[j]+nl[i]*F.n[j];
  var m=X.mo;return{vM:nrm(meVArot(Q,m.vM)),vS:nrm(meVArot(Q,m.vS)),vN:nrm(meVArot(Q,m.vN)),c0:m.c0,cs:m.cs,A:m.A,B:m.B,Cn:m.Cn,R:m.R};}
function meSetVa(id,v){var d=gmDom(id);if(!d||!d.est)return;d.est.va=v;gmDirty(true);mePanel();}
"""


def patch(s):
    # ---- parameter bawaan baru; domain lama (d.im tanpa pinE) tetap seperti sebelumnya ----
    s = rep(s, "var IMDEF={on:false,minT:1,pinD:15,aoi:15,res:2,smo:1,rob:true,src:'both',topo:true,ori:'auto',dip:60,ddir:0,aS:50,aD:50,pitch:0};",
            "var IMDEF={on:false,minT:1,pinD:15,aoi:15,res:2,smo:1,rob:true,src:'both',topo:true,ori:'auto',dip:60,ddir:0,aS:50,aD:50,pitch:0,vo:'lin',voR:40,pinE:true,pinR:0};")
    s = rep(s, "function imPar(d){var P=Object.assign({},IMDEF,d&&d.im||{});",
            "function imPar(d){var P=Object.assign({},IMDEF,d&&d.im||{});if(d&&d.im&&d.im.pinE===undefined)P.pinE=false;")
    s = rep(s, "/* ---------- bangun solid satu domain ---------- */", HELPERS + "\n/* ---------- bangun solid satu domain ---------- */")
    # ---- imBuild: RBF dengan tren, pinch-out bor kosong ----
    s = rep(s, """  var gH=imTpsR(mp(TH),lev),gW=imTpsR(mp(TW),lev);if(!gH||!gW)throw new Error('sistem RBF singular (titik segaris / terlalu sedikit)');
  var mkF=function(g){return Tr?function(s,dd){var a=Tr(s,dd);return g(a[0],a[1]);}:g;},fH=mkF(gH),fW=mkF(gW);""",
            """  var VT=imTrend(d,P,Fr,X),imFit=function(T){if(VT)return imTpsRV(T,lev,VT,+P.aS||1,+P.aD||1);var g=imTpsR(mp(T),lev);return g?(Tr?function(s,dd){var a=Tr(s,dd);return g(a[0],a[1]);}:g):null;};
  var fH=imFit(TH),fW=imFit(TW);if(!fH||!fW)throw new Error('sistem RBF singular (titik segaris / terlalu sedikit)');""")
    s = rep(s, "if(nst){var g1=imTpsR(mp(TH.concat(addH)),lev),g2=imTpsR(mp(TW.concat(addW)),lev);if(g1&&g2){gH=g1;gW=g2;fH=mkF(gH);fW=mkF(gW);}}",
            "if(nst){var g1=imFit(TH.concat(addH)),g2=imFit(TW.concat(addW));if(g1&&g2){fH=g1;fW=g2;}}")
    s = rep(s, "  var A=QH.concat(QW),GR=imGroups(A,Math.max(aoi,res0)),smin=1e18",
            "  var EP=imEmpty(d,P,Fr,fH,fW,QH,QW);\n  var A=QH.concat(QW),GR=imGroups(A,Math.max(aoi,res0)),smin=1e18")
    s = rep(s, "var f=B?0:tap(Math.min(1,ed)),h=fH(s,dd)", "var f=(B?0:tap(Math.min(1,ed)))*(EP&&EP.n?EP.g(s,dd):1),h=fH(s,dd)")
    s = rep(s, "return{mesh:m,fr:Fr,fH:fH,fW:fW,minT:minT,st:{",
            "return{mesh:m,fr:Fr,fH:fH,fW:fW,minT:minT,vt:VT,th0:(+P.pitch||0)*Math.PI/180,ep:EP?EP.pts:[],st:{nvt:VT?VT.n:0,nem:EP?EP.n:0,emIds:EP?EP.ids:[],emR:EP?EP.Rp:0,")
    s = rep(s, "P.aS,P.aD,P.pitch,P.top==='topo'&&imTopoOk()",
            "P.aS,P.aD,P.pitch,P.vo,P.voR,P.pinE,P.pinR,window.holeData?Object.keys(holeData).length:0,P.top==='topo'&&imTopoOk()")
    # ---- panel RBF: tren & pinch-out bor kosong ----
    s = rep(s, "Tebal tetap dari jarak HW&ndash;FW.</div>'+",
            "Tebal tetap dari jarak HW&ndash;FW.</div>'+"
            "'<div class=imsec>Orientasi bervariasi (tren pitch)</div>'+"
            "'<div class=\"g2 f\"><div><label>Pitch elipsoid</label><select onchange=\"imSet(\\'vo\\',this.value)\"><option value=lin'+(P.vo!=='off'?' selected':'')+'>Bervariasi: ikuti lineasi struktur</option><option value=off'+(P.vo==='off'?' selected':'')+'>Tetap (satu pitch)</option></select></div>'+"
            "'<div><label>Radius pengaruh tren (m)</label>'+inp('voR',P.voR!=null?P.voR:40,'any',1,'Di luar radius ini dari lineasi, pitch kembali ke nilai di atas')+'</div></div>'+"
            "'<div class=hint style=\"margin-top:-4px\">Pitch lokal diinterpolasi dari titik struktur yang punya <b>plunge / trend</b> (lineasi: arah shoot, striasi, sumbu lipatan) — isi di Data Referensi &rsaquo; Struktur atau kolom Plunge / Trend di CSV. '+(Ra&&Ra.st&&Ra.st.nvt?'<b>'+Ra.st.nvt+' lineasi dipakai.</b>':'Belum ada lineasi di sekitar domain ini: pitch tetap.')+'</div>'+"
            "'<div class=imsec>Pinch-out di bor tanpa vein</div>'+"
            "'<div class=\"g2 f\"><label class=sw style=\"margin:0\"><input type=checkbox '+(P.pinE!==false?'checked':'')+' onchange=\"imSet(\\'pinE\\',this.checked)\">Menipis ke nol di bor yang menembus bidang vein tanpa interval domain</label>'+"
            "'<div><label>Radius penipisan (m, 0 = otomatis)</label>'+inp('pinR',P.pinR||0,'any',0,'0 = setengah median jarak antar kontak bor (5–30 m); selalu dibatasi 0,8 x jarak ke kontak bor terdekat')+'</div></div>'+"
            "(Ra&&Ra.st&&P.pinE!==false?'<div class=hint style=\"margin-top:-4px\">'+(Ra.st.nem?'<b>'+Ra.st.nem+' bor kosong</b> memotong bidang vein (radius '+imN(Ra.st.emR,1)+' m): '+gmE((Ra.st.emIds||[]).slice(0,12).join(', '))+((Ra.st.emIds||[]).length>12?', …':''):'Tidak ada bor kosong yang memotong bidang vein.')+'</div>':'')+")
    # ---- struktur: lineasi (plunge / trend) ----
    s = rep(s, "var cK=f(/^(ket|keterangan|desc|description|remark|remarks|type|tipe|jenis|catatan)/,6);",
            "var cK=f(/^(ket|keterangan|desc|description|remark|remarks|type|tipe|jenis|catatan)/,6),cPl=hasH?f(/^(plunge|pl|plg|linplunge|lplunge|lineasiplunge)$/,-1):-1,cTr=hasH?f(/^(trend|tr|plgaz|plungeaz|plungeazimuth|plungedir|lintrend|ltrend|lineasitrend)$/,-1):-1;")
    s = rep(s, "STR.P.push({id:stId(),no:cNo>=0?c[cNo]:String(n+1),x:x,y:y,z:z,dip:d,az:((a%360)+360)%360,ket:cK>=0?(c[cK]||''):'',fid:fid});n++;",
            "var pl=cPl>=0?num(c[cPl]):null,tr=cTr>=0?num(c[cTr]):null;STR.P.push({id:stId(),no:cNo>=0?c[cNo]:String(n+1),x:x,y:y,z:z,dip:d,az:((a%360)+360)%360,pl:pl!==null&&tr!==null?pl:null,tr:pl!==null&&tr!==null?((tr%360)+360)%360:null,ket:cK>=0?(c[cK]||''):'',fid:fid});n++;")
    s = rep(s, "Import CSV <code>No, X, Y, Z, Dip, Dip_Azimuth, Keterangan</code>",
            "Import CSV <code>No, X, Y, Z, Dip, Dip_Azimuth, Plunge, Trend, Keterangan</code> (Plunge / Trend = lineasi, opsional)")
    s = rep(s, """'<label>Keterangan</label><input type=text value="'+stE(p.ket)+'" onchange="stSet(\\''+id+'\\',\\'ket\\',this.value)" placeholder="mis. kontak vein, sesar, kekar">'+""",
            """'<div class="g3 f"><div><label>Plunge (lineasi)</label><input type=number step=any value="'+(p.pl!=null?p.pl:'')+'" placeholder="kosong" onchange="stSet(\\''+id+'\\',\\'pl\\',this.value===\\'\\'?null:+this.value)"></div><div><label>Trend (lineasi)</label><input type=number step=any value="'+(p.tr!=null?p.tr:'')+'" placeholder="kosong" onchange="stSet(\\''+id+'\\',\\'tr\\',this.value===\\'\\'?null:+this.value)"></div><div class=hint style="align-self:end;margin:0">arah shoot / striasi; dipakai tren pitch RBF</div></div>'+
    '<label>Keterangan</label><input type=text value="'+stE(p.ket)+'" onchange="stSet(\\''+id+'\\',\\'ket\\',this.value)" placeholder="mis. kontak vein, sesar, kekar">'+""")
    s = rep(s, "<td>'+Math.round(p.dip)+'/'+('00'+Math.round(p.az)).slice(-3)+'</td>",
            "<td>'+Math.round(p.dip)+'/'+('00'+Math.round(p.az)).slice(-3)+(p.pl!=null?' <small>&rarr;'+Math.round(p.pl)+'/'+('00'+Math.round(p.tr)).slice(-3)+'</small>':'')+'</td>")
    # ---- Model Estimation: orientasi dinamis ----
    s = rep(s, "D.push({d:d,P:P,mo:mo,C:C,", "D.push({d:d,P:P,mo:mo,va:P.va==='vein'?meVAprep(d):null,C:C,")
    s = rep(s, "var x=it.x-offX,y=it.y-offY,z=it.z,res=null;\n    for(var p=0;p<P.P.length;p++){var pp=P.P[p],sel=okSearch(mo,X.I,X.C,x,y,z,+pp.mult,+pp.max,+pp.mph||0);if(sel.length<+pp.min)continue;var r=okKrige(mo,X.C,X.z,sel,x,y,z,dc.D,dc.cbb);",
            "var x=it.x-offX,y=it.y-offY,z=it.z,res=null,cbb=dc.cbb;if(X.va){var mv=meVA(X,x,y,z);if(mv){mo=mv;cbb=okCbb(mo,dc.D);X.nva=(X.nva||0)+1;}}\n    for(var p=0;p<P.P.length;p++){var pp=P.P[p],sel=okSearch(mo,X.I,X.C,x,y,z,+pp.mult,+pp.max,+pp.mph||0);if(sel.length<+pp.min)continue;var r=okKrige(mo,X.C,X.z,sel,x,y,z,dc.D,cbb);")
    s = rep(s, "  h+='<div class=\"g3 f\"><div><label>Unsur</label><input type=text value=\"'+gmE(P.el)+'\" disabled>",
            "  h+='<div class=\"g2 f\"><div><label>Orientasi elipsoid</label><select onchange=\"meSetVa(\\''+id+'\\',this.value)\"><option value=fix'+(P.va!=='vein'?' selected':'')+'>Tetap (satu arah)</option><option value=vein'+(P.va==='vein'?' selected':'')+'>Dinamis: ikuti HW / FW vein</option></select></div>'+"
            "'<div class=hint style=\"align-self:end;margin:0\">'+(P.va==='vein'?'Sumbu variogram &amp; pencarian diputar per blok searah bidang vein setempat (strike / dip lokal dari solid RBF).':'Satu elipsoid untuk seluruh domain.')+'</div></div>';\n"
            "  h+='<div class=\"g3 f\"><div><label>Unsur</label><input type=text value=\"'+gmE(P.el)+'\" disabled>")
    s = rep(s, "n:GS.R.st?GS.R.st.n:0};", "n:GS.R.st?GS.R.st.n:0};if(_va)d.est.va=_va;")
    s = rep(s, "  d.est={el:GS.R.el,", "  var _va=d.est&&d.est.va;d.est={el:GS.R.el,")
    return s


TAIL = r"""
/* ringkasan run: orientasi dinamis */
(function(){if(typeof meCommit!=='function')return;var _mc=meCommit;meCommit=function(J){var r=_mc.apply(this,arguments);try{var L=J.D.filter(function(x){return x.va&&!x.err;}).map(function(x){return gmE(x.d.name)+' ('+(x.nva||0)+' blok)';});
  if(L.length){ME.msg=(ME.msg||'')+'<br><small>Orientasi elipsoid dinamis mengikuti HW / FW: '+L.join(', ')+'</small>';mePanel();}}catch(e){console.error(e);}return r;};})();
/* titik tembus bor kosong di 3D */
(function(){if(typeof imTraces!=='function')return;var _t=imTraces;imTraces=function(T,o){var r=_t.apply(this,arguments);try{if(GM.lay.im===false||VIEW2D)return r;var X=[],Y=[],Z=[],tx=[];GM.doms.forEach(function(d){var R=IM.R[d.id];if(!d.vis||!R||!R.ep||!R.ep.length)return;R.ep.forEach(function(e){X.push(e.x);Y.push(e.y);Z.push(e.z);tx.push(e.id+' @ '+e.m.toFixed(1)+' m: bor tanpa '+d.name+' → pinch-out');});});
  if(X.length)T.push({type:'scatter3d',mode:'markers',x:X,y:Y,z:Z,text:tx,hoverinfo:'text',name:'Bor kosong (pinch-out)',marker:{size:5,symbol:'x',color:'#c92a2a'}});}catch(e){}return r;};})();
"""
