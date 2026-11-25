/* a81 · (24 Nov 2026, pemilik)
   A) POSISI SAYATAN DI 3D — empat pilihan, SEMUA MATI bawaan ("Keempatnya mati saja default"), tombol di jendela Sayatan:
      1 Bidang 3D   : tirai tegak semi-transparan sepanjang A→B + label A / B (juga centang "Sayatan · bidang" di Lapisan)
      2 Peta kunci  : denah kecil di pojok gambar sayatan (string desain, garis A–B, arah utara) — ikut tercetak di PNG
      3 Kursor 3D   : kursor di sayatan → penanda di posisi yang sama di 3D (jarak dari A · RL)
      4 Lihat di 3D : kamera tegak lurus bidang sayatan, model di depan bidang dipotong; klik lagi = kembali
   B) DATA IMPOR DI PANEL LAPISAN — dulu hanya topografi yang tercatat. Kini pit final impor tampil & tercatat di semua mode
      (bukan hanya Staging), dan block model punya baris sendiri (centang = tampilkan Block model 3D). */
const SYX={plane:false,key:false,cur:false,cut:false,fin:true};try{const o=JSON.parse(localStorage.getItem('psSayX')||'{}');for(const k of ['plane','key','cur','fin'])if(k in o)SYX[k]=!!o[k];}catch(_){}
function syxSave(){try{localStorage.setItem('psSayX',JSON.stringify({plane:SYX.plane,key:SYX.key,cur:SYX.cur,fin:SYX.fin}));}catch(_){}}
function syxOpen(){const w=$('sayw');return !!(w&&w.style.display==='flex'&&SAY.a);}
function syxZ(L){let lo=1e9,hi=-1e9;const n=40;for(let i=0;i<=n;i++){const t=i/n,z=topoZ(L.a[0]+(L.b[0]-L.a[0])*t,L.a[1]+(L.b[1]-L.a[1])*t);if(isFinite(z)){lo=Math.min(lo,z);hi=Math.max(hi,z);}}
 try{const R0=curR();if(R0&&isFinite(R0.zmin))lo=Math.min(lo,R0.zmin);}catch(_){}try{if(FIN&&isFinite(FIN.zmin))lo=Math.min(lo,FIN.zmin);}catch(_){}
 if(!(hi>lo)){lo=0;hi=100;}return [lo-10,hi+12];}
/* 1 · bidang */
function syxPlane(){if(!G.sayp){G.sayp=new THREE.Group();W.add(G.sayp);}clr(G.sayp);if(!SYX.plane||!syxOpen())return;const L=sayGeo();if(!L)return;const [z0,z1]=syxZ(L);
 const P=[V(L.a[0],L.a[1],z0),V(L.b[0],L.b[1],z0),V(L.b[0],L.b[1],z1),V(L.a[0],L.a[1],z1)],pos=[];for(const q of [0,1,2,0,2,3])pos.push(P[q].x,P[q].y,P[q].z);
 const bg=new THREE.BufferGeometry();bg.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));const me=new THREE.Mesh(bg,new THREE.MeshBasicMaterial({color:0xe8590c,transparent:true,opacity:SYX.cut?0.06:0.2,side:THREE.DoubleSide,depthWrite:false}));me.renderOrder=7;G.sayp.add(me);
 const o=lineObj([[L.a[0],L.a[1],z0],[L.b[0],L.b[1],z0],[L.b[0],L.b[1],z1],[L.a[0],L.a[1],z1]],'#e8590c',true,{transparent:true,opacity:.9});o.renderOrder=8;G.sayp.add(o);
 for(const [p,t,c] of [[L.a,'A','#e8590c'],[L.b,'B','#1b2a4e']]){try{const s=sprite(t,c,0.03,V(p[0],p[1],z1+6));s.renderOrder=9;if(s.material)s.material.depthTest=false;G.sayp.add(s);}catch(_){}}}
