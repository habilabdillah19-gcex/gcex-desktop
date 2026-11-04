/* ================= GC-Ex Block Model: REPORTING BLOCK MODEL (grade × tonase dengan constraint) =================
   Port dari GC-Ex Drillhole (Reporting BM), disesuaikan dengan data GC-Ex Block Model:
   - Domain / volume : semua blok, atribut kategori block model, atau di dalam wireframe Data Referensi.
   - Permukaan       : di bawah topografi (sisa / remaining), atau di dalam desain pit (antara pit & topografi).
   - Batas DTM       : wireframe / DTM Data Referensi, di atas atau di bawahnya (mis. batas oksidasi, mined-out).
   - Elevasi & area  : RL min / maks; poligon dari string Surpac Data Referensi, string digitasi / dig block, boundary as-mined.
   - Filter atribut  : mis. kelas >= 1.
   Blok dihitung utuh berdasarkan titik pusat (seperti Surpac). SG mengikuti pengaturan Block Model > Filter & SG
   (SG tetap atau kolom SG, termasuk SG pengganti). Hasil: tabel per cut-off, ringkasan per RL / bench / kategori,
   kurva grade-tonase, CSV, dan opsi tampilkan hanya blok terlapor. */
(function(){if(window.RP||typeof BX==='undefined')return;
var RP=window.RP={o:null,res:null,sec:'1',ci:0,note:''};
var $=function(i){return document.getElementById(i);};
function rpE(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return '&#'+c.charCodeAt(0)+';';});}
function rpN(v,d){if(v==null||!isFinite(v))return '-';return(+v).toLocaleString('id-ID',{minimumFractionDigits:d||0,maximumFractionDigits:d||0});}
function rpUnitDef(a){var u=null;try{if(window.elUnit)u=elUnit(a);}catch(e){}if(u)return u;return /^(cu|zn|pb|fe|s|stot|scis|c|mn)(_|pct|$)/i.test(a)||/pct$/i.test(a)?'%':'g/t';}
function rpDate(){var d=new Date(),p=function(n){return(n<10?'0':'')+n;};return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());}
function rpFl(){try{if(window.lyBench&&BX.ui&&BX.ui.fl){var B=lyBench();if(B&&isFinite(B[0])&&isFinite(B[1])&&B[0]>B[1])return B;}}catch(e){}return null;}
function rpIsGrade(a){return !/^(x|y|z|xc|yc|zc|x_?cent|y_?cent|z_?cent|dx|dy|dz|xinc|yinc|zinc|sg|dens|density|bd|rock|class|kelas|est_|domain|id$|ijk)/i.test(a);}
function rpDef(){var m=BX.m,U=BX.ui||{},nums=Object.keys(m.num),gs=nums.filter(rpIsGrade);
  var g=m.num[U.attr]&&rpIsGrade(U.attr)?U.attr:(gs.filter(function(n){return /^au/i.test(n);})[0]||gs[0]||nums[0]);
  var at=[g];gs.forEach(function(n){if(at.indexOf(n)<0&&at.length<4)at.push(n);});var u={};at.forEach(function(a){u[a]=rpUnitDef(a);});
  var F=rpFl(),bh=F?Math.round((F[0]-F[1])*1000)/1000:5,ref=F?F[0]:0;
  return{gr:g,atts:at,unit:u,dom:'all',cat:{},surf:(window.OV&&OV.topoF&&OV.topoF.x&&OV.topoF.x.length)?'topo':'none',z0:'',z1:'',poly:'',polyOut:false,fA:'',fOp:'ge',fV:'',
    cuts:'0, 0.3, 0.5, 1, 2',grp:'bench',bh:bh,bref:ref,catAttr:'',show:false,sx:[],frac:true};}
function rpO(){if(!BX.m)return null;if(!RP.o||RP.o._m!==BX.m.name){RP.o=rpDef();RP.o._m=BX.m.name;}return RP.o;}
/* permukaan dari titik / kontur (koordinat lokal) -> z IDW, dicache per kolom blok */
function rpSurf(o){var B=10,cells={};for(var i=0;i<o.x.length;i++){if(o.x[i]===null||o.x[i]===undefined)continue;var k=(Math.floor(o.x[i]/B)+50000)*100000+Math.floor(o.y[i]/B)+50000;(cells[k]||(cells[k]=[])).push(i);}
  return function(x,y){var cx=Math.floor(x/B),cy=Math.floor(y/B);for(var R=1;R<=3;R++){var sw=0,sz=0,np=0,rm=R*B*R*B;for(var a=cx-R;a<=cx+R;a++)for(var b=cy-R;b<=cy+R;b++){var L=cells[(a+50000)*100000+b+50000];if(!L)continue;
      for(var k2=0;k2<L.length;k2++){var q=L[k2],dx=o.x[q]-x,dy=o.y[q]-y,d2=dx*dx+dy*dy;if(d2>rm)continue;if(d2<1e-4)return o.z[q];var w=1/d2;sw+=w;sz+=w*o.z[q];np++;}}if(np>=3)return sz/sw;}return null;};}
