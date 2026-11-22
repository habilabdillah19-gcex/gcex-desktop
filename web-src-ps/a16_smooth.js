/* a16 — penghalus gelombang string.
   Crest / toe / lantai mewarisi gelombang kecil dari proyeksi topografi (garis potong topo, poligon di-snap ke topo) dan dari operasi poligon.
   Gelombang dengan panjang gelombang < ±3σ dihaluskan (Gaussian menurut panjang busur); yang TIDAK berubah:
   - sudut bench / takik jalan (sudut yang tetap tajam pada skala 4 m dan 8 m),
   - titik sambungan (ujung string lain: tepi jalan, garis ujung ruas) dan bagian yang berimpit dengan string lain (dinding runcing / batas area),
   - bentuk besar (pergeseran tiap titik dibatasi σ).
   Pengaman: string yang sudah dihaluskan tidak boleh menambah persilangan dengan string lain atau dirinya sendiri; bila menambah, σ diperkecil
   (½, ¼), dan bila tetap menambah, string dibiarkan seperti semula. Pengaturan: Langkah bentuk pit → "Haluskan gelombang string" (m, 0 = mati). */
function smSig(){const e=$('pss');if(window.__NOSMS)return 0;const v=e?+e.value:3;return isFinite(v)&&v>0?v:0;}
function smArc(P){const s=[0];for(let i=1;i<P.length;i++)s.push(s[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));return s;}
/* titik pada jarak busur t (P terbuka) */
function smAt(P,S,t){if(t<=0)return P[0];const n=P.length;if(t>=S[n-1])return P[n-1];let lo=0,hi=n-1;while(hi-lo>1){const m=(lo+hi)>>1;if(S[m]<=t)lo=m;else hi=m;}const d=S[hi]-S[lo]||1,u=(t-S[lo])/d;return [P[lo][0]+(P[hi][0]-P[lo][0])*u,P[lo][1]+(P[hi][1]-P[lo][1])*u];}
function smAng(a,b){const la=Math.hypot(a[0],a[1]),lb=Math.hypot(b[0],b[1]);if(la<1e-6||lb<1e-6)return 0;return Math.acos(Math.max(-1,Math.min(1,(a[0]*b[0]+a[1]*b[1])/(la*lb))))*180/Math.PI;}
/* sudut nyata: tetap tajam pada skala 4 m dan 8 m (gelombang kecil hilang pada skala 8 m) */
function smCorners(P,S,closed){const n=P.length,L=S[n-1],ang=new Float64Array(n),at=t=>{if(closed){t=((t%L)+L)%L;}return smAt(P,S,t);};
 for(let i=0;i<n;i++){const s=S[i];if(!closed&&(s<2||s>L-2))continue;const a4=smAng([P[i][0]-at(s-4)[0],P[i][1]-at(s-4)[1]],[at(s+4)[0]-P[i][0],at(s+4)[1]-P[i][1]]),a8=smAng([P[i][0]-at(s-8)[0],P[i][1]-at(s-8)[1]],[at(s+8)[0]-P[i][0],at(s+8)[1]-P[i][1]]);if(a4>40&&a8>28){const v1=[P[i][0]-at(s-4)[0],P[i][1]-at(s-4)[1]],v2=[at(s+4)[0]-P[i][0],at(s+4)[1]-P[i][1]];ang[i]=a4*((v1[0]*v2[1]-v1[1]*v2[0])>=0?1:-1);}}
 const pin=new Uint8Array(n),A=i=>Math.abs(ang[i]);for(let i=0;i<n;i++){if(!ang[i])continue;let mx=true;for(let j=i-1;j>=0&&S[i]-S[j]<=3;j--)if(A(j)>A(i)){mx=false;break;}if(mx)for(let j=i+1;j<n&&S[j]-S[i]<=3;j++)if(A(j)>=A(i)){mx=false;break;}if(mx)pin[i]=1;}
 /* tangga kecil (dua sudut berlawanan arah berdekatan, arah garis sebelum & sesudah tetap) = gelombang, bukan sudut bench */
 const ids=[];for(let i=0;i<n;i++)if(pin[i])ids.push(i);for(let q=0;q+1<ids.length;q++){const i=ids[q],j=ids[q+1];if(S[j]-S[i]>8||Math.sign(ang[i])===Math.sign(ang[j]))continue;const a0=at(S[i]-6),b0=at(S[j]+6),d=smAng([P[i][0]-a0[0],P[i][1]-a0[1]],[b0[0]-P[j][0],b0[1]-P[j][1]]);if(d<20){pin[i]=0;pin[j]=0;q++;}}
 return pin;}
