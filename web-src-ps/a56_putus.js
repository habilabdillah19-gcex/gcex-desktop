/* a56: Putus INSTAN (23 Nov). Tombol "Putus" kini menyalakan mode putus: klik di ruas string mana pun (tidak perlu memilih
   string / titik dulu) → ruas itu dihapus seketika (garis jadi dua; poligon terbuka). Mode tetap aktif untuk memutus ruas lain;
   keluar = klik tombol Putus lagi atau Esc. Ruas di bawah kursor disorot merah. Ctrl+Z membatalkan seperti biasa. */
const PUT={on:false,hl:null};
function putSeg(e){const S=mwS(),r=R.domElement.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let b=null,bd=12;
 S.forEach((s,si)=>{let pa=null;s.pts.forEach((p,vi)=>{const q=scr(p[0],p[1],p[2]);if(pa&&q[2]<1&&pa[2]<1){const dx=q[0]-pa[0],dy=q[1]-pa[1],L2=dx*dx+dy*dy||1,t=Math.max(0,Math.min(1,((mx-pa[0])*dx+(my-pa[1])*dy)/L2)),d=Math.hypot(mx-pa[0]-dx*t,my-pa[1]-dy*t);if(d<bd){bd=d;b={si,i:vi-1};}}pa=q;});});return b;}
function putHl(h){if(PUT.hl){try{G.mw.remove(PUT.hl);clr(PUT.hl);}catch(_){}PUT.hl=null;}if(!h)return;const s=mwS()[h.si];if(!s)return;const a=s.pts[h.i],b=s.pts[h.i+1];if(!a||!b)return;
 try{PUT.hl=lineObj([a,b],0xe03131);if(PUT.hl.material){PUT.hl.material.depthTest=false;PUT.hl.renderOrder=99;}G.mw.add(PUT.hl);}catch(_){}}
function putCut(h){const S=mwS(),s=S[h.si],L=mwL(),i=h.i;
 if(s.closed){const P=openPts(s),m=P.length,R2=[];for(let k=1;k<=m;k++)R2.push(P[(i+k)%m].slice());L[h.si]=R2;mwApply(L,'Putus poligon (ruas '+(i+1)+')',[]);}
 else{const A=s.pts.slice(0,i+1).map(p=>p.slice()),B=s.pts.slice(i+1).map(p=>p.slice()),out=[];L.forEach((q,k)=>{if(k!==h.si){out.push(q);return;}if(A.length>=2)out.push(A);if(B.length>=2)out.push(B);});mwApply(out,'Putus garis (ruas '+(i+1)+')',[]);}}
function putSet(on){PUT.on=!!on;putHl(null);try{cv.style.cursor=on?'crosshair':'';}catch(_){}document.querySelectorAll('button.tb').forEach(b=>{if(/Putus/.test(b.textContent))b.classList.toggle('on',PUT.on);});
 if(on){try{MWS.ppick=null;MWS.pick=false;}catch(_){}try{mwInfo('<b>Mode Putus</b>: klik ruas string yang ingin diputus (disorot merah). Klik tombol Putus lagi / Esc = selesai.','warn');}catch(_){}}else{try{mwInfo();}catch(_){}}}
MWOP.brk=function(){needED();putSet(!PUT.on);};
{const _ec=window.edClick;window.edClick=e=>{if(PUT.on&&ED&&MODE==='edit'){const h=putSeg(e);if(!h){try{mwInfo('Klik lebih dekat ke ruas string.','warn');}catch(_){}return;}putHl(null);try{putCut(h);}catch(err){try{mwAfter('&#9888; '+esc(err.message),'warn');}catch(_){}}try{cv.style.cursor='crosshair';}catch(_){}return;}return _ec&&_ec(e);};}
(function(){let t0=0;R.domElement.addEventListener('pointermove',e=>{if(!PUT.on||MODE!=='edit'||!ED)return;const n=performance.now();if(n-t0<40)return;t0=n;const h=putSeg(e),k=h?h.si+':'+h.i:'';if(k!==PUT.k){PUT.k=k;putHl(h);}});
 addEventListener('keydown',e=>{if(e.key==='Escape'&&PUT.on){putSet(false);}},true);
 setInterval(()=>{if(PUT.on&&(MODE!=='edit'||!ED))putSet(false);},500);})();
