/* a87: LAPORAN BLOCK MODEL DESAIN DIBATASI POLIGON / STRING (pemilik 26 Nov 2026: "report block model berdasarkan desain yang dipilih,
   dengan constraint seperti di Surpac"; lalu: impor .str, lalu: "dibatasi dengan string yang tampil di 3D (yang sudah di-klik)" + dalam / luar).
   Jendela Block model → "Laporan desain (topografi → desain)" → baris "batas poligon":
     ✎ Digit poligon     : klik titik-titik di 3D · klik ganda / Enter = selesai · Backspace = hapus titik terakhir · Esc = batal
     ☝ Pilih string di 3D : klik string apa pun yang tampil (crest / toe, garis potong topo, blok tambang, pit impor, poligon berkas batas) ·
                            Ctrl+klik = tambah / lepas · Esc / Enter = selesai. String terbuka ditutup otomatis.
     ⇧ Impor .str / .dxf : satu poligon → langsung jadi batas; banyak poligon (mis. blok mining / strip) → tampil sebagai pilihan berlabel
                            nomor string, lalu diklik mana yang dihitung (tombol "Semua" di bilah atas kanvas).
     di dalam / di luar  : constraint INSIDE / OUTSIDE cara Surpac (pusat blok).
     ✕ Hapus batas       : laporan kembali untuk seluruh desain.
   Ruang galian tanpa blok (dihitung waste) ikut dibatasi. Batas tidak disimpan ke project (sekali pakai).
   Hitungan ada di gtDesign (a36) lewat GT.poly (daftar cincin) + GT.polyOut; modul ini antarmuka, digitasi, pemilihan. */
function gpArea(P){let a=0;for(let i=0,j=P.length-1;i<P.length;j=i++)a+=(P[j][0]*P[i][1]-P[i][0]*P[j][1]);return Math.abs(a)/2;}
/* act = cincin aktif [{r:[[E,N(,Z)]…],lab,src}] · set = poligon pilihan dari berkas [{r,lab,src:'set'}] */
const GP={on:false,pts:[],cur:null,dn:null,pk:false,hov:null,act:[],set:[],setNm:'',run:null,again:false,rep:false,raf:0};
function gpRings(){const P=GT.poly;return P&&P.length?(Array.isArray(P[0][0])?P:[P]):[];}
function gpKey(r){return r.length+':'+r[0][0].toFixed(2)+','+r[0][1].toFixed(2)+':'+gpArea(r).toFixed(1);}
function gpZ(x,y){let z=NaN;try{z=topoZ(x,y);}catch(_){}if(!(z===z)){try{const R0=curR();if(R0&&isFinite(R0.zmin))z=R0.zmin;}catch(_){}}return z===z?z:0;}
/* garis 3D sebuah cincin: titik ber-Z (string dari 3D) digambar di elevasinya; titik tanpa Z (digit / berkas) ditempel ke topografi */
function gpPath(P,close){const L=[],has=P.length&&isFinite(P[0][2]);if(has){for(const p of P)L.push([p[0],p[1],p[2]+0.3]);if(close&&P.length>2)L.push(L[0]);return L;}
 const add=(a,b)=>{const n=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/8));for(let k=0;k<n;k++){const t=k/n,x=a[0]+(b[0]-a[0])*t,y=a[1]+(b[1]-a[1])*t;L.push([x,y,gpZ(x,y)+0.6]);}};
 for(let i=0;i<P.length-1;i++)add(P[i],P[i+1]);const e=P[P.length-1];if(close&&P.length>2){add(e,P[0]);L.push([P[0][0],P[0][1],gpZ(P[0][0],P[0][1])+0.6]);}else L.push([e[0],e[1],gpZ(e[0],e[1])+0.6]);return L;}
