/* ================= Mode Edit pit jadi ================= */
/* {nm,base:{S,foot,tin},zmin,zref,sel,orig,type,rpt,auto,out,est} */
function ringArea(pts){let a=0;for(let i=0;i<pts.length-1;i++){const p=pts[i],q=pts[i+1];a+=p[0]*q[1]-q[0]*p[1];}return Math.abs(a/2);}
/* string bench: >= 60% titik pada satu RL (sisanya boleh bagian jalan yang turun); string terbuka tetap boleh dipilih */
function oldS(L){return L.map(l=>{const cnt=new Map();for(const p of l){const k=Math.round(p[2]*10);cnt.set(k,(cnt.get(k)||0)+1);}let km=0,bc=-1;for(const [k,c] of cnt)if(c>bc){bc=c;km=k;}const zm=km/10;let on=0;for(const p of l)if(Math.abs(p[2]-zm)<0.3)on++;
 let z0=1e9,z1=-1e9,zs=0;for(const p of l){z0=Math.min(z0,p[2]);z1=Math.max(z1,p[2]);zs+=p[2];}const closed=l.length>3&&Math.hypot(l[0][0]-l[l.length-1][0],l[0][1]-l[l.length-1][1])<0.5;const pts=l.map(p=>p.slice());if(closed)pts[pts.length-1]=pts[0].slice();
 const flat=l.length>=3&&on/l.length>=0.6,pure=z1-z0<0.25;return {t:'old',z:flat?zm:zs/l.length,pts,flat,pure,closed,area:closed?ringArea(pts):0};});}
function median(a){if(!a.length)return NaN;a=a.slice().sort((x,y)=>x-y);return a[a.length>>1];}
/* perkiraan parameter pit lama */
function estOld(S){const fl=S.filter(s=>s.flat&&s.closed&&s.area>20),by=new Map();for(const s of fl){const k=Math.round(s.z*10)/10;if(!by.has(k))by.set(k,[]);by.get(k).push(s);}
 const lv=[...by.keys()].sort((a,b)=>a-b),dz=[];for(let i=1;i<lv.length;i++)dz.push(+(lv[i]-lv[i-1]).toFixed(2));const H=median(dz.filter(d=>d>1));
 const berms=[],bw=[];for(const z of lv){const g=by.get(z);if(g.length<2)continue;g.sort((a,b)=>a.area-b.area);const sm=g[0],bg=g[g.length-1];if(bg.area-sm.area<20)continue;berms.push(z);const r=bg.pts.map(p=>[p[0],p[1]]),c=ringCum(r);const ds=[];for(let i=0;i<sm.pts.length;i+=3)ds.push(ringNear(r,c,sm.pts[i]).d);bw.push(median(ds));}
 const fa=[];for(let i=1;i<lv.length;i++){const lo=by.get(lv[i-1]),hi=by.get(lv[i]);const cr=hi.slice().sort((a,b)=>a.area-b.area)[0],to=lo.slice().sort((a,b)=>b.area-a.area)[0];const r=to.pts.map(p=>[p[0],p[1]]),c=ringCum(r),ds=[];for(let k=0;k<cr.pts.length;k+=4)ds.push(ringNear(r,c,cr.pts[k]).d);const a=median(ds);if(a>0.05)fa.push(Math.atan2(lv[i]-lv[i-1],a)*180/Math.PI);}
 const bd=[];for(let i=1;i<berms.length;i++)bd.push(berms[i]-berms[i-1]);const N=isFinite(H)&&bd.length?Math.max(1,Math.round(median(bd)/H)):NaN;
 return {H,A:median(fa),B:median(bw),N,berms,zref:berms.length?berms[0]:(lv.length?lv[0]:NaN),lv};}
function edLoad(L,fname,R0){const f={name:fname};const S=oldS(L);const foot=footOf(S);if(!foot.length)throw new Error('tidak ada string tertutup (crest/toe) di file ini');
  const tin=R0&&R0.tin?R0.tin:surfOf(S,foot,40);let zmin=1e9;for(const s of S)for(const p of s.pts)zmin=Math.min(zmin,p[2]);const est=estOld(S);
  ED={nm:f.name,base:{S,foot,tin,zmin,day:null},zmin,zref:est.zref,est,sel:-1,out:null};ED.base.vol=volOf(ED.base);
  let h='<b>'+esc(f.name)+'</b>: '+S.length+' string ('+S.filter(s=>s.flat).length+' string bench, '+S.filter(s=>!s.flat).length+' jalan/miring). Lantai RL '+f1(zmin)+'.';
  const ok=isFinite(est.H)&&est.H>=2&&est.H<=20&&(!isFinite(est.A)||(est.A>=30&&est.A<=85))&&(!est.berms.length||est.B<=20);if(!ok)h+='<br><span class="hint">Parameter pit lama tidak bisa dibaca otomatis dari file ini — isi manual di tab Pit final langkah 3.</span>';if(ok)h+='<br>Terbaca: tinggi bench <b>'+est.H+' m</b>'+(isFinite(est.A)?', muka ±<b>'+est.A.toFixed(0)+'°</b>':'')+(est.berms.length?', berm ±<b>'+f1(est.B)+' m</b> tiap '+est.N+' bench (RL '+est.berms.join(', ')+')':', tanpa berm')+'.'+
   ' <button id="euse" class="sm">Pakai parameter ini</button>';
  if(TP.length)h+='<br>Volume galian pit lama: <b>'+nf(ED.base.vol.tot)+' m³</b>';
  $('einfo').innerHTML=h;const ub=$('euse');if(ub)ub.onclick=()=>{if(isFinite(est.H))$('pH').value=est.H;if(isFinite(est.A))$('pA').value=Math.round(est.A);if(est.berms.length){$('pB').value=+est.B.toFixed(1);$('pN').value=est.N;}else $('pB').value=0;prmUpd();ub.textContent='✓ dipakai';ub.disabled=true;};
  $('einfo').innerHTML+=' <a href="#" class="del" id="edel">&#128465; Hapus pit impor</a>';$('edel').onclick=ev=>{ev.preventDefault();if(!confirm('Hapus pit impor '+ED.nm+'?'))return;ED=null;edStopPick();clr(G.edit);$('einfo').innerHTML='';$('eseli').innerHTML='';$('eres').innerHTML='';$('etyrow').hidden=true;$('e1st').textContent='';$('e2st').textContent='';$('e3st').textContent='';pitRedraw();};$('e1st').textContent='✓';pitRedraw();view('sw');$('eseli').innerHTML='';}
$('epf').onchange=async e=>{const f=e.target.files[0];e.target.value='';if(!f)return;if(MODE!=='edit')$('mode').querySelector('[data-m="edit"]').click();winShow($('iw'),false);try{const L=await readFileL(f);setO(L[0][0]);edLoad(L,f.name);}catch(err){alert(f.name+': '+err.message);}};
/* pilih string */
let EPICK=false;function edStopPick(){EPICK=false;$('esel').classList.remove('on');cv.style.cursor='';}
$('esel').onclick=()=>{if(!ED){alert('Impor pit dulu (langkah 1).');return;}if(EPICK){edStopPick();return;}rPickStop();EPICK=true;$('esel').classList.add('on');cv.style.cursor='pointer';$('eseli').innerHTML='Klik garis bench (string datar) di tampilan 3D.';};
function nearStr(e,S,flatOnly,tol){const r=R.domElement.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let best=-1,bd=tol||12;
 S.forEach((s,i)=>{if(flatOnly&&!s.flat)return;let pa=null;for(const p of s.pts){const q=scr(p[0],p[1],p[2]);if(pa&&q[2]<1&&pa[2]<1){const dx=q[0]-pa[0],dy=q[1]-pa[1],L2=dx*dx+dy*dy||1,t=Math.max(0,Math.min(1,((mx-pa[0])*dx+(my-pa[1])*dy)/L2)),d=Math.hypot(mx-pa[0]-dx*t,my-pa[1]-dy*t);if(d<bd){bd=d;best=i;}}pa=q;}});return best;}
window.edClick=e=>{if(MODE!=='edit'||!ED)return;if(EPICK){const S=ED.base.S;let i=nearStr(e,S,true,18);if(i<0)i=nearStr(e,S,false,12);if(i<0)return;const s=S[i];
  if(!s.closed||!s.flat){edStopPick();ED.out=null;ED.sel=i;ED.orig=s.pts.map(p=>p.slice());$('etyrow').hidden=true;$('eseli').innerHTML='Terpilih: <b>string terbuka / jalan</b> · '+s.pts.length+' titik · RL '+f1(Math.min(...s.pts.map(p=>p[2])))+'–'+f1(Math.max(...s.pts.map(p=>p[2])))+'<br><span class="hint">Edit bebas: seret titik (RL tiap titik tetap, atau ikut titik target bila snap), tidak membentuk ulang bench. Klik <b>Selesai seret</b> untuk memperbarui permukaan.</span>';$('e2st').textContent='string terbuka';pitRedraw();return;}
  if(s.closed&&!s.pure){const U=s.pts.map(p=>[p[0],p[1],s.z]);s.note='bagian jalan di string ini diratakan ke RL '+f1(s.z);s.pts=U;s.pure=true;s.area=ringArea(U);}
  edStopPick();if(ED.out){ED.out=null;}ED.sel=i;ED.orig=s.pts.map(p=>p.slice());const same=S.filter((q,j)=>j!==i&&q.flat&&q.closed&&Math.abs(q.z-s.z)<0.2);
  ED.type=same.some(q=>q.area<s.area-20)?'toe':'crest';$('ety').value=ED.type;$('etyrow').hidden=false;ED.auto=autoRamp(s);ED.rpt=null;$('erOn').checked=!!ED.auto;$('erpk').disabled=false;
  $('eseli').innerHTML='Terpilih: string RL <b>'+f1(s.z)+'</b> · '+(s.pts.length-1)+' titik · keliling '+nf(ringCum(s.pts.slice(0,-1).map(p=>[p[0],p[1]])).pop())+' m'+(same.length?'<br>Di RL yang sama ada '+same.length+' string lain (pasangan berm).':'')+(ED.auto?'<br>Jalan lama memotong RL ini — jalan akan dilanjutkan otomatis.':'')+(s.note?'<br><span class="warn">'+s.note+'.</span>':'');
  $('e2st').textContent='RL '+f1(s.z);pitRedraw();return;}
 if(EPK){const s=ED.base.S[ED.sel],p=hitPlane(e,s.z);if(p){ED.rpt=[p[0],p[1]];EPK=false;$('erpk').classList.remove('on');cv.style.cursor='';$('erOn').checked=true;edDraw();}}};