try{window.__PS3.put={on:v=>putSet(v),seg:h=>putCut(h),st:()=>PUT.on,w:(si,i)=>mwS()[si].pts[i],near:(si,j)=>{const S=mwS(),p=S[si].pts[j<0?S[si].pts.length-1:j];let b=[1e9,-1,-1];S.forEach((s,i)=>s.pts.forEach((q,k)=>{if(i===si)return;if(Math.abs(q[2]-p[2])>0.6)return;const d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<b[0])b=[+d.toFixed(2),i,k,s.closed,s.pts.length,S[i].t];}));return b;},n:()=>mwS().map(s=>s.pts.length+(s.closed?'c':'o')).join(' '),mid:(si,i)=>{const s=mwS()[si],a=s.pts[i],b=s.pts[i+1],q=scr((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2),r=R.domElement.getBoundingClientRect();return [q[0]+r.left,q[1]+r.top,q[2]];}};}catch(_){}
/* Ujung string terbuka selalu terlihat (pemilik: "seolah-olah terhubung, padahal terputus"):
   (1) string terpilih di Edit titik: kedua ujungnya diberi tanda merah besar + label "ujung";
   (2) Sorot ujung lepas kini MENYALA bawaan di mode Edit (titik merah di setiap ujung yang tidak tersambung). */
try{MWS.loose=true;const c=$('mwlo');if(c)c.checked=true;}catch(_){}
{const _d=window.edDraw;window.edDraw=function(){const r=_d&&_d.apply(this,arguments);try{if(!ED||ED.sel<0||ED.out)return r;const s=ED.base.S[ED.sel];if(!s||s.closed||s.pts.length<2)return r;
 const E=[s.pts[0],s.pts[s.pts.length-1]],g=new THREE.BufferGeometry().setFromPoints(E.map(p=>V(p[0],p[1],(s.flat&&s.pure?s.z:p[2])+0.3)));const m=new THREE.Points(g,new THREE.PointsMaterial({color:'#e03131',size:16,sizeAttenuation:false,depthTest:false}));m.renderOrder=15;G.edit.add(m);
 E.forEach((p,k)=>{try{const sp=sprite(k?'ujung akhir':'ujung awal','#e03131',0.016,V(p[0],p[1],(s.flat&&s.pure?s.z:p[2])+2.5));sp.renderOrder=15;if(sp.material)sp.material.depthTest=false;G.edit.add(sp);}catch(_){}});
 const gap=Math.hypot(E[0][0]-E[1][0],E[0][1]-E[1][1]);try{const el=$('eseli');if(el&&!/celah ujung/.test(el.innerHTML))el.insertAdjacentHTML('beforeend',' · <span style="color:#e03131">terbuka, celah ujung '+gap.toFixed(1)+' m</span>');}catch(_){}}catch(e){console.warn('ujung',e);}return r;};}
/* putus saat ada revisi belum diterima: terima dulu supaya yang diputus = yang tampil */
{const _c=putCut;putCut=function(h){try{if(ED&&ED.out){EH.next='Hasil diterima';edAccept();}}catch(_){}return _c.apply(this,arguments);};}
/* Sorot string di bawah kursor (mode Edit): seluruh string disorot cyan + kedua ujungnya (bila terbuka), supaya terlihat
   jelas string mana yang benar-benar tersambung — garis string lain yang lewat di celah tidak lagi tampak "menyambung". */
