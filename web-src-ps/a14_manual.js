/* ===== a14: pengaman hasil edit (riwayat + simpan otomatis), Edit Manual (freehand), Play-Doh (kuas sapuan) — 16 Nov 2026 ===== */

/* ---------- 1. riwayat & simpan otomatis ---------- */
const EH={st:[],i:-1,busy:false,next:null};
function ehSnap(){return ED.base.S.map(s=>s.pts.map(p=>p.slice()));}
function ehPush(label){if(!ED||EH.busy)return;EH.st=EH.st.slice(0,EH.i+1);EH.st.push({label,L:ehSnap(),nm:ED.nm,t:Date.now()});if(EH.st.length>40)EH.st.shift();EH.i=EH.st.length-1;ehSave();ehUI();}
function ehGo(k){const h=EH.st[k];if(!h)return;EH.busy=true;try{if(ED)ED.out=null;edLoad(h.L.map(l=>l.map(p=>p.slice())),h.nm);}finally{EH.busy=false;}EH.i=k;ehSave();ehUI();try{pitRedraw();}catch(_){}mwAfter();}
{const _el=edLoad;edLoad=function(L,fn,R0){const r=_el.apply(this,arguments);if(!EH.busy){ehPush(EH.next||(R0?'Hasil diterima':'Dimuat: '+fn));}EH.next=null;return r;};}
function idb(){return new Promise((res,rej)=>{let q;try{q=indexedDB.open('pitstudio',1);}catch(e){rej(e);return;}q.onupgradeneeded=()=>q.result.createObjectStore('kv');q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error);});}
async function kvSet(k,v){const d=await idb();return new Promise((res,rej)=>{const t=d.transaction('kv','readwrite');t.objectStore('kv').put(v,k);t.oncomplete=()=>res();t.onerror=()=>rej(t.error);});}
async function kvGet(k){const d=await idb();return new Promise((res,rej)=>{const t=d.transaction('kv','readonly'),q=t.objectStore('kv').get(k);q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error);});}
async function kvDel(k){const d=await idb();return new Promise(res=>{const t=d.transaction('kv','readwrite');t.objectStore('kv').delete(k);t.oncomplete=()=>res();});}
let EH_SAVED=null;
function ehSave(){clearTimeout(ehSave.t);ehSave.t=setTimeout(()=>{const h=EH.st[EH.i];if(!h)return;kvSet('edit',{label:h.label,nm:h.nm,t:h.t,L:h.L}).then(()=>{EH_SAVED=Date.now();ehUI();}).catch(e=>{console.warn('simpan otomatis',e);EH_SAVED=-1;ehUI();});},400);}
const tFmt=t=>{const d=new Date(t);return d.toLocaleDateString('id-ID')+' '+d.toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'});};
function ehUI(){const el=$('ehbar');if(!el)return;if(!ED||!EH.st.length){el.innerHTML='<span class="hint">Riwayat edit kosong. Setiap hasil yang diterima, alat Edit Manual, dan sapuan Play-Doh tersimpan otomatis di peramban ini.</span>';return;}
 const h=EH.st[EH.i];el.innerHTML='<div class="fl" style="margin:0;gap:4px"><button id="ehun" class="sm"'+(EH.i<=0?' disabled':'')+' title="Kembali satu langkah (Ctrl+Z)">&#8630; Batalkan</button><button id="ehre" class="sm"'+(EH.i>=EH.st.length-1?' disabled':'')+' title="Ulangi (Ctrl+Y)">&#8631; Ulangi</button><select id="ehsel" style="flex:1">'+EH.st.map((x,k)=>'<option value="'+k+'"'+(k===EH.i?' selected':'')+'>'+(k+1)+'. '+esc(x.label)+' · '+new Date(x.t).toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'})+'</option>').join('')+'</select><button id="ehpj" class="sm" title="Simpan project (.pit.json) berisi hasil edit yang tampil sekarang">&#128190;</button></div>'
  +'<div class="hint">Langkah '+(EH.i+1)+'/'+EH.st.length+': <b>'+esc(h.label)+'</b>'+(EH_SAVED>0?' · &#10003; tersimpan otomatis '+new Date(EH_SAVED).toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'}):EH_SAVED===-1?' · <span class="warn">simpan otomatis gagal — pakai &#128190;</span>':'')+(ED.out?' · <span class="warn">ada hasil yang belum diterima</span>':'')+'</div>';
 $('ehun').onclick=()=>ehGo(EH.i-1);$('ehre').onclick=()=>ehGo(EH.i+1);$('ehsel').onchange=e=>ehGo(+e.target.value);$('ehpj').onclick=()=>{const b=$('pjs');if(b)b.click();};}
async function ehRestoreOffer(){let v=null;try{v=await kvGet('edit');}catch(e){return;}const el=$('ehrest');if(!el)return;if(!v||!v.L||!v.L.length){el.hidden=true;return;}el.hidden=false;
 el.innerHTML='&#128190; Ada hasil edit tersimpan otomatis: <b>'+esc(v.nm||'pit')+'</b> — '+esc(v.label||'')+' ('+tFmt(v.t)+', '+v.L.length+' string). <a href="#" id="ehrok"><b>Pulihkan</b></a> · <a href="#" id="ehrno">Buang</a>';
 $('ehrok').onclick=e=>{e.preventDefault();try{if(MODE!=='edit')$('mode').querySelector('[data-m="edit"]').click();}catch(_){}try{setO(v.L[0][0]);}catch(_){}EH.next='Dipulihkan ('+(v.label||'')+')';edLoad(v.L,v.nm||'pulihan.str');el.hidden=true;try{pitRedraw();}catch(_){}};
 $('ehrno').onclick=e=>{e.preventDefault();kvDel('edit');el.hidden=true;};}
setTimeout(ehRestoreOffer,600);
/* edit titik di langkah 2 (seret / tambah / hapus titik / luruskan) → setelah Selesai seret, catat di riwayat */
$('edone').addEventListener('click',()=>{const was=ED&&ED.dirty;setTimeout(()=>{if(was&&ED&&!ED.out)ehPush('Edit titik string (langkah 2)');},60);},true);
addEventListener('beforeunload',e=>{if(ED&&ED.out){e.preventDefault();e.returnValue='';}});
addEventListener('keydown',e=>{if(MODE!=='edit'||!ED||/INPUT|SELECT|TEXTAREA/.test((e.target&&e.target.tagName)||''))return;if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&EH.i>0){e.preventDefault();ehGo(EH.i-1);}else if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'&&EH.i<EH.st.length-1){e.preventDefault();ehGo(EH.i+1);}});

/* ---------- 2. Edit Manual (freehand) ---------- */
G.mw=new THREE.Group();W.add(G.mw);
const MWS={sel:[],pick:false,ppick:null,pv:[],loose:false};
function mwS(){return ED?ED.base.S:[];}
function looseEnds(S,tol){tol=tol||1;const o=[];const H=new Map(),k=(x,y)=>Math.floor(x/4)+'_'+Math.floor(y/4);S.forEach((s,i)=>{for(let j=0;j<s.pts.length;j++){const p=s.pts[j],kk=k(p[0],p[1]);let a=H.get(kk);if(!a)H.set(kk,a=[]);a.push([i,j]);}});
 S.forEach((s,i)=>{if(s.closed||s.pts.length<2)return;for(const j of [0,s.pts.length-1]){const p=s.pts[j];let bd=1e9;const cx=Math.floor(p[0]/4),cy=Math.floor(p[1]/4);for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++){for(const [i2,j2] of (H.get((cx+dx)+'_'+(cy+dy))||[])){if(i2===i&&j2===j)continue;const q=S[i2].pts[j2];if(Math.abs(q[2]-p[2])>0.6)continue;if(i2===i&&Math.abs(j2-j)<2)continue;bd=Math.min(bd,Math.hypot(q[0]-p[0],q[1]-p[1]));}
   /* juga ke tengah ruas string lain */}
  if(bd>tol){for(let i2=0;i2<S.length&&bd>tol;i2++){if(i2===i)continue;const P=S[i2].pts;for(let m=1;m<P.length;m++){const a=P[m-1],b=P[m];if(Math.abs(a[2]-p[2])>0.6&&Math.abs(b[2]-p[2])>0.6)continue;const ex=b[0]-a[0],ey=b[1]-a[1],L2=ex*ex+ey*ey||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*ex+(p[1]-a[1])*ey)/L2)),d=Math.hypot(p[0]-a[0]-ex*t,p[1]-a[1]-ey*t);if(d<bd)bd=d;}}}
  if(bd>tol)o.push({i,j,p,d:bd});}});return o;}
function mwDraw(){clr(G.mw);if(!ED||MODE!=='edit')return;const S=mwS(),C=['#d6336c','#1c7ed6','#2b8a3e','#f08c00'];
 MWS.sel.forEach((i,k)=>{const s=S[i];if(!s)return;const o=lineObj(s.pts.map(p=>[p[0],p[1],p[2]+0.15]),C[k%4],false,{depthTest:false});o.renderOrder=11;G.mw.add(o);
  const g=new THREE.BufferGeometry().setFromPoints(s.pts.map(p=>V(p[0],p[1],p[2]+0.15)));const m=new THREE.Points(g,new THREE.PointsMaterial({color:C[k%4],size:6,sizeAttenuation:false,depthTest:false}));m.renderOrder=12;G.mw.add(m);
  const e0=s.pts[0];G.mw.add(sprite(k===0?'A':'B',C[k%4],0.022,V(e0[0],e0[1],e0[2]+2)));});
 for(const v of MWS.pv){const s=S[v.si];if(!s)continue;const p=s.pts[v.vi];const g=new THREE.BufferGeometry().setFromPoints([V(p[0],p[1],p[2]+0.2)]);const m=new THREE.Points(g,new THREE.PointsMaterial({color:'#000',size:11,sizeAttenuation:false,depthTest:false}));m.renderOrder=13;G.mw.add(m);}
 if(MWS.loose){const L=looseEnds(S,+$('mwtol').value||1);if(L.length){const g=new THREE.BufferGeometry().setFromPoints(L.map(x=>V(x.p[0],x.p[1],x.p[2]+0.3)));const m=new THREE.Points(g,new THREE.PointsMaterial({color:'#e03131',size:12,sizeAttenuation:false,depthTest:false}));m.renderOrder=14;G.mw.add(m);}}}
