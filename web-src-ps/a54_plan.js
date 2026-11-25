/* a54: RENCANA TAMBANG — penjadwalan blok tambang 4 tahap (pemilik 23 Nov 2026, mengikuti alur Minex):
   1 Persiapan  : kalender (shift / hari / minggu / bulan, shift per hari, hari libur), fleet (unit dari Pengaturan unit × jumlah),
                  blok tambang (bench × strip × blok, dari Pit Schedule) → "Tampilkan blok 3D".
   2 Target     : target per periode (ton ore, kadar minimum, SR maksimum BCM/t, BCM total) + urutan (bench dulu / strip dulu, arah
                  strip & blok, jarak bench atas) → Jalankan: blok diisi otomatis per periode sampai kapasitas fleet, mengejar target.
   3 Detail     : aturan (bench atas dulu, akses dari tepi strip), klik blok di 3D = kunci ke periode terpilih (Shift = lepas),
                  cabang rencana (simpan / pakai / bandingkan).
   4 Keluaran   : laporan per periode (target vs hasil), produktivitas fleet, sisa cadangan per bench, ekspor .csv (Excel),
                  face position per periode (.str garis batas & .dxf permukaan).
   3D: blok padat (tanpa transparansi) yang atasnya mengikuti topografi; warna per periode / kadar / fleet; blok yang sudah tergali
   hilang saat diputar, blok periode berjalan diberi garis tepi; garis face position; lini waktu di bawah tampilan 3D. */
