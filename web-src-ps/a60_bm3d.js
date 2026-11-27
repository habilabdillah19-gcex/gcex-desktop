/* a60: BLOCK MODEL 3D di dalam desain (pemilik 24 Nov): tampilkan bentuk block model GC di dalam desain yang dibuat, diedit,
   atau staging — lengkap dengan filter dan pengaturan warna.
   - Sumber: block model .mdl yang sudah dimuat (Jadwal → Block model), dibaca untuk area desain terpilih (gtEnsure).
   - Batas: blok di dalam desain = pusat blok di bawah / pada topografi dan di atas / pada desain (cara Surpac, TIN presisi;
     sama persis dengan Laporan G×T desain) — atau "semua blok di bawah topografi" di area itu.
   - Filter: rentang nilai atribut, rentang RL (sayat horizontal), kelas (sembunyikan waste / kelas tertentu).
   - Warna: kelas G×T (ikut aturan laporan) atau gradasi atribut apa pun (skema + batas bawah / atas), transparansi, celah blok.
   - Kursor di atas blok = isi blok. Ikut diperbarui otomatis saat desain berubah (G×T otomatis).
   Menu: Tampilan → Block model 3D; Project Tree → Data → Block model. */
const B3={ka:'',flt:[],hideK:{},on:false,ds:'',attr:'',mode:'kelas',ramp:'spektrum',lo:'',hi:'',inDes:true,hide:{},zlo:'',zhi:'',fmin:'',fmax:'',op:1,gap:0.06,g:null,mesh:null,idx:null,busy:false,stat:null};
try{const s=JSON.parse(localStorage.getItem('psBm3d')||'{}');for(const k of ['attr','mode','ramp','lo','hi','inDes','hide','op','gap','ka','flt','hideK'])if(k in s)B3[k]=s[k];if(!Array.isArray(B3.flt))B3.flt=[];if(!B3.hideK||typeof B3.hideK!=='object')B3.hideK={};}catch(_){}
function b3Ka(){const m=GT.m;return B3.ka&&m&&m.num&&m.num[B3.ka]?B3.ka:GT.attr;}
function b3Hide(ka){if(!ka||ka===GT.attr)return B3.hide;return B3.hideK[ka]||(B3.hideK[ka]={});}
function b3Save(){try{const o={};for(const k of ['attr','mode','ramp','lo','hi','inDes','hide','op','gap','ka','flt','hideK'])o[k]=B3[k];localStorage.setItem('psBm3d',JSON.stringify(o));}catch(_){}}
const B3R={spektrum:['#2b5fb4','#33a86f','#eed64d','#db5438'],panas:['#fff5c0','#f9a13a','#d7301f','#67000d'],hijau:['#f2f7e6','#9ccf6c','#3c8f3a','#0b4d1e'],abu:['#f0f0f0','#b0b0b0','#6e6e6e','#2e2e2e']};
function b3Ramp(t){const R=B3R[B3.ramp]||B3R.spektrum,u=Math.max(0,Math.min(1,t))*(R.length-1),a=Math.min(Math.floor(u),R.length-2),f=u-a;const c1=new THREE.Color(R[a]),c2=new THREE.Color(R[a+1]);return c1.lerp(c2,f);}
function b3Clear(){if(B3.g){B3.g.parent&&B3.g.parent.remove(B3.g);try{B3.g.traverse(o=>{o.geometry&&o.geometry.dispose();o.material&&o.material.dispose&&o.material.dispose();});}catch(_){}B3.g=null;B3.mesh=null;B3.idx=null;}}
function b3Msg(h,c){const e=$('b3st');if(e)e.innerHTML=h?'<span style="color:'+(c?'#c92a2a':'#495057')+'">'+h+'</span>':'';}
/* pilih blok sesuai desain + filter */
async function b3Run(){if(B3.busy)return;if(!GT.file){b3Msg('Muat block model .mdl dulu: <a href="#" id="b3ld">Jadwal → Block model…</a>',1);const a=$('b3ld');if(a)a.onclick=e=>{e.preventDefault();gtOpen(true);};b3Clear();return;}
 const D=schDes(),d=D.find(x=>x.id===B3.ds)||D[0];if(!d){b3Msg('Belum ada desain (Pit final, staging, atau pit yang diedit).',1);b3Clear();return;}B3.ds=d.id;
 const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G);if(!tp){b3Msg('Muat topografi dulu.',1);return;}
 B3.busy=true;b3Msg('Membaca block model untuk "'+esc(d.nm)+'"…');
 try{const G=d.G;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,zlo=1e18,zhi=-1e18;
  for(let j=0;j<G.ny;j++)for(let i=0;i<G.nx;i++){const z=G.Z[j*G.nx+i];if(!(z===z))continue;const x=G.x0+i*G.cell,y=G.y0+j*G.cell,zt=gridZ(tp.G,x,y);if(!(zt===zt)||!(z<zt-0.05))continue;if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y;if(z<zlo)zlo=z;if(zt>zhi)zhi=zt;}
  if(!(zlo<1e17))throw new Error('Desain "'+d.nm+'" tidak memotong topografi aktif.');
  await gtEnsure({x0:x0-G.cell,x1:x1+G.cell,y0:y0-G.cell,y1:y1+G.cell,zlo,zhi,tp,c:Math.max(1,G.cell)});const m=GT.m;
  const names=Object.keys(m.num||{});if(!B3.attr||!m.num[B3.attr])B3.attr=GT.attr&&m.num[GT.attr]?GT.attr:names[0];
  const fT=pxTopoFn(tp),fD=pxDesFn(d),A=m.num[B3.attr],Gr=m.num[GT.attr]||A,SGa=GT.sg?m.num[GT.sg]:null;
  const zl=B3.zlo===''?-1e18:+B3.zlo,zh=B3.zhi===''?1e18:+B3.zhi,fl=B3.fmin===''?-1e18:+B3.fmin,fh=B3.fmax===''?1e18:+B3.fmax;
  const KA=b3Ka(),KAu=KA===GT.attr,KAv=m.num[KA]||Gr,KR=ufRules(KA).length,HK=b3Hide(KA),FL=(B3.flt||[]).filter(f=>f&&f.a&&m.num[f.a]);
  const sel=[],K=KR,st={n:0,t:new Array(K+1).fill(0),c:new Array(K+1).fill(0),vmin:1e18,vmax:-1e18,zmin:1e18,zmax:-1e18};
  for(let b=0;b<m.n;b++){const x=m.x[b],y=m.y[b],cz=m.z[b];if(x<x0-G.cell||x>x1+G.cell||y<y0-G.cell||y>y1+G.cell)continue;
   const zt=fT?fT(x,y):gridZ(tp.G,x,y);if(!(zt===zt)||cz>zt)continue;
   if(B3.inDes){const zd=fD?fD(x,y):gridZ(G,x,y);if(!(zd===zd)||cz<zd)continue;}
   if(cz<zl||cz>zh)continue;const v=A[b];if(v===v&&(v<fl||v>fh))continue;if(!(v===v)&&(B3.fmin!==''||B3.fmax!==''))continue;
   const c=KAu?gtCls(Gr[b]):ufCls(KA,KAv[b]),ck=c<0?K:c;if(HK[ck])continue;if(FL.length&&!ufPass(FL,a=>m.num[a][b]))continue;
   let sg=SGa?SGa[b]:GT.sgc;if(!(sg>0))sg=GT.sgc;const t=m.sx[b]*m.sy[b]*m.sz[b]*sg;st.t[ck]+=t;st.c[ck]++;st.n++;
   if(v===v){if(v<st.vmin)st.vmin=v;if(v>st.vmax)st.vmax=v;}if(cz<st.zmin)st.zmin=cz;if(cz>st.zmax)st.zmax=cz;sel.push(b);}
  B3.stat=st;B3.sel=sel;B3.d=d;b3Draw();b3Ui();
  b3Msg(st.n?'<b>'+st.n.toLocaleString('id-ID')+'</b> blok · '+esc(d.nm)+(B3.inDes?' (di dalam desain, pusat blok)':' (semua di bawah topografi)'):'Tidak ada blok yang lolos filter.',!st.n);}
 catch(e){b3Msg('&#9888; '+esc(e.message),1);}finally{B3.busy=false;}}
