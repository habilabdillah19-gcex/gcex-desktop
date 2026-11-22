/* a41: Pit Schedule lebih intuitif.
   1) Panel disusun sebagai 4 LANGKAH bernomor (Area → Blok tambang → Alat & cara gali → Jalankan & hasil): satu langkah terbuka,
      tiap judul memberi tahu status / apa yang harus dilakukan; langkah berikutnya terbuka sendiri. "semua" membuka semuanya.
   2) Batas area bisa diambil dari desain dengan satu klik.
   3) SINKRON 3D: selama mode gambar / pilih (batas, jalur gali, arah strip, klik blok, gambar desain, garis sayatan) seret kiri
      TIDAK memutar tampilan. Putar = seret tombol tengah, geser = seret kanan, zoom = roda. Petunjuk tampil di atas 3D. */
const UX={sel:null,cur:-1,all:false};
/* desain acuan jadwal: pilihan pengguna di langkah 1 (berdiri sendiri dari mode Pit final / Staging) */
function schRefDes(D){D=D||schDes();return D.find(x=>x.id===SCH.refId)||D.find(x=>x.id==='res')||D[0];}
(function(){const bd=$('schbd');if(!bd||$('uxs1'))return;const st=document.createElement('style');st.textContent=
`.uxs{border:1px solid #dde3ee;border-radius:6px;margin:4px 0;background:#fff}.uxs>.uxh{display:flex;align-items:center;gap:6px;padding:4px 6px;cursor:pointer;user-select:none;border-radius:6px}.uxs>.uxh:hover{background:#f4f6fa}
.uxn{flex:0 0 20px;height:20px;border-radius:50%;background:#adb5bd;color:#fff;font-weight:700;font-size:11.5px;display:flex;align-items:center;justify-content:center}.uxs.done .uxn{background:#2f9e44}.uxs.cur .uxn{background:#f08c00}
.uxt{font-weight:700;white-space:nowrap}.uxi{flex:1;font-size:11px;color:#6c757d;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}.uxs.cur{border-color:#f0b34a;box-shadow:0 0 0 2px rgba(240,140,0,.13)}.uxs.cur .uxi{color:#b35c00}
.uxb{padding:2px 6px 6px;display:none}.uxs.open>.uxb{display:block}.uxway{display:flex;align-items:center;gap:6px;margin:3px 0}.uxway button{flex:0 0 132px;text-align:left;font-weight:700}.uxway span{font-size:11px;color:#6c757d;line-height:1.25}
#uxtop{display:flex;align-items:center;gap:6px;font-size:11px;color:#6c757d;margin-bottom:2px}#schinf{background:#fffdf5;border:1px solid #f1e3b5;border-radius:5px;padding:4px 6px;margin:2px 0 4px}#schtb{max-height:150px!important}#schres details>div{max-height:120px;overflow:auto}#gttb{max-height:170px;overflow:auto}#schinf:empty{display:none}
#uxhint{position:fixed;left:50%;top:86px;transform:translateX(-50%);z-index:45;background:rgba(20,32,58,.92);color:#fff;border-radius:6px;padding:5px 12px;font:12px system-ui,Segoe UI,Arial,sans-serif;display:none;max-width:70vw;text-align:center;pointer-events:none;box-shadow:0 3px 12px rgba(0,0,0,.25)}#uxhint b{color:#ffd43b}#uxhint small{display:block;opacity:.8;font-size:10.5px;margin-top:1px}`;
 document.head.appendChild(st);const mk=(i,t)=>{const d=document.createElement('div');d.className='uxs';d.id='uxs'+i;d.innerHTML='<div class="uxh"><span class="uxn">'+i+'</span><span class="uxt">'+t+'</span><span class="uxi" id="uxi'+i+'"></span></div><div class="uxb" id="uxb'+i+'"></div>';d.firstChild.onclick=()=>{UX.sel=UX.sel===i&&!d.classList.contains('cur')?null:i;uxSync(true);};return d;};
 const S=[0,mk(1,'Data & area'),mk(2,'Blok tambang'),mk(3,'Alat & cara gali'),mk(4,'Hasil & laporan')],B=i=>S[i].lastChild,kids=[...bd.children];
 const top=document.createElement('div');top.id='uxtop';top.innerHTML='<span>Ikuti langkah 1 → 4. Judul langkah menunjukkan apa yang perlu dilakukan.</span><span style="flex:1"></span><label title="Buka semua langkah sekaligus (tampilan lama)"><input type="checkbox" id="uxall"> semua</label>';
 const row=h=>{const r=document.createElement('div');r.className='r';if(h)r.innerHTML=h;return r;};
 try{
  /* 1 Area */
  const Q1=id=>S[1].querySelector('#'+id);
  B(1).appendChild(row('<span style="flex:0 0 78px;color:#495057">Topografi</span><span id="uxtp" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>'));
  B(1).appendChild(row('<span style="flex:0 0 78px;color:#495057" title="Batas / permukaan desain yang menjadi lantai galian jadwal. Diimpor langsung di sini — tidak perlu masuk mode Pit final / Staging.">Desain acuan</span><select id="uxdes" style="flex:1;min-width:0;font-size:11.5px"></select><button id="uxdfb" title="Impor string desain acuan (.str / .dxf): pit final, staging, atau batas tambang lain">&#8679; Impor</button><input type="file" id="uxdf" accept=".str,.dxf,.txt" hidden>'));
  B(1).appendChild(row('<span style="flex:0 0 78px;color:#495057">Block model</span><span id="uxbm" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span><button id="uxbmb" title="Muat block model Surpac (.mdl) untuk kadar, tonase dan SR">&#8679; Muat .mdl</button><button id="uxbmc" title="Atribut kadar / SG, aturan blok, kelas kadar & tujuan">&#9881;</button>'));
  Q1('uxdfb').onclick=()=>{if(!TP.some(q=>q.on&&q.G)){schMsg('Impor topografi dulu (menu Impor).',1);return;}$('uxdf').click();};
  Q1('uxdf').onchange=async e=>{const f=e.target.files[0];e.target.value='';if(!f)return;try{const L=await readFileL(f);finFromL(L,f.name);if(!(FIN&&FIN.rg&&FIN.rg.G))throw new Error('permukaan desain tidak bisa dibentuk dari berkas ini (perlu string bench crest / toe).');SCH.refId='fin';uxSync(true);mbAutoCalc();schMsg('Desain acuan: <b>'+esc(f.name)+'</b>. Lanjut: gambar Batas fase atau <b>Pakai batas desain</b>.');}catch(err){schMsg(esc(f.name+': '+err.message),1);}};
  Q1('uxdes').onchange=()=>{SCH.refId=$('uxdes').value;mbAutoCalc();uxSync(true);};
  Q1('uxbmb').onclick=()=>{gtWin();$('gtf').click();};Q1('uxbmc').onclick=()=>gtOpen(true);
  const r1=row();r1.appendChild($('schap'));const bdz=document.createElement('button');bdz.id='uxbd';bdz.innerHTML='&#9635; Pakai batas desain';bdz.title='Batas area diambil dari tapak galian desain (pit final / staging / pit final impor) — tanpa menggambar';r1.appendChild(bdz);r1.appendChild($('schbn'));B(1).appendChild(r1);B(1).appendChild($('schdg').parentElement);
  const n1=row('<span style="font-size:11px;color:#6c757d">Klik <b>Batas fase</b>, lalu klik titik-titik batas di 3D (Enter / klik ganda = selesai). Di luar batas tidak digali.</span>');B(1).appendChild(n1);
  /* 2 Blok tambang */
  B(2).appendChild($('mbrow'));B(2).appendChild(kids[1]);B(2).appendChild($('mbopt'));B(2).appendChild($('mbleg'));
  /* 3 Alat & cara gali */
  const w=(btn,tx)=>{const r=document.createElement('div');r.className='uxway';r.appendChild(btn);const s=document.createElement('span');s.innerHTML=tx;r.appendChild(s);return r;};
  B(3).appendChild(row('<span style="font-size:11px;color:#6c757d">Pilih cara gali (boleh digabung). Alat tiap fleet diatur di kartu fleet di bawah.</span>'));
  B(3).appendChild(w($('schego'),'seluruh area turun bench demi bench — langsung dihitung, laporan tiap bench'));
  B(3).appendChild(w($('mbpk'),'klik blok tambang di 3D satu per satu; urutan klik = urutan gali fleet tujuan'));
  B(3).appendChild(w($('schal'),'tarik garis arah gali alat di 3D; lebar = strip, dalam = 1 bench per lintasan'));
  const r3=row();r3.appendChild($('schfl'));r3.appendChild($('schtr').parentElement);B(3).appendChild(r3);B(3).appendChild($('schtl'));B(3).appendChild($('sched'));B(3).appendChild($('schrun').parentElement);
  /* 4 Jalankan & hasil */
  B(4).appendChild($('schres'));B(4).appendChild($('schph'));
  for(const k of kids)if(k.parentElement===bd&&k.id!=='schinf')k.style.display='none';
  bd.insertBefore(top,bd.firstChild);bd.insertBefore($('schinf'),top.nextSibling);for(let i=1;i<=4;i++)bd.appendChild(S[i]);try{const u=$('schun');if(u&&u.value==='h'){u.value='s';}}catch(_){}
  $('uxall').onchange=()=>{UX.all=$('uxall').checked;try{localStorage.setItem('psSchAll',UX.all?'1':'');}catch(_){}uxSync(true);};try{UX.all=!!localStorage.getItem('psSchAll');$('uxall').checked=UX.all;}catch(_){}
  bdz.onclick=()=>{try{uxBndDesign();}catch(e){schMsg(esc(e.message),1);}};
 }catch(e){console.error('ux',e);}
 const h=document.createElement('div');h.id='uxhint';document.body.appendChild(h);})();
