/* ================= ORE GEOMETRY (GC-Ex Drillhole) =================
   Referensi geologist untuk melihat deposit secara utuh SEBELUM pemodelan & estimasi.
   TIDAK menulis apa pun ke basis data struktur, Geological Modelling, maupun Model Estimation.
   ① Intercept otomatis per bor (cut-off, panjang min, dilusi) -> GT (kadar x m) dijumlah per bor, tebal sebenarnya terhadap bidang acuan
   ② Long section GT (bawaan vertikal, azimuth / dip bisa disetel): RBF spheroidal lokal 2D, kontur kelas GT, juga permukaan berwarna di 3D
   ③ Ore shoot: gambar sumbu di long section / usulan otomatis -> pitch, plunge / trend (hanya di menu ini; export CSV opsional)
   ④ Grade shell 3D: RBF indikator / numerik spheroidal lokal (Web Worker), N baris assay terbawah, marching tetrahedra, validasi, export OBJ / DXF */

/* ---------- mesin numerik (dipakai di halaman & di Web Worker) ---------- */
function OGENG(){var E={};
  E.kap=function(a){return Math.sqrt(Math.pow(0.04,-2/a)-1);};
  /* kovarians spheroidal (keluarga Cauchy umum, cov(range) = 0,04 -> 96 % sill di range); linear = -r */
  E.cov=function(kern,a){if(kern==='lin')return function(r2){return -Math.sqrt(r2);};var k2=Math.pow(E.kap(a),2),h=a/2;
    if(a===3)return function(r2){var q=1+k2*r2;return 1/(q*Math.sqrt(q));};return function(r2){return Math.pow(1+k2*r2,-h);};};
  /* indeks tetangga di ruang isotropik (range = 1) */
  E.index=function(P,d,n){var lo=[],hi=[],j,i;for(j=0;j<d;j++){lo[j]=1e18;hi[j]=-1e18;}
    for(i=0;i<n;i++)for(j=0;j<d;j++){var v=P[i*d+j];if(v<lo[j])lo[j]=v;if(v>hi[j])hi[j]=v;}
    var cs=1,D=[],nc=1;for(j=0;j<d;j++)nc*=Math.max(1,Math.floor(hi[j]-lo[j])+3);if(nc>2e7)cs=Math.cbrt(nc/2e7)*1.01;
    nc=1;for(j=0;j<d;j++){lo[j]=Math.floor(lo[j]/cs)-1;D[j]=Math.floor(hi[j]/cs)-lo[j]+2;nc*=D[j];}
    var cell=new Int32Array(n),cnt=new Int32Array(nc+1);
    for(i=0;i<n;i++){var c=0,m=1;for(j=0;j<d;j++){c+=(Math.floor(P[i*d+j]/cs)-lo[j])*m;m*=D[j];}cell[i]=c;cnt[c+1]++;}
    for(i=0;i<nc;i++)cnt[i+1]+=cnt[i];var pos=cnt.slice(0,nc),idx=new Int32Array(n);for(i=0;i<n;i++)idx[pos[cell[i]]++]=i;
    var R=Math.ceil(1/cs);return{P:P,d:d,n:n,cs:cs,lo:lo,D:D,st:cnt,idx:idx,R:R};};
  E.query=function(X,q,ci,cd){var d=X.d,cs=X.cs,R=X.R,c=[],j,k=0;for(j=0;j<d;j++)c[j]=Math.floor(q[j]/cs)-X.lo[j];
    var D=X.D,P=X.P;
    if(d===2){for(var a=c[0]-R;a<=c[0]+R;a++){if(a<0||a>=D[0])continue;for(var b=c[1]-R;b<=c[1]+R;b++){if(b<0||b>=D[1])continue;var cc=a+b*D[0];
          for(var s=X.st[cc],e=X.st[cc+1];s<e;s++){var p=X.idx[s],dx=P[p*2]-q[0],dy=P[p*2+1]-q[1],r2=dx*dx+dy*dy;if(r2<1){if(k<ci.length){ci[k]=p;cd[k]=r2;k++;}}}}}return k;}
    for(var a3=c[0]-R;a3<=c[0]+R;a3++){if(a3<0||a3>=D[0])continue;for(var b3=c[1]-R;b3<=c[1]+R;b3++){if(b3<0||b3>=D[1])continue;for(var z3=c[2]-R;z3<=c[2]+R;z3++){if(z3<0||z3>=D[2])continue;var c3=a3+D[0]*(b3+D[1]*z3);
          for(var s3=X.st[c3],e3=X.st[c3+1];s3<e3;s3++){var p3=X.idx[s3],ex=P[p3*3]-q[0],ey=P[p3*3+1]-q[1],ez=P[p3*3+2]-q[2],q2=ex*ex+ey*ey+ez*ez;if(q2<1){if(k<ci.length){ci[k]=p3;cd[k]=q2;k++;}}}}}}return k;};
  E.solve=function(A,b,m){for(var c=0;c<m;c++){var p=c,mx=Math.abs(A[c*m+c]);for(var r=c+1;r<m;r++){var v=Math.abs(A[r*m+c]);if(v>mx){mx=v;p=r;}}if(mx<1e-12)return false;
      if(p!==c){for(var k=0;k<m;k++){var t=A[c*m+k];A[c*m+k]=A[p*m+k];A[p*m+k]=t;}var tb=b[c];b[c]=b[p];b[p]=tb;}
      for(r=c+1;r<m;r++){var f=A[r*m+c]/A[c*m+c];if(f===0)continue;for(k=c;k<m;k++)A[r*m+k]-=f*A[c*m+k];b[r]-=f*b[c];}}
    for(c=m-1;c>=0;c--){var s=b[c];for(k=c+1;k<m;k++)s-=A[c*m+k]*b[k];b[c]=s/A[c*m+c];}return true;};
  /* RBF lokal (kovarians + konstanta, setara kriging lokal) pada grid; o: {d,P(iso),V,n,M(dxd),c,org,nn,st,k,alpha,nug,kern,clamp} */
  E.interp=function(o,prog){var d=o.d,X=E.index(o.P,d,o.n),cov=E.cov(o.kern,o.alpha),nug=o.kern==='lin'?0:Math.max(0,Math.min(0.95,+o.nug||0)),sill=1-nug;
    var K=Math.max(4,o.k|0),ci=new Int32Array(4000),cd=new Float64Array(4000),m=K+1,A=new Float64Array(m*m),b=new Float64Array(m),sel=new Int32Array(K),M=o.M,c=o.c,P=o.P,V=o.V;
    var nx=o.nn[0],ny=o.nn[1],nz=d===3?o.nn[2]:1,N=nx*ny*nz,out=new Float32Array(N),q=[0,0,0],x=[0,0,0],nAct=0,ord=[];
    for(var g=0;g<N;g++){var i=g%nx,r=(g-i)/nx,j=r%ny,kk=(r-j)/ny;x[0]=o.org[0]+i*o.st[0]-c[0];x[1]=o.org[1]+j*o.st[1]-c[1];if(d===3)x[2]=o.org[2]+kk*o.st[2]-c[2];
      for(var a=0;a<d;a++){var s=0;for(var e=0;e<d;e++)s+=M[a*d+e]*x[e];q[a]=s;}
      var nc=E.query(X,q,ci,cd);if(!nc){out[g]=NaN;if(prog&&(g&65535)===0)prog(g/N);continue;}nAct++;
      var kn;if(nc<=K){kn=nc;for(a=0;a<nc;a++)sel[a]=a;}else{ord.length=nc;for(a=0;a<nc;a++)ord[a]=a;ord.sort(function(u,v){return cd[u]-cd[v];});kn=K;for(a=0;a<K;a++)sel[a]=ord[a];}
      var mm=kn+1;for(a=0;a<kn;a++){var pa=ci[sel[a]];for(e=a;e<kn;e++){var pb=ci[sel[e]],r2=0;for(var t=0;t<d;t++){var dd=P[pa*d+t]-P[pb*d+t];r2+=dd*dd;}var v=a===e?(o.kern==='lin'?0:sill)+nug+1e-9:cov(r2)*sill;A[a*mm+e]=v;A[e*mm+a]=v;}
        A[a*mm+kn]=1;A[kn*mm+a]=1;b[a]=(o.kern==='lin'?cov(cd[sel[a]]):cov(cd[sel[a]])*sill);}
      A[kn*mm+kn]=0;b[kn]=1;var est=0;
      if(kn===1)est=V[ci[sel[0]]];else if(E.solve(A,b,mm)){for(a=0;a<kn;a++)est+=b[a]*V[ci[sel[a]]];}else{for(a=0;a<kn;a++)est+=V[ci[sel[a]]];est/=kn;}
      if(o.clamp){if(est<o.clamp[0])est=o.clamp[0];if(est>o.clamp[1])est=o.clamp[1];}out[g]=est;
      if(prog&&(g&65535)===0)prog(g/N);}
    return{v:out,nAct:nAct};};
  /* marching tetrahedra (6 tetra per sel), segitiga diorientasikan keluar (ke nilai < T) */
  E.mt=function(Vv,nn,org,st,T,bg,maxTri){var nx=nn[0],ny=nn[1],nz=nn[2],N=nx*ny*nz,X=[],Y=[],Z=[],I=[],J=[],Kk=[],map=new Map(),over=false,nIn=0;
    var val=function(g){var v=Vv[g];return v!==v?bg:v;};
    for(var g0=0;g0<N;g0++){var v0=Vv[g0];if(v0===v0&&v0>=T)nIn++;}
    var pos=function(g){var i=g%nx,r=(g-i)/nx,j=r%ny,k=(r-j)/ny;return[org[0]+i*st[0],org[1]+j*st[1],org[2]+k*st[2]];};
    var vert=function(a,b){var key=a<b?a*N+b:b*N+a,h=map.get(key);if(h!==undefined)return h;var va=val(a),vb=val(b),t=(T-va)/(vb-va);if(!(t>=0))t=0;if(t>1)t=1;var pa=pos(a),pb=pos(b);h=X.length;
      X.push(pa[0]+(pb[0]-pa[0])*t);Y.push(pa[1]+(pb[1]-pa[1])*t);Z.push(pa[2]+(pb[2]-pa[2])*t);map.set(key,h);return h;};
    var tri=function(a,b,c,gi,go){var ux=X[b]-X[a],uy=Y[b]-Y[a],uz=Z[b]-Z[a],vx=X[c]-X[a],vy=Y[c]-Y[a],vz=Z[c]-Z[a],nx2=uy*vz-uz*vy,ny2=uz*vx-ux*vz,nz2=ux*vy-uy*vx;
      if(nx2===0&&ny2===0&&nz2===0)return;var pi=pos(gi),po=pos(go);if(nx2*(po[0]-pi[0])+ny2*(po[1]-pi[1])+nz2*(po[2]-pi[2])<0){I.push(a);J.push(c);Kk.push(b);}else{I.push(a);J.push(b);Kk.push(c);}};
    var TET=[[0,5,1,6],[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6]],off=[0,1,1+nx,nx,nx*ny,1+nx*ny,1+nx+nx*ny,nx+nx*ny],cv=new Float64Array(8),cg=new Int32Array(8);
    for(var k=0;k<nz-1&&!over;k++)for(var j=0;j<ny-1;j++)for(var i=0;i<nx-1;i++){var g=i+nx*(j+ny*k),ni=0;for(var c=0;c<8;c++){cg[c]=g+off[c];cv[c]=val(cg[c]);if(cv[c]>=T)ni++;}if(ni===0||ni===8)continue;
      for(var t=0;t<6;t++){var q=TET[t],ins=[],outs=[];for(var u=0;u<4;u++){if(cv[q[u]]>=T)ins.push(cg[q[u]]);else outs.push(cg[q[u]]);}
        if(ins.length===0||ins.length===4)continue;
        if(ins.length===1)tri(vert(ins[0],outs[0]),vert(ins[0],outs[1]),vert(ins[0],outs[2]),ins[0],outs[0]);
        else if(ins.length===3)tri(vert(outs[0],ins[0]),vert(outs[0],ins[1]),vert(outs[0],ins[2]),ins[0],outs[0]);
        else{var a1=vert(ins[0],outs[0]),a2=vert(ins[0],outs[1]),a3=vert(ins[1],outs[1]),a4=vert(ins[1],outs[0]);tri(a1,a2,a3,ins[0],outs[0]);tri(a1,a3,a4,ins[0],outs[0]);}}
      if(I.length>maxTri){over=true;break;}}
    return{x:Float32Array.from(X),y:Float32Array.from(Y),z:Float32Array.from(Z),i:Int32Array.from(I),j:Int32Array.from(J),k:Int32Array.from(Kk),nIn:nIn,over:over};};
  return E;}