/* Gaussian satu ruas terbuka P[a..b] (pantulan ganjil di kedua ujung), lalu koreksi linier supaya ujung berpindah tepat ke sasarannya (TA/TB) */
function smPiece(P,S,a,b,sig,out,TA,TB){const w=3*sig,A=P[a],B=P[b],sa=S[a],sb=S[b];let j0=a;
 for(let i=a+1;i<b;i++){const si=S[i];let wx=0,wy=0,ws=0;const add=(x,y,d,ds)=>{const g=Math.exp(-0.5*(d/sig)*(d/sig))*ds;wx+=g*x;wy+=g*y;ws+=g;};
  while(j0<b&&S[j0]<si-w)j0++;for(let j=Math.max(a,j0-1);j<=b;j++){const d=S[j]-si;if(d>w)break;const ds=((j<b?S[j+1]:S[j])-(j>a?S[j-1]:S[j]))/2||0.5;add(P[j][0],P[j][1],d,ds);}
  /* pantulan ganjil terhadap ujung a dan b */if(si-sa<w)for(let j=a+1;j<=b;j++){const d=(sa-(S[j]-sa))-si;if(d<-w)break;add(2*A[0]-P[j][0],2*A[1]-P[j][1],d,((j<b?S[j+1]:S[j])-S[j-1])/2||0.5);}
  if(sb-si<w)for(let j=b-1;j>=a;j--){const d=(sb+(sb-S[j]))-si;if(d>w)break;add(2*B[0]-P[j][0],2*B[1]-P[j][1],d,(S[j+1]-(j>a?S[j-1]:S[j]))/2||0.5);}
  if(ws>0){const u=(si-sa)/((sb-sa)||1),cx=(1-u)*(TA[0]-A[0])+u*(TB[0]-B[0]),cy=(1-u)*(TA[1]-A[1])+u*(TB[1]-B[1]);out[i]=[wx/ws+cx,wy/ws+cy];}}}