function b3Draw(){b3Clear();if(!B3.on||!B3.sel||!B3.sel.length){return;}const m=GT.m,S=B3.sel,n=S.length,A=m.num[B3.attr],Gr=m.num[GT.attr]||A;
 let lo=+B3.lo,hi=+B3.hi;if(B3.lo===''||!(lo===lo))lo=B3.stat.vmin;if(B3.hi===''||!(hi===hi))hi=B3.stat.vmax;if(!(hi>lo))hi=lo+1;
 const geo=new THREE.BoxGeometry(1,1,1),mat=new THREE.MeshLambertMaterial({transparent:B3.op<1,opacity:B3.op,depthWrite:B3.op>=1});
 const M=new THREE.InstancedMesh(geo,mat,n),o=new THREE.Object3D(),col=new THREE.Color(),Wc=new THREE.Color('#a59a8b'),KA=b3Ka(),KAv=m.num[KA]||Gr,RC_=ufRules(KA).map(r=>new THREE.Color(r.c)),gp=1-Math.max(0,Math.min(0.4,B3.gap));
 for(let i=0;i<n;i++){const b=S[i];o.position.copy(V(m.x[b],m.y[b],m.z[b]));o.scale.set(m.sx[b]*gp,m.sz[b]*gp,m.sy[b]*gp);o.updateMatrix();M.setMatrixAt(i,o.matrix);
  if(B3.mode==='kelas'){const c=KA===GT.attr?gtCls(Gr[b]):ufCls(KA,KAv[b]);col.copy(c<0?Wc:RC_[c]);}else{const v=A[b];if(v===v)col.copy(b3Ramp((v-lo)/(hi-lo)));else col.set('#cccccc');}M.setColorAt(i,col);}
 M.instanceMatrix.needsUpdate=true;if(M.instanceColor)M.instanceColor.needsUpdate=true;M.renderOrder=3;
 const g=new THREE.Group();g.add(M);W.add(g);B3.g=g;/* lapisan jadwal (sel / blok tambang) menutupi block model → disembunyikan selama tampil */B3.mesh=M;B3.lohi=[lo,hi];}