function mwInfo(msg,cls){const S=mwS();let h='';if(!ED){h='<span class="warn">Belum ada pit di tab Edit. Impor pit atau pakai hasil Desain baru dulu.</span>';}
 else{const LE=looseEnds(S,+$('mwtol').value||1);h='<b>Terpilih:</b> '+(MWS.sel.length?MWS.sel.map((i,k)=>{const s=S[i];if(!s)return '';let L=0;for(let j=1;j<s.pts.length;j++)L+=Math.hypot(s.pts[j][0]-s.pts[j-1][0],s.pts[j][1]-s.pts[j-1][1]);return '<b>'+(k?'B':'A')+'</b> '+(s.closed?'poligon':'garis')+' · '+s.pts.length+' titik · '+nf(L)+' m · RL '+(s.flat?f1(s.z):f1(Math.min(...s.pts.map(p=>p[2])))+'–'+f1(Math.max(...s.pts.map(p=>p[2]))));}).join('<br>'):'<span class="hint">belum ada — klik <b>Pilih string</b> lalu klik garis di 3D (Shift+klik = string kedua)</span>')
  +'<br><b>Ujung lepas</b> (celah &gt; '+f1(+$('mwtol').value||1)+' m): <span class="'+(LE.length?'warn':'ok')+'">'+LE.length+'</span>'+(LE.length?' <span class="hint">— centang Sorot untuk melihat, atau Perbaiki sambungan otomatis</span>':'');}
 if(msg)h='<div class="'+(cls||'ok')+'" style="margin-bottom:4px">'+msg+'</div>'+h;$('mwinf').innerHTML=h;}
function mwAfter(msg,cls){MWS.sel=MWS.sel.filter(i=>i<mwS().length);MWS.pv=[];mwDraw();mwInfo(msg,cls);}
/* terapkan daftar titik baru → bangun ulang string & permukaan, catat di riwayat */
function mwApply(L,label,newSel){if(ED.out){EH.next='Hasil diterima';edAccept();}EH.next=label;const nm=ED.nm;edLoad(L,nm);MWS.sel=newSel||[];try{pitRedraw();}catch(_){}mwAfter('&#10003; '+label);}
function mwNeed(n){if(!ED)throw new Error('Impor pit dulu di tab Edit.');if(MWS.sel.length<n)throw new Error(n===2?'Pilih dua string (klik, lalu Shift+klik string kedua).':'Pilih satu string dulu.');}
const mwL=()=>mwS().map(s=>s.pts.map(p=>p.slice()));
const openPts=s=>s.closed?s.pts.slice(0,-1).map(p=>p.slice()):s.pts.map(p=>p.slice());
const closeIt=P=>P.concat([P[0].slice()]);
function mwPickPoint(n,msg,cb,row,title){mwNeed(1);MWS.pick=true;MWS.pv=[];MWS.ppick={n,cb};cv.style.cursor='crosshair';mwShow(row||null,title);if(row)$('mwgo').hidden=true;mwInfo(msg,'warn');}
function mwClick(e){const S=mwS();if(MWS.ppick){/* titik pada string terpilih terdekat ke kursor */const r=R.domElement.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let b=null,bd=16;for(const si of MWS.sel){const s=S[si];s.pts.forEach((p,vi)=>{const q=scr(p[0],p[1],p[2]);if(q[2]>=1)return;const d=Math.hypot(q[0]-mx,q[1]-my);if(d<bd){bd=d;b={si,vi};}});}
  if(!b){mwInfo('Klik lebih dekat ke titik pada string terpilih (titik berwarna).','warn');return;}MWS.pv.push(b);mwDraw();if(MWS.pv.length>=MWS.ppick.n){const cb=MWS.ppick.cb,pv=MWS.pv.slice();MWS.ppick=null;MWS.pick=false;cv.style.cursor='';try{cb(pv);}catch(err){mwAfter('&#9888; '+esc(err.message),'warn');}}return;}
 let i=nearStr(e,S,false,14);if(i<0){mwInfo('Tidak ada string di dekat klik.','warn');return;}if(e.shiftKey||e.ctrlKey){if(MWS.sel.includes(i))MWS.sel=MWS.sel.filter(x=>x!==i);else MWS.sel=MWS.sel.slice(-1).concat([i]);}else MWS.sel=[i];mwDraw();mwInfo();}
{const _ec=window.edClick;window.edClick=e=>{if(MWS.pick&&ED&&MODE==='edit'){mwClick(e);return;}return _ec&&_ec(e);};}
function rdp3(P,tol){if(P.length<3)return P.slice();const k=rdpL(P,tol);return k;}
function offOpen(P,d){/* offset garis terbuka ke kiri (+) / kanan (−), sambungan miter dibatasi */const n=P.length,o=[];for(let i=0;i<n;i++){const a=P[Math.max(0,i-1)],b=P[Math.min(n-1,i+1)];let tx=b[0]-a[0],ty=b[1]-a[1],L=Math.hypot(tx,ty)||1;tx/=L;ty/=L;let nx=-ty,ny=tx,k=1;
  if(i>0&&i<n-1){const u=[P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]],l=Math.hypot(u[0],u[1])||1,n1=[-u[1]/l,u[0]/l],c=nx*n1[0]+ny*n1[1];k=1/Math.max(0.5,c);}o.push([P[i][0]+nx*d*k,P[i][1]+ny*d*k,P[i][2]]);}return o;}