var OGE=OGENG();

/* ---------- status & parameter ---------- */
var OG={sec:'1',R:null,L:null,S:null,axes:[],draw:null,view:'3d',busy:false,msg:'',
  p:{el:'',cut:1,minL:1,dil:2,zTol:10,plane:'auto',pdip:70,pddir:135,
     ls:'v',lsAz:'',lsDip:70,lsR1:0,lsR2:0,lsAng:0,lsAlpha:3,lsNug:0,lsRes:0,lsTr:'log',lsCls:'',show3d:true,
     gs:{mode:'ind',el:'',cuts:'0.5, 1, 2',pth:0.5,tr:'log',rows:100000,comp:2,ori:'plane',dip:70,ddir:135,pitch:0,r1:50,r2:30,r3:8,alpha:3,nug:0.1,k:16,res:0,show:true}},
  on:true};
function ogE(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return '&#'+c.charCodeAt(0)+';';});}
function ogN(v,d){if(v==null||!isFinite(v))return '-';return(+v).toLocaleString('id-ID',{minimumFractionDigits:d||0,maximumFractionDigits:d||0});}
function ogEl(){var e=OG.p.el;if(!e||elements.indexOf(e)<0){e=elements.filter(function(x){return /^au/i.test(x);})[0]||elements[0]||'';OG.p.el=e;}return e;}
function ogNum(v,def){var x=parseFloat(String(v).replace(',','.'));return isFinite(x)?x:def;}
var OGR=Math.PI/180;
function ogVec(dip,ddir){var d=dip*OGR,a=ddir*OGR;return{s:[Math.sin(a-Math.PI/2),Math.cos(a-Math.PI/2),0],dd:[Math.sin(a)*Math.cos(d),Math.cos(a)*Math.cos(d),-Math.sin(d)],n:[Math.sin(a)*Math.sin(d),Math.cos(a)*Math.sin(d),Math.cos(d)]};}
function ogDot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
function ogCr(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
function ogNz(v){var l=Math.hypot(v[0],v[1],v[2])||1;return[v[0]/l,v[1]/l,v[2]/l];}
function ogPT(l){l=ogNz(l);if(l[2]>0)l=[-l[0],-l[1],-l[2]];return{pl:Math.asin(Math.min(1,-l[2]))/OGR,tr:((Math.atan2(l[0],l[1])/OGR)+360)%360,l:l};}
function ogPitch(l,pl){/* pitch: sudut dari arah strike (aturan tangan kanan) ke garis, di bidang vein, 0-180 */var V=ogVec(pl.dip,pl.ddir),a=Math.atan2(ogDot(l,V.dd),ogDot(l,V.s))/OGR;if(a<0)a+=180;return a%180;}

/* ---------- ① intercept per bor ---------- */
function ogRuns(A,ei,cut,minL,dil){/* A: interval terurut [f,t,v]; hasil: [{f,t,len,gt,avg}] */
  var S=[],cur=null;A.forEach(function(a){var v=a[2];if(v!=null&&v>=cut){if(cur&&a[0]-cur.t<=0.05){cur.t=a[1];cur.s.push(a);}else{cur={f:a[0],t:a[1],s:[a]};S.push(cur);}}else cur=null;});
  var gtOf=function(f,t){var g=0;A.forEach(function(a){if(a[1]<=f||a[0]>=t||a[2]==null)return;g+=a[2]*(Math.min(t,a[1])-Math.max(f,a[0]));});return g;};
  var R=S.map(function(s){return{f:s.f,t:s.t};});
  for(var it=0;it<200;it++){var done=true;for(var i=0;i+1<R.length;i++){var a=R[i],b=R[i+1],gap=b.f-a.t;if(gap<=dil){var g=gtOf(a.f,b.t);if(g/(b.t-a.f)>=cut){R.splice(i,2,{f:a.f,t:b.t});done=false;break;}}}if(done)break;}
  return R.map(function(r){var len=r.t-r.f,g=gtOf(r.f,r.t);return{f:r.f,t:r.t,len:len,gt:g,avg:len>0?g/len:0};}).filter(function(r){return r.len>=minL-1e-9;});}
function ogDir(id,m){var h=holeData[id],a=getXYZ(id,Math.max(0,m-0.5)),b=getXYZ(id,Math.min(h.maxD,m+0.5));return ogNz([b.x-a.x,b.y-a.y,b.z-a.z]);}
function ogPlaneFit(Pts,W){var n=0,c=[0,0,0],sw=0;Pts.forEach(function(p,i){var w=W[i];c[0]+=w*p[0];c[1]+=w*p[1];c[2]+=w*p[2];sw+=w;});if(!(sw>0))return null;c=c.map(function(v){return v/sw;});
  var C=[[0,0,0],[0,0,0],[0,0,0]];Pts.forEach(function(p,i){var e=[p[0]-c[0],p[1]-c[1],p[2]-c[2]],w=W[i];for(var a=0;a<3;a++)for(var b=0;b<3;b++)C[a][b]+=w*e[a]*e[b];});
  var E=gmEig3(C),k=0;for(var i=1;i<3;i++)if(E.val[i]<E.val[k])k=i;var nv=ogNz(E.vec[k]);if(nv[2]<0)nv=nv.map(function(v){return -v;});
  var dip=Math.acos(Math.min(1,nv[2]))/OGR,ddir=((Math.atan2(nv[0],nv[1])/OGR)+360)%360;return{c:c,dip:dip,ddir:ddir};}
function ogIcpt(){var P=OG.p,el=ogEl(),ei=elements.indexOf(el);if(ei<0){OG.msg='Belum ada data assay.';return null;}
  var cut=ogNum(P.cut,1),minL=Math.max(0,ogNum(P.minL,1)),dil=Math.max(0,ogNum(P.dil,2)),H=[],all=[];
  Object.keys(holeData).forEach(function(id){var A=(groupedAssays[id]||[]).filter(function(a){return a[2]>a[1];}).map(function(a){var v=a[4][ei];return[a[1],a[2],v==null||!isFinite(v)?null:+v];}).sort(function(a,b){return a[0]-b[0];});
    if(!A.some(function(a){return a[2]!=null;}))return;var R=ogRuns(A,ei,cut,minL,dil);var h={id:id,A:A,ic:R};
    R.forEach(function(r){var m=(r.f+r.t)/2,p=getXYZ(id,m);r.p=[p.x,p.y,p.z];r.m=m;all.push(r);});H.push(h);});
  /* bidang acuan */
  var pl;if(P.plane==='man')pl={dip:ogNum(P.pdip,70),ddir:ogNum(P.pddir,135)};else{var fit=ogPlaneFit(all.map(function(r){return r.p;}),all.map(function(r){return Math.max(1e-3,r.gt);}));pl=fit||{dip:70,ddir:135};}
  var V=ogVec(pl.dip,pl.ddir),c=[0,0,0],sw=0;all.forEach(function(r){var w=Math.max(1e-3,r.gt);c[0]+=w*r.p[0];c[1]+=w*r.p[1];c[2]+=w*r.p[2];sw+=w;});
  if(sw>0)c=c.map(function(v){return v/sw;});else{var n0=0;Object.keys(holeData).forEach(function(id){var h=holeData[id];c[0]+=h.x;c[1]+=h.y;c[2]+=h.z;n0++;});c=c.map(function(v){return v/Math.max(1,n0);});}
  pl.c=c;pl.n=V.n;pl.s=V.s;pl.dd=V.dd;pl.strike=(pl.ddir+270)%360;
  var zt=Math.max(0,ogNum(P.zTol,10)),out=[],nZero=0,nSkip=0;
  H.forEach(function(h){if(h.ic.length){var gA=0,gT=0,L=0,LT=0,px=0,py=0,pz=0;h.ic.forEach(function(r){var cs=Math.abs(ogDot(ogDir(h.id,r.m),V.n));r.cos=cs;gA+=r.gt;gT+=r.gt*cs;L+=r.len;LT+=r.len*cs;var w=Math.max(1e-6,r.gt);px+=w*r.p[0];py+=w*r.p[1];pz+=w*r.p[2];});
      var sw2=h.ic.reduce(function(a,r){return a+Math.max(1e-6,r.gt);},0);out.push({id:h.id,n:h.ic.length,gtA:gA,gt:gT,len:L,tt:LT,avg:L>0?gA/L:0,p:[px/sw2,py/sw2,pz/sw2],ic:h.ic});return;}
    /* bor tanpa intercept: GT 0 di titik tembus bidang acuan (atau titik terdekat <= toleransi) pada interval ber-assay */
    var best=null,prev=null;h.A.forEach(function(a){if(a[2]==null)return;var m=(a[0]+a[1])/2,p=getXYZ(h.id,m),s=ogDot([p.x-c[0],p.y-c[1],p.z-c[2]],V.n);
      if(prev&&(s===0||(s>0)!==(prev.s>0))&&m-prev.m<=Math.max(3,a[1]-a[0]+prev.len+0.01)){var t=prev.s/(prev.s-s),mm=prev.m+(m-prev.m)*t,q=getXYZ(h.id,mm);best={p:[q.x,q.y,q.z],d:0};}
      if(!best||best.d>0){if(Math.abs(s)<=zt&&(!best||Math.abs(s)<best.d))best={p:[p.x,p.y,p.z],d:Math.abs(s)};}prev={s:s,m:m,len:a[1]-a[0]};});
    if(best){out.push({id:h.id,n:0,gtA:0,gt:0,len:0,tt:0,avg:0,p:best.p,ic:[],zero:true});nZero++;}else nSkip++;});
  OG.R={el:el,cut:cut,minL:minL,dil:dil,pl:pl,H:out,nIc:all.length,nHit:out.filter(function(h){return h.n;}).length,nZero:nZero,nSkip:nSkip,when:Date.now()};OG.L=null;return OG.R;}

/* ---------- ② long section ---------- */
function ogLSFrame(){var R=OG.R,P=OG.p;if(!R)return null;var pl=R.pl,az,dp;
  if(P.ls==='vein'){az=pl.strike;dp=pl.dip;}else{az=P.lsAz===''||P.lsAz==null?pl.strike:ogNum(P.lsAz,pl.strike);dp=P.ls==='man'?Math.max(1,Math.min(90,ogNum(P.lsDip,70))):90;}
  var V=ogVec(dp,(az+90)%360),eu=V.s,ev=[-V.dd[0],-V.dd[1],-V.dd[2]],nl=ogCr(eu,ev),c=pl.c,vert=dp>=89.999;
  return{az:az,dip:dp,eu:eu,ev:ev,n:nl,c:c,vert:vert,
    to:function(p){return[ogDot([p[0]-c[0],p[1]-c[1],p[2]-c[2]],eu),vert?p[2]:ogDot([p[0]-c[0],p[1]-c[1],p[2]-c[2]],ev)];},
    from:function(u,v){return vert?[c[0]+u*eu[0],c[1]+u*eu[1],v]:[c[0]+u*eu[0]+v*ev[0],c[1]+u*eu[1]+v*ev[1],c[2]+u*eu[2]+v*ev[2]];}};}
function ogToVein(p,F){/* proyeksi titik bidang long section ke bidang vein acuan sepanjang normal long section */var pl=OG.R.pl,dn=ogDot(pl.n,F.n);if(Math.abs(dn)<0.15)return p;var t=-ogDot(pl.n,[p[0]-pl.c[0],p[1]-pl.c[1],p[2]-pl.c[2]])/dn;return[p[0]+t*F.n[0],p[1]+t*F.n[1],p[2]+t*F.n[2]];}
function ogCls(mx){var P=OG.p,L=String(P.lsCls||'').split(/[;,\s]+/).map(Number).filter(function(v){return isFinite(v)&&v>0;}).sort(function(a,b){return a-b;});
  if(L.length)return L;var B=[0.5,1,2,5,10,20,50,100,200,500,1000];L=B.filter(function(v){return v<mx;});while(L.length>6)L.shift();if(!L.length)L=[mx/2];return L;}
function ogLS(){var R=OG.R,P=OG.p;if(!R)return null;var F=ogLSFrame(),U=[],Vv=[],G=[];R.H.forEach(function(h){var q=F.to(h.p);U.push(q[0]);Vv.push(q[1]);G.push(h.gt);});var n=U.length;if(n<3){OG.L={F:F,U:U,V:Vv,G:G,grid:null};return OG.L;}
  /* jarak tetangga terdekat (median) -> range & resolusi otomatis */
  var nn=[];for(var i=0;i<n;i+=Math.max(1,Math.floor(n/400))){var m=1e18;for(var j=0;j<n;j++){if(j===i)continue;var d=Math.hypot(U[i]-U[j],Vv[i]-Vv[j]);if(d>0.01&&d<m)m=d;}if(m<1e18)nn.push(m);}nn.sort(function(a,b){return a-b;});var med=nn.length?nn[Math.floor(nn.length/2)]:10;
  var r1=ogNum(P.lsR1,0)>0?ogNum(P.lsR1,0):Math.max(10,4*med),r2=ogNum(P.lsR2,0)>0?ogNum(P.lsR2,0):r1,ang=ogNum(P.lsAng,0)*OGR,res=ogNum(P.lsRes,0)>0?ogNum(P.lsRes,0):Math.max(0.5,med/3);
  var u0=Math.min.apply(null,U),u1=Math.max.apply(null,U),v0=Math.min.apply(null,Vv),v1=Math.max.apply(null,Vv),mg=Math.min(r1,r2)*0.5;u0-=mg;u1+=mg;v0-=mg;v1+=mg;
  while(((u1-u0)/res+1)*((v1-v0)/res+1)>250000)res*=1.25;var nx=Math.floor((u1-u0)/res)+1,ny=Math.floor((v1-v0)/res)+1;
  var ca=Math.cos(ang),sa=Math.sin(ang),M=[ca/r1,sa/r1,-sa/r2,ca/r2],cx=(u0+u1)/2,cy=(v0+v1)/2,Pi=new Float64Array(n*2),tr=P.lsTr==='log',Y=new Float64Array(n);
  for(i=0;i<n;i++){var x=U[i]-cx,y=Vv[i]-cy;Pi[i*2]=M[0]*x+M[1]*y;Pi[i*2+1]=M[2]*x+M[3]*y;Y[i]=tr?Math.log(G[i]+1):G[i];}
  var t0=performance.now(),r=OGE.interp({d:2,P:Pi,V:Y,n:n,M:M,c:[cx,cy],org:[u0,v0],nn:[nx,ny],st:[res,res],k:20,alpha:ogNum(P.lsAlpha,3),nug:ogNum(P.lsNug,0),kern:'sph',clamp:null});
  var Z=[];for(j=0;j<ny;j++){var row=[];for(i=0;i<nx;i++){var v=r.v[i+j*nx];row.push(v!==v?null:Math.max(0,tr?Math.exp(v)-1:v));}Z.push(row);}
  var xs=[],ys=[];for(i=0;i<nx;i++)xs.push(u0+i*res);for(j=0;j<ny;j++)ys.push(v0+j*res);
  OG.L={F:F,U:U,V:Vv,G:G,grid:{x:xs,y:ys,z:Z,nx:nx,ny:ny,res:res},r1:r1,r2:r2,ang:ang/OGR,med:med,ms:performance.now()-t0};return OG.L;}
function ogIdx(v,B){/* nilai GT -> indeks kelas kontinu (garis kontur tepat di batas kelas) */if(v==null)return null;if(v<=B[0])return v/B[0];for(var i=0;i+1<B.length;i++)if(v<=B[i+1])return 1+i+(v-B[i])/(B[i+1]-B[i]);return B.length+Math.min(1,(v-B[B.length-1])/B[B.length-1]);}
var OGCS=[[0,'#2b3a8c'],[0.2,'#2c7bb6'],[0.4,'#abd9e9'],[0.55,'#ffffbf'],[0.75,'#fdae61'],[0.9,'#e8590c'],[1,'#b2182b']];

/* ---------- tampilan long section (menggantikan area 3D) ---------- */
function ogShowLS(on){OG.view=on?'ls':'3d';var host=$('plotDiv').parentNode,d=$('ogDiv');if(on&&!d){d=document.createElement('div');d.id='ogDiv';host.appendChild(d);d.innerHTML='<div id=ogPlot></div><div id=ogXY></div>';ogEvents();}
  if(d)d.style.display=on?'block':'none';if(on)ogPlotLS();else{try{updatePlot();}catch(e){}}ogPanel();}
function ogPlotLS(){var gd=$('ogPlot');if(!gd||OG.view!=='ls')return;var L=OG.L||(OG.R?ogLS():null),dark=document.body.classList.contains('dark'),T=[],ann=[];
  if(!L){Plotly.react(gd,[],{title:{text:'Hitung intercept dulu (① Data & intercept)'},paper_bgcolor:dark?'#1f232b':'#fff'});return;}
  var mx=Math.max.apply(null,L.G.concat([1])),B=ogCls(mx);
  if(L.grid){var Zi=L.grid.z.map(function(r){return r.map(function(v){return ogIdx(v,B);});});
    T.push({type:'contour',x:L.grid.x,y:L.grid.y,z:Zi,zmin:0,zmax:B.length+1,colorscale:OGCS,contours:{start:1,end:B.length,size:1,coloring:'fill',showlabels:false},line:{color:'rgba(20,20,20,.55)',width:0.8},connectgaps:false,hoverinfo:'skip',
      colorbar:{title:{text:'GT ('+ogE(OG.R.el)+' x m)',side:'right'},tickvals:[0].concat(B.map(function(b,i){return i+1;})),ticktext:['0'].concat(B.map(function(b){return ogN(b,b<1?1:0);})),len:0.8,thickness:14},name:'GT'});}
  var H=OG.R.H,hz=[],hv=[];H.forEach(function(h,i){(h.zero?hz:hv).push(i);});
  T.push({type:'scatter',mode:'markers',x:hz.map(function(i){return L.U[i];}),y:hz.map(function(i){return L.V[i];}),marker:{size:5,color:'rgba(0,0,0,0)',line:{color:dark?'#ced4da':'#495057',width:1}},name:'Bor tanpa intercept (GT 0)',text:hz.map(function(i){return H[i].id;}),hovertemplate:'%{text}<br>GT 0<extra></extra>'});
  T.push({type:'scatter',mode:'markers',x:hv.map(function(i){return L.U[i];}),y:hv.map(function(i){return L.V[i];}),marker:{size:9,color:hv.map(function(i){return ogIdx(H[i].gt,B);}),cmin:0,cmax:B.length+1,colorscale:OGCS,line:{color:dark?'#f8f9fa':'#111',width:1.4}},name:'Bor dengan intercept',
    text:hv.map(function(i){var h=H[i];return '<b>'+ogE(h.id)+'</b><br>GT '+ogN(h.gt,2)+' (semu '+ogN(h.gtA,2)+')<br>'+h.n+' intercept · '+ogN(h.len,1)+' m semu / '+ogN(h.tt,1)+' m tebal sebenarnya<br>rata-rata '+ogN(h.avg,2);}),hovertemplate:'%{text}<extra></extra>'});
  OG.axes.forEach(function(a,k){if(!a.ls||a.ls.az==null)return;var q1=L.F.to(a.p1),q2=L.F.to(a.p2);T.push({type:'scatter',mode:'lines+markers',x:[q1[0],q2[0]],y:[q1[1],q2[1]],line:{color:a.auto?'#1971c2':'#111',width:3,dash:a.auto?'dash':'solid'},marker:{size:6,symbol:['circle','triangle-down'],color:'#111'},name:a.name,hoverinfo:'name',showlegend:false});
    ann.push({x:q2[0],y:q2[1],text:ogE(a.name)+': pitch '+ogN(a.pitch,0)+'° · '+ogN(a.pl,0)+'→'+('00'+Math.round(a.tr)).slice(-3),showarrow:false,xanchor:'left',yanchor:'top',font:{size:11,color:dark?'#f8f9fa':'#111'},bgcolor:dark?'rgba(31,35,43,.8)':'rgba(255,255,255,.85)'});});
  if(OG.draw&&OG.draw.a)T.push({type:'scatter',mode:'markers',x:[OG.draw.a[0]],y:[OG.draw.a[1]],marker:{size:11,symbol:'x',color:'#e8590c'},hoverinfo:'skip',showlegend:false});
  var F=L.F,lay={margin:{l:70,r:20,t:46,b:56},paper_bgcolor:dark?'#1f232b':'#fff',plot_bgcolor:dark?'#1f232b':'#fff',font:{color:dark?'#e9ecef':'#212529',size:11},hovermode:'closest',dragmode:OG.draw?false:'pan',
    title:{text:'Long section GT '+ogE(OG.R.el)+' · '+(F.vert?'vertikal, azimuth '+ogN(F.az,0)+'°':'bidang miring '+ogN(F.dip,0)+'° ke '+ogN((F.az+90)%360,0)+'°')+' · cut-off '+ogN(OG.R.cut,2)+' · '+OG.R.nHit+' bor ber-intercept, '+OG.R.nZero+' bor GT 0',font:{size:13}},
    xaxis:{title:{text:'Jarak sepanjang long section (m) → '+ogN(F.az,0)+'°'},zeroline:false,gridcolor:dark?'#343a40':'#e9ecef'},yaxis:{title:{text:F.vert?'RL (m)':'Jarak di bidang, naik-dip (m)'},scaleanchor:'x',scaleratio:1,zeroline:false,gridcolor:dark?'#343a40':'#e9ecef'},
    legend:{orientation:'h',y:-0.12},annotations:ann.concat([{xref:'paper',yref:'paper',x:1,y:-0.13,text:'© Copyright Habil Abdillah 2026',showarrow:false,font:{size:9,color:'#868e96'},xanchor:'right'}])};
  Plotly.react(gd,T,lay,{scrollZoom:true,displaylogo:false,responsive:true,doubleClick:'autosize'});}
function ogEvents(){var gd=$('ogPlot');if(!gd)return;
  gd.addEventListener('click',function(e){if(!OG.draw||!gd._fullLayout)return;var xa=gd._fullLayout.xaxis,ya=gd._fullLayout.yaxis,r=gd.getBoundingClientRect(),x=xa.p2l(e.clientX-r.left-xa._offset),y=ya.p2l(e.clientY-r.top-ya._offset);if(!isFinite(x)||!isFinite(y))return;
    if(!OG.draw.a){OG.draw.a=[x,y];ogPlotLS();return;}var a=OG.draw.a;OG.draw=null;ogAxisLS(a,[x,y]);ogPlotLS();ogPanel();},true);
  gd.addEventListener('mousemove',function(e){if(!gd._fullLayout)return;var xa=gd._fullLayout.xaxis,ya=gd._fullLayout.yaxis,r=gd.getBoundingClientRect(),x=xa.p2l(e.clientX-r.left-xa._offset),y=ya.p2l(e.clientY-r.top-ya._offset),t=$('ogXY');if(t&&isFinite(x)&&isFinite(y))t.textContent=(OG.draw?(OG.draw.a?'Klik titik ke-2 (arah menunjam) · Esc batal · ':'Klik titik ke-1 sumbu shoot · '):'')+'jarak '+x.toFixed(1)+' m · '+(OG.L&&OG.L.F.vert?'RL ':'v ')+y.toFixed(1);});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&OG.draw){OG.draw=null;ogPlotLS();ogPanel();}});}