function gpCen(r){let x=0,y=0;for(const p of r){x+=p[0];y+=p[1];}return [x/r.length,y/r.length];}
function gpDraw(){if(!G.gpoly){G.gpoly=new THREE.Group();W.add(G.gpoly);}clr(G.gpoly);const line=(L,col,op,ro)=>{if(L.length>1){const o=lineObj(L,col,false,{depthTest:false,transparent:true,opacity:op});o.renderOrder=ro;G.gpoly.add(o);}};
 const AK=new Set(GP.act.map(a=>gpKey(a.r)));
 for(const s of GP.set){const a=AK.has(gpKey(s.r));if(!s.L)s.L=gpPath(s.r,true);if(!a)line(s.L,'#f08c00',.55,10);try{const c=gpCen(s.r),sp=sprite(s.lab,a?'#c2410c':'#b06a00',a?0.03:0.022,V(c[0],c[1],gpZ(c[0],c[1])+2));if(sp){try{LBLS.delete(sp);}catch(_){}sp.renderOrder=13;G.gpoly.add(sp);}/* di luar perapian label otomatis: nomor blok harus selalu tampil */}catch(_){}}
 if(GP.on){const P=GP.pts.concat(GP.cur?[GP.cur]:[]);if(P.length)line(gpPath(P,GP.pts.length>2),'#e8590c',.95,11);
  for(const p of GP.pts){const m=new THREE.Mesh(new THREE.SphereGeometry(1.4,10,8),new THREE.MeshBasicMaterial({color:0xe8590c,depthTest:false}));m.position.copy(V(p[0],p[1],gpZ(p[0],p[1])+0.6));m.renderOrder=12;G.gpoly.add(m);}}
 else for(const a of GP.act){if(!a.L)a.L=gpPath(a.r,true);line(a.L,'#e8590c',.98,11);}
 gpHov();}
function gpHov(){if(!G.gphov){G.gphov=new THREE.Group();W.add(G.gphov);}clr(G.gphov);const h=GP.pk&&GP.hov;if(!h||h.bad)return;const o=lineObj(h.L||(h.L=gpPath(h.r,true)),'#ffd43b',false,{depthTest:false,transparent:true,opacity:1});o.renderOrder=14;G.gphov.add(o);}
function gpLabs(){const A=GP.act;if(!A.length)return '';if(A.length===1)return A[0].nm||A[0].lab;const st=A.every(a=>a.src==='set');const l=A.slice(0,8).map(a=>a.lab).join(', ')+(A.length>8?', …':'');return st?GP.setNm+' · string '+l:A.length+' string';}
/* SATU pintu sinkronisasi: daftar aktif → GT.poly → garis 3D → status → laporan dihitung ulang (bila laporan pernah diminta) */
function gpSync(go){GT.poly=GP.act.length?GP.act.map(a=>a.r.map(p=>[p[0],p[1]])):null;GT.polyNm=gpLabs();if(!GP.act.length)GT.polyOut=false;gpDraw();gpUi();if(go!==false&&(GP.act.length||GP.rep))gpGo();}
function gpUi(){const s=$('gpst');if(!s)return;const b=$('gpdg'),k=$('gppk'),x=$('gpdel'),io=$('gpio'),im=$('gpimb'),A=GP.act,n=A.length;
 b.classList.toggle('on',GP.on);b.innerHTML=GP.on?'&#10003; Selesai':'&#9998; Digit poligon';k.classList.toggle('on',GP.pk);k.innerHTML=GP.pk?'&#10003; Selesai memilih':'&#9757; Pilih string di 3D';k.style.display=GP.on?'none':'';b.style.display=GP.pk?'none':'';im.style.display=GP.on||GP.pk?'none':'';
 io.style.display=n&&!GP.on?'':'none';if(io.value!==(GT.polyOut?'1':'0'))io.value=GT.polyOut?'1':'0';
 x.style.display=(n||GP.set.length)&&!GP.on?'':'none';x.innerHTML=n?'&#10005; Hapus batas':'&#10005; Tutup '+esc(GP.setNm);x.title=n?'Hapus batas: laporan untuk seluruh desain':'Lepas poligon pilihan dari berkas ini';
 const info=n?'<b style="color:#e8590c">aktif · '+(GT.polyOut?'di LUAR':'di dalam')+'</b> · '+(n>1?n+' poligon · ':'')+schF(A.reduce((a,r)=>a+gpArea(r.r),0)/1e4,2)+' ha · '+esc(gpLabs()):GP.set.length?esc(GP.setNm)+': '+GP.set.length+' poligon tampil — belum ada yang dipilih (laporan seluruh desain)':'tanpa batas (seluruh desain)';
 s.innerHTML=GP.on?'klik titik di 3D ('+GP.pts.length+') · klik ganda / Enter = selesai · Esc = batal':GP.pk?(GP.set.length?'klik di dalam poligon '+esc(GP.setNm):'klik string di 3D')+' · Ctrl+klik = tambah / lepas · Esc = selesai<br>'+info:info;}