$('ety').onchange=()=>{ED&&(ED.type=$('ety').value);};
/* jalan lama yang memotong RL string terpilih */
/* ukur jalan lama di bawah RL terpilih: lebar, kemiringan, pola (lurus/switchback/spiral), arah turun */
function rampMeasure(sel,au){const z=sel.z,E=[];for(const s of ED.base.S){if(s===sel||s.pure||s.closed)continue;const pts=s.pts.filter(p=>p[2]<=z+0.05);if(pts.length<3)continue;
  let near=1e9;for(const p of pts)near=Math.min(near,Math.hypot(p[0]-au.p[0],p[1]-au.p[1]));if(near>40)continue;E.push(s.pts);}
 if(!E.length)return null;
 /* rangkai potongan jalan per bench menjadi satu jalur menurun */
 const pcs=ED.base.S.filter(q=>q!==sel&&!q.pure&&!q.closed&&q.pts.length>1).map(q=>{const p=q.pts.slice();if(p[0][2]<p[p.length-1][2])p.reverse();return p;}).filter(p=>p[0][2]<=z+0.05);
 let e=E[0].slice();if(e[0][2]<e[e.length-1][2])e.reverse();const used=new Set();let guard=0;
 for(;;){if(++guard>200)break;const end=e[e.length-1];let bi=-1,bd=8;pcs.forEach((p,i)=>{if(used.has(i))return;const d=Math.hypot(p[0][0]-end[0],p[0][1]-end[1])+Math.abs(p[0][2]-end[2])*2;if(d<bd&&p[0][2]<=end[2]+0.1){bd=d;bi=i;}});if(bi<0)break;used.add(bi);e=e.concat(pcs[bi].slice(1));}
 guard=0;for(;;){if(++guard>200)break;const st0=e[0];let bi=-1,bd=8;pcs.forEach((p,i)=>{if(used.has(i))return;const q=p[p.length-1];const d=Math.hypot(q[0]-st0[0],q[1]-st0[1])+Math.abs(q[2]-st0[2])*2;if(d<bd&&q[2]>=st0[2]-0.1&&p!==e){bd=d;bi=i;}});if(bi<0)break;used.add(bi);e=pcs[bi].slice(0,-1).concat(e);}let L=0,dz=0;const hd=[];for(let i=1;i<e.length;i++){const a=e[i-1],b=e[i],l=Math.hypot(b[0]-a[0],b[1]-a[1]);if(l<0.3)continue;L+=l;dz+=Math.abs(b[2]-a[2]);hd.push({h:Math.atan2(b[1]-a[1],b[0]-a[0]),l,flat:Math.abs(b[2]-a[2])<0.02*l});}
 const sl=hd.filter(x=>!x.flat);let slL=0,slz=0;for(let i=1;i<e.length;i++){const a=e[i-1],b=e[i],l=Math.hypot(b[0]-a[0],b[1]-a[1]),d=Math.abs(b[2]-a[2]);if(d>0.02*l){slL+=l;slz+=d;}}
 const g=slL>5?slz/slL:NaN;let W=NaN;if(E.length>1){const ds=[];for(const p of E[1]){let m=1e9;for(let i=1;i<e.length;i++){const a=e[i-1],b=e[i],dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2));m=Math.min(m,Math.hypot(p[0]-a[0]-dx*t,p[1]-a[1]-dy*t));}ds.push(m);}ds.sort((x,y)=>x-y);W=ds[ds.length>>1];}
 /* ukuran jalan lama yang lebih tahan: kemiringan = median (beda RL / panjang) tiap potongan tepi jalan; lebar = median jarak ke tepi seberang pada RL yang sama */
 let g2=NaN,W2=NaN;{const gs=[];for(const q of pcs){let l=0;for(let i=1;i<q.length;i++)l+=Math.hypot(q[i][0]-q[i-1][0],q[i][1]-q[i-1][1]);const d=q[0][2]-q[q.length-1][2];if(l>8&&d>0.5)gs.push(d/l);}if(gs.length){gs.sort((a,b)=>a-b);g2=gs[gs.length>>1];}
  const ws=[];pcs.forEach((q,i)=>{if(q[0][2]-q[q.length-1][2]<0.5)return;for(let k=0;k<q.length;k+=Math.max(1,Math.floor(q.length/12))){const a=q[k];let m=1e9;pcs.forEach((r,j)=>{if(j===i)return;for(let t=1;t<r.length;t++){const b0=r[t-1],b1=r[t];if(Math.min(b0[2],b1[2])>a[2]+0.4||Math.max(b0[2],b1[2])<a[2]-0.4)continue;const dz=b1[2]-b0[2],u=Math.abs(dz)>1e-6?Math.max(0,Math.min(1,(a[2]-b0[2])/dz)):0.5,x=b0[0]+(b1[0]-b0[0])*u,y=b0[1]+(b1[1]-b0[1])*u,d=Math.hypot(x-a[0],y-a[1]);if(d>2&&d<m)m=d;}});if(m<60)ws.push(m);}});if(ws.length>3){ws.sort((a,b)=>a-b);W2=ws[ws.length>>1];}}
 /* pola: berbalik tajam = switchback; berputar terus = spiral; lurus = bebas */
 let rev=false,turn=0;for(let i=1;i<sl.length;i++){let d=sl[i].h-sl[i-1].h;while(d>Math.PI)d-=2*Math.PI;while(d<-Math.PI)d+=2*Math.PI;if(Math.abs(d)>2.2)rev=true;turn+=d;}
 const mode=rev?'zig':Math.abs(turn)>1.6?'spiral':'free';
 /* arah turun pada titik potong */let v=null;{let bi=0,bd=1e9;e.forEach((p,i)=>{const d=Math.hypot(p[0]-au.p[0],p[1]-au.p[1]);if(d<bd){bd=d;bi=i;}});const a=e[Math.max(0,bi-2)],b=e[Math.min(e.length-1,bi+2)];let dx=b[0]-a[0],dy=b[1]-a[1];if(b[2]>a[2]){dx=-dx;dy=-dy;}const l=Math.hypot(dx,dy)||1;v=[dx/l,dy/l];}
 return {g:isFinite(g2)?g2:g,W:isFinite(W2)?W2:W,mode,v};}
function edRoadBelow(sel){/* jalan lama yang mulai DI BAWAH string terpilih: titik dan RL awalnya, supaya ikut dibangun ulang (tidak terhapus) */const z=sel.z;let zt=-1e9;for(const s of ED.base.S){if(s===sel||s.pure||s.flat)continue;let a=1e9,b=-1e9;for(const p of s.pts){a=Math.min(a,p[2]);b=Math.max(b,p[2]);}if(b-a<1)continue;for(const p of s.pts)if(p[2]<z-0.2&&p[2]>zt)zt=p[2];}
 if(zt<-1e8)return null;const zq=zt-0.4,cand=[];for(const s of ED.base.S){if(s===sel||s.pure||s.flat)continue;for(let i=1;i<s.pts.length;i++){const a=s.pts[i-1],b=s.pts[i];if((a[2]-zq)*(b[2]-zq)<=0&&a[2]!==b[2]){const t=(zq-a[2])/(b[2]-a[2]),lo=a[2]<b[2]?a:b,hi=a[2]<b[2]?b:a;cand.push({p:[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t],dn:[lo[0]-hi[0],lo[1]-hi[1]],sid:s});}}}
 if(!cand.length)return null;const r=sel.pts.slice(0,-1).map(p=>[p[0],p[1]]);let ar=0;for(let i=0;i<r.length;i++){const p=r[i],q=r[(i+1)%r.length];ar+=p[0]*q[1]-q[0]*p[1];}if(ar<0)r.reverse();const c=ringCum(r);
 /* pasangan tepi jalan yang paling atas */let k0=cand[0],k1=null;for(const q of cand.slice(1)){const d=Math.hypot(q.p[0]-k0.p[0],q.p[1]-k0.p[1]);if(q.sid!==k0.sid&&d>2&&d<40){k1=q;break;}}const p=[(k0.p[0]+(k1||k0).p[0])/2,(k0.p[1]+(k1||k0).p[1])/2],n=ringNear(r,c,p),A=ringAt(r,c,n.s),tg=[-A.n[1],A.n[0]],dot=tg[0]*k0.dn[0]+tg[1]*k0.dn[1];return {p,dir:dot>=0?1:-1,z:zt};}
function autoRamp(sel){const z=sel.z,cand=[];for(const s of ED.base.S){if(s===sel||s.pure)continue;for(let i=1;i<s.pts.length;i++){const a=s.pts[i-1],b=s.pts[i];if((a[2]-z)*(b[2]-z)<=0&&a[2]!==b[2]){const t=(z-a[2])/(b[2]-a[2]);const lo=a[2]<b[2]?a:b,hi=a[2]<b[2]?b:a;cand.push({p:[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t],dn:[lo[0]-hi[0],lo[1]-hi[1]],sid:s});}}}
 if(!cand.length)return null;const r=sel.pts.slice(0,-1).map(p=>[p[0],p[1]]);let ar=0;for(let i=0;i<r.length;i++){const p=r[i],q=r[(i+1)%r.length];ar+=p[0]*q[1]-q[0]*p[1];}if(ar<0)r.reverse();const c=ringCum(r);
 cand.sort((A,B)=>ringNear(r,c,A.p).d-ringNear(r,c,B.p).d);/* dua tepi jalan dari string berbeda (bukan titik ganda pada string yang sama) */const k=[cand[0]];for(const q of cand.slice(1)){if(q.sid!==cand[0].sid&&Math.hypot(q.p[0]-cand[0].p[0],q.p[1]-cand[0].p[1])>2&&Math.hypot(q.p[0]-cand[0].p[0],q.p[1]-cand[0].p[1])<40){k.push(q);break;}}const p=[(k[0].p[0]+(k[1]||k[0]).p[0])/2,(k[0].p[1]+(k[1]||k[0]).p[1])/2];
 if(ringNear(r,c,p).d>30)return null;const n=ringNear(r,c,p),A=ringAt(r,c,n.s),tg=[-A.n[1],A.n[0]],dot=tg[0]*k[0].dn[0]+tg[1]*k[0].dn[1];return {p,dir:dot>=0?1:-1};}