/* DTM segitiga (wireframe Data Referensi, koordinat dunia) -> [z min, z maks] di (x,y) */
var RPTIN=new WeakMap();
function rpTinFn(T){if(!T||!T.v||!T.t)return null;if(RPTIN.has(T))return RPTIN.get(T);var V=T.v,Tr=T.t,nt=Tr.length/3,x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,i;
  for(i=0;i<V.length;i+=3){if(V[i]<x0)x0=V[i];if(V[i]>x1)x1=V[i];if(V[i+1]<y0)y0=V[i+1];if(V[i+1]>y1)y1=V[i+1];}
  var B=Math.max(1,Math.min(100,Math.sqrt(Math.max(1,(x1-x0)*(y1-y0))/Math.max(1,nt))*2)),nx=Math.floor((x1-x0)/B)+1,cells=new Map();
  for(var t=0;t<nt;t++){var a=Tr[t*3]*3,b=Tr[t*3+1]*3,c=Tr[t*3+2]*3,ax=Math.min(V[a],V[b],V[c]),bx=Math.max(V[a],V[b],V[c]),ay=Math.min(V[a+1],V[b+1],V[c+1]),by=Math.max(V[a+1],V[b+1],V[c+1]);
    for(var cx=Math.floor((ax-x0)/B);cx<=Math.floor((bx-x0)/B);cx++)for(var cy=Math.floor((ay-y0)/B);cy<=Math.floor((by-y0)/B);cy++){var k=cy*nx+cx,L=cells.get(k);if(!L)cells.set(k,L=[]);L.push(t);}}
  var fn=function(x,y){if(x<x0||x>x1||y<y0||y>y1)return null;var L=cells.get(Math.floor((y-y0)/B)*nx+Math.floor((x-x0)/B));if(!L)return null;var lo=Infinity,hi=-Infinity;
    for(var j=0;j<L.length;j++){var t2=L[j],a2=Tr[t2*3]*3,b2=Tr[t2*3+1]*3,c2=Tr[t2*3+2]*3,X1=V[a2],Y1=V[a2+1],X2=V[b2],Y2=V[b2+1],X3=V[c2],Y3=V[c2+1],d=(Y2-Y3)*(X1-X3)+(X3-X2)*(Y1-Y3);if(Math.abs(d)<1e-12)continue;
      var l1=((Y2-Y3)*(x-X3)+(X3-X2)*(y-Y3))/d,l2=((Y3-Y1)*(x-X3)+(X1-X3)*(y-Y3))/d,l3=1-l1-l2,e=-1e-9;if(l1<e||l2<e||l3<e)continue;var z=l1*V[a2+2]+l2*V[b2+2]+l3*V[c2+2];if(z<lo)lo=z;if(z>hi)hi=z;}
    return hi>-Infinity?[lo,hi]:null;};RPTIN.set(T,fn);return fn;}
/* titik di dalam solid tertutup (wireframe, koordinat lokal): hitung perpotongan sinar ke atas */
function rpInside(m){if(m._rpIn)return m._rpIn;if(window.mdLocal)mdLocal(m);var X=m._x,Y=m._y,Z=m._z,I=m._i,J=m._j,K=m._k,nt=m.nt,x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(var i=0;i<m.nv;i++){x0=Math.min(x0,X[i]);x1=Math.max(x1,X[i]);y0=Math.min(y0,Y[i]);y1=Math.max(y1,Y[i]);}
  var cs=Math.max(0.5,Math.sqrt((x1-x0)*(y1-y0)/Math.max(1,nt/3))),nx=Math.max(1,Math.ceil((x1-x0)/cs)),ny=Math.max(1,Math.ceil((y1-y0)/cs));while(nx*ny>2e6){cs*=1.5;nx=Math.ceil((x1-x0)/cs);ny=Math.ceil((y1-y0)/cs);}
  var Gd=new Array(nx*ny);for(var t=0;t<nt;t++){var a=I[t],b=J[t],c=K[t],gx0=Math.floor((Math.min(X[a],X[b],X[c])-x0)/cs),gx1=Math.floor((Math.max(X[a],X[b],X[c])-x0)/cs),gy0=Math.floor((Math.min(Y[a],Y[b],Y[c])-y0)/cs),gy1=Math.floor((Math.max(Y[a],Y[b],Y[c])-y0)/cs);
    for(var gy=Math.max(0,gy0);gy<=Math.min(ny-1,gy1);gy++)for(var gx=Math.max(0,gx0);gx<=Math.min(nx-1,gx1);gx++){var k=gy*nx+gx;(Gd[k]||(Gd[k]=[])).push(t);}}
  var f=function(px,py,pz){px+=1.37e-6;py+=2.71e-6;var gx=Math.floor((px-x0)/cs),gy=Math.floor((py-y0)/cs);if(gx<0||gy<0||gx>=nx||gy>=ny)return false;var L=Gd[gy*nx+gx];if(!L)return false;var cnt=0;
    for(var q=0;q<L.length;q++){var t=L[q],a=I[t],b=J[t],c=K[t],ax=X[a],ay=Y[a],bx=X[b],by=Y[b],cx=X[c],cy=Y[c],den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy);if(Math.abs(den)<1e-12)continue;
      var l1=((by-cy)*(px-cx)+(cx-bx)*(py-cy))/den,l2=((cy-ay)*(px-cx)+(ax-cx)*(py-cy))/den,l3=1-l1-l2;if(l1<0||l2<0||l3<0)continue;if(l1*Z[a]+l2*Z[b]+l3*Z[c]>pz)cnt++;}return(cnt&1)===1;};
  return(m._rpIn={f:f});}