function gpBar(on){let b=$('gpbar');const w=$('bmw');if(w&&!w.classList.contains('docked')&&!w.classList.contains('dkd')){const f=on==='dig';w.style.opacity=f?'.18':'';w.style.pointerEvents=f?'none':'';}if(b){b.remove();b=null;}if(!on)return;
 b=document.createElement('div');b.id='gpbar';b.style.cssText='position:absolute;left:50%;top:44px;transform:translateX(-50%);z-index:30;background:#F7F5F0;border:1px solid #D3CDC1;border-radius:2px;padding:5px 8px;font-size:12px;display:flex;gap:8px;align-items:center;box-shadow:0 2px 8px #0000002a;white-space:nowrap';
 if(on==='dig'){b.innerHTML='<b>Batas laporan</b><span>'+GP.pts.length+' titik · klik di 3D menambah titik · klik ganda / Enter = selesai · Backspace = hapus titik terakhir</span><button id="gpbok" style="font-weight:700">&#10003; Selesai</button><button id="gpbno">Batal</button>';}
 else{b.innerHTML='<b>Batas laporan</b><span>'+GP.act.length+' terpilih · '+(GP.set.length?'klik di dalam poligon':'klik string')+' · Ctrl+klik = tambah / lepas</span>'+(GP.set.length?'<button id="gpball">Semua ('+GP.set.length+')</button>':'')+(GP.act.length?'<button id="gpbnone">Kosongkan</button>':'')+'<button id="gpbok" style="font-weight:700">&#10003; Selesai</button>';}
 cv.appendChild(b);for(const ev of ['pointerdown','pointermove','click','dblclick'])b.addEventListener(ev,e=>e.stopPropagation());/* fase gelembung: tombol di bilah tetap menerima kliknya */const q=i=>b.querySelector('#'+i);
 if(on==='dig'){q('gpbok').addEventListener('click',()=>gpEnd(true));q('gpbno').addEventListener('click',()=>gpEnd(false));}
 else{q('gpbok').addEventListener('click',()=>gpPkEnd());if(q('gpball'))q('gpball').addEventListener('click',()=>{GP.act=GP.set.slice();gpSync();gpBar('pk');});if(q('gpbnone'))q('gpbnone').addEventListener('click',()=>{GP.act=[];gpSync();gpBar('pk');});}}
function gpOthersOff(){try{modeOff();}catch(_){}try{if(SCH.dig)schDigEnd(false);}catch(_){}try{if(SAY.pick)sayPickToggle(false);}catch(_){}try{if(DG)digStop();}catch(_){}}
function gpEnd(ok){if(!GP.on)return;GP.on=false;GP.cur=null;cv.style.cursor='';gpBar(false);if(ok&&GP.pts.length<3)try{schMsg('Poligon batas perlu minimal 3 titik — dibatalkan.',1);}catch(_){}
 if(ok&&GP.pts.length>=3){GP.act=[{r:GP.pts.map(p=>[p[0],p[1]]),lab:'poligon digit',src:'dig'}];GP.pts=[];gpSync();}else{GP.pts=[];gpDraw();gpUi();}}