function uxState(){const ph=schPh(),bn=ph&&ph.bnd&&ph.bnd.length>=3,T=SCH.tasks.filter(t=>t.on),d=[bn,!!MB.R,T.length>0,!!SCH.sim],I=[];
 if(bn){let a=0;const b=ph.bnd;for(let i=0;i<b.length;i++){const p=b[i],q=b[(i+1)%b.length];a+=p[0]*q[1]-q[0]*p[1];}I[0]=b.length+' titik · '+schF(Math.abs(a)/2/1e4,2)+' ha';}else I[0]=!TP.some(q=>q.G)?'impor topografi dulu':SCH.dig&&SCH.dig.type==='bnd'?'klik titik batas di 3D…':'impor desain acuan & block model, lalu tentukan batas';
 if(MB.R){let o=0,m=0;for(const q of MB.R.L){o+=q.ore;m+=q.met;}I[1]=MB.R.L.length+' blok'+(MB.R.bm?' · '+gtShort(o)+' t ore @ '+(o>0?(m/o).toFixed(2):'–')+' g/t':' · muat .mdl untuk kadar');}else I[1]=bn?(MB.err?'⚠ '+MB.err:'menghitung…'):'dibuat otomatis setelah batas ada';
 if(T.length){const nb=T.filter(t=>t.mbk).length,nl=T.filter(t=>t.type==='line'&&!t.mbk).length,na=T.length-nb-nl,g=new Set(T.filter(t=>t.type==='line').map(t=>t.grp||'A1')).size;I[2]=[g?g+' fleet':'',nb?nb+' blok':'',nl?nl+' jalur':'',na?na+' area':''].filter(Boolean).join(' · ')+(SCH.sim?'':' → tekan ▶ Jalankan');}else I[2]=bn?'pilih: Turun per bench / Klik blok / Jalur gali':'setelah langkah 1';
 I[3]=SCH.sim?gtShort(SCH.sim.vtot||0)+' BCM terjadwal'+(GT.res?' · laporan siap':''):'muncul setelah Jalankan';
 const cur=!d[0]?0:!SCH.sim?2:3;d[2]=d[2]&&!!SCH.sim||(T.length>0&&!!SCH.sim);return {d,I,cur};}