const MWOP={
 join(){mwNeed(2);const S=mwS(),[ia,ib]=MWS.sel,a=S[ia],b=S[ib];if(a.closed||b.closed)throw new Error('Sambung hanya untuk garis terbuka. Buka poligon dulu dengan Putus.');let A=a.pts.map(p=>p.slice()),B=b.pts.map(p=>p.slice());
  const dd=(p,q)=>Math.hypot(p[0]-q[0],p[1]-q[1]);const c=[[dd(A[A.length-1],B[0]),0],[dd(A[A.length-1],B[B.length-1]),1],[dd(A[0],B[0]),2],[dd(A[0],B[B.length-1]),3]].sort((x,y)=>x[0]-y[0])[0];
  if(c[1]===1)B.reverse();else if(c[1]===2)A.reverse();else if(c[1]===3){A.reverse();B.reverse();}if(dd(A[A.length-1],B[0])<0.05)B.shift();let J=A.concat(B);const tol=+$('mwtol').value||1;let cl='';if(dd(J[0],J[J.length-1])<=tol&&J.length>3){J[J.length-1]=J[0].slice();cl=' dan ditutup menjadi poligon';}
  const L=mwL();L[ia]=J;L.splice(ib,1);mwApply(L,'Sambung 2 string (celah '+f1(c[0])+' m)'+cl,[ia>ib?ia-1:ia]);},
 brk(){mwPickPoint(1,'Klik titik tempat string diputus.',pv=>{const S=mwS(),{si,vi}=pv[0],s=S[si],L=mwL();if(s.closed){const P=openPts(s),m=P.length,R2=[];for(let k=0;k<m;k++)R2.push(P[(vi+k)%m]);/* poligon dibuka: ruas terakhir (sebelum titik) dihapus */L[si]=R2;mwApply(L,'Putus poligon di titik '+(vi+1),[si]);}
  else{if(vi===0||vi===s.pts.length-1)throw new Error('Titik ujung tidak bisa diputus — pilih titik di tengah.');const P=s.pts.map(p=>p.slice());L[si]=P.slice(0,vi+1);L.push(P.slice(vi).map(p=>p.slice()));mwApply(L,'Putus garis di titik '+(vi+1),[si,L.length-1]);}});},
 cut(){mwPickPoint(2,'Klik dua titik: bagian di antara keduanya dihapus (memotong string).',pv=>{if(pv[0].si!==pv[1].si)throw new Error('Kedua titik harus pada string yang sama.');const S=mwS(),si=pv[0].si,s=S[si],L=mwL();let i0=Math.min(pv[0].vi,pv[1].vi),i1=Math.max(pv[0].vi,pv[1].vi);if(i1-i0<1)throw new Error('Pilih dua titik berbeda.');
  if(s.closed){const P=openPts(s);L[si]=P.slice(i1).concat(P.slice(0,i0+1));}else{L[si]=s.pts.slice(0,i0+1).map(p=>p.slice());if(i1<s.pts.length-1)L.push(s.pts.slice(i1).map(p=>p.slice()));if(L[si].length<2)L.splice(si,1);}mwApply(L,'Potong string di antara titik '+(i0+1)+'–'+(i1+1),[]);});},
 close(){mwNeed(1);const S=mwS(),L=mwL();let n=0;for(const i of MWS.sel){const s=S[i];if(s.closed||s.pts.length<3)continue;L[i]=closeIt(s.pts.map(p=>p.slice()));n++;}if(!n)throw new Error('String terpilih sudah poligon atau terlalu pendek.');mwApply(L,'Jadikan poligon ('+n+' string)',MWS.sel);},
 reduce(){mwNeed(1);const tol=+$('mwred').value||0.5,S=mwS(),L=mwL();let a=0,b=0;for(const i of MWS.sel){const s=S[i];const P=openPts(s);a+=P.length;let Q=s.closed?rdp3(P.concat([P[0]]),tol).slice(0,-1):rdp3(P,tol);if(Q.length<(s.closed?3:2))Q=P;b+=Q.length;L[i]=s.closed?closeIt(Q):Q;}mwApply(L,'Kurangi titik '+a+' → '+b+' (toleransi '+f1(tol)+' m)',MWS.sel);},
 dens(){mwNeed(1);const st=+$('mwden').value||2,S=mwS(),L=mwL();let a=0,b=0;for(const i of MWS.sel){const s=S[i];const P=s.pts.map(p=>p.slice());a+=P.length;const Q=densify(P,st);b+=Q.length;L[i]=Q;}mwApply(L,'Perapat titik '+a+' → '+b+' (jarak '+f1(st)+' m)',MWS.sel);},
 snap(){mwPickPoint(2,'Klik titik yang akan dipindah, lalu klik titik tujuan (boleh di string lain yang terpilih).',pv=>{if(pv[0].si===pv[1].si&&pv[0].vi===pv[1].vi)throw new Error('Pilih dua titik berbeda.');const S=mwS(),a=pv[0],b=pv[1],s=S[a.si],T=S[b.si].pts[b.vi],L=mwL(),P=L[a.si];const o=P[a.vi],d=Math.hypot(T[0]-o[0],T[1]-o[1]),dz=$('mwsz').checked?T[2]-o[2]:0;const zk=!$('mwsz').checked;P[a.vi]=[T[0],T[1],zk?o[2]:T[2]];
  if(s.closed){if(a.vi===0)P[P.length-1]=P[0].slice();else if(a.vi===P.length-1)P[0]=P[P.length-1].slice();}
  mwApply(L,'Snap titik '+(a.vi+1)+' ke titik '+(b.vi+1)+' (geser '+f1(d)+' m'+(Math.abs(dz)>0.01?', RL '+(dz>0?'+':'')+f1(dz)+' m':'')+')',MWS.sel);
  if(s.flat&&Math.abs(dz)>0.25)mwInfo('&#10003; Titik dipindah tepat ke titik tujuan. Catatan: RL titik ini berubah '+(dz>0?'+':'')+f1(dz)+' m, sehingga string '+(s.closed?'poligon':'garis')+' RL '+f1(s.z)+' kini tidak datar di titik itu (wajar bila titik tujuan bagian jalan). Matikan &#8220;RL ikut titik tujuan&#8221; bila hanya posisi E, N yang ingin dipindah.','ok');},'snapx','Snap titik ke titik');},
 straight(){mwPickPoint(2,'Klik dua titik: string di antara keduanya diluruskan (titik di antaranya dihapus).',pv=>{if(pv[0].si!==pv[1].si)throw new Error('Kedua titik harus pada string yang sama.');const S=mwS(),si=pv[0].si,s=S[si],L=mwL();const i0=Math.min(pv[0].vi,pv[1].vi),i1=Math.max(pv[0].vi,pv[1].vi);if(i1-i0<2)throw new Error('Tidak ada titik di antara kedua titik itu.');
  const P=s.pts.map(p=>p.slice());L[si]=P.slice(0,i0+1).concat(P.slice(i1));if(s.closed)L[si][L[si].length-1]=L[si][0].slice();mwApply(L,'Luruskan titik '+(i0+1)+'–'+(i1+1)+' ('+(i1-i0-1)+' titik dihapus)',[si]);});},
 smooth(){mwNeed(1);const k=Math.max(1,Math.round(+$('mwsm').value||2)),S=mwS(),L=mwL();for(const i of MWS.sel){const s=S[i],P=openPts(s),n=P.length;const Q=P.map((p,j)=>{if(!s.closed&&(j===0||j===n-1))return p.slice();let x=0,y=0,c=0;for(let d=-k;d<=k;d++){let m=j+d;if(s.closed)m=(m+n)%n;else if(m<0||m>=n)continue;x+=P[m][0];y+=P[m][1];c++;}return [x/c,y/c,p[2]];});L[i]=s.closed?closeIt(Q):Q;}mwApply(L,'Haluskan (±'+k+' titik)',MWS.sel);},
 offset(){mwNeed(1);const d=+$('mwoff').value||0;if(!d)throw new Error('Isi jarak offset (+ keluar/kiri, − dalam/kanan).');const copy=$('mwocp').checked,dz=+$('mwodz').value||0,S=mwS(),L=mwL(),add=[];let rm=[];
  for(const i of MWS.sel){const s=S[i];let out=[];if(s.closed){let P=[toC(openPts(s))];if(cArea(P[0])<0)P=[P[0].slice().reverse()];const Q=cOff(P,d).filter(r=>Math.abs(cArea(r))>0.5);for(const r of Q){const R2=ringOf(r).map(p=>{let bz=s.z,bd=1e18;if(!s.flat)for(const q of s.pts){const e=Math.hypot(q[0]-p[0],q[1]-p[1]);if(e<bd){bd=e;bz=q[2];}}return [p[0],p[1],bz+dz];});out.push(closeIt(R2));}}
   else out=[offOpen(s.pts,d).map(p=>[p[0],p[1],p[2]+dz])];if(!out.length)throw new Error('Offset '+f1(d)+' m menghapus string '+(MWS.sel.indexOf(i)?'B':'A')+' (terlalu kecil untuk jarak itu).');if(!copy){L[i]=out[0];for(const r of out.slice(1))add.push(r);}else for(const r of out)add.push(r);}
  const n0=L.length;for(const r of add)L.push(r);mwApply(L,'Offset '+f1(d)+' m'+(dz?' · RL '+(dz>0?'+':'')+f1(dz)+' m':'')+(copy?' (salinan)':''),copy?add.map((_,k)=>n0+k):MWS.sel);},
 proj(){mwNeed(1);const m=$('mwpm').value,S=mwS(),L=mwL();let miss=0,n=0;const zf=m==='rl'?+$('mwprl').value:NaN;if(m==='rl'&&!isFinite(zf))throw new Error('Isi RL tujuan.');
  for(const i of MWS.sel){L[i]=S[i].pts.map(p=>{let z=p[2];if(m==='rl')z=zf;else if(m==='topo'){const t=TP.length?topoZ(p[0],p[1]):NaN;if(isFinite(t))z=t;else miss++;}else if(m==='pit'){const t=ED.base.tin&&ED.base.tin.G?gridZ(ED.base.tin.G,p[0],p[1]):NaN;if(isFinite(t))z=t;else miss++;}n++;return [p[0],p[1],z];});}
  mwApply(L,'Project ke '+({rl:'RL '+f1(zf),topo:'topografi',pit:'permukaan pit'}[m])+(miss?' ('+miss+'/'+n+' titik di luar data, RL tetap)':''),MWS.sel);},
 rev(){mwNeed(1);const L=mwL();for(const i of MWS.sel)L[i]=L[i].slice().reverse();mwApply(L,'Balik arah string',MWS.sel);},
 del(){mwNeed(1);const L=mwL(),k=new Set(MWS.sel);const n=k.size;mwApply(L.filter((_,i)=>!k.has(i)),'Hapus '+n+' string',[]);},
 dup(){mwNeed(1);const dx=+$('mwmx').value||0,dy=+$('mwmy').value||0,dz=+$('mwmz').value||0,S=mwS(),L=mwL(),n0=L.length;for(const i of MWS.sel)L.push(S[i].pts.map(p=>[p[0]+dx,p[1]+dy,p[2]+dz]));mwApply(L,'Salin string (geser '+f1(dx)+', '+f1(dy)+', '+f1(dz)+')',MWS.sel.map((_,k)=>n0+k));},
 move(){mwNeed(1);const dx=+$('mwmx').value||0,dy=+$('mwmy').value||0,dz=+$('mwmz').value||0;if(!dx&&!dy&&!dz)throw new Error('Isi geser E/N/RL.');const L=mwL();for(const i of MWS.sel)L[i]=L[i].map(p=>[p[0]+dx,p[1]+dy,p[2]+dz]);mwApply(L,'Geser string ('+f1(dx)+', '+f1(dy)+', '+f1(dz)+')',MWS.sel);},
 autofix(){if(!ED)throw new Error('Impor pit dulu.');const tol=+$('mwfx').value||3,t1=+$('mwtol').value||1;let L=mwL(),n=0;
  for(let pass=0;pass<4;pass++){const S=oldS(L),LE=looseEnds(S,t1);let k=0;
   for(const e of LE){if(e.d>tol)continue;const p=L[e.i][e.j];let b=null,bd=tol;for(let i2=0;i2<L.length;i2++){if(i2===e.i)continue;const P=L[i2];for(let m=1;m<P.length;m++){const a=P[m-1],c=P[m];if(Math.abs(a[2]-p[2])>0.6&&Math.abs(c[2]-p[2])>0.6)continue;const ex=c[0]-a[0],ey=c[1]-a[1],L2=ex*ex+ey*ey||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*ex+(p[1]-a[1])*ey)/L2)),d=Math.hypot(p[0]-a[0]-ex*t,p[1]-a[1]-ey*t);if(d<bd){bd=d;b=[a[0]+ex*t,a[1]+ey*t,a[2]+(c[2]-a[2])*t];}}}
    if(!b)continue;const Q=L[e.i],dx=b[0]-Q[e.j][0],dy=b[1]-Q[e.j][1],m=Q.length,KM=Math.max(1,Math.min(4,Math.floor(m/2)));for(let q=0;q<KM;q++){const j=e.j?m-1-q:q,f=1-q/KM;Q[j]=[Q[j][0]+dx*f,Q[j][1]+dy*f,Q[j][2]];}Q[e.j][2]=b[2];k++;}
   n+=k;if(!k)break;}
  if(!n)throw new Error('Tidak ada ujung lepas dengan celah ≤ '+f1(tol)+' m — tidak ada yang putus.'+(MWS.sel.length===2?' Untuk menjadikan string A dan B satu string, klik ➕ Sambung (bilah alat) atau Edit Manual ▾ → Sambungan → Sambung A + B.':' Untuk menggabungkan dua string jadi satu, pilih keduanya (klik, lalu Shift+klik) dan klik ➕ Sambung.'));mwApply(L,'Perbaiki sambungan otomatis ('+n+' ujung, celah ≤ '+f1(tol)+' m)',MWS.sel);}
};
/* ---- menu bertingkat (cascade) ---- */
function cmBuild(items){const m=document.createElement('div');m.className='cmenu';for(const it of items){if(it==='-'){m.insertAdjacentHTML('beforeend','<div class="sep"></div>');continue;}if(it.hd){m.insertAdjacentHTML('beforeend','<div class="hd">'+esc(it.hd)+'</div>');continue;}
  const d=document.createElement('div'),dis=it.dis&&it.dis(),on=it.on&&it.on();d.className='ci'+(dis?' dis':'')+(on?' on':'');d.innerHTML='<span class="ic">'+(on?'&#10003;':(it.ic||''))+'</span><span>'+esc(it.t)+'</span>'+(it.sub?'<span class="ar">&#9656;</span>':it.kb?'<span class="kb">'+esc(it.kb)+'</span>':'');if(it.tip)d.title=it.tip;
  if(it.sub)d.appendChild(cmBuild(it.sub));else if(!dis)d.onclick=e=>{e.stopPropagation();cmClose();try{it.fn();}catch(err){mwShow(null);mwAfter('&#9888; '+esc(err.message),'warn');}};m.appendChild(d);}return m;}