function rpPip(P,x,y){var c=false,n=P.length;for(var i=0,j=n-1;i<n;j=i++){var a=P[i],b=P[j];if(((a[1]>y)!==(b[1]>y))&&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]))c=!c;}return c;}
function rpBB(P){var b=[1e18,-1e18,1e18,-1e18];P.forEach(function(p){b[0]=Math.min(b[0],p[0]);b[1]=Math.max(b[1],p[0]);b[2]=Math.min(b[2],p[1]);b[3]=Math.max(b[3],p[1]);});return b;}
function rpStrGroups(S){var segs=[],cur=[],si=0;for(var i=0;i<S.x.length;i++){if(isNaN(S.x[i])||S.x[i]===null){if(cur.length)segs.push({sn:S.sn?S.sn[si]:0,p:cur});cur=[];si++;continue;}cur.push([S.x[i],S.y[i]]);}if(cur.length)segs.push({sn:S.sn?S.sn[si]:0,p:cur});return segs;}
/* sumber poligon: [id, label, fungsi pembuat daftar ring (koordinat lokal)] */
function rpPolySrc(){var L=[],loc=function(S){var x0=window.offX||0,y0=window.offY||0;return S.map(function(p){return[p[0]-x0,p[1]-y0];});};
  (window.MD&&MD.str||[]).forEach(function(S,i){var g=rpStrGroups(S).filter(function(q){return q.p.length>=3;}),sn={};g.forEach(function(q){sn[q.sn]=(sn[q.sn]||0)+1;});var ks=Object.keys(sn).sort(function(a,b){return a-b;});if(!ks.length)return;
    /* string Data Referensi: deteksi koordinat dunia vs lokal */
    var wd=Math.abs(g[0].p[0][0])>1e5||Math.abs(g[0].p[0][1])>1e5;
    L.push(['st:'+i+':*','String '+S.name+(ks.length>1?' (semua nomor)':'')+' · '+g.length+' segmen',function(){return g.map(function(q){return wd?loc(q.p):q.p;});}]);
    if(ks.length>1)ks.forEach(function(k){L.push(['st:'+i+':'+k,'String '+S.name+' · nomor '+k,function(){return g.filter(function(q){return String(q.sn)===k;}).map(function(q){return wd?loc(q.p):q.p;});}]);});});
  var D=(window.DG&&DG.S||[]).filter(function(s){return s.closed&&!s.inner&&s.pts&&s.pts.length>=3;});
  if(D.length){var by={};D.forEach(function(s){(by[s.no]||(by[s.no]=[])).push(s);});
    L.push(['dg:*','String digitasi / dig block (semua tertutup) · '+D.length,function(){return D.map(function(s){return s.pts;});}]);
    Object.keys(by).sort(function(a,b){return a-b;}).forEach(function(k){if(Object.keys(by).length>1)L.push(['dg:'+k,'String digitasi nomor '+k+' · '+by[k].length+' poligon',function(){return by[k].map(function(s){return s.pts;});}]);});}
  var A=[];try{if(window.amBndAll)A=amBndAll().filter(function(x){return x.on!==false&&x.pts&&x.pts.length>=3;});}catch(e){}
  if(A.length)L.push(['am:*','Boundary as-mined (semua aktif) · '+A.length,function(){return A.map(function(x){return x.pts;});}]);
  return L;}
function rpPoly(id){var s=rpPolySrc().filter(function(p){return p[0]===id;})[0];if(!s)return null;var R=s[2]().map(function(P){return{p:P,b:rpBB(P)};});if(!R.length)return null;
  return{name:s[1].replace(/ · .*$/,''),f:function(x,y){for(var k=0;k<R.length;k++){var g=R[k];if(x<g.b[0]||x>g.b[1]||y<g.b[2]||y>g.b[3])continue;if(rpPip(g.p,x,y))return true;}return false;}};}
function rpDomList(){var L=[['all','Semua blok (tanpa batas domain)']],m=BX.m;Object.keys(m.cat).forEach(function(k){L.push(['cat:'+k,'Atribut kategori: '+k]);});(window.MD&&MD.models||[]).forEach(function(w,i){L.push(['wf:'+i,'Di dalam wireframe: '+w.name]);});return L;}
function rpDomFn(o,m){var v=o.dom;if(!v||v==='all')return{f:null,lab:'semua blok'};
  if(v.indexOf('cat:')===0){var C=m.cat[v.slice(4)];if(!C)return{f:null,lab:''};var on=o.cat||{},sel=C.dict.map(function(s){return on[s]!==false;});return{f:function(i){var c=C.codes[i];return c!==65535&&sel[c];},lab:v.slice(4)+' = '+C.dict.filter(function(s,k){return sel[k];}).join(', ')};}
  if(v.indexOf('wf:')===0){var w=MD.models[+v.slice(3)];if(!w)throw new Error('Wireframe tidak ditemukan.');var W=rpInside(w);return{f:function(i,x,y,z){return W.f(x,y,z);},lab:'di dalam wireframe '+w.name};}return{f:null,lab:''};}
