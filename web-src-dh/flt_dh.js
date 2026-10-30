/* ================= GC-Ex Drillhole 0.21: SESAR 3D (bidang sesar, vektor offset, waktu & urutan umur) =================
   Sesar = jejak (garis struktur Peta / koordinat manual) + dip / dip direction -> bidang 3D (jejak diperpanjang ke arah dip).
   Panjang jejak = panjang bidang searah strike (area terpengaruh); Atas / Bawah = jangkauan searah dip.
   Atribut: jenis (normal / naik / mendatar dekstral / sinistral / oblik), vektor gerak hanging wall (trend / plunge),
   offset (m, net slip), waktu (pre / syn / post mineralisasi), urutan umur (1 = tertua) & relasi "memotong".
   Integrasi (sesar aktif):
   - POST mineralisasi + offset > 0 : sampel / kontak dipulihkan (restore) mulai sesar termuda -> model & estimasi di ruang
     pulih -> hasil digeser kembali (forward). Translasi kaku searah vektor gerak (diproyeksikan ke bidang sesar).
   - Batas keras (default: post tanpa offset; opsional untuk syn / post): sampel tidak dipakai menyeberang bidang sesar.
   - SYN mineralisasi : titik-semu orientasi di bidang sesar (dalam jarak pengaruh) -> RBF vein mengikuti bidang sesar;
     di Geomodeller Stratified-Laterite: batas keras interpolasi ketebalan (growth fault).
   - PRE mineralisasi : referensi saja (ikut tergeser sesar post yang lebih muda).
   Sesar yang lebih muda menggeser bidang sesar yang lebih tua (tampilan 3D / Sayatan). */
var FLT={F:[],lay:true,op:0.35,lab:true,ver:0,sel:null,msg:''};
var FLTPAL=['#c92a2a','#5f3dc4','#1864ab','#087f5b','#e67700','#862e9c','#0b7285','#5c940d'];
var FLTTY={normal:'Normal (HW turun)',naik:'Naik / thrust (HW naik)',dex:'Mendatar dekstral',sin:'Mendatar sinistral',obl:'Oblik (trend / plunge manual)'};
var FLTTM={pre:'Pre-mineralisasi',syn:'Syn-mineralisasi',post:'Post-mineralisasi'};
function fltE(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function fltN(v,d){return v==null||!isFinite(v)?'-':(+v).toLocaleString('id-ID',{maximumFractionDigits:d==null?1:d,minimumFractionDigits:0});}
function fltId(){return 'f'+Date.now().toString(36)+Math.random().toString(36).slice(2,5);}
function fltGet(id){for(var i=0;i<FLT.F.length;i++)if(FLT.F[i].id===id)return FLT.F[i];return null;}
function fltRad(a){return(+a||0)*Math.PI/180;}
function fltDir(tr,pl){var t=fltRad(tr),p=fltRad(pl);return[Math.sin(t)*Math.cos(p),Math.cos(t)*Math.cos(p),-Math.sin(p)];}
function fltDv(f){return fltDir(f.dd,Math.max(0,Math.min(90,+f.dip||0)));}
function fltNup(f){var a=fltRad(f.dd),d=fltRad(Math.max(0,Math.min(90,+f.dip||0)));return[Math.sin(a)*Math.sin(d),Math.cos(a)*Math.sin(d),Math.cos(d)];}
function fltNorm(v){var l=Math.hypot(v[0],v[1],v[2])||1;return[v[0]/l,v[1]/l,v[2]/l];}
/* arah gerak hanging wall relatif footwall (otomatis per jenis; oblik = trend / plunge pengguna, arah "naik" membalik) */
function fltSlipTP(f){var dd=+f.dd||0,dip=+f.dip||0;if(f.ty==='normal')return{tr:dd,pl:dip,up:false};if(f.ty==='naik')return{tr:dd,pl:dip,up:true};
  if(f.ty==='dex')return{tr:(dd+90)%360,pl:0,up:false};if(f.ty==='sin')return{tr:(dd+270)%360,pl:0,up:false};return{tr:+f.str||0,pl:+f.spl||0,up:!!f.sup};}
function fltSlip(f){var o=fltSlipTP(f),v=fltDir(o.tr,o.pl);if(o.up)v=[-v[0],-v[1],-v[2]];var n=fltNup(f),k=v[0]*n[0]+v[1]*n[1]+v[2]*n[2];return fltNorm([v[0]-k*n[0],v[1]-k*n[1],v[2]-k*n[2]]);}
function fltOff(f){return f.tm==='post'?Math.max(0,+f.off||0):0;}
function fltHbOn(f){return f.hb!=null?!!f.hb:(f.tm==='post'&&!(fltOff(f)>0));}
function fltNew(o){var n=FLT.F.length;var f=Object.assign({id:fltId(),name:'F'+(n+1),col:FLTPAL[n%FLTPAL.length],on:true,tr:[],zm:'topo',z0:null,dip:70,dd:90,up:20,dn:250,tip:0,ty:'normal',str:0,spl:0,sup:false,off:0,tm:'post',age:n+1,cuts:[],hb:null,infl:30,ket:''},o||{});FLT.F.push(f);FLT.sel=f.id;return f;}
function fltDirty(geo){FLT.ver++;FLT._P=null;if(window.SA&&SA.dirty)SA.dirty();try{if(window.IM)IM.sc={};}catch(e){}try{if(window.SL)SL.R=null;}catch(e){}try{fltPanel();}catch(e){}
  if(geo!==false){try{if(window.gmDirty)gmDirty();else updatePlot();}catch(e){console.error(e);}}else{try{updatePlot();}catch(e){}}try{if(window.mapRefresh&&window.MAP&&MAP.on)mapRefresh();}catch(e){}try{if(window.PT&&PT.render)PT.render(true);}catch(e){}}
/* ---------- geometri ---------- */
function fltTopo(){try{return typeof imTopoOk==='function'&&imTopoOk();}catch(e){return false;}}
function fltZ0(f){if(f.z0!=null&&isFinite(+f.z0))return +f.z0;try{return Math.round(G.z1);}catch(e){return 0;}}
function fltTr3(f){var tz=fltTopo();return(f.tr||[]).map(function(q){var x=q[0]-offX,y=q[1]-offY,z=null;if(f.zm!=='fix'&&tz){try{z=topoZ(x,y);}catch(e){}}if(z==null||!isFinite(z))z=fltZ0(f);return[x,y,z];});}
function fltGeom(f,pcs){var dip=Math.max(0,Math.min(90,+f.dip||0)),a=fltRad(f.dd);
  var P=pcs.filter(function(p){return p.length>1;}).map(function(p){var cum=[0];for(var i=1;i<p.length;i++)cum.push(cum[i-1]+Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]));return{p:p,cum:cum,len:cum[cum.length-1]};});
  return{f:f,id:f.id,pcs:P,dv:fltDv(f),dh:[Math.sin(a),Math.cos(a)],cosd:Math.cos(fltRad(dip)),vert:dip>=89.5,up:Math.max(0,+f.up||0),dn:Math.max(1,+f.dn||1),tip:Math.max(0,+f.tip||0),s:fltSlip(f),off:fltOff(f)};}
