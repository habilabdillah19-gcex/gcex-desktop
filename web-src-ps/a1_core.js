'use strict';
let STG=null,FIN=null,RES=null,ED=null,CURM=null,BASE=null,RPK=null,RSTART=null,DG=null;
/* ================= Pit Studio · inti ================= */
const $=id=>document.getElementById(id),esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])),f1=v=>(+v).toFixed(1),nf=(v,d=0)=>(+v).toLocaleString('id-ID',{minimumFractionDigits:d,maximumFractionDigits:d});
let O=[0,0,0],OSET=false;function setO(p){if(OSET||!p)return;O=[Math.round(p[0]),Math.round(p[1]),Math.round(p[2])];OSET=true;}
const cv=$('cv'),R=new THREE.WebGLRenderer({antialias:true,alpha:true});R.setClearColor(0x000000,0);R.setPixelRatio(Math.min(devicePixelRatio,2));cv.appendChild(R.domElement);
const S=new THREE.Scene();S.background=null;
const C=new THREE.PerspectiveCamera(45,1,0.5,30000);C.position.set(-300,300,300);
const CT=new THREE.OrbitControls(C,R.domElement);CT.enableDamping=true;CT.dampingFactor=0.12;CT.screenSpacePanning=true;
S.add(new THREE.HemisphereLight(0xffffff,0x5d6b7c,0.72));const DL=new THREE.DirectionalLight(0xffffff,0.7);DL.position.set(-400,600,250);S.add(DL);const DL2=new THREE.DirectionalLight(0xffffff,0.22);DL2.position.set(300,200,-300);S.add(DL2);
const W=new THREE.Group();S.add(W);
const G={};for(const k of ['topo','pit','str','ref','fin','edit','tmp','lab'])W.add(G[k]=new THREE.Group());
function V(E,N,Z){return new THREE.Vector3(E-O[0],Z-O[2],-(N-O[1]));}
function rs(){const w=cv.clientWidth,h=cv.clientHeight;R.setSize(w,h);C.aspect=w/h;C.updateProjectionMatrix();}addEventListener("resize",rs);rs();try{new ResizeObserver(()=>rs()).observe(cv);}catch(_){}
(function loop(){requestAnimationFrame(loop);CT.update();R.render(S,C);})();
function clr(g){while(g.children.length){const o=g.children.pop();o.traverse(q=>{if(q.geometry)q.geometry.dispose();if(q.material){if(q.material.map)q.material.map.dispose();q.material.dispose();}});}}
function dot(c){const cn=document.createElement('canvas');cn.width=cn.height=64;const x=cn.getContext('2d');x.beginPath();x.arc(32,32,26,0,7);x.fillStyle=c;x.fill();x.lineWidth=6;x.strokeStyle='#1b2a4e';x.stroke();return new THREE.CanvasTexture(cn);}
const TX={w:dot('#ffffff'),y:dot('#fab005'),g:dot('#12b886'),b:dot('#1f6feb')};
function sprite(t,col,sz,pos){const cn=document.createElement('canvas'),x=cn.getContext('2d');x.font='600 26px Inter,Arial';const w=Math.ceil(x.measureText(t).width)+12;cn.width=w;cn.height=34;x.font='600 26px Inter,Arial';/* latar transparan: teks dengan lingkar putih tipis supaya tetap terbaca di atas topografi / blok (24 Nov) */x.lineJoin='round';x.lineWidth=6;x.strokeStyle='rgba(255,255,255,.72)';x.strokeText(t,6,26);x.fillStyle=col;x.fillText(t,6,26);
 const s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(cn),sizeAttenuation:false,depthTest:false,transparent:true}));s.scale.set(sz*w/34,sz,1);s.userData.lb=[sz*w/34,sz];s.center.set(0,0);s.position.copy(pos);s.renderOrder=8;try{LBLS.add(s);}catch(_){}return s;}