/* 2 · peta kunci (digambar di kanvas sayatan → ikut PNG) */
function syxKey(){if(!SYX.key||!syxOpen())return;const L=sayGeo(),cv2=$('saycv');if(!L||!cv2||!SAY.pw)return;const g=cv2.getContext('2d'),w=Math.min(170,Math.max(120,SAY.pw*0.24)),h=w*0.82,x0=SAY.ml+SAY.pw-w-8,y0=SAY.mt+SAY.ph-h-8;
 const S=[];try{const R0=curR();if(R0&&R0.S)for(const s of R0.S)if(s.pts&&s.pts.length>2&&(s.t==='crest'||s.t==='toe'||!s.t))S.push(s.pts);}catch(_){}try{if(!S.length&&FIN&&FIN.S)for(const s of FIN.S)S.push(s.pts);}catch(_){}
 let ax=Math.min(L.a[0],L.b[0]),bx=Math.max(L.a[0],L.b[0]),ay=Math.min(L.a[1],L.b[1]),by=Math.max(L.a[1],L.b[1]);for(const s of S)for(const p of s){if(p[0]<ax)ax=p[0];if(p[0]>bx)bx=p[0];if(p[1]<ay)ay=p[1];if(p[1]>by)by=p[1];}
 const pad=12,hd=13,k=Math.min((w-2*pad)/Math.max(1,bx-ax),(h-2*pad-hd)/Math.max(1,by-ay)),cx=(ax+bx)/2,cy=(ay+by)/2,X=e=>x0+w/2+(e-cx)*k,Y=n=>y0+hd+(h-hd)/2-(n-cy)*k;
 g.save();g.fillStyle='rgba(247,245,240,.96)';g.fillRect(x0,y0,w,h);g.strokeStyle='#1C2733';g.lineWidth=1;g.strokeRect(x0+.5,y0+.5,w,h);g.fillStyle='#1C2733';g.font='bold 9px system-ui,Arial';g.fillText('PETA KUNCI',x0+6,y0+11);
 g.beginPath();g.rect(x0+1,y0+hd,w-2,h-hd-1);g.clip();g.strokeStyle='#c0392b';g.lineWidth=0.7;for(const s of S){const st=Math.max(1,Math.floor(s.length/120));g.beginPath();for(let i=0;i<s.length;i+=st){const p=s[i];if(i===0)g.moveTo(X(p[0]),Y(p[1]));else g.lineTo(X(p[0]),Y(p[1]));}g.stroke();}
 if(!S.length){g.fillStyle='#868e96';g.font='9px system-ui,Arial';g.fillText('(belum ada desain)',x0+6,y0+h-6);}
 g.strokeStyle='#e8590c';g.lineWidth=2;g.beginPath();g.moveTo(X(L.a[0]),Y(L.a[1]));g.lineTo(X(L.b[0]),Y(L.b[1]));g.stroke();g.font='bold 11px system-ui,Arial';g.fillStyle='#e8590c';g.fillText('A',X(L.a[0])-10,Y(L.a[1])+4);g.fillStyle='#1b2a4e';g.fillText('B',X(L.b[0])+4,Y(L.b[1])+4);g.restore();
 /* arah utara */const nx=x0+w-12,ny=y0+hd+20;g.save();g.strokeStyle='#1C2733';g.fillStyle='#1C2733';g.lineWidth=1.3;g.beginPath();g.moveTo(nx,ny+9);g.lineTo(nx,ny-9);g.moveTo(nx-4,ny-3);g.lineTo(nx,ny-10);g.lineTo(nx+4,ny-3);g.stroke();g.font='bold 9px system-ui,Arial';g.fillText('U',nx-3,ny+19);g.restore();}
/* 3 · kursor terhubung */
function syxCur(e){if(!G.sayc){G.sayc=new THREE.Group();W.add(G.sayc);}clr(G.sayc);if(!e||!SYX.cur||!syxOpen()||!SAY.view||!SAY.pw)return;const L=sayGeo(),cv2=$('saycv');if(!L)return;const r=cv2.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
 if(mx<SAY.ml||mx>SAY.ml+SAY.pw||my<SAY.mt||my>SAY.mt+SAY.ph)return;const [s,z]=sayInv(mx,my);if(s<0||s>L.L)return;const E=L.a[0]+L.ux*s,N=L.a[1]+L.uy*s,[z0,z1]=syxZ(L);
 const v=lineObj([[E,N,z0],[E,N,z1]],'#1C2733',false,{depthTest:false,transparent:true,opacity:.8});v.renderOrder=9;G.sayc.add(v);
 const rad=Math.max(1.2,L.L/140),m=new THREE.Mesh(new THREE.SphereGeometry(rad,14,10),new THREE.MeshBasicMaterial({color:0xffd43b,depthTest:false}));m.position.copy(V(E,N,z));m.renderOrder=10;G.sayc.add(m);
 try{const sp=sprite('jarak '+nf(s)+' m · RL '+f1(z),'#1C2733',0.018,V(E,N,z1+3));sp.renderOrder=10;if(sp.material)sp.material.depthTest=false;G.sayc.add(sp);}catch(_){}}