const HOV={g:null,k:''};
function hovClr(){if(HOV.g){HOV.g.parent&&HOV.g.parent.remove(HOV.g);clr(HOV.g);HOV.g=null;}HOV.k='';try{const t=$('hovtip');if(t)t.style.display='none';}catch(_){}}
(function(){let t0=0;const tip=document.createElement('div');tip.id='hovtip';tip.style.cssText='position:fixed;z-index:60;pointer-events:none;background:#1f2a37;color:#fff;font:11.5px system-ui;padding:3px 7px;border-radius:4px;display:none;white-space:nowrap';document.body.appendChild(tip);
 R.domElement.addEventListener('pointermove',e=>{if(MODE!=='edit'||!ED||PUT.on||e.buttons){if(HOV.k)hovClr();return;}const n=performance.now();if(n-t0<60)return;t0=n;
  let S,i=-1;try{S=mwS();i=nearStr(e,S,false,9);}catch(_){i=-1;}if(i<0){if(HOV.k)hovClr();return;}const s=S[i],k=i+':'+s.pts.length;
  tip.innerHTML='String '+(i+1)+' · '+(s.closed?'poligon tertutup':'<b style="color:#ffa8a8">garis terbuka</b>')+' · '+s.pts.length+' titik · RL '+f1(s.flat?s.z:s.pts[0][2]);tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+12)+'px';tip.style.display='';
  if(k===HOV.k)return;hovClr();HOV.k=k;tip.style.display='';const g=new THREE.Group();g.renderOrder=16;
  const o=lineObj(s.pts.map(p=>[p[0],p[1],p[2]+0.25]),'#15aabf',false,{depthTest:false});o.renderOrder=16;g.add(o);
  if(!s.closed){const E=[s.pts[0],s.pts[s.pts.length-1]],gg=new THREE.BufferGeometry().setFromPoints(E.map(p=>V(p[0],p[1],p[2]+0.3)));const m=new THREE.Points(gg,new THREE.PointsMaterial({color:'#e03131',size:14,sizeAttenuation:false,depthTest:false}));m.renderOrder=17;g.add(m);}
  W.add(g);HOV.g=g;});
 R.domElement.addEventListener('pointerleave',()=>hovClr());})();
/* SAMBUNG INSTAN (pemilik 23 Nov: "setelah string diputus segmen, dia tidak dapat digabungkan").
   Sebab: poligon yang diputus menjadi SATU garis terbuka; Sambung lama mewajibkan DUA string terpilih → galat "Pilih dua string".
   Kini tombol Sambung:
   - 2 string terpilih → sambung A + B seperti biasa;
   - 1 garis terbuka terpilih → kedua ujungnya disambung kembali (jadi poligon);
   - tidak ada pilihan → MODE SAMBUNG: klik ujung string pertama, lalu ujung string kedua (atau ujung lain string yang sama)
     → langsung tersambung. Ujung terpilih ditandai; mode tetap aktif; Esc / klik Sambung lagi = selesai. */
const SMB={on:false,a:null,g:null};
function smbEndHit(e){const S=mwS();let i=-1;try{i=nearStr(e,S,false,14);}catch(_){}if(i<0)return null;const s=S[i];if(s.closed)return {i,closed:true};
 const r=R.domElement.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,E=[0,s.pts.length-1].map(j=>{const p=s.pts[j],q=scr(p[0],p[1],p[2]);return {j,d:Math.hypot(q[0]-mx,q[1]-my)};}).sort((a,b)=>a.d-b.d);return {i,j:E[0].j};}
function smbMark(){if(SMB.g){SMB.g.parent&&SMB.g.parent.remove(SMB.g);clr(SMB.g);SMB.g=null;}if(!SMB.on||!SMB.a)return;const s=mwS()[SMB.a.i];if(!s)return;const p=s.pts[SMB.a.j],g=new THREE.Group();
 const m=new THREE.Points(new THREE.BufferGeometry().setFromPoints([V(p[0],p[1],p[2]+0.35)]),new THREE.PointsMaterial({color:'#7048e8',size:18,sizeAttenuation:false,depthTest:false}));m.renderOrder=18;g.add(m);
 const o=lineObj(s.pts.map(q=>[q[0],q[1],q[2]+0.2]),'#7048e8',false,{depthTest:false});o.renderOrder=17;g.add(o);try{const sp=sprite('ujung 1','#7048e8',0.016,V(p[0],p[1],p[2]+2.5));sp.renderOrder=18;if(sp.material)sp.material.depthTest=false;g.add(sp);}catch(_){}W.add(g);SMB.g=g;}