function gpStart(){if(GP.on){gpEnd(true);return;}if(GP.pk)gpPkEnd();gpOthersOff();GP.on=true;GP.pts=[];GP.cur=null;cv.style.cursor='crosshair';gpBar('dig');gpDraw();gpUi();try{schMsg('Batas laporan: klik titik-titik poligon di 3D, klik ganda / Enter untuk selesai.');}catch(_){}}
function gpGo(){if(!GT.file||!schDes().length)return;try{const ds=$('gdds');if(ds&&!GP.des)GP.des=ds.value;}catch(_){}const b=$('gdgo');if(b)b.click();}
/* laporan dihitung berurutan: klik beruntun saat hitungan berjalan → dihitung SEKALI lagi dengan pilihan terakhir (tak ada hasil basi) */
{const _g=gtDesign;gtDesign=function(){
 /* hitungan ringkasan otomatis (a46): lewat apa adanya, tanpa batas; sesudahnya laporan berbatas milik pengguna dipulihkan (desain pilihan pengguna juga) */
 if(typeof AG!=='undefined'&&AG.run){const p=_g.apply(this,arguments),f=()=>{if(GP.act.length&&GP.rep)gpLater();};Promise.resolve(p).then(f,f);return p;}
 GP.rep=true;if(GP.run){GP.again=true;return GP.run;}const p=_g.apply(this,arguments);GP.run=p;const fin=()=>{if(GP.run===p)GP.run=null;if(GP.again){GP.again=false;setTimeout(gpGo,0);}};p.then(fin,fin);return p;};}
function gpLater(){clearTimeout(GP.lt);GP.lt=setTimeout(function t(){if(typeof AG!=='undefined'&&AG.run){GP.lt=setTimeout(t,200);return;}try{const s=$('gdds');if(s&&GP.des&&s.value!==GP.des&&[...s.options].some(o=>o.value===GP.des))s.value=GP.des;}catch(_){}gpGo();},250);}

/* ---------- pilih string yang tampil di 3D ---------- */
function gpPx(x,y,z){const v=V(x,y,z);W.localToWorld(v);v.project(C);if(v.z>1)return null;const r=R.domElement.getBoundingClientRect();return [r.left+(v.x+1)/2*r.width,r.top+(1-v.y)/2*r.height];}
function gpSegD(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],l=dx*dx+dy*dy;let t=l?((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l:0;t=Math.max(0,Math.min(1,t));return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);}
function gpChain(o,idx){const P=o.geometry.attributes.position,n=P.count,eq=(i,j)=>P.getX(i)===P.getX(j)&&P.getY(i)===P.getY(j)&&P.getZ(i)===P.getZ(j),I=[];
 if(o.isLineSegments){let a=idx-(idx%2),b=a;while(a-2>=0&&eq(a-1,a))a-=2;while(b+3<n&&eq(b+1,b+2))b+=2;for(let i=a;i<=b;i+=2)I.push(i);I.push(b+1);}else{for(let i=0;i<n;i++)I.push(i);if(o.isLineLoop)I.push(0);}
 const out=[],t=new THREE.Vector3();for(const i of I){t.set(P.getX(i),P.getY(i),P.getZ(i)).applyMatrix4(o.matrixWorld);W.worldToLocal(t);const p=[t.x+O[0],O[1]-t.z,t.y+O[2]],q=out[out.length-1];if(!q||Math.hypot(q[0]-p[0],q[1]-p[1])>1e-3||Math.abs(q[2]-p[2])>1e-3)out.push(p);}return out;}
function gpScene(e){ndc(e);const L=[];const walk=o=>{if(!o.visible||o===G.gpoly||o===G.gphov)return;if((o.isLineSegments||o.isLine)&&o.geometry&&o.geometry.attributes&&o.geometry.attributes.position&&!o.geometry.index)L.push(o);for(const c of o.children)walk(c);};walk(W);if(!L.length)return null;
 const d=C.position.distanceTo(CT.target),h=R.domElement.clientHeight||800,wpp=C.isPerspectiveCamera?2*d*Math.tan(C.fov*Math.PI/360)/h:(C.top-C.bottom)/(C.zoom||1)/h;RC.params.Line=RC.params.Line||{};const old=RC.params.Line.threshold;RC.params.Line.threshold=wpp*7;let H=[];try{H=RC.intersectObjects(L,false);}catch(_){}finally{RC.params.Line.threshold=old;}
 const rc=R.domElement.getBoundingClientRect();let best=null,bd=10;for(const x of H.slice(0,60)){const v=x.point.clone().project(C),dd=Math.hypot(rc.left+(v.x+1)/2*rc.width-e.clientX,rc.top+(1-v.y)/2*rc.height-e.clientY);if(dd<bd){bd=dd;best=x;}}if(!best)return null;
 const P=gpChain(best.object,best.index||0);let cl=false;if(P.length>=4&&Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1])<0.05){P.pop();cl=true;}
 if(P.length<3||gpArea(P)<=1)return {bad:true,d:bd};return {r:P,lab:cl?'string 3D':'string 3D (ditutup otomatis)',src:'3d',d:bd};}