/* posisi titik terhadap bidang: null = di luar jangkauan sesar; hw = di hanging wall; tf = faktor taper ujung */
function fltHit(g,x,y,z){var b=null,dh=g.dh;
  for(var k=0;k<g.pcs.length;k++){var pc=g.pcs[k],p=pc.p;for(var i=1;i<p.length;i++){var A=p[i-1],B=p[i],ex=B[0]-A[0],ey=B[1]-A[1],det=ex*dh[1]-dh[0]*ey;if(Math.abs(det)<1e-9)continue;
      var px=x-A[0],py=y-A[1],mu=(px*dh[1]-dh[0]*py)/det;if(mu<-1e-9||mu>1+1e-9)continue;var l=(ex*py-ey*px)/det;
      if(!b||Math.abs(l)<Math.abs(b.l))b={l:l,zt:A[2]+mu*(B[2]-A[2]),s:pc.cum[i-1]+mu*(pc.cum[i]-pc.cum[i-1]),len:pc.len};}}
  if(!b)return null;var t,hw,e;if(!g.vert){t=b.l/g.cosd;var zs=b.zt+t*g.dv[2];hw=z>zs;e=z-zs;}else{t=b.zt-z;hw=b.l>0;e=b.l;}
  if(t<-g.up||t>g.dn)return null;var tf=g.tip>0?Math.min(1,Math.min(b.s,b.len-b.s)/g.tip):1;return{hw:hw,t:t,e:e,tf:Math.max(0,tf)};}
function fltRestL(p,L){var q=[p[0],p[1],p[2]],m='';for(var k=0;k<L.length;k++){var g=L[k],h=fltHit(g,q[0],q[1],q[2]);if(h&&h.hw){var o=g.off*h.tf;q[0]-=g.s[0]*o;q[1]-=g.s[1]*o;q[2]-=g.s[2]*o;m+='1';}else m+='0';}return{p:q,m:m};}
function fltFwdL(p,L){var q=[p[0],p[1],p[2]],m='';for(var k=L.length-1;k>=0;k--){var g=L[k],h=fltHit(g,q[0],q[1],q[2]);if(h&&h.hw){var o=g.off*h.tf;q[0]+=g.s[0]*o;q[1]+=g.s[1]*o;q[2]+=g.s[2]*o;m='1'+m;}else m='0'+m;}return{p:q,m:m};}
function fltOrder(){return FLT.F.filter(function(f){return f.on!==false&&f.tr&&f.tr.length>1;}).map(function(f,i){return{f:f,i:FLT.F.indexOf(f)};}).sort(function(a,b){return(+b.f.age||0)-(+a.f.age||0)||b.i-a.i;}).map(function(o){return o.f;});}
function fltPrep(){var tk=fltTopo()?(OV.topoF&&OV.topoF.x?OV.topoF.x.length:1):0,k=FLT.ver+'|'+tk+'|'+offX;if(FLT._P&&FLT._P.k===k)return FLT._P;
  var rest=[],out={k:k,all:[],rest:rest,hb:[],syn:[]};
  fltOrder().forEach(function(f){var P3=fltTr3(f),codes=[],R3=P3.map(function(p){var o=fltRestL(p,rest);codes.push(o.m);return o.p;}),pcs=[],cur=[R3[0]];
    for(var i=1;i<R3.length;i++){if(codes[i]!==codes[i-1]){pcs.push(cur);cur=[R3[i]];}else cur.push(R3[i]);}pcs.push(cur);
    var gr=fltGeom(f,pcs);gr.younger=rest.slice();var o={f:f,gp:fltGeom(f,[P3]),gr:gr};out.all.push(o);
    if(fltHbOn(f)&&f.tm!=='pre')out.hb.push(gr);if(f.tm==='syn')out.syn.push(o);if(fltOff(f)>0)rest.push(gr);});
  FLT._P=out;return out;}