const PLC=['#1c7ed6','#f08c00','#2f9e44','#ae3ec9','#e03131','#0ca678','#f59f00','#4263eb','#d6336c','#74b816','#1098ad','#fd7e14'];
const PL={qN:0,q:[],cfg:null,res:null,lock:new Map(),br:[],cur:-1,col:'kadar',on:false,pick:false,play:0,g:null,fb:null,hov:null};
function plCfgDef(){const d=new Date();d.setDate(d.getDate()+1);return {mode:'man',fillAuto:false,cal:{t:'hari',start:d.toISOString().slice(0,10),n:14,sh:2,lib:''},fl:[],tg:{ore:0,gmin:0,srmax:0,bcm:0},sq:{mode:'bench',ds:1,db:1,lead:1,prec:false,acc:false}};}
function plCfg(){if(PL.cfg)return PL.cfg;try{PL.cfg=JSON.parse(localStorage.getItem('psPlanCfg')||'null');}catch(_){PL.cfg=null;}const D=plCfgDef();D.mode='man';if(!PL.cfg)PL.cfg=D;for(const k of ['cal','tg','sq'])PL.cfg[k]=Object.assign({},D[k],PL.cfg[k]||{});if(!Array.isArray(PL.cfg.fl))PL.cfg.fl=[];return PL.cfg;}
function plSave(){try{localStorage.setItem('psPlanCfg',JSON.stringify(PL.cfg));}catch(_){}}
function plFleets(){const c=plCfg();if(!c.fl.length){const L=ulGet();const F=schFleets();for(const [g,ls] of F){const t=ls[0];c.fl.push({nm:'Fleet '+g,u:t.ulib||(L.find(x=>x.alat===t.alat)||L[0]).id,n:Math.max(1,t.nu|0)});}if(!c.fl.length)c.fl.push({nm:'Fleet A1',u:(L.find(x=>x.alat==='ex120')||L[0]).id,n:1});}return c.fl;}
function plFcap(f){const u=ulGet().find(x=>x.id===f.u);return u?ulCap(u)*Math.max(1,f.n|0):0;}
/* ---------- kalender ---------- */
const PLBL=['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
function plDay(d){return d.getDate()+' '+PLBL[d.getMonth()];}
function plCal(N){const c=plCfg().cal,lib=new Set(String(c.lib||'').split(/[,;\s]+/).filter(Boolean)),st=new Date((c.start||'2026-12-01')+'T00:00:00'),sh=Math.max(1,c.sh|0),P=[];N=Math.max(1,Math.min(5000,N||400));
 const iso=d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'),add=(d,k)=>{const x=new Date(d);x.setDate(x.getDate()+k);return x;};
 const off=new Set((c.off||[]).map(Number)),isOff=d=>lib.has(iso(d))||off.has(d.getDay());
 if(c.t==='shift'){let d=new Date(st),s=0;for(let g=0;P.length<N&&g<50000;g++){if(!isOff(d))P.push({lab:'S'+(s+1)+' '+plDay(d),shifts:1,d0:new Date(d),d1:new Date(d)});s++;if(s>=sh){s=0;d=add(d,1);}}return P;}
 let d=new Date(st);for(let i=0;i<N;i++){let a=d,b;if(c.t==='hari')b=add(a,1);else if(c.t==='minggu')b=add(a,7);else{b=new Date(a.getFullYear(),a.getMonth()+1,1);}let days=0;for(let x=new Date(a);x<b;x=add(x,1))if(!isOff(x))days++;
  const lab=c.t==='hari'?plDay(a):c.t==='minggu'?'Mg '+(i+1)+' ('+plDay(a)+')':PLBL[a.getMonth()]+' '+a.getFullYear();P.push({lab,shifts:days*sh,d0:a,d1:add(b,-1)});d=b;}return P;}
/* ---------- blok ---------- */
function plBlocks(){const R=MB.R;if(!R)return null;const B=R.L.filter(o=>o.vol>1||o.nb>0);return {R,B,byKey:new Map(B.map(o=>[o.key,o]))};}
function plRank(o,sq){const s=o.s*sq.ds,b=o.b*sq.db;return sq.mode==='strip'?[s,-o.k,b]:[-o.k,s,b];}
/* ---------- penjadwal target ---------- */
function plRun(){const X=plBlocks();if(!X)throw new Error('Belum ada blok tambang — buka Pit Schedule, gambar Batas fase, lalu hitung Blok tambang.');const c=plCfg(),sq=c.sq,tg=c.tg,F=plFleets(),cal=plCal(c.cal.t==='shift'?5000:c.cal.t==='hari'?3000:c.cal.t==='minggu'?600:150),man=c.mode!=='auto';
 const caps=F.map(plFcap);if(!caps.some(v=>v>0))throw new Error('Kapasitas fleet 0 — atur unit di Pengaturan unit.');
 const B=X.B.slice().sort((a,b)=>{const p=plRank(a,sq),q=plRank(b,sq);return p[0]-q[0]||p[1]-q[1]||p[2]-q[2];}),M=X.byKey,done=new Map(),rem=new Map(),part=new Map(),fleetOf=new Map();
 const has=(k,s,b)=>M.has(mbKey(k,s,b)),fin=key=>!M.has(key)||done.has(key);
 const ok=o=>{if(sq.prec){for(let d=0;d<=Math.max(0,sq.lead|0);d++){const bb=o.b+d*sq.db;if(has(o.k+1,o.s,bb)&&!fin(mbKey(o.k+1,o.s,bb)))return false;}}
  if(sq.acc){const pb=o.b-sq.db,ps=o.s-sq.ds;const a1=!has(o.k,o.s,pb)||done.has(mbKey(o.k,o.s,pb))||rem.has(mbKey(o.k,o.s,pb)),a2=has(o.k,ps,o.b)&&done.has(mbKey(o.k,ps,o.b));if(!a1&&!a2)return false;}return true;};
 const P=cal.map((q,p)=>({p,lab:q.lab,shifts:q.shifts,d0:q.d0,d1:q.d1,cap:caps.reduce((a,v)=>a+v,0)*q.shifts,fc:caps.map(v=>v*q.shifts),fu:caps.map(()=>0),blocks:[],vol:0,ore:0,met:0,wv:0,wt:0,viol:0}));
 const take=(o,P0,f)=>{const key=o.key;let r=rem.has(key)?rem.get(key):1;f=Math.min(f,r);if(!(f>1e-6))return 0;r-=f;rem.set(key,r);
  if(!P0.blocks.includes(key))P0.blocks.push(key);P0.vol+=o.vol*f;P0.ore+=(o.ore||0)*f;P0.met+=(o.met||0)*f;P0.wv+=(o.wv!=null?o.wv:o.vol)*f;P0.wt+=(o.waste||0)*f;
  let fi=0,best=-1e18;P0.fc.forEach((v,i)=>{const x=v-P0.fu[i];if(x>best){best=x;fi=i;}});P0.fu[fi]+=o.vol*f;if(!fleetOf.has(key))fleetOf.set(key,fi);(part.get(key)||part.set(key,[]).get(key)).push({p:P0.p,f,fi});
  if(r<=1e-6){done.set(key,P0.p);rem.delete(key);}return f;};
 const Q=(PL.q||[]).slice(0,Math.min(PL.q.length,PL.qN|0)).filter(k=>M.has(k));let qi=0;
 let idle=0;for(const P0 of P){const lim=tg.bcm>0?Math.min(P0.cap,tg.bcm):P0.cap,room=()=>lim-P0.vol;
  {/* periode mengalir: berhenti bila tidak ada lagi yang bisa digali */const anyLock=[...PL.lock.values()].some(pp=>pp>=P0.p),work=rem.size>0||anyLock||(man?(Q.some(k=>!done.has(k))||(c.fillAuto&&B.some(q=>!done.has(q.key)))):B.some(q=>!done.has(q.key)));if(!work)break;}
  /* 1. blok terkunci ke periode ini (seluruh sisanya) */for(const [key,pp] of PL.lock)if(pp===P0.p&&!done.has(key)&&M.has(key)){const o=M.get(key);if(!ok(o))P0.viol++;take(o,P0,1);}
  for(let guard=0;guard<200000&&room()>1e-3;guard++){let o=null;
   /* 2. blok yang sedang digali (sebagian) dilanjutkan */for(const key of rem.keys()){if(!done.has(key)&&!(PL.lock.has(key)&&PL.lock.get(key)!==P0.p)){o=M.get(key);break;}}
   /* 3. manual: urutan klik */if(!o&&man){while(qi<Q.length&&(done.has(Q[qi])||(PL.lock.has(Q[qi])&&PL.lock.get(Q[qi])!==P0.p)))qi++;if(qi<Q.length){o=M.get(Q[qi]);if(!ok(o))P0.viol++;}}
   /* 4. otomatis (atau sisa setelah antrean manual bila dipilih) */if(!o&&(!man||c.fillAuto)){const E=B.filter(q=>!done.has(q.key)&&!rem.has(q.key)&&!(PL.lock.has(q.key))&&!Q.includes(q.key)&&ok(q));if(E.length){o=E[0];const sr=P0.ore>0?P0.wv/P0.ore:Infinity;
     if(tg.ore>0&&P0.ore<tg.ore){const eo=E.find(q=>q.ore>0&&(!(tg.gmin>0)||q.g>=tg.gmin));if(eo&&(tg.srmax>0?sr>tg.srmax:true))o=eo;}else if(tg.srmax>0&&sr>tg.srmax){const eo=E.find(q=>q.ore>0);if(eo)o=eo;}}}
   if(!o)break;const r0=rem.has(o.key)?rem.get(o.key):1,f=Math.min(r0,room()/Math.max(1e-9,o.vol));if(take(o,P0,f)<=1e-6)break;}
  if(P0.shifts>0&&!P0.blocks.length){if(++idle>3)break;}else if(P0.blocks.length)idle=0;}
 /* buang periode kosong di ujung */while(P.length&&!P[P.length-1].blocks.length)P.pop();
 const left=B.filter(o=>!done.has(o.key));PL.res={P,done,rem,part,fleetOf,left,F:F.map(f=>Object.assign({},f)),tg:Object.assign({},tg),man,at:Date.now()};if(PL.cur>=P.length||PL.cur<-1)PL.cur=0;plDraw3d();plTL();plUi();
 schMsg('Rencana tambang ('+(man?'manual':'otomatis')+'): '+done.size+' blok selesai'+(rem.size?', '+rem.size+' sebagian':'')+', '+left.length+' blok belum / belum selesai.');return PL.res;}
/* ---------- 3D: blok padat mengikuti topografi ---------- */
function plColOf(o){const r=PL.res;if(PL.col==='per'){const p=r?r.done.get(o.key):undefined;if(p==null)return '#868e96';/* gradasi urut periode: awal biru → akhir merah */const n=Math.max(1,r.P.length-1),t=p/n,R4=['#2b5fb4','#33a86f','#eed64d','#db5438'],u=t*3,a=Math.min(Math.floor(u),2);return '#'+new THREE.Color(R4[a]).lerp(new THREE.Color(R4[a+1]),u-a).getHexString();}
 if(PL.col==='fleet'){const f=r?r.fleetOf.get(o.key):undefined;return f==null?'#868e96':PLC[(f*3+1)%PLC.length];}
 try{const R=MB.R;let gm=0,om=0,sm=0;for(const q of R.L){if(q.ore>0){gm=Math.max(gm,q.g);om=Math.max(om,q.ore);if(isFinite(q.sr))sm=Math.max(sm,q.sr);}}const c=mbColor(o,{gm:gm||1,om:om||1,sm:Math.min(sm||1,10),sc:new Map()});return '#'+new THREE.Color(c[0],c[1],c[2]).getHexString();}catch(_){return '#868e96';}}
function plCells(){const R=MB.R,Gd=SCH.grid;if(!R||!Gd)return null;if(PL._cells&&PL._cells.R===R&&PL._cells.Gd===Gd)return PL._cells.m;const m=new Map(),{nx,ny}=Gd;
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const c=j*nx+i;if(R.cs[c]<-1e8)continue;const k0=R.cs[c]-R.smin+1+'|'+(R.cb[c]-R.bmin+1);let a=m.get(k0);if(!a)m.set(k0,a=[]);a.push(c);}PL._cells={R,Gd,m};return m;}
function plDraw3d(){schGrp();if(!PL.g){PL.g=new THREE.Group();SCH.g.add(PL.g);}const g=PL.g;while(g.children.length){const c=g.children[0];g.remove(c);clr(c);}PL.fb=null;if(!PL.on)return;
 const R=MB.R,Gd=SCH.grid,CM=plCells();if(!R||!Gd||!CM)return;const r=PL.res,cur=PL.cur,{nx}=Gd,pos=[],col=[],fb=[],ed=[],edC=[];
 const QS=new Set((PL.q||[]).slice(PL.qN|0)),vis=o=>{if(!r||cur<0)return true;const p=r.done.get(o.key);return p===undefined||p>=cur;};
 const quad=(A,B2,C2,D2,rgb,sh,key)=>{for(const q of [A,B2,C2,A,C2,D2]){pos.push(q.x,q.y,q.z);col.push(rgb.r*sh,rgb.g*sh,rgb.b*sh);}fb.push(key,key);};
 for(const o of R.L){if(!vis(o))continue;const cells=CM.get(o.s+'|'+o.b);if(!cells)continue;const rgb=new THREE.Color(QS.has(o.key)&&!(r&&r.done.has(o.key))?'#ffa94d':plColOf(o)),bt=o.k*R.bhE,tt=(o.k+1)*R.bhE,inB=new Map(),now=r&&r.done.get(o.key)===cur&&cur>=0;
  for(const c of cells){const top=Math.min(Gd.z0[c],tt),bot=Math.max(R.fl[c],bt);if(top>bot+1e-3)inB.set(c,[top,bot]);}if(!inB.size)continue;
  for(const [c,[top,bot]] of inB){const i=c%nx,j=(c-i)/nx,K=[[i,j],[i+1,j],[i+1,j+1],[i,j+1]].map(u=>schCorner(Gd,u[0],u[1]));const T=K.map(w=>V(w[0],w[1],top)),Bt=K.map(w=>V(w[0],w[1],bot));
   quad(T[0],T[1],T[2],T[3],rgb,1,o.key);const nb=[[c-nx,0,1],[c+1,1,2],[c+nx,2,3],[c-1,3,0]];
   for(const [cn,a,b] of nb){const out=(a===1&&i===nx-1)||(a===3&&i===0)||!inB.has(cn);if(!out)continue;quad(Bt[a],Bt[b],T[b],T[a],rgb,0.68,o.key);ed.push(T[a].x,T[a].y,T[a].z,T[b].x,T[b].y,T[b].z);edC.push(now?1:0.12,now?0.85:0.14,now?0:0.16,now?1:0.12,now?0.85:0.14,now?0:0.16);}}}
 if(pos.length){const bg=new THREE.BufferGeometry();bg.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));bg.setAttribute('color',new THREE.Float32BufferAttribute(col,3));const me=new THREE.Mesh(bg,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:1}));me.renderOrder=3;g.add(me);PL.fb={me,fb};}
 if(ed.length){const lg=new THREE.BufferGeometry();lg.setAttribute('position',new THREE.Float32BufferAttribute(ed,3));lg.setAttribute('color',new THREE.Float32BufferAttribute(edC,3));const L=new THREE.LineSegments(lg,new THREE.LineBasicMaterial({vertexColors:true}));L.renderOrder=4;g.add(L);}
 /* antrean klik: label per kolom "#urutan ↓jumlah bench" di atas blok antrean teratas */if(QS.size){const colQ=new Map();PL.q.forEach((key,ix)=>{const o=R.M.get(key);if(!o)return;const ck=o.s+'|'+o.b;let a=colQ.get(ck);if(!a)colQ.set(ck,a={o,n:0,i0:ix});a.n++;if(o.k>a.o.k)a.o=o;});
  for(const a of colQ.values()){const cells=CM.get(a.o.s+'|'+a.o.b);if(!cells||!cells.length)continue;let x=0,y=0,z=-1e9;for(const c of cells){const i=c%nx,j=(c-i)/nx,w=schCorner(Gd,i+0.5,j+0.5);x+=w[0];y+=w[1];z=Math.max(z,Math.min(Gd.z0[c],(a.o.k+1)*R.bhE));}x/=cells.length;y/=cells.length;
   try{const sp=sprite('#'+(a.i0+1)+(a.n>1?' ↓'+a.n+' bench':''),'#b35c00',0.014,V(x,y,z+2));sp.renderOrder=9;if(sp.material)sp.material.depthTest=false;g.add(sp);}catch(_){}}}
 /* face position: batas galian kumulatif s/d periode berjalan, per bench */if(r&&cur>=0){for(const L2 of plFaceLines(cur)){const o=lineObj(L2.map(p=>[p[0],p[1],p[2]+0.4]),'#ffd43b',false,{depthTest:false});o.renderOrder=7;g.add(o);}}
 try{MB.g&&(MB.g.visible=!PL.on);}catch(_){}}