let CM=null;function cmClose(){if(CM){CM.remove();CM=null;}document.querySelectorAll('#mbmw,#mbpd').forEach(b=>b.classList.remove('on'));}
function cmOpen(btn,items){const was=CM&&CM._b===btn;cmClose();if(was)return;const m=cmBuild(items);m._b=btn;document.body.appendChild(m);const r=btn.getBoundingClientRect();m.style.left=Math.min(r.left,innerWidth-250)+'px';m.style.top=(r.bottom+2)+'px';CM=m;btn.classList.add('on');}
addEventListener('pointerdown',e=>{if(CM&&!CM.contains(e.target)&&e.target!==CM._b&&!(CM._b&&CM._b.contains(e.target)))cmClose();},true);addEventListener('keydown',e=>{if(e.key==='Escape')cmClose();});
function mwShow(row,title){winShow($('mw'),true);document.querySelectorAll('#mw .mwr').forEach(x=>x.classList.toggle('on',!!row&&x.dataset.row.split(' ').includes(row)));const g=$('mwgo');g.hidden=!row||row==='loose';g.dataset.op=row||'';g.textContent='Terapkan';$('mwtt').innerHTML='&#9998; '+esc(title||'Edit Manual');mwDraw();mwInfo();}
const needED=()=>{if(!ED)throw new Error('Impor pit atau pakai hasil Desain baru di tab Edit dulu.');if(MODE!=='edit')try{$('mode').querySelector('[data-m="edit"]').click();}catch(_){}};
const run=op=>()=>{needED();MWOP[op]();winShow($('mw'),true);};
const prm=(row,title)=>()=>{needED();mwShow(row,title);};
function pickToggle(){needED();if(MWS.pick&&!MWS.ppick){MWS.pick=false;cv.style.cursor='';mwInfo();return;}MWS.pick=true;MWS.ppick=null;cv.style.cursor='pointer';mwShow(null,'Pilih string');mwInfo('Klik garis di 3D. Shift+klik = string kedua (B). Pilih lagi di menu untuk berhenti.','warn');}
function mwMenu(){return [
 {t:'Pilih string',ic:'&#8982;',kb:'klik · Shift+klik',fn:pickToggle,on:()=>MWS.pick&&!MWS.ppick},
 {t:'Lepas pilihan',ic:'&#10005;',kb:'Esc',fn:()=>selClear(),dis:()=>!MWS.sel.length&&!(ED&&ED.sel>=0)},
 '-',
 {t:'Sambungan',ic:'&#128279;',sub:[
  {t:'Sambung A + B',ic:'&#10133;',fn:run('join'),tip:'Sambung dua garis terbuka di ujung terdekat; bila ujung akhirnya bertemu, jadi poligon'},
  {t:'Putus di titik',ic:'&#9986;',fn:run('brk'),tip:'Garis → dua garis; poligon → dibuka di titik itu'},
  {t:'Potong antara 2 titik',ic:'&#9988;',fn:run('cut')},
  {t:'Jadikan poligon',ic:'&#11040;',fn:run('close')},
  '-',
  {t:'Perbaiki sambungan otomatis…',ic:'&#128295;',fn:prm('autofix','Perbaiki sambungan otomatis')},
  {t:'Sorot ujung lepas',ic:'&#9679;',fn:()=>{needED();MWS.loose=!MWS.loose;$('mwlo').checked=MWS.loose;mwDraw();mwShow(null);},on:()=>MWS.loose},
  {t:'Batas celah lepas…',ic:'&#8596;',fn:prm('loose','Batas celah lepas')}]},
 {t:'Titik',ic:'&#8226;',sub:[
  {t:'Kurangi titik (filter)…',ic:'&#8756;',fn:prm('reduce','Kurangi titik')},
  {t:'Perapat titik (subdivide)…',ic:'&#43;',fn:prm('dens','Perapat titik')},
  {t:'Snap titik ke titik',ic:'&#8982;&#8594;',fn:run('snap'),tip:'Klik titik yang dipindah, lalu titik tujuan: titik pindah tepat ke titik tujuan (E, N, RL)'},
  {t:'Luruskan antara 2 titik',ic:'&#10187;',fn:run('straight')},
  {t:'Haluskan…',ic:'&#8776;',fn:prm('smooth','Haluskan')}]},
 {t:'Bentuk',ic:'&#11040;',sub:[
  {t:'Offset…',ic:'&#8649;',fn:prm('offset','Offset')},
  {t:'Project ke',ic:'&#8615;',sub:[
   {t:'RL tetap…',fn:()=>{$('mwpm').value='rl';$('mwprl').disabled=false;prm('proj','Project ke RL')();}},
   {t:'Topografi',fn:()=>{$('mwpm').value='topo';run('proj')();}},
   {t:'Permukaan pit',fn:()=>{$('mwpm').value='pit';run('proj')();}}]},
  {t:'Geser…',ic:'&#10021;',fn:()=>{prm('move dup','Geser / salin')();$('mwgo').dataset.op='move';$('mwgo').textContent='Geser';}},
  {t:'Salin + geser…',ic:'&#10697;',fn:()=>{prm('move dup','Geser / salin')();$('mwgo').dataset.op='dup';$('mwgo').textContent='Salin + geser';}},
  {t:'Balik arah',ic:'&#8646;',fn:run('rev')},
  {t:'Hapus string',ic:'&#128465;',fn:run('del')}]},
 '-',
 {t:'Batalkan',ic:'&#8630;',kb:'Ctrl+Z',fn:()=>ehGo(EH.i-1),dis:()=>EH.i<=0},
 {t:'Ulangi',ic:'&#8631;',kb:'Ctrl+Y',fn:()=>ehGo(EH.i+1),dis:()=>EH.i>=EH.st.length-1},
 {t:'Simpan project (.pit.json)',ic:'&#128190;',fn:()=>{const b=$('pjs');if(b)b.click();}},
 {t:'Panel info Edit Manual',ic:'&#8505;',fn:()=>{needED();mwShow(null);}}];}
function pdMenu(){return [
 {t:'Sapu: dorong dinding keluar',ic:'&#8596;',fn:()=>pdStart('push')},
 {t:'Sapu: tarik dinding ke dalam',ic:'&#8594;&#8592;',fn:()=>pdStart('shrink')},
 '-',
 {t:'Kekuatan & jari-jari kuas…',ic:'&#9881;',fn:()=>winShow($('pdw'),true)},
 {t:'Batalkan sapuan terakhir',ic:'&#8630;',kb:'Ctrl+Z',fn:()=>ehGo(EH.i-1),dis:()=>EH.i<=0}];}
function pdStart(kind){if(!ED){winShow($('pdw'),true);pdInfo('Impor pit atau pakai hasil Desain baru di tab Edit dulu.','warn');return;}if(MODE!=='edit')try{$('mode').querySelector('[data-m="edit"]').click();}catch(_){}$('pdm').value=kind;document.querySelectorAll('#pdmb [data-v]').forEach(x=>x.classList.toggle('on',x.dataset.v===kind));winShow($('pdw'),true);pdArm(true);}
function mwInit(){const b=$('mwb');if(!b)return;
 $('mwgo').onclick=e=>{e.preventDefault();const op=$('mwgo').dataset.op;if(!op)return;try{MWOP[op]();}catch(err){mwAfter('&#9888; '+esc(err.message),'warn');}};
 $('mwlo').onchange=()=>{MWS.loose=$('mwlo').checked;mwDraw();};$('mwtol').onchange=()=>{mwDraw();mwInfo();};
 $('mwpm').onchange=()=>{$('mwprl').disabled=$('mwpm').value!=='rl';};
 $('mbmw').onclick=()=>cmOpen($('mbmw'),mwMenu());$('mbpd').onclick=()=>cmOpen($('mbpd'),pdMenu());}
mwInit();

/* ---------- 3. Play-Doh: kuas sapuan dorong / tarik dinding ---------- */
G.pd=new THREE.Group();W.add(G.pd);
const PD={arm:false,drag:null,pts:[]};
function pdInfo(h,cls){$('pdinf').innerHTML=h?'<div class="'+(cls||'')+'">'+h+'</div>':'';}
function pdZ(){const f=edFloor();return f?f.z:(ED?ED.zmin:0);}
function pdDrawStroke(){clr(G.pd);if(PD.pts.length<2)return;const z=pdZ()+0.5,r=+$('pdr').value||25;const o=lineObj(PD.pts.map(p=>[p[0],p[1],z]),'#ae3ec9',false,{depthTest:false});o.renderOrder=12;G.pd.add(o);
 const c=[];for(let k=0;k<=24;k++){const t=k/24*2*Math.PI,p=PD.pts[PD.pts.length-1];c.push([p[0]+r*Math.cos(t),p[1]+r*Math.sin(t),z]);}const o2=lineObj(c,'#ae3ec9',false,{depthTest:false});o2.renderOrder=12;G.pd.add(o2);}
function pdArm(on){PD.arm=on;$('pdgo').classList.toggle('on',on);cv.style.cursor=on?'crosshair':'';if(on)pdInfo('Tahan klik kiri lalu <b>sapukan</b> kuas di sepanjang dinding yang ingin '+($('pdm').value==='push'?'didorong keluar':'ditarik ke dalam')+'. Lepas klik = terapkan.','warn');}
cv.addEventListener('pointerdown',e=>{if(!PD.arm||e.button!==0||MODE!=='edit'||!ED)return;const p=hitPlane(e,pdZ());if(!p)return;e.stopPropagation();e.preventDefault();CT.enabled=false;PD.drag=true;PD.pts=[[p[0],p[1]]];pdDrawStroke();},true);
cv.addEventListener('pointermove',e=>{if(!PD.drag)return;const p=hitPlane(e,pdZ());if(!p)return;const q=PD.pts[PD.pts.length-1];if(Math.hypot(p[0]-q[0],p[1]-q[1])>1.5){PD.pts.push([p[0],p[1]]);pdDrawStroke();}},true);
addEventListener('pointerup',e=>{if(!PD.drag)return;PD.drag=null;CT.enabled=true;pdArm(false);setTimeout(pdApply,20);},true);
function pdApply(){if(!ED||PD.pts.length<1)return;const kind=$('pdm').value,d=Math.max(0.5,+$('pds').value||5),r=Math.max(3,+$('pdr').value||25);const v0=ED.base.vol?ED.base.vol.tot:0;
 const dz0=ED.dzone,zu=ED.zoneUsed;let res=null;try{if(ED.out){EH.next='Hasil diterima';edAccept();}ED.dzone=null;ED.lastResize=null;ED.brush={pts:densify(PD.pts.map(p=>[p[0],p[1],0]),2).map(p=>[p[0],p[1]]),r};res=runResize(kind,d);}catch(err){ED.brush=null;ED.dzone=dz0;clr(G.pd);pdInfo('&#9888; '+esc(err.message).replace(/\n/g,'<br>'),'warn');return;}
 ED.brush=null;ED.dzone=dz0;ED.zoneUsed=zu;EH.next='Play-Doh: '+(kind==='push'?'dorong':'tarik')+' '+f1(d)+' m (kuas '+f1(r)+' m)';edAccept();ED.lastResize=null;clr(G.pd);
 const v1=ED.base.vol?ED.base.vol.tot:0,LE=looseEnds(ED.base.S,1);pdInfo('&#10003; Sapuan diterapkan: '+(kind==='push'?'dorong keluar':'tarik ke dalam')+' '+f1(d)+' m · volume '+(v1-v0>=0?'+':'')+nf(v1-v0)+' m³ · ujung lepas '+LE.length+'. <span class="hint">Batalkan dengan &#8630; di panel Edit atau Ctrl+Z.</span>','ok');try{pitRedraw();}catch(_){}}