function fltAct(){var P=fltPrep();return P.rest.length+P.hb.length+P.syn.length>0;}
function fltRestore(x,y,z){var P=fltPrep();if(!P.rest.length)return[x,y,z];return fltRestL([x,y,z],P.rest).p;}
function fltForward(x,y,z){var P=fltPrep();if(!P.rest.length)return[x,y,z];return fltFwdL([x,y,z],P.rest).p;}
function fltCode(q){var P=fltPrep();if(!P.hb.length)return null;var s='';for(var k=0;k<P.hb.length;k++){var h=fltHit(P.hb[k],q[0],q[1],q[2]);s+=h?(h.hw?'1':'0'):'-';}return s;}
/* kode blok-sesar sama? ('-' = di luar jangkauan sesar itu -> tidak membatasi) */
function fltSame(a,b){if(a==null||b==null)return true;for(var i=0;i<a.length;i++){var x=a[i],y=b[i];if(x!=='-'&&y!=='-'&&x!==y)return false;}return true;}
/* titik blok present -> koordinat pulih + kode batas keras untuk filter pencarian sampel */
function fltQ(x,y,z){if(!FLT._act)return[x,y,z];var q=fltRestore(x,y,z);FLT._code=fltCode(q);return q;}
window.OKF=function(c){return !FLT._act||FLT._code==null||fltSame(c.fc,FLT._code);};
/* mesh bidang sesar (kerangka sesar itu sendiri) -> digeser sesar yang lebih muda; segitiga yang terpotong sesar muda dibuang */
function fltMesh(o){var g=o.gr,f=o.f,X=[],Y=[],Z=[],I=[],J=[],K=[],M=[],up=g.up,dn=g.dn,nt=Math.max(2,Math.min(60,Math.ceil((up+dn)/8)));
  g.pcs.forEach(function(pc){var S=[];for(var i=0;i<pc.p.length;i++){if(i){var a=pc.p[i-1],b=pc.p[i],L=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.max(1,Math.ceil(L/10));for(var j=1;j<n;j++){var t=j/n;S.push([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]);}}S.push(pc.p[i]);}
    var base=X.length,ns=S.length;S.forEach(function(s){for(var k=0;k<=nt;k++){var t=-up+(up+dn)*k/nt,p=[s[0]+t*g.dv[0],s[1]+t*g.dv[1],s[2]+t*g.dv[2]],r=g.younger.length?fltFwdL(p,g.younger):{p:p,m:''};X.push(r.p[0]);Y.push(r.p[1]);Z.push(r.p[2]);M.push(r.m);}});
    for(var i2=0;i2<ns-1;i2++)for(var k2=0;k2<nt;k2++){var a2=base+i2*(nt+1)+k2,b2=a2+nt+1,c2=b2+1,d2=a2+1;[[a2,b2,c2],[a2,c2,d2]].forEach(function(T){if(M[T[0]]!==M[T[1]]||M[T[1]]!==M[T[2]])return;I.push(T[0]);J.push(T[1]);K.push(T[2]);});}});
  return{name:f.name,col:f.col,_x:Float32Array.from(X),_y:Float32Array.from(Y),_z:Float32Array.from(Z),_i:Int32Array.from(I),_j:Int32Array.from(J),_k:Int32Array.from(K),nv:X.length,nt:I.length};}
function fltMeshes(){var P=fltPrep(),k=P.k;if(FLT._M&&FLT._M.k===k)return FLT._M.L;var L=P.all.map(function(o){return{o:o,m:fltMesh(o)};});FLT._M={k:k,L:L,sc:{}};return L;}
/* ---------- validasi urutan umur & relasi memotong ---------- */
function fltCheck(){var W=[],F=FLT.F;F.forEach(function(f){(f.cuts||[]).forEach(function(id){var g=fltGet(id);if(!g)return;if(!((+f.age||0)>(+g.age||0)))W.push(f.name+' memotong '+g.name+', tetapi urutan umurnya tidak lebih muda ('+f.age+' vs '+g.age+')');
      if(f.tm==='pre'&&g.tm!=='pre')W.push(f.name+' (pre) tidak mungkin memotong '+g.name+' ('+g.tm+')');if(f.tm==='syn'&&g.tm==='post')W.push(f.name+' (syn) tidak mungkin memotong '+g.name+' (post)');});
    if(f.tm==='post'&&!(f.tr&&f.tr.length>1))W.push(f.name+': jejak belum ada');});
  /* siklus */
  var st={},cyc=[],vis=function(f,path){if(st[f.id]===1){cyc.push(path.concat([f.name]).join(' → '));return;}if(st[f.id]===2)return;st[f.id]=1;(f.cuts||[]).forEach(function(id){var g=fltGet(id);if(g)vis(g,path.concat([f.name]));});st[f.id]=2;};
  F.forEach(function(f){vis(f,[]);});cyc.forEach(function(c){W.push('Relasi memotong melingkar: '+c);});
  var post=F.filter(function(f){return f.tm==='post';}),pre=F.filter(function(f){return f.tm!=='post';});post.forEach(function(p){pre.forEach(function(q){if((+p.age||0)<(+q.age||0))W.push(p.name+' (post) lebih tua dari '+q.name+' ('+q.tm+') — periksa urutan umur');});});
  return W;}
/* urutan umur otomatis: pre < syn < post, lalu relasi memotong (topologis), lalu urutan lama */
function fltAutoAge(){var F=FLT.F,rk={pre:0,syn:1,post:2},done={},out=[],guard=0;
  var older=function(f){return F.filter(function(g){return (g.cuts||[]).indexOf(f.id)>=0?false:(f.cuts||[]).indexOf(g.id)>=0;});};
  while(out.length<F.length&&guard++<1000){var c=F.filter(function(f){return !done[f.id]&&older(f).every(function(g){return done[g.id];});});
    if(!c.length){c=F.filter(function(f){return !done[f.id];});}c.sort(function(a,b){return rk[a.tm]-rk[b.tm]||(+a.age||0)-(+b.age||0)||F.indexOf(a)-F.indexOf(b);});var f=c[0];done[f.id]=1;out.push(f);}
  out.forEach(function(f,i){f.age=i+1;});fltDirty();}