function rpSurfList(){return(window.MD&&MD.models||[]).map(function(w,i){return['wf:'+i,w.name];});}
function rpRun(){var m=BX.m,o=rpO();if(!m||!o)return;RP.note='';var t0=performance.now(),msg=$('rpMsg');
  try{var cuts=String(o.cuts).split(/[;, ]+/).map(function(s){return parseFloat(String(s).replace(',','.'));}).filter(isFinite).sort(function(a,b){return a-b;});if(!cuts.length)cuts=[0];
    var G=m.num[o.gr];if(!G)throw new Error('Pilih atribut kadar untuk cut-off.');var atts=o.atts.filter(function(a){return m.num[a];});if(atts.indexOf(o.gr)<0)atts.unshift(o.gr);
    var D=rpDomFn(o,m),tz=null,pz=null,cache={},offx=window.offX||0,offy=window.offY||0;
    if(o.surf==='topo'||o.surf==='pit'){if(!(OV.topoF&&OV.topoF.x&&OV.topoF.x.length))throw new Error('Topografi belum ada (Data Spasial › Topografi).');tz=rpSurf(OV.topoF);}
    if(o.surf==='pit'){if(!(OV.pitF&&OV.pitF.x&&OV.pitF.x.length))throw new Error('Desain pit belum ada (Data Spasial › Desain pit).');pz=rpSurf(OV.pitF);}
    var SX=(o.sx||[]).map(function(q){var w=MD.models[+String(q.k).slice(3)],fn=w&&rpTinFn(w);if(!fn)throw new Error('Batas DTM tambahan tidak ditemukan. Hapus barisnya atau import ulang.');return{fn:fn,n:w.name,side:q.side,c:{}};});
    var z0=parseFloat(o.z0),z1=parseFloat(o.z1),PL=o.poly?rpPoly(o.poly):null,FA=o.fA&&m.num[o.fA]?m.num[o.fA]:null,fv=parseFloat(o.fV),U=BX.ui||{},SGA=U.sgCol&&m.num[U.sgCol]?m.num[U.sgCol]:null;
    if(o.poly&&!PL)throw new Error('Poligon area tidak ditemukan.');
    var grp=o.grp,bh=Math.max(0.1,+o.bh||5),br=+o.bref||0;
    var GC=grp==='cat'&&m.cat[o.catAttr]?m.cat[o.catAttr]:null;
    /* sb_frac = proporsi volume blok yang benar-benar di dalam solid (sub-blocking GC-Ex Drill Hole).
       TANPA pembobotan ini, blok perbatasan dihitung 100% sehingga tonase di Block Model berbeda dari
       laporan Drill Hole untuk block model yang sama -- justru dilusi batas yang sudah diukur jadi hilang. */
    var FRA=(o.frac!==false&&m.num['sb_frac'])?m.num['sb_frac']:null,FR=[],nPart=0;
    var n=m.n,mask=new Uint8Array(n),T=[],I=[],Kg=[],nb=0,nOut={dom:0,surf:0,ext:0,z:0,poly:0,f:0,nan:0,sg:0},pOut=!!o.polyOut;
    for(var i=0;i<n;i++){var x=m.x[i]-offx,y=m.y[i]-offy,z=m.z[i];
      if(z0===z0&&z<z0||z1===z1&&z>z1){nOut.z++;continue;}
      if(PL&&PL.f(x,y)===pOut){nOut.poly++;continue;}
      if(FA){var fa=FA[i];if(!isFinite(fa)||(o.fOp==='ge'?fa<fv:o.fOp==='le'?fa>fv:o.fOp==='eq'?Math.abs(fa-fv)>1e-9:false)){nOut.f++;continue;}}
      var ck=Math.round(x*2)+'|'+Math.round(y*2);
      if(tz){var c=cache[ck];if(!c)c=cache[ck]=[tz(x,y),pz?pz(x,y):null];if(c[0]!==null&&z>c[0]){nOut.surf++;continue;}if(pz){if(c[1]===null||z<c[1]){nOut.surf++;continue;}}}
      if(SX.length){var bad=0;for(var s2=0;s2<SX.length;s2++){var S2=SX[s2],r2=S2.c[ck];if(r2===undefined)r2=S2.c[ck]=S2.fn(m.x[i],m.y[i]);if(r2===null){bad=1;break;}if(S2.side==='above'?z<=r2[0]:z>=r2[1]){bad=2;break;}}if(bad){if(bad===1)nOut.ext++;else nOut.surf++;continue;}}
      if(D.f&&!D.f(i,x,y,z)){nOut.dom++;continue;}
      var g=G[i];if(!isFinite(g)||g<=-90){nOut.nan++;continue;}
      var sg=window.bxSGv?bxSGv(SGA?SGA[i]:NaN):(+U.sg||2.6);if(!(sg>0)){nOut.sg++;continue;}
      var fr=1;if(FRA){var fv2=FRA[i];fr=(isFinite(fv2)&&fv2>=0&&fv2<=1)?fv2:1;if(fr<=0){nOut.frac=(nOut.frac||0)+1;continue;}if(fr<0.999)nPart++;}
      mask[i]=1;T.push(m.sx[i]*m.sy[i]*m.sz[i]*sg*fr);I.push(i);FR.push(fr);
      Kg.push(grp==='bench'?Math.floor((z-br)/bh+1e-9):grp==='cat'?(GC&&GC.codes[i]!==65535?GC.dict[GC.codes[i]]:'(kosong)'):'Total');nb++;}
    var agg=function(filt){var R={};for(var j=0;j<I.length;j++){var i2=I[j];if(!filt(i2))continue;var k=Kg[j],r=R[k]||(R[k]={n:0,v:0,t:0,s:{}});var t=T[j];r.n++;r.t+=t;r.v+=m.sx[i2]*m.sy[i2]*m.sz[i2]*(FR.length?FR[j]:1);
        atts.forEach(function(a){var v=m.num[a][i2];if(isFinite(v)&&v>-90){var q=r.s[a]||(r.s[a]={tw:0,w:0});q.tw+=t*v;q.w+=t;}});}return R;};
    var rows=cuts.map(function(c){return{c:c,G:agg(function(i2){return G[i2]>=c;})};});
    BX.rpMask=mask;BX.rpVer=(BX.rpVer||0)+1;
    var big=m.mdl&&m.mdl.via==='backend';
    RP.res={rows:rows,cuts:cuts,atts:atts,unit:Object.assign({},o.unit),nb:nb,nOut:nOut,lab:D.lab,ms:Math.round(performance.now()-t0),grp:grp,bh:bh,br:br,surf:o.surf,
      sxD:SX.map(function(q){return(q.side==='above'?'di atas ':'di bawah ')+q.n;}),poly:PL&&((pOut?'di luar ':'di dalam ')+PL.name),z0:o.z0,z1:o.z1,f:FA?o.fA+' '+{ge:'≥',le:'≤',eq:'='}[o.fOp]+' '+o.fV:'',gr:o.gr,
      frac:FRA?('proporsi volume sub-blok (sb_frac): '+rpN(nPart)+' blok sebagian'):(m.num['sb_frac']?'sb_frac ADA tetapi pembobotan dimatikan':''),nPart:nPart,
      sg:SGA?'SG kolom '+U.sgCol:'SG '+(+U.sg||2.6),date:new Date().toLocaleString('id-ID'),bm:m.name,big:big,nTot:n};
    RP.sec='2';RP.ci=Math.min(RP.ci||0,rows.length-1);if(o.show){BX.rpOnly=true;BX.sc={};updatePlot();}rpPanel();}
  catch(e){console.error(e);if(msg)msg.innerHTML='<span class=warn>'+rpE(e.message)+'</span>';else alert(e.message);}}
function rpMetal(a,t,g,u){if(u==='%')return t*g/100;if(u==='ppb')return t*g/1000;return t*g;}
function rpMetU(u){return u==='%'?'t logam':'gram';}
function rpTot(G){var r={n:0,v:0,t:0,s:{}};Object.keys(G).forEach(function(k){var a=G[k];r.n+=a.n;r.v+=a.v;r.t+=a.t;Object.keys(a.s).forEach(function(at){var q=r.s[at]||(r.s[at]={tw:0,w:0});q.tw+=a.s[at].tw;q.w+=a.s[at].w;});});return r;}
function rpBenchLab(R,k){var lo=R.br+k*R.bh,hi=lo+R.bh;return 'RL '+rpN(hi,1)+' – '+rpN(lo,1);}
function rpTable(){var R=RP.res;if(!R)return '';var at=R.atts,h='<div class=rpwrap><table class="pltb rptb"><tr><th>Cut-off<br><small>'+rpE(R.gr)+'</small></th><th>Blok</th><th>Volume<br><small>m³</small></th><th>Tonase<br><small>t</small></th>'+
    at.map(function(a){return '<th>'+rpE(a)+'<br><small>'+rpE(R.unit[a]||'g/t')+'</small></th><th>Logam<br><small>'+rpMetU(R.unit[a])+'</small></th>';}).join('')+'</tr>';
  R.rows.forEach(function(r){var T=rpTot(r.G);h+='<tr><td>≥ '+r.c+'</td><td>'+rpN(T.n)+'</td><td>'+rpN(T.v)+'</td><td><b>'+rpN(T.t)+'</b></td>'+at.map(function(a){var q=T.s[a],g=q&&q.w?q.tw/q.w:NaN;return '<td><b>'+rpN(g,3)+'</b></td><td>'+rpN(isFinite(g)?rpMetal(a,T.t,g,R.unit[a]):NaN,R.unit[a]==='%'?1:0)+'</td>';}).join('')+'</tr>';});
  return h+'</table></div>';}