/* berkas poligon pilihan sedang tampil → HANYA poligon berkas itu yang dipilih (klik di dalamnya; tepi bersama antar-blok tidak ambigu);
   tanpa berkas → string apa pun yang tampil di 3D */
function gpPick(e){if(GP.set.length){const p=gpHit(e);if(p){let in_=null;for(const s of GP.set)if(inPoly(p,s.r)&&(!in_||gpArea(s.r)<gpArea(in_.r)))in_=s;if(in_)return in_;}
  const m=[e.clientX,e.clientY];let best=null,bd=9;for(const s of GP.set){if(!s.L)s.L=gpPath(s.r,true);let a=null;for(const q of s.L){const b=gpPx(q[0],q[1],q[2]);if(a&&b){const d=gpSegD(m,a,b);if(d<bd){bd=d;best=s;}}a=b;}}return best;}
 return gpScene(e);}
function gpPk(){if(GP.pk){gpPkEnd();return;}if(GP.on)gpEnd(false);gpOthersOff();GP.pk=true;GP.hov=null;cv.style.cursor='pointer';gpBar('pk');gpUi();try{schMsg('Batas laporan: klik string yang tampil di 3D (Ctrl+klik = tambah / lepas), Esc untuk selesai.');}catch(_){}}
function gpPkEnd(){if(!GP.pk)return;GP.pk=false;GP.hov=null;cv.style.cursor='';gpBar(false);gpHov();gpUi();}
function gpTake(h,add){if(!h){try{schMsg(GP.set.length?'Klik di dalam salah satu poligon '+esc(GP.setNm)+'. Untuk memilih string lain di 3D, tutup berkas itu dulu.':'Tidak ada string di bawah kursor — klik tepat pada garisnya.',1);}catch(_){}return false;}if(h.bad){try{schMsg('String itu tidak membentuk luasan di tampak atas (kurang dari 3 titik / tegak) — pilih string lain.',1);}catch(_){}return false;}
 const k=gpKey(h.r),it={r:h.r,lab:h.lab,src:h.src,nm:h.nm,L:null};if(add){const i=GP.act.findIndex(a=>gpKey(a.r)===k);if(i>=0)GP.act.splice(i,1);else GP.act.push(it);}else GP.act=[it];gpSync();if(GP.pk)gpBar('pk');return true;}

