/* ================= GC-Ex Drillhole 0.21: GEOMODELLER STRATIFIED-LATERITE DEPOSIT =================
   Untuk endapan berlapis mengikuti permukaan (laterit Ni / bauksit) dan stratiform (sedex):
   Lapisan  : urutan lapisan atas -> bawah dari kode log geologi (Limonit / Saprolit / Bedrock …), densitas & kadar air.
   Permukaan: kontak bor -> grid 2D: atap (topografi / kontak) lalu ketebalan per lapisan (isopach, ditumpuk ke bawah)
                atau elevasi langsung (urutan dipaksa). Interpolasi IDW anisotropis-bebas, ekstrapolasi dibatasi jarak.
                Sesar 3D: post + offset -> kontak dipulihkan dulu, permukaan digeser kembali (terpotong di bidang sesar);
                batas keras / syn (growth fault) -> interpolasi tidak menyeberang sesar.
   Estimasi : per lapisan di koordinat UNFOLD (proporsional di antara atap & lantai lapisan, atau kedalaman dari atap)
                - 3D blok (OK / IDW) atau 2D akumulasi (ketebalan × kadar, untuk lapisan tipis / sedex). Multi-unsur.
   Laporan  : volume, WMT, DMT (kadar air), kadar rata-rata (basis kering), rasio unsur (mis. SiO2/MgO), cut-off.
   Hasil ke block model GC aktif sebagai atribut sl_lapisan, sl_<unsur>, sl_pass, sl_ns (+ sl_rasio). */
var SL={ci:-1,L:[],o:{cell:5,ext:30,p:2,nmax:12,top:'auto',sm:'tebal',base:true,comp:1,el:[],ra:'',rb:'',cut:0,pel:''},R:null,S:null,job:null,msg:'',lay:true,op:0.5,ctc:true,ver:0};
var SLPAL=['#c2410c','#a16207','#65a30d','#0f766e','#1d4ed8','#7c3aed','#be185d','#57534e'];
var SLPRE={
  lat:{t:'Laterit nikel',L:[{name:'Limonit',k:/LIM|LIMO/i,dens:1.6,moist:35},{name:'Saprolit',k:/SAP/i,dens:1.65,moist:30},{name:'Bedrock',k:/BED|BRK|^BR$|FRESH|PERID|ULTRA|HARZ|DUNIT/i,dens:2.4,moist:5}],base:true},
  bx:{t:'Bauksit',L:[{name:'Overburden',k:/^OB|OVERB|SOIL|TOP/i,dens:1.5,moist:25},{name:'Bauksit',k:/BX|BAUX/i,dens:1.9,moist:15},{name:'Kaolin / lempung',k:/KAOL|CLAY|LEMP|^CL/i,dens:1.8,moist:20},{name:'Batuan dasar',k:/BED|BRK|GRAN|FRESH|BASAL/i,dens:2.5,moist:3}],base:true},
  sdx:{t:'Stratiform (sedex)',L:[{name:'Hanging wall',k:/^HW|HANG/i,dens:2.6,moist:2},{name:'Lapisan bijih',k:/ORE|MSU|SULF|SEDEX|^MS/i,dens:3.4,moist:1},{name:'Footwall',k:/^FW|FOOT/i,dens:2.6,moist:2}],base:false}};