const LBLS=new Set();
function lineObj(pts,col,closed,opts){const p=[];const n=pts.length;for(let i=0;i<n-(closed?0:1);i++){const a=pts[i],b=pts[(i+1)%n];const A=V(a[0],a[1],a[2]),B=V(b[0],b[1],b[2]);p.push(A.x,A.y,A.z,B.x,B.y,B.z);}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));return new THREE.LineSegments(g,new THREE.LineBasicMaterial(Object.assign({color:col},opts||{})));}
function dl(data,nm,type){const b=data instanceof Blob?data:new Blob([typeof data==='string'&&/csv/.test(type||'')?'﻿'+data:data],{type:type||'text/plain'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=nm;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},2000);}
function today(){const d=new Date(),p=x=>String(x).padStart(2,'0');return d.getFullYear()+p(d.getMonth()+1)+p(d.getDate());}

/* ---------- baca .str (teks / biner) & .dxf ---------- */
function topoParse(txt,nm){const L=[];let cur=[];
 if(/\.dxf$/i.test(nm)||/^\s*0\s*[\r\n]+\s*SECTION/i.test(txt)){const t=txt.split(/\r?\n/).map(s=>s.trim());let ent='',el=0,pt=null,inV=false;const flush=()=>{if(cur.length)L.push(cur);cur=[];};
  for(let i=0;i+1<t.length;i+=2){const c=t[i],v=t[i+1];
   if(c==='0'){if(pt){cur.push(pt);pt=null;}if(v==='LWPOLYLINE'||v==='POLYLINE'||v==='LINE'||v==='POINT'){flush();ent=v;el=0;inV=false;}else if(v==='VERTEX'){inV=true;}else if(v==='SEQEND'||ent==='LWPOLYLINE'||ent==='LINE'||ent==='POINT'){if(ent!=='POLYLINE'||v==='SEQEND'){flush();ent=v==='SEQEND'?'':ent==='POLYLINE'?ent:'';}}continue;}
   if(!ent)continue;if(c==='38')el=+v;/* kepala POLYLINE (10/20/30) hanya titik semu + elevasi, bukan vertex */if(ent==='POLYLINE'&&!inV){if(c==='30')el=+v||0;continue;}if(c==='10'||c==='11'){if(pt)cur.push(pt);pt=[+v,0,el];}if((c==='20'||c==='21')&&pt)pt[1]=+v;if((c==='30'||c==='31')&&pt)pt[2]=(+v)||el;}
  if(pt)cur.push(pt);flush();}
 else{txt.split(/\r?\n/).slice(2).forEach(s=>{const f=s.split(',');if(f.length<4)return;const id=+f[0];if(!id){if(cur.length)L.push(cur);cur=[];return;}const y=+f[1],x=+f[2],z=+f[3];if(isFinite(x)&&isFinite(y)&&isFinite(z))cur.push([x,y,z]);});if(cur.length)L.push(cur);}
 return L;}
function topoBin(buf){const u=new Uint8Array(buf);let nl=0,h=0;for(;h<u.length&&nl<2;h++)if(u[h]===10)nl++;if(nl<2)return null;
 let z=0;for(let i=h;i<Math.min(u.length,h+400);i++)if(u[i]===0)z++;if(z<20)return null;const dv=new DataView(buf);
 const rec=(p,le)=>{if(p+29>u.length)return null;const sn=dv.getInt32(p,le);if(sn<0||sn>1e7)return null;const v=[dv.getFloat64(p+4,le),dv.getFloat64(p+12,le),dv.getFloat64(p+20,le)];
  for(const q of v)if(!isFinite(q)||Math.abs(q)>1e9||(q!==0&&Math.abs(q)<1e-6))return null;if(sn>0&&v[0]===0&&v[1]===0)return null;let e=p+28;const lim=Math.min(u.length,p+28+1024);while(e<lim&&u[e]!==0)e++;if(e>=lim)return null;return {sn,v,n:e-p+1};};
 let best=null;for(const le of [false,true])for(let s=h;s<h+16;s++){let p=s,n=0;while(n<3000){const r=rec(p,le);if(!r)break;n++;p+=r.n;}if(!best||n>best.n)best={s,le,n};}
 if(!best||best.n<2)throw new Error('format .str biner tidak dikenali');
 const L=[];let cur=[],p=best.s;for(;;){const r=rec(p,best.le);if(!r)break;p+=r.n;if(r.sn===0){if(cur.length)L.push(cur);cur=[];}else cur.push([r.v[1],r.v[0],r.v[2]]);}
 if(cur.length)L.push(cur);return L;}