/* ---------- tampilan 3D / Sayatan 2D / Peta ---------- */
function fltTraces(T,o){if(!FLT.lay||VIEW2D||!FLT.F.length)return;var L;try{L=fltMeshes();}catch(e){console.error(e);return;}
  L.forEach(function(q){var m=q.m,f=q.o.f;if(!m.nt)return;T.push({type:'mesh3d',name:'Sesar '+f.name+' ('+(FLTTM[f.tm]||'')+(fltOff(f)>0?', offset '+fltN(fltOff(f))+' m':'')+')',x:m._x,y:m._y,z:m._z,i:m._i,j:m._j,k:m._k,color:f.col,opacity:o&&o.clip?Math.min(0.15,FLT.op):FLT.op,flatshading:true,hoverinfo:'name',showlegend:true});
    if(o&&o.clip&&o.K){var X=[],Y=[],Z=[];fltSlice(q,o.K).forEach(function(l){l.p.forEach(function(p){X.push(p[0]);Y.push(p[1]);Z.push(p[2]);});X.push(null);Y.push(null);Z.push(null);});if(X.length)T.push({type:'scatter3d',mode:'lines',x:X,y:Y,z:Z,line:{color:f.col,width:8},name:'Sesar '+f.name+' (sayatan)',hoverinfo:'name',showlegend:false});}
    var g=q.o.gp;if(FLT.lab&&g.pcs.length){var pc=g.pcs[0].p,mid=pc[Math.floor(pc.length/2)],s=fltSlip(f),off=fltOff(f),e=Math.max(15,Math.min(60,off*3||25));
      T.push({type:'scatter3d',mode:'text',x:[mid[0]],y:[mid[1]],z:[mid[2]+6],text:[f.name+' '+Math.round(f.dip)+'/'+('00'+Math.round(f.dd)).slice(-3)],textfont:{size:11,color:f.col},hoverinfo:'skip',showlegend:false});
      if(off>0)T.push({type:'cone',x:[mid[0]],y:[mid[1]],z:[mid[2]],u:[s[0]*e],v:[s[1]*e],w:[s[2]*e],sizemode:'absolute',sizeref:Math.max(4,e*0.35),anchor:'tail',colorscale:[[0,f.col],[1,f.col]],showscale:false,name:'Vektor gerak HW '+f.name,hoverinfo:'name',showlegend:false});}});}
function fltSlice(q,K){var k=K[0],key=q.o.f.id+'|'+JSON.stringify([k.n,k.c,k.lo,k.hi]),S=FLT._M.sc;if(S[key])return S[key];var L=[];try{L=wfSlice(q.m,{n:k.n,c:k.c},(k.lo+k.hi)/2);}catch(e){}S[key]=L;return L;}
function fltTraces2D(o,F){if(!FLT.lay||!FLT.F.length||!o.K)return[];var out=[],L;try{L=fltMeshes();}catch(e){return[];}
  L.forEach(function(q){var f=q.o.f,x=[],y=[],lx=null,ly=null;fltSlice(q,o.K).forEach(function(l){l.p.forEach(function(p){var a=F(p[0],p[1],p[2]);x.push(a[0]);y.push(a[1]);if(lx==null||a[1]>ly){lx=a[0];ly=a[1];}});x.push(null);y.push(null);});
    if(!x.length)return;out.push({type:'scatter',mode:'lines',x:x,y:y,line:{color:f.col,width:3,dash:f.tm==='pre'?'dot':f.tm==='syn'?'dashdot':'solid'},name:'Sesar '+f.name,hoverinfo:'name',showlegend:true});
    if(FLT.lab)out.push({type:'scatter',mode:'text',x:[lx],y:[ly],text:[f.name+(fltOff(f)>0?' ('+fltN(fltOff(f))+' m)':'')],textposition:'top center',textfont:{size:11,color:f.col},hoverinfo:'skip',showlegend:false});});
  return out;}
function fltMapTr(){var T=[];if(!FLT.lay)return T;FLT.F.forEach(function(f){if(f.on===false||!f.tr||f.tr.length<2)return;var x=[],y=[];f.tr.forEach(function(p){x.push(p[0]);y.push(p[1]);});
    T.push({type:'scatter',mode:'lines',x:x,y:y,line:{color:f.col,width:3.4},name:'Sesar '+f.name,hoverinfo:'name',showlegend:true});
    var i=Math.floor((f.tr.length-1)/2),a=f.tr[i],b=f.tr[i+1],mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2,L=Math.max(8,Math.hypot(b[0]-a[0],b[1]-a[1])*0.12),r=fltRad(f.dd);
    T.push({type:'scatter',mode:'lines+text',x:[mx,mx+Math.sin(r)*L],y:[my,my+Math.cos(r)*L],text:['',Math.round(f.dip)+'°'],textposition:'middle right',textfont:{size:10,color:f.col},line:{color:f.col,width:2},hoverinfo:'skip',showlegend:false});
    if(FLT.lab)T.push({type:'scatter',mode:'text',x:[f.tr[0][0]],y:[f.tr[0][1]],text:[f.name+' · '+(FLTTM[f.tm]||'').replace('-mineralisasi','')+(fltOff(f)>0?' · '+fltN(fltOff(f))+' m':'')],textposition:'top left',textfont:{size:10,color:f.col},hoverinfo:'skip',showlegend:false});});return T;}