/* menghaluskan satu string; pinT(x,y) → null (bebas) atau [x,y] sasaran titik tetap. Hasil {Z (setelah RDP), P (titik rapat asal), R (posisi baru)} */
function smLine(pts,sig,pinT,closed,noCor){if(pts.length<4)return null;let P=densify(pts,1).map(p=>p.slice());if(closed&&Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1])<1e-6)P.pop();const n=P.length;if(n<8)return null;
  if(closed)P.push(P[0].slice());const S=smArc(P),m=P.length;const cor=noCor?new Uint8Array(m):smCorners(P,S,closed),tg=new Array(m).fill(null);
 for(let i=0;i<m;i++){if(cor[i])tg[i]=[P[i][0],P[i][1]];else if(pinT){const t=pinT(P[i][0],P[i][1]);if(t)tg[i]=t;}}
 if(!closed){if(!tg[0])tg[0]=[P[0][0],P[0][1]];if(!tg[m-1])tg[m-1]=[P[m-1][0],P[m-1][1]];}else tg[m-1]=tg[0];
 const out=P.map((p,i)=>tg[i]?tg[i].slice():[p[0],p[1]]);let idx=[];for(let i=0;i<m;i++)if(tg[i])idx.push(i);
 if(closed&&!idx.length){/* cincin tanpa titik tetap: Gaussian melingkar */const L=S[m-1],w=3*sig;for(let i=0;i<m-1;i++){let wx=0,wy=0,ws=0;for(let k=-1;k<=1;k++)for(let j=0;j<m-1;j++){const d=S[j]+k*L-S[i];if(Math.abs(d)>w)continue;const ds=((S[j+1]-S[Math.max(0,j-1)])/2)||0.5,g=Math.exp(-0.5*(d/sig)*(d/sig))*ds;wx+=g*P[j][0];wy+=g*P[j][1];ws+=g;}if(ws>0)out[i]=[wx/ws,wy/ws];}out[m-1]=out[0].slice();}
 else{if(closed){/* putar supaya mulai di titik tetap */const r=idx[0],P2=P.slice(r,m-1).concat(P.slice(0,r+1)),S2=smArc(P2),t2=[];for(let i=0;i<P2.length;i++)t2.push(tg[(i+r)%(m-1)]);const o2=P2.map((p,i)=>t2[i]?t2[i].slice():[p[0],p[1]]);let a=0;for(let i=1;i<P2.length;i++)if(t2[i]){if(i-a>2)smPiece(P2,S2,a,i,sig,o2,t2[a],t2[i]);a=i;}
   for(let i=0;i<P2.length;i++)out[(i+r)%(m-1)]=o2[i];out[m-1]=out[0].slice();}
  else{let a=0;for(let i=1;i<m;i++)if(tg[i]){if(i-a>2)smPiece(P,S,a,i,sig,out,tg[a],tg[i]);a=i;}}}
 /* batas pergeseran = σ (titik bersasaran tidak dibatasi) */let moved=0;const R=[];for(let i=0;i<m;i++){let dx=out[i][0]-P[i][0],dy=out[i][1]-P[i][1];const d=Math.hypot(dx,dy);if(!tg[i]&&d>sig){dx*=sig/d;dy*=sig/d;}moved=Math.max(moved,Math.hypot(dx,dy));R.push([P[i][0]+dx,P[i][1]+dy,P[i][2],tg[i]?1:0]);}
 if(moved<0.05)return null;
 /* buang titik segaris (RDP 5 cm), titik tetap dipertahankan */const keep=new Uint8Array(m);keep[0]=keep[m-1]=1;for(let i=0;i<m;i++)if(R[i][3]&&cor[i])keep[i]=1;
 const rdp=(a,b)=>{if(b-a<2)return;const ax=R[a][0],ay=R[a][1],bx=R[b][0],by=R[b][1],L=Math.hypot(bx-ax,by-ay)||1e-9;let dm=0,k=-1;for(let i=a+1;i<b;i++){const d=Math.abs((bx-ax)*(ay-R[i][1])-(ax-R[i][0])*(by-ay))/L;if(d>dm){dm=d;k=i;}}if(dm>0.03){keep[k]=1;rdp(a,k);rdp(k,b);}};
 let a=0;for(let i=1;i<m;i++)if(keep[i]){rdp(a,i);a=i;}const Z=[];for(let i=0;i<m;i++)if(keep[i])Z.push([R[i][0],R[i][1],R[i][2]]);if(closed){Z[Z.length-1]=Z[0].slice();}return {Z,P,R};}
/* indeks ruas semua string (grid 4 m) untuk uji silang & uji berimpit */
function smIndex(S){const c=4,M=new Map(),key=(i,j)=>i+'_'+j;S.forEach((s,k)=>{const P=s.pts;for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i],i0=Math.floor(Math.min(a[0],b[0])/c),i1=Math.floor(Math.max(a[0],b[0])/c),j0=Math.floor(Math.min(a[1],b[1])/c),j1=Math.floor(Math.max(a[1],b[1])/c);for(let x=i0;x<=i1;x++)for(let y=j0;y<=j1;y++){const kk=key(x,y);let L=M.get(kk);if(!L)M.set(kk,L=[]);L.push([k,i]);}}});
 return {c,M,near(x,y,r){const o=[],i0=Math.floor((x-r)/c),i1=Math.floor((x+r)/c),j0=Math.floor((y-r)/c),j1=Math.floor((y+r)/c);for(let i=i0;i<=i1;i++)for(let j=j0;j<=j1;j++){const L=M.get(key(i,j));if(L)for(const e of L)o.push(e);}return o;}};}