function strRead(buf,nm){return topoBin(buf)||topoParse(new TextDecoder('utf-8').decode(buf),nm);}
async function readFileL(f){const L=strRead(await f.arrayBuffer(),f.name).map(l=>l.filter(p=>p.every(isFinite))).filter(l=>l.length);if(!L.length)throw new Error('tidak ada string berkoordinat');return L;}

/* ---------- TIN & grid ---------- */
function tinFrom(L,maxE,brk){const key=new Map(),X=[],Y=[],Z=[],CE=[];for(const l of L){let pi=-1;for(const q of l){const k=Math.round(q[0]*100)+'_'+Math.round(q[1]*100);let i=key.get(k);if(i===undefined){i=X.length;key.set(k,i);X.push(q[0]);Y.push(q[1]);Z.push(q[2]);}if(pi>=0&&pi!==i)CE.push(pi,i);pi=i;}}
 const n=X.length;if(n<3)throw new Error('titik terlalu sedikit');const c=new Float64Array(n*2);for(let i=0;i<n;i++){c[i*2]=X[i]-O[0];c[i*2+1]=Y[i]-O[1];}
 const DL=new Delaunator(c);/* garis patah hanya untuk permukaan pit (surfOf); topografi & pit final tetap Delaunay biasa agar RL topo tidak berubah */if(brk&&!window.__NOCDT)try{tinConstrain(DL,c,CE);}catch(e){console.warn('cdt',e);}const T0=DL.triangles,T=[];for(let t=0;t<T0.length;t+=3){if(maxE>0){let m=0;for(const [a,b] of [[T0[t],T0[t+1]],[T0[t+1],T0[t+2]],[T0[t+2],T0[t]]])m=Math.max(m,Math.hypot(X[a]-X[b],Y[a]-Y[b]));if(m>maxE)continue;}T.push(T0[t],T0[t+1],T0[t+2]);}
 let z0=1e9,z1=-1e9;for(const z of Z){if(z<z0)z0=z;if(z>z1)z1=z;}return {X,Y,Z,T,z0,z1};}
/* string sebagai garis patah (breakline): tiap ruas string dipaksa menjadi sisi segitiga dengan membalik sisi yang memotongnya.
 Tanpa ini Delaunay bebas menghubungkan titik lintas string (mis. melompati jalan di sambungan jalan–bench) → permukaan tampak pecah. */