let EPK=false;$('erpk').onclick=()=>{if(!ED||ED.sel<0)return;EPK=!EPK;$('erpk').classList.toggle('on',EPK);cv.style.cursor=EPK?'crosshair':'';};
/* gambar pegangan */
/* titik string: tertutup → tanpa titik penutup; terbuka → semua titik, Z tiap titik dipertahankan */
function verts(s){return s.closed?s.pts.slice(0,-1):s.pts;}
function vz(s,p){return s.flat&&s.pure?s.z:p[2];}
window.edDraw=()=>{clr(G.edit);if(!ED||ED.sel<0||ED.out)return;const s=ED.base.S[ED.sel];G.edit.add(lineObj(s.pts.map(p=>[p[0],p[1],vz(s,p)+0.15]),COL.sel,false,{depthTest:false}));
 const U=verts(s),pv=[],pm=[],nseg=s.closed?U.length:U.length-1;for(let i=0;i<U.length;i++){const a=U[i],v=V(a[0],a[1],vz(s,a)+0.15);pv.push(v.x,v.y,v.z);}
 for(let i=0;i<nseg;i++){const a=U[i],b=U[(i+1)%U.length],m=V((a[0]+b[0])/2,(a[1]+b[1])/2,(vz(s,a)+vz(s,b))/2+0.15);pm.push(m.x,m.y,m.z);}
 const mk=(arr,tx,sz)=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(arr,3));const o=new THREE.Points(g,new THREE.PointsMaterial({size:sz,sizeAttenuation:false,map:tx,transparent:true,alphaTest:.4,depthTest:false}));o.renderOrder=10;return o;};
 G.edit.add(mk(pm,TX.y,8));G.edit.add(mk(pv,TX.w,11));
 const rp=ED.rpt||(($('erOn').checked&&ED.auto)?ED.auto.p:null);if(rp&&s.closed){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:TX.g,sizeAttenuation:false,depthTest:false}));sp.scale.set(.03,.03,1);sp.position.copy(V(rp[0],rp[1],s.z+0.4));sp.renderOrder=11;G.edit.add(sp);}};
/* seret titik + snap ke titik string target */
let DRG=null;
function vtxAt(e){const s=ED.base.S[ED.sel],U=verts(s),nseg=s.closed?U.length:U.length-1,r=R.domElement.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let bi=-1,bd=10,mi=-1,md=9;
 for(let i=0;i<U.length;i++){const q=scr(U[i][0],U[i][1],vz(s,U[i]));const d=Math.hypot(q[0]-mx,q[1]-my);if(d<bd){bd=d;bi=i;}}
 for(let i=0;i<nseg;i++){const a=U[i],b=U[(i+1)%U.length],m=scr((a[0]+b[0])/2,(a[1]+b[1])/2,(vz(s,a)+vz(s,b))/2),dm=Math.hypot(m[0]-mx,m[1]-my);if(dm<md){md=dm;mi=i;}}return {v:bi,m:bi<0?mi:-1};}
function setU(s,U){s.pts=U.map(p=>[p[0],p[1],s.flat&&s.pure?s.z:p[2]]);if(s.closed){s.pts.push(s.pts[0].slice());s.area=ringArea(s.pts);}}
function snapTarget(e,s){if(!$('esnp').checked)return null;const r=R.domElement.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let best=null,bd=+$('esnpx').value||12;
 const pools=[ED.base.S];for(const P of pools)for(const q of P){if(q===s)continue;for(const p of q.pts){const t=scr(p[0],p[1],p[2]);if(t[2]>1)continue;const d=Math.hypot(t[0]-mx,t[1]-my);if(d<bd){bd=d;best=p;}}}
 if(!best&&$('esnpt').checked&&TP.length){const p=hitTopo(e);if(p&&typeof topoSnap==='function'){const q=topoSnap(p[0],p[1],3);if(q)best=[q[0],q[1],q[2]];}}return best;}
cv.addEventListener('pointerdown',e=>{if(MODE!=='edit'||!ED||ED.sel<0||ED.out||EPICK||EPK||e.button!==0||e.target!==R.domElement||(typeof MVX!=='undefined'&&MVX.on))return;const h=vtxAt(e);if(h.v<0&&h.m<0)return;
 const s=ED.base.S[ED.sel];let U=verts(s).map(p=>p.slice());e.stopPropagation();CT.enabled=false;
 if(h.v>=0&&e.shiftKey){if(U.length>(s.closed?3:2)){U.splice(h.v,1);setU(s,U);edDraw();ED.dirty=true;edCommitSoon();}CT.enabled=true;return;}
 if(h.m>=0){const a=U[h.m],b=U[(h.m+1)%U.length];U.splice(h.m+1,0,[(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2]);setU(s,U);DRG={i:h.m+1};}else DRG={i:h.v};edDraw();},true);
let SNPM=null;
addEventListener('pointermove',e=>{if(!DRG)return;const s=ED.base.S[ED.sel],U=verts(s).map(p=>p.slice()),zv=vz(s,U[DRG.i]);let p=hitPlane(e,zv);if(!p)return;let sn=snapTarget(e,s),txt='';
 if(sn){p=[sn[0],sn[1],s.flat&&s.pure?zv:sn[2]];txt=' · <b>snap</b>';}else p=[p[0],p[1],zv];U[DRG.i]=p;setU(s,U);edDraw();
 if(sn){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:TX.b,sizeAttenuation:false,depthTest:false}));sp.scale.set(.022,.022,1);sp.position.copy(V(sn[0],sn[1],sn[2]+0.3));sp.renderOrder=12;G.edit.add(sp);}
 tip('E '+p[0].toFixed(2)+' · N '+p[1].toFixed(2)+' · RL '+f1(p[2])+txt,e);});
addEventListener('pointerup',()=>{if(!DRG)return;DRG=null;CT.enabled=true;tip(null);const s=ED.base.S[ED.sel];$('e2st').textContent=(s.closed?'RL '+f1(s.z):'string terbuka')+' · diubah';ED.dirty=true;edCommitSoon();});
/* seret / sisip / hapus titik langsung diterapkan (permukaan, string & riwayat) 0,4 s setelah dilepas — dulu baru saat tombol Selesai,
   sehingga garis string & permukaan tertinggal dari titik yang diseret dan tidak tercatat di riwayat */
let EDCT=0;function edCommitSoon(){clearTimeout(EDCT);EDCT=setTimeout(()=>{if(DRG||!ED||!ED.dirty||ED.out)return;const S=ED.base.S;try{ED.base.foot=footOf(S);ED.base.tin=surfOf(S,ED.base.foot,40);ED.base.vol=volOf(ED.base);}catch(e){console.warn(e);}ED.dirty=false;pitRedraw();try{ehPush('Seret titik string');}catch(_){}$('e2st').textContent='✓ diterapkan';},400);}
$('eund').onclick=()=>{if(!ED||ED.sel<0)return;const s=ED.base.S[ED.sel];s.pts=ED.orig.map(p=>p.slice());s.area=ringArea(s.pts);ED.out=null;pitRedraw();$('eres').innerHTML='';};
$('edone').onclick=()=>{edStopPick();EPK=false;clr(G.edit);if(ED&&ED.dirty&&!ED.out){ED.dirty=false;const S=ED.base.S;ED.base.foot=footOf(S);ED.base.tin=surfOf(S,ED.base.foot,40);ED.base.vol=volOf(ED.base);pitRedraw();}$('e2st').textContent=ED&&ED.sel>=0?'✓ RL '+f1(ED.base.S[ED.sel].z):'';};
/* perbarui bench di bawah */
function cutBelow(s,z){const out=[];let cur=[];for(let i=0;i<s.pts.length;i++){const p=s.pts[i];if(p[2]>=z-0.01){if(!cur.length&&i>0){const a=s.pts[i-1];if(a[2]<z){const t=(z-a[2])/(p[2]-a[2]);cur.push([a[0]+(p[0]-a[0])*t,a[1]+(p[1]-a[1])*t,z]);}}cur.push(p);}
  else{if(cur.length){const a=s.pts[i-1],t=(z-a[2])/(p[2]-a[2]);cur.push([a[0]+(p[0]-a[0])*t,a[1]+(p[1]-a[1])*t,z]);if(cur.length>1)out.push(cur);cur=[];}}}
 if(cur.length>1)out.push(cur);return out.map(pts=>({t:'old',z:s.z,pts,flat:false,closed:false}));}