/* ---------- integrasi pemodelan ---------- */
(function(){
  /* RBF vein: kontak dipulihkan, model dibangun di ruang pulih, mesh digeser kembali; uji "di dalam solid" lewat ruang pulih */
  if(typeof imBuild==='function'){var _ib=imBuild,_wi=wfInside;
    window.wfInside=wfInside=function(m){if(m&&m._fltW)return m._fltW;return _wi.apply(this,arguments);};
    window.imBuild=imBuild=function(d,P,X){var Pp=fltPrep();if(!Pp.rest.length)return _ib.apply(this,arguments);
      var rp=function(p){var q=fltRestore(p[0],p[1],p[2]);return q.concat(p.slice(3));},X2=Object.assign({},X,{H:X.H.map(rp),W:X.W.map(rp)});
      var _tz=window.topoZ,_gx=window.getXYZ,NR;
      window.getXYZ=getXYZ=function(id,m){var p=_gx(id,m),q=fltRestore(p.x,p.y,p.z);return{x:q[0],y:q[1],z:q[2]};};
      window.topoZ=topoZ=function(x,y){var z0=_tz(x,y);if(z0==null||!isFinite(z0))return z0;var z=z0;for(var it=0;it<2;it++){var f=fltForward(x,y,z),zt=_tz(f[0],f[1]);if(zt==null||!isFinite(zt))break;z=z+(zt-f[2]);}return z;};
      try{NR=_ib.call(this,d,P,X2);}finally{window.getXYZ=getXYZ=_gx;window.topoZ=topoZ=_tz;}
      var m=NR.mesh,n=m.nv,Wr=_wi({_x:m._x,_y:m._y,_z:m._z,_i:m._i,_j:m._j,_k:m._k,nv:m.nv,nt:m.nt}),x=new Float32Array(n),y=new Float32Array(n),z=new Float32Array(n),M=new Array(n);
      for(var i=0;i<n;i++){var r=fltFwdL([m._x[i],m._y[i],m._z[i]],Pp.rest);x[i]=r.p[0];y[i]=r.p[1];z[i]=r.p[2];M[i]=r.m;}
      var I=[],J=[],K=[],cut=0;for(var t=0;t<m.nt;t++){var a=m._i[t],b=m._j[t],c=m._k[t];if(M[a]!==M[b]||M[b]!==M[c]){cut++;continue;}I.push(a);J.push(b);K.push(c);}
      m._x=x;m._y=y;m._z=z;m._i=Int32Array.from(I);m._j=Int32Array.from(J);m._k=Int32Array.from(K);m.nt=I.length;
      m._fltW={f:function(px,py,pz){var q=fltRestore(px,py,pz);return Wr.f(q[0],q[1],q[2]);},open:Wr.open||0};NR._W=m._fltW;NR.W=m._fltW;NR.st.flt={n:Pp.rest.length,cut:cut};return NR;};}
  if(typeof imKey==='function'){var _ik=imKey;window.imKey=imKey=function(){var k=_ik.apply(this,arguments),P=fltPrep();return k+'|flt:'+(P.rest.length||P.syn.length?P.k:'0');};}
  /* syn-mineralisasi: titik-semu orientasi di bidang sesar dekat data domain */
  if(typeof stForDom==='function'){var _sf=stForDom;window.stForDom=stForDom=function(d,P,X){var out=_sf.apply(this,arguments);try{if(P&&P.str===false)return out;var Pp=fltPrep();if(!Pp.syn.length)return out;
      var B=(X.H||[]).concat(X.W||[]);if(!B.length)return out;Pp.syn.forEach(function(o){var g=o.gr,R=Math.max(1,+o.f.infl||30),n=fltNup(o.f);if(n[2]<0)n=[-n[0],-n[1],-n[2]];
        g.pcs.forEach(function(pc){for(var s=0;s<=pc.len;s+=Math.max(5,R/3)){var k=1;while(k<pc.cum.length-1&&pc.cum[k]<s)k++;var a=pc.p[k-1],b=pc.p[k],u=(s-pc.cum[k-1])/Math.max(1e-9,pc.cum[k]-pc.cum[k-1]);
            for(var t=-g.up;t<=g.dn;t+=Math.max(5,R/3)){var c=[a[0]+(b[0]-a[0])*u+t*g.dv[0],a[1]+(b[1]-a[1])*u+t*g.dv[1],a[2]+(b[2]-a[2])*u+t*g.dv[2]],dm=1e18;
              for(var i=0;i<B.length;i+=Math.max(1,Math.floor(B.length/1500))){var q=B[i],e=(q[0]-c[0])*(q[0]-c[0])+(q[1]-c[1])*(q[1]-c[1])+(q[2]-c[2])*(q[2]-c[2]);if(e<dm)dm=e;}
              if(Math.sqrt(dm)<=R)out.push({c:c,n:n,id:'flt.'+o.f.id});}}});});}catch(e){console.error(e);}return out;};}
  /* Model Estimation: komposit & blok di ruang pulih, batas keras sesar */
  if(typeof meComps==='function'){var _mc=meComps;window.meComps=meComps=function(){var C=_mc.apply(this,arguments);if(!FLT._me)return C;var P=fltPrep();if(!P.rest.length&&!P.hb.length)return C;
      C.forEach(function(c){var q=fltRestore(c.x,c.y,c.z);c.x=q[0];c.y=q[1];c.z=q[2];c.fc=fltCode(q);});return C;};}
  if(typeof meRun==='function'){var _mr=meRun;window.meRun=meRun=function(){var on=!ME.job&&fltAct();FLT._me=on;FLT._act=on;try{return _mr.apply(this,arguments);}finally{FLT._me=false;if(!ME.job)FLT._act=false;}};}
  if(typeof meStep==='function'){var _ms=meStep;window.meStep=meStep=function(){var r=_ms.apply(this,arguments);if(!ME.job)FLT._act=false;return r;};}
  /* tampilan */
  if(typeof dgTraces==='function'){var _dt=dgTraces;window.dgTraces=dgTraces=function(T,o){_dt.apply(this,arguments);try{fltTraces(T,o||{});}catch(e){console.error(e);}};}
  var _b2=window.bxTraces2D;window.bxTraces2D=function(o,F){var r=_b2?_b2.apply(this,arguments):[];try{r=r.concat(fltTraces2D(o,F));}catch(e){console.error(e);}return r;};
  if(typeof mapTraces==='function'){var _mt=mapTraces;window.mapTraces=mapTraces=function(){var T=_mt.apply(this,arguments);try{T=T.concat(fltMapTr());}catch(e){console.error(e);}return T;};}
  if(typeof lyrDef==='function'){var _ld=lyrDef;window.lyrDef=lyrDef=function(){var L=_ld.apply(this,arguments),k=-1;L.forEach(function(it,i){if(it.k==='sg')k=i;});L.splice(k+1,0,{k:'flt',t:'Sesar 3D (bidang)',c:{get:function(){return FLT.lay;},set:function(v){FLT.lay=v;if(window.SA&&SA.dirty)SA.dirty();},ok:function(){return FLT.F.length>0;}}});return L;};}
  /* simpan per proyek */
  var _c=SA.collectWork;SA.collectWork=function(){var w=_c.apply(this,arguments);try{w.flt={F:FLT.F,lay:FLT.lay,op:FLT.op,lab:FLT.lab};}catch(e){}return w;};
  var _a=SA.applyWork;SA.applyWork=function(W){try{var o=W&&W.flt;FLT.F=o&&o.F?o.F:[];if(o){['lay','op','lab'].forEach(function(k){if(o[k]!=null)FLT[k]=o[k];});}FLT.ver++;FLT._P=null;FLT._M=null;FLT.sel=null;}catch(e){console.error(e);}var r=_a.apply(this,arguments);try{fltPanel();}catch(e){}return r;};
})();
/* ---------- input ---------- */
function fltFromMap(fid){var mf=(window.MAP&&MAP.F||[]).filter(function(x){return x.id===fid;})[0];if(!mf){alert('Pilih garis struktur di Peta dulu.');return;}
  var ty=/naik|thrust/i.test(mf.type||'')?'naik':/geser|mendatar|dekstral/i.test(mf.type||'')?'dex':/sinistral/i.test(mf.type||'')?'sin':'normal',p=mf.pts,a=p[0],b=p[p.length-1],az=Math.atan2(b[0]-a[0],b[1]-a[1])*180/Math.PI;
  var f=fltNew({name:(mf.name&&!/^Sesar/i.test(mf.name)?mf.name:'F'+(FLT.F.length+1)),tr:p.map(function(q){return[+q[0],+q[1]];}),ty:ty,dd:Math.round(((az+90)%360+360)%360),src:'map:'+fid,ket:mf.type||''});
  if(ty==='dex'||ty==='sin')f.dip=85;fltDirty();}