function smbSet(on){SMB.on=!!on;SMB.a=null;smbMark();if(on){try{putSet(false);}catch(_){}}try{cv.style.cursor=on?'crosshair':'';}catch(_){}
 document.querySelectorAll('button.tb').forEach(b=>{if(/Sambung/.test(b.textContent))b.classList.toggle('on',SMB.on);});
 if(on){try{mwInfo('<b>Mode Sambung</b>: klik dekat <b>ujung</b> string pertama, lalu dekat ujung string kedua (atau ujung lain string yang sama untuk menutup poligon). Esc = selesai.','warn');}catch(_){}}else{try{mwInfo();}catch(_){}}}
function smbJoin(a,b){const S=mwS(),L=mwL();
 if(a.i===b.i){const s=S[a.i];if(s.pts.length<3)throw new Error('String terlalu pendek untuk ditutup.');const P=s.pts.map(p=>p.slice()),gap=Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1]);L[a.i]=closeIt(P);mwApply(L,'Sambung kembali kedua ujung (celah '+f1(gap)+' m) → poligon',[a.i]);return;}
 let A=S[a.i].pts.map(p=>p.slice()),B=S[b.i].pts.map(p=>p.slice());if(a.j===0)A.reverse();if(b.j!==0)B.reverse();/* ujung yang DIKLIK yang disambung */
 const gap=Math.hypot(A[A.length-1][0]-B[0][0],A[A.length-1][1]-B[0][1]);if(gap<0.05)B.shift();let J=A.concat(B),cl='';const tol=+$('mwtol').value||1;
 if(J.length>3&&Math.hypot(J[0][0]-J[J.length-1][0],J[0][1]-J[J.length-1][1])<=tol){J[J.length-1]=J[0].slice();cl=' dan ditutup menjadi poligon';}
 L[a.i]=J;L.splice(b.i,1);mwApply(L,'Sambung 2 string (celah '+f1(gap)+' m)'+cl,[a.i>b.i?a.i-1:a.i]);}
{const _j=MWOP.join;MWOP.join=function(){needED();const S=mwS();
 if(MWS.sel.length>=2){if(MWS.sel[0]===MWS.sel[1])throw new Error('String A dan B sama — untuk menyambung kedua ujungnya pilih satu string saja lalu klik Sambung.');return _j.apply(this,arguments);}
 if(MWS.sel.length===1){const i=MWS.sel[0],s=S[i];if(s&&!s.closed){smbJoin({i,j:0},{i,j:s.pts.length-1});return;}}
 smbSet(!SMB.on);};}
{const _ec=window.edClick;window.edClick=e=>{if(SMB.on&&ED&&MODE==='edit'){const h=smbEndHit(e);if(!h){try{mwInfo('Klik lebih dekat ke ujung string.','warn');}catch(_){}return;}
  if(h.closed){try{mwInfo('String itu poligon tertutup — tidak punya ujung. Putus dulu bila ingin disambung ke string lain.','warn');}catch(_){}return;}
  if(!SMB.a){SMB.a=h;smbMark();try{mwInfo('Ujung 1 dipilih. Klik ujung string kedua (atau ujung lain string ini untuk menutup poligon).','warn');}catch(_){}return;}
  if(SMB.a.i===h.i&&SMB.a.j===h.j){try{mwInfo('Itu ujung yang sama — klik ujung lainnya.','warn');}catch(_){}return;}
  const a=SMB.a;SMB.a=null;smbMark();try{smbJoin(a,h);}catch(err){try{mwAfter('&#9888; '+esc(err.message),'warn');}catch(_){}}try{cv.style.cursor='crosshair';}catch(_){}return;}return _ec&&_ec(e);};}