function smSegX(a,b,c,d,strict){const r0=b[0]-a[0],r1=b[1]-a[1],q0=d[0]-c[0],q1=d[1]-c[1],den=r0*q1-r1*q0;if(Math.abs(den)<1e-12)return false;const t=((c[0]-a[0])*q1-(c[1]-a[1])*q0)/den,u=((c[0]-a[0])*r1-(c[1]-a[1])*r0)/den;if(!(t>1e-6&&t<1-1e-6&&u>1e-6&&u<1-1e-6))return false;if(strict)return true;/* garis (hampir) berimpit yang berselang-seling bukan silang nyata: sudut < 20° dan jarak ujung ruas pendek ke ruas lain < 0,5 m */const la=Math.hypot(r0,r1),lq=Math.hypot(q0,q1),sn=Math.abs(den)/(la*lq||1);if(sn<0.34){const [p1,p2,s1,s2]=la<lq?[a,b,c,d]:[c,d,a,b];const ld=p=>Math.abs((s2[0]-s1[0])*(s1[1]-p[1])-(s1[0]-p[0])*(s2[1]-s1[1]))/(Math.hypot(s2[0]-s1[0],s2[1]-s1[1])||1);if(ld(p1)<0.5&&ld(p2)<0.5)return false;}return true;}
function smDist(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],L=dx*dx+dy*dy;let t=L>0?((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L:0;t=Math.max(0,Math.min(1,t));return Math.hypot(a[0]+dx*t-p[0],a[1]+dy*t-p[1]);}
/* jumlah persilangan string P (calon pengganti S[k]) dengan string lain + dirinya sendiri */
function smCross(P,k,S,IX,flt,vis,L){let n=0;const at=(a,b,c,d)=>{const r0=b[0]-a[0],r1=b[1]-a[1],q0=d[0]-c[0],q1=d[1]-c[1],den=r0*q1-r1*q0,t=((c[0]-a[0])*q1-(c[1]-a[1])*q0)/den;return [a[0]+r0*t,a[1]+r1*t];};const seen=new Set();for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i],mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2,r=Math.hypot(b[0]-a[0],b[1]-a[1])/2+0.01;
  for(const [k2,j] of IX.near(mx,my,r)){if(k2===k||(flt&&!flt(k2)))continue;const id=i+'|'+k2+'|'+j;if(seen.has(id))continue;seen.add(id);const Q=S[k2].pts;/* longgar (abaikan selang-seling garis berimpit) hanya antar-cincin pada RL sama */const s2=S[k2],sk=S[k]||{},loose=sk.t&&s2.pts&&Math.abs((s2.z||0)-(sk.z||0))<0.01&&/^(crest|toe|floor)$/.test(s2.t)&&/^(crest|toe|floor)$/.test(sk.t);if(smSegX(a,b,Q[j-1],Q[j],!loose)){if(vis&&!vis(k2,a,b,Q[j-1],Q[j]))continue;n++;if(L)L.push([k2,...at(a,b,Q[j-1],Q[j])]);}}}
 /* silang diri (grid lokal) */const c=4,G=new Map();for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i],i0=Math.floor(Math.min(a[0],b[0])/c),i1=Math.floor(Math.max(a[0],b[0])/c),j0=Math.floor(Math.min(a[1],b[1])/c),j1=Math.floor(Math.max(a[1],b[1])/c);for(let x=i0;x<=i1;x++)for(let y=j0;y<=j1;y++){const kk=x+'_'+y;let L=G.get(kk);if(!L)G.set(kk,L=[]);for(const j of L)if(Math.abs(j-i)>1&&!(i===P.length-1&&j===1)&&smSegX(P[j-1],P[j],a,b)){n++;if(L)L.push([k,...at(P[j-1],P[j],a,b)]);}L.push(i);}}return n;}
