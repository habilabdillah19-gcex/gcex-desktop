# -*- coding: utf-8 -*-
"""GC-Ex Drillhole — integrasi data struktur & pemetaan permukaan (0.10.0).
Semua data struktur memakai SATU basis data (STR) dan dipakai bersama oleh Geological Modelling (RBF, tren pitch),
Model Estimation (OK dinamis), Data Referensi, Map dan 3D:
  1. Flag struktur GM (5): selain bidang (dip / dip azimuth) kini juga lineasi (plunge / trend), nilai menempel untuk klik berikutnya.
  2. Titik pick-up Map dengan kolom Dip / Dip_Azimuth (/ Plunge / Trend) otomatis masuk basis data struktur
     (elevasi dari RL atau topografi); baris yang hanya berisi plunge / trend = lineasi untuk tren pitch.
  3. Garis Map (Vein / urat, Kontak, garis lain) dapat dikaitkan ke domain sebagai jejak singkapan:
     tengah vein + lebar singkapan -> titik bantu HW / FW di permukaan (elevasi topografi / RL) untuk solid RBF.
  4. Garis sumbu antiklin / sinklin / lineasi di Map (dengan plunge) dipakai sebagai lineasi tren pitch.
Dipanggil dari build_dh.py sesudah gm2_patch: s = gm3_patch.patch(s); TAIL disisipkan di akhir sumber viewer."""


def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, 'gm3_patch: pola ditemukan %d kali (harus %d): %s' % (c, n, a[:90])
    return s.replace(a, b)