/* ---------- panel ---------- */
(function(){const w=document.createElement('div');w.id='b3w';w.className='flw win';w.style.width='360px';
 w.innerHTML='<div class="flh"><b>&#9638; Block model 3D</b><span class="sp"></span><button class="x">&#10005;</button></div><div class="flb" id="b3b"></div>';
 const iw=$('iw');(iw&&iw.parentNode?iw.parentNode:document.body).insertBefore(w,iw||null);
 const st=document.createElement('style');st.textContent='#b3b .r{display:flex;gap:5px;align-items:center;margin:3px 0;flex-wrap:wrap}#b3b input[type=number]{width:62px}#b3b select{max-width:150px}#b3b .lg{display:flex;align-items:center;gap:5px;font-size:11.5px;margin:1px 0}#b3b .lg i{width:12px;height:12px;border-radius:2px;display:inline-block}#b3b .lg.off{opacity:.4}#b3b details{margin-top:4px}#b3b summary{cursor:pointer;font-weight:600}';document.head.appendChild(st);
 w.querySelector('.x').onclick=()=>b3Show(false);try{flDrag(w);}catch(_){}/* panel dibuat sesudah dockInit: pasang tombol tempel / lepas (pemilik 25 Nov: panel tidak bisa digeser) */try{dockInit();}catch(_){}})();