/* garis batas sel tergali (kumulatif s/d periode p) per bench → ruas yang dirangkai */
function plFaceMask(p){const r=PL.res,R=MB.R,Gd=SCH.grid,CM=plCells();if(!r||!R||!Gd||!CM)return null;const M=new Map();/* k → Set sel */
 for(const [key,pp] of r.done){if(pp>p)continue;const o=R.M.get(key);if(!o)continue;const cells=CM.get(o.s+'|'+o.b)||[];let S=M.get(o.k);if(!S)M.set(o.k,S=new Set());for(const c of cells){const top=Math.min(Gd.z0[c],(o.k+1)*R.bhE),bot=Math.max(R.fl[c],o.k*R.bhE);if(top>bot+1e-3)S.add(c);}}return M;}
function plFaceLines(p){const M=plFaceMask(p);if(!M)return [];const Gd=SCH.grid,R=MB.R,{nx,ny}=Gd,out=[];
 for(const [k,S] of M){const z=k*R.bhE,E=new Map(),key=(i,j)=>i+','+j,add=(a,b)=>{(E.get(a)||E.set(a,[]).get(a)).push(b);(E.get(b)||E.set(b,[]).get(b)).push(a);};
  for(const c of S){const i=c%nx,j=(c-i)/nx;if(j===0||!S.has(c-nx))add(key(i,j),key(i+1,j));if(i===nx-1||!S.has(c+1))add(key(i+1,j),key(i+1,j+1));if(j===ny-1||!S.has(c+nx))add(key(i,j+1),key(i+1,j+1));if(i===0||!S.has(c-1))add(key(i,j),key(i,j+1));}
  const used=new Set(),ek=(a,b)=>a<b?a+'|'+b:b+'|'+a;for(const [a0] of E){for(const b0 of E.get(a0)){if(used.has(ek(a0,b0)))continue;const L=[a0];let a=a0,b=b0;used.add(ek(a,b));for(let g=0;g<1e6;g++){L.push(b);const nx2=(E.get(b)||[]).find(q=>!used.has(ek(b,q)));if(!nx2)break;used.add(ek(b,nx2));a=b;b=nx2;}
   out.push(L.map(s=>{const [i,j]=s.split(',').map(Number),w=schCorner(Gd,i,j);return [w[0],w[1],z];}));}}}return out;}