function pdInit(){if(!$('pdgo'))return;$('pdgo').onclick=()=>{if(!ED){pdInfo('Impor pit atau pakai hasil Desain baru di tab Edit dulu.','warn');return;}if(MODE!=='edit')try{$('mode').querySelector('[data-m="edit"]').click();}catch(_){}pdArm(!PD.arm);};
 document.querySelectorAll('#pdmb [data-v]').forEach(b=>b.onclick=()=>{$('pdm').value=b.dataset.v;document.querySelectorAll('#pdmb [data-v]').forEach(x=>x.classList.toggle('on',x===b));});}
pdInit();
window.__PS3.manual={op:(k)=>MWOP[k](),sel:a=>{MWS.sel=a;mwDraw();mwInfo();},loose:t=>looseEnds(mwS(),t||1).length,looseL:t=>looseEnds(mwS(),t||1).map(x=>[x.i,x.j,x.p.map(v=>+v.toFixed(1)),+x.d.toFixed(2),mwS()[x.i].flat,mwS()[x.i].pts.length]),hist:()=>EH.st.map(h=>h.label),undo:()=>ehGo(EH.i-1),brush:(kind,d,r,pts)=>{$('pdm').value=kind;$('pds').value=d;$('pdr').value=r;PD.pts=pts;pdApply();return $('pdinf').innerText;},kv:()=>kvGet('edit').then(v=>v&&{label:v.label,n:v.L.length})};

/* ---------- 4. langkah Edit otomatis → menu bertingkat + jendela (panel kiri tinggal riwayat & ringkasan; pemilik 16 Nov 12:22) ---------- */
const EDW=[];
function edCascade(){const M=$('m-edit');if(!M)return;const host=$('mw').parentNode;[...M.querySelectorAll(':scope > .step')].forEach((st,k)=>{const sh=st.querySelector('.sh'),sb=st.querySelector(':scope > .sb');if(!sh||!sb)return;const title=sh.querySelector('b').innerHTML,stEl=sh.querySelector('.st');
  const w=document.createElement('div');w.className='flw win edw';w.id='edw'+(k+1);w.innerHTML='<div class="flh"><b>'+(k+1)+'. '+title+'</b><span class="note" data-st></span><span class="sp"></span><button class="x" title="Tutup">&#10005;</button></div><div class="flb"></div>';w.querySelector('.flb').appendChild(sb);host.appendChild(w);try{flDrag(w);}catch(_){}w.querySelector('.x').onclick=()=>winShow(w,false);st.classList.add('inwin');
  if(stEl){const mo=new MutationObserver(()=>{w.querySelector('[data-st]').textContent=stEl.textContent;edSum();});mo.observe(stEl,{childList:true,characterData:true,subtree:true});}EDW.push({w,title,stEl});});
 $('mbea').onclick=()=>cmOpen($('mbea'),eaMenu());edSum();}
function edOpen(k){if(MODE!=='edit')try{$('mode').querySelector('[data-m="edit"]').click();}catch(_){}const x=EDW[k];if(!x)return;EDW.forEach((y,j)=>{if(j!==k&&y.w.style.display==='block'&&!y.pin)winShow(y.w,false);});winShow(x.w,true);}
function eaMenu(){const nm=t=>{const d=document.createElement('div');d.innerHTML=t;return d.textContent;};return [
 {t:'Impor pit (.str / .dxf)…',ic:'&#8679;',fn:()=>{$('epf').click();}},
 '-'].concat(EDW.map((x,k)=>({t:(k+1)+'. '+nm(x.title),ic:['&#128194;','&#9998;','&#8615;','&#9660;','&#8596;','&#128197;'][k]||'',kb:x.stEl?x.stEl.textContent:'',fn:()=>edOpen(k)})));}
function edSum(){const el=$('edsum');if(!el)return;if(!ED){el.innerHTML='<span class="hint">Belum ada pit. Buka <b>&#9881; Edit Otomatis &#9662; → Impor pit</b> atau <b>1. Sumber</b> untuk memakai hasil Desain baru.</span>';return;}
 const v=ED.base&&ED.base.vol?ED.base.vol.tot:null;el.innerHTML='<b>'+esc(ED.nm||'pit')+'</b> · '+ED.base.S.length+' string'+(v?' · volume '+nf(v)+' m³':'')+(ED.out?'<br><span class="warn">Ada hasil yang belum diterima — buka langkahnya di menu &#9881; Edit Otomatis.</span>':'')+'<div class="hint" style="margin-top:3px">Langkah edit ada di menu <b>&#9881; Edit Otomatis &#9662;</b>, alat string di <b>&#9998; Edit Manual &#9662;</b>, kuas di <b>&#128396; Play-Doh &#9662;</b>.</div>';}
{const _u=ehUI;ehUI=function(){_u();try{edSum();}catch(_){}};}
edCascade();

/* ---------- 5. bilah alat baris kedua (pola Ore Works #otb) + ulangi alat terakhir — pemilik 16 Nov 12:25–12:29 ---------- */
let LASTT=null;
function tbFlat(items,out){for(const it of items){if(it==='-'||it.hd)continue;if(it.sub)tbFlat(it.sub,out);else out.push(it);}return out;}
function tbDo(it){try{it.fn();if(!/Pilih string|Sorot|Batalkan|Ulangi|Bilah/.test(it.t)){LASTT=it;tbLast();}}catch(err){mwShow(null);mwAfter('&#9888; '+esc(err.message),'warn');}setTimeout(tbState,50);}
function tbLast(){const b=$('tbrep');if(!b)return;b.disabled=!LASTT;b.title=LASTT?'Ulangi alat terakhir: '+LASTT.t.replace('…','')+' (tombol R)':'Ulangi alat terakhir (tombol R) — belum ada alat yang dipakai';}
/* label pendek di bilah alat */
const TBL={'Impor pit (.str / .dxf)…':'Impor','Pilih string':'Pilih','Snap titik ke titik':'Snap','Sambung A + B':'Sambung','Putus di titik':'Putus','Potong antara 2 titik':'Potong','Jadikan poligon':'Poligon','Perbaiki sambungan otomatis…':'Perbaiki','Sorot ujung lepas':'Ujung lepas','Kurangi titik (filter)…':'Kurangi','Perapat titik (subdivide)…':'Perapat','Luruskan antara 2 titik':'Luruskan','Haluskan…':'Haluskan','Offset…':'Offset','RL tetap…':'→RL','Topografi':'→Topo','Permukaan pit':'→Pit','Geser…':'Geser','Salin + geser…':'Salin','Balik arah':'Balik','Hapus string':'Hapus','Sapu: dorong dinding keluar':'Dorong','Sapu: tarik dinding ke dalam':'Tarik','Kekuatan & jari-jari kuas…':'Kuas'};
const TBX=new Set(['Panel info Edit Manual','Simpan project (.pit.json)','Batalkan','Ulangi','Batas celah lepas…','Batalkan sapuan terakhir','Bilah alat berikon']);
function tbBuild(){let T=$('ptb');if(!T){T=document.createElement('div');T.id='ptb';const w=$('wrap');w.parentNode.insertBefore(T,w);}T.innerHTML='';
 const sep=()=>T.insertAdjacentHTML('beforeend','<span class="ts"></span>'),lab=t=>T.insertAdjacentHTML('beforeend','<span class="tl">'+t+'</span>');
 const btn=(it,lbl)=>{const b=document.createElement('button');b.className='tb'+(lbl&&!/^(Pilih|Snap|Sambung|Putus|Perbaiki|Offset|Dorong|Tarik)$/.test(lbl)?' lp':'');b.innerHTML='<i>'+(it.ic||'•')+'</i>'+(lbl?'<span>'+esc(lbl)+'</span>':'');b.title=it.t.replace('…','')+(it.kb?' ('+it.kb+')':'')+(it.tip?' — '+it.tip:'');b._it=it;b.onclick=()=>tbDo(it);T.appendChild(b);return b;};
 /* tampilan (kedua mode) */
 [['plan','&#9634;','Plan'],['sw','&#11091;','SW'],['ne','&#11090;','NE'],['ew','&#8678;','Timur'],['ns','&#8679;','Selatan'],['fit','&#9974;','Pas']].forEach(v=>{btn({t:'Pandangan '+v[2],ic:v[1],fn:()=>{const b=document.querySelector('#vw2 [data-v="'+v[0]+'"]');if(b)b.click();}},'').classList.add('vw');});
 const E=document.createElement('span');E.id='ptbe';E.style.display='contents';T.appendChild(E);const add=(it,l)=>{const b=btn(it,l);E.appendChild(b);return b;},esep=()=>E.insertAdjacentHTML('beforeend','<span class="ts"></span>'),elab=t=>E.insertAdjacentHTML('beforeend','<span class="tl">'+t+'</span>');
 esep();add({t:'Batalkan',ic:'&#8630;',kb:'Ctrl+Z',fn:()=>ehGo(EH.i-1),dis:()=>EH.i<=0});add({t:'Ulangi',ic:'&#8631;',kb:'Ctrl+Y',fn:()=>ehGo(EH.i+1),dis:()=>EH.i>=EH.st.length-1});
 const hs=document.createElement('select');hs.id='ptbh';hs.title='Riwayat edit (tersimpan otomatis)';hs.onchange=()=>ehGo(+hs.value);E.appendChild(hs);add({t:'Simpan project (.pit.json)',ic:'&#128190;',fn:()=>{const b=$('pjs');if(b)b.click();}});
 const r=document.createElement('button');r.className='tb';r.id='tbrep';r.innerHTML='<i>&#8635;</i>';r.onclick=()=>{if(LASTT)tbDo(LASTT);};E.appendChild(r);
 /* langkah Edit Otomatis hanya di menu (pemilik 16 Nov 13:52) */
 esep();elab('Manual');const TBW=['Pilih string','Lepas pilihan','Snap titik ke titik','Sambung A + B','Putus di titik','Jadikan poligon','Perbaiki sambungan otomatis…','Kurangi titik (filter)…','Luruskan antara 2 titik','Offset…','Geser…','Hapus string','Sorot ujung lepas'];const MI=tbFlat(mwMenu(),[]);TBW.forEach(t=>{const it=MI.find(x=>x.t===t);if(it)add(it,TBL[t]||'');});
 esep();elab('Play-Doh');pdMenu().filter(it=>it!=='-'&&!TBX.has(it.t)).forEach(it=>add(it,TBL[it.t]||''));
 tbLast();tbState();}