function rpGroupTable(ci){var R=RP.res;if(!R||R.grp==='none')return '';var r=R.rows[ci]||R.rows[0],at=R.atts,keys=Object.keys(r.G);
  keys.sort(function(a,b){return R.grp==='bench'?(+b)-(+a):String(a).localeCompare(String(b));});
  var lab=function(k){return R.grp==='bench'?rpBenchLab(R,+k):k;};
  var h='<div class=rpwrap><table class="pltb rptb"><tr><th>'+(R.grp==='bench'?'RL (atas – bawah)':'Kategori')+'</th><th>Blok</th><th>Tonase t</th>'+at.map(function(a){return '<th>'+rpE(a)+'</th><th>Logam</th>';}).join('')+'</tr>';
  keys.forEach(function(k){var g=r.G[k];h+='<tr><td>'+rpE(lab(k))+'</td><td>'+rpN(g.n)+'</td><td>'+rpN(g.t)+'</td>'+at.map(function(a){var q=g.s[a],v=q&&q.w?q.tw/q.w:NaN;return '<td>'+rpN(v,3)+'</td><td>'+rpN(isFinite(v)?rpMetal(a,g.t,v,R.unit[a]):NaN,R.unit[a]==='%'?1:0)+'</td>';}).join('')+'</tr>';});
  var T=rpTot(r.G);h+='<tr class=tot><td>Total</td><td>'+rpN(T.n)+'</td><td>'+rpN(T.t)+'</td>'+at.map(function(a){var q=T.s[a],v=q&&q.w?q.tw/q.w:NaN;return '<td>'+rpN(v,3)+'</td><td>'+rpN(isFinite(v)?rpMetal(a,T.t,v,R.unit[a]):NaN,R.unit[a]==='%'?1:0)+'</td>';}).join('')+'</tr>';
  return h+'</table></div>';}
function rpChart(){var R=RP.res,el=$('rpGT');if(!R||!el||!window.Plotly)return;var g=R.gr,X=R.cuts,Tn=[],Gr=[];R.rows.forEach(function(r){var T=rpTot(r.G),q=T.s[g];Tn.push(T.t/1000);Gr.push(q&&q.w?q.tw/q.w:null);});
  var dk=document.body.classList.contains('dark')||($('darkMode')&&$('darkMode').checked),fg=dk?'#dbe3ec':'#1c2733',gr=dk?'#2a3746':'#e3e8ee';
  Plotly.react(el,[{type:'bar',x:X.map(String),y:Tn,name:'Tonase (kt)',marker:{color:'#233a7e'},hovertemplate:'≥ %{x}: %{y:,.1f} kt<extra></extra>'},{type:'scatter',mode:'lines+markers',x:X.map(String),y:Gr,name:'Kadar '+g,yaxis:'y2',line:{color:'#e8590c',width:2.5},hovertemplate:'≥ %{x}: %{y:.3f}<extra></extra>'}],
    {height:240,margin:{l:48,r:46,t:30,b:40},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{size:10,color:fg},xaxis:{title:{text:'Cut-off '+g},type:'category',gridcolor:gr},yaxis:{title:{text:'Tonase (kt)'},gridcolor:gr},yaxis2:{title:{text:'Kadar'},overlaying:'y',side:'right',showgrid:false},legend:{orientation:'h',x:0,y:1.18}},{displaylogo:false,responsive:true,displayModeBar:false});}
function rpDesc(){var R=RP.res;if(!R)return '';return [R.lab,R.surf==='topo'?'di bawah topografi (sisa)':R.surf==='pit'?'di dalam desain pit & di bawah topografi':'',(R.sxD||[]).join(', '),(R.z0!==''||R.z1!=='')?'RL '+(R.z0||'…')+' – '+(R.z1||'…'):'',R.poly?'poligon '+R.poly:'',R.f,R.sg,R.frac].filter(Boolean).join(' · ');}
function rpCsv(){var R=RP.res;if(!R)return;var at=R.atts,L=['# Reporting block model GC-Ex Block Model','# Block model: '+R.bm,'# Constraint: '+rpDesc(),'# Tanggal: '+R.date];
  L.push(['CUTOFF','GRUP','BLOK','VOLUME_M3','TONASE_T'].concat(at.map(function(a){return a+'_'+(R.unit[a]||'g/t').replace('/','_');}),at.map(function(a){return 'LOGAM_'+a+'_'+(R.unit[a]==='%'?'T':'G');})).join(','));
  R.rows.forEach(function(r){var ks=Object.keys(r.G).sort(function(a,b){return R.grp==='bench'?(+b)-(+a):String(a).localeCompare(String(b));});ks.forEach(function(k){var g=r.G[k];L.push([r.c,'"'+(R.grp==='bench'?rpBenchLab(R,+k):k)+'"',g.n,g.v.toFixed(1),g.t.toFixed(1)].concat(at.map(function(a){var q=g.s[a];return q&&q.w?(q.tw/q.w).toFixed(4):'';}),at.map(function(a){var q=g.s[a];return q&&q.w?rpMetal(a,g.t,q.tw/q.w,R.unit[a]).toFixed(2):'';})).join(','));});
    var T=rpTot(r.G);L.push([r.c,'TOTAL',T.n,T.v.toFixed(1),T.t.toFixed(1)].concat(at.map(function(a){var q=T.s[a];return q&&q.w?(q.tw/q.w).toFixed(4):'';}),at.map(function(a){var q=T.s[a];return q&&q.w?rpMetal(a,T.t,q.tw/q.w,R.unit[a]).toFixed(2):'';})).join(','));});
  dgDl(L.join('\r\n')+'\r\n','Reporting_BM_'+String(R.bm).replace(/[^A-Za-z0-9_-]+/g,'_')+'_'+rpDate()+'.csv','text/csv');}