function fltManual(){var s=prompt('Jejak sesar (koordinat dunia) — X1,Y1;X2,Y2[;X3,Y3 …]','');if(!s)return;var P=s.split(';').map(function(q){var v=q.split(/[,\s]+/).filter(Boolean).map(Number);return v;}).filter(function(v){return v.length>=2&&isFinite(v[0])&&isFinite(v[1]);});
  if(P.length<2){alert('Butuh minimal 2 titik X,Y.');return;}var a=P[0],b=P[P.length-1],az=Math.atan2(b[0]-a[0],b[1]-a[1])*180/Math.PI;fltNew({tr:P.map(function(v){return[v[0],v[1]];}),dd:Math.round(((az+90)%360+360)%360)});fltDirty();}
function fltSet(id,k,v){var f=fltGet(id);if(!f)return;if(['dip','dd','up','dn','tip','str','spl','off','age','infl','z0'].indexOf(k)>=0){v=v===''||v==null?null:+v;if(v!=null&&!isFinite(v))return;}
  if(k==='dip')v=Math.max(0,Math.min(90,v||0));if(k==='dd'||k==='str')v=((v||0)%360+360)%360;if(k==='spl')v=Math.max(0,Math.min(90,v||0));f[k]=v;
  if(k==='ty'&&v==='obl'){var o=fltSlipTP(Object.assign({},f,{ty:'normal'}));f.str=Math.round(o.tr);f.spl=Math.round(o.pl);}
  fltDirty(['name','col','ket'].indexOf(k)<0);}