function tinConstrain(D,c,CE){const tri=D.triangles,he=D.halfedges,n=c.length/2,nx=e=>e%3===2?e-2:e+1,pv=e=>e%3===0?e+2:e-1,ine=new Int32Array(n).fill(-1);
 for(let e=0;e<tri.length;e++){const p=tri[nx(e)];if(he[e]===-1||ine[p]===-1)ine[p]=e;}
 const or=(a,b,p)=>(c[b*2]-c[a*2])*(c[p*2+1]-c[a*2+1])-(c[b*2+1]-c[a*2+1])*(c[p*2]-c[a*2]);
 const cross=(a,b,u,v)=>{const o1=or(a,b,u),o2=or(a,b,v),o3=or(u,v,a),o4=or(u,v,b);return ((o1>0&&o2<0)||(o1<0&&o2>0))&&((o3>0&&o4<0)||(o3<0&&o4>0));};
 const around=(p,cb)=>{const st=ine[p];if(st<0)return -1;let e=st,r,g=0;do{r=cb(e);if(r!==undefined)return r;e=he[nx(e)];}while(e!==-1&&e!==st&&++g<500);if(e===-1){e=st;g=0;while(++g<500){const o=he[e];if(o===-1)break;e=pv(o);if(e===st)break;r=cb(e);if(r!==undefined)return r;}}return -1;};
 const find=(u,v)=>around(u,e=>{if(tri[pv(e)]===v)return nx(e);if(tri[e]===v&&he[e]!==-1)return he[e];});
 const link=(a,b)=>{he[a]=b;if(b!==-1)he[b]=a;},fix=t=>{for(let e=t;e<t+3;e++){const p=tri[nx(e)];if(he[e]===-1||ine[p]===-1||tri[nx(ine[p])]!==p||he[ine[p]]!==-1)ine[p]=e;}};
 const flip=a=>{const b=he[a],a0=a-a%3,ar=a0+(a+2)%3,b0=b-b%3,bl=b0+(b+2)%3,p0=tri[ar],p1=tri[bl];tri[a]=p1;tri[b]=p0;const hbl=he[bl];link(a,hbl);link(b,he[ar]);link(ar,bl);for(const q of [tri[a0],tri[a0+1],tri[a0+2],tri[b0],tri[b0+1],tri[b0+2]])ine[q]=-1;fix(a0);fix(b0);return [p0,p1];};
 const DB=window.__CDTDBG,cnt=k=>{if(DB)DB[k]=(DB[k]||0)+1;};const enforce=(A,B,dep)=>{if(A===B)return;if(dep>8){cnt('dalam');return;}if(find(A,B)>=0)return;
  /* sisi pertama yang dipotong ruas A→B, atau titik yang tepat berada di garis */let e0=-1,mid=-1;around(A,e=>{const x=tri[e],y=tri[pv(e)];if(x===B||y===B){e0=-2;return 1;}for(const w of [x,y]){if(Math.abs(or(A,B,w))<1e-7){const d=(c[w*2]-c[A*2])*(c[B*2]-c[A*2])+(c[w*2+1]-c[A*2+1])*(c[B*2+1]-c[A*2+1]),l2=(c[B*2]-c[A*2])**2+(c[B*2+1]-c[A*2+1])**2;if(d>0&&d<l2){mid=w;return 1;}}}if(cross(A,B,y,x)){e0=pv(e);return 1;}});
  if(e0===-2)return;if(mid>=0){enforce(A,mid,dep+1);enforce(mid,B,dep+1);return;}if(e0<0){cnt('tanpaSisiAwal');return;}
  const Q=[];let e=e0,g=0;while(++g<4000){Q.push([tri[e],tri[nx(e)]]);const o=he[e];if(o===-1){cnt('tepiLuar');return;}const w=tri[pv(o)];if(w===B)break;const s=or(A,B,w);if(Math.abs(s)<1e-7){/* garis melewati titik w: pecah di w */enforce(A,w,dep+1);enforce(w,B,dep+1);return;}/* o: v→u; sisi berikut: u→w = nx(o), w→v = pv(o) */const su=or(A,B,tri[nx(o)]);e=(su>0)===(s>0)?pv(o):nx(o);}
  let it=0;const lim=Q.length*60+60;while(Q.length&&++it<lim){const [u,v]=Q.shift();const h=find(u,v);if(h<0)continue;const b=he[h];if(b===-1)continue;const p0=tri[pv(h)],p1=tri[pv(b)];if(!cross(p0,p1,u,v)){Q.push([u,v]);continue;}flip(h);if(p0!==A&&p0!==B&&p1!==A&&p1!==B&&cross(A,B,p0,p1))Q.push([p0,p1]);}if(Q.length)cnt('batasPutaran');else if(find(A,B)<0)cnt('gagalLain');else cnt('ok');};
 for(let i=0;i<CE.length;i+=2)enforce(CE[i],CE[i+1],0);}