function uxData(){const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G),D=schDes(),sel=$('uxdes'),h=D.length?D.map(x=>'<option value="'+x.id+'">'+esc(x.nm)+'</option>').join(''):'<option value="">(belum ada — Impor)</option>';if(sel.innerHTML!==h)sel.innerHTML=h;const r=schRefDes(D);if(r&&sel.value!==r.id)sel.value=r.id;
 const t=tp?esc(String(tp.nm).replace(/^[0-9a-f]{8}-/,'')):'<span style="color:#c92a2a">belum ada — menu Impor → topografi</span>';if($('uxtp').innerHTML!==t)$('uxtp').innerHTML=t;
 const b=GT.file?esc(GT.file.name)+' · '+esc(GT.attr||''):'<span style="color:#b35c00">belum dimuat (tanpa kadar)</span>';if($('uxbm').innerHTML!==b)$('uxbm').innerHTML=b;return [tp?1:0,D.length,GT.file?1:0];}
function uxSync(force){if(!$('uxs1'))return;let DA;try{DA=uxData();}catch(_){}let X;try{X=uxState();}catch(_){return;}const demo=(typeof DMO!=='undefined'&&DMO.on),all=UX.all||(demo&&!UX.keep),sg=JSON.stringify([X,UX.sel,all,DA]);if(!force&&sg===UX.sg)return;UX.sg=sg;
 if(X.cur!==UX.cur){UX.cur=X.cur;UX.sel=X.cur+1;}
 for(let i=1;i<=4;i++){const s=$('uxs'+i);s.classList.toggle('done',!!X.d[i-1]);s.classList.toggle('cur',X.cur===i-1);s.classList.toggle('open',all||UX.sel===i);$('uxi'+i).textContent=(X.d[i-1]?'✓ ':'')+X.I[i-1];$('uxi'+i).title=X.I[i-1];}}