function slE(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function slN(v,d){return v==null||!isFinite(v)?'-':(+v).toLocaleString('id-ID',{maximumFractionDigits:d==null?1:d,minimumFractionDigits:0});}
function slEstDef(base){return{on:!base,mode:'3d',met:'ok',az:0,r1:60,r2:60,r3:3,nug:0.2,nmin:3,nmax:16,mph:4,unf:'prop',p:2};}
function slNewL(o,i){return Object.assign({id:'l'+Date.now().toString(36)+Math.random().toString(36).slice(2,5),name:'Lapisan '+(i+1),col:SLPAL[i%SLPAL.length],codes:[],dens:1.8,moist:20,vis:true,est:slEstDef(false)},o||{});}
function slCats(){var o=[];(window.CAT||[]).forEach(function(c,i){if(c.src==='g'||c.src==='a')o.push(i);});return o;}
function slDict(ci){var C=CAT[ci];return C&&C.d?C.d:[];}
function slCodeName(ci,c){try{return geoName(ci,c);}catch(e){var d=slDict(ci);return d[c]!=null?d[c]:String(c);}}
function slDirty(keepR){SL.ver++;if(!keepR)SL.R=null;if(window.SA&&SA.dirty)SA.dirty();try{slPanel();}catch(e){}try{updatePlot();}catch(e){}try{if(window.PT&&PT.render)PT.render(true);}catch(e){}}
function slFlt(){return typeof fltPrep==='function'?fltPrep():{rest:[],hb:[]};}
function slRest(x,y,z){return typeof fltRestore==='function'?fltRestore(x,y,z):[x,y,z];}
function slCode(q){return typeof fltCode==='function'?fltCode(q):null;}
function slSame(a,b){return typeof fltSame==='function'?fltSame(a,b):true;}
/* ---------- data kontak per hole ---------- */
function slData(){var ci=SL.ci,L=SL.L,nl=L.length,H=[];if(ci<0||!CAT[ci]||!nl)return H;var cm={};L.forEach(function(l,i){(l.codes||[]).forEach(function(c){cm[c]=i;});});
  Object.keys(holeData).forEach(function(id){var h=holeData[id],T=L.map(function(){return null;});
    geoIntervals(ci,id).forEach(function(v){var i=cm[v[2]];if(i==null)return;var f=v[0],t=Math.min(v[1],h.maxD);if(!(t>f))return;var o=T[i];if(!o)T[i]={f:f,t:t};else{o.f=Math.min(o.f,f);o.t=Math.max(o.t,t);}});
    if(!T.some(Boolean))return;var rec={id:id,L:[]};
    for(var i=0;i<nl;i++){var o=T[i],r=null;if(o)r={f:o.f,t:o.t,pres:1};else{for(var j=i+1;j<nl;j++)if(T[j]){r={f:T[j].f,t:T[j].f,pres:0};break;}}
      if(r){r.cens=r.pres&&r.t>=h.maxD-0.05&&!(SL.o.base&&i===nl-1);var a=getXYZ(id,r.f),b=getXYZ(id,r.t),FR=slFlt().rest,qa=FR.length?fltRestL([a.x,a.y,a.z],FR):{p:[a.x,a.y,a.z],m:''},qb=FR.length?fltRestL([b.x,b.y,b.z],FR):{p:[b.x,b.y,b.z],m:''},ra=qa.p,rb=qb.p;
        /* atap & lantai di blok sesar berbeda (lapisan terpotong sesar di dalam hole): kontak tetap dipakai, ketebalan tidak */
        if(qa.m!==qb.m){r.split=1;r.cens=true;}
        r.x=(ra[0]+rb[0])/2;r.y=(ra[1]+rb[1])/2;r.zt=ra[2];r.zb=rb[2];r.T=Math.max(0,ra[2]-rb[2]);r.pt=[a.x,a.y,a.z];r.pb=[b.x,b.y,b.z];r.c=slCode([r.x,r.y,(r.zt+r.zb)/2]);}
      rec.L.push(r);}
    H.push(rec);});return H;}
/* ---------- interpolasi grid (IDW, tetangga terdekat, batas keras sesar) ---------- */
function slIdx(D,B){var M={};D.forEach(function(d,i){var k=Math.floor(d.x/B)+'_'+Math.floor(d.y/B);(M[k]||(M[k]=[])).push(i);});return{B:B,M:M};}
function slNear(D,I,x,y,n,code,maxR){var B=I.B,ci=Math.floor(x/B),cj=Math.floor(y/B),best=[],r=0,lim=Math.max(2,Math.ceil((maxR||1e9)/B)+1);
  while(r<=lim){for(var i=ci-r;i<=ci+r;i++)for(var j=cj-r;j<=cj+r;j++){if(Math.max(Math.abs(i-ci),Math.abs(j-cj))!==r)continue;var L=I.M[i+'_'+j];if(!L)continue;
      for(var t=0;t<L.length;t++){var d=D[L[t]];if(code!=null&&!slSame(d.c,code))continue;var e=Math.hypot(d.x-x,d.y-y);if(best.length<n)best.push([e,d]);else if(e<best[n-1][0])best[n-1]=[e,d];else continue;best.sort(function(a,b){return a[0]-b[0];});}}
    if(best.length>=n&&best[best.length-1][0]<=r*B)break;r++;if(r>400)break;}return best;}
function slIdw(D,I,x,y,code){var o=SL.o,N=slNear(D,I,x,y,Math.max(1,+o.nmax||12),code);if(!N.length&&code!=null)N=slNear(D,I,x,y,Math.max(1,+o.nmax||12),null);if(!N.length)return NaN;
  if(N[0][0]<1e-6)return N[0][1].v;var sw=0,sv=0,p=Math.max(0.5,+o.p||2);N.forEach(function(q){var w=1/Math.pow(q[0],p);sw+=w;sv+=w*q[1].v;});return sv/sw;}
function slBuild(){var t0=performance.now(),H=slData(),L=SL.L,nl=L.length,o=SL.o;if(nl<1)throw new Error('belum ada lapisan');if(!H.length)throw new Error('tidak ada hole yang menembus kode lapisan (periksa kolom geologi & kode)');
  var hasB=!!o.base&&nl>1,nT=hasB?nl-1:nl,F=slFlt();
  var all=[];H.forEach(function(h){h.L.forEach(function(r){if(r)all.push(r);});});
  var x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;all.forEach(function(r){x0=Math.min(x0,r.x);x1=Math.max(x1,r.x);y0=Math.min(y0,r.y);y1=Math.max(y1,r.y);});
  var ext=Math.max(0,+o.ext||30),cell=Math.max(0.5,+o.cell||5);x0-=ext;x1+=ext;y0-=ext;y1+=ext;while(((x1-x0)/cell+1)*((y1-y0)/cell+1)>160000)cell*=1.25;
  var nx=Math.max(2,Math.ceil((x1-x0)/cell)+1),ny=Math.max(2,Math.ceil((y1-y0)/cell)+1),N=nx*ny;
  /* atap dari topografi: kedalaman kontak di bawah topo (present); dengan sesar post: node pulih -> posisi present -> topo, dikurangi geseran */
  var useTopo=(o.top==='topo'||o.top==='auto')&&typeof imTopoOk==='function'&&imTopoOk();
  var D0=H.map(function(h){var r=h.L[0];if(!r)return null;var v=r.zt;if(useTopo){var z=null;try{z=topoZ(r.pt[0],r.pt[1]);}catch(e){}if(z==null||!isFinite(z))return null;v=Math.max(0,z-r.pt[2]);}return{x:r.x,y:r.y,v:v,c:r.c};}).filter(Boolean);
  if(!D0.length)throw new Error('kontak atap lapisan pertama tidak ada');
  var all2=D0.map(function(d){return{x:d.x,y:d.y};}),IH=slIdx(all2,Math.max(cell*2,ext||10)),I0=slIdx(D0,Math.max(cell*2,10));
  /* mask: dalam jarak ekstrapolasi dari hole */
  var mask=new Uint8Array(N),ZR=new Float64Array(N).fill(NaN),gx=function(i){return x0+i*cell;},gy=function(j){return y0+j*cell;};
  var DZ=H.map(function(h){var r=h.L[0];return r?{x:r.x,y:r.y,v:r.zt,c:null}:null;}).filter(Boolean),IZ=slIdx(DZ,Math.max(cell*2,10));
  for(var j=0;j<ny;j++)for(var i=0;i<nx;i++){var k=j*nx+i,x=gx(i),y=gy(j),nn=slNear(all2,IH,x,y,1,null,ext+cell);if(!nn.length||nn[0][0]>ext+1e-6)continue;mask[k]=1;ZR[k]=slIdw(DZ,IZ,x,y,null);}
  var code=new Array(N);for(k=0;k<N;k++)code[k]=mask[k]&&F.hb&&F.hb.length?slCode([gx(k%nx),gy(Math.floor(k/nx)),ZR[k]]):null;
  var S=[],st=[];for(var s=0;s<=nT;s++)S.push(new Float64Array(N).fill(NaN));
  for(k=0;k<N;k++){if(!mask[k])continue;var xx=gx(k%nx),yy=gy(Math.floor(k/nx)),v0=slIdw(D0,I0,xx,yy,code[k]);if(useTopo){var tz=null,sh=0;try{if(F.rest.length&&isFinite(ZR[k])){var fw=fltForward(xx,yy,ZR[k]-v0);sh=fw[2]-(ZR[k]-v0);tz=topoZ(fw[0],fw[1]);}else tz=topoZ(xx,yy);}catch(e){}S[0][k]=(tz!=null&&isFinite(tz))?tz-v0-sh:ZR[k];}else S[0][k]=v0;}
  for(var l=0;l<nT;l++){var Dt=[],De=[];H.forEach(function(h){var r=h.L[l];if(!r)return;if(!r.cens)Dt.push({x:r.x,y:r.y,v:r.T,c:r.c});var rb=h.L[l+1];if(!r.cens||!r.pres||r.split)De.push({x:r.x,y:r.y,v:r.zb,c:r.c});});
    var It=slIdx(Dt.length?Dt:[{x:0,y:0}],Math.max(cell*2,10)),Ie=slIdx(De.length?De:[{x:0,y:0}],Math.max(cell*2,10)),tm=0,tn=1e18,tx=0;Dt.forEach(function(d){tm+=d.v;tn=Math.min(tn,d.v);tx=Math.max(tx,d.v);});
    st.push({n:Dt.length,nc:H.filter(function(h){return h.L[l]&&h.L[l].cens;}).length,np:H.filter(function(h){return h.L[l]&&h.L[l].pres;}).length,ns:H.filter(function(h){return h.L[l]&&h.L[l].split;}).length,tav:Dt.length?tm/Dt.length:0,tmin:Dt.length?tn:0,tmax:tx});
    for(k=0;k<N;k++){if(!mask[k])continue;var a=S[l][k],xk=gx(k%nx),yk=gy(Math.floor(k/nx)),b;
      if(o.sm==='elev'&&De.length)b=Math.min(a,slIdw(De,Ie,xk,yk,code[k]));else{var t=Dt.length?slIdw(Dt,It,xk,yk,code[k]):0;b=a-Math.max(0,isFinite(t)?t:0);}S[l+1][k]=b;}}
  var vol=[];for(l=0;l<nT;l++){var v=0;for(k=0;k<N;k++)if(mask[k]&&isFinite(S[l][k])&&isFinite(S[l+1][k]))v+=Math.max(0,S[l][k]-S[l+1][k])*cell*cell;vol.push(v);}
  var R={x0:x0,y0:y0,cell:cell,nx:nx,ny:ny,mask:mask,S:S,nT:nT,hasB:hasB,H:H,st:st,vol:vol,nh:H.length,topo:useTopo,nRest:F.rest.length,nHb:(F.hb||[]).length,ms:0};
  R.M=S.map(function(Sk,q){return slMesh(R,Sk,q);});R.ms=performance.now()-t0;R.sig=slSig();return R;}
function slSig(){return JSON.stringify([SL.ci,SL.L.map(function(l){return[l.codes,l.id];}),SL.o.cell,SL.o.ext,SL.o.p,SL.o.nmax,SL.o.top,SL.o.sm,SL.o.base,window.FLT?FLT.ver:0,window.holeData?Object.keys(holeData).length:0]);}
function slMesh(R,Sk,q){var nx=R.nx,ny=R.ny,N=nx*ny,ix=new Int32Array(N).fill(-1),X=[],Y=[],Z=[],M=[],F=slFlt();
  for(var k=0;k<N;k++){var x=R.x0+(k%nx)*R.cell,y=R.y0+Math.floor(k/nx)*R.cell,z=Sk[k];if(!isFinite(z))continue;ix[k]=X.length;
    if(F.rest.length){var r=fltFwdL([x,y,z],F.rest);X.push(r.p[0]);Y.push(r.p[1]);Z.push(r.p[2]);M.push(r.m);}else{X.push(x);Y.push(y);Z.push(z);M.push('');}}
  var I=[],J=[],K=[],ok=function(a,b,c){a=ix[a];b=ix[b];c=ix[c];if(a<0||b<0||c<0||M[a]!==M[b]||M[b]!==M[c])return false;I.push(a);J.push(b);K.push(c);return true;};
  for(var j=0;j<ny-1;j++)for(var i=0;i<nx-1;i++){var a=j*nx+i,b=a+1,c=a+nx+1,d=a+nx;ok(a,b,c);ok(a,c,d);}
  return{name:slSurfName(q),_x:Float32Array.from(X),_y:Float32Array.from(Y),_z:Float32Array.from(Z),_i:Int32Array.from(I),_j:Int32Array.from(J),_k:Int32Array.from(K),nv:X.length,nt:I.length};}
function slSurfName(q){var L=SL.L;if(q<L.length&&q<(SL.R?SL.R.nT:L.length))return 'Atap '+(L[q]?L[q].name:'');if(SL.o.base&&L.length>1)return 'Atap '+L[L.length-1].name;return 'Lantai '+(L[L.length-1]?L[L.length-1].name:'');}
function slEnsure(){if(SL.R&&SL.R.sig===slSig())return SL.R;try{SL.R=slBuild();SL.err='';}catch(e){SL.R=null;SL.err=e.message;}return SL.R;}
function slAt(R,Sk,x,y){var fx=(x-R.x0)/R.cell,fy=(y-R.y0)/R.cell,i=Math.floor(fx),j=Math.floor(fy);if(i<0||j<0||i>=R.nx-1||j>=R.ny-1){i=Math.max(0,Math.min(R.nx-1,Math.round(fx)));j=Math.max(0,Math.min(R.ny-1,Math.round(fy)));if(Math.abs(fx-i)>1||Math.abs(fy-j)>1)return NaN;var v=Sk[j*R.nx+i];return v;}
  var u=fx-i,v2=fy-j,W=[[(1-u)*(1-v2),j*R.nx+i],[u*(1-v2),j*R.nx+i+1],[(1-u)*v2,(j+1)*R.nx+i],[u*v2,(j+1)*R.nx+i+1]],sw=0,s=0;W.forEach(function(q){var z=Sk[q[1]];if(isFinite(z)&&q[0]>0){sw+=q[0];s+=q[0]*z;}});return sw>1e-9?s/sw:NaN;}
/* lapisan pada titik present (koordinat lokal): {k, top, bot, q (koordinat pulih)} atau null */
function slLayerAt(R,x,y,z){var q=slRest(x,y,z),t=slAt(R,R.S[0],q[0],q[1]);if(!isFinite(t)||q[2]>t)return null;
  for(var k=0;k<R.nT;k++){var a=slAt(R,R.S[k],q[0],q[1]),b=slAt(R,R.S[k+1],q[0],q[1]);if(!isFinite(b))return null;if(q[2]>b)return{k:k,top:a,bot:b,q:q};}
  if(R.hasB)return{k:SL.L.length-1,top:slAt(R,R.S[R.nT],q[0],q[1]),bot:-1e9,q:q};return null;}
/* ---------- estimasi ---------- */
function slMo(e,two){if(e.m&&e.m.vM){var M=e.m,o={vM:M.vM.slice(),vS:M.vS.slice(),vN:two?[0,0,1]:M.vN.slice(),c0:+M.c0,cs:M.cs.map(Number),A:M.A.map(Number),B:M.B.map(Number),Cn:two?M.Cn.map(function(){return 1;}):M.Cn.map(Number)};o.R=[Math.max.apply(null,o.A),Math.max.apply(null,o.B),Math.max.apply(null,o.Cn)];return o;}
  var a=(+e.az||0)*Math.PI/180,c0=Math.max(0,Math.min(0.95,+e.nug||0));return{vM:[Math.sin(a),Math.cos(a),0],vS:[Math.sin(a+Math.PI/2),Math.cos(a+Math.PI/2),0],vN:[0,0,1],c0:c0,cs:[1-c0],A:[Math.max(1,+e.r1||50)],B:[Math.max(1,+e.r2||50)],Cn:[two?1:Math.max(0.2,+e.r3||3)],R:[Math.max(1,+e.r1||50),Math.max(1,+e.r2||50),two?1:Math.max(0.2,+e.r3||3)]};}
function slEls(){var E=(window.elements||[]);var L=(SL.o.el||[]).filter(function(e){return E.indexOf(e)>=0;});if(!L.length&&E.length)L=E.slice(0,Math.min(6,E.length));return L;}
function slIsBase(k){return !!SL.o.base&&SL.L.length>1&&k===SL.L.length-1;}
function slComps(R,k,els){var l=SL.L[k],e=l.est,unf=slIsBase(k)?'top':e.unf,cl=Math.max(0,+SL.o.comp||0),EI=els.map(function(x){return elements.indexOf(x);}),C=[],Tm=0,nT=0;
  R.H.forEach(function(h){var r=h.L[k];if(r&&r.pres&&r.T>0){Tm+=r.T;nT++;}});var Tref=nT?Math.max(0.5,Tm/nT):1;
  R.H.forEach(function(h){var r=h.L[k];if(!r||!r.pres||!(r.t>r.f))return;var A=(groupedAssays[h.id]||[]).filter(function(a){return a[2]>a[1]&&a[2]>r.f&&a[1]<r.t;});if(!A.length)return;
    var segs=[];if(e.mode==='2d'||cl<=0)segs=[[r.f,r.t]];else{var n=Math.max(1,Math.round((r.t-r.f)/cl));for(var q=0;q<n;q++)segs.push([r.f+(r.t-r.f)*q/n,r.f+(r.t-r.f)*(q+1)/n]);}
    segs.forEach(function(sg){var len=0,V=EI.map(function(){return[0,0];});A.forEach(function(a){var o=Math.min(sg[1],a[2])-Math.max(sg[0],a[1]);if(o<=0)return;len+=o;EI.forEach(function(ei,q){var v=a[4][ei];if(v!=null&&isFinite(v)){V[q][0]+=o*v;V[q][1]+=o;}});});
      if(len<0.5*(sg[1]-sg[0])-1e-9)return;var vals=V.map(function(w,q){var v=w[1]>0?w[0]/w[1]:NaN,tc=e.tc?+e.tc[els[q]]:0;return tc>0&&isFinite(v)?Math.min(v,tc):v;});var p=getXYZ(h.id,(sg[0]+sg[1])/2),q2=slRest(p.x,p.y,p.z),z;
      if(e.mode==='2d'){C.push({id:h.id,x:r.x,y:r.y,z:0,T:r.T,v:vals,fc:r.c,f:sg[0],t:sg[1],len:sg[1]-sg[0]});return;}
      var th=r.zt-r.zb;z=unf==='top'?r.zt-q2[2]:(th>0.01?(r.zt-q2[2])/th*Tref:Tref/2);C.push({id:h.id,x:q2[0],y:q2[1],z:z,v:vals,fc:r.c,f:sg[0],t:sg[1],len:sg[1]-sg[0]});});});
  C.Tref=Tref;return C;}
function slRun(){if(SL.job){SL.job.cancel=true;return;}var m=window.BX&&BX.m;if(!m){alert('Import block model GC dulu (menu Block Model).');return;}try{meEnsure();}catch(e){}
  var R=slEnsure();if(!R){alert('Permukaan lapisan belum bisa dibangun: '+(SL.err||''));return;}var els=slEls();if(!els.length){alert('Database assay belum punya unsur.');return;}
  var P=[],X={};SL.L.forEach(function(l,k){if(!l.est||!l.est.on)return;var C=slComps(R,k,els);if(C.length<1){X[k]={err:'tanpa komposit'};return;}var two=l.est.mode==='2d',mo=slMo(l.est,two);
    X[k]={C:C,z0:new Float64Array(C.length),unf:slIsBase(k)?'top':l.est.unf,mo:mo,two:two,I:okIndex(C,Math.max(5,mo.R[0]/2)),Tref:C.Tref,e:l.est,cnt:[0,0,0],nE:0,nF:0,dc:{}};});
  if(!Object.keys(X).some(function(k){return !X[k].err;})){alert('Tidak ada lapisan dengan estimasi aktif yang punya komposit.');return;}
  var n=m.n,lay=new Uint16Array(n).fill(65535),items=[];for(var i=0;i<n;i++){var la=slLayerAt(R,m.x[i]-offX,m.y[i]-offY,m.z[i]);if(!la)continue;lay[i]=la.k;if(X[la.k]&&!X[la.k].err)items.push([i,la]);}
  var V={};els.forEach(function(e){V[e]=new Float32Array(n).fill(-99);});
  SL.job={m:m,R:R,X:X,items:items,els:els,lay:lay,V:V,ps:new Uint8Array(n),ns:new Uint16Array(n),i:0,t0:performance.now(),cancel:false};SL.msg='';slPanel();setTimeout(slStep,10);}
function slStep(){var J=SL.job;if(!J)return;var t=performance.now(),m=J.m,saveAct=window.FLT?FLT._act:false;if(window.FLT)FLT._act=true;
  try{while(J.i<J.items.length&&performance.now()-t<45){var it=J.items[J.i],i=it[0],la=it[1],X=J.X[la.k],e=X.e,q=la.q,x=q[0],y=q[1],z;
      if(X.two)z=0;else{var th=la.top-la.bot;z=X.unf==='top'?la.top-q[2]:(th>0.01?(la.top-q[2])/th*X.Tref:X.Tref/2);}
      if(window.FLT)FLT._code=slCode([q[0],q[1],q[2]]);
      var sz=X.two?1:(X.unf==='top'?m.sz[i]:m.sz[i]*X.Tref/Math.max(0.01,la.top-la.bot)),dk=m.sx[i]+'_'+m.sy[i]+'_'+sz.toFixed(2),dc=X.dc[dk];
      if(!dc){var nd=e.nd&&e.nd.length===3?e.nd:[2,2,2],D=okDisc([m.sx[i],m.sy[i],X.two?0:sz],[nd[0],nd[1],X.two?1:nd[2]]);dc=X.dc[dk]={D:D,cbb:okCbb(X.mo,D)};}
      var PS=e.P&&e.P.length?e.P.map(function(q){return{mult:+q.mult,min:+q.min,max:+q.max,mph:+q.mph||0};}):[{mult:1,min:Math.max(1,+e.nmin||3),max:Math.max(2,+e.nmax||16)},{mult:2,min:Math.max(1,(+e.nmin||3)-1),max:Math.max(2,+e.nmax||16)},{mult:3,min:1,max:Math.max(2,+e.nmax||16)}],res=null;
      for(var p=0;p<PS.length;p++){var sel=okSearch(X.mo,X.I,X.C,x,y,z,PS[p].mult,PS[p].max,X.two?0:(PS[p].mph!=null?PS[p].mph:Math.max(0,+e.mph||0)));if(sel.length<PS[p].min)continue;var w=null;
        if(e.met==='ok'&&sel.length>1){var r=okKrige(X.mo,X.C,X.z0,sel,x,y,z,dc.D,dc.cbb);if(r)w=Array.prototype.slice.call(r.w,0,sel.length);}
        if(!w){var pw=Math.max(0.5,+e.p||2);w=sel.map(function(si){var c=X.C[si],d=Math.sqrt(meDn(X.mo,c.x-x,c.y-y,c.z-z,1));return 1/Math.pow(Math.max(d,1e-3),pw);});}
        res={w:w,sel:sel,p:p+1};break;}
      if(res){X.nE++;X.cnt[res.p-1]++;J.ps[i]=res.p;J.ns[i]=res.sel.length;J.els.forEach(function(el,q2){var sw=0,s=0,st=0,stw=0;res.sel.forEach(function(si,k){var c=X.C[si],v=c.v[q2];if(!isFinite(v))return;var wk=res.w[k];
            if(X.two){s+=wk*v*c.T;st+=wk*c.T;sw+=wk;}else{s+=wk*v;sw+=wk;}});
          var est=X.two?(st>1e-9?s/st:NaN):(Math.abs(sw)>1e-9?s/sw:NaN);if(isFinite(est))J.V[el][i]=Math.max(0,est);});}else X.nF++;
      J.i++;if(J.cancel)break;}}finally{if(window.FLT){FLT._act=saveAct;FLT._code=null;}}
  var pc=J.items.length?Math.round(100*J.i/J.items.length):100,bar=$('slBar'),tx=$('slPct');if(bar)bar.style.width=pc+'%';if(tx)tx.textContent=pc+'% ('+J.i+'/'+J.items.length+' blok)';
  if(J.cancel){SL.job=null;SL.msg='Dibatalkan.';slPanel();return;}if(J.i<J.items.length){setTimeout(slStep,0);return;}
  var ms=Math.round(performance.now()-J.t0);SL.S={key:slBmKey(m),n:m.n,lay:J.lay,V:J.V,ps:J.ps,ns:J.ns,els:J.els,names:SL.L.map(function(l){return l.name;}),when:new Date().toISOString().slice(0,16).replace('T',' '),ms:ms,
    st:Object.keys(J.X).map(function(k){var X=J.X[k];return{k:+k,name:SL.L[k].name,err:X.err||'',nC:X.C?X.C.length:0,nE:X.nE||0,nF:X.nF||0,cnt:X.cnt||[]};})};
  SL.job=null;SL.msg='&#10003; Estimasi selesai ('+(ms/1000).toFixed(1)+' s): '+SL.S.st.map(function(s){return s.err?'<span class=warn>'+slE(s.name)+': '+s.err+'</span>':'<b>'+slE(s.name)+'</b> '+s.nE+' blok'+(s.nF?' ('+s.nF+' tanpa sampel)':'');}).join(' · ');
  slApply(true);slPanel();try{updatePlot();}catch(e){}if(window.SA&&SA.dirty)SA.dirty();}
function slBmKey(m){return m.n+'|'+(m.src&&m.src.name||m.name||'')+'|'+(m.n?[m.x[0],m.y[0],m.z[0]].join(','):'');}
function slAN(e){return 'sl_'+String(e).toLowerCase().replace(/[^a-z0-9]+/g,'');}
function slApply(force){var m=window.BX&&BX.m,S=SL.S;if(!m)return;var A=['sl_lapisan','sl_pass','sl_ns','sl_rasio'].concat(S?S.els.map(slAN):[]);
  if(!S||S.key!==slBmKey(m)){A.forEach(function(k){if(m.num&&m.num[k])delete m.num[k];if(m.cat&&m.cat[k])delete m.cat[k];});if(m.mdl&&m.mdl.add)m.mdl.add=m.mdl.add.filter(function(a){return !/^sl_/.test(a.name);});return;}
  if(!force&&m.num[slAN(S.els[0])]&&m._slVer===S.when)return;
  var n=m.n,lay=S.lay instanceof Uint16Array?S.lay:Uint16Array.from(S.lay),cnt=S.names.map(function(){return 0;});for(var i=0;i<n;i++)if(lay[i]!==65535&&lay[i]<cnt.length)cnt[lay[i]]++;
  m.cat.sl_lapisan={codes:lay,dict:S.names.slice(),cnt:cnt};var f64=function(a){var o=new Float64Array(n);for(var i=0;i<n;i++)o[i]=a[i];return o;};
  S.els.forEach(function(e){m.num[slAN(e)]=f64(S.V[e]);});m.num.sl_pass=f64(S.ps);m.num.sl_ns=f64(S.ns);
  var ra=SL.o.ra,rb=SL.o.rb;if(ra&&rb&&S.V[ra]&&S.V[rb]){var o=new Float64Array(n).fill(-99);for(i=0;i<n;i++){var a=S.V[ra][i],b=S.V[rb][i];if(a>=0&&b>0)o[i]=a/b;}m.num.sl_rasio=o;}else delete m.num.sl_rasio;
  if(m.mdl){m.mdl.add=(m.mdl.add||[]).filter(function(a){return !/^sl_/.test(a.name);}).concat(S.els.map(function(e){return{name:slAN(e),type:2,dec:3,def:-99};}),[{name:'sl_pass',type:2,dec:0,def:0},{name:'sl_ns',type:2,dec:0,def:0}],m.num.sl_rasio?[{name:'sl_rasio',type:2,dec:3,def:-99}]:[],[{name:'sl_lapisan',type:3,def:'-'}]);}
  m._slVer=S.when;BX.ver++;BX.sc={};}
/* ---------- laporan ---------- */
function slReport(){var m=window.BX&&BX.m,S=SL.S;if(!m||!S||S.key!==slBmKey(m))return null;var els=S.els,pel=els.indexOf(SL.o.pel)>=0?SL.o.pel:els[0],cut=+SL.o.cut||0,ra=SL.o.ra,rb=SL.o.rb,R=SL.R;
  var rows=SL.L.map(function(l,k){return{k:k,name:l.name,dens:+l.dens||0,moist:+l.moist||0,n:0,vol:0,g:els.map(function(){return[0,0];}),gv:R&&R.vol[k]!=null?R.vol[k]:null};});
  for(var i=0;i<m.n;i++){var k=S.lay[i];if(k===65535||!rows[k])continue;var pv=S.V[pel]?S.V[pel][i]:-99;if(cut>0&&!(pv>=cut))continue;var r=rows[k],v=m.sx[i]*m.sy[i]*m.sz[i],dmt=v*r.dens*(1-r.moist/100);r.n++;r.vol+=v;
    els.forEach(function(e,q){var x=S.V[e][i];if(x>=0){r.g[q][0]+=x*dmt;r.g[q][1]+=dmt;}});}
  rows.forEach(function(r){r.wmt=r.vol*r.dens;r.dmt=r.wmt*(1-r.moist/100);r.avg=r.g.map(function(a){return a[1]>0?a[0]/a[1]:NaN;});var ia=els.indexOf(ra),ib=els.indexOf(rb);r.rat=ia>=0&&ib>=0&&r.avg[ib]>0?r.avg[ia]/r.avg[ib]:NaN;});
  return{rows:rows,els:els,pel:pel,cut:cut,ra:ra,rb:rb};}
function slRepCsv(){var Q=slReport();if(!Q){alert('Jalankan estimasi dulu.');return;}var h=['Lapisan','Blok','Volume_m3','Densitas','Kadar_air_pct','WMT','DMT'].concat(Q.els.map(function(e){return e;}),Q.ra&&Q.rb?['Rasio_'+Q.ra+'_'+Q.rb]:[],['Volume_grid_m3']),r=[h.join(',')];
  Q.rows.forEach(function(o){r.push([o.name,o.n,o.vol.toFixed(1),o.dens,o.moist,o.wmt.toFixed(1),o.dmt.toFixed(1)].concat(o.avg.map(function(v){return isFinite(v)?v.toFixed(4):'';}),Q.ra&&Q.rb?[isFinite(o.rat)?o.rat.toFixed(3):'']:[],[o.gv!=null?o.gv.toFixed(1):'']).join(','));});
  r.push('');r.push('Cut-off '+Q.pel+' >= '+Q.cut);slDl(r.join('\r\n'),'laporan_lapisan.csv','text/csv');}
function slDl(t,name,ty){return gxSimpan('\ufeff'+t,name,ty||'text/plain');}
function slGridCsv(){var R=slEnsure();if(!R){alert(SL.err||'Permukaan belum ada.');return;}var h=['X','Y'];for(var q=0;q<=R.nT;q++)h.push('Z_'+slSurfName(q).replace(/\s+/g,'_'));for(q=0;q<R.nT;q++)h.push('Tebal_'+SL.L[q].name.replace(/\s+/g,'_'));
  var r=[h.join(',')];for(var k=0;k<R.nx*R.ny;k++){if(!R.mask[k])continue;var x=R.x0+(k%R.nx)*R.cell,y=R.y0+Math.floor(k/R.nx)*R.cell,row=[(x+offX).toFixed(2),(y+offY).toFixed(2)];for(q=0;q<=R.nT;q++)row.push(isFinite(R.S[q][k])?R.S[q][k].toFixed(3):'');for(q=0;q<R.nT;q++)row.push(isFinite(R.S[q][k])&&isFinite(R.S[q+1][k])?(R.S[q][k]-R.S[q+1][k]).toFixed(3):'');r.push(row.join(','));}
  r.push('# grid kerangka pulih (sebelum digeser sesar post) bila ada sesar post ber-offset');slDl(r.join('\r\n'),'grid_lapisan.csv','text/csv');}
function slDxf(){var R=slEnsure();if(!R){alert(SL.err||'Permukaan belum ada.');return;}var o=['0','SECTION','2','ENTITIES'];R.M.forEach(function(m,q){var ly=slSurfName(q).replace(/[^\w\-]/g,'_');for(var t=0;t<m.nt;t++){var V=[m._i[t],m._j[t],m._k[t],m._k[t]];o.push('0','3DFACE','8',ly);V.forEach(function(v,c){o.push(String(10+c),(m._x[v]+offX).toFixed(3),String(20+c),(m._y[v]+offY).toFixed(3),String(30+c),(+m._z[v]).toFixed(3));});}});o.push('0','ENDSEC','0','EOF');slDl(o.join('\r\n'),'permukaan_lapisan.dxf','application/dxf');}
/* ---------- tampilan ---------- */
function slSurfCol(q){var L=SL.L;return(L[Math.min(q,L.length-1)]||{}).col||'#888';}
function slSurfVis(q){var L=SL.L,l=L[Math.min(q,L.length-1)];return !l||l.vis!==false;}
function slTraces(T,o){if(!SL.lay||VIEW2D||!SL.L.length||SL.ci<0)return;var R=slEnsure();if(!R)return;
  R.M.forEach(function(m,q){if(!m.nt||!slSurfVis(q))return;T.push({type:'mesh3d',name:'Lapisan: '+m.name,x:m._x,y:m._y,z:m._z,i:m._i,j:m._j,k:m._k,color:slSurfCol(q),opacity:o&&o.clip?Math.min(0.2,SL.op):SL.op,flatshading:false,lighting:{ambient:0.6,diffuse:0.7},hoverinfo:'name',showlegend:true});
    if(o&&o.clip&&o.K){var X=[],Y=[],Z=[];slSlice(R,q,o.K).forEach(function(l){l.p.forEach(function(p){X.push(p[0]);Y.push(p[1]);Z.push(p[2]);});X.push(null);Y.push(null);Z.push(null);});if(X.length)T.push({type:'scatter3d',mode:'lines',x:X,y:Y,z:Z,line:{color:slSurfCol(q),width:6},name:m.name+' (sayatan)',hoverinfo:'name',showlegend:false});}});
  if(SL.ctc){SL.L.forEach(function(l,k){if(l.vis===false)return;var x=[],y=[],z=[],t=[];R.H.forEach(function(h){var r=h.L[k];if(!r||!r.pres)return;if(o&&o.clip&&o.K&&!inK(o.K,{x:r.pt[0],y:r.pt[1],z:r.pt[2]}))return;x.push(r.pt[0]);y.push(r.pt[1]);z.push(r.pt[2]);t.push(h.id+' atap '+l.name+' ('+r.T.toFixed(1)+' m)');});
    if(x.length)T.push({type:'scatter3d',mode:'markers',x:x,y:y,z:z,text:t,hoverinfo:'text',marker:{size:3,color:l.col,line:{color:'#111',width:0.5}},name:'Kontak atap '+l.name,showlegend:false});});}}
function slSlice(R,q,K){var k=K[0],key=q+'|'+JSON.stringify([k.n,k.c,k.lo,k.hi]);R.sc=R.sc||{};if(R.sc[key])return R.sc[key];var L=[];try{L=wfSlice(R.M[q],{n:k.n,c:k.c},(k.lo+k.hi)/2);}catch(e){}R.sc[key]=L;return L;}
function slTraces2D(o,F){if(!SL.lay||!SL.L.length||SL.ci<0||!o.K)return[];var R=slEnsure();if(!R)return[];var out=[];
  R.M.forEach(function(m,q){if(!slSurfVis(q))return;var x=[],y=[],lx=null,ly=null;slSlice(R,q,o.K).forEach(function(l){l.p.forEach(function(p){var a=F(p[0],p[1],p[2]);x.push(a[0]);y.push(a[1]);if(lx==null||a[0]<lx){lx=a[0];ly=a[1];}});x.push(null);y.push(null);});
    if(!x.length)return;out.push({type:'scatter',mode:'lines',x:x,y:y,line:{color:slSurfCol(q),width:2.4},name:m.name,hoverinfo:'name',showlegend:true});out.push({type:'scatter',mode:'text',x:[lx],y:[ly],text:[m.name],textposition:'top right',textfont:{size:10,color:slSurfCol(q)},hoverinfo:'skip',showlegend:false});});
  return out;}
/* ---------- panel ---------- */
function slPreset(k){var P=SLPRE[k];if(!P)return;if(SL.L.length&&!confirm('Ganti daftar lapisan dengan preset '+P.t+'?'))return;var d=SL.ci>=0?slDict(SL.ci):[];
  SL.L=P.L.map(function(o,i){var l=slNewL({name:o.name,dens:o.dens||2,moist:o.moist||0},i);d.forEach(function(nm,c){if(o.k.test(String(nm)))l.codes.push(c);});if(P.base&&i===P.L.length-1)l.est=slEstDef(true);return l;});SL.o.base=!!P.base;
  if(k==='sdx')SL.L.forEach(function(l){l.est.mode=/bijih/i.test(l.name)?'2d':'3d';l.est.on=/bijih/i.test(l.name);});slDirty();}
function slSetO(k,v){SL.o[k]=v;slDirty(['ra','rb','cut','pel','el','comp'].indexOf(k)>=0);if(k==='ra'||k==='rb')slApply(true);}
function slSetL(i,k,v){var l=SL.L[i];if(!l)return;l[k]=v;slDirty(['name','col','dens','moist','vis'].indexOf(k)>=0);}
function slSetE(i,k,v){var l=SL.L[i];if(!l)return;l.est[k]=v;if(['az','r1','r2','r3','nug','nmin','nmax','mph'].indexOf(k)>=0){l.est.m=null;l.est.P=null;l.est.vsrc='manual';}slDirty(true);}
function slCodeT(i,c,on){var l=SL.L[i];if(!l)return;SL.L.forEach(function(o){o.codes=o.codes.filter(function(x){return x!==c;});});if(on)l.codes.push(c);slDirty();}
function slAdd(){SL.L.push(slNewL({},SL.L.length));slDirty();}
function slDel(i){if(!confirm('Hapus lapisan '+SL.L[i].name+'?'))return;SL.L.splice(i,1);slDirty();}
function slMove(i,d){var j=i+d;if(j<0||j>=SL.L.length)return;var t=SL.L[i];SL.L[i]=SL.L[j];SL.L[j]=t;slDirty();}
function slElT(e,on){var L=slEls().slice();L=L.filter(function(x){return x!==e;});if(on)L.push(e);SL.o.el=L;slDirty(true);}
function slPanel(){var b=$('slBody');if(!b)return;var cats=slCats(),o=SL.o,L=SL.L,E=window.elements||[];if(SL.ci<0&&cats.length){var pf=-1;cats.forEach(function(i){if(pf<0&&/LITH|LAPIS|LAYER|HORIZ|ZONE/i.test(CAT[i].name))pf=i;});SL.ci=pf>=0?pf:cats[0];}
  var h='<div class=hint style="margin:-4px 0 8px">Pemodelan endapan <b>berlapis</b>: laterit nikel &amp; bauksit (mengikuti permukaan), stratiform / sedex. Lapisan dari kode log geologi &rarr; permukaan atap / lantai (grid) &rarr; estimasi per lapisan di koordinat <b>unfold</b> &rarr; laporan WMT / DMT. Sesar 3D (menu Sesar) ikut diperhitungkan.</div>';
  /* Lapisan */
  h+='<h4>Lapisan</h4><div class="g2 f"><div><label>Kolom geologi</label><select onchange="SL.ci=+this.value;slDirty()">'+cats.map(function(i){return '<option value='+i+(i===SL.ci?' selected':'')+'>'+slE(CAT[i].name)+'</option>';}).join('')+'</select></div>'+
    '<div><label>Preset</label><select onchange="if(this.value)slPreset(this.value);this.value=\'\'"><option value="">— pilih —</option>'+Object.keys(SLPRE).map(function(k){return '<option value='+k+'>'+SLPRE[k].t+'</option>';}).join('')+'</select></div></div>';
  if(!cats.length)h+='<div class=warn>Tabel geologi belum ada di proyek ini (import geologi dengan kolom litologi / zona laterit).</div>';
  var d=SL.ci>=0?slDict(SL.ci):[];
  if(L.length)h+='<div class=gmlist><table class=pltb><tr><th></th><th>Lapisan (atas &rarr; bawah)</th><th>Kode log</th><th>Densitas</th><th>Air %</th><th></th></tr>'+L.map(function(l,i){var isB=o.base&&i===L.length-1&&L.length>1;
      return '<tr><td><input type=checkbox '+(l.vis!==false?'checked':'')+' title="Tampil" onchange="slSetL('+i+',\'vis\',this.checked)"><input type=color value="'+l.col+'" style="width:22px;height:18px;padding:0;border:0" onchange="slSetL('+i+',\'col\',this.value)"></td>'+
        '<td><input type=text value="'+slE(l.name)+'" style="width:96px" onchange="slSetL('+i+',\'name\',this.value)">'+(isB?'<div class=hint>dasar (tanpa lantai)</div>':'')+'</td>'+
        '<td><details><summary>'+(l.codes.length?l.codes.map(function(c){return slE(slCodeName(SL.ci,c));}).join(', '):'<span class=warn>pilih kode</span>')+'</summary>'+d.map(function(nm,c){return '<label class=sw style="margin:0;display:flex"><input type=checkbox '+(l.codes.indexOf(c)>=0?'checked':'')+' onchange="slCodeT('+i+','+c+',this.checked)">'+slE(nm)+'</label>';}).join('')+'</details></td>'+
        '<td><input type=number step=0.01 value="'+l.dens+'" style="width:52px" onchange="slSetL('+i+',\'dens\',+this.value)"></td><td><input type=number step=1 value="'+l.moist+'" style="width:44px" onchange="slSetL('+i+',\'moist\',+this.value)"></td>'+
        '<td style="white-space:nowrap"><a href="#" onclick="slMove('+i+',-1);return false">&#9650;</a> <a href="#" onclick="slMove('+i+',1);return false">&#9660;</a> <a href="#" class=warn onclick="slDel('+i+');return false">&#10005;</a></td></tr>';}).join('')+'</table></div>';
  h+='<div class="g2 f"><button onclick="slAdd()">+ Lapisan</button><label class=sw style="margin:0" title="Lapisan terakhir = batuan dasar: hanya atapnya yang dimodelkan"><input type=checkbox '+(o.base?'checked':'')+' onchange="slSetO(\'base\',this.checked)">Lapisan terakhir = dasar</label></div>';
  /* Permukaan */
  var R=SL.L.length&&SL.ci>=0?slEnsure():null;
  h+='<h4>Permukaan lapisan</h4><div class="g3 f"><div><label>Sel grid (m)</label><input type=number step=any value="'+o.cell+'" onchange="slSetO(\'cell\',+this.value)"></div><div><label>Ekstrapolasi maks (m)</label><input type=number step=any value="'+o.ext+'" onchange="slSetO(\'ext\',+this.value)"></div><div><label>Pangkat IDW / N tetangga</label><div style="display:flex;gap:3px"><input type=number step=0.5 value="'+o.p+'" onchange="slSetO(\'p\',+this.value)"><input type=number step=1 value="'+o.nmax+'" onchange="slSetO(\'nmax\',+this.value)"></div></div></div>'+
    '<div class="g2 f"><div><label>Atap lapisan pertama</label><select onchange="slSetO(\'top\',this.value)"><option value=auto'+(o.top==='auto'?' selected':'')+'>Otomatis</option><option value=topo'+(o.top==='topo'?' selected':'')+'>Topografi − kedalaman kontak</option><option value=bor'+(o.top==='bor'?' selected':'')+'>Elevasi kontak bor</option></select></div>'+
    '<div><label>Metode lapisan bawah</label><select onchange="slSetO(\'sm\',this.value)"><option value=tebal'+(o.sm!=='elev'?' selected':'')+'>Ketebalan (isopach) ditumpuk</option><option value=elev'+(o.sm==='elev'?' selected':'')+'>Elevasi kontak langsung</option></select></div></div>';
  if(SL.err&&!R)h+='<div class=warn>'+slE(SL.err)+'</div>';
  if(R){h+='<div class="box gmstate">'+R.nh+' hole · grid '+R.nx+' × '+R.ny+' @ '+slN(R.cell)+' m · atap: '+(R.topo?'topografi':'kontak bor')+(R.nRest?' · <b>'+R.nRest+' sesar post dipulihkan</b>':'')+(R.nHb?' · '+R.nHb+' batas keras':'')+' · '+(R.ms/1000).toFixed(2)+' s</div>'+
      '<div class=gmlist><table class=pltb><tr><th>Lapisan</th><th>Hole tembus</th><th>Tebal rata² (min–maks)</th><th>Volume grid</th></tr>'+R.st.map(function(s,i){return '<tr><td>'+slE(SL.L[i].name)+'</td><td>'+s.np+(s.nc-(s.ns||0)>0?' <span class=hint title="hole berhenti di dalam lapisan (tebal minimum, tidak dipakai untuk isopach)">('+(s.nc-(s.ns||0))+' berhenti di lapisan)</span>':'')+(s.ns?' <span class=hint title="atap dan lantai lapisan di hole ini ada di blok sesar berbeda: kontak dipakai, ketebalan tidak">('+s.ns+' terpotong sesar)</span>':'')+'</td><td>'+slN(s.tav,2)+' ('+slN(s.tmin,1)+'–'+slN(s.tmax,1)+') m</td><td>'+slN(R.vol[i],0)+' m&sup3;</td></tr>';}).join('')+'</table></div>'+
      '<div class="g3 f"><label class=sw style="margin:0"><input type=checkbox '+(SL.lay?'checked':'')+' onchange="SL.lay=this.checked;updatePlot()">Tampil 3D</label><label class=sw style="margin:0"><input type=checkbox '+(SL.ctc?'checked':'')+' onchange="SL.ctc=this.checked;updatePlot()">Titik kontak</label><input type=range min=0.1 max=1 step=0.05 value="'+SL.op+'" title="Transparansi" onchange="SL.op=+this.value;updatePlot()"></div>'+
      '<div class="g2 f"><button onclick="slGridCsv()">&#8681; Grid CSV (atap / tebal)</button><button onclick="slDxf()">&#8681; DXF permukaan</button></div>';}
  /* Estimasi */
  var els=slEls();h+='<h4>Estimasi per lapisan</h4><div class=f><label>Unsur</label><div class=chips>'+E.map(function(e){return '<label class=sw style="margin:0 8px 0 0;display:inline-flex"><input type=checkbox '+(els.indexOf(e)>=0?'checked':'')+' onchange="slElT(\''+slE(e)+'\',this.checked)">'+slE(e)+'</label>';}).join('')+'</div></div>'+
    '<div class="g3 f"><div><label>Komposit (m, 0 = per lapisan)</label><input type=number step=any value="'+o.comp+'" onchange="slSetO(\'comp\',+this.value)"></div><div><label>Rasio: pembilang</label><select onchange="slSetO(\'ra\',this.value)"><option value="">—</option>'+els.map(function(e){return '<option'+(e===o.ra?' selected':'')+'>'+slE(e)+'</option>';}).join('')+'</select></div><div><label>penyebut</label><select onchange="slSetO(\'rb\',this.value)"><option value="">—</option>'+els.map(function(e){return '<option'+(e===o.rb?' selected':'')+'>'+slE(e)+'</option>';}).join('')+'</select></div></div>';
  if(L.length)h+='<div class=gmlist><table class=pltb><tr><th>Lapisan</th><th>Aktif</th><th>Mode</th><th>Metode</th><th>Unfold</th><th>Az</th><th>R mayor / minor / vert</th><th>Nug</th><th>Min / Maks / per hole</th></tr>'+L.map(function(l,i){var e=l.est,n=function(k,w,st){return '<input type=number step="'+(st||'any')+'" value="'+e[k]+'" style="width:'+(w||40)+'px" onchange="slSetE('+i+',\''+k+'\',+this.value)">';},s=function(k,O){return '<select onchange="slSetE('+i+',\''+k+'\',this.value)">'+O.map(function(q){return '<option value="'+q[0]+'"'+(e[k]===q[0]?' selected':'')+'>'+q[1]+'</option>';}).join('')+'</select>';};
      return '<tr><td>'+slE(l.name)+(e.m?'<div class=hint title="'+slE(e.vsrc||'')+'">variogram: Geostatistik</div>':'')+'</td><td><input type=checkbox '+(e.on?'checked':'')+' onchange="slSetE('+i+',\'on\',this.checked)"></td><td>'+s('mode',[['3d','Blok 3D'],['2d','Akumulasi 2D']])+'</td><td>'+s('met',[['ok','OK'],['idw','IDW']])+'</td><td>'+(e.mode==='2d'?'-':s('unf',[['prop','Proporsional'],['top','Dari atap']]))+'</td><td>'+n('az',38)+'</td><td style="white-space:nowrap">'+n('r1')+n('r2')+(e.mode==='2d'?'':n('r3',34))+'</td><td>'+n('nug',38)+'</td><td style="white-space:nowrap">'+n('nmin',30,1)+n('nmax',30,1)+(e.mode==='2d'?'':n('mph',30,1))+'</td></tr>';}).join('')+'</table></div>'+
    '<div class=hint>Unfold <b>proporsional</b>: posisi relatif antara atap &amp; lantai lapisan (cocok laterit, ketebalan bervariasi). <b>Dari atap</b>: kedalaman di bawah atap. <b>Akumulasi 2D</b>: tebal × kadar per hole, kadar blok = &Sigma;(w·T·kadar)/&Sigma;(w·T) — untuk lapisan tipis / sedex. R vertikal di ruang unfold (m).</div>';
  h+='<div class="g2 f"><button class=btn-pri id=slBtn onclick="slRun()"'+(window.BX&&BX.m?'':' disabled title="Import block model GC dulu"')+'>'+(SL.job?'&#9632; Batalkan':'&#9654; Jalankan estimasi lapisan')+'</button><span id=slPct class=hint></span></div><div class=prog style="height:5px;background:var(--bd,#ddd);border-radius:3px"><div id=slBar style="height:5px;width:0;background:#e8590c;border-radius:3px"></div></div>'+(SL.msg?'<div class="box gmstate" style="margin-top:6px">'+SL.msg+'</div>':'');
  /* Laporan */
  h+='<h4>Laporan</h4>';var Q=slReport();
  h+='<div class="g2 f"><div><label>Cut-off unsur</label><select onchange="slSetO(\'pel\',this.value)">'+els.map(function(e){return '<option'+(e===(Q?Q.pel:o.pel)?' selected':'')+'>'+slE(e)+'</option>';}).join('')+'</select></div><div><label>Cut-off (&ge;)</label><input type=number step=any value="'+o.cut+'" onchange="slSetO(\'cut\',+this.value)"></div></div>';
  if(!Q)h+='<div class=hint>'+(SL.S&&window.BX&&BX.m?'Block model berubah sejak estimasi terakhir — jalankan ulang.':'Jalankan estimasi lapisan dulu.')+'</div>';
  else h+='<div class=gmlist><table class=pltb><tr><th>Lapisan</th><th>Volume</th><th>WMT</th><th>DMT</th>'+Q.els.map(function(e){return '<th>'+slE(e)+'</th>';}).join('')+(Q.ra&&Q.rb?'<th>'+slE(Q.ra+'/'+Q.rb)+'</th>':'')+'</tr>'+Q.rows.map(function(r){return '<tr><td>'+slE(r.name)+'</td><td>'+slN(r.vol,0)+'</td><td>'+slN(r.wmt,0)+'</td><td><b>'+slN(r.dmt,0)+'</b></td>'+r.avg.map(function(v){return '<td>'+slN(v,3)+'</td>';}).join('')+(Q.ra&&Q.rb?'<td>'+slN(r.rat,2)+'</td>':'')+'</tr>';}).join('')+'</table></div>'+
    '<div class=hint>WMT = volume × densitas basah; DMT = WMT × (1 − kadar air). Kadar rata-rata ditimbang DMT. Blok di-assign ke lapisan dari titik tengahnya.</div><button style="width:100%" onclick="slRepCsv()">&#8681; Laporan CSV</button>';
  try{h+=slValHtml();}catch(e){console.error(e);}
  b.innerHTML=h;try{uiSecTabs(b,'sl',['Lapisan','Permukaan','Estimasi','Laporan','Validasi']);}catch(e){}}
/* ---------- pasang: rail, panel, tree, 3D / 2D, simpan ---------- */
function gxRail(id,html,title,after,body,h3){var side=$('side');if(!side||$('p'+id))return;var s=document.createElement('section');s.id='p'+id;s.hidden=true;s.innerHTML='<h3>'+h3+'</h3><div id='+body+'></div>';side.appendChild(s);
  var ref=$(after);if(ref&&ref.parentNode){var bt=document.createElement('button');bt.className='rb';bt.id='rb'+id;bt.title=title;bt.innerHTML=html;bt.onclick=function(){uiTab(id);};ref.parentNode.insertBefore(bt,ref.nextSibling);}}
(function(){
  gxRail('FLT',"<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linejoin='round'><path d='M3 6h7l-3 6h7'/><path d='M4 18h7l3-6' stroke-dasharray='2 2'/><path d='M14 3l-6 18' stroke-width='2.2'/></svg>Sesar 3D",'Sesar 3D: bidang sesar, offset, waktu (pre / syn / post) & urutan umur','rbSlice','fltBody','Sesar 3D (Struktur Geologi)');
  gxRail('SL',"<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linejoin='round'><path d='M3 7c4-2 7 1 9 0s5-2 9 0'/><path d='M3 12c4-2 7 1 9 0s5-2 9 0' stroke-dasharray='2.5 2'/><path d='M3 17c4-2 7 1 9 0s5-2 9 0'/></svg>Geomodeller<br>Strata-Laterit",'Geomodeller Stratified-Laterite Deposit: laterit Ni / bauksit / stratiform (sedex)','rbGM','slBody','Geomodeller Stratified-Laterite Deposit');
  var _u=uiTab;uiTab=function(n){var r=_u.apply(this,arguments);['FLT','SL'].forEach(function(k){var p=$('p'+k),b=$('rb'+k);if(p)p.hidden=n!==k;if(b)b.className='rb'+(n===k?' on':'');});
    if(n==='FLT'||n==='SL'){document.querySelectorAll('#side>section').forEach(function(s){if(s.id!=='p'+n)s.hidden=true;});document.querySelectorAll('.rb.on').forEach(function(b){if(b.id!=='rb'+n)b.className='rb';});try{if(n==='FLT')fltPanel();else slPanel();}catch(e){console.error(e);}}return r;};window.uiTab=uiTab;
  var _dt=dgTraces;dgTraces=function(T,o){_dt.apply(this,arguments);try{slTraces(T,o||{});}catch(e){console.error(e);}};window.dgTraces=dgTraces;
  var _b2=window.bxTraces2D;window.bxTraces2D=function(o,F){var r=_b2?_b2.apply(this,arguments):[];try{r=r.concat(slTraces2D(o,F));}catch(e){console.error(e);}return r;};
  if(typeof meApply==='function'){var _ma=meApply;meApply=function(){var r=_ma.apply(this,arguments);try{slApply(!!r);}catch(e){console.error(e);}return r;};window.meApply=meApply;}
  if(typeof lyrDef==='function'){var _ld=lyrDef;lyrDef=function(){var L=_ld.apply(this,arguments);L.push({g:'Geomodeller Stratified-Laterite'},{k:'slv',t:'Permukaan lapisan',c:{get:function(){return SL.lay;},set:function(v){SL.lay=v;},ok:function(){return SL.L.length>0;}}});return L;};window.lyrDef=lyrDef;}
  var pk=function(S){if(!S)return null;var c=function(a){return Array.prototype.map.call(a,function(v){return Math.round(v*10000)/10000;});};var V={};S.els.forEach(function(e){V[e]=c(S.V[e]);});return Object.assign({},S,{lay:Array.from(S.lay),V:V,ps:Array.from(S.ps),ns:Array.from(S.ns)});};
  var upk=function(S){if(!S||!S.lay)return null;var V={};(S.els||[]).forEach(function(e){V[e]=Float32Array.from(S.V[e]||[]);});return Object.assign({},S,{lay:Uint16Array.from(S.lay),V:V,ps:Uint8Array.from(S.ps||[]),ns:Uint16Array.from(S.ns||[])});};
  var _c=SA.collectWork;SA.collectWork=function(){var w=_c.apply(this,arguments);try{w.sl={ci:SL.ci,ciN:SL.ci>=0&&CAT[SL.ci]?CAT[SL.ci].name:'',L:SL.L,o:SL.o,lay:SL.lay,op:SL.op,ctc:SL.ctc,S:pk(SL.S)};}catch(e){console.error(e);}return w;};
  var _a=SA.applyWork;SA.applyWork=function(W){try{var o=W&&W.sl;SL.R=null;SL.S=null;SL.msg='';if(o){SL.L=o.L||[];SL.o=Object.assign({},SL.o,o.o||{});['lay','op','ctc'].forEach(function(k){if(o[k]!=null)SL[k]=o[k];});SL.ci=o.ci!=null?o.ci:-1;
        if(o.ciN){CAT.forEach(function(c,i){if(c.name===o.ciN)SL.ci=i;});}SL.S=upk(o.S);}else{SL.L=[];SL.ci=-1;}}catch(e){console.error(e);}var r=_a.apply(this,arguments);try{slApply(true);slPanel();}catch(e){}return r;};
})();
/* database proyek SQLite (gcex_proyek.db): tabel sesar & lapisan (khusus Drillhole) */
(function w(n){if(window.PDB&&PDB.tables&&!PDB._slw){PDB._slw=1;var _t=PDB.tables;PDB.tables=function(){var T=_t.apply(this,arguments);
    try{if(window.FLT)T.push({name:'sesar',key:['id'],cols:['id','nama','waktu','urutan_umur','jenis','dip','dip_direction','slip_trend','slip_plunge','offset_m','batas_keras','memotong','jejak'],
      rows:FLT.F.map(function(f){var o=fltSlipTP(f);return[f.id,f.name,f.tm,+f.age||0,f.ty,+f.dip,+f.dd,Math.round(o.tr),Math.round(o.pl),fltOff(f),fltHbOn(f)?1:0,(f.cuts||[]).map(function(i){var g=fltGet(i);return g?g.name:i;}).join(' '),JSON.stringify(f.tr||[])];})});}catch(e){}
    try{if(window.SL&&SL.L.length)T.push({name:'lapisan',key:['urutan'],cols:['urutan','nama','kode_log','densitas','kadar_air_pct','mode_estimasi','unfold','volume_grid_m3'],
      rows:SL.L.map(function(l,i){return[i+1,l.name,(l.codes||[]).map(function(c){return slCodeName(SL.ci,c);}).join(' '),+l.dens,+l.moist,l.est&&l.est.on?l.est.mode:'-',l.est?l.est.unf:'',SL.R&&SL.R.vol[i]!=null?Math.round(SL.R.vol[i]):null];})});}catch(e){}
    return T;};}else if((n||0)<40)setTimeout(function(){w((n||0)+1);},250);})();

/* ================= 0.21.1: GEOSTATISTIK PER LAPISAN (ruang unfold) & VALIDASI =================
   Geostatistik → pilih "Lapisan (unfold)": komposit lapisan (koordinat pulih sesar, Z = unfold; akumulasi 2D: nilai = tebal × kadar, Z = 0)
   dipakai Statistik / Variogram / Anisotropi (bidang datar: arah 0° = timur) / Model / KNA. "Simpan ke lapisan" mengisi
   model variogram, pass, diskretisasi & top-cut lapisan (Estimasi). Validasi: swath komposit vs blok, grade-tonase DMT. */
GS.sl=null;
function slGsComps(k,ei){var R=slEnsure();if(!R)throw new Error(SL.err||'permukaan lapisan belum ada');var l=SL.L[k];if(!l)return[];var el=elements[ei],e=l.est,two=e.mode==='2d',tc0=e.tc;e.tc=null;var C;try{C=slComps(R,k,[el]);}finally{e.tc=tc0;}
  return C.filter(function(c){return isFinite(c.v[0]);}).map(function(c){var v=two?c.v[0]*c.T:c.v[0];return{id:c.id,f:c.f,t:c.t,d:(c.f+c.t)/2,len:c.len,v:v,x:c.x,y:c.y,z:c.z,s:c.x,w:c.y,fc:c.fc};});}
function slGsS(){return{g:{m:'U',u:[1,0,0],w:[0,1,0],n:[0,0,1],c:[0,0,0],az:90,dip:0},pos:0,thick:0,K:[],K2:null};}
function slGsLabel(k){var l=SL.L[k],e=l?l.est:{},R=SL.R;return 'Lapisan '+(l?l.name:'?')+' — '+(e.mode==='2d'?'akumulasi 2D (tebal × kadar)':'unfold '+(e.unf==='top'||slIsBase(k)?'dari atap':'proporsional'))+(R&&R.nRest?' · sesar dipulihkan':'');}
(function(){
  var _gc=gsComps;gsComps=function(ids,ei){if(GS.sl==null||!SL.L[GS.sl])return _gc.apply(this,arguments);return slGsComps(GS.sl,ei);};window.gsComps=gsComps;
  var _gr=gsRun;gsRun=function(){if(GS.sl==null||!SL.L[GS.sl])return _gr.apply(this,arguments);var _sk=secK,_sl=secLabel,k=GS.sl;
    secK=function(){return slGsS();};secLabel=function(){return slGsLabel(k);};window.secK=secK;window.secLabel=secLabel;
    try{var r=_gr.apply(this,arguments);if(GS.R){GS.R.sl=k;GS.R.slMode=SL.L[k].est.mode;}return r;}catch(e){console.error(e);try{$('gsSum').innerHTML='<span class=warn>'+slE(e.message)+'</span>';}catch(e2){}}
    finally{secK=_sk;secLabel=_sl;window.secK=_sk;window.secLabel=_sl;}};window.gsRun=gsRun;
  if(typeof okRun==='function'){var _or=okRun;okRun=function(){if(GS.sl!=null){try{$('okMsg').innerHTML='<span class=warn>Uji estimasi grid tidak tersedia untuk sumber Lapisan (ruang unfold). Pakai KNA, lalu <b>Simpan ke lapisan</b> dan jalankan estimasi di Geomodeller Stratified-Laterite .</span>';}catch(e){}return;}return _or.apply(this,arguments);};window.okRun=okRun;}
  var _gb=window.gsBar;window.gsBar=function(){if(_gb)_gb.apply(this,arguments);var b=$('gsDomBar');if(!b||!SL.L.length)return;var on=GS.sl!=null&&SL.L[GS.sl];
    var h='<span style="margin-left:10px">Lapisan</span><select onchange="slGsSet(this.value)"><option value="">— (domain / sayatan)</option>'+SL.L.map(function(l,i){return '<option value='+i+(on&&GS.sl===i?' selected':'')+'>'+slE(l.name)+(l.est.mode==='2d'?' (akumulasi 2D)':' (unfold)')+'</option>';}).join('')+'</select>'+(on?'<small>'+slE(slGsLabel(GS.sl))+'</small>':'');
    b.insertAdjacentHTML('beforeend',h);if(on){b.classList.add('on');var s0=b.querySelector('select');if(s0)s0.disabled=true;}};
  var _td=window.gsToDomHtml;if(_td){gsToDomHtml=function(){if(GS.sl==null||!SL.L[GS.sl])return _td.apply(this,arguments);var l=SL.L[GS.sl];
      return '<div class=box style="margin-top:8px"><b>Simpan parameter ke lapisan</b><div class=note>Model variogram (tab Model), pass &amp; diskretisasi (di atas) dan top-cut disimpan ke lapisan <b>'+slE(l.name)+'</b> untuk dipakai <b>Geomodeller Stratified-Laterite Estimasi</b>. Satu model dipakai semua unsur lapisan itu.</div><button class=btn-pri onclick="slFromGs()">&#8681; Simpan ke lapisan '+slE(l.name)+'</button><div id=slGsMsg class=note></div></div>';};window.gsToDomHtml=gsToDomHtml;}
})();
function slGsSet(v){GS.sl=v===''||v==null?null:+v;try{gsBar();}catch(e){}try{gsRun();}catch(e){console.error(e);}try{if(GS.tab==='E'&&$('gsDomBox'))$('gsDomBox').innerHTML=gsToDomHtml();}catch(e){}}
function slFromGs(){var k=GS.sl,l=SL.L[k];if(!l||!GS.R||GS.R.sl!==k){alert('Jalankan Geostatistik dengan sumber Lapisan dulu.');return;}var m=okModel();if(!m){alert('Lakukan fitting model variogram dulu (tab Model).');return;}
  /* jangkauan vertikal (ruang unfold) dari variogram downhole bila Minor tidak diisi di tab Model */
  var Md=GS.R.M&&GS.R.M.d,vsrc='downhole';if(!m.minorSet&&Md&&Md.length){m.Cn=m.Cn.map(function(c,i){return Math.max(0.2,+(Md[i]!=null?Md[i]:Md[0])||c);});}else vsrc=m.minorSet?'minor (tab Model)':'-';
  var P=okPasses(),e=l.est,az=(Math.atan2(m.vM[0],m.vM[1])*180/Math.PI+360)%360;e.m={vM:m.vM,vS:m.vS,vN:m.vN,c0:m.c0,cs:m.cs,A:m.A,B:m.B,Cn:m.Cn};if(P.length)e.P=P;e.nd=okNd();
  e.az=Math.round(az);e.r1=Math.round(Math.max.apply(null,m.A)*10)/10;e.r2=Math.round(Math.max.apply(null,m.B)*10)/10;e.r3=Math.round(Math.max.apply(null,m.Cn)*100)/100;e.nug=Math.round(m.c0*1000)/1000;
  if(P.length){e.nmin=P[0].min;e.nmax=P[0].max;e.mph=P[0].mph;}e.met='ok';e.tc=e.tc||{};if(GS.R.slMode!=='2d'){if(GS.R.tc)e.tc[GS.R.el]=GS.R.tc;else delete e.tc[GS.R.el];}
  e.vsrc='vertikal: '+vsrc+' · '+GS.R.el+' · '+(GS.R.label||'')+' · '+new Date().toISOString().slice(0,16).replace('T',' ');slDirty(true);
  try{$('slGsMsg').innerHTML='&#10003; Tersimpan ke '+slE(l.name)+': az '+e.az+'&deg;, range '+e.r1+' / '+e.r2+' / '+e.r3+' m, nugget '+e.nug+'. Lanjut di Geomodeller Stratified-Laterite .';}catch(x){}}
/* ---------- validasi ---------- */
SL.v={k:0,el:'',dir:'x',bw:25,cuts:'0,0.5,1,1.2,1.5,1.8,2'};
function slVal(){var m=window.BX&&BX.m,S=SL.S,R=SL.R;if(!m||!S||S.key!==slBmKey(m)||!R)return null;var v=SL.v,k=Math.min(SL.L.length-1,+v.k||0),l=SL.L[k],el=S.els.indexOf(v.el)>=0?v.el:S.els[0];if(!l)return null;
  var E=S.V[el],C=slComps(R,k,[el]),two=l.est.mode==='2d',dir=v.dir,bw=Math.max(0.1,+v.bw||25),sw={},key=function(x,y,z){var q=dir==='x'?x:dir==='y'?y:z;return Math.floor(q/bw);};
  var Tm=C.Tref||1,sc=0,sl=0;C.forEach(function(c){var g=c.v[0];if(!isFinite(g))return;var w=two?c.T:c.len;sc+=g*w;sl+=w;var kk=key(c.x+offX,c.y+offY,two?0:c.z),b=sw[kk]||(sw[kk]={c:0,cw:0,e:0,ne:0,nc:0});b.c+=g*w;b.cw+=w;b.nc++;});
  var se=0,ne=0;for(var i=0;i<m.n;i++){if(S.lay[i]!==k||!(E[i]>=0))continue;se+=E[i];ne++;var z=0;if(!two&&dir==='z'){var la=slLayerAt(R,m.x[i]-offX,m.y[i]-offY,m.z[i]);if(!la)continue;var th=la.top-la.bot,unf=(l.est.unf==='top'||slIsBase(k));z=unf?la.top-la.q[2]:(th>0.01?(la.top-la.q[2])/th*Tm:Tm/2);}
    var xx=m.x[i],yy=m.y[i];if(dir!=='z'&&R.nRest){var qq=slRest(m.x[i]-offX,m.y[i]-offY,m.z[i]);xx=qq[0]+offX;yy=qq[1]+offY;}
    var kk=key(xx,yy,z),b=sw[kk]||(sw[kk]={c:0,cw:0,e:0,ne:0,nc:0});b.e+=E[i];b.ne++;}
  var rows=Object.keys(sw).map(Number).sort(function(a,b){return a-b;}).map(function(kk){var b=sw[kk];return[(kk+0.5)*bw,b.cw?b.c/b.cw:null,b.ne?b.e/b.ne:null,null,b.nc];});
  var cuts=String(v.cuts).split(/[;, ]+/).map(Number).filter(function(x){return isFinite(x);}).sort(function(a,b){return a-b;}),dens=+l.dens||0,ms=+l.moist||0,gt=cuts.map(function(c){var vol=0,mt=0;for(var i=0;i<m.n;i++){if(S.lay[i]!==k||!(E[i]>=c)||!(E[i]>=0))continue;var vv=m.sx[i]*m.sy[i]*m.sz[i];vol+=vv;mt+=vv*dens*(1-ms/100)*E[i];}var dmt=vol*dens*(1-ms/100);return[c,vol,dmt,dmt>0?mt/dmt:NaN];});
  return{k:k,l:l,el:el,two:two,nC:C.length,cm:sl?sc/sl:NaN,em:ne?se/ne:NaN,ne:ne,sw:rows,gt:gt,dir:dir,bw:bw};}
function slValHtml(){var h='<h4>Validasi lapisan</h4>',S=SL.S;if(!S){return h+'<div class=hint>Jalankan estimasi lapisan dulu.</div>';}var v=SL.v;
  h+='<div class="g3 f"><div><label>Lapisan</label><select onchange="SL.v.k=+this.value;slPanel()">'+SL.L.map(function(l,i){return '<option value='+i+(i===+v.k?' selected':'')+'>'+slE(l.name)+'</option>';}).join('')+'</select></div>'+
    '<div><label>Unsur</label><select onchange="SL.v.el=this.value;slPanel()">'+S.els.map(function(e){return '<option'+(e===v.el?' selected':'')+'>'+slE(e)+'</option>';}).join('')+'</select></div>'+
    '<div><label>Swath / bin (m)</label><div style="display:flex;gap:3px"><select onchange="SL.v.dir=this.value;slPanel()"><option value=x'+(v.dir==='x'?' selected':'')+'>Easting</option><option value=y'+(v.dir==='y'?' selected':'')+'>Northing</option><option value=z'+(v.dir==='z'?' selected':'')+'>Unfold Z</option></select><input type=number step=any value="'+v.bw+'" style="width:46px" onchange="SL.v.bw=+this.value;slPanel()"></div></div></div>';
  var Q=null;try{Q=slVal();}catch(e){console.error(e);}if(!Q)return h+'<div class=hint>Block model berubah sejak estimasi terakhir — jalankan ulang.</div>';
  var d=isFinite(Q.cm)&&Q.cm?100*(Q.em-Q.cm)/Q.cm:NaN;
  h+='<div class="box gmstate">'+slE(Q.l.name)+' · '+slE(Q.el)+': komposit '+Q.nC+' (rata-rata '+(Q.two?'tertimbang tebal':'tertimbang panjang')+' <b>'+slN(Q.cm,3)+'</b>) vs blok '+Q.ne+' (rata-rata <b>'+slN(Q.em,3)+'</b>)'+(isFinite(d)?' · selisih <b class="'+(Math.abs(d)>10?'warn':'')+'">'+(d>0?'+':'')+slN(d,1)+'%</b>':'')+'</div>';
  var svg='';try{svg=meSwathSvg(Q.sw,Q.el).replace('jarak sepanjang strike (m), bin 10 m',(Q.dir==='x'?'Easting':Q.dir==='y'?'Northing':'Z unfold')+' (m), bin '+Q.bw+' m').replace('- - GC lama','').replace('estimasi baru','blok (sl_'+Q.el+')');}catch(e){}
  h+=svg+'<div class=gmlist><table class=pltb><tr><th>Cut-off '+slE(Q.el)+' &ge;</th><th>Volume</th><th>DMT</th><th>Kadar</th></tr>'+Q.gt.map(function(r){return '<tr><td>'+slN(r[0],2)+'</td><td>'+slN(r[1],0)+'</td><td>'+slN(r[2],0)+'</td><td>'+slN(r[3],3)+'</td></tr>';}).join('')+'</table></div>'+
    '<div class="f"><label>Cut-off grade-tonase</label><input type=text value="'+slE(v.cuts)+'" onchange="SL.v.cuts=this.value;slPanel()"></div><div class=hint>Swath: rata-rata komposit (oranye) vs rata-rata blok (biru) per bin; kurva blok sebaiknya mengikuti komposit tetapi lebih halus. Selisih global &gt; 10% perlu dicek (top-cut, range, jumlah sampel). Koordinat swath = ruang pulih sesar.</div>';
  return h;}