HELPERS = r"""
/* ================= GM v3: data struktur & pemetaan permukaan terintegrasi ================= */
var MAPLIN={'Sumbu antiklin':1,'Sumbu sinklin':1,'Lineasi / shoot':1};
function mapOk(){return typeof MAP!=='undefined'&&MAP&&MAP.F;}
function mapIsD(f,d){return f&&f.dom!=null&&f.dom!==''&&String(f.dom)===String(d.id);}
/* elevasi titik peta (koordinat dunia): RL bila ada, kalau tidak dari topografi */
function mapZ(x,y,z){if(z!=null&&z!==''&&isFinite(+z))return +z;var v=null;try{if(imTopoOk())v=topoZ(x-offX,y-offY);}catch(e){}return v!=null&&isFinite(v)?v:null;}
/* sidik jari data Map yang dipakai pemodelan (kosong bila tidak ada -> kunci model lama tidak berubah) */
function mapGmKey(){if(!mapOk())return '';var a=[];MAP.F.forEach(function(f){if(f.vis===false)return;if((f.dom!=null&&f.dom!=='')||f.lin)a.push([f.id,f.dom||'',f.lin||'',f.w,f.vr,f.ddir,f.pl,f.rev,f.pts]);});
  (MAP.PF||[]).forEach(function(f){if(!f.on)return;var L=f.P.filter(function(p){return p[5]&&p[5].pl!=null&&p[5].dip==null;});if(L.length)a.push([f.id,L.map(function(p){return[p[1],p[2],p[3],p[5].pl,p[5].tr];})]);});
  return a.length?'m'+imHash(JSON.stringify(a)):'';}
/* jejak singkapan vein (garis Map terkait domain) -> titik bantu HW / FW permukaan (koordinat lokal, titik lunak) */
function mapOutcrop(d,P,H,W,r){var out={n:0,f:[],miss:[]};if(P.mapo===false||!mapOk())return out;
  var F=MAP.F.filter(function(f){return mapIsD(f,d)&&f.vis!==false&&!f.closed&&f.pts&&f.pts.length>=2;});if(!F.length)return out;var hd;
  F.forEach(function(f){var vr=f.vr||'mid',w=Math.max(0,+f.w||0),dir=null;
    if(f.ddir!=null&&f.ddir!==''&&isFinite(+f.ddir)){var a0=(+f.ddir)*Math.PI/180;dir=[Math.sin(a0),Math.cos(a0)];}
    else{if(hd===undefined){hd=null;if(H.length>=3&&W.length>=3){try{var Fr=imFrame(H,W,P),l=Math.hypot(Fr.n[0],Fr.n[1]);if(l>1e-6)hd=[Fr.n[0]/l,Fr.n[1]/l];}catch(e){}}}dir=hd;}
    if(vr==='mid'&&w>0&&!dir){out.miss.push(f.name+': arah dip belum diketahui (isi arah dip vein di Map)');return;}
    var st=Math.max(1,r),k=0,nz=0;
    for(var i=1;i<f.pts.length;i++){var a=f.pts[i-1],b=f.pts[i],L=Math.hypot(b[0]-a[0],b[1]-a[1]);if(L<1e-6)continue;var px=-(b[1]-a[1])/L,py=(b[0]-a[0])/L;if(dir&&px*dir[0]+py*dir[1]<0){px=-px;py=-py;}
      var hz=a.length>2&&b.length>2&&a[2]!=null&&b[2]!=null&&isFinite(a[2])&&isFinite(b[2]),n=Math.max(1,Math.ceil(L/st));
      for(var j=(i===1?0:1);j<=n;j++){var t=j/n,x=a[0]+(b[0]-a[0])*t,y=a[1]+(b[1]-a[1])*t,z0=hz?a[2]+(b[2]-a[2])*t:null;
        var put=function(L2,o){var X=x+px*o,Y=y+py*o,z=z0!=null?z0:mapZ(X,Y);if(z==null){nz++;return;}L2.push([X-offX,Y-offY,z,0,0]);k++;};
        if(vr==='HW')put(H,0);else if(vr==='FW')put(W,0);else{put(H,w/2);put(W,-w/2);}}}
    if(k){out.n+=k;out.f.push(f.name);}else if(nz)out.miss.push(f.name+': elevasi tidak diketahui (topografi belum ada)');});
  return out;}
/* lineasi tambahan dari Map: baris pick-up yang hanya berisi plunge / trend, dan garis sumbu lipatan / lineasi */
function stLinX(d,P,X){var out=[];if(!mapOk())return out;var R=Math.max(+((P.strR!=null)?P.strR:(window.STR?STR.rad:25))||0,+P.voR||40),B=X?X.H.concat(X.W):[];
  var near=function(c){if(!B.length)return false;var dm=1e18,stp=Math.max(1,Math.floor(B.length/2000));for(var i=0;i<B.length;i+=stp){var q=B[i],e=(q[0]-c[0])*(q[0]-c[0])+(q[1]-c[1])*(q[1]-c[1])+(q[2]-c[2])*(q[2]-c[2]);if(e<dm)dm=e;}return Math.sqrt(dm)<=R;};
  (MAP.PF||[]).forEach(function(f){if(!f.on)return;f.P.forEach(function(p){var s=p[5];if(!s||s.pl==null||s.tr==null||s.dip!=null)return;var z=mapZ(p[1],p[2],p[3]);if(z==null)return;var c=[p[1]-offX,p[2]-offY,z];if(near(c))out.push({c:c,pl:+s.pl,tr:+s.tr,id:p[0],src:'pf'});});});
  MAP.F.forEach(function(f){if(f.vis===false||!f.lin||f.closed||!f.pts||f.pts.length<2)return;if(f.lin!=='*'&&String(f.lin)!==String(d.id))return;var st=Math.max(5,(+P.voR||40)/3),pl=Math.max(0,Math.min(90,+f.pl||0));
    for(var i=1;i<f.pts.length;i++){var a=f.pts[i-1],b=f.pts[i],L=Math.hypot(b[0]-a[0],b[1]-a[1]);if(L<1e-6)continue;var tr=(Math.atan2(b[0]-a[0],b[1]-a[1])*180/Math.PI+(f.rev?180:0)+720)%360,n=Math.max(1,Math.ceil(L/st));
      for(var j=(i===1?0:1);j<=n;j++){var t=j/n,x=a[0]+(b[0]-a[0])*t,y=a[1]+(b[1]-a[1])*t,z=mapZ(x,y,(a.length>2&&b.length>2&&a[2]!=null&&b[2]!=null)?a[2]+(b[2]-a[2])*t:null);if(z==null)continue;var c=[x-offX,y-offY,z];if(f.lin==='*'&&!near(c))continue;out.push({c:c,pl:pl,tr:tr,id:f.name,src:'map'});}}});
  return out;}
/* RBF dengan orientasi bervariasi yang stabil: beberapa TPS anisotropi global (pitch tiap 15°, kernel valid) dicampur
   per lokasi menurut pitch tren setempat -> mengikuti tren tanpa osilasi (menggantikan kernel rotasi pasangan 0.9.0) */
function imTpsVB(T,lev,VT,P){var st=15,need={},s0=1e18,s1=-1e18,d0=1e18,d1=-1e18;if(T.length<3)return null;T.forEach(function(p){s0=Math.min(s0,p[0]);s1=Math.max(s1,p[0]);d0=Math.min(d0,p[1]);d1=Math.max(d1,p[1]);});
  var ang=function(s,dd){var a=VT.pitch(s,dd)*180/Math.PI;return((a%180)+180)%180;},mark=function(a){var i=Math.floor(a/st);need[i%12]=1;need[(i+1)%12]=1;};
  T.forEach(function(p){mark(ang(p[0],p[1]));});var mg=Math.max(+P.aoi||15,+P.pinD||15)+30;for(var i=0;i<=24;i++)for(var j=0;j<=24;j++)mark(ang(s0-mg+(s1-s0+2*mg)*i/24,d0-mg+(d1-d0+2*mg)*j/24));
  var F={},K=[];for(var k in need){var Tr=imAniso(Object.assign({},P,{pitch:k*st})),g=imTpsR(T.map(function(q){var a=Tr(q[0],q[1]);return[a[0],a[1],q[2],q[3]];}),lev);if(!g)return null;F[k]=(function(g,Tr){return function(s,dd){var a=Tr(s,dd);return g(a[0],a[1]);};})(g,Tr);K.push(+k);}
  var near=function(i){var b=null,bd=99;K.forEach(function(k){var e=Math.abs(k-i)%12;e=Math.min(e,12-e);if(e<bd){bd=e;b=k;}});return F[b];};
  var f=function(s,dd){var a=ang(s,dd),i=Math.floor(a/st),t=a/st-i,A=F[i%12],B=F[(i+1)%12];if(!A||!B)return(A||B||near(i%12))(s,dd);t=t*t*(3-2*t);return t<1e-9?A(s,dd):t>1-1e-9?B(s,dd):(1-t)*A(s,dd)+t*B(s,dd);};f.nk=K.length;return f;}
/* panel RBF: data permukaan */
function imMapHtml(d,P,Ra){if(!d||!mapOk())return '';var F=MAP.F.filter(function(f){return mapIsD(f,d);}),Lf=MAP.F.filter(function(f){return f.lin&&(f.lin==='*'||String(f.lin)===String(d.id));}),S=Ra&&Ra.st;
  var h='<div class=imsec>Data permukaan (Map)</div><label class=sw style="margin:0"><input type=checkbox '+(P.mapo!==false?'checked':'')+' onchange="imSet(\'mapo\',this.checked)">Pakai jejak singkapan vein hasil pemetaan</label>';
  h+='<div class=hint style="margin-top:-2px">'+(F.length?'<b>'+F.length+' garis Map</b> terkait domain ini: '+gmE(F.map(function(f){return f.name+((f.vr||'mid')!=='mid'?' (kontak '+f.vr+')':' (lebar '+(+f.w||0)+' m)');}).join(', '))+(S&&S.nmo&&P.mapo!==false?' &rarr; <b>'+S.nmo+' titik HW / FW permukaan</b> masuk RBF.':'')+((S&&S.mom&&S.mom.length)?' <span class=warn>Dilewati: '+gmE(S.mom.join('; '))+'</span>':'')
    :'Belum ada. Di menu <b>Map</b> pilih garis vein hasil digitasi (atau garis dari titik pick-up), lalu isi <i>Jejak singkapan vein untuk domain</i> &amp; <i>lebar singkapan</i>.')+
    (Lf.length?'<br>'+Lf.length+' garis sumbu lipatan / lineasi Map dipakai sebagai tren pitch'+(S&&S.nlx?' ('+S.nlx+' titik lineasi)':'')+'.':'')+'</div>';
  return h;}
"""