/* ---------- arahkan kursor / klik blok ---------- */
(function(){const tip=document.createElement('div');tip.id='pltip';tip.style.cssText='position:fixed;z-index:9;display:none;pointer-events:none;background:rgba(28,39,51,.94);color:#fff;border-left:3px solid #B5893E;border-radius:4px;padding:4px 8px;font:11.5px/1.45 system-ui,Segoe UI,Arial,sans-serif;max-width:300px';document.body.appendChild(tip);
 const rc=new THREE.Raycaster(),hit=e=>{if(!PL.on||!PL.fb)return null;const r=R.domElement.getBoundingClientRect(),m=new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);rc.setFromCamera(m,C);const h=rc.intersectObject(PL.fb.me,false)[0];if(!h)return null;return MB.R.M.get(PL.fb.fb[Math.floor(h.faceIndex/1)])||null;};
 let t0=0;R.domElement.addEventListener('pointermove',e=>{if(!PL.on||(MODE==='edit'&&typeof HOV!=='undefined'&&HOV.k)||(typeof B3!=='undefined'&&B3.on&&B3.mesh)||(SCH.g&&!SCH.g.visible)){tip.style.display='none';return;}const n=performance.now();if(n-t0<60)return;t0=n;const o=hit(e);if(!o){tip.style.display='none';return;}const r=PL.res,p=r&&r.done.get(o.key),f=r&&r.fleetOf.get(o.key),lk=PL.lock.get(o.key);
  tip.innerHTML='<b>'+esc(o.nm)+'</b><br>'+schF(o.vol)+' BCM'+(o.ore>0?' · ore '+schF(o.ore)+' t @ '+o.g.toFixed(2)+' g/t':'')+(o.wv!=null?' · waste '+schF(o.wv)+' BCM':'')+(o.ore>0&&isFinite(o.sr)?' · SR '+o.sr.toFixed(2):'')+'<br>'+(p!=null&&r?'Periode '+(p+1)+' · '+esc(r.P[p].lab)+(f!=null?' · '+esc(r.F[f].nm):''):'belum terjadwal')+(lk!=null?' · 🔒 dikunci ke periode '+(lk+1):'')+(PL.q.includes(o.key)?' · antrean #'+(PL.q.indexOf(o.key)+1):'')+(r&&r.rem&&r.rem.has(o.key)?' · sisa '+Math.round(r.rem.get(o.key)*100)+'% (sebagian)':'');
  tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+12)+'px';tip.style.display='block';});
 R.domElement.addEventListener('pointerleave',()=>{tip.style.display='none';});
 let dn=null;R.domElement.addEventListener('pointerdown',e=>{dn=PL.pick&&e.button===0?[e.clientX,e.clientY]:null;},true);
 R.domElement.addEventListener('pointerup',e=>{if(!PL.pick||!dn)return;const d=Math.hypot(e.clientX-dn[0],e.clientY-dn[1]);dn=null;if(d>4)return;const o=hit(e);if(!o)return;
  if(PL.pick==='q'){plQClick(o,e.shiftKey);return;}
  if(e.shiftKey){PL.lock.delete(o.key);schMsg('"'+esc(o.nm)+'" dilepas dari kunci.');}else{const p=Math.max(0,PL.cur);PL.lock.set(o.key,p);schMsg('"'+esc(o.nm)+'" dikunci ke periode '+(p+1)+' — tekan Jalankan untuk menjadwalkan ulang.');}plUi();},true);})();
/* klik blok: blok yang SUDAH di antrean diklik lagi = bench di bawahnya pada kolom yang sama (tanpa Jalankan dulu);
   Shift + klik = keluarkan bench terdalam kolom itu dari antrean */
function plQClick(o,shift){const R=MB.R,n0=PL.qN|0,col=PL.q.map((k,ix)=>({q:R.M.get(k),ix})).filter(x=>x.q&&x.q.s===o.s&&x.q.b===o.b),pend=col.filter(x=>x.ix>=n0);
 if(shift){if(!pend.length){schMsg('Blok ini sudah dijalankan — tidak bisa dikeluarkan dengan Shift + klik (pakai Kosongkan / Kunci).',1);return;}const d=pend[pend.length-1];PL.q.splice(d.ix,1);schMsg('"'+esc(d.q.nm)+'" batal dipilih.');plDraw3d();plUi();return;}
 if(pend.length){schMsg('Kolom S'+o.s+'-'+String(o.b).padStart(2,'0')+' sudah dipilih (<b>'+esc(pend[0].q.nm)+'</b>). Tekan <b>▶ Jalankan</b> dulu, baru kolom ini bisa diturunkan ke bench berikutnya.',1);return;}
 let pick=o;if(col.length){const d=col.reduce((a,x)=>x.q.k<a.q.k?x:a).q;pick=null;for(let k=d.k-1;k>=d.k-60;k--){const q=R.M.get(mbKey(k,o.s,o.b));if(q){pick=q;break;}}
  if(!pick){schMsg('Kolom S'+o.s+'-'+String(o.b).padStart(2,'0')+' sudah sampai bench terbawah desain.',1);return;}}
 PL.q.push(pick.key);schMsg('Dipilih: <b>'+esc(pick.nm)+'</b> (antrean #'+PL.q.length+'). '+(PL.q.length-n0)+' blok menunggu <b>▶ Jalankan</b>.');plDraw3d();plUi();try{uxSync(true);}catch(_){}}
