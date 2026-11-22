/* ================= Mesin desain bench + jalan spiral ================= */
const RAMP=()=>({on:$('rOn').checked,W:+$('rW').value||12,g:Math.max(0.02,(+$('rG').value||10)/100),dir:+rdir()});
function bandPoly(arc,d0,d1){const o=[];for(const q of arc)o.push([q.p[0]+q.n[0]*d1(q.t),q.p[1]+q.n[1]*d1(q.t)]);for(let k=arc.length-1;k>=0;k--){const q=arc[k];o.push([q.p[0]+q.n[0]*d0(q.t),q.p[1]+q.n[1]*d0(q.t)]);}return [toC(o)];}
function arcFrom(P,pt,len,dir){const br=bigRing(P);if(!br)return null;const r=ringOf(br),c=ringCum(r),per=c[c.length-1],n=ringNear(r,c,pt);const L=Math.min(len,per*0.92);return {arc:ringArc(r,c,n.s,L,dir,1.5),short:len>per*0.92,per};}
/* ---------- string & permukaan ---------- */
function ringPts(path,z){const r=path.map(q=>[q.X/CS+O[0],q.Y/CS+O[1],z]);r.push(r[0].slice());return r;}
/* rapikan string tepi jalan: buang lipatan balik (titik yang berbalik arah pada ruas pendek) dan simpul (string memotong dirinya sendiri).
 Lipatan muncul di tikungan tajam / ujung ramp karena tepi jalan dibuat dari offset normal dinding. */
function roadTidy(P0){/* aktif. Pengaruh ke volume desain baru < 0,01%; pada uji perdalam selisih volume tambahan berubah 1% (= 0,2% dari volume pit) karena permukaan pit lama & baru sama-sama ditriangulasi ulang. Matikan dengan window.__NORT=1 */if(window.__NORT||!P0||P0.length<4)return P0;let P=P0.map(p=>p.slice());
 for(let pass=0;pass<12;pass++){let ch=false;
  for(let i=1;i<P.length-1;i++){const a=[P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]],b=[P[i+1][0]-P[i][0],P[i+1][1]-P[i][1]],la=Math.hypot(a[0],a[1]),lb=Math.hypot(b[0],b[1]);if(la<0.02){P.splice(i,1);ch=true;i--;continue;}if(lb<1e-9)continue;if((a[0]*b[0]+a[1]*b[1])/(la*lb)<-0.7&&Math.min(la,lb)<2&&P.length>3){P.splice(i,1);ch=true;i--;}}
  /* simpul: ruas i memotong ruas j (j>i+1, jendela 40 titik) → titik di antaranya diganti titik potong */
  const LW=window.__RTSMALL?8:40,LL=window.__RTSMALL?10:Math.max(10,3*((typeof RAMP==='function'&&RAMP().W)||12));/* simpul sampai 3 × lebar jalan: tepi dalam jalan yang berbelok di sudut sempit (ujung jalan sump, 16 Nov) — tepi yang menyilang dirinya sendiri tidak pernah sah */
  outer:for(let i=0;i<P.length-3;i++)for(let j=i+2;j<Math.min(P.length-1,i+LW);j++){{let ll=0;for(let k=i+1;k<=j;k++)ll+=Math.hypot(P[k][0]-P[k-1][0],P[k][1]-P[k-1][1]);if(ll>LL)continue;}const p=P[i],q=P[i+1],u=P[j],v=P[j+1],d1=[q[0]-p[0],q[1]-p[1]],d2=[v[0]-u[0],v[1]-u[1]],den=d1[0]*d2[1]-d1[1]*d2[0];if(Math.abs(den)<1e-9)continue;const t=((u[0]-p[0])*d2[1]-(u[1]-p[1])*d2[0])/den,w=((u[0]-p[0])*d1[1]-(u[1]-p[1])*d1[0])/den;if(t>1e-6&&t<1-1e-6&&w>1e-6&&w<1-1e-6){const X=[p[0]+d1[0]*t,p[1]+d1[1]*t,p[2]+(q[2]-p[2])*t];P.splice(i+1,j-i,X);ch=true;break outer;}}
  if(!ch)break;}
 return P.length>=2?P:P0;}
/* string bench harus bersarang: toe di dalam crest bench yang sama (≥ 5 cm), crest bench bawah di dalam toe bench atasnya (RL sama).
 Penghalusan & pemotongan tiap cincin secara terpisah bisa membuat garis RL berbeda saling silang beberapa desimeter; di sini cincin bawah dipotong
 ke cincin atasnya sehingga yang tadinya silang menjadi sejajar rapat. Bench yang memakai jalan pit final dilewati (crest-nya sengaja memuat badan jalan). */
function nestFix(B){if(window.__NONEST2||B.length<1)return B;const ar=Q=>Q.reduce((t,r)=>t+Math.abs(cArea(r)),0),O=B.map(b=>Object.assign({},b));
 for(let i=O.length-1;i>=0;i--){const b=O[i];if(!b.crest||!b.toe||!b.crest.length||!b.toe.length)continue;
  {const k0=CORNER;try{CORNER='miter';const lim=cOff(b.crest,-0.05);CORNER=k0;const t=cInter(b.toe,lim);if(t.length&&ar(b.toe)-ar(t)>0.05)b.toe=t;}catch(e){}finally{CORNER=k0;}}
  if(i>0){const lo=O[i-1];if(lo.crest&&lo.crest.length&&Math.abs(lo.zc-b.zt)<1e-6&&!lo.fa){try{let c=cInter(lo.crest,b.toe);/* di lereng, bagian crest bench bawah yang permukaan topo-nya lebih rendah dari RL ini memang boleh di luar toe bench atas (di situ tidak ada muka bench: galian mulai dari permukaan). Hanya bagian yang masih berupa batuan yang dijepit. */if(TP.length&&BASE&&typeof topoAbove==='function'){const TA=topoAbove(b.zt);const airPart=TA.length?cDiff(lo.crest,TA):lo.crest;if(airPart.length)c=c.length?cUnion(c,airPart):airPart;}if(c.length&&ar(lo.crest)-ar(c)>0.05)lo.crest=c;}catch(e){}}}}
 /* pita jalan vs cincin bench: badan ramp tidak digali sampai RL toe, jadi pita jalan (di antara dua tepinya) harus di LUAR poligon toe bench itu dan di DALAM poligon crest-nya.
    Pembulatan cincin di ujung takik jalan bisa membuat tepi jalan menyilang toe/crest beberapa desimeter; di sini toe dikurangi pita jalan dan crest digabung dengannya (lebihan 5 cm). */
 if(!window.__NORIB)for(const b of O){const RB=[];for(const rd of (b.roads||(b.road?[b.road]:[]))){if(rd.landing||!rd.in||!rd.out||rd.in.length<2||rd.out.length<2)continue;RB.push(toC(rd.in.map(p=>[p[0],p[1]]).concat(rd.out.map(p=>[p[0],p[1]]).reverse())));}
  if(!RB.length||!b.toe||!b.toe.length)continue;const k0=CORNER;try{CORNER='miter';let R=cClean(ClipperLib.Clipper.SimplifyPolygons(RB,ClipperLib.PolyFillType.pftNonZero));R=cOff(R,0.05);CORNER=k0;if(!R.length)continue;b._rib=R;const t=cDiff(b.toe,R);if(t.length&&ar(b.toe)-ar(t)>0.05)b.toe=t;if(b.crest&&b.crest.length){const c=cUnion(b.crest,R);if(c.length&&ar(c)-ar(b.crest)>0.05)b.crest=c;}}catch(e){}finally{CORNER=k0;}}
 /* toe bench ini dan crest bench bawah yang semula SATU poligon (tanpa berm) harus tetap satu poligon setelah dirapikan, supaya string-nya tidak rangkap / saling silang */
 for(let i=1;i<O.length;i++){if(B[i-1].crest!==B[i].toe||!O[i].toe||!O[i].toe.length)continue;try{let X=O[i].toe;const rb=O[i-1]._rib;if(rb&&rb.length)X=cUnion(X,rb);if(X.length){O[i].toe=X;O[i-1].crest=X;}}catch(e){}}
 /* sambungan dengan berm: jalan bench bawah yang memotong berm (permukaan jalan di bawah RL toe bench atas) berada di bawah udara, jadi toe bench atas melingkarinya.
    Hanya komponen pita jalan yang bersinggungan dengan toe itu yang digabung. */
 if(!window.__NORIB2)for(let i=1;i<O.length;i++){if(B[i-1].crest===B[i].toe)continue;const rb=O[i-1]._rib,T=O[i].toe;if(!rb||!rb.length||!T||!T.length)continue;try{const nearT=cOff(T,0.3),add=[];for(const r of rb){if(cArea(r)<=0)continue;const x=cInter([r],nearT);if(ar(x)>0.3)add.push(r);}if(add.length){const X=cUnion(T,add);if(X.length&&ar(X)-ar(T)>0.05){const Cu=O[i].crest;let Y=X;if(Cu&&Cu.length){const k0=CORNER;try{CORNER='miter';Y=cInter(X,cOff(Cu,-0.05));}finally{CORNER=k0;}}O[i].toe=Y.length?Y:T;}}}catch(e){}}
 for(let i=0;i<O.length;i++)O[i]._toe0=B[i].toe;return O;}