function strSmooth(S0,EX){const sig=smSig();if(!sig||!S0||!S0.length)return S0;const t0=performance.now();/* EX: string lain yang ikut tampil (jalan final pinjaman) — penghalang & titik sambung, tidak diubah */const S=EX&&EX.length?S0.concat(EX):S0;
 const isRing=s=>(s.t==='crest'||s.t==='toe'||s.t==='floor')&&s.pts.length>=5,zk=z=>Math.round(z*100);
 /* titik sambungan: ujung string terbuka */const J=[];for(const s of S){const P=s.pts;if(P.length<2)continue;if(Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1])>1e-6){J.push(P[0],P[P.length-1]);}}
 const JI=smIndex(J.map(p=>({pts:[p,p]})));let IX=smIndex(S);let nS=0,nK=0;
 /* kelompok per RL: cincin pada RL sama sering berimpit sebagian (crest bench bawah = toe bench atas di dinding tanpa berm) → digeser bersama */
 const isOpen=s=>s.pts.length>1&&Math.hypot(s.pts[0][0]-s.pts[s.pts.length-1][0],s.pts[0][1]-s.pts[s.pts.length-1][1])>1e-6;
 const grp=new Map();S.forEach((s,k)=>{if(!isRing(s))return;const g=zk(s.z);if(!grp.has(g))grp.set(g,[]);grp.get(g).push(k);});
 for(const [g,ks] of grp){/* pengaman dihitung terhadap string RL sama, jalan / string terbuka, dan diri sendiri (cincin RL lain memang bisa bersilang di denah di atas topo) */const flt=null;/* cincin RL lain: silang dihitung hanya bila titik silang tampak (di bawah topografi untuk kedua RL), sama seperti tolok ukur kerapian */
  const vis=(k2,a,b,c,d)=>{const s2=S[k2];if(zk(s2.z)===g||isOpen(s2)||!isRing(s2))return true;if(!TP.length)return true;const r0=b[0]-a[0],r1=b[1]-a[1],q0=d[0]-c[0],q1=d[1]-c[1],den=r0*q1-r1*q0,t=((c[0]-a[0])*q1-(c[1]-a[1])*q0)/den,x=a[0]+r0*t,y=a[1]+r1*t,tz=topoZ(x,y);if(!isFinite(tz))return false;return g/100<=tz+0.05&&s2.z<=tz+0.05;};const L0=[];const c0=ks.reduce((t,k)=>t+smCross(S[k].pts,k,S,IX,flt,vis,L0),0);let done=false;
  for(const f of [1,0.5,0.25]){const NEW=new Map(),PR=[];/* titik rapat asal → posisi baru, cincin yang sudah diproses di kelompok ini */
   const PI={c:1,M:new Map(),add(p,q){const k=Math.floor(p[0])+'_'+Math.floor(p[1]);let L=this.M.get(k);if(!L)this.M.set(k,L=[]);L.push([p,q]);},get(x,y,r){let b=null,bd=r;/* hasil: pergeseran titik asal terdekat */for(let i=Math.floor(x-r);i<=Math.floor(x+r);i++)for(let j=Math.floor(y-r);j<=Math.floor(y+r);j++){const L=this.M.get(i+'_'+j);if(L)for(const [p,q] of L){const d=Math.hypot(p[0]-x,p[1]-y);if(d<bd){bd=d;b=[q[0]-p[0],q[1]-p[1]];}}}return b;}};
   for(const k of ks){const s=S[k],P=s.pts,closed=Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1])<1e-6;
    const pinT=(x,y)=>{for(const [k2] of JI.near(x,y,0.4)){const q=J[k2];if(Math.hypot(q[0]-x,q[1]-y)<0.4)return [x,y];}
     /* dekat cincin RL sama yang sudah diproses (berimpit / sejajar ≤ 1,5 m) → ikut pergeseran yang sama supaya tidak bersilang */const q=PI.get(x,y,1.5);if(q)return [x+q[0],y+q[1]];
     /* dekat tepi jalan / string terbuka (≤ 1 m) atau berimpit dengan cincin RL lain (≤ 0,15 m) → tetap */for(const [k2,j] of IX.near(x,y,1.0)){if(k2===k||ks.includes(k2))continue;const Q=S[k2].pts,r=isOpen(S[k2])?1.0:0.15;if(smDist([x,y],Q[j-1],Q[j])<r)return [x,y];}return null;};
    const r=smLine(P,sig*f,pinT,closed);if(!r)continue;NEW.set(k,r.Z);for(let i=0;i<r.P.length;i++)PI.add(r.P[i],r.R[i]);}
   if(!NEW.size){done=true;break;}
   /* pengaman: persilangan kelompok (dengan versi baru anggota kelompok) tidak boleh bertambah */
   const S2=S.map((s,k)=>NEW.has(k)?{t:s.t,z:s.z,pts:NEW.get(k)}:s),IX2=smIndex(S2);const L1=[];const c1=ks.reduce((t,k)=>t+smCross(S2[k].pts,k,S2,IX2,flt,vis,L1),0);/* tiap silang baru harus dekat (≤ 3 m) silang lama dengan string yang sama — silang tidak boleh berpindah tempat */const fresh=L1.filter(q=>!L0.some(o=>o[0]===q[0]&&Math.hypot(o[1]-q[1],o[2]-q[2])<=3)).length;
   if(c1<=c0&&!fresh){for(const [k,Z] of NEW){S[k].pts0=S[k].pts;S[k].pts=Z;S[k].sm=1;nS++;}IX=IX2;done=true;break;}}
  if(!done)nK+=ks.length;}
 window.__PS3=window.__PS3||{};for(const s of S0)s.bs=1;window.__PS3.smst={sig,smoothed:nS,kept:nK,ms:Math.round(performance.now()-t0)};return S0;}