function b3Off(){B3.on=false;b3Clear();try{if(B3.schV&&SCH.g){SCH.g.visible=!!SCH.show||true;B3.schV=false;}}catch(_){}}
function b3Ui(){const b=$('b3b');if(!b)return;const D=schDes(),m=GT.m,names=m&&m.num?Object.keys(m.num):[],st=B3.stat,K=GT.rules.length;
 const opt=(v,l,c)=>'<option value="'+esc(v)+'"'+(v===c?' selected':'')+'>'+esc(l)+'</option>';
 let h='<label style="display:flex;gap:6px;align-items:center;font-weight:600"><input type="checkbox" id="b3on"'+(B3.on?' checked':'')+'> Tampilkan block model di 3D</label>';
 h+='<div class="r">Desain <select id="b3ds">'+(D.length?D.map(x=>opt(x.id,x.nm,B3.ds||D[0].id)).join(''):'<option>— belum ada —</option>')+'</select></div>';
 h+='<div class="r"><label><input type="radio" name="b3in" value="1"'+(B3.inDes?' checked':'')+'> di dalam desain</label><label><input type="radio" name="b3in" value="0"'+(!B3.inDes?' checked':'')+'> semua di bawah topografi</label></div>';
 h+='<details open><summary>Warna</summary><div class="r"><label><input type="radio" name="b3m" value="kelas"'+(B3.mode==='kelas'?' checked':'')+'> kelas G×T</label><label><input type="radio" name="b3m" value="grad"'+(B3.mode==='grad'?' checked':'')+'> gradasi atribut</label></div>';
 if(B3.mode==='kelas'){const KA=b3Ka(),R=ufRules(KA),HK=b3Hide(KA),KR=R.length;h+='<div class="r">Kelas unsur <select id="b3ka" title="Unsur yang menentukan kelas (warna)">'+names.map(n=>opt(n,n,KA)).join('')+'</select> <a href="#" id="b3ke">atur kelas</a></div><div class="hint">Klik kelas untuk sembunyikan / tampilkan.'+(KA===GT.attr?' Kelas '+esc(GT.attr)+' mengikuti Laporan G×T.':'')+'</div>';
  R.forEach((r,i)=>{h+='<div class="lg'+(HK[i]?' off':'')+'" data-k="'+i+'" style="cursor:pointer"><i style="background:'+r.c+'"></i><b>'+esc(r.m)+'</b> '+esc(KA)+' '+r.lo+(r.hi!==''&&r.hi!=null?'–'+r.hi:'+')+(st&&st.c.length===KR+1?' · '+st.c[i].toLocaleString('id-ID')+' blok · '+gtShort(st.t[i])+' t':'')+'</div>';});
  h+='<div class="lg'+(HK[KR]?' off':'')+'" data-k="'+KR+'" style="cursor:pointer"><i style="background:#a59a8b"></i><b>'+(KA===GT.attr?'Waste':'Di bawah kelas')+'</b>'+(st&&st.c.length===KR+1?' · '+st.c[KR].toLocaleString('id-ID')+' blok · '+gtShort(st.t[KR])+' t':'')+'</div>';}
 else{h+='<div class="r">Atribut <select id="b3at">'+names.map(n=>opt(n,n,B3.attr)).join('')+'</select> Skema <select id="b3rp">'+Object.keys(B3R).map(k=>opt(k,k,B3.ramp)).join('')+'</select></div>';
  h+='<div style="height:9px;border-radius:4px;background:linear-gradient(90deg,'+(B3R[B3.ramp]||B3R.spektrum).join(',')+')"></div><div class="r" style="justify-content:space-between">bawah <input id="b3lo" type="number" step="any" value="'+esc(B3.lo)+'" placeholder="'+(B3.lohi?(+B3.lohi[0]).toFixed(2):'auto')+'"> atas <input id="b3hi" type="number" step="any" value="'+esc(B3.hi)+'" placeholder="'+(B3.lohi?(+B3.lohi[1]).toFixed(2):'auto')+'"></div>';}
 h+='<div class="r">Transparansi <input id="b3op" type="range" min="0.2" max="1" step="0.05" value="'+B3.op+'" style="width:90px"> Celah <input id="b3gp" type="range" min="0" max="0.3" step="0.02" value="'+B3.gap+'" style="width:70px"></div></details>';
 h+='<details'+((B3.flt.length||B3.zlo!==''||B3.zhi!=='')?' open':'')+'><summary>Filter</summary><div id="b3flt"></div>'+
  '<div class="r">RL dari <input id="b3zlo" type="number" step="any" value="'+esc(B3.zlo)+'" placeholder="'+(st&&st.n?f1(st.zmin):'')+'"> s/d <input id="b3zhi" type="number" step="any" value="'+esc(B3.zhi)+'" placeholder="'+(st&&st.n?f1(st.zmax):'')+'"></div>'+
  '<div class="hint">Filter unsur: pilih unsur, lalu rentang kadar (kosong = tanpa batas) atau kelas yang ditampilkan. RL: kosong = tanpa batas.</div><button id="b3fx">Hapus filter</button></details>';
 h+='<div class="r" style="margin-top:6px"><button id="b3go" class="pri">&#8635; Perbarui</button><span id="b3st" style="font-size:11.5px"></span></div>';
 const keep=$('b3st')?$('b3st').innerHTML:'';b.innerHTML=h;$('b3st').innerHTML=keep;
 const re=()=>{b3Save();b3Run();};
 $('b3on').onchange=()=>{B3.on=$('b3on').checked;if(B3.on)b3Run();else b3Off();};
 if($('b3ds'))$('b3ds').onchange=()=>{B3.ds=$('b3ds').value;re();};
 b.querySelectorAll('[name=b3in]').forEach(x=>x.onchange=()=>{B3.inDes=x.value==='1';re();});
 b.querySelectorAll('[name=b3m]').forEach(x=>x.onchange=()=>{B3.mode=x.value;b3Save();b3Draw();b3Ui();});
 b.querySelectorAll('.lg[data-k]').forEach(x=>x.onclick=()=>{const k=+x.dataset.k,HK=b3Hide(b3Ka());HK[k]=!HK[k];re();});
 if($('b3ka'))$('b3ka').onchange=()=>{B3.ka=$('b3ka').value;re();};const ke=$('b3ke');if(ke)ke.onclick=e=>{e.preventDefault();ufKlsDlg(b3Ka(),()=>{b3Save();b3Run();});};
 ufFltUi($('b3flt'),B3.flt,re);
 if($('b3at'))$('b3at').onchange=()=>{B3.attr=$('b3at').value;B3.lo='';B3.hi='';re();};
 if($('b3rp'))$('b3rp').onchange=()=>{B3.ramp=$('b3rp').value;b3Save();b3Draw();b3Ui();};
 const num=(id,k,run)=>{const e=$(id);if(e)e.onchange=()=>{B3[k]=e.value.trim();b3Save();if(run)b3Run();else{b3Draw();b3Ui();}};};
 num('b3lo','lo',false);num('b3hi','hi',false);num('b3zlo','zlo',true);num('b3zhi','zhi',true);
 $('b3op').oninput=()=>{B3.op=+$('b3op').value;b3Save();if(B3.mesh){B3.mesh.material.opacity=B3.op;B3.mesh.material.transparent=B3.op<1;B3.mesh.material.depthWrite=B3.op>=1;B3.mesh.material.needsUpdate=true;}};
 $('b3gp').onchange=()=>{B3.gap=+$('b3gp').value;b3Save();b3Draw();};
 $('b3fx').onclick=()=>{B3.fmin=B3.fmax=B3.zlo=B3.zhi='';B3.flt.length=0;B3.hide={};B3.hideK={};re();};
 $('b3go').onclick=()=>b3Run();}