/* ---------- lini waktu ---------- */
function plTL(){let b=$('pltl');if(!b){b=document.createElement('div');b.id='pltl';b.style.cssText='position:fixed;z-index:9;display:none;background:rgba(255,255,255,.97);border:1px solid #D3CDC1;border-radius:6px;box-shadow:0 2px 10px rgba(0,0,0,.15);padding:4px 6px;font:11px/1.3 system-ui,Segoe UI,Arial,sans-serif;color:#1C2733';document.body.appendChild(b);
  b.addEventListener('click',e=>{const a=e.target.closest('[data-tp]');if(a){PL.cur=+a.dataset.tp;plStop();plDraw3d();plTL();return;}const k=e.target.closest('[data-tk]');if(!k)return;const v=k.dataset.tk;if(v==='play'){PL.play?plStop():plPlay();}else if(v==='prev'){PL.cur=Math.max(-1,PL.cur-1);plDraw3d();plTL();}else if(v==='next'){PL.cur=Math.min(PL.res.P.length-1,PL.cur+1);plDraw3d();plTL();}else if(v==='x'){PL.on=false;plDraw3d();plTL();plUi();}});}
 const r=PL.res;if(!PL.on||!r){b.style.display='none';return;}const tg=r.tg,F=n=>gtShort(n);
 const cells=r.P.map((q,i)=>{const sr=q.ore>0?q.wv/q.ore:null,miss=(tg.ore>0&&q.ore<tg.ore*0.98)||(tg.srmax>0&&sr!=null&&sr>tg.srmax*1.02)||(tg.gmin>0&&q.ore>0&&q.met/q.ore<tg.gmin)||q.viol>0,u=q.cap>0?q.vol/q.cap:0;
  return '<div data-tp="'+i+'" title="'+esc(q.lab)+(q.viol?' · '+q.viol+' blok kunci melanggar urutan':'')+'" style="cursor:pointer;min-width:64px;border:'+(i===PL.cur?'2px solid #1C2733':'1px solid #e3dfd6')+';border-top:4px solid '+PLC[i%PLC.length]+';border-radius:3px;padding:2px 4px;background:'+(miss?'#fff5f5':'#fff')+(miss?';outline:1px solid #e03131':'')+'"><div style="font-weight:600;white-space:nowrap">'+esc(q.lab)+'</div><div>'+(q.ore>0?F(q.ore)+' t · '+(q.met/q.ore).toFixed(2):F(q.vol)+' BCM')+'</div><div style="color:#6c757d">SR '+(sr==null?'–':sr.toFixed(2))+' · '+Math.round(u*100)+'%</div></div>';}).join('');
 b.innerHTML='<div style="display:flex;gap:6px;align-items:center;margin-bottom:3px"><button data-tk="prev">◀</button><button data-tk="play">'+(PL.play?'❚❚':'▶')+'</button><button data-tk="next">▶|</button><b>'+(PL.cur<0?'Sebelum menambang':'Periode '+(PL.cur+1)+' · '+esc(r.P[PL.cur].lab))+'</b><span style="flex:1"></span><span style="color:#6c757d">garis merah = target tidak tercapai · klik periode = lihat di 3D</span><button data-tk="x" title="Tutup lini waktu">✕</button></div><div style="display:flex;gap:4px;overflow-x:auto;padding-bottom:2px">'+cells+'</div>';
 try{const c=$('cv').getBoundingClientRect();b.style.left=(c.left+8)+'px';b.style.width=Math.max(300,c.width-16)+'px';b.style.top=(c.bottom-b.offsetHeight-8)+'px';}catch(_){}b.style.display='block';
 try{const c=$('cv').getBoundingClientRect();b.style.top=(c.bottom-b.offsetHeight-8)+'px';}catch(_){}}
function plPlay(){if(!PL.res)return;plStop();if(PL.cur>=PL.res.P.length-1)PL.cur=-1;PL.play=setInterval(()=>{if(PL.cur>=PL.res.P.length-1){plStop();return;}PL.cur++;plDraw3d();plTL();},900);plTL();}
function plStop(){if(PL.play){clearInterval(PL.play);PL.play=0;}}
setInterval(()=>{try{if(PL.on&&PL.res&&$('pltl')&&$('pltl').style.display==='block'){const c=$('cv').getBoundingClientRect(),b=$('pltl');b.style.left=(c.left+8)+'px';b.style.width=Math.max(300,c.width-16)+'px';b.style.top=(c.bottom-b.offsetHeight-8)+'px';}}catch(_){}},500);
/* ---------- laporan & ekspor ---------- */
function plRep(){const r=PL.res;if(!r)return null;const tg=r.tg,rows=r.P.map((q,i)=>{const sr=q.ore>0?q.wv/q.ore:null,g=q.ore>0?q.met/q.ore:null;return {i,lab:q.lab,n:q.blocks.length,vol:q.vol,ore:q.ore,g,wv:q.wv,wt:q.wt,sr,cap:q.cap,u:q.cap>0?q.vol/q.cap:0,okO:!(tg.ore>0)||q.ore>=tg.ore*0.98,okS:!(tg.srmax>0)||sr==null||sr<=tg.srmax*1.02,okG:!(tg.gmin>0)||g==null||g>=tg.gmin,viol:q.viol};});
 const F=r.F.map((f,i)=>{let av=0,us=0;for(const q of r.P){av+=q.fc[i];us+=q.fu[i];}return {nm:f.nm,u:(ulGet().find(x=>x.id===f.u)||{}).nm||f.u,n:f.n,av,us,pct:av>0?us/av:0};});
 const RB=new Map();for(const o of r.left){let a=RB.get(o.k);if(!a)RB.set(o.k,a={k:o.k,n:0,vol:0,ore:0,met:0,wv:0});a.n++;a.vol+=o.vol;a.ore+=o.ore||0;a.met+=o.met||0;a.wv+=(o.wv!=null?o.wv:o.vol);}
 return {rows,F,res:[...RB.values()].sort((a,b)=>b.k-a.k)};}
function plCsv(){const X=plRep();if(!X)return;const q=s=>'"'+String(s).replace(/"/g,'""')+'"',L=[],bh=MB.R.bhE;
 L.push(q('RENCANA TAMBANG — '+schPh().nm));L.push(['Periode','Label','Blok','Total BCM','Ore t','Kadar g/t','Waste BCM','Waste t','SR (BCM/t)','Kapasitas BCM','Utilisasi %','Target ore','Target SR','Target kadar'].map(q).join(','));
 for(const r of X.rows)L.push([r.i+1,q(r.lab),r.n,r.vol.toFixed(1),r.ore.toFixed(1),r.g==null?'':r.g.toFixed(3),r.wv.toFixed(1),r.wt.toFixed(1),r.sr==null?'':r.sr.toFixed(3),r.cap.toFixed(0),(r.u*100).toFixed(1),r.okO?'ya':'TIDAK',r.okS?'ya':'TIDAK',r.okG?'ya':'TIDAK'].join(','));
 L.push('');L.push(q('PRODUKTIVITAS FLEET'));L.push(['Fleet','Unit','Jumlah','Tersedia BCM','Terpakai BCM','Utilisasi %'].map(q).join(','));for(const f of X.F)L.push([q(f.nm),q(f.u),f.n,f.av.toFixed(0),f.us.toFixed(0),(f.pct*100).toFixed(1)].join(','));
 L.push('');L.push(q('SISA CADANGAN (belum terjadwal)'));L.push(['Bench RL','Blok','BCM','Ore t','Kadar g/t','Waste BCM','SR'].map(q).join(','));for(const a of X.res)L.push([q(schF(a.k*bh,1)+'–'+schF((a.k+1)*bh,1)),a.n,a.vol.toFixed(1),a.ore.toFixed(1),a.ore>0?(a.met/a.ore).toFixed(3):'',a.wv.toFixed(1),a.ore>0?(a.wv/a.ore).toFixed(3):''].join(','));
 L.push('');L.push(q('BLOK TERJADWAL'));L.push(['Blok','Periode','Label','Fleet','Bagian %','BCM','Ore t','Kadar g/t','Waste BCM'].map(q).join(','));const r=PL.res;for(const [key,pp] of r.part){const o=MB.R.M.get(key);if(!o)continue;for(const x of pp)L.push([q(o.nm),x.p+1,q(r.P[x.p].lab),q(r.F[x.fi]?r.F[x.fi].nm:''),(x.f*100).toFixed(0),(o.vol*x.f).toFixed(1),((o.ore||0)*x.f).toFixed(1),o.ore>0?o.g.toFixed(3):'',((o.wv!=null?o.wv:o.vol)*x.f).toFixed(1)].join(','));}
 dl('﻿'+L.join('\r\n'),'rencana_tambang_'+today()+'.csv','text/csv');}
function plFaceStr(){const r=PL.res;if(!r)return;const L=[pjName()+'_face,'+new Date().toLocaleDateString('en-GB')+',,ssi_styles:survey.ssi','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'];
 r.P.forEach((q,p)=>{if(!q.blocks.length)return;for(const ln of plFaceLines(p)){for(const v of ln)L.push((p+1)+', '+v[1].toFixed(3)+', '+v[0].toFixed(3)+', '+v[2].toFixed(3)+', face_periode_'+(p+1)+', '+q.lab.replace(/,/g,' '));L.push('0, 0.000, 0.000, 0.000,');}});
 L.push('0, 0.000, 0.000, 0.000, END');dl(L.join('\r\n')+'\r\n',pjName()+'_face_position_'+today()+'.str');}
function plFaceDxf(){const r=PL.res,Gd=SCH.grid,R=MB.R;if(!r||!Gd||!R)return;const p=Math.max(0,PL.cur),M=plFaceMask(p),{nx,ny}=Gd,Z=Float32Array.from(Gd.z0);
 for(const [k,S] of M)for(const c of S)Z[c]=Math.min(Z[c],Math.max(R.fl[c],k*R.bhE));
 const out=[dxfHead()],F3=(a,b,c2,zz)=>out.push('0\n3DFACE\n8\nFACE_P'+(p+1)+'\n'+[a,b,c2,c2].map((w,k)=>(10+k)+'\n'+w[0].toFixed(3)+'\n'+(20+k)+'\n'+w[1].toFixed(3)+'\n'+(30+k)+'\n'+zz.toFixed(3)+'\n').join(''));
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const c=j*nx+i,z=Z[c];if(!(z===z))continue;const K=[[i,j],[i+1,j],[i+1,j+1],[i,j+1]].map(u=>schCorner(Gd,u[0],u[1]));F3(K[0],K[1],K[2],z);F3(K[0],K[2],K[3],z);}
 out.push('0\nENDSEC\n0\nEOF\n');dl(new Blob(out,{type:'application/dxf'}),pjName()+'_face_periode'+(p+1)+'_'+today()+'.dxf');}