$('ego').onclick=()=>{if(!ED){alert('Impor pit dulu.');return;}if(ED.sel<0){alert('Pilih string bench dulu (langkah 2).');return;}$('eres').innerHTML='Menghitung…';setTimeout(()=>{try{runEdit();}catch(err){console.error(err);$('eres').innerHTML='<span class="bad">Gagal: '+esc(err.message)+'</span>';}},20);};
let EUP=false;
function runEdit(){EUP=$('eup').checked;if(!ED.base.S[ED.sel].closed||!ED.base.S[ED.sel].flat)throw new Error('String terpilih adalah string terbuka/jalan — hanya bisa diedit bebas. Pilih string bench tertutup untuk membentuk ulang bench di bawahnya.');const S=ED.base.S,s=S[ED.sel],z=s.z,type=$('ety').value,p=prmAt(z-0.01);const U=s.pts.slice(0,-1);let C=cClean(ClipperLib.Clipper.SimplifyPolygons([toC(U)],ClipperLib.PolyFillType.pftNonZero));
 if(type==='toe')C=cOff(C,-p.B);if(!C.length)throw new Error('string terlalu kecil');
 const rp=RAMP();let start=null,mode=null,ms=null;if($('erOn').checked){start=ED.rpt||(ED.auto&&ED.auto.p);if(!ED.rpt&&ED.auto)rp.dir=ED.auto.dir;}/* jalan lama mulai di bawah string ini: tetap dibangun ulang dari RL awalnya */let low=null;if(!start&&$('ekeep')&&$('ekeep').checked){low=edRoadBelow(s);if(low){start=low.p;rp.dir=low.dir;}}rp.on=!!start;
 if(start&&ED.auto&&$('eadp').checked){ms=rampMeasure(s,ED.auto);if(ms){if(!ED.fromRes){if(isFinite(ms.g)&&ms.g>0.02&&ms.g<0.3)rp.g=ms.g;if(isFinite(ms.W)&&ms.W>4&&ms.W<40)rp.W=ms.W;}mode=ms.mode;}}
 const R0={ai:0,nm:'A',pt:start,strike:ms&&ms.v,dir:rp.dir,sbs:[],sbEnd:false,on:true,first:false};if(low){R0.zE=low.z;delete R0.first;ED.lowRoad=low;}else ED.lowRoad=null;if(mode==='free'&&ms&&ms.v){Object.assign(R0,{free:true,p0:start,v:ms.v,zs:z});}
 /* pit dari tab Desain baru dengan batas topo: bagian sisi rendah (topo < RL) tetap mengikuti proyeksi batas asli, dan staging tetap dijaga pit final — supaya membangun ulang tidak membuang sisi rendah */const xo={};ED.keepLow=false;if(ED.fromRes&&BASE&&BASE.mode==='topo'&&TP.length){try{const ts=topoStart();xo.proj=ts.proj;ED.keepLow=true;}catch(_){}}if(ED.fromRes==='stage'&&FIN){try{const CL=finClamp();if(CL){xo.clamp=CL;xo.lim=limAt;xo.noAdopt=true;}}catch(_){}}
 const d=genDown(C,z,Object.assign({ramps:start?[R0]:[],zref:ED.zref,zmin:ED.zmin,rp,mode:mode||undefined},xo));ED.lastRamp=ms?{W:rp.W,g:rp.g,mode}:null;
 const selRing=s.pts.map(p=>[p[0],p[1]]),origRing=ED.orig.map(p=>[p[0],p[1]]);const keep=[];
 let UPS=[],Bup=[];if(EUP){/* bench di atas ikut: bangun ulang ke atas dari string terpilih */const pu=prmAt(z+0.01);let T0=cClean(ClipperLib.Clipper.SimplifyPolygons([toC(U)],ClipperLib.PolyFillType.pftNonZero));if(type==='crest'&&isBerm(z,ED.zref,pB(pu,z)))T0=offS(T0,1,z,'B',pu);
  let ztop=-1e9;for(const q of S)if(q.flat)ztop=Math.max(ztop,q.z);const u=genUp(T0,z,{ramps:[],zref:ED.zref,zmax:ztop});Bup=u.B;UPS=benchStrings(Bup,null).filter(q=>!(q.t==='toe'&&Math.abs(q.z-z)<0.01));}
/* hanya string di area yang diedit yang diganti; area lain (mis. Area 2) tetap */
 const fracIn=(q,rings)=>{let n=0;for(const p of q.pts)if(rings.some(r=>inPoly(p,r)))n++;return n/Math.max(1,q.pts.length);};
 const selR=[selRing,origRing],upAt=zz=>{const b=Bup.find(b=>Math.abs(b.zc-zz)<0.05)||Bup.find(b=>Math.abs(b.zt-zz)<0.05);return b?(Math.abs(b.zc-zz)<0.05?b.crest:b.toe).filter(r=>cArea(r)>0).map(ringOf):null;};
 const upTop=Bup.length?Bup[Bup.length-1].crest.filter(r=>cArea(r)>0).map(ringOf):[];
 if(EUP&&type==='crest')keep.push({t:'crest',z,pts:s.pts.map(p=>p.slice())});
 S.forEach((q,j)=>{if(ED.drop&&ED.drop.includes(j))return;/* string terbuka yang sudah digabung ke cincinnya */if(j===ED.sel){if(type==='toe')keep.push({t:'toe',z,pts:q.pts.map(p=>p.slice())});return;}
  if(q.flat){if(q.z>z+0.2){if(!EUP)keep.push(q);else{const R=upAt(q.z);if(!R||fracIn(q,R.map(r=>r))<0.5)keep.push(q);}}
   else if(Math.abs(q.z-z)<=0.2){const f=q.pts[0];if(!(inPoly(f,selRing)||inPoly(f,origRing))||q.area>s.area+20)keep.push(q);}
   else if(fracIn(q,selR)<0.5)keep.push(q);return;}
  let zmn=1e9,zmx=-1e9;for(const p of q.pts){zmn=Math.min(zmn,p[2]);zmx=Math.max(zmx,p[2]);}const inSel=fracIn(q,selR)>0||(upTop.length&&fracIn(q,upTop)>0.5);
  if(!inSel){keep.push(q);return;}if(EUP&&zmn>z-0.05&&upTop.length&&fracIn(q,upTop)>0.5)return;if(EUP&&zmx>z+0.05&&upTop.length&&fracIn(q,upTop)>0.5)return;keep.push(...cutBelow(q,z));});
 const B=d.B.slice().reverse().concat(Bup);const NS=benchStrings(d.B.slice().reverse(),d.floor).concat(UPS);const all=keep.concat(NS),foot=footOf(all.filter(q=>q.t!=='old'||q.closed)),tin=surfOf(all,foot);
 let zmin=1e9;for(const q of NS)for(const pp of q.pts)zmin=Math.min(zmin,pp[2]);
 ED.out={S:all,foot,tin,zmin:Math.min(zmin,z),floorS:NS.filter(q=>q.t==='floor'),B};ED.out.vol=volOf(ED.out);ED.out.day=dayOf(ED.out);dayDraw(ED.out);layRender();ED.out.kpi={n:B.length};clr(G.edit);pitRedraw();
 /* beda volume vs pit lama */
 let dv=0,cell=ED.out.vol.cell;const Fp=ED.out.foot;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const r of Fp)for(const q of r){x0=Math.min(x0,q[0]);x1=Math.max(x1,q[0]);y0=Math.min(y0,q[1]);y1=Math.max(y1,q[1]);}
 for(let y=y0+cell/2;y<y1;y+=cell)for(let x=x0+cell/2;x<x1;x+=cell){if(!inFoot(Fp,x,y))continue;const zn=gridZ(tin.G,x,y);let zo=gridZ(ED.base.tin.G,x,y);const zt=topoZ(x,y);if(!isFinite(zn))continue;if(!isFinite(zo))zo=isFinite(zt)?zt:zn;let a=Math.min(zo,isFinite(zt)?zt:1e9),b=Math.min(zn,isFinite(zt)?zt:1e9);dv+=(a-b)*cell*cell;}
 let h='<div class="kpi"><div><b>'+B.length+'</b><span>bench baru</span></div><div><b>'+(dv>=0?'+':'')+nf(dv)+'</b><span>m³ vs pit lama</span></div><div><b>'+f1(ED.out.zmin)+'</b><span>RL lantai</span></div></div>';
 h+=(EUP?'Bench di atas RL '+f1(z)+' ikut dibangun ulang ('+Bup.length+' bench). ':'Bench di atas RL '+f1(z)+' tidak diubah. ')+(rp.on&&ED.lowRoad?'Jalan lama dipertahankan: dibangun ulang mulai RL '+f1(ED.lowRoad.z)+' (batas string yang diedit tetap; jalan memakan ke dalam).':rp.on?'Jalan dilanjutkan '+(ED.lastRamp?'mengikuti jalan lama ('+{zig:'lurus + switchback',spiral:'spiral',free:'lurus'}[ED.lastRamp.mode]+', '+f1(ED.lastRamp.W)+' m, '+(ED.lastRamp.g*100).toFixed(1)+'%)':(rp.dir>0?'berlawanan':'searah')+' jarum jam')+'.':'Tanpa jalan baru.');for(const w of d.warn)h+='<br><span class="warn">⚠ '+esc(w)+'</span>';
 h+='<br><a href="#" id="eohw">Volume per bench</a> · <a href="#" id="eoxw">Ekspor</a> · <a href="#" id="eagain">Ubah lagi</a> · <a href="#" id="eacc"><b>Terima &amp; edit lanjut</b></a>';$('eres').innerHTML=h;$('e3st').textContent='✓';
 $('eohw').onclick=ev=>{ev.preventDefault();winShow($('hw'),true);};$('eoxw').onclick=ev=>{ev.preventDefault();winShow($('xw'),true);};$('eagain').onclick=ev=>{ev.preventDefault();ED.out=null;pitRedraw();$('eres').innerHTML='';};$('eacc').onclick=ev=>{ev.preventDefault();edAccept();};
 if($('hw').style.display==='block')hwFill();}

/* pakai hasil desain sekarang sebagai pit yang diedit */
$('efrom').onclick=()=>{const R0=window.__DK==='stage'?STG:(RES||STG);if(!R0){alert('Belum ada hasil di tab Desain baru.');return;}const L=R0.S.filter(s=>s.t!=='road'||true).map(s=>s.pts.map(p=>p.slice()));edLoad(L,(R0===STG?'Hasil staging':'Hasil pit final')+' ('+$('pjn').textContent+')',R0);if(ED)ED.fromRes=R0===STG?'stage':'new';};
/* luruskan string terpilih: buang taji/takik & titik zig-zag */
/* garis terbuka (jalan, potongan string Surpac): ujung dikunci supaya sambungan tidak lepas; RL tiap titik diinterpolasi sepanjang garis */
function straightOpen(P0,r){let P=P0.map(p=>p.slice());const ang=(a,b,c)=>{const u=[b[0]-a[0],b[1]-a[1]],v=[c[0]-b[0],c[1]-b[1]],lu=Math.hypot(u[0],u[1])||1e-9,lv=Math.hypot(v[0],v[1])||1e-9;return {c:(u[0]*v[0]+u[1]*v[1])/(lu*lv),lu,lv};};
 /* 1. taji: titik tempat garis berbalik tajam (< 30°) dengan kaki pendek */for(let it=0;it<5;it++){let ch=false;for(let i=1;i<P.length-1;i++){const g=ang(P[i-1],P[i],P[i+1]);if(g.c<-0.866&&Math.min(g.lu,g.lv)<3*r){P.splice(i,1);ch=true;i--;}}if(!ch)break;}
 /* 2. zig-zag kecil */if(P.length>2)P=rdpL(P,Math.min(0.4*r,1));
 /* 3. bulatkan sudut: busur kuadratik antara titik singgung */if(P.length<3)return P;const O=[P[0]];for(let i=1;i<P.length-1;i++){const a=P[i-1],b=P[i],c=P[i+1],g=ang(a,b,c);const th=Math.acos(Math.max(-1,Math.min(1,g.c)));if(th<0.15){O.push(b);continue;}let t=Math.min(r*Math.tan(th/2),0.45*g.lu,0.45*g.lv);
  const p0=[b[0]+(a[0]-b[0])*t/g.lu,b[1]+(a[1]-b[1])*t/g.lu,b[2]+(a[2]-b[2])*t/g.lu],p2=[b[0]+(c[0]-b[0])*t/g.lv,b[1]+(c[1]-b[1])*t/g.lv,b[2]+(c[2]-b[2])*t/g.lv],m=Math.max(2,Math.ceil(th/0.35));for(let k=0;k<=m;k++){const u=k/m,w0=(1-u)*(1-u),w1=2*u*(1-u),w2=u*u;O.push([w0*p0[0]+w1*b[0]+w2*p2[0],w0*p0[1]+w1*b[1]+w2*p2[1],w0*p0[2]+w1*b[2]+w2*p2[2]]);}}
 O.push(P[P.length-1]);return O;}