/* tepi jalan harus maju terus sepanjang jalan: titik yang berjalan mundur (gerigi offset di tikungan cekung) dibuang.
 Acuan = tepi pasangan yang lebih bersih (lebih sedikit titik balik); kemajuan diukur sebagai jarak sepanjang acuan + proyeksi ke garis singgungnya. Ujung awal & akhir dipertahankan. */
function roadRevN(P){let n=0;for(let i=1;i<P.length-1;i++){const ax=P[i][0]-P[i-1][0],ay=P[i][1]-P[i-1][1],bx=P[i+1][0]-P[i][0],by=P[i+1][1]-P[i][1],la=Math.hypot(ax,ay),lb=Math.hypot(bx,by);if(la>1e-6&&lb>1e-6&&(ax*bx+ay*by)/(la*lb)<-0.5)n++;}return n;}
function roadMono(E,R){if(window.__NOMONO||!E||!R||E.length!==R.length||E.length<4)return E;const n=E.length,c=[0];for(let i=1;i<n;i++)c.push(c[i-1]+Math.hypot(R[i][0]-R[i-1][0],R[i][1]-R[i-1][1]));
 const t=E.map((p,i)=>{const a=R[Math.max(0,i-1)],b=R[Math.min(n-1,i+1)],l=Math.hypot(b[0]-a[0],b[1]-a[1])||1;return c[i]+((p[0]-R[i][0])*(b[0]-a[0])+(p[1]-R[i][1])*(b[1]-a[1]))/l;});
 const K=[0];for(let i=1;i<n-1;i++)if(t[i]>t[K[K.length-1]]+0.05)K.push(i);while(K.length>1&&t[K[K.length-1]]>=t[n-1]-0.05)K.pop();K.push(n-1);let Q=K.length>=2?K.map(i=>E[i].slice()):E.map(p=>p.slice());
 /* ekor walet: titik dengan belokan balik > 135° pada tepi ini (tepi acuan mulus) dibuang berulang; ujung dipertahankan */
 for(let g=0;g<200&&Q.length>2;g++){let hit=-1;for(let i=1;i<Q.length-1;i++){const ax=Q[i][0]-Q[i-1][0],ay=Q[i][1]-Q[i-1][1],bx=Q[i+1][0]-Q[i][0],by=Q[i+1][1]-Q[i][1],la=Math.hypot(ax,ay),lb=Math.hypot(bx,by);if(la<1e-6||lb<1e-6||(ax*bx+ay*by)/(la*lb)<-0.7){hit=i;break;}}if(hit<0)break;Q.splice(hit,1);}
 return Q;}
function benchStrings(B,floor){B=nestFix(B);const S=[];const nB=B.length;for(let i=0;i<nB;i++){const b=B[i];
  for(const r of b.crest)S.push({t:'crest',z:b.zc,pts:ringPts(r,b.zc)});
  let lowerCrestSame=i>0&&Math.abs(B[i-1].zc-b.zt)<1e-6&&!B[i-1].berm&&B[i-1].crest===b.toe;
  /* crest bench bawah nyaris sama dengan toe bench ini (tanpa berm; hanya beda pembulatan potong) → cukup satu string, jangan rangkap */
  if(!lowerCrestSame&&i>0&&!window.__NODEDUP&&Math.abs(B[i-1].zc-b.zt)<1e-6&&!B[i-1].berm&&B[i-1].crest&&B[i-1].crest.length&&b.toe.length){try{const ar=Q=>Q.reduce((t,r)=>t+Math.abs(cArea(r)),0),x=cBool(B[i-1].crest,b.toe,ClipperLib.ClipType.ctXor),ax=ar(x),a0=ar(b.toe);if(ax<Math.max(2,0.002*a0))lowerCrestSame=true;}catch(e){}}
  const FL=floor?(Array.isArray(floor)?floor:[floor]):[];if(!lowerCrestSame&&!FL.some(f=>Math.abs(f.z-b.zt)<1e-6&&(f.P===b.toe||f.P===b._toe0||f.P===b._sp0)))for(const r of b.toe)S.push({t:'toe',z:b.zt,pts:ringPts(r,b.zt)});
  for(const rd of (b.roads||(b.road?[b.road]:[]))){
   /* landasan putar: lingkaran datar di titik balik. Lajur yang masuk / keluar landasan sudah miring di dalam lingkaran itu, jadi garis landasan = lingkaran dikurangi pita lajur
      (bench ini dan bench di atasnya); tanpa ini garis lingkaran menyilang tepi lajur pada RL berbeda. */
   if(rd.landing&&!window.__NOPAD&&rd.in&&rd.in.length>3){try{let rib=b._rib||[];const up=B[i+1];if(up&&up._rib&&up._rib.length)rib=rib.length?cUnion(rib,up._rib):up._rib;if(rib.length){const pad=cDiff([toC(rd.in.slice(0,-1).map(p=>[p[0],p[1]]))],rib).filter(r=>Math.abs(cArea(r))>4);const zl=rd.in[0][2];for(const r of pad)S.push({t:'road',z:b.zt,pts:ringPts(r,zl),fin:true,landing:true});continue;}}catch(e){}}
   {const okP=rd.in&&rd.out&&rd.in.length===rd.out.length&&rd.in.length>3&&!rd.fin,rI=okP?roadRevN(rd.in):0,rO=okP?roadRevN(rd.out):0,mI=okP&&rI>rO?roadMono(rd.in,rd.out):rd.in,mO=okP&&rO>rI?roadMono(rd.out,rd.in):rd.out;
    const eI=rd.in&&rd.in.length>1?(rd.fin?rd.in.map(p=>p.slice()):roadTidy(mI)):null,eO=rd.out&&rd.out.length>1?(rd.fin?rd.out.map(p=>p.slice()):roadTidy(mO)):null;if(eI)S.push({t:'road',z:b.zt,pts:eI,fin:!!rd.fin});if(eO)S.push({t:'road',z:b.zt,pts:eO,fin:!!rd.fin});
    /* garis ujung ruas jalan (tepi ke tepi, datar): menutup pita jalan di kedua ujungnya sehingga ujung tepi jalan tersambung dan permukaan punya sisi yang jelas di awal/akhir ramp */
    if(eI&&eO&&!rd.fin&&!window.__NOCAP){for(const [p,q] of [[eI[0],eO[0]],[eI[eI.length-1],eO[eO.length-1]]]){const d=Math.hypot(p[0]-q[0],p[1]-q[1]);if(d>0.5&&d<3*RAMP().W&&Math.abs(p[2]-q[2])<0.3)S.push({t:'road',z:b.zt,pts:[p.slice(),q.slice()],cap:true});}}}}}
 /* duri & celah selebar nol pada cincin bench (bekas operasi poligon): titik tempat cincin berbalik hampir 180° dibuang berulang; bentuk lain tidak berubah */
 if(!window.__NODESPIKE)for(const q of S){if(!(q.t==='crest'||q.t==='toe'||q.t==='floor')||q.pts.length<5)continue;const P=q.pts;const cl=Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1])<1e-6;if(!cl)continue;let R=P.slice(0,-1);
  for(let g=0;g<400&&R.length>3;g++){let hit=-1;const n=R.length;for(let i=0;i<n;i++){const a0=R[(i-1+n)%n],b0=R[i],c0=R[(i+1)%n],ax=b0[0]-a0[0],ay=b0[1]-a0[1],bx=c0[0]-b0[0],by=c0[1]-b0[1],la=Math.hypot(ax,ay),lb=Math.hypot(bx,by);if(la<1e-4||lb<1e-4){hit=i;break;}if((ax*bx+ay*by)/(la*lb)<-0.97){/* lebar duri: jarak titik tetangga */const w=Math.abs(ax*by-ay*bx)/Math.max(la,lb);if(w<0.3){hit=i;break;}}}if(hit<0)break;R.splice(hit,1);}
  if(R.length>=3&&R.length<P.length-1)q.pts=R.concat([R[0].slice()]);}
 /* garis tutup ujung jalan yang menyilang string jalan lain pada RL berbeda dibuang (menandakan tangga RL antar ruas; cacat itu tetap terlihat sebagai ujung jalan menggantung) */
 if(!window.__NOCAP){const sx=(p,q,u,v)=>{const o=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);return o(p,q,u)*o(p,q,v)<-1e-9&&o(u,v,p)*o(u,v,q)<-1e-9;};const RD=S.filter(x=>!x.cap);
  for(let k=S.length-1;k>=0;k--){const c=S[k];if(!c.cap)continue;const p=c.pts[0],q=c.pts[1];let bad=false;for(const r of RD){for(let j=1;j<r.pts.length&&!bad;j++){const u=r.pts[j-1],v=r.pts[j];if(Math.abs((u[2]+v[2])/2-p[2])<0.3)continue;if(sx(p,q,u,v))bad=true;}if(bad)break;}if(bad)S.splice(k,1);}}
 for(const f of (floor?(Array.isArray(floor)?floor:[floor]):[])){/* lantai = toe bench terbawah: pakai cincin yang sudah dirapikan */const bb=B.find(b=>Math.abs(f.z-b.zt)<1e-6&&(b._toe0===f.P||b._sp0===f.P)&&b.toe!==f.P);for(const r of (bb?bb.toe:f.P))S.push({t:'floor',z:f.z,pts:ringPts(r,f.z)});}return S;}