function tbFit(){const T=$('ptb');if(!T)return;T.classList.remove('tbc','tb1');if(T.scrollWidth>T.clientWidth+2)T.classList.add('tb1');if(T.scrollWidth>T.clientWidth+2)T.classList.add('tbc');}
function tbState(){const T=$('ptb');if(!T)return;const ed=MODE==='edit';$('ptbe').style.display=ed?'contents':'none';for(const b of T.querySelectorAll('button.tb')){const it=b._it;if(!it)continue;b.classList.toggle('on',!!(it.on&&it.on()));b.disabled=!!(it.dis&&it.dis());}
 const hs=$('ptbh');if(hs){hs.innerHTML=EH.st.length?EH.st.map((x,k)=>'<option value="'+k+'"'+(k===EH.i?' selected':'')+'>'+(k+1)+'/'+EH.st.length+' · '+esc(x.label)+'</option>').join(''):'<option>riwayat kosong</option>';hs.disabled=!EH.st.length;}
 tbFit();sideAuto();}
addEventListener('resize',()=>setTimeout(tbFit,50));
addEventListener('keydown',e=>{if(MODE!=='edit'||/INPUT|SELECT|TEXTAREA/.test((e.target&&e.target.tagName)||'')||e.ctrlKey||e.metaKey||e.altKey)return;if(e.key==='r'||e.key==='R'){if(LASTT){e.preventDefault();tbDo(LASTT);}}});
document.querySelectorAll('#tabs button,#mode button').forEach(b=>b.addEventListener('click',()=>setTimeout(()=>{tbState();edSum();},30)));
{const _u=ehUI;ehUI=function(){_u();try{tbState();}catch(_){}};}
{const _d=mwDraw;mwDraw=function(){_d();try{tbState();}catch(_){}};}

/* ---------- 6. tempel ⇤ / lepas ⇱ (pola Ore Works); panel kiri mode Edit hanya muncul bila ada jendela tertempel ---------- */
const DOCKX=new Set(['lgw','lay','lyw']);
const CRUMB={mw:'Edit Manual',pdw:'Play-Doh',tdw:'Rekomendasi sistem'};
function dockInit(){const side=$('side');if(!side)return;let D=$('dock');if(!D){D=document.createElement('div');D.id='dock';side.insertBefore(D,side.firstChild);}
 let saved={};try{saved=JSON.parse(localStorage.getItem('ps_dock')||'{}');}catch(_){}
 document.querySelectorAll('.flw.win').forEach(w=>{if(!w.id||DOCKX.has(w.id)||w.querySelector('.pin'))return;const h=w.querySelector('.flh'),x=h&&h.querySelector('.x');if(!h)return;const p=document.createElement('button');p.className='pin';p.innerHTML='&#8676;';p.title='Tempel ke panel kiri';h.insertBefore(p,x||null);w._home=w.parentNode;
  p.onclick=e=>{e.stopPropagation();dockSet(w,!w.classList.contains('docked'));};if(saved[w.id])dockSet(w,true,true);});
 /* jejak menu di judul jendela */
 EDW.forEach((x,k)=>{const b=x.w.querySelector('.flh b');b.innerHTML='<span class="cr">Edit Otomatis &#8250; </span>'+(k+1)+' · '+x.title;});
 for(const id in CRUMB){const w=$(id),b=w&&w.querySelector('.flh b');if(b&&!b.querySelector('.cr'))b.insertAdjacentHTML('afterbegin','<span class="cr">'+CRUMB[id]+' &#8250; </span>');}}
function dockSet(w,on,quiet){const D=$('dock'),p=w.querySelector('.pin');if(on){D.appendChild(w);w.classList.add('docked');if(p){p.innerHTML='&#8689;';p.title='Lepas jadi jendela mengambang';}if(!quiet)winShow(w,true);}
 else{(w._home||document.body).appendChild(w);w.classList.remove('docked');if(p){p.innerHTML='&#8676;';p.title='Tempel ke panel kiri';}if(!quiet)winShow(w,true);}
 let saved={};try{saved=JSON.parse(localStorage.getItem('ps_dock')||'{}');}catch(_){}saved[w.id]=on;try{localStorage.setItem('ps_dock',JSON.stringify(saved));}catch(_){}sideAuto();}