$('estr').onclick=()=>{if(!ED||ED.sel<0){alert('Pilih string dulu.');return;}if(!ED.base.S[ED.sel].closed){const s=ED.base.S[ED.sel],r=Math.max(0.3,+$('esr').value||2),n0=s.pts.length;const U=straightOpen(s.pts,r);s.pts=U;ED.out=null;ED.dirty=true;edDraw();$('e2st').textContent='string terbuka · diluruskan';$('eseli').innerHTML+='<br><span class="ok">Diluruskan: '+n0+' → '+U.length+' titik (ujung tetap di tempat).</span>';return;}const s=ED.base.S[ED.sel],r=Math.max(0.3,+$('esr').value||2);let P=cClean(ClipperLib.Clipper.SimplifyPolygons([toC(s.pts.slice(0,-1))],ClipperLib.PolyFillType.pftNonZero));
 const k0=CORNER;CORNER='round';let Q=cOff(cOff(P,r),-r);Q=cOff(cOff(Q,-r),r);CORNER=k0;if(!Q.length)return;let best=Q[0];for(const q of Q)if(Math.abs(cArea(q))>Math.abs(cArea(best)))best=q;
 best=ClipperLib.Clipper.CleanPolygon(best,Math.min(r*0.4,1)*CS);const U=ringOf(best).map(p=>[p[0],p[1],s.z]);setU(s,U);ED.out=null;ED.dirty=true;edDraw();$('e2st').textContent='RL '+f1(s.z)+' · diluruskan';};

/* ---------- perdalam pit: tambah bench di bawah lantai sekarang ---------- */
function edFloor(){if(!ED)return null;const S=ED.base.S;let zf=1e9;for(const s of S)if(s.flat&&s.closed&&s.pure)zf=Math.min(zf,s.z);if(zf>1e8)return null;const fl=S.filter(s=>s.flat&&s.closed&&s.pure&&Math.abs(s.z-zf)<0.05);return {z:zf,S:fl};}
setInterval(()=>{const f=edFloor();const el=$('edfl');if(el)el.textContent=f?'RL '+f1(f.z)+' ('+f.S.length+' poligon)':'–';},1000);
$('edgo').onclick=()=>{if(!ED){alert('Impor pit atau pakai hasil Desain baru dulu.');return;}const zt=parseFloat($('edz').value),f=edFloor();if(!f){alert('Lantai pit tidak ditemukan (string datar tertutup terendah).');return;}
 if(!isFinite(zt)||zt>=f.z-0.5){alert('RL lantai baru harus lebih rendah dari RL '+f1(f.z)+'.');return;}$('edres').innerHTML='Menghitung…';setTimeout(()=>{try{runDeepen(f,zt);}catch(err){console.error(err);$('edres').innerHTML='<span class="bad">Gagal: '+esc(err.message)+'</span>';}},20);};
function oldSec(S,z,kind){let T=[],Cc=[];const L=S.filter(s=>s.flat&&s.pure&&s.closed&&Math.abs(s.z-z)<0.05);for(const s of L){const P=cClean(ClipperLib.Clipper.SimplifyPolygons([toC(s.pts.slice(0,-1))],ClipperLib.PolyFillType.pftNonZero));const inner=L.some(q=>q!==s&&q.area<s.area-5&&inPoly(q.pts[0],s.pts));if(inner)T=T.length?cUnion(T,P):P;else{Cc=Cc.length?cUnion(Cc,P):P;}}
 if(!T.length)T=Cc;if(!Cc.length)Cc=T;return kind==='T'?T:Cc;}
function runDeepen(f,zt){const S=ED.base.S,z=f.z;let C=[];for(const s of f.S){const P=cClean(ClipperLib.Clipper.SimplifyPolygons([toC(s.pts.slice(0,-1))],ClipperLib.PolyFillType.pftNonZero));C=C.length?cUnion(C,P):P;}
 /* sump: perdalam hanya di dalam poligon; lantai lama tetap, tanpa pushback */const SZ=ED.dzone&&ED.dzone.length?ED.dzone:null;if(SZ){C=cInter(C,SZ).filter(r=>Math.abs(cArea(r))>1);if(!C.length)throw new Error('Poligon sump tidak memotong lantai RL '+f1(z)+'.');}
 /* lebar yang dibutuhkan agar lantai baru >= lantai minimum: dorong dinding lama bila perlu (pushback) */
 const p0=prmAt(z-0.01),n=Math.ceil((z-zt)/p0.H-1e-6),F=PN().F,rpw=RAMP().W;const wantR=!SZ||$('edzr').checked;let need=F+2*n*p0.a+(wantR?rpw:0)+Math.floor(n/Math.max(1,p0.N))*2*p0.B,wd=cWidth(C),delta=SZ?0:Math.max(0,(need-wd)/2);
 let Cn=delta>0.05?cOff(C,delta):C,UP=[],zstop=z;
 /* baca jalan lama dari ujung bawahnya */let best=null;for(const s of S){if(s.pure||s.closed)continue;for(const p of s.pts)if(Math.abs(p[2]-z)<2){if(!best||p[2]<best[2])best=p;}}
 const rp=RAMP();let ms=null,mode,v=null;if(best){ms=rampMeasure({z:z+80,pts:[]},{p:[best[0],best[1]]});if(ms){if(isFinite(ms.g)&&ms.g>0.02&&ms.g<0.3)rp.g=ms.g;if(isFinite(ms.W)&&ms.W>4&&ms.W<40)rp.W=ms.W;mode=ms.mode;v=ms.v;}}
 const mk=(pt,vv,zs)=>{const d=dirFromVec(Cn,pt,vv);const R0={ai:0,nm:'A',pt:d.pt,strike:vv,dir:d.dir,sbs:[],sbEnd:false,on:true,first:false};if(mode==='free')Object.assign(R0,{free:true,p0:d.pt,v:vv,zs});return R0;};
 if(delta>0.05){/* pushback: bangun ke atas dari lantai yang dilebarkan, jalan dibuat ulang meniru jalan lama, sampai menyatu dengan desain lama */
  let st={up:true,P:Cn,z,pend:[]},rr=best&&v?[mk([best[0],best[1]],[-v[0],-v[1]],z)]:[];
  for(let i=0;i<120;i++){const r=benchStep(st,rr,{zref:ED.zref,rp,mode});if(r.stop||!r.bench)break;const zc=r.bench.zc,oc=oldSec(S,zc,'C');let cr=oc.length?cUnion(r.bench.crest,oc):r.bench.crest;
   let a0=0,a1=0;for(const q of cr)a0+=Math.abs(cArea(q));for(const q of oc)a1+=Math.abs(cArea(q));r.bench.crest=cr;UP.push(r.bench);zstop=zc;if(oc.length&&a0-a1<3)break;if(!oc.length&&crestOut(cr,zc))break;
   const ot=oldSec(S,zc,'T');let nt=r.next.P;if(ot.length)nt=cUnion(nt,ot);st={up:true,P:nt,z:zc,pend:[]};rr=r.ramps;}}
 let ramps=wantR&&best&&v?[mk([best[0],best[1]],v,z)]:[];if(SZ&&wantR&&best&&!C.some(r=>inPoly([best[0],best[1]],ringOf(r)))){/* jalan sump mulai dari titik dinding sump terdekat ke ujung jalan lama */let q=null,dq=1e18;for(const r of C)for(const p of ringOf(r)){const d=Math.hypot(p[0]-best[0],p[1]-best[1]);if(d<dq){dq=d;q=p;}}if(q){const cx=C.map(ringOf)[0].reduce((a,p,_,A)=>[a[0]+p[0]/A.length,a[1]+p[1]/A.length],[0,0]);ramps=[mk(q,[cx[0]-q[0],cx[1]-q[1]],z)];}}
 if(SZ&&ramps.length&&!window.__SUMPOLD){/* jalan sump mengitari dinding sump (spiral), bukan lurus menyeberangi lantai menuju titik tengah (pemilik 16 Nov) */mode='spiral';const R0=ramps[0];delete R0.free;delete R0.p0;delete R0.v;delete R0.zs;}
 const gd_=(m,rr)=>genDown(Cn,z,Object.assign({ramps:rr,zref:ED.zref,zmin:zt,rp,mode:m},SZ?{F:+$('edzf').value||0,FA:0}:{}));let d=gd_(mode,ramps),sumpSB='';
 if(SZ&&ramps.length&&mode==='spiral'&&!window.__SUMPOLD){/* spiral mentok (tidak sampai lantai target / jalan tidak sampai dasar) → coba switchback, ambil yang lebih dalam */
  const ok=x=>{if(!x||!x.B.length)return {z:1e9,road:false};const Bs=x.B.slice().sort((a,b)=>a.zt-b.zt),zf=Bs[0].zt;const zr=Math.min(...Bs.filter(b=>(b.roads||[]).length).map(b=>b.zt));return {z:zf,road:isFinite(zr)&&zr<=zf+0.1};};
  const a=ok(d);if(a.z>zt+0.01||!a.road){try{const R1=Object.assign({},ramps[0],{sbs:[],sbEnd:false});const d2=gd_('zig',[R1]),b=ok(d2);if(b.z<a.z-0.01||(Math.abs(b.z-a.z)<0.01&&b.road&&!a.road)){d=d2;mode='zig';sumpSB='Jalan sump mengitari dinding tidak muat sampai RL '+f1(zt)+' — dipakai switchback (menyusuri dinding lalu berbalik). ';}}catch(e){console.warn(e);}}}const B=d.B.slice().reverse();if(!B.length)throw new Error(d.warn[0]||'tidak ada bench yang bisa dibuat');
 const NS=benchStrings(B,d.floor).concat(UP.length?benchStrings(UP,null).filter(q=>!(q.t==='toe'&&Math.abs(q.z-z)<0.01)):[]);
 /* string lama: buang lantai lama & string datar di zona pushback; jalan lama di zona pushback dipotong */
 const keep=[];for(const s of S){if(f.S.includes(s)&&!SZ)continue;if(s.flat&&s.pure){if(UP.length&&s.z<zstop-0.05)continue;if(UP.length&&Math.abs(s.z-zstop)<0.05){const crs=UP[UP.length-1].crest;let inside=true;for(const p of s.pts)if(!crs.some(r=>inPoly(p,ringOf(r)))){inside=false;break;}if(inside&&s.area<1e9)continue;}keep.push(s);}else keep.push(...(UP.length?cutBelow(s,zstop):[s]));}
 const all=keep.concat(NS),foot=footOf(all.filter(q=>q.t!=='old'||q.closed)),tin=surfOf(all,foot);
 let zmin=1e9;for(const q of NS)for(const p of q.pts)zmin=Math.min(zmin,p[2]);
 ED.out={S:all,foot,tin,zmin,floorS:NS.filter(q=>q.t==='floor'),B:B.concat(UP)};ED.out.vol=volOf(ED.out);ED.out.day=dayOf(ED.out);ED.out.kpi={n:B.length+UP.length};clr(G.edit);pitRedraw();dayDraw(ED.out);layRender();
 const dv=ED.out.vol.tot-(ED.base.vol?ED.base.vol.tot:0);let rl=0;for(const b of B)for(const r of (b.roads||[]))for(let i=1;i<r.in.length;i++)rl+=Math.hypot(r.in[i][0]-r.in[i-1][0],r.in[i][1]-r.in[i-1][1]);
 let h='<div class="kpi"><div><b>'+B.length+'</b><span>bench baru di bawah</span></div><div><b>+'+nf(dv)+'</b><span>m³ tambahan</span></div><div><b>'+f1(zmin)+'</b><span>RL lantai baru</span></div></div>';
 h+='Lantai RL '+f1(z)+' → '+f1(zmin)+'. '+(UP.length?'<b>Pushback:</b> lantai lama dilebarkan '+f1(delta)+' m agar muat; dinding RL '+f1(z)+'–'+f1(zstop)+' ('+UP.length+' bench) disesuaikan, di atas RL '+f1(zstop)+' desain lama tetap. ':'Desain lama tidak berubah. ');
 h+=sumpSB+(ramps.length?'Jalan diteruskan '+nf(rl)+' m'+(ms?' meniru jalan lama ('+({zig:'lurus + switchback',spiral:'spiral',free:'lurus'}[mode]||'')+', '+f1(rp.W)+' m, '+(rp.g*100).toFixed(1)+'%)':'')+'.':'Tidak ada jalan lama — bench tanpa jalan.');
 if(zmin>zt+0.5)h+='<br><span class="warn">⚠ Berhenti di RL '+f1(zmin)+' sebelum target '+f1(zt)+'.</span>';for(const w of d.warn)h+='<br><span class="warn">⚠ '+esc(w)+'</span>';
 h+='<br><a href="#" id="edhw">Volume per bench</a> · <a href="#" id="edxw">Ekspor</a> · <a href="#" id="edun">Batalkan</a>';$('edres').innerHTML=h;$('e4st').textContent='✓ RL '+f1(zmin);
 $('edhw').onclick=e=>{e.preventDefault();winShow($('hw'),true);};$('edxw').onclick=e=>{e.preventDefault();winShow($('xw'),true);};$('edun').onclick=e=>{e.preventDefault();ED.out=null;pitRedraw();$('edres').innerHTML='';$('e4st').textContent='';};}