/* ---------- ③ ore shoot ---------- */
function ogAxisFrom(l,cen,len,name,auto){var pl=OG.R.pl,o=ogPT(l),half=Math.max(5,len/2),p1=[cen[0]-o.l[0]*half,cen[1]-o.l[1]*half,cen[2]-o.l[2]*half],p2=[cen[0]+o.l[0]*half,cen[1]+o.l[1]*half,cen[2]+o.l[2]*half];
  return{id:'ax'+Date.now().toString(36)+Math.random().toString(36).slice(2,5),name:name,pl:o.pl,tr:o.tr,pitch:ogPitch(o.l,pl),p1:p1,p2:p2,len:2*half,auto:!!auto,ls:{az:1},vein:{dip:pl.dip,ddir:pl.ddir}};}
function ogAxisLS(a,b){var L=OG.L,F=L.F;var A=ogToVein(F.from(a[0],a[1]),F),B=ogToVein(F.from(b[0],b[1]),F),dls=[(b[0]-a[0])*F.eu[0]+(F.vert?0:(b[1]-a[1])*F.ev[0]),(b[0]-a[0])*F.eu[1]+(F.vert?0:(b[1]-a[1])*F.ev[1]),(b[0]-a[0])*F.eu[2]+(F.vert?(b[1]-a[1]):(b[1]-a[1])*F.ev[2])];
  /* garis di long section = proyeksi garis di bidang vein: arah = perpotongan bidang vein dgn bidang (garis, normal LS) */
  var l=ogCr(OG.R.pl.n,ogCr(dls,F.n));if(Math.hypot(l[0],l[1],l[2])<1e-9)l=dls;l=ogNz(l);if(ogDot(l,dls)<0)l=l.map(function(v){return -v;});
  var cen=[(A[0]+B[0])/2,(A[1]+B[1])/2,(A[2]+B[2])/2],len=Math.hypot(B[0]-A[0],B[1]-A[1],B[2]-A[2]);var ax=ogAxisFrom(l,cen,len,'Shoot '+(OG.axes.filter(function(x){return !x.auto;}).length+1),false);ax.p1=A;ax.p2=B;OG.axes.push(ax);ogDirty();}