function densify(pts,step){const o=[pts[0]];for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i],d=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.ceil(d/step);for(let k=1;k<=n;k++){const t=k/n;o.push([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]);}}return o;}
function footOf(S){let U=[];for(const s of S){if(s.t!=='crest'&&s.t!=='toe'&&s.t!=='floor'&&s.t!=='old')continue;if(s.pts.length<4)continue;const a=s.pts[0],b=s.pts[s.pts.length-1];if(Math.hypot(a[0]-b[0],a[1]-b[1])>0.5)continue;U=U.length?cUnion(U,[toC(s.pts)]):cClean(ClipperLib.Clipper.SimplifyPolygons([toC(s.pts)],ClipperLib.PolyFillType.pftNonZero));}
 return U.map(ringOf);}
function inFoot(F,E,N){for(const r of F)if(inPoly([E,N],r))return true;return false;}
function surfOf(S,foot,maxE,air){/* bagian string yang jauh di atas topo (udara) tidak ikut triangulasi: string bertumpuk di udara membuat segitiga tegak */const AH=air&&TP.length?(window.__AIRH>0?window.__AIRH:2)/* 2 m: crest yang 2–5 m di atas tanah masih mengunci toe di bawahnya (TD1 toe RL 305) */:0;const L=[];
 /* string rangkap: bagian string datar yang berimpit (≤ 0,4 m, RL sama) dengan string yang sudah masuk tidak ikut triangulasi lagi.
    Dua garis nyaris berimpit membuat garis patah saling mengunci (ruas tidak bisa dipaksa) dan menghasilkan serpihan tipis. String aslinya tidak diubah. */
 const DD=!window.__NODD,HH=new Map(),hk=(x,y)=>Math.floor(x*2)+'_'+Math.floor(y*2),twin=(p)=>{const cx=Math.floor(p[0]*2),cy=Math.floor(p[1]*2);let bq=null,bd=0.4;for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++){const a=HH.get((cx+dx)+'_'+(cy+dy));if(!a)continue;for(const q of a){if(Math.abs(q[2]-p[2])>0.05)continue;const d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<bd){bd=d;bq=q;}}}return bq;};
 for(const s of S){const d=densify(s.pts,2),flat=DD&&(s.t==='crest'||s.t==='toe'||s.t==='floor'),tw=flat?d.map(twin):null;let cur=[];const flush=()=>{if(cur.length>1)L.push(cur);cur=[];};
  for(let i=0;i<d.length;i++){const p=d[i];let airP=false;if(AH){const tz=topoZ(p[0],p[1]);airP=isFinite(tz)&&p[2]>tz+AH;}if(airP){if(AH&&!flat){if(cur.length)L.push(cur);cur=[];}else flush();continue;}
   if(tw&&tw[i]){/* titik rangkap: tutup potongan berjalan tepat di titik kembarannya, lalu lewati */if(cur.length){cur.push(tw[i].slice());flush();}continue;}
   if(tw&&i>0&&tw[i-1]&&!cur.length)cur.push(tw[i-1].slice());/* potongan baru dimulai dari titik kembaran sebelumnya agar tersambung */cur.push(p);}
  if(flat)flush();else if(cur.length)L.push(cur);
  if(flat)for(const p of densify(s.pts,0.5)){const k=hk(p[0],p[1]);let a=HH.get(k);if(!a)HH.set(k,a=[]);a.push(p);}}const tin=tinFrom(L,maxE||0,true);const T=[],{X,Y,Z}=tin,ft=foot.map(r=>r);
 for(let t=0;t<tin.T.length;t+=3){const a=tin.T[t],b=tin.T[t+1],c=tin.T[t+2],cx=(X[a]+X[b]+X[c])/3,cy=(Y[a]+Y[b]+Y[c])/3;if(inFoot(ft,cx,cy))T.push(a,b,c);}tin.T=T;tin.G=gridOf(tin,1);return tin;}