TAIL = r"""
/* ================= GM v3: tampilan & sinkronisasi Map <-> basis data struktur ================= */
MAPST['Lineasi / shoot']=MAPST['Lineasi / shoot']||{c:'#2b8a3e',w:1.8,d:'longdash'};
/* titik pick-up ber-dip / dip azimuth -> basis data struktur (satu file STR per file pick-up) */
function mapPfStr(f){if(!window.STR||!f)return 0;var fid='pf_'+f.id;STR.P=STR.P.filter(function(p){return p.fid!==fid;});STR.F=STR.F.filter(function(x){return x.id!==fid;});var n=0,nl=0;
  f.P.forEach(function(p){var s=p[5];if(!s)return;if(s.dip==null){if(s.pl!=null)nl++;return;}var z=mapZ(p[1],p[2],p[3]);if(z==null)z=(window.G&&isFinite(G.z1))?G.z1:0;
    STR.P.push({id:stId(),no:p[0],x:p[1],y:p[2],z:z,dip:s.dip,az:s.az,pl:s.pl,tr:s.tr,ket:p[4]==='-'?'':p[4],fid:fid});n++;});
  if(n)STR.F.push({id:fid,name:f.name+' (Map pick-up)',on:f.on!==false,kind:'map',pf:f.id});if(n||nl)stDirty(true);return{n:n,nl:nl};}
(function(){var _d=mapPtDel;mapPtDel=function(id){var n=MAP.PF.length,r=_d.apply(this,arguments);if(MAP.PF.length<n&&window.STR){var fid='pf_'+id;if(STR.F.some(function(x){return x.id===fid;})){STR.P=STR.P.filter(function(p){return p.fid!==fid;});STR.F=STR.F.filter(function(x){return x.id!==fid;});stDirty(true);}}return r;};
  var _s=mapPtSet;mapPtSet=function(id,k,v){var r=_s.apply(this,arguments);if(k==='on'&&window.STR){var sf=stFile('pf_'+id);if(sf){sf.on=v;stDirty(true);}}return r;};
  var _md=mapDirty;mapDirty=function(){var r=_md.apply(this,arguments);try{var k=mapGmKey();if(k!==MAP._gk){var first=MAP._gk===undefined;MAP._gk=k;if(!first||k){try{IM.sc={};}catch(e){}gmDirty(true);}}}catch(e){console.error(e);}return r;};})();
/* kotak atribut fitur terpilih di Map: kaitan ke Geological Modelling */
function mapGmBox(){var f=MAP.sel&&MAP.F.filter(function(x){return x.id===MAP.sel;})[0];if(!f||f.closed||f.kind==='alt'||f.kind==='lith')return '';var D=window.GM?GM.doms:[],q='\''+f.id+'\'',isL=f.kind==='str'&&MAPLIN[f.type];
  var opt=function(v,cur,t){return '<option value="'+mapE(v)+'"'+(String(cur)===String(v)?' selected':'')+'>'+mapE(t)+'</option>';},h='<div class="box mapgm" style="margin:6px 0"><b>Integrasi ke Geological Modelling: '+mapE(f.name)+'</b>';
  if(isL){h+='<div class="g3 f"><div><label>Tren pitch RBF</label><select onchange="mapSetF('+q+',\'lin\',this.value)">'+opt('',f.lin||'','Tidak dipakai')+opt('*',f.lin||'','Semua domain di dekatnya')+D.map(function(d){return opt(d.id,f.lin||'',d.name);}).join('')+'</select></div>'+
      '<div><label>Plunge (&deg;)</label><input type=number step=any min=0 max=90 value="'+(+f.pl||0)+'" onchange="mapSetF('+q+',\'pl\',+this.value)"></div><div><label>Arah plunge</label><select onchange="mapSetF('+q+',\'rev\',this.value===\'1\')">'+opt('0',f.rev?'1':'0','Searah digitasi')+opt('1',f.rev?'1':'0','Berlawanan')+'</select></div></div>'+
      '<div class=hint style="margin-top:-4px">Arah garis (trend) + plunge = lineasi untuk tren pitch elipsoid RBF (Geological Modelling &#9315; &rsaquo; Orientasi bervariasi). Elevasi dari topografi.</div>';}
  else if(f.kind==='str'&&!/^(Vein|Kontak)/.test(f.type))h+='<div class=hint>Garis <b>'+mapE(f.type)+'</b> hanya untuk peta. Untuk pemodelan pakai tipe <b>Vein / urat</b> atau <b>Kontak</b> (jejak singkapan), atau <b>Sumbu antiklin / sinklin / Lineasi / shoot</b> (tren pitch).</div>';
  else{var vr=f.vr||'mid';h+='<div class="g2 f"><div><label>Jejak singkapan vein untuk domain</label><select onchange="mapSetF('+q+',\'dom\',this.value||null)">'+opt('',f.dom||'','Tidak dipakai')+D.map(function(d){return opt(d.id,f.dom||'',d.name);}).join('')+'</select></div>'+
      '<div><label>Garis ini adalah</label><select onchange="mapSetF('+q+',\'vr\',this.value)">'+opt('mid',vr,'Tengah vein (pakai lebar)')+opt('HW',vr,'Kontak HW')+opt('FW',vr,'Kontak FW')+'</select></div></div>';
    if(vr==='mid')h+='<div class="g2 f"><div><label>Lebar singkapan (m, horizontal)</label><input type=number step=any min=0 value="'+(f.w!=null?f.w:'')+'" placeholder="0" onchange="mapSetF('+q+',\'w\',+this.value)"></div><div><label>Arah dip vein (&deg;, kosong = otomatis dari bor)</label><input type=number step=any min=0 max=360 value="'+(f.ddir!=null?f.ddir:'')+'" placeholder="otomatis" onchange="mapSetF('+q+',\'ddir\',this.value===\'\'?null:+this.value)"></div></div>';
    var noT=f.dom&&!imTopoOk()&&!(f.pts[0]&&f.pts[0].length>2);
    h+='<div class=hint style="margin-top:-4px">Jejak menjadi titik bantu HW / FW di permukaan untuk solid RBF domain tersebut (elevasi dari RL titik pick-up atau topografi). Sisi HW = ke arah dip.'+(noT?' <span class=warn>Topografi belum ada: elevasi jejak tidak bisa ditentukan.</span>':'')+'</div>';}
  return h+'</div>';}
function mapGmTag(f){var d=f.dom&&window.gmDom?(GM.doms.filter(function(x){return String(x.id)===String(f.dom);})[0]):null,s='';if(d)s+=' &middot; <b style="color:'+d.col+'">GM: '+mapE(d.name)+'</b>';if(f.lin)s+=' &middot; <b>tren pitch</b>';return s;}
/* simbol lineasi (panah trend + angka plunge) di Map */
(function(){var _m=mapStrSym;mapStrSym=function(){var o=_m.apply(this,arguments);try{var L=+MAP.sym||10,r=Math.PI/180,add=function(x,y,pl,tr){var a=tr*r,ex=x+0.9*L*Math.sin(a),ey=y+0.9*L*Math.cos(a);o.x.push(x,ex,null);o.y.push(y,ey,null);
      [150,-150].forEach(function(b){var c=a+b*r;o.x.push(ex,ex+0.3*L*Math.sin(c),null);o.y.push(ey,ey+0.3*L*Math.cos(c),null);});o.tx.push(x+1.15*L*Math.sin(a));o.ty.push(y+1.15*L*Math.cos(a));o.tt.push(String(Math.round(pl)));};
    if(window.STR)STR.P.forEach(function(p){if(stOn(p)&&p.pl!=null&&p.tr!=null&&isFinite(+p.pl)&&isFinite(+p.tr))add(p.x,p.y,+p.pl,+p.tr);});
    (MAP.PF||[]).forEach(function(f){if(f.on)f.P.forEach(function(p){var s=p[5];if(s&&s.dip==null&&s.pl!=null&&s.tr!=null)add(p[1],p[2],+s.pl,+s.tr);});});}catch(e){console.error(e);}return o;};})();
/* lineasi di 3D */
(function(){var _t=stTraces;stTraces=function(T,o){var r0=_t.apply(this,arguments);try{if(!STR.lay||VIEW2D||!STR.P.length)return r0;var r=Math.max(0.5,+STR.sz||5),X=[],Y=[],Z=[],rd=Math.PI/180;
    STR.P.forEach(function(p){if(!stOn(p)||p.pl==null||p.tr==null||!isFinite(+p.pl)||!isFinite(+p.tr))return;var c=stLoc(p);if(o&&o.clip&&o.K&&!inK(o.K,{x:c[0],y:c[1],z:c[2]}))return;var pl=(+p.pl)*rd,tr=(+p.tr)*rd,l=[Math.cos(pl)*Math.sin(tr),Math.cos(pl)*Math.cos(tr),-Math.sin(pl)];
      X.push(c[0],c[0]+1.6*r*l[0],null);Y.push(c[1],c[1]+1.6*r*l[1],null);Z.push(c[2],c[2]+1.6*r*l[2],null);});
    if(X.length)T.push({type:'scatter3d',mode:'lines',x:X,y:Y,z:Z,line:{color:'#2b8a3e',width:6},name:'Lineasi (plunge / trend)',hoverinfo:'name',showlegend:false});}catch(e){console.error(e);}return r0;};})();
/* jejak singkapan vein dari Map di 3D (di atas topografi) */
(function(){if(typeof imTraces!=='function')return;var _t=imTraces;imTraces=function(T,o){var r=_t.apply(this,arguments);try{if(GM.lay.im===false||VIEW2D||!mapOk())return r;
    GM.doms.forEach(function(d){if(!d.vis||imPar(d).mapo===false)return;var X=[],Y=[],Z=[];MAP.F.forEach(function(f){if(!mapIsD(f,d)||f.vis===false||!f.pts||f.pts.length<2)return;
      for(var i=1;i<f.pts.length;i++){var a=f.pts[i-1],b=f.pts[i],n=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/2));for(var j=(i===1?0:1);j<=n;j++){var t=j/n,x=a[0]+(b[0]-a[0])*t,y=a[1]+(b[1]-a[1])*t,z=mapZ(x,y,(a.length>2&&b.length>2&&a[2]!=null&&b[2]!=null)?a[2]+(b[2]-a[2])*t:null);if(z==null){X.push(null);Y.push(null);Z.push(null);continue;}X.push(x-offX);Y.push(y-offY);Z.push(z+0.3);}}X.push(null);Y.push(null);Z.push(null);});
      if(X.length>1)T.push({type:'scatter3d',mode:'lines',x:X,y:Y,z:Z,line:{color:d.col,width:7,dash:'dash'},name:d.name+' jejak singkapan (Map)',hoverinfo:'name'});});}catch(e){console.error(e);}return r;};})();
/* ringkasan basis data struktur terpadu di GM (5) */
function stDbHtml(){var c={gm:0,ref:0,map:0},nl=0,pl=0,mo=0,ml=0;STR.P.forEach(function(p){var f=stFile(p.fid);if(p.fid==='gm')c.gm++;else if(f&&f.kind==='map')c.map++;else c.ref++;if(p.pl!=null&&p.tr!=null)nl++;});
  if(mapOk()){(MAP.PF||[]).forEach(function(f){f.P.forEach(function(p){if(p[5]&&p[5].dip==null&&p[5].pl!=null)pl++;});});MAP.F.forEach(function(f){if(f.dom!=null&&f.dom!=='')mo++;if(f.lin)ml++;});}
  return '<div class="box gmstate" style="margin-top:6px"><b>Basis data struktur terpadu</b> <small>(satu tabel: dipakai RBF &#9315;, OK dinamis, Map &amp; 3D)</small><br>Bidang: '+c.gm+' flag GM &middot; '+c.ref+' Data Referensi / CSV / manual &middot; '+c.map+' pick-up Map<br>Lineasi: '+(nl+pl)+' titik'+(pl?' (termasuk '+pl+' lineasi saja dari pick-up Map)':'')+(ml?' &middot; '+ml+' garis sumbu lipatan / lineasi Map':'')+'<br>Jejak singkapan vein dari Map: '+mo+' garis</div>';}
(function(){var _s=stGmHtml;stGmHtml=function(){var h=_s.apply(this,arguments);try{h+=stDbHtml();}catch(e){console.error(e);}return h;};})();
"""