/* jadikan hasil edit sebagai pit dasar agar bisa diedit lagi (mis. merapikan string jalan) */
function edAccept(){if(!ED||!ED.out)return;const R0=ED.out,nm=ED.nm;edLoad(R0.S.map(q=>q.pts.map(p=>p.slice())),nm,R0);$('eres').innerHTML='<span class="ok">Hasil diterima — sekarang bisa memilih string lain (termasuk string jalan) untuk diedit.</span>';}
window.__vtx=(x,y)=>vtxAt({clientX:x,clientY:y});window.__drg=()=>DRG;

/* poligon pembatas pendalaman (sump) */
function edzDraw(){if(!G.edz){G.edz=new THREE.Group();W.add(G.edz);}clr(G.edz);const f=edFloor();if(!ED||!ED.dzone)return;const z=f?f.z:0;for(const r of ED.dzone)G.edz.add(Object.assign(lineObj(frC(r,z+0.3),'#e8590c',true,{depthTest:false}),{renderOrder:9}));}
$('edzb').onclick=()=>{if(!ED){alert('Impor pit atau pakai hasil Desain baru dulu.');return;}const f=edFloor();if(!f){alert('Lantai pit tidak ditemukan.');return;}$('edz').dataset.k=1;
digStart('poly',ring=>{const P=cClean(ClipperLib.Clipper.SimplifyPolygons([toC(ring)],ClipperLib.PolyFillType.pftNonZero));ED.dzone=ED.dzone&&ED.dzone.length?cUnion(ED.dzone,P):P;edzDraw();let A=0;for(const r of ED.dzone)A+=Math.abs(cArea(r));$('edzi').innerHTML='Sump: '+ED.dzone.length+' poligon · '+nf(A)+' m² — hanya lantai di dalamnya yang diperdalam; lantai lama tetap.';});
 if(DG)DG.zp=f.z;$('edzi').innerHTML='<b>Gambar poligon sump</b> di denah lantai RL '+f1(f.z)+' — klik titik, Enter = selesai.';};
$('edzc').onclick=()=>{if(ED)ED.dzone=null;edzDraw();$('edzi').innerHTML='';};
/* klik ganda pada string di 3D = langsung pilih string untuk diedit (tanpa tombol) */
cv.addEventListener('dblclick',e=>{if(MODE!=='edit'||!ED||DG||EPK)return;EPICK=true;window.edClick(e);if(EPICK)edStopPick();});

/* ================= Push Back / Shrinkage =================
 Seluruh desain lama digeser horizontal (bukan dibangun ulang) sehingga POLA JALAN TETAP:
  - string bench tertutup (crest/toe/lantai): offset ±d (global = offset tepat; dengan poligon = digeser penuh di dalam poligon,
    meruncing ke 0 dalam jarak transisi di luar poligon agar dinding tetap menyambung)
  - string jalan / miring: tiap titik digeser searah normal keluar bench terdekat sejauh pergeseran di titik itu → bentuk,
    lebar & kemiringan jalan dipertahankan; jalan tetap menempel di dindingnya
  - Push Back: bila crest teratas kini di bawah topografi, bench ditambah ke atas (geoteknik aktif) sampai topografi,
    jalan diteruskan dari ujung atasnya meniru pola lama
  - Shrinkage: lantai dicek terhadap lantai minimum; bagian di atas topografi terpotong otomatis */