/* ---------- tampilan hasil ---------- */
function drawStrings(S,g,opac,col0){for(const s of S){const col=col0||COL[s.t]||COL.old;for(const pc of (TP.length?cutPieces(s,true):[s.pts]))g.add(lineObj(pc.map(p=>[p[0],p[1],p[2]+0.08]),col,false,opac?{transparent:true,opacity:opac}:null));}}
/* potong segitiga tepat di garis d=0 (marching triangles): simpan bagian d<=0, titik baru diinterpolasi linear */
function splitTris(X,Y,Z,T,dfn){const n0=X.length,d=new Float64Array(n0);for(let i=0;i<n0;i++)d[i]=NaN;const D=i=>{if(i>=n0)return 0;let v=d[i];if(v!==v){v=dfn(i);if(v!==v)v=-1;d[i]=v;}return v;};
 const NX=[],NY=[],NZ=[],E=new Map(),out=[];const mid=(a,b)=>{const k=a<b?a*4194304+b:b*4194304+a;let r=E.get(k);if(r!==undefined)return r;const da=D(a),db=D(b),t=da/(da-db);NX.push(X[a]+(X[b]-X[a])*t);NY.push(Y[a]+(Y[b]-Y[a])*t);NZ.push(Z[a]+(Z[b]-Z[a])*t);r=n0+NX.length-1;E.set(k,r);return r;};
 for(let t=0;t<T.length;t+=3){const v=[T[t],T[t+1],T[t+2]],dv=v.map(D),neg=dv.map(x=>x<=0),c=neg.filter(Boolean).length;if(c===3){out.push(v[0],v[1],v[2]);continue;}if(c===0)continue;
  for(let r=0;r<3;r++){const a=v[r],b=v[(r+1)%3],cc=v[(r+2)%3];if(c===1&&neg[r]){out.push(a,mid(a,b),mid(a,cc));break;}if(c===2&&!neg[(r+2)%3]){const m1=mid(b,cc),m2=mid(a,cc);out.push(a,b,m1,a,m1,m2);break;}}}
 if(!NX.length)return {X,Y,Z,T:out};const cat=(A,B)=>{const o=new Float64Array(A.length+B.length);o.set(A);o.set(B,A.length);return o;};return {X:cat(X,NX),Y:cat(Y,NY),Z:cat(Z,NZ),T:out};}
function pitMesh(tin0){const sp=TP.length?splitTris(tin0.X,tin0.Y,tin0.Z,tin0.T,i=>{const tz=topoZ(tin0.X[i],tin0.Y[i]);return isFinite(tz)?tin0.Z[i]-tz-0.02:-1;}):tin0;const {X,Y,Z}=sp,n=X.length,keep=sp.T,tin={z0:tin0.z0,z1:tin0.z1};
 const pos=new Float32Array(n*3),col=new Float32Array(n*3),z0=tin.z0,zr=Math.max(tin.z1-z0,1);for(let i=0;i<n;i++){pos[i*3]=X[i]-O[0];pos[i*3+1]=Z[i]-O[2];pos[i*3+2]=-(Y[i]-O[1]);const t=(Z[i]-z0)/zr;col[i*3]=.45+.35*t;col[i*3+1]=.55+.3*t;col[i*3+2]=.78+.15*t;}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('color',new THREE.BufferAttribute(col,3));g.setIndex(keep);g.computeVertexNormals();
 const M=new THREE.Mesh(g,new THREE.MeshPhongMaterial({vertexColors:true,flatShading:true,shininess:20,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1}));M.userData.sp=sp;return M;}
function cutTopo(foot,tin){for(const s of TP){if(s.cutK===foot&&s.g)continue;s.cutK=foot;if(!foot){const had=s.Tshow;s.Tshow=null;s.show=null;s.cut=null;if(had||!s.g)tpBuild(s);continue;}const {X,Y,Z,T}=s.tin;
  /* topo dipotong tepat di garis potong (daylight) supaya rapat dengan permukaan pit */let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const r of foot)for(const p of r){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}
  const sp=splitTris(X,Y,Z,T,i=>{const x=X[i],y=Y[i];if(x<x0-1||x>x1+1||y<y0-1||y>y1+1)return -1;const pz=gridZ(tin.G,x,y);return isFinite(pz)?Z[i]-pz-0.02:-1;});
  s.show=sp;s.Tshow=sp.T;s.cut=(a,b)=>{const mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2;if(!inFoot(foot,mx,my))return false;const pz=gridZ(tin.G,mx,my);return pz<(a[2]+b[2])/2-0.05;};tpBuild(s);}}
function labels(S){clr(G.lab);const seen=new Set();const zs=[...new Set(S.filter(s=>s.t==='crest').map(s=>Math.round(s.z*10)))].sort((a,b)=>a-b),keepZ=new Set(zs.filter((z,i)=>i%3===2||i===zs.length-1));for(const s of S){if(s.t!=='crest'&&s.t!=='floor')continue;if(s.t==='crest'&&zs.length>8&&!keepZ.has(Math.round(s.z*10)))continue;const k=s.t+Math.round(s.z*10);if(seen.has(k))continue;seen.add(k);let p=s.pts[0];for(const q of s.pts)if(q[0]>p[0])p=q;rlLabel((s.t==='floor'?'Lantai ':'')+'RL '+(+s.z.toFixed(1)),p[0],p[1],s.z+0.6,s.t==='floor'?COL.floor:'#1b2a4e');}}
function pitRedraw(){clr(G.pit);clr(G.str);clr(G.lab);CURM=null;const R0=curR();
 if(typeof dayDraw==='function')dayDraw(R0);if(R0){drawStrings(R0.S,G.str);if(R0.tin){R0.mesh=pitMesh(R0.tin);G.pit.add(R0.mesh);CURM=R0.mesh;}cutTopo(R0.foot,R0.tin);labels(R0.S);}else cutTopo(null);
 G.ref.children.forEach(o=>{if(o.userData.rs)o.visible=!R0;});G.ref.visible=MODE!=='edit'&&G.ref.userData.on!==false;if(MODE==='edit'&&window.edDraw)edDraw();else clr(G.edit);if(window.planDraw)planDraw();G.lab.visible=$('lbrl').checked;legend();}
/* ---------- volume ---------- */
function volOf(R0){const out={tot:0,area:0,rows:[],cell:1};if(!R0||!R0.tin)return out;const F=R0.foot;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const r of F)for(const p of r){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}
 const cell=Math.max(0.5,Math.ceil(Math.sqrt((x1-x0)*(y1-y0)/600000)*2)/2),H=PN().H,bins=new Map();let zb=R0.zmin;if(!isFinite(zb)){zb=1e9;for(const b of (R0.B||[]))zb=Math.min(zb,b.zt);if(!isFinite(zb)||zb>1e8)zb=R0.tin.z0||0;}/* tanpa zmin → loop tak berujung */out.cell=cell;
 for(let y=y0+cell/2;y<y1;y+=cell)for(let x=x0+cell/2;x<x1;x+=cell){if(!inFoot(F,x,y))continue;const zp=gridZ(R0.tin.G,x,y);if(!isFinite(zp))continue;out.area+=cell*cell;let zt=topoZ(x,y);if(R0.cap&&isFinite(zt)){const c=R0.cap(x,y);if(isFinite(c))zt=Math.min(zt,c);}if(!isFinite(zt)||zt<=zp)continue;out.tot+=(zt-zp)*cell*cell;
  let k=Math.floor((zp-zb)/H);for(;;k++){const lo=zb+k*H,hi=lo+H;if(lo>=zt)break;const ov=Math.min(hi,zt)-Math.max(lo,zp);if(ov>0)bins.set(k,(bins.get(k)||0)+ov*cell*cell);}}
 out.rows=[...bins.entries()].sort((a,b)=>a[0]-b[0]).map(([k,v])=>({lo:zb+k*H,hi:zb+(k+1)*H,v}));return out;}
/* overall slope: dari tiap titik crest yang masih di dalam tanah (crest tertinggi per lokasi) ke lantai terdekat */
function slopeStat(R0){const cr=R0.S.filter(s=>s.t==='crest'||s.t==='old');if(!cr.length||!R0.floorS||!R0.floorS.length)return null;const fl=R0.floorS.map(s=>{const r=s.pts.map(p=>[p[0],p[1]]);return {r,c:ringCum(r),z:s.z};});
 const best=new Map();for(const s of cr){const st=Math.max(1,Math.floor(s.pts.length/80));for(let i=0;i<s.pts.length;i+=st){const q=s.pts[i],tq=topoZ(q[0],q[1]);if(isFinite(tq)&&tq<s.z-0.5)continue;const k=Math.round(q[0]/10)+'_'+Math.round(q[1]/10);const o=best.get(k);if(!o||s.z>o[2])best.set(k,[q[0],q[1],s.z]);}}
 const ang=[];for(const q of best.values()){let bd=1e18,bz=0;for(const f of fl){if(f.z>q[2]-1)continue;const n=ringNear(f.r,f.c,q);if(n.d<bd){bd=n.d;bz=f.z;}}if(bd<1e17&&bd>0.5&&q[2]-bz>=10)ang.push(Math.atan2(q[2]-bz,bd)*180/Math.PI);}
 if(!ang.length)return null;ang.sort((a,b)=>a-b);const p95=ang[Math.floor(ang.length*0.95)];return {mean:ang.reduce((a,b)=>a+b,0)/ang.length,max:p95,min:ang[0]};}