function rpSet(k,v){var o=rpO();o[k]=v;if(k==='dom')o.cat={};rpPanel();}
function rpAtt(a,on){var o=rpO(),i=o.atts.indexOf(a);if(on&&i<0){o.atts.push(a);o.unit[a]=o.unit[a]||rpUnitDef(a);}if(!on&&i>=0)o.atts.splice(i,1);rpPanel();}
function rpSx(i,k,v){var o=rpO();o.sx=o.sx||[];if(k==='del')o.sx.splice(i,1);else if(k==='add')o.sx.push({k:(rpSurfList()[0]||[''])[0],side:'below'});else o.sx[i][k]=v;rpPanel();}
function rpShow(on){if(on&&!BX.rpMask){var o0=rpO();if(o0){o0.show=true;rpRun();}return;}BX.rpOnly=!!on;var o=rpO();if(o)o.show=!!on;BX.sc={};if(on&&$('bxShow'))$('bxShow').checked=true;updatePlot();rpPanel();}
async function rpImpWf(inp){var o=rpO(),n0=MD.models.length;await mdImport(inp);for(var i=n0;i<MD.models.length;i++)o.sx.push({k:'wf:'+i,side:'below'});RP.note=($('mdMsg')||{}).innerHTML||'';rpPanel();}
async function rpImpStr(inp){var o=rpO(),n0=MD.str.length;await mdStr(inp);if(MD.str.length>n0)o.poly='st:'+n0+':*';RP.note=($('mdMsg')||{}).innerHTML||'';rpPanel();}
function rpFlNow(){var o=rpO(),F=rpFl();if(!F){alert('Belum ada flitch aktif (langkah Flitch Aktif).');return;}o.bh=Math.round((F[0]-F[1])*1000)/1000;o.bref=F[0];o.grp='bench';rpPanel();}
function rpPanel(){var b=$('rpBody');if(!b)return;var m=window.BX&&BX.m;if(!m){b.innerHTML='<div class="box gmstate">Belum ada block model. Import lewat langkah <b>Block Model</b>.</div>';return;}
  var o=rpO(),nums=Object.keys(m.num),sel=function(id,opts,val,on){return '<select '+(id?'id='+id+' ':'')+'onchange="'+on+'">'+opts.map(function(p){return '<option value="'+rpE(p[0])+'"'+(String(p[0])===String(val)?' selected':'')+'>'+rpE(p[1])+'</option>';}).join('')+'</select>';};
  var big=m.mdl&&m.mdl.via==='backend',h='<div class=hint style="margin:-2px 0 8px">Hitung <b>tonase × kadar</b> block model <b>'+rpE(m.name)+'</b> ('+rpN(m.n)+' blok dimuat) yang dibatasi <b>constraint</b>. Blok dihitung utuh berdasarkan titik pusatnya (seperti Surpac).'+
    (big?' <span class=warn>Block model .mdl besar: hanya blok yang dimuat (rentang RL saat import) yang dihitung.</span>':'')+'</div>';
  h+='<div class="uitabs rptabs"><button class="'+(RP.sec==='1'?'on':'')+'" onclick="RP.sec=\'1\';rpPanel()">&#9312; Atribut</button><button class="'+(RP.sec==='c'?'on':'')+'" onclick="RP.sec=\'c\';rpPanel()">&#9313; Constraint</button><button class="'+(RP.sec==='2'?'on':'')+'" onclick="RP.sec=\'2\';rpPanel()">&#9314; Hasil</button></div>';
  if(RP.sec==='1'){
    h+='<h4>Atribut yang dilaporkan</h4><div class=hint>Centang atribut kadar dan satuannya. Logam: g/t &amp; ppm &rarr; gram; % &rarr; ton logam.</div><div class=rpatt>'+nums.map(function(a){var on=o.atts.indexOf(a)>=0;return '<div class="rpa'+(on?' on':'')+'"><label><input type=checkbox '+(on?'checked':'')+' onchange="rpAtt(\''+rpE(a)+'\',this.checked)"> '+rpE(a)+'</label>'+(on?sel('',[['g/t','g/t'],['ppm','ppm'],['ppb','ppb'],['%','%']],o.unit[a]||'g/t',"RP.o.unit['"+rpE(a)+"']=this.value"):'')+'</div>';}).join('')+'</div>';
    h+='<div class="g2 f"><div><label>Atribut untuk cut-off</label>'+sel('',nums.map(function(a){return[a,a];}),o.gr,"rpSet('gr',this.value)")+'</div><div><label>Cut-off (pisah koma)</label><input type=text value="'+rpE(o.cuts)+'" onchange="RP.o.cuts=this.value"></div></div>';
    var U=BX.ui||{};h+='<div class=hint>Densitas: <b>'+(U.sgCol?'kolom '+rpE(U.sgCol):'SG tetap '+rpE(U.sg||2.6))+'</b> — ikut pengaturan <a href="#" onclick="PT&&PT.select(\'bm.flt\');return false">Block Model › Filter &amp; SG</a>.</div>';
    h+='<h4>Ringkasan per RL / pengelompokan</h4><div class="g2 f"><div>'+sel('',[['none','Tanpa grup'],['bench','Per RL (bench / flitch)']].concat(Object.keys(m.cat).length?[['cat','Per atribut kategori']]:[]),o.grp,"rpSet('grp',this.value)")+'</div><div>'+(o.grp==='cat'?sel('',Object.keys(m.cat).map(function(k){return[k,k];}),o.catAttr||Object.keys(m.cat)[0],"RP.o.catAttr=this.value"):'')+'</div></div>';
    if(m.num['sb_frac'])h+='<label class=sw><input type=checkbox '+(o.frac!==false?'checked':'')+' onchange="RP.o.frac=this.checked"> Timbang volume &amp; tonase dengan proporsi sub-blok (<code>sb_frac</code>)</label><div class=hint style="margin-top:-4px">Block model ini pernah dipecah di batas solid oleh GC-Ex Drill Hole. Dengan pembobotan ini, blok perbatasan dihitung <b>sebagian</b> &mdash; angkanya sama dengan laporan di Drill Hole. Dimatikan = blok perbatasan dihitung utuh (cara Surpac).</div>';
    if(o.grp==='bench')h+='<div class="g3 f"><div><label>Tinggi (m)</label><input type=number step=any value="'+rpE(o.bh)+'" onchange="RP.o.bh=+this.value"></div><div><label>RL acuan</label><input type=number step=any value="'+rpE(o.bref)+'" onchange="RP.o.bref=+this.value" title="Batas bench / flitch dihitung dari RL ini, mis. RL atas flitch"></div><div style="align-self:end"><button onclick="rpFlNow()" title="Tinggi & RL acuan = flitch aktif">= flitch aktif</button></div></div><div class=hint>Batas RL = RL acuan ± kelipatan tinggi. Blok masuk RL menurut titik pusatnya.</div>';
    h+='<button class=btn-pri style="width:100%;margin-top:6px" onclick="RP.sec=\'c\';rpPanel()">Lanjut: constraint &rarr;</button>';}
  else if(RP.sec==='c'){
    if(RP.note)h+='<div class="box gmstate">'+RP.note+'</div>';
    h+='<h4>Domain / volume</h4>'+sel('',rpDomList(),o.dom,"rpSet('dom',this.value)");
    if(o.dom.indexOf('cat:')===0){var C=m.cat[o.dom.slice(4)];if(C)h+='<div class=rpcat>'+C.dict.map(function(s,k){return '<label><input type=checkbox '+(o.cat[s]!==false?'checked':'')+' onchange="RP.o.cat[\''+rpE(s)+'\']=this.checked"> '+rpE(s)+(C.cnt?' <small>'+rpN(C.cnt[k])+'</small>':'')+'</label>';}).join('')+'</div>';}
    var hasT=window.OV&&OV.topoF&&OV.topoF.x&&OV.topoF.x.length,hasP=window.OV&&OV.pitF&&OV.pitF.x&&OV.pitF.x.length;
    h+='<h4>Permukaan (sisa / remaining)</h4>'+sel('',[['none','Tanpa batas permukaan'],['topo','Di bawah topografi (sisa / remaining)'],['pit','Di dalam desain pit (antara pit & topografi)']],o.surf,"rpSet('surf',this.value)")+
      '<div class=hint>Topografi: '+(hasT?'<b>ada</b>':'<span class=warn>belum ada</span>')+' · Desain pit: '+(hasP?'<b>ada</b>':'<i>belum ada</i>')+'. Ganti lewat <b>Data Spasial</b>. Blok dihitung bila titik pusatnya di bawah topografi (dan di atas pit).</div>';
    o.sx=o.sx||[];var SL=rpSurfList();
    h+='<h4>Batas DTM tambahan</h4>'+(o.sx.length?o.sx.map(function(q,i){return '<div class="g3 f"><div style="grid-column:span 2">'+sel('',SL.length?SL:[['','(tidak ada DTM)']],q.k,"rpSx("+i+",'k',this.value)")+'</div><div style="display:flex;gap:4px">'+sel('',[['below','di bawah'],['above','di atas']],q.side,"rpSx("+i+",'side',this.value)")+'<button class=x onclick="rpSx('+i+',\'del\')" title="Hapus">&times;</button></div></div>';}).join(''):'<div class=hint>Mis. di bawah batas oksidasi, di atas mined-out / survey akhir bulan (DTM di Data Referensi).</div>')+
      '<div class="g2 f">'+(SL.length?'<button onclick="rpSx(0,\'add\')">+ Tambah batas DTM</button>':'<span></span>')+'<label class="mdbtn" title="Import DTM / wireframe ke Data Referensi dan pakai sebagai batas">+ Import DTM<input type=file multiple accept=".dtm,.str,.dxf,.obj,.msh" style="display:none" onchange="rpImpWf(this)"></label></div>';
    h+='<h4>Elevasi &amp; area</h4><div class="g2 f"><div><label>RL min</label><input type=number step=any value="'+rpE(o.z0)+'" onchange="RP.o.z0=this.value" placeholder="tanpa batas"></div><div><label>RL maks</label><input type=number step=any value="'+rpE(o.z1)+'" onchange="RP.o.z1=this.value" placeholder="tanpa batas"></div></div>';
    var PLs=rpPolySrc().map(function(p){return[p[0],p[1]];});
    h+='<label>Poligon area</label><div class="g3 f"><div style="grid-column:span 2">'+sel('',[['','Tanpa poligon']].concat(PLs),o.poly,"RP.o.poly=this.value")+'</div><div>'+sel('',[['in','di dalam'],['out','di luar']],o.polyOut?'out':'in',"RP.o.polyOut=this.value==='out'")+'</div></div>'+
      '<div class="g2 f"><span class=hint style="margin:0">String Surpac, string digitasi / dig block, boundary as-mined.</span><label class="mdbtn">+ Import string<input type=file multiple accept=".str,.dxf" style="display:none" onchange="rpImpStr(this)"></label></div>';
    h+='<h4>Filter atribut (opsional)</h4><div class="g3 f"><div>'+sel('',[['','—']].concat(nums.map(function(a){return[a,a];})),o.fA,"rpSet('fA',this.value)")+'</div><div>'+sel('',[['ge','≥'],['le','≤'],['eq','=']],o.fOp,"RP.o.fOp=this.value")+'</div><div><input type=number step=any value="'+rpE(o.fV)+'" onchange="RP.o.fV=this.value" placeholder="nilai"></div></div>';
    h+='<label class=sw style="margin-top:6px"><input type=checkbox '+(o.show?'checked':'')+' onchange="RP.o.show=this.checked"> Tampilkan hanya blok terlapor</label>';
    h+='<button class=btn-pri id=rpGo style="width:100%;height:32px;margin-top:8px" onclick="rpRun()">&#9654; Hitung reporting</button><div id=rpMsg class=hint></div>';}
  else{var R=RP.res;if(!R){h+='<div class="box gmstate">Belum ada hasil. Atur atribut &amp; constraint lalu klik <b>Hitung reporting</b>.</div><button class=btn-pri style="width:100%" onclick="RP.sec=\'c\';rpPanel()">Ke constraint</button>';}
    else{h+='<div class="box gmstate rpsum"><b>'+rpN(R.nb)+' dari '+rpN(R.nTot)+' blok</b> memenuhi constraint ('+R.ms+' ms)<br><small>'+rpE(rpDesc())+'</small><br><small>Dikeluarkan: '+([['dom','domain'],['surf','permukaan'],['ext','di luar DTM'],['z','elevasi'],['poly','poligon'],['f','filter'],['nan','kadar kosong'],['sg','SG 0']].filter(function(p){return R.nOut[p[0]];}).map(function(p){return p[1]+' '+rpN(R.nOut[p[0]]);}).join(' · ')||'—')+'</small></div>';
      h+='<h4>Grade × tonase per cut-off</h4>'+rpTable()+'<div id=rpGT class=rpchart></div>';
      if(R.grp!=='none')h+='<h4>'+(R.grp==='bench'?'Ringkasan per RL':'Per kategori')+'</h4><div class="g2 f"><label style="align-self:center">Cut-off</label>'+sel('rpCi',R.rows.map(function(r,i){return[i,'≥ '+r.c];}),RP.ci||0,"RP.ci=+this.value;rpPanel()")+'</div>'+rpGroupTable(RP.ci||0);
      h+='<div class="g2 f" style="margin-top:8px"><button class=btn-pri onclick="rpCsv()">&#8681; Export CSV</button><button onclick="rpShow('+(BX.rpOnly?0:1)+')">'+(BX.rpOnly?'Tampilkan semua blok':'&#128065; Hanya blok terlapor')+'</button></div>';}}
  b.innerHTML=h;if(RP.sec==='2'&&RP.res)setTimeout(rpChart,30);}