function b3Show(on){const w=$('b3w');if(!w)return;winShow(w,on);if(on){if(!B3.ds){const D=schDes();const pref=['edo','edb','stg','res','fin'];for(const p of pref){if(D.find(x=>x.id===p)){B3.ds=p;break;}}}b3Ui();if(!B3.on){B3.on=true;b3Ui();}b3Run();}}
/* desain yang sedang diedit (ED.base) ikut daftar desain → bisa dilaporkan & ditampilkan */
{const _d=schDes;schDes=function(){const o=_d.apply(this,arguments);try{if(typeof ED!=='undefined'&&ED&&ED.base&&ED.base.tin&&ED.base.tin.G&&ED.base!==RES&&ED.base!==STG&&!o.find(x=>x.id==='edb'))o.push({id:'edb',nm:'Pit sedang diedit'+(ED.nm?' ('+String(ED.nm).slice(0,24)+')':''),G:ED.base.tin.G,tin:ED.base.tin});}catch(_){}return o;};}
/* desain berubah (G×T otomatis menghitung ulang) → blok 3D ikut */
{const _g=gtDesign;gtDesign=function(){const r=_g.apply(this,arguments);Promise.resolve(r).then(()=>{if(B3.on&&!B3.busy){clearTimeout(B3._t);B3._t=setTimeout(b3Run,150);}},()=>{});return r;};}
/* kursor di atas blok → isi blok */
(function(){const tip=document.createElement('div');tip.style.cssText='position:fixed;z-index:61;pointer-events:none;background:#1f2a37;color:#fff;font:11.5px system-ui;padding:4px 8px;border-radius:4px;display:none;line-height:1.35';document.body.appendChild(tip);let t0=0;
 R.domElement.addEventListener('pointermove',e=>{if(!B3.mesh||e.buttons){tip.style.display='none';return;}const n=performance.now();if(n-t0<70)return;t0=n;
  try{if(typeof HOV!=='undefined'&&HOV.k){tip.style.display='none';return;}}catch(_){}
  ndc(e);const h=RC.intersectObject(B3.mesh,false)[0];if(!h||h.instanceId==null){tip.style.display='none';return;}const m=GT.m,b=B3.sel[h.instanceId];
  const rows=Object.keys(m.num).slice(0,8).map(k=>{const v=m.num[k][b];return esc(k)+': <b>'+(v===v?(Math.abs(v)>=100?f1(v):(+v).toFixed(3)):'—')+'</b>';});
  const KA=b3Ka(),c=ufCls(KA,(m.num[KA]||[])[b]),RR=ufRules(KA);tip.innerHTML='Blok E '+f1(m.x[b])+' · N '+f1(m.y[b])+' · RL '+f1(m.z[b])+' ('+f1(m.sx[b])+'×'+f1(m.sy[b])+'×'+f1(m.sz[b])+' m)<br>'+(KA===GT.attr?'':esc(KA)+' ')+(c<0?ufBawah(KA):'<b>'+esc(RR[c].m)+'</b>')+' · '+rows.join(' · ');
  tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+12)+'px';tip.style.display='';});
 R.domElement.addEventListener('pointerleave',()=>tip.style.display='none');})();