function gridOf(tin,cellWanted){const {X,Y,Z,T}=tin;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(let i=0;i<X.length;i++){if(X[i]<x0)x0=X[i];if(X[i]>x1)x1=X[i];if(Y[i]<y0)y0=Y[i];if(Y[i]>y1)y1=Y[i];}
 const cell=cellWanted||Math.max(1,Math.ceil(Math.max(x1-x0,y1-y0)/800)),nx=Math.floor((x1-x0)/cell)+2,ny=Math.floor((y1-y0)/cell)+2,Gz=new Float32Array(nx*ny).fill(NaN);
 for(let t=0;t<T.length;t+=3){const a=T[t],b=T[t+1],c=T[t+2],ax=(X[a]-x0)/cell,ay=(Y[a]-y0)/cell,bx=(X[b]-x0)/cell,by=(Y[b]-y0)/cell,cx=(X[c]-x0)/cell,cy=(Y[c]-y0)/cell,det=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy);if(!det)continue;
  const i0=Math.max(0,Math.ceil(Math.min(ax,bx,cx))),i1=Math.min(nx-1,Math.floor(Math.max(ax,bx,cx))),j0=Math.max(0,Math.ceil(Math.min(ay,by,cy))),j1=Math.min(ny-1,Math.floor(Math.max(ay,by,cy)));
  for(let j=j0;j<=j1;j++)for(let i=i0;i<=i1;i++){const l1=((by-cy)*(i-cx)+(cx-bx)*(j-cy))/det,l2=((cy-ay)*(i-cx)+(ax-cx)*(j-cy))/det,l3=1-l1-l2;if(l1>=-1e-6&&l2>=-1e-6&&l3>=-1e-6)Gz[j*nx+i]=l1*Z[a]+l2*Z[b]+l3*Z[c];}}
 return {x0,y0,cell,nx,ny,Z:Gz};}
function gridZ(Gd,E,N){if(!Gd)return NaN;const fx=(E-Gd.x0)/Gd.cell,fy=(N-Gd.y0)/Gd.cell,i=Math.floor(fx),j=Math.floor(fy);if(i<0||j<0||i>=Gd.nx-1||j>=Gd.ny-1)return NaN;const tx=fx-i,ty=fy-j;let s=0,w=0;
 for(const q of [[0,0,(1-tx)*(1-ty)],[1,0,tx*(1-ty)],[0,1,(1-tx)*ty],[1,1,tx*ty]]){const z=Gd.Z[(j+q[1])*Gd.nx+i+q[0]];if(!isNaN(z)){s+=z*q[2];w+=q[2];}}return w>1e-9?s/w:NaN;}

/* ---------- topografi ---------- */
const TP=[];
/* WS = permukaan kerja: grid permukaan galian yang sudah ada (Edit ▸ front bulanan). topoZ = topografi yang sudah dikurangi galian itu */const WS=[];
function topoZ(E,N){let m=NaN;for(const s of TP){if(!s.on)continue;const z=gridZ(s.G,E,N);if(!isNaN(z)&&!(m<=z))m=z;}if(WS.length&&!isNaN(m))for(const g of WS){const z=gridZ(g,E,N);if(z<m)m=z;}return m;}
function tpBuild(s){if(s.g){G.topo.remove(s.g);clr(s.g);}s.g=new THREE.Group();G.topo.add(s.g);s.g.visible=s.on;const {z0,z1}=s.tin,{X,Y,Z}=s.show||s.tin,T=s.Tshow||s.tin.T,n=X.length;
 const pos=new Float32Array(n*3),col=new Float32Array(n*3),zr=Math.max(z1-z0,1),C3=[[.62,.70,.52],[.72,.78,.58],[.84,.82,.66],[.93,.91,.84]];
 for(let i=0;i<n;i++){pos[i*3]=X[i]-O[0];pos[i*3+1]=Z[i]-O[2];pos[i*3+2]=-(Y[i]-O[1]);let t=(Z[i]-z0)/zr*3;const a=Math.min(Math.floor(t),2),f=t-a;for(let c=0;c<3;c++)col[i*3+c]=C3[a][c]+(C3[a+1][c]-C3[a][c])*f;}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('color',new THREE.BufferAttribute(col,3));g.setIndex(T);g.computeVertexNormals();
 const op=+$('tpo').value;s.mesh=new THREE.Mesh(g,new THREE.MeshPhongMaterial({vertexColors:true,flatShading:true,shininess:8,specular:0x111111,side:THREE.DoubleSide,transparent:op<1,opacity:op,depthWrite:op>=1,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1}));s.g.add(s.mesh);
 const lp=[];for(const l of s.L)for(let k=0;k+1<l.length;k++){const a=l[k],b=l[k+1];if(s.cut&&s.cut(a,b))continue;lp.push(a[0]-O[0],a[2]-O[2]+0.05,-(a[1]-O[1]),b[0]-O[0],b[2]-O[2]+0.05,-(b[1]-O[1]));}
 const lg=new THREE.BufferGeometry();lg.setAttribute('position',new THREE.Float32BufferAttribute(lp,3));s.g.add(new THREE.LineSegments(lg,new THREE.LineBasicMaterial({color:0x5a4630,transparent:true,opacity:.55})));}