/* ---------- tombol Buat pit ---------- */
$('go').onclick=()=>{if(!BASE){alert('Langkah 2: buat bentuk awal pit dulu (garis urat atau poligon).');openStep('s2');return;}if(gmode()==='bench'){try{ibStart();}catch(err){alert(err.message);}return;}const t0=performance.now();$('res').innerHTML='Menghitung…';
 setTimeout(()=>{try{runNew();$('res').innerHTML+=' <span class="hint">('+((performance.now()-t0)/1000).toFixed(1)+' dtk)</span>';}catch(err){console.error(err);$('res').innerHTML='<span class="bad">Gagal: '+esc(err.message)+'</span>';}},20);};
/* desain atas→bawah dari batas topo (dipakai Desain baru dan Edit ▸ front bulanan) */
/* pola "Lurus bebas" pada desain atas→bawah (pit final & staging): satu ramp lurus dari bibir ke dasar.
 Pintu masuk = titik yang ditarik di langkah 3 (arah = arah tarikan); tanpa tarikan → bibir terendah yang muat, arah dicari otomatis. */
function lineRamps(ts,CL,zt){const a0=areas()[0],w=[];AU.b0=null;let pl=auLine({at:a0&&a0.rs?a0.rs.slice():null,av:a0&&a0.rv?a0.rv.slice():null},ts,CL,zt);
 if(pl.err&&a0&&a0.rv){const p2=auLine({at:a0.rs?a0.rs.slice():null,av:null},ts,CL,zt);if(!p2.err){pl=p2;w.push('ℹ Arah tarikan tidak muat untuk ramp lurus; arah dicari otomatis dari titik masuk yang sama.');}}
 if(pl.err&&a0&&a0.rs){const p3=auLine({at:null,av:null},ts,CL,zt);if(!p3.err){pl=p3;w.push('ℹ Dari titik masuk yang ditarik ramp lurus tidak muat; pintu masuk dipindah ke bibir terendah yang muat.');}}
 if(pl.err)return {ramps:[],warn:['⚠ Jalan lurus: '+pl.err+'.']};
 if(pl.direct)return {ramps:[],warn:['ℹ Tidak perlu ramp: bibir pit terendah RL '+f1(pl.zl)+' sudah setinggi / lebih rendah dari lantai RL '+f1(pl.zf)+' — alat masuk langsung dari permukaan di sisi rendah.']};
 return {ramps:[pl.rm],warn:w.concat(pl.msg),pl};}
/* beda tinggi di sambungan jalan staging → jalan pit final: ujung bawah jalan staging vs RL jalan final terdekat di denah */
function roadStepB(B){let E=null;const F=[];for(const b of B)for(const rd of (b.roads||[])){if(!rd.in||rd.in.length<2)continue;if(rd.fin){let a=1e9,c=-1e9;for(const p of rd.in){a=Math.min(a,p[2]);c=Math.max(c,p[2]);}if(c-a>0.3)for(const p of rd.in)F.push(p);}else for(const p of [rd.in[0],rd.in[rd.in.length-1]])if(!E||p[2]<E[2])E=p;}
 if(!E||!F.length)return null;let bd=1e9,bz=NaN;for(const p of F){const d=Math.hypot(p[0]-E[0],p[1]-E[1]);if(d<bd){bd=d;bz=p[2];}}if(!(bd<1.5*RAMP().W))return null;const dz=E[2]-bz;return Math.abs(dz)>1?{dz,d:bd,z:E[2],zf:bz}:null;}
function topoDesign(CL,z){const r=topoDesign0(CL,z);if(!CL||window.__NOHT2)return r;let st=null;try{st=roadStepB(r.d.B);}catch(e){}if(!st)return r;
 /* sambungan beda tinggi: coba lagi dengan sasaran = puncak ramp jalan final (bukan ujung landasan). Dipakai bila sambungannya rata (atau jalan staging dibuat utuh) dan lantai tidak lebih dangkal. */
 let r2=null;FIN_HITOP=true;try{r2=topoDesign0(CL,z);}catch(e){console.warn(e);}finally{FIN_HITOP=false;}
 if(r2&&r2.d&&r2.d.B.length){const fz=x=>x.d.floor?x.d.floor.z:1e9;let s2=null;try{s2=roadStepB(r2.d.B);}catch(e){}if(!s2&&fz(r2)<=fz(r)+0.01){r2.d.warn.push('ℹ Sambungan ke jalan pit final diperiksa: cara biasa membuat jalan staging tiba di RL '+f1(st.z)+' sementara jalan final di sampingnya sudah di RL '+f1(st.zf)+' (beda '+f1(Math.abs(st.dz))+' m). Desain ini memakai sambungan yang rata.');return r2;}}
 r.d.warn.push('⚠ Sambungan ke jalan pit final tidak rata: jalan staging tiba di RL '+f1(st.z)+', jalan final di sampingnya di RL '+f1(st.zf)+' (beda '+f1(Math.abs(st.dz))+' m). Saran: pindahkan pintu masuk jalan staging, atau matikan Pakai jalan pit final.');return r;}