/* menu & Project Tree */
try{const _A=window.__PS3&&window.__PS3.shAct;}catch(_){}
try{window.__PS3.b3={S:B3,run:()=>b3Run(),show:v=>b3Show(v!==false),n:()=>B3.sel?B3.sel.length:0};}catch(_){}
/* 25 Nov (pemilik): "legenda yang disetting untuk block model kenapa tidak muncul di Legenda 3D?" → bagian Block model ditambahkan
   ke Legenda 3D selama block model tampil: kelas (unsur, warna, rentang; kelas yang disembunyikan tidak dicantumkan) atau gradasi
   atribut (skema + batas), ditambah ringkasan filter unsur / RL yang aktif. */
function b3LegHtml(){if(!B3.on||!B3.mesh||!B3.sel||!B3.sel.length)return '';const sw=(c,t)=>'<div class="lr"><i style="height:11px;border:1px solid #0002;background:'+c+'"></i>'+t+'</div>';let h='<div class="lr" style="margin-top:5px;font-weight:600">Block model 3D · '+B3.sel.length.toLocaleString('id-ID')+' blok</div>';
 if(B3.mode==='kelas'){const KA=b3Ka(),R=ufRules(KA),HK=b3Hide(KA);R.forEach((r,i)=>{if(!HK[i])h+=sw(r.c,esc(r.m)+' · '+esc(KA)+' '+r.lo+(r.hi===''||r.hi==null?'+':'–'+r.hi));});if(!HK[R.length])h+=sw('#a59a8b',KA===GT.attr?'Waste':esc(KA)+' di bawah kelas');}
 else{const L=B3.lohi||[0,1],R=B3R[B3.ramp]||B3R.spektrum;h+='<div class="lr" style="display:block">'+esc(B3.attr)+' <span style="display:inline-block;width:90px;height:9px;vertical-align:middle;border-radius:2px;background:linear-gradient(90deg,'+R.join(',')+')"></span> '+gtExFmt(+L[0])+' – '+gtExFmt(+L[1])+'</div>';}
 const F=(B3.flt||[]).filter(f=>f&&f.a).map(f=>{if(f.md==='kls'){const R=ufRules(f.a),on=R.map((r,k)=>f.h&&f.h[k]?null:r.m).filter(Boolean);if(!(f.h&&f.h.w))on.push(ufBawah(f.a));return on.length===R.length+1?null:esc(f.a)+': '+on.map(esc).join(', ');}
  const lo=f.lo===''||f.lo==null?null:f.lo,hi=f.hi===''||f.hi==null?null:f.hi;if(lo==null&&hi==null)return null;return esc(f.a)+' '+(lo!=null&&hi!=null?lo+'–'+hi:lo!=null?'≥ '+lo:'≤ '+hi);}).filter(Boolean);
 if(B3.zlo!==''||B3.zhi!=='')F.push('RL '+(B3.zlo===''?'…':B3.zlo)+'–'+(B3.zhi===''?'…':B3.zhi));
 if(F.length)h+='<div class="lr" style="display:block;color:#b35c00;font-size:11px">Filter: '+F.join(' · ')+'</div>';return h;}
{const _l=legend;legend=function(){const r=_l.apply(this,arguments);try{const b=$('lgb'),x=b3LegHtml();if(b&&x){if(b.querySelector('.hint'))b.innerHTML='';b.insertAdjacentHTML('beforeend',x);}}catch(e){console.warn(e);}return r;};}
{const _d=b3Draw;b3Draw=function(){const r=_d.apply(this,arguments);try{legend();}catch(_){}return r;};}
{const _o=b3Off;b3Off=function(){const r=_o.apply(this,arguments);try{legend();}catch(_){}return r;};}