function tpList(){const el=$('tpl');el.innerHTML='';TP.forEach(s=>{const r=document.createElement('div');r.className='dsr';r.innerHTML='<input type="checkbox"'+(s.on?' checked':'')+'><span class="t" title="'+esc(s.nm)+'"><b>'+esc(s.nm)+'</b><br><span class="hint">'+nf(s.tin.T.length/3)+' segitiga · RL '+Math.round(s.tin.z0)+'–'+Math.round(s.tin.z1)+'</span></span><button title="Hapus">&#10005;</button>';
 r.querySelector('input').onchange=e=>{s.on=e.target.checked;s.g.visible=s.on;afterTopo();};r.querySelector('button').onclick=()=>{if(!confirm('Hapus topografi '+s.nm+'?'))return;G.topo.remove(s.g);clr(s.g);TP.splice(TP.indexOf(s),1);tpList();afterTopo();};el.appendChild(r);});
 stepSt('s1',TP.length?TP.length+' permukaan':'',TP.length>0);const ts=$('tpsum');if(ts)ts.innerHTML=TP.length?TP.map(s=>'&#10003; '+esc(s.nm)+' · RL '+Math.round(s.tin.z0)+'–'+Math.round(s.tin.z1)).join('<br>'):'Belum ada topografi.';}
function afterTopo(){if(window.pitRedraw)pitRedraw();}
$('tpf').onchange=async e=>{for(const f of [...e.target.files]){try{const L=await readFileL(f);setO(L[0][0]);const s={nm:f.name,L,on:true,tin:tinFrom(L,0)};s.G=gridOf(s.tin);TP.push(s);tpBuild(s);}catch(err){alert(f.name+': '+err.message);}}e.target.value='';tpList();afterTopo();view('sw',true);};
$('tpo').oninput=()=>TP.forEach(tpBuild);