/* ---------- impor dari berkas string Surpac (.str teks / biner) atau .dxf ---------- */
function gpStrIds(buf,nm){try{if(/\.dxf$/i.test(nm)||topoBin(buf))return null;const ids=[];let n=0,id0=0;new TextDecoder('utf-8').decode(buf).split(/\r?\n/).slice(2).forEach(s=>{const f=s.split(',');if(f.length<4)return;const id=+f[0];if(!id){if(n)ids.push(id0);n=0;return;}const y=+f[1],x=+f[2],z=+f[3];if(isFinite(x)&&isFinite(y)&&isFinite(z)){if(!n)id0=id;n++;}});if(n)ids.push(id0);return ids;}catch(_){return null;}}
async function gpImport(f){const buf=await f.arrayBuffer(),L0=strRead(buf,f.name)||[];let ids=gpStrIds(buf,f.name);if(!ids||ids.length!==L0.length)ids=null;
 const L=L0.map((l,i)=>({p:l.filter(p=>p.every(isFinite)),id:ids?ids[i]:i+1})).filter(o=>o.p.length>=3);if(!L.length)throw new Error('Tidak ada string berkoordinat (≥ 3 titik) di '+f.name);
 const closed=l=>l.length>=4&&Math.hypot(l[0][0]-l[l.length-1][0],l[0][1]-l[l.length-1][1])<0.05;let R=L.filter(o=>closed(o.p)).map(o=>({p:o.p.slice(0,-1),id:o.id})),auto=false;
 if(!R.length){R=[L.slice().sort((a,b)=>gpArea(b.p)-gpArea(a.p))[0]];auto=true;}R=R.filter(o=>o.p.length>=3&&gpArea(o.p)>1);if(!R.length)throw new Error('Poligon di '+f.name+' tidak punya luas.');
 if(GP.on)gpEnd(false);const seen={};const items=R.map(o=>{seen[o.id]=(seen[o.id]||0)+1;return {r:o.p.map(p=>[p[0],p[1]]),lab:String(o.id)+(seen[o.id]>1?'/'+seen[o.id]:''),src:'set',L:null};});
 if(items.length===1){if(GP.pk)gpPkEnd();GP.set=[];GP.setNm='';items[0].src='file';items[0].nm=f.name;items[0].lab=f.name;GP.act=[items[0]];gpSync();try{schMsg('Batas laporan diimpor dari <b>'+esc(f.name)+'</b>'+(auto?' (string terbuka — ditutup otomatis)':'')+'.');}catch(_){}}
 else{GP.set=items;GP.setNm=f.name;GP.act=[];gpSync();if(!GP.pk)gpPk();else gpBar('pk');try{schMsg('<b>'+esc(f.name)+'</b>: '+items.length+' poligon tampil di 3D — klik yang mau dihitung (Ctrl+klik = tambah / lepas).');}catch(_){}}
 return {n:items.length,auto};}
function gpClear(){if(GP.act.length){GP.act=[];gpSync();}else{GP.set=[];GP.setNm='';if(GP.pk)gpPkEnd();gpSync(false);}if(GP.pk)gpBar('pk');}
function gpHit(e){let p=null;try{p=hitTopo(e);}catch(_){}if(!p){let z=0;try{const R0=curR();if(R0&&isFinite(R0.zmin))z=R0.zmin;}catch(_){}try{p=hitPlane(e,z);}catch(_){}}return p?[p[0],p[1]]:null;}
(function(){const E=cv,inBar=e=>!!(e.target&&e.target.closest&&e.target.closest('#gpbar'));
 E.addEventListener('pointerdown',e=>{if(inBar(e))return;if((GP.on||GP.pk)&&e.button===0)GP.dn=[e.clientX,e.clientY];},true);
 E.addEventListener('pointermove',e=>{if(inBar(e))return;if(GP.on){const p=gpHit(e);if(p){GP.cur=p;gpDraw();}return;}if(!GP.pk||e.buttons)return;const ev={clientX:e.clientX,clientY:e.clientY};if(GP.raf)return;GP.raf=requestAnimationFrame(()=>{GP.raf=0;if(!GP.pk)return;let h=null;try{h=gpPick(ev);}catch(_){}const k=h&&!h.bad?gpKey(h.r):'',k0=GP.hov&&!GP.hov.bad?gpKey(GP.hov.r):'';if(k!==k0){GP.hov=h;gpHov();}});},true);
 E.addEventListener('click',e=>{if(inBar(e))return;if(!GP.on&&!GP.pk)return;e.stopPropagation();e.preventDefault();if(GP.dn&&Math.hypot(e.clientX-GP.dn[0],e.clientY-GP.dn[1])>5)return;if(e.detail>1)return;
  if(GP.pk){let h=null;try{h=gpPick(e);}catch(err){console.warn('gp pick',err);}gpTake(h,e.ctrlKey||e.metaKey||e.shiftKey);return;}
  const p=gpHit(e);if(!p)return;GP.pts.push(p);gpDraw();gpUi();gpBar('dig');},true);
 E.addEventListener('dblclick',e=>{if(inBar(e))return;if(GP.pk){e.stopPropagation();e.preventDefault();return;}if(!GP.on)return;e.stopPropagation();e.preventDefault();gpEnd(true);},true);
 addEventListener('keydown',e=>{if(!GP.on&&!GP.pk)return;const t=e.target;if(t&&/INPUT|SELECT|TEXTAREA/.test(t.tagName))return;
  if(GP.pk){if(e.key==='Enter'||e.key==='Escape'){e.preventDefault();e.stopPropagation();gpPkEnd();}return;}
  if(e.key==='Enter'){e.preventDefault();e.stopPropagation();gpEnd(true);}else if(e.key==='Escape'){e.preventDefault();e.stopPropagation();gpEnd(false);}else if(e.key==='Backspace'){e.preventDefault();GP.pts.pop();gpDraw();gpUi();gpBar('dig');}},true);})();