function topoDesign0(CL,z){if($('rOn').checked&&rpat()==='free'){const ts=topoStart(),zt=aBot(BASE),L=lineRamps(ts,CL,zt),d=genDown(ts.C,ts.z,{ramps:L.ramps,zref:z,clamp:CL,lim:CL?limAt:null,finRoads:CL?finRoadStrings():null,proj:ts.proj,zmin:zt,mode:'spiral',noAdopt:true});d.warn=L.warn.concat(d.warn);return {d,ts};}
 const ts=topoStart(),zt=aBot(BASE),R0=rampsInit(),o0={zref:z,clamp:CL,lim:CL?limAt:null,finRoads:CL?finRoadStrings():null,proj:ts.proj,zmin:zt},run=(rs,x)=>genDown(ts.C,ts.z,Object.assign({},o0,{ramps:rs},x||{}));
  const pw=[],RS=BASE.lockEntry?R0:stgRamps(ts,CL,R0,zt,pw),/* pintu masuk terkunci (front bulanan): tidak direncanakan ulang ke jalan final */planned=RS.some(r=>r.toFin),MISS=/tidak bertemu ujung atas jalan pit final|belum tepat tiba/;let d=run(RS);
  /* 1) titik masuk yang ditarik manual diuji: bila jalannya menggantung di atas topografi (ditarik di sisi tinggi lereng) atau tidak terbentuk, pintu masuk dipindah ke bibir terendah */
  let base=R0,moved=null;if(TP.length&&!planned&&!BASE.lockEntry&&R0.some(r=>!r.autoLip)){const a0=roadAir(d.B);if(!a0.n||a0.air/a0.n>0.15){const R1=R0.map(r=>Object.assign({},r,{autoLip:true})),d2=run(R1),a1=roadAir(d2.B);if(a1.n&&(!a0.n||a1.air/a1.n<0.5*a0.air/a0.n)){d=d2;base=R1;moved=a0.n?'Titik masuk jalan yang ditarik ada di sisi tinggi lereng: '+Math.round(100*a0.air/a0.n)+'% jalannya akan menggantung di atas topografi. Pintu masuk dipindah otomatis ke bibir terendah pit.':'Dari titik masuk yang ditarik jalan tidak bisa dibentuk (topografi di titik itu tidak lebih tinggi dari lantai). Pintu masuk dipindah otomatis ke bibir terendah pit.';}}}
  /* 2) jalan staging harus menerus dari bibir pit sampai lantai. Bila tidak bisa dipertemukan dengan jalan pit final (mis. jalan final memasuki poligon staging masih di bawah tanah),
     jalan staging dibuat sendiri sampai lantai dan bentuk jalan final tidak dipakai di staging ini (dinding tetap mengikuti dinding final) */
  if(CL&&R0.length&&(d.warn.some(w=>MISS.test(w))||(planned&&pw.some(w=>MISS.test(w))))){d=run(base,{noAdopt:true});
   /* jalan staging dibuat sendiri: pintu masuk tarikan manual belum tentu baik (mis. di sisi tinggi lereng → jalan sangat panjang, lantai tidak tercapai).
      Bandingkan dengan pintu di bibir terendah; pakai yang mencapai lantai lebih dalam, atau lantai sama dengan jalan jauh lebih pendek. */
   if(TP.length&&!BASE.lockEntry&&base.some(r=>!r.autoLip)&&!window.__NOFB2){try{const rl=x=>{let l=0;for(const b of x.B)for(const r of (b.roads||[]))for(let i=1;i<r.in.length;i++)l+=Math.hypot(r.in[i][0]-r.in[i-1][0],r.in[i][1]-r.in[i-1][1]);return l;},fz=x=>x.floor?x.floor.z:1e9,d2=run(base.map(r=>Object.assign({},r,{autoLip:true})),{noAdopt:true});
     if(d2.B.length&&(fz(d2)<fz(d)-0.01||(Math.abs(fz(d2)-fz(d))<0.01&&rl(d2)>1&&rl(d2)<0.7*rl(d)))){const f1_=fz(d),l1=rl(d);d=d2;moved='Dari titik masuk yang ditarik, jalan staging sendiri sepanjang '+nf(l1)+' m hanya mencapai lantai RL '+f1(f1_)+'. Pintu masuk dipindah otomatis ke bibir terendah pit: jalan '+nf(rl(d2))+' m, lantai RL '+f1(fz(d2))+'.';}}catch(e){console.warn(e);}}
   d.warn.push('Jalan pit final tidak bisa disambung dari permukaan di dalam poligon staging ini (ujung atasnya masih di bawah tanah / tidak terjangkau jalan staging). Jalan staging dibuat sendiri dari bibir pit sampai lantai; bentuk jalan final tidak dipakai di staging ini. Agar memakai jalan final, perluas poligon sampai jalan final keluar ke permukaan.');}
  else if(planned)for(const w of pw)d.warn.push('ℹ '+w);if(moved)d.warn.push(moved);
  return {d,ts};}
function runNew(){const CL=MODE==='stage'?finClamp():null;if(MODE==='stage'&&!CL&&!confirm('Belum ada batas pit final (langkah 0). Lanjutkan staging TANPA batas pit final?'))throw new Error('Langkah 0: tentukan pit final dulu, atau lanjutkan tanpa batas.');const tops=areas().map(aTop),zmax=tops.every(isFinite)?Math.max(...tops):NaN,z=BASE.z;let P=BASE.P;let B=[],warn=[],floor=null,zmin=z;
 if(BASE.mode==='bot'){window.__FLCW=[];const ss=startSet(CL);const r=genUp(ss.P0,ss.z0,{ramps:rampsInit(),zmax,zref:ss.z0,clamp:CL,lim:CL?limAt:null,finRoads:CL?finRoadStrings():null,pend:ss.pend});if(window.__FLCW&&window.__FLCW.length)for(const w of window.__FLCW)r.warn.unshift('ℹ '+w);B=r.B;warn=r.warn;floor=ss.floors;zmin=ss.z0;}
 else if(BASE.mode==='topo'){const td=topoDesign(CL,z),d=td.d,ts=td.ts;B=d.B.slice().reverse();warn=d.warn;floor=d.floor;zmin=floor?floor.z:ts.z;}
 else{const d=genDown(P,z,{ramps:rampsInit(),zref:z,clamp:CL,zmin:aBot(BASE)});B=d.B.slice().reverse();warn=d.warn;floor=d.floor;zmin=floor?floor.z:z;
  let need=false;if(TP.length)for(const r of P){for(const q of r){const tz=topoZ(q.X/CS+O[0],q.Y/CS+O[1]);if(tz>z+0.5){need=true;break;}}}
  if(need){const p=prmAt(z+0.01);const toe0=isBerm(z,z,p)?cOff(P,p.B):P;const u=genUp(toe0,z,{ramps:[],zmax,zref:z,clamp:CL});B=B.concat(u.B);warn=warn.concat(u.warn);}}
 B=rlTrim(B,warn);showResult(B,floor,warn,zmin);}