/* tampilan block model: hanya blok terlapor */
if(typeof bxPass==='function'){var _p=bxPass;window.bxPass=bxPass=function(i){if(BX.rpOnly&&BX.rpMask&&BX.m&&BX.rpMask.length===BX.m.n&&!BX.rpMask[i])return false;return _p(i);};}
if(typeof bxSel==='function'){var _s=bxSel;window.bxSel=bxSel=function(o){var k=BX.rpOnly?'r'+BX.rpVer:'';if(BX._rpk!==k){BX._rpk=k;BX.sc={};}return _s(o);};}
/* panel & tab */
(function(){var side=$('side');if(!side||$('pRep'))return;var s=document.createElement('section');s.id='pRep';s.hidden=true;s.innerHTML='<h3>Reporting Block Model</h3><div id=rpBody></div>';side.appendChild(s);
  var _u=uiTab;window.uiTab=uiTab=function(n){if(n==='Rep'){var r=_u.call(this,'BM');$('pBM').hidden=true;var rb=$('rbBM');if(rb)rb.className='rb';s.hidden=false;rpPanel();return r;}s.hidden=true;return _u.apply(this,arguments);};
  var css=document.createElement('style');css.id='rpCss';css.textContent=
    '.rpatt{display:grid;grid-template-columns:1fr 1fr;gap:3px 8px;margin:4px 0 8px}.rpa{display:flex;align-items:center;gap:4px;min-width:0}.rpa label{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin:0}.rpa select{width:58px;min-height:22px}'+
    '.rpcat{display:flex;flex-wrap:wrap;gap:2px 10px;margin:4px 0}.rpwrap{overflow-x:auto;margin:4px 0 6px}.rptb{font-size:11px;width:100%;border-collapse:collapse}.rptb th{background:var(--pr,#233a7e);color:#fff;font-weight:600;padding:3px 4px;text-align:right;white-space:nowrap}.rptb th:first-child{text-align:left}'+
    '.rptb td{padding:2px 4px;text-align:right;border-bottom:1px solid var(--bd,#d5dbe3);font-variant-numeric:tabular-nums;white-space:nowrap}.rptb td:first-child{text-align:left}.rptb tr.tot td{font-weight:700;border-top:1.5px solid var(--tx,#1c2733)}.rpchart{height:240px}.rpsum small{color:var(--mu,#6b7785)}'+
    '#pRep .rptabs{display:flex;gap:3px}#pRep .rptabs button{flex:1}#pRep .rptabs button.on{background:var(--mj,#f0c047);border-color:var(--mjln,#d6a12b);color:#1d2b5e;font-weight:700}';
  document.head.appendChild(css);
  var _bp=window.bxPanel;if(_bp)window.bxPanel=bxPanel=function(){var r=_bp.apply(this,arguments);try{if(!s.hidden)rpPanel();}catch(e){}return r;};})();
Object.assign(window,{rpRun:rpRun,rpPanel:rpPanel,rpSet:rpSet,rpAtt:rpAtt,rpSx:rpSx,rpShow:rpShow,rpCsv:rpCsv,rpImpWf:rpImpWf,rpImpStr:rpImpStr,rpFlNow:rpFlNow,rpO:rpO});
})();
/* watermark hak cipta di setiap halaman PDF (dig plan, layout as-mined, report rekonsiliasi) */
(function(){if(typeof lyPdf!=='function'||window._wmPdf)return;window._wmPdf=1;var _l=lyPdf;
  lyPdf=window.lyPdf=function(pages){try{(pages||[]).forEach(function(pg){if(pg&&pg.ops&&pg.W&&!pg._wm){pg._wm=1;pg.ops.push({t:'text',x:pg.W-4,y:2.2,s:2,txt:window.GCEX_COPY||'Copyright Habil Abdillah 2026',col:'#8a94a3',anchor:'e'});}});}catch(e){}return _l.apply(this,arguments);};})();