function ogAuto(){/* arah kemenerusan GT terbaik di bidang vein: fan variogram GT (log) semua bor termasuk GT 0, 36 arah, toleransi ±12,5° */
  var R=OG.R;if(!R)return null;var V=R.pl,H=R.H;if(H.filter(function(h){return h.gt>0;}).length<5)return null;
  var P=H.map(function(h){var e=[h.p[0]-V.c[0],h.p[1]-V.c[1],h.p[2]-V.c[2]];return[ogDot(e,V.s),ogDot(e,V.dd),Math.log(h.gt+1),h.gt];}),n=P.length;
  if(n>1500){var st=n/1500,Q=[];for(var q=0;q<1500;q++)Q.push(P[Math.floor(q*st)]);P=Q;n=P.length;}
  var nn=[];for(var i=0;i<n;i+=Math.max(1,Math.floor(n/300))){var m=1e18;for(var j=0;j<n;j++){if(j===i)continue;var d=Math.hypot(P[i][0]-P[j][0],P[i][1]-P[j][1]);if(d>0.01&&d<m)m=d;}if(m<1e18)nn.push(m);}
  nn.sort(function(a,b){return a-b;});var med=nn.length?nn[Math.floor(nn.length/2)]:10,h1=0.5*med,h2=4.5*med,NB=36,S=new Float64Array(NB),C=new Float64Array(NB);
  for(i=0;i<n;i++)for(j=i+1;j<n;j++){var du=P[j][0]-P[i][0],dv=P[j][1]-P[i][1],dd2=Math.hypot(du,dv);if(dd2<h1||dd2>h2)continue;var a=Math.atan2(dv,du)/OGR;a=((a%180)+180)%180;var g=0.5*(P[i][2]-P[j][2])*(P[i][2]-P[j][2]);
    for(var b=0;b<NB;b++){var df=Math.abs(a-b*5);df=Math.min(df,180-df);if(df<=12.5){S[b]+=g;C[b]++;}}}
  var G=[];for(b=0;b<NB;b++)G.push(C[b]>=20?S[b]/C[b]:null);var Gs=G.map(function(v,b){var L=[G[(b+NB-1)%NB],v,G[(b+1)%NB]].filter(function(x){return x!=null;});return L.length?L.reduce(function(a,x){return a+x;},0)/L.length:null;});
  var bi=-1;Gs.forEach(function(v,b){if(v!=null&&(bi<0||v<Gs[bi]))bi=b;});if(bi<0)return null;var gp=Gs[(bi+18)%NB],th=bi*5*OGR;
  var l=ogNz([Math.cos(th)*V.s[0]+Math.sin(th)*V.dd[0],Math.cos(th)*V.s[1]+Math.sin(th)*V.dd[1],Math.cos(th)*V.s[2]+Math.sin(th)*V.dd[2]]);
  /* posisi sumbu: pusat bor GT tertinggi (persentil 75); panjang = sebaran zona tsb searah sumbu */
  var Hp=R.H.filter(function(h){return h.gt>0;}),gg=Hp.map(function(h){return h.gt;}).sort(function(a,b){return a-b;}),thr=gg[Math.floor(gg.length*0.75)],T=Hp.filter(function(h){return h.gt>=thr;}),sw=0,cen=[0,0,0];
  T.forEach(function(h){sw+=h.gt;for(var k=0;k<3;k++)cen[k]+=h.gt*h.p[k];});cen=cen.map(function(v){return v/sw;});var pr=T.map(function(h){return ogDot([h.p[0]-cen[0],h.p[1]-cen[1],h.p[2]-cen[2]],l);}),len=Math.max(20,Math.max.apply(null,pr)-Math.min.apply(null,pr));
  return{l:l,cen:cen,len:len,el:gp!=null&&Gs[bi]>0?gp/Gs[bi]:1,n:n,thr:thr,G:Gs,lag:[h1,h2]};}