/* 4 · lihat di 3D (potong di bidang) */
function syxCut(on){SYX.cut=!!on;try{if(SYX.cut){const L=sayGeo();if(!L){SYX.cut=false;return;}if(!SYX._cam)SYX._cam={p:C.position.clone(),t:CT.target.clone(),u:C.up.clone()};const [z0,z1]=syxZ(L),pa=V(L.a[0],L.a[1],(z0+z1)/2),pb=V(L.b[0],L.b[1],(z0+z1)/2);pa.y*=W.scale.y||1;pb.y*=W.scale.y||1;
   const mid=pa.clone().add(pb).multiplyScalar(.5),dir=pb.clone().sub(pa).normalize(),f=new THREE.Vector3(0,1,0).cross(dir).normalize(),asp=(R.domElement.clientWidth||1)/(R.domElement.clientHeight||1),D=Math.max(L.L*0.56/asp,(z1-z0)*(W.scale.y||1)*0.62)/Math.tan((C.fov||45)*Math.PI/360);
   CT.target.copy(mid);C.position.copy(mid).addScaledVector(f,-D);C.up.set(0,1,0);C.updateProjectionMatrix();CT.update();R.clippingPlanes=[new THREE.Plane(f.clone(),-f.dot(mid)+0.05)];}
  else{R.clippingPlanes=[];if(SYX._cam){C.position.copy(SYX._cam.p);CT.target.copy(SYX._cam.t);C.up.copy(SYX._cam.u);C.updateProjectionMatrix();CT.update();SYX._cam=null;}}}catch(e){console.warn('syx cut',e);SYX.cut=false;try{R.clippingPlanes=[];}catch(_){}}
 syxPlane();syxUi();}
function syxUi(){const w=$('sayw');if(!w)return;let b=$('syxb');if(!b){const sb=$('sayb');if(!sb)return;b=document.createElement('span');b.id='syxb';b.style.cssText='display:inline-flex;gap:3px;align-items:center;margin-left:6px;padding-left:8px;border-left:1px solid #c9d3e1';
   b.innerHTML='<span style="font-size:11px;color:#6c757d">di 3D:</span>'+[['plane','&#9645; Bidang','Tampilkan bidang sayatan (tirai tegak A→B) di tampilan 3D'],['key','&#9635; Peta kunci','Denah kecil di pojok gambar sayatan: desain, garis A–B, arah utara — ikut tercetak di PNG'],['cur','&#8982; Kursor','Kursor di gambar sayatan ikut ditandai di posisi yang sama di 3D (jarak dari A · RL)'],['cut','&#9986; Lihat di 3D','Kamera menghadap tegak lurus bidang sayatan dan model di depannya dipotong; klik lagi = kembali']].map(x=>'<button data-sx="'+x[0]+'" title="'+x[2]+'">'+x[1]+'</button>').join('');
   sb.appendChild(b);b.addEventListener('click',e=>{const t=e.target.closest('[data-sx]');if(!t)return;const k=t.dataset.sx;if(k==='cut'){syxCut(!SYX.cut);return;}SYX[k]=!SYX[k];syxSave();if(k==='plane')syxPlane();if(k==='key')sayDraw();if(k==='cur'&&!SYX.cur)syxCur(null);syxUi();try{layRender();}catch(_){}});
   const cv2=$('saycv');if(cv2){cv2.addEventListener('mousemove',e=>{if(SYX.cur)syxCur(e);});cv2.addEventListener('mouseleave',()=>syxCur(null));}}
 for(const t of b.querySelectorAll('[data-sx]'))t.classList.toggle('on',!!SYX[t.dataset.sx]);}
{const _d=sayDraw;sayDraw=function(){const r=_d.apply(this,arguments);try{syxKey();}catch(e){console.warn('syx key',e);}return r;};}
{const _l=sayLine3D;sayLine3D=function(tmp){const r=_l.apply(this,arguments);try{if(!tmp){syxPlane();if(SYX.cut)syxCut(true);}}catch(e){console.warn('syx',e);}return r;};}
/* jendela Sayatan ditutup → potongan & penanda dilepas */
setInterval(()=>{try{syxUi();if(!syxOpen()){if(SYX.cut)syxCut(false);if(G.sayp&&G.sayp.children.length)clr(G.sayp);if(G.sayc&&G.sayc.children.length)clr(G.sayc);}else if(SYX.plane&&G.sayp&&!G.sayp.children.length)syxPlane();}catch(_){}},800);