let SIDE_W=null;function sideAuto(){const side=$('side'),D=$('dock');if(!side||!D)return;const ed=MODE==='edit',has=[...D.children].some(w=>w.style.display==='block');const want=ed&&!has;if(want!==!!side._auto){side._auto=want;side.classList.toggle('hid',want);const sp=$('split');if(sp)sp.style.display=want?'none':'';setTimeout(()=>dispatchEvent(new Event('resize')),30);}}
{const _w=winShow;winShow=function(w,on){const r=_w.apply(this,arguments);try{if(w&&w.classList&&w.classList.contains('docked'))sideAuto();}catch(_){}return r;};}
/* ringkasan pit & tawaran pulihkan: ke bilah status / kanvas (panel kiri mode Edit kosong) */
function edMove(){const sb=$('sbar'),es=$('edsum'),er=$('ehrest'),eb=$('ehbar');if(eb)eb.style.display='none';if(sb&&es){es.className='sbe';sb.insertBefore(es,sb.querySelector('.sp'));}if(er){er.classList.add('ehtoast');$('cv').appendChild(er);}}
{const _s=edSum;edSum=function(){_s();const el=$('edsum');if(!el)return;el.style.display=MODE==='edit'?'':'none';if(!ED){el.innerHTML='Edit: belum ada pit — &#9881; Edit Otomatis &#9662; → Impor pit';return;}const v=ED.base&&ED.base.vol?ED.base.vol.tot:null;el.innerHTML='Edit: <b>'+esc(ED.nm||'pit')+'</b> · '+ED.base.S.length+' string'+(v?' · '+nf(v)+' m³':'')+(ED.out?' · <span class="warn">hasil belum diterima</span>':'')+(EH_SAVED>0?' · tersimpan otomatis '+new Date(EH_SAVED).toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'}):'');};}
edMove();tbBuild();dockInit();sideAuto();edSum();
window.__PS3.ui={dock:(id,on)=>dockSet($(id),on),tb:()=>[...document.querySelectorAll('#ptb button.tb')].filter(b=>b.offsetParent).map(b=>b.title.slice(0,24)),side:()=>!$('side').classList.contains('hid')};

/* ---------- 7. mode Desain baru dengan pola yang sama (pemilik 16 Nov 13:13) ---------- */
const DSW=[];
function dsCascade(){const M=$('m-new');if(!M)return;const host=$('mw').parentNode;let n=0;[...M.querySelectorAll(':scope > .step')].forEach(st=>{if(st.hidden)return;const sh=st.querySelector('.sh'),sb=st.querySelector(':scope > .sb');if(!sh||!sb)return;n++;const title=sh.querySelector('b').innerHTML,stEl=sh.querySelector('.st');
  const w=document.createElement('div');w.className='flw win edw';w.id='dsw'+n;w.innerHTML='<div class="flh"><b><span class="cr">Desain baru &#8250; </span>'+n+' · '+title+'</b><span class="note" data-st></span><span class="sp"></span><button class="x" title="Tutup">&#10005;</button></div><div class="flb"></div>';w.querySelector('.flb').appendChild(sb);host.appendChild(w);try{flDrag(w);}catch(_){}w.querySelector('.x').onclick=()=>winShow(w,false);st.classList.add('inwin');
  if(stEl){const mo=new MutationObserver(()=>{w.querySelector('[data-st]').textContent=stEl.textContent;});mo.observe(stEl,{childList:true,characterData:true,subtree:true});w.querySelector('[data-st]').textContent=stEl.textContent;}DSW.push({w,title,stEl,id:st.id});});
 const dk=$('dkindw');if(dk)dk.style.display='none';
 $('mbds').onclick=()=>cmOpen($('mbds'),dsMenu());}
function dsOpen(k){if(MODE==='edit')try{$('tabs').querySelector('[data-t="design"]').click();}catch(_){}const x=DSW[k];if(!x)return;DSW.forEach((y,j)=>{if(j!==k&&y.w.style.display==='block'&&!y.w.classList.contains('docked'))winShow(y.w,false);});winShow(x.w,true);}
openStep=function(id){const k=DSW.findIndex(x=>x.id===id);if(k>=0)dsOpen(k);else document.querySelectorAll('#m-new .step').forEach(x=>x.classList.toggle('open',x.id===id));};
const dkCur=()=>{const b=document.querySelector('#dkind button.on');return b?b.dataset.v:'new';};
const dkSet=v=>{const b=document.querySelector('#dkind [data-v="'+v+'"]');if(b)b.click();setTimeout(tbState,50);};
function dsGo(){const k=DSW.findIndex(x=>x.w.querySelector('#go'));if(k>=0)dsOpen(k);const g=$('go');if(g)g.click();}
function dsMenu(){const nm=t=>{const d=document.createElement('div');d.innerHTML=t;return d.textContent;};return [
 {hd:'Pit final / Staging: pilih di bilah alat'}].concat(DSW.map((x,k)=>({t:(k+1)+'. '+nm(x.title),ic:['&#11040;','&#9881;','&#8605;','&#9654;'][k]||'',kb:x.stEl?x.stEl.textContent:'',fn:()=>dsOpen(k)})),['-',
 {t:'Bilah alat berikon',ic:'&#9776;',fn:tbToggle,on:()=>TB_ON}]);}
let TB_ON=true;function tbToggle(){TB_ON=!TB_ON;const T=$('ptb');if(T)T.style.display=TB_ON?'':'none';setTimeout(()=>dispatchEvent(new Event('resize')),30);}
dsCascade();
/* bilah alat: kelompok Desain (tampil di mode Desain) */
{const _b=tbBuild;tbBuild=function(){_b();const T=$('ptb');if(!T)return;const D=document.createElement('span');D.id='ptbd';D.style.display='contents';const vw=[...T.querySelectorAll('.tb.vw')].pop();vw.after(D);
  const mk=(it,lbl,cls)=>{const b=document.createElement('button');b.className='tb'+(cls?' '+cls:'');b.innerHTML='<i>'+it.ic+'</i>'+(lbl?'<span>'+esc(lbl)+'</span>':'');b.title=it.t;b._it=it;b.onclick=()=>{try{it.fn();}catch(e){alert(e.message);}setTimeout(tbState,50);};D.appendChild(b);};
  D.insertAdjacentHTML('beforeend','<span class="ts"></span>');mk({t:'Pit final',ic:'&#9650;',fn:()=>dkSet('new'),on:()=>dkCur()==='new'},'Pit final');mk({t:'Staging (dibatasi pit final)',ic:'&#9638;',fn:()=>dkSet('stage'),on:()=>dkCur()==='stage'},'Staging');
  /* langkah Desain hanya di menu */
  D.insertAdjacentHTML('beforeend','<span class="ts"></span>');mk({t:'Buat pit (langkah 4)',ic:'&#9654;',fn:dsGo},'Buat pit');
  /* Desain terpandu & Rancang Otomatis hanya di menu */
  tbState();};}
{const _s=tbState;tbState=function(){_s();const d=$('ptbd'),ed=MODE==='edit';if(d)d.style.display=ed?'none':'contents';for(const id of ['mbea','mbmw','mbpd']){const b=$(id);if(b)b.style.display=ed?'':'none';}const b=$('mbds');if(b)b.style.display=ed?'none':'';if(d)for(const x of d.querySelectorAll('button.tb')){const it=x._it;if(it&&it.on)x.classList.toggle('on',!!it.on());}tbFit();sideAuto();};}
sideAuto=function(){const side=$('side'),D=$('dock');if(!side||!D)return;const has=[...D.children].some(w=>w.style.display==='block');const want=!has;if(want!==!!side._auto){side._auto=want;side.classList.toggle('hid',want);const sp=$('split');if(sp)sp.style.display=want?'none':'';setTimeout(()=>dispatchEvent(new Event('resize')),30);}};
document.querySelectorAll('#dkind button').forEach(b=>b.addEventListener('click',()=>setTimeout(tbState,30)));
tbBuild();dockInit();sideAuto();
window.__PS3.ui.ds=()=>DSW.map(x=>x.w.id);

/* ---------- 8. bilah menu ringkas: ikon label disembunyikan, Desain terpandu & Rancang Otomatis masuk menu Desain baru ---------- */
function mbarTidy(){const M=$('mbar');if(!M)return;for(const b of M.querySelectorAll('.mbb')){if(b.dataset.tidy)continue;b.dataset.tidy=1;const n=b.firstChild;if(n&&n.nodeType===3){const m=/^\s*([^\sA-Za-z0-9?]+)\s+(.*)$/.exec(n.textContent);if(m){n.textContent=m[2];const i=document.createElement('span');i.className='mi';i.textContent=m[1]+' ';b.insertBefore(i,n);}}}
 const mv=[...M.querySelectorAll('.mbb')].filter(b=>/Desain terpandu|Rancang Otomatis/.test(b.textContent));mv.forEach(b=>b.style.display='none');MBMV=mv;}
let MBMV=[];
{const _m=dsMenu;dsMenu=function(){const a=_m(),k=a.findIndex(x=>x&&x.t==='Bilah alat berikon')-2;const ex=MBMV.map(b=>({t:b.textContent.replace(/^\s*\S+\s/,'').trim()||b.textContent.trim(),ic:/terpandu/i.test(b.textContent)?'&#9998;':'&#9881;',tip:b.title,fn:()=>b.click()}));return a.slice(0,k+1).concat(['-'],ex,a.slice(k+1));};}
mbarTidy();
window.__PS3.ui.mbar=()=>{const m=$('mbar');return [m.scrollWidth,m.clientWidth];};
window.__PS3.lim=(z,k)=>{try{return limAt(z,k||'C').map(ringOf);}catch(e){return 'ERR '+e.message;}};window.__PS3.finLv=()=>FIN&&FIN.lv.map(l=>l.z);
window.__PS3.areg=()=>{const AR=areas(),R=areaRegions();return {pa:AR.map(a=>(a.PA||[]).map(r=>Math.round(cArea(r)))),top:AR.map(aTop),reg:R?R.P.map(P=>P.map(r=>Math.round(cArea(r)))):null,regR:R?R.P.map(P=>P.map(ringOf)):null,paR:AR.map(a=>(a.PA||[]).map(ringOf))};};
/* jendela langkah milik mode lain ditutup saat mode berganti */
let LASTMODE=MODE;{const _s=tbState;tbState=function(){const ed=MODE==='edit',was=LASTMODE==='edit';if(ed!==was){LASTMODE=MODE;(ed?DSW:EDW).forEach(x=>{if(x.w.style.display==='block')winShow(x.w,false);});if(ed&&$('mw')&&$('pdw')){}else{for(const id of ['mw','pdw']){const w=$(id);if(w&&w.style.display==='block')winShow(w,false);}}}LASTMODE=MODE;_s();};}
window.__PS3.bchk=()=>{const R=curR();return R.B.map(b=>({zt:b.zt,zc:b.zc,ai:b.ai,cr:(b.crest||[]).map(r=>{const q=ringOf(r);let ax=0;for(let i=0;i<q.length;i++){const a=q[i],c=q[(i+1)%q.length];if(Math.abs(a[0]-c[0])<0.01||Math.abs(a[1]-c[1])<0.01)ax++;}return [q.length,ax,Math.round(Math.abs(cArea(r)))];}),keys:Object.keys(b).join(',')}));};

/* ---------- 9. lepas pilihan: Esc, klik tempat kosong, tombol bilah alat (pemilik 16 Nov 14:06) ---------- */
function selClear(){let n=0;if(MWS.sel.length||MWS.pv.length||MWS.ppick){MWS.sel=[];MWS.pv=[];MWS.ppick=null;n++;}if(MWS.pick){MWS.pick=false;cv.style.cursor='';}
 if(ED&&ED.sel>=0){if(ED.dirty){try{$('edone').click();}catch(_){}}ED.sel=-1;ED.orig=null;try{edStopPick();}catch(_){}try{clr(G.edit);}catch(_){}const e=$('eseli');if(e)e.innerHTML='';const t=$('etyrow');if(t)t.hidden=true;n++;try{pitRedraw();}catch(_){}}
 mwDraw();try{mwInfo();}catch(_){}return n;}
addEventListener('keydown',e=>{if(e.key!=='Escape'||MODE!=='edit'||CM||DG||/INPUT|SELECT|TEXTAREA/.test((e.target&&e.target.tagName)||''))return;if(PD.arm){pdArm(false);return;}selClear();});
/* klik di tempat kosong saat memilih = lepas pilihan */
{const _c=mwClick;mwClick=function(e){if(!MWS.ppick&&!(e.shiftKey||e.ctrlKey)&&nearStr(e,mwS(),false,14)<0){selClear();MWS.pick=true;cv.style.cursor='pointer';mwInfo('Pilihan dilepas. Klik garis untuk memilih lagi, atau Esc untuk berhenti memilih.','ok');return;}return _c(e);};}

/* ---------- 10. RL atas per area = permukaan tahap sebelumnya yang miring (bukan dipotong tegak per wilayah raster) — BU4, 16 Nov ----------
   Di dalam bukaan area k pada RL atasnya (dasar area di-offset sejauh proyeksi lereng), permukaan = RL atas; di luar bukaan permukaan naik
   mengikuti kemiringan keseluruhan geoteknik. Permukaan kerja = min(topografi, permukaan tahap). Bench di atasnya = udara, dipotong seperti
   bibir pit di topografi. Hanya untuk ≥ 2 area dengan RL atas; satu area tetap cara lama. window.__CAPOLD = cara lama. */
let CAPG=null;
function capBuild(){CAPG=null;if(window.__CAPOLD||!BASE||MODE==='edit')return;const AR=areas();if(AR.length<2)return;const L=[];
 for(const a of AR){const t=aTop(a);if(!isFinite(t))continue;const PA=(a.PA||[]).filter(r=>cArea(r)>0);if(!PA.length)continue;const zb=areaZ(a);const p0=prmAt(zb+0.01),O=t>zb?cOff(PA,projDist(t-zb,p0)):PA;const p=prmAt(t+0.01),k=p.H/Math.max(0.1,p.a+p.B/Math.max(1,p.N));L.push({t,R:O.filter(r=>cArea(r)>0).map(ringOf),k});}
 if(!L.length)return;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const a of AR)for(const r of (a.PA||[]))for(const q of ringOf(r)){x0=Math.min(x0,q[0]);x1=Math.max(x1,q[0]);y0=Math.min(y0,q[1]);y1=Math.max(y1,q[1]);}
 const m=500,c=2;x0-=m;y0-=m;x1+=m;y1+=m;const nx=Math.ceil((x1-x0)/c)+1,ny=Math.ceil((y1-y0)/c)+1,Z=new Float32Array(nx*ny);
 const dist=(R,x,y)=>{let bd=1e18,ins=false;for(const r of R){let c2=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const a=r[i],b=r[j];if(((a[1]>y)!==(b[1]>y))&&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]))c2=!c2;const ex=b[0]-a[0],ey=b[1]-a[1],l2=ex*ex+ey*ey||1e-9,tt=Math.max(0,Math.min(1,((x-a[0])*ex+(y-a[1])*ey)/l2)),dx=x-a[0]-ex*tt,dy=y-a[1]-ey*tt,d=dx*dx+dy*dy;if(d<bd)bd=d;}if(c2)ins=true;}return ins?0:Math.sqrt(bd);};
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const x=x0+i*c,y=y0+j*c;let z=Infinity;for(const q of L){const v=q.t+q.k*dist(q.R,x,y);if(v<z)z=v;}Z[j*nx+i]=z;}
 CAPG={x0,y0,c,nx,ny,Z,L};}
function capZ(x,y){const G=CAPG;if(!G)return Infinity;const fx=(x-G.x0)/G.c,fy=(y-G.y0)/G.c,i=Math.floor(fx),j=Math.floor(fy);if(i<0||j<0||i>=G.nx-1||j>=G.ny-1)return Infinity;const u=fx-i,v=fy-j,Z=G.Z,n=G.nx;return Z[j*n+i]*(1-u)*(1-v)+Z[j*n+i+1]*u*(1-v)+Z[(j+1)*n+i]*(1-u)*v+Z[(j+1)*n+i+1]*u*v;}
{const _tz=topoZ;topoZ=function(E,N){const t=_tz(E,N);if(!CAPG||MODE==='edit'||!isFinite(t))return t;const c=capZ(E,N);return c<t?c:t;};}
{const _rn=runNew;runNew=function(){try{capBuild();}catch(e){console.warn('capBuild',e);CAPG=null;}return _rn.apply(this,arguments);};}
{const _rt=rlTrim;rlTrim=function(B,warn){if(!CAPG)return _rt(B,warn);const AR=areas();warn.push('ℹ RL atas per area: '+AR.map((a,k)=>{const t=aTop(a);return isFinite(t)?(a.kind==='line'?'Urat ':'Area ')+(k+1)+' ≤ RL '+f1(t):null;}).filter(Boolean).join(', ')+' — dianggap sudah tergali (tahap sebelumnya, lereng sesuai geoteknik); bench di atasnya dipotong seperti bibir pit.');return B;};}
{const _rc=rlCap;rlCap=function(foot){if(CAPG)return null;return _rc(foot);};}
window.__PS3.cap=()=>CAPG&&{n:CAPG.L.length,t:CAPG.L.map(q=>q.t),k:CAPG.L.map(q=>+q.k.toFixed(3))};