/* ---------- cabang rencana ---------- */
function plBrSave(){const r=PL.res;if(!r){alert('Jalankan dulu.');return;}const X=plRep(),nm=prompt('Nama cabang rencana:','Rencana '+String.fromCharCode(65+PL.br.length));if(!nm)return;
 let o=0,m=0,w=0,v=0;for(const q of r.P){o+=q.ore;m+=q.met;w+=q.wv;v+=q.vol;}PL.br.push({nm,res:r,lock:new Map(PL.lock),cfg:JSON.parse(JSON.stringify(plCfg())),sum:{o,m,w,v,left:r.left.length,miss:X.rows.filter(q=>!(q.okO&&q.okS&&q.okG)).length}});plUi();}
/* ---------- antarmuka ---------- */
function plOpen(){try{caraOpen();}catch(e){console.warn(e);}}
function plUi(){const b=$('plwb');if(!b)return;const c=plCfg(),F=plFleets(),L=ulGet(),X=plBlocks(),r=PL.res,n=(k,v,w,st)=>'<input data-pk="'+k+'" type="number" step="any" value="'+v+'" style="width:'+(w||56)+'px"'+(st||'')+'>';
 const sec=(no,ti,st,body,open)=>'<details class="plsec"'+(open?' open':'')+' style="border:1px solid #D3CDC1;border-radius:6px;margin:5px 0;background:#fff"><summary style="padding:5px 8px;cursor:pointer;display:flex;gap:6px;align-items:center"><span style="width:16px;text-align:center;color:#2B5F9E">'+no+'</span><b>'+ti+'</b><span style="flex:1"></span><span style="font-size:11px;color:#6c757d">'+st+'</span></summary><div style="padding:4px 9px 8px">'+body+'</div></details>';
 const capT=F.reduce((a,f)=>a+plFcap(f),0);
 let h='';
 h+=sec('📅','Kalender & fleet','tampil per '+c.cal.t+' · '+F.length+' fleet',
  '<div class="r"><b>Kalender</b> <a href="#" data-pa="kal" style="font-size:11px">⚙ kalender kerja</a></div><div class="r">tampilkan per <select data-pc="t">'+[['shift','shift'],['hari','hari'],['minggu','minggu'],['bulan','bulan']].map(o=>'<option value="'+o[0]+'"'+(c.cal.t===o[0]?' selected':'')+'>'+o[1]+'</option>').join('')+'</select></div>'+'<div class="r" style="font-size:11.5px;color:#495057">'+esc(kalSum())+'</div>'+(r&&r.P.length?'<div class="r" style="font-size:11px;color:#2b5f9e">selesai '+plDay(r.P[r.P.length-1].d1)+' '+r.P[r.P.length-1].d1.getFullYear()+' · '+r.P.length+' '+({shift:'shift',hari:'hari',minggu:'minggu',bulan:'bulan'}[c.cal.t]||'periode')+' (mengikuti volume & kapasitas)</div>':'<div class="hint">Lama jadwal tidak perlu diisi: periode bertambah sendiri sampai blok yang dipilih habis digali menurut kapasitas fleet.</div>')+
  '<div class="r" style="margin-top:6px"><b>Fleet</b> <span style="color:#6c757d;font-size:11px">kapasitas dari Pengaturan unit</span> <a href="#" data-pa="unit" style="font-size:11px">⚙ unit</a></div>'+
  F.map((f,i)=>'<div class="r" data-fi="'+i+'"><input data-ff="nm" type="text" value="'+esc(f.nm)+'" style="width:78px"><select data-ff="u">'+L.map(u=>'<option value="'+u.id+'"'+(u.id===f.u?' selected':'')+'>'+esc(u.nm)+'</option>').join('')+'</select> × <input data-ff="n" type="number" value="'+f.n+'" style="width:38px"><span style="font-size:11px;color:#5b3a12">'+schF(plFcap(f))+' BCM/shift</span>'+(F.length>1?'<button data-ffx title="Hapus">✕</button>':'')+'</div>').join('')+
  '<div class="r"><button data-pa="fadd">+ Fleet</button><span style="font-size:11px;color:#5b3a12">total '+schF(capT)+' BCM/shift</span></div>',!r&&!(PL.q&&PL.q.length));
 const man=c.mode!=='auto';
 h+=sec('⇣',man?'Klik blok':'Urutan otomatis',r?'✓ '+r.done.size+' blok selesai'+(r.rem&&r.rem.size?' · '+r.rem.size+' sebagian':''):(man?'manual · '+PL.q.length+' blok diklik':'otomatis'),
  (man?'<div class="hint">Urutan klik = urutan gali. Blok yang sudah dipilih tidak bisa dipilih lagi sebelum <b>▶ Jalankan</b>; sesudahnya klik kolom yang sama = turun 1 bench. Penurunan terkendali bench demi bench. Shift + klik = keluarkan. Periode terisi sendiri menurut kapasitas fleet; blok besar boleh berlanjut ke periode berikutnya.</div>'+
   '<div class="r"><button data-pa="pq" class="'+(PL.pick==='q'?'pri':'')+'">'+(PL.pick==='q'?'✓ Klik blok di 3D aktif':'☝ Klik blok di 3D')+'</button>'+(PL.q.length>(PL.qN|0)?'<span style="font-size:11px;color:#b35c00">'+(PL.q.length-(PL.qN|0))+' blok menunggu Jalankan</span><button data-pa="qundo" title="Batalkan pilihan terakhir yang belum dijalankan">↶ batal 1</button>':'')+(PL.q.length?'<button data-pa="qclr">kosongkan</button>':'')+'</div>'+
   '<label class="r"><input type="checkbox" data-pf'+(c.fillAuto?' checked':'')+'> sisa blok yang belum diklik diisi otomatis</label>'
  :'<div class="r">urutan <select data-ps="mode"><option value="bench"'+(c.sq.mode==='bench'?' selected':'')+'>bench dulu (atas → bawah)</option><option value="strip"'+(c.sq.mode==='strip'?' selected':'')+'>strip dulu (turun per strip)</option></select></div>'+
   '<div class="r">arah strip <select data-ps="ds"><option value="1"'+(c.sq.ds>0?' selected':'')+'>S1 → akhir</option><option value="-1"'+(c.sq.ds<0?' selected':'')+'>akhir → S1</option></select> blok <select data-ps="db"><option value="1"'+(c.sq.db>0?' selected':'')+'>01 → akhir</option><option value="-1"'+(c.sq.db<0?' selected':'')+'>akhir → 01</option></select></div>')+
  '<details style="margin-top:5px"'+((c.tg.ore||c.tg.gmin||c.tg.srmax||c.tg.bcm)?' open':'')+'><summary style="cursor:pointer"><b>Target per periode</b> <span style="color:#6c757d;font-size:11px">(opsional — kosongkan bila belum ada)</span></summary>'+
  '<div class="r">ore '+n('tg.ore',c.tg.ore||'',74)+' t &nbsp;kadar min '+n('tg.gmin',c.tg.gmin||'',48)+' g/t</div><div class="r">SR maks '+n('tg.srmax',c.tg.srmax||'',48)+' BCM/t &nbsp;BCM maks '+n('tg.bcm',c.tg.bcm||'',74)+'</div><div class="hint">'+(man?'Pada mode manual target hanya dipantau (garis merah di lini waktu), tidak mengubah urutan klik.':'Pada mode otomatis blok ore didahulukan bila target ore / SR belum tercapai.')+'</div></details>'+
  '<div class="r" style="margin-top:5px"><button data-pa="run" class="pri">▶ '+(man?'Jalankan':'Jalankan otomatis')+'</button>'+(r?'<button data-pa="play">'+(PL.play?'❚❚ Jeda':'▶ Putar di 3D')+'</button>':'')+'</div>',true);
 const nl=PL.lock.size;
 h+=sec('⚙','Detail & aturan',nl+' blok dikunci · '+PL.br.length+' cabang',
  '<label class="r"><input type="checkbox" data-pb="prec"'+(c.sq.prec?' checked':'')+'> bench atas lebih dulu, unggul '+n('sq.lead',c.sq.lead,38)+' blok</label><label class="r"><input type="checkbox" data-pb="acc"'+(c.sq.acc?' checked':'')+'> akses: maju dari tepi strip / blok tetangga yang sudah tergali</label>'+
  '<div class="r" style="margin-top:4px"><button data-pa="pick" class="'+(PL.pick==='lock'?'pri':'')+'">'+(PL.pick==='lock'?'✓ Kunci aktif':'🔒 Kunci blok ke periode')+'</button>'+(nl?'<button data-pa="unl">Lepas semua kunci</button>':'')+'</div><div class="hint">Pilih periode di lini waktu, lalu klik blok di 3D = dikunci ke periode itu (Shift + klik = lepas). Jalankan lagi untuk menyusun ulang.</div>'+
  '<div class="r" style="margin-top:6px"><b>Cabang rencana</b> <button data-pa="brs">＋ Simpan rencana ini</button></div>'+(PL.br.length?'<table class="pltb"><tr><th>Cabang</th><th>Ore t</th><th>g/t</th><th>SR</th><th>sisa</th><th>meleset</th><th></th></tr>'+PL.br.map((x,i)=>'<tr><td>'+esc(x.nm)+'</td><td>'+gtShort(x.sum.o)+'</td><td>'+(x.sum.o>0?(x.sum.m/x.sum.o).toFixed(2):'–')+'</td><td>'+(x.sum.o>0?(x.sum.w/x.sum.o).toFixed(2):'–')+'</td><td>'+x.sum.left+'</td><td>'+x.sum.miss+'</td><td><button data-bu="'+i+'">pakai</button><button data-bx="'+i+'">✕</button></td></tr>').join('')+'</table>':''),false);
 let rep='<div class="hint">Jalankan rencana dulu.</div>';const XR=plRep();
 if(XR){rep='<table class="pltb"><tr><th>Periode</th><th>Ore t</th><th>g/t</th><th>Waste BCM</th><th>SR</th><th>Kap.</th></tr>'+XR.rows.map(q=>'<tr data-tp2="'+q.i+'" style="cursor:pointer'+(q.i===PL.cur?';background:#e7f0fb':'')+'"><td><i style="display:inline-block;width:8px;height:8px;background:'+PLC[q.i%PLC.length]+'"></i> '+esc(q.lab)+'</td><td'+(q.okO?'':' style="color:#c92a2a"')+'>'+gtShort(q.ore)+'</td><td'+(q.okG?'':' style="color:#c92a2a"')+'>'+(q.g==null?'–':q.g.toFixed(2))+'</td><td>'+gtShort(q.wv)+'</td><td'+(q.okS?'':' style="color:#c92a2a"')+'>'+(q.sr==null?'–':q.sr.toFixed(2))+'</td><td>'+Math.round(q.u*100)+'%</td></tr>').join('')+'</table>'+
  '<div class="r" style="margin-top:5px"><b>Produktivitas fleet</b></div><table class="pltb"><tr><th>Fleet</th><th>Unit</th><th>Tersedia</th><th>Terpakai</th><th>%</th></tr>'+XR.F.map(f=>'<tr><td>'+esc(f.nm)+'</td><td>'+esc(f.u)+' ×'+f.n+'</td><td>'+gtShort(f.av)+'</td><td>'+gtShort(f.us)+'</td><td>'+Math.round(f.pct*100)+'%</td></tr>').join('')+'</table>'+
  '<div class="r" style="margin-top:5px"><b>Sisa cadangan</b> ('+r.left.length+' blok)</div>'+(XR.res.length?'<table class="pltb"><tr><th>Bench</th><th>Blok</th><th>Ore t</th><th>g/t</th><th>Waste BCM</th></tr>'+XR.res.map(a=>'<tr><td>RL '+schF((a.k+1)*MB.R.bhE,1)+'</td><td>'+a.n+'</td><td>'+gtShort(a.ore)+'</td><td>'+(a.ore>0?(a.met/a.ore).toFixed(2):'–')+'</td><td>'+gtShort(a.wv)+'</td></tr>').join('')+'</table>':'<div class="hint">Semua blok terjadwal.</div>')+
  '<div class="r" style="margin-top:6px"><button data-pa="csv">⇩ Laporan Excel (.csv)</button><button data-pa="fstr">⇩ Face position (.str)</button><button data-pa="fdxf">⇩ Permukaan periode (.dxf)</button></div>';}
 const h4=sec('▦','Hasil rencana',r?(XR.rows.filter(q=>!(q.okO&&q.okS&&q.okG)).length+' periode meleset target'):'muncul setelah Jalankan',rep,!!r);
 h+='<div class="r" style="margin-top:4px">warna 3D <select data-pcol><option value="per"'+(PL.col==='per'?' selected':'')+'>per periode</option><option value="kadar"'+(PL.col==='kadar'?' selected':'')+'>ikut warna blok (langkah 2)</option><option value="fleet"'+(PL.col==='fleet'?' selected':'')+'>fleet</option></select></div>';
 const b2=$('plwr'),DS=()=>[...b.querySelectorAll('details.plsec'),...(b2?b2.querySelectorAll('details.plsec'):[])],open=DS().map(d=>d.open);b.innerHTML=h;if(b2)b2.innerHTML=h4;else b.insertAdjacentHTML('beforeend',h4);if(open.length)DS().forEach((d,i)=>{if(open[i]!==undefined)d.open=open[i];});
 const Q=q=>[...b.querySelectorAll(q),...(b2?b2.querySelectorAll(q):[])];
 if(!document.getElementById('plcss')){const st=document.createElement('style');st.id='plcss';st.textContent='.pltb{border-collapse:collapse;width:100%;font-size:11px;margin-top:3px}.pltb th,.pltb td{border-bottom:1px solid #eee;padding:2px 4px;text-align:right}.pltb th:first-child,.pltb td:first-child{text-align:left}.pltb th{background:#F7F5F0}#plwb .r,#plwr .r{display:flex;flex-wrap:wrap;gap:4px 6px;align-items:center;margin:3px 0}';document.head.appendChild(st);}
 const re=()=>{plSave();plUi();};
 Q('[data-pk]').forEach(x=>x.onchange=()=>{const [a,k]=x.dataset.pk.split('.');c[a][k]=+x.value||0;plSave();if(PL.res){try{plRun();return;}catch(_){}}re();});
 Q('[data-pc]').forEach(x=>x.onchange=()=>{c.cal[x.dataset.pc]=x.value;plSave();if(PL.res){PL.lock.clear();try{plRun();return;}catch(_){}}re();});
 Q('[data-ps]').forEach(x=>x.onchange=()=>{const k=x.dataset.ps;c.sq[k]=k==='mode'?x.value:+x.value;re();});
 Q('[data-pb]').forEach(x=>x.onchange=()=>{c.sq[x.dataset.pb]=x.checked;re();});Q('[data-pm]').forEach(x=>x.onchange=()=>{c.mode=x.dataset.pm;if(c.mode==='auto'&&PL.pick==='q')PL.pick=false;re();});{const x=b.querySelector('[data-pf]');if(x)x.onchange=()=>{c.fillAuto=x.checked;re();};}
 Q('[data-fi]').forEach(rw=>{const f=F[+rw.dataset.fi];rw.querySelectorAll('[data-ff]').forEach(x=>x.onchange=()=>{const k=x.dataset.ff;f[k]=k==='n'?Math.max(1,+x.value|0):x.value;re();});const xx=rw.querySelector('[data-ffx]');if(xx)xx.onclick=()=>{F.splice(F.indexOf(f),1);re();};});
 const pc=b.querySelector('[data-pcol]');if(pc)pc.onchange=()=>{PL.col=pc.value;plDraw3d();};
 Q('[data-tp2]').forEach(x=>x.onclick=()=>{PL.cur=+x.dataset.tp2;plStop();plDraw3d();plTL();plUi();});
 Q('[data-bu]').forEach(x=>x.onclick=()=>{const B=PL.br[+x.dataset.bu];PL.res=B.res;PL.lock=new Map(B.lock);PL.cfg=JSON.parse(JSON.stringify(B.cfg));plSave();PL.cur=0;plDraw3d();plTL();plUi();});
 Q('[data-bx]').forEach(x=>x.onclick=()=>{PL.br.splice(+x.dataset.bx,1);plUi();});
 Q('[data-pa]').forEach(x=>x.onclick=e=>{e.preventDefault();const a=x.dataset.pa;try{
  if(a==='unit')ulOpen();else if(a==='fadd'){F.push({nm:'Fleet A'+(F.length+1),u:(F[F.length-1]||{}).u||L[0].id,n:1});re();}
  else if(a==='blk'){mbCalc(true).then(()=>{PL._cells=null;PL.res=null;plUi();plDraw3d();}).catch(er=>schMsg(esc(er.message),1));}
  else if(a==='show'){PL.on=!PL.on;plDraw3d();plTL();plUi();}else if(a==='kal'){kalOpen();return;}else if(a==='run'){PL.on=true;PL.qN=PL.q.length;plRun();}else if(a==='play'){PL.play?plStop():plPlay();plUi();}
  else if(a==='pq'){PL.pick=PL.pick==='q'?false:'q';if(PL.pick){PL.on=true;try{mbPick(false);}catch(_){}}cv.style.cursor=PL.pick?'pointer':'';plDraw3d();plUi();}else if(a==='qundo'){if(PL.q.length>(PL.qN|0)){PL.q.pop();plDraw3d();plUi();}else schMsg('Tidak ada pilihan yang belum dijalankan.',1);}else if(a==='qclr'){PL.q=[];PL.qN=0;PL.res=null;plDraw3d();plTL();plUi();}
  else if(a==='pick'){PL.pick=PL.pick==='lock'?false:'lock';if(PL.pick){PL.on=true;plDraw3d();try{mbPick(false);}catch(_){}}cv.style.cursor=PL.pick?'pointer':'';plUi();}else if(a==='unl'){PL.lock.clear();plUi();}
  else if(a==='brs')plBrSave();else if(a==='csv')plCsv();else if(a==='fstr')plFaceStr();else if(a==='fdxf')plFaceDxf();}catch(er){alert(er.message);}});}
/* blok tambang dihitung ulang → tampilan rencana ikut */
{const _c=mbCalc;mbCalc=async function(){const r=await _c.apply(this,arguments);try{PL._cells=null;if(PL.on){if(PL.res)PL.res=null;plDraw3d();plTL();plUi();}}catch(_){}return r;};}
{const _d=mbDraw;mbDraw=function(){const r=_d.apply(this,arguments);try{if(MB.g)MB.g.visible=!PL.on;}catch(_){}return r;};}
window.__PS3.pl={S:PL,run:()=>plRun(),open:()=>plOpen(),rep:()=>plRep(),draw:()=>plDraw3d(),face:p=>plFaceLines(p).length,cfg:()=>plCfg()};