/* batas area dari tapak galian desain: selubung cembung sel desain yang lebih rendah dari topografi */
function uxBndDesign(){const ph=schPh();if(ph.lock)throw new Error(ph.nm+' sudah dikunci.');const D=schDes();if(!D.length)throw new Error('Belum ada desain. Buat desain dulu, atau impor pit final di mode Staging — atau gambar batasnya dengan Batas fase.');
 const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G);if(!tp)throw new Error('Impor topografi dulu.');const d=schRefDes(D),G=d.G,P=[],st=Math.max(1,Math.round(Math.sqrt(G.nx*G.ny/60000)));
 for(let j=0;j<G.ny;j+=st)for(let i=0;i<G.nx;i+=st){const z=G.Z[j*G.nx+i];if(!(z===z))continue;const x=G.x0+i*G.cell,y=G.y0+j*G.cell,t=gridZ(tp.G,x,y);if(t===t&&t-z>0.5)P.push([x,y]);}
 if(P.length<3)throw new Error('Desain "'+d.nm+'" tidak punya galian di bawah topografi aktif.');
 P.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const cr=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]),lo=[],up=[];for(const p of P){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],p)<=0)lo.pop();lo.push(p);}for(let k=P.length-1;k>=0;k--){const p=P[k];while(up.length>=2&&cr(up[up.length-2],up[up.length-1],p)<=0)up.pop();up.push(p);}
 let H=lo.slice(0,-1).concat(up.slice(0,-1));let cx=0,cy=0;for(const p of H){cx+=p[0];cy+=p[1];}cx/=H.length;cy/=H.length;const pad=G.cell*st+2;
 H=H.map(p=>{const dx=p[0]-cx,dy=p[1]-cy,l=Math.hypot(dx,dy)||1;return [p[0]+dx/l*pad,p[1]+dy/l*pad];});
 /* sederhanakan: simpan titik bila arah berbelok > 10° sejak titik tersimpan terakhir (atau sudah > 150 m) */const Q=[H[0]];for(let k=1;k<H.length;k++){const a=Q[Q.length-1],b=H[k],c=H[(k+1)%H.length],h1=Math.atan2(b[1]-a[1],b[0]-a[0]),h2=Math.atan2(c[1]-b[1],c[0]-b[0]);let da=Math.abs(h2-h1);if(da>Math.PI)da=2*Math.PI-da;if(da>0.175||Math.hypot(b[0]-a[0],b[1]-a[1])>150)Q.push(b);}
 if(SCH.dig)schDigEnd(false);ph.bnd=(Q.length>=3?Q:H).map(p=>{const z=topoZ(p[0],p[1]);return [p[0],p[1],z===z?z:0];});if(!SCH.sim)SCH.grid=null;schTasks();schDrawStatic();schMsg('Batas area diambil dari tapak <b>'+esc(d.nm)+'</b> ('+ph.bnd.length+' titik). Blok tambang dihitung otomatis.');uxSync(true);}