function roadAir(B){let n=0,air=0;for(const b of B)for(const r of (b.roads||[])){if(r.fin||!r.out||r.out.length!==r.in.length)continue;for(let i=0;i<r.in.length;i++){const x=(r.in[i][0]+r.out[i][0])/2,y=(r.in[i][1]+r.out[i][1])/2,zz=(r.in[i][2]+r.out[i][2])/2,t=topoZ(x,y);if(!isFinite(t))continue;n++;if(t<zz-1)air++;}}return {n,air};}
function showResult(B,floor,warn,zmin,inter){B.sort((a,b)=>a.zt-b.zt);if(!B.length)throw new Error(warn[0]||'tidak ada bench yang terbentuk');
 const JR=MODE==='stage'?joinRoads(B):[];/* string utuh; bagian di atas topo dipotong saat tampil/ekspor (cutPieces) */const S0=benchStrings(B,floor),S=S0.concat(JR),foot=footOf(S0),tin=surfOf(S0,foot,0,BASE&&BASE.mode==='topo');/* jalan final yang dipinjam (JR) hanya tampil/ekspor, tidak ikut triangulasi */const RES=Object.assign({cap:rlCap(foot),B,S,foot,tin,floor,zmin:Math.min(zmin,B[0].zt),warn,floorS:S.filter(s=>s.t==='floor')},{stage:MODE==='stage'});RES.day=dayOf(RES);if(BASE&&(BASE.mode==='topo'||BASE.mode==='top')&&window.roadCheck){try{const q=roadCheck(RES);if(q&&q.pieces){const W=RAMP().W;const jb=q.gaps.filter(g=>g>1.5&&g<W*1.15).length,gap=q.gaps.filter(g=>g>=W*1.15).length;
  warn.push('Cek jalan: '+nf(q.len)+' m · kemiringan maks '+q.gradeMax+'% · lebar '+q.wmin+'–'+q.wmax+' m · '+(gap?gap+' sambungan putus':'tersambung')+(jb?' · '+jb+' switchback':'')+(q.ovl>20?' · ⚠ '+q.ovl+' titik jalan bertumpuk':'')+(q.offSurf/Math.max(1,q.ptsSurf)>0.15?' · ⚠ '+Math.round(100*q.offSurf/q.ptsSurf)+'% badan jalan tidak rata dengan permukaan':''));
  const zr=Math.min(...B.filter(b=>(b.roads||[]).length).map(b=>b.zt)),zf=B[0].zt;if(isFinite(zr)&&zr>zf+H0()+0.1)warn.push('⚠ Lantai RL '+f1(zf)+' s/d RL '+f1(zr)+' belum punya akses jalan — ubah arah/pola jalan, tambah Bench Break, atau naikkan RL target.');}}catch(e){console.warn(e);}}if(TP.length){const ar=roadAir(B);if(ar.n&&ar.air/ar.n>0.1)warn.push(Math.round(100*ar.air/ar.n)+'% badan jalan berada di atas topografi (menggantung di udara) — pindahkan titik masuk/arah jalan ke sisi yang masih berupa batuan.');}if(JR.length){const zj=Math.min(...B.filter(b=>isFinite(b.join)).map(b=>b.join));warn.push('Jalan staging menyambung ke jalan pit final mulai RL '+f1(zj)+' ('+JR.length+' potong string jalan final dipakai).');}if(MODE==='stage')STG=RES;else window.__setRES(RES);pitRedraw();
 const V0=volOf(RES);RES.vol=V0;const ss=slopeStat(RES),ztop=B[B.length-1].zc;let rl=0;for(const b of B)for(const rd of (b.roads||[]))if(!rd.fin)for(let i=1;i<rd.in.length;i++){const a=rd.in[i-1],c=rd.in[i];rl+=Math.hypot(c[0]-a[0],c[1]-a[1],c[2]-a[2]);}
 RES.kpi={n:B.length,vol:V0.tot,zfl:RES.zmin,ztop,rl,ss};const pO=PN().O;
 let h='<div class="kpi"><div><b>'+B.length+'</b><span>bench</span></div><div><b>'+nf(V0.tot/1000,1)+'</b><span>ribu m³ galian</span></div><div><b>'+f1(ztop-RES.zmin)+' m</b><span>kedalaman</span></div></div>';
 h+='Lantai RL '+f1(RES.zmin)+' · crest teratas RL '+f1(ztop)+(rl?' · jalan '+nf(rl)+' m':'');
 if(ss)h+='<br>Overall slope aktual: rata-rata <b>'+ss.mean.toFixed(1)+'°</b>, paling curam '+ss.max.toFixed(1)+'° '+(ss.max>pO+0.5?'<span class="bad">&gt; '+pO+'°</span>':'<span class="ok">≤ '+pO+'°</span>');
 if(RES.stage)h+=stgInfo(RES);for(const w0 of warn){const w=String(w0).replace(/^(⚠\s*)+/,'');h+=/^ℹ/.test(w)?'<br><span class="hint">'+esc(w)+'</span>':'<br><span class="warn">⚠ '+esc(w)+'</span>';}h+='<br><a href="#" id="ohw">Lihat volume per bench</a> · <a href="#" id="oxw">Ekspor</a>';
 h+=' · <a href="#" class="del" id="rdel">&#128465; Hapus hasil</a>';$('res').innerHTML=h;$('rdel').onclick=e=>{e.preventDefault();if(!confirm('Hapus hasil pit ini?'))return;if(MODE==='stage')STG=null;else window.__setRES(null);ibReset();pitRedraw();$('res').innerHTML='';stepSt('s5','',false);};$('ohw').onclick=e=>{e.preventDefault();winShow($('hw'),true);};$('oxw').onclick=e=>{e.preventDefault();winShow($('xw'),true);};stepSt('s5',B.length+' bench',true);if($('hw').style.display==='block')hwFill();if(inter)$('res').innerHTML+=' <span class="hint">(bench demi bench)</span>';else view('sw',true);}
function hwFill(){const R0=curR(),el=$('hwb');if(!R0||!R0.vol){el.innerHTML='<div class="hint">Buat pit dulu.</div>';return;}const V0=R0.vol;
 let h='<div class="kpi"><div><b>'+nf(V0.tot)+'</b><span>m³ galian total</span></div><div><b>'+nf(V0.area)+'</b><span>m² bukaan pit</span></div><div><b>'+(R0.kpi?R0.kpi.n:'–')+'</b><span>bench</span></div></div>';
 h+='<div style="max-height:340px;overflow:auto"><table class="vt"><thead><tr><th>Bench (RL)</th><th>Volume m³</th><th>Kumulatif m³</th></tr></thead><tbody>';let c=0;const rows=V0.rows.slice().reverse();for(const r of rows){c+=r.v;h+='<tr><td>'+f1(r.lo)+' – '+f1(r.hi)+'</td><td>'+nf(r.v)+'</td><td>'+nf(c)+'</td></tr>';}
 h+='<tr class="tot"><td>Total</td><td>'+nf(V0.tot)+'</td><td></td></tr></tbody></table></div><div class="hint">Volume = topografi dikurangi permukaan pit (grid '+V0.cell+' m), dibagi per interval tinggi bench dari lantai. Tanpa faktor swell.</div>';el.innerHTML=h;}
window.__setRES=r=>{RES=r;};

function H0(){return PN().H;}

/* staging atas→bawah + jalan final: pintu masuk jalan direncanakan mundur dari jalan final (opsi "menuju jalan final") */
function stgRamps(ts,CL,ramps,zt,warn){if(!CL||!ramps.length||!$('sfroad')||!$('sfroad').checked)return ramps;let pl=null;try{pl=planToFinRoad(ts,{zref:BASE.z,clamp:CL,lim:limAt,finRoads:finRoadStrings(),proj:ts.proj,zmin:zt});}catch(e){console.warn(e);}
 if(!pl)return ramps;const mk=e=>{const rm=Object.assign({},ramps[0]);rm.pt=e.slice();rm.p0=e.slice();rm.free=false;rm.straight=false;rm.dv=pl.dv;rm.dir=1;rm.toFin=pl;rm.autoLip=false;return rm;};
 /* koreksi iteratif: jalan staging di bench dalam lebih pendek kelilingnya → titik tiba bergeser. Geser pintu masuk sepanjang selisih panjang, ulangi */
 const o2={zref:BASE.z,clamp:CL,lim:limAt,finRoads:finRoadStrings(),proj:ts.proj,zmin:zt},g=RAMP().g,W=RAMP().W,hi=pl.path[0];let e=pl.entry.slice(),best=null;
 const PE=pl.P;let sh=0;const hist=[];for(let it=0;it<5;it++){const rm=mk(e);const d=genDown(ts.C,ts.z,Object.assign({},o2,{ramps:[rm].concat(ramps.slice(1))}));
  let dh=1e9,zc=NaN;for(const b of d.B)for(const r of (b.roads||[])){if(r.fin||!r.out||r.out.length!==r.in.length)continue;for(let i=0;i<r.in.length;i++){const c=[(r.in[i][0]+r.out[i][0])/2,(r.in[i][1]+r.out[i][1])/2,r.in[i][2]];const h=Math.hypot(c[0]-hi[0],c[1]-hi[1]);if(c[2]>=hi[2]-0.3&&h<dh+0.01&&(h<dh-0.5||c[2]<zc)){dh=h;zc=c[2];}}}
  const adopt=d.B.some(b=>b.fa),err=isFinite(zc)?(zc-hi[2]):99,sc=Math.abs(err)*2+(dh>2*W?dh:0)+(adopt?0:50);if(!best||sc<best.sc)best={sc,e:e.slice(),err,dh,adopt,it};
  if(Math.abs(err)<1.2&&dh<2*W&&adopt)break;/* terlalu tinggi saat tiba → jalan perlu lebih panjang: mundurkan pintu masuk (berlawanan arah turun) */
  hist.push([sh,err]);/* secant pada geseran (m sepanjang crest bench masuk) */let nsh;if(hist.length>=2){const [a1,e1]=hist[hist.length-2],[a2,e2]=hist[hist.length-1];nsh=Math.abs(e2-e1)>0.3?a2-e2*(a2-a1)/(e2-e1):a2+(isFinite(zc)?err/g:2*W);}else nsh=sh+(isFinite(zc)?err/g:2*W);
  nsh=Math.max(sh-200,Math.min(sh+200,nsh));const Rr=ringFor(PE,pl.entry);if(!Rr)break;const t=tanAt(Rr.r,Rr.c,Rr.n.s,4),dn=(pl.dv&&(t[0]*pl.dv[0]+t[1]*pl.dv[1])<0)?-1:1;sh=nsh;const A=ringAt(Rr.r,Rr.c,Rr.n.s-dn*sh).p;e=[A[0],A[1]];}
 const rm=mk(best.e);if(warn&&best.dh>2*W)warn.push('⚠ Jalan staging belum tepat tiba di jalan pit final (selisih '+f1(best.dh)+' m, beda RL '+f1(best.err)+' m).');
 if(warn)warn.push('Jalan staging direncanakan menuju ujung atas jalan pit final (RL '+f1(pl.zh)+'): pintu masuk di ('+f1(pl.entry[0])+', '+f1(pl.entry[1])+'), '+(pl.path.length-1)+' ruas.');
 return [rm].concat(ramps.slice(1));}