function fltCut(id,oid,on){var f=fltGet(id);if(!f)return;f.cuts=(f.cuts||[]).filter(function(x){return x!==oid;});if(on)f.cuts.push(oid);fltDirty();}
function fltDel(id){var f=fltGet(id);if(!f||!confirm('Hapus sesar '+f.name+'?'))return;FLT.F=FLT.F.filter(function(x){return x!==f;});FLT.F.forEach(function(g){g.cuts=(g.cuts||[]).filter(function(x){return x!==id;});});if(FLT.sel===id)FLT.sel=null;fltDirty();}
function fltFlip(id){var f=fltGet(id);if(f)fltSet(id,'dd',(f.dd+180)%360);}
function fltCsv(){var r=['Nama,Waktu,Urutan_umur,Jenis,Dip,Dip_Direction,Atas_m,Bawah_m,Taper_ujung_m,Slip_Trend,Slip_Plunge,Slip_HW_naik,Offset_m,Batas_keras,Pengaruh_syn_m,Memotong,Jejak_XY,Keterangan'];
  FLT.F.forEach(function(f){var o=fltSlipTP(f);r.push([f.name,f.tm,f.age,f.ty,f.dip,f.dd,f.up,f.dn,f.tip,Math.round(o.tr),Math.round(o.pl),o.up?1:0,fltOff(f),fltHbOn(f)?1:0,f.infl,(f.cuts||[]).map(function(i){var g=fltGet(i);return g?g.name:'';}).join(' '),(f.tr||[]).map(function(p){return(+p[0]).toFixed(2)+' '+(+p[1]).toFixed(2);}).join(' | '),f.ket||''].map(function(v){v=String(v==null?'':v);return /[,"\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}).join(','));});
  var b=new Blob(['﻿'+r.join('\r\n')],{type:'text/csv'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='sesar_3d.csv';a.click();}
function fltDxf(){var L=fltMeshes(),o=['0','SECTION','2','ENTITIES'];L.forEach(function(q){var m=q.m,ly=String(q.o.f.name).replace(/[^\w\-]/g,'_');for(var t=0;t<m.nt;t++){var V=[m._i[t],m._j[t],m._k[t],m._k[t]];o.push('0','3DFACE','8','SESAR_'+ly);V.forEach(function(v,c){o.push(String(10+c),(m._x[v]+offX).toFixed(3),String(20+c),(m._y[v]+offY).toFixed(3),String(30+c),(+m._z[v]).toFixed(3));});}});o.push('0','ENDSEC','0','EOF');
  var b=new Blob([o.join('\r\n')],{type:'application/dxf'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='sesar_3d.dxf';a.click();}
/* ---------- panel ---------- */
function fltPanel(){var b=$('fltBody');if(!b)return;var F=FLT.F,sel=fltGet(FLT.sel),MF=(window.MAP&&MAP.F||[]).filter(function(x){return x.kind==='str'&&x.pts&&x.pts.length>1;});
  var h='<div class=hint style="margin:-4px 0 8px">Sesar sebagai <b>bidang 3D</b>: jejak (garis struktur di Peta atau koordinat) + dip / dip direction. Panjang bidang searah strike = panjang jejak digitasi. '+
    '<b>Post</b>-mineralisasi dengan offset: data dipulihkan dulu (mulai sesar termuda), lalu model vein / lapisan &amp; estimasi digeser kembali. <b>Syn</b>: bidang sesar mengontrol orientasi vein. <b>Pre</b>: referensi.</div>';
  h+='<h4>Buat sesar</h4><div class="g2 f"><select id=fltMapSel>'+(MF.length?MF.map(function(m){return '<option value="'+m.id+'">'+fltE((m.type||'Struktur')+(m.name&&m.name!==m.type?' · '+m.name:''))+' ('+m.pts.length+' titik)</option>';}).join(''):'<option value="">(belum ada garis struktur di Peta)</option>')+'</select>'+
    '<button class=btn-pri onclick="fltFromMap($(\'fltMapSel\').value)"'+(MF.length?'':' disabled')+'>+ Dari garis Peta</button></div>'+
    '<div class="g2 f"><button onclick="uiTab(\'Map\');try{MAP.kind=\'str\';mapPanel();}catch(e){}" title="Digitasi garis struktur (jenis Sesar …) di Peta, lalu kembali ke sini">&#9998; Digitasi jejak di Peta</button><button onclick="fltManual()">+ Koordinat manual</button></div>';
  h+='<h4>Daftar sesar ('+F.length+')</h4>';
  if(F.length){h+='<div class=gmlist><table class=pltb><tr><th></th><th>Nama</th><th>Waktu</th><th>Umur</th><th>Dip/DD</th><th>Offset</th></tr>'+F.map(function(f){return '<tr class="'+(f.id===FLT.sel?'on':'')+'" style="cursor:pointer" onclick="FLT.sel=\''+f.id+'\';fltPanel()"><td><input type=checkbox '+(f.on!==false?'checked':'')+' onclick="event.stopPropagation()" onchange="fltSet(\''+f.id+'\',\'on\',this.checked)"></td><td><span style="display:inline-block;width:9px;height:9px;border-radius:2px;background:'+f.col+';margin-right:4px"></span><b>'+fltE(f.name)+'</b></td><td>'+fltE(f.tm)+'</td><td>'+fltE(f.age)+'</td><td>'+Math.round(f.dip)+'/'+('00'+Math.round(f.dd)).slice(-3)+'</td><td>'+(f.tm==='post'?fltN(f.off):'-')+'</td></tr>';}).join('')+'</table></div>';
    h+='<div class="g2 f"><button onclick="fltAutoAge()" title="pre &lt; syn &lt; post, lalu sesar yang memotong lebih muda dari yang dipotong">&#8645; Urutkan umur otomatis</button><button onclick="fltCsv()">&#8681; CSV</button></div>'+
      '<div class="g3 f"><label class=sw style="margin:0"><input type=checkbox '+(FLT.lay?'checked':'')+' onchange="FLT.lay=this.checked;fltDirty(false)">Tampil</label><label class=sw style="margin:0"><input type=checkbox '+(FLT.lab?'checked':'')+' onchange="FLT.lab=this.checked;fltDirty(false)">Label</label><button onclick="fltDxf()">&#8681; DXF bidang</button></div>'+
      '<div class=f><label>Transparansi bidang</label><input type=range min=0.05 max=0.9 step=0.05 value="'+FLT.op+'" onchange="FLT.op=+this.value;fltDirty(false)"></div>';}
  else h+='<div class=hint>Belum ada sesar.</div>';
  if(sel){var id=sel.id,inp=function(k,v,st,w){return '<input type=number step="'+(st||'any')+'" value="'+(v==null?'':v)+'" style="width:'+(w||'100%')+'" onchange="fltSet(\''+id+'\',\''+k+'\',this.value)">';},opt=function(o,cur){return Object.keys(o).map(function(k){return '<option value="'+k+'"'+(k===cur?' selected':'')+'>'+o[k]+'</option>';}).join('');},tp=fltSlipTP(sel);
    h+='<h4>Atribut sesar: '+fltE(sel.name)+'</h4>'+
      '<div class="g2 f"><div><label>Nama</label><input type=text value="'+fltE(sel.name)+'" onchange="fltSet(\''+id+'\',\'name\',this.value)"></div><div><label>Warna</label><input type=color value="'+sel.col+'" onchange="fltSet(\''+id+'\',\'col\',this.value)"></div></div>'+
      '<div class="g2 f"><div><label>Waktu terhadap mineralisasi</label><select onchange="fltSet(\''+id+'\',\'tm\',this.value)">'+opt(FLTTM,sel.tm)+'</select></div><div><label>Urutan umur (1 = tertua)</label>'+inp('age',sel.age,1)+'</div></div>'+
      '<div class="g2 f"><div><label>Dip (&deg;)</label>'+inp('dip',sel.dip)+'</div><div><label>Dip direction (&deg;) <a href="#" onclick="fltFlip(\''+id+'\');return false" title="Balik arah kemiringan">&#8646;</a></label>'+inp('dd',sel.dd)+'</div></div>'+
      '<div class="g3 f"><div><label>Atas jejak (m)</label>'+inp('up',sel.up)+'</div><div><label>Bawah / searah dip (m)</label>'+inp('dn',sel.dn)+'</div><div><label title="Offset mengecil linear ke nol di ujung jejak sepanjang jarak ini (0 = offset penuh sampai ujung)">Taper ujung (m)</label>'+inp('tip',sel.tip)+'</div></div>'+
      '<div class="g2 f"><div><label>Jenis</label><select onchange="fltSet(\''+id+'\',\'ty\',this.value)">'+opt(FLTTY,sel.ty)+'</select></div><div><label>Offset / net slip (m)</label>'+(sel.tm==='post'?inp('off',sel.off):'<input disabled value="hanya post">')+'</div></div>';
    if(sel.ty==='obl')h+='<div class="g3 f"><div><label>Trend gerak (&deg;)</label>'+inp('str',sel.str)+'</div><div><label>Plunge gerak (&deg;)</label>'+inp('spl',sel.spl)+'</div><div><label>HW bergerak</label><select onchange="fltSet(\''+id+'\',\'sup\',this.value===\'1\')"><option value=0'+(sel.sup?'':' selected')+'>searah plunge (turun)</option><option value=1'+(sel.sup?' selected':'')+'>berlawanan (naik)</option></select></div></div>';
    else h+='<div class=hint>Vektor gerak HW: trend '+Math.round(tp.tr)+'&deg; / plunge '+Math.round(tp.pl)+'&deg;'+(tp.up?' (HW naik)':'')+'. Pilih <b>Oblik</b> untuk mengisi trend / plunge garis gores sendiri.</div>';
    h+='<div class="g2 f"><label class=sw style="margin:0" title="Sampel tidak dipakai menyeberang bidang sesar ini (estimasi vein & interpolasi lapisan)"><input type=checkbox '+(fltHbOn(sel)?'checked':'')+(sel.tm==='pre'?' disabled':'')+' onchange="fltSet(\''+id+'\',\'hb\',this.checked)">Batas keras</label>'+
      (sel.tm==='syn'?'<div><label>Jarak pengaruh syn (m)</label>'+inp('infl',sel.infl)+'</div>':'<span></span>')+'</div>'+
      '<div class="g2 f"><div><label>Elevasi jejak</label><select onchange="fltSet(\''+id+'\',\'zm\',this.value)"><option value=topo'+(sel.zm!=='fix'?' selected':'')+'>Topografi aktif</option><option value=fix'+(sel.zm==='fix'?' selected':'')+'>Tetap (Z)</option></select></div><div><label>Z tetap / tanpa topo</label>'+inp('z0',sel.z0!=null?sel.z0:fltZ0(sel))+'</div></div>';
    var oth=F.filter(function(g){return g!==sel;});
    if(oth.length)h+='<div class=f><label>Memotong (sesar yang lebih tua)</label><div class=chips>'+oth.map(function(g){var on=(sel.cuts||[]).indexOf(g.id)>=0;return '<label class=sw style="margin:0 8px 0 0;display:inline-flex"><input type=checkbox '+(on?'checked':'')+' onchange="fltCut(\''+id+'\',\''+g.id+'\',this.checked)">'+fltE(g.name)+'</label>';}).join('')+'</div></div>';
    h+='<div class=f><label>Keterangan</label><input type=text value="'+fltE(sel.ket||'')+'" onchange="fltSet(\''+id+'\',\'ket\',this.value)"></div>'+
      '<div class=hint>Jejak: '+(sel.tr||[]).length+' titik, panjang '+fltN((function(){var L=0,p=sel.tr||[];for(var i=1;i<p.length;i++)L+=Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]);return L;})(),0)+' m.</div>'+
      '<button class=danger style="width:100%" onclick="fltDel(\''+id+'\')">Hapus sesar</button>';}
  var W=fltCheck(),P=fltPrep();h+='<h4>Pengaruh ke pemodelan</h4><div class="box gmstate">'+
    P.rest.length+' sesar post dengan offset (dipulihkan: '+P.rest.map(function(g){return fltE(g.f.name);}).join(' → ')+(P.rest.length?' , termuda dulu':'')+')<br>'+
    P.hb.length+' batas keras · '+P.syn.length+' sesar syn (kontrol orientasi vein)<br><span class=hint>Berlaku di Geomodeller Vein (solid RBF), Model Estimation, dan Geomodeller Stratified-Laterite.</span></div>'+
    (W.length?'<div class=warn style="margin-top:6px">&#9888; '+W.map(fltE).join('<br>&#9888; ')+'</div>':'');
  b.innerHTML=h;}