def patch(s):
    # ---- helper (sebelum imBuild) ----
    s = rep(s, "/* ---------- bangun solid satu domain ---------- */", HELPERS + "\n/* ---------- bangun solid satu domain ---------- */")
    # ---- imPts: jejak singkapan dari Map ----
    s = rep(s, "return{H:H,W:W,nc:nc,nj:nj,sn:SN,nsp:nsp,spk:Object.keys(SP)};}",
            "var MO={n:0,f:[],miss:[]};try{MO=mapOutcrop(d,P,H,W,r);}catch(e){console.error(e);}return{H:H,W:W,nc:nc,nj:nj,sn:SN,nsp:nsp,spk:Object.keys(SP),nmo:MO.n,mof:MO.f,mom:MO.miss};}")
    # ---- imKey: lineasi Map (hanya bila ada -> kunci proyek lama tetap) ----
    s = rep(s, "return imHash(JSON.stringify([5,window.STR?STR.ver:0,",
            "var _mk=window.mapGmKey?mapGmKey():'';return imHash((_mk?_mk+'#':'')+JSON.stringify([5,window.STR?STR.ver:0,")
    # ---- imTrend (gm2): lineasi tambahan dari Map ----
    s = rep(s, "function imTrend(d,P,Fr,X){if(P.vo==='off'||!window.STR||!STR.P||!STR.P.length)return null;",
            "function imTrend(d,P,Fr,X){if(P.vo==='off'||!window.STR||!STR.P)return null;var LX=[];try{LX=stLinX(d,P,X);}catch(e){console.error(e);}if(!STR.P.length&&!LX.length)return null;")
    s = rep(s, "  if(!L.length)return null;var th0=(+P.pitch||0)*rad,",
            "  var nx=0;LX.forEach(function(o){var pl=o.pl*rad,tr=o.tr*rad,l=[Math.cos(pl)*Math.sin(tr),Math.cos(pl)*Math.cos(tr),-Math.sin(pl)],ls=dot(l,Fr.u),ld=dot(l,Fr.v);if(Math.hypot(ls,ld)<0.3)return;var th=Math.atan2(ld,ls),q=imLoc(Fr,o.c.concat([0]));L.push({s:q[0],d:q[1],c2:Math.cos(2*th),s2:Math.sin(2*th),th:th*180/Math.PI,id:o.id,src:o.src});nx++;});\n"
            "  if(!L.length)return null;var th0=(+P.pitch||0)*rad,")
    s = rep(s, "fn.n=L.length;fn.L=L;", "fn.n=L.length;fn.nx=nx;fn.L=L;")
    s = rep(s, "if(VT)return imTpsRV(T,lev,VT,+P.aS||1,+P.aD||1);", "if(VT)return imTpsVB(T,lev,VT,P);")
    s = rep(s, "st:{nvt:VT?VT.n:0,", "st:{nmo:X.nmo||0,mof:X.mof||[],mom:X.mom||[],nlx:VT&&VT.nx||0,nvt:VT?VT.n:0,")
    # ---- panel RBF ----
    s = rep(s, "'<div class=imsec>Orientasi vein (strike / dip relatif)</div>'+",
            "imMapHtml(act,P,Ra)+'<div class=imsec>Orientasi vein (strike / dip relatif)</div>'+")
    s = rep(s, "(lineasi: arah shoot, striasi, sumbu lipatan) — isi di Data Referensi &rsaquo; Struktur atau kolom Plunge / Trend di CSV. ",
            "(lineasi: arah shoot, striasi, sumbu lipatan) dari basis data struktur: flag GM &#9316;, Data Referensi &rsaquo; Struktur / CSV, titik pick-up Map (kolom Plunge / Trend), dan garis sumbu lipatan / lineasi di Map. ")
    # ---- GM (5): lineasi pada flag struktur ----
    s = rep(s, "<h4>&#9316; Flag struktur (dip / dip azimuth)</h4>", "<h4>&#9316; Flag struktur (bidang + lineasi)</h4>")
    s = rep(s, "Struktur ikut membentuk solid RBF.</div>';",
            "Struktur ikut membentuk solid RBF. Isi <b>plunge / trend</b> bila ada lineasi (arah shoot, striasi, sumbu lipatan): dipakai tren pitch RBF &amp; OK dinamis.</div>';")
    s = rep(s, """<div><label>No berikut</label><input type=number step=1 value="'+STR.nx+'" onchange="STR.nx=+this.value||1"></div></div>';""",
            """<div><label>No berikut</label><input type=number step=1 value="'+STR.nx+'" onchange="STR.nx=+this.value||1"></div></div>';
  h+='<div class="g3 f"><div><label>Plunge (&deg;)</label><input type=number step=any min=0 max=90 value="'+(STR.sd.pl!=null?STR.sd.pl:'')+'" placeholder="kosong" onchange="STR.sd.pl=this.value===\\'\\'?null:+this.value"></div><div><label>Trend (&deg;)</label><input type=number step=any min=0 max=360 value="'+(STR.sd.tr!=null?STR.sd.tr:'')+'" placeholder="kosong" onchange="STR.sd.tr=this.value===\\'\\'?null:+this.value"></div><div class=hint style="align-self:end;margin:0">kosongkan bila tidak ada lineasi</div></div>';""")
    s = rep(s, "<th>No</th><th>Dip/Az</th><th>Elev</th><th></th>", "<th>No</th><th>Dip/Az</th><th>Plunge/Trend</th><th>Elev</th><th></th>")
    s = rep(s, """onchange="stSet(\\''+p.id+'\\',\\'az\\',+this.value)"></td><td>'+p.z.toFixed(0)+'</td>""",
            """onchange="stSet(\\''+p.id+'\\',\\'az\\',+this.value)"></td><td><input type=number step=any value="'+(p.pl!=null?p.pl:'')+'" placeholder="-" style="width:40px" onchange="stSet(\\''+p.id+'\\',\\'pl\\',this.value===\\'\\'?null:+this.value)">/<input type=number step=any value="'+(p.tr!=null?p.tr:'')+'" placeholder="-" style="width:46px" onchange="stSet(\\''+p.id+'\\',\\'tr\\',this.value===\\'\\'?null:+this.value)"></td><td>'+p.z.toFixed(0)+'</td>""")
    s = rep(s, "ket:STR.sd.ket,fid:'man'},o);",
            "ket:STR.sd.ket,pl:STR.sd.pl!=null&&STR.sd.tr!=null?STR.sd.pl:null,tr:STR.sd.pl!=null&&STR.sd.tr!=null?STR.sd.tr:null,fid:'man'},o);")
    # ---- Data Referensi > Struktur: sumber Map ----
    s = rep(s, "p.fid==='man'?'manual':'file'", "p.fid==='man'?'manual':((stFile(p.fid)||{}).kind==='map'?'Map':'file')")
    s = rep(s, "ditampilkan di menu <b>Map</b> dengan simbol USGS.</div>",
            "ditampilkan di menu <b>Map</b> dengan simbol USGS. Satu basis data dengan flag struktur Geological Modelling &#9316; dan titik pick-up Map yang berkolom Dip / Dip_Azimuth.</div>")
    # ---- Map: pick-up dengan kolom struktur ----
    s = rep(s, "cC=f(/^(code|kode|desc|description|ket|keterangan|feature|fitur|layer)/,4);",
            "cC=f(/^(code|kode|desc|description|ket|keterangan|feature|fitur|layer)/,4),sDp=hasH?f(/^(dip|kemiringan)$/,-1):-1,sAz=hasH?f(/^(dipaz|dipazi|dipazimuth|dipdir|dipdirection|ddir|dd|azimuth|azi|az|arahdip)$/,-1):-1,sPl=hasH?f(/^(plunge|pl|plg)$/,-1):-1,sTr=hasH?f(/^(trend|tr|plungeaz|plungeazimuth|plungedir)$/,-1):-1;")
    s = rep(s, "P.push([cI>=0?c[cI]:String(i+1),e,n,cZ>=0?num(c[cZ]):null,cC>=0?(c[cC]||'-'):'-']);",
            "var _r=[cI>=0?c[cI]:String(i+1),e,n,cZ>=0?num(c[cZ]):null,cC>=0?(c[cC]||'-'):'-'],dp=sDp>=0?num(c[sDp]):null,az=sAz>=0?num(c[sAz]):null,pl=sPl>=0?num(c[sPl]):null,tr=sTr>=0?num(c[sTr]):null,okP=dp!==null&&az!==null&&dp>=0&&dp<=90,okL=pl!==null&&tr!==null&&pl>=0&&pl<=90;"
            "if(okP||okL)_r.push({dip:okP?dp:null,az:okP?((az%360)+360)%360:null,pl:okL?pl:null,tr:okL?((tr%360)+360)%360:null});P.push(_r);")
    s = rep(s, "MAP.PF.push({id:mapId(),name:name,on:true,lab:'id',line:false,P:P});",
            "var _pf={id:mapId(),name:name,on:true,lab:'id',line:false,P:P};MAP.PF.push(_pf);var _ns=window.mapPfStr?mapPfStr(_pf):0;")
    s = rep(s, "return P.length+(bad?' ('+bad+' baris tanpa koordinat dilewati)':'');}",
            "return P.length+(bad?' ('+bad+' baris tanpa koordinat dilewati)':'')+(_ns&&(_ns.n||_ns.nl)?' - '+(_ns.n?_ns.n+' data dip / dip azimuth':'')+(_ns.n&&_ns.nl?' + ':'')+(_ns.nl?_ns.nl+' lineasi':'')+' masuk basis data struktur (dipakai RBF)':'');}")
    s = rep(s, "CSV <code>ID, East, North, RL, Code</code> (header fleksibel;",
            "CSV <code>ID, East, North, RL, Code</code>, opsional <code>Dip, Dip_Azimuth, Plunge, Trend</code> &rarr; data struktur langsung masuk basis data struktur &amp; pemodelan (header fleksibel;")
    s = rep(s, "(by[p[4]]=by[p[4]]||[]).push([p[1],p[2]]);",
            "(by[p[4]]=by[p[4]]||[]).push(p[3]!=null&&isFinite(p[3])?[p[1],p[2],p[3]]:[p[1],p[2]]);")
    # ---- Map: tipe lineasi, kotak integrasi, tanda di daftar fitur ----
    s = rep(s, "'Kontak':{c:'#212529',w:1.4,d:'solid'}};", "'Kontak':{c:'#212529',w:1.4,d:'solid'},'Lineasi / shoot':{c:'#2b8a3e',w:1.8,d:'longdash'}};")
    s = rep(s, """'<div class="g2 f"><button onclick="mapExport(\\'dxf\\')">&#8681; DXF</button>""",
            """(window.mapGmBox?mapGmBox():'')+'<div class="g2 f"><button onclick="mapExport(\\'dxf\\')">&#8681; DXF</button>""")
    s = rep(s, "<br><small>'+mapE(MAPK[f.kind])+'</small>", "<br><small>'+mapE(MAPK[f.kind])+(window.mapGmTag?mapGmTag(f):'')+'</small>")
    return s