/* Rancang Otomatis: cari pintu masuk jalan staging yang TIBA di ujung atas jalan pit final.
 Kasar: titik tiap ±30 m sepanjang batas atas × 2 arah; halus: ±8 m di sekitar yang terbaik. Tiap uji hanya dirancang
 sampai 2 bench di bawah ujung jalan final (cepat). Nilai = jarak horizontal terdekat pusat jalan ke ujung jalan final
 + 4 × beda RL saat itu; harus juga terjadi adopsi jalan final. */
function searchFinEntry(ts,CL,ramps,zt,mode,prog){if(!CL||!ramps.length)return null;const o0={zref:BASE.z,clamp:CL,lim:limAt,finRoads:finRoadStrings(),proj:ts.proj};
 const pl=planToFinRoad(ts,Object.assign({},o0,{zmin:zt}));if(!pl)return null;const hi=pl.path[0],H=PN().H,W=RAMP().W;const zs=Math.max(isFinite(zt)?zt:-1e9,hi[2]-2*H);
 const R=ringFor(ts.C,pl.entry);if(!R)return null;const per=R.c[R.c.length-1];
 const test=(sx,dir)=>{const A=ringAt(R.r,R.c,R.n.s+sx).p;const rm=Object.assign({},ramps[0],{pt:[A[0],A[1]],p0:[A[0],A[1]],free:false,straight:false,dv:null,dir,act:false,first:true});
  const d=genDown(ts.C,ts.z,Object.assign({},o0,{ramps:[rm],zmin:zs,mode}));let best=1e9,adopt=d.B.some(b=>b.fa);
  for(const b of d.B)for(const r of (b.roads||[])){if(r.fin||!r.out||r.out.length!==r.in.length)continue;for(let i=0;i<r.in.length;i+=2){const c=[(r.in[i][0]+r.out[i][0])/2,(r.in[i][1]+r.out[i][1])/2,r.in[i][2]];const e=Math.hypot(c[0]-hi[0],c[1]-hi[1])+4*Math.abs(c[2]-hi[2]);if(e<best)best=e;}}
  const miss=(d.warn||[]).some(w=>/tidak bertemu ujung atas/.test(w));return {sx,dir,e:best+(adopt?0:200)+(miss?50:0),pt:[A[0],A[1]],adopt,miss};};
 let res=[];const step=Math.max(20,Math.min(40,per/24));let n=0;const tot=Math.ceil(per/step)*2;
 for(let sx=0;sx<per;sx+=step)for(const dir of [1,-1]){res.push(test(sx,dir));n++;if(prog)prog(n,tot);}
 res.sort((a,b)=>a.e-b.e);const b0=res[0];for(let k=-3;k<=3;k++){if(!k)continue;res.push(test(b0.sx+k*step/4,b0.dir));}res.sort((a,b)=>a.e-b.e);
 const b=res[0];return {pt:b.pt,dir:b.dir,e:b.e,adopt:b.adopt,miss:b.miss,hi,tried:res.length};}

/* ===== RL atas / RL bawah per area =====
 Wilayah tiap area = sel denah yang paling dekat ke dasar area itu (raster 2 m). Bench di atas RL atas area dipotong dari
 wilayahnya, dan volume dihitung dari min(topografi, RL atas) → volume tidak melebihi irisan RL bawah–atas yang diminta. */
function areaRegions(){const AR=areas();if(AR.length<2)return null;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;const RR=AR.map(a=>(a.PA||[]).filter(r=>cArea(r)>0).map(ringOf));
 for(const R of RR)for(const r of R)for(const p of r){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}const m=400;x0-=m;y0-=m;x1+=m;y1+=m;const c=4;
 const dist=(R,p)=>{if(R.some(r=>inPoly(p,r)))return 0;let d=1e18;for(const r of R)for(let i=0;i<r.length;i+=2){const q=r[i];d=Math.min(d,(q[0]-p[0])**2+(q[1]-p[1])**2);}return d;};
 const nx=Math.ceil((x1-x0)/c),ny=Math.ceil((y1-y0)/c),lab=new Int16Array(nx*ny);for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const p=[x0+(i+.5)*c,y0+(j+.5)*c];let b=0,bd=1e30;RR.forEach((R,k)=>{const d=dist(R,p);if(d<bd){bd=d;b=k;}});lab[j*nx+i]=b;}
 const out=AR.map(()=>[]);for(let k=0;k<AR.length;k++){const R=[];for(let j=0;j<ny;j++){let i0=-1;for(let i=0;i<=nx;i++){const ok=i<nx&&lab[j*nx+i]===k;if(ok&&i0<0)i0=i;else if(!ok&&i0>=0){R.push(toC([[x0+i0*c,y0+j*c],[x0+i*c,y0+j*c],[x0+i*c,y0+(j+1)*c],[x0+i0*c,y0+(j+1)*c]]));i0=-1;}}}out[k]=R.length?cBool(R,[],ClipperLib.ClipType.ctUnion):[];}
 return {P:out,lab,x0,y0,c,nx,ny};}
function rlTrim(B,warn){if(!BASE)return B;const AR=areas(),tops=AR.map(aTop);if(!tops.some(isFinite))return B;const REG=areaRegions();
 const cut=[];AR.forEach((a,k)=>{const t=tops[k];if(!isFinite(t))return;cut.push({t,P:REG?REG.P[k]:null,nm:(a.kind==='line'?'Urat ':'Area ')+(k+1)});});
 const out=[];for(const b of B){let cr=b.crest,to=b.toe,rd=b.roads||[];let gone=false,ch=false;for(const q of cut){if(b.zc<=q.t+1e-6)continue;if(!q.P){gone=true;break;}cr=cDiff(cr,q.P);to=cDiff(to,q.P);ch=true;}
  if(gone)continue;if(!ch){out.push(b);continue;}/* hanya bench yang benar-benar dipotong yang diubah — jalan bench lain tetap utuh */cr=cr.filter(r=>Math.abs(cArea(r))>2);to=to.filter(r=>Math.abs(cArea(r))>2);if(!cr.length&&!to.length)continue;out.push(Object.assign({},b,{crest:cr,toe:to,roads:clipRoads(rd,cOff(cr,(pB(prmAt(b.zc),b.zc).B||0)+PN().a+3))}));}
 if(out.length<B.length||cut.length)warn.push('Batas RL atas: '+cut.map(q=>q.nm+' ≤ RL '+f1(q.t)).join(', ')+' — bench di atasnya tidak dibuat, volume dihitung sampai RL atas.');return out;}
function rlCap(foot){if(!BASE)return null;const AR=areas(),tops=AR.map(aTop);if(!tops.some(isFinite))return null;if(AR.length<2){const t=tops[0];return isFinite(t)?(()=>t):null;}
 const REG=areaRegions();if(!REG)return null;return (x,y)=>{const i=Math.floor((x-REG.x0)/REG.c),j=Math.floor((y-REG.y0)/REG.c);if(i<0||j<0||i>=REG.nx||j>=REG.ny)return NaN;const t=tops[REG.lab[j*REG.nx+i]];return isFinite(t)?t:NaN;};}