/* ---------- sinkron 3D: mode gambar tidak memutar tampilan ---------- */
(function(){const M0=Object.assign({},CT.mouseButtons),T0=Object.assign({},CT.touches||{});let on=null,txt='';
 const mode=()=>{try{if(SCH.dig)return {bnd:'Batas fase',line:'Jalur gali',poly:'Area gali',haul:'Jalur angkut',dir:'Arah strip'}[SCH.dig.type]||'Gambar';}catch(_){}try{if(MB.pick)return 'Klik blok';}catch(_){}try{if(typeof DG!=='undefined'&&DG)return 'Gambar desain';}catch(_){}try{if(SAY.pick)return 'Garis sayatan';}catch(_){}return '';};
 setInterval(()=>{const m=mode(),h=$('uxhint');if(!!m!==on){on=!!m;if(on){CT.mouseButtons={LEFT:-1,MIDDLE:THREE.MOUSE.ROTATE,RIGHT:THREE.MOUSE.PAN};try{CT.touches={ONE:-1,TWO:THREE.TOUCH.DOLLY_PAN};}catch(_){}}else{CT.mouseButtons=Object.assign({},M0);try{CT.touches=Object.assign({},T0);}catch(_){}}}
  let t='';if(m){const d=SCH.dig,n=d?d.pts.length:0,what=m==='Klik blok'?'klik blok = jadwalkan · klik lagi blok yang sama = bench berikutnya (lebih dalam) · Shift + klik = batal · tombol Klik blok = selesai':m==='Arah strip'?'klik titik A lalu B, kemudian Enter':m==='Gambar desain'||m==='Garis sayatan'?'klik titik di 3D':'klik titik di 3D'+(n?' ('+n+' titik)':'')+' · Enter / klik ganda = selesai · Backspace = hapus titik · Esc = batal';
   t='<b>'+m+'</b> — '+what+'<small>tampilan terkunci dari putaran: roda = zoom · seret kanan = geser · seret tombol tengah = putar</small>';}
  if(t!==txt){txt=t;h.innerHTML=t;h.style.display=t&&(UX.keep||!(typeof DMO!=='undefined'&&DMO.on))?'block':'none';}
  try{uxSync();}catch(_){}},150);})();
try{window.__PS3.ux={state:()=>uxState(),bnd:()=>uxBndDesign(),sync:()=>uxSync(true),btn:()=>JSON.stringify(CT.mouseButtons)};}catch(_){}
/* ---------- pilihan alat diingat: alat gali / angkut, unit, jam, PA, UA dst. yang terakhir diatur menjadi bawaan fleet & area baru,
   juga setelah Reset dan saat aplikasi dibuka lagi (localStorage psSchAlat) ---------- */
const UXEQ=['alat','pm2','bkt','cyc','ff','eff','sw','prod','unit','sch','pa','ua','nu','hl','hk','hp','hv','vl','ve','td','ts','hn','hf','hg'];
function uxEqGet(){try{return JSON.parse(localStorage.getItem('psSchAlat')||'null');}catch(_){return null;}}
function uxEqSave(){try{let t=null;if(typeof SCH.sel==='string'){const g=SCH.sel.slice(2);t=[...SCH.tasks].reverse().find(x=>x.type==='line'&&(x.grp||'A1')===g);}else t=SCH.tasks.find(x=>x.id===SCH.sel);if(!t)return;const o={};for(const k of UXEQ)if(t[k]!==undefined)o[k]=t[k];localStorage.setItem('psSchAlat',JSON.stringify(o));}catch(_){}}
(function(){const e=$('sched');if(e){e.addEventListener('change',()=>setTimeout(uxEqSave,0));e.addEventListener('input',()=>{clearTimeout(UX._eq);UX._eq=setTimeout(uxEqSave,400);});}})();
{const _a=schAdd;schAdd=function(type,P,o){try{if(type==='line'||type==='poly'){const has=type==='line'&&SCH.tasks.some(x=>x.type==='line'),pf=uxEqGet();if(pf&&!has)o=Object.assign({},pf,o||{});}}catch(_){}return _a.call(this,type,P,o);};}