/* ---------- 11. ▶ Jalankan rekomendasi otomatis (pemilik 16 Nov 15:06) ---------- */
let LASTINTER=false,RA_PREV=null,RA_LOG=null;
{const _sr=showResult;showResult=function(){LASTINTER=!!arguments[4];return _sr.apply(this,arguments);};}
const raSet=(id,v)=>{const e=$(id);if(!e)return;e.value=v;e.dispatchEvent(new Event('input'));e.dispatchEvent(new Event('change'));};
function raFixes(){let R=null;try{R=curR();}catch(_){}const W=((R&&R.warn)||[]).map(String),F=[];let m;
 for(const w of W){if((m=/RL bawah ([\d.]+) tidak tercapai[^]*?lantai RL ([\d.]+)/.exec(w))&&$('pZmin').value!==m[2])F.push({nm:'RL bawah galian '+($('pZmin').value||'otomatis')+' → '+m[2]+' (dasar yang tercapai)',go:()=>raSet('pZmin',m[2])});
  if((m=/naikkan kemiringan jalan ke ([\d.]+)%/.exec(w))&&+$('rG').value<+m[1])F.push({nm:'Kemiringan jalan '+$('rG').value+'% → '+m[1]+'%',go:()=>raSet('rG',m[1])});}
 return F;}
function raSnap(){return {pZmin:$('pZmin').value,rG:$('rG').value,tidy:tidySet()};}
function raRestore(){const p=RA_PREV;if(!p)return;raSet('pZmin',p.pZmin);raSet('rG',p.rG);tidyApply(p.tidy);RA_PREV=null;RA_LOG=null;try{runNew();}catch(e){alert(e.message);}}
function raRun(){if(TIDY_BUSY)return;if(LASTINTER&&!confirm('Hasil ini dari Desain terpandu (bench demi bench). Menjalankan rekomendasi otomatis akan merancang ulang pit secara otomatis dan menimpa bench yang Anda buat. Lanjutkan?'))return;
 let c0=null;try{c0=tidyGet();}catch(_){}RA_PREV=raSnap();const done=[];
 const b=$('tdwb');if(b)b.insertAdjacentHTML('afterbegin','<div class="info" id="rabusy">&#9203; Menjalankan rekomendasi otomatis…</div>');
 /* 1. pengaturan kerapian terbaik dulu (bisa mencapai RL bawah yang diminta), 2. lalu saran yang masih berlaku pada hasil barunya */
 setTimeout(()=>{if(LASTINTER){try{TIDY_LOCK=true;tidyLock();runNew();}catch(e){alert(e.message);return;}}
  TIDY_RES=null;tidySearch();const wait=setInterval(()=>{if(TIDY_BUSY)return;clearInterval(wait);const T=TIDY_RES;if(T&&T.best>0&&T.rows[T.best]&&!T.rows[T.best].err){done.push('Pengaturan kerapian: '+tidyNm(T.rows[T.best].o));tidyApply(T.rows[T.best].o);try{runNew();}catch(e){console.warn(e);}}
   const F=raFixes();if(F.length){for(const f of F){try{f.go();done.push(f.nm);}catch(e){console.warn(e);}}try{TIDY_LOCK=true;tidyLock();runNew();}catch(e){console.warn(e);}}
   let c1=null;try{c1=tidyGet();}catch(_){}RA_LOG={done,c0,c1};try{tidyNote();}catch(_){}},300);},30);}
{const _tn=tidyNote;tidyNote=function(){_tn();const b=$('tdwb');if(!b||TIDY_BUSY)return;const F=raFixes();let h='<div class="sec" id="rasec">';
 if(RA_LOG){const L=RA_LOG,f=c=>c?'menggantung '+c.dang+' · silang '+c.crossDz+' · tidak dipatuhi '+c.noReason+' · vol '+nf(c.vol/1000)+' rb m³':'—';h+='<b>Rekomendasi otomatis sudah dijalankan</b><div>'+(L.done.length?L.done.map(x=>'&#10003; '+esc(x)).join('<br>'):'Tidak ada pengaturan yang perlu diubah; pengaturan Anda sudah yang terbaik dari yang diuji.')+'</div><div class="hint">Sebelum: '+f(L.c0)+'<br>Sesudah: '+f(L.c1)+'</div>'+(RA_PREV?'<button id="raundo" class="sm">&#8630; Kembalikan pengaturan sebelumnya</button>':'');}
 else{h+='<button id="rago" class="pri" style="width:100%">&#9654; Jalankan rekomendasi otomatis</button><div class="hint">'+(F.length?'Akan diterapkan: '+F.map(x=>esc(x.nm)).join('; ')+', lalu ':'')+'pit dirancang ulang dengan beberapa pengaturan kerapian dan yang terbaik dipakai (lantai tidak lebih dangkal, volume berubah &lt; 2%). Pengaturan sebelumnya bisa dikembalikan.'+(LASTINTER?' <b>Hasil ini dari Desain terpandu — menjalankannya akan menimpa bench yang Anda buat.</b>':'')+'</div>';}
 h+='</div>';b.insertAdjacentHTML('beforeend',h);const g=$('rago');if(g)g.onclick=raRun;const u=$('raundo');if(u)u.onclick=raRestore;};}
$('go').addEventListener('click',()=>{if(!TIDY_LOCK){RA_LOG=null;}},true);
window.__PS3.ra={run:raRun,log:()=>RA_LOG&&{done:RA_LOG.done,c0:RA_LOG.c0&&{d:RA_LOG.c0.dang,x:RA_LOG.c0.crossDz,n:RA_LOG.c0.noReason},c1:RA_LOG.c1&&{d:RA_LOG.c1.dang,x:RA_LOG.c1.crossDz,n:RA_LOG.c1.noReason}},fixes:()=>raFixes().map(f=>f.nm)};

/* ---------- 12. saran terukur untuk "badan jalan di atas topografi" + peringatan kembar dibuang (pemilik 16 Nov 15:13) ---------- */
function airAdvice(force){let R=null;try{R=curR();}catch(_){}if(!R||!R.B||!TP.length)return '';let wb=null,wn=0;
 for(const b of R.B){let n=0,a=0;for(const r of (b.roads||[])){if(r.fin||!r.out||r.out.length!==r.in.length)continue;for(let i=0;i<r.in.length;i++){const x=(r.in[i][0]+r.out[i][0])/2,y=(r.in[i][1]+r.out[i][1])/2,zz=(r.in[i][2]+r.out[i][2])/2,t=topoZ(x,y);if(!isFinite(t))continue;n++;if(t<zz-1)a++;}}if(a>wn||(force&&!wb&&n)){wn=Math.max(wn,a);wb=b;}}
 if(!wb)return '';const rings=(wb.crest||[]).map(ringOf).filter(r=>r.length>2);if(!rings.length)return '';rings.sort((p,q)=>Math.abs(cArea(toC(q)))-Math.abs(cArea(toC(p))));const ring=rings[0],z=wb.zc;
 const P=densify(ring.concat([ring[0]]).map(p=>[p[0],p[1],0]),2);P.pop();const ok=P.map(p=>{const t=topoZ(p[0],p[1]);return isFinite(t)&&t>=z-0.5;}),n=P.length;if(!n)return '';
 const fr=ok.filter(Boolean).length/n;let best=null;for(let s=0;s<n;s++){if(!ok[s]||ok[(s-1+n)%n])continue;let k=0;while(k<n&&ok[(s+k)%n])k++;if(!best||k>best.k)best={s,k};}
 if(!best&&ok.every(Boolean))best={s:0,k:n};
 let h='<br><b>Saran (dihitung dari dinding bench RL '+f1(wb.zt)+'–'+f1(z)+'):</b> ';
 if(!best||best.k*2<RAMP().W*3)return h+'hampir seluruh dinding bench ini ('+Math.round(100*(1-fr))+'%) berada di atas topografi — bench ini terbuka ke lereng, jalan tidak diperlukan di sini. Pakai bentuk awal <b>Batas topo (atas → bawah)</b> di langkah 1: di sisi rendah bench dibuka ke lereng dan jalan otomatis masuk dari bibir terendah, atau mulai jalan dari bench yang lebih rendah.';
 const c=P[(best.s+Math.floor(best.k/2))%n],L=best.k*2;
 return h+(fr<0.95?'hanya '+Math.round(100*fr)+'% dinding bench ini yang masih berupa batuan':Math.round(100*fr)+'% dinding bench ini masih berupa batuan')+' (tanah ≥ RL '+f1(z)+'). Busur batuan terpanjang ±'+nf(L)+' m berpusat di <b>E '+f1(c[0])+', N '+f1(c[1])+'</b>. Pindahkan titik awal jalan / klik <b>Tarik arah jalan</b> di dinding itu supaya jalan menempel pada batuan'+(L<12/Math.max(0.01,RAMP().g)*0+0?'':'')+'. Bila busur itu lebih pendek dari ±'+nf(prmAt(z).H/Math.max(0.01,RAMP().g))+' m (panjang jalan satu bench pada '+(RAMP().g*100).toFixed(0)+'%), jalan perlu switchback di sana, atau pakai <b>Batas topo (atas → bawah)</b> agar sisi rendah dibuka ke lereng.';}
{const _ws=warnSaran;warnSaran=function(w){const r=_ws(w);if(r)return r;if(/badan jalan berada di atas topografi/.test(String(w))){try{return airAdvice();}catch(e){console.warn(e);}}return r;};}
/* peringatan kembar (terkumpul dari tiap pratinjau Desain terpandu) cukup sekali */
{const _sr2=showResult;showResult=function(B,floor,warn){if(Array.isArray(warn)){const seen=new Set();for(let i=warn.length-1;i>=0;i--){const k=String(warn[i]).replace(/\d+%/,'#%');if(/badan jalan berada di atas topografi/.test(k)){if(seen.has('air')){warn.splice(i,1);continue;}seen.add('air');}}}return _sr2.apply(this,arguments);};}
window.__PS3.airAdv=f=>airAdvice(f);