function ogAutoAdd(){var A=ogAuto();if(!A){alert('Data GT belum cukup (perlu minimal 5 bor ber-intercept).');return;}OG.axes=OG.axes.filter(function(x){return !x.auto;});var ax=ogAxisFrom(A.l,A.cen,A.len,'Usulan otomatis',true);ax.el=A.el;OG.axes.push(ax);ogDirty();}
function ogAxDel(id){OG.axes=OG.axes.filter(function(a){return a.id!==id;});ogDirty();}
function ogAxCsv(){if(!OG.axes.length){alert('Belum ada sumbu shoot.');return;}var L=['No,X,Y,Z,Dip,Dip_Azimuth,Plunge,Trend,Pitch,Keterangan'];
  OG.axes.forEach(function(a,i){var c=[(a.p1[0]+a.p2[0])/2+offX,(a.p1[1]+a.p2[1])/2+offY,(a.p1[2]+a.p2[2])/2];L.push([i+1,c[0].toFixed(2),c[1].toFixed(2),c[2].toFixed(2),a.vein.dip.toFixed(1),a.vein.ddir.toFixed(1),a.pl.toFixed(1),a.tr.toFixed(1),a.pitch.toFixed(1),'"Ore Geometry: '+String(a.name).replace(/"/g,"'")+'"'].join(','));});
  gxDl(new Blob(['﻿'+L.join('\r\n')],{type:'text/csv'}),'OreGeometry_SumbuShoot_'+gxSlug(SA&&SA.D&&SA.D.name||'proyek')+'_'+gxDate()+'.csv');}
function ogFieldLin(){/* lineasi lapangan di basis data struktur: hanya ditampilkan sebagai pembanding (dibaca, tidak diubah) */if(!window.STR||!OG.R)return[];var pl=OG.R.pl;
  return STR.P.filter(function(p){return p.pl!=null&&p.tr!=null&&isFinite(+p.pl)&&isFinite(+p.tr)&&(typeof stOn!=='function'||stOn(p));}).map(function(p){var l=[Math.cos(p.pl*OGR)*Math.sin(p.tr*OGR),Math.cos(p.pl*OGR)*Math.cos(p.tr*OGR),-Math.sin(p.pl*OGR)],off=Math.asin(Math.min(1,Math.abs(ogDot(l,pl.n))))/OGR;return{no:p.no,pl:+p.pl,tr:+p.tr,pitch:ogPitch(l,pl),off:off};});}

/* ---------- ④ grade shell 3D ---------- */
function ogGsRows(){var gs=OG.p.gs,el=gs.el&&elements.indexOf(gs.el)>=0?gs.el:ogEl(),ei=elements.indexOf(el),A=window.assays||[],N=Math.max(1000,ogNum(gs.rows,100000)|0),L=[];
  for(var i=A.length-1;i>=0&&L.length<N;i--){var a=A[i],v=a[4]&&a[4][ei];if(v==null||!isFinite(v)||!(a[2]>a[1])||!holeData[a[0]])continue;L.push(a);}return{el:el,ei:ei,rows:L,total:A.length};}
function ogGsPts(){var X=ogGsRows(),gs=OG.p.gs,cl=Math.max(0,ogNum(gs.comp,2)),by={},out=[];X.rows.forEach(function(a){(by[a[0]]=by[a[0]]||[]).push(a);});
  Object.keys(by).forEach(function(id){var A=by[id].sort(function(p,q){return p[1]-q[1];});
    if(!(cl>0)){A.forEach(function(a){var m=(a[1]+a[2])/2,p=getXYZ(id,m);out.push([p.x,p.y,p.z,+a[4][X.ei]]);});return;}
    var f0=A[0][1],acc=0,len=0,bin=Math.floor((A[0][1]-f0)/cl);var flush=function(b){if(len>=cl*0.5){var m=f0+(b+0.5)*cl,p=getXYZ(id,Math.min(m,holeData[id].maxD));out.push([p.x,p.y,p.z,acc/len]);}acc=0;len=0;};
    A.forEach(function(a){var f=a[1];while(f<a[2]-1e-9){var b=Math.floor((f-f0)/cl+1e-9),e=Math.min(a[2],f0+(b+1)*cl);if(b!==bin){flush(bin);bin=b;}acc+=+a[4][X.ei]*(e-f);len+=e-f;f=e;}});flush(bin);});
  return{el:X.el,P:out,nRows:X.rows.length,total:X.total};}
function ogGsAxes(){var gs=OG.p.gs,dip,ddir;if(gs.ori==='plane'&&OG.R){dip=OG.R.pl.dip;ddir=OG.R.pl.ddir;}else{dip=ogNum(gs.dip,70);ddir=ogNum(gs.ddir,135);}
  var V=ogVec(dip,ddir),p=ogNum(gs.pitch,0)*OGR,mj=[0,1,2].map(function(k){return Math.cos(p)*V.s[k]+Math.sin(p)*V.dd[k];}),sm=[0,1,2].map(function(k){return -Math.sin(p)*V.s[k]+Math.cos(p)*V.dd[k];});
  return{dip:dip,ddir:ddir,pitch:ogNum(gs.pitch,0),mj:mj,sm:sm,mn:V.n,pt:ogPT(mj)};}
var OGW=null,OGWJ={};
function ogWorker(){if(OGW)return OGW;try{var src='var E=('+OGENG.toString()+')();self.onmessage=function(ev){var o=ev.data;try{var r=E.interp(o,function(f){self.postMessage({id:o.id,prog:f});});var M=[];(o.T||[]).forEach(function(T){M.push(E.mt(r.v,o.nn,o.org,o.st,T,o.bg,o.maxTri));});self.postMessage({id:o.id,v:r.v,nAct:r.nAct,M:M});}catch(e){self.postMessage({id:o.id,err:String(e&&e.message||e)});}};';
    OGW=new Worker(URL.createObjectURL(new Blob([src],{type:'text/javascript'})));OGW.onmessage=function(ev){var d=ev.data,j=OGWJ[d.id];if(!j)return;if(d.prog!=null){j.prog(d.prog);return;}delete OGWJ[d.id];if(d.err)j.rej(new Error(d.err));else j.res(d);};}catch(e){OGW=false;}return OGW;}
function ogRunJob(o,prog){var W=ogWorker();if(!W){var r=OGE.interp(o,prog),M=(o.T||[]).map(function(T){return OGE.mt(r.v,o.nn,o.org,o.st,T,o.bg,o.maxTri);});return Promise.resolve({v:r.v,nAct:r.nAct,M:M});}
  return new Promise(function(res,rej){var id='j'+Date.now()+Math.random();OGWJ[id]={res:res,rej:rej,prog:prog||function(){}};o.id=id;W.postMessage(o);});}
async function ogShell(prev){if(OG.busy)return;var gs=OG.p.gs,X=ogGsPts(),n=X.P.length;if(n<10){alert('Data assay '+(X.el||'')+' belum cukup untuk grade shell.');return;}
  var cuts=String(gs.cuts).split(/[;,\s]+/).map(Number).filter(function(v){return isFinite(v)&&v>0;}).sort(function(a,b){return a-b;});if(!cuts.length){alert('Isi minimal satu cut-off.');return;}
  var Ax=ogGsAxes(),r1=Math.max(0.5,ogNum(gs.r1,50)),r2=Math.max(0.5,ogNum(gs.r2,30)),r3=Math.max(0.2,ogNum(gs.r3,8)),M=[Ax.mj[0]/r1,Ax.mj[1]/r1,Ax.mj[2]/r1,Ax.sm[0]/r2,Ax.sm[1]/r2,Ax.sm[2]/r2,Ax.mn[0]/r3,Ax.mn[1]/r3,Ax.mn[2]/r3];
  var lo=[1e18,1e18,1e18],hi=[-1e18,-1e18,-1e18];X.P.forEach(function(p){for(var k=0;k<3;k++){if(p[k]<lo[k])lo[k]=p[k];if(p[k]>hi[k])hi[k]=p[k];}});var mg=Math.min(r3,4);lo=lo.map(function(v){return v-mg;});hi=hi.map(function(v,k){return v+mg;});
  var maxN=prev?400000:3000000,res=ogNum(gs.res,0)>0?ogNum(gs.res,0):Math.max(1,Math.min(r3,10)/2),vol=(hi[0]-lo[0])*(hi[1]-lo[1])*(hi[2]-lo[2]);if(prev)res=Math.max(res*2,Math.cbrt(vol/maxN));while(vol/(res*res*res)>maxN)res*=1.15;
  var nn=[0,1,2].map(function(k){return Math.max(2,Math.floor((hi[k]-lo[k])/res)+2);}),c=[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,(lo[2]+hi[2])/2],Pi=new Float64Array(n*3);
  X.P.forEach(function(p,i){var e=[p[0]-c[0],p[1]-c[1],p[2]-c[2]];for(var a=0;a<3;a++)Pi[i*3+a]=M[a*3]*e[0]+M[a*3+1]*e[1]+M[a*3+2]*e[2];});
  var ind=gs.mode!=='num',tr=!ind&&gs.tr==='log',eps=0.001,jobs=[];
  if(ind)cuts.forEach(function(ct){jobs.push({cuts:[ct],V:Float64Array.from(X.P.map(function(p){return p[3]>=ct?1:0;})),T:[Math.min(0.99,Math.max(0.01,ogNum(gs.pth,0.5)))],bg:0,clamp:[0,1]});});
  else{var V=Float64Array.from(X.P.map(function(p){return tr?Math.log(Math.max(0,p[3])+eps):p[3];})),mn=1e18;for(var z0=0;z0<V.length;z0++)if(V[z0]<mn)mn=V[z0];jobs.push({cuts:cuts,V:V,T:cuts.map(function(ct){return tr?Math.log(ct+eps):ct;}),bg:mn-1,clamp:null});}
  OG.busy=true;OG.msg='Menghitung grade shell'+(prev?' (pratinjau)':'')+'… '+ogN(n)+' titik, grid '+nn.join(' × ')+' ('+ogN(res,1)+' m)';ogPanel();var t0=performance.now(),S={el:X.el,n:n,nRows:X.nRows,total:X.total,res:res,nn:nn,org:lo,mode:ind?'ind':'num',prev:!!prev,Ax:Ax,r:[r1,r2,r3],shells:[],when:Date.now()};
  try{for(var q=0;q<jobs.length;q++){var J=jobs[q],o={d:3,P:Pi,V:J.V,n:n,M:M,c:c,org:lo,nn:nn,st:[res,res,res],k:Math.max(6,Math.min(40,ogNum(gs.k,16)|0)),alpha:ogNum(gs.alpha,3),nug:ogNum(gs.nug,0.1),kern:'sph',clamp:J.clamp,T:J.T,bg:J.bg,maxTri:1500000};
      var R=await ogRunJob(o,function(f){var b=$('ogProg');if(b)b.style.width=Math.round(100*(q+f)/jobs.length)+'%';});
      J.T.forEach(function(T,k){var m=R.M[k],ct=J.cuts[k],gv=R.v;/* validasi: nilai grid (trilinear) di posisi sampel */
        var nA=0,nAin=0,nB=0,nBin=0;X.P.forEach(function(p){var ins=ogTri(gv,nn,lo,res,p,J.bg)>=T;if(p[3]>=ct){nA++;if(ins)nAin++;}else{nB++;if(ins)nBin++;}});
        S.shells.push({cut:ct,T:T,x:m.x,y:m.y,z:m.z,i:m.i,j:m.j,k:m.k,nt:m.i.length,vol:m.nIn*res*res*res,over:m.over,nA:nA,nAin:nAin,nB:nB,nBin:nBin,show:true});});}
    S.ms=performance.now()-t0;OG.S=S;OG.msg='&#10003; Grade shell selesai ('+(S.ms/1000).toFixed(1)+' s'+(prev?', pratinjau kasar':'')+').';}
  catch(e){console.error(e);OG.msg='<span class=warn>Gagal: '+ogE(e.message)+'</span>';}
  OG.busy=false;ogPanel();try{updatePlot();}catch(e){}}
function ogTri(V,nn,o,st,p,bg){var fx=(p[0]-o[0])/st,fy=(p[1]-o[1])/st,fz=(p[2]-o[2])/st,i=Math.floor(fx),j=Math.floor(fy),k=Math.floor(fz);if(i<0||j<0||k<0||i>=nn[0]-1||j>=nn[1]-1||k>=nn[2]-1)return bg;
  var tx=fx-i,ty=fy-j,tz=fz-k,g=function(a,b,c){var v=V[(i+a)+nn[0]*((j+b)+nn[1]*(k+c))];return v!==v?bg:v;};
  return g(0,0,0)*(1-tx)*(1-ty)*(1-tz)+g(1,0,0)*tx*(1-ty)*(1-tz)+g(0,1,0)*(1-tx)*ty*(1-tz)+g(1,1,0)*tx*ty*(1-tz)+g(0,0,1)*(1-tx)*(1-ty)*tz+g(1,0,1)*tx*(1-ty)*tz+g(0,1,1)*(1-tx)*ty*tz+g(1,1,1)*tx*ty*tz;}
function ogShellExp(fmt){var S=OG.S;if(!S||!S.shells.length){alert('Belum ada grade shell.');return;}var files=[],nm=gxSlug(SA&&SA.D&&SA.D.name||'proyek');
  S.shells.forEach(function(s){if(!s.show||!s.nt)return;var base='GradeShell_'+gxSlug(S.el)+'_'+String(s.cut).replace('.','p')+'_'+nm,L=[];
    if(fmt==='obj'){L.push('# GC-Ex Ore Geometry grade shell '+S.el+' >= '+s.cut+' ('+(S.mode==='ind'?'indikator p='+s.T:'numerik')+')');for(var i=0;i<s.x.length;i++)L.push('v '+(s.x[i]+offX).toFixed(3)+' '+(s.y[i]+offY).toFixed(3)+' '+s.z[i].toFixed(3));for(i=0;i<s.nt;i++)L.push('f '+(s.i[i]+1)+' '+(s.j[i]+1)+' '+(s.k[i]+1));files.push({name:base+'.obj',data:L.join('\n')});}
    else{L.push('0\nSECTION\n2\nENTITIES');var P=function(a){return (s.x[a]+offX).toFixed(3)+'\n'+(s.y[a]+offY).toFixed(3)+'\n'+s.z[a].toFixed(3);};for(var t=0;t<s.nt;t++){var a=s.i[t],b=s.j[t],c=s.k[t],v=[a,b,c,c];L.push('0\n3DFACE\n8\nGS_'+String(s.cut).replace('.','p')+v.map(function(x,q){var p=P(x).split('\n');return '\n1'+q+'\n'+p[0]+'\n2'+q+'\n'+p[1]+'\n3'+q+'\n'+p[2];}).join(''));}L.push('0\nENDSEC\n0\nEOF');files.push({name:base+'.dxf',data:L.join('\n')});}});
  if(!files.length)return;if(files.length===1)gxDl(new Blob([files[0].data],{type:'text/plain'}),files[0].name);else gxDl(gxZip(files),'GradeShell_'+gxSlug(S.el)+'_'+nm+'_'+gxDate()+'.zip');}
function ogIcCsv(){var R=OG.R;if(!R){alert('Hitung intercept dulu.');return;}var L=['HoleID,From,To,Panjang_semu,Kadar_rata2,GT_semu,Cos_ke_normal,GT_sebenarnya,X,Y,Z'];
  R.H.forEach(function(h){if(!h.n){L.push([h.id,'','',0,0,0,'',0,(h.p[0]+offX).toFixed(2),(h.p[1]+offY).toFixed(2),h.p[2].toFixed(2)].join(','));return;}h.ic.forEach(function(r){L.push([h.id,r.f,r.t,r.len.toFixed(2),r.avg.toFixed(3),r.gt.toFixed(3),r.cos.toFixed(3),(r.gt*r.cos).toFixed(3),(r.p[0]+offX).toFixed(2),(r.p[1]+offY).toFixed(2),r.p[2].toFixed(2)].join(','));});});
  gxDl(new Blob(['﻿'+L.join('\r\n')],{type:'text/csv'}),'OreGeometry_Intercept_'+gxSlug(R.el)+'_'+gxDate()+'.csv');}

/* ---------- 3D ---------- */
function ogTraces(T,o){if(!OG.on||VIEW2D)return;try{
  if(OG.p.show3d&&OG.R){var L=OG.L||ogLS();if(L&&L.grid){var g=L.grid,F=L.F,mx=Math.max.apply(null,L.G.concat([1])),B=ogCls(mx),X=[],Y=[],Z=[],I=[],J=[],K=[],C=[],id=new Int32Array(g.nx*g.ny).fill(-1);
      for(var j=0;j<g.ny;j++)for(var i=0;i<g.nx;i++){var v=g.z[j][i];if(v==null)continue;var p=ogToVein(F.from(g.x[i],g.y[j]),F);id[i+j*g.nx]=X.length;X.push(p[0]);Y.push(p[1]);Z.push(p[2]);C.push(ogIdx(v,B));}
      for(j=0;j<g.ny-1;j++)for(i=0;i<g.nx-1;i++){var a=id[i+j*g.nx],b=id[i+1+j*g.nx],c=id[i+1+(j+1)*g.nx],d=id[i+(j+1)*g.nx];if(a<0||b<0||c<0||d<0)continue;I.push(a,a);J.push(b,c);K.push(c,d);}
      if(I.length)T.push({type:'mesh3d',name:'Ore Geometry: GT '+OG.R.el+' (bidang vein)',x:X,y:Y,z:Z,i:I,j:J,k:K,intensity:C,cmin:0,cmax:B.length+1,colorscale:OGCS,showscale:false,opacity:0.85,flatshading:true,hoverinfo:'name',showlegend:true});}
    var H=OG.R.H.filter(function(h){return h.n;});if(H.length)T.push({type:'scatter3d',mode:'markers',x:H.map(function(h){return h.p[0];}),y:H.map(function(h){return h.p[1];}),z:H.map(function(h){return h.p[2];}),marker:{size:3,color:'#111'},text:H.map(function(h){return h.id+': GT '+h.gt.toFixed(2);}),hoverinfo:'text',name:'Ore Geometry: titik intercept',showlegend:false});}
  if(OG.axes.length){var ax=[],ay=[],az=[];OG.axes.forEach(function(a){ax.push(a.p1[0],a.p2[0],null);ay.push(a.p1[1],a.p2[1],null);az.push(a.p1[2],a.p2[2],null);});T.push({type:'scatter3d',mode:'lines',x:ax,y:ay,z:az,line:{color:'#1971c2',width:9},name:'Ore Geometry: sumbu shoot',hoverinfo:'name'});
    T.push({type:'scatter3d',mode:'text',x:OG.axes.map(function(a){return a.p2[0];}),y:OG.axes.map(function(a){return a.p2[1];}),z:OG.axes.map(function(a){return a.p2[2];}),text:OG.axes.map(function(a){return a.name+' '+Math.round(a.pl)+'→'+('00'+Math.round(a.tr)).slice(-3);}),textfont:{size:11,color:'#1971c2'},hoverinfo:'skip',showlegend:false});}
  if(OG.S&&OG.p.gs.show){var cols=['#fab005','#fd7e14','#e8590c','#c92a2a','#862e9c','#5f3dc4'];OG.S.shells.forEach(function(s,q){if(!s.show||!s.nt)return;T.push({type:'mesh3d',name:'Grade shell '+OG.S.el+' ≥ '+s.cut,x:s.x,y:s.y,z:s.z,i:s.i,j:s.j,k:s.k,color:cols[q%cols.length],opacity:Math.max(0.18,0.5-0.1*q),flatshading:false,lighting:{ambient:0.55,diffuse:0.8,specular:0.15},hoverinfo:'name',showlegend:true});});}
  }catch(e){console.error(e);}}

/* ---------- panel ---------- */
function ogDirty(){if(window.SA&&SA.dirty)SA.dirty();ogPanel();if(OG.view==='ls')ogPlotLS();else{try{updatePlot();}catch(e){}}}
function ogSet(k,v,re){OG.p[k]=v;if(re==='ic'){OG.R=null;OG.L=null;}else if(re==='ls')OG.L=null;ogDirty();}
function ogGs(k,v){OG.p.gs[k]=v;ogPanel();}
function ogSec(s){OG.sec=s;if(s==='2'&&OG.R&&OG.view!=='ls')ogShowLS(true);else if(s!=='2'&&s!=='3'&&OG.view==='ls')ogShowLS(false);else ogPanel();}
function ogRunIc(){var t0=performance.now();var R=ogIcpt();OG.msg=R?'&#10003; '+ogN(R.nIc)+' intercept di '+R.nHit+' bor, '+R.nZero+' bor GT 0 ('+((performance.now()-t0)/1000).toFixed(1)+' s)':OG.msg;if(R)ogLS();ogDirty();}
function ogPanel(){var b=$('ogBody');if(!b)return;var P=OG.p,R=OG.R,L=OG.L,el=ogEl(),sec=OG.sec,tabs=[['1','① Intercept'],['2','② Long section'],['3','③ Ore shoot'],['4','④ Grade shell'],['a','Semua']];
  var inp=function(k,v,st,tt,re){return '<input type=number step='+(st||'any')+' value="'+ogE(v)+'"'+(tt?' title="'+ogE(tt)+'"':'')+' onchange="ogSet(\''+k+'\',this.value'+(re?',\''+re+'\'':'')+')">';},
    gin=function(k,v,st,tt){return '<input type=number step='+(st||'any')+' value="'+ogE(v)+'"'+(tt?' title="'+ogE(tt)+'"':'')+' onchange="ogGs(\''+k+'\',this.value)">';},
    sel=function(oc,opts,cur){return '<select onchange="'+oc+'">'+opts.map(function(o){return '<option value="'+ogE(o[0])+'"'+(String(cur)===String(o[0])?' selected':'')+'>'+ogE(o[1])+'</option>';}).join('')+'</select>';},on=function(s){return sec==='a'||sec===s;};
  var h='<div class=hint style="margin-top:-2px"><b>Referensi geologist</b> untuk melihat geometri deposit secara utuh sebelum pemodelan &amp; estimasi. Hasil menu ini <b>tidak</b> dipakai Geological Modelling, basis data struktur, maupun Model Estimation.</div>';
  h+='<div class=rptabs>'+tabs.map(function(t){return '<button class="'+(sec===t[0]?'on':'')+'" onclick="ogSec(\''+t[0]+'\')">'+t[1]+'</button>';}).join('')+'</div>';
  if(OG.msg)h+='<div class="box gmstate" style="margin-bottom:6px">'+OG.msg+(OG.busy?'<div style="height:6px;background:var(--bd);border-radius:3px;margin-top:6px;overflow:hidden"><div id=ogProg style="height:6px;width:0;background:var(--pr)"></div></div>':'')+'</div>';
  if(on('1')){h+='<h4>Intercept per bor (akumulasi GT)</h4><div class="g2 f"><div><label>Unsur</label>'+sel("ogSet('el',this.value,'ic')",elements.map(function(e){return[e,e];}),el)+'</div><div><label>Cut-off intercept</label>'+inp('cut',P.cut,'any','Sampel ≥ cut-off membentuk intercept','ic')+'</div></div>'+
      '<div class="g3 f"><div><label>Panjang min (m)</label>'+inp('minL',P.minL,'any','Intercept lebih pendek diabaikan','ic')+'</div><div><label>Dilusi internal maks (m)</label>'+inp('dil',P.dil,'any','Sisipan di bawah cut-off sepanjang ini boleh digabung bila rata-rata gabungan tetap ≥ cut-off','ic')+'</div><div><label>Toleransi bor GT 0 (m)</label>'+inp('zTol',P.zTol,'any','Bor tanpa intercept dipakai sebagai GT 0 di titik tembus bidang acuan, atau di titik terdekat bila jaraknya ≤ toleransi','ic')+'</div></div>'+
      '<div class=hint style="margin-top:-4px">GT = &Sigma;(kadar &times; panjang) semua intercept dalam satu bor (dijumlah per bor), dikoreksi ke <b>tebal sebenarnya</b> (cos sudut bor terhadap normal bidang acuan).</div>'+
      '<div class="g3 f"><div><label>Bidang acuan</label>'+sel("ogSet('plane',this.value,'ic')",[['auto','Otomatis dari intercept'],['man','Manual']],P.plane)+'</div>'+(P.plane==='man'?'<div><label>Dip (&deg;)</label>'+inp('pdip',P.pdip,'any','','ic')+'</div><div><label>Dip dir (&deg;)</label>'+inp('pddir',P.pddir,'any','','ic')+'</div>':'<div class=hint style="grid-column:span 2;align-self:end;margin:0">'+(R?'Dip '+ogN(R.pl.dip,0)+'&deg; &rarr; '+ogN(R.pl.ddir,0)+'&deg; (strike '+ogN(R.pl.strike,0)+'&deg;)':'dihitung dari sebaran intercept (bobot GT)')+'</div>')+'</div>'+
      '<button class=btn-pri style="width:100%" onclick="ogRunIc()">&#9654; Hitung intercept &amp; GT</button>';
    if(R){var top=R.H.filter(function(x){return x.n;}).sort(function(a,b){return b.gt-a.gt;}).slice(0,10);
      h+='<div class="box gmstate" style="margin-top:6px"><b>'+ogN(R.nIc)+' intercept</b> di '+R.nHit+' bor · '+R.nZero+' bor GT 0 · '+R.nSkip+' bor dilewati (tidak menembus bidang acuan / tanpa assay '+ogE(R.el)+')<br>Bidang acuan dip '+ogN(R.pl.dip,0)+'&deg; ke '+ogN(R.pl.ddir,0)+'&deg;</div>'+
        (top.length?'<div class=gmlist style="max-height:180px"><table class=pltb><tr><th>HoleID</th><th>Int.</th><th>Tebal sebenarnya</th><th>Rata-rata</th><th>GT</th></tr>'+top.map(function(x){return '<tr><td>'+ogE(x.id)+'</td><td>'+x.n+'</td><td>'+ogN(x.tt,2)+' m</td><td>'+ogN(x.avg,2)+'</td><td><b>'+ogN(x.gt,2)+'</b></td></tr>';}).join('')+'</table></div>':'')+
        '<button style="width:100%" onclick="ogIcCsv()">&#8681; Export intercept (CSV)</button>';}}
  if(on('2')){h+='<h4>Long section GT</h4>'+(R?'':'<div class=hint>Hitung intercept dulu.</div>')+
      '<div class="g3 f"><div><label>Jenis</label>'+sel("ogSet('ls',this.value,'ls')",[['v','Vertikal'],['vein','Bidang vein (miring)'],['man','Manual (azimuth + dip)']],P.ls)+'</div>'+(P.ls!=='vein'?'<div><label>Azimuth (&deg;, kosong = strike)</label><input type=number step=any value="'+ogE(P.lsAz)+'" placeholder="'+(R?ogN(R.pl.strike,0):'auto')+'" onchange="ogSet(\'lsAz\',this.value,\'ls\')"></div>':'<div></div>')+(P.ls==='man'?'<div><label>Dip bidang (&deg;)</label>'+inp('lsDip',P.lsDip,'any','','ls')+'</div>':'<div></div>')+'</div>'+
      '<div class=imsec>RBF 2D (spheroidal lokal)</div><div class="g3 f"><div><label>Range mayor (m, 0 = auto)</label>'+inp('lsR1',P.lsR1,'any','Bawaan 4 x median jarak antar bor di long section','ls')+'</div><div><label>Range minor (m, 0 = = mayor)</label>'+inp('lsR2',P.lsR2,'any','','ls')+'</div><div><label>Arah mayor di LS (&deg;)</label>'+inp('lsAng',P.lsAng,'any','Sudut sumbu mayor dari sumbu horizontal long section (berlawanan jarum jam)','ls')+'</div></div>'+
      '<div class="g3 f"><div><label>Alpha</label>'+sel("ogSet('lsAlpha',+this.value,'ls')",[[3,'3 (turun cepat)'],[5,'5'],[7,'7'],[9,'9 (halus)']],P.lsAlpha)+'</div><div><label>Nugget (0–0,9)</label>'+inp('lsNug',P.lsNug,'any','','ls')+'</div><div><label>Transformasi</label>'+sel("ogSet('lsTr',this.value,'ls')",[['log','log(GT+1)'],['none','Tanpa']],P.lsTr)+'</div></div>'+
      '<div class="g2 f"><div><label>Resolusi grid (m, 0 = auto)</label>'+inp('lsRes',P.lsRes,'any','','ls')+'</div><div><label>Kelas GT (kosong = auto)</label><input type=text value="'+ogE(P.lsCls)+'" placeholder="mis. 1, 2, 5, 10, 20" onchange="ogSet(\'lsCls\',this.value)"></div></div>'+
      (L&&L.grid?'<div class=hint style="margin-top:-4px">Range '+ogN(L.r1,0)+' / '+ogN(L.r2,0)+' m · median jarak bor '+ogN(L.med,1)+' m · grid '+L.grid.nx+' × '+L.grid.ny+' ('+ogN(L.grid.res,1)+' m) · '+ogN(L.ms,0)+' ms. Di luar range data, kontur tidak diekstrapolasi.</div>':'')+
      '<div class="g2 f"><button class="'+(OG.view==='ls'?'':'btn-pri')+'" onclick="ogShowLS('+(OG.view==='ls'?'false':'true')+')"'+(R?'':' disabled')+'>'+(OG.view==='ls'?'&#9664; Kembali ke 3D':'Tampilkan long section &#9654;')+'</button><label class=sw style="align-self:center"><input type=checkbox '+(P.show3d?'checked':'')+' onchange="ogSet(\'show3d\',this.checked)">GT di 3D (bidang vein)</label></div>';}
  if(on('3')){var Au=R?ogAuto():null,FL=ogFieldLin();h+='<h4>Ore shoot: pitch, plunge &amp; trend</h4>'+(R?'':'<div class=hint>Hitung intercept dulu.</div>')+
      '<div class=hint style="margin-top:-2px">Gambar sumbu shoot di long section (2 klik: atas &rarr; arah menunjam). Garis di long section dikembalikan ke bidang vein acuan, lalu dihitung <b>pitch</b> (di bidang vein, dari arah strike), <b>plunge</b> dan <b>trend</b>.</div>'+
      '<div class="g2 f"><button class="'+(OG.draw?'btn-pri':'')+'" onclick="if(OG.view!==\'ls\')ogShowLS(true);OG.draw=OG.draw?null:{a:null};ogPlotLS();ogPanel()"'+(R?'':' disabled')+'>'+(OG.draw?'&#9679; Klik di long section&hellip; (Esc)':'&#9998; Gambar sumbu shoot')+'</button><button onclick="ogAutoAdd()"'+(R?'':' disabled')+'>&#9881; Usulan otomatis</button></div>'+
      (Au?'<div class=hint>Usulan otomatis (fan variogram GT di bidang vein, '+Au.n+' bor termasuk GT 0, jarak '+ogN(Au.lag[0],0)+'–'+ogN(Au.lag[1],0)+' m): pitch '+ogN(ogPitch(Au.l,R.pl),0)+'&deg;, plunge '+ogN(ogPT(Au.l).pl,0)+'&deg; &rarr; '+ogN(ogPT(Au.l).tr,0)+'&deg;; rasio kemenerusan '+ogN(Au.el,1)+' : 1'+(Au.el<1.5?' <span class=warn>(lemah: arah kurang jelas)</span>':'')+'.</div>':'');
    if(OG.axes.length)h+='<div class=gmlist style="max-height:200px"><table class=pltb><tr><th>Sumbu</th><th>Pitch</th><th>Plunge &rarr; trend</th><th>Panjang</th><th></th></tr>'+OG.axes.map(function(a){return '<tr><td><input type=text value="'+ogE(a.name)+'" style="width:110px" onchange="var a=OG.axes.filter(function(x){return x.id===\''+a.id+'\';})[0];if(a){a.name=this.value;ogDirty();}"></td><td>'+ogN(a.pitch,0)+'&deg;</td><td><b>'+ogN(a.pl,0)+'&deg; &rarr; '+('00'+Math.round(a.tr)).slice(-3)+'&deg;</b></td><td>'+ogN(a.len,0)+' m</td><td><button class=x onclick="ogAxDel(\''+a.id+'\')">&times;</button></td></tr>';}).join('')+'</table></div>'+
      '<button style="width:100%" onclick="ogAxCsv()" title="Format sama dengan CSV struktur (No, X, Y, Z, Dip, Dip_Azimuth, Plunge, Trend). Tidak otomatis masuk basis data struktur.">&#8681; Export sumbu shoot (CSV)</button>';
    if(FL.length)h+='<div class=hint style="margin-top:6px"><b>Pembanding</b> — lineasi lapangan di basis data struktur (dibaca saja): '+FL.slice(0,8).map(function(f){return ogE(f.no)+' '+ogN(f.pl,0)+'→'+('00'+Math.round(f.tr)).slice(-3)+' (pitch '+ogN(f.pitch,0)+'&deg;'+(f.off>20?', '+ogN(f.off,0)+'&deg; keluar bidang':'')+')';}).join(' · ')+(FL.length>8?' …':'')+'</div>';}
  if(on('4')){var gs=P.gs,Ax=ogGsAxes(),nA=(window.assays||[]).length,S=OG.S;h+='<h4>Grade shell 3D (seluruh data bor)</h4>'+
      '<div class="g3 f"><div><label>Metode</label>'+sel("ogGs('mode',this.value)",[['ind','Indikator (peluang)'],['num','Numerik']],gs.mode)+'</div><div><label>Unsur</label>'+sel("ogGs('el',this.value)",elements.map(function(e){return[e,e];}),gs.el||el)+'</div><div><label>Cut-off (pisah koma)</label><input type=text value="'+ogE(gs.cuts)+'" onchange="ogGs(\'cuts\',this.value)"></div></div>'+
      '<div class="g3 f">'+(gs.mode!=='num'?'<div><label>Ambang peluang</label>'+gin('pth',gs.pth,'any','Shell = peluang ≥ nilai ini (bawaan 0,5)')+'</div>':'<div><label>Transformasi</label>'+sel("ogGs('tr',this.value)",[['log','Log'],['none','Tanpa']],gs.tr)+'</div>')+'<div><label>Maks baris assay</label>'+gin('rows',gs.rows,1,'Bila data lebih besar, dipakai baris paling bawah (terbaru) tabel assay')+'</div><div><label>Komposit (m, 0 = asli)</label>'+gin('comp',gs.comp)+'</div></div>'+
      '<div class=hint style="margin-top:-4px">'+(gs.mode==='num'?'Numerik cenderung menyusutkan shell pada vein tipis (kadar dirata-rata dengan sampel di luar vein); untuk emas disarankan indikator. ':'')+'Tabel assay: '+ogN(nA)+' baris'+(nA>ogNum(gs.rows,100000)?' &rarr; dipakai <b>'+ogN(ogNum(gs.rows,100000))+' baris paling bawah</b>':'')+'. Tanpa batas domain.</div>'+
      '<div class=imsec>Elipsoid (spheroidal lokal)</div><div class="g3 f"><div><label>Orientasi</label>'+sel("ogGs('ori',this.value)",[['plane','Bidang acuan ①'],['man','Manual']],gs.ori)+'</div>'+(gs.ori==='man'?'<div><label>Dip (&deg;)</label>'+gin('dip',gs.dip)+'</div><div><label>Dip dir (&deg;)</label>'+gin('ddir',gs.ddir)+'</div>':'<div class=hint style="grid-column:span 2;align-self:end;margin:0">'+(OG.R?'dip '+ogN(Ax.dip,0)+'&deg; &rarr; '+ogN(Ax.ddir,0)+'&deg;':'hitung intercept dulu, atau pilih Manual')+'</div>')+'</div>'+
      '<div class="g3 f"><div><label>Pitch mayor (&deg;)</label>'+gin('pitch',gs.pitch,'any','Sudut sumbu mayor dari strike di bidang')+'</div><div class=hint style="grid-column:span 2;align-self:end;margin:0">Sumbu mayor: plunge <b>'+ogN(Ax.pt.pl,0)+'&deg; &rarr; '+ogN(Ax.pt.tr,0)+'&deg;</b>'+(OG.axes.length?' · <a href=javascript:void(0) onclick="var a=OG.axes[OG.axes.length-1];OG.p.gs.ori=\'man\';OG.p.gs.dip=+a.vein.dip.toFixed(1);OG.p.gs.ddir=+a.vein.ddir.toFixed(1);OG.p.gs.pitch=+a.pitch.toFixed(1);ogPanel()">pakai sumbu shoot terakhir</a>':'')+'</div></div>'+
      '<div class="g3 f"><div><label>Range mayor (m)</label>'+gin('r1',gs.r1)+'</div><div><label>Semi (m)</label>'+gin('r2',gs.r2)+'</div><div><label>Minor (m)</label>'+gin('r3',gs.r3)+'</div></div>'+
      '<div class="g3 f"><div><label>Alpha</label>'+sel("ogGs('alpha',+this.value)",[[3,'3'],[5,'5'],[7,'7'],[9,'9']],gs.alpha)+'</div><div><label>Nugget (0–0,9)</label>'+gin('nug',gs.nug)+'</div><div><label>Resolusi (m, 0 = auto)</label>'+gin('res',gs.res)+'</div></div>'+
      '<div class="g2 f"><button onclick="ogShell(true)"'+(OG.busy?' disabled':'')+'>&#9654; Pratinjau cepat</button><button class=btn-pri onclick="ogShell(false)"'+(OG.busy?' disabled':'')+'>&#9654;&#9654; Hitung grade shell</button></div>';
    if(S&&S.shells.length){h+='<div class="box gmstate" style="margin-top:6px">'+ogE(S.el)+' · '+(S.mode==='ind'?'indikator':'numerik')+(S.prev?' · <b>pratinjau</b>':'')+' · '+ogN(S.n)+' titik ('+ogN(S.nRows)+' baris assay) · grid '+S.nn.join(' × ')+' @ '+ogN(S.res,1)+' m · '+(S.ms/1000).toFixed(1)+' s<br>Elipsoid '+S.r.map(function(v){return ogN(v,0);}).join(' / ')+' m, mayor '+ogN(S.Ax.pt.pl,0)+'&deg; &rarr; '+ogN(S.Ax.pt.tr,0)+'&deg;</div>'+
        '<div class=gmlist><table class=pltb><tr><th></th><th>Cut-off</th><th>Volume</th><th>Sampel &ge; cut di dalam</th><th>Sampel &lt; cut di dalam</th></tr>'+S.shells.map(function(s,q){return '<tr><td><input type=checkbox '+(s.show?'checked':'')+' onchange="OG.S.shells['+q+'].show=this.checked;updatePlot()"></td><td><b>&ge; '+ogN(s.cut,2)+'</b></td><td>'+ogN(s.vol,0)+' m&sup3;'+(s.over?' <span class=warn>(terpotong)</span>':'')+'</td><td>'+(s.nA?ogN(100*s.nAin/s.nA,0)+'% dari '+ogN(s.nA):'-')+'</td><td>'+(s.nAin+s.nBin?ogN(100*s.nBin/(s.nAin+s.nBin),0)+'% isi shell':'-')+'</td></tr>';}).join('')+'</table></div>'+
        '<div class="g3 f"><label class=sw style="margin:0"><input type=checkbox '+(gs.show?'checked':'')+' onchange="OG.p.gs.show=this.checked;updatePlot()">Tampil di 3D</label><button onclick="ogShellExp(\'obj\')">&#8681; OBJ</button><button onclick="ogShellExp(\'dxf\')">&#8681; DXF</button></div>';}}
  b.innerHTML=h;}

/* ---------- pasang: panel, tree tab, 3D, simpan ---------- */
(function(){var side=$('side');if(!side||$('pOG'))return;var s=document.createElement('section');s.id='pOG';s.hidden=true;s.innerHTML='<h3>Ore Geometry</h3><div id=ogBody></div>';side.appendChild(s);
  var st=document.createElement('style');st.textContent='#ogDiv{position:absolute;inset:0;z-index:8;background:var(--sf);display:none}#ogPlot{position:absolute;inset:0}#ogXY{position:absolute;left:10px;bottom:6px;z-index:3;font:12px Arial;background:rgba(255,255,255,.85);color:#222;padding:2px 6px;border-radius:4px}';document.head.appendChild(st);
  var _u=uiTab;uiTab=function(n){var r=_u.apply(this,arguments);var p=$('pOG');if(p)p.hidden=n!=='OG';if(n==='OG'){['Rep','Val'].forEach(function(k){var q=$('p'+k);if(q)q.hidden=true;});try{if(uiSideW()<440)uiSideW(440);}catch(e){}if(!OG.R&&window.elements&&elements.length&&!OG._auto){OG._auto=1;setTimeout(function(){try{ogRunIc();}catch(e){console.error(e);}},60);}ogPanel();}else if(OG.view==='ls'){var d=$('ogDiv');if(d)d.style.display='none';OG.view='3d';}return r;};
  if(typeof imTraces==='function'){var _t=imTraces;imTraces=function(T,o){var r=_t.apply(this,arguments);ogTraces(T,o||{});return r;};}
  var _c=SA.collectWork;SA.collectWork=function(){var w=_c.apply(this,arguments);try{w.og={p:OG.p,axes:OG.axes,on:OG.on};}catch(e){}return w;};
  var _a=SA.applyWork;SA.applyWork=function(W){try{if(W&&W.og){var o=W.og;if(o.p){var g=Object.assign({},OG.p.gs,o.p.gs||{});OG.p=Object.assign({},OG.p,o.p);OG.p.gs=g;}OG.axes=o.axes||[];if(o.on!=null)OG.on=o.on;OG.R=null;OG.L=null;OG.S=null;}}catch(e){console.error(e);}return _a.apply(this,arguments);};
  window.addEventListener('resize',function(){if(OG.view==='ls'){try{Plotly.Plots.resize('ogPlot');}catch(e){}}});})();