function runResize(kind,d){/* berantai: hasil push back / shrinkage sebelumnya yang belum dijadikan dasar otomatis diterima dulu, supaya sisi lain bisa diubah tanpa kehilangan hasil pertama */let chained=false;if(ED&&ED.out&&ED.lastResize){const dz=ED.dzone,zu=ED.zoneUsed;edAccept();ED.dzone=dz;ED.zoneUsed=zu;chained=true;try{edzDraw();}catch(_){}}const S=ED.base.S;let f=edFloor();if(!f){/* desain terbuka (mis. staging Surpac): lantai = string datar terendah */let zf=1e9;for(const q of S)if(q.flat)zf=Math.min(zf,q.z);if(zf>1e8)throw new Error('Tidak ada string bench datar.');f={z:zf,S:[],open:true};}const sg=kind==='push'?1:-1,Z=ED.dzone&&ED.dzone.length?ED.dzone:null,F=PN().F;
 let ZR=Z?Z.map(ringOf):null,T=Math.max(2*d,20);
 const segD=(p,a,b)=>{const dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2));return Math.hypot(p[0]-a[0]-dx*t,p[1]-a[1]-dy*t);};
 const w=p=>{if(!ZR)return 1;if(ZR.some(r=>inPoly(p,r)))return 1;let m=1e9;for(const r of ZR)for(let i=0;i<r.length;i++)m=Math.min(m,segD(p,r[i],r[(i+1)%r.length]));return Math.max(0,1-m/T);};
 const near=(R,p)=>{let bd=1e18,q=null;for(const r of R)for(let i=0;i<r.length;i++){const a=r[i],b=r[(i+1)%r.length],dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2)),x=a[0]+dx*t,y=a[1]+dy*t,e=Math.hypot(p[0]-x,p[1]-y);if(e<bd){bd=e;q=[x,y];}}return q;};
 /* 1. semua string digeser dengan medan geser yang SAMA (dari bentuk dinding yang dihaluskan) → bench & jalan tetap berimpit */const flatC=S.filter(s=>s.flat&&s.closed&&s.pts.length>3),NS=[],moved=new Set();
 const lv=[...new Set(S.filter(q=>q.flat).map(s=>Math.round(s.z*100)/100))].sort((a,b)=>a-b),ringsAt=new Map();for(const z of lv)ringsAt.set(z,flatC.filter(s=>Math.abs(s.z-z)<0.01).map(s=>s.pts.slice(0,-1)));

 /* bentuk dinding dihaluskan (tanpa takik jalan) → vektor geser q'−q dari cincin halus ke offset-nya; lalu dihaluskan sepanjang string */const W0=RAMP().W,RS=new Map();const rsAt=z=>{if(RS.has(z))return RS.get(z);const rz=ringsAt.get(z)||[];const P=rz.length?cBool(rz.map(r=>toC(r)),[],ClipperLib.ClipType.ctUnion):tinSec(ED.base.tin,z);const c0=CORNER;CORNER='round';let A0=cOff(cOff(P,W0),-W0);A0=cOff(cOff(A0,-W0),W0);if(!A0.length)A0=P;const A1=cOff(A0,sg*d);CORNER=c0;const v={a:A0.filter(r=>cArea(r)>0).map(ringOf),b:A1.filter(r=>cArea(r)>0).map(ringOf)};RS.set(z,v);return v;};
 /* SATU medan geser untuk semua RL: arah = normal keluar dari cincin acuan (lantai yang dibulatkan). Semua titik pada kolom vertikal
   yang sama bergeser sama → string tidak pernah saling memotong, bench & jalan tetap sejajar seperti desain lama */
 let RefP=f.S.length?cBool(f.S.map(q=>toC(q.pts.slice(0,-1))),[],ClipperLib.ClipType.ctUnion):tinSec(ED.base.tin,f.z+0.5);{const c0=CORNER;CORNER='round';const rr=Math.max(W0,d+5);let A0=cOff(cOff(RefP,rr),-rr);const ro=window.__ROPEN0?rr*0.5:Math.min(rr*0.5,7.5);/* opening tidak ikut membesar dengan d: dulu shrinkage 35 m membuang ujung lantai sempit dari acuan → bobot geser 0 di dalam poligon */A0=cOff(cOff(A0,-ro),ro);CORNER=c0;if(A0.length)RefP=A0;}
 const REF=RefP.filter(r=>cArea(r)>0).map(ringOf);
 /* kuas Play-Doh: wilayah pengaruh = lingkaran kuas di titik-titik sapuan yang diproyeksikan ke tepi lantai (acuan kolom), transisi ½ jari-jari */
 if(ED.brush&&REF.length){const r=ED.brush.r,C=[];for(const p of ED.brush.pts){const q=near(REF,p);if(!q)continue;const c=[];for(let k=0;k<24;k++){const t=k/24*2*Math.PI;c.push([q[0]+r*Math.cos(t),q[1]+r*Math.sin(t)]);}C.push(toC(c));}if(!C.length)throw new Error('Sapuan kuas tidak mengenai dinding pit.');ZR=cBool(C,[],ClipperLib.ClipType.ctUnion).filter(r=>cArea(r)>0).map(ringOf);T=Math.max(8,0.5*r);}
 const vec=p=>{if(!REF.length)return [0,0];const q=near(REF,p);let dx=p[0]-q[0],dy=p[1]-q[1],L=Math.hypot(dx,dy);const inside=REF.some(r=>inPoly(p,r));
  if(L<0.5){/* di atas cincin: pakai normal tepi terdekat */let bd=1e18,nn=[0,0];for(const r of REF)for(let k=0;k<r.length;k++){const a=r[k],b=r[(k+1)%r.length],ex=b[0]-a[0],ey=b[1]-a[1],l2=ex*ex+ey*ey||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*ex+(p[1]-a[1])*ey)/l2)),e=Math.hypot(p[0]-a[0]-ex*t,p[1]-a[1]-ey*t);if(e<bd){bd=e;const l=Math.sqrt(l2);nn=[ey/l,-ex/l];}}
   let ar=0;for(const r of REF)for(let k=0;k<r.length;k++){const a=r[k],b=r[(k+1)%r.length];ar+=a[0]*b[1]-b[0]*a[1];}if(ar<0)nn=[-nn[0],-nn[1]];dx=nn[0];dy=nn[1];L=1;}
  else if(inside){dx=-dx;dy=-dy;}/* bobot poligon dinilai di TEPI LANTAI (titik acuan q), bukan di titik itu sendiri: semua bench & jalan pada satu garis keluar dari lantai bergeser sama → jarak antar bench, lebar berm & lebar jalan tidak terhimpit di zona transisi */const ww=w(q)*sg*d/L;return [dx*ww,dy*ww];};window.__VEC=p=>{const q=REF.length?near(REF,p):null;return {v:vec(p),q,wq:q?w(q):null,wp:w(p)};};;

 const smooth=(V,cl)=>window.__NOSM?V:V.map((_,i)=>{let x=0,y=0,n=0;for(let k=-4;k<=4;k++){let j=i+k;if(cl)j=(j+V.length)%V.length;else if(j<0||j>=V.length)continue;x+=V[j][0];y+=V[j][1];n++;}return [x/n,y/n];});
 for(const s of flatC){const src=s.pts.slice(0,-1);const dense=densify(src.concat([src[0]]).map(q=>[q[0],q[1],s.z]),2);dense.pop();const V=smooth(dense.map(vec),true);
  let Q=[toC(dense.map((v,i)=>[v[0]+V[i][0],v[1]+V[i][1]]))];Q=cClean(ClipperLib.Clipper.SimplifyPolygons(Q,ClipperLib.PolyFillType.pftNonZero));Q=tidy(Q).filter(r=>Math.abs(cArea(r))>1);
  moved.add(s);for(const r of Q)NS.push({t:f.S.includes(s)?'floor':'old',z:s.z,pts:ringPts(r,s.z),flat:true,pure:true,closed:true,area:Math.abs(cArea(r))});}
 /* shrinkage melebihi lebar lantai setempat: cincin yang digeser ke dalam saling menumpuk lalu dibersihkan kembali ke bentuk luar → pit tidak menyempit
    (16 Nov, pit final Z3: 10 m → lantai 6.159 m², 20 m → 6.646 m² dari 6.651). Medan geser sebanding dengan d, jadi jarak maksimum dicari pada cincin lantai. */
 if(sg<0&&!window.__NODMAX){const fr=flatC.filter(q=>f.S.includes(q));if(fr.length){const AR=k=>{let a=0;for(const q of fr){const src=q.pts.slice(0,-1),dn=densify(src.concat([src[0]]).map(p=>[p[0],p[1],q.z]),2);dn.pop();const V=smooth(dn.map(vec),true);let Q=[toC(dn.map((v,i)=>[v[0]+V[i][0]*k,v[1]+V[i][1]*k]))];Q=cClean(ClipperLib.Clipper.SimplifyPolygons(Q,ClipperLib.PolyFillType.pftNonZero));Q=tidy(Q).filter(r=>Math.abs(cArea(r))>1);for(const r of Q)a+=Math.abs(cArea(r));}return a;};
  const st=Math.max(0.5,d/40);let am=AR(0),dm=0;const DBG=[[0,Math.round(am)]];for(let x=st;x<=d+1e-6;x+=st){const a=AR(x/d);DBG.push([+x.toFixed(1),Math.round(a)]);if(a<am-0.5){am=a;dm=x;}}window.__DMAX={DBG,fr:fr.length,flatC:flatC.length,fS:f.S.length};
  if(dm<d-Math.max(1,0.1*d)){const rec=Math.max(0.5,Math.floor(dm*0.9*2)/2);if(ED.brush)throw new Error('Sapuan tarik '+f1(d)+' m terlalu kuat untuk bentuk lantai di bawah kuas: lantai di bagian tersempit tidak muat ditarik sejauh itu (lantai terkecil tercapai pada ±'+f1(dm)+' m).\n\nSaran: kekuatan per sapuan '+f1(Math.max(0.5,Math.floor(dm*0.9*2)/2))+' m, lalu sapukan lagi bila perlu, atau perkecil jari-jari kuas supaya tidak mengenai ujung lantai yang sempit.');throw new Error('Shrinkage '+f1(d)+' m terlalu besar untuk bentuk lantai di dalam poligon: lantai di bagian tersempit tidak muat digeser sejauh itu, sehingga string lantai saling menumpuk dan pit justru tidak menyempit (lantai terkecil tercapai pada ±'+f1(dm)+' m).\n\nSaran: pakai shrinkage '+f1(rec)+' m. Bila perlu lebih sempit, klik Jadikan dasar lalu ulangi shrinkage dengan jarak yang sama, atau perkecil poligon batas supaya tidak mencakup ujung lantai yang sempit.');}}}
 /* lantai minimum */const FL=NS.filter(q=>Math.abs(q.z-f.z)<0.05);if(!FL.length&&!f.open)throw new Error('Lantai habis — jarak terlalu besar.');if(sg<0&&F>0&&FL.length){const FP=FL.map(q=>toC(q.pts.slice(0,-1)));if(!cOff(FP,-F/2+0.01).length)throw new Error('Lantai baru lebih sempit dari lantai minimum '+F+' m — kurangi jarak.');}
 /* 2. string jalan / miring / potongan terbuka: medan geser yang sama.
    Ujung potongan yang berimpit (≤ 1 m, RL ±0,6) diberi SATU vektor geser bersama, dan smoothing dikurangi bertahap ke ujung —
    dulu tiap potongan merata-ratakan tetangganya sendiri sehingga sambungan pit final Surpac terbuka 1–3 m setelah shrinkage (16 Nov). */
 const PAIR=new Map(),EK=[];if(!window.__NOENDJ)for(const s of S){if(moved.has(s)||s.pts.length<2)continue;for(const p of [s.pts[0],s.pts[s.pts.length-1]]){let c=EK.find(e=>Math.abs(e.z-p[2])<0.6&&Math.hypot(e.x-p[0],e.y-p[1])<1);if(!c)EK.push(c={x:p[0],y:p[1],z:p[2],n:0,sx:0,sy:0});c.sx+=p[0];c.sy+=p[1];c.n++;}}
 for(const c of EK){c.v=vec([c.sx/c.n,c.sy/c.n]);}const endV=p=>{const c=EK.find(e=>Math.abs(e.z-p[2])<0.6&&Math.hypot(e.x-p[0],e.y-p[1])<1);return c&&c.n>1?c.v:null;};
 for(const s of S){if(moved.has(s))continue;const cl0=s.closed&&Math.hypot(s.pts[0][0]-s.pts[s.pts.length-1][0],s.pts[0][1]-s.pts[s.pts.length-1][1])<0.5;let Vs=smooth(s.pts.map(vec),cl0);
  if(!cl0&&EK.length){const m=s.pts.length,e0=endV(s.pts[0]),e1=endV(s.pts[m-1]);if(e0||e1)Vs=Vs.map((v,i)=>{let r=v;const t0=Math.min(1,i/4),t1=Math.min(1,(m-1-i)/4);if(e0&&t0<1)r=[e0[0]*(1-t0)+r[0]*t0,e0[1]*(1-t0)+r[1]*t0];if(e1&&t1<1)r=[e1[0]*(1-t1)+r[0]*t1,e1[1]*(1-t1)+r[1]*t1];return r;});}
  const np=s.pts.map((p,i)=>[p[0]+Vs[i][0],p[1]+Vs[i][1],p[2]]);if(s.closed&&np.length>2){const a=s.pts[0],b=s.pts[s.pts.length-1];if(Math.hypot(a[0]-b[0],a[1]-b[1])<0.5)np[np.length-1]=np[0].slice();}const ns_=Object.assign({},s,{pts:np});NS.push(ns_);PAIR.set(s,ns_);}
 /* 2b. ujung potongan yang semula menempel (≤ 1 m) ke string lain — termasuk ke tengahnya (sambungan T) — dikunci lagi ke posisi baru string pasangannya */
 if(!window.__NOENDJ){const nearSeg=(P,p,cl)=>{let bd=1e18,bq=null;const m=P.length;for(let i=0;i<m-(cl?0:1);i++){const a=P[i],b=P[(i+1)%m];if(Math.abs((a[2]+b[2])/2-p[2])>0.6&&Math.abs(a[2]-p[2])>0.6)continue;const dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2)),x=a[0]+dx*t,y=a[1]+dy*t,e=Math.hypot(p[0]-x,p[1]-y);if(e<bd){bd=e;bq=[x,y];}}return {d:bd,q:bq};};
  for(const [s0,s1] of PAIR){if(s0.closed||s0.pts.length<2)continue;const m=s0.pts.length;for(const e of [0,m-1]){const p=s0.pts[e];let best=null;for(const o of S){if(o===s0)continue;const r=nearSeg(o.pts,p,o.closed);if(r.d<1&&(!best||r.d<best.d))best={d:r.d,o};}if(!best)continue;
   const vp=vec(p),T=[p[0]+vp[0],p[1]+vp[1],p[2]];let tg=null;const cand=moved.has(best.o)?NS.filter(q=>q.pure&&Math.abs(q.z-best.o.z)<0.05):[PAIR.get(best.o)].filter(Boolean);for(const c of cand){const r=nearSeg(c.pts,T,c.closed);if(r.q&&r.d<4&&(!tg||r.d<tg.d))tg={d:r.d,q:r.q};}if(!tg)continue;
   const dx=tg.q[0]-s1.pts[e][0],dy=tg.q[1]-s1.pts[e][1];const KM=Math.max(1,Math.min(5,Math.floor(m/2)));for(let k=0;k<KM;k++){const i=e?m-1-k:k,f=1-k/KM;s1.pts[i]=[s1.pts[i][0]+dx*f,s1.pts[i][1]+dy*f,s1.pts[i][2]];}}}}
 /* 3. Push Back: tambah bench ke atas bila crest teratas kini di dalam batuan */let UP=[],rl=0;if(sg>0&&TP.length){const zt=lv[lv.length-1],TC=NS.filter(q=>q.closed&&Math.abs(q.z-zt)<0.05).map(q=>toC(q.pts.slice(0,-1)));
  if(TC.length&&!crestOut(TC,zt)){let best=null;for(const q of NS){if(q.pure||q.closed)continue;for(const p of q.pts)if(!best||p[2]>best[2])best=p;}const rp=RAMP();let mode=rpat(),v=null;
   if(best){const ms=rampMeasure({z:zt+80,pts:[]},{p:[best[0],best[1]]});if(ms){if(isFinite(ms.g)&&ms.g>0.02&&ms.g<0.3)rp.g=ms.g;if(isFinite(ms.W)&&ms.W>4&&ms.W<40)rp.W=ms.W;mode=ms.mode||mode;v=ms.v;}}
   const tz=topoZ(best?best[0]:0,best?best[1]:0),rr=best&&Math.abs(best[2]-zt)<1.5&&v?(()=>{const q=dirFromVec(TC,[best[0],best[1]],v);return [{ai:0,nm:'A',pt:q.pt,strike:v,dir:q.dir,sbs:[],sbEnd:false,on:true,first:false}];})():[];
   const tt=NS.filter(q=>q.closed&&q.t!=='floor'&&Math.abs(q.z-zt)<0.05);/* bench baru dibangun dari crest teratas (sebagai toe) */let st={up:true,P:TC,z:zt,pend:[]},rk=rr;for(let i=0;i<60;i++){const r=benchStep(st,rk,{zref:ED.zref,rp,mode});if(!r.bench)break;UP.push(r.bench);if(r.stop||crestOut(r.bench.crest,r.bench.zc))break;st=r.next;rk=r.ramps;}
   if(UP.length){for(const q of benchStrings(UP,null))if(!(q.t==='toe'&&Math.abs(q.z-zt)<0.05))NS.push(q);for(const b of UP)for(const r of (b.roads||[]))for(let i=1;i<r.in.length;i++)rl+=Math.hypot(r.in[i][0]-r.in[i-1][0],r.in[i][1]-r.in[i-1][1]);}}}
 const all=NS,foot=footOf(all.filter(q=>q.closed)),tin=surfOf(all,foot);let zmin=1e9;for(const q of all)for(const p of q.pts)zmin=Math.min(zmin,p[2]);
 ED.out={S:all,foot,tin,zmin,floorS:all.filter(q=>q.t==='floor'),B:UP};ED.out.vol=volOf(ED.out);ED.out.day=dayOf(ED.out);ED.out.kpi={n:UP.length};clr(G.edit);pitRedraw();dayDraw(ED.out);layRender();
 const A=P=>P.reduce((a,q)=>a+(q.area||0),0),dv=ED.out.vol.tot-(ED.base.vol?ED.base.vol.tot:0);const res={kind,d,dv,nUp:UP.length,rl,aF:A(FL),aF0:f.S.reduce((a,q)=>a+(q.area||0),0)};ED.lastResize=res;
 let h='<div class="kpi"><div><b>'+(dv>=0?'+':'')+nf(dv)+'</b><span>m³ '+(dv>=0?'tambahan':'berkurang')+'</span></div><div><b>'+nf(res.aF)+'</b><span>m² lantai (dulu '+nf(res.aF0)+')</span></div><div><b>'+UP.length+'</b><span>bench tambahan di atas</span></div></div>';
 h+=(sg>0?'<b>Push Back</b> ':'<b>Shrinkage</b> ')+f1(d)+' m'+(Z?' di dalam poligon batas (transisi '+f1(T)+' m ke dinding lama)':' seluruh pit')+'. Semua string digeser horizontal — bentuk bench &amp; <b>pola jalan lama dipertahankan</b> (lebar &amp; kemiringan tetap).';
 if(UP.length)h+='<br>Crest teratas kini di bawah topografi → '+UP.length+' bench ditambah ke atas'+(rl?', jalan diteruskan '+nf(rl)+' m meniru pola lama':'')+'.';
 if(chained)h+='<br>ℹ Hasil push back / shrinkage sebelumnya otomatis dijadikan dasar; perubahan ini ditambahkan di atasnya.';ED.zoneUsed=!!Z;h+='<br><a href="#" id="erun">Batalkan</a> · <a href="#" id="erok">Jadikan dasar (edit lagi)</a>';$('erres').innerHTML=h;$('e5st').textContent='✓ '+(sg>0?'push back':'shrinkage')+' '+f1(d)+' m';
 $('erun').onclick=e=>{e.preventDefault();ED.out=null;pitRedraw();$('erres').innerHTML='';$('e5st').textContent='';};$('erok').onclick=e=>{e.preventDefault();if(typeof edAccept==='function')edAccept();};return res;}