/* ---------- B. data impor di panel Lapisan ---------- */
function finxDraw(){if(!G.finx){G.finx=new THREE.Group();W.add(G.finx);}const sig=FIN?(FIN.nm+'|'+FIN.S.length+'|'+MODE+'|'+SYX.fin):'';if(G.finx.userData.sig===sig)return;G.finx.userData.sig=sig;clr(G.finx);if(!FIN||MODE==='stage'||!SYX.fin)return;
 for(const s of FIN.S){const o=lineObj(s.pts.map(p=>[p[0],p[1],p[2]+0.05]),COL.fin||'#7048e8',false,{transparent:true,opacity:.55});o.renderOrder=2;G.finx.add(o);}}
{const _l=window.layRender;window.layRender=function(){const r=_l.apply(this,arguments);try{const el=$('layb');if(!el)return r;const add=(nm,col,vis,set,del)=>{const d=document.createElement('div');d.className='lrow';d.innerHTML='<input type="checkbox"'+(vis?' checked':'')+'><i style="background:'+col+'"></i><span class="t" title="'+esc(nm)+'">'+esc(nm)+'</span>'+(del?'<button class="x" title="Hapus dari project">&#10005;</button>':'');d.querySelector('input').onchange=e=>set(e.target.checked);if(del)d.querySelector('button').onclick=del;
   /* setelah baris topografi */let ref=null;for(const c of el.children){if(c.classList.contains('lrow')&&/^Topografi|^Topography|^Topograf/.test((c.querySelector('.t')||{}).textContent||''))ref=c;}if(ref&&ref.nextSibling)el.insertBefore(d,ref.nextSibling);else el.appendChild(d);};
  try{if(GT.file)add('Block model · '+GT.file.name,'#ff1a1a',!!(B3.on&&B3.g&&LYX.b3!==false),v=>{try{LYX.b3=true;lyxSave();if(v)b3Show(true);else{b3Off();try{winShow($('b3w'),false);}catch(_){}}}catch(e){console.warn(e);}setTimeout(()=>{try{layRender();}catch(_){}},400);});}catch(_){}
  if(FIN&&MODE!=='stage')add('Pit final impor · '+String(FIN.nm||'').replace(/^[0-9a-f]{8}-/,''),COL.fin||'#7048e8',!!SYX.fin,v=>{SYX.fin=v;syxSave();finxDraw();},()=>{if(!confirm('Hapus pit final impor dari project?'))return;const d=$('sfdel');if(d)d.click();else{FIN=null;}finxDraw();try{layRender();}catch(_){}});
  if(syxOpen())add('Sayatan · bidang','#e8590c',!!SYX.plane,v=>{SYX.plane=v;syxSave();syxPlane();syxUi();});
 }catch(e){console.warn('lay data',e);}return r;};}
{let sig='';setInterval(()=>{try{finxDraw();const s=(FIN?FIN.nm:'')+'|'+(GT.file?GT.file.name:'')+'|'+MODE+'|'+(syxOpen()?1:0)+'|'+(B3.on?1:0);if(s!==sig){sig=s;layRender();}}catch(_){}},900);}
try{window.__PS3.syx={st:()=>({plane:SYX.plane,key:SYX.key,cur:SYX.cur,cut:SYX.cut,fin:SYX.fin}),set:(k,v)=>{if(k==='cut')syxCut(v);else{SYX[k]=!!v;syxSave();syxPlane();try{sayDraw();}catch(_){}syxUi();}},n:()=>[G.sayp?G.sayp.children.length:0,G.sayc?G.sayc.children.length:0,R.clippingPlanes?R.clippingPlanes.length:0,G.finx?G.finx.children.length:0]};}catch(_){}