/* ---------- Clipper ---------- */
const CS=100,JT=ClipperLib.JoinType,ET=ClipperLib.EndType;
const toC=pts=>pts.map(p=>({X:Math.round((p[0]-O[0])*CS),Y:Math.round((p[1]-O[1])*CS)}));
const frC=(path,z)=>path.map(q=>[q.X/CS+O[0],q.Y/CS+O[1],z]);
function cArea(p){return ClipperLib.Clipper.Area(p)/(CS*CS);}
function cClean(P,minA){const o=[];for(const p of P){const a=cArea(p);if(a>(minA||1))o.push(p);}return o;}
let CORNER='miter';/* sudut bench: 'miter' = tajam seperti Surpac, 'round' = bulat */
function cOff(P,d){if(!P.length)return [];const co=new ClipperLib.ClipperOffset(2.5,0.08*CS);co.AddPaths(P,CORNER==='miter'?JT.jtMiter:JT.jtRound,ET.etClosedPolygon);const out=new ClipperLib.Paths();co.Execute(out,d*CS);return cClean(ClipperLib.Clipper.CleanPolygons(out,0.02*CS));}
function cBool(A,B,type){const c=new ClipperLib.Clipper();c.AddPaths(A,ClipperLib.PolyType.ptSubject,true);c.AddPaths(B,ClipperLib.PolyType.ptClip,true);const out=new ClipperLib.Paths();c.Execute(type,out,ClipperLib.PolyFillType.pftNonZero,ClipperLib.PolyFillType.pftNonZero);return cClean(out);}
const cUnion=(A,B)=>cBool(A,B,ClipperLib.ClipType.ctUnion),cDiff=(A,B)=>cBool(A,B,ClipperLib.ClipType.ctDifference);
const cInter=(A,B)=>cBool(A,B,ClipperLib.ClipType.ctIntersection);
function cLineBuf(pts,w){const co=new ClipperLib.ClipperOffset(2.5,0.08*CS);co.AddPath(toC(pts),CORNER==='miter'?JT.jtMiter:JT.jtRound,CORNER==='miter'?ET.etOpenSquare:ET.etOpenRound);const out=new ClipperLib.Paths();co.Execute(out,w/2*CS);return cClean(out);}
function cWidth(P){/* lebar minimum perkiraan: offset ke dalam sampai habis */let lo=0,hi=500;for(let k=0;k<14;k++){const m=(lo+hi)/2;if(cOff(P,-m).length)lo=m;else hi=m;}return lo*2;}
/* cincin (ring) dalam koordinat dunia [E,N], arah CCW */
function ringOf(path){let r=path.map(q=>[q.X/CS+O[0],q.Y/CS+O[1]]);let a=0;for(let i=0;i<r.length;i++){const p=r[i],q=r[(i+1)%r.length];a+=p[0]*q[1]-q[0]*p[1];}if(a<0)r.reverse();return r;}
function ringCum(r){const c=[0];for(let i=0;i<r.length;i++){const p=r[i],q=r[(i+1)%r.length];c.push(c[i]+Math.hypot(q[0]-p[0],q[1]-p[1]));}return c;}
function ringNear(r,c,p){let best=1e18,bs=0;for(let i=0;i<r.length;i++){const a=r[i],b=r[(i+1)%r.length],dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy||1e-12,t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2)),x=a[0]+dx*t,y=a[1]+dy*t,d=Math.hypot(p[0]-x,p[1]-y);if(d<best){best=d;bs=c[i]+t*(c[i+1]-c[i]);}}return {s:bs,d:best};}
function ringAt(r,c,s){const P=c[c.length-1];s=((s%P)+P)%P;let i=0;while(i<r.length-1&&c[i+1]<s)i++;const a=r[i],b=r[(i+1)%r.length],L=c[i+1]-c[i]||1e-9,t=(s-c[i])/L,dx=(b[0]-a[0])/L,dy=(b[1]-a[1])/L;return {p:[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t],n:[dy,-dx],i};}
/* contoh titik sepanjang busur cincin + normal keluar (dirata-rata di sudut) */
function ringArc(r,c,s0,len,dir,step){const o=[],P=c[c.length-1],m=Math.max(2,Math.ceil(len/(step||1)));const T=[];for(let k=0;k<=m;k++)T.push(k/m);
 /* sudut cincin (mis. sudut lantai segi enam) ikut diambil: tanpa ini tepi jalan memotong sudut lantai (tali busur) → tepi jalan masuk ke lantai / silang (pit dua lantai 19 Nov) */
 if(!window.__ARCNOV&&len>1e-6){for(let i=0;i<c.length-1;i++){for(const w of [-1,0,1]){const sv=c[i]+w*P;const t=(sv-s0)*dir/len;if(t>1e-4&&t<1-1e-4)T.push(t);}}T.sort((a,b)=>a-b);}
 for(const t of T){const s=s0+dir*len*t,A=ringAt(r,c,s),B=ringAt(r,c,s+0.6),Cc=ringAt(r,c,s-0.6);let nx=B.n[0]+Cc.n[0]+2*A.n[0],ny=B.n[1]+Cc.n[1]+2*A.n[1];const l=Math.hypot(nx,ny)||1;o.push({p:A.p,n:[nx/l,ny/l],t});}return o;}
function inPoly(p,r){let c=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const a=r[i],b=r[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c;}return c;}