/* normal keluar dari bench terdekat (RL paling dekat) di titik p */
function ringNormal(p,s,ringsAt,lv){let zb=null,bd=1e9;for(const z of lv){const e=Math.abs(z-p[2]);if(e<bd){bd=e;zb=z;}}if(zb===null)return [0,0];const R=ringsAt.get(zb);let best=null;
 for(const r of R){const n=r.length;for(let i=0;i<n;i++){const a=r[i],b=r[(i+1)%n],dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy||1e-9,t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2)),e=Math.hypot(p[0]-a[0]-dx*t,p[1]-a[1]-dy*t);if(!best||e<best.e){const L=Math.sqrt(L2);best={e,n:[dy/L,-dx/L],r};}}}
 if(!best)return [0,0];/* arah keluar: sisi yang menjauhi bagian dalam poligon */let ar=0;const rr=best.r;for(let i=0;i<rr.length;i++){const a=rr[i],b=rr[(i+1)%rr.length];ar+=a[0]*b[1]-b[0]*a[1];}const o=ar>0?1:-1;return [best.n[0]*o,best.n[1]*o];}
$('epush').onclick=()=>{if(!ED){alert('Impor pit atau pakai hasil Desain baru dulu.');return;}try{runResize('push',Math.max(0.5,+$('erd').value||10));}catch(e){alert(e.message);}};
$('eshr').onclick=()=>{if(!ED){alert('Impor pit atau pakai hasil Desain baru dulu.');return;}try{runResize('shrink',Math.max(0.5,+$('erd').value||10));}catch(e){alert(e.message);}};

/* penampang permukaan desain pada RL z (sel grid dengan Z ≤ z) — untuk desain bertali terbuka */
function tinSec(tin,z){if(!tin||!tin.G)return [];const Gd=tin.G,c=Gd.cell,R=[];for(let j=0;j<Gd.ny;j++){let i0=-1;for(let i=0;i<=Gd.nx;i++){const v=i<Gd.nx?Gd.Z[j*Gd.nx+i]:NaN;const ok=v<=z+0.1;if(ok&&i0<0)i0=i;else if(!ok&&i0>=0){const x0=Gd.x0+(i0-0.5)*c,x1=Gd.x0+(i-0.5)*c,y0=Gd.y0+(j-0.5)*c;R.push(toC([[x0,y0],[x1,y0],[x1,y0+c],[x0,y0+c]]));i0=-1;}}}
 let U=R.length?cBool(R,[],ClipperLib.ClipType.ctUnion):[];if(U.length)U=cOff(cOff(U,1),-1).filter(r=>Math.abs(cArea(r))>20);return U;}