addEventListener('keydown',e=>{if(e.key==='Escape'&&SMB.on)smbSet(false);},true);
setInterval(()=>{if(SMB.on&&(MODE!=='edit'||!ED))smbSet(false);},500);
{const _p=putSet;putSet=function(on){if(on&&SMB.on){SMB.on=false;SMB.a=null;smbMark();document.querySelectorAll('button.tb').forEach(b=>{if(/Sambung/.test(b.textContent))b.classList.remove('on');});}return _p.apply(this,arguments);};}
try{Object.assign(window.__PS3.put,{smb:v=>smbSet(v),smbSt:()=>SMB.on,vx:(si,i)=>{const p=mwS()[si].pts[i<0?mwS()[si].pts.length+i:i],q=scr(p[0],p[1],p[2]),r=R.domElement.getBoundingClientRect();return [q[0]+r.left,q[1]+r.top,q[2]];}});}catch(_){}
/* alat lain dimulai → mode Putus / Sambung dimatikan (dulu klik alat Potong / Luruskan tertangkap mode Sambung) */
function modeOff(keepPD){try{if(!keepPD&&PD.arm&&!PD.drag){pdArm(false);pdInfo('');}}catch(_){}try{if(MVX.on)mvToggle(false);}catch(_){}try{if(SMB.on)smbSet(false);}catch(_){}try{if(PUT.on)putSet(false);}catch(_){}}
{const _m=mwPickPoint;mwPickPoint=function(){modeOff();return _m.apply(this,arguments);};}
{const _p=pickToggle;pickToggle=function(){modeOff();return _p.apply(this,arguments);};}
try{const _mv=mvToggle;mvToggle=function(on){if(on)modeOff();return _mv.apply(this,arguments);};}catch(_){}
/* celah sambung besar (> 50 m) → minta konfirmasi; hampir pasti salah klik */
{const _s=smbJoin;smbJoin=function(a,b){const S=mwS(),A=S[a.i].pts[a.j],B=S[b.i].pts[b.j],g=Math.hypot(A[0]-B[0],A[1]-B[1]);if(g>50&&!confirm('Kedua ujung berjarak '+f1(g)+' m. Tetap sambung?'))return;return _s.apply(this,arguments);};}
/* satu alat aktif pada satu waktu: menekan tombol alat lain mematikan mode Putus / Sambung / kuas Dorong-Tarik / Pindah titik */
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('button.tb,.mwm button,.mwi,[data-mwk],#esel,#pdgo');if(!b)return;const t=b.textContent;
 if(/Putus/.test(t)){try{if(PD.arm)pdArm(false);if(MVX.on)mvToggle(false);}catch(_){}return;}if(/Sambung/.test(t)){try{if(PD.arm)pdArm(false);if(MVX.on)mvToggle(false);}catch(_){}return;}
 if(/Dorong|Tarik/.test(t)||b.id==='pdgo'){if(SMB.on)smbSet(false);if(PUT.on)putSet(false);try{if(MVX.on)mvToggle(false);}catch(_){}return;}
 if(/Snap/.test(t)){if(SMB.on)smbSet(false);if(PUT.on)putSet(false);try{if(PD.arm)pdArm(false);}catch(_){}return;}
 modeOff();},true);
/* tombol Dorong / Tarik = sakelar: klik lagi saat kuas jenis yang sama aktif → selesai */
{const _ps=pdStart;pdStart=function(kind){try{if(PD.arm&&$('pdm').value===kind){pdArm(false);pdInfo('');tbState&&setTimeout(tbState,30);return;}}catch(_){}const r=_ps.apply(this,arguments);try{setTimeout(tbState,30);}catch(_){}return r;};}
{const a=putSet;putSet=function(){const r=a.apply(this,arguments);try{setTimeout(tbState,20);}catch(_){}return r;};}
{const a=smbSet;smbSet=function(){const r=a.apply(this,arguments);try{setTimeout(tbState,20);}catch(_){}return r;};}
{const a=pdArm;pdArm=function(){const r=a.apply(this,arguments);try{setTimeout(tbState,20);}catch(_){}return r;};}