/* baris antarmuka di jendela Block model */
{const _w=gtWin;gtWin=function(){const r=_w.apply(this,arguments);try{if(!$('gprow')){const go=$('gdgo'),row=go&&go.closest('.r');if(row){row.insertAdjacentHTML('afterend','<div class="r" id="gprow" title="Batasi laporan desain dengan poligon: didigit di 3D, dipilih dari string yang tampil di 3D, atau diimpor dari berkas .str / .dxf — blok dihitung bila pusatnya di dalam (atau di luar) poligon, seperti constraint Surpac">batas poligon <button id="gpdg">&#9998; Digit poligon</button><button id="gppk" title="Klik string yang tampil di 3D (crest / toe, garis potong topo, blok tambang, pit impor, poligon berkas) sebagai batas laporan · Ctrl+klik = tambah / lepas">&#9757; Pilih string di 3D</button><button id="gpimb" title="Impor poligon dari berkas string Surpac (.str) atau .dxf — satu poligon langsung jadi batas; banyak poligon (blok mining) tampil untuk dipilih">&#8679; Impor .str / .dxf</button><input id="gpimf" type="file" accept=".str,.dxf" hidden><select id="gpio" title="Constraint INSIDE / OUTSIDE: hitung blok yang pusatnya di dalam atau di luar poligon" style="display:none"><option value="0">di dalam</option><option value="1">di luar</option></select><button id="gpdel" style="display:none">&#10005; Hapus batas</button><span id="gpst" style="font-size:11px;color:#6c757d;display:block;flex:0 0 100%;white-space:normal;margin-top:2px"></span></div>');
   try{const ds=$('gdds');GP.des=ds.value;ds.addEventListener('change',e=>{if(!(typeof AG!=='undefined'&&AG.run))GP.des=e.target.value;});}catch(_){}$('gpdg').onclick=gpStart;$('gppk').onclick=gpPk;$('gpdel').onclick=gpClear;$('gpio').onchange=e=>{GT.polyOut=e.target.value==='1';gpSync();};$('gpimb').onclick=()=>$('gpimf').click();
   $('gpimf').onchange=e=>{const f=e.target.files[0];e.target.value='';if(f)gpImport(f).catch(err=>{$('gdsum').innerHTML='<span style="color:#c92a2a">'+esc(err.message)+'</span>';try{schMsg(esc(err.message),1);}catch(_){}});};gpUi();}}}catch(e){console.warn('gp',e);}return r;};}
/* jendela Block model ditutup saat digit / memilih → mode dihentikan; status selalu mengikuti keadaan */
setInterval(()=>{try{if(GP.on||GP.pk){const w=$('bmw');if(!w||w.style.display==='none'){if(GP.on)gpEnd(false);gpPkEnd();}}gpUi();}catch(_){}},1000);
try{window.__PS3.gp={set:P=>{GP.act=P&&P.length>=3?[{r:P.map(p=>[p[0],p[1]]),lab:'poligon',src:'api'}]:[];gpSync(false);},imp:f=>gpImport(f),get:()=>GT.poly,st:()=>({on:GP.on,n:GP.pts.length,pk:GP.pk,act:GP.act.map(a=>a.lab),set:GP.set.length,out:!!GT.polyOut,busy:!!GP.run,hov:GP.hov?(GP.hov.bad?'bad':GP.hov.lab):null}),start:gpStart,end:gpEnd,pick:gpPk,pickEnd:gpPkEnd,out:b=>{GT.polyOut=!!b;gpSync();},px:(x,y,z)=>gpPx(x,y,z),z:gpZ,area:gpArea};}catch(_){}