/* pasang pada pembuat string bench (pit final, staging, edit) */
{const _bs=benchStrings;benchStrings=function(B,floor){const EX=window.__SMX;window.__SMX=null;return strSmooth(_bs(B,floor),EX);};}
/* jalan final pinjaman (staging) dibuat tepat sebelum string bench → diingat sebagai penghalang */
{const _jr=joinRoads;joinRoads=function(B){const r=_jr(B);window.__SMX=r;return r;};}
/* jaring pengaman akhir: tolok ukur kerapian (menggantung / silang / tidak dipatuhi) dihitung untuk string asli dan string halus.
   Bila yang halus lebih buruk, string halus di sekitar titik masalah dikembalikan ke asal (berulang), dan bila tetap lebih buruk semuanya dikembalikan. */
function smVerify(){const R=curR(),C=window.__PS3&&window.__PS3.conn;if(!R||!R.S||!C)return;const sm=R.S.filter(s=>s.sm&&s.pts0);if(!sm.length)return;
 /* permukaan & tapak dari string asli (tolok ukur memakai keduanya) */let tinO=R.tin,footO=R.foot;try{const SO=R.S.filter(s=>s.bs).map(s=>Object.assign({},s,{pts:s.pts0||s.pts}));footO=footOf(SO);tinO=surfOf(SO,footO,0,BASE&&BASE.mode==='topo');}catch(e){console.warn(e);}
 const tinN=R.tin,footN=R.foot;const swap=on=>{for(const s of sm){if(on){s._n=s.pts;s.pts=s.pts0;}else s.pts=s._n;}R.tin=on?tinO:tinN;R.foot=on?footO:footN;};swap(true);const c0=C();swap(false);if(!c0)return;let c1=C();if(!c1)return;
 const worse=c=>c.dang>c0.dang||c.crossDz>c0.crossDz||c.noReason>c0.noReason;let back=0;
 for(let it=0;it<4&&worse(c1);it++){const L=[].concat((c1.XZ||[]).map(q=>[q[0],q[1]]),(c1.NR||[]).map(q=>[q[0],q[1]]));let n=0;for(const s of sm){if(!s.sm)continue;if(L.some(q=>s.pts.some(p=>Math.hypot(p[0]-q[0],p[1]-q[1])<4))){s.pts=s.pts0;s.sm=0;n++;}}back+=n;if(!n)break;try{const SC=R.S.filter(s=>s.bs);R.foot=footOf(SC);R.tin=surfOf(SC,R.foot,0,BASE&&BASE.mode==='topo');}catch(e){}c1=C();}
 if(worse(c1)){for(const s of sm)if(s.sm){s.pts=s.pts0;s.sm=0;back++;}R.tin=tinO;R.foot=footO;c1=C();}
 if(window.__PS3.smst){window.__PS3.smst.c0=[c0.dang,c0.crossDz,c0.noReason];window.__PS3.smst.c1=[c1.dang,c1.crossDz,c1.noReason];}if(back){try{pitRedraw();}catch(_){}if(window.__PS3.smst)window.__PS3.smst.back=back;}window.__PS3.lastC=c1;}
{const _sr=showResult;showResult=function(){const r=_sr.apply(this,arguments);try{smVerify();}catch(e){console.warn(e);}return r;};}
/* garis potong topo: dari raster 1 m (bertangga) → dihaluskan lalu diproyeksikan ulang ke topografi */
{const _do=dayOf;dayOf=function(R0){const D=_do(R0);const sig=smSig();if(!sig)return D;for(const s of D){const r=smLine(s.pts,Math.max(2,sig),null,true,true);if(r)s.pts=densify(r.Z,2).map(p=>{const t=topoZ(p[0],p[1]);return [p[0],p[1],isFinite(t)?+t.toFixed(3):p[2]];});}return D;};}
/* jalan luar: garis crest potongan / kaki timbunan mengikuti tanah → dihaluskan (ujung tetap), z diproyeksikan ulang ke topografi */
{const _xb=xrBuild1;xrBuild1=function(o){const r=_xb(o);const sig=smSig();if(sig)for(const s of r.strs){if(s.t!=='xcut'&&s.t!=='xfill')continue;const r_=smLine(s.pts,Math.max(6,2*sig),null,false,true);/* garis daylight mengikuti tanah → skala lebih besar */if(r_)s.pts=densify(r_.Z,1).map(p=>{const t=topoZ(p[0],p[1]);return [p[0],p[1],isFinite(t)?t:p[2]];});}return r;};}
window.__PS3=window.__PS3||{};window.__PS3.sm={line:smLine,all:strSmooth};
